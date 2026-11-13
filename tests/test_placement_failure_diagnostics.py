"""Refused attempts remain refused while preserving their concrete explanation."""
import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from autorouter import placement, placement_gui as pg, placement_intent as intent
from tests import test_placement_gui as gui_fixture
from tests.test_placement_gui import window_method


class FailureDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='placement-failure-diagnostics-')
        self.addCleanup(temp.cleanup); self.root = Path(temp.name).resolve()
        (self.root/'work').mkdir(); self.path = self.root/'work/result.json'
        self.binding = 'a'*64
        self.record = dict(schema=1, kind=placement.KIND, status='failed', placement_qualified=False,
            binding_sha256=self.binding, reason='Native refusal: two new silkscreen findings',
            **{key:False for key in placement.AUTHORITY})

    def write(self, value):
        self.path.write_text(json.dumps(value))

    def test_bound_negative_worker_reason_is_diagnostic_only_and_byte_preserving(self):
        self.write(self.record); before = self.path.read_bytes()
        result = placement._worker_refusal(self.root, self.binding)
        self.assertEqual(result['reason'], self.record['reason'])
        self.assertTrue(result['diagnostic_only']); self.assertFalse(result['grants_approval'])
        self.assertEqual(self.path.read_bytes(), before)

    def test_positive_corrupt_wrong_binding_or_authority_cannot_be_negative_proof(self):
        for key,value in [('status','pending_candidate'),('placement_qualified',True),('accepted',True),
                          ('binding_sha256','b'*64),('schema',True),('reason','x'*4097),
                          ('reason','injected\x00reason'),('kind','another-tool')]:
            row=copy.deepcopy(self.record);row[key]=value;self.write(row)
            with self.subTest(key=key):self.assertIsNone(placement._worker_refusal(self.root,self.binding))
        self.path.write_text('{')
        self.assertIsNone(placement._worker_refusal(self.root,self.binding))
        self.path.unlink();self.assertIsNone(placement._worker_refusal(self.root,self.binding))
        other=self.root/'elsewhere';other.write_text(json.dumps(self.record));self.path.symlink_to(other)
        self.assertIsNone(placement._worker_refusal(self.root,self.binding))

    def test_context_zone_and_protection_limits_survive_rebuild_presentation(self):
        inspection=dict(observation=dict(scope=intent.contract.CONTEXT_SCOPE),limitations=list(intent.CONTEXT_LIMITS))
        text='\n'.join(pg.placement_limits(inspection,rebuild=True))
        self.assertIn('derived fill may change',text)
        self.assertIn('protected nets with copper pours are refused',text)
        self.assertIn('exact affected-copper plan requires review',text)
        self.assertNotIn('preserved copper/zone movement boundaries still apply',text)

    def test_GUI_reports_negative_reason_without_adopting_or_opening_candidate(self):
        for record,expected in [(dict(status='failed',placement_qualified=False,
                                     reason='Native refusal: silk_overlap'), 'silk_overlap'),
                                (dict(status='pending_candidate',placement_qualified=True,
                                      reason='claimed positive'), 'did not complete'),
                                ([], 'did not complete')]:
            window=gui_fixture.PlacementGuiTests().window();window.start=Mock();window.owned_workspace=Mock(return_value=self.root)
            window.gate.review.decision=Mock(return_value={'choice':'reviewed_draft'})
            window_method('qualify_draft')(window,None)
            action=window.start.call_args.args[1];job=Mock()
            job.run.return_value=dict(exit_code=2,log_truncated=False,cancel_requested=False)
            with self.subTest(record=record), patch.object(pg,'write_new_json',return_value=self.root/'draft.json'), \
                    patch.object(pg,'qualification_command',return_value=['owned-test-CLI']), \
                    patch.object(pg.gui,'read_record',return_value=record), \
                    patch.object(placement,'check') as check, \
                    self.assertRaisesRegex(ValueError,expected):
                action(job,threading.Event())
            check.assert_not_called();self.assertIsNone(window.qualified)


if __name__=='__main__':unittest.main()
