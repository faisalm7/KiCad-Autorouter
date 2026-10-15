"""Preference publication controls with real files and explicitly mocked workers.

These test cancellation and receipt consistency, never native routing correctness.
The full-checker cases reuse the existing synthetic receipt fixture.
"""
from contextlib import ExitStack
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import tempfile
import time
import unittest
from unittest.mock import patch

from autorouter import adapter, board_floor as g, config as c, floor_route as f
from autorouter import pipeline as p, preferences as pref

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / '.cache'


class FakeWorkerJob:
    """No subprocesses: emit only enough files to reach real publication code."""
    def __init__(self, out, seconds, remaining=None, *, protect_local_settings=False):
        if protect_local_settings is not True:
            raise AssertionError('production publication must request PRL protection')
        self.protect_local_settings = protect_local_settings
        self.out = Path(out); self.out.mkdir(); self.steps = []
        self.started = time.monotonic(); self.deadline = self.started + seconds
        self.cpu_started = time.process_time()

    def drc(self, *args):
        return {'warnings': 0, 'findings': []}

    def step(self, name, argv, *args, **kwargs):
        row = {'name': name, 'argv': [str(arg) for arg in argv], 'cwd': str(self.out),
               'status': 'success', 'exit_code': 0, 'cleanup_complete': True,
               'cpu_seconds': 0.0, 'monitor_cpu_seconds': 0.0, 'wall_seconds': 0.0,
               'max_rss_bytes': 0}
        self.steps.append(row)
        (self.out / (name + '-process.json')).write_text(json.dumps(row))
        (self.out / 'routes.ses').write_text('(session fake)')
        return row

    def native(self, name, mode, *args):
        if mode == 'export': Path(args[1]).write_text('(pcb fake)')
        elif mode == 'import': shutil.copyfile(args[0], args[1])
        elif mode == 'metrics': Path(args[1]).write_text(json.dumps({'version': '10.0.0'}))
        else: raise AssertionError(mode)


class PreferencePublicationTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix='preference-publication-', dir=SCRATCH)
        self.addCleanup(temporary.cleanup); self.root = Path(temporary.name)
        self.count = 0

    def exercise_route(self, guidance='native', mutation=None, overrides=None):
        self.count += 1
        work = self.root / str(self.count); work.mkdir()
        source = work / 'project'; shutil.copytree(ROOT / 'fixtures/smoke', source)
        before = p.tree_hash(source)
        preset = work / 'preset.json'
        choices = dict(pref.DEFAULTS, guidance=guidance,
                       adapter='both' if guidance != 'native' else 'none')
        preset.write_text(json.dumps(choices)); out = work / 'run'
        original_sha, original_save = p.sha, p.save_json
        original_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
        state = {'checked': False, 'triggered': False}

        def validation(job, original, candidate, hashes, protected, **kwargs):
            (job.out / 'final-drc.json').write_text('{}')
            return original_sha(candidate), {'warnings': 0, 'findings': []}

        def context(job, mode, board, **kwargs):
            (job.out / 'native.dsn').write_text('(pcb fake)')
            return {'obstacles': []}

        def checker(path):
            state['checked'] = True
            if mutation == 'canonical_after_checker':
                record = json.loads(Path(path).read_text())
                record['engine_profile'] = 'tuned'; Path(path).write_text(json.dumps(record))
                state['triggered'] = True
            return {'current': True}

        def metadata():
            if mutation == 'preset_during_final_metadata' and state['checked'] and not state['triggered']:
                preset.write_text(json.dumps(dict(choices, seconds=60)))
                state['triggered'] = True
            return {'implementation_sha256': {}}

        def save(path, record):
            original_save(path, record)
            if Path(path) == out / 'result.json' and record.get('accepted') and not state['triggered']:
                if mutation in ('SIGINT', 'SIGTERM'):
                    state['triggered'] = True
                    os.kill(os.getpid(), getattr(signal, mutation))  # This owned test process only.
                elif mutation == 'interrupt_after_positive_write':
                    state['triggered'] = True; raise KeyboardInterrupt('owned control')

        with ExitStack() as stack:
            replacements = [('Job', FakeWorkerJob), ('sha', lambda path: c.JAR_SHA256 if Path(path) == c.JAR else original_sha(path)),
                            ('check_storage', lambda: None), ('tool_manifest', metadata),
                            ('validate_candidate', validation), ('native_rejection_reasons', lambda native: []),
                            ('native_accepted', lambda native: True), ('check_result', checker), ('save_json', save)]
            for name, value in replacements: stack.enter_context(patch.object(p, name, value))
            stack.enter_context(patch.object(f, 'FloorJob', FakeWorkerJob))
            stack.enter_context(patch.object(f, 'acquire_context', context))
            stack.enter_context(patch.object(f, 'policy_contract', return_value=(b'(pcb fake)', {})))
            stack.enter_context(patch.object(g, 'qualify_scope', return_value=None))
            stack.enter_context(patch.object(g, 'verify_chain', return_value=None))
            stack.enter_context(patch.object(adapter, 'adapt_dsn', return_value=[]))
            result = p.route(source / 'smoke.kicad_pcb', out, settings_path=preset,
                             preference_overrides=overrides)
        canonical = json.loads((out / 'result.json').read_text())
        self.assertEqual(p.tree_hash(source), before)
        for sig, handler in original_handlers.items(): self.assertEqual(signal.getsignal(sig), handler)
        if mutation:
            self.assertTrue(state['triggered'])
            self.assertFalse(result['accepted']); self.assertFalse(canonical['accepted'])
            self.assertTrue(list(out.glob('invalidated-result-*')))
        else:
            self.assertTrue(result['accepted'], result)
            self.assertEqual(canonical, result)
        return result, out

    def test_native_and_floor_unchanged_controls_reach_positive_publication(self):
        for policy in ('native', 'board-floors-v1'):
            with self.subTest(policy=policy): self.exercise_route(policy)

    def test_explicit_override_reaches_actual_task_budget_and_engine_argv(self):
        result, out = self.exercise_route(overrides={'seconds': 60, 'scoring_preference': 'via_low'})
        self.assertEqual(result['budget_seconds'], 60)
        self.assertEqual(result['cpu_budget_seconds'], 60)
        self.assertEqual(result['scoring_variant'], 'via_low')
        p.check_preferences_record(out, result)  # Real full argv/settings binder.

    def test_native_keyboard_interrupt_after_positive_write_invalidates(self):
        self.exercise_route(mutation='interrupt_after_positive_write')

    def test_native_actual_self_signals_invalidate_and_restore_handlers(self):
        for sig in ('SIGINT', 'SIGTERM'):
            with self.subTest(signal=sig): self.exercise_route(mutation=sig)

    def test_native_and_floor_canonical_change_at_checker_return_invalidates(self):
        for policy in ('native', 'board-floors-v1'):
            with self.subTest(policy=policy): self.exercise_route(policy, 'canonical_after_checker')

    def test_native_and_floor_late_metadata_preset_change_invalidates(self):
        for policy in ('native', 'board-floors-v1'):
            with self.subTest(policy=policy): self.exercise_route(policy, 'preset_during_final_metadata')

    def receipt_fixture(self):
        spec = importlib.util.spec_from_file_location('_preference_existing_receipt_fixture', ROOT / 'tests/test_result.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        fixture = module.ResultFreshnessTests(); temporary = tempfile.TemporaryDirectory
        with patch.object(module.tempfile, 'TemporaryDirectory', side_effect=lambda **kwargs: temporary(dir=self.root)):
            fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        request = {'captured': None, 'snapshot': pref.snapshot(), 'effective': pref.resolve()}
        p.capture_preferences(fixture.data, fixture.run, request)
        fixture.data.update(adapter='none', engine_profile='standard', scoring_variant=None)
        settings = p.engine_profile_settings('standard', 100)
        settings.update(outer_task_wall_budget_seconds=120, outer_task_cpu_budget_seconds=120)
        process = {'name': 'engine', 'status': 'success', 'exit_code': 0, 'cleanup_complete': True,
                   'argv': p.engine_argv(fixture.run, settings['argv']), 'cwd': str(fixture.run),
                   'wall_seconds': 0, 'cpu_seconds': 0, 'monitor_cpu_seconds': 0}
        # Replace the inherited zero-cost generic engine during setup; the
        # preference-bound process is the sole engine before any late fault.
        fixture.data['steps'] = [row for row in fixture.data['steps'] if row.get('name') != 'engine']
        fixture.data.update(engine_budget=settings); fixture.data['steps'].insert(0, process)
        (fixture.run / 'engine-process.json').write_text(json.dumps(process)); fixture.save_receipt()
        return fixture

    def test_standalone_readback_rechecks_snapshot_and_receipt_after_code_inventory(self):
        for mutation in (None, 'snapshot', 'receipt'):
            with self.subTest(mutation=mutation):
                fixture = self.receipt_fixture(); inventory = p.tree_hash; triggered = []
                def late_inventory(path):
                    value = inventory(path)
                    if mutation and Path(path) == fixture.run / 'code' and not triggered:
                        triggered.append(True)
                        target = fixture.run / ('routing-preferences.json' if mutation == 'snapshot' else 'result.json')
                        if mutation == 'snapshot': target.write_bytes(target.read_bytes() + b' ')
                        else:
                            changed = json.loads(target.read_text()); changed['engine_profile'] = 'tuned'
                            target.write_text(json.dumps(changed))
                    return value
                with patch.object(p, 'tree_hash', late_inventory):
                    if mutation:
                        with self.assertRaises(p.Rejected): p.check_result(fixture.receipt)
                        self.assertTrue(triggered)
                    else: self.assertTrue(p.check_result(fixture.receipt)['current'])

    def test_complete_material_freshness_after_late_code_inventory(self):
        for mutation in ('source_project','candidate_project','snapshot_project','native_report','native_input_project'):
            with self.subTest(mutation=mutation):
                fixture=self.receipt_fixture();inventory=p.tree_hash;triggered=[]
                targets={'source_project':fixture.source.with_suffix('.kicad_pro'),
                    'candidate_project':fixture.candidate.with_suffix('.kicad_pro'),
                    'snapshot_project':(fixture.run/'snapshot'/fixture.source.name).with_suffix('.kicad_pro'),
                    'native_report':fixture.native,
                    'native_input_project':(fixture.run/'final-drc-input'/fixture.source.name).with_suffix('.kicad_pro')}
                def late(path):
                    value=inventory(path)
                    if Path(path)==fixture.run/'code' and not triggered:
                        target=targets[mutation];target.write_bytes(target.read_bytes()+b'\n');triggered.append(True)
                    return value
                with patch.object(p,'tree_hash',late),self.assertRaises(p.Rejected):p.check_result(fixture.receipt)
                self.assertTrue(triggered)

    def test_material_changes_during_final_engine_read_reject(self):
        for mutation in (None,'candidate','task_dsn'):
            with self.subTest(mutation=mutation):
                fixture=self.receipt_fixture();dsn=fixture.run/'task.dsn'
                # Explicit owned setup rebuilds a complete current zero-alias
                # export. The later tested mutation is never repaired.
                from tests.normal_prl_fixture import refresh_authored_normal_export
                refresh_authored_normal_export(fixture.run,fixture.data,test_root=fixture.root)
                fixture.save_receipt()
                read=f.read_json;calls=[];triggered=[]
                def late(path):
                    value=read(path)
                    if Path(path)==fixture.run/'engine-process.json':
                        calls.append(True)
                        # source_all checks both absence of layer flags and the
                        # exact process, twice. Trigger the final fourth read.
                        if mutation and len(calls)==4:
                            target=fixture.candidate if mutation=='candidate' else dsn
                            target.write_bytes(target.read_bytes()+b'\n');triggered.append(True)
                    return value
                with patch.object(f,'read_json',late):
                    if mutation:
                        with self.assertRaises(p.Rejected):p.check_result(fixture.receipt)
                        self.assertTrue(triggered)
                    else:self.assertTrue(p.check_result(fixture.receipt)['current'])


if __name__ == '__main__': unittest.main()
