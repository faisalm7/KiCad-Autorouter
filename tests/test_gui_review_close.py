"""Observed open-review recovery; source/candidate authority remains in CLI."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import json
import sys
import tempfile
import unittest
from autorouter import gui, handoff as h
from tests.test_gui import displayed_inputs, window_method


class ReviewCloseTests(unittest.TestCase):
    def test_refine_closes_idle_review_without_choosing_or_exporting(self):
        record = object()
        window = SimpleNamespace(flow=record, busy=False, closing=False, chooser=None,
            warning_dialog=None, _on_refine=Mock(), Close=Mock(),
            board_review=SimpleNamespace(selected_item=lambda: {'label': 'R2 pad 1'}))
        act = window_method('act')
        for blocked in ('busy', 'closing', 'warning_dialog'):
            prior = getattr(window, blocked)
            setattr(window, blocked, True)
            act(window, 'refine')
            setattr(window, blocked, prior)
        window.Close.assert_not_called()
        act(window, 'refine')
        window.Close.assert_called_once_with()
        self.assertEqual(window._refinement, 'R2 pad 1')
        self.assertIs(window.flow, record)
        window._on_refine.assert_not_called()

    def test_refinement_callback_runs_once_after_exact_child_cleanup(self):
        child = SimpleNamespace(closing=True, busy=False, warning_dialog=object(), timer=Mock(),
            Destroy=Mock(), _refinement='R2', _on_refine=Mock(), _on_closed=Mock())
        wx = SimpleNamespace(CallAfter=Mock())
        with patch.dict(sys.modules, {'wx': wx}):
            self.assertFalse(gui._finish_window_close(child))
            wx.CallAfter.assert_not_called()
            child.warning_dialog = None
            self.assertTrue(gui._finish_window_close(child))
            self.assertFalse(gui._finish_window_close(child))
        child.Destroy.assert_called_once_with()
        wx.CallAfter.assert_called_once_with(child._on_refine, 'R2')

    def test_drawing_failure_clears_review_acknowledgement(self):
        window = SimpleNamespace(inspected=Mock(), log=Mock(), workspace_tabs=Mock(),
                                 review_key=Mock(), refresh=Mock())
        window_method('review_picture_failed')(window, 'owned raster failure')
        window.inspected.SetValue.assert_called_once_with(False)
        window.workspace_tabs.SetSelection.assert_called_once_with(1)
        self.assertIn('owned raster failure', window.log.AppendText.call_args.args[0])

    def test_display_setup_error_cannot_arm_an_export_worker(self):
        request = gui.Request('/owned/board.kicad_pcb', '/owned/runs', json.dumps(dict(gui.pref.DEFAULTS)), True)
        inspector = Mock()
        inspector.finding_changed.side_effect = ValueError('owned display setup failure')
        window = SimpleNamespace(flow=object(), job=None, busy=False, chooser=None, closing=False,
            in_workspace=True, workspace_render={'diagrams': {'F.Cu': {}}}, board_review=inspector,
            refused=Mock(), **displayed_inputs(request))
        act = window_method('act')
        act(window, 'export')
        window.refused.assert_called_once_with('owned display setup failure')
        self.assertFalse(window.busy)
        self.assertIsNone(window.job)

    def test_actual_accept_callback_retains_route_and_review_on_observed_lock(self):
        flow = SimpleNamespace(workspace=Path('/owned/job'), ready={'preview','route','review'},
                               records={'route':{'accepted':True}}, choice=None)
        window = SimpleNamespace(flow=flow, chooser=None, busy=False, inspected=Mock(),
            status=Mock(), log=Mock(), refresh=Mock(), refused=Mock())
        window.inspected.GetValue.return_value=True
        hint=Mock(side_effect=h.ReviewProjectOpen('Use File > Close Project'))
        callback=window_method('act',review_close_hint=hint)
        callback(window,'accept')
        self.assertIs(window.flow,flow);self.assertEqual(flow.ready,{'preview','route','review'})
        self.assertEqual(flow.records,{'route':{'accepted':True}});self.assertIsNone(flow.choice)
        window.inspected.SetValue.assert_called_once_with(False);window.refused.assert_not_called()
        self.assertFalse(window.busy);self.assertIn('no acceptance',window.log.SetValue.call_args.args[0])

    def test_hint_uses_real_bounded_inventory_without_ignoring_locks_or_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();project=root/'review/project';project.mkdir(parents=True)
            (project/'board.kicad_pcb').write_text('owned unchanged control')
            lock=project/'~board.kicad_pro.lck';lock.write_text('owned lock')
            with self.assertRaises(h.ReviewProjectOpen):gui.review_close_hint(root)
            lock.unlink();(project/'board-backups').mkdir();(project/'board-backups/owned.zip').write_bytes(b'owned')
            gui.review_close_hint(root)
            (project/'alias').symlink_to(project/'board.kicad_pcb')
            with self.assertRaises(h.Rejected):gui.review_close_hint(root)

    def test_missing_acknowledgement_never_discards_recoverable_review_or_starts_work(self):
        flow=object();window=SimpleNamespace(flow=flow,chooser=None,busy=False,
            inspected=Mock(),status=Mock(),log=Mock(),refresh=Mock(),refused=Mock())
        window.inspected.GetValue.return_value=False;hint=Mock()
        window_method('act',review_close_hint=hint)(window,'accept')
        self.assertIs(window.flow,flow);self.assertFalse(window.busy)
        hint.assert_not_called();window.refused.assert_not_called()
        self.assertIn('no acceptance',window.log.SetValue.call_args.args[0])

    def test_only_acknowledged_current_review_enables_accept(self):
        ready = SimpleNamespace(ready={'preview', 'route', 'review'}, choice=None)
        window = SimpleNamespace(flow=ready, busy=False, inspected=Mock(), board=Mock(),
            output=Mock(), ack=Mock(), edit_controls=[], layout_panel=Mock(),
            buttons={name: Mock() for name in ('accept', 'reject')})
        window.ack.GetValue.return_value = True
        refresh = window_method('refresh')
        for checked in (False, True, False):
            window.inspected.GetValue.return_value = checked
            refresh(window)
            window.buttons['accept'].Enable.assert_called_with(checked)
            window.buttons['reject'].Enable.assert_called_with(True)
        window.inspected.GetValue.return_value = True
        window.flow = None
        refresh(window)
        for button in window.buttons.values():
            button.Enable.assert_called_with(False)

    def test_saved_source_actions_follow_acknowledgement_without_disabling_cancel(self):
        window = SimpleNamespace(flow=None, busy=False, inspected=Mock(), board=Mock(),
            output=Mock(), ack=Mock(), edit_controls=[], layout_panel=Mock(),
            buttons={name: Mock() for name in ('preview', 'inspect', 'cancel')})
        refresh = window_method('refresh')
        for closed in (False, True, False):
            window.ack.GetValue.return_value = closed
            refresh(window)
            for name in ('preview', 'inspect'):
                window.buttons[name].Enable.assert_called_with(closed)
            window.buttons['cancel'].Enable.assert_called_with(False)
        window.busy = True
        refresh(window)
        window.buttons['preview'].Enable.assert_called_with(False)
        window.buttons['cancel'].Enable.assert_called_with(True)
        window.busy = False
        window.private_placement_source = True
        refresh(window)
        window.buttons['preview'].Enable.assert_called_with(True)

    def test_uppercase_nested_marker_is_also_a_refusal(self):
        with self.assertRaises(h.ReviewProjectOpen):h.require_closed_review({'nested/~board.kicad_sch.LCK':'owned'})


if __name__=='__main__':unittest.main()
