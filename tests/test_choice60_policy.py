"""Prospective generic60/60 contracts and whole-CLI headroom; no Native."""
import ast,copy
from pathlib import Path
from types import SimpleNamespace
import unittest
from autorouter import handoff as h,preferences,strategy
from scripts import qualify_current_method as method,qualify_comparison_portfolio as portfolio
from scripts import freeze_current_comparison as frozen,report_current_comparison as report
from tests import test_completed_cli_cost as fixture

def fields():return dict(handoff_stage_policy='bounded-review60-choice60-v3',delivery_stage_seconds=dict(review=60,choice=60))

class Choice60Contracts(unittest.TestCase):
    def test_current_namespaces_and_caps_are_exact_old_execution_refuses(self):
        current=dict(fields(),kind=method.CHOICE60_KIND,improve_finalization_reserve_seconds=40)
        runtime=SimpleNamespace(STAGE_POLICY=h.STAGE_POLICY,REVIEW_SECONDS=h.REVIEW_SECONDS,CHOICE_SECONDS=h.CHOICE_SECONDS,SECONDS=h.SECONDS)
        self.assertEqual(method.method_contract(current['kind']),(method.IMPROVE_POPULATION,'qualify-current-method-005.py'))
        self.assertEqual(method.method_reserve(current),40)
        self.assertEqual(method.delivery_stage_contract(current,runtime),dict(review=60,choice=60))
        old=dict(kind=method.REVIEW60_KIND,handoff_stage_policy=method.REVIEW60_POLICY,delivery_stage_seconds=dict(review=60,choice=30))
        with self.assertRaises(ValueError):method.delivery_stage_contract(old,runtime)
        for change in (dict(kind=method.REVIEW60_KIND),dict(handoff_stage_policy=method.REVIEW60_POLICY),dict(delivery_stage_seconds=dict(review=60,choice=True)),dict(delivery_stage_seconds=dict(review=60,choice=60.)),dict(delivery_stage_seconds=dict(review=60,choice=30))):
            with self.subTest(change=change),self.assertRaises(ValueError):method.delivery_stage_contract(dict(current,**change),runtime)
        self.assertEqual(method.LIMITS,dict(routing_seconds=420,method_wall_cpu_cap_seconds=450,delivery_wall_cpu_cap_seconds=600,export_validation_seconds=120))

    def test_portfolio_and_freezer_new_family_are_exact_but_native_gate_closed(self):
        runtime=SimpleNamespace(STAGE_POLICY=h.STAGE_POLICY,REVIEW_SECONDS=60,CHOICE_SECONDS=60)
        self.assertEqual(portfolio.delivery_stage_contract(dict(fields(),kind=portfolio.CHOICE60_KIND),runtime),dict(review=60,choice=60))
        for bad in (dict(kind=portfolio.REVIEW60_KIND),dict(delivery_stage_seconds=dict(review=60,choice=30))):
            with self.subTest(bad=bad),self.assertRaises(ValueError):portfolio.delivery_stage_contract({**fields(),'kind':portfolio.CHOICE60_KIND,**bad},runtime)
        self.assertEqual(frozen.contract(frozen.CHOICE60_VERSION)[2:],(frozen.CHOICE60_POPULATION_KIND,method.CHOICE60_KIND,'qualify-current-method-005.py'))
        with self.assertRaisesRegex(ValueError,'qualification gate'):frozen.qualification_scope({},Path('/owned/runtime'),'a'*64,{}, {},frozen.CHOICE60_VERSION)
        with self.assertRaisesRegex(ValueError,'bindings remain pending'):frozen.choice60_qualification_summary(fields(),'a'*40,'/owned/runtime','b'*64)

    def test_new_enclosure_refuses_mixed_historical_policy_and_changed600(self):
        root=ast.parse(Path(frozen.ROOT/'scripts/enclose_current_comparison.py').read_text())
        nodes=[node for node in root.body if isinstance(node,ast.FunctionDef) and node.name in ('ordinary_method_contract','review60_contract','choice60_contract')]
        scope={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'enclosure-contract-only','exec'),scope)
        plan=dict(fields(),kind=method.CHOICE60_KIND,arm='Cimprove',limits=dict(frozen.LIMITS),whole_wall_full_cpu_seconds=600,pass_key='controls_passed')
        child=Path('/owned/qualify-current-method-005.py');self.assertTrue(scope['ordinary_method_contract'](plan,child,False))
        for change in (dict(handoff_stage_policy=method.REVIEW60_POLICY),dict(delivery_stage_seconds=dict(review=60,choice=30)),dict(whole_wall_full_cpu_seconds=600.),dict(limits=dict(frozen.LIMITS,delivery_wall_cpu_cap_seconds=601))):
            self.assertFalse(scope['choice60_contract'](dict(plan,**change),child,False))
        self.assertFalse(scope['ordinary_method_contract'](plan,Path('/owned/qualify-current-method-004.py'),False))

    def test_preset_scope_refusal_is_owner_facing_and_never_changes_requirements(self):
        settings=dict(preferences.DEFAULTS,scope='partial_completion');before=copy.deepcopy(settings)
        with self.assertRaisesRegex(h.Rejected,'Improve requires whole-board.*Use Route'):
            strategy.pruning_scope(settings)
        self.assertEqual(settings,before)

class BothCompletedCliHeadroom(unittest.TestCase):
    refresh_bound_records=fixture.CompletedCliReportingControls.refresh_bound_records
    facts=fixture.CompletedCliReportingControls.facts
    def setUp(self):
        fixture.CompletedCliReportingControls.setUp(self)
        self.plan.update(fields(),kind=method.CHOICE60_KIND);self.data.update(fields(),kind=method.CHOICE60_KIND)
        for name in ('review','choice'):
            self.bound_records[name].update(handoff_stage_policy=h.STAGE_POLICY,budget_seconds=60,cpu_budget_seconds=60)
        self.refresh_bound_records()
        self.choice=next(row for row in self.data['processes'] if row['stage']=='choice')['completed_cli_exit']
        self.choice.update(wall_seconds=35.,full_CPU_seconds=34.)

    def test_each_review_and_choice_completed_clock_must_have45second_margin(self):
        actual=self.facts();self.assertTrue(actual['complete_review_and_choice_cli_headroom_qualified'])
        self.assertEqual(actual['choice_stage_headroom_seconds'],dict(wall=25.,CPU=26.))
        for sample in (self.review,self.choice):
            for key in ('wall_seconds','full_CPU_seconds'):
                old=sample[key];sample[key]=45.001
                self.assertFalse(self.facts()['complete_review_and_choice_cli_headroom_qualified']);sample[key]=old

    def test_current_choice_samples_and_both_receipt_policies_remain_bound(self):
        self.choice.update(wall_seconds=2.,full_CPU_seconds=2.)
        self.bound_records['choice'].update(wall_seconds=55.,total_cpu_seconds=55.)
        self.refresh_bound_records()
        with self.assertRaisesRegex(ValueError,'omits bound choice'):self.facts()
        self.bound_records['choice'].update(wall_seconds=1.,total_cpu_seconds=1.,handoff_stage_policy=method.REVIEW60_POLICY,budget_seconds=30,cpu_budget_seconds=30)
        self.refresh_bound_records()
        with self.assertRaisesRegex(h.Rejected,'fixed stage budget/policy'):self.facts()
