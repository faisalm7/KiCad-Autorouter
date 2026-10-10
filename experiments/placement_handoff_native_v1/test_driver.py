"""Pure/native-receipt read-only guards; never invoke native KiCad or an engine."""
import copy,hashlib,json,subprocess,tempfile,unittest,io,os,signal
from contextlib import ExitStack
from pathlib import Path
from unittest import mock
import driver as d

class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_receipt=d.read(d.RECEIPT);cls.verified=d.p.check_result(d.RECEIPT)
        cls.files=d.payload(Path(cls.original_receipt['candidate']).parent)
        cls.sourcefiles=d.payload(Path(cls.original_receipt['source']).parent)
        cls.board=cls.files['fixture.kicad_pcb'];cls.project=cls.files['fixture.kicad_pro']
    def setUp(self):self.tmp=tempfile.TemporaryDirectory(prefix='pure-',dir=d.HERE);self.out=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def inputs(self):
        root=self.out/'root';(root/'.runs').mkdir(parents=True)
        source=root/'source';d.copy_bytes(self.sourcefiles,source)
        run=root/'.runs/accepted';run.mkdir();d.copy_bytes(self.files,run/'candidate')
        data=copy.deepcopy(self.original_receipt);data.update(source=str(source/'fixture.kicad_pcb'),candidate=str(run/'candidate/fixture.kicad_pcb'))
        receipt=run/'result.json';d.p.save_json(receipt,data)
        handoff=root/'.runs/handoff';handoff.mkdir();d.copy_bytes(self.files,handoff/'project')
        review={'schema':1,'status':'ready_for_manual_review','input_policy':d.POLICY,'source_receipt_schema':3,'receipt':str(receipt),'receipt_sha256':d.sha(d.io.read_bytes(receipt)),
                'verified_candidate_sha256':d.CANDIDATE_SHA,'candidate_sha256':d.CANDIDATE_SHA,'project':str(handoff/'project'),'board':str(handoff/'project/fixture.kicad_pcb'),
                'native_validation_performed':False,'initial_project_hashes':d.hashes(self.files),'budget_seconds':30,'cpu_budget_seconds':30,'within_budget':True,'wall_seconds':1.0,'total_cpu_seconds':0.5}
        d.p.save_json(handoff/'review.json',review)
        verified={**self.verified,'candidate':data['candidate']}
        return root,receipt,handoff/'review.json',review,verified
    def bind(self,inputs,checker=None):
        root,receipt,handoff,review,verified=inputs
        with mock.patch.object(d,'ROOT',root),mock.patch.object(d,'RECEIPT',receipt),mock.patch.object(d,'RECEIPT_SHA',d.sha(d.io.read_bytes(receipt))),mock.patch.object(d.p,'check_result',side_effect=checker or (lambda _:verified)):
            return d.bind_handoff(receipt,handoff)
    def test_original_actual_receipt_readback_and_fixed_candidate(self):
        self.assertEqual(self.verified['candidate_sha256'],d.CANDIDATE_SHA);self.assertEqual(self.verified['input_policy'],d.POLICY)
        self.assertEqual(d.sha(d.io.read_bytes(d.RECEIPT)),d.RECEIPT_SHA)
    def test_complete_project_binding_synthetic_handoff(self):
        inputs=self.inputs();bound,files=self.bind(inputs)
        self.assertEqual(files,self.files);self.assertEqual(bound['candidate_hashes'],d.hashes(self.files))
    def test_handoff_modes_and_boolean_schema_rejected(self):
        inputs=self.inputs();root,receipt,handoff,review,verified=inputs
        for field,value in [('schema',True),('input_policy','native'),('source_receipt_schema',2),('native_validation_performed',True),('verified_candidate_sha256','0'*64),('accepted',1),('applied',True),('within_budget',1)]:
            with self.subTest(field=field):
                changed={**review,field:value};d.p.save_json(handoff,changed)
                with self.assertRaises(d.p.Rejected):self.bind(inputs)
    def test_handoff_resource_samples_fail_closed(self):
        inputs=self.inputs();handoff=inputs[2];review=inputs[3]
        for field,value in [('budget_seconds',60),('wall_seconds',30.01),('total_cpu_seconds',-1),('wall_seconds',True),('within_budget',False)]:
            with self.subTest(field=field):
                d.p.save_json(handoff,{**review,field:value})
                with self.assertRaises(d.p.Rejected):self.bind(inputs)
    def test_wrong_metadata_project_path_rejected(self):
        inputs=self.inputs();d.p.save_json(inputs[2],{**inputs[3],'project':str(inputs[0]/'source')})
        with self.assertRaises(d.p.Rejected):self.bind(inputs)
    def test_copied_rule_mutated_during_checker_rejected(self):
        inputs=self.inputs()
        def check(_):
            (inputs[2].parent/'project/fixture.kicad_pro').write_bytes(b'{}');return inputs[4]
        with self.assertRaises(d.p.Rejected):self.bind(inputs,check)
    def test_native_evidence_mutated_during_checker_rejected(self):
        inputs=self.inputs()
        def check(_):
            (inputs[1].parent/'unrecorded-raw-report.json').write_bytes(b'{}');return inputs[4]
        with self.assertRaisesRegex(d.p.Rejected,'input changed'):self.bind(inputs,check)
    def test_original_rules_mutated_during_checker_rejected(self):
        inputs=self.inputs()
        def check(_):
            (inputs[0]/'source/fixture.kicad_pro').write_bytes(b'{}');return inputs[4]
        with self.assertRaises(d.p.Rejected):self.bind(inputs,check)
    def test_exact_positive_and_single_via_negative_recipe(self):
        positive,pro,recipe=d.prior.prepare('positive',self.board,self.project)
        self.assertEqual((positive,pro),(self.board,self.project))
        negative,pro,recipe=d.prior.prepare('missing_via',self.board,self.project)
        before=d.sx.parse(self.board.decode());after=d.sx.parse(negative.decode())
        self.assertEqual(pro,self.project);self.assertEqual(d.p.immutable(before),d.p.immutable(after))
        self.assertEqual(d.p.routes(after),[r for r in d.p.routes(before) if r[0]!='via']);self.assertEqual(len(recipe['adjacent_route_uuids']),2)
        self.assertEqual([x for x in before if x not in d.p.routes(before)],[x for x in after if x not in d.p.routes(after)])
    def test_required_via_not_arbitrary_open(self):
        _,_,recipe=d.prior.prepare('missing_via',self.board,self.project)
        native={'opens':1,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':[{'type':'unconnected_items','severity':'error','items':[{'uuid':'wrong'}]}]}
        self.assertFalse(d.prior.diagnostic_pass('missing_via',native,recipe,[])[0])
        native['findings'][0]['items']=[{'uuid':x} for x in recipe['adjacent_route_uuids']]
        self.assertTrue(d.prior.diagnostic_pass('missing_via',native,recipe,[])[0])
        native['findings'][0]['excluded']=True;self.assertFalse(d.prior.diagnostic_pass('missing_via',native,recipe,[])[0])
    def test_positive_requires_clean_native(self):
        native={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':[]}
        self.assertTrue(d.prior.diagnostic_pass('positive',native,{},[])[0]);native['warnings']=1
        self.assertFalse(d.prior.diagnostic_pass('positive',native,{},[])[0])
    def test_snapshot_rejects_uncommitted_helpers(self):
        with mock.patch.object(d.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'wrong',b'')):
            with self.assertRaisesRegex(d.p.Rejected,'commit exact'):d.snapshot(self.out,{'implementation_sha256':{},'git_head':'fake'},lambda:1)
        self.assertFalse((self.out/'code').exists())
    def test_explicit_flag_required(self):
        with mock.patch.object(d,'bind_handoff') as bind:
            with self.assertRaisesRegex(d.p.Rejected,'run-native'):d.experiment(self.out/'none',d.RECEIPT,self.out/'none')
        bind.assert_not_called()
    def test_only_drc_argv_allowed_before_subprocess(self):
        job=object.__new__(d.NativeJob);job.out=self.out;job.board_name='fixture.kicad_pcb'
        with mock.patch.object(d,'run') as worker:
            for name,args in [('engine',['java']),('native-drc',d.drc_argv(self.out,Path(job.board_name))+['--save-board'])]:
                with self.subTest(name=name):
                    with self.assertRaisesRegex(d.p.Rejected,'exact nonsaving'):job.step(name,args,already_sandboxed=True)
        worker.assert_not_called()
    def test_native_stage_raw_bytes_cannot_rebase(self):
        board=self.out/'candidate/fixture.kicad_pcb';board.parent.mkdir();board.write_bytes(self.board)
        path=self.out/'native-drc.json';path.write_bytes(b'{}')
        job=object.__new__(d.NativeJob);job.out=self.out;job.frozen_stage={'native-drc.json':d.sha(b'{}')}
        path.write_bytes(b'{"date":"changed"}')
        with self.assertRaisesRegex(d.p.Rejected,'stage changed'):d.check_case(job,board,{},d.inventory(board.parent))
    def publish(self,stable,remaining=lambda:1,account=lambda:None):
        record={'status':'completed','controls_passed':True,'routing_accepted':False,'gui_qualified':False}
        return d.publish(self.out,record,stable,account,remaining)
    def test_publication_after_write_cancel(self):
        result=self.publish(mock.Mock(side_effect=[None,KeyboardInterrupt()]))
        self.assertEqual(result['status'],'cancelled');self.assertFalse(d.read(self.out/'summary.json')['controls_passed'])
    def test_publication_after_write_stale(self):
        result=self.publish(mock.Mock(side_effect=[None,d.p.Rejected('stale')]))
        self.assertFalse(result['controls_passed']);self.assertTrue(list(self.out.glob('invalidated-*')))
    def test_publication_final_cap(self):
        result=self.publish(lambda:None,remaining=mock.Mock(side_effect=[1,0]))
        self.assertFalse(result['controls_passed'])
    def test_publication_metadata_tamper(self):
        def stable():
            path=self.out/'summary.json'
            if path.exists():d.p.save_json(path,{'controls_passed':True,'routing_accepted':True})
        result=self.publish(stable);self.assertFalse(result['controls_passed']);self.assertFalse(d.read(self.out/'summary.json')['routing_accepted'])
    def test_corrective_write_failure_vacates_positive_and_partial(self):
        real=d.p.save_json;count=0
        def writer(path,record):
            nonlocal count
            count+=1
            if count==1:return real(path,record)
            real(path.with_suffix('.json.partial'),record);raise OSError('intentional correction failure')
        with mock.patch.object(d.p,'save_json',side_effect=writer):result=self.publish(mock.Mock(side_effect=[None,d.p.Rejected('stale')]))
        self.assertFalse(result['controls_passed']);self.assertFalse((self.out/'summary.json').exists());self.assertFalse((self.out/'summary.json.partial').exists())
    def test_output_reuse_symlink_and_outside_rejected(self):
        link=self.out/'link';link.symlink_to(self.out)
        with self.assertRaises(d.p.Rejected):d.owned(link)
        with self.assertRaises(d.p.Rejected):d.owned(d.ROOT.parent/'unrelated',False)
        with self.assertRaisesRegex(d.p.Rejected,'fresh direct'):d.experiment(self.out,d.RECEIPT,self.out/'review.json',run_native=True)

    def flow(self, event=None):
        """Real copied files/runner boundary; native worker/checker are explicitly fake."""
        inputs=self.inputs();root,receipt,handoff,review,verified=inputs
        helper=root/'autorouter/fixture.py';helper.parent.mkdir();helper.write_bytes(b'# pure fake helper\n')
        output=root/'.runs/control';tools={'files':{},'implementation_sha256':{'autorouter/fixture.py':d.sha(helper.read_bytes())},'git_head':'fake-pure-head'}
        raws={case:copy.deepcopy(d.read(d.ROOT/'.runs/placement-production-controls-native-002'/case/'diagnostic/diagnostic-drc.json')) for case in ('positive','missing_via')}
        raw_report_read=d.p.parse_report;check_case=d.check_case
        def notify(where,**data):
            if event:event(where,root=root,output=output,inputs=inputs,**data)
        def manifest():notify('manifest');return tools
        def snapshot(out,tools,remaining):
            d.copy_bytes({'autorouter/fixture.py':helper.read_bytes()},out/'code');return tools['implementation_sha256']
        def runner(argv,**kwargs):
            folder=kwargs['cwd'];case=folder.name;notify('worker',case=case)
            d.p.save_json(folder/'native-drc.json',raws[case]);kwargs['log'].write_bytes(b'PURE fake worker; no native executed\n')
            return {'argv':argv,'cwd':str(folder),'exit_code':0 if case=='positive' else 5,'status':'success' if case=='positive' else 'nonzero_exit','cleanup_complete':True,'cpu_seconds':.001,'monitor_cpu_seconds':.001}
        def parse(path,name):
            result=raw_report_read(path,name);notify('parsed',path=path);return result
        def checked(job,board,native,expected):
            result=check_case(job,board,native,expected);notify('bound',job=job);return result
        with ExitStack() as stack:
            for obj,name,value in [(d,'ROOT',root),(d,'RECEIPT',receipt),(d,'RECEIPT_SHA',d.sha(d.io.read_bytes(receipt))),(d,'snapshot',snapshot),(d,'run',runner),(d,'check_case',checked),(d.p,'parse_report',parse),(d.p,'tool_manifest',manifest),(d.p,'check_storage',lambda:None),(d.p,'check_result',lambda _:verified)]:stack.enter_context(mock.patch.object(obj,name,value))
            result=d.experiment(output,receipt,handoff,run_native=True)
        return result,output
    def test_fake_native_whole_flow_positive_and_negative(self):
        result,out=self.flow();self.assertEqual(result['status'],'completed');self.assertTrue(result['controls_passed'])
        self.assertEqual([x['case'] for x in result['cases']],['positive','missing_via']);self.assertEqual(len(result['steps']),2)
        self.assertFalse(result['routing_accepted']);self.assertFalse(result['gui_qualified']);self.assertTrue(result['within_budget'])
        self.assertEqual(result['planned_project_copy_bytes'],4*sum(map(len,self.files.values())))
    def test_first_stage_cannot_rebase_during_second_worker(self):
        def event(where,**info):
            if where=='worker' and info['case']=='missing_via':
                path=info['output']/'positive/native-drc.json';raw=d.read(path);raw['date']='changed';d.p.save_json(path,raw)
        result,out=self.flow(event);self.assertFalse(result['controls_passed']);self.assertFalse(d.read(out/'summary.json')['controls_passed'])
    def test_stage_mutation_after_native_parse_rejected(self):
        changed=False
        def event(where,**info):
            nonlocal changed
            if where=='parsed' and not changed:
                changed=True;raw=d.read(info['path']);raw['date']='changed';d.p.save_json(info['path'],raw)
        result,out=self.flow(event);self.assertTrue(changed);self.assertFalse(result['controls_passed'])
    def test_raw_mutation_after_binding_rejected(self):
        changed=False
        def event(where,**info):
            nonlocal changed
            if where=='bound' and not changed:
                changed=True;path=info['job'].out/'native-drc.json';raw=d.read(path);raw['date']='changed';d.p.save_json(path,raw)
        result,out=self.flow(event);self.assertTrue(changed);self.assertFalse(result['controls_passed'])
    def test_original_changed_in_postpublication_metadata_rejected(self):
        changed=False
        def event(where,**info):
            nonlocal changed
            if where=='manifest' and (info['output']/'summary.json').exists() and not changed:
                changed=True;(info['root']/'source/fixture.kicad_pro').write_bytes(b'{}')
        result,out=self.flow(event);self.assertTrue(changed);self.assertFalse(result['controls_passed']);self.assertIsNone(result['original_inputs_unchanged'])
    def test_completed_copy_changed_in_final_metadata_rejected(self):
        changed=False
        def event(where,**info):
            nonlocal changed
            if where=='manifest' and (info['output']/'summary.json').exists() and not changed:
                changed=True;(info['output']/'positive/candidate/fixture.kicad_pro').write_bytes(b'{}')
        result,out=self.flow(event);self.assertTrue(changed);self.assertFalse(result['controls_passed'])
    def test_fake_worker_cancellation_never_positive(self):
        def event(where,**info):
            if where=='worker':raise KeyboardInterrupt
        result,out=self.flow(event);self.assertEqual(result['status'],'cancelled');self.assertFalse(result['controls_passed'])

    def signals(self,sig):
        root=self.out/'signal-root';(root/'.runs').mkdir(parents=True);output=root/'.runs/control';output.mkdir()
        before={x:signal.getsignal(x) for x in (signal.SIGINT,signal.SIGTERM)}
        def fake_experiment(*args,**kwargs):
            count=0
            def stable():
                nonlocal count
                count+=1
                if count==2:os.kill(os.getpid(),sig)
            return d.publish(output,{'status':'completed','controls_passed':True},stable,lambda:None,lambda:1)
        with mock.patch.object(d,'ROOT',root),mock.patch.object(d,'experiment',side_effect=fake_experiment),mock.patch('sys.stdout',new=io.StringIO()):
            status=d.main(['--output',str(output),'--receipt',str(root/'result.json'),'--handoff',str(root/'review.json'),'--run-native'])
        self.assertEqual(status,2);self.assertEqual(d.read(output/'summary.json')['status'],'cancelled');self.assertFalse(d.read(output/'summary.json')['controls_passed'])
        self.assertEqual(before,{x:signal.getsignal(x) for x in before})
    def test_real_python_self_sigint_publication(self):self.signals(signal.SIGINT)
    def test_real_python_self_sigterm_publication(self):self.signals(signal.SIGTERM)

    def test_final_size_scan_receipt_mutation_rejected(self):
        def sizing(path):
            value=d.read(path/'summary.json');value.update(routing_accepted=True,controls_passed=True);d.p.save_json(path/'summary.json',value);return 0
        with mock.patch.object(d,'size',side_effect=sizing):result=self.publish(lambda:None)
        self.assertEqual(result['status'],'invalidated');self.assertFalse(result['controls_passed']);self.assertFalse(d.read(self.out/'summary.json')['routing_accepted'])
        self.assertTrue(list(self.out.glob('invalidated-*')))
    def test_final_size_scan_budget_consumption_rejected(self):
        exhausted=False
        def sizing(path):
            nonlocal exhausted
            exhausted=True;return 0
        with mock.patch.object(d,'size',side_effect=sizing):result=self.publish(lambda:None,remaining=lambda:0 if exhausted else 1)
        self.assertTrue(exhausted);self.assertEqual(result['status'],'invalidated');self.assertFalse(d.read(self.out/'summary.json')['controls_passed'])

    def test_final_size_scan_inmemory_receipt_mutation_rejected(self):
        record={'status':'completed','controls_passed':True,'scope':'fixed'}
        def sizing(path):record['scope']='changed';return 0
        with mock.patch.object(d,'size',side_effect=sizing):result=d.publish(self.out,record,lambda:None,lambda:None,lambda:1)
        self.assertEqual(result['status'],'invalidated');self.assertFalse(result['controls_passed']);self.assertEqual(d.read(self.out/'summary.json'),result)

if __name__=='__main__':unittest.main()
