"""Constructed review-boundary regressions; actual Native/GUI qualification is separate."""
import json
import os
import stat
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import handoff as h, strategy as s, review_view as view, local_settings as local
from autorouter.pipeline import Rejected, sha
from tests import test_handoff as fixture


class Native7ReviewBoundaryTests(unittest.TestCase):
    def setUp(self):
        fixture.ReviewCopyTests.setUp(self)

    def not_ready(self,target):
        fixture.ReviewCopyTests.not_ready(self,target)

    def recognized(self,*_):
        self.assertEqual(self.check.call_count,1)  # Full central read precedes narrowing.
        return {'source-derived':'constructed boundary only'}

    def test_recognized_parent_keeps_two_full_reads_and_final_metadata_after_write(self):
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
        self.assertEqual(self.check.call_count,2)
        self.assertGreaterEqual(events.count('published'),2)
        self.assertEqual(events[-1],'published')
        self.assertEqual(h.SECONDS,30)

    def test_failed_first_full_read_never_reaches_source_recognition(self):
        self.check.return_value['current']=False
        with patch.object(s,'native7_parent') as recognize:
            with self.assertRaises(Rejected):h.review_copy(self.receipt,self.root/'review')
            recognize.assert_not_called()

    def test_receipt_marker_alone_cannot_select_narrower_callbacks(self):
        data=dict(self.data,native7_improve_parent={'policy':'forged'})
        self.receipt.write_text(json.dumps(data))
        with self.assertRaises(Rejected):h.review_copy(self.receipt,self.root/'review',render=True)
        self.assertEqual(self.check.call_count,0)
        self.assertFalse((self.root/'review').exists())

    def test_second_full_read_after_render_still_refuses_stale_parent(self):
        verified=dict(self.check.return_value);self.check.side_effect=[verified,Rejected('stale parent')]
        target=self.root/'review'
        with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=lambda *a,**kw:kw['material']()),patch.object(view,'render',return_value=None):
            with self.assertRaisesRegex(Rejected,'stale parent'):h.review_copy(self.receipt,target,render=True)
        self.not_ready(target)

    def test_render_callback_still_checks_all_source_bytes(self):
        target=self.root/'review'
        def rendered(destination,before,candidate,report,remaining,stable,**ctx):
            (self.source/'board.kicad_pro').write_text('changed original rules')
            stable()
        with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=lambda *a,**kw:kw['material']()),patch.object(view,'render',side_effect=rendered):
            with self.assertRaisesRegex(Rejected,'source project'):h.review_copy(self.receipt,target,render=True)
        self.not_ready(target)

    def test_late_publication_mutations_are_not_hidden_by_omitted_third_semantic_read(self):
        save=h.save_json;target=self.root/'review'
        def changed(path,record):
            save(path,record)
            if record['status']=='ready_for_manual_review':
                (self.candidate/'board.kicad_dru').write_text('relaxed after second full read')
        with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=lambda *a,**kw:kw['material']()),patch.object(h,'save_json',side_effect=changed):
            with self.assertRaises(Rejected):h.review_copy(self.receipt,target)
        self.assertEqual(self.check.call_count,2)
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
