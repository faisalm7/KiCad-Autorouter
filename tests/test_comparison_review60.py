"""Constructed prospective budget contract controls; no Native or routing."""
import copy
from types import SimpleNamespace
import unittest
from scripts import qualify_current_method as q


class Review60MethodContractControls(unittest.TestCase):
    def setUp(self):
        self.plan=dict(kind=q.REVIEW60_KIND,handoff_stage_policy=q.REVIEW60_POLICY,
            delivery_stage_seconds=dict(review=60,choice=30),improve_finalization_reserve_seconds=40)
        self.runtime=SimpleNamespace(STAGE_POLICY=q.REVIEW60_POLICY,REVIEW_SECONDS=60,CHOICE_SECONDS=30,SECONDS=30)

    def test_new_protocol_preserves_total_routing_method_export_limits_and_separate_stages(self):
        self.assertEqual(q.LIMITS,dict(routing_seconds=420,method_wall_cpu_cap_seconds=450,
            delivery_wall_cpu_cap_seconds=600,export_validation_seconds=120))
        self.assertEqual(q.method_contract(q.REVIEW60_KIND),(q.IMPROVE_POPULATION,'qualify-current-method-004.py'))
        self.assertEqual(q.method_reserve(self.plan),40)
        self.assertEqual(q.delivery_stage_contract(self.plan,self.runtime),dict(review=60,choice=30))

    def test_policy_missing_old_or_receipt_selected_allocations_refuse(self):
        changes=[dict(handoff_stage_policy=None),dict(handoff_stage_policy='old'),
            dict(delivery_stage_seconds=dict(review=30,choice=30)),
            dict(delivery_stage_seconds=dict(review=60.,choice=30)),
            dict(delivery_stage_seconds=dict(review=60,choice=60)),
            dict(delivery_stage_seconds=dict(review=60,choice=30,export=120))]
        for change in changes:
            with self.subTest(change=change),self.assertRaises(ValueError):
                q.delivery_stage_contract(dict(self.plan,**change),self.runtime)
        for kind in (q.KIND,q.IMPROVE_KIND,q.CURRENT40_KIND):
            with self.subTest(kind=kind),self.assertRaises(ValueError):q.delivery_stage_contract(dict(kind=kind),self.runtime)

    def test_changed_runtime_stage_caps_cannot_be_authorized_by_matching_receipt(self):
        for field,value in (('REVIEW_SECONDS',90),('CHOICE_SECONDS',60),('REVIEW_SECONDS',60.0),('STAGE_POLICY','changed')):
            runtime=copy.copy(self.runtime);setattr(runtime,field,value)
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):q.delivery_stage_contract(self.plan,runtime)
