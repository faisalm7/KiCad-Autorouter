"""Pure schema3 constraint controls, never Native or clearance certification."""
import copy
from decimal import localcontext
import unittest
from unittest.mock import patch
import uuid

from autorouter import placement_annotations as annotations
from experiments.constrained_placement_v1 import constraints as c


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'owned-selected-copper-baseline:' + name))


A, B, F = (uid(name) for name in ('A', 'B', 'fixed'))


def component(identity, position):
    return dict(id=identity, position_mm=position, size_mm=[2, 2], rotation_deg=0,
        side='front', locked=False, pads=[], allowed_region_mm=[0, 0, 20, 10],
        allowed_rotations_deg=[0, 90], allowed_sides=['front', 'back'])


def facts(*, annotated=False):
    value = dict(schema=3, fixed_context_policy=c.FIXED_CONTEXT_POLICY,
        selected_copper_baseline_policy=c.SELECTED_COPPER_BASELINE_POLICY,
        proxy_anchor_offsets_twice_nm={A: [0, 0], B: [0, 0]},
        board=dict(kind='rectangle', bounds_mm=[0, 0, 20, 10], cutouts=[]),
        components=[component(A, [4, 4]), component(B, [9, 4]), component(F, [15, 4])],
        selected=[A, B], fixed_components=[F], groups=[], tracks=[], clearance_mm=.2,
        keepouts=[dict(id=uid('copper-A'), kind=c.PRESERVED_COPPER,
                      bounds_mm=[3.1, 3.5, 3.2, 4.5], sides=['front']),
                  dict(id=uid('copper-B'), kind=c.PRESERVED_COPPER,
                      bounds_mm=[8.1, 3.5, 8.2, 4.5], sides=['front'])])
    if annotated:
        value['components'][0]['position_mm'] = [4.0000005, 4.000001]
        value['components'][1]['position_mm'] = [9.0000005, 4]
        value[c.PROXY_ANCHOR_OFFSETS] = {A: [1, 2], B: [-1, -2]}
        value['annotation_context'] = dict(schema=1, policy=annotations.POLICY,
            scope=annotations.SCOPE, source_board_sha256='a'*64, outline_nm=[0, 0, 20000000, 10000000],
            silk_clearance_nm=0, footprint_anchors_nm={A: [4000000, 4000000],
                B: [9000001, 4000001], F: [15000000, 4000000]},
            movable_owners=[A, B], rows=[])
    return value


class SelectedCopperBaselineTests(unittest.TestCase):
    def both(self, value, alternative):
        expected = copy.deepcopy(alternative)
        self.assertEqual(c.validate_alternative(value, alternative), expected)
        self.assertEqual(c._alternative_validator(value)(alternative), expected)

    def refuse_both(self, value, alternative=None):
        alternative = c.original_alternative(value) if alternative is None else alternative
        for factory in (lambda: lambda alt: c.validate_alternative(value, alt),
                        lambda: c._alternative_validator(value)):
            with self.assertRaises(c.Refused): factory()(alternative)

    def pose(self, alt, identity=A):
        return next(row for row in alt['transforms'] if row['component_id'] == identity)

    def test_exact_original_selected_poses_allow_only_typed_copper(self):
        value = facts(); before = copy.deepcopy(value)
        self.both(value, c.original_alternative(value))
        self.assertEqual(value, before)
        for keepout in value['keepouts']: keepout['kind'] = 'rectangle'
        self.refuse_both(value)

    def test_each_selected_component_is_independent_and_changed_pose_is_strict(self):
        value = facts(); original = c.original_alternative(value)
        for field, changed in (('x_mm', 4.000001), ('rotation_deg', 90), ('side', 'back')):
            alt = copy.deepcopy(original); self.pose(alt)[field] = changed
            self.refuse_both(value, alt)
        moved = copy.deepcopy(original); self.pose(moved)['y_mm'] = 8
        self.both(value, moved)  # B alone still occupies its exact baseline copper overlap.

    def test_no_board_region_pair_or_real_user_keepout_waiver(self):
        for fault in ('board', 'region', 'pair', 'user-rectangle'):
            value = facts()
            if fault == 'board': value['board']['bounds_mm'][0] = 3.1
            if fault == 'region': value['components'][0]['allowed_region_mm'][2] = 4.5
            if fault == 'pair': value['components'][1]['position_mm'] = [4.5, 4]
            if fault == 'user-rectangle': value['keepouts'].append(dict(id=uid('real-user'),
                kind='rectangle', bounds_mm=[3.1, 3.5, 3.2, 4.5], sides=['front']))
            with self.subTest(fault=fault): self.refuse_both(value)

    def test_fixed_locked_and_tracked_parts_stay_immutable(self):
        for fault in ('fixed', 'locked', 'tracked'):
            value = facts()
            if fault == 'fixed': identity = F
            else:
                identity = A
                if fault == 'locked': value['components'][0]['locked'] = True
                else:
                    value['components'][0]['pads'] = [dict(id=uid('pad-A'), net='net-A', offset_mm=[0, 0])]
                    value['tracks'] = [dict(id=uid('track'), net='net-A', pad_ids=[uid('pad-A')])]
            alt = c.original_alternative(value); self.pose(alt, identity)['y_mm'] = 8
            with self.subTest(fault=fault): self.refuse_both(value, alt)

    def test_old_schema2_still_refuses_selected_baseline_overlap(self):
        value = facts(); value['schema'] = 2
        value.pop('selected_copper_baseline_policy'); value.pop(c.PROXY_ANCHOR_OFFSETS)
        self.refuse_both(value)
        # Old v1 rejects typed preserved-copper keepouts rather than inheriting schema3.
        value['schema'] = 1; value.pop('fixed_context_policy')
        self.refuse_both(value)

    def test_schema_policy_and_exact_selected_offsets_cannot_be_laundered(self):
        for fault in ('missing-policy', 'policy', 'missing-map', 'missing-ID', 'extra-ID',
                      'bool', 'float', 'tuple', 'range', 'length', 'fixed-policy', 'old-schema-extra'):
            value = facts()
            if fault == 'missing-policy': value.pop('selected_copper_baseline_policy')
            if fault == 'policy': value['selected_copper_baseline_policy'] = 'other'
            if fault == 'missing-map': value.pop(c.PROXY_ANCHOR_OFFSETS)
            if fault == 'missing-ID': value[c.PROXY_ANCHOR_OFFSETS].pop(B)
            if fault == 'extra-ID': value[c.PROXY_ANCHOR_OFFSETS][F] = [0, 0]
            if fault == 'bool': value[c.PROXY_ANCHOR_OFFSETS][A][0] = True
            if fault == 'float': value[c.PROXY_ANCHOR_OFFSETS][A][0] = .5
            if fault == 'tuple': value[c.PROXY_ANCHOR_OFFSETS][A] = (0, 0)
            if fault == 'range': value[c.PROXY_ANCHOR_OFFSETS][A][0] = 4000000001
            if fault == 'length': value[c.PROXY_ANCHOR_OFFSETS][A].append(0)
            if fault == 'fixed-policy': value['fixed_context_policy'] = 'other'
            if fault == 'old-schema-extra': value['schema'] = 2
            with self.subTest(fault=fault): self.refuse_both(value)

    def test_half_nanometre_source_proxy_offsets_bind_exact_real_annotation_anchors(self):
        value = facts(annotated=True)
        with localcontext() as context:
            context.prec = 6
            self.both(value, c.original_alternative(value))
        for fault in ('real-anchor', 'offset', 'proxy', 'board', 'movable'):
            bad = copy.deepcopy(value)
            if fault == 'real-anchor': bad['annotation_context']['footprint_anchors_nm'][A][0] += 1
            if fault == 'offset': bad[c.PROXY_ANCHOR_OFFSETS][A][0] += 1
            if fault == 'proxy': bad['components'][0]['position_mm'][0] += .000001
            if fault == 'board': bad['annotation_context']['outline_nm'][0] += 1
            if fault == 'movable': bad['annotation_context']['movable_owners'].remove(A)
            with self.subTest(fault=fault): self.refuse_both(bad)

    def test_annotation_moves_subtract_offsets_before_integer_nm_rounding(self):
        value = facts(annotated=True); alt = c.original_alternative(value)
        self.pose(alt)['y_mm'] = 8.000001
        expected = {A: [4000000, 8000000], B: [9000001, 4000001]}
        actual_check = annotations._check_prepared_moves
        calls = []
        def observe(context, moves):
            calls.append(copy.deepcopy(moves))
            self.assertEqual(moves, expected)
            return actual_check(context, moves)
        with patch.object(annotations, '_check_prepared_moves', side_effect=observe), localcontext() as context:
            context.prec = 6
            self.both(value, alt)
        self.assertEqual(calls, [expected, expected])

    def test_exact_annotation_board_conversion_is_independent_of_ambient_precision(self):
        value = facts(annotated=True)
        value['board']['bounds_mm'] = [0, 0, 1934.567891, 1000.000001]
        value['annotation_context']['outline_nm'] = [0, 0, 1934567891, 1000000001]
        expected = c.prepare(value)
        with localcontext() as context:
            context.prec = 6
            self.assertEqual(c.prepare(value), expected)
            self.both(value, c.original_alternative(value))
        bad = copy.deepcopy(value)
        bad['annotation_context']['outline_nm'][2] += 1
        with localcontext() as context:
            context.prec = 6
            self.refuse_both(bad)

    def test_annotation_conflicts_remain_mandatory_for_new_poses(self):
        value = facts(annotated=True)
        value['annotation_context']['rows'] = [
            dict(uuid=uid('moving-mask'), owner=A, kind='mask', bbox_nm=[0, 0, 100000, 100000], mask_expansion_nm=0),
            dict(uuid=uid('fixed-silk'), owner=None, kind='silk', bbox_nm=[7000000,7000000,7200000,7200000])]
        self.both(value, c.original_alternative(value))
        alt = c.original_alternative(value); self.pose(alt).update(x_mm=7.0000005, y_mm=7.000001)
        self.refuse_both(value, alt)

    def test_cached_snapshot_and_final_source_digest_stay_independent(self):
        value = facts(annotated=True); original = c.original_alternative(value)
        cached = c._alternative_validator(value)
        value[c.PROXY_ANCHOR_OFFSETS][A][0] += 1
        self.assertEqual(cached(original), original)
        with self.assertRaises(c.Refused): c.validate_alternative(value, original)
        stale = copy.deepcopy(original); stale['source_sha256'] = '0'*64
        with self.assertRaises(c.Refused): cached(stale)


if __name__ == '__main__':
    unittest.main()
