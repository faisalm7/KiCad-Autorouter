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
