"""Prepared-search equivalence and final fences; small pure owned fixtures."""
import copy
import threading
import unittest
from unittest.mock import patch

from autorouter import placement_annotations as annotations
from experiments.constrained_placement_v1 import constraints as c, prototype as p
from tests.test_constrained_placement_prototype import fixture, transform


def annotated_fixture():
    source=fixture();identities={row['id']:'00000000-0000-4000-8000-%012x' % (index+1)
                                for index,row in enumerate(source['components'])}
    for row in source['components']:row['id']=identities[row['id']]
    source['selected']=[identities[name] for name in source['selected']]
    source['fixed_components']=[identities[name] for name in source['fixed_components']]
    source.update(schema=2,fixed_context_policy=c.FIXED_CONTEXT_POLICY)
    source['annotation_context']=dict(schema=1,policy=annotations.POLICY,scope=annotations.SCOPE,
        source_board_sha256='1'*64,outline_nm=[0,0,40000000,40000000],silk_clearance_nm=100000,
        footprint_anchors_nm={row['id']:[int(value*1000000) for value in row['position_mm']] for row in source['components']},
        movable_owners=list(source['selected']),rows=[
            dict(uuid='00000000-0000-4000-8000-000000000020',owner=source['selected'][0],kind='silk',bbox_nm=[-100000,-100000,100000,100000]),
            dict(uuid='00000000-0000-4000-8000-000000000021',owner=None,kind='silk',bbox_nm=[27900000,9900000,28100000,10100000])])
    return source


class SearchValidatorControls(unittest.TestCase):
    def test_prepare_digest_and_fixed_census_once_per_private_snapshot(self):
        source=fixture();original=c.original_alternative(source)
        with patch.object(c,'prepare',wraps=c.prepare) as prepare,patch.object(c,'digest',wraps=c.digest) as digest, \
                patch.object(c,'immovable',wraps=c.immovable) as fixed:
            validate=c._alternative_validator(source)
            prepared_calls=prepare.call_count;digest_calls=digest.call_count;fixed_calls=fixed.call_count
            self.assertEqual(prepared_calls,1);self.assertEqual(digest_calls,1)
            for x in (25,24,23):
                candidate=copy.deepcopy(original);transform(candidate,'selected-b')['x_mm']=x
                self.assertEqual(validate(candidate),candidate)
            self.assertEqual(prepare.call_count,prepared_calls)
            self.assertEqual(digest.call_count,digest_calls)
            self.assertEqual(fixed.call_count,fixed_calls)
            c.validate_alternative(source,original)
            self.assertEqual(prepare.call_count,prepared_calls+1)
            self.assertEqual(digest.call_count,digest_calls+1)

    def test_public_and_prepared_keep_every_pose_geometry_and_binding_refusal(self):
        source=fixture();source['components'][1]['allowed_rotations_deg']=[0]
        original=c.original_alternative(source);validate=c._alternative_validator(source)
        cases=[('outside',{'x_mm':50},'outside rectangular'),('keepout',{'x_mm':16,'y_mm':16},'keepout'),
               ('overlap',{'x_mm':34,'y_mm':28},'overlap'),('rotation',{'rotation_deg':90},'orientation'),
               ('side',{'side':'back'},'Side flips'),('unknown',{'component_id':'missing'},'unknown')]
        for name,changes,message in cases:
            candidate=copy.deepcopy(original);transform(candidate,'selected-b').update(changes)
            for check in (validate,lambda value:c.validate_alternative(source,value)):
                with self.subTest(case=name,check=check),self.assertRaisesRegex(c.Refused,message):check(candidate)
        for fault in ('binding','fixed','duplicate','missing','extra','bool','infinite'):
            candidate=copy.deepcopy(original)
            if fault=='binding':candidate['source_sha256']='0'*64
            if fault=='fixed':transform(candidate,'anchor')['x_mm']+=1
            if fault=='duplicate':candidate['transforms'][1]=copy.deepcopy(candidate['transforms'][0])
            if fault=='missing':candidate['transforms'].pop()
            if fault=='extra':candidate['transforms'][1]['approval']=True
            if fault=='bool':transform(candidate,'selected-b')['x_mm']=True
            if fault=='infinite':transform(candidate,'selected-b')['x_mm']=float('inf')
            for check in (validate,lambda value:c.validate_alternative(source,value)):
                with self.subTest(fault=fault,check=check),self.assertRaises(c.Refused):check(candidate)

    def test_snapshot_is_detached_and_public_call_revalidates_current_source(self):
        source=fixture();original=c.original_alternative(source);validate=c._alternative_validator(source)
        source['components'][1]['allowed_region_mm']=[30,0,40,40]
        self.assertEqual(validate(original),original)
        with self.assertRaisesRegex(c.Refused,'source binding'):c.validate_alternative(source,original)
        with self.assertRaisesRegex(c.Refused,'allowed region'):
            c.validate_alternative(source,c.original_alternative(source))
        detached=validate(original);detached['transforms'].clear()
        self.assertEqual(validate(original),original)
        source['unknown_permission']=True
        with self.assertRaises(c.Refused):c.validate_alternative(source,original)
        self.assertEqual(validate(original),original)

    def test_annotation_moves_fully_revalidate_context_each_time_and_still_refuse_new_conflicts(self):
        source=annotated_fixture();original=c.original_alternative(source)
        with patch.object(annotations,'validate',wraps=annotations.validate) as context_validate, \
                patch.object(annotations,'check_moves',wraps=annotations.check_moves) as moves:
            validate=c._alternative_validator(source);initial_context_calls=context_validate.call_count
            self.assertEqual(initial_context_calls,1)
            self.assertEqual(validate(original),original);self.assertEqual(validate(original),original)
            self.assertEqual(moves.call_count,2);self.assertEqual(context_validate.call_count,initial_context_calls+2)
            changed=copy.deepcopy(original);transform(changed,source['selected'][0])['x_mm']=28
            for check in (validate,lambda value:c.validate_alternative(source,value)):
                with self.assertRaisesRegex(c.Refused,'annotation conflict'):check(changed)

    def test_annotation_snapshot_does_not_follow_mutated_caller_context(self):
        source=annotated_fixture();original=c.original_alternative(source);validate=c._alternative_validator(source)
        source['annotation_context']['footprint_anchors_nm'][source['selected'][0]][0]+=1
        self.assertEqual(validate(original),original)
        with self.assertRaisesRegex(c.Refused,'source anchor differs'):c.validate_alternative(source,original)

    def test_one_factory_per_search_reused_across_alternatives_and_never_across_searches(self):
        source=fixture();created=[];actual=c._alternative_validator
        def factory(facts):
            validate=actual(facts);created.append(validate);return validate
        with patch.object(p,'_alternative_validator',side_effect=factory):
            first=p.propose(source,seed=7,steps=10,alternatives=2,seconds=2)
            self.assertEqual(len(created),1)
            second=p.propose(source,seed=7,steps=10,alternatives=2,seconds=2)
        self.assertEqual(len(created),2);self.assertIsNot(created[0],created[1])
        self.assertEqual(first['status'],'proposals_ready');self.assertEqual(first['alternatives'],second['alternatives'])
        self.assertEqual(first['counts']['attempted_moves'],20)
        self.assertEqual(first['upstream_commit'],'12bb5556fc5c1db287285425aea49a1d79dc8ffa')

    def test_public_completed_and_final_checks_survive_even_if_private_validator_is_corrupted(self):
        source=fixture()
        def outside(engine,**_):engine.board.components['selected-b'].x=50
        with patch.object(p,'_alternative_validator',return_value=lambda value:copy.deepcopy(value)), \
                patch.object(p.Annealer,'run',outside),patch.object(p,'validate_alternative',wraps=c.validate_alternative) as public:
            with self.assertRaisesRegex(c.Refused,'outside rectangular'):p.propose(source,alternatives=1,steps=1)
        self.assertGreaterEqual(public.call_count,2)
        calls=[]
        def final_fence(facts,candidate):
            calls.append(copy.deepcopy(candidate))
            if len(calls)==3:raise c.Refused('independent final fence')
            return c.validate_alternative(facts,candidate)
        def valid_move(engine,**_):engine.board.components['selected-b'].x=24
        with patch.object(p.Annealer,'run',valid_move),patch.object(p,'validate_alternative',side_effect=final_fence):
            with self.assertRaisesRegex(c.Refused,'independent final fence'):p.propose(source,alternatives=1,steps=1)
        self.assertEqual(len(calls),3)

    def test_cancellation_deadline_and_source_mutation_still_fail_closed(self):
        source=fixture();event=threading.Event();event.set()
        with patch.object(p,'_alternative_validator',wraps=c._alternative_validator) as factory:
            result=p.propose(source,cancel_event=event,steps=1,alternatives=1)
        self.assertEqual(result['status'],'cancelled');self.assertEqual(result['alternatives'],[]);factory.assert_not_called()
        event.clear();move=p._ConstrainedAnnealer._move
        def cancel_after(engine,method,*args):
            value=move(engine,method,*args);event.set();return value
        with patch.object(p._ConstrainedAnnealer,'_move',cancel_after):
            result=p.propose(source,cancel_event=event,steps=2,alternatives=1)
        self.assertEqual(result['status'],'cancelled');self.assertEqual(result['alternatives'],[])
        self.assertEqual(result['counts']['attempted_moves'],1)
        with patch.object(p.time,'monotonic',side_effect=[0.0,6.0,6.0]):
            result=p.propose(source,seconds=1,steps=1,alternatives=1)
        self.assertEqual(result['status'],'budget_exhausted');self.assertEqual(result['alternatives'],[])
        def changed(engine,**_):source['components'][1]['pads'][0]['net']='changed after intake'
        with patch.object(p.Annealer,'run',changed),self.assertRaisesRegex(c.Refused,'source facts changed'):
            p.propose(source,steps=1,alternatives=1)


if __name__=='__main__':unittest.main()
