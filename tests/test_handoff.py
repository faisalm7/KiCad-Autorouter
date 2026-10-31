"""Filesystem safety controls; these are not native validation evidence."""
import json
import copy
import os
import signal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import handoff as h
from autorouter.handoff import review_copy
from autorouter.pipeline import Rejected, sha

class ReviewCopyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent);self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.source=self.root/'source';self.source.mkdir()
        self.run=self.root/'run';self.run.mkdir();self.candidate=self.run/'candidate';self.candidate.mkdir()
        (self.candidate/'board.kicad_pcb').write_text('(kicad_pcb)')
        (self.candidate/'board.kicad_pro').write_text('{}')
        (self.candidate/'board.kicad_dru').write_text('(version 1)')
        (self.source/'board.kicad_pcb').write_text('(original)')
        (self.source/'board.kicad_pro').write_text('{}')
        self.receipt=self.run/'result.json'
        self.data={'schema':1,'source':str(self.source/'board.kicad_pcb'),'candidate':str(self.candidate/'board.kicad_pcb'),'candidate_sha256':sha(self.candidate/'board.kicad_pcb')}
        self.receipt.write_text(json.dumps(self.data))
        self.check=patch('autorouter.handoff.check_result',return_value={'current':True,'applied':False,'candidate':str(self.candidate/'board.kicad_pcb'),'candidate_sha256':sha(self.candidate/'board.kicad_pcb')}).start();self.addCleanup(patch.stopall)
    def test_complete_copy_without_altering_run(self):
        target=self.root/'review';result=review_copy(self.receipt,target)
        self.assertEqual((target/'project/board.kicad_pcb').read_bytes(),(self.candidate/'board.kicad_pcb').read_bytes())
        self.assertEqual((target/'project/board.kicad_pro').read_bytes(),b'{}')
        self.assertEqual(result['status'],'ready_for_manual_review');self.assertEqual(self.check.call_count,3);self.assertIs(result['native_validation_performed'],False);self.assertTrue(result['within_budget'])
    def test_no_existing_destination(self):
        target=self.root/'review';target.mkdir();(target/'keep').write_text('untouched')
        with self.assertRaises(Rejected):review_copy(self.receipt,target)
        self.assertEqual((target/'keep').read_text(),'untouched')
    def test_no_copy_inside_source_or_run(self):
        for target in (self.source/'review',self.run/'review'):
            with self.assertRaises(Rejected):review_copy(self.receipt,target)
            self.assertFalse(target.exists())
    def test_no_symlink_ancestor(self):
        (self.root/'link').symlink_to(self.root/'source',target_is_directory=True)
        with self.assertRaises(Rejected):review_copy(self.receipt,self.root/'link/review')
    def test_stale_second_check_never_emits_ready_receipt(self):
        self.check.side_effect=[{'current':True,'applied':False,'candidate':str(self.candidate/'board.kicad_pcb'),'candidate_sha256':sha(self.candidate/'board.kicad_pcb')},Rejected('stale')]
        target=self.root/'review'
        with self.assertRaises(Rejected):review_copy(self.receipt,target)
        self.not_ready(target)

    def test_changed_valid_receipt_during_copy_is_rejected(self):
        verified={'current':True,'applied':False,'candidate':str(self.candidate/'board.kicad_pcb'),'candidate_sha256':sha(self.candidate/'board.kicad_pcb')}
        def second_check(_):
            if self.check.call_count == 2:
                self.receipt.write_text(self.receipt.read_text()+' ')
            return verified
        self.check.side_effect=second_check
        target=self.root/'review'
        with self.assertRaises(Rejected):review_copy(self.receipt,target)
        self.not_ready(target)

    def not_ready(self,target):
        path=target/'review.json'
        if path.exists():self.assertNotEqual(json.loads(path.read_text()).get('status'),'ready_for_manual_review')
    def update_receipt(self,**values):
        self.data.update(values);self.receipt.write_text(json.dumps(self.data))
    def inject_check(self,callback,at=2):
        verified=copy.deepcopy(self.check.return_value)
        def checking(_):
            if self.check.call_count==at:callback()
            return copy.deepcopy(verified)
        self.check.side_effect=checking
    def test_complete_copied_project_and_rules_rechecked_after_second_validator(self):
        for name in ('board.kicad_pro','board.kicad_dru'):
            with self.subTest(name=name):
                target=self.root/('review-'+name)
                self.check.reset_mock();self.inject_check(lambda:(target/'project'/name).write_text('relaxed rules'))
                with self.assertRaisesRegex(Rejected,'copied project'):review_copy(self.receipt,target)
                self.not_ready(target)
    def test_whole_source_evidence_and_candidate_rechecked_after_validator(self):
        for path in (self.source/'board.kicad_pro',self.candidate/'board.kicad_dru',self.run/'extra.json'):
            with self.subTest(path=path):
                existed=path.exists();before=path.read_bytes() if existed else None
                target=self.root/('review-'+path.parent.name+'-'+path.name)
                self.check.reset_mock();self.inject_check(lambda:path.write_bytes(b'changed'))
                with self.assertRaises(Rejected):review_copy(self.receipt,target)
                self.not_ready(target)
                if existed:path.write_bytes(before)
                else:path.unlink()
    def test_late_checker_changes_all_material_are_rejected(self):
        for kind in ('source','candidate','copy','evidence','receipt'):
            with self.subTest(kind=kind):
                target=self.root/('review-'+kind)
                path={'source':self.source/'board.kicad_pro','candidate':self.candidate/'board.kicad_dru','copy':target/'project/board.kicad_pro','evidence':self.run/'extra.json','receipt':self.receipt}[kind]
                existed=path.exists();before=path.read_bytes() if existed else None
                self.check.reset_mock();self.inject_check(lambda:path.write_bytes(b'changed'),at=3)
                with self.assertRaises(Rejected):review_copy(self.receipt,target)
                self.not_ready(target);self.assertTrue(list(target.glob('invalidated-review-*')))
                if existed:path.write_bytes(before)
                elif path.exists():path.unlink()
    def test_policy_candidate_or_hash_return_switch_rejected(self):
        for key,value in (('input_policy',h.pc.POLICY),('candidate',str(self.source/'board.kicad_pcb')),('candidate_sha256','0'*64),('current',False),('applied',True)):
            with self.subTest(key=key):
                base=copy.deepcopy(self.check.return_value);changed={**base,key:value}
                self.check.side_effect=[base,changed];target=self.root/('review-'+key)
                with self.assertRaisesRegex(Rejected,'central receipt'):review_copy(self.receipt,target)
                self.not_ready(target)
    def test_schema2_unknown_and_diagnostic_remain_blocked(self):
        values=[{'schema':2,'input_policy':'board-floors-v1','adapter':'both','scope':'whole_board_unlocked_routing','baseline':'B1','scoring_variant':None},
                {'schema':1,'input_policy':'unknown'},{'schema':1,'diagnostic_schema':1}]
        for index,value in enumerate(values):
            with self.subTest(value=value):
                base=copy.deepcopy(self.data);self.update_receipt(**value);self.check.reset_mock();target=self.root/('review-'+str(index))
                with self.assertRaises(Rejected):review_copy(self.receipt,target)
                self.check.assert_not_called();self.assertFalse(target.exists());self.data=base;self.receipt.write_text(json.dumps(base))
    def test_schema3_correct_central_policy_admitted(self):
        self.update_receipt(schema=3,input_policy=h.pc.POLICY,adapter='both',scope='whole_board_unlocked_routing',baseline='completion_only_probe',engine_profile='completion-only',scoring_variant='via_default',planning_parameters=h.pc.parameters())
        self.check.return_value['input_policy']=h.pc.POLICY;target=self.root/'review'
        result=review_copy(self.receipt,target)
        self.assertEqual(result['source_receipt_schema'],3);self.assertEqual(result['input_policy'],h.pc.POLICY)
        self.assertEqual(result['initial_project_hashes'],h.pc.inventory(self.candidate));self.assertFalse(result['native_validation_performed'])
    def test_schema3_downgrade_or_missing_policy_never_infers_native(self):
        for value in ({'schema':3},{'schema':1,'planning_parameters':h.pc.parameters()}):
            with self.subTest(value=value):
                self.update_receipt(**value)
                with self.assertRaises(Rejected):review_copy(self.receipt,self.root/'review')
                self.assertFalse((self.root/'review').exists())
    def test_receipt_duplicate_and_nonfinite_rejected_before_checker(self):
        original=self.receipt.read_text()
        for tail in (',"schema":1}',',"extra":NaN}'):
            self.receipt.write_text(original[:-1]+tail)
            with self.assertRaises(Rejected):review_copy(self.receipt,self.root/'review')
        self.check.assert_not_called()
    def test_size_and_entry_bounds_precede_legacy_checker(self):
        with patch.object(h,'EVIDENCE_BYTES',8):
            with self.assertRaises(Rejected):review_copy(self.receipt,self.root/'review')
        self.check.assert_not_called();self.assertFalse((self.root/'review').exists())
        real=h.pc.inventory
        def restricted(path,**kwargs):return real(path,**{**kwargs,'max_entries':1})
        with patch.object(h.pc,'inventory',restricted):
            with self.assertRaisesRegex(Rejected,'entry ceiling'):review_copy(self.receipt,self.root/'review')
        self.check.assert_not_called()
    def test_capture_growth_rejected_before_central_checker(self):
        real=h.pc.inventory
        def capture(path,**kwargs):
            result=real(path,**kwargs)
            if kwargs.get('contents'):(self.candidate/'board.kicad_pro').write_text('grew')
            return result
        with patch.object(h.pc,'inventory',capture):
            with self.assertRaises(Rejected):review_copy(self.receipt,self.root/'review')
        self.check.assert_not_called();self.assertFalse((self.root/'review').exists())
    def test_receipt_symlink_rejected_without_resolution(self):
        link=self.run/'alias.json';link.symlink_to(self.receipt)
        with self.assertRaisesRegex(Rejected,'symlink'):review_copy(link,self.root/'review')
        self.check.assert_not_called()
    def test_runtime_change_after_check_rejected(self):
        real=h.runtime_inventory;calls=0
        def changed():
            nonlocal calls
            calls+=1;value=real()
            if self.check.call_count>=2:value['injected.py']='a'*64
            return value
        with patch.object(h,'runtime_inventory',changed):
            with self.assertRaisesRegex(Rejected,'runtime source'):review_copy(self.receipt,self.root/'review')
        self.not_ready(self.root/'review')
    def publication_case(self,callback):
        target=self.root/'review';save=h.save_json;fired=False
        def wrapper(path,record):
            nonlocal fired
            save(path,record)
            if record['status']=='ready_for_manual_review' and not fired:
                fired=True;callback(path,record,target)
        with patch.object(h,'save_json',wrapper):
            with self.assertRaises((Rejected,OSError)):review_copy(self.receipt,target)
        self.not_ready(target);return target
    def test_after_ready_save_source_change_invalidates(self):
        target=self.publication_case(lambda *_:(self.source/'board.kicad_pro').write_text('changed'))
        self.assertTrue(list(target.glob('invalidated-review-*')))
    def test_after_ready_save_copy_change_invalidates(self):
        self.publication_case(lambda path,record,target:(target/'project/board.kicad_dru').write_text('changed'))
    def test_after_ready_save_record_change_invalidates(self):
        self.publication_case(lambda path,record,target:path.write_text(json.dumps({**record,'candidate_sha256':'0'*64})))
    def test_writer_mutating_returned_record_invalidates(self):
        self.publication_case(lambda path,record,target:record.update(candidate_sha256='0'*64))
    def test_actual_self_signals_after_ready_restore_handlers(self):
        for sig in (signal.SIGINT,signal.SIGTERM):
            with self.subTest(sig=sig):
                before={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
                target=self.publication_case(lambda *_:os.kill(os.getpid(),sig))
                self.assertEqual(json.loads((target/'review.json').read_text())['status'],'cancelled')
                self.assertEqual({s:signal.getsignal(s) for s in before},before)
                target.rename(self.root/('review-'+str(sig)))
    def test_failed_corrective_write_retains_no_ready_canonical(self):
        target=self.root/'review';save=h.save_json;calls=0
        def broken(path,record):
            nonlocal calls
            calls+=1
            if calls==1:save(path,record);raise KeyboardInterrupt
            save(path.with_name(path.name+'.partial'),record);raise OSError('corrective failed')
        with patch.object(h,'save_json',broken):
            with self.assertRaisesRegex(Rejected,'cancelled'):review_copy(self.receipt,target)
        self.assertFalse((target/'review.json').exists());self.assertFalse((target/'review.json.partial').exists());self.assertEqual(len(list(target.glob('invalidated-review-*'))),2)
    def test_initial_partial_write_interruption_retained(self):
        target=self.root/'review';save=h.save_json;calls=0
        def partial(path,record):
            nonlocal calls
            calls+=1
            if calls==1:save(path.with_name(path.name+'.partial'),record);raise KeyboardInterrupt
            save(path,record)
        with patch.object(h,'save_json',partial):
            with self.assertRaisesRegex(Rejected,'cancelled'):review_copy(self.receipt,target)
        self.not_ready(target);self.assertTrue(list(target.glob('invalidated-review-*partial')))
    def test_final_cpu_cap_invalidates_ready(self):
        now=[0.0];real=h.save_json
        def save(path,record):
            real(path,record)
            if record['status']=='ready_for_manual_review':now[0]=float(h.REVIEW_SECONDS+1)
        with patch.object(h,'cpu_seconds',side_effect=lambda:now[0]),patch.object(h,'save_json',save):
            with self.assertRaisesRegex(Rejected,'CPU ceiling'):review_copy(self.receipt,self.root/'review')
        self.not_ready(self.root/'review')
    def test_child_cpu_is_counted(self):
        import types
        with patch.object(h.resource,'getrusage',side_effect=[types.SimpleNamespace(ru_utime=1,ru_stime=2),types.SimpleNamespace(ru_utime=3,ru_stime=4)]):
            self.assertEqual(h.cpu_seconds(),10)

    def test_final_wall_cap_invalidates_ready(self):
        now=[0.0];real=h.save_json
        def save(path,record):
            real(path,record)
            if record['status']=='ready_for_manual_review':now[0]=float(h.REVIEW_SECONDS+1)
        with patch.object(h.time,'monotonic',side_effect=lambda:now[0]),patch.object(h,'save_json',save):
            with self.assertRaisesRegex(Rejected,'wall or full CPU'):review_copy(self.receipt,self.root/'review')
        self.not_ready(self.root/'review')

    def test_final_material_callback_cannot_change_canonical_ready(self):
        target=self.root/'review';real=h.runtime_inventory;after_last_check=0;injected=False
        def checking():
            nonlocal after_last_check,injected
            result=real()
            if self.check.call_count==3:
                after_last_check+=1
                if after_last_check==2:
                    path=target/'review.json';data=json.loads(path.read_text());data['candidate_sha256']='0'*64;path.write_text(json.dumps(data));injected=True
            return result
        with patch.object(h,'runtime_inventory',checking):
            with self.assertRaisesRegex(Rejected,'final material'):review_copy(self.receipt,target)
        self.assertTrue(injected);self.not_ready(target);self.assertTrue(list(target.glob('invalidated-review-*')))
