"""Pure guards only: fabricated native contexts are not native qualification."""
import copy,hashlib,json,shutil,subprocess,tempfile,unittest
from pathlib import Path
from unittest import mock
import driver as d

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def flow_case(OUT,name,observation='export'):
    base=OUT/name;base.mkdir(parents=True);(base/'.runs').mkdir();source=base/'source';source.mkdir()
    for path in (d.SOURCE,d.SOURCE.with_suffix('.kicad_pro')):shutil.copyfile(path,source/path.name)
    board=source/d.SOURCE.name;receipt=base/'acquisition.json';receipt.write_text('{"mocked_scope":true}')
    helper=base/'helper.py';helper.write_text('# tiny frozen helper\n')
    hashes=d.inventory(source);total=sum(p.stat().st_size for p in source.iterdir());out=base/'.runs/out'
    tool=base/'synthetic-tool';tool.write_bytes(b'not executable')
    tools={'git_head':'synthetic-controlled-commit','implementation_sha256':{},'files':{str(tool):digest(tool)}}
    mutation={};calls=[]
    def snapshot(out,tools,remaining):
        (out/'code').mkdir();shutil.copy2(helper,out/'code/helper.py');return {'helper.py':digest(helper)}
    def tool_manifest():
        if name in ('late_source','late_helper','late_tool') and (out/'summary.json').exists() and not mutation:
            target={'late_source':board,'late_helper':helper,'late_tool':tool}[name]
            mutation.update(path=str(target),before=digest(target));target.write_bytes(target.read_bytes()+b'\n; late change\n');mutation['after']=digest(target)
        return copy.deepcopy(tools)
    original_read=d.read
    def read(path):
        raw=original_read(path)
        if name=='parsed_observation' and Path(path)==out/'observation.json' and not mutation:
            changed=copy.deepcopy(raw);changed['floors_nm']['min_clearance']=999999
            mutation.update(path=str(path),before=digest(path));d.p.save_json(path,changed);mutation['after']=digest(path)
        return raw
    original_binding=d.drc_binding;original_parser=d.p.parse_report
    def change_report(path):
        raw=original_read(path);raw['date']='changed-after-validation'
        mutation.update(path=str(path),before=digest(path));d.p.save_json(path,raw);mutation['after']=digest(path)
    def binding(*args):
        result=original_binding(*args)
        if name=='captured_drc_binding' and not mutation:change_report(out/'original-drc.json')
        if name=='captured_drc_binding_file' and not mutation:
            path=out/'original-drc-binding.json';raw=original_read(path);raw['untrusted_note']='changed'
            mutation.update(path=str(path),before=digest(path));d.p.save_json(path,raw);mutation['after']=digest(path)
        return result
    def parse_report(path,board_name):
        result=original_parser(path,board_name)
        if name=='parsed_drc' and not mutation:change_report(Path(path))
        return result
    def run(argv,*,cwd,log,**kwargs):
        log=Path(log);log.write_text('synthetic native observation; no process executed\n');calls.append(argv)
        if log.stem=='observe':
            notes=d.source_notes(d.sx.read(board),d.read(board.with_suffix('.kicad_pro')))
            if observation=='export' or name=='unexpected_dsn':(out/'native.dsn').write_text('(pcb synthetic)')
            observed={'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','mode':d.observation_mode(observation),'source':str(out/'observe-input'/board.name),
                'board_sha256':hashes[board.name],'project_sha256':hashes[board.with_suffix('.kicad_pro').name],'dsn_sha256':digest(out/'native.dsn') if observation=='export' else None,
                'input_hashes_before':hashes,'input_hashes_after':hashes,'limits':d.f.LIMITS,'board_saved':False,'routing_accepted':False,
                'pads':notes['source_pads_identity'],'routes':[{'uuid':uid} for uid in notes['source_route_ids']],
                'nets':[{'name':name} for name in notes['source_nonempty_nets']],
                'floors_nm':{'min_track_width':100000,'min_clearance':100000,'min_via_diameter':400000,'min_through_hole_diameter':200000,'min_via_annular_width':100000}}
            d.p.save_json(out/'observation.json',observed)
        elif log.stem=='original-drc':
            native={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':board.name,'violations':[],'unconnected_items':[],
                'schematic_parity':[],'ignored_checks':[],'included_severities':['error','warning','exclusion']}
            d.p.save_json(out/'original-drc.json',native)
            if name=='late_dsn':(out/'native.dsn').write_text('(pcb unexpected)')
            if name=='rebased_observation':
                path=out/'observation.json';raw=d.read(path);mutation.update(path=str(path),before=digest(path));raw['floors_nm']['min_clearance']=999999
                d.p.save_json(path,raw);mutation['after']=digest(path)
        else:raise AssertionError('unexpected stage')
        return {'status':'success','exit_code':0,'argv':argv,'cwd':str(cwd),'log':str(log),'cleanup_complete':True,'cpu_seconds':0.0,'monitor_cpu_seconds':0.0}
    original_read=d.read
    def read_hook(path):
        value=original_read(path)
        if name=='capture_observation' and Path(path)==out/'observation.json' and not mutation:
            changed=copy.deepcopy(value);changed['floors_nm']['min_clearance']=999999
            mutation.update(path=str(path),before=digest(Path(path)));d.p.save_json(Path(path),changed);mutation['after']=digest(Path(path))
        return value
    with mock.patch.object(d,'read',side_effect=read_hook),mock.patch.object(d,'ROOT',base),mock.patch.object(d,'SOURCE',board),mock.patch.object(d,'RECEIPT',receipt),mock.patch.object(d,'RECEIPT_SHA',digest(receipt)),\
         mock.patch.object(d,'source_binding',return_value=(hashes,total)),mock.patch.object(d,'snapshot',side_effect=snapshot),mock.patch.object(d,'read',side_effect=read),mock.patch.object(d,'drc_binding',side_effect=binding),mock.patch.object(d.p,'parse_report',side_effect=parse_report),\
         mock.patch.object(d.p,'tool_manifest',side_effect=tool_manifest),mock.patch.object(d.p,'check_storage',return_value=0),mock.patch.object(d,'run',side_effect=run):
        result=d.experiment(out,run_native=True,observation=observation)
    saved=d.read(out/'summary.json');observed=d.read(out/'observation.json')
    return {'case':name,'observations_complete':saved['observations_complete'],'status':saved['status'],'error':saved.get('error'),
        'reported_observation_sha256':saved.get('observation_sha256'),'actual_observation_sha256':digest(out/'observation.json'),
        'reported_floor':saved.get('native_effective_floors_nm',{}).get('min_clearance'),'actual_floor':observed['floors_nm']['min_clearance'],
        'observation':saved['observation'],'native_observation_mode':saved['native_observation_mode'],'dsn_export_requested':saved['dsn_export_requested'],'dsn_export_succeeded':saved['dsn_export_succeeded'],'native_dsn_sha256':saved['native_dsn_sha256'],'stage_one_evidence':saved.get('stage_one_evidence'),'steps':saved['steps'],
        'reported_original_unchanged':saved.get('original_inputs_unchanged'),'actual_source_unchanged':d.inventory(source)==hashes,
        'mutation':mutation,'mock_native_stages':len(calls),'actual_native_processes':0,
        'expected_complete':name=='unchanged','expectation_satisfied':saved['observations_complete']==(name=='unchanged')}

class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes,cls.total=d.source_binding()
        cls.board=d.sx.read(d.SOURCE);cls.project=d.read(d.SOURCE.with_suffix('.kicad_pro'))
        cls.notes=d.source_notes(cls.board,cls.project)
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='pure-',dir=d.HERE)
        self.out=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def record(self):return {'status':'observations_complete','observations_complete':True,'routing_accepted':False}
    def context(self,observation='export'):
        board=self.out/'observe-input'/d.SOURCE.name
        if observation=='export':(self.out/'native.dsn').write_bytes(b'(pcb test)')
        raw={'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','mode':d.observation_mode(observation),'source':str(board),
             'board_sha256':d.BOARD_SHA,'project_sha256':d.PROJECT_SHA,'dsn_sha256':d.p.sha(self.out/'native.dsn') if observation=='export' else None,
             'input_hashes_before':self.hashes,'input_hashes_after':self.hashes,'limits':d.f.LIMITS,'board_saved':False,'routing_accepted':False,
             'pads':copy.deepcopy(self.notes['source_pads_identity']),
             'routes':[{'uuid':x} for x in self.notes['source_route_ids']],
             'nets':[{'name':x} for x in self.notes['source_nonempty_nets']]}
        return raw
    def put_context(self,raw):d.p.save_json(self.out/'observation.json',raw)
    def test_default_export_argv_preserved(self):
        expected=d.f.context_argv('export',self.out/'observe-input'/d.SOURCE.name,self.out/'observation.json',self.out/'native.dsn')
        self.assertEqual(d.observe_argv(self.out),expected)
        self.assertEqual(d.observe_argv(self.out,'export'),expected)
    def test_context_only_uses_exact_existing_final_argv(self):
        expected=d.f.context_argv('final',self.out/'observe-input'/d.SOURCE.name,self.out/'observation.json')
        self.assertEqual(d.observe_argv(self.out,'context-only'),expected)
        self.assertNotIn(str(self.out/'native.dsn'),expected)
    def test_context_only_whole_flow_mock_positive(self):
        row=flow_case(self.out,'unchanged','context-only')
        self.assertTrue(row['observations_complete']);self.assertTrue(row['actual_source_unchanged'])
        self.assertEqual((row['observation'],row['native_observation_mode']),('context-only','final'))
        self.assertIs(row['dsn_export_requested'],False);self.assertIs(row['dsn_export_succeeded'],False);self.assertIsNone(row['native_dsn_sha256'])
        self.assertEqual(set(row['stage_one_evidence']),{'observation.json','observe-process.json','observe.log'})
        self.assertEqual([s['name'] for s in row['steps']],['observe','original-drc'])
        self.assertNotIn('export',row['steps'][0]['argv']);self.assertNotIn('--save-board',row['steps'][1]['argv'])
    def test_context_only_no_dsn_identity_positive(self):
        raw=self.context('context-only');self.put_context(raw)
        self.assertEqual(d.observe_binding(self.out,self.hashes,self.notes,'context-only'),raw)
        self.assertFalse((self.out/'native.dsn').exists())
    def test_context_only_rejects_export_mode_even_without_dsn(self):
        raw=self.context('context-only');raw['mode']='export';self.put_context(raw)
        with self.assertRaises(d.p.Rejected):d.observe_binding(self.out,self.hashes,self.notes,'context-only')
    def test_context_only_rejects_reported_dsn_digest(self):
        raw=self.context('context-only');raw['dsn_sha256']='a'*64;self.put_context(raw)
        with self.assertRaises(d.p.Rejected):d.observe_binding(self.out,self.hashes,self.notes,'context-only')
    def test_context_only_rejects_unexpected_dsn_file_directory_dangling_link(self):
        raw=self.context('context-only');self.put_context(raw);path=self.out/'native.dsn'
        for kind in ('file','directory','dangling-link'):
            with self.subTest(kind=kind):
                if kind=='file':path.write_bytes(b'(pcb unexpected)')
                elif kind=='directory':path.mkdir()
                else:path.symlink_to(self.out/'absent')
                try:
                    with self.assertRaisesRegex(d.p.Rejected,'unexpected DSN'):d.observe_binding(self.out,self.hashes,self.notes,'context-only')
                finally:
                    if path.is_dir() and not path.is_symlink():path.rmdir()
                    else:path.unlink()
    def test_context_only_wrong_argv_rejected_before_native(self):
        job=object.__new__(d.ObservationJob);job.out=self.out;job.observation='context-only';job.remaining=lambda:30
        with mock.patch.object(d,'run') as worker:
            for argv in (d.observe_argv(self.out,'export'),d.observe_argv(self.out,'context-only')+[str(self.out/'native.dsn')]):
                with self.assertRaisesRegex(d.p.Rejected,'exact nonsaving'):job.step('observe',argv,already_sandboxed=True)
        worker.assert_not_called()
    def test_export_job_rejects_context_argv(self):
        job=object.__new__(d.ObservationJob);job.out=self.out;job.observation='export';job.remaining=lambda:30
        with mock.patch.object(d,'run') as worker:
            with self.assertRaisesRegex(d.p.Rejected,'exact nonsaving'):job.step('observe',d.observe_argv(self.out,'context-only'),already_sandboxed=True)
        worker.assert_not_called()
    def test_context_only_stage_output_unexpected_dsn_rejects(self):
        row=flow_case(self.out,'unexpected_dsn','context-only')
        self.assertFalse(row['observations_complete']);self.assertIn('unexpected DSN',row['error']);self.assertEqual(row['mock_native_stages'],1)
    def test_context_only_second_stage_dsn_rejects(self):
        row=flow_case(self.out,'late_dsn','context-only')
        self.assertFalse(row['observations_complete']);self.assertIn('unexpected DSN',row['error']);self.assertEqual(row['mock_native_stages'],2)
    def test_context_only_retains_both_stage_and_material_freezes(self):
        for name in ('parsed_observation','rebased_observation','parsed_drc','captured_drc_binding','captured_drc_binding_file','late_source','late_helper','late_tool'):
            with self.subTest(name=name):
                row=flow_case(self.out,name,'context-only');self.assertTrue(row['expectation_satisfied']);self.assertFalse(row['observations_complete'])
    def test_unknown_selection_rejects_before_output(self):
        path=self.out/'never-created'
        for value in ('final','context_only',None,True):
            with self.subTest(value=value):
                with self.assertRaisesRegex(d.p.Rejected,'unknown observation'):d.experiment(path,run_native=True,observation=value)
        self.assertFalse(path.exists())
    def test_cli_selector_and_default_preserve_lock_and_handlers(self):
        root=self.out/'root';(root/'.runs').mkdir(parents=True)
        for args,selected in (([],'export'),(['--observation','context-only'],'context-only')):
            with self.subTest(selected=selected),mock.patch.object(d,'ROOT',root),mock.patch.object(d,'experiment',return_value={'status':'observations_complete','observations_complete':True}) as experiment,mock.patch('builtins.print'):
                previous={sig:d.signal.getsignal(sig) for sig in (d.signal.SIGINT,d.signal.SIGTERM)}
                out=root/'.runs/run';self.assertEqual(d.main(['--output',str(out),'--run-native',*args]),0)
                experiment.assert_called_once_with(out,run_native=True,observation=selected)
                self.assertEqual({sig:d.signal.getsignal(sig) for sig in previous},previous)

    def test_whole_flow_mock_positive(self):
        row=flow_case(self.out,'unchanged');self.assertTrue(row['expectation_satisfied']);self.assertTrue(row['actual_source_unchanged'])
    def test_stage_one_cannot_rebase_changed_observation(self):
        row=flow_case(self.out,'rebased_observation');self.assertTrue(row['expectation_satisfied']);self.assertIn('stage-one',row['error'])
    def test_stage_one_freeze_precedes_observation_parse(self):
        row=flow_case(self.out,'parsed_observation');self.assertTrue(row['expectation_satisfied']);self.assertIn('stage-one',row['error'])
    def test_postmetadata_source_change_invalidates(self):
        row=flow_case(self.out,'late_source');self.assertTrue(row['expectation_satisfied']);self.assertFalse(row['actual_source_unchanged']);self.assertIsNone(row['reported_original_unchanged'])
    def test_postmetadata_helper_change_invalidates(self):
        row=flow_case(self.out,'late_helper');self.assertTrue(row['expectation_satisfied']);self.assertIn('core/helper',row['error'])
    def test_postmetadata_tool_change_invalidates(self):
        row=flow_case(self.out,'late_tool');self.assertTrue(row['expectation_satisfied']);self.assertIn('tool material',row['error'])
    def test_stage_two_freeze_precedes_drc_parse(self):
        row=flow_case(self.out,'parsed_drc');self.assertTrue(row['expectation_satisfied']);self.assertIn('stage-two',row['error'])
    def test_stage_two_report_cannot_rebase_after_binding(self):
        row=flow_case(self.out,'captured_drc_binding');self.assertTrue(row['expectation_satisfied']);self.assertIn('stage-two',row['error'])
    def test_drc_final_binding_must_equal_recorded_binding(self):
        row=flow_case(self.out,'captured_drc_binding_file');self.assertTrue(row['expectation_satisfied']);self.assertIn('recorded native binding',row['error'])
    def test_actual_source_and_gate_remain_unsupported(self):
        self.assertEqual((len(self.hashes),self.total),(26,4194990))
        with self.assertRaisesRegex(d.p.Rejected,'unqualified board format'):d.p.preflight(d.SOURCE)
        self.assertFalse(self.notes['dependency_complete']);self.assertFalse(self.notes['format_support_qualified'])
        self.assertEqual(len(self.notes['source_zone_intent_ast']),3)
        self.assertEqual(len(self.notes['source_route_ids']),8)
    def test_source_recipe_rejects_format_relabel(self):
        board=copy.deepcopy(self.board);d.sx.one(board,'version')[1]='20260101'
        with self.assertRaisesRegex(d.p.Rejected,'format'):d.source_notes(board,self.project)
    def test_source_receipt_hash_rechecked(self):
        with mock.patch.object(d,'RECEIPT_SHA','0'*64):
            with self.assertRaisesRegex(d.p.Rejected,'receipt changed'):d.source_binding()
    def test_source_census_no_route_removal(self):
        board=copy.deepcopy(self.board);board.remove(d.p.routes(board)[0])
        with self.assertRaisesRegex(d.p.Rejected,'census'):d.source_notes(board,self.project)
    def test_fabricated_identity_positive_only(self):
        raw=self.context();self.put_context(raw)
        self.assertEqual(d.observe_binding(self.out,self.hashes,self.notes),raw)
    def test_observation_pad_identity_mutation(self):
        raw=self.context();raw['pads'][0]['net']='wrong';self.put_context(raw)
        with self.assertRaisesRegex(d.p.Rejected,'terminal'):d.observe_binding(self.out,self.hashes,self.notes)
    def test_observation_duplicate_pad(self):
        raw=self.context();raw['pads'][1]=raw['pads'][0];self.put_context(raw)
        with self.assertRaisesRegex(d.p.Rejected,'terminal'):d.observe_binding(self.out,self.hashes,self.notes)
    def test_observation_route_loss(self):
        raw=self.context();raw['routes'].pop();self.put_context(raw)
        with self.assertRaisesRegex(d.p.Rejected,'route/net'):d.observe_binding(self.out,self.hashes,self.notes)
    def test_observation_mode_units_save_rules_and_dsn(self):
        for field,value in [('mode','final'),('units','mm'),('board_saved',True),('project_sha256','a'*64),('dsn_sha256','a'*64)]:
            with self.subTest(field=field):
                raw=self.context();raw[field]=value;self.put_context(raw)
                with self.assertRaises(d.p.Rejected):d.observe_binding(self.out,self.hashes,self.notes)
    def test_observation_input_inventory_mismatch(self):
        raw=self.context();raw['input_hashes_after']={};self.put_context(raw)
        with self.assertRaises(d.p.Rejected):d.observe_binding(self.out,self.hashes,self.notes)
    def test_path_symlink_and_reuse(self):
        link=self.out/'link';link.symlink_to(d.SOURCE)
        with self.assertRaises(d.p.Rejected):d.owned(link)
        with self.assertRaises(d.p.Rejected):d.owned(d.ROOT/'.runs',output=True)
        with self.assertRaises(d.p.Rejected):d.owned(d.ROOT.parent/'outside')
    def test_flag_required_before_output(self):
        with self.assertRaisesRegex(d.p.Rejected,'run-native'):d.experiment(self.out/'never-created')
        self.assertFalse((self.out/'never-created').exists())
    def test_two_copy_payload_reservation(self):
        with mock.patch.object(d,'size',return_value=0):d.reserve_copy(self.out,self.total,2)
        with mock.patch.object(d,'size',return_value=d.LIMIT-self.total):
            with self.assertRaisesRegex(d.p.Rejected,'20MiB'):d.reserve_copy(self.out,self.total,1)
    def test_snapshot_exact_committed_bytes(self):
        def git(argv,**kwargs):return subprocess.CompletedProcess(argv,0,(d.ROOT/argv[2].split(':',1)[1]).read_bytes(),b'')
        with mock.patch.object(d.subprocess,'run',side_effect=git):
            hashes=d.snapshot(self.out,{'git_head':'mock-head','implementation_sha256':{}})
        self.assertEqual(d.inventory(self.out/'code'),hashes)
    def test_snapshot_commit_difference_before_copy(self):
        with mock.patch.object(d.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'changed',b'')):
            with self.assertRaisesRegex(d.p.Rejected,'commit exact'):d.snapshot(self.out,{'git_head':'mock-head','implementation_sha256':{}})
        self.assertFalse((self.out/'code').exists())
    def test_snapshot_budget_before_git(self):
        with mock.patch.object(d.subprocess,'run') as command:
            with self.assertRaisesRegex(d.p.Rejected,'budget'):d.snapshot(self.out,{'git_head':'mock-head','implementation_sha256':{}},lambda:0)
        command.assert_not_called()
    def test_only_exact_native_argv(self):
        job=object.__new__(d.ObservationJob);job.out=self.out;job.observation='export';job.remaining=lambda:30
        with mock.patch.object(d,'run') as worker:
            for name,argv in [('engine',['java']),('observe',['evil']),('original-drc',d.drc_argv(self.out)+['--save-board'])]:
                with self.subTest(name=name):
                    with self.assertRaisesRegex(d.p.Rejected,'exact nonsaving'):job.step(name,argv,already_sandboxed=True)
        worker.assert_not_called()
    def test_exact_argv_budget_before_native(self):
        job=object.__new__(d.ObservationJob);job.out=self.out;job.observation='export';job.remaining=lambda:0
        with mock.patch.object(d,'run') as worker:
            with self.assertRaisesRegex(d.p.Rejected,'budget'):job.step('original-drc',d.drc_argv(self.out),already_sandboxed=True)
        worker.assert_not_called()
    def drc_fixture(self):
        target=self.out/'original-drc-input'/d.SOURCE.name;target.parent.mkdir()
        target.write_bytes(b'owned mocked board');target.with_suffix('.kicad_pro').write_bytes(b'{"original":true}')
        hashes=d.inventory(target.parent)
        report={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':d.SOURCE.name,
                'violations':[],'unconnected_items':[],'schematic_parity':[],'ignored_checks':[],
                'included_severities':['error','warning','exclusion']}
        d.p.save_json(self.out/'original-drc.json',report)
        d.p.save_json(self.out/'original-drc-binding.json',{'source':str(self.out/'observe-input'/d.SOURCE.name),'input':str(target),'saved':False,'before':hashes,'after':hashes})
        process={'argv':d.drc_argv(self.out),'cwd':str(self.out),'name':'original-drc','exit_code':0,'status':'success','cleanup_complete':True}
        d.p.save_json(self.out/'original-drc-process.json',process)
        return hashes,[process],d.p.parse_report(self.out/'original-drc.json',d.SOURCE.name)
    def test_drc_binding_positive_is_observation_only(self):
        hashes,steps,native=self.drc_fixture();receipt=d.drc_binding(self.out,steps,hashes,native)
        self.assertEqual(receipt['board_sha256'],hashes[d.SOURCE.name]);self.assertNotIn('accepted',receipt)
    def test_drc_changed_project_rejected(self):
        hashes,steps,native=self.drc_fixture()
        (self.out/'original-drc-input'/d.SOURCE.with_suffix('.kicad_pro').name).write_text('{}')
        with self.assertRaisesRegex(d.p.Rejected,'copied original'):d.drc_binding(self.out,steps,hashes,native)
    def test_drc_save_and_argv_mismatch_rejected(self):
        hashes,steps,native=self.drc_fixture();steps[0]['argv'].insert(-1,'--save-board')
        d.p.save_json(self.out/'original-drc-process.json',steps[0])
        with self.assertRaisesRegex(d.p.Rejected,'provenance'):d.drc_binding(self.out,steps,hashes,native)
    def test_drc_raw_findings_mismatch_rejected(self):
        hashes,steps,native=self.drc_fixture();native['warnings']=1
        with self.assertRaisesRegex(d.p.Rejected,'raw DRC'):d.drc_binding(self.out,steps,hashes,native)
    def test_publish_positive_semantics_false_routing(self):
        result=d.publish(self.out,self.record(),lambda:None,lambda:None,lambda:1)
        self.assertTrue(result['observations_complete']);self.assertFalse(result['routing_accepted'])
        self.assertEqual(d.read(self.out/'summary.json'),result)
    def test_postwrite_stale_invalidates(self):
        with mock.patch.object(d,'size',return_value=0):
            result=d.publish(self.out,self.record(),mock.Mock(side_effect=[None,d.p.Rejected('stale')]),lambda:None,lambda:1)
        self.assertFalse(result['observations_complete']);self.assertTrue(list(self.out.glob('invalidated-*')))
        self.assertFalse(d.read(self.out/'summary.json')['observations_complete'])
    def test_postwrite_cancel_invalidates(self):
        result=d.publish(self.out,self.record(),mock.Mock(side_effect=[None,KeyboardInterrupt()]),lambda:None,lambda:1)
        self.assertEqual(result['status'],'cancelled');self.assertFalse(d.read(self.out/'summary.json')['observations_complete'])
    def test_postwrite_receipt_tamper_invalidates(self):
        def stable():
            path=self.out/'summary.json'
            if path.exists():
                raw=d.read(path);raw['routing_accepted']=True;d.p.save_json(path,raw)
        result=d.publish(self.out,self.record(),stable,lambda:None,lambda:1)
        self.assertFalse(result['observations_complete']);self.assertFalse(d.read(self.out/'summary.json')['routing_accepted'])
    def test_final_cap_rejects_positive(self):
        for cap in ['cpu','disk']:
            with self.subTest(cap=cap):
                path=self.out/cap;path.mkdir()
                with mock.patch.object(d,'size',return_value=d.LIMIT+1 if cap=='disk' else 0):
                    result=d.publish(path,self.record(),lambda:None,lambda:None,lambda:0 if cap=='cpu' else 1)
                self.assertFalse(result['observations_complete'])
    def test_failed_corrective_write_leaves_no_positive(self):
        save=d.p.save_json;calls=0
        def broken(path,record):
            nonlocal calls
            calls+=1
            if calls==1:return save(path,record)
            save(path.with_name(path.name+'.partial'),record);raise OSError('injected corrective failure')
        with mock.patch.object(d.p,'save_json',side_effect=broken):
            result=d.publish(self.out,self.record(),mock.Mock(side_effect=[None,d.p.Rejected('stale')]),lambda:None,lambda:1)
        self.assertFalse(result['observations_complete']);self.assertFalse((self.out/'summary.json').exists());self.assertFalse((self.out/'summary.json.partial').exists())
    def test_initial_partial_write_preserved_invalid(self):
        save=d.p.save_json;calls=0
        def broken(path,record):
            nonlocal calls
            calls+=1
            if calls==1:
                save(path.with_name(path.name+'.partial'),record);raise OSError('injected initial write failure')
            return save(path,record)
        with mock.patch.object(d.p,'save_json',side_effect=broken):result=d.publish(self.out,self.record(),lambda:None,lambda:None,lambda:1)
        self.assertFalse(result['observations_complete']);self.assertTrue(list(self.out.glob('invalidated-*partial')))
        self.assertFalse(d.read(self.out/'summary.json')['observations_complete'])

if __name__=='__main__':unittest.main()
