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
                           inspection={'source': '/owned/source.kicad_pcb'}, intent=None,
                           copper_plan=None, observation={})


class PlacementGuiTests(unittest.TestCase):
    def gate(self):
        gate = pg.ReviewGate(); gate.attach(review()); gate.acknowledged = True
        return gate

    def window(self):
        gate = self.gate()
        window = SimpleNamespace(gate=gate, job=gui.CliJob(), busy=False, routing=None, finalized=False,
            qualified=None, validation_revoked=False, pending_coordinates={}, editing_component=None,
            cancel_event=threading.Event(), inspection=gate.review.inspection,
            ack=Mock(), picture=Mock(), alternative=Mock(), part=Mock(), parts=Mock(),
            x=Mock(), y=Mock(), status=Mock(), timer=Mock(), findings=Mock(),
            copper_policy=Mock(), rigid_group=Mock(), original_group=Mock(), protected_names=Mock(), protected_route_ids=Mock(),
            current_review_settings=Mock(),
            refresh=Mock(), message=Mock(), present=Mock(), layout_panel=Mock(), Destroy=Mock(), Hide=Mock())
        window.copper_policy.GetSelection.return_value = 0
        window.rigid_group.GetValue.return_value = False
        window.rebuild_copper = MethodType(window_method('rebuild_copper'), window)
        window.revoke = MethodType(window_method('revoke'), window)
        window.edit_component = MethodType(window_method('edit_component'), window)
        window.finish_close = MethodType(window_method('finish_close'), window)
        return window

    def test_explicit_literal_ack_and_each_ticket_dependency(self):
        gate = self.gate(); ticket = gate.ticket(); self.assertIsNone(gate.check(ticket))
        for ack in (False, 1, 'yes', None):
            gate.acknowledged = ack
            with self.subTest(ack=ack), self.assertRaises(ValueError): gate.check(ticket)
        gate.acknowledged = True
        for field, mutation in (('revision', 2), ('pose', {'x': 4}), ('settings', {'selected': []}),
                                ('inspection', {'source': '/other.kicad_pcb'}),
                                ('copper_plan', {'changed': True}), ('observation', {'changed': True})):
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
            settings=dict(selected=['one'], region_nm=[0, 0, 10, 10]), moves={'one': [1, 1]}, alternatives=[{}],
            copper_plan=None, observation={})
        window.coordinates = Mock(); bitmap = Mock(); bitmap.GetSize.return_value = (850, 486)
        window.alternative.GetSelection.return_value = 0
        window.present = MethodType(window_method('present', bitmap_with_labels=Mock(return_value=bitmap)), window)
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

    def test_search_timeout_cancel_or_no_change_never_adopts_a_draft(self):
        window = self.window(); window.options = Mock(return_value={'search': {'seconds': 2}})
        window.start = Mock(); window.render = Mock()
        window_method('find_alternatives')(window, None)
        adopt = window.start.call_args.args[2]
        for status, message in (('budget_exhausted', 'time limit'),
                                ('no_changed_alternative', 'current constraints'),
                                ('cancelled', 'cancelled'), ('untrusted', 'unsupported result')):
            with self.subTest(status=status), patch.object(pg.intent, 'Review') as review:
                with self.assertRaisesRegex(ValueError, message):
                    adopt({'search': {'status': status, 'alternatives': [{'untrusted': 'draft'}]}})
                review.assert_not_called()
                window.render.assert_not_called()

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
        present = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'present')
        self.assertIn('Edited draft.', ast.unparse(present))

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

    def test_routing_handoff_keeps_chosen_output_and_mandatory_guard(self):
        window = self.window(); guard = Mock(); frame = Mock(source_guard=guard)
        window.routing_output_hint = '/chosen/candidate jobs'
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard,
                                witness={'candidate': '/owned/candidate.kicad_pcb'})
        with patch.object(gui, 'create_window', return_value=frame) as factory:
            window_method('open_routing')(window, None)
        frame.output.SetValue.assert_called_once_with('/chosen/candidate jobs')
        self.assertIs(factory.call_args.kwargs['source_guard'], guard)
        frame.Show.assert_called_once(); frame.Destroy.assert_not_called()

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

    def presentation_window(self):
        """Small presentation model; no claim of actual Native qualification."""
        window = self.window()
        item = dict(uuid='one', reference='J1', fixed_reasons=[])
        second = dict(uuid='two', reference='J2', fixed_reasons=[])
        draft = SimpleNamespace(revision=1, pose={'one': [1000000, 2000000], 'two': [3000000, 4000000]},
            moves={'one': [1000000, 2000000], 'two': [3000000, 4000000]}, alternatives=[{}, {}],
            inspection=dict(components=[item, second], observation={}, source='/owned/source.kicad_pcb'),
            settings=dict(selected=['one', 'two'], region_nm=[0, 0, 10000000, 10000000]), intent=None,
            copper_plan=None, observation={})
        window.gate.attach(draft); window.gate.acknowledged = True; window.inspection = draft.inspection
        window.alternative.GetSelection.return_value = 1; window.part.GetSelection.return_value = 1
        window.editing_component = 'two'
        window.x.GetValue.return_value = '3'; window.y.GetValue.return_value = '4'
        window.updating = False
        bitmap = Mock(); bitmap.GetSize.return_value = (850, 486)
        window.present = MethodType(window_method('present', wx=SimpleNamespace(NOT_FOUND=-1),
            bitmap_with_labels=Mock(return_value=bitmap)), window)
        witness = dict(candidate='/owned/separate/candidate.kicad_pcb', findings=dict(opens=2,
            blocking=0, warnings=1, exclusions=0, ignored_checks=[dict(key='retained_check', description='Retained ignored check')],
            findings=[dict(severity='warning', type='library_mismatch', description='Retained source warning')]))
        result = dict(ticket=window.gate.ticket(), witness=witness, guard=Mock())
        return window, result

    def test_native_adoption_presents_actual_findings_and_pending_routing_without_resetting_controls(self):
        window, result = self.presentation_window(); window.start = Mock()
        original = copy.deepcopy(window.gate.review.moves)
        window_method('qualify_draft')(window, None); adopt = window.start.call_args.args[2]
        with patch.object(pg.placement_view, 'render', return_value='<svg/>') as render:
            adopt(result)
        self.assertIs(window.qualified, result)
        self.assertEqual(render.call_args.kwargs['state'], 'Placement validated — routing pending')
        self.assertEqual(render.call_args.kwargs['title'], 'Placement review')
        text = window.findings.SetValue.call_args.args[0]
        self.assertIn('Status: placement validated; routing pending', text)
        self.assertNotIn('not reported', text)
        self.assertIn('2 opens; 0 blocking; 1 warnings; 0 exclusions', text)
        self.assertIn('Retained source warning', text); self.assertIn('Retained ignored check', text)
        self.assertIn('No electrical or manufacturing approval', text)
        self.assertEqual(window.gate.review.moves, original)
        window.part.SetSelection.assert_not_called(); window.alternative.SetSelection.assert_not_called()
        window.x.ChangeValue.assert_not_called(); window.y.ChangeValue.assert_not_called()

    def test_draft_and_edited_labels_use_current_selection_without_changing_it(self):
        window, _ = self.presentation_window()
        with patch.object(pg.placement_view, 'render', return_value='<svg/>') as render:
            window.present()
            self.assertEqual(render.call_args.kwargs['state'], 'Geometry draft — Native validation required')
            self.assertIn('Alternative 2.', window.findings.SetValue.call_args.args[0])
            window.alternative.GetSelection.return_value = -1; window.present()
        self.assertIn('Edited draft.', window.findings.SetValue.call_args.args[0])
        self.assertNotIn('Alternative 1.', window.findings.SetValue.call_args.args[0])
        window.part.SetSelection.assert_not_called(); window.alternative.SetSelection.assert_not_called()

    def test_options_preserve_explicit_inspected_scope(self):
        window, _ = self.presentation_window()
        window.inspection['observation']['scope'] = 'explicit-observed-scope'
        window.parts.IsChecked.side_effect = [True, True]
        window.region = [Mock() for _ in range(4)]
        for field, value in zip(window.region, ('0', '0', '10', '10')):
            field.GetValue.return_value = value
        expected = {'guarded': 'settings'}
        with patch.object(pg.intent, 'settings', return_value=expected) as settings, patch.object(pg.intent, 'facts') as facts:
            self.assertIs(window_method('options')(window), expected)
        settings.assert_called_once_with(['one', 'two'], [0, 0, 10000000, 10000000], scope='explicit-observed-scope')
        facts.assert_called_once_with(window.inspection, expected)

    def test_findings_use_inspected_scope_limits_without_inheriting_old_pth_claim(self):
        window, result = self.presentation_window()
        window.gate.review.inspection['limitations'] = ['Explicit scope: fixed-angle SMD translation only.']
        # Changing the inspected limitations also changes the bound ticket.
        result['ticket'] = window.gate.ticket(); window.qualified = result
        with patch.object(pg.placement_view, 'render', return_value='<svg/>'):
            window.present()
        text = window.findings.SetValue.call_args.args[0]
        self.assertIn('fixed-angle SMD translation only', text)
        self.assertNotIn('circular through-hole pads', text)
        self.assertIn('Placement validated', text)

    def test_pending_coordinate_text_replaces_success_without_altering_text_pose_or_selection(self):
        window, result = self.presentation_window(); window.qualified = result
        original = copy.deepcopy(window.gate.review.moves)
        window.x.GetValue.return_value = '26.'
        with patch.object(pg.placement_view, 'render', return_value='<svg/>') as render:
            window_method('pending_edit')(window, Mock())
        self.assertIsNone(window.qualified); self.assertTrue(window.gate.dirty)
        with self.assertRaises(ValueError): window.gate.check(result['ticket'])
        self.assertEqual(render.call_args.kwargs['state'], 'Pending edits — displayed pose has not been updated')
        text = window.findings.SetValue.call_args.args[0]
        self.assertNotIn('Placement validated', text); self.assertNotIn('Native findings:', text)
        self.assertIn('No current Native placement validation', text)
        self.assertEqual(window.gate.review.moves, original)
        window.part.SetSelection.assert_not_called(); window.alternative.SetSelection.assert_not_called()
        window.x.ChangeValue.assert_not_called(); window.y.ChangeValue.assert_not_called()

    def test_cancel_and_acknowledgement_change_remove_success_and_revoke_routing(self):
        for action in ('cancel_work', 'acknowledge'):
            window, result = self.presentation_window(); window.qualified = result
            window.ack.GetValue.return_value = False
            with self.subTest(action=action), patch.object(pg.placement_view, 'render', return_value='<svg/>') as render:
                window_method(action)(window, None)
            self.assertIsNone(window.qualified)
            with self.assertRaises(ValueError): window.gate.check(result['ticket'])
            self.assertEqual(render.call_args.kwargs['state'], 'Validation revoked — review and validate again')
            self.assertNotIn('Placement validated', window.findings.SetValue.call_args.args[0])

    def test_source_settings_and_rejection_clear_success_findings_and_diagram(self):
        for action in ('source_changed', 'settings_changed', 'reject_draft'):
            window, result = self.presentation_window(); window.qualified = result
            window.owned_workspace = Mock(side_effect=ValueError('receipt write deliberately unavailable'))
            with self.subTest(action=action): window_method(action)(window, Mock())
            self.assertIsNone(window.qualified); self.assertIsNone(window.gate.review)
            window.picture.SetBitmap.assert_called_once_with('empty-bitmap')
            text = window.findings.SetValue.call_args.args[0]
            self.assertIn('No current placement draft or validation', text)
            self.assertNotIn('Placement validated', text)
            with self.assertRaises(ValueError): window.gate.check(result['ticket'])

    def test_failed_edit_retains_pose_and_pending_text_but_not_qualification(self):
        window, result = self.presentation_window(); window.qualified = result
        original = copy.deepcopy(window.gate.review.moves)
        window.gate.review.edit_many = Mock(side_effect=ValueError('outside allowed rectangle'))
        with patch.object(pg.placement_view, 'render', return_value='<svg/>') as render:
            window_method('edit')(window, None)
        self.assertIsNone(window.qualified); self.assertTrue(window.gate.dirty)
        self.assertIn('Pending edits', render.call_args.kwargs['state'])
        self.assertEqual(window.gate.review.moves, original)
        window.x.ChangeValue.assert_not_called(); window.y.ChangeValue.assert_not_called()
        window.part.SetSelection.assert_not_called(); window.alternative.SetSelection.assert_not_called()
        self.assertIn('previous pose retained', window.message.call_args.args[0])

    def test_component_switch_preserves_pending_text_and_loads_committed_selection(self):
        window, result = self.presentation_window(); window.present = Mock()
        window.coordinates = MethodType(window_method('coordinates'), window)
        window.x.GetValue.return_value = '20.'; window.y.GetValue.return_value = '10.4'
        window_method('pending_edit')(window, Mock())
        self.assertEqual(window.pending_coordinates, {'two': ['20.', '10.4']})
        queued = []; wx = SimpleNamespace(CallAfter=lambda action: queued.append(action))
        # Popup still reports the previous part during its event; commits later.
        window_method('select_part', wx=wx)(window, None)
        window.part.GetSelection.return_value = 0
        queued.pop()()
        self.assertEqual(window.editing_component, 'one')
        window.x.ChangeValue.assert_called_with('1'); window.y.ChangeValue.assert_called_with('2')
        self.assertTrue(window.gate.dirty)
        with self.assertRaises(ValueError): window.gate.check(result['ticket'])
        window.part.GetSelection.return_value = 1
        window_method('select_part', wx=wx)(window, None); queued.pop()()
        window.x.ChangeValue.assert_called_with('20.'); window.y.ChangeValue.assert_called_with('10.4')
        self.assertEqual(window.pending_coordinates, {'two': ['20.', '10.4']})

    def test_queued_component_load_cannot_overwrite_a_newer_edit_or_review(self):
        for action in ('edit', 'discard', 'close'):
            window, _ = self.presentation_window(); window.present = Mock(); window.coordinates = Mock()
            queued = []; wx = SimpleNamespace(CallAfter=lambda function: queued.append(function))
            window_method('select_part', wx=wx)(window, None)
            if action == 'close': window.gate.close()
            elif action == 'discard': window.revoke(discard=True)
            else: window_method('pending_edit')(window, Mock())
            queued.pop()()
            window.coordinates.assert_not_called()

    def test_unloaded_component_text_cannot_be_assigned_to_another_part(self):
        for action in ('pending_edit', 'edit'):
            window, result = self.presentation_window(); window.present = Mock()
            window.gate.review.edit_many = Mock(); window.part.GetSelection.return_value = 0
            # Coordinates still belong to part two while popup now displays one.
            window.pending_coordinates = {'two': ['20', '10.4']}
            window_method(action)(window, Mock())
            self.assertEqual(window.pending_coordinates, {'two': ['20', '10.4']})
            window.gate.review.edit_many.assert_not_called(); self.assertTrue(window.gate.dirty)
            self.assertIsNone(window.qualified)
            with self.assertRaises(ValueError): window.gate.check(result['ticket'])
            self.assertIn('Choose the component again', window.message.call_args.args[0])

    def test_update_submits_all_pending_components_once_and_keeps_refusal_atomic(self):
        for rejected in (False, True):
            window, _ = self.presentation_window(); window.present = Mock(); window.render = Mock()
            window.pending_coordinates = {'one': ['16.2', '10.4']}
            window.x.GetValue.return_value = '20.8'; window.y.GetValue.return_value = '10.4'
            window.gate.review.edit_many = Mock(side_effect=ValueError('overlap') if rejected else None)
            original = copy.deepcopy(window.gate.review.moves)
            window_method('edit')(window, None)
            window.gate.review.edit_many.assert_called_once_with({'one': ['16.2', '10.4'], 'two': ['20.8', '10.4']})
            self.assertFalse(window.gate.acknowledged)
            if rejected:
                window.render.assert_not_called(); self.assertTrue(window.gate.dirty)
                self.assertEqual(window.gate.review.moves, original)
                self.assertEqual(len(window.pending_coordinates), 2)
            else:
                window.render.assert_called_once_with(); self.assertFalse(window.gate.dirty)

    def test_explicit_render_or_discard_clears_pending_coordinates(self):
        window, _ = self.presentation_window(); window.present = Mock(); window.coordinates = Mock()
        window.pending_coordinates = {'two': ['20.', '10.4']}
        window_method('render', wx=SimpleNamespace(NOT_FOUND=-1))(window)
        self.assertEqual(window.pending_coordinates, {})
        window.pending_coordinates = {'two': ['20.', '10.4']}
        window.revoke(discard=True)
        self.assertEqual(window.pending_coordinates, {}); self.assertIsNone(window.editing_component)

    def test_invalid_alternative_cannot_clear_dirty_batch_or_reenable_approval(self):
        window, _ = self.presentation_window(); window.present = Mock(); window.render = Mock()
        window.pending_coordinates = {'two': ['20.', '10.4']}
        window.gate.review.choose = Mock(side_effect=ValueError('Unavailable alternative'))
        window_method('choose_alternative')(window, None)
        self.assertTrue(window.gate.dirty); self.assertFalse(window.gate.acknowledged)
        self.assertEqual(window.pending_coordinates, {'two': ['20.', '10.4']})
        window.render.assert_not_called()

    def test_invalid_alternative_cannot_approve_unbound_typed_coordinates(self):
        window, _ = self.presentation_window(); window.present = Mock(); window.render = Mock()
        window.part.GetSelection.return_value = 0  # Text still belongs to part two.
        window_method('pending_edit')(window, Mock())
        self.assertTrue(window.gate.dirty); self.assertEqual(window.pending_coordinates, {})
        window.gate.review.choose = Mock(side_effect=ValueError('Unavailable alternative'))
        window_method('choose_alternative')(window, None)
        self.assertTrue(window.gate.dirty)
        window.ack.GetValue.return_value = True
        window_method('acknowledge')(window, None)
        with self.assertRaises(ValueError): window.gate.ticket()
        self.assertFalse(window.gate.acknowledged); window.render.assert_not_called()

    def test_redraw_failure_rolls_back_real_atomic_edit_and_preserves_typed_batch(self):
        from autorouter import placement_intent as intent
        from experiments.placement_native_proposal_v1 import contract, multipad_fixture as fixture
        with tempfile.TemporaryDirectory(prefix='placement-redraw-') as temporary:
            board = fixture.write_project(Path(temporary).resolve() / 'source')
            inspected = intent.inspect_saved(board)
            selected = [fixture.uid(ref + '-footprint') for ref in ('J1', 'J2')]
            settings = intent.settings(selected, [7000000, 7000000, 31000000, 13000000])
            moves = dict(zip(selected, [[14000000, 10000000], [20000000, 10000000]]))
            pose = contract.validate_moves(inspected['observation'], moves,
                scope=contract.MULTIPAD_SCOPE, selected=selected, region_nm=settings['region_nm'])
            review = intent.Review(dict(kind='autorouter.placement-proposals.v1', inspection=inspected,
                settings=settings, search=dict(status='proposals_ready', alternatives=[dict(candidate=pose)])))
            window, _ = self.presentation_window(); window.gate.attach(review)
            window.editing_component = selected[1]; window.part.GetSelection.return_value = 1
            window.pending_coordinates = {selected[0]: ['20', '10']}
            window.x.GetValue.return_value = '14'; window.y.GetValue.return_value = '10'
            window.coordinates = MethodType(window_method('coordinates'), window)
            window.render = MethodType(window_method('render', wx=SimpleNamespace(NOT_FOUND=-1)), window)
            window.present = Mock(side_effect=RuntimeError('deliberate bitmap failure'))
            previous = copy.deepcopy((review.pose, review.moves, review.revision))
            window_method('edit')(window, None)
            self.assertEqual((review.pose, review.moves, review.revision), previous)
            self.assertEqual(window.pending_coordinates, {selected[0]: ['20', '10'], selected[1]: ['14', '10']})
            window.x.ChangeValue.assert_called_with('14'); window.y.ChangeValue.assert_called_with('10')
            window.part.SetSelection.assert_called_with(1)
            self.assertIsNone(review.intent); self.assertTrue(window.gate.dirty)
            self.assertFalse(window.gate.acknowledged); self.assertIsNone(window.qualified)
            self.assertIn('previous pose retained', window.message.call_args.args[0])

    def test_stale_origin_at_routing_open_removes_success_and_handoff_authority(self):
        window, result = self.presentation_window(); window.qualified = result
        result['guard'].check.side_effect = ValueError('source changed on disk')
        with patch.object(pg.placement_view, 'render', return_value='<svg/>') as render, patch.object(gui, 'create_window') as factory:
            window_method('open_routing')(window, None)
        factory.assert_not_called(); self.assertIsNone(window.qualified)
        self.assertIn('Validation revoked', render.call_args.kwargs['state'])
        self.assertNotIn('Placement validated', window.findings.SetValue.call_args.args[0])
        self.assertIn('source changed on disk', window.message.call_args.args[0])

    def test_presentation_cannot_keep_success_after_review_ticket_changes(self):
        window, result = self.presentation_window(); window.qualified = result
        window.gate.review.revision += 1
        with patch.object(pg.placement_view, 'render', return_value='<svg/>') as render:
            window.present()
        self.assertIsNone(window.qualified)
        self.assertIn('Validation revoked', render.call_args.kwargs['state'])
        self.assertNotIn('Placement validated', window.findings.SetValue.call_args.args[0])

    def test_refusal_or_cancellation_keeps_unapplied_coordinate_text_dirty(self):
        for action in ('present', 'cancel_work', 'open_routing', 'finish'):
            window, result = self.presentation_window(); window.qualified = result
            window.gate.invalidate(dirty=True); window.x.GetValue.return_value = '26.'
            with self.subTest(action=action), patch.object(pg.placement_view, 'render', return_value='<svg/>'):
                if action == 'present': window.present()
                elif action == 'finish':
                    window_method('finish')(window, window.job, window.gate.generation,
                                            None, 'validation refused', Mock())
                else: window_method(action)(window, None)
            self.assertIsNone(window.qualified); self.assertTrue(window.gate.dirty)
            window.gate.acknowledged = True
            with self.assertRaises(ValueError): window.gate.ticket()
            window.x.ChangeValue.assert_not_called(); window.y.ChangeValue.assert_not_called()
            self.assertIn('Pending edits', window.findings.SetValue.call_args.args[0])

    def test_render_and_bitmap_failure_cannot_prevent_cancel_or_leave_success(self):
        for failure in ('render', 'bitmap'):
            window, result = self.presentation_window(); window.qualified = result
            window.busy = True
            original = copy.deepcopy(window.gate.review.moves)
            def fail(*args, **kwargs):
                self.assertTrue(window.cancel_event.is_set())
                self.assertTrue(window.job.cancel_requested)
                raise RuntimeError('deliberate ' + failure + ' failure')
            if failure == 'bitmap':
                window.present = MethodType(window_method('present', wx=SimpleNamespace(NOT_FOUND=-1),
                    bitmap_with_labels=fail), window)
            with self.subTest(failure=failure), patch.object(pg.placement_view, 'render',
                    side_effect=fail if failure == 'render' else None, return_value='<svg/>'):
                window_method('cancel_work')(window, None)
            self.assertIsNone(window.qualified)
            with self.assertRaises(ValueError): window.gate.check(result['ticket'])
            window.picture.SetBitmap.assert_called_once_with('empty-bitmap')
            text = window.findings.SetValue.call_args.args[0]
            self.assertIn('Placement preview refused: deliberate ' + failure + ' failure', text)
            self.assertIn('No current placement validation', text)
            self.assertNotIn('Placement validated', text)
            self.assertEqual(window.gate.review.moves, original)
            window.part.SetSelection.assert_not_called(); window.alternative.SetSelection.assert_not_called()
            window.x.ChangeValue.assert_not_called(); window.y.ChangeValue.assert_not_called()

    def test_stale_presentation_failure_keeps_revocation_and_pending_edits_visible(self):
        for failure in ('render', 'bitmap'):
            window, result = self.presentation_window(); window.qualified = result
            window.gate.invalidate(dirty=True); window.x.GetValue.return_value = '26.'
            original = copy.deepcopy(window.gate.review.moves)
            bitmap = Mock(side_effect=RuntimeError('deliberate bitmap failure'))
            window.present = MethodType(window_method('present', wx=SimpleNamespace(NOT_FOUND=-1),
                bitmap_with_labels=bitmap), window)
            with self.subTest(failure=failure), patch.object(pg.placement_view, 'render',
                    side_effect=RuntimeError('deliberate render failure') if failure == 'render' else None,
                    return_value='<svg/>') as render:
                window.present()
            self.assertEqual(render.call_count, 1)  # Stale-ticket re-entry is bounded.
            self.assertIsNone(window.qualified); self.assertTrue(window.gate.dirty)
            with self.assertRaises(ValueError): window.gate.check(result['ticket'])
            window.picture.SetBitmap.assert_called_once_with('empty-bitmap')
            text = window.findings.SetValue.call_args.args[0]
            self.assertIn('Placement preview refused: deliberate ' + failure + ' failure', text)
            self.assertIn('pending coordinate text are retained', text)
            self.assertNotIn('Placement validated', text)
            self.assertEqual(window.gate.review.moves, original)
            window.part.SetSelection.assert_not_called(); window.alternative.SetSelection.assert_not_called()
            window.x.ChangeValue.assert_not_called(); window.y.ChangeValue.assert_not_called()

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
