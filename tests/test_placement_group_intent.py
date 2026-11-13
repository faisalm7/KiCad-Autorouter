"""Source-bound rigid-group intent/proof controls; no Native qualification claim."""
import copy
from decimal import Decimal, localcontext
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from autorouter import placement, placement_copper as copper, placement_intent as intent
from autorouter import placement_gui as pg, sexpr as sx
from experiments.constrained_placement_v1 import constraints
from experiments.placement_native_proposal_v1 import contract
from tests import test_placement_copper_intent as copper_intent
from tests import test_placement_gui as gui_tests


class RigidGroupIntent(unittest.TestCase):
    def setUp(self):
        copper_intent.CopperPlacementIntent.setUp(self)
        self.ordinary = copy.deepcopy(self.settings)
        self.settings = intent.settings(self.selected, self.settings['region_nm'], scope=self.scope,
            copper_policy=intent.COPPER_POLICY, group_policy=intent.GROUP_POLICY)
        self.observation = intent.effective_observation(self.inspection, self.settings)
        self.anchors = {row['uuid']: row['position_nm'] for row in self.observation['footprints']}
        self.moves = {key: [self.anchors[key][0] + 1_000_000, self.anchors[key][1] + 100_000]
                      for key in self.selected}

    def review(self):
        facts = intent.facts(self.inspection, self.settings)
        pose = contract.validate_moves(self.observation, self.moves,
            scope=self.scope, selected=self.selected, region_nm=self.settings['region_nm'])
        pose['source_sha256'] = constraints.digest(facts)
        return intent.Review(dict(kind='autorouter.placement-proposals.v1',
            inspection=self.inspection, settings=self.settings,
            copper_plan=intent.copper_plan(self.inspection, self.settings),
            search=dict(status='proposals_ready', alternatives=[dict(candidate=pose)])))

    def test_v4_preserves_old_contract_and_requires_explicit_bound_policy(self):
        self.assertEqual(self.ordinary['schema'], 3)
        self.assertNotIn('group_policy', self.ordinary)
        self.assertEqual(self.settings['schema'], 4)
        self.assertEqual(intent.validate_settings(self.settings), self.settings)
        self.assertTrue(intent.rebuilds_copper(self.settings))
        for key, value in (('schema', 3), ('group_policy', None), ('group_policy', True),
                           ('group_policy', 'free'), ('preserve_existing', True),
                           ('copper_policy', None), ('search', dict(self.settings['search'], steps=999))):
            changed = dict(self.settings, **{key: value})
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                intent.validate_settings(changed)
        with self.assertRaisesRegex(ValueError, 'explicit affected-net'):
            intent.settings(self.selected, self.settings['region_nm'], scope=self.scope,
                            group_policy=intent.GROUP_POLICY)

    def test_group_facts_are_detached_all_selected_and_source_bound(self):
        facts = intent.facts(self.inspection, self.settings)
        self.assertEqual(facts['groups'], [dict(policy=intent.GROUP_POLICY, members=self.selected)])
        facts['groups'][0]['members'].reverse()
        self.assertEqual(intent.facts(self.inspection, self.settings)['groups'][0]['members'], self.selected)
        self.assertEqual(self.original, intent.gui.source_inventory(self.board))

    def test_one_member_edit_translates_every_member_and_preserves_relative_positions(self):
        review = self.review(); before = copy.deepcopy(review.moves)
        review.edit(self.selected[0], '14', '10.2')
        audit = intent.group_moves(self.observation, self.settings, review.moves)
        self.assertEqual(audit['delta_nm'], [2_000_000, 200_000])
        self.assertNotEqual(review.moves, before)
        for axis in (0, 1):
            self.assertEqual(review.moves[self.selected[1]][axis] - review.moves[self.selected[0]][axis],
                             self.anchors[self.selected[1]][axis] - self.anchors[self.selected[0]][axis])
        self.assertIsNone(review.intent)

    def test_inconsistent_atomic_edits_refuse_and_revoke_prior_intent(self):
        review = self.review(); before = copy.deepcopy(review.moves)
        review.decision(acknowledged=True, accepted=True)
        with self.assertRaisesRegex(ValueError, 'same displacement'):
            review.edit_many({self.selected[0]: ['14', '10.2'], self.selected[1]: ['27', '10.2']})
        self.assertEqual(review.moves, before); self.assertIsNone(review.intent)
        with self.assertRaises(ValueError): review.edit(self.selected[0], '100', '100')
        self.assertEqual(review.moves, before)

    def test_draft_one_nm_shear_refuses_even_with_recomputed_untrusted_hashes(self):
        review = self.review(); draft = review.decision(acknowledged=True, accepted=True)
        self.assertEqual(intent.validate_draft(self.inspection, draft), draft)
        changed = copy.deepcopy(draft); changed['moves_nm'][self.selected[1]][0] += 1
        pose = contract.validate_moves(self.observation, changed['moves_nm'], scope=self.scope,
            selected=self.selected, region_nm=self.settings['region_nm'])
        pose['source_sha256'] = changed['facts_sha256']
        changed['pose_sha256'] = constraints.digest(pose)
        with self.assertRaisesRegex(ValueError, 'Rigid group|relative positions'):
            intent.validate_draft(self.inspection, changed)

    def test_actual_candidate_and_integer_move_checks_refuse_one_nm_shear(self):
        prepared = copper.prepare(self.source, intent.copper_plan(self.inspection, self.settings))
        tree = contract.translated_tree(prepared, self.moves, scope=self.scope,
            selected=self.selected, region_nm=self.settings['region_nm'])
        raw = (sx.dump(tree)+'\n').encode()
        result = intent.group_candidate(self.source, raw, self.settings, self.moves)
        self.assertTrue(result['actual_candidate_anchors_verified'])
        key = self.selected[1]
        part = next(row for row in sx.children(tree, 'footprint') if contract.uid(row) == key)
        sx.one(part, 'at')[1] = str((self.moves[key][0]+1)/1_000_000)
        with self.assertRaisesRegex(ValueError, 'Actual candidate anchors'):
            intent.group_candidate(self.source, (sx.dump(tree)+'\n').encode(), self.settings, self.moves)
        bad = copy.deepcopy(self.moves); bad[key][0] += 1
        with self.assertRaisesRegex(ValueError, 'shear'): intent.group_moves(self.observation, self.settings, bad)
        for value in (True, 1.0, '1'):
            bad = copy.deepcopy(self.moves); bad[key][0] = value
            with self.assertRaises(ValueError): intent.group_moves(self.observation, self.settings, bad)

    def test_group_quantization_uses_one_shared_delta_with_asymmetric_half_nm_proxies(self):
        facts = intent.facts(self.inspection, self.settings)
        # Pure proxy arithmetic control: half-nm centres on distinct members.
        for i, row in enumerate(facts['components']):
            if row['id'] in self.selected:
                row['position_mm'][0] += (0.0000005 if row['id'] == self.selected[0] else -0.0000005)
        pose = constraints.original_alternative(facts)
        for row in pose['transforms']:
            if row['component_id'] in self.selected: row['x_mm'] += 0.100000001
        # Without an observation, source anchors must be integer, so reject the
        # synthetic half-nm source rather than inventing actual footprint poses.
        with self.assertRaisesRegex(ValueError, 'integer anchors'):
            contract.quantized_translation(facts, pose)

    def test_actual_odd_integer_anchor_cannot_shear_when_snapped(self):
        tree = sx.parse(self.source.decode())
        for part in sx.children(tree, 'footprint'):
            key = contract.uid(part)
            if key not in self.selected: continue
            if key == self.selected[1]: sx.one(part, 'at')[1] = '26.000001'
        self.board.write_text(sx.dump(tree)+'\n')
        inspection = intent.inspect_saved(self.board)
        observation = intent.effective_observation(inspection, self.settings)
        facts = intent.facts(inspection, self.settings)
        pose = constraints.original_alternative(facts)
        naive = {}
        for row in pose['transforms']:
            if row['component_id'] not in self.selected: continue
            row['x_mm'] += 0.0000005  # Half a nanometre: one shared rounding choice.
            offset = contract._proxy_offset(observation, row['component_id'])
            source = next(part for part in observation['footprints'] if part['uuid'] == row['component_id'])
            naive[row['component_id']] = int((Decimal(str(row['x_mm']))*1000000-offset[0]).to_integral_value()) - source['position_nm'][0]
        self.assertEqual(set(naive.values()), {0, 1}, 'Control must demonstrate independent-rounding shear')
        _, moves = contract.quantized_translation(facts, pose, observation=observation)
        audit = intent.group_moves(observation, self.settings, moves)
        self.assertEqual(audit['delta_nm'], [0, 0])

    def test_group_protection_and_prepared_paths_use_semantics_not_schema_three(self):
        protected = intent.settings(self.selected, self.settings['region_nm'], scope=self.scope,
            copper_policy=intent.COPPER_POLICY, group_policy=intent.GROUP_POLICY, protected_names=['ROUTE_A'])
        with self.assertRaises(ValueError): intent.facts(self.inspection, protected)
        _, paths = placement._paths(self.root/'output', dict(intent=dict(settings=self.settings), inspection=dict(source=str(self.board))))
        self.assertIn('prepared', paths)
        lines = '\n'.join(pg.placement_limits(self.inspection, rebuild=True, grouped=True))
        self.assertIn('Rigid selected group', lines)

    def test_original_arrangement_is_explicit_manual_review_not_search_success(self):
        with patch.object(intent.prototype, 'propose', side_effect=AssertionError('No search requested')):
            proposal = intent.original_proposal(self.inspection, self.settings)
        self.assertEqual(proposal['search']['status'], 'original_for_review')
        self.assertIs(proposal['search']['search_performed'], False)
        review = intent.Review(proposal)
        self.assertEqual(intent.group_moves(self.observation, self.settings, review.moves)['delta_nm'], [0, 0])
        review.edit(self.selected[0], '13', '10.1')
        self.assertEqual(intent.group_moves(self.observation, self.settings, review.moves)['delta_nm'], [1000000, 100000])
        changed = copy.deepcopy(proposal)
        changed['search']['alternatives'][0]['candidate'] = review.pose
        with self.assertRaisesRegex(ValueError, 'Original arrangement'):
            intent.Review(changed)

    def test_group_integer_readback_and_manual_edits_ignore_ambient_decimal_precision(self):
        prepared = copper.prepare(self.source, intent.copper_plan(self.inspection, self.settings))
        tree = contract.translated_tree(prepared, self.moves, scope=self.scope,
            selected=self.selected, region_nm=self.settings['region_nm'])
        raw = (sx.dump(tree)+'\n').encode()
        part = next(row for row in sx.children(tree, 'footprint') if contract.uid(row) == self.selected[1])
        sx.one(part, 'at')[1] = str((self.moves[self.selected[1]][0]+1)/1_000_000)
        shear = (sx.dump(tree)+'\n').encode()
        for precision in (6, 28):
            review = self.review()
            with self.subTest(precision=precision), localcontext() as context:
                context.prec = precision
                self.assertTrue(intent.group_candidate(self.source, raw, self.settings, self.moves)['actual_candidate_anchors_verified'])
                with self.assertRaisesRegex(ValueError, 'Actual candidate anchors'):
                    intent.group_candidate(self.source, shear, self.settings, self.moves)
                review.edit(self.selected[0], '12.000001', '10')
                self.assertEqual(intent.group_moves(self.observation, self.settings, review.moves)['delta_nm'], [1, 0])
                draft = review.decision(acknowledged=True, accepted=True)
                self.assertEqual(intent.validate_draft(self.inspection, draft), draft)
                for atom in ('13.0000000000000000000000000000000000000000000000000000000001',
                             '1e1000000', '1e-1000000', 'NaN', '2000.000001', '0.0000001'):
                    with self.assertRaises(ValueError): intent._group_nm(atom)

    def test_group_render_failure_restores_current_unedited_member_and_pending_text(self):
        review = self.review(); window = gui_tests.PlacementGuiTests().window()
        window.gate.attach(review); window.editing_component = self.selected[1]
        window.part.GetSelection.return_value = 1
        window.x.GetValue.return_value = '27'; window.y.GetValue.return_value = '10.1'
        window.pending_coordinates = {self.selected[0]: ['14', '10.2']}
        window.render = unittest.mock.Mock(side_effect=RuntimeError('deliberate group preview failure'))
        previous = copy.deepcopy((review.pose, review.moves, review.revision))
        gui_tests.window_method('edit')(window, None)
        self.assertEqual((review.pose, review.moves, review.revision), previous)
        self.assertEqual(window.pending_coordinates, {self.selected[0]: ['14', '10.2']})
        window.x.ChangeValue.assert_called_with('27'); window.y.ChangeValue.assert_called_with('10.1')
        self.assertIsNone(review.intent); self.assertTrue(window.gate.dirty)
        self.assertIn('previous pose retained', window.message.call_args.args[0])

    def test_final_route_boundary_checks_actual_group_before_route_auditor(self):
        destination = self.root/'candidate'; destination.mkdir()
        for source in self.board.parent.iterdir(): shutil.copy2(source, destination/source.name)
        target = destination/self.board.name
        prepared = copper.prepare(self.source, intent.copper_plan(self.inspection, self.settings))
        tree = contract.translated_tree(prepared, self.moves, scope=self.scope,
            selected=self.selected, region_nm=self.settings['region_nm'])
        bad = next(row for row in sx.children(tree, 'footprint') if contract.uid(row) == self.selected[0])
        sx.one(bad, 'at')[1] = str((self.moves[self.selected[0]][0]+1)/1_000_000)
        target.write_text(sx.dump(tree)+'\n')
        draft = self.review().decision(acknowledged=True, accepted=True)
        witness = dict(binding=dict(intent=draft, inspection=self.inspection))
        settings = placement.routing_settings(witness)
        with patch.object(copper, 'audit_routed', side_effect=AssertionError('sheared group reached routing audit')):
            with self.assertRaisesRegex(ValueError, 'Actual candidate anchors'):
                placement._routing_task(witness, settings, 'route', target)


if __name__ == '__main__': unittest.main()
