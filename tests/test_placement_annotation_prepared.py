"""Pure detached-search controls; no Native geometry/DRC qualification."""
import copy
import unittest
from unittest.mock import patch

from autorouter import placement_annotations as annotations
from experiments.constrained_placement_v1 import constraints as c
from tests import test_placement_annotation_geometry as geometry


OTHER = geometry.uid('other-fixed-owner')


def facts():
    def component(identity, position):
        return dict(id=identity, position_mm=position, size_mm=[.2, .2], rotation_deg=0,
            side='front', locked=False, pads=[], allowed_region_mm=[0, 0, 40, 40],
            allowed_rotations_deg=[0], allowed_sides=['front'])
    context = geometry.context()
    context['footprint_anchors_nm'][OTHER] = [30000000, 30000000]
    return dict(schema=2, fixed_context_policy=c.FIXED_CONTEXT_POLICY,
        board=dict(kind='rectangle', bounds_mm=[0, 0, 40, 40], cutouts=[]),
        components=[component(geometry.TEXT, [10, 10]), component(geometry.CIRCLE, [20, 10]),
                    component(OTHER, [30, 30])],
        selected=[geometry.TEXT], fixed_components=[geometry.CIRCLE, OTHER],
        groups=[], tracks=[], keepouts=[], clearance_mm=0, annotation_context=context)


def moved(source, x=9.9, y=10):
    alternative = c.original_alternative(source)
    next(row for row in alternative['transforms'] if row['component_id'] == geometry.TEXT).update(x_mm=x, y_mm=y)
    return alternative


class PreparedAnnotationTests(unittest.TestCase):
    def test_one_validated_snapshot_reuses_only_static_context(self):
        source = facts()
        candidate = moved(source)
        before = copy.deepcopy(source)
        with patch.object(annotations, 'validate', wraps=annotations.validate) as validate, \
                patch.object(annotations, '_check_prepared_moves', wraps=annotations._check_prepared_moves) as moves, \
                patch.object(annotations, 'check_moves', side_effect=AssertionError('Public context not the prepared seam')):
            check = c._alternative_validator(source)
            self.assertEqual(validate.call_count, 1)
            for unused in range(3):
                self.assertEqual(check(candidate), candidate)
            self.assertEqual(validate.call_count, 1)
            self.assertEqual(moves.call_count, 3)
            self.assertEqual(c.validate_alternative(source, candidate), candidate)
            self.assertEqual(validate.call_count, 2)
            self.assertEqual(moves.call_count, 4)
        self.assertEqual(source, before)

    def test_cached_and_public_checks_still_refuse_ring_contact_and_outboard_silk(self):
        source = facts()
        check = c._alternative_validator(source)
        for candidate, reason in [(moved(source, 12, 12), 'annotation conflict'),
                                  (moved(source, 35.5, 10), 'silkscreen proxy exceeds')]:
            for validator in (check, lambda value: c.validate_alternative(source, value)):
                with self.subTest(reason=reason), self.assertRaisesRegex(c.Refused, reason):
                    validator(candidate)
        self.assertEqual(check(moved(source)), moved(source))

    def test_private_move_checker_keeps_owner_and_exact_move_fences(self):
        context = annotations.validate(geometry.context())
        for moves, reason in [({geometry.CIRCLE: [20000001, 10000000]}, 'captured movable'),
                              ({geometry.TEXT: [True, 10000000]}, 'integer'),
                              ({geometry.TEXT: [10000000]}, 'integer-nanometre annotation coordinates'),
                              ({'unknown': [10000000, 10000000]}, 'captured movable')]:
            with self.subTest(moves=moves), self.assertRaisesRegex(ValueError, reason):
                annotations._check_prepared_moves(context, moves)

    def test_caller_context_mutation_cannot_change_detached_snapshot_or_pass_public_final(self):
        source = facts()
        candidate = moved(source)
        check = c._alternative_validator(source)
        source['annotation_context']['rows'][0]['geometry']['holes_filled'] = False
        self.assertEqual(check(candidate), candidate)
        with self.assertRaisesRegex(c.Refused, 'Native annotation context'):
            c.validate_alternative(source, candidate)
        with self.assertRaisesRegex(ValueError, 'geometry'):
            annotations.check_moves(source['annotation_context'], {geometry.TEXT: [9900000, 10000000]})

    def test_fresh_public_move_and_final_alternative_always_validate(self):
        source = facts()
        with patch.object(annotations, 'validate', wraps=annotations.validate) as validate:
            for unused in range(2):
                annotations.check_moves(source['annotation_context'], {geometry.TEXT: [9900000, 10000000]})
            self.assertEqual(validate.call_count, 2)
            for unused in range(2):
                c.validate_alternative(source, moved(source))
            self.assertEqual(validate.call_count, 4)
        for fault in ('policy', 'role', 'geometry'):
            bad = facts()
            if fault == 'policy': bad['annotation_context']['policy'] = 'unreviewed'
            elif fault == 'role': bad['annotation_context']['movable_owners'] = []
            else: bad['annotation_context']['rows'][0]['geometry']['outer_contours_nm'][0][0][0] = True
            for validator in (lambda: c._alternative_validator(bad),
                              lambda: c.validate_alternative(bad, c.original_alternative(bad))):
                with self.subTest(fault=fault), patch.object(annotations, '_check_prepared_moves',
                        side_effect=AssertionError('Invalid context reached move seam')), self.assertRaises(c.Refused):
                    validator()

    def test_snapshot_return_is_detached_and_separate_operations_revalidate(self):
        source = facts()
        candidate = moved(source)
        with patch.object(annotations, 'validate', wraps=annotations.validate) as validate:
            first = c._alternative_validator(source)
            result = first(candidate)
            result['transforms'].clear()
            self.assertEqual(first(candidate), candidate)
            second = c._alternative_validator(source)
            self.assertIsNot(first, second)
            self.assertEqual(second(candidate), candidate)
            self.assertEqual(validate.call_count, 2)
        candidate['source_sha256'] = '0' * 64
        with self.assertRaisesRegex(c.Refused, 'source binding'):
            first(candidate)


if __name__ == '__main__':
    unittest.main()
