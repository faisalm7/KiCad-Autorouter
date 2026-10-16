"""GUI013 preview refusal presentation controls; no wx/Native qualification."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from autorouter import gui
from tests import test_gui as gt


class PreviewRefusalTests(unittest.TestCase):
    setUp = gt.GuiWorkflowTests.setUp
    request = gt.GuiWorkflowTests.request
    flow = gt.GuiWorkflowTests.flow

    reason = ('unsupported: schematic class intent not qualified: schematic '
              'netclass_flag unsupported: PCB class membership and inheritance '
              'are not independently verified: owned-four-copper-forced-inner.kicad_sch')

    def rejection_log(self, flow, reason=None):
        path = flow.workspace / 'preview.command.log'
        path.write_text(json.dumps({'status': 'rejected', 'reason': self.reason if reason is None else reason}))
        return path

    def test_route_and_improve_rejection_reason_is_diagnostic_only(self):
        for method in ('route', 'improve'):
            with self.subTest(method=method):
                self.settings = dict(self.settings, profile='tuned', adapter='both')
                flow = self.request(method=method).prepare()
                log = self.rejection_log(flow)
                before = (set(flow.ready), dict(flow.records), flow.choice)
                with self.assertRaises(ValueError) as error:
                    flow.adopt('preview', dict(cancel_requested=False, log_truncated=False, exit_code=2), log)
                text = str(error.exception)
                self.assertIn(self.reason, text)
                self.assertIn('fresh preview', text)
                self.assertIn('No preview or candidate was accepted', text)
                self.assertIn('Full failure log: ' + str(log), text)
                self.assertEqual((flow.ready, flow.records, flow.choice), before)

    def test_cancel_signal_or_truncation_skips_diagnostic(self):
        flow = self.flow(); log = self.rejection_log(flow)
        for cancel, truncated, code in ((True, False, 2), (False, True, 2),
                                       (False, False, 130), (False, False, 143),
                                       (False, False, -2), (False, False, -15)):
            with self.subTest(cancel=cancel, truncated=truncated, code=code), \
                    patch.object(gui, 'read_record') as read, \
                    self.assertRaisesRegex(ValueError, 'failed or was cancelled'):
                flow.adopt('preview', dict(cancel_requested=cancel, log_truncated=truncated, exit_code=code), log)
            read.assert_not_called()
            self.assertFalse(flow.ready); self.assertFalse(flow.records)

    def test_only_exact_preview_exit_two_reads_preview_detail(self):
        flow = self.flow(); log = self.rejection_log(flow)
        for code in (1, 3, 2.0, '2', None, True):
            with self.subTest(code=code), patch.object(gui, 'failed_preview_detail') as detail, \
                    self.assertRaisesRegex(ValueError, 'failed or was cancelled'):
                flow.adopt('preview', dict(cancel_requested=False, log_truncated=False, exit_code=code), log)
            detail.assert_not_called()
        for stage in ('route', 'review', 'choice', 'export', 'verify_export', 'unknown'):
            with self.subTest(stage=stage), patch.object(gui, 'failed_preview_detail') as detail, \
                    self.assertRaisesRegex(ValueError, 'failed or was cancelled'):
                flow.adopt(stage, dict(cancel_requested=False, log_truncated=False, exit_code=2), log)
            detail.assert_not_called()

    def test_unknown_positive_conflicting_or_malformed_shape_stays_generic(self):
        flow = self.flow(); log = self.rejection_log(flow)
        values = ({}, [], {'status': 'preview', 'reason': 'success'},
                  {'status': 'cancelled', 'reason': 'cancelled'},
                  {'status': 'rejected'}, {'status': 'rejected', 'reason': 3},
                  {'status': 'rejected', 'reason': '  '},
                  {'status': 'rejected', 'reason': 'unsafe', 'accepted': True},
                  {'status': 'rejected', 'reason': 'unknown shape', 'extra': 1})
        for value in values:
            log.write_text(json.dumps(value))
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'failed or was cancelled'):
                flow.adopt('preview', dict(cancel_requested=False, log_truncated=False, exit_code=2), log)
            self.assertFalse(flow.ready); self.assertFalse(flow.records)
        for raw in ('{corrupt', '{"status":"rejected","reason":"one","reason":"two"}',
                    '{"status":"rejected","reason":NaN}', 'diagnostic\n{"status":"rejected","reason":"no"}'):
            log.write_text(raw)
            with self.subTest(raw=raw): self.assertIsNone(gui.failed_preview_detail(log))
        self.assertIsNone(gui.failed_preview_detail(log.with_name('missing')))

    def test_reason_is_short_printable_and_empty_controls_remain_generic(self):
        flow = self.flow(); log = self.rejection_log(flow, 'x\n\x1b' * 2000)
        text = gui.failed_preview_detail(log)
        self.assertIn('[detail shortened]', text)
        self.assertNotIn('\x1b', text)
        self.assertIn(str(log), text)
        self.assertLess(len(text), gui.FAILURE_REASON_LIMIT + len(str(log)) + 300)
        log = self.rejection_log(flow, '\n\x1b\t')
        self.assertIsNone(gui.failed_preview_detail(log))

    def test_stale_saved_source_takes_precedence_over_diagnostic(self):
        flow = self.flow(); log = self.rejection_log(flow)
        self.board.with_suffix('.kicad_pro').write_bytes(b'changed saved project\n')
        with patch.object(gui, 'read_record') as read, \
                self.assertRaisesRegex(ValueError, 'Saved source project changed'):
            flow.adopt('preview', dict(cancel_requested=False, log_truncated=False, exit_code=2), log)
        read.assert_not_called()
        self.assertFalse(flow.ready); self.assertFalse(flow.records)

    def test_actual_finished_callback_shows_reason_and_discards_prior_ui_state(self):
        flow = self.flow(); log = self.rejection_log(flow)
        flow.ready.update(('preview', 'route'))
        flow.records['route'] = {'accepted': True}
        with self.assertRaises(ValueError) as error:
            flow.adopt('preview', dict(cancel_requested=False, log_truncated=False, exit_code=2), log)
        job = gui.CliJob()
        window = SimpleNamespace(job=job, flow=flow, busy=True, inspected=Mock(),
            status=Mock(), log=Mock(), refresh=Mock(), closing=False)
        window.refused = lambda message: gt.window_method('refused')(window, message)
        with patch.object(gui.subprocess, 'Popen') as opener:
            gt.window_method('finished')(window, job, None, 'preview', None, str(error.exception))
        opener.assert_not_called()
        self.assertIsNone(window.flow); self.assertIsNone(window.job)
        self.assertFalse(flow.ready); self.assertFalse(flow.records)
        self.assertIsNone(flow.choice)
        text = window.log.SetValue.call_args.args[0]
        self.assertIn(self.reason, text)
        self.assertIn('fresh preview', text)
        self.assertIn(str(log), text)
        self.assertIn('No positive state adopted', text)
        self.assertNotIn('Status: preview', text)


if __name__ == '__main__': unittest.main()
