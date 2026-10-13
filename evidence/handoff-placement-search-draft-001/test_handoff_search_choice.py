"""Pure policy/disposition threat controls; no native worker or PCB approval."""
from pathlib import Path
import copy,importlib.util,json,os,signal,shutil,sys,tempfile,unittest
from unittest.mock import patch
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/handoff.py').is_file());HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
if (HERE/'handoff.py').is_file():
    spec=importlib.util.spec_from_file_location('autorouter.handoff_candidate',HERE/'handoff.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
else:
    from autorouter import handoff as h
from autorouter import placement_strategy as ps
from autorouter.pipeline import Rejected,sha
class Controls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        self.source=self.root/'source';self.source.mkdir();self.run=self.root/'run';self.run.mkdir();self.candidate=self.run/'candidate';self.candidate.mkdir()
        for folder,board in [(self.source,b'(original)'),(self.candidate,b'(candidate)')]:
            (folder/'board.kicad_pcb').write_bytes(board);(folder/'board.kicad_pro').write_bytes(b'{}');(folder/'board.kicad_dru').write_bytes(b'(version 1)')
        self.receipt=self.run/'result.json';self.data={'schema':1,'source':str(self.source/'board.kicad_pcb'),'candidate':str(self.candidate/'board.kicad_pcb'),'candidate_sha256':sha(self.candidate/'board.kicad_pcb'),
            'native':{'opens':0,'blocking':0,'warnings':1,'exclusions':0,'ignored_checks':[],'findings':[{'type':'lib_footprint_mismatch','severity':'warning','items':[]}]},'metrics':{'track_length_mm':1,'vias':0}}
        self.write();self.mock=patch.object(h,'check_result',return_value={'current':True,'applied':False,'candidate':self.data['candidate'],'candidate_sha256':self.data['candidate_sha256']});self.check=self.mock.start();self.addCleanup(self.mock.stop)
    def write(self):self.receipt.write_text(json.dumps(self.data))
    def search(self):
        self.data.update(schema=4,input_policy=h.f.SEARCH_POLICY,adapter='both',scope='whole_board_unlocked_routing',engine_profile='tuned',scoring_variant='via_default',baseline='B2_tuned',planning_parameters=h.pc.parameters())
        path=self.run/'placement-search.json';h.save_json(path,h.f.search_contract('tuned','via_default'));self.data['placement_search']={'file':path.name,'sha256':sha(path)};self.write();self.check.return_value['input_policy']=h.f.SEARCH_POLICY
    def pruning(self):
        self.data.update(schema=5,input_policy=ps.POLICY,strategy=ps.STRATEGY,baseline='C-prototype',adapter='both',engine_profile='tuned',scoring_variant='via_default',scope='whole_board_unlocked_routing',proposal_policy='feedback')
        path=self.run/'pruning-contract.json';h.save_json(path,ps.contract());self.data['pruning_contract']={'file':path.name,'sha256':sha(path)};self.write();self.check.return_value['input_policy']=ps.POLICY
    def review(self):return h.review_copy(self.receipt,self.root/'review')
    def choose(self,choice='accept',name='choice'):return h.review_choice(self.root/'review/review.json',self.root/name,choice)
    def test_search_and_pruning_only_with_exact_policy_and_central_identity(self):
        for setup,expected in [(self.search,h.f.SEARCH_POLICY),(self.pruning,ps.POLICY)]:
            with self.subTest(expected=expected):
                # Separate source/run per case; no mixed markers or policy downgrade.
                self.data={k:v for k,v in self.data.items() if k in ('source','candidate','candidate_sha256','native','metrics')};self.data['schema']=1
                for p in self.run.iterdir():
                    if p.is_file() and p.name!='result.json':p.unlink()
                setup();target=self.root/('review-'+expected);record=h.review_copy(self.receipt,target)
                self.assertEqual(record['input_policy'],expected);self.assertEqual(record['source_receipt_schema'],self.data['schema']);self.assertFalse(record['native_validation_performed'])
    def test_mixed_missing_or_downgraded_markers_never_create_review(self):
        self.pruning();self.data['schema']=4;self.write()
        with self.assertRaises(Rejected):self.review()
        self.check.assert_not_called();self.assertFalse((self.root/'review').exists())
    def test_central_policy_mismatch_invalidates_search_handoff(self):
        self.search();self.check.return_value['input_policy']=ps.POLICY
        with self.assertRaisesRegex(Rejected,'central receipt'):self.review()
        self.assertFalse((self.root/'review').exists())
    def test_choice_never_inherits_native_approval_or_application(self):
        self.review();result=self.choose();self.assertTrue(result['choice_recorded']);self.assertEqual(result['choice'],'accept')
        for key in ('routing_accepted','applied','native_validation_performed','human_pcb_approval_observed'):self.assertFalse(result[key])
        self.assertTrue(result['fresh_native_validation_required']);self.assertEqual(result['saved_native_findings'],self.data['native']);self.assertEqual(result['status'],'disposition_recorded')
    def test_gui_metadata_changes_are_recorded_without_becoming_rules_authority(self):
        self.review();(self.root/'review/project/board.kicad_pro').write_text('{"changed":"GUI metadata or rules"}');(self.root/'review/project/board.kicad_prl').write_text('{}')
        result=self.choose();self.assertFalse(result['review_project_matches_recorded_candidate']);self.assertEqual(result['review_project_changes']['changed'],['board.kicad_pro']);self.assertEqual(result['review_project_changes']['added'],['board.kicad_prl']);self.assertFalse(result['routing_accepted']);self.assertTrue(result['fresh_native_validation_required'])
    def test_changed_review_board_blocks_accept_but_reject_is_persistent(self):
        self.review();(self.root/'review/project/board.kicad_pcb').write_text('(edited)')
        with self.assertRaisesRegex(Rejected,'board changed'):self.choose()
        result=self.choose('reject','reject');self.assertEqual(result['choice'],'reject');self.assertFalse(result['candidate_board_unchanged']);self.assertTrue((self.root/'review/project/board.kicad_pcb').exists())
    def test_unknown_choice_and_nonready_review_fail_before_output(self):
        self.review()
        with self.assertRaisesRegex(Rejected,'accept or reject'):self.choose(True)
        path=self.root/'review/review.json';record=json.loads(path.read_text());record['status']='cancelled';path.write_text(json.dumps(record))
        with self.assertRaisesRegex(Rejected,'ready review'):self.choose()
        self.assertFalse((self.root/'choice').exists())
    def test_stale_source_candidate_report_and_complete_evidence_fail(self):
        self.review()
        for path in (self.source/'board.kicad_pro',self.candidate/'board.kicad_dru',self.receipt,self.run/'new.json'):
            with self.subTest(path=path):
                old=path.read_bytes() if path.exists() else None;path.write_text('changed')
                with self.assertRaises((Rejected,ValueError)):self.choose()
                self.assertFalse((self.root/'choice').exists())
                if old is None:path.unlink()
                else:path.write_bytes(old)
    def test_escaped_review_project_or_symlink_never_inspected(self):
        self.review();path=self.root/'review/review.json';record=json.loads(path.read_text());record['project']=str(self.source);path.write_text(json.dumps(record))
        with self.assertRaisesRegex(Rejected,'identity'):self.choose()
    def test_mid_check_and_publication_mutations_invalidate_choice(self):
        self.review();verified=copy.deepcopy(self.check.return_value);self.check.reset_mock()
        def changing(_):
            if self.check.call_count==2:(self.root/'review/project/board.kicad_pro').write_text('changed')
            return verified
        self.check.side_effect=changing
        with self.assertRaisesRegex(Rejected,'material changed'):self.choose()
        record=json.loads((self.root/'choice/choice.json').read_text());self.assertFalse(record['choice_recorded']);self.assertEqual(record['status'],'rejected')
    def test_late_writer_tamper_does_not_leave_canonical_choice(self):
        self.review();save=h.save_json
        def changed(path,record):
            save(path,record)
            if record['status']=='disposition_recorded':path.write_text(json.dumps({**record,'choice':'reject'}))
        with patch.object(h,'save_json',changed),self.assertRaisesRegex(Rejected,'publication'):self.choose()
        record=json.loads((self.root/'choice/choice.json').read_text());self.assertFalse(record['choice_recorded']);self.assertTrue(list((self.root/'choice').glob('invalidated-choice-*')))
    def test_actual_self_sigterm_after_choice_restores_handlers_and_invalidates(self):
        self.review();prior={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)};save=h.save_json;sent=False
        def cancelled(path,record):
            nonlocal sent
            save(path,record)
            if record['status']=='disposition_recorded' and not sent:sent=True;os.kill(os.getpid(),signal.SIGTERM)
        with patch.object(h,'save_json',cancelled),self.assertRaisesRegex(Rejected,'cancelled'):self.choose()
        self.assertEqual({sig:signal.getsignal(sig) for sig in prior},prior);record=json.loads((self.root/'choice/choice.json').read_text());self.assertFalse(record['choice_recorded']);self.assertEqual(record['status'],'cancelled')
    def test_bound_preview_tampering_is_rejected_before_choice(self):
        self.review();folder=self.root/'review';shutil.copytree(self.source,folder/'before');html=folder/'preview.html';html.write_text('<html>pure boundary fixture</html>')
        path=folder/'review.json';record=json.loads(path.read_text());record['preview']={'plotter_sha256':sha(h.c.CLI),'input_trees':{},'files':{'preview.html':sha(html)}};path.write_text(json.dumps(record));html.write_text('tampered')
        with self.assertRaisesRegex(Rejected,'preview changed'):self.choose()
        self.assertFalse((self.root/'choice').exists())
    def test_missing_preview_contract_is_rejected_before_choice(self):
        self.review();(self.root/'review/preview.html').write_text('<html>unbound</html>')
        with self.assertRaisesRegex(Rejected,'preview binding'):self.choose()
        self.assertFalse((self.root/'choice').exists())
    def test_existing_or_protected_choice_destination_keeps_all_files(self):
        self.review();target=self.root/'choice';target.mkdir();(target/'keep').write_text('untouched')
        with self.assertRaises(Rejected):self.choose()
        self.assertEqual((target/'keep').read_text(),'untouched')
        with self.assertRaisesRegex(Rejected,'outside'):h.review_choice(self.root/'review/review.json',self.run/'choice','accept')
    def test_final_budget_crossing_invalidates_record(self):
        self.review();now=[0.0];save=h.save_json
        def late(path,record):
            save(path,record)
            if record['status']=='disposition_recorded':now[0]=31.0
        with patch.object(h,'cpu_seconds',side_effect=lambda:now[0]),patch.object(h,'save_json',late),self.assertRaisesRegex(Rejected,'ceiling'):self.choose()
        self.assertFalse(json.loads((self.root/'choice/choice.json').read_text())['choice_recorded'])
if __name__=='__main__':unittest.main()
