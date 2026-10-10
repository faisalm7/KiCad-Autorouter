"""Pure policy/receipt controls; no native validation or routing is simulated as proof."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from autorouter import pipeline as p, strategy, handoff
from scripts import experiment_quality as quality, experiment_portfolio as portfolio
from scripts import experiment_paired as paired
import test_result as receipt_support


def finding(kind='padstack', severity='warning', **extra):
    return dict(type=kind, severity=severity, items=[{'uuid': 'controlled-pad'}], **extra)


class NativePolicyControls(unittest.TestCase):
    def native(self, *findings):
        return {'opens': 0, 'blocking': 0, 'warnings': len(findings),
                'exclusions': 0, 'ignored_checks': [], 'findings': list(findings)}

    def test_critical_warnings_fail_without_reclassifying_native_counts(self):
        for kind in ('padstack', 'padstack_invalid', 'clearance'):
            with self.subTest(kind=kind):
                native = self.native(finding(kind)); before = copy.deepcopy(native)
                self.assertFalse(p.native_accepted(native))
                self.assertFalse(strategy._valid(native))
                self.assertIn('policy-critical native finding: '+kind+' (warning)',
                              p.native_rejection_reasons(native))
                self.assertEqual(native, before)
                self.assertEqual(native['blocking'], 0)

    def test_ordinary_warning_is_preserved_and_allowed(self):
        native = self.native(finding('track_dangling'))
        self.assertTrue(p.native_accepted(native)); self.assertTrue(strategy._valid(native))
        self.assertEqual(native['warnings'], 1)

    def test_unknown_findings_fail_without_reclassifying_native_counts(self):
        for severity in ('warning', 'error', 'exclusion'):
            with self.subTest(severity=severity):
                native = self.native(finding('future_unqualified_check', severity))
                before = copy.deepcopy(native)
                self.assertFalse(p.native_accepted(native))
                self.assertFalse(strategy._valid(native))
                self.assertIn('unknown native finding semantics: future_unqualified_check',
                              p.native_rejection_reasons(native))
                self.assertEqual(native, before)

    def test_direct_helper_does_not_trust_forged_zero_counters(self):
        for item in (finding('track_dangling', 'error'), finding('track_dangling', excluded=True),
                     finding('track_dangling', 'exclusion')):
            with self.subTest(item=item): self.assertFalse(p.native_accepted(self.native(item)))

    def test_missing_or_malformed_summary_cannot_look_clean(self):
        cases = [None, {}, [], dict(self.native(), findings=None),
                 dict(self.native(), findings=[{}]), dict(self.native(), opens=False),
                 dict(self.native(), blocking=-1), dict(self.native(), exclusions='0'),
                 self.native(finding(excluded='false')), self.native(finding(severity=[])),
                 dict(self.native(), ignored_checks=None),
                 dict(self.native(), ignored_checks=[{'key':'padstack'}])]
        absent = self.native(); del absent['findings']; cases.append(absent)
        for native in cases:
            with self.subTest(native=native): self.assertFalse(p.native_accepted(native))

    def test_preflight_admits_only_padstack_warning_exception_and_never_edits_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            board = Path(tmp)/'board.kicad_pcb'
            board.write_text('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)))')
            for key, severity, permitted in [('padstack','warning',True), ('padstack','error',True),
                ('padstack','ignore',False), ('clearance','warning',False),
                ('clearance','ignore',False), ('padstack_invalid','warning',False),
                ('padstack_invalid','error',False), ('unknown_check','error',False)]:
                with self.subTest(key=key, severity=severity):
                    project = board.with_suffix('.kicad_pro')
                    project.write_text(json.dumps({'board':{'design_settings':{'rule_severities':{key:severity}}}}))
                    before = project.read_bytes()
                    if permitted: self.assertTrue(p.preflight(board))
                    else:
                        with self.assertRaises(p.Rejected): p.preflight(board)
                    self.assertEqual(project.read_bytes(), before)


class PolicyReceiptControls(unittest.TestCase):
    def setUp(self):
        # Reuse the filesystem receipt factory, not its test methods or mocks.
        self.case = receipt_support.ResultFreshnessTests(methodName='runTest')
        self.case.setUp(); self.addCleanup(self.case.doCleanups)

    def install_finding(self, kind='padstack'):
        case = self.case
        raw = copy.deepcopy(case.native_shape)
        raw['violations'] = [finding(kind)]
        case.native.write_text(json.dumps(raw))
        case.data['native'] = p.parse_report(case.native, case.source.name)
        case.data['native_report_sha256'] = p.sha(case.native)
        case.data['whole_project_drc_clean'] = False
        process_path = case.run/'final-drc-process.json'
        process = json.loads(process_path.read_text()); process.update(status='nonzero_exit', exit_code=5)
        process_path.write_text(json.dumps(process))
        case.data['steps'][0].update(status='nonzero_exit', exit_code=5)
        case.save_receipt()
        return case.data

    def test_parser_shape_stays_compatible_with_archived_native_summary(self):
        native = self.install_finding()['native']
        self.assertEqual(set(native), {'opens','blocking','warnings','exclusions','ignored_checks','findings'})
        self.assertEqual(native['findings'], [finding()])
        self.assertEqual((native['opens'],native['blocking'],native['warnings'],native['exclusions']), (0,0,1,0))

    def test_consistently_rehashed_accepted_receipt_still_rejects_critical_warning(self):
        for kind in ('padstack','padstack_invalid'):
            self.install_finding(kind)
            with self.subTest(kind=kind), self.assertRaisesRegex(p.Rejected, 'policy-critical native finding: '+kind):
                p.check_result(self.case.receipt)

    def test_ordinary_warning_receipt_still_verifies(self):
        self.install_finding('track_dangling')
        self.assertTrue(p.check_result(self.case.receipt)['current'])

    def test_rehashed_unknown_warning_receipt_and_handoff_reject(self):
        self.install_finding('future_unqualified_check')
        with self.assertRaisesRegex(p.Rejected, 'unknown native finding semantics'):
            p.check_result(self.case.receipt)
        target = self.case.root/'unknown-review'
        with self.assertRaisesRegex(p.Rejected, 'unknown native finding semantics'):
            handoff.review_copy(self.case.receipt, target)
        self.assertFalse(target.exists())

    def test_missing_warning_severity_and_disabled_padstack_remain_rejected(self):
        case = self.case
        for change in ('missing_warning','ignored_padstack'):
            raw = copy.deepcopy(case.native_shape)
            if change == 'missing_warning': raw['included_severities'].remove('warning')
            else: raw['ignored_checks'] = [{'key':'padstack','description':'ignored'}]
            case.native.write_text(json.dumps(raw))
            with self.subTest(change=change), self.assertRaises(p.Rejected): p.parse_report(case.native, case.source.name)

    def test_handoff_rejects_before_creating_review_copy(self):
        self.install_finding(); target = self.case.root/'review'
        with self.assertRaisesRegex(p.Rejected, 'policy-critical'):
            handoff.review_copy(self.case.receipt, target)
        self.assertFalse(target.exists())

    def test_quality_and_paired_c_arm_cannot_admit_rehashed_critical_warning(self):
        case = self.case; data = self.install_finding()
        data.update(adapter='both',engine_profile='tuned',proposal_policy='feedback',incumbent_baseline='B2_tuned')
        (case.run/'incumbent').mkdir()
        incumbent = case.run/'incumbent/result.json'
        incumbent.write_text(json.dumps(dict(data)))
        data['incumbent'] = {'receipt':str(incumbent)}; case.save_receipt()
        for arm in (dict(id='B2',adapter='both',engine_profile='tuned',operation='route'), paired.C_ARM):
            with self.subTest(arm=arm['id']):
                row = quality.summarize(arm,case.run,data,2,2)
                self.assertTrue(row['protocol_contract_verified'])
                self.assertFalse(row['accepted']); self.assertFalse(row['receipt_verified'])
                self.assertIn('policy-critical',row['receipt_verification_error'])

    def portfolio_row(self):
        case = self.case; data = self.install_finding()
        data.update(adapter='both',engine_profile='tuned',scoring_variant='via_default')
        engine = p.engine_profile_settings('tuned',120,scoring_variant='via_default')
        engine.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
        step = {'name':'engine','argv':['java',*engine['argv']],'status':'success',
                'exit_code':0,'cleanup_complete':True,'wall_seconds':0,'cpu_seconds':0,'monitor_cpu_seconds':0}
        (case.run/'engine-process.json').write_text(json.dumps(step))
        data.update(engine_budget=engine); data['steps'].append(step); case.save_receipt()
        row = {'id':'via_default','eligible':True,'status':'routing_accepted','assigned_seconds':120,
               'result':str(case.receipt),'result_sha256':p.sha(case.receipt),
               'candidate':str(case.candidate),'candidate_sha256':data['candidate_sha256'],
               'native_report_sha256':data['native_report_sha256'],'vias':0,'length_mm':2.0}
        frozen = {'tools':data['tools'],'source_hashes':data['source_hashes']}
        return row,frozen

    def test_portfolio_selection_rechecks_central_policy(self):
        row,frozen = self.portfolio_row()
        with self.assertRaisesRegex(p.Rejected,'policy-critical'):
            portfolio.verify_row(row,self.case.source,frozen)

    def test_paired_portfolio_frontier_rechecks_central_policy(self):
        row,frozen = self.portfolio_row(); directory = self.case.run.parent
        protocol = {'freeze':frozen,'variants':list(portfolio.VARIANTS)}
        (directory/'protocol.json').write_text(json.dumps(protocol))
        summary = {'status':'completed','comparison_eligible':True,'trials':[row],
                   'selected':row,'pareto_frontier':['via_default'],'wall_seconds':2,'total_cpu_seconds':2,
                   'protocol_sha256':p.sha(directory/'protocol.json')}
        (directory/'portfolio-summary.json').write_text(json.dumps(summary))
        with self.assertRaisesRegex(p.Rejected,'policy-critical'):
            paired.verify_portfolio(directory,summary,self.case.source,frozen)


if __name__ == '__main__': unittest.main()
