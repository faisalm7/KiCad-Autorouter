"""Pure fixed-allocation controls; no native/JVM or routing-quality claims."""
import copy,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import ExitStack,contextmanager
from autorouter import placement_strategy as ps,pipeline as p,floor_route as f,sexpr as sx,strategy as strategy
from scripts import experiment_paired as paired,experiment_quality as quality
HERE=Path(__file__).resolve().parent

class AllocationControls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name);self.out=self.folder/'run';self.out.mkdir()
    def receipt(self,allocation=ps.LEGACY_ALLOCATION):
        settings=ps.contract(allocation);marker=self.out/'pruning-contract.json';p.save_json(marker,settings)
        value={'schema':5,'input_policy':ps.POLICY,'strategy':ps.STRATEGY,'baseline':'C-prototype','adapter':'both',
            'engine_profile':settings['incumbent_profile'],'scoring_variant':'via_default','scope':'whole_board_unlocked_routing',
            'proposal_policy':'feedback','pruning_contract':{'file':marker.name,'sha256':p.sha(marker)},'budget_seconds':120.,
            'incumbent_assigned_seconds':100. if allocation==ps.LEGACY_ALLOCATION else 85.}
        if allocation==ps.STANDARD_ALLOCATION:
            value.update(pruning_allocation=allocation,incumbent_assignment_observation={'elapsed_wall_seconds':1.,'elapsed_full_cpu_seconds':2.})
        inc={'schema':4,'input_policy':f.SEARCH_POLICY,'adapter':'both','scope':'whole_board_unlocked_routing','accepted':True,
             'engine_profile':settings['incumbent_profile'],'scoring_variant':'via_default',
             'budget_seconds':value['incumbent_assigned_seconds'],'cpu_budget_seconds':value['incumbent_assigned_seconds']}
        return value,inc
    def test_legacy_contract_serialization_matches_actual_pair002(self):
        marker=self.out/'pruning-contract.json';p.save_json(marker,ps.contract())
        self.assertEqual(p.sha(marker),'e2f71244b7f297cb8d5a858ae253ac35e123090fcb5592eff0123053945ea744')
        row,inc=self.receipt();self.assertTrue(ps.recognize(row,self.out));self.assertEqual(ps.check_incumbent_allocation(row,inc),ps.LEGACY_ALLOCATION)
    def test_new_contract_and_root_marker_cannot_relabel_old_runs(self):
        row,inc=self.receipt(ps.STANDARD_ALLOCATION);self.assertEqual(ps.contract(ps.STANDARD_ALLOCATION)['schema'],2)
        self.assertTrue(ps.recognize(row,self.out));self.assertEqual(ps.check_incumbent_allocation(row,inc),ps.STANDARD_ALLOCATION)
        for changed in ({k:v for k,v in row.items() if k!='pruning_allocation'},dict(row,engine_profile='tuned'),dict(row,pruning_allocation=ps.LEGACY_ALLOCATION)):
            with self.subTest(changed=changed),self.assertRaises(p.Rejected):ps.recognize(changed,self.out)
        p.save_json(self.out/'pruning-contract.json',ps.contract())
        row['pruning_contract']['sha256']=p.sha(self.out/'pruning-contract.json')
        with self.assertRaises(p.Rejected):ps.recognize(row,self.out)
    def test_new_order_longest_individuals_then_lazy_current_whole_nets_is_replayed(self):
        best=self.out/'board.kicad_pcb';tree=sx.parse('(kicad_pcb (segment (net 1) (start 0 0) (end 8 0) (uuid "long")) (segment (net 1) (start 0 1) (end 1 1) (uuid "short")))');sx.write(best,tree)
        nets={'1'};states=[{'grouped':None,'individual':None} for _ in range(2)]
        records=[]
        for _ in range(3):
            pair=[ps.next_base_proposal(state,best,nets,'individual-first') for state in states]
            self.assertEqual(pair[0],pair[1]);records.append(pair[0])
        self.assertEqual([x['kind'] for x in records],['individual_segment','individual_segment','whole_zone_net'])
        self.assertEqual([x['ranking_length_mm'] for x in records[:2]],[8.,1.])
        self.assertTrue(all(ps.next_base_proposal(state,best,nets,'individual-first') is None for state in states))
        old={'grouped':strategy.proposals(tree,nets,[],True),'individual':None}
        self.assertEqual(ps.next_base_proposal(old,best,nets)['kind'],'whole_zone_net')
        self.assertNotEqual(records[0],strategy.proposals(tree,nets,[],True)[0])
        # A selected deletion changes the later whole-net parent; do not use stale initial IDs.
        state={'grouped':None,'individual':None};first=ps.next_base_proposal(state,best,nets,'individual-first')
        sx.write(best,ps.deletion(best,first,nets));second=ps.next_base_proposal(state,best,nets,'individual-first')
        whole=ps.next_base_proposal(state,best,nets,'individual-first');self.assertEqual(whole['route_ids'],second['route_ids'])
    def test_rehashed_order_and_reserve_contract_changes_do_not_admit_variant(self):
        row,_=self.receipt(ps.STANDARD_ALLOCATION);marker=self.out/'pruning-contract.json'
        for changes in ({'proposal_order':'whole-first'},{'final_reserve_seconds':15.},{'incumbent_max_seconds':86.}):
            p.save_json(marker,dict(ps.contract(ps.STANDARD_ALLOCATION),**changes));row['pruning_contract']['sha256']=p.sha(marker)
            with self.subTest(changes=changes),self.assertRaises(p.Rejected):ps.recognize(row,self.out)
    def test_unknown_allocation_and_native_downgrade_are_blocked(self):
        for value in (True,None,'standard','standard-86-v1',{}):
            with self.subTest(value=value),self.assertRaises(p.Rejected):ps.contract(value)
        with self.assertRaises(p.Rejected):ps.recognize({'schema':1,'pruning_allocation':ps.STANDARD_ALLOCATION},self.out)
    def test_allocation_charges_slower_wall_or_full_cpu_without_reducing_reserve(self):
        self.assertEqual(ps.incumbent_assignment(120,1,2,ps.STANDARD_ALLOCATION),85)
        self.assertEqual(ps.incumbent_assignment(100,1,10,ps.STANDARD_ALLOCATION),65)
        self.assertEqual(ps.incumbent_assignment(100,20,1,ps.STANDARD_ALLOCATION),55)
        self.assertEqual(ps.incumbent_assignment(60,1,2,ps.STANDARD_ALLOCATION),33)
        self.assertEqual(ps.incumbent_assignment(120,1,2,ps.LEGACY_ALLOCATION),103)
        for x in (True,float('nan'),float('inf'),-1):
            with self.subTest(x=x),self.assertRaises(p.Rejected):ps.incumbent_assignment(120,x,1,ps.STANDARD_ALLOCATION)
    def test_readback_binds_exact_assignment_observation_profile_and_both_caps(self):
        row,inc=self.receipt(ps.STANDARD_ALLOCATION)
        self.assertEqual(ps.check_incumbent_allocation(row,inc),ps.STANDARD_ALLOCATION)
        for change in ({'engine_profile':'tuned'},{'budget_seconds':86},{'cpu_budget_seconds':84}):
            with self.subTest(change=change),self.assertRaises(p.Rejected):ps.check_incumbent_allocation(row,dict(inc,**change))
        for observed in (None,{}, {'elapsed_wall_seconds':1,'elapsed_full_cpu_seconds':31}, {'elapsed_wall_seconds':True,'elapsed_full_cpu_seconds':2}):
            changed=dict(row,incumbent_assignment_observation=observed)
            with self.subTest(observed=observed),self.assertRaises(p.Rejected):ps.check_incumbent_allocation(changed,inc)
        legacy,old=self.receipt();legacy['incumbent_assignment_observation']={'elapsed_wall_seconds':1,'elapsed_full_cpu_seconds':2}
        with self.assertRaises(p.Rejected):ps.check_incumbent_allocation(legacy,old)
    def test_actual_prune_invocation_owns_fresh_profile_and_preserves_failed_incumbent(self):
        # Route is mocked and deliberately rejected before any validator/worker.
        source=self.folder/'source';source.mkdir();board=source/'board.kicad_pcb';board.write_text('pure original')
        results=[]
        def job(out,seconds,remaining):out.mkdir();return SimpleNamespace(out=out,steps=[])
        def failed(*args,**kwargs):
            results.append((args,kwargs));basis=args[1];basis.mkdir();p.save_json(basis/'result.json',{'accepted':False})
            return {'steps':[],'accepted':False,'status':'drc_rejected','reason':'declared synthetic incumbent rejection'}
        tools={'implementation_sha256':{}}
        with ExitStack() as stack:
            for target,name,value in [(f,'FloorJob',job),(p,'check_storage',lambda:None),(p,'preflight',lambda _:[]),
                (ps.pc,'narrow_source',lambda _:None),(ps.pc,'inventory',lambda _:{}),(ps.pc,'evidence_inventory',lambda _:{}),
                (p,'tool_manifest',lambda:tools),(f,'route',failed),(f,'publish',lambda out,report,*_:report)]:stack.enter_context(patch.object(target,name,value))
            stack.enter_context(patch.object(ps.time,'monotonic',return_value=0.));stack.enter_context(patch.object(ps.time,'process_time',return_value=0.));stack.enter_context(patch.object(f,'child_cpu',return_value=0.))
            for allocation in (ps.LEGACY_ALLOCATION,ps.STANDARD_ALLOCATION):
                result=ps.prune(board,self.folder/allocation,120,allocation=allocation)
                self.assertFalse(result['accepted']);self.assertIn('declared synthetic incumbent rejection',result['reason'])
                args,kwargs=results[-1];self.assertEqual(args[0],board.resolve());self.assertEqual(args[1],self.folder/allocation/'incumbent')
                self.assertEqual(args[2],105 if allocation==ps.LEGACY_ALLOCATION else 85);self.assertEqual(args[5],'tuned' if allocation==ps.LEGACY_ALLOCATION else 'standard')
                self.assertEqual(kwargs,{'guidance_policy':f.SEARCH_POLICY})
                self.assertEqual('pruning_allocation' in result,allocation==ps.STANDARD_ALLOCATION)
                self.assertEqual('incumbent_assignment_observation' in result,allocation==ps.STANDARD_ALLOCATION)
    def test_actual_first_attempt_reaches_validation_under_time_reserve_for_both_paths(self):
        # The full _prune control path runs to its first real deletion/copy and
        # mocked validation callback. No engine/native worker or accepted PCB.
        for allocation in (ps.LEGACY_ALLOCATION,ps.STANDARD_ALLOCATION):
            with self.subTest(allocation=allocation):
                source=self.folder/(allocation+'-source');source.mkdir();board=source/'board.kicad_pcb'
                original=sx.parse('(kicad_pcb (segment (net 1) (start 0 0) (end 8 0) (uuid "long")) (segment (net 1) (start 0 1) (end 1 1) (uuid "short")) (zone (net 1)))')
                sx.write(board,original);board.with_suffix('.kicad_pro').write_text('{}')
                clock={'wall':0.,'cpu':0.};reached=[]
                def job(out,seconds,remaining):out.mkdir();return SimpleNamespace(out=out,steps=[],seconds=seconds,remaining=remaining)
                def own_incumbent(*args,**kwargs):
                    basis=args[1];basis.mkdir();candidate=basis/'candidate'/board.name
                    ps.shutil.copytree(source,candidate.parent)
                    result={'steps':[],'accepted':True,'status':'routing_accepted','candidate':str(candidate),
                        'metrics':{'track_length_mm':9.,'vias':0},'native':{'findings':[]},'source_drc':{'findings':[]},'task_sha256':'pure-task'}
                    p.save_json(basis/'result.json',result);p.save_json(basis/'floor-policy.json',{'pure':'guidance'})
                    clock.update(wall=60.,cpu=70. if allocation==ps.LEGACY_ALLOCATION else 85.);return result
                def validation(trial,actual_original,candidate,hashes,protected,**kwargs):
                    reached.append((trial,candidate,kwargs));expected_cap=12. if allocation==ps.LEGACY_ALLOCATION else 10.
                    self.assertEqual(trial.seconds,expected_cap);self.assertEqual(trial.remaining(),expected_cap)
                    self.assertEqual(actual_original,original);self.assertEqual(protected,[]);self.assertEqual(kwargs['guidance_basis'],trial.out.parent.parent/'incumbent')
                    self.assertTrue(candidate.exists());self.assertLess(len(p.routes(sx.read(candidate))),len(p.routes(original)))
                    # Deliberate partial failure/overshoot prevents another attempt
                    # and accepted final publication. Failed compute remains in trial.json.
                    clock.update(wall=99.,cpu=109.);raise p.Rejected('deliberate pure first-attempt callback rejection')
                with ExitStack() as stack:
                    replacements=[(f,'FloorJob',job),(p,'check_storage',lambda:None),(p,'preflight',lambda _:copy.deepcopy(original)),
                        (ps.pc,'narrow_source',lambda _:None),(p,'tool_manifest',lambda:{'implementation_sha256':{}}),
                        (f,'route',own_incumbent),(p,'check_result',lambda *_:{'current':True}),
                        (p,'validate_candidate',validation),(ps.time,'monotonic',lambda:clock['wall']),
                        (ps.time,'process_time',lambda:clock['cpu']),(f,'child_cpu',lambda:0.)]
                    for target,name,value in replacements:stack.enter_context(patch.object(target,name,value))
                    out=self.folder/(allocation+'-attempt');result=ps.prune(board,out,120,allocation=allocation)
                self.assertEqual(len(reached),1,result.get('reason'));self.assertFalse(result['accepted']);self.assertEqual(len(result['trials']),1)
                row=result['trials'][0];self.assertFalse(row['completed']);self.assertFalse(row['accepted']);self.assertIn('deliberate pure first-attempt callback rejection',row['error'])
                self.assertEqual(row['total_cpu_seconds'],39. if allocation==ps.LEGACY_ALLOCATION else 24.);self.assertEqual(result['total_cpu_seconds'],109.)
                self.assertNotIn('UnboundLocalError',result.get('reason',''));self.assertIn('final native reserve exhausted',result['reason'])
                self.assertEqual(json.loads((out/'trials/0000/trial.json').read_text()),row)
                self.assertEqual(row['proposal']['kind'],'whole_zone_net' if allocation==ps.LEGACY_ALLOCATION else 'individual_segment')
    def test_shared_quality_summary_requires_exact_declared_new_variant(self):
        row,inc=self.receipt(ps.STANDARD_ALLOCATION);(self.out/'incumbent').mkdir();p.save_json(self.out/'incumbent/result.json',inc)
        row.update(accepted=True,status='routing_accepted',wall_seconds=1.,total_cpu_seconds=1.,incumbent_receipt_sha256=p.sha(self.out/'incumbent/result.json'))
        p.save_json(self.out/'result.json',row)
        arm={'id':'C_feedback','adapter':'both','engine_profile':'standard','operation':'placement_prune','input_policy':ps.POLICY,
            'strategy':ps.STRATEGY,'pruning_allocation':ps.STANDARD_ALLOCATION,'pruning_allocation_contract':ps.contract(ps.STANDARD_ALLOCATION)}
        with patch.object(p,'check_result',return_value={'current':True}):
            self.assertTrue(quality.summarize(arm,self.out,row,1.,1.)['accepted'])
            for changed in (dict(arm,engine_profile='tuned'),{k:v for k,v in arm.items() if k!='pruning_allocation'},dict(arm,pruning_allocation_contract=ps.contract())):
                with self.subTest(changed=changed):self.assertFalse(quality.summarize(changed,self.out,row,1.,1.)['accepted'])
            row['incumbent_assignment_observation']['elapsed_full_cpu_seconds']=31.;p.save_json(self.out/'result.json',row)
            self.assertFalse(quality.summarize(arm,self.out,row,1.,1.)['accepted'])
    def test_failed_native_trial_process_cost_is_still_retained(self):
        candidate=self.out/'candidate/board.kicad_pcb'
        process={'name':'refill-drc','cwd':str(self.out),'argv':[*f.SANDBOX,str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(self.out/'refill-drc.json'),'--save-board',str(self.out/'refill/board.kicad_pcb')],
            'status':'timeout','exit_code':None,'cleanup_complete':True,'wall_seconds':12.1,'cpu_seconds':11.8,'monitor_cpu_seconds':.1}
        p.save_json(self.out/'refill-drc-process.json',process)
        row={'candidate':str(candidate),'assigned_seconds':12.,'completed':False,'wall_seconds':12.2,'total_cpu_seconds':12.,'steps':[process]}
        self.assertEqual(ps.trial_process_history(self.out,row),row['steps'])
        for changed in (dict(row,steps=[]),dict(row,total_cpu_seconds=0),dict(row,completed=True)):
            with self.subTest(changed=changed),self.assertRaises(p.Rejected):ps.trial_process_history(self.out,changed)


class PairedAllocationControls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'.runs').mkdir();(self.root/'source').mkdir();self.board=self.root/'source/board.kicad_pcb';self.board.write_text('pure original')
        self.script=self.root/'wrapper.py';self.script.write_text('pure frozen wrapper');self.wall=0.;self.cpu=0.;self.calls=[];self.c_cost=20.
        self.out=self.root/'.runs/pair';self.stack=ExitStack();self.addCleanup(self.stack.close)
        def freeze(_):self.wall+=10.;self.cpu+=8.;return {'tools':{'git_head':'synthetic'},'source_hashes':{},'files_sha256':{}}
        @contextmanager
        def session():
            self.wall+=1.;self.cpu+=1.
            try:yield
            finally:self.wall+=2.;self.cpu+=2.
        def route(*args,**kwargs):
            self.calls.append(('route',args,kwargs));self.wall+=20.;self.cpu+=20.
            return {'tools':{'git_head':'synthetic'},'source_hashes':{},'accepted':True,'status':'routing_accepted','steps':[]}
        def prune(*args,**kwargs):
            self.calls.append(('prune',args,kwargs));self.wall+=self.c_cost;self.cpu+=self.c_cost
            return {'tools':{'git_head':'synthetic'},'source_hashes':{},'accepted':True,'status':'routing_accepted','steps':[]}
        def portfolio(directory,project,**kwargs):
            self.calls.append(('portfolio',(directory,project),kwargs));self.wall+=20.;self.cpu+=20.
            return {'id':'B2_portfolio','accepted':True,'status':'completed','guidance_policy':f.SEARCH_POLICY,
                    'wall_budget_seconds':kwargs['budget'],'cpu_budget_seconds':kwargs['budget'],
                    'trials':[{'id':'via_default','guidance_policy':f.SEARCH_POLICY,'vias':2,'length_mm':100.}],
                    'pareto_frontier':['via_default'],'selected':{'id':'via_default'}}
        replacements=[(paired.c,'ROOT',self.root),(paired,'SCRIPT',self.script),(paired.time,'monotonic',lambda:self.wall),
            (paired.q,'total_process_cpu',lambda:self.cpu),(paired.q,'selected_source',lambda _:(self.board,'synthetic')),
            (paired.portfolio,'freeze',freeze),(paired.q,'verify_freeze',lambda *_:None),
            (paired.subprocess,'run',lambda *_args,**_kwargs:SimpleNamespace(stdout=self.script.read_bytes())),
            (paired.p,'validation_readback_session',session),(paired.p,'route',route),(paired.f,'route',route),(paired.ps,'prune',prune),
            (paired.ps.pc,'inventory',lambda *_args,**_kwargs:{}),(paired.portfolio,'experiment',portfolio),
            (paired,'verify_portfolio',lambda directory,result,*_:result),
            (paired.q,'summarize',lambda arm,*_:dict(arm,accepted=True,status='routing_accepted',vias=2,length_mm=100.)),
            (paired.q,'observations',lambda *_:[{'final_delivery_accepted':True}])]
        for target,name,value in replacements:self.stack.enter_context(patch.object(target,name,value))
    def test_explicit_standard_system_freezes_and_invokes_fresh_own_allocation(self):
        result=paired.experiment(self.out,project_name='multichannel',system='placement-standard')
        protocol=json.loads((self.out/'protocol.json').read_text());self.assertEqual(protocol['arm_order'],['B0','B1','B2_portfolio','C_feedback'])
        self.assertEqual(protocol['pruning_allocation'],ps.STANDARD_ALLOCATION);self.assertEqual(protocol['system_contract']['pruning_allocation_contract'],ps.contract(ps.STANDARD_ALLOCATION))
        self.assertEqual(protocol['system_contract']['engine_profile'],'standard');self.assertEqual(protocol['wall_budget_per_arm_seconds'],120.);self.assertEqual(protocol['cpu_budget_per_arm_seconds'],120.)
        self.assertEqual([x[0] for x in self.calls],['route','route','portfolio','prune'])
        call=self.calls[-1];self.assertEqual(call[1],(self.board,self.out/'C_feedback',104.));self.assertEqual(call[2],{'allocation':ps.STANDARD_ALLOCATION})
        self.assertEqual(result['shared_overhead_wall_seconds'],13.);self.assertEqual(result['shared_overhead_cpu_seconds'],11.)
        self.assertTrue(all(row['accepted'] for row in result['results']));self.assertTrue(all(row['charged_cpu_seconds']==31. for row in result['results']))
    def test_new_allocation_does_not_escape_shared_delivery_caps(self):
        self.c_cost=108.;result=paired.experiment(self.out,project_name='multichannel',system='placement-standard')
        row=result['results'][-1];self.assertTrue(row['accepted_before_shared_charge']);self.assertEqual(row['charged_wall_seconds'],121.)
        self.assertEqual(row['charged_cpu_seconds'],119.);self.assertFalse(row['accepted']);self.assertFalse(row['observations'][0]['final_delivery_accepted'])
        self.assertEqual(result['comparisons'],[])
    def test_legacy_placement_system_keeps_undeclared_default_tuned_call(self):
        paired.experiment(self.out,project_name='multichannel',system='placement')
        protocol=json.loads((self.out/'protocol.json').read_text());self.assertNotIn('pruning_allocation',protocol)
        self.assertNotIn('pruning_allocation',protocol['system_contract']);self.assertEqual(protocol['system_contract']['engine_profile'],'tuned')
        self.assertEqual(self.calls[-1][2],{})

if __name__=='__main__':unittest.main()
