"""Pure wrapper controls. Mocked stages never establish native routing validity."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE))
import diagnostic_route as d
import experiment_search as pair
FIXTURE=d.ROOT/'evidence/placement-area-native-001/allowed_placement/candidate'

def clean():return dict(opens=0,blocking=0,warnings=0,exclusions=0,ignored_checks=[],findings=[])

class ScopeTests(unittest.TestCase):
    def setUp(self):self.source=d.sx.read(FIXTURE/'fixture.kicad_pcb')
    def test_owned_allowed_fixture_only(self):
        self.assertEqual(len(d.narrow_source(self.source)),1)
        self.assertEqual(d.observer.AREA_LIMITS['footprints'],512)
        self.assertEqual(d.observer.LIMITS,d.f.LIMITS)
    def test_every_genuine_flag_rejected_even_if_native_would_miss(self):
        for flag in d.placement.FLAGS:
            source=copy.deepcopy(self.source);d.sx.one(d.sx.one(d.sx.children(source,'zone')[0],'keepout'),flag)[1]='not_allowed'
            with self.subTest(flag=flag),self.assertRaises((ValueError,d.p.Rejected)):d.narrow_source(source)
    def test_disabled_or_missing_flag_rejected(self):
        source=copy.deepcopy(self.source);d.sx.one(d.sx.one(d.sx.children(source,'zone')[0],'placement'),'enabled')[1]='no'
        with self.assertRaises((ValueError,d.p.Rejected)):d.narrow_source(source)
        source=copy.deepcopy(self.source);d.sx.one(d.sx.children(source,'zone')[0],'keepout').pop()
        with self.assertRaises((ValueError,d.p.Rejected)):d.narrow_source(source)
    def test_legacy_module_alias_rejected(self):
        self.source.append(['module','"legacy"'])
        with self.assertRaisesRegex(d.p.Rejected,'legacy'):d.narrow_source(self.source)
    def test_no_area_and_protected_routing_rejected(self):
        source=[n for n in self.source if not isinstance(n,list) or not n or n[0]!='zone']
        with self.assertRaises(d.p.Rejected):d.narrow_source(source)
        d.sx.children(self.source,'segment')[0].append(['locked','yes'])
        with self.assertRaises(ValueError):d.g.task_from_source(self.source)
    def test_owned_path_refuses_symlink_and_parent_escape(self):
        with tempfile.TemporaryDirectory(dir=HERE) as name:
            root=Path(name);(root/'link').symlink_to(FIXTURE,target_is_directory=True)
            for bad in (root/'link/fixture.kicad_pcb',root/'../escape'):
                with self.assertRaises(d.p.Rejected):d.owned(bad)
    def test_observer_cap_preserves_prior_bound_and_explicitly_allows114(self):
        pcb=SimpleNamespace(PLACEMENT_SOURCE_T_SHEETNAME=0,PLACEMENT_SOURCE_T_COMPONENT_CLASS=1,PLACEMENT_SOURCE_T_GROUP_PLACEMENT=2,PLACEMENT_SOURCE_T_DESIGN_BLOCK=3)
        def board(count):return SimpleNamespace(Zones=lambda:[],GetFootprints=lambda:[SimpleNamespace(Zones=lambda:[]) for _ in range(count)])
        self.assertEqual(d.observer.observe_areas(board(114),pcb)['footprint_zone_count'],0)
        with self.assertRaisesRegex(ValueError,'footprint'):d.observer.observe_areas(board(513),pcb)
        with self.assertRaises(ValueError):d.observer.native_bool(1)
    def test_reviewed_transform_pin(self):self.assertEqual(d.p.sha(HERE/'placement_transform.py'),d.TRANSFORM_SHA)

class ObserverExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.root=Path(self.tmp.name);self.input=self.root/'input';self.input.mkdir()
        self.board=self.input/'fixture.kicad_pcb';self.board.write_text('owned mock native source');self.board.with_suffix('.kicad_pro').write_text('{}')
        self.dsn=self.root/'native.dsn';self.output=self.root/'floor.json';self.areas=self.root/'areas.json'
        settings=SimpleNamespace(**{value:300000 for value in d.observer.FLOORS.values()})
        self.native=SimpleNamespace(GetCopperLayerCount=lambda:2,SynchronizeNetsAndNetClasses=lambda _:None,Zones=lambda:[],GetFootprints=lambda:[],GetPads=lambda:[],GetNetsByName=lambda:{},GetTracks=lambda:[],GetDrawings=lambda:[],GetDesignSettings=lambda:settings)
    def tearDown(self):self.tmp.cleanup()
    def collect(self,export):
        pcb=SimpleNamespace(PLACEMENT_SOURCE_T_SHEETNAME=0,PLACEMENT_SOURCE_T_COMPONENT_CLASS=1,PLACEMENT_SOURCE_T_GROUP_PLACEMENT=2,PLACEMENT_SOURCE_T_DESIGN_BLOCK=3,GetBuildVersion=lambda:'10.0.0',LoadBoard=lambda _:self.native,ExportSpecctraDSN=export)
        with patch.dict(sys.modules,{'pcbnew':pcb}):d.observer.collect(str(self.board),str(self.output),str(self.areas),str(self.dsn))
    def test_actual_empty_export_refused_before_context_publication(self):
        def export(*_):self.dsn.write_bytes(b'');return True
        with self.assertRaisesRegex(ValueError,'bounded native DSN'):self.collect(export)
        self.assertFalse(self.output.exists());self.assertFalse(self.areas.exists())
    def test_actual_symlink_export_refused_before_context_publication(self):
        def export(*_):self.dsn.symlink_to(self.board);return True
        with self.assertRaisesRegex(ValueError,'bounded native DSN'):self.collect(export)
        self.assertFalse(self.output.exists());self.assertFalse(self.areas.exists())
    def test_oversize_export_stat_refused_without_large_allocation(self):
        import os
        original=Path.stat
        def stat(path,*args,**kwargs):
            value=original(path,*args,**kwargs)
            if path==self.dsn:
                fields=list(value);fields[6]=20*1024*1024+1;return os.stat_result(fields)
            return value
        def export(*_):self.dsn.write_bytes(b'x');return True
        with patch.object(Path,'stat',stat),self.assertRaisesRegex(ValueError,'bounded native DSN'):self.collect(export)
        self.assertFalse(self.output.exists());self.assertEqual(self.dsn.read_bytes(),b'x')
    def test_one_loaded_board_and_export_feed_both_bound_contexts(self):
        calls=[]
        def export(native,*_):calls.append(native);self.dsn.write_bytes(b'owned mock DSN');return True
        self.collect(export);self.assertEqual(calls,[self.native])
        floor=d.f.read_json(self.output);areas=d.f.read_json(self.areas)
        for key in ('source','board_sha256','project_sha256','input_hashes_before','input_hashes_after','dsn_sha256'):
            self.assertEqual(floor[key],areas[key])

class DerivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.out=Path(self.tmp.name);self.source=d.sx.read(FIXTURE/'fixture.kicad_pcb');self.task=d.g.task_from_source(self.source)
        for name in ('snapshot','floor-export-input'):(self.out/name).mkdir()
        original=(d.sx.dump(self.source)+'\n').encode();task=(d.sx.dump(self.task)+'\n').encode();project=(FIXTURE/'fixture.kicad_pro').read_bytes()
        for name,board in [('snapshot',original),('floor-export-input',task)]:
            (self.out/name/'fixture.kicad_pcb').write_bytes(board);(self.out/name/'fixture.kicad_pro').write_bytes(project)
        self.hashes=d.p.tree_hash(self.out/'snapshot');expected=d.p.tree_hash(self.out/'floor-export-input');board=self.out/'floor-export-input/fixture.kicad_pcb'
        d.p.save_json(self.out/'route-meta.json',{'board_name':board.name,'policy':d.POLICIES[0]})
        for name,value in [('native.dsn',b'raw'),('floor-guided.dsn',b'guided'),('placement-guided.dsn',b'placed'),('pre-adapter.dsn',b'planned'),('task.dsn',b'adapted')]: (self.out/name).write_bytes(value)
        d.p.save_json(self.out/'floor-policy.json',{'contract':'frozen'})
        d.p.save_json(self.out/'placement-transform.json',{'removed_count':2})
        d.p.save_json(self.out/'search-guidance.json',{'planning':'bound'})
        native=dict(source=str(board),board_sha256=expected[board.name],project_sha256=expected['fixture.kicad_pro'],input_hashes_before=expected,input_hashes_after=expected,mode='export',dsn_sha256=d.g.sha(b'raw'),limits=d.f.LIMITS,board_saved=False,routes=[],obstacles=[])
        d.p.save_json(self.out/'floor-export-context.json',native)
        d.p.save_json(self.out/'area-context.json',dict(source=str(board),limits=d.observer.AREA_LIMITS,adapter_transformation_performed=False,routing_accepted=False))
        self.patches=[patch.object(d.placement,'native_binding',return_value=None),patch.object(d.f,'policy_contract',return_value=(b'guided',{'contract':'frozen'})),patch.object(d.g,'adapter_bytes',return_value=b'adapted'),patch.object(d.placement,'transform',return_value=(b'placed',{'removed_count':2})),patch.object(d.g,'qualify',return_value={}),patch.object(d.search,'transform',return_value=(b'planned',{'planning':'bound'}))]
        for x in self.patches:x.start()
    def tearDown(self):
        for x in reversed(self.patches):x.stop()
        self.tmp.cleanup()
    def call(self):return d.derive(self.out,self.hashes,d.POLICIES[0])
    def test_complete_wrapper_chain_checks(self):self.assertEqual(self.call()[2]['placement_removed_count'],2)
    def test_original_project_tamper_rejected(self):
        (self.out/'snapshot/fixture.kicad_pro').write_text('{}')
        with self.assertRaises(d.p.Rejected):self.call()
    def test_export_task_change_rejected(self):
        (self.out/'floor-export-input/fixture.kicad_pcb').write_text('(kicad_pcb)')
        with self.assertRaises(d.p.Rejected):self.call()
    def test_raw_context_binding_rejected(self):
        (self.out/'native.dsn').write_bytes(b'other')
        with self.assertRaises(d.p.Rejected):self.call()
    def test_each_engine_input_stage_change_rejected(self):
        for name,value in [('floor-guided.dsn',b'guided'),('placement-guided.dsn',b'placed'),('pre-adapter.dsn',b'planned'),('task.dsn',b'adapted')]:
            with self.subTest(name=name):
                (self.out/name).write_bytes(b'changed')
                with self.assertRaises(d.p.Rejected):self.call()
                (self.out/name).write_bytes(value)
    def test_changed_removal_receipt_is_rejected(self):
        d.p.save_json(self.out/'placement-transform.json',{})
        with self.assertRaises(d.p.Rejected):self.call()

class AccountingTests(unittest.TestCase):
    def value(self):return dict(native=clean(),budget_seconds=60,cpu_budget_seconds=60,wall_seconds=5,total_cpu_seconds=4,parent_cpu_seconds=1,waited_child_cpu_seconds=3,steps=[dict(cpu_seconds=2,monitor_cpu_seconds=1)],routing_accepted=True,status='diagnostic_accepted')
    def test_finite_sum_and_measured_monitor_cpu(self):self.assertTrue(d.audit_accounting(self.value()))
    def test_invalid_numbers_caps_and_underreported_cpu_reject(self):
        for changed in [dict(wall_seconds=True),dict(total_cpu_seconds=float('nan')),dict(cpu_budget_seconds=61),dict(total_cpu_seconds=3),dict(parent_cpu_seconds=2,waited_child_cpu_seconds=2),dict(wall_seconds=61),dict(total_cpu_seconds=61,parent_cpu_seconds=58)]:
            value=self.value();value.update(changed)
            with self.subTest(changed=changed),self.assertRaises(d.p.Rejected):d.audit_accounting(value)
    def test_negative_or_boolean_process_cpu_rejects(self):
        for bad in (-1,True,None):
            value=self.value();value['steps'][0]['cpu_seconds']=bad
            with self.assertRaises(d.p.Rejected):d.audit_accounting(value)
    def test_true_native_failure_never_accepted(self):
        value=self.value();value['native']['opens']=1
        with self.assertRaises(d.p.Rejected):d.audit_accounting(value)
        value.update(routing_accepted=False,status='drc_rejected');self.assertFalse(d.audit_accounting(value))

class PublicationTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.out=Path(self.tmp.name);self.value={'native':clean(),'status':'diagnostic_accepted','routing_accepted':True,'production_qualified':False}
    def tearDown(self):self.tmp.cleanup()
    def run_publish(self,stable=lambda:None,remaining=lambda:10,checker=lambda _:None):return d.publish_result(self.out,self.value,stable,lambda:None,remaining,checker)
    def rejected(self):
        path=self.out/'result.json'
        if path.exists():self.assertFalse(d.f.read_json(path)['routing_accepted'])
    def test_cancel_after_positive_write_failed_correction_no_canonical(self):
        calls=[];real=d.p.save_json
        def save(path,value):
            calls.append(1)
            if len(calls)>1:raise OSError('correction failed')
            real(path,value)
        def check(_):raise KeyboardInterrupt
        with patch.object(d.p,'save_json',save):self.run_publish(checker=check)
        self.assertFalse((self.out/'result.json').exists());self.assertTrue(list(self.out.glob('invalidated-result-*')))
    def test_partial_interrupt_retains_evidence(self):
        calls=[];real=d.p.save_json
        def save(path,value):
            calls.append(1)
            if len(calls)==1:path.with_suffix('.json.partial').write_text('{');raise KeyboardInterrupt
            real(path,value)
        with patch.object(d.p,'save_json',save):self.run_publish()
        self.rejected();self.assertTrue(list(self.out.glob('invalidated-result-*partial')))
    def test_receipt_mutated_during_checker_rejected(self):
        def check(path):value=d.f.read_json(path);value['added']=True;d.p.save_json(path,value)
        self.run_publish(checker=check);self.rejected()
    def test_stale_artifacts_or_budget_after_publication_rejected(self):
        def check(_):raise d.p.Rejected('bound evidence changed')
        self.run_publish(checker=check);self.rejected()
        self.run_publish(remaining=lambda:0);self.rejected()

class FixtureGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.root=Path(self.tmp.name);self.path=self.root/'result.json';self.frozen={'tools':{},'files_sha256':{}}
        self.value={'source':str(FIXTURE/'fixture.kicad_pcb'),'source_hashes':d.f.read_json(HERE/'protocol.json')['qualification_fixture']['source_hashes'],'tools':{},'freeze':{'files_sha256':{}},'policy':d.POLICIES[2],'native':clean(),'metrics':{'vias':1}}
    def tearDown(self):self.tmp.cleanup()
    def call(self):
        d.p.save_json(self.path,self.value)
        with patch.object(d,'check_result',return_value={'routing_accepted':True}):return pair.fixture_gate(self.path,self.frozen)
    def test_exact_owned_fixture_gate(self):self.assertEqual(self.call(),d.p.tree_hash(self.root))
    def test_same_project_different_board_or_extra_input_is_not_fixture(self):
        for key in ('fixture.kicad_pcb','added.json'):
            old=copy.deepcopy(self.value);self.value['source_hashes'][key]='0'*64
            with self.assertRaises(d.p.Rejected):self.call()
            self.value=old
    def test_reference_policy_or_changed_code_not_qualification(self):
        self.value['policy']=d.POLICIES[0]
        with self.assertRaises(d.p.Rejected):self.call()
        self.value['policy']=d.POLICIES[2];self.value['freeze']['files_sha256']={'other':'f'*64}
        with self.assertRaises(d.p.Rejected):self.call()

class PairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.base=Path(self.tmp.name);self.source=self.base/'source';self.source.mkdir();self.board=self.source/'board.kicad_pcb';self.board.write_text('owned stub source')
        self.fixture=self.base/'fixture';self.fixture.mkdir();self.qualified=self.base/'qualification-source';self.qualified.mkdir();(self.qualified/'fixture.kicad_pcb').write_text('owned qualification source');d.p.save_json(self.fixture/'result.json',{'source':str(self.qualified/'fixture.kicad_pcb'),'source_hashes':d.p.tree_hash(self.qualified)})
        self.code=self.base/'helper.py';self.code.write_text('pass\n');self.out=d.ROOT/'.runs'/('placement-pure-'+self.base.name)
        self.frozen={'tools':{},'files_sha256':{str(self.code.relative_to(d.ROOT)):d.p.sha(self.code)}}
        self.patches=[patch.object(d.p,'check_storage'),patch.object(pair,'selected_source',return_value=(self.board,{'family':'synthetic'})),patch.object(d.p,'preflight',return_value=[]),patch.object(d,'narrow_source'),patch.object(d,'freeze',return_value=self.frozen),patch.object(d,'verify_freeze'),patch.object(pair,'fixture_gate',return_value=d.p.tree_hash(self.fixture)),patch.object(d,'check_result',return_value={'diagnostic_verified':True,'routing_accepted':True}),patch.object(d,'route',side_effect=self.route)]
        for x in self.patches:x.start()
    def tearDown(self):
        for x in reversed(self.patches):x.stop()
        import shutil
        if self.out.exists():shutil.rmtree(self.out)
        self.tmp.cleanup()
    def route(self,source,out,assigned,policy):
        out.mkdir();(out/'native.dsn').write_text('(pcb "display" (parser (string_quote ")) (structure))')
        value=dict(status='diagnostic_accepted',tools={},source_hashes=d.p.tree_hash(self.source),budget_seconds=assigned,policy=policy,native=clean(),metrics={'track_length_mm':1,'vias':1},peak_child_rss_bytes=0,chain={})
        d.p.save_json(out/'result.json',value);return value
    def run_pair(self):return pair.experiment(self.out,self.fixture/'result.json')
    def test_shared_overhead_all_three_arms_and_identical_assignment(self):
        value=self.run_pair();self.assertTrue(value['comparison_eligible']);self.assertTrue(all(x['accepted'] for x in value['results']))
        for x in value['results']:
            self.assertAlmostEqual(x['charged_wall_seconds'],x['invocation_wall_seconds']+value['shared_wall_seconds']);self.assertAlmostEqual(x['charged_cpu_seconds'],x['invocation_cpu_seconds']+value['shared_cpu_seconds'])
        self.assertEqual(len(value['results']),3)
        self.assertEqual(len({d.f.read_json(self.out/('arm-'+str(i))/'result.json')['budget_seconds'] for i in range(3)}),1)
    def test_completed_inventory_not_replaced_after_real_file_mutation(self):
        original=d.p.tree_hash;calls=[];before={}
        def tree(path):
            if Path(path)==self.out/'arm-0':
                calls.append(1)
                if len(calls)==1:
                    value=original(path);before.update(value);return value
                if len(calls)==2:(Path(path)/'native.dsn').write_text('tampered after initial completed inventory')
            return original(path)
        with patch.object(d.p,'tree_hash',side_effect=tree):value=self.run_pair()
        self.assertEqual(value['status'],'invalidated');self.assertFalse(value['comparison_eligible'])
        self.assertEqual(value['completed_trees'][str(self.out/'arm-0')],before)
        self.assertNotEqual(value['completed_trees'][str(self.out/'arm-0')]['native.dsn'],d.p.sha(self.out/'arm-0/native.dsn'))
    def test_final_artifact_staleness_invalidates_comparison(self):
        calls=[]
        def check(path):
            calls.append(1)
            if len(calls)==4:(self.out/'arm-0/native.dsn').write_text('stale')
            return {'diagnostic_verified':True,'routing_accepted':True}
        with patch.object(d,'check_result',side_effect=check):value=self.run_pair()
        self.assertFalse(value['comparison_eligible']);self.assertTrue(all(not x['accepted']for x in value['results']))
    def test_external_qualification_source_tamper_invalidates_pair(self):
        calls=[]
        def check(path):
            calls.append(1)
            if len(calls)==4:(self.qualified/'fixture.kicad_pcb').write_text('changed after fixture gate')
            return {'diagnostic_verified':True,'routing_accepted':True}
        with patch.object(d,'check_result',side_effect=check):value=self.run_pair()
        self.assertFalse(value['comparison_eligible']);self.assertTrue(all(not x['accepted'] for x in value['results']))
    def test_summary_mutation_during_final_check_rejects(self):
        calls=[]
        def check(path):
            calls.append(1)
            if len(calls)==4:
                s=self.out/'summary.json';v=d.f.read_json(s);v['added']=True;d.p.save_json(s,v)
            return {'diagnostic_verified':True,'routing_accepted':True}
        with patch.object(d,'check_result',side_effect=check):value=self.run_pair()
        self.assertFalse(value['comparison_eligible'])
    def test_cancel_after_summary_failed_correction_no_positive_canonical(self):
        real=d.p.save_json;calls=[]
        def save(path,value):
            if path.name=='summary.json':
                calls.append(1)
                if len(calls)>1:raise OSError('correction failed')
                real(path,value);raise KeyboardInterrupt
            real(path,value)
        with patch.object(d.p,'save_json',save):value=self.run_pair()
        self.assertFalse(value['comparison_eligible']);self.assertFalse((self.out/'summary.json').exists());self.assertTrue(list(self.out.glob('invalidated-*summary.json')))
    def test_postpublication_cpu_cap_rejects(self):
        real=d.p.save_json;elapsed=[0]
        def save(path,value):
            real(path,value)
            if path.name=='summary.json' and value['status']=='completed':elapsed[0]=200
        with patch.object(d,'cpu',side_effect=lambda:elapsed[0]),patch.object(d.p,'save_json',save):value=self.run_pair()
        self.assertFalse(value['comparison_eligible']);self.assertTrue(all(not x['accepted'] for x in value['results']))
    def test_invalid_baseline_never_gets_quality_delta(self):
        rows=[dict(diagnostic_verified=True,accepted=False,opens=1,blocking=0,warnings=0,exclusions=0),dict(diagnostic_verified=True,accepted=True,opens=0,blocking=0,warnings=0,exclusions=0,length_mm=1,vias=0)]
        for index,row in enumerate(rows):row['policy']=d.POLICIES[index]
        value=pair.compare_pair(*rows);self.assertEqual(value['completion_difference'],1);self.assertNotIn('length_delta_mm',value)

if __name__=='__main__':unittest.main()
