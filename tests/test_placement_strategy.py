"""Pure lineage/policy regression controls; these never establish native quality."""
import copy,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import test_board_floor_policy as fixture
from autorouter import placement_strategy as ps,pipeline as p,floor_route as f,sexpr as sx,strategy as s

class SharedStages(unittest.TestCase):
    setUp=fixture.FloorReceipt.setUp
    save=fixture.FloorReceipt.save
    def stage(self):
        row=copy.deepcopy(self.data)
        row['steps']=[x for x in row['steps'] if x['name'] in ('refill-drc','floor-final','final-drc','metrics')]
        before=p.transplant_routes(self.task,sx.read(self.out/'imported.kicad_pcb'))
        return row,before
    def test_actual_stage_directory_wins_over_same_name_in_incumbent(self):
        row,before=self.stage();step=next(x for x in row['steps'] if x['name']=='final-drc')
        foreign=dict(step,cwd=str(self.out/'incumbent'),emitted_candidate='foreign',validated_input_sha256='wrong')
        row['steps'].insert(0,foreign)
        candidate,native,metrics=ps.check_candidate_stage(self.out,row,self.original,self.hashes,self.out,before)
        self.assertEqual(candidate,self.candidate);self.assertEqual(native,self.data['native'])
        self.assertEqual(metrics,self.data['metrics'])
        row['steps'].append(step)
        with self.assertRaises(p.Rejected):ps.check_candidate_stage(self.out,row,self.original,self.hashes,self.out,before)
    def test_reconstructed_parent_cannot_change_even_with_unchanged_final(self):
        row,before=self.stage();ps.check_candidate_stage(self.out,row,self.original,self.hashes,self.out,before)
        changed=copy.deepcopy(before);changed.remove(p.routes(changed)[0])
        with self.assertRaises(p.Rejected):ps.check_candidate_stage(self.out,row,self.original,self.hashes,self.out,changed)
    def test_rehashed_original_rule_change_rejects(self):
        row,before=self.stage();project=self.candidate.with_suffix('.kicad_pro');raw=json.loads(project.read_text())
        raw['board']['design_settings']['rule_severities']['clearance']='ignore';project.write_text(json.dumps(raw))
        with self.assertRaises(p.Rejected):ps.check_candidate_stage(self.out,row,self.original,self.hashes,self.out,before)
    def test_guidance_basis_requires_contract_before_any_native(self):
        job=SimpleNamespace(out=self.out)
        with self.assertRaisesRegex(p.Rejected,'requires a contract'):
            p.validate_candidate(job,self.original,self.candidate,self.hashes,[],guidance_basis=self.out)

class PruningSelection(unittest.TestCase):
    def test_duplicate_warning_is_new_even_when_identity_already_exists(self):
        warning={'type':'track_dangling','severity':'warning','items':[{'uuid':'same'}]}
        old={'findings':[warning]};new={'findings':[warning,copy.deepcopy(warning)]}
        self.assertFalse(ps.improves({'track_length_mm':1,'vias':0},{'track_length_mm':2,'vias':0},new,old))
        self.assertTrue(ps.improves({'track_length_mm':1,'vias':0},{'track_length_mm':2,'vias':0},old,new))
    def test_deletion_rejects_duplicate_wrong_net_and_locked_route(self):
        with tempfile.TemporaryDirectory(dir=fixture.ROOT/".cache") as tmp:
            path=Path(tmp)/'board.kicad_pcb'
            tree=sx.parse('(kicad_pcb (segment (net 1) (start 0 0) (end 1 0) (uuid "one")) (segment (net 1) (locked yes) (uuid "protected")))')
            sx.write(path,tree);a,b=[s.route_id(x) for x in p.routes(tree)]
            self.assertEqual(len(p.routes(ps.deletion(path,{'net':'1','route_ids':[a]},{'1'}))),1)
            for proposal in ({'net':'1','route_ids':[a,a]},{'net':'2','route_ids':[a]},{'net':'1','route_ids':[b]},{'net':'1','route_ids':['absent']}):
                with self.subTest(proposal=proposal),self.assertRaises(p.Rejected):ps.deletion(path,proposal,{'1'})
    def test_policy_marker_cannot_be_downgraded_or_mixed(self):
        with tempfile.TemporaryDirectory(dir=fixture.ROOT/".cache") as tmp:
            out=Path(tmp);marker=out/'pruning-contract.json';p.save_json(marker,ps.contract())
            row={'schema':5,'input_policy':ps.POLICY,'strategy':ps.STRATEGY,'baseline':'C-prototype','adapter':'both','engine_profile':'tuned','scoring_variant':'via_default','scope':'whole_board_unlocked_routing','proposal_policy':'feedback','pruning_contract':{'file':marker.name,'sha256':p.sha(marker)}}
            self.assertTrue(ps.recognize(row,out))
            for key,value in [('schema',1),('input_policy','native'),('strategy','native_validated_zone_net_pruning'),('routing_preferences',{}),('scope','partial_completion')]:
                with self.subTest(key=key),self.assertRaises(p.Rejected):ps.recognize(dict(row,**{key:value}),out)
            with self.assertRaises(p.Rejected):ps.recognize({'schema':1},out)
    def test_incomplete_feedback_parent_never_reaches_native_feedback(self):
        row={'completed':False,'accepted':False,'status':'quality_rejected','parent':'owned-parent'}
        with patch.object(s,'feedback_proposal') as call:
            with self.assertRaises(p.Rejected):ps.feedback_decision(row,Path('owned-parent'),{},set())
            call.assert_not_called()
    def test_deterministic_base_order_excludes_duplicate_or_reordered_proposals(self):
        with tempfile.TemporaryDirectory(dir=fixture.ROOT/'.cache') as tmp:
            best=Path(tmp)/'board.kicad_pcb'
            tree=sx.parse('(kicad_pcb (segment (net 1) (start 0 0) (end 8 0) (uuid "long")) (segment (net 1) (start 0 1) (end 1 1) (uuid "short")))')
            sx.write(best,tree);nets={'1'}
            state={'grouped':s.proposals(tree,nets,[],True),'individual':None}
            self.assertEqual(ps.next_base_proposal(state,best,nets)['kind'],'whole_zone_net')
            self.assertEqual(ps.next_base_proposal(state,best,nets)['ranking_length_mm'],8.)
            self.assertEqual(ps.next_base_proposal(state,best,nets)['ranking_length_mm'],1.)
            self.assertIsNone(ps.next_base_proposal(state,best,nets))
    def test_bare_legacy_receipt_is_not_reclassified(self):
        with tempfile.TemporaryDirectory(dir=fixture.ROOT/".cache") as tmp:self.assertFalse(ps.recognize({'schema':1,'strategy':'native_validated_zone_net_pruning'},Path(tmp)))

class FailedProcessHistory(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=fixture.ROOT/'.cache');self.addCleanup(self.tmp.cleanup)
        self.out=Path(self.tmp.name);candidate=self.out/'candidate/board.kicad_pcb'
        argv=[*f.SANDBOX,str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones',
            '--exit-code-violations','--output',str(self.out/'refill-drc.json'),'--save-board',str(self.out/'refill/board.kicad_pcb')]
        self.process={'name':'refill-drc','cwd':str(self.out),'argv':argv,'status':'timeout','exit_code':None,'cleanup_complete':True,
            'wall_seconds':9.,'cpu_seconds':8.,'monitor_cpu_seconds':.1}
        p.save_json(self.out/'refill-drc-process.json',self.process)
        self.row={'candidate':str(candidate),'assigned_seconds':12.,'completed':False,'wall_seconds':9.2,'total_cpu_seconds':8.3,'steps':[copy.deepcopy(self.process)]}
    def test_failed_process_is_retained_and_honest_cleanup_overshoot_allowed(self):
        self.assertEqual(ps.trial_process_history(self.out,self.row),self.row['steps'])
        self.row['assigned_seconds']=4.
        self.assertEqual(ps.trial_process_history(self.out,self.row),self.row['steps'])
        self.row['completed']=True
        with self.assertRaises(p.Rejected):ps.trial_process_history(self.out,self.row)
    def test_failed_process_cannot_be_omitted_or_its_cost_rehashed_away(self):
        for changes in ({'steps':[]},{'wall_seconds':0.},{'total_cpu_seconds':0.}):
            with self.subTest(changes=changes),self.assertRaises(p.Rejected):ps.trial_process_history(self.out,dict(self.row,**changes))
    def test_process_argv_and_raw_fields_must_match_even_when_failed(self):
        row=copy.deepcopy(self.row);row['steps'][0]['cpu_seconds']=0.
        with self.assertRaises(p.Rejected):ps.trial_process_history(self.out,row)
        self.process['argv'].remove('--save-board');row['steps']=[self.process];p.save_json(self.out/'refill-drc-process.json',self.process)
        with self.assertRaises(p.Rejected):ps.trial_process_history(self.out,row)
    def test_failed_trial_finite_bounds_are_mandatory(self):
        for changes in ({'assigned_seconds':True},{'assigned_seconds':3.},{'wall_seconds':float('nan')},{'total_cpu_seconds':-1.}):
            with self.subTest(changes=changes),self.assertRaises(p.Rejected):ps.trial_process_history(self.out,dict(self.row,**changes))

if __name__=='__main__':unittest.main()
