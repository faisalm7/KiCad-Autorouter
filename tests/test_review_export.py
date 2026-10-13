"""Pure native-process seams for export transactions; no PCB qualification."""
from pathlib import Path
from contextlib import ExitStack,contextmanager
import copy,importlib.util,json,os,signal,sys,tempfile,unittest
from unittest.mock import patch
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
if (HERE/'review_export.py').is_file():
    spec=importlib.util.spec_from_file_location('autorouter.review_export_candidate',HERE/'review_export.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
else:
    from autorouter import review_export as e
from autorouter import handoff as h,pipeline as p,floor_route as f,sexpr as sx,placement_strategy as ps

class ExportControls(unittest.TestCase):
    def test_impossible_parent_or_component_compute_is_rejected(self):
        self.export();path=self.output/'export.json';original=f.read_json(path)
        mutations=[{'parent_cpu_seconds':-1.,'control_child_cpu_seconds':1.,'total_cpu_seconds':0.},
                   {'parent_cpu_seconds':True},{'parent_cpu_seconds':float('nan')},
                   {'child_step_cpu_seconds':1.},{'monitor_cpu_seconds':1.},{'control_child_cpu_seconds':-1.}]
        for change in mutations:
            with self.subTest(change=change):
                path.write_text(json.dumps({**original,**change}))
                with self.assertRaises(p.Rejected):e.check_export(path)
        path.write_text(json.dumps(original));self.assertTrue(e.check_export(path)['current'])
    def test_sequential_native_wall_history_cannot_exceed_entire_export(self):
        seam=self.native_run
        def impossible(*args,**kwargs):
            result=seam(*args,**kwargs);result['wall_seconds']=1.;return result
        with patch.object(e,'run',side_effect=impossible),self.assertRaisesRegex(p.Rejected,'wall budget'):self.export()
        self.no_positive();self.preserved()
    def test_derived_delivery_claims_must_match_actual_validated_output(self):
        self.export();path=self.output/'export.json';original=f.read_json(path)
        changes={'whole_project_drc_clean':True,'project_file':str(self.source/'board.kicad_pro'),
                 'original_geometry_and_routing_unchanged':False,'source_hashes':{},
                 'preview_board_sha256':'0'*64,'final_sha_changed_after_refill':not original['final_sha_changed_after_refill'],
                 'output_ceiling_bytes':e.OUTPUT_BYTES+1,'output_file_ceiling':e.OUTPUT_FILES+1,
                 'original_routing_receipt_compute':{'budget_seconds':1.,'cpu_budget_seconds':1.,'wall_seconds':0.,'total_cpu_seconds':0.}}
        for key,value in changes.items():
            with self.subTest(field=key):
                path.write_text(json.dumps({**original,key:value}))
                with self.assertRaises(p.Rejected):e.check_export(path)
        path.write_text(json.dumps(original));self.assertTrue(e.check_export(path)['current'])
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        self.source=self.root/'source';self.source.mkdir();self.run=self.root/'routing';self.run.mkdir();self.candidate=self.run/'candidate';self.candidate.mkdir()
        tree=sx.parse('(kicad_pcb (version 20241229) (layers (0 "F.Cu" signal) (31 "B.Cu" signal)) (net 1 "SIG"))')
        self.track=sx.parse('(segment (start 0 0) (end 1 0) (width 0.25) (layer "F.Cu") (net 1) (uuid "track"))')
        sx.write(self.source/'board.kicad_pcb',tree);sx.write(self.candidate/'board.kicad_pcb',tree+[self.track])
        for folder in (self.source,self.candidate):(folder/'board.kicad_pro').write_text('{}')
        self.warning={'type':'lib_footprint_mismatch','severity':'warning','description':'pure seam warning','items':[{'uuid':'warning-item','description':'pure seam'}]}
        self.native={'opens':0,'blocking':0,'warnings':1,'exclusions':0,'ignored_checks':[],'findings':[self.warning]}
        self.metrics={'version':'10.0.0','pads':0,'footprints':0,'zones':0,'vias':0,'track_length_mm':1.,'copper_layers':2}
        self.report={'schema':1,'source':str(self.source/'board.kicad_pcb'),'candidate':str(self.candidate/'board.kicad_pcb'),
            'candidate_sha256':p.sha(self.candidate/'board.kicad_pcb'),'source_hashes':e.witness(self.source,project=True)['files'],
            'scope':'whole_board_unlocked_routing','accepted':True,'status':'routing_accepted','native':self.native,'metrics':self.metrics}
        self.receipt=self.run/'result.json';p.save_json(self.receipt,self.report);self.native_mode='valid';self.calls=[]
        self.identity={'current':True,'applied':False,'candidate':self.report['candidate'],'candidate_sha256':self.report['candidate_sha256']}
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(h,'check_result',return_value=self.identity));self.stack.enter_context(patch.object(p,'check_result',return_value=self.identity))
        self.stack.enter_context(patch.object(p,'tool_manifest',return_value={'implementation_sha256':{},'files':{}}))
        self.stack.enter_context(patch.object(e,'run',side_effect=self.native_run))
        h.review_copy(self.receipt,self.root/'review');self.choice=self.root/'choice/choice.json';h.review_choice(self.root/'review/review.json',self.choice.parent,'accept')
        self.output=self.root/'export';self.inputs={str(path):e.witness(path) for path in (self.source,self.run,self.root/'review',self.choice.parent)}
    def native_run(self,argv,*,cwd,log,**kwargs):
        self.calls.append((argv,kwargs));name=log.stem;log.write_bytes(b'')
        if name in ('refill-drc','final-drc'):
            target=Path(argv[argv.index('--output')+1]);board=Path(argv[-1]);findings=[copy.deepcopy(self.warning)]
            if self.native_mode=='invalid' and name=='final-drc':findings.append({'type':'clearance','severity':'error','items':[],'description':'deliberate pure invalid seam'})
            if self.native_mode=='rule-change' and name=='refill-drc':board.with_suffix('.kicad_pro').write_text('{"tampered":"native rule mutation"}')
            if self.native_mode=='cancel':os.kill(os.getpid(),signal.SIGTERM)
            raw={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':board.name,'violations':findings,
                 'unconnected_items':[],'schematic_parity':[],'ignored_checks':[],'included_severities':['error','warning','exclusion']}
            target.write_text(json.dumps(raw));exit_code=5
        elif name=='metrics':Path(argv[-1]).write_text(json.dumps(self.metrics));exit_code=0
        else:raise AssertionError('Unexpected native seam stage '+name)
        return {'argv':argv,'cwd':str(cwd),'log':str(log),'log_bytes':0,'log_truncated':False,'status':'nonzero_exit' if exit_code else 'success',
            'exit_code':exit_code,'cleanup_complete':True,'wall_seconds':0.,'cpu_seconds':0.,'monitor_cpu_seconds':0.}
    def export(self):return e.export(self.choice,self.output)
    def preserved(self):
        self.assertEqual({str(path):e.witness(path) for path in (self.source,self.run,self.root/'review',self.choice.parent)},self.inputs)
    def no_positive(self):
        record=json.loads((self.output/'export.json').read_text());self.assertFalse(record['export_accepted']);self.assertNotEqual(record['status'],'export_validated')
    def test_actual_shared_validate_refill_and_readback_run_into_separate_copy(self):
        result=self.export();self.assertTrue(result['export_accepted']);self.assertTrue(result['native_validation_performed'])
        self.assertEqual([Path(x[0][-1]).name for x in self.calls],['board.kicad_pcb','board.kicad_pcb','metrics.json'])
        self.assertTrue(all(x[0][:3]==e.f.SANDBOX for x in self.calls));self.assertTrue(all(x[1]['max_workdir_bytes']==e.OUTPUT_BYTES for x in self.calls))
        self.assertEqual(result['native'],self.native);self.assertEqual(result['metrics'],self.metrics);self.assertTrue(e.check_export(self.output/'export.json')['current'])
        for key in ('applied','human_pcb_approval_observed','physical_electrical_validation','new_engine_execution'):self.assertFalse(result[key])
        self.preserved()
    def test_gui_rules_before_choice_are_never_export_authority(self):
        # Build a new intent after an observed GUI metadata change.
        (self.root/'review/project/board.kicad_pro').write_text('{"GUI":"unvalidated different rules"}')
        newer=self.root/'new-choice';h.review_choice(self.root/'review/review.json',newer,'accept');self.choice=newer/'choice.json'
        result=self.export();self.assertTrue(result['export_accepted']);self.assertEqual(Path(result['project_file']).read_bytes(),(self.source/'board.kicad_pro').read_bytes())
        self.assertNotEqual(Path(result['project_file']).read_bytes(),(self.root/'review/project/board.kicad_pro').read_bytes())
    def test_protected_original_copper_and_empty_original_directories_survive_export(self):
        protected=sx.parse('(segment (start 2 0) (end 3 0) (width 0.25) (layer "F.Cu") (net 1) (uuid "protected") (locked yes))')
        for folder in (self.source,self.candidate):
            board=folder/'board.kicad_pcb';tree=sx.read(board);tree.append(protected);sx.write(board,tree);(folder/'empty-original-directory').mkdir()
        self.metrics['track_length_mm']=2.;self.report.update(candidate_sha256=p.sha(self.candidate/'board.kicad_pcb'),source_hashes=e.witness(self.source,project=True)['files'])
        self.identity['candidate_sha256']=self.report['candidate_sha256'];p.save_json(self.receipt,self.report)
        h.review_copy(self.receipt,self.root/'protected-review');h.review_choice(self.root/'protected-review/review.json',self.root/'protected-choice','accept');self.choice=self.root/'protected-choice/choice.json'
        result=self.export();candidate=Path(result['candidate']);self.assertTrue(result['export_accepted']);self.assertIn(protected,p.routes(sx.read(candidate)))
        self.assertTrue((candidate.parent/'empty-original-directory').is_dir())
        self.assertTrue((self.output/'validation/snapshot/empty-original-directory').is_dir());self.assertTrue(e.check_export(self.output/'export.json')['current'])
    def test_runtime_and_native_pin_manifest_cannot_be_stripped_from_export_proof(self):
        self.export();path=self.output/'export.json';data=json.loads(path.read_text());data['tools']={};path.write_text(json.dumps(data))
        with self.assertRaises(p.Rejected):e.check_export(path)
    def test_reject_or_changed_choice_never_enters_native(self):
        record=json.loads(self.choice.read_text());record['choice']='reject';self.choice.write_text(json.dumps(record))
        with self.assertRaises(p.Rejected):self.export()
        self.assertEqual(self.calls,[]);self.assertFalse(self.output.exists())
    def test_stale_original_receipt_review_board_gui_metadata_or_empty_evidence_directory_blocks(self):
        for path,body in [(self.source/'board.kicad_pro',b'{"changed":true}'),(self.receipt,b'{}'),(self.root/'review/project/board.kicad_pcb',b'edited'),(self.root/'review/project/board.kicad_pro',b'edited')]:
            with self.subTest(path=path):
                old=path.read_bytes();path.write_bytes(body)
                with self.assertRaises((p.Rejected,KeyError,ValueError)):self.export()
                path.write_bytes(old);self.assertFalse(self.output.exists());self.assertEqual(self.calls,[])
        (self.run/'new-empty-directory').mkdir()
        with self.assertRaises(p.Rejected):self.export()
        self.assertEqual(self.calls,[])
    def test_changed_bound_preview_is_rejected_before_native(self):
        review=self.root/'review/review.json';data=json.loads(review.read_text());before=self.root/'review/before'
        import shutil
        shutil.copytree(self.source,before);html=self.root/'review/preview.html';html.write_text('pure preview')
        data['preview']={'plotter_sha256':p.sha(e.c.CLI),'input_trees':{},'files':{'preview.html':p.sha(html)}};review.write_text(json.dumps(data))
        newer=self.root/'preview-choice';h.review_choice(review,newer,'accept');self.choice=newer/'choice.json';html.write_text('tampered')
        with self.assertRaises(p.Rejected):self.export()
        self.assertEqual(self.calls,[])
    def test_fresh_invalid_native_and_rule_mutation_fail_with_preserved_first_failure(self):
        for mode in ('invalid','rule-change'):
            with self.subTest(mode=mode):
                self.native_mode=mode;self.output=self.root/('export-'+mode)
                with self.assertRaises(p.Rejected):self.export()
                self.no_positive();self.assertTrue((self.output/'validation').exists());self.preserved()
        self.assertTrue((self.root/'export-rule-change/validation/refill-drc-failure.json').exists())
    def test_cancellation_during_actual_shared_drc_restores_handlers_and_retains_failure(self):
        prior={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)};self.native_mode='cancel'
        with self.assertRaisesRegex(p.Rejected,'cancelled'):self.export()
        self.assertEqual({sig:signal.getsignal(sig) for sig in prior},prior);self.no_positive();self.preserved()
        self.assertTrue((self.output/'validation/refill-drc-failure.json').exists())
        failed=json.loads((self.output/'export.json').read_text())
        self.assertEqual(failed['budget_seconds'],e.SECONDS)
        self.assertEqual(failed['cpu_budget_seconds'],e.SECONDS)
        p.check_resource_accounting(failed,child_key='child_step_cpu_seconds')
    def test_session_cleanup_signal_and_full_cpu_overshoot_cannot_leave_positive(self):
        for mode in ('signal','CPU'):
            with self.subTest(mode=mode):
                self.output=self.root/('cleanup-'+mode);extra=[0.];real=h.cpu_seconds
                @contextmanager
                def session():
                    try:yield
                    finally:
                        if mode=='signal':raise KeyboardInterrupt
                        extra[0]=121.
                with patch.object(p,'validation_readback_session',session),patch.object(h,'cpu_seconds',side_effect=lambda:real()+extra[0]):
                    with self.assertRaises(p.Rejected):self.export()
                self.no_positive();self.assertTrue(list(self.output.glob('invalidated-export-*')));self.preserved()
    def test_context_exit_directory_replacement_never_touches_preexisting_target(self):
        for fail in (False,True):
            with self.subTest(session_exception=fail):
                self.output=self.root/('owner-output-'+str(fail));retained=self.root/('retained-owned-'+str(fail));replacement=self.root/('preexisting-target-'+str(fail));replacement.mkdir()
                (replacement/'keep').write_text('preserve original target');(replacement/'export.json').write_text('preexisting unrelated metadata')
                before=e.witness(replacement)
                @contextmanager
                def session():
                    try:yield
                    finally:
                        self.output.rename(retained);replacement.rename(self.output)
                        if fail:raise RuntimeError('deliberate session cleanup exception')
                expected=RuntimeError if fail else p.Rejected
                with patch.object(p,'validation_readback_session',session),self.assertRaises(expected) as error:self.export()
                if fail:self.assertIn('deliberate session cleanup exception',str(error.exception))
                self.assertEqual(e.witness(self.output),before);self.assertTrue((retained/'export.json').exists());self.preserved()
                with self.assertRaises(p.Rejected):e.check_export(retained/'export.json')
    def test_context_exit_exception_without_replacement_invalidates_ready_export(self):
        @contextmanager
        def session():
            try:yield
            finally:raise RuntimeError('deliberate final session failure')
        with patch.object(p,'validation_readback_session',session),self.assertRaisesRegex(RuntimeError,'deliberate final session failure'):self.export()
        self.no_positive();self.assertTrue(list(self.output.glob('invalidated-export-*')));self.preserved()
    def test_corrective_writer_mutating_record_and_disk_cannot_leave_positive(self):
        self.native_mode='invalid';save=p.save_json
        def writer(path,record):
            if path.name=='export.json' and record.get('status')=='rejected':record.update(status='export_validated',export_accepted=True)
            save(path,record)
        with patch.object(p,'save_json',side_effect=writer),self.assertRaises(p.Rejected):self.export()
        self.assertFalse((self.output/'export.json').exists());self.assertTrue(list(self.output.glob('invalidated-export-*')));self.preserved()
    def test_candidate_report_tampering_cannot_rehash_away_shared_reconstruction(self):
        result=self.export();candidate=Path(result['candidate']);tree=sx.read(candidate);tree.remove(p.routes(tree)[0]);sx.write(candidate,tree)
        path=self.output/'export.json';data=json.loads(path.read_text());data['candidate_sha256']=p.sha(candidate);data['export_evidence']=e.evidence(self.output);path.write_text(json.dumps(data))
        with self.assertRaises(p.Rejected):e.check_export(path)
    def test_positive_publication_or_final_material_mutation_is_invalidated(self):
        save=p.save_json;sent=False
        def tamper(path,record):
            nonlocal sent
            save(path,record)
            if path.name=='export.json' and record.get('export_accepted') and not sent:
                sent=True;data=json.loads(path.read_text());data['candidate_sha256']='wrong';path.write_text(json.dumps(data))
        with patch.object(p,'save_json',side_effect=tamper),self.assertRaises(p.Rejected):self.export()
        self.no_positive();self.preserved()
    def test_preexisting_or_protected_outputs_remain_unchanged(self):
        self.output.mkdir();sentinel=self.output/'keep';sentinel.write_text('unchanged')
        with self.assertRaises(p.Rejected):self.export()
        self.assertEqual(sentinel.read_text(),'unchanged');self.assertEqual(self.calls,[])
        self.output=self.source/'inside'
        with self.assertRaises(p.Rejected):self.export()
        self.assertFalse(self.output.exists())
    def test_unknown_receipt_and_finite_budgets_cannot_downgrade_policy(self):
        for value in (True,float('nan'),29,121):
            with self.subTest(value=value),self.assertRaises(p.Rejected):e.export(self.choice,self.output,value)
        report=copy.deepcopy(self.report);report.update(schema=2,input_policy='board-floors-v1');p.save_json(self.receipt,report)
        with self.assertRaises((p.Rejected,KeyError,FileNotFoundError)):self.export()
        self.assertEqual(self.calls,[])
    def test_no_solver_stage_can_be_executed(self):
        job=e.ExportJob(self.root/'isolated-job',120,lambda:120)
        with self.assertRaisesRegex(p.Rejected,'prohibits'):job.step('engine',['ignored'])
        self.assertEqual(self.calls,[])
    def test_shared_guidance_and_layer_lineage_selectors_use_original_receipt(self):
        binding={'receipt':str(self.receipt),'source':str(self.source/'board.kicad_pcb'),'input_policy':f.PLACEMENT_POLICY};report=copy.deepcopy(self.report)
        with patch.object(f,'read_json',return_value={'pure':'contract'}):
            basis,contract,_=e.lineage(binding,report);self.assertEqual(basis,self.receipt.parent)
            binding['input_policy']=f.SEARCH_POLICY;self.assertEqual(e.lineage(binding,report)[0],self.receipt.parent)
            binding['input_policy']=ps.POLICY;self.assertEqual(e.lineage(binding,report)[0],self.receipt.parent/'incumbent')
        binding['input_policy']='native';report.update(layer_binding={'declared':'binding'},routing_preferences={'effective':{'declared':'effective'}})
        with patch.object(p,'layer_markers',return_value=True),patch.object(p,'layer_contract',return_value={'pure':'layers'}) as call:
            self.assertEqual(e.lineage(binding,report)[2],{'pure':'layers'});self.assertEqual(call.call_args.args[0],self.receipt.parent)

if __name__=='__main__':unittest.main()
