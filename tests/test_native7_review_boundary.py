"""Constructed review-boundary regressions; actual Native/GUI qualification is separate."""
import json
import shutil
import os
import stat
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from autorouter import handoff as h, strategy as s, review_view as view, local_settings as local
from autorouter.pipeline import Rejected, sha
from tests import test_handoff as fixture


class Native7ReviewBoundaryTests(unittest.TestCase):
    def setUp(self):
        fixture.ReviewCopyTests.setUp(self)
        # This handoff fixture has no real Improve Context. Isolate only that
        # prerequisite, retaining the actual operation policy fingerprint.
        guard=patch.object(h,'_review_validation_guard',side_effect=self.validation_guard)
        guard.start();self.addCleanup(guard.stop)

    def validation_guard(self,directory,report,identity,*,entry_owner=None):
        def check():
            if h._review_validation_identity()!=identity:
                raise Rejected('review validation policy changed in constructed Context seam')
        check()
        return check

    def not_ready(self,target):
        fixture.ReviewCopyTests.not_ready(self,target)

    def recognized(self,*_):
        self.assertEqual(self.check.call_count,1)  # Full central read precedes narrowing.
        return {'source-derived':'constructed boundary only'}

    def test_recognized_parent_keeps_one_full_read_and_final_metadata_after_write(self):
        target=self.root/'review';events=[]
        def guarded(*args,**kwargs):
            kwargs['material']()
            events.append('published' if (target/'review.json').exists() else 'metadata')
        def rendered(destination,before,candidate,report,remaining,stable,**ctx):
            count=len(events)
            for _ in range(4):stable()
            self.assertEqual(len(events),count)  # Byte custody, not repeated parent semantics.
            self.assertGreater(remaining(),0)
            return None
        with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=guarded),patch.object(view,'render',side_effect=rendered):
            record=h.review_copy(self.receipt,target,render=True)
        self.assertEqual(record['status'],'ready_for_manual_review')
        self.assertEqual(self.check.call_count,1)
        self.assertGreaterEqual(events.count('published'),1)
        self.assertEqual(events[-1],'published')
        self.assertEqual(h.SECONDS,30)

    def test_failed_first_full_read_never_reaches_source_recognition(self):
        self.check.return_value['current']=False
        with patch.object(s,'native7_parent') as recognize:
            with self.assertRaises(Rejected):h.review_copy(self.receipt,self.root/'review')
            recognize.assert_not_called()

    def test_selected_entry_keeps_all_final_guards_after_one_complete_read(self):
        target=self.root/'review';events=[]
        def guarded(*args,**kwargs):
            kwargs['material']();events.append('published' if (target/'review.json').exists() else 'final')
        def rendered(*args,**kwargs):
            self.assertEqual(self.check.call_count,1);self.assertEqual(events,[])
        with patch.object(s,'native7_marked',return_value=True),patch.object(s,'_native7_parent_policy'), \
                patch.object(s,'_native7_parent_shape'),patch.object(s,'native7_parent',side_effect=self.recognized), \
                patch.object(h,'delivery_guards',side_effect=guarded),patch.object(view,'render',side_effect=rendered):
            result=h.review_copy(self.receipt,target,render=True)
        self.assertEqual(result['status'],'ready_for_manual_review');self.assertEqual(events,['final','published'])

    def test_same_byte_routing_parent_replacement_during_initial_reader_refuses(self):
        target=self.root/'review';retained=self.root/'original-run';verified=dict(self.check.return_value)
        def replaced(*args,**kwargs):
            self.run.rename(retained);shutil.copytree(retained,self.run);return verified
        self.check.side_effect=replaced
        try:
            with patch.object(s,'native7_marked',return_value=True),patch.object(s,'_native7_parent_policy'), \
                    patch.object(s,'_native7_parent_shape'),patch.object(s,'native7_parent') as recognize:
                with self.assertRaises(Rejected):h.review_copy(self.receipt,target)
                recognize.assert_not_called()
            self.assertFalse(target.exists())
        finally:
            if retained.exists():shutil.rmtree(self.run);retained.rename(self.run)

    def test_receipt_marker_alone_cannot_select_narrower_callbacks(self):
        data=dict(self.data,native7_improve_parent={'policy':'forged'})
        self.receipt.write_text(json.dumps(data))
        with self.assertRaises(Rejected):h.review_copy(self.receipt,self.root/'review',render=True)
        self.assertEqual(self.check.call_count,0)
        self.assertFalse((self.root/'review').exists())

    def test_semantic_reader_replacement_during_render_is_rejected_without_file_change(self):
        target=self.root/'review'
        with ExitStack() as changes:
            def rendered(destination,before,candidate,report,remaining,stable,**ctx):
                changes.enter_context(patch.object(h.p,'_check_result_uncached',lambda *a,**kw:None))
                stable()
            with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=lambda *a,**kw:kw['material']()),patch.object(view,'render',side_effect=rendered):
                with self.assertRaisesRegex(Rejected,'policy changed'):h.review_copy(self.receipt,target,render=True)
        self.assertEqual(self.check.call_count,1)
        self.not_ready(target)

    def test_policy_replacement_during_first_full_read_refuses_before_copy(self):
        verified=dict(self.check.return_value)
        target=self.root/'review'
        with ExitStack() as changes:
            def checked(*args,**kwargs):
                changes.enter_context(patch.object(s,'check_single_selection',lambda *a,**kw:None))
                return verified
            self.check.side_effect=checked
            with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=lambda *a,**kw:kw['material']()):
                with self.assertRaisesRegex(Rejected,'policy changed'):h.review_copy(self.receipt,target)
        self.assertEqual(self.check.call_count,1)
        self.assertFalse(target.exists())

    def test_render_callback_still_checks_all_source_bytes(self):
        target=self.root/'review'
        def rendered(destination,before,candidate,report,remaining,stable,**ctx):
            (self.source/'board.kicad_pro').write_text('changed original rules')
            stable()
        with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=lambda *a,**kw:kw['material']()),patch.object(view,'render',side_effect=rendered):
            with self.assertRaisesRegex(Rejected,'source project'):h.review_copy(self.receipt,target,render=True)
        self.not_ready(target)

    def test_in_memory_report_cannot_change_while_receipt_bytes_stay_same(self):
        target=self.root/'review';raw=self.receipt.read_bytes()
        def rendered(destination,before,candidate,report,remaining,stable,**ctx):
            report['native']={'warnings':0,'findings':[]}
            stable()
        with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=lambda *a,**kw:kw['material']()),patch.object(view,'render',side_effect=rendered):
            with self.assertRaisesRegex(Rejected,'in-memory'):
                h.review_copy(self.receipt,target,render=True)
        self.assertEqual(self.receipt.read_bytes(),raw)
        self.assertEqual(self.check.call_count,1)
        self.not_ready(target)

    def test_late_publication_mutations_are_not_hidden_by_one_semantic_read(self):
        save=h.save_json;target=self.root/'review'
        def changed(path,record):
            save(path,record)
            if record['status']=='ready_for_manual_review':
                (self.candidate/'board.kicad_dru').write_text('relaxed after initial full read')
        with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=lambda *a,**kw:kw['material']()),patch.object(h,'save_json',side_effect=changed):
            with self.assertRaises(Rejected):h.review_copy(self.receipt,target)
        self.assertEqual(self.check.call_count,1)
        self.not_ready(target)

    @unittest.skipUnless(sys.platform=='darwin' and hasattr(os,'chflags'),'actual Mac file flags required')
    def test_flag_only_change_during_render_is_rejected_by_immediate_full_metadata_fence(self):
        native=self.run/'final-drc-input';native.mkdir();prl=native/'board.kicad_prl';prl.write_text('{}')
        before={prl.name:sha(prl)}
        event=dict(policy=local.POLICY,present=True,path=str(prl),sha256=before[prl.name],flags_before=0,flags_during=stat.UF_IMMUTABLE,flags_restored=True,bytes_unchanged=True)
        def guarded(*a,**kw):
            kw['material']();local.check_preserved(prl,before,event)
        def rendered(destination,source,candidate,report,remaining,stable,**ctx):
            os.chflags(prl,stat.UF_IMMUTABLE,follow_symlinks=False)
            stable()  # Bytes unchanged; full metadata must still refuse before readiness.
            return None
        target=self.root/'review'
        try:
            with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=guarded),patch.object(view,'render',side_effect=rendered):
                with self.assertRaisesRegex(Rejected,'flags'):h.review_copy(self.receipt,target,render=True)
            self.not_ready(target)
        finally:os.chflags(prl,0,follow_symlinks=False)
