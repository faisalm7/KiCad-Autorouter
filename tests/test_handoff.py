"""Filesystem safety controls; these are not native validation evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter.handoff import review_copy
from autorouter.pipeline import Rejected, sha

class ReviewCopyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.source=self.root/'source';self.source.mkdir()
        self.run=self.root/'run';self.run.mkdir();self.candidate=self.run/'candidate';self.candidate.mkdir()
        (self.candidate/'board.kicad_pcb').write_text('(kicad_pcb)')
        (self.candidate/'board.kicad_pro').write_text('{}')
        self.receipt=self.run/'result.json';self.receipt.write_text(json.dumps({'source':str(self.source/'board.kicad_pcb')}))
        self.check=patch('autorouter.handoff.check_result',return_value={'candidate':str(self.candidate/'board.kicad_pcb'),'candidate_sha256':sha(self.candidate/'board.kicad_pcb')}).start();self.addCleanup(patch.stopall)
    def test_complete_copy_without_altering_run(self):
        target=self.root/'review';result=review_copy(self.receipt,target)
        self.assertEqual((target/'project/board.kicad_pcb').read_bytes(),(self.candidate/'board.kicad_pcb').read_bytes())
        self.assertEqual((target/'project/board.kicad_pro').read_bytes(),b'{}')
        self.assertEqual(result['status'],'ready_for_manual_review');self.assertEqual(self.check.call_count,2)
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
        self.check.side_effect=[{'candidate':str(self.candidate/'board.kicad_pcb'),'candidate_sha256':sha(self.candidate/'board.kicad_pcb')},Rejected('stale')]
        target=self.root/'review'
        with self.assertRaises(Rejected):review_copy(self.receipt,target)
        self.assertFalse((target/'review.json').exists())

    def test_changed_valid_receipt_during_copy_is_rejected(self):
        verified={'candidate':str(self.candidate/'board.kicad_pcb'),'candidate_sha256':sha(self.candidate/'board.kicad_pcb')}
        def second_check(_):
            if self.check.call_count == 2:
                self.receipt.write_text(self.receipt.read_text()+' ')
            return verified
        self.check.side_effect=second_check
        target=self.root/'review'
        with self.assertRaises(Rejected):review_copy(self.receipt,target)
        self.assertFalse((target/'review.json').exists())
