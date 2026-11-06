"""Pure placement UI lifecycle/dispatch controls; not actual wx/Native qualification."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import threading
from types import MethodType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import gui, placement_gui as pg


def window_method(name, **overrides):
    tree = ast.parse(Path(pg.__file__).read_text())
    factory = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'create_window')
    window = next(node for node in factory.body if isinstance(node, ast.ClassDef) and node.name == 'Window')
    function = next(node for node in window.body if isinstance(node, ast.FunctionDef) and node.name == name)
    namespace = dict(vars(pg), wx=Mock(NullBitmap='empty-bitmap'), on_closed=None)
    namespace.update(overrides)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])), pg.__file__, 'exec'), namespace)
    return namespace[name]


def review():
    return SimpleNamespace(revision=1, pose={'x': 3}, settings={'selected': ['one', 'two']},
                           inspection={'source': '/owned/source.kicad_pcb'}, intent=None)


class PlacementGuiTests(unittest.TestCase):
    def gate(self):
        gate = pg.ReviewGate(); gate.attach(review()); gate.acknowledged = True
        return gate

    def window(self):
        gate = self.gate()
        window = SimpleNamespace(gate=gate, job=gui.CliJob(), busy=False, routing=None, finalized=False,
            qualified=None, cancel_event=threading.Event(), inspection=gate.review.inspection,
            ack=Mock(), picture=Mock(), alternative=Mock(), part=Mock(), parts=Mock(),
            x=Mock(), y=Mock(), status=Mock(), timer=Mock(), findings=Mock(),
            refresh=Mock(), message=Mock(), layout_panel=Mock(), Destroy=Mock(), Hide=Mock())
        window.revoke = MethodType(window_method('revoke'), window)
        window.finish_close = MethodType(window_method('finish_close'), window)
        return window

    def test_explicit_literal_ack_and_each_ticket_dependency(self):
        gate = self.gate(); ticket = gate.ticket(); self.assertIsNone(gate.check(ticket))
        for ack in (False, 1, 'yes', None):
            gate.acknowledged = ack
            with self.subTest(ack=ack), self.assertRaises(ValueError): gate.check(ticket)
        gate.acknowledged = True
        for field, mutation in (('revision', 2), ('pose', {'x': 4}), ('settings', {'selected': []}),
                                ('inspection', {'source': '/other.kicad_pcb'})):
            original = getattr(gate.review, field); setattr(gate.review, field, mutation)
            with self.subTest(field=field), self.assertRaises(ValueError): gate.check(ticket)
            setattr(gate.review, field, original)
        self.assertIsNone(gate.check(ticket))

    def test_pending_edit_cancel_reject_and_close_revoke_old_tickets(self):
        for action in ('dirty', 'invalidate', 'attach', 'close'):
            gate = self.gate(); ticket = gate.ticket(); gate.review.intent = {'choice': 'reviewed_draft'}
            with self.subTest(action=action):
                if action == 'dirty': gate.invalidate(dirty=True)
                elif action == 'invalidate': gate.invalidate()
                elif action == 'attach': gate.attach(review())
                else: gate.close()
                with self.assertRaises(ValueError): gate.check(ticket)
                self.assertIsNone(gate.review.intent)

    def test_decimal_region_refuses_nonfinite_excessive_precision_and_bounds(self):
        self.assertEqual(pg.millimetres('-12.000001'), -12000001)
        self.assertEqual(pg.mm(-12000001), '-12.000001')
        for value in ('', 'nan', 'Infinity', '1e99', '2000.000001', '0.0000001', 'x', 1, True, '0' * 33):
            with self.subTest(value=value), self.assertRaises(ValueError): pg.millimetres(value)

    def test_compact_component_labels_keep_complete_reasons_in_findings(self):
        row = dict(reference='J4', fixed_reasons=['Shares a net with existing copper'])
        self.assertEqual(pg.component_label(row), 'J4 · fixed (routed net)')
        self.assertIn('J4: Shares a net with existing copper', pg.component_findings({'components': [row]}))
        row['fixed_reasons'].append('Locked in KiCad')
        self.assertEqual(pg.component_label(row), 'J4 · fixed (routed net, locked)')
        self.assertIn('Locked in KiCad', pg.component_findings({'components': [row]}))

    def test_render_reflows_scrolled_panel_after_bitmap_grows(self):
        window = self.window(); window.Layout = Mock(); window.panel = Mock()
        window.layout_panel = MethodType(window_method('layout_panel'), window)
        item = dict(uuid='one', reference='J1', fixed_reasons=[])
        window.gate.review = SimpleNamespace(inspection=dict(components=[item], observation={}, source='/owned/source'),
            settings=dict(selected=['one'], region_nm=[0, 0, 10, 10]), moves={'one': [1, 1]}, alternatives=[{}])
        window.coordinates = Mock(); bitmap = Mock(); bitmap.GetSize.return_value = (850, 486)
        with patch.object(pg.placement_view, 'render', return_value='<svg/>'):
            window_method('render', bitmap_with_labels=Mock(return_value=bitmap))(window, 0)
        window.picture.SetBitmap.assert_called_once_with(bitmap)
        window.picture.SetMinSize.assert_called_once_with((850, 486))
        window.panel.Layout.assert_called_once(); window.panel.FitInside.assert_called_once()

    def test_new_private_settings_refuse_overwrite_links_and_oversized_records(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); path = root / 'settings.json'
            pg.write_new_json(path, {'selected': ['owned']})
            original = path.read_bytes(); self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises((ValueError, OSError)): pg.write_new_json(path, {})
            self.assertEqual(path.read_bytes(), original)
            link = root / 'linked.json'; link.symlink_to(path)
            with self.assertRaises((ValueError, OSError, pg.h.Rejected)): pg.write_new_json(link, {})
            self.assertEqual(path.read_bytes(), original)
            huge = root / 'huge.json'
            with self.assertRaises(ValueError): pg.write_new_json(huge, {'data': 'x' * 65536})
            self.assertFalse(huge.exists())

    def test_qualification_dispatch_is_exact_bounded_argv_with_fresh_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); (root / '.runs').mkdir(); (root / '.venv/bin').mkdir(parents=True)
            python = root / '.venv/bin/python'; python.write_bytes(b'owned-not-executed'); python.chmod(0o700)
            draft = root / "review ' $(literal).json"; pg.write_new_json(draft, {'draft': 'owned'})
            output = root / '.runs/new-job'
            with patch.object(pg.c, 'ROOT', root):
                argv = pg.qualification_command(draft, output)
                self.assertEqual(argv, [str(python), '-B', '-m', 'autorouter.placement', '--draft', str(draft),
                    '--draft-sha256', hashlib.sha256(draft.read_bytes()).hexdigest(), '--output', str(output), '--qualify'])
                self.assertFalse(output.exists()); output.mkdir()
                with self.assertRaises(ValueError): pg.qualification_command(draft, output)
                with self.assertRaises(ValueError): pg.qualification_command(draft, root / 'wrong-parent')

    def test_revoke_closes_routing_cancels_authority_and_clears_rejected_preview(self):
        window = self.window(); ticket = window.gate.ticket(); window.routing = Mock()
        window.qualified = {'old': 'candidate'}; window.revoke(discard=True)
        window.routing.Close.assert_called_once(); self.assertIsNone(window.qualified)
        self.assertIsNone(window.gate.review); window.picture.SetBitmap.assert_called_once_with('empty-bitmap')
        window.alternative.Set.assert_called_once_with([]); window.part.Set.assert_called_once_with([])
        with self.assertRaises(ValueError): window.gate.check(ticket)

    def test_queued_result_never_adopts_after_late_cancel_changed_inputs_or_close(self):
        for fault in ('cancel', 'changed', 'closed'):
            window = self.window(); generation = window.gate.generation; adopt = Mock()
            if fault == 'cancel': window.job.cancel()
            elif fault == 'changed': window.gate.invalidate()
            else: window.gate.close()
            with self.subTest(fault=fault):
                window_method('finish')(window, window.job, generation, {'success': True}, None, adopt)
                adopt.assert_not_called()
                if fault == 'closed': window.Destroy.assert_called_once()

    def test_worker_exception_keeps_receipt_and_never_adopts(self):
        window = self.window(); adopt = Mock()
        window_method('finish')(window, window.job, window.gate.generation, None, 'Native output failed', adopt)
        adopt.assert_not_called(); self.assertIsNone(window.qualified)
        self.assertIn('Native output failed', window.message.call_args.args[0])

    def test_close_requests_existing_worker_and_child_cleanup_before_destroy(self):
        window = self.window(); window.busy = True; window.routing = Mock(); event = Mock()
        window_method('close')(window, event)
        self.assertTrue(window.gate.closed); self.assertTrue(window.cancel_event.is_set())
        self.assertTrue(window.job.cancel_requested); window.routing.Close.assert_called_once()
        window.Hide.assert_called_once(); window.Destroy.assert_not_called(); event.Veto.assert_called_once()

    def test_parent_close_waits_for_both_worker_and_owned_routing_frame(self):
        window = self.window(); window.busy = True; window.routing = Mock(); window.gate.close()
        window.finish_close(); window.Destroy.assert_not_called()
        # Own worker finishes first: the existing child still controls cleanup.
        window_method('finish')(window, window.job, window.gate.generation, None, None, Mock())
        window.Destroy.assert_not_called()
        window.routing = None; window.finish_close(); window.Destroy.assert_called_once()
        window.finish_close(); window.Destroy.assert_called_once()

    def test_parent_notification_is_queued_once_only_after_both_cleanup_scopes(self):
        window = self.window(); window.busy = True; window.routing = Mock(); window.gate.close()
        callback = Mock(); wx = Mock(); calls = Mock()
        calls.attach_mock(window.Destroy, 'destroy'); calls.attach_mock(wx.CallAfter, 'call_after')
        window.finish_close = MethodType(window_method('finish_close', on_closed=callback, wx=wx), window)
        window.finish_close(); wx.CallAfter.assert_not_called()
        window.busy = False; window.finish_close(); wx.CallAfter.assert_not_called()
        window.routing = None; window.finish_close(); window.finish_close()
        self.assertEqual([row[0] for row in calls.mock_calls], ['destroy', 'call_after'])
        wx.CallAfter.assert_called_once_with(callback); callback.assert_not_called()
        wx.CallAfter.call_args.args[0]()
        callback.assert_called_once_with()

    def test_rendered_edit_is_never_mislabeled_as_first_alternative(self):
        tree = ast.parse(Path(pg.__file__).read_text())
        factory = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'create_window')
        cls = next(n for n in factory.body if isinstance(n, ast.ClassDef))
        render = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'render')
        self.assertIsInstance(render.args.defaults[-1], ast.Constant)
        self.assertIsNone(render.args.defaults[-1].value)
        self.assertIn('wx.NOT_FOUND', ast.unparse(render))
        self.assertIn('Edited draft.', ast.unparse(render))

    def test_late_cancel_during_guard_prevents_even_routing_frame_construction(self):
        window = self.window(); guard = Mock(); guard.check.side_effect = lambda _: window.job.cancel()
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard, witness={'candidate': '/owned/candidate.kicad_pcb'})
        with patch.object(gui, 'create_window') as factory:
            window_method('open_routing')(window, None)
        factory.assert_not_called(); self.assertIsNone(window.routing)

    def test_late_stale_guard_destroys_unshown_frame_without_routing(self):
        window = self.window(); guard = Mock(); guard.check.side_effect = [None, ValueError('source changed')]
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard, witness={'candidate': '/owned/candidate.kicad_pcb'})
        frame = Mock()
        with patch.object(gui, 'create_window', return_value=frame) as factory:
            window_method('open_routing')(window, None)
        factory.assert_called_once()
        self.assertEqual(factory.call_args.args, ('/owned/candidate.kicad_pcb',))
        self.assertIs(factory.call_args.kwargs['source_guard'], guard)
        self.assertTrue(callable(factory.call_args.kwargs['on_closed']))
        frame.Destroy.assert_called_once(); frame.Show.assert_not_called(); self.assertIsNone(window.routing)

    def test_explicit_routing_close_callback_releases_child_and_finishes_parent_close(self):
        window = self.window(); guard = Mock(); frame = Mock(source_guard=guard)
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard,
                                witness={'candidate': '/owned/candidate.kicad_pcb'})
        with patch.object(gui, 'create_window', return_value=frame) as factory:
            window_method('open_routing')(window, None)
        closed = factory.call_args.kwargs['on_closed']
        frame.Show.assert_called_once(); frame.Bind.assert_not_called()
        self.assertIs(window.routing, frame)
        window_method('close')(window, Mock())
        frame.Close.assert_called_once(); window.Destroy.assert_not_called()
        closed(); closed()
        self.assertIsNone(window.routing); window.Destroy.assert_called_once()

    def test_existing_routing_frame_is_not_duplicated_or_rebound(self):
        window = self.window(); guard = Mock(); frame = Mock(source_guard=guard); window.routing = frame
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard, witness={'candidate': '/owned/candidate.kicad_pcb'})
        with patch.object(gui, 'create_window') as factory:
            window_method('open_routing')(window, None)
            frame.Raise.assert_called_once(); factory.assert_not_called()
            frame.source_guard = Mock(); frame.Raise.reset_mock()
            window_method('open_routing')(window, None)
            frame.Raise.assert_not_called(); factory.assert_not_called()

    def test_qualification_cannot_overlap_closing_routing_frame(self):
        window = self.window(); window.routing = Mock(); window.start = Mock()
        window_method('qualify_draft')(window, None)
        window.start.assert_not_called(); self.assertIn('previous routing window', window.message.call_args.args[0])

    def test_qualification_adoption_rechecks_cancel_after_origin_guard(self):
        window = self.window(); window.start = Mock()
        window_method('qualify_draft')(window, None)
        adopt = window.start.call_args.args[2]
        guard = Mock(); guard.check.side_effect = lambda _: window.job.cancel()
        with self.assertRaises(ValueError):
            adopt(dict(guard=guard, witness={'candidate': '/owned/candidate.kicad_pcb'}))
        self.assertIsNone(window.qualified); window.findings.SetValue.assert_not_called()

    def test_actual_callback_rejects_and_records_without_inventing_acknowledgement(self):
        window = self.window(); window.gate.acknowledged = False
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp).resolve(); window.owned_workspace = lambda: folder
            window_method('reject_draft')(window, None)
            paths = list(folder.iterdir()); self.assertEqual(len(paths), 1)
            record = json.loads(paths[0].read_bytes())
            self.assertEqual(record['choice'], 'reject'); self.assertFalse(record['approval_granted'])
            self.assertFalse(record['execution_authorized']); self.assertFalse(record['human_PCB_approval'])
            self.assertIsNone(window.gate.review); self.assertFalse(window.gate.acknowledged)

    def test_factory_refuses_missing_app_worker_thread_and_nested_main(self):
        wx = Mock(); svg = Mock(); wx.GetApp.return_value = None
        with patch.dict(sys.modules, {'wx': wx, 'wx.svg': svg}):
            for callback in (False, True, 'approve', {}, 1):
                with self.subTest(callback=callback), self.assertRaises(ValueError):
                    pg.create_window('', on_closed=callback)
            with self.assertRaises(ValueError): pg.create_window('')
            wx.GetApp.return_value = object()
            with patch.object(threading, 'current_thread', return_value=object()):
                with self.assertRaises(ValueError): pg.create_window('')
            with self.assertRaises(ValueError): pg.main([])
        wx.App.assert_not_called()


if __name__ == '__main__':
    unittest.main()
