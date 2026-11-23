"""Application composition/lifecycle controls; not actual wx qualification."""
import ast
import copy
from pathlib import Path
import signal
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import board_review_gui, gui, placement_gui
from tests import test_gui as base


def passive_wx():
    """Controlled widgets for the complete real constructor, not pixel proof."""
    class Widget:
        def __init__(self, parent=None, *args, **kwargs):
            self.parent = parent; self.value = kwargs.get('value', '')
            self.label = kwargs.get('label', ''); self.selection = 0
            self.items = []
            self.size = kwargs.get('size'); self.minimum = None
            self.wrap_widths = []; self.bindings = []; self.sizer = None
            self.font = Mock()
        def __getattr__(self, name):
            value = Mock(); setattr(self, name, value); return value
        def GetFont(self): return self.font
        def FromDIP(self, value): return value
        def SetMinSize(self, value): self.minimum = value
        def GetEffectiveMinSize(self):
            return SimpleNamespace(width=self.minimum[0] if self.minimum is not None else max(80, len(self.value) * 7))
        def SetSizer(self, value): self.sizer = value
        def SetSelection(self, value): self.selection = value
        def GetSelection(self): return self.selection
        def Set(self, items): self.items = list(items)
        def SetStringSelection(self, item): self.selection = self.items.index(item)
        def GetStringSelection(self): return self.items[self.selection] if 0 <= self.selection < len(self.items) else ''
        def GetValue(self): return self.value
        def SetValue(self, value): self.value = value
        def ChangeValue(self, value): self.value = value
        def SetLabel(self, value): self.label = value
        def GetLabel(self): return self.label
        def GetClientSize(self):
            if self.parent is not None: return self.parent.GetClientSize()
            return SimpleNamespace(width=self.size[0], height=self.size[1])
        def SetSize(self, size): self.size = size
        def GetPane(self): return Widget(self)
        def Wrap(self, width): self.wrap_widths.append(width)
        def Bind(self, event, callback, *args): self.bindings.append((event, callback))
    class Sizer:
        def __init__(self, *args, **kwargs): self.children = []
        def Add(self, child, *args, **kwargs): self.children.append((child, args, kwargs))
        def AddGrowableCol(self, *args): pass
        def AddStretchSpacer(self, *args): pass
    class Wx(SimpleNamespace):
        def __getattr__(self, name): return name if name.startswith('EVT_') else 0
    return Wx(Frame=Widget, ScrolledWindow=Widget, StaticText=Widget, Button=Widget,
        TextCtrl=Widget, CheckBox=Widget, Choice=Widget, CollapsiblePane=Widget,
        Timer=Widget, BoxSizer=Sizer, FlexGridSizer=Sizer, GetApp=lambda: object())


def outer_factory(constructor):
    """Exercise the real outer factory while existing tests cover Window methods.

    Substitute only widget construction: this suite neither needs nor certifies
    a display server, native wx widgets, or KiCad integration.
    """
    tree = ast.parse(Path(gui.__file__).read_text())
    function = copy.deepcopy(next(node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == 'create_window'))
    replacement = ast.parse('def Window():\n    return _construct(board, source_guard)\n').body[0]
    function.body = [copy.deepcopy(replacement) if isinstance(node, ast.ClassDef) and node.name == 'Window'
                     else node for node in function.body]
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    context = dict(vars(gui), _construct=constructor)
    exec(compile(module, gui.__file__, 'exec'), context)
    return context['create_window']


class WindowFactory(unittest.TestCase):
    setUp = base.GuiWorkflowTests.setUp

    def wx(self, application):
        return SimpleNamespace(GetApp=Mock(return_value=application), App=Mock(), CallAfter=Mock())

    def test_board_search_marks_exact_net_and_clears_an_ambiguous_query(self):
        wx = passive_wx(); wx.Panel = wx.Frame; wx.ComboBox = wx.Choice; wx.Colour = str
        canvas = Mock()
        first = dict(id='a', label='J1 pad 1', kind='pad', net='GND', detail='Through-hole', point=(5, 5))
        second = dict(id='b', label='Track 1', kind='track', net='GND', detail='Protected', point=(20, 5))
        third = dict(second, id='c', label='Track 2', net='Gnd', point=(40, 5))
        scene = dict(svg='<svg></svg>', size=(100, 100), items=(first, second, third))
        with patch.object(placement_gui, 'board_canvas', return_value=canvas), \
                patch.object(board_review_gui.chrome, 'colours', return_value=('#000000',) * 3), \
                patch.object(board_review_gui.review_view, 'inspect_item', return_value={'marked': first}):
            view = board_review_gui.board_review(wx, None, Mock(), empty_note='Owned board')
            view.set_view(scene=scene)
            view.select('a')
            canvas.SetScene.assert_called_with({'marked': first}, keep_view=True)
            view.item_detail.SetLabelText.assert_called_with('GND · Through-hole')
            view.objects.SetValue('GND')
            view.object_search(None)
            self.assertIsNone(view.selected_item())
            self.assertEqual(view.ids, ['a', 'b'])
            self.assertEqual(view.objects.GetValue(), 'GND')
            marked = canvas.SetScene.call_args.args[0]['svg']
            self.assertEqual(marked.count('data-role="inspected-net-item"'), 2)
            self.assertNotIn('cx="40"', marked)
            self.assertEqual(view.refinement_note(), 'Net GND · F.Cu')
            view.item_detail.SetLabelText.assert_called_with('2 displayed items marked · Choose one for details.')
            view.objects.SetValue('gNd')
            view.object_search(None)
            canvas.SetScene.assert_called_with(scene, keep_view=True)
            self.assertEqual(view.refinement_note(), '')
            view.item_title.SetLabelText.assert_called_with('3 matching items')

    def test_refinement_preserves_the_located_finding_note(self):
        wx = passive_wx(); wx.Panel = wx.Frame; wx.ComboBox = wx.Choice; wx.Colour = str
        canvas = Mock()
        front = dict(svg='<svg></svg>', size=(100, 100), mm_to_svg=(1, 0, 0))
        back = dict(front)
        row = dict(index=0, label='1. Library footprint changed', layers=('B.Cu',),
                   points=(SimpleNamespace(xy=(20, 30), layers=('B.Cu',)),))
        with patch.object(placement_gui, 'board_canvas', return_value=canvas), \
                patch.object(board_review_gui.chrome, 'colours', return_value=('#000000',) * 3):
            view = board_review_gui.board_review(wx, None, Mock(), empty_note='Owned board')
            view.set_view({'diagrams': {'F.Cu': front, 'B.Cu': back}, 'findings': (row,)})
            view.locations.SetSelection(1)
            view.finding_changed(None)
            canvas.focus_item.assert_called_once_with((20, 30))
            self.assertIn('data-role="finding-location"', canvas.SetScene.call_args.args[0]['svg'])
            self.assertEqual(view.refinement_note(), 'Finding on B.Cu · 1. Library footprint changed')
            view.set_view(scene=front)
            self.assertEqual(view.refinement_note(), '')

    def test_passive_inspector_reports_a_raster_failure(self):
        wx = passive_wx(); wx.Panel = wx.Frame; wx.ComboBox = wx.Choice; wx.Colour = str
        canvas = Mock(); failure = Mock()
        with patch.object(placement_gui, 'board_canvas', return_value=canvas), \
                patch.object(board_review_gui.chrome, 'colours', return_value=('#000000',) * 3):
            view = board_review_gui.board_review(wx, None, failure, empty_note='Owned board')
            canvas.SetScene.side_effect = [ValueError('owned raster failure'), None]
            self.assertFalse(view.redraw())
        failure.assert_called_once_with('owned raster failure')
        canvas.SetScene.assert_called_with(None)

    def test_existing_application_gets_one_unshown_frame_and_exact_guard(self):
        origin = self.root / 'origin.json'; origin.write_bytes(b'checked origin')
        def verify():
            if origin.read_bytes() != b'checked origin': raise ValueError('origin changed')
        guard = gui.SourceGuard(self.board, verify)
        frame = Mock(); construct = Mock(return_value=frame); wx = self.wx(object())
        with patch.dict(sys.modules, wx=wx), patch.object(gui.signal, 'signal') as signals:
            result = outer_factory(construct)(str(self.board), source_guard=guard)
        self.assertIs(result, frame)
        construct.assert_called_once_with(str(self.board), guard)
        frame.Show.assert_not_called(); frame.MainLoop.assert_not_called()
        wx.App.assert_not_called(); wx.CallAfter.assert_not_called(); signals.assert_not_called()

    def test_missing_application_refuses_before_widget_construction(self):
        construct = Mock(); wx = self.wx(None)
        with patch.dict(sys.modules, wx=wx), self.assertRaisesRegex(ValueError, 'Create the wx application'):
            outer_factory(construct)()
        construct.assert_not_called(); wx.App.assert_not_called()

    def test_path_object_is_normalized_but_nonpath_refuses(self):
        construct = Mock(); factory = outer_factory(construct); wx = self.wx(object())
        with patch.dict(sys.modules, wx=wx):
            factory(self.board)
            construct.assert_called_once_with(str(self.board), None)
            with self.assertRaisesRegex(ValueError, 'exact saved PCB path'): factory(None)
        self.assertEqual(construct.call_count, 1)

    def test_worker_thread_cannot_construct_native_frame(self):
        construct = Mock(); factory = outer_factory(construct); wx = self.wx(object()); errors = []
        def worker():
            try: factory()
            except Exception as exc: errors.append(exc)
        with patch.dict(sys.modules, wx=wx):
            thread = threading.Thread(target=worker); thread.start(); thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(errors), 1); self.assertIsInstance(errors[0], ValueError)
        self.assertIn('main thread', str(errors[0])); construct.assert_not_called()

    def test_stale_or_mismatched_guard_refuses_before_creating_frame(self):
        guard = gui.SourceGuard(self.board, lambda: None)
        construct = Mock(); factory = outer_factory(construct); wx = self.wx(object())
        other = self.root / 'another.kicad_pcb'; other.write_bytes(b'other source')
        with patch.dict(sys.modules, wx=wx):
            with self.assertRaisesRegex(ValueError, 'Displayed PCB differs'):
                factory(str(other), source_guard=guard)
            self.board.write_bytes(b'changed source')
            with self.assertRaisesRegex(ValueError, 'Bound source project changed'):
                factory(str(self.board), source_guard=guard)
        construct.assert_not_called()

    def test_unavailable_wx_keeps_actionable_error(self):
        with patch.dict(sys.modules, wx=None), self.assertRaisesRegex(SystemExit, 'pinned KiCad bundled Python'):
            outer_factory(Mock())()

    def test_plain_main_creates_one_app_and_preserves_signal_close_and_cleanup(self):
        app = Mock(); job = Mock(); frame = Mock(job=job)
        wx = self.wx(None); wx.App.return_value = app
        wx.CallAfter.side_effect = lambda callback: callback()
        old = object(); installed = {}
        def set_signal(number, handler): installed[number] = handler
        def loop(): installed[signal.SIGINT]()
        app.MainLoop.side_effect = loop
        with patch.dict(sys.modules, wx=wx), patch.object(gui, 'create_window', return_value=frame) as create, \
                patch.object(gui.signal, 'getsignal', return_value=old), patch.object(gui.signal, 'signal', side_effect=set_signal):
            self.assertEqual(gui.main(['--board', str(self.board)]), 0)
        wx.App.assert_called_once_with(False)
        create.assert_called_once_with(str(self.board), source_guard=None, source_note='')
        frame.Show.assert_called_once_with(); app.MainLoop.assert_called_once_with()
        frame.Close.assert_called_once_with(); job.cancel.assert_called_once_with()
        self.assertEqual(installed, {signal.SIGINT: old, signal.SIGTERM: old})

    def test_main_loop_failure_still_restores_signals_and_cancels_active_job(self):
        app = Mock(); app.MainLoop.side_effect = RuntimeError('loop failed')
        frame = Mock(job=Mock()); wx = self.wx(None); wx.App.return_value = app
        old = object(); installed = {}
        with patch.dict(sys.modules, wx=wx), patch.object(gui, 'create_window', return_value=frame), \
                patch.object(gui.signal, 'getsignal', return_value=old), \
                patch.object(gui.signal, 'signal', side_effect=lambda number, handler: installed.update({number: handler})), \
                self.assertRaisesRegex(RuntimeError, 'loop failed'):
            gui.main([])
        frame.job.cancel.assert_called_once_with()
        self.assertEqual(installed, {signal.SIGINT: old, signal.SIGTERM: old})

    def test_main_refuses_nested_application_loop(self):
        wx = self.wx(object())
        with patch.dict(sys.modules, wx=wx), patch.object(gui, 'create_window') as create, \
                self.assertRaisesRegex(ValueError, 'already exists'):
            gui.main([])
        create.assert_not_called(); wx.App.assert_not_called()

    def test_saved_copy_restart_waits_for_closed_routing_view(self):
        notes = []
        target = self.root / 'exported.kicad_pcb'
        wx = self.wx(object())
        window = SimpleNamespace(closing=True, busy=True, timer=Mock(), Destroy=lambda: notes.append('destroy'),
            _next_saved_source=target, _on_closed=lambda: notes.append('return'),
            _on_saved_source=lambda board: notes.append(board))
        with patch.dict(sys.modules, wx=wx):
            self.assertFalse(gui._finish_window_close(window))
            wx.CallAfter.assert_not_called()
            window.busy = False
            self.assertTrue(gui._finish_window_close(window))
            callback, = wx.CallAfter.call_args.args
            self.assertEqual(notes, ['destroy'])
            callback()
            self.assertFalse(gui._finish_window_close(window))
        self.assertEqual(notes, ['destroy', 'return', target])

    def test_real_constructor_bounds_long_path_and_choice_minima_and_expands_panel(self):
        wx = passive_wx()
        long_path = '/owned saved project/' + '/nested working folder' * 30 + '/board.kicad_pcb'
        with patch.dict(sys.modules, wx=wx):
            window = gui.create_window(long_path)
        self.assertEqual(window.board.GetValue(), long_path)
        self.assertEqual(window.board.GetEffectiveMinSize().width, 160)
        self.assertEqual(window.output.GetEffectiveMinSize().width, 160)
        self.assertEqual(window.model_config.GetEffectiveMinSize().width, 160)
        self.assertTrue(all(control.GetEffectiveMinSize().width == 160 for control in window.choices.values()))
        self.assertEqual(window.method.GetEffectiveMinSize().width, 160)
        self.assertEqual(window.minimum, (720, 640))
        self.assertIs(window.sizer.children[0][0], window.panel)
        self.assertEqual(window.sizer.children[0][1][0], 1)
        window.Show.assert_not_called(); window.MainLoop.assert_not_called()

    def test_real_window_reflows_dynamic_labels_on_resize_show_and_refresh(self):
        wx = passive_wx()
        with patch.dict(sys.modules, wx=wx): window = gui.create_window('')
        window.status.SetLabel('A current finding with details. ' * 40)
        for size in ((820, 780), (1024, 720), (720, 640)):
            with self.subTest(size=size):
                window.SetSize(size); event = Mock()
                window.layout_changed(event); event.Skip.assert_called_once_with()
                self.assertEqual(window.status.wrap_widths[-1], size[0] - 40)
                window.refresh()
                self.assertEqual(window.export_note.wrap_widths[-1], size[0] - 40)
                self.assertEqual(window.assistant_note.wrap_widths[-1], size[0] - 40)
        events = [event for event, callback in window.bindings if callback == window.layout_changed]
        self.assertIn('EVT_SIZE', events); self.assertIn('EVT_SHOW', events)
        self.assertIn('File > Close Project', window.ack.GetLabel())
        self.assertIn('\n', window.ack.GetLabel())

    def test_manual_selected_scope_sets_completion_profile_and_revokes_preview(self):
        wx = passive_wx()
        with patch.dict(sys.modules, wx=wx), patch.object(gui.c, 'NATIVE_VERSION', '10.0.7'):
            window = gui.create_window(str(self.board))
            window.choices['profile'].SetSelection(1)  # Earlier explicit More search choice.
            window.nets.SetValue('ROUTE_A\nROUTE_B')
            window.seconds.SetValue('85')
            window.flow = SimpleNamespace(workspace=self.root)
            window.inspected.SetValue(True)
            scope = window.choices['scope']
            callback, = [call for name, call in scope.bindings if name == 'EVT_CHOICE']
            scope.SetSelection(2)
            callback(Mock())
            config = window.config()
            self.assertEqual(config['profile'], 'completion-only')
            self.assertEqual(config['nets'], ['ROUTE_A', 'ROUTE_B'])
            self.assertEqual(config['seconds'], 85)
            self.assertIsNone(window.flow)
            self.assertFalse(window.inspected.GetValue())
            scope.SetSelection(0)
            callback(Mock())
            self.assertEqual(window.config()['profile'], 'tuned')
            self.assertEqual(window.config()['seconds'], 85)


if __name__ == '__main__': unittest.main()
