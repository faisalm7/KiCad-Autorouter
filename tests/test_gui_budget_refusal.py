"""Prospective GUI operational-floor/failed-diagnostic controls; no Native proof."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch
from autorouter import gui, preferences as pref
from tests import test_gui as gt


class GuiBudgetTests(unittest.TestCase):
    setUp = gt.GuiWorkflowTests.setUp
    request = gt.GuiWorkflowTests.request
    flow = gt.GuiWorkflowTests.flow

    def test_actual_config_captures_displayed_text_instead_of_cached_spin_integer(self):
        control = Mock(); control.GetTextValue.return_value = '60'; control.GetValue.return_value = 120
        window = SimpleNamespace(choices={}, seconds=control)
        settings = gt.window_method('config')(window)
        self.assertEqual(settings['seconds'], 60)
        control.GetValue.assert_not_called()
        with self.assertRaisesRegex(ValueError, '90 seconds'): gui.check_improve_settings(dict(settings, profile='tuned'))

    def test_actual_config_refuses_invalid_visible_budget(self):
        for text in ('', 'NaN', '60.5', '9001', '-1', '0'):
            control = Mock(); control.GetTextValue.return_value = text; control.GetValue.return_value = 120
            with self.subTest(text=text), self.assertRaises(ValueError):
                gt.window_method('config')(SimpleNamespace(choices={}, seconds=control))
            control.GetValue.assert_not_called()

    def test_improve_60_refuses_before_workspace_and_90_preserves_exact_budget(self):
        for seconds in (60, 90):
            settings = dict(self.settings, profile='tuned', seconds=seconds, scoring_preference='via_high')
            request = gui.Request(str(self.board), str(self.output), json.dumps(settings), True, 'improve')
            if seconds == 60:
                with self.assertRaisesRegex(ValueError, '90 seconds'): request.prepare()
                self.assertEqual(list(self.output.iterdir()), [])
            else:
                flow = request.prepare()
                self.assertEqual(json.loads(flow.settings_bytes), settings)
        from autorouter.strategy import pruning_scope
        self.assertEqual(pruning_scope(dict(pref.DEFAULTS, profile='tuned', seconds=60))['seconds'], 60)
        self.assertEqual(gui.improve_preset(dict(pref.DEFAULTS, seconds=90))['seconds'], 90)
        with self.assertRaisesRegex(ValueError, '90 seconds'): gui.improve_preset(dict(pref.DEFAULTS, seconds=60))

    def test_failure_reason_bound_no_positive_adoption_and_cancel_precedence(self):
        flow = self.flow(); log = flow.workspace / 'route.command.log'
        path = flow.workspace / 'route/result.json'
        failed = dict(status='incumbent_rejected', accepted=False,
            reason='Rejected: insufficient remaining budget for engine grace and native finalization reserves')
        with patch.object(gui, 'read_record', return_value=failed) as read:
            with self.assertRaises(ValueError) as got:
                flow.adopt('route', dict(cancel_requested=False, exit_code=2, log_truncated=False), log)
            self.assertIn(failed['reason'], str(got.exception)); self.assertIn(str(path), str(got.exception))
            self.assertIn('No candidate accepted', str(got.exception)); self.assertFalse(flow.ready)
            read.reset_mock()
            for cancel, truncated in ((True, False), (False, True)):
                with self.assertRaisesRegex(ValueError, 'failed or was cancelled'):
                    flow.adopt('route', dict(cancel_requested=cancel, exit_code=2, log_truncated=truncated), log)
                read.assert_not_called()
            for code in (130, 143, -2, -15, -9):
                with self.subTest(exit_code=code), self.assertRaisesRegex(ValueError, 'failed or was cancelled'):
                    flow.adopt('route', dict(cancel_requested=False, exit_code=code, log_truncated=False), log)
                read.assert_not_called()
        with patch.object(gui, 'read_record', return_value=dict(failed, reason='x'*2000)):
            detail = gui.failed_route_detail(path)
        self.assertIn('[detail shortened]', detail); self.assertIn(str(path), detail)
        self.assertNotIn('x'*(gui.FAILURE_REASON_LIMIT+1), detail)

    def test_missing_corrupt_or_positive_failure_receipt_falls_back(self):
        flow = self.flow(); process = dict(cancel_requested=False, exit_code=2, log_truncated=False)
        for row in ([], {}, dict(status='routing_accepted', accepted=True, reason='forged'),
                    dict(status='cancelled', accepted=False, reason='cancelled'),
                    dict(status=3, accepted=False, reason='malformed'), dict(status='rejected', accepted=False)):
            with self.subTest(row=row), patch.object(gui, 'read_record', return_value=row):
                with self.assertRaisesRegex(ValueError, 'failed or was cancelled'):
                    flow.adopt('route', process, flow.workspace/'route.command.log')
            self.assertFalse(flow.ready)
        for error in (FileNotFoundError(), ValueError('corrupt')):
            with patch.object(gui, 'read_record', side_effect=error):
                self.assertIsNone(gui.failed_route_detail(flow.workspace/'route/result.json'))

    def test_actual_load_callback_enforces_floor_without_rewriting_budget(self):
        for seconds in (60, 90):
            with self.subTest(seconds=seconds):
                callback = gt.window_method('load_preset')
                wx = callback.__globals__['wx']; wx.FD_OPEN=1; wx.FD_FILE_MUST_EXIST=2; wx.ID_OK=1
                dialog=MagicMock(); dialog.__enter__.return_value=dialog; dialog.ShowModal.return_value=1
                wx.FileDialog.return_value=dialog
                window=SimpleNamespace(busy=False, method=Mock(), choices={'profile':Mock()},
                    values={'profile':[('Tuned','tuned')]}, seconds=Mock(), nets=Mock(), flow=object(),
                    inspected=Mock(), refresh=Mock())
                window.method.GetSelection.return_value=1
                loaded=dict(pref.DEFAULTS, profile='tuned', seconds=seconds)
                with patch.object(gui.pref, 'load', return_value=object()), patch.object(gui.pref, 'resolve', return_value=loaded):
                    callback(window, None)
                if seconds == 60:
                    window.choices['profile'].SetSelection.assert_not_called()
                    window.seconds.SetValue.assert_not_called(); window.nets.SetValue.assert_not_called()
                    wx.MessageBox.assert_called_once()
                else:
                    window.seconds.SetValue.assert_called_once_with(90)
                    wx.MessageBox.assert_not_called()
                self.assertEqual(loaded['seconds'], seconds)


if __name__ == '__main__': unittest.main()
