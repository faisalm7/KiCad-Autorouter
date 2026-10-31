"""Prospective administrative policy controls; no Native/process execution."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from scripts import freeze_current_comparison as frozen, qualify_current_method as method
from scripts import qualify_comparison_portfolio as portfolio, report_current_comparison as report


def fields():return dict(handoff_stage_policy='bounded-review60-choice30-v2',delivery_stage_seconds=dict(review=60,choice=30))
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return hashlib.sha256(path.read_bytes()).hexdigest()


class Review60AdministrativeContracts(unittest.TestCase):
    def setUp(self):
        path=Path(frozen.__file__).with_name('enclose_current_comparison.py')
        nodes=[node for node in ast.parse(path.read_text()).body if isinstance(node,ast.FunctionDef)
            and node.name in ('ordinary_method_contract','review60_contract')]
        scope={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'::inert-functions','exec'),scope)
        self.enclosed=scope['review60_contract'];self.ordinary=scope['ordinary_method_contract']
        self.runtime=SimpleNamespace(STAGE_POLICY='bounded-review60-choice30-v2',REVIEW_SECONDS=60,CHOICE_SECONDS=30,SECONDS=30)
        self.plan=dict(fields(),kind=method.REVIEW60_KIND,arm='Cimprove',limits=dict(frozen.LIMITS),
            whole_wall_full_cpu_seconds=600,pass_key='controls_passed')

    def test_new_child_kind_and_namespace_do_not_admit_other_methods_or_changed_budgets(self):
        child=Path('qualify-current-method-004.py')
        self.assertTrue(self.enclosed(self.plan,child,False));self.assertTrue(self.ordinary(self.plan,child,False))
        for key,value in (('routing_seconds',421),('delivery_wall_cpu_cap_seconds',900),('export_validation_seconds',121)):
            plan=copy.deepcopy(self.plan);plan['limits'][key]=value
            self.assertFalse(self.enclosed(plan,child,False))
        for change in (dict(arm='Cthermal'),dict(kind=method.CURRENT40_KIND),dict(handoff_stage_policy=None),
                dict(delivery_stage_seconds=dict(review=60.,choice=30)),dict(whole_wall_full_cpu_seconds=600.)):
            self.assertFalse(self.enclosed(dict(self.plan,**change),child,False))
        self.assertFalse(self.enclosed(self.plan,Path('qualify-current-method-003.py'),False))
        self.assertFalse(self.enclosed(self.plan,child,True))
        stock=dict(self.plan,arm='B0');self.assertTrue(self.enclosed(stock,child,False));self.assertFalse(self.ordinary(stock,child,False))

    def test_portfolio_uses_same_new_stages_without_changing_restart_or_complete_caps(self):
        plan=dict(fields(),kind=portfolio.REVIEW60_KIND,whole_wall_full_cpu_seconds=600,pass_key='controls_passed',**frozen.LIMITS)
        self.assertTrue(self.enclosed(plan,Path('qualify_comparison_portfolio.py'),True))
        self.assertEqual(portfolio.delivery_stage_contract(plan,self.runtime),dict(review=60,choice=30))
        for change in (dict(kind=portfolio.KIND),dict(delivery_stage_seconds=dict(review=30,choice=30)),dict(handoff_stage_policy=None)):
            with self.subTest(change=change),self.assertRaises(ValueError):portfolio.delivery_stage_contract(dict(plan,**change),self.runtime)
        self.assertEqual(portfolio.LIMITS,dict(frozen.LIMITS,allocation='balanced',trial_readback_reserve_seconds=30,root_finalization_reserve_seconds=15))

    def test_old_enclosure_namespace_stays_old_and_cannot_mix_new_stage_fields(self):
        plan=dict(kind=method.CURRENT40_KIND,arm='Cimprove')
        self.assertTrue(self.ordinary(plan,Path('qualify-current-method-003.py'),False))
        self.assertTrue(self.enclosed(plan,Path('qualify-current-method-003.py'),False))
        self.assertFalse(self.enclosed(dict(plan,**fields()),Path('qualify-current-method-003.py'),False))

    def test_new_freezer_contract_is_explicit_but_unobserved_native_gate_remains_closed(self):
        values=frozen.contract(frozen.REVIEW60_VERSION)
        self.assertEqual(values[2:],(frozen.REVIEW60_POPULATION_KIND,method.REVIEW60_KIND,'qualify-current-method-004.py'))
        with self.assertRaisesRegex(ValueError,'not yet qualified'):
            frozen.qualification_scope({},Path('/owned/runtime'),'a'*64,{}, {},frozen.REVIEW60_VERSION)
        with self.assertRaisesRegex(ValueError,'pending'):
            frozen.review60_qualification_summary(dict(fields()),'a'*40,'/owned/runtime','b'*64)
        self.assertEqual(frozen.contract(frozen.CURRENT40_VERSION)[3:],(method.CURRENT40_KIND,'qualify-current-method-003.py'))

    def test_reporter_stage_fields_reject_old_or_float_allocation(self):
        self.assertEqual(frozen.review60_stage_fields(fields()),dict(review=60,choice=30))
        for change in (dict(handoff_stage_policy=None),dict(delivery_stage_seconds=dict(review=30,choice=30)),
                dict(delivery_stage_seconds=dict(review=60,choice=True)),dict(delivery_stage_seconds=dict(review=60.,choice=30))):
            with self.subTest(change=change),self.assertRaises(ValueError):frozen.review60_stage_fields(dict(fields(),**change))

    def test_stored_stage_facts_cannot_promote_sample_margin_to_complete_headroom(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();route=root/'route/result.json';route_pin=write(route,dict(owned=True))
            review_path=root/'review/review.json';choice_path=root/'choice/choice.json';export_path=root/'export/export.json'
            def stage(seconds):return dict(handoff_stage_policy='bounded-review60-choice30-v2',budget_seconds=seconds,cpu_budget_seconds=seconds,
                wall_seconds=35. if seconds==60 else 10.,total_cpu_seconds=30. if seconds==60 else 9.,within_budget=True)
            review=dict(stage(60),status='ready_for_manual_review',receipt=str(route),receipt_sha256=route_pin);review_pin=write(review_path,review)
            choice=dict(stage(30),status='disposition_recorded',choice='accept',choice_recorded=True,receipt=str(route),receipt_sha256=route_pin,review=str(review_path),review_sha256=review_pin);choice_pin=write(choice_path,choice)
            exported=dict(inputs=dict(receipt=str(route),receipt_sha256=route_pin,review=str(review_path),review_sha256=review_pin,
                choice=str(choice_path),choice_sha256=choice_pin));write(export_path,exported)
            data=dict(selected_route_receipt=str(route),export_receipt=str(export_path))
            result=report.delivery_stage_facts(fields(),data,[root])
            self.assertFalse(result['complete_stage_headroom_qualified'])
            with self.assertRaisesRegex(ValueError,'escaped frozen arm'):
                report.delivery_stage_facts(fields(),data,[root/'unrelated-owned-arm'])
            # Even a completely rebound legacy review remains the wrong policy.
            review.update(budget_seconds=30,cpu_budget_seconds=30,wall_seconds=1.,total_cpu_seconds=1.)
            review_pin=write(review_path,review);choice['review_sha256']=review_pin;choice_pin=write(choice_path,choice)
            exported['inputs'].update(review_sha256=review_pin,choice_sha256=choice_pin);write(export_path,exported)
            with self.assertRaisesRegex(ValueError,'historical review60/choice30 fixed stage budget/policy'):report.delivery_stage_facts(fields(),data,[root])
