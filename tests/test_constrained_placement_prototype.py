"""Small synthetic proxy controls; no KiCad, application or routing claims."""
import copy
import hashlib
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

from experiments.constrained_placement_v1 import constraints as c, prototype as p


def fixture():
    def part(cid, x, y, net='signal', locked=False):
        return dict(id=cid, position_mm=[x, y], size_mm=[2, 2], rotation_deg=0,
                    side='front', locked=locked,
                    pads=[dict(id=cid + '/A7', net=net, offset_mm=[0, 0])],
                    allowed_region_mm=[0, 0, 40, 40],
                    allowed_rotations_deg=[0, 90, 180, 270], allowed_sides=['front'])
    return dict(schema=1, board=dict(kind='rectangle', bounds_mm=[0, 0, 40, 40], cutouts=[]),
                components=[part('anchor', 4, 4, locked=True), part('selected-b', 25, 10),
                            part('selected-c', 34, 28), part('track-anchor', 4, 33, 'tracked-net')],
                selected=['selected-b', 'selected-c'], fixed_components=['anchor'], groups=[],
                tracks=[], keepouts=[dict(id='restricted', kind='rectangle',
                    bounds_mm=[15, 15, 18, 18], sides=['front', 'back'])], clearance_mm=0.5)


def transform(alternative, cid):
    return next(t for t in alternative['transforms'] if t['component_id'] == cid)


def region_fixture(*, joint=False):
    source = fixture()
    regions = ([[8, 4, 14, 8]] * 2 if joint else
               [[8, 8, 14, 14], [23, 28, 30, 35]])
    for component, region in zip(source['components'][1:3], regions):
        component['allowed_region_mm'] = list(region)
        component['allowed_rotations_deg'] = [component['rotation_deg']]
    return source


class RegionInitialization(unittest.TestCase):
    """Finite synthetic initializer controls; no Native/application authority."""

    def propose(self, source, **options):
        return p.propose(source, steps=20, alternatives=1, seconds=2,
                         region_initialization=p.REGION_INITIALIZATION_POLICY, **options)

    def assert_no_authority(self, result):
        for record in (result, result['region_initialization']):
            for field in ('native_validation_performed', 'execution_authorized', 'approval_granted'):
                self.assertIs(record[field], False)

    def test_default_target_region_refusal_and_result_shape_are_unchanged(self):
        source = region_fixture(); before = copy.deepcopy(source)
        with self.assertRaisesRegex(c.Refused, 'Initially feasible.*allowed region'):
            p.propose(source)
        with self.assertRaisesRegex(c.Refused, 'allowed region'):
            p.source_context(source)
        self.assertEqual(source, before)
        result = p.propose(fixture(), steps=1, alternatives=1, seconds=2)
        self.assertNotIn('region_initialization', result)

    def test_single_selected_source_context_is_original_bound_but_not_a_valid_target(self):
        source = region_fixture(); source['selected'] = ['selected-b']
        source['components'][2]['allowed_region_mm'] = [0, 0, 40, 40]
        before = copy.deepcopy(source)
        context = p.source_context(source, region_initialization=p.REGION_INITIALIZATION_POLICY)
        self.assertEqual(context, c.original_alternative(source))
        self.assertEqual(context['source_sha256'], c.digest(source))
        with self.assertRaisesRegex(c.Refused, 'allowed region'):
            c.validate_alternative(source, context)
        with self.assertRaisesRegex(c.Refused, 'at least two movable'):
            self.propose(source)
        self.assertEqual(source, before)

    def test_two_source_regions_seed_then_real_search_preserves_original_facts(self):
        source = region_fixture(); before = copy.deepcopy(source)
        result = self.propose(source)
        self.assertEqual(result['status'], 'proposals_ready')
        record = result['region_initialization']
        self.assertEqual(record['status'], 'seed_ready')
        self.assertEqual(record['candidates_checked'], 1)
        self.assertIs(record['source_context_only'], True)
        self.assertIs(record['seed_publicly_validated'], True)
        self.assertEqual(record['original_facts_sha256'], c.digest(before))
        self.assertEqual(result['source_sha256'], c.digest(before))
        self.assertGreater(result['counts']['attempted_moves'], 0)
        self.assertEqual(c.validate_alternative(source, record['seed']), record['seed'])
        for item in result['alternatives']:
            self.assertEqual(c.validate_alternative(source, item['candidate']), item['candidate'])
        self.assertEqual(source, before)
        self.assert_no_authority(result)

    def test_joint_seed_resolves_clamp_conflict_deterministically_without_score_gain(self):
        source = region_fixture(joint=True)
        clamped = c.original_alternative(source)
        for identity in source['selected']:
            transform(clamped, identity).update(x_mm=13, y_mm=7)
        with self.assertRaisesRegex(c.Refused, 'overlap'):
            c.validate_alternative(source, clamped)
        with patch.object(p.Annealer, 'run', return_value=None):
            first = self.propose(source); second = self.propose(source)
        self.assertEqual(first['status'], 'proposals_ready')
        self.assertEqual(first['region_initialization'], second['region_initialization'])
        self.assertEqual(first['alternatives'], second['alternatives'])
        record = first['region_initialization']
        self.assertGreater(record['candidates_checked'], 1)
        self.assertLessEqual(record['candidates_checked'], 256)
        self.assertEqual(record['candidate_limit'], p.MAX_REGION_SEED_CANDIDATES)
        self.assertEqual(c.validate_alternative(source, record['seed']), record['seed'])
        item = first['alternatives'][0]
        self.assertEqual(item['candidate'], record['seed'])
        self.assertEqual(item['before_proxy_cost'], item['after_proxy_cost'])
        self.assertEqual(first['bounds']['wall_and_cpu_seconds'], 2)

    def test_finite_seed_miss_has_no_alternative_or_application_authority(self):
        source = region_fixture()
        for component in source['components'][1:3]:
            component['allowed_region_mm'] = [8, 4, 10, 6]
        with patch.object(p.Annealer, 'run') as run:
            result = self.propose(source)
        run.assert_not_called()
        self.assertEqual(result['status'], 'no_feasible_region_seed')
        self.assertEqual(result['alternatives'], [])
        self.assertEqual(result['counts']['attempted_alternatives'], 0)
        record = result['region_initialization']
        self.assertEqual(record['status'], 'no_feasible_region_seed')
        self.assertEqual(record['candidates_checked'], 1)
        self.assertNotIn('seed', record)
        self.assertIs(record['seed_publicly_validated'], False)
        self.assertTrue(any('not infeasibility proof' in line for line in result['limits']))
        self.assert_no_authority(result)

    def test_target_region_cannot_repair_physical_or_unselected_source_conflicts(self):
        cases = []
        source = region_fixture(); source['components'][1]['position_mm'] = [0.5, 10]
        cases.append(('outside rectangular board', source))
        source = region_fixture(); source['components'][1]['position_mm'] = [34, 28]
        cases.append(('overlap', source))
        source = region_fixture(); source['components'][1]['position_mm'] = [16, 16]
        cases.append(('keepout', source))
        source = region_fixture(); source['components'][0]['position_mm'] = [0.5, 4]
        cases.append(('outside rectangular board', source))
        source = region_fixture(); source['components'][3]['allowed_region_mm'] = [20, 20, 30, 30]
        cases.append(('allowed region', source))
        source = region_fixture(); source['components'][1]['allowed_rotations_deg'] = [90]
        cases.append(('orientation', source))
        for error, source in cases:
            before = copy.deepcopy(source)
            with self.subTest(error=error), patch.object(p.Annealer, 'run') as run:
                with self.assertRaisesRegex(c.Refused, error):
                    self.propose(source)
                run.assert_not_called()
                self.assertEqual(source, before)

    def test_fixed_locked_tracked_selected_parts_and_larger_or_group_scope_refuse(self):
        cases = []
        source = region_fixture(); source['fixed_components'].append('selected-b'); cases.append(source)
        source = region_fixture(); source['components'][1]['locked'] = True; cases.append(source)
        source = region_fixture()
        source['tracks'] = [dict(id='existing-track', net='signal', pad_ids=['selected-b/A7'])]
        cases.append(source)
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(c.Refused, 'fixed/locked/tracked'):
                    p.source_context(source, region_initialization=p.REGION_INITIALIZATION_POLICY)
                with self.assertRaises(c.Refused):
                    self.propose(source)
        source = region_fixture(); source['selected'].append('track-anchor')
        with self.assertRaisesRegex(c.Refused, 'at most two independent'):
            self.propose(source)
        source = region_fixture()
        source['groups'] = [dict(policy=c.RIGID_TRANSLATION_POLICY, members=source['selected'])]
        with self.assertRaisesRegex(c.Refused, 'at most two independent'):
            self.propose(source)
        for policy in (True, '', 'selected-target-region-initialization-v2'):
            with self.subTest(policy=policy), self.assertRaisesRegex(c.Refused, 'Unsupported region initialization'):
                p.propose(region_fixture(), region_initialization=policy)

    def test_private_filter_cannot_authorize_an_invalid_chosen_seed(self):
        source = region_fixture(joint=True)
        # Deliberately broken private filter accepts the first overlapping clamp.
        # The independently constructed public validator must reject it before search.
        with patch.object(p, '_alternative_validator', return_value=copy.deepcopy) as private, \
                patch.object(p, 'validate_alternative', wraps=c.validate_alternative) as public, \
                patch.object(p.Annealer, 'run') as run:
            with self.assertRaisesRegex(c.Refused, 'overlap'):
                self.propose(source)
        private.assert_called_once(); run.assert_not_called()
        chosen = public.call_args.args[1]
        self.assertEqual(chosen['source_sha256'], c.digest(source))
        self.assertEqual(transform(chosen, 'selected-b')['x_mm'], 13)
        self.assertEqual(transform(chosen, 'selected-c')['x_mm'], 13)

    def test_seed_preserves_fixed_poses_angles_sides_and_rotated_dimensions(self):
        source = region_fixture()
        source['components'][1].update(size_mm=[4, 2], rotation_deg=90,
            allowed_rotations_deg=[90], side='back', allowed_sides=['back'],
            allowed_region_mm=[8, 4, 14, 10])
        source['components'][2].update(size_mm=[2, 4], rotation_deg=180,
            allowed_rotations_deg=[180], allowed_region_mm=[22, 22, 28, 28])
        before = copy.deepcopy(source); original = c.original_alternative(source)
        with patch.object(p.Annealer, 'run', return_value=None):
            result = self.propose(source)
        seed = result['region_initialization']['seed']
        self.assertEqual((transform(seed, 'selected-b')['x_mm'], transform(seed, 'selected-b')['y_mm']), (13, 8))
        for component in source['components']:
            pose = transform(seed, component['id'])
            self.assertEqual(pose['rotation_deg'], component['rotation_deg'])
            self.assertEqual(pose['side'], component['side'])
            if component['id'] in c.immovable(source):
                self.assertEqual(pose, transform(original, component['id']))
        self.assertEqual(c.validate_alternative(source, seed), seed)
        self.assertEqual(seed['source_sha256'], c.digest(before))
        self.assertEqual(source, before)

    def test_cancellation_during_seed_discards_seed_and_alternatives(self):
        source = region_fixture(); event = threading.Event()
        original_factory = p._alternative_validator
        def factory(facts):
            validate = original_factory(facts)
            def cancel_after_validate(candidate):
                value = validate(candidate); event.set(); return value
            return cancel_after_validate
        with patch.object(p, '_alternative_validator', side_effect=factory), \
                patch.object(p.Annealer, 'run') as run:
            result = self.propose(source, cancel_event=event)
        run.assert_not_called()
        self.assertEqual(result['status'], 'cancelled')
        self.assertEqual(result['alternatives'], [])
        self.assertEqual(result['region_initialization']['candidates_checked'], 1)
        self.assertNotIn('seed', result['region_initialization'])
        self.assertIs(result['region_initialization']['seed_publicly_validated'], False)

    def test_wall_and_cpu_deadline_during_seed_share_the_two_second_budget(self):
        original_factory = p._alternative_validator
        for exhausted_clock in ('wall', 'cpu'):
            clock = dict(wall=0.0, cpu=0.0)
            def factory(facts):
                validate = original_factory(facts)
                def exhaust_after_validate(candidate):
                    value = validate(candidate); clock[exhausted_clock] = 2.0; return value
                return exhaust_after_validate
            with self.subTest(clock=exhausted_clock), \
                    patch.object(p.time, 'monotonic', side_effect=lambda: clock['wall']), \
                    patch.object(p.time, 'process_time', side_effect=lambda: clock['cpu']), \
                    patch.object(p, '_alternative_validator', side_effect=factory), \
                    patch.object(p.Annealer, 'run') as run:
                result = self.propose(region_fixture())
            run.assert_not_called()
            self.assertEqual(result['status'], 'budget_exhausted')
            self.assertEqual(result['alternatives'], [])
            self.assertEqual(result['bounds']['wall_and_cpu_seconds'], 2)
            self.assertEqual(result['region_initialization']['candidates_checked'], 1)
            self.assertNotIn('seed', result['region_initialization'])

    def test_cancel_and_deadlines_during_final_readback_discard_all_proposals(self):
        for interruption in ('cancelled', 'wall', 'cpu'):
            event = threading.Event(); clock = dict(wall=0.0, cpu=0.0)
            state = dict(engine_finished=False, validations_after_engine=0)
            def finish_engine(engine, **options):
                state['engine_finished'] = True
            def validate(facts, candidate):
                value = c.validate_alternative(facts, candidate)
                if state['engine_finished']:
                    state['validations_after_engine'] += 1
                    if state['validations_after_engine'] == 2:
                        if interruption == 'cancelled': event.set()
                        else: clock[interruption] = 2.0
                return value
            with self.subTest(interruption=interruption), \
                    patch.object(p.time, 'monotonic', side_effect=lambda: clock['wall']), \
                    patch.object(p.time, 'process_time', side_effect=lambda: clock['cpu']), \
                    patch.object(p, 'validate_alternative', side_effect=validate), \
                    patch.object(p.Annealer, 'run', finish_engine):
                result = self.propose(region_fixture(), cancel_event=event)
            self.assertEqual(state['validations_after_engine'], 2)
            self.assertEqual(result['status'], 'cancelled' if interruption == 'cancelled' else 'budget_exhausted')
            self.assertEqual(result['alternatives'], [])
            self.assertNotIn('seed', result['region_initialization'])
            self.assertIs(result['region_initialization']['seed_publicly_validated'], False)
            self.assert_no_authority(result)

    def test_source_mutation_during_final_region_readback_is_refused(self):
        source = region_fixture(); state = dict(engine_finished=False, validations_after_engine=0)
        def finish_engine(engine, **options):
            state['engine_finished'] = True
        def mutate_on_final_readback(facts, candidate):
            value = c.validate_alternative(facts, candidate)
            if state['engine_finished']:
                state['validations_after_engine'] += 1
                if state['validations_after_engine'] == 2:
                    source['components'][1]['position_mm'][0] += 1
            return value
        with patch.object(p.Annealer, 'run', finish_engine), \
                patch.object(p, 'validate_alternative', side_effect=mutate_on_final_readback), \
                self.assertRaisesRegex(c.Refused, 'changed during final region readback'):
            self.propose(source)
        self.assertEqual(state['validations_after_engine'], 2)


class ConstrainedPlacementPrototype(unittest.TestCase):
    def test_huge_json_integer_is_a_controlled_refusal(self):
        source = fixture(); source['components'][1]['position_mm'][0] = 10**400
        with self.assertRaisesRegex(c.Refused, 'bounded finite number'):
            c.prepare(source)

    def test_tiny_or_collapsed_rectangles_cannot_hide_overlap(self):
        source = fixture(); source['clearance_mm'] = 0
        for component in source['components'][1:3]:
            component['size_mm'] = [1e-15, 1e-15]
            component['position_mm'] = [25, 10]
        with self.assertRaisesRegex(c.Refused, 'at least one nanometre'):
            c.validate_alternative(source, c.original_alternative(source))
        for rectangle in ([25, 10, 25, 10], [0, 0, 1e-15, 1e-15]):
            with self.subTest(rectangle=rectangle), self.assertRaises(c.Refused):
                c.rect(rectangle, 'tiny region')
        component = dict(size_mm=[1e-15, 1e-15])
        with self.assertRaisesRegex(c.Refused, 'collapsed'):
            c.bounds(component, dict(x_mm=25, y_mm=10, rotation_deg=0))

    def test_vendored_source_and_license_match_pinned_official_blobs(self):
        root = Path(p.__file__).parent
        record = json.loads((root / 'upstream.json').read_text())
        self.assertEqual(record['commit'], p.UPSTREAM_COMMIT)
        self.assertEqual(record['license'], 'MIT')
        for item in record['files']:
            raw = (root / item['local_path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item['sha256'])
            self.assertEqual(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
                             record['expected_git_blob_sha1'][item['upstream_path']])
        self.assertIn('Copyright (c) 2026 DTU and EKB Contributors', (root / 'vendor/LICENSE').read_text())

    def test_real_reused_search_is_deterministic_valid_and_source_preserving(self):
        source = fixture(); before = copy.deepcopy(source)
        first = p.propose(source, seed=7, steps=160, alternatives=2, seconds=5)
        second = p.propose(source, seed=7, steps=160, alternatives=2, seconds=5)
        self.assertEqual(first['status'], 'proposals_ready')
        self.assertEqual(first['alternatives'], second['alternatives'])
        self.assertEqual(source, before)
        self.assertLessEqual(len(first['alternatives']), 2)
        self.assertEqual(first['counts']['attempted_moves'], 320)
        self.assertEqual(first['source_sha256'], c.digest(source))
        for item in first['alternatives']:
            self.assertEqual(c.validate_alternative(source, item['candidate']), item['candidate'])
            self.assertLess(item['after_proxy_cost'], item['before_proxy_cost'])
        for key in ('execution_authorized', 'approval_granted', 'native_validation_performed'):
            self.assertIs(first[key], False)

    def test_restricted_regions_and_orientations_survive_real_search(self):
        source = fixture()
        for part in source['components'][1:3]:
            part['allowed_region_mm'] = [20, 1, 39, 39]
            part['allowed_rotations_deg'] = [0, 180]
        result = p.propose(source, seed=3, steps=160, alternatives=2, seconds=5)
        self.assertEqual(result['status'], 'proposals_ready')
        self.assertGreater(result['counts']['constraint_rejected_moves'], 0)
        for item in result['alternatives']:
            c.validate_alternative(source, item['candidate'])
            for cid in source['selected']:
                self.assertIn(transform(item['candidate'], cid)['rotation_deg'], [0, 180])

    def test_independent_out_of_bounds_region_keepout_and_overlap_refusals(self):
        source = fixture()
        cases = [({'x_mm': 50}, 'outside rectangular board'),
                 ({'x_mm': 16, 'y_mm': 16}, 'keepout'),
                 ({'x_mm': 34, 'y_mm': 28}, 'overlap')]
        for changes, message in cases:
            candidate = c.original_alternative(source)
            transform(candidate, 'selected-b').update(changes)
            with self.subTest(message=message), self.assertRaisesRegex(c.Refused, message):
                c.validate_alternative(source, candidate)
        source['components'][1]['allowed_region_mm'] = [20, 0, 40, 40]
        candidate = c.original_alternative(source)
        transform(candidate, 'selected-b')['x_mm'] = 19
        with self.assertRaisesRegex(c.Refused, 'allowed region'):
            c.validate_alternative(source, candidate)

    def test_locked_fixed_unselected_and_tracked_components_are_immovable(self):
        source = fixture()
        source['selected'].append('track-anchor')
        source['tracks'] = [dict(id='existing-track', net='tracked-net', pad_ids=['track-anchor/A7'])]
        candidate = c.original_alternative(source)
        for cid in ('anchor', 'track-anchor'):
            changed = copy.deepcopy(candidate); transform(changed, cid)['x_mm'] += 1
            with self.subTest(cid=cid), self.assertRaisesRegex(c.Refused, 'tracked component moved'):
                c.validate_alternative(source, changed)
        result = p.propose(source, seed=2, steps=80, alternatives=1, seconds=5)
        self.assertEqual(result['status'], 'proposals_ready')
        self.assertIn('track-anchor', result['fixed_components'])
        for item in result['alternatives']:
            self.assertEqual(transform(item['candidate'], 'track-anchor'), transform(candidate, 'track-anchor'))
        source['tracks'] = []; source['selected'].remove('track-anchor')
        changed = c.original_alternative(source); transform(changed, 'track-anchor')['x_mm'] += 1
        with self.assertRaisesRegex(c.Refused, 'unselected'):
            c.validate_alternative(source, changed)

    def test_tracked_net_freezes_even_unspecified_terminal_incidence(self):
        source = fixture()
        source['components'][1]['pads'][0]['net'] = 'tracked-net'
        source['tracks'] = [dict(id='track', net='tracked-net', pad_ids=['track-anchor/A7'])]
        self.assertIn('selected-b', c.immovable(source))
        with self.assertRaisesRegex(c.Refused, 'at least two movable'):
            p.propose(source)
        source['tracks'][0]['pad_ids'] = ['missing-pad']
        with self.assertRaisesRegex(c.Refused, 'incidence/net'):
            c.prepare(source)

    def test_infeasible_initial_rectangle_refuses_without_mutation(self):
        source = fixture(); source['components'][1]['size_mm'] = [50, 2]
        before = copy.deepcopy(source)
        with self.assertRaisesRegex(c.Refused, 'Initially feasible'):
            p.propose(source)
        self.assertEqual(source, before)

    def test_forbidden_side_orientation_and_forged_identity_refuse(self):
        source = fixture(); source['components'][1]['allowed_rotations_deg'] = [0]
        for field, value, error in (('rotation_deg', 90, 'orientation'), ('side', 'back', 'Side flips'),
                                     ('component_id', 'unknown', 'unknown')):
            candidate = c.original_alternative(source); transform(candidate, 'selected-b')[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(c.Refused, error):
                c.validate_alternative(source, candidate)
        candidate = c.original_alternative(source); candidate['transforms'].pop()
        with self.assertRaises(c.Refused):c.validate_alternative(source, candidate)
        candidate = c.original_alternative(source); candidate['transforms'][1]['pads'] = []
        with self.assertRaises(c.Refused):c.validate_alternative(source, candidate)

    def test_connectivity_pad_ids_and_source_binding_are_exact(self):
        source = fixture(); candidate = c.original_alternative(source)
        for field, value in (('id', 'renamed-B9'), ('net', 'different-net')):
            changed = copy.deepcopy(source); changed['components'][1]['pads'][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(c.Refused, 'source binding'):
                c.validate_alternative(changed, candidate)
        duplicate = copy.deepcopy(source)
        duplicate['components'][1]['pads'][0]['id'] = 'anchor/A7'
        with self.assertRaisesRegex(c.Refused, 'duplicate'):
            c.prepare(duplicate)

    def test_engine_pad_mutation_is_detected(self):
        source = fixture(); before = copy.deepcopy(source)
        def corrupt(engine, **_):
            engine.board.components['selected-b'].pads[0].name = 'lost-A7'
        with patch.object(p.Annealer, 'run', corrupt), self.assertRaisesRegex(c.Refused, 'Engine changed'):
            p.propose(source, alternatives=1)
        self.assertEqual(source, before)

    def test_power_like_names_are_not_interpreted_or_excluded(self):
        source = fixture()
        for part in source['components'][:3]:part['pads'][0]['net'] = 'GND/VDD'
        board = p._model(source)
        engine = p._ConstrainedAnnealer(board, source, 0, lambda: None,
                                       dict(attempted_moves=0, constraint_rejected_moves=0))
        self.assertEqual(set(board.nets()), set(engine.net_members))
        self.assertFalse(engine.decap)
        for part in source['components']:
            self.assertEqual([pad.name for pad in board.components[part['id']].pads], [part['id'] + '/A7'])

    def test_cancellation_before_and_during_search_discards_proposals(self):
        source = fixture(); event = threading.Event(); event.set()
        result = p.propose(source, cancel_event=event)
        self.assertEqual(result['status'], 'cancelled'); self.assertEqual(result['alternatives'], [])
        self.assertEqual(result['counts']['attempted_moves'], 0)
        event.clear(); move = p._ConstrainedAnnealer._move
        def cancel_after_move(engine, method, *args):
            value = move(engine, method, *args); event.set(); return value
        with patch.object(p._ConstrainedAnnealer, '_move', cancel_after_move):
            result = p.propose(source, cancel_event=event)
        self.assertEqual(result['status'], 'cancelled'); self.assertEqual(result['alternatives'], [])
        self.assertEqual(result['counts']['attempted_moves'], 1)

    def test_deadline_and_numeric_budgets_are_bounded(self):
        with patch.object(p.time, 'monotonic', side_effect=[0.0, 6.0, 6.0]):
            result = p.propose(fixture(), seconds=1)
        self.assertEqual(result['status'], 'budget_exhausted'); self.assertEqual(result['alternatives'], [])
        for options in ({'seed': True}, {'steps': 1001}, {'alternatives': 4},
                        {'seed': 2**31 - 1, 'alternatives': 2},
                        {'seconds': float('nan')}, {'seconds': 5.1}, {'cancel_event': lambda: False}):
            with self.subTest(options=options), self.assertRaises(c.Refused):
                p.propose(fixture(), **options)

    def test_groups_polygon_cutouts_and_unannounced_fields_refuse(self):
        cases = []
        source = fixture(); source['groups'] = [{'members': source['selected'], 'rigid': True}]; cases.append(source)
        source = fixture(); source['board']['kind'] = 'polygon'; cases.append(source)
        source = fixture(); source['board']['cutouts'] = [[1, 1, 2, 2]]; cases.append(source)
        source = fixture(); source['approval_granted'] = True; cases.append(source)
        for source in cases:
            with self.subTest(source=source), self.assertRaises(c.Refused):p.propose(source)
        source = fixture(); source['selected'] = [part['id'] for part in source['components']]
        source['fixed_components'] = []; source['components'][0]['locked'] = False
        with self.assertRaisesRegex(c.Refused, 'anchor'):
            p.propose(source)


if __name__ == '__main__':
    unittest.main()
