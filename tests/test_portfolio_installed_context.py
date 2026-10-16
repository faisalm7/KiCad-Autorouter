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
            patch.object(m.p, 'check_storage'), patch.object(m.p, 'check_result', side_effect=self.checked)]
        changes.extend(patch.object(module, '__file__', str(self.runtime / 'autorouter' / Path(module.__file__).name))
                       for module in modules)
        for change in changes: change.start(); self.addCleanup(change.stop)
        self.context = m.InstalledContext(self.runtime, self.board, 'owned-exposed-fixture',
            copy.deepcopy(self.tools), dict(self.source_hashes), self.admin, self.head,
            {name: hashlib.sha256(raw).hexdigest() for name, raw in sources.items()},
            self.admin / 'scripts/controller.py')
        self.wall = self.cpu = 0.; self.calls = []; self.bad_second = None; self.after_second = None
        self.negative_second = False
        self.output = self.runtime / '.runs/new-portfolio'

    def git(self, *arguments):
        return subprocess.run(['git', '-C', str(self.admin), *arguments], capture_output=True,
                              check=True, timeout=5).stdout

    def checked(self, receipt):
        data = json.loads(receipt.read_bytes())
        return {'current': True, 'applied': False, 'candidate': data['candidate'],
                'candidate_sha256': data['candidate_sha256']}

    def receipt(self, directory, assigned, variant):
        directory.mkdir()
        engine = m.p.engine_profile_settings('tuned', assigned, scoring_variant=variant)
        engine.update(outer_task_wall_budget_seconds=assigned, outer_task_cpu_budget_seconds=assigned)
        step = {'name': 'engine', 'argv': ['java', *engine['argv']], 'status': 'success',
                'exit_code': 0, 'cleanup_complete': True}
        m.p.save_json(directory / 'engine-process.json', step)
        data = {'source': str(self.board), 'source_hashes': self.source_hashes, 'tools': self.tools,
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
                data.update(accepted=False, status='drc_rejected')
                m.p.save_json(directory / 'result.json', data)
            if self.after_second: self.after_second()
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

    def test_normal_negative_is_distinguished_but_cannot_bypass_absent_reader(self):
        self.negative_second = True
        result = self.run_portfolio()
        self.assertFalse(result['comparison_eligible']); self.assertIsNone(result['selected'])
        self.assertIn('normal negative routing receipt lacks independent negative reader', result['reason'])
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


if __name__ == '__main__': unittest.main()
