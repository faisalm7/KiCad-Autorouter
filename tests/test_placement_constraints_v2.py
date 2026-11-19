"""Versioned settings only. Real source/protection validation, no inference or CAD."""
import copy
import json
from pathlib import Path
import tempfile
from types import MethodType
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

from autorouter import design_intent as design, gui, placement_intent as placement
from autorouter import placement_gui as pg
from experiments.placement_native_proposal_v1 import multipad_fixture
from tests import test_placement_copper_gui as controls, test_placement_gui as ui
from tests import test_placement_copper as copper_fixtures


class ConstraintProposal(unittest.TestCase):
    tool = 'propose_placement_constraints_v2'
    request = 'Select J1 and J2, use X 8–30 mm and Y 8–12 mm, and allow 60 seconds to route.'

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='constraint-v2-', dir=Path.cwd())
        self.addCleanup(tmp.cleanup)
        self.board = multipad_fixture.write_project(Path(tmp.name) / 'source')
        self.inspection = placement.inspect_saved(self.board)
        self.ids = {row['reference']: row['uuid'] for row in self.inspection['components']}
        self.controls = dict(selected=[], fixed=[self.ids['J3']], region_nm=None,
            region_limit_nm=[7_000_000, 7_000_000, 31_000_000, 13_000_000],
            route_seconds=90, policy=dict(scope=self.inspection['observation']['scope'],
                copper_policy=placement.COPPER_POLICY, protected_names=['KEEP'],
                protected_route_ids=[]))
        self.args = dict(selected_refs=['J1', 'J2'], region_nm=[8_000_000, 8_000_000, 30_000_000, 12_000_000],
                         route_seconds=60)

    def review(self):
        return design.PlacementConstraintReview(self.inspection, self.controls,
                                                request=self.request, revision=1)

    def receive(self, review, args=None, **current):
        return review.receive(self.tool, self.args if args is None else args, self.controls,
                              **(dict(request=self.request, revision=1, source=self.board) | current))

    def adopt(self, review, offer, **current):
        return review.adopt(offer, self.controls,
                            **(dict(request=self.request, revision=1, source=self.board) | current))

    def test_propose_from_blank_draft_and_deliberately_adopt_only_settings(self):
        before = gui.source_inventory(self.board)
        original = copy.deepcopy(self.controls)
        review = self.review()
        context = review.model_context()
        self.assertEqual(context['current']['selected_refs'], [])
        self.assertIn({'ref': 'J3', 'fixed': True}, context['components'])
        self.assertNotIn(str(self.board.parent), json.dumps(context))
        self.assertNotIn(self.ids['J1'], json.dumps(context))
        with patch.object(placement, 'propose', side_effect=AssertionError('No placement search')):
            offer = self.receive(review)
            self.assertIs(offer['execution_authorized'], False)
            self.assertIs(offer['approval_granted'], False)
            self.assertEqual(offer['after'], self.args)
            self.assertEqual(offer['copper_plan']['incident_names'], ['ROUTE_A', 'ROUTE_B'])
            self.assertEqual(offer['placement_settings']['protected_names'], ['KEEP'])
            values = self.adopt(review, offer)
        self.assertEqual(values['placement_settings'], placement.validate_settings(offer['placement_settings']))
        self.assertEqual(values['route_seconds'], 60)
        self.assertEqual(self.controls, original)
        self.assertEqual(gui.source_inventory(self.board), before)
        with self.assertRaises(design.PendingContextChanged):
            self.adopt(review, offer)

    def test_malformed_unknown_duplicate_fixed_and_boundary_edits_refuse(self):
        for edit in (dict(selected_refs=['J1', 'connector']), dict(selected_refs=['J1', 'J1']),
                     dict(selected_refs=['J1', 'J3']), dict(region_nm=[0, 0, 1, 1]),
                     dict(route_seconds=True), dict(approved=True)):
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                self.receive(self.review(), self.args | edit)

    def test_locked_or_protected_context_is_not_overridden(self):
        self.controls['fixed'] = []
        # J3 lies on KEEP. A proposed selection cannot grant copper permission.
        with self.assertRaises(ValueError):
            self.receive(self.review(), self.args | dict(selected_refs=['J1', 'J3']))
        self.controls['policy'] = dict(scope=self.inspection['observation']['scope'])
        with self.assertRaises(ValueError):
            self.receive(self.review(), self.args | dict(selected_refs=['J1', 'J3']))

    def test_freshness_at_receipt_and_review_after_controls_edit_or_source_edit(self):
        review = self.review()
        with self.assertRaises(design.PendingContextChanged):
            self.receive(review, revision=2)
        review = self.review()
        offer = self.receive(review)
        self.board.with_suffix('.kicad_pro').write_bytes(
            self.board.with_suffix('.kicad_pro').read_bytes() + b'\n')
        with self.assertRaisesRegex(design.PendingContextChanged, 'Saved project changed'):
            self.adopt(review, offer)

    def test_another_visible_project_invalidates_receipt_and_adoption(self):
        other = multipad_fixture.write_project(self.board.parent.with_name('other'))
        review = self.review()
        with self.assertRaises(design.PendingContextChanged):
            self.receive(review, source=other)
        review = self.review()
        offer = self.receive(review)
        with self.assertRaises(design.PendingContextChanged):
            self.adopt(review, offer, source=other)

    def test_ambiguous_or_unsupported_clarification_cannot_be_adopted(self):
        for reason in design.CLARIFICATION_REASONS:
            review = self.review()
            text = dict(reason=reason, questions=['Which connector should stay fixed?'])
            answer = review.receive('clarify_design_request', text, self.controls,
                                   request=self.request, revision=1, source=self.board)
            self.assertIs(answer['execution_authorized'], False)
            with self.assertRaises(design.PendingContextChanged):
                self.receive(review)

    def test_cancel_and_review_tampering_do_not_adopt(self):
        review = self.review()
        offer = self.receive(review)
        offer['approval_granted'] = True
        with self.assertRaises(design.IntentError):
            self.adopt(review, offer)
        review.cancel()
        with self.assertRaises(design.PendingContextChanged):
            self.receive(review)
        self.assertEqual(design.placement_tool_schema()['function']['name'], 'propose_placement_route')
        v2 = design.placement_constraints_contract_v2()['tools'][0]['function']
        self.assertEqual(v2['name'], self.tool)
        self.assertEqual(set(v2['parameters']['required']), set(self.args))

    def test_budget_only_is_reviewable_before_parts_or_area_are_set(self):
        review = self.review()
        offer = self.receive(review, dict(selected_refs=None, region_nm=None, route_seconds=60))
        self.assertIsNone(offer['placement_settings'])
        self.assertEqual(self.adopt(review, offer),
            dict(placement_settings=None, selected=[], region_nm=None, route_seconds=60))

    def window(self):
        w = ui.PlacementGuiTests().window()
        w.gate.review = None
        w.inspection = self.inspection
        w.board = controls.text_control(str(self.board))
        w.route_budget = controls.text_control('90')
        w.assistant_request = controls.text_control('Select J1, J2\nArea 8, 8 to 30, 12 mm\nRouting time 60 s')
        w.region = [controls.text_control(pg.mm(n)) for n in self.controls['region_limit_nm']]
        w.parts = controls.parts_control(self.inspection['components'], [])
        w.copper_policy.GetSelection.return_value = 1
        w.protected_names = controls.text_control('KEEP')
        w.protected_route_ids = controls.text_control('')
        w.constraint_summary = controls.text_control('')
        w.constraint_edit, w.constraint_map = Mock(), Mock()
        w.constraint_key = Mock()
        w.constraint_fields = [controls.text_control('') for _ in range(3)]
        w.constraint_review = w.constraint_offer = None
        w.constraint_edited = w.updating = False
        w.find_alternatives = Mock()
        w.start = Mock()
        for method in ('constraint_inputs', 'constraint_binding', 'constraint_draft_terms',
                'preview_constraints', 'show_constraint_offer', 'constraint_draft_changed',
                'clear_constraint_offer', 'discard_constraints', 'use_constraints',
                'update_constraint_map', 'constraint_preview_error'):
            setattr(w, method, MethodType(ui.window_method(method), w))
        return w

    @staticmethod
    def preview_in_window(w):
        w.preview_constraints(None)
        prepare, show = w.start.call_args.args[1:]
        show(prepare(Mock(), None))

    def test_window_reviews_in_context_edits_and_uses_only_ordinary_settings(self):
        w = self.window()
        before = w.constraint_inputs()
        self.preview_in_window(w)
        self.assertEqual(w.constraint_inputs(), before)
        self.assertIn('Routing time  90 s → 60 s', w.constraint_summary.GetValue())
        self.assertIn('Protected nets  KEEP', w.constraint_summary.GetValue())
        scene = w.constraint_map.SetScene.call_args.args[0]
        self.assertIn('data-protected="true"', scene['svg'])
        self.assertIn('data-role="allowed-region"', scene['svg'])
        w.constraint_fields[2].ChangeValue('75')
        w.constraint_draft_changed(Mock())
        w.use_constraints(None)
        self.assertEqual(w.route_budget.GetValue(), '90')
        self.preview_in_window(w)
        self.assertIn('90 s → 75 s', w.constraint_summary.GetValue())
        w.use_constraints(None)
        result = w.constraint_inputs()
        self.assertEqual(set(result['selected']), {self.ids['J1'], self.ids['J2']})
        self.assertEqual(result['region_nm'], self.args['region_nm'])
        self.assertEqual(result['route_seconds'], 75)
        self.assertEqual(result['policy'], before['policy'])
        self.assertIsNone(w.constraint_offer)
        self.assertFalse(w.gate.acknowledged)
        w.find_alternatives.assert_not_called()

    def test_window_discard_and_late_state_changes_do_not_adopt(self):
        w = self.window()
        before = w.constraint_inputs()
        self.preview_in_window(w)
        w.discard_constraints(None)
        self.assertIsNone(w.constraint_offer)
        self.assertEqual(w.constraint_inputs(), before)
        self.preview_in_window(w)
        w.assistant_request.ChangeValue('Routing time 80 s')
        w.use_constraints(None)
        self.assertEqual(w.constraint_inputs(), before)
        self.assertIn('unavailable', w.constraint_summary.GetValue())
        self.preview_in_window(w)
        self.board.with_suffix('.kicad_pro').write_bytes(
            self.board.with_suffix('.kicad_pro').read_bytes() + b'\n')
        w.use_constraints(None)
        self.assertEqual(w.constraint_inputs(), before)
        self.assertIn('Saved project changed', w.constraint_summary.GetValue())

    def test_local_request_refuses_unknown_or_repeated_instructions(self):
        self.assertEqual(pg.local_constraint_request(pg.LOCAL_REQUEST_EXAMPLE),
            dict(selected_refs=['J1', 'J2'], region_nm=[14_000_000,8_000_000,22_000_000,13_000_000],
                 route_seconds=75))
        for text in ('Select J1, J2 and unlock copper', 'Select J1, J1',
                     'Routing time 60 s\nRouting time 80 s', 'Area 1, 2 to 3, 4 cm'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                pg.local_constraint_request(text)

    def test_board_preview_distinguishes_the_full_checked_copper_partition(self):
        raw = copper_fixtures.raw(copper_fixtures.source_tree())
        fixture = copper_fixtures.fixture
        observation = placement.contract.inspect_board(raw, scope=placement.contract.ORDINARY_SCOPE)
        inspection = dict(observation=observation,
                          components=[dict(uuid=row['uuid'], reference=row['reference'])
                                      for row in observation['footprints']])
        plan = placement.copper.propose(raw, fixture.selected(), protected_names=['KEEP'],
                                        scope=observation['scope'])
        state = dict(policy=dict(copper_policy=placement.COPPER_POLICY, protected_names=['KEEP']))
        offer = dict(copper_plan=plan, after=dict(selected_refs=['J1', 'J2'],
                                                  region_nm=copper_fixtures.REGION))
        diagram = ET.fromstring(pg.constraint_scene(inspection, state, offer)['svg'])
        found = {element.attrib['data-route']: element.attrib['data-protected']
                 for element in diagram if 'data-route' in element.attrib}
        self.assertEqual(found, {**{row['uuid']: 'true' for row in plan['protected_routes']},
                                 **{row['uuid']: 'false' for row in plan['removed_routes']}})
        self.assertTrue(any(not row['locked'] for row in plan['protected_routes']))

    def test_unavailable_picture_preserves_readable_review_and_copper_counts(self):
        w = self.window()
        w.constraint_map.SetScene.side_effect = [ValueError('Display fixture failed.'), None]
        self.preview_in_window(w)
        self.assertIn('routes stay protected', w.constraint_summary.GetValue())
        self.assertIn('Board preview unavailable.', w.constraint_summary.GetValue())


if __name__ == '__main__':
    unittest.main()
