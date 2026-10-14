"""Completed-prefix controls reuse the existing continuation fixture/validator."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch
from tests.test_portfolio_resume import ResumeControls
from scripts import experiment_portfolio as m
from autorouter import pipeline as p, floor_route as f


class CompletedResumeControls(ResumeControls):
    def setUp(self):
        super().setUp()
        self.old_budget=74.3810895409988
        data=json.loads((self.old/'01-via_default/result.json').read_text())
        engine=p.engine_profile_settings('tuned',55.,scoring_variant='via_default')
        engine.update(outer_task_wall_budget_seconds=55.,outer_task_cpu_budget_seconds=55.)
        data.update(engine_budget=engine,budget_seconds=55.,cpu_budget_seconds=55.)
        data['steps'][0]['argv']=['java',*engine['argv']]
        p.save_json(self.old/'01-via_default/engine-process.json',data['steps'][0])
        p.save_json(self.old/'01-via_default/result.json',data)
        old=json.loads((self.old/'portfolio-summary.json').read_text());row=old['trials'][0]
        row.update(eligible=True,assigned_seconds=55.,result_sha256=p.sha(self.old/'01-via_default/result.json'))
        old.update(status='completed',comparison_eligible=True,selected=copy.deepcopy(row),
            stop_reason='insufficient remaining budget for another attempt and reserves',
            pareto_frontier=['via_default'],wall_budget_seconds=self.old_budget,cpu_budget_seconds=self.old_budget,
            wall_seconds=20.,total_cpu_seconds=18.)
        old.pop('reason')
        protocol=json.loads((self.old/'protocol.json').read_text())
        protocol.update(wall_budget_seconds=self.old_budget,cpu_budget_seconds=self.old_budget)
        p.save_json(self.old/'protocol.json',protocol);old['protocol_sha256']=p.sha(self.old/'protocol.json')
        p.save_json(self.old/'portfolio-summary.json',old)
        invoice=json.loads((self.base/'B2_portfolio-invocation.json').read_text())
        invoice.update(assigned_seconds=self.old_budget,result_sha256=p.sha(self.old/'portfolio-summary.json'),
            invocation_wall_seconds=21.,invocation_cpu_seconds=19.)
        p.save_json(self.base/'B2_portfolio-invocation.json',invoice)
        p.save_json(self.base/'paired-summary.json',{'results':[invoice]})
        p.save_json(self.base/'protocol.json',{'inner_allowance_seconds':self.old_budget,'freeze':self.oldf,
            'wall_budget_per_arm_seconds':120.,'cpu_budget_per_arm_seconds':120.})
        self.plan.update(schema=2,policy=m.COMPLETED_PREFIX_POLICY,project='arcdice',budget_seconds=100.,
            old_budget_seconds=self.old_budget,new_budget_seconds=100.,outer_arm_budget_seconds=120.,
            full_arm_charge_required=True,prior_invocation_wall_seconds=21.,prior_invocation_cpu_seconds=19.)
        self.repin();self.wall=self.cpu=0.;self.calls=[]

    def repin(self):
        for name in self.plan['artifacts']:self.plan['artifacts'][name]=p.sha(name)
        self.plan['retained_inventory_sha256']=hashlib.sha256(f.canonical(m.pc.inventory(self.old,with_directories=True)).encode()).hexdigest()
        self.planpin=self.save_plan()

    def resumed(self,**kwargs):
        return m.experiment(self.out,'arcdice',budget=100.,resume_plan=self.planpath,resume_plan_sha256=self.planpin,**kwargs)

    def test_only_unattempted_variants_and_full_prior_cost(self):
        before=m.pc.inventory(self.old,with_directories=True)
        result=self.resumed()
        self.assertEqual(self.calls,[('via_low',64.),('via_high',54.)])
        self.assertTrue(result['comparison_eligible']);self.assertEqual(len(result['trials']),3)
        self.assertEqual((result['wall_seconds'],result['total_cpu_seconds']),(41.,43.))
        self.assertEqual(result['completed_prefix_allocation']['outer_arm_budget_seconds'],120.)
        self.assertTrue(result['completed_prefix_allocation']['full_arm_charge_required'])
        self.assertEqual(m.pc.inventory(self.old,with_directories=True),before)
        protocol=json.loads((self.out/'protocol.json').read_text())
        self.assertEqual(m.trial_freeze(protocol,result['trials'][0]),self.oldf)

    def test_undercharging_prior_invoice_is_rejected(self):
        self.plan['prior_invocation_wall_seconds']=20.;self.planpin=self.save_plan()
        result=self.resumed();self.assertFalse(result['comparison_eligible']);self.assertEqual(self.calls,[])
        self.assertIn('complete measured',result['reason'])

    def test_bad_allocations_or_missing_outer_accounting_reject(self):
        for key,value in [('old_budget_seconds',True),('old_budget_seconds',100.),
                          ('new_budget_seconds',90.),('outer_arm_budget_seconds',100.),
                          ('full_arm_charge_required',False)]:
            with self.subTest(key=key),patch.dict(self.plan,{key:value}):
                self.planpin=self.save_plan()
                with self.assertRaises(p.Rejected):m.resume_basis(self.planpath,self.planpin,self.board,self.frozen,100.,'arcdice',None)
        with self.assertRaises(p.Rejected):m.resume_basis(self.planpath,self.planpin,self.board,self.frozen,100.,'sonde',None)

    def test_repinning_failed_or_nondefault_prefix_cannot_authorize_resume(self):
        original=json.loads((self.old/'portfolio-summary.json').read_text())
        for change in ({'comparison_eligible':False},{'selected':None},{'stop_reason':'unknown'},{'status':'cancelled'}):
            with self.subTest(change=change):
                old=copy.deepcopy(original);old.update(change);p.save_json(self.old/'portfolio-summary.json',old)
                invoice=json.loads((self.base/'B2_portfolio-invocation.json').read_text());invoice['result_sha256']=p.sha(self.old/'portfolio-summary.json')
                p.save_json(self.base/'B2_portfolio-invocation.json',invoice);p.save_json(self.base/'paired-summary.json',{'results':[invoice]});self.repin()
                with self.assertRaises(p.Rejected):m.resume_basis(self.planpath,self.planpin,self.board,self.frozen,100.,'arcdice',None)

    def test_any_unpinned_extra_inventory_rejects(self):
        (self.old/'unreferenced').write_text('changed')
        result=self.resumed();self.assertFalse(result['comparison_eligible']);self.assertEqual(self.calls,[])

    def test_source_or_core_changes_remain_blocking(self):
        self.frozen['source_hashes']['changed']='changed'
        result=self.resumed();self.assertFalse(result['comparison_eligible']);self.assertEqual(self.calls,[])
        self.assertIn('core',result['reason'])


def load_tests(loader,tests,pattern):
    return unittest.TestSuite(CompletedResumeControls(name) for name in CompletedResumeControls.__dict__ if name.startswith('test_'))


if __name__=='__main__':unittest.main()
