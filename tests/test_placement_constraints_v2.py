"""Versioned settings only. Real source/protection validation, no inference or CAD."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import design_intent as design, gui, placement_intent as placement
from experiments.placement_native_proposal_v1 import multipad_fixture


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


if __name__ == '__main__':
    unittest.main()
