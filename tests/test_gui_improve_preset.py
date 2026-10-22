"""Prospective portable UX controls, not GUI/Native qualification."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch
from autorouter import gui, preferences as pref
from tests.test_gui import window_method


class ImprovePresetTests(unittest.TestCase):
    def test_defaults_and_custom_via_keep_task_constraints(self):
        for scoring in (None, 'via_high'):
            original = dict(pref.DEFAULTS, scoring_preference=scoring)
            result = gui.improve_preset(original)
            self.assertEqual(result, dict(original, profile='tuned', adapter='both'))
            self.assertEqual(original, dict(pref.DEFAULTS, scoring_preference=scoring))

    def test_incompatible_task_refused_without_rewriting_input(self):
        cases = [dict(pref.DEFAULTS, scope='partial_completion'),
                 dict(pref.DEFAULTS, profile='tuned', layers=['F.Cu']),
                 dict(pref.DEFAULTS, seconds=20),
                 dict(pref.DEFAULTS, profile='completion-only', scope='selected_nets', nets=['GND'])]
        for original in cases:
            before = dict(original)
            with self.subTest(config=original), self.assertRaises(ValueError):
                gui.improve_preset(original)
            self.assertEqual(original, before)

    def window(self, config):
        choices = {'profile': Mock(), 'adapter': Mock()}
        window = SimpleNamespace(busy=False, flow=object(), inspected=Mock(), method=Mock(),
            config=Mock(return_value=config), choices=choices, status=Mock(), refresh=Mock(), refused=Mock(),
            values={'profile': [('Standard', 'standard'), ('Tuned', 'tuned')],
                    'adapter': [('Stock', 'none'), ('Both', 'both')]})
        window.method.GetSelection.return_value = 1
        return window

    def test_actual_method_callback_changes_only_algorithm_widgets_or_refuses(self):
        callback = window_method('method_changed')
        good = self.window(dict(pref.DEFAULTS, scoring_preference='via_low'))
        callback(good, Mock())
        good.choices['profile'].SetSelection.assert_called_once_with(1)
        good.choices['adapter'].SetSelection.assert_called_once_with(1)
        good.method.SetSelection.assert_not_called()
        self.assertIsNone(good.flow)
        bad = self.window(dict(pref.DEFAULTS, scope='partial_completion'))
        callback(bad, Mock())
        bad.method.SetSelection.assert_not_called()
        callback.__globals__['wx'].CallAfter.assert_called_once_with(bad.method.SetSelection, 0)
        for control in bad.choices.values(): control.SetSelection.assert_not_called()
        bad.refused.assert_called_once()
        callback.__globals__['wx'].MessageBox.assert_not_called()

    def test_load_incompatible_settings_in_improve_refuses_before_widget_writes(self):
        callback = window_method('load_preset')
        wx = callback.__globals__['wx']; wx.FD_OPEN = 1; wx.FD_FILE_MUST_EXIST = 2; wx.ID_OK = 1
        dialog = MagicMock(); dialog.__enter__.return_value = dialog
        dialog.ShowModal.return_value = 1; dialog.GetPath.return_value = '/owned/preset.json'
        wx.FileDialog.return_value = dialog
        window = self.window(dict(pref.DEFAULTS)); window.seconds = Mock(); window.nets = Mock()
        def choose(dialog, loaded):
            try: loaded('/owned/preset.json')
            except Exception as exc: window.refused(str(exc))
        window.choose_path = choose
        with patch.object(gui.pref, 'load', return_value=object()), patch.object(gui.pref, 'resolve', return_value=dict(pref.DEFAULTS)):
            callback(window, None)
        for control in window.choices.values(): control.SetSelection.assert_not_called()
        window.seconds.SetValue.assert_not_called(); window.nets.SetValue.assert_not_called()
        window.refused.assert_called_once()
        wx.MessageBox.assert_not_called()

    def test_load_valid_settings_clears_previous_result_and_requires_new_preview(self):
        callback = window_method('load_preset')
        wx = callback.__globals__['wx']; wx.FD_OPEN = 1; wx.FD_FILE_MUST_EXIST = 2
        config = dict(pref.DEFAULTS, profile='tuned', seconds=90)
        window = self.window(config)
        window.seconds = Mock(); window.nets = Mock(); window.log = Mock()
        window.choose_path = lambda dialog, loaded: loaded('/owned/preset.json')
        with patch.object(gui.pref, 'load', return_value=object()), \
                patch.object(gui.pref, 'resolve', return_value=config):
            callback(window, None)
        self.assertIsNone(window.flow)
        window.inspected.SetValue.assert_called_once_with(False)
        window.log.SetValue.assert_called_once_with(
            'Settings loaded. Preview the saved project to start a new job.')
        window.refresh.assert_called_once()
        window.refused.assert_not_called()


if __name__ == '__main__': unittest.main()
