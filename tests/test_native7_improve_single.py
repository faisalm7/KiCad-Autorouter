"""Constructed selection controls, not actual selected7/Native qualification.

The Native replay primitive is mocked explicitly to isolate ancestry checks.
These controls establish ancestry logic only; Native/installed/GUI proof is separate.
"""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,sexpr as sx,strategy as s
from tests.test_strategy import BOARD,candidate_tree,metrics

class SingleSelectionPrerequisiteTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name).resolve()
        for name in ('code','snapshot','trials','incumbent/candidate','candidate'):(self.root/name).mkdir(parents=True)
        code=self.root/'code/strategy.py';code.write_bytes(Path(s.__file__).read_bytes())
        self.source=self.root/'source/owned.kicad_pcb';self.source.parent.mkdir();self.source.write_text(BOARD)
        (self.root/'snapshot'/self.source.name).write_text(BOARD)
        self.tree=candidate_tree(sx.parse(BOARD));self.best=self.root/'incumbent/candidate'/self.source.name;sx.write(self.best,self.tree)
        self.native={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'findings':[]}
        self.inc={'accepted':True,'status':'routing_accepted','candidate':str(self.best),'candidate_sha256':p.sha(self.best),
            'metrics':metrics(self.tree),'native':self.native,'steps':[]}
        p.save_json(self.root/'incumbent/result.json',self.inc);sx.write(self.root/'candidate'/self.source.name,self.tree)
        self.data=dict(schema=1,single_selection_policy=s.SINGLE_SELECTION_POLICY,strategy='native_validated_zone_net_pruning',
            proposal_policy='single',engine_profile='tuned',adapter='both',scope='whole_board_unlocked_routing',
            finalization_reserve_seconds=25.,finalization_cpu_reserve_seconds=25.,source=str(self.source),
            tools={'implementation_sha256':{'autorouter/strategy.py':p.sha(code)}},trials=[],steps=[],improvements=0,
            best_observed_candidate=str(self.best),best_observed_metrics=metrics(self.tree),metrics=metrics(self.tree),
            candidate_sha256=p.sha(self.root/'candidate'/self.source.name),native=self.native)
        for item in (patch.object(s.c,'NATIVE_VERSION','10.0.7'),patch.object(s,'check_pruning_preferences')):
            item.start();self.addCleanup(item.stop)
    def check(self):return s.check_single_selection(self.root,self.data)
    def trial(self,accepted=True):
        folder=self.root/'trials/trial-0000';folder.mkdir();(folder/'candidate').mkdir()
        proposal=s.proposals(self.tree,{'1'},[r for r in p.routes(self.tree) if p.locked(r)],False)[0]
        after=s.delete_routes(self.tree,proposal['route_ids'],{'1'},[r for r in p.routes(self.tree) if p.locked(r)])
        sx.write(folder/'pre-refill.kicad_pcb',after);sx.write(folder/'candidate'/self.source.name,after)
        result=dict(id=folder.name,proposal=proposal,base_candidate_sha256=p.sha(self.best),accepted=accepted,
            status='improvement_validated' if accepted else 'quality_rejected',metrics=metrics(after),native=self.native,steps=[])
        p.save_json(folder/'result.json',result)
        self.data['trials']=[dict(id=folder.name,receipt=str(folder/'result.json'),status=result['status'],accepted=accepted)]
        if accepted:
            sx.write(self.root/'candidate'/self.source.name,after)
            self.data.update(best_observed_candidate=str(folder/'candidate'/self.source.name),best_observed_metrics=metrics(after),
                metrics=metrics(after),improvements=1,candidate_sha256=p.sha(self.root/'candidate'/self.source.name))
        return folder,result
    def test_no_improvement_returns_exact_retained_incumbent(self):self.assertEqual(self.check(),self.best)
    def test_selected_single_deletion_and_protected_copper_are_reconstructed(self):
        folder,_=self.trial()
        with patch.object(s,'_adaptive_trial_native',return_value=True) as replay:
            self.assertEqual(self.check(),folder/'candidate'/self.source.name)
            self.assertEqual(replay.call_args.kwargs,{'guard_key':'single_trial_guard'})
    def test_incomplete_trial_cannot_be_selected(self):
        self.trial()
        with patch.object(s,'_adaptive_trial_native',return_value=False),self.assertRaises(p.Rejected):self.check()
    def test_reauthored_trial_cannot_switch_incumbent_or_policy(self):
        folder,result=self.trial()
        for key,value in [('base_candidate_sha256','0'*64),('proposal',dict(result['proposal'],kind='native_warning_cleanup'))]:
            bad=copy.deepcopy(result);bad[key]=value;p.save_json(folder/'result.json',bad)
            with patch.object(s,'_adaptive_trial_native',return_value=True),self.assertRaises(p.Rejected):self.check()
    def test_final_hash_does_not_hide_protected_or_selected_copper_change(self):
        self.trial();final=self.root/'candidate'/self.source.name;tree=sx.read(final)
        locked=next(r for r in p.routes(tree) if p.locked(r));sx.one(locked,'width')[1]='0.300001';sx.write(final,tree)
        self.data['candidate_sha256']=p.sha(final)
        with patch.object(s,'_adaptive_trial_native',return_value=True),self.assertRaises(p.Rejected):self.check()
    def test_source_policy_population_and_compute_census_cannot_downgrade(self):
        for key,value in [('single_selection_policy',None),('proposal_policy','feedback'),('engine_profile','standard'),('steps',[{'phase':'omitted'}])]:
            with self.subTest(key=key):
                before=copy.deepcopy(self.data);self.data[key]=value
                with self.assertRaises(p.Rejected):self.check()
                self.data=before
        (self.root/'trials/hidden').mkdir()
        with self.assertRaises(p.Rejected):self.check()

    def test_real_primitive_guard_dispatch_stops_before_or_reaches_binding(self):
        # Exercise the actual dispatch and reserve predicates. The sentinel
        # replaces only the first subsequent file/Native binding primitive;
        # it does not claim that a constructed record passed Native validation.
        data={'budget_seconds':90.,'cpu_budget_seconds':90.,'source':str(self.source),'source_hashes':{}}
        guard={'wall_deadline_elapsed_seconds':65.,'work_cpu_limit_seconds':65.}
        for field in ('adaptive_trial_guard','single_trial_guard'):
            record={'id':'trial-0000','status':'quality_rejected','steps':[],
                'finished_elapsed_seconds':10.,'finished_observed_cpu_seconds':10.,
                'candidate_sha256':'a'*64,field:guard}
            for selected in ('default','adaptive_trial_guard','single_trial_guard'):
                options={} if selected=='default' else {'guard_key':selected}
                expected='adaptive_trial_guard' if selected=='default' else selected
                with self.subTest(field=field,selected=selected),patch.object(p,'verify_candidate_files',
                        side_effect=p.Rejected('binding sentinel after guard')) as binding:
                    if field==expected:
                        with self.assertRaisesRegex(p.Rejected,'binding sentinel after guard'):
                            s._adaptive_trial_native(self.root,data,record,**options)
                        binding.assert_called_once()
                    else:
                        self.assertFalse(s._adaptive_trial_native(self.root,data,record,**options))
                        binding.assert_not_called()
        for invalid in (None,True,{},'other_guard'):
            with self.subTest(invalid=invalid),patch.object(p,'verify_candidate_files') as binding:
                with self.assertRaises(p.Rejected):s._adaptive_trial_native(self.root,data,record,guard_key=invalid)
                binding.assert_not_called()

if __name__=='__main__':unittest.main()
