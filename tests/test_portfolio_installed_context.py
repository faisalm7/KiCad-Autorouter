"""Tiny owned source/process controls; mocked receipts do not qualify routing."""
import copy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import experiment_portfolio as m

REAL_PYTHON = sys.executable


class InstalledPortfolioContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.runtime = self.base / "runtime with spaces ' $(literal)"; self.runtime.mkdir()
        (self.runtime / '.runs').mkdir(); (self.runtime / '.venv/bin').mkdir(parents=True)
        (self.runtime / '.venv/bin/python').symlink_to(REAL_PYTHON)
        self.admin = self.base / 'administration'; (self.admin / 'scripts').mkdir(parents=True)
        sources = {'scripts/experiment_portfolio.py': Path(m.__file__).read_bytes(),
                   'scripts/experiment_quality.py': Path(m.q.__file__).read_bytes(),
                   'scripts/controller.py': b'# owned inert controller fixture\n'}
        for name, raw in sources.items(): (self.admin / name).write_bytes(raw)
        self.git('init', '-q'); self.git('add', 'scripts')
        self.git('-c', 'user.name=Owned fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'Owned installed context fixture')
        self.head = m.pv.git_head(self.admin)
        self.source = self.base / 'external original'; self.source.mkdir()
        self.board = self.source / 'board.kicad_pcb'
        for suffix, raw in (('.kicad_pcb', b'owned PCB fixture\n'), ('.kicad_pro', b'{}'),
                            ('.kicad_sch', b'owned complete SCH fixture\n')):
            self.board.with_suffix(suffix).write_bytes(raw)
        self.source_hashes = m.pc.inventory(self.source)
        modules = (m.p, m.pc, m.f, m.pv, m.runtime_runner)
        implementation = {}
        for module in modules:
            path = self.runtime / 'autorouter' / Path(module.__file__).name
            path.parent.mkdir(exist_ok=True); path.write_bytes(b'# inert runtime fixture\n')
            implementation[str(path.relative_to(self.runtime))] = hashlib.sha256(path.read_bytes()).hexdigest()
        (self.runtime / 'toolchain.lock.json').write_bytes(b'{}')
        (self.runtime / m.pv.MANIFEST).write_bytes(b'{}')
        self.tools = {'implementation_sha256': implementation, 'git_head': 'a' * 40,
            'source_provenance': {'kind': m.pv.KIND, 'manifest_sha256': hashlib.sha256(b'{}').hexdigest()}}
        changes = [patch.object(m.c, 'ROOT', self.runtime), patch.object(m, 'SCRIPT', self.admin / 'scripts/experiment_portfolio.py'),
            patch.object(m.q, '__file__', str(self.admin / 'scripts/experiment_quality.py')),
            patch.object(sys, 'executable', str(self.runtime / '.venv/bin/python')),
            patch.object(sys, 'prefix', str(self.runtime / '.venv')),
            patch.object(m.p, 'tool_manifest', side_effect=lambda: copy.deepcopy(self.tools)),
            patch.object(m.p, 'check_storage'), patch.object(m.p, 'check_result', side_effect=self.checked),
            patch.object(m.p, 'check_rejected_routing_attempt', side_effect=self.rejected)]
        changes.extend(patch.object(module, '__file__', str(self.runtime / 'autorouter' / Path(module.__file__).name))
                       for module in modules)
        for change in changes: change.start(); self.addCleanup(change.stop)
        self.context = m.InstalledContext(self.runtime, self.board, 'owned-exposed-fixture',
            copy.deepcopy(self.tools), dict(self.source_hashes), self.admin, self.head,
            {name: hashlib.sha256(raw).hexdigest() for name, raw in sources.items()},
            self.admin / 'scripts/controller.py')
        self.wall = self.cpu = 0.; self.calls = []; self.bad_second = None; self.after_second = None
        self.negative_second = False
        self.negative_calls = 0; self.negative_cost = 0.; self.negative_cost_at = None; self.negative_response_change = None
        self.negative_error = None; self.negative_error_at = None; self.after_third = None
        self.output = self.runtime / '.runs/new-portfolio'

    def git(self, *arguments):
        return subprocess.run(['git', '-C', str(self.admin), *arguments], capture_output=True,
                              check=True, timeout=5).stdout

    def checked(self, receipt):
        data = json.loads(receipt.read_bytes())
        return {'current': True, 'applied': False, 'candidate': data['candidate'],
                'candidate_sha256': data['candidate_sha256']}

    def rejected(self, receipt):
        self.negative_calls += 1
        if self.negative_cost_at is None or self.negative_calls == self.negative_cost_at:
            self.cpu += self.negative_cost
        if self.negative_error and (self.negative_error_at is None or self.negative_calls == self.negative_error_at):
            raise self.negative_error
        data = json.loads(receipt.read_bytes())
        checked = {'current': False, 'validated_rejection': True, 'routing_accepted': False, 'applied': False,
            'candidate': data['candidate'], 'candidate_sha256': data['candidate_sha256'],
            'native_report_sha256': data['native_report_sha256'],
            'native_rejection_reasons': data['native_rejection_reasons'],
            'receipt_sha256': hashlib.sha256(receipt.read_bytes()).hexdigest()}
        if self.negative_response_change: checked.update(self.negative_response_change)
        return checked

    def receipt(self, directory, assigned, variant):
        directory.mkdir()
        engine = m.p.engine_profile_settings('tuned', assigned, scoring_variant=variant)
        engine.update(outer_task_wall_budget_seconds=assigned, outer_task_cpu_budget_seconds=assigned)
        step = {'name': 'engine', 'argv': ['java', *engine['argv']], 'status': 'success',
                'exit_code': 0, 'cleanup_complete': True}
        m.p.save_json(directory / 'engine-process.json', step)
        data = {'source': str(self.board), 'source_hashes': self.source_hashes, 'tools': self.tools,
            'schema': 1, 'baseline': 'B2_tuned',
            'status': 'routing_accepted', 'accepted': True, 'scope': 'whole_board_unlocked_routing',
            'adapter': 'both', 'engine_profile': 'tuned', 'scoring_variant': variant,
            'budget_seconds': assigned, 'cpu_budget_seconds': assigned,
            'candidate': str(directory / 'candidate/board.kicad_pcb'), 'candidate_sha256': 'a' * 64,
            'native_report_sha256': 'b' * 64, 'metrics': {'vias': 2, 'track_length_mm': 100. - len(self.calls)},
            'steps': [step], 'engine_budget': engine, 'native': {'opens': 0, 'blocking': 0, 'exclusions': 0}}
        m.p.save_json(directory / 'result.json', data)
        return data

    def fake_runner(self, argv, **options):
        variant = argv[argv.index('--scoring-preference') + 1]
        assigned = float(argv[argv.index('--seconds') + 1]); directory = Path(argv[argv.index('--output') + 1])
        self.calls.append((variant, assigned, argv, options))
        self.wall += 9.; self.cpu += 12.
        data = self.receipt(directory, assigned, variant)
        options['log'].write_bytes(b'owned inert CLI output\n')
        process = dict(argv=argv, status='success', exit_code=0, cleanup_complete=True,
                       log_truncated=False, wall_seconds=9., cpu_seconds=11.,
                       supervisor_cpu_seconds=1., monitor_cpu_seconds=0.)
        if len(self.calls) == 2:
            if self.bad_second: process.update(self.bad_second)
            if self.negative_second:
                process.update(status='nonzero_exit', exit_code=2)
                data.update(accepted=False, status='drc_rejected', native_rejection_reasons=['native opens=1'])
                data['native']['opens'] = 1
                m.p.save_json(directory / 'result.json', data)
            if self.after_second: self.after_second()
        if len(self.calls) == 3 and self.after_third: self.after_third()
        return process

    def run_portfolio(self, **extra):
        with patch.object(m.time, 'monotonic', side_effect=lambda: self.wall), \
             patch.object(m.q, 'total_process_cpu', side_effect=lambda: self.cpu), \
             patch.object(m.runtime_runner, 'run', side_effect=self.fake_runner), \
             patch.object(m.q, 'selected_source', side_effect=AssertionError('source-only selector called')), \
             patch.object(m, 'freeze', side_effect=AssertionError('legacy Git freeze called')):
            return m.experiment(self.output, installed_context=self.context, **extra)

    def test_exact_context_existing_loop_and_independent_reader(self):
        result = self.run_portfolio()
        self.assertTrue(result['comparison_eligible']); self.assertEqual(result['status'], 'completed')
        self.assertEqual([(name, budget) for name, budget, *_ in self.calls],
                         [('via_default', 105.), ('via_low', 93.), ('via_high', 81.)])
        self.assertEqual(result['selected']['id'], 'via_high')
        self.assertEqual(result['pareto_frontier'], ['via_high'])
        self.assertGreaterEqual(m.p.check_result.call_count, 3)
        self.assertTrue((self.output / 'frozen-administration/scripts/controller.py').is_file())
        frozen = json.loads((self.output / 'protocol.json').read_bytes())['freeze']
        self.assertEqual(frozen['installed_context']['administration_head'], self.head)
        self.assertEqual(result['total_cpu_seconds'], 36.)
        for name, assigned, argv, options in self.calls:
            self.assertEqual(argv[:len(m.f.SANDBOX)], m.f.SANDBOX)
            self.assertEqual(options['cwd'], self.output)
            self.assertEqual(options['timeout'], assigned)
            self.assertEqual(argv[argv.index('--profile') + 1], 'tuned')
            self.assertEqual(argv[argv.index('--layers') + 1], 'source_all')
            self.assertNotIn('PYTHONPATH', options['env'])
        row = result['trials'][0]
        Path(row['installed_cli']['log']['file']).write_bytes(b'changed retained log')
        with self.assertRaisesRegex(m.p.Rejected, 'process/log/result changed'):
            m.verify_row(row, self.board, frozen)

    def test_wrong_runtime_module_interpreter_or_current_tools_refuses(self):
        for change in (patch.object(m.p, '__file__', str(self.admin / 'pipeline.py')),
                       patch.object(sys, 'executable', REAL_PYTHON),
                       patch.object(m.p, 'tool_manifest', return_value={})):
            with self.subTest(change=change), change, self.assertRaises(m.p.Rejected): self.context.check()
        self.context.tools['unexpected'] = True
        with self.assertRaisesRegex(m.p.Rejected, 'expectations changed'): self.context.check()

    def test_complete_external_source_missing_extra_changed_or_linked_refuses(self):
        path = self.board.with_suffix('.kicad_sch'); original = path.read_bytes()
        path.unlink()
        with self.assertRaises(m.p.Rejected): self.context.check()
        path.write_bytes(original); path.write_bytes(original + b'drift')
        with self.assertRaises(m.p.Rejected): self.context.check()
        path.write_bytes(original); extra = self.source / 'extra'; extra.write_bytes(b'extra')
        with self.assertRaises(m.p.Rejected): self.context.check()
        extra.unlink(); alias = self.base / 'hardlink'; os.link(path, alias)
        with self.assertRaises(m.p.Rejected): self.context.check()
        alias.unlink(); self.context.check()

    def test_external_administration_must_be_complete_clean_exact_head_blobs(self):
        controller = self.context.controller; original = controller.read_bytes()
        controller.write_bytes(b'# changed\n')
        with self.assertRaises(m.p.Rejected): self.context.check()
        self.git('update-index', '--assume-unchanged', 'scripts/controller.py')
        with self.assertRaisesRegex(m.p.Rejected, 'administration bytes changed'): self.context.check()
        controller.write_bytes(original)
        incomplete = dict(self.context.administration_files_sha256); incomplete.pop('scripts/controller.py')
        with self.assertRaisesRegex(m.p.Rejected, 'controller source pins'):
            replace(self.context, administration_files_sha256=incomplete).check()
        with self.assertRaises(m.p.Rejected): replace(self.context, administration_head='b' * 40).check()

    def test_malformed_context_guidance_and_resume_refuse_before_attempts(self):
        for change in ({'runtime': str(self.runtime)}, {'source_hashes': {'../escape': 'a' * 64}},
                       {'tools': {}}, {'family': ''}, {'administration_head': 'not-a-head'}):
            with self.subTest(change=change), self.assertRaises((m.p.Rejected, ValueError)):
                replace(self.context, **change)
        for extra in ({'guidance_policy': 'placement-search-v1'},
                      {'resume_plan': 'never-read', 'resume_plan_sha256': 'a' * 64}):
            with self.subTest(extra=extra), self.assertRaises(m.p.Rejected): self.run_portfolio(**extra)
        self.assertEqual(self.calls, []); self.assertFalse(self.output.exists())

    def test_process_failures_after_a_valid_trial_cannot_select_incumbent(self):
        cases = [{'status': 'nonzero_exit', 'exit_code': 2}, {'cleanup_complete': False},
                 {'log_truncated': True}, {'cpu_seconds': None}, {'cpu_seconds': 1000.},
                 {'wall_seconds': 1000.}, {'argv': ['wrong CLI']}]
        for index, change in enumerate(cases):
            with self.subTest(change=change):
                self.output = self.runtime / f'.runs/failure-{index}'
                self.calls = []; self.wall = self.cpu = 0.; self.bad_second = change
                result = self.run_portfolio()
                self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
                self.assertEqual(result['status'], 'invalidated'); self.assertEqual(len(self.calls), 2)
                self.assertTrue(result['trials'][0]['eligible'])
                self.assertEqual(set(result['trials'][1]['installed_cli']), {'process', 'log', 'result'})

    def test_cancelled_process_is_terminal_even_with_existing_incumbent(self):
        self.bad_second = {'status': 'cancelled', 'exit_code': 130}
        result = self.run_portfolio()
        self.assertEqual(result['status'], 'cancelled'); self.assertFalse(result['comparison_eligible'])
        self.assertIsNone(result['selected']); self.assertEqual(len(self.calls), 2)

    def test_verified_negative_remains_ineligible_and_continues_fixed_portfolio(self):
        self.negative_second = True
        result = self.run_portfolio()
        self.assertTrue(result['comparison_eligible']); self.assertEqual(len(self.calls), 3)
        self.assertEqual(result['selected']['id'], 'via_high')
        row = result['trials'][1]
        self.assertTrue(row['validated_rejection']); self.assertFalse(row['eligible'])
        self.assertFalse(row['accepted_in_trial_receipt'])
        self.assertFalse(row['negative_readback']['current'])
        self.assertEqual(set(row['installed_cli']), {'process', 'log', 'result', 'rejection'})
        self.assertGreaterEqual(self.negative_calls, 4)  # Classify, row, final selection, publication.

    def test_negative_api_refusal_or_cancel_never_falls_back_to_earlier_winner(self):
        for index, error in enumerate((m.p.Rejected('unknown Native evidence'), KeyboardInterrupt())):
            with self.subTest(error=type(error).__name__):
                self.output = self.runtime / f'.runs/negative-refusal-{index}'
                self.calls = []; self.wall = self.cpu = 0.; self.negative_calls = 0
                self.negative_second = True; self.negative_error = error
                result = self.run_portfolio()
                self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
                self.assertEqual(result['status'], 'cancelled' if isinstance(error, KeyboardInterrupt) else 'invalidated')
                self.assertEqual(len(self.calls), 2)

    def test_negative_return_flags_reasons_and_identity_cannot_promote_or_hide_drift(self):
        changes = [{'current': True}, {'validated_rejection': 1}, {'routing_accepted': True},
            {'applied': True}, {'receipt_sha256': '0' * 64}, {'candidate': '/another/candidate'},
            {'native_report_sha256': '0' * 64}, {'native_rejection_reasons': []}]
        for index, change in enumerate(changes):
            with self.subTest(change=change):
                self.output = self.runtime / f'.runs/negative-identity-{index}'
                self.calls = []; self.wall = self.cpu = 0.; self.negative_calls = 0
                self.negative_second = True; self.negative_response_change = change
                result = self.run_portfolio()
                self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
                self.assertIn('negative diagnostic identity', result['reason'])
                self.assertEqual(len(self.calls), 2)

    def test_negative_diagnostic_cannot_substitute_another_assignment_or_baseline(self):
        directory = self.runtime / '.runs/negative-assignment'; data = self.receipt(directory, 100., 'via_low')
        data.update(accepted=False, status='drc_rejected', native_rejection_reasons=['native opens=1'])
        changes = [{'schema': True}, {'baseline': 'B1'}, {'adapter': 'none'}, {'engine_profile': 'standard'},
            {'scope': 'partial_completion'}, {'source': '/another/source.kicad_pcb'},
            {'source_hashes': {}}, {'tools': {}}, {'scoring_variant': 'via_default'},
            {'budget_seconds': 99.}, {'cpu_budget_seconds': 99.}]
        for change in changes:
            with self.subTest(change=change):
                m.p.save_json(directory / 'result.json', {**data, **change})
                with self.assertRaisesRegex(m.p.Rejected, 'negative trial differs'):
                    m._installed_negative_readback(directory / 'result.json', self.board,
                        {'tools': self.tools, 'source_hashes': self.source_hashes}, 100., 'via_low')
        self.assertEqual(self.negative_calls, 0)

    def test_late_negative_reader_refusal_invalidates_prior_and_later_positives(self):
        for call in (3, 4, 5, 6):
            with self.subTest(diagnostic_call=call):
                self.output = self.runtime / f'.runs/negative-late-{call}'
                self.calls = []; self.wall = self.cpu = 0.; self.negative_calls = 0
                self.negative_second = True; self.negative_error_at = call
                self.negative_error = m.p.Rejected('late original rules or raw Native report changed')
                result = self.run_portfolio()
                self.assertEqual(len(self.calls), 3); self.assertEqual(self.negative_calls, call)
                self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
                self.assertIn('late original rules', result['reason'])

    def test_late_negative_process_log_result_or_diagnostic_tamper_refuses(self):
        for index, name in enumerate(('02-via_low.cli-process.json', '02-via_low.cli.log',
                                     '02-via_low/result.json', '02-via_low.cli-rejection.json')):
            with self.subTest(name=name):
                self.output = self.runtime / f'.runs/negative-tamper-{index}'
                self.calls = []; self.wall = self.cpu = 0.; self.negative_calls = 0
                self.negative_second = True
                self.after_third = lambda name=name: (self.output / name).write_bytes(b'changed negative witness')
                result = self.run_portfolio()
                self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
                self.assertIn('retained process/log/result changed', result['reason'])
                self.assertEqual(len(self.calls), 3)

    def test_negative_changed_during_positive_summary_publication_invalidates_it(self):
        self.negative_second = True; injected = []
        save = m.p.save_json
        def publish(path, data):
            saved = save(path, data)
            if (Path(path) == self.output / 'portfolio-summary.json'
                    and data.get('comparison_eligible') is True and not injected):
                injected.append(True)
                (self.output / '02-via_low.cli-rejection.json').write_bytes(b'changed during publication')
            return saved
        with patch.object(m.p, 'save_json', side_effect=publish): result = self.run_portfolio()
        self.assertTrue(injected)
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
        self.assertIn('retained process/log/result changed', result['reason'])
        stored = json.loads((self.output / 'portfolio-summary.json').read_bytes())
        self.assertFalse(stored['comparison_eligible'])

    def test_negative_tamper_during_second_eligible_write_is_inside_final_readonly_fence(self):
        self.negative_second = True; eligible_writes = []
        save = m.p.save_json
        def publish(path, data):
            saved = save(path, data)
            if Path(path) == self.output / 'portfolio-summary.json' and data.get('comparison_eligible') is True:
                eligible_writes.append(True)
                if len(eligible_writes) == 2:
                    (self.output / '02-via_low.cli-rejection.json').write_bytes(b'changed after last eligible write')
            return saved
        with patch.object(m.p, 'save_json', side_effect=publish): result = self.run_portfolio()
        self.assertEqual(len(eligible_writes), 2)
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
        self.assertIn('retained process/log/result changed', result['reason'])
        self.assertTrue(list(self.output.glob('invalidated-portfolio-summary-*.json')))
        stored = json.loads((self.output / 'portfolio-summary.json').read_bytes())
        self.assertFalse(stored['comparison_eligible']); self.assertIsNone(stored['selected'])

    def test_all_negative_diagnostic_cpu_is_charged_including_final_readbacks(self):
        self.negative_second = True; self.negative_cost = 2.
        result = self.run_portfolio()
        self.assertTrue(result['comparison_eligible'])
        self.assertEqual(self.cpu, 36. + 2. * self.negative_calls)
        self.assertEqual(result['total_cpu_seconds'], self.cpu - 2.)  # Literal pre-final-fence sample.
        self.assertIn('complete external whole-process accounting is required', result['accounting_point'])
        row = result['trials'][1]
        self.assertEqual(row['invocation_cpu_seconds'], 16.)
        self.assertEqual(row['negative_readback_cpu_seconds'], 2. * (self.negative_calls - 3))
        self.assertEqual(self.calls[2][1], 77.)

    def test_final_readonly_negative_fence_enforces_assignment_without_positive_rewrite(self):
        self.negative_second = True; self.negative_cost = 70.; self.negative_cost_at = 6
        #120 balanced yields35s, below the unchanged41s minimum and starts no trials.
        result = self.run_portfolio(allocation='balanced', budget=180)
        self.assertEqual(self.negative_calls, 6)
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
        self.assertLess(result['total_cpu_seconds'], 120.)
        self.assertIn('diagnostic readbacks exceeded assigned', result['reason'])

    def test_final_readonly_fence_global_cpu_cap_cannot_rewrite_positive(self):
        self.negative_second = True; eligible_writes = []
        save = m.p.save_json
        def publish(path, data):
            saved = save(path, data)
            if Path(path) == self.output / 'portfolio-summary.json' and data.get('comparison_eligible') is True:
                eligible_writes.append(True)
                if len(eligible_writes) == 2: self.cpu = 121.
            return saved
        with patch.object(m.p, 'save_json', side_effect=publish): result = self.run_portfolio()
        self.assertEqual(len(eligible_writes), 2)
        self.assertEqual(result['status'], 'budget_exceeded')
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])

    def test_negative_diagnostic_cost_can_exhaust_assignment_before_global_cap(self):
        self.negative_second = True; self.negative_cost = 35.
        #180 allows real mock attempts; two35s diagnostics exceed76.5s assigned,
        # while the whole invocation remains below its global allowance.
        result = self.run_portfolio(allocation='balanced', budget=180)
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
        self.assertEqual(result['status'], 'invalidated'); self.assertLess(result['total_cpu_seconds'], 120.)
        self.assertIn('including diagnostic checks exceeded assigned', result['reason'])
        self.assertEqual(len(self.calls), 2)

    def test_source_or_process_evidence_drift_invalidates_complete_portfolio(self):
        self.after_second = lambda: (self.output / '01-via_default.cli.log').write_bytes(b'drift')
        result = self.run_portfolio()
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
        self.assertIn('process/log/result changed', result['reason'])

    def test_source_change_after_attempt_cannot_retain_earlier_winner(self):
        self.after_second = lambda: self.board.write_bytes(b'changed original input')
        result = self.run_portfolio()
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
        self.assertIn('external installed source project changed', result['reason'])
        self.assertEqual(len(self.calls), 2)

    def test_accepted_cli_receipt_cannot_override_independent_reader_refusal(self):
        with patch.object(m.p, 'check_result', side_effect=m.p.Rejected('deliberately invalid native evidence')):
            result = self.run_portfolio()
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
        self.assertIn('deliberately invalid native evidence', result['reason'])
        self.assertEqual(len(self.calls), 1)

    def test_real_bounded_exec_bootstrap_runs_only_inert_installed_cli_fixture(self):
        package = self.runtime / 'autorouter'; (package / '__init__.py').write_bytes(b'')
        (package / '__main__.py').write_text('import json,pathlib,sys\n'
            'args=sys.argv[1:]; out=pathlib.Path(args[args.index("--output")+1]); out.mkdir()\n'
            '(out/"result.json").write_text(json.dumps(dict(accepted=True,status="routing_accepted",argv=args)))\n')
        work = self.runtime / '.runs/real-inert-cli'; work.mkdir()
        result = m._installed_attempt(self.context, work / '01-via_low', 5., 'via_low')
        self.assertEqual(result['argv'][0], 'route')
        self.assertEqual(result['argv'][-2:], ['--scoring-preference', 'via_low'])
        self.assertTrue((work / '01-via_low.cli-process.json').is_file())
        self.assertNotIn('candidate_sha256', result)  # Inert process proof only, never route validity.

    def test_default_path_retains_original_source_freeze_and_python_attempts(self):
        frozen = {'tools': self.tools, 'source_hashes': self.source_hashes, 'files_sha256': {}}
        def route(board, directory, assigned, keep, adapter, profile, *, scoring_variant):
            self.calls.append((scoring_variant, assigned)); self.wall += 9.; self.cpu += 12.
            return self.receipt(directory, assigned, scoring_variant)
        with patch.object(m.time, 'monotonic', side_effect=lambda: self.wall), \
             patch.object(m.q, 'total_process_cpu', side_effect=lambda: self.cpu), \
             patch.object(m.q, 'selected_source', return_value=(self.board, 'legacy-fixture')) as selected, \
             patch.object(m, 'freeze', return_value=frozen) as freeze, \
             patch.object(m.q, 'verify_freeze') as verify, patch.object(m.p, 'route', side_effect=route), \
             patch.object(m.runtime_runner, 'run', side_effect=AssertionError('installed runner used')):
            result = m.experiment(self.output)
        self.assertTrue(result['comparison_eligible']); selected.assert_called_once(); freeze.assert_called_once()
        self.assertTrue(verify.called); self.assertNotIn('installed_cli', result['trials'][0])


class ComparisonPortfolioAPITests(unittest.TestCase):
    """No Git/Native/process execution; real seals, allocation and file readers.

    Authored engine rows below are fixtures, never actual execution evidence.
    Existing CLI/Git fixture controls above remain a separate integration gate.
    """
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve(); self.runtime = self.base/'runtime'
        (self.runtime/'.runs').mkdir(parents=True); (self.runtime/'.venv').mkdir()
        self.admin = self.base/'admin'; (self.admin/'scripts').mkdir(parents=True)
        admin = {'scripts/experiment_portfolio.py': Path(m.__file__).read_bytes(),
                 'scripts/experiment_quality.py': Path(m.q.__file__).read_bytes(),
                 'scripts/controller.py': b'# inert caller fixture\n'}
        self.blobs = {hashlib.sha1(raw).hexdigest(): raw for raw in admin.values()}
        for name,raw in admin.items(): (self.admin/name).write_bytes(raw)
        self.board = self.base/'source/owned.kicad_pcb'; self.board.parent.mkdir()
        for suffix,raw in (('.kicad_pcb',b'(kicad_pcb)\n'),('.kicad_pro',b'{}\n'),
                           ('.kicad_sch',b'(kicad_sch)\n')):
            self.board.with_suffix(suffix).write_bytes(raw)
        self.hashes=m.pc.inventory(self.board.parent)
        modules=(m.p,m.pc,m.f,m.pv,m.runtime_runner,m.cmp); implementation={}
        for module in modules:
            path=self.runtime/'autorouter'/Path(module.__file__).name
            path.parent.mkdir(exist_ok=True);path.write_bytes(Path(module.__file__).read_bytes())
            implementation[str(path.relative_to(self.runtime))]=hashlib.sha256(path.read_bytes()).hexdigest()
        for name in ('toolchain.lock.json',m.pv.MANIFEST):(self.runtime/name).write_bytes(b'{}')
        self.tools=dict(implementation_sha256=implementation,git_head='a'*40,files={},kicad='10.0.7',
            comparison_route_policy=m.cmp.POLICY,source_provenance=dict(kind=m.pv.KIND,
            native_version='10.0.7',manifest_sha256=hashlib.sha256(b'{}').hexdigest()))
        self.output=self.runtime/'.runs/native7-comparison-portfolio-control';self.registry={}
        self.wall=self.cpu=0.;self.calls=[];self.readers=[];self.events=[];self.mode='positive'
        self.after_second=None;self.after_third=None;self.reader_error=None;self.read_cost=0.
        self.reader_counts={};self.on_reader=None;self.after_summary=None
        self.summary_published=False;self.final_scores=set();self.metadata_dirty=False;self.late_metadata_fault=False
        changes=[patch.object(m.c,'ROOT',self.runtime),patch.object(m.c,'NATIVE_VERSION','10.0.7'),
            patch.object(m,'SCRIPT',self.admin/'scripts/experiment_portfolio.py'),
            patch.object(m.q,'__file__',str(self.admin/'scripts/experiment_quality.py')),
            patch.object(sys,'executable',str(self.runtime/'.venv/bin/python')),
            patch.object(sys,'prefix',str(self.runtime/'.venv')),
            patch.object(m.pv,'git_head',return_value='a'*40),patch.object(m.pv,'_git',side_effect=self.git_bytes),
            patch.object(m.p,'tool_manifest',side_effect=self.manifest),patch.object(m.p,'check_storage'),
            patch.object(m.p,'route',side_effect=self.route),patch.object(m.p,'check_result',side_effect=self.checked),
            patch.object(m.p,'check_rejected_routing_attempt',side_effect=self.rejected),
            patch.object(m.p,'check_experimental_local_settings',side_effect=self.metadata),
            patch.object(m.runtime_runner,'run',side_effect=AssertionError('API invented CLI execution')),
            patch.object(m.subprocess,'run',side_effect=AssertionError('test attempted subprocess/Git')),
            patch.object(m.time,'monotonic',side_effect=lambda:self.wall),
            patch.object(m.q,'total_process_cpu',side_effect=lambda:self.cpu)]
        changes += [patch.object(module,'__file__',str(self.runtime/'autorouter'/Path(module.__file__).name))
                    for module in modules]
        for change in changes:change.start();self.addCleanup(change.stop)
        self.context=m.InstalledContext(self.runtime,self.board,'owned-exposed-fixture',
            copy.deepcopy(self.tools),dict(self.hashes),self.admin,'a'*40,
            {name:hashlib.sha256(raw).hexdigest() for name,raw in admin.items()},self.admin/'scripts/controller.py',
            comparison_policy=m.COMPARISON_API_POLICY,comparison_output=self.output)

    def git_bytes(self,root,*argv,**kwargs):
        if argv[0]=='status':return b''
        if argv[0]=='ls-tree':
            return b''.join(b'100644 blob '+hashlib.sha1((self.admin/name).read_bytes()).hexdigest().encode()+
                b'\t'+name.encode()+b'\0' for name in argv[argv.index('--')+1:])
        if argv[:2]==('cat-file','-s'):return str(len(self.blobs[argv[2]])).encode()
        if argv[:2]==('cat-file','blob'):return self.blobs[argv[2]]
        raise AssertionError('unexpected Git reader call '+repr(argv))

    def manifest(self):
        self.events.append('tools')
        if self.late_metadata_fault and self.final_scores==set(m.VARIANTS):self.metadata_dirty=True
        return copy.deepcopy(self.tools)

    def metadata(self,*args):
        self.events.append('metadata')
        if self.metadata_dirty:raise m.p.Rejected('late owned PRL metadata fault')

    def route(self,board,directory,seconds,keep,adapter,profile,*,scoring_variant,comparison_context):
        self.calls.append((scoring_variant,seconds,comparison_context,directory))
        self.assertIs(self.registry[scoring_variant],comparison_context)
        self.assertEqual((board,keep,adapter,profile),(self.board,False,'both','tuned'))
        comparison_context.check();directory.mkdir();(directory/'code').mkdir()
        for name in ('comparison.py','pipeline.py'):
            (directory/'code'/name).write_bytes((self.runtime/'autorouter'/name).read_bytes())
        self.wall+=9.;self.cpu+=12.
        engine=m.p.engine_profile_settings('tuned',seconds,scoring_variant=scoring_variant)
        engine.update(outer_task_wall_budget_seconds=seconds,outer_task_cpu_budget_seconds=seconds)
        step=dict(name='engine',argv=['authored-worker-fixture',*engine['argv']],status='success',exit_code=0,cleanup_complete=True)
        m.p.save_json(directory/'engine-process.json',step)
        negative=self.mode=='negative' or self.mode=='mixed' and len(self.calls)==2
        data=dict(schema=1,source=str(board),source_hashes=dict(self.hashes),tools=copy.deepcopy(self.tools),
            engine_profile=profile,baseline='B2_tuned',adapter=adapter,scoring_variant=scoring_variant,
            scope='whole_board_unlocked_routing',budget_seconds=seconds,cpu_budget_seconds=seconds,
            schematic_parity='checked by final native DRC',status='drc_rejected' if negative else 'routing_accepted',
            accepted=not negative,candidate=str(directory/'candidate'/board.name),candidate_sha256='a'*64,
            native_report_sha256='b'*64,native_rejection_reasons=['native opens=1'] if negative else [],
            native=dict(opens=int(negative),blocking=0,warnings=0,exclusions=0),
            metrics=dict(vias=2,track_length_mm=100.-len(self.calls)),engine_budget=engine,steps=[step])
        if len(self.calls)==2 and self.mode in ('cancelled','unsupported'):data.update(accepted=False,status=self.mode)
        m.cmp.bind(directory,data,comparison_context);m.p.save_json(directory/'result.json',data)
        if len(self.calls)==2 and self.after_second:self.after_second()
        if len(self.calls)==3 and self.after_third:self.after_third()
        return data

    def reader(self,receipt,context,negative):
        self.readers.append((negative,context));self.cpu+=self.read_cost
        key=(negative,context.scoring_variant)
        self.reader_counts[key]=self.reader_counts.get(key,0)+1
        if self.on_reader:self.on_reader(negative,context,self.reader_counts[key])
        if self.reader_error:raise self.reader_error
        data=m.f.read_json(receipt);m.cmp.check_record(receipt.parent,data,context)
        if self.summary_published:self.final_scores.add(context.scoring_variant)
        return data

    def checked(self,receipt,*,comparison_context):
        d=self.reader(receipt,comparison_context,False)
        return dict(current=True,applied=False,candidate=d['candidate'],candidate_sha256=d['candidate_sha256'],production_admitted=False)

    def rejected(self,receipt,*,comparison_context):
        d=self.reader(receipt,comparison_context,True)
        return dict(current=False,applied=False,validated_rejection=True,routing_accepted=False,
            candidate=d['candidate'],candidate_sha256=d['candidate_sha256'],native_report_sha256=d['native_report_sha256'],
            native_rejection_reasons=d['native_rejection_reasons'],receipt_sha256=m.p.sha(receipt),production_admitted=False)

    def run_portfolio(self,**kwargs):
        save=m.p.save_json
        def published(path,data):
            result=save(path,data)
            if (Path(path)==self.output/'portfolio-summary.json'
                    and data.get('status') in ('completed','no_valid_candidate')):
                self.summary_published=True
                if self.after_summary:
                    callback,self.after_summary=self.after_summary,None
                    callback()
            return result
        with patch.object(m.p,'save_json',side_effect=published):
            return m.experiment(self.output,installed_context=self.context,comparison_contexts=self.registry,
                installed_trial_policy=m.INSTALLED_TRIAL_RESERVE_POLICY,allocation='balanced',budget=420.,**kwargs)

    def test_live_contexts_fixed_order_reserved_paths_no_cli_and_winning_delivery_authority(self):
        result=self.run_portfolio();self.assertTrue(result['comparison_eligible'])
        self.assertEqual([x[0] for x in self.calls],list(m.VARIANTS))
        self.assertEqual([x[1] for x in self.calls],[105.,166.5,351.])
        self.assertFalse(result['accepted']);self.assertFalse(result['production_admitted'])
        self.assertEqual(self.events[-3:],['metadata']*3)
        for variant,seconds,context,directory in self.calls:
            self.assertIs(self.registry[variant],context);self.assertEqual(context.scoring_variant,variant)
            self.assertEqual(directory.parent.parent,self.runtime/'.runs');self.assertEqual(directory.name,'route')
            self.assertTrue(directory.parent.name.startswith(m.cmp.PREFIX));self.assertNotIn(self.output,directory.parents)
        winner=self.registry[result['selected']['id']]
        self.assertEqual(m.cmp.delivery_record(winner)['comparison_delivery_context']['route'],result['selected']['result'])
        self.assertTrue(all(context is self.registry[context.scoring_variant] for _,context in self.readers))
        self.assertTrue(all('installed_api' in row and 'installed_cli' not in row for row in result['trials']))

    def test_completed_negative_never_eligible_and_all_three_are_retained(self):
        self.mode='negative';result=self.run_portfolio()
        self.assertEqual(result['status'],'no_valid_candidate');self.assertIsNone(result['selected'])
        self.assertTrue(result['all_variants_attempted'])
        self.assertTrue(all(row['validated_rejection'] and not row['eligible'] for row in result['trials']))
        self.assertTrue(all(negative for negative,_ in self.readers))
        # Classification, initial row, pre-ranking and final private-row replay.
        self.assertEqual(self.reader_counts,{(True,name):4 for name in m.VARIANTS})
        self.assertEqual(self.events[-3:],['metadata']*3)

    def test_mixed_positive_negative_uses_same_live_context_on_late_replays(self):
        self.mode='mixed';result=self.run_portfolio();self.assertTrue(result['comparison_eligible'])
        self.assertTrue(result['trials'][1]['validated_rejection']);self.assertEqual(result['selected']['id'],'via_high')
        self.assertEqual(self.reader_counts[(True,'via_low')],4)

    def test_final_negative_reader_refusal_invalidates_retained_positive(self):
        self.mode='mixed'
        def fail(negative,context,count):
            if negative and count==4:raise m.p.Rejected('final Native rejection readback refused')
        self.on_reader=fail;result=self.run_portfolio()
        self.assertEqual(result['status'],'invalidated');self.assertIsNone(result['selected'])
        self.assertTrue(result['trials'][0]['eligible']);self.assertFalse(result['comparison_eligible'])
        self.assertIn('final Native rejection readback refused',result['reason'])
        self.assertTrue(list(self.output.glob('invalidated-portfolio-summary-*.json')))

    def test_negative_final_publication_source_tamper_cannot_qualify(self):
        self.mode='negative'
        self.after_summary=lambda:self.board.with_suffix('.kicad_pro').write_bytes(b'{"changed":true}')
        result=self.run_portfolio()
        self.assertEqual(result['status'],'invalidated');self.assertIsNone(result['selected'])
        self.assertFalse(result['comparison_eligible']);self.assertEqual(len(self.calls),3)

    def test_later_negative_reader_cannot_tamper_already_replayed_material(self):
        self.mode='negative'
        def tamper(negative,context,count):
            if negative and context.scoring_variant=='via_high' and count==4:
                path=self.registry['via_default'].output/'result.json'
                data=m.f.read_json(path);data['candidate_sha256']='c'*64;m.p.save_json(path,data)
        self.on_reader=tamper;result=self.run_portfolio()
        self.assertEqual(result['status'],'invalidated');self.assertIsNone(result['selected'])
        self.assertFalse(result['comparison_eligible']);self.assertIn('final caller/evidence changed',result['reason'])

    def test_cancel_during_final_negative_replay_is_terminal(self):
        self.mode='negative'
        def cancel(negative,context,count):
            if negative and count==4:raise KeyboardInterrupt
        self.on_reader=cancel;result=self.run_portfolio()
        self.assertEqual(result['status'],'cancelled');self.assertIsNone(result['selected'])
        self.assertFalse(result['comparison_eligible']);self.assertEqual(len(self.calls),3)
        self.assertTrue(list(self.output.glob('invalidated-portfolio-summary-*.json')))
        self.assertFalse(any((context.output.parent/'export').exists() for context in self.registry.values()))

    def test_final_private_negative_replay_still_enforces_trial_cpu_cap(self):
        self.mode='negative';self.read_cost=34.;result=self.run_portfolio()
        self.assertEqual(result['status'],'invalidated');self.assertIsNone(result['selected'])
        self.assertIn('diagnostic readbacks exceeded assigned',result['reason'])
        self.assertGreaterEqual(result['total_cpu_seconds'],12.*3+34.*len(self.readers))

    def test_final_metadata_cost_still_enforces_whole_cpu_cap(self):
        from autorouter import local_settings as local
        self.mode='negative'
        def over_cap(packets,cli):self.cpu=421.
        with patch.object(local,'check_final_events',side_effect=over_cap):result=self.run_portfolio()
        self.assertEqual(result['status'],'budget_exceeded');self.assertIsNone(result['selected'])
        self.assertFalse(result['comparison_eligible']);self.assertEqual(result['total_cpu_seconds'],421.)

    def test_cancel_after_incumbent_is_terminal_without_fallback(self):
        self.mode='cancelled';result=self.run_portfolio()
        self.assertEqual(result['status'],'cancelled')
        self.assertIsNone(result['selected']);self.assertFalse(result['comparison_eligible'])
        self.assertEqual(len(self.calls),2);self.assertTrue(result['trials'][0]['eligible'])

    def test_unsupported_does_not_become_completed_native_failure(self):
        self.mode='unsupported';result=self.run_portfolio()
        self.assertEqual(result['status'],'invalidated');self.assertIsNone(result['selected'])
        self.assertNotIn('validated_rejection',result['trials'][-1]);self.assertEqual(len(self.calls),2)

    def test_missing_replaced_or_wrong_context_refuses_instead_of_receipt_authority(self):
        result=self.run_portfolio();row=result['trials'][0];frozen=m.f.read_json(self.output/'protocol.json')['freeze']
        for context in (None,self.registry['via_high']):
            with self.subTest(context=context),self.assertRaises(m.p.Rejected):
                m.verify_row(row,self.board,frozen,comparison_context=context)
        with self.assertRaises(m.p.Rejected):m.verify_row(row,self.board,frozen)

    def test_registry_change_invalidates_existing_winner(self):
        self.after_second=lambda:self.registry.pop('via_default')
        result=self.run_portfolio();self.assertFalse(result['comparison_eligible']);self.assertIsNone(result['selected'])
        self.assertIn('registry changed',result['reason'])

    def test_stale_source_or_retained_receipt_invalidates_whole_portfolio(self):
        self.after_second=lambda:self.board.with_suffix('.kicad_pro').write_bytes(b'{"changed":true}')
        result=self.run_portfolio();self.assertFalse(result['comparison_eligible']);self.assertIsNone(result['selected'])
        self.assertEqual(len(self.calls),2)

    def test_retained_result_change_after_three_trials_cannot_keep_winner(self):
        def tamper():
            receipt=self.calls[0][3]/'result.json'
            row=m.f.read_json(receipt);row['candidate_sha256']='c'*64;m.p.save_json(receipt,row)
        self.after_third=tamper;result=self.run_portfolio()
        self.assertFalse(result['comparison_eligible']);self.assertIsNone(result['selected'])
        self.assertEqual(len(self.calls),3);self.assertIn('evidence changed',result['reason'])

    def test_combined_context_marker_deletion_cannot_choose_cli_fallback(self):
        def tamper():
            directory=self.calls[0][3];(directory/m.cmp.SIDECAR).unlink()
            row=m.f.read_json(directory/'result.json');row.pop('comparison_route');row.pop('production_admitted')
            m.p.save_json(directory/'result.json',row)
        self.after_third=tamper;result=self.run_portfolio()
        self.assertFalse(result['comparison_eligible']);self.assertIsNone(result['selected'])
        self.assertEqual(len(self.calls),3);self.assertIn('evidence changed',result['reason'])

    def test_reader_refusal_and_readback_cpu_exhaustion_do_not_fallback(self):
        self.after_second=lambda:setattr(self,'reader_error',m.p.Rejected('invalid actual proof fixture'))
        result=self.run_portfolio();self.assertFalse(result['comparison_eligible']);self.assertIsNone(result['selected'])
        self.assertEqual(len(self.calls),2);self.assertTrue(result['trials'][0]['eligible'])

    def test_positive_replay_cost_is_charged_to_assignment_and_whole_cpu(self):
        self.read_cost=70.;result=self.run_portfolio()
        self.assertFalse(result['comparison_eligible']);self.assertIsNone(result['selected'])
        self.assertIn('readbacks exceeded assigned',result['reason'])
        self.assertGreaterEqual(self.cpu,12.*len(self.calls)+70.*len(self.readers))

    def test_shared_cross_root_guard_runs_after_all_material_metadata_helpers(self):
        from autorouter import local_settings as local
        def grouped(packets, cli):
            self.assertEqual(self.events[-3:], ['metadata']*3)
            self.assertEqual(len(packets), 3)
            self.assertEqual(cli, m.c.CLI)
            raise m.p.Rejected('cross-root metadata fault fixture')
        with patch.object(local, 'check_final_events', side_effect=grouped) as replay:
            result = self.run_portfolio()
        replay.assert_called_once()
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
        self.assertIn('cross-root metadata fault fixture', result['reason'])

    def test_final_administration_tool_callback_cannot_escape_metadata_replay(self):
        self.late_metadata_fault=True;result=self.run_portfolio()
        self.assertTrue(self.metadata_dirty);self.assertFalse(result['comparison_eligible']);self.assertIsNone(result['selected'])
        self.assertIn('late owned PRL metadata fault',result['reason'])

    def test_final_tool_readback_does_not_apply_owned_source_file_size_limit(self):
        tool=self.base/'owned-inert-large-tool';tool.write_bytes(b'x'*(m.pv.MAX_FILE_BYTES+1))
        self.tools['files'][str(tool)]=hashlib.sha256(tool.read_bytes()).hexdigest()
        self.context=replace(self.context,tools=copy.deepcopy(self.tools))
        result=self.run_portfolio();self.assertTrue(result['comparison_eligible'])

    def test_retained_administration_drift_cannot_keep_valid_trial_winner(self):
        self.after_third=lambda:(self.output/'frozen-administration/scripts/controller.py').write_bytes(b'changed')
        result=self.run_portfolio();self.assertFalse(result['comparison_eligible']);self.assertIsNone(result['selected'])
        self.assertIn('final administration changed',result['reason'])

    def test_api_choice_output_registry_and_reserve_are_explicit_sealed_requirements(self):
        for changes in ({'comparison_policy':'unknown'}, {'comparison_output':self.runtime/'.runs/ordinary'},
                        {'comparison_policy':None}, {'comparison_output':None}):
            with self.subTest(changes=changes),self.assertRaises(m.p.Rejected):replace(self.context,**changes)
        for extra in ({'comparison_contexts':None},{'comparison_contexts':{'via_default':object()}},
                      {'installed_trial_policy':None}):
            args=dict(installed_context=self.context,comparison_contexts={},installed_trial_policy=m.INSTALLED_TRIAL_RESERVE_POLICY)
            args.update(extra)
            with self.subTest(extra=extra),self.assertRaises(m.p.Rejected):m.experiment(self.output,**args)
        with patch.object(m.c,'NATIVE_VERSION','10.0.0'),self.assertRaises(m.p.Rejected):self.context.check()
        object.__setattr__(self.context,'comparison_policy',None)
        with self.assertRaisesRegex(m.p.Rejected,'expectations changed'):self.context.check()


class PortfolioControllerDiagnosticTests(unittest.TestCase):
    def test_failed_method_is_rejected_before_valid_or_negative_outcome_dispatch(self):
        from scripts import qualify_comparison_portfolio as controller
        failed=dict(status='budget_exceeded',wall_seconds=358.1369,total_cpu_seconds=420.9365,
            wall_budget_seconds=420,cpu_budget_seconds=420,comparison_eligible=False,selected=None)
        with self.assertRaises(ValueError) as caught:controller.require_completed_portfolio(failed)
        self.assertIn('portfolio budget_exceeded',str(caught.exception))
        self.assertIn('CPU=420.9365s',str(caught.exception));self.assertIn('caps wall=420s CPU=420s',str(caught.exception))
        self.assertNotIn('claims routing/delivery acceptance',str(caught.exception))
        failed.update(status='invalidated',reason='late proof changed',comparison_eligible=True)
        with self.assertRaisesRegex(ValueError,'invalidated.*late proof changed'):
            controller.require_completed_portfolio(failed)
        failed['status']='cancelled'
        with self.assertRaises(KeyboardInterrupt):controller.require_completed_portfolio(failed)
        for status in ('completed','no_valid_candidate'):
            controller.require_completed_portfolio(dict(status=status))


if __name__ == '__main__': unittest.main()
