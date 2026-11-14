"""Owned pure region-initialization controls, never Native qualification."""
import copy
import unittest
from unittest.mock import patch

from autorouter import placement_copper as copper, pipeline
from experiments.constrained_placement_v1 import constraints, prototype
from experiments.placement_native_proposal_v1 import contract as c, worker
from experiments.placement_native_proposal_v1 import ordinary_fixture as fixture
from tests.test_placement_tht_scope import board, fp, raw


class PlacementRegionContract(unittest.TestCase):
    def setUp(self):
        self.tree = board()
        self.source = raw(self.tree)
        self.selected = fixture.selected()
        self.region = [14_000_000, 7_000_000, 31_000_000, 13_000_000]
        self.options = dict(scope=c.THT_BASELINE_SCOPE, selected=self.selected, region_nm=self.region)
        self.opted = dict(self.options, region_initialization=prototype.REGION_INITIALIZATION_POLICY)
        self.observed = c.inspect_board(self.source, scope=c.THT_BASELINE_SCOPE)
        anchors = {row['uuid']: row['position_nm'] for row in self.observed['footprints']}
        self.original = {key: list(anchors[key]) for key in self.selected}
        self.target = copy.deepcopy(self.original)
        self.target[self.selected[0]] = [16_000_000, 10_000_000]

    def test_default_and_explicit_none_keep_legacy_options_facts_and_bytes(self):
        options = dict(self.options, region_nm=[7_000_000, 7_000_000, 31_000_000, 13_000_000])
        self.assertEqual(c.scope_options(**options), options)
        self.assertEqual(c.scope_options(**options, region_initialization=None), options)
        with patch.object(prototype, 'source_context', side_effect=AssertionError('not the default path')):
            facts = c.facts_from_observation(self.observed, **options)
            self.assertEqual(c.facts_from_observation(self.observed, **options, region_initialization=None), facts)
            candidate = raw(c.translated_tree(self.source, self.target, **options))
            self.assertEqual(raw(c.translated_tree(self.source, self.target, **options, region_initialization=None)), candidate)
            self.assertEqual(c.check_translation(self.source, candidate, self.target, **options),
                             c.check_translation(self.source, candidate, self.target, **options, region_initialization=None))
        self.assertNotIn('region_initialization', facts)

    def test_opt_in_admits_source_outside_destination_without_changing_final_facts(self):
        before = copy.deepcopy(self.observed)
        with self.assertRaisesRegex(ValueError, 'allowed region'):
            c.facts_from_observation(self.observed, **self.options)
        facts = c.facts_from_observation(self.observed, **self.opted)
        for component in facts['components']:
            if component['id'] in self.selected:
                self.assertEqual(component['allowed_region_mm'], [14, 7, 31, 13])
        with self.assertRaisesRegex(ValueError, 'allowed region'):
            constraints.validate_alternative(facts, constraints.original_alternative(facts))
        c.validate_moves(self.observed, self.target, **self.opted)
        candidate = raw(c.translated_tree(self.source, self.target, **self.opted))
        self.assertTrue(c.check_translation(self.source, candidate, self.target, **self.opted)['exact_immutable_AST'])
        self.assertEqual(self.observed, before)
        self.assertEqual(self.source, raw(self.tree))

    def test_unchanged_and_partial_destination_targets_are_still_refused(self):
        with self.assertRaisesRegex(ValueError, 'allowed region'):
            c.validate_moves(self.observed, self.original, **self.opted)
        bad = copy.deepcopy(self.target)
        bad[self.selected[0]][0] = self.region[0]
        with self.assertRaisesRegex(ValueError, 'allowed region'):
            c.validate_moves(self.observed, bad, **self.opted)
        bad[self.selected[0]][0] = 40_000_000
        with self.assertRaisesRegex(ValueError, 'outside rectangular board'):
            c.validate_moves(self.observed, bad, **self.opted)

    def test_only_exact_policy_baseline_scope_and_two_selected_are_admitted(self):
        for value in (True, 1, {}, [], '', 'ignore-source-regions'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                c.scope_options(**self.options, region_initialization=value)
        for scope in (c.DEFAULT_SCOPE, c.MULTIPAD_SCOPE, c.ORDINARY_SCOPE, c.CONTEXT_SCOPE, c.THT_SCOPE):
            with self.subTest(scope=scope), self.assertRaisesRegex(ValueError, 'source-baseline'):
                c.scope_options(**dict(self.opted, scope=scope))
        three = self.selected + [c.uid(fp(self.tree, 'J3'))]
        with self.assertRaisesRegex(ValueError, 'at most two'):
            c.scope_options(**dict(self.opted, selected=three))

    def test_original_board_and_pair_conflicts_are_not_destination_waivers(self):
        for at, message in ((['4', '10', '90'], 'outside rectangular board'),
                            (['26', '10', '90'], 'rectangles overlap')):
            tree = copy.deepcopy(self.tree)
            c.sx.one(fp(tree, 'J1'), 'at')[1:] = at
            observed = c.inspect_board(raw(tree), scope=c.THT_BASELINE_SCOPE)
            with self.subTest(at=at), self.assertRaisesRegex(ValueError, message):
                c.facts_from_observation(observed, **self.opted)

    def test_locked_or_nonselected_components_never_gain_movement_authority(self):
        tree = copy.deepcopy(self.tree)
        fp(tree, 'J1').append(['locked', 'yes'])
        observed = c.inspect_board(raw(tree), scope=c.THT_BASELINE_SCOPE)
        with self.assertRaisesRegex(ValueError, 'fixed in ordinary|movable'):
            c.facts_from_observation(observed, **self.opted)
        moved_fixed = dict(self.target)
        moved_fixed[c.uid(fp(self.tree, 'J3'))] = [16_000_000, 16_000_000]
        with self.assertRaisesRegex(ValueError, 'Exact prospectively selected'):
            c.validate_moves(self.observed, moved_fixed, **self.opted)

    def test_changed_pose_cannot_intersect_retained_copper(self):
        options = dict(self.opted, region_nm=[14_000_000, 14_000_000, 31_000_000, 19_000_000])
        target = {self.selected[0]: [16_000_000, 16_000_000], self.selected[1]: [29_000_000, 16_000_000]}
        c.facts_from_observation(self.observed, **options)
        with self.assertRaisesRegex(ValueError, 'keepout'):
            c.validate_moves(self.observed, target, **options)

    def test_copper_audits_bind_option_and_keep_protection_and_final_regions(self):
        plan = copper.propose(self.source, self.selected, scope=c.THT_BASELINE_SCOPE,
                              protected_route_ids=[row['uuid'] for row in self.observed['routes']])
        prepared = copper.prepare(self.source, plan)
        candidate = raw(c.translated_tree(prepared, self.target, **self.opted))
        for audit in (copper.audit_translation, copper.audit_routed):
            with self.subTest(audit=audit.__name__):
                result = audit(self.source, candidate, plan, self.target, scope=c.THT_BASELINE_SCOPE,
                               region_nm=self.region, region_initialization=prototype.REGION_INITIALIZATION_POLICY)
                self.assertTrue(result['audit_passed'])
                self.assertEqual(result['placement_options']['region_initialization'], prototype.REGION_INITIALIZATION_POLICY)
                self.assertFalse(result['execution_authorized'])
                with self.assertRaisesRegex(ValueError, 'allowed region'):
                    audit(self.source, self.source, plan, self.original, scope=c.THT_BASELINE_SCOPE,
                          region_nm=self.region, region_initialization=prototype.REGION_INITIALIZATION_POLICY)
        protected_fault = c.read_board(candidate)
        c.sx.one(c.sx.children(protected_fault, 'segment')[0], 'width')[1] = '0.2'
        with self.assertRaisesRegex(pipeline.Rejected, 'protected route'):
            copper.audit_routed(self.source, raw(protected_fault), plan, self.target,
                scope=c.THT_BASELINE_SCOPE, region_nm=self.region,
                region_initialization=prototype.REGION_INITIALIZATION_POLICY)

    def test_candidate_immutable_fields_cannot_be_changed_under_initialization(self):
        candidate = c.translated_tree(self.source, self.target, **self.opted)
        c.sx.one(fp(candidate, 'J3'), 'at')[1] = '12.000001'
        with self.assertRaisesRegex(ValueError, 'beyond selected translations'):
            c.check_translation(self.source, raw(candidate), self.target, **self.opted)

    def test_worker_flag_is_explicit_complete_and_never_inferred(self):
        self.assertEqual(worker.request_scope({}, c), c.scope_options())
        geometry = dict(placement_scope=c.THT_BASELINE_SCOPE, selected_footprints=self.selected,
                        allowed_region_nm=self.region)
        self.assertEqual(worker.request_scope(geometry, c), self.options)
        flagged = dict(geometry, region_initialization=prototype.REGION_INITIALIZATION_POLICY)
        self.assertEqual(worker.request_scope(flagged, c), self.opted)
        for value in (None, True, 1, '', 'other'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                worker.request_scope(dict(geometry, region_initialization=value), c)
        for missing in geometry:
            bad = dict(flagged); del bad[missing]
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, 'Complete explicit|complete explicit'):
                worker.request_scope(bad, c)
        with self.assertRaises(ValueError):
            worker.request_scope(dict(flagged, placement_scope=c.THT_SCOPE), c)


if __name__ == '__main__':
    unittest.main()
