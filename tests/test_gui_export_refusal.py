"""Regression for GUI060's generic stale-export refusal; no Native proof."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from autorouter import gui
from tests import test_gui as gt


class ExportRefusalTests(unittest.TestCase):
    setUp = gt.GuiWorkflowTests.setUp
    request = gt.GuiWorkflowTests.request
    flow = gt.GuiWorkflowTests.flow

    def test_real_cli_negative_shape_is_diagnostic_only(self):
        flow = self.flow()
        flow.ready.update(('review', 'export', 'verify_export'))
        flow.records['export'] = {'export_accepted': True}
        log = flow.workspace / 'inspect-export-owned.command.log'
        log.write_text(json.dumps({'current': False, 'reason': 'export inputs/runtime/evidence changed'}))
        before = (set(flow.ready), dict(flow.records))
        process = dict(cancel_requested=False, log_truncated=False, exit_code=2)
        with self.assertRaises(ValueError) as error:
            flow.adopt('verify_export', process, log)
        self.assertIn('changed after validation', str(error.exception))
        self.assertIn(str(log), str(error.exception))
        self.assertIn('fresh preview', str(error.exception))
        self.assertEqual((flow.ready, flow.records), before)

    def test_cancel_signal_or_truncation_takes_precedence_over_detail(self):
        flow = self.flow()
        for cancel, truncated, code in ((True, False, 2), (False, True, 2),
                                      (False, False, 130), (False, False, -15)):
            with self.subTest(cancel=cancel, truncated=truncated, code=code), \
                    patch.object(gui, 'read_record') as read, \
                    self.assertRaisesRegex(ValueError, 'failed or was cancelled'):
                flow.adopt('verify_export', dict(cancel_requested=cancel,
                    log_truncated=truncated, exit_code=code), flow.workspace / 'not-read')
            read.assert_not_called()

    def test_missing_malformed_or_positive_diagnostic_never_authorizes(self):
        flow = self.flow()
        log = flow.workspace / 'inspect-export-owned.command.log'
        for value in ({}, [], {'current': True, 'reason': 'success'},
                      {'current': 0, 'reason': 'stale'}, {'current': False},
                      {'current': False, 'reason': 3}):
            log.write_text(json.dumps(value))
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'failed or was cancelled'):
                flow.adopt('verify_export', dict(cancel_requested=False,
                    log_truncated=False, exit_code=2), log)
            self.assertFalse(flow.ready)
        log.write_text('{corrupt')
        self.assertIsNone(gui.failed_export_check_detail(log))
        self.assertIsNone(gui.failed_export_check_detail(log.with_name('missing')))

    def test_diagnostic_is_short_printable_and_never_opens_project(self):
        flow = self.flow()
        log = flow.workspace / 'inspect-export-owned.command.log'
        log.write_text(json.dumps({'current': False, 'reason': 'x\n\x1b' * 2000}))
        detail = gui.failed_export_check_detail(log)
        self.assertIn('[detail shortened]', detail)
        self.assertNotIn('\x1b', detail)
        self.assertIn(str(log), detail)
        window = SimpleNamespace(job=SimpleNamespace(cancel_requested=False), flow=flow,
            busy=True, inspected=Mock(), status=Mock(), log=Mock(), refresh=Mock(), closing=False)
        window.refused = lambda error: gt.window_method('refused')(window, error)
        with patch.object(gui.subprocess, 'Popen') as opener:
            gt.window_method('opened')(window, 'export', None, detail)
        opener.assert_not_called()
        self.assertIsNone(window.flow)
        self.assertIn(detail, window.log.SetValue.call_args.args[0])

