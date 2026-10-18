"""Synthetic allocation controls; no Native/JVM routing or CI runs.

Reuse the existing owned installed-context fixture. Mock clock/process costs
demonstrate accounting and refusal behavior, never a routing-quality outcome.
"""
import copy
import json
from pathlib import Path
import unittest

from scripts import experiment_portfolio as m
from tests import test_portfolio_installed_context as fixture


class InstalledTrialReserveControls(unittest.TestCase):
    setUp = fixture.InstalledPortfolioContextTests.setUp
    git = fixture.InstalledPortfolioContextTests.git
    checked = fixture.InstalledPortfolioContextTests.checked
    rejected = fixture.InstalledPortfolioContextTests.rejected
    receipt = fixture.InstalledPortfolioContextTests.receipt
    run_portfolio = fixture.InstalledPortfolioContextTests.run_portfolio

    def fake_runner(self, argv, **options):
        process = fixture.InstalledPortfolioContextTests.fake_runner(self, argv, **options)
        if getattr(self, 'saturating_first', False) and len(self.calls) == 1:
            allowance = self.calls[-1][1]
            cost = allowance + 1. if getattr(self, 'route_overshoot', False) else allowance - 9.
            self.cpu += cost - 12.
            process.update(cpu_seconds=cost - 1., supervisor_cpu_seconds=1.)
            directory = Path(argv[argv.index('--output') + 1])
            data = m.f.read_json(directory / 'result.json')
            data.update(accepted=False, status='drc_rejected', native_rejection_reasons=['native opens=1'])
            data['native']['opens'] = 1
            m.p.save_json(directory / 'result.json', data)
            process.update(status='nonzero_exit', exit_code=2)
        return process

    def reserved(self, **kwargs):
        return self.run_portfolio(installed_trial_policy=m.INSTALLED_TRIAL_RESERVE_POLICY, **kwargs)

    def freeze(self):
        return m.f.read_json(self.output / 'protocol.json')['freeze']

    def test_legacy_default_keeps_exact_assignments_and_no_reservation_markers(self):
        result = self.run_portfolio()
        self.assertEqual([row[1] for row in self.calls], [105., 93., 81.])
        self.assertTrue(result['comparison_eligible'])
        self.assertNotIn('installed_trial_accounting_policy', result)
        self.assertNotIn('installed_trial_accounting_policy', m.f.read_json(self.output / 'protocol.json'))
        self.assertTrue(all('route_allowance_seconds' not in row for row in result['trials']))

    def test_reserved_routes_bind_actual_lower_budget_without_charging_unused_reserve(self):
        result = self.reserved()
        self.assertTrue(result['comparison_eligible'])
        self.assertEqual(result['wall_budget_seconds'], 120.)
        self.assertEqual(result['total_cpu_seconds'], 36.)
        self.assertEqual(result['trial_readback_reserve_seconds'], 30.)
        self.assertEqual([row['assigned_seconds'] for row in result['trials']], [105., 93., 81.])
        self.assertEqual([row[1] for row in self.calls], [75., 63., 51.])
        for row, (_, route, argv, options) in zip(result['trials'], self.calls):
            self.assertEqual(options['timeout'], route)
            self.assertEqual(float(argv[argv.index('--seconds') + 1]), route)
            receipt = m.f.read_json(Path(row['result']))
            self.assertEqual(receipt['budget_seconds'], route)
            self.assertEqual(receipt['cpu_budget_seconds'], route)
            self.assertEqual(receipt['engine_budget']['outer_task_cpu_budget_seconds'], route)
            self.assertEqual(row['route_allowance_seconds'] + 30., row['assigned_seconds'])
            m.verify_row(row, self.board, self.freeze())

    def test_reserved_negative_fits_same_trial_cap_that_legacy_allocation_exhausts(self):
        for reserve in (False, True):
            with self.subTest(reserve=reserve):
                self.output = self.runtime / ('.runs/reserved' if reserve else '.runs/legacy')
                self.calls = []; self.wall = self.cpu = 0.; self.negative_calls = 0
                self.saturating_first = True; self.negative_cost = 2.
                result = self.reserved() if reserve else self.run_portfolio()
                self.assertEqual(len(self.calls), 1)
                self.assertFalse(result['comparison_eligible'])
                self.assertIsNone(result['selected'])
                row = result['trials'][0]
                self.assertEqual(row['assigned_seconds'], 105.)
                self.assertLess(self.cpu, 120.)
                if reserve:
                    self.assertEqual(result['status'], 'no_valid_candidate')
                    self.assertEqual(self.negative_calls, 6)
                    self.assertEqual(self.cpu, 78.)
                    self.assertTrue(row['validated_rejection'])
                    self.assertFalse(row['eligible'])
                    m.verify_negative_row(row, self.board, self.freeze())
                else:
                    self.assertEqual(result['status'], 'invalidated')
                    self.assertIn('diagnostic readbacks exceeded assigned', result['reason'])

    def test_reserved_negative_audit_overrun_still_invalidates_below_global_cap(self):
        self.saturating_first = True; self.negative_cost = 8.
        result = self.reserved()
        self.assertEqual(result['status'], 'invalidated')
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
        self.assertGreater(self.cpu, result['trials'][0]['assigned_seconds'])
        self.assertLess(self.cpu, result['cpu_budget_seconds'])
        self.assertIn('diagnostic readbacks exceeded assigned', result['reason'])

    def test_route_process_cannot_borrow_the_diagnostic_reserve(self):
        self.saturating_first = self.route_overshoot = True
        result = self.reserved()
        self.assertEqual(result['status'], 'invalidated')
        self.assertEqual(len(self.calls), 1); self.assertEqual(self.negative_calls, 0)
        self.assertLess(self.cpu, result['trials'][0]['assigned_seconds'])
        self.assertIn('installed CLI process failed, exceeded bounds', result['reason'])

    def test_final_negative_fence_enforces_both_trial_and_global_caps(self):
        for cost in (50., 60.):
            with self.subTest(cost=cost):
                self.output = self.runtime / ('.runs/final-' + str(int(cost)))
                self.calls = []; self.wall = self.cpu = 0.; self.negative_calls = 0
                self.saturating_first = True; self.negative_cost = cost; self.negative_cost_at = 6
                result = self.reserved()
                self.assertEqual(self.negative_calls, 6)
                self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
                self.assertEqual(result['status'], 'invalidated' if cost == 50. else 'budget_exceeded')
                self.assertTrue(list(self.output.glob('invalidated-portfolio-summary-*.json')))

    def test_minimum_route_and_native_reserves_are_checked_after_audit_reservation(self):
        result = self.reserved(budget=180, allocation='balanced')
        self.assertEqual(self.calls, [])
        self.assertEqual(result['status'], 'no_valid_candidate')
        self.assertEqual(result['skipped_variants'][0]['assigned_if_started_seconds'], 55.)
        self.assertEqual(result['skipped_variants'][0]['route_allowance_if_started_seconds'], 25.)
        self.assertEqual(result['unattempted_variants'], list(m.VARIANTS))

    def test_row_or_protocol_reservation_cannot_be_deleted_or_relabelled(self):
        result = self.reserved(); original = result['trials'][0]
        path = self.output / 'protocol.json'; protocol = m.f.read_json(path)
        for fault in ('row_missing', 'row_all_missing', 'policy', 'route', 'reserve',
                      'protocol_missing', 'protocol_unknown', 'both_missing'):
            with self.subTest(fault=fault):
                row = copy.deepcopy(original); value = copy.deepcopy(protocol)
                if fault == 'row_missing': row.pop('route_allowance_seconds')
                elif fault in {'row_all_missing', 'both_missing'}:
                    for key in ('installed_trial_accounting_policy', 'route_allowance_seconds',
                                'trial_readback_reserve_seconds'): row.pop(key)
                elif fault == 'policy': row['installed_trial_accounting_policy'] = 'unknown'
                elif fault == 'route': row['route_allowance_seconds'] += 1.
                elif fault == 'reserve': row['trial_readback_reserve_seconds'] = 29.
                if fault in {'protocol_missing', 'both_missing'}:
                    for key in ('installed_trial_accounting_policy', 'trial_readback_reserve_seconds'): value.pop(key)
                elif fault == 'protocol_unknown': value['installed_trial_accounting_policy'] = 'unknown'
                m.p.save_json(path, value)
                with self.assertRaises(m.p.Rejected): m.verify_row(row, self.board, protocol['freeze'])
        m.p.save_json(path, protocol)

    def test_receipt_cannot_claim_total_trial_allowance_after_reauthored_hashes(self):
        result = self.reserved(); row = result['trials'][0]
        path = Path(row['result']); data = m.f.read_json(path)
        data['budget_seconds'] = data['cpu_budget_seconds'] = row['assigned_seconds']
        m.p.save_json(path, data)
        row['result_sha256'] = m.p.sha(path)
        row['installed_cli']['result']['sha256'] = m.p.sha(path)
        with self.assertRaisesRegex(m.p.Rejected, 'frozen portfolio contract'):
            m.verify_row(row, self.board, self.freeze())

    def test_reserved_late_cancellation_and_negative_process_tamper_never_fall_back(self):
        self.negative_second = True; self.negative_cost = 2.
        self.negative_error = KeyboardInterrupt(); self.negative_error_at = 6
        result = self.reserved()
        self.assertEqual(result['status'], 'cancelled')
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
        self.output = self.runtime / '.runs/tamper'
        self.calls = []; self.wall = self.cpu = 0.; self.negative_calls = 0
        self.negative_error = None
        self.after_third = lambda: (self.output / '02-via_low.cli.log').write_bytes(b'late changed witness')
        result = self.reserved()
        self.assertEqual(result['status'], 'invalidated')
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])

    def test_opt_in_requires_a_known_policy_and_fresh_installed_context(self):
        for value in ('unknown', True, [], {}):
            with self.subTest(value=value), self.assertRaises(m.p.Rejected):
                m.experiment(self.output, installed_context=self.context, installed_trial_policy=value)
            self.assertFalse(self.output.exists())
        with self.assertRaisesRegex(m.p.Rejected, 'fresh installed context'):
            m.experiment(self.output, installed_trial_policy=m.INSTALLED_TRIAL_RESERVE_POLICY)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
