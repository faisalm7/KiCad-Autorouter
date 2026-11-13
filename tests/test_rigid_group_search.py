"""Rigid proxy-search controls; no Native placement or routing qualification."""
import copy
from decimal import Decimal
import threading
import unittest
from unittest.mock import patch

from experiments.constrained_placement_v1 import constraints as c, prototype as p
from tests.test_constrained_placement_prototype import fixture, transform
from tests.test_placement_search_validator import annotated_fixture


def grouped():
    value = fixture()
    value['groups'] = [dict(policy=c.RIGID_TRANSLATION_POLICY, members=list(value['selected']))]
    return value


def shifted(source, dx, dy):
    value = c.original_alternative(source)
    for row in value['transforms']:
        if row['component_id'] in source['selected']:
            row['x_mm'] += dx; row['y_mm'] += dy
    return value


def engine(source):
    facts = c.prepare(source); counts = dict(attempted_moves=0, constraint_rejected_moves=0)
    model = p._model(facts)
    return p._ConstrainedAnnealer(model, facts, 7, lambda: None, counts), counts


def poses(value):
    return {key:(row.x,row.y,row.rot) for key,row in value.board.components.items()}


class RigidGroupSearchControls(unittest.TestCase):
    def test_valid_group_translation_and_original_angle_side_are_independent_constraints(self):
        source = grouped(); source['components'][2]['rotation_deg'] = 90
        before = copy.deepcopy(source); candidate = shifted(source,-1,0)
        self.assertEqual(c.validate_alternative(source,candidate),candidate)
        for key,value,message in [('rotation_deg',180,'orientation changed'),('side','back','Side flips')]:
            wrong = copy.deepcopy(candidate); transform(wrong,'selected-c')[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(c.Refused,message): c.validate_alternative(source,wrong)
        self.assertEqual(source,before)

    def test_one_nm_shear_refuses_in_fresh_and_prepared_validators(self):
        source = grouped(); candidate = shifted(source,-1,0)
        transform(candidate,'selected-c')['x_mm'] += .000001
        for validate in (c._alternative_validator(source),lambda row:c.validate_alternative(source,row)):
            with self.assertRaisesRegex(c.Refused,'relative position'): validate(candidate)

    def test_proxy_arithmetic_tolerance_is_smaller_than_two_micro_nm(self):
        source = grouped(); candidate = shifted(source,-1,0)
        transform(candidate,'selected-c')['x_mm'] += .000000000002
        self.assertLessEqual(c.RIGID_PROXY_TOLERANCE_NM,Decimal('0.000001'))
        with self.assertRaisesRegex(c.Refused,'relative position'): c.validate_alternative(source,candidate)

    def test_exact_policy_order_population_and_fixed_membership_are_mandatory(self):
        for mode in ('unknown_policy','extra_field','partial','unknown','duplicate','reordered',
                     'two_groups','locked','fixed','tracked','too_many','not_list'):
            source = grouped(); group = source['groups'][0]
            if mode == 'unknown_policy': group['policy'] = 'soft-cohesion'
            elif mode == 'extra_field': group['rotate'] = True
            elif mode == 'partial': group['members'] = group['members'][:1]
            elif mode == 'unknown': group['members'][1] = 'missing'
            elif mode == 'duplicate': group['members'][1] = group['members'][0]
            elif mode == 'reordered': group['members'].reverse()
            elif mode == 'two_groups': source['groups'].append(copy.deepcopy(group))
            elif mode == 'locked': source['components'][1]['locked'] = True
            elif mode == 'fixed': source['fixed_components'].append('selected-b')
            elif mode == 'tracked': source['tracks'] = [dict(id='kept',net='signal',pad_ids=['selected-b/A7'])]
            elif mode == 'too_many': group['members'] = ['part'+str(i) for i in range(17)]
            else: source['groups'] = ()
            with self.subTest(mode=mode), self.assertRaises(c.Refused): c.prepare(source)

    def test_grouped_geometry_keepouts_regions_and_fixed_collisions_are_not_waived(self):
        source = grouped()
        for delta,message in [((-9,6),'keepout'),((20,0),'outside rectangular'),((-21,-6),'overlap')]:
            with self.subTest(delta=delta),self.assertRaisesRegex(c.Refused,message):
                c.validate_alternative(source,shifted(source,*delta))
        source['components'][1]['allowed_region_mm'] = [24,8,27,12]
        with self.assertRaisesRegex(c.Refused,'allowed region'): c.validate_alternative(source,shifted(source,-2,0))

    def test_grouped_annotation_checks_are_not_waived(self):
        source = annotated_fixture()
        source['groups'] = [dict(policy=c.RIGID_TRANSLATION_POLICY,members=list(source['selected']))]
        with self.assertRaisesRegex(c.Refused,'Native annotation prefilter'):
            c.validate_alternative(source,shifted(source,3,0))

    def test_atomic_nudge_costs_whole_group_and_uses_one_integer_offset_without_clamping(self):
        source = grouped(); source['components'][1]['position_mm'] = [25.0000005,10.0000005]
        source['components'][2]['position_mm'] = [34.0000015,28.0000015]
        value,counts = engine(source); before = poses(value)
        with patch.object(value.rng,'random',side_effect=[.6,.4]), \
                patch.object(value,'local_cost',side_effect=[10,5]) as cost, \
                patch.object(value,'_clamp',side_effect=AssertionError('individual clamp forbidden')), \
                patch.object(p.Annealer,'_try_nudge',side_effect=AssertionError('individual nudge forbidden')):
            self.assertEqual(value._try_nudge(1),-5)
        self.assertEqual([[row.ref for row in call.args[0]] for call in cost.call_args_list],
                         [source['selected'],source['selected']])
        deltas = []
        for identity in source['selected']:
            deltas.append([(Decimal(str(a))-Decimal(str(b)))*1000000
                           for a,b in zip(poses(value)[identity][:2],before[identity][:2])])
        for delta in deltas:
            self.assertTrue(all(abs(a-b)<=c.RIGID_PROXY_TOLERANCE_NM for a,b in zip(delta,[200000,-200000])))
        self.assertEqual(poses(value)['anchor'],before['anchor'])
        self.assertEqual(counts,dict(attempted_moves=1,constraint_rejected_moves=0))
        c.validate_alternative(source,p._candidate(c.prepare(source),value.board))

    def test_objective_rejection_rolls_back_all_members_exactly(self):
        value,counts = engine(grouped()); before = poses(value)
        with patch.object(value.rng,'random',side_effect=[.6,.4]),patch.object(value,'local_cost',side_effect=[0,10]):
            self.assertIsNone(value._try_nudge(0))
        self.assertEqual(poses(value),before)
        self.assertEqual(counts['constraint_rejected_moves'],0)

    def test_infeasible_atomic_nudge_rolls_back_the_complete_pose(self):
        value,counts = engine(grouped()); before = poses(value)
        with patch.object(value.rng,'random',side_effect=[.99,.99]),patch.object(value,'local_cost',side_effect=[10,5]):
            self.assertIsNone(value._try_nudge(20))
        self.assertEqual(poses(value),before)
        self.assertEqual(counts,dict(attempted_moves=1,constraint_rejected_moves=1))

    def test_grouped_rotation_and_independent_swap_are_disabled(self):
        value,counts = engine(grouped()); before = poses(value)
        with patch.object(p.Annealer,'_try_rotate',side_effect=AssertionError('group rotation forbidden')), \
                patch.object(p.Annealer,'_try_swap',side_effect=AssertionError('member swap forbidden')):
            self.assertIsNone(value._try_rotate(1)); self.assertIsNone(value._try_swap())
        self.assertEqual(poses(value),before); self.assertEqual(counts['attempted_moves'],0)

    def test_old_empty_group_path_and_context_fact_schema_remain_unchanged(self):
        source = fixture(); self.assertEqual(c.prepare(source),source); value,counts = engine(source)
        with patch.object(p.Annealer,'_try_nudge',return_value=None) as nudge, \
                patch.object(p.Annealer,'_try_rotate',return_value=None) as rotate, \
                patch.object(p.Annealer,'_try_swap',return_value=None) as swap:
            value._try_nudge(1); value._try_rotate(1); value._try_swap()
        nudge.assert_called_once_with(1); rotate.assert_called_once_with(1); swap.assert_called_once_with()
        self.assertEqual(counts['attempted_moves'],3)
        context = grouped(); context.update(schema=2,fixed_context_policy=c.FIXED_CONTEXT_POLICY)
        self.assertEqual(c.validate_alternative(context,c.original_alternative(context)),c.original_alternative(context))

    def test_real_group_search_returns_changed_bound_alternatives_and_preserves_source(self):
        source = grouped(); before = copy.deepcopy(source)
        result = p.propose(source,seed=7,steps=160,alternatives=2,seconds=2)
        self.assertEqual(result['status'],'proposals_ready'); self.assertTrue(result['alternatives'])
        for row in result['alternatives']:
            c.validate_alternative(source,row['candidate'])
            self.assertLess(row['after_proxy_cost'],row['before_proxy_cost'])
        self.assertEqual(source,before)
        self.assertTrue(result['source_unchanged']); self.assertFalse(result['execution_authorized'])
        self.assertFalse(result['native_validation_performed'])

    def test_cancellation_during_group_move_discards_results_and_rolls_back(self):
        source = grouped(); before = copy.deepcopy(source); event = threading.Event(); event.set()
        result = p.propose(source,steps=1,alternatives=1,cancel_event=event)
        self.assertEqual(result['status'],'cancelled'); self.assertEqual(result['alternatives'],[])
        event.clear(); actual = p._ConstrainedAnnealer._nudge_rigid_group; captured = []
        def cancelled(value,temperature):
            captured.append((value,poses(value)))
            result = actual(value,temperature); event.set(); return result
        with patch.object(p._ConstrainedAnnealer,'_nudge_rigid_group',cancelled):
            result = p.propose(source,seed=7,steps=2,alternatives=1,cancel_event=event)
        self.assertEqual(result['status'],'cancelled'); self.assertEqual(result['alternatives'],[])
        self.assertTrue(captured); self.assertEqual(poses(captured[0][0]),captured[0][1])
        self.assertEqual(source,before)

    def test_independent_final_validation_rejects_shear_even_with_corrupt_private_validator(self):
        source = grouped()
        def shear(value,**_): value.board.components['selected-b'].x += .000001
        with patch.object(p,'_alternative_validator',return_value=lambda value:copy.deepcopy(value)), \
                patch.object(p.Annealer,'run',shear):
            with self.assertRaisesRegex(c.Refused,'relative position'): p.propose(source,steps=1,alternatives=1)

    def test_mutated_caller_group_binding_and_deadline_cannot_return_a_candidate(self):
        source = grouped()
        def changed(_engine,**_): source['groups'][0]['members'].reverse()
        with patch.object(p.Annealer,'run',changed):
            with self.assertRaisesRegex(c.Refused,'source facts changed'): p.propose(source,steps=1,alternatives=1)
        source = grouped()
        with patch.object(p.time,'monotonic',side_effect=[0.0,6.0,6.0]):
            result = p.propose(source,seconds=1,steps=1,alternatives=1)
        self.assertEqual(result['status'],'budget_exhausted'); self.assertEqual(result['alternatives'],[])


if __name__ == '__main__': unittest.main()
