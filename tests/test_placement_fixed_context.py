"""Fixed context is immutable, not permission for new moving conflicts."""
import copy
import unittest

from experiments.constrained_placement_v1 import constraints as c, prototype


def facts():
    def part(identity, x, y):
        return dict(id=identity, position_mm=[x, y], size_mm=[2, 2],
                    rotation_deg=0, side='front', locked=False,
                    pads=[dict(id=identity + '-pad', net='signal', offset_mm=[0, 0])],
                    allowed_region_mm=[0, 0, 40, 40],
                    allowed_rotations_deg=[0], allowed_sides=['front'])
    return dict(schema=2, fixed_context_policy=c.FIXED_CONTEXT_POLICY,
                board=dict(kind='rectangle', bounds_mm=[0, 0, 40, 40], cutouts=[]),
                components=[part('fixed-a', 0, 4), part('fixed-b', 0, 4),
                            part('move-a', 20, 10), part('move-b', 30, 25)],
                selected=['move-a', 'move-b'], fixed_components=['fixed-a', 'fixed-b'],
                groups=[], tracks=[], keepouts=[dict(id='copper', kind=c.PRESERVED_COPPER,
                    bounds_mm=[0, 2, 2, 7], sides=['front'])], clearance_mm=.3)


def row(alternative, identity):
    return next(t for t in alternative['transforms'] if t['component_id'] == identity)


class FixedContextTests(unittest.TestCase):
    def test_exact_fixed_baseline_can_be_outside_proxy_bounds_and_overlap(self):
        source = facts(); before = copy.deepcopy(source)
        original = c.original_alternative(source)
        self.assertEqual(c.validate_alternative(source, original), original)
        self.assertEqual(source, before)
        old = copy.deepcopy(source); old['schema'] = 1; del old['fixed_context_policy']
        old['keepouts'][0]['kind'] = 'rectangle'
        with self.assertRaisesRegex(c.Refused, 'outside rectangular board'):
            c.validate_alternative(old, c.original_alternative(old))

    def test_fixed_pose_changes_are_refused_even_with_inherited_conflicts(self):
        source = facts()
        for changes in ({'x_mm': .01}, {'rotation_deg': 90}, {'side': 'back'}):
            candidate = c.original_alternative(source); row(candidate, 'fixed-a').update(changes)
            with self.subTest(changes=changes), self.assertRaises(c.Refused):
                c.validate_alternative(source, candidate)

    def test_explicit_fixed_region_and_hard_keepout_are_not_waived(self):
        source = facts(); source['components'][0]['allowed_region_mm'] = [1, 1, 10, 10]
        with self.assertRaisesRegex(c.Refused, 'allowed region'):
            c.validate_alternative(source, c.original_alternative(source))
        source = facts(); source['keepouts'][0]['kind'] = 'rectangle'
        with self.assertRaisesRegex(c.Refused, 'keepout'):
            c.validate_alternative(source, c.original_alternative(source))

    def test_every_new_moving_boundary_region_pair_and_obstacle_is_checked(self):
        source = facts()
        cases = [({'x_mm': .1}, 'outside rectangular board'),
                 ({'x_mm': 1.5, 'y_mm': 4}, 'keepout'),
                 ({'x_mm': 30, 'y_mm': 25}, 'overlap')]
        for changes, reason in cases:
            candidate = c.original_alternative(source); row(candidate, 'move-a').update(changes)
            with self.subTest(reason=reason), self.assertRaisesRegex(c.Refused, reason):
                c.validate_alternative(source, candidate)
        # A fixed part inside the outline is still a moving-part obstacle.
        source['components'][0]['position_mm'] = [12, 12]
        candidate = c.original_alternative(source); row(candidate, 'move-a').update(x_mm=12, y_mm=12)
        with self.assertRaisesRegex(c.Refused, 'overlap'):
            c.validate_alternative(source, candidate)
        source['components'][2]['allowed_region_mm'] = [19, 0, 40, 40]
        candidate = c.original_alternative(source); row(candidate, 'move-a')['x_mm'] = 18
        with self.assertRaisesRegex(c.Refused, 'allowed region'):
            c.validate_alternative(source, candidate)

    def test_initial_moving_conflict_is_not_grandfathered(self):
        source = facts(); source['components'][2]['position_mm'] = [0, 4]
        with self.assertRaisesRegex(c.Refused, 'outside rectangular board'):
            c.validate_alternative(source, c.original_alternative(source))
        with self.assertRaisesRegex(c.Refused, 'Initially feasible'):
            prototype.propose(source, seed=7, steps=10, alternatives=1, seconds=1)

    def test_schema_policy_and_source_binding_cannot_be_substituted(self):
        source = facts(); candidate = c.original_alternative(source)
        for key, value in (('fixed_context_policy', 'ignore-all'), ('schema', True), ('schema', 3)):
            bad = copy.deepcopy(source); bad[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(c.Refused):
                c.validate_alternative(bad, candidate)
        bad = copy.deepcopy(source); bad['selected'].append('fixed-a')
        bad['fixed_components'].remove('fixed-a')
        with self.assertRaisesRegex(c.Refused, 'binding differs'):
            c.validate_alternative(bad, candidate)
        with self.assertRaisesRegex(c.Refused, 'outside rectangular board'):
            c.validate_alternative(bad, c.original_alternative(bad))

    def test_real_reused_search_preserves_fixed_baseline_and_constraints(self):
        source = facts(); before = copy.deepcopy(source)
        result = prototype.propose(source, seed=7, steps=80, alternatives=2, seconds=2)
        self.assertEqual(result['status'], 'proposals_ready')
        for alternative in result['alternatives']:
            candidate = alternative['candidate']; c.validate_alternative(source, candidate)
            for identity in ('fixed-a', 'fixed-b'):
                self.assertEqual(row(candidate, identity), row(c.original_alternative(source), identity))
        self.assertEqual(source, before)


if __name__ == '__main__':
    unittest.main()
