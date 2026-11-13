"""Real placement-entry callback bodies, without a display or Native claims."""
import ast
import copy
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import gui, placement_gui
from tests.test_gui import window_method


def placement_factory(constructor):
    """Keep actual factory admission; substitute only wx widget construction."""
    tree = ast.parse(Path(placement_gui.__file__).read_text())
    factory = copy.deepcopy(next(node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == 'create_window'))
    construct = ast.parse('def Window():\n    return _construct(board, on_closed)\n').body[0]
    factory.body = [copy.deepcopy(construct) if isinstance(node, ast.ClassDef) and node.name == 'Window'
                    else node for node in factory.body]
    context = dict(vars(placement_gui), _construct=constructor)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[])),
                 placement_gui.__file__, 'exec'), context)
    return context['create_window']


class PlacementEntry(unittest.TestCase):
    def setUp(self):
        self.window = SimpleNamespace(busy=False, closing=False, chooser=None, source_guard=None,
            placement_window=None, board=Mock(), output=Mock(), status=Mock(), Show=Mock(), Hide=Mock(), Raise=Mock(),
            Close=Mock(), Destroy=Mock(), timer=Mock(), job=Mock())
        self.board = '/owned saved project/exact board.kicad_pcb'
        self.window.board.GetValue.return_value = self.board
        self.window.output.GetValue.return_value = '/chosen/candidate jobs'
        self.child = Mock()
        self.factory_patch = patch.object(placement_gui, 'create_window', return_value=self.child)
        self.factory = self.factory_patch.start(); self.addCleanup(self.factory_patch.stop)
        self.open = window_method('open_placement'); self.close = window_method('close')

    def event(self, *, veto=True):
        return Mock(CanVeto=Mock(return_value=veto))

    def test_busy_chooser_or_closing_never_launches_or_changes_visibility(self):
        for field, value in [('busy', True), ('chooser', object()), ('closing', True)]:
            with self.subTest(field=field):
                previous = getattr(self.window, field); setattr(self.window, field, value)
                self.open(self.window, None); setattr(self.window, field, previous)
        self.factory.assert_not_called(); self.window.Hide.assert_not_called(); self.window.Show.assert_not_called()
        self.assertIsNone(self.window.placement_window)

    def test_bound_placement_source_refuses_recursive_placement(self):
        self.window.source_guard = object()
        self.open(self.window, None)
        self.factory.assert_not_called(); self.window.Hide.assert_not_called()
        self.assertIn('bound placement candidate', self.window.status.SetLabel.call_args.args[0])

    def test_exact_displayed_board_opens_one_child_then_hides_parent(self):
        calls = []; self.child.Show.side_effect = lambda: calls.append('show child')
        self.window.Hide.side_effect = lambda: calls.append('hide parent')
        self.open(self.window, None)
        self.assertIs(self.window.placement_window, self.child)
        self.factory.assert_called_once()
        self.assertEqual(self.factory.call_args.args, (self.board,))
        self.assertEqual(set(self.factory.call_args.kwargs), {'on_closed', 'output_hint'})
        self.assertEqual(self.factory.call_args.kwargs['output_hint'], '/chosen/candidate jobs')
        self.assertTrue(callable(self.factory.call_args.kwargs['on_closed']))
        self.assertEqual(calls, ['show child', 'hide parent'])
        self.open(self.window, None)
        self.assertEqual(self.factory.call_count, 1); self.child.Raise.assert_called_once_with()
        self.assertEqual(self.child.Show.call_count, 1); self.assertEqual(self.window.Hide.call_count, 1)

    def test_entry_composes_actual_factory_with_existing_app_and_no_nested_loop(self):
        # Unlike a replacement create_window mock, exercise its actual app/thread admission.
        wx = ModuleType('wx'); svg = ModuleType('wx.svg'); wx.svg = svg
        application = Mock(); wx.GetApp = Mock(return_value=application); wx.App = Mock()
        construct = Mock(return_value=self.child)
        actual = placement_factory(construct); self.factory.side_effect = actual
        with patch.dict(sys.modules, {'wx': wx, 'wx.svg': svg}):
            self.open(self.window, None)
        wx.GetApp.assert_called_once_with(); wx.App.assert_not_called(); application.MainLoop.assert_not_called()
        construct.assert_called_once_with(self.board, self.factory.call_args.kwargs['on_closed'])
        self.child.Show.assert_called_once_with(); self.window.Hide.assert_called_once_with()

    def test_constructor_failure_keeps_parent_visible_and_allows_retry(self):
        self.factory.side_effect = ValueError('saved PCB unavailable')
        self.open(self.window, None)
        self.assertIsNone(self.window.placement_window); self.window.Hide.assert_not_called()
        self.window.Show.assert_called_once_with()
        self.assertIn('saved PCB unavailable', self.window.status.SetLabel.call_args.args[0])
        self.factory.side_effect = None; self.open(self.window, None)
        self.assertIs(self.window.placement_window, self.child)

    def test_explicit_closed_callback_clears_reference_and_restores_parent_then_reopens(self):
        self.open(self.window, None); finished = self.factory.call_args.kwargs['on_closed']
        finished()
        self.assertIsNone(self.window.placement_window)
        self.window.Show.assert_called_once_with(); self.window.Raise.assert_called_once_with()
        self.window.Close.assert_not_called()
        next_child = Mock(); self.factory.return_value = next_child
        self.open(self.window, None)
        self.assertIs(self.window.placement_window, next_child); self.assertEqual(self.factory.call_count, 2)
        self.child.Raise.assert_not_called(); next_child.Show.assert_called_once_with()

    def test_parent_close_waits_for_child_cleanup_then_explicit_callback_finishes_close(self):
        self.open(self.window, None); finished = self.factory.call_args.kwargs['on_closed']
        self.window.Close.side_effect = lambda: self.close(self.window, self.event())
        event = self.event(); self.close(self.window, event)
        self.assertTrue(self.window.closing); self.child.Close.assert_called_once_with(); event.Veto.assert_called_once_with()
        self.window.Destroy.assert_not_called(); self.window.timer.Stop.assert_not_called()
        self.window.Show.assert_not_called(); self.window.job.cancel.assert_not_called()
        finished()
        self.assertIsNone(self.window.placement_window); self.window.Close.assert_called_once_with()
        self.window.timer.Stop.assert_called_once_with(); self.window.Destroy.assert_called_once_with()
        self.window.Show.assert_not_called(); self.window.Raise.assert_not_called()

    def test_nonvetoable_parent_close_still_waits_for_child_notification(self):
        self.open(self.window, None); event = self.event(veto=False)
        self.close(self.window, event)
        self.assertTrue(self.window.closing); self.child.Close.assert_called_once_with()
        event.Veto.assert_not_called(); self.window.Destroy.assert_not_called(); self.window.timer.Stop.assert_not_called()

    def test_child_still_active_prevents_parent_destruction_after_repeated_close(self):
        self.open(self.window, None)
        for _ in range(2):
            event = self.event(); self.close(self.window, event); event.Veto.assert_called_once_with()
        self.assertIs(self.window.placement_window, self.child)
        self.assertEqual(self.child.Close.call_count, 2)
        self.window.Destroy.assert_not_called(); self.window.timer.Stop.assert_not_called()

    def test_no_child_retains_existing_chooser_worker_and_idle_close_lifecycle(self):
        self.window.chooser = object(); event = self.event(); self.close(self.window, event)
        event.Veto.assert_called_once_with(); self.window.Destroy.assert_not_called(); self.window.job.cancel.assert_not_called()
        self.window.chooser = None; self.window.busy = True
        event = self.event(); self.close(self.window, event)
        self.window.job.cancel.assert_called_once_with(); event.Veto.assert_called_once_with()
        self.window.Destroy.assert_not_called(); self.window.timer.Stop.assert_not_called()
        self.window.busy = False; self.close(self.window, self.event())
        self.window.timer.Stop.assert_called_once_with(); self.window.Destroy.assert_called_once_with()

    def test_routing_close_notification_waits_for_every_owned_cleanup_scope(self):
        self.window.closing = True; self.window.warning_dialog = None
        callback = Mock(); self.window._on_closed = callback; wx = Mock()
        calls = Mock(); calls.attach_mock(self.window.Destroy, 'destroy'); calls.attach_mock(wx.CallAfter, 'notify')
        with patch.dict(sys.modules, {'wx': wx}):
            for field, value in (('busy', True), ('chooser', object()), ('warning_dialog', object()),
                                 ('placement_window', object())):
                with self.subTest(field=field):
                    previous = getattr(self.window, field); setattr(self.window, field, value)
                    self.assertFalse(gui._finish_window_close(self.window))
                    setattr(self.window, field, previous)
                    self.window.Destroy.assert_not_called(); wx.CallAfter.assert_not_called()
            self.assertTrue(gui._finish_window_close(self.window))
            self.assertFalse(gui._finish_window_close(self.window))
        self.assertEqual([call[0] for call in calls.mock_calls], ['destroy', 'notify'])
        wx.CallAfter.assert_called_once_with(callback); callback.assert_not_called()
        wx.CallAfter.call_args.args[0](); callback.assert_called_once_with()

    def test_routing_factory_refuses_noncallable_parent_hook_before_construction(self):
        from tests.test_gui_window_factory import outer_factory
        construct = Mock(); create = outer_factory(construct)
        for callback in (False, True, 'approve', {}, 1):
            with self.subTest(callback=callback), self.assertRaisesRegex(ValueError, 'callable'):
                create(on_closed=callback)
        construct.assert_not_called()

    def test_idle_close_notifies_parent_once_and_nonvetoable_active_close_waits(self):
        self.window._on_closed = Mock(); wx = Mock()
        with patch.dict(sys.modules, {'wx': wx}):
            self.window.busy = True; event = self.event(veto=False)
            self.close(self.window, event)
            event.Veto.assert_not_called(); wx.CallAfter.assert_not_called()
            self.window.job.cancel.assert_called_once(); self.window.Destroy.assert_not_called()
            self.window.busy = False
            self.close(self.window, self.event()); self.close(self.window, self.event())
        self.window.Destroy.assert_called_once()
        wx.CallAfter.assert_called_once_with(self.window._on_closed)


if __name__ == '__main__': unittest.main()
