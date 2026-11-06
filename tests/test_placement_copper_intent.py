"""Explicit affected-copper review on owned saved sources; no Native authority."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from autorouter import gui, pipeline, placement_copper as copper, placement_intent as intent, sexpr as sx
from experiments.constrained_placement_v1 import constraints
from experiments.placement_native_proposal_v1 import contract, multipad_fixture, ordinary_fixture
from tests.test_placement_copper import REGION, fp, raw, route, source_tree


class CopperPlacementIntent(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='placement-copper-intent-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.board = ordinary_fixture.write_project(self.root / 'saved project')
        self.source = raw(source_tree())
        self.board.write_bytes(self.source)
        self.selected = ordinary_fixture.selected()
        self.scope = contract.ORDINARY_SCOPE
        self.settings = intent.settings(self.selected, REGION, scope=self.scope,
                                        copper_policy=intent.COPPER_POLICY)
        self.inspection = intent.inspect_saved(self.board)
        self.original = gui.source_inventory(self.board)

    def refused(self, call, *args, **kwargs):
        with self.assertRaises((ValueError, pipeline.Rejected)):
            call(*args, **kwargs)

    def proposal(self, settings=None):
        # Review-only tests use an actual, independently checked geometry pose.
        # Dedicated proposer/cancellation tests below execute the bounded search.
        value = self.settings if settings is None else settings
        plan = intent.copper_plan(self.inspection, value)
        observation = contract.inspect_board(copper.prepare(self.source, plan), scope=self.scope)
        moves = dict(zip(self.selected, ([14_000_000, 10_000_000], [24_000_000, 10_000_000])))
        candidate = contract.validate_moves(observation, moves, scope=self.scope,
                                            selected=self.selected, region_nm=REGION)
        return dict(kind='autorouter.placement-proposals.v1', inspection=copy.deepcopy(self.inspection),
                    settings=copy.deepcopy(value), copper_plan=plan,
                    search=dict(status='proposals_ready', alternatives=[dict(candidate=candidate)]))

    def test_preserve_defaults_are_exact_and_still_refuse_incident_routing(self):
        expected = dict(schema=1, kind=intent.SETTINGS_KIND, selected=self.selected, region_nm=REGION,
                        preserve_existing=True, orientation='preserve', side='preserve',
                        search=dict(seed=7, steps=160, alternatives=2, seconds=2))
        self.assertEqual(intent.settings(self.selected, REGION), expected)
        expected.update(schema=2, kind=intent.ORDINARY_SETTINGS_KIND, scope=self.scope)
        value = intent.settings(self.selected, REGION, scope=self.scope)
        self.assertEqual(value, expected)
        self.assertIsNone(intent.copper_plan(self.inspection, value))
        self.assertEqual(intent.effective_observation(self.inspection, value), self.inspection['observation'])
        self.refused(intent.facts, self.inspection, value)
        self.refused(intent.settings, self.selected, REGION, protected_names=[])
        self.refused(intent.settings, self.selected, REGION, protected_route_ids=[])
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_v3_settings_are_explicit_detached_and_strict_json(self):
        names = ['KEEP']; ids = [contract.uid(pipeline.routes(source_tree())[0])]
        value = intent.settings(self.selected, REGION, scope=self.scope,
            copper_policy=intent.COPPER_POLICY, protected_names=names, protected_route_ids=ids)
        self.assertEqual(value['schema'], 3); self.assertEqual(value['kind'], intent.COPPER_SETTINGS_KIND)
        self.assertIs(value['preserve_existing'], False)
        names.clear(); ids.clear()
        self.assertEqual(value['protected_names'], ['KEEP']); self.assertEqual(len(value['protected_route_ids']), 1)
        path = self.root / 'placement settings.json'; path.write_text(json.dumps(value))
        self.assertEqual(intent.load_settings(path), value)
        cases = [('schema', True), ('schema', 3.0), ('preserve_existing', True),
                 ('copper_policy', None), ('copper_policy', 'anything'), ('scope', contract.DEFAULT_SCOPE),
                 ('protected_names', ()), ('protected_names', [True]), ('protected_names', ['KEEP', 'KEEP']),
                 ('protected_route_ids', ()), ('protected_route_ids', [True]),
                 ('protected_route_ids', ['00000000-0000-0000-0000-000000000000']),
                 ('execution_authorized', True), ('search', dict(value['search'], seconds=2.0))]
        for key, replacement in cases:
            changed = copy.deepcopy(value); changed[key] = replacement
            with self.subTest(field=key, replacement=replacement): self.refused(intent.validate_settings, changed)
        for key in value:
            changed = copy.deepcopy(value); del changed[key]
            with self.subTest(missing=key): self.refused(intent.validate_settings, changed)
        for document in (b'{"schema":3,"schema":3}', b'{"x":NaN}', b' ' * (65536 + 1)):
            path.write_bytes(document)
            with self.subTest(document=document[:40]): self.refused(intent.load_settings, path)

    def test_fresh_plan_and_prepared_observation_preserve_original_and_unrelated_copper(self):
        snapshot = copy.deepcopy(self.inspection)
        with patch('subprocess.Popen', side_effect=AssertionError('intent must stay pure')):
            plan = intent.copper_plan(self.inspection, self.settings)
            observation = intent.effective_observation(self.inspection, self.settings)
            facts = intent.facts(self.inspection, self.settings)
        self.assertEqual(plan, copper.propose(self.source, self.selected))
        self.assertEqual(plan['incident_names'], ['ROUTE_A', 'ROUTE_B'])
        self.assertEqual(len(plan['removed_routes']), 3)
        self.assertEqual({row['net_name'] for row in plan['protected_routes']}, {'KEEP', 'GND'})
        self.assertEqual(observation, contract.inspect_board(copper.prepare(self.source, plan), scope=self.scope))
        self.assertEqual(observation['route_count'], 2)
        self.assertFalse(set(self.selected) & constraints.immovable(facts))
        self.assertTrue(any(row['locked'] for row in observation['routes']))
        self.assertEqual(self.inspection, snapshot)
        self.assertEqual(self.inspection['observation']['route_count'], 5)
        self.assertTrue(all(row['fixed_reasons'] for row in self.inspection['components'] if row['uuid'] in self.selected))
        self.assertEqual(gui.source_inventory(self.board), self.original)
        self.assertEqual(hashlib.sha256(self.source).hexdigest(), plan['source_sha256'])

    def test_multipad_explicit_policy_uses_prepared_geometry_without_changing_v1(self):
        board = multipad_fixture.write_project(self.root / 'multipad project')
        tree = multipad_fixture.board(); tree.append(route('multipad-intent', 'ROUTE_A'))
        board.write_bytes(raw(tree)); inspection = intent.inspect_saved(board)
        selected = [multipad_fixture.uid(ref + '-footprint') for ref in ('J1', 'J2')]
        old = intent.settings(selected, REGION)
        self.refused(intent.facts, inspection, old)
        value = intent.settings(selected, REGION, copper_policy=intent.COPPER_POLICY)
        self.assertEqual(value['scope'], contract.MULTIPAD_SCOPE)
        self.assertFalse(set(selected) & constraints.immovable(intent.facts(inspection, value)))
        self.assertEqual(len(intent.copper_plan(inspection, value)['removed_routes']), 1)

    def test_incident_protection_and_unknown_protection_refuse_not_silently_ignore(self):
        for kwargs in (dict(protected_names=['ROUTE_A']), dict(protected_names=['UNKNOWN']),
                       dict(protected_route_ids=[contract.uid(pipeline.routes(source_tree())[1])]),
                       dict(protected_route_ids=[self.selected[0]])):
            value = intent.settings(self.selected, REGION, scope=self.scope,
                                    copper_policy=intent.COPPER_POLICY, **kwargs)
            with self.subTest(kwargs=kwargs): self.refused(intent.copper_plan, self.inspection, value)
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_locked_ineligible_and_preserved_region_stay_blocked(self):
        tree = source_tree(); fp(tree).append(['locked', 'yes'])
        self.board.write_bytes(raw(tree)); locked = intent.inspect_saved(self.board)
        self.refused(intent.facts, locked, self.settings)
        tree = source_tree(); pipeline.routes(tree)[1].append(['locked', 'yes'])
        self.board.write_bytes(raw(tree)); locked_route = intent.inspect_saved(self.board)
        self.refused(intent.copper_plan, locked_route, self.settings)
        self.board.write_bytes(self.source)
        fixed = next(row['uuid'] for row in self.inspection['components'] if row['reference'] == 'J5')
        value = intent.settings([self.selected[0], fixed], REGION, scope=self.scope,
                                copper_policy=intent.COPPER_POLICY)
        self.refused(intent.facts, self.inspection, value)
        value = intent.settings(self.selected, [7_000_000, 7_000_000, 31_000_000, 29_000_000],
                                scope=self.scope, copper_policy=intent.COPPER_POLICY)
        self.refused(intent.facts, self.inspection, value)

    def test_actual_search_and_cancellation_use_effective_task_without_authority(self):
        with patch('subprocess.Popen', side_effect=AssertionError('search must stay pure')):
            result = intent.propose(self.inspection, self.settings)
        self.assertEqual(result['search']['status'], 'proposals_ready')
        self.assertEqual(result['copper_plan'], intent.copper_plan(self.inspection, self.settings))
        self.assertEqual(result['limitations'], list(intent.COPPER_LIMITS))
        facts = intent.facts(self.inspection, self.settings)
        for row in result['search']['alternatives']:
            constraints.validate_alternative(facts, row['candidate'])
            self.assertEqual(set(row['moves_nm']), set(self.selected))
        for key in ('native_validation_performed', 'execution_authorized', 'approval_granted'):
            self.assertIs(result[key], False)
        cancel = threading.Event(); cancel.set()
        cancelled = intent.propose(self.inspection, self.settings, cancel_event=cancel)
        self.assertEqual(cancelled['search']['status'], 'cancelled')
        self.assertEqual(cancelled['search']['alternatives'], [])
        self.refused(intent.Review, cancelled)
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_review_and_exact_draft_bind_plan_but_never_approve_copper_removal(self):
        proposal = self.proposal(); review = intent.Review(proposal)
        self.assertEqual(review.copper_plan, proposal['copper_plan'])
        self.assertEqual(review.observation['route_count'], 2)
        proposal['copper_plan']['removed_routes'].clear()
        self.assertEqual(len(review.copper_plan['removed_routes']), 3)
        review.edit_many({self.selected[0]: ['16.2', '10.4'], self.selected[1]: ['20.8', '10.4']})
        draft = review.decision(acknowledged=True, accepted=True)
        self.assertEqual(intent.validate_draft(self.inspection, draft), draft)
        self.assertEqual(draft['copper_plan'], review.copper_plan)
        self.assertEqual(draft['moves_nm'][self.selected[0]], [16_200_000, 10_400_000])
        for field in ('native_validation_performed', 'execution_authorized', 'approval_granted',
                      'routing_accepted', 'warning_acknowledged', 'human_PCB_approval'):
            self.assertIs(draft[field], False)
        rejected = review.decision(acknowledged=True, accepted=False)
        self.assertEqual(rejected['choice'], 'reject')
        self.refused(intent.validate_draft, self.inspection, rejected)
        self.refused(review.edit_many, {self.selected[0]: ['nan', '10']})
        self.assertIsNone(review.intent)
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_missing_or_forged_proposal_plan_is_not_reviewable(self):
        proposal = self.proposal()
        for mode in ('missing', 'removed', 'authority', 'source', 'tuple'):
            changed = copy.deepcopy(proposal)
            if mode == 'missing': changed.pop('copper_plan')
            elif mode == 'removed': changed['copper_plan']['removed_routes'].clear()
            elif mode == 'authority': changed['copper_plan']['approval_granted'] = True
            elif mode == 'tuple': changed['copper_plan']['selected'] = tuple(changed['copper_plan']['selected'])
            else: changed['copper_plan']['source_sha256'] = '0' * 64
            with self.subTest(mode=mode): self.refused(intent.Review, changed)

    def test_forged_draft_plan_policy_pose_and_authority_refuse(self):
        review = intent.Review(self.proposal()); draft = review.decision(acknowledged=True, accepted=True)
        for mode in ('missing_plan', 'plan_routes', 'plan_authority', 'plan_tuple', 'protection', 'policy', 'pose', 'authority'):
            changed = copy.deepcopy(draft)
            if mode == 'missing_plan': changed.pop('copper_plan')
            elif mode == 'plan_routes': changed['copper_plan']['protected_routes'].clear()
            elif mode == 'plan_authority': changed['copper_plan']['execution_authorized'] = True
            elif mode == 'plan_tuple': changed['copper_plan']['selected'] = tuple(changed['copper_plan']['selected'])
            elif mode == 'protection': changed['settings']['protected_names'] = ['KEEP']
            elif mode == 'policy': changed['settings']['copper_policy'] = 'preserve'
            elif mode == 'pose': changed['moves_nm'][self.selected[0]][0] += 100_000
            else: changed['approval_granted'] = True
            with self.subTest(mode=mode): self.refused(intent.validate_draft, self.inspection, changed)

    def test_changed_review_settings_plan_or_pose_revoke_prior_intent(self):
        proposal = self.proposal()
        for mode in ('protection', 'region', 'plan', 'observation', 'pose'):
            review = intent.Review(proposal); review.decision(acknowledged=True, accepted=True)
            if mode == 'protection': review.settings['protected_names'] = ['KEEP']
            elif mode == 'region': review.settings['region_nm'][0] += 100_000
            elif mode == 'plan': review.copper_plan['removed_routes'].clear()
            elif mode == 'observation': review.observation['route_count'] = 0
            else: review.pose['transforms'][0]['x_mm'] = -100
            with self.subTest(mode=mode): self.refused(review.decision, acknowledged=True, accepted=True)
            self.assertIsNone(review.intent)

    def test_changed_source_revokes_review_and_refuses_recomputation(self):
        review = intent.Review(self.proposal()); draft = review.decision(acknowledged=True, accepted=True)
        self.board.write_bytes(self.source + b'\n')
        self.refused(intent.copper_plan, self.inspection, self.settings)
        self.refused(intent.effective_observation, self.inspection, self.settings)
        self.refused(intent.validate_draft, self.inspection, draft)
        self.refused(review.decision, acknowledged=True, accepted=True)
        self.assertIsNone(review.intent)

    def test_captured_source_bytes_are_checked_before_planning(self):
        check = intent.current
        def change_after_check(inspection):
            result = check(inspection)
            self.board.write_bytes(self.source + b'\n')
            return result
        with patch.object(intent, 'current', side_effect=change_after_check), \
             patch.object(copper, 'propose', side_effect=AssertionError('changed capture must refuse before planning')):
            self.refused(intent.copper_plan, self.inspection, self.settings)

    def test_preparation_uses_captured_bytes_and_final_source_fence_refuses_late_change(self):
        prepare = copper.prepare
        def change_after_prepare(source, plan):
            self.assertEqual(source, self.source)
            result = prepare(source, plan)
            project = self.board.with_suffix('.kicad_pro')
            project.write_bytes(project.read_bytes() + b'\n')
            return result
        with patch.object(copper, 'prepare', side_effect=change_after_prepare):
            self.refused(intent.effective_observation, self.inspection, self.settings)


if __name__ == '__main__':
    unittest.main()
