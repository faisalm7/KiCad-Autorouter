"""Pure target-region settings/review controls; no fabricated Native qualification."""
import copy
from decimal import localcontext, ROUND_DOWN
import unittest
from pathlib import Path
from unittest.mock import patch

from autorouter import placement, placement_intent as intent
from experiments.constrained_placement_v1 import constraints, prototype
from experiments.placement_native_proposal_v1 import contract
from tests import test_placement_source_baseline as baseline_fixture


class RegionPlacementWorkflow(unittest.TestCase):
    def setUp(self):
        # Reuse the owned metadata/off-anchor fixture and explicitly synthetic
        # unit-test context. Actual source/target Native evidence is a separate gate.
        fixture = baseline_fixture.SourceCopperBaseline()
        fixture.setUp()
        self.inspection = fixture.inspection()
        self.inspection['source_hashes'] = {'pure-fixture.kicad_pcb': 'a' * 64}
        self.observation = fixture.observation
        self.selected = fixture.selected
        self.region = [14_000_000, 8_000_000, 22_000_000, 13_000_000]

    def settings(self, **kwargs):
        return intent.settings(self.selected, self.region,
            scope=contract.THT_BASELINE_SCOPE,
            region_initialization=prototype.REGION_INITIALIZATION_POLICY, **kwargs)

    def proposal(self):
        settings = self.settings()
        moves = dict(zip(self.selected, ([16_000_000, 10_000_000], [20_000_000, 10_000_000])))
        pose = contract.validate_moves(self.observation, moves, **intent.contract_options(settings))
        facts = intent._facts_context(self.inspection, settings, None, self.observation)
        pose['source_sha256'] = constraints.digest(facts)
        return dict(kind='autorouter.placement-proposals.v1', inspection=copy.deepcopy(self.inspection),
            settings=settings, search=dict(status='proposals_ready', alternatives=[dict(candidate=pose)]))

    def test_explicit_policy_persists_with_exact_legacy_and_protection_semantics(self):
        value = self.settings()
        self.assertEqual(value['schema'], 5)
        self.assertEqual(value['kind'], intent.REGION_SETTINGS_KIND)
        self.assertEqual(intent.validate_settings(value), value)
        self.assertTrue(value['preserve_existing'])
        rebuilt = self.settings(copper_policy=intent.COPPER_POLICY,
            protected_names=['KEEP'], protected_route_ids=[])
        self.assertTrue(intent.rebuilds_copper(rebuilt))
        self.assertEqual(intent.validate_settings(rebuilt), rebuilt)
        self.assertEqual(rebuilt['protected_names'], ['KEEP'])
        legacy = intent.settings(self.selected, self.region, scope=contract.THT_BASELINE_SCOPE)
        self.assertNotIn('region_initialization', legacy)
        with self.assertRaisesRegex(ValueError, 'allowed region'):
            intent._facts_context(self.inspection, legacy, None, self.observation)
        facts = intent._facts_context(self.inspection, value, None, self.observation)
        with self.assertRaisesRegex(ValueError, 'allowed region'):
            constraints.validate_alternative(facts, constraints.original_alternative(facts))
        self.assertEqual([row['allowed_region_mm'] for row in facts['components'] if row['id'] in self.selected],
                         [[14., 8., 22., 13.]] * 2)

    def test_unknown_missing_or_laundered_policy_authority_and_group_refuse(self):
        value = self.settings()
        for fault in ('missing', 'unknown', 'bool', 'old-schema', 'group', 'authority', 'baseline'):
            changed = copy.deepcopy(value)
            if fault == 'missing': changed.pop('region_initialization')
            if fault == 'unknown': changed['region_initialization'] = 'ignore-regions'
            if fault == 'bool': changed['region_initialization'] = True
            if fault == 'old-schema': changed['schema'] = 2
            if fault == 'group': changed['group_policy'] = intent.GROUP_POLICY
            if fault == 'authority': changed['approval_granted'] = True
            if fault == 'baseline': changed.pop('selected_copper_baseline_policy')
            with self.subTest(fault=fault), self.assertRaises(ValueError): intent.validate_settings(changed)
        with self.assertRaises(ValueError):
            intent.settings(self.selected[:1], self.region, scope=contract.THT_BASELINE_SCOPE,
                            region_initialization=prototype.REGION_INITIALIZATION_POLICY)

    def test_native_source_baseline_and_annotations_still_required(self):
        for fault in ('not-run', 'blocking', 'receipt', 'source', 'annotation'):
            changed = copy.deepcopy(self.inspection)
            if fault == 'not-run': changed['native_source_baseline']['native_validation_performed'] = False
            if fault == 'blocking': changed['native_source_baseline']['native']['blocking'] = 1
            if fault == 'receipt': changed['native_source_baseline']['receipt_sha256'] = 'd' * 64
            if fault == 'source': changed['native_source_baseline']['source_board_sha256'] = 'e' * 64
            if fault == 'annotation': changed['annotation_context']['footprint_anchors_nm'][self.selected[0]][0] += 1
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                intent._facts_context(changed, self.settings(), None, self.observation)

    def test_shared_review_target_edit_and_draft_remain_bound_and_unapproved(self):
        with patch.object(intent, 'current'):
            review = intent.Review(self.proposal())
            draft = review.decision(acknowledged=True, accepted=True)
            self.assertEqual(intent.validate_draft(self.inspection, draft), draft)
            for name in ('execution_authorized', 'approval_granted', 'routing_accepted',
                         'warning_acknowledged', 'human_PCB_approval'):
                self.assertIs(draft[name], False)
            for fault in ('policy', 'target', 'moves', 'pose', 'authority'):
                changed = copy.deepcopy(draft)
                if fault == 'policy': changed['settings'].pop('region_initialization')
                if fault == 'target': changed['settings']['region_nm'][2] -= 2_000_000
                if fault == 'moves': changed['moves_nm'][self.selected[0]][0] = 12_000_000
                if fault == 'pose': changed['pose_sha256'] = 'f' * 64
                if fault == 'authority': changed['execution_authorized'] = True
                with self.subTest(fault=fault), self.assertRaises(ValueError): intent.validate_draft(self.inspection, changed)
            before = copy.deepcopy(review.pose)
            with self.assertRaises(ValueError): review.edit(self.selected[0], '12', '10')
            self.assertIsNone(review.intent)
            self.assertEqual(review.pose, before)

    def test_exact_manual_edit_and_half_even_quantization_ignore_ambient_context(self):
        for precision in (3, 6, 28):
            with self.subTest(precision=precision), patch.object(intent, 'current'):
                review = intent.Review(self.proposal())
                with localcontext() as context:
                    context.prec = precision
                    context.rounding = ROUND_DOWN
                    review.edit(self.selected[0], '16.123456', '10')
                self.assertEqual(review.moves[self.selected[0]], [16123456, 10000000])
                with localcontext() as context:
                    context.prec = precision
                    context.rounding = ROUND_DOWN
                    review.edit(self.selected[0], '16.1234565', '10')
                self.assertEqual(review.moves[self.selected[0]], [16123456, 10000000])

    def test_no_seed_or_cancelled_proposal_never_becomes_review_or_authority(self):
        settings = self.settings()
        for status in ('no_feasible_region_seed', 'cancelled', 'budget_exhausted'):
            result = dict(status=status, alternatives=[])
            with patch.object(intent, 'current'), patch.object(prototype, 'propose', return_value=result) as call:
                proposal = intent.propose(self.inspection, settings)
                self.assertEqual(call.call_args.kwargs['region_initialization'], prototype.REGION_INITIALIZATION_POLICY)
                self.assertEqual(call.call_args.kwargs['seconds'], 2)
                self.assertFalse(proposal['execution_authorized'])
                with self.assertRaises(ValueError): intent.Review(proposal)

    def test_native_request_and_original_to_final_options_carry_exact_policy(self):
        settings = self.settings()
        binding = dict(intent=dict(settings=settings, moves_nm={}),
            runtime_manifest_sha256='a' * 64, wrapper_sha256='b' * 64, code_sha256={})
        options = placement._options(binding)
        self.assertEqual(options['region_initialization'], prototype.REGION_INITIALIZATION_POLICY)
        # Request construction is pure; the owned directory identity is a small
        # existing test location, never a Native execution or candidate approval.
        work = Path(__file__).resolve().parent
        request = placement._request(binding, work, 'capture', work/'fixture.kicad_pcb',
                                     work/'candidate.kicad_pcb', {})
        self.assertEqual(request['region_initialization'], options['region_initialization'])
        self.assertEqual(request['allowed_region_nm'], self.region)
        legacy = dict(binding, intent=dict(settings=intent.settings(self.selected, self.region,
            scope=contract.THT_BASELINE_SCOPE), moves_nm={}))
        self.assertNotIn('region_initialization', placement._options(legacy))
        self.assertNotIn('region_initialization', placement._request(legacy, work, 'capture',
            work/'fixture.kicad_pcb', work/'candidate.kicad_pcb', {}))


if __name__ == '__main__': unittest.main()
