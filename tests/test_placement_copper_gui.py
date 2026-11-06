"""Owned-source placement control tests; no actual wx or Native qualification."""
import copy
import json
from pathlib import Path
import tempfile
from types import MethodType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import gui, placement_copper as copper, placement_gui as pg, placement_intent as intent
from experiments.placement_native_proposal_v1 import contract, multipad_fixture, ordinary_fixture
from tests.test_gui import window_method as route_method
from tests.test_placement_copper import REGION, raw, source_tree
from tests import test_placement_gui as base
from tests.test_placement_gui import window_method


def text_control(value=''):
    control = Mock()
    control.GetValue.return_value = value
    control.SetValue.side_effect = lambda changed: setattr(control.GetValue, 'return_value', changed)
    control.ChangeValue.side_effect = control.SetValue.side_effect
    return control


def choice_control(value=0):
    control = Mock()
    control.GetSelection.return_value = value
    control.SetSelection.side_effect = lambda changed: setattr(control.GetSelection, 'return_value', changed)
    return control


def parts_control(rows, checked):
    control = Mock(); state = set(checked)
    control.IsChecked.side_effect = lambda index: index in state
    control.Check.side_effect = lambda index, value: state.add(index) if value else state.discard(index)
    control.Set.side_effect = lambda labels: state.clear()
    return control


def routing_frame():
    values = dict(scope=[('Whole', 'whole_board_unlocked_routing'), ('Partial', 'partial_completion'), ('Selected', 'selected_nets')],
        profile=[('Standard', 'standard'), ('Tuned', 'tuned'), ('Complete', 'completion-only')],
        adapter=[('Both', 'both'), ('None', 'none')], layers=[('All', 'source_all'), ('Front', ['F.Cu'])],
        scoring_preference=[('Default', None), ('Low', 'via_low')])
    frame = SimpleNamespace(values=values, choices={key: choice_control() for key in values},
        method=choice_control(2), seconds=text_control('15'), nets=text_control('UNRELATED'),
        status=Mock(), refresh=Mock(), Show=Mock(), Destroy=Mock())
    frame.config = MethodType(route_method('config'), frame)
    return frame


class CopperPlacementGui(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='placement-copper-gui-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.board = ordinary_fixture.write_project(self.root / 'source')
        self.source = raw(source_tree()); self.board.write_bytes(self.source)
        self.inspection = intent.inspect_saved(self.board)
        self.selected = ordinary_fixture.selected()
        self.settings = intent.settings(self.selected, REGION, scope=contract.ORDINARY_SCOPE,
                                        copper_policy=intent.COPPER_POLICY)
        self.original = gui.source_inventory(self.board)

    def window(self, *, rebuild=True, reviewed=False):
        window = base.PlacementGuiTests().window()
        window.board = text_control(str(self.board)); window.inspection = self.inspection
        window.copper_policy = choice_control(1 if rebuild else 0)
        window.protected_names = text_control(); window.protected_route_ids = text_control()
        window.parts = parts_control(self.inspection['components'],
            [i for i, row in enumerate(self.inspection['components']) if row['uuid'] in self.selected])
        window.region = [text_control(pg.mm(number)) for number in REGION]
        window.updating = False
        for method in ('options', 'current_review_settings', 'refresh_parts'):
            setattr(window, method, MethodType(window_method(method), window))
        if reviewed:
            plan = intent.copper_plan(self.inspection, self.settings)
            observation = contract.inspect_board(copper.prepare(self.source, plan), scope=contract.ORDINARY_SCOPE)
            moves = dict(zip(self.selected, ([14_000_000, 10_000_000], [24_000_000, 10_000_000])))
            candidate = contract.validate_moves(observation, moves, scope=contract.ORDINARY_SCOPE,
                                                selected=self.selected, region_nm=REGION)
            review = intent.Review(dict(kind='autorouter.placement-proposals.v1', inspection=self.inspection,
                settings=self.settings, copper_plan=plan,
                search=dict(status='proposals_ready', alternatives=[dict(candidate=candidate)])))
            window.gate.attach(review); window.gate.acknowledged = True
            window.alternative.GetSelection.return_value = 0
        else:
            window.gate.review = None; window.gate.acknowledged = False
        return window

    def test_default_preserves_all_and_only_explicit_option_enables_routed_parts(self):
        window = self.window(rebuild=False)
        with self.assertRaises(ValueError): window.options()
        routed = next(row for row in self.inspection['components'] if row['uuid'] == self.selected[0])
        self.assertIn('fixed (routed net)', pg.component_label(routed))
        self.assertIn('reroute required', pg.component_label(routed, rebuild=True))
        locked = dict(routed, fixed_reasons=[pg.ROUTED_REASON, 'Locked in KiCad'])
        self.assertTrue(pg.blocking_reasons(locked, rebuild=True))
        self.assertIn('fixed (locked)', pg.component_label(locked, rebuild=True))
        ineligible = dict(routed, fixed_reasons=[pg.ROUTED_REASON, 'Unsupported selected pad geometry'])
        self.assertTrue(pg.blocking_reasons(ineligible, rebuild=True))
        window.copper_policy.SetSelection(1)
        self.assertEqual(window.options(), self.settings)
        window.protected_names.SetValue('ROUTE_A')
        with self.assertRaises(ValueError): window.options()
        window.protected_names.SetValue('KEEP')
        self.assertEqual(window.options()['protected_names'], ['KEEP'])
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_advanced_fields_are_exact_and_unsupported_policy_refuses(self):
        window = self.window()
        keep = intent.copper_plan(self.inspection, self.settings)['protected_routes'][0]['uuid']
        window.protected_names.SetValue('KEEP\nGND\n')
        window.protected_route_ids.SetValue(keep + '\n')
        value = window.options()
        self.assertEqual(value['protected_names'], ['KEEP', 'GND'])
        self.assertEqual(value['protected_route_ids'], [keep])
        for text in (keep + '\n' + keep, 'not-a-uuid', ' ' + keep):
            window.protected_route_ids.SetValue(text)
            with self.subTest(text=text), self.assertRaises(ValueError): window.options()
        for selection in (-1, 2, True):
            window.copper_policy.GetSelection.return_value = selection
            with self.subTest(selection=selection), self.assertRaises(ValueError): window.options()

    def test_policy_change_revokes_immediately_then_reads_committed_popup(self):
        window = self.window(reviewed=True)
        window.qualified = dict(ticket=window.gate.ticket())
        queued = []; wx = SimpleNamespace(CallAfter=queued.append)
        window_method('policy_changed', wx=wx)(window, Mock())
        self.assertIsNone(window.gate.review); self.assertIsNone(window.qualified)
        # The event saw rebuild; the Cocoa popup later commits preserve-all.
        window.copper_policy.SetSelection(0)
        queued.pop()()
        self.assertFalse(any(window.parts.IsChecked(i) for i in range(len(self.inspection['components']))))
        index = next(i for i, row in enumerate(self.inspection['components']) if row['uuid'] == self.selected[0])
        self.assertIn('fixed (routed net)', window.parts.Set.call_args.args[0][index])
        self.assertIn('no copper was changed', window.message.call_args.args[0])

    def test_checkbox_cannot_select_locked_or_ineligible_parts_in_rebuild_mode(self):
        window = self.window()
        fixed_index = next(i for i, row in enumerate(self.inspection['components']) if row['reference'] == 'J5')
        window.parts.Check(fixed_index, True)
        window_method('settings_changed')(window, Mock())
        self.assertFalse(window.parts.IsChecked(fixed_index))
        for i, row in enumerate(self.inspection['components']):
            if row['uuid'] in self.selected: self.assertTrue(window.parts.IsChecked(i))

    def test_live_review_uses_prepared_copper_and_truthful_plan_findings(self):
        window = self.window(reviewed=True); review = window.gate.review
        bitmap = Mock(); bitmap.GetSize.return_value = (850, 500)
        with patch.object(pg.placement_view, 'render', return_value='<svg/>') as render:
            window_method('present', bitmap_with_labels=Mock(return_value=bitmap),
                          wx=SimpleNamespace(NOT_FOUND=-1))(window)
        self.assertEqual(render.call_args.args[0], review.observation)
        self.assertEqual(render.call_args.args[0]['route_count'], 2)
        self.assertEqual(review.inspection['observation']['route_count'], 5)
        text = window.findings.SetValue.call_args.args[0]
        self.assertIn('3 existing routes to rebuild; 2 routes retained', text)
        self.assertIn('ROUTE_A, ROUTE_B', text)
        self.assertIn('not approval to execute', text)
        self.assertIn('two-pad SMD', text)
        self.assertNotIn('Original copper and unselected/fixed components are preserved.', text)
        self.assertNotIn('Every existing copper item is preserved.', text)
        self.assertNotIn('Placement validated', text)

    def test_displayed_policy_and_protection_changes_without_events_refuse_review(self):
        window = self.window(reviewed=True); review = window.gate.review
        with patch.object(intent, 'facts', side_effect=AssertionError('display comparison must not repeat geometry work')):
            window.current_review_settings(review)
        for mode in ('policy', 'protected', 'region', 'source'):
            window.copper_policy.SetSelection(1); window.protected_names.SetValue('')
            window.region[0].SetValue('7'); window.board.SetValue(str(self.board))
            if mode == 'policy': window.copper_policy.SetSelection(0)
            elif mode == 'protected': window.protected_names.SetValue('KEEP')
            elif mode == 'region': window.region[0].SetValue('7.1')
            else:
                other = self.root / 'other.kicad_pcb'; other.write_bytes(self.source)
                window.board.SetValue(str(other))
            with self.subTest(mode=mode), self.assertRaises(ValueError): window.current_review_settings(review)

    def test_stale_policy_blocks_qualification_and_queued_native_adoption(self):
        window = self.window(reviewed=True); window.start = Mock()
        window_method('qualify_draft')(window, None)
        self.assertEqual(window.start.call_count, 1)
        adopt = window.start.call_args.args[2]
        window.copper_policy.SetSelection(0)
        result = dict(guard=Mock(), witness={'candidate': str(self.board)}, ticket=window.gate.ticket())
        with self.assertRaises(ValueError): adopt(result)
        result['guard'].check.assert_called_once(); self.assertIsNone(window.qualified)
        window.start.reset_mock()
        window_method('qualify_draft')(window, None)
        window.start.assert_not_called()
        self.assertIn('Qualification refused', window.message.call_args.args[0])

    def test_late_policy_change_during_origin_read_cannot_adopt_native_result(self):
        window = self.window(reviewed=True); window.start = Mock()
        window_method('qualify_draft')(window, None)
        adopt = window.start.call_args.args[2]
        guard = Mock(); guard.check.side_effect = lambda _: window.copper_policy.SetSelection(0)
        result = dict(guard=guard, witness={'candidate': str(self.board)}, ticket=window.gate.ticket())
        with self.assertRaises(ValueError): adopt(result)
        self.assertIsNone(window.qualified)

    def test_late_review_revocation_after_last_input_read_destroys_unshown_routing_frame(self):
        window = self.window(reviewed=True); frame = routing_frame(); guard = Mock()
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard, witness={'candidate': str(self.board)})
        check = window.current_review_settings; calls = []
        def checked(review):
            check(review); calls.append(True)
            if len(calls) == 2: window.gate.invalidate()
        window.current_review_settings = checked
        with patch.object(gui, 'create_window', return_value=frame):
            window_method('open_routing')(window, None)
        self.assertIsNone(window.routing); self.assertIsNone(window.qualified)
        frame.Destroy.assert_called_once(); frame.Show.assert_not_called()

    def test_persistent_v3_save_then_v2_and_v1_reload_without_implicit_execution(self):
        window = self.window(); window.copper_policy.SetSelection(0)
        value = copy.deepcopy(self.settings); value['protected_names'] = ['KEEP']
        path = self.root / 'settings.json'; path.write_text(json.dumps(value))
        dialog = Mock(); dialog.__enter__ = Mock(return_value=dialog); dialog.__exit__ = Mock(return_value=False)
        dialog.ShowModal.return_value = 1; dialog.GetPath.return_value = str(path)
        wx = SimpleNamespace(FileDialog=Mock(return_value=dialog), FD_OPEN=1, FD_FILE_MUST_EXIST=2, ID_OK=1)
        window_method('load_settings', wx=wx)(window, None)
        self.assertEqual(window.copper_policy.GetSelection(), 1)
        self.assertEqual(window.protected_names.GetValue(), 'KEEP')
        self.assertEqual(window.options(), value)
        self.assertIsNone(window.gate.review); self.assertIsNone(window.qualified)
        saved = self.root / 'saved-v3.json'; dialog.GetPath.return_value = str(saved)
        wx.FD_SAVE = 4
        window_method('save_settings', wx=wx)(window, None)
        self.assertEqual(intent.load_settings(saved), value)
        dialog.GetPath.return_value = str(path)
        # An unrouted owned source legitimately admits unchanged preserve-all v2.
        board = ordinary_fixture.write_project(self.root / 'unrouted source')
        window.board.SetValue(str(board)); window.inspection = intent.inspect_saved(board)
        legacy = intent.settings(self.selected, REGION, scope=contract.ORDINARY_SCOPE)
        path.write_text(json.dumps(legacy))
        window_method('load_settings', wx=wx)(window, None)
        self.assertEqual(window.copper_policy.GetSelection(), 0)
        self.assertEqual(window.protected_names.GetValue(), '')
        self.assertEqual(window.protected_route_ids.GetValue(), '')
        self.assertEqual(window.options(), legacy)
        board = multipad_fixture.write_project(self.root / 'multipad source')
        window.board.SetValue(str(board)); window.inspection = intent.inspect_saved(board)
        selected = [multipad_fixture.uid(ref + '-footprint') for ref in ('J1', 'J2')]
        old = intent.settings(selected, REGION)
        path.write_text(json.dumps(old))
        window_method('load_settings', wx=wx)(window, None)
        self.assertEqual(window.options(), old)
        self.assertEqual(window.options()['schema'], 1)

    def test_routing_prefill_is_exact_visible_and_never_starts_or_accepts(self):
        frame = routing_frame(); plan = intent.copper_plan(self.inspection, self.settings)
        pg.prefill_copper_routing(frame, plan)
        actual = frame.config()
        self.assertEqual(actual, dict(gui.pref.DEFAULTS, scope='selected_nets', profile='completion-only',
            nets=['ROUTE_A', 'ROUTE_B'], seconds=90))
        self.assertEqual(frame.method.GetSelection(), 0)
        self.assertEqual(frame.seconds.GetValue(), '90')
        self.assertEqual(frame.nets.GetValue(), 'ROUTE_A\nROUTE_B')
        self.assertIn('no route or acceptance has started', frame.status.SetLabel.call_args.args[0])
        frame.Show.assert_not_called()
        frame.nets.SetValue.side_effect = None
        frame.nets.GetValue.return_value = 'WRONG'
        with self.assertRaises(ValueError): pg.prefill_copper_routing(frame, plan)

    def test_open_routing_prefills_before_show_and_stale_current_policy_refuses(self):
        window = self.window(reviewed=True); frame = routing_frame(); guard = Mock()
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard, witness={'candidate': str(self.board)})
        with patch.object(gui, 'create_window', return_value=frame):
            window_method('open_routing')(window, None)
        frame.Show.assert_called_once()
        self.assertEqual(frame.config()['nets'], ['ROUTE_A', 'ROUTE_B'])
        self.assertEqual(frame.config()['seconds'], 90)
        window.routing = None; window.copper_policy.SetSelection(0)
        with patch.object(gui, 'create_window') as factory:
            window_method('open_routing')(window, None)
        factory.assert_not_called(); self.assertIsNone(window.qualified)


if __name__ == '__main__':
    unittest.main()
