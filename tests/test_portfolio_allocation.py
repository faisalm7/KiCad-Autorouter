"""Budget/allocation falsifiers; mocked trial flow is not native evidence."""
import json
import unittest
from unittest.mock import patch
from autorouter import pipeline as p
from scripts import experiment_portfolio as m
from tests import test_portfolio as harness
from tests import test_portfolio_completed_resume as completed_harness


class PortfolioAllocation(unittest.TestCase):
    # Reuse the existing pure control harness without inheriting its test cases.
    setUp=harness.PortfolioControls.setUp
    route=harness.PortfolioControls.route
    checked=harness.PortfolioControls.checked

    def test_legacy_default_budget_and_remaining_policy_are_preserved(self):
        result=m.experiment(self.out)
        protocol=json.loads((self.out/'protocol.json').read_text())
        self.assertEqual(self.calls,[('via_default',105.),('via_low',80.),('via_high',55.)])
        self.assertEqual(result['wall_budget_seconds'],120.)
        self.assertEqual(protocol['allocation'],'remaining')
        self.assertEqual(result['allocation'],'remaining')
        self.assertEqual(result['attempted_variants'],list(m.VARIANTS))
        self.assertTrue(result['all_variants_attempted'])

    def test_balanced_allocation_charges_cpu_and_reuses_only_unspent_allowance(self):
        self.costs=[(18.,40.)]*3
        result=m.experiment(self.out,budget=300,allocation='balanced',outer_ceiling=360)
        self.assertEqual(self.calls,[('via_default',95.),('via_low',122.5),('via_high',205.)])
        self.assertEqual(result['total_cpu_seconds'],120.)
        self.assertEqual(result['wall_seconds'],54.)
        self.assertTrue(result['comparison_eligible'])
        self.assertTrue(result['all_variants_attempted'])
        protocol=json.loads((self.out/'protocol.json').read_text())
        self.assertEqual(protocol['allocation'],'balanced')
        self.assertEqual(protocol['operational_outer_ceiling_seconds'],360)
        self.assertEqual([row['unattempted_variants_at_assignment'] for row in result['trials']],[3,2,1])
        self.assertEqual([row['remaining_wall_full_cpu_seconds_at_assignment'] for row in result['trials']],[300.,260.,220.])
        self.assertEqual(result['selected']['id'],'via_high')

    def test_wall_can_limit_balanced_allocation_independently_of_cpu(self):
        self.costs=[(70.,20.)]*3
        result=m.experiment(self.out,budget=300,allocation='balanced')
        self.assertEqual(self.calls,[('via_default',95.),('via_low',107.5),('via_high',145.)])
        self.assertEqual(result['wall_seconds'],210.)
        self.assertEqual(result['total_cpu_seconds'],60.)

    def test_failed_first_attempt_retains_costs_and_does_not_stop_complementary_variants(self):
        route=self.route
        def failed(*args,**kwargs):
            result=route(*args,**kwargs)
            if len(self.calls)==1:
                result.update(status='drc_rejected',accepted=False,native={'opens':1,'blocking':0,'exclusions':0})
                p.save_json(args[1]/'result.json',result)
            return result
        with patch.object(p,'route',side_effect=failed):
            result=m.experiment(self.out,budget=260,allocation='balanced')
        self.assertEqual(len(self.calls),3)
        self.assertFalse(result['trials'][0]['eligible'])
        self.assertEqual(result['trials'][0]['status'],'drc_rejected')
        self.assertEqual(result['total_cpu_seconds'],75.)
        self.assertEqual(result['wall_seconds'],54.)
        self.assertTrue(result['all_variants_attempted'])

    def test_meaningless_budget_skips_every_variant_with_explicit_reserve_reason(self):
        result=m.experiment(self.out,allocation='balanced')
        self.assertEqual(self.calls,[])
        self.assertEqual(result['status'],'no_valid_candidate')
        self.assertFalse(result['comparison_eligible'])
        self.assertFalse(result['all_variants_attempted'])
        self.assertEqual(result['unattempted_variants'],list(m.VARIANTS))
        self.assertEqual([row['id'] for row in result['skipped_variants']],list(m.VARIANTS))
        self.assertTrue(all('reserves' in row['reason'] for row in result['skipped_variants']))
        self.assertEqual(result['skipped_variants'][0]['assigned_if_started_seconds'],35.)

    def test_cpu_overshoot_retains_whole_failed_cost_and_skipped_coverage(self):
        self.costs=[(18.,300.)]
        result=m.experiment(self.out,budget=240,allocation='balanced')
        self.assertEqual(result['status'],'budget_exceeded')
        self.assertFalse(result['comparison_eligible']);self.assertIsNone(result['selected'])
        self.assertEqual(result['total_cpu_seconds'],300.)
        self.assertEqual(len(result['trials']),1)
        self.assertEqual(result['unattempted_variants'],['via_low','via_high'])
        self.assertTrue(all('reserve' in row['reason'] for row in result['skipped_variants']))

    def test_explicit_operational900_allows_bound_trial_above120_without_changing_default(self):
        result=m.experiment(self.out,budget=900,allocation='balanced',outer_ceiling=900)
        self.assertEqual(self.calls[0][1],295.)
        self.assertTrue(result['comparison_eligible'])
        self.assertEqual(m.BUDGET,120.)
        self.assertEqual(result['wall_budget_seconds'],900)

    def test_invalid_allocation_budget_or_declared_ceiling_rejects_before_output(self):
        for parameters in ({'budget':901},{'budget':59},{'budget':True},{'budget':float('nan')},
                {'budget':float('inf')},{'budget':240,'outer_ceiling':120},
                {'outer_ceiling':901},{'outer_ceiling':True},{'outer_ceiling':float('nan')},
                {'allocation':'board-identity-selection'},{'allocation':None}):
            with self.subTest(parameters=parameters),self.assertRaises(p.Rejected):
                m.experiment(self.out,**parameters)
            self.assertFalse(self.out.exists())

    def test_balanced_and_extended_resume_reject_before_prefix_reads_or_writes(self):
        for parameters in ({'allocation':'balanced'},{'budget':240}):
            with self.subTest(parameters=parameters),patch.object(m.pc,'read_bytes') as read:
                with self.assertRaisesRegex(p.Rejected,'legacy remaining'):
                    m.experiment(self.out,resume_plan='/missing',resume_plan_sha256='0'*64,**parameters)
                read.assert_not_called();self.assertFalse(self.out.exists())
        with patch.object(m.pc,'read_bytes') as read,self.assertRaisesRegex(p.Rejected,'legacy120'):
            m.resume_basis('/missing','0'*64,self.board,self.frozen,240,'arcdice',None)
        read.assert_not_called()

    def test_assigned_trial_allowance_must_be_finite_bounded_and_bound_to_receipt(self):
        for value in (True,0,-1,float('nan'),float('inf'),901):
            with self.subTest(value=value),self.assertRaisesRegex(p.Rejected,'bounded assigned'):
                m.verify_row({'assigned_seconds':value},self.board,self.frozen)
        result=m.experiment(self.out,budget=900,allocation='balanced')
        row=dict(result['trials'][0]);row['assigned_seconds']+=1
        with self.assertRaisesRegex(p.Rejected,'recorded allocation'):
            m.verify_row(row,self.board,self.frozen)

    def test_recorded_policy_count_and_available_budget_cannot_be_relabelled(self):
        result=m.experiment(self.out,budget=260,allocation='balanced')
        for mutation in ('allocation','unattempted_variants_at_assignment','remaining_wall_full_cpu_seconds_at_assignment','missing'):
            row=dict(result['trials'][0])
            if mutation=='missing':del row['allocation']
            elif mutation=='allocation':row[mutation]='remaining'
            elif mutation=='unattempted_variants_at_assignment':row[mutation]=True
            else:row[mutation]+=1
            with self.subTest(mutation=mutation),self.assertRaisesRegex(p.Rejected,'recorded allocation'):
                m.verify_row(row,self.board,self.frozen)

    def test_completed_prefix_metadata_cannot_shadow_remaining_policy(self):
        case=completed_harness.CompletedResumeControls('test_only_unattempted_variants_and_full_prior_cost')
        self.addCleanup(case.doCleanups);case.setUp()
        result=case.resumed()
        self.assertEqual(case.calls,[('via_low',64.),('via_high',54.)])
        self.assertEqual(result['allocation'],'remaining')
        self.assertEqual([row['allocation'] for row in result['trials'][1:]],['remaining','remaining'])
        self.assertEqual(result['completed_prefix_allocation']['policy'],m.COMPLETED_PREFIX_POLICY)
        self.assertEqual((result['wall_seconds'],result['total_cpu_seconds']),(41.,43.))
        self.assertTrue(result['comparison_eligible']);self.assertTrue(result['all_variants_attempted'])
        protocol=json.loads((case.out/'protocol.json').read_text())
        self.assertEqual(protocol['allocation'],'remaining')
        self.assertEqual(protocol['completed_prefix_allocation'],result['completed_prefix_allocation'])


if __name__=='__main__':unittest.main()
