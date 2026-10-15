"""Native-pruning preference freshness and final-publication regressions.

Reuse the established synthetic receipt builder and actual full checker. The
incumbent's journals/settings are real files, and no checker/worker is mocked.
These controls prove local consistency only; they are not native routing proof.
"""
import ast
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from autorouter import config as c, floor_route as f, pipeline as p, preferences as pref, strategy as s
from autorouter.handoff import capture_destination, owned_destination
from tests import test_result as receipt_support

ROOT = Path(__file__).resolve().parents[1]


class PruningPreferenceFreshness(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / '.cache'
        scratch.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)

    def fixture(self, scoring=None):
        case = receipt_support.ResultFreshnessTests(methodName='runTest')
        original_temporary = tempfile.TemporaryDirectory
        with patch.object(receipt_support.tempfile, 'TemporaryDirectory',
                          side_effect=lambda **kwargs: original_temporary(dir=self.workspace)):
            case.setUp()
        self.addCleanup(case.doCleanups)
        run, data = case.run, case.data
        # Isolate preference consistency from the separate edge-transport
        # module. Every retained implementation file still matches its pin.
        (run / 'code/native_edge.py').unlink()
        del data['tools']['implementation_sha256']['autorouter/native_edge.py']
        incumbent = run / 'incumbent'
        # The current captured producer requires a real owned direct-import
        # population. Copy the complete software fixture, then rebase only its
        # owned journal paths; no old producer declaration is removed or faked.
        retained = list(run.iterdir())
        incumbent.mkdir()
        for path in retained:
            if path.is_dir():
                shutil.copytree(path, incumbent / path.name)
            else:
                shutil.copy2(path, incumbent / path.name)

        def rebase(value):
            if isinstance(value, str):
                if value == str(run):
                    return str(incumbent)
                return str(incumbent) + value[len(str(run)):] if value.startswith(str(run) + '/') else value
            if isinstance(value, list):
                return [rebase(row) for row in value]
            if isinstance(value, dict):
                return {key: rebase(row) for key, row in value.items()}
            return value

        for path in incumbent.rglob('*.json'):
            record = f.read_json(path)
            rebased = rebase(record)
            if rebased != record:
                p.save_json(path, rebased)
        inc = rebase(copy.deepcopy(data))
        inc.update(adapter='both', engine_profile='tuned', scoring_variant=scoring)
        from tests.normal_prl_fixture import refresh_authored_normal_import
        refresh_authored_normal_import(incumbent, inc, test_root=case.root)
        settings = p.engine_profile_settings('tuned', 90, scoring_variant=scoring)
        settings.update(outer_task_wall_budget_seconds=120, outer_task_cpu_budget_seconds=120)
        engine = dict(name='engine', cwd=str(incumbent), argv=p.engine_argv(incumbent, settings['argv']),
                      status='success', exit_code=0, cleanup_complete=True,
                      wall_seconds=0, cpu_seconds=0, monitor_cpu_seconds=0)
        p.save_json(incumbent / 'engine-process.json', engine)
        inc.update(steps=[engine] + inc['steps'], engine_budget=settings)
        p.save_json(incumbent / 'result.json', inc)
        # C derives its candidate from that child and has only its own final
        # Native stage. Keep every nested worker/proof, without claiming that
        # C itself exported/imported the same candidate a second time.
        final_steps = [row for row in data['steps'] if row['name'] == 'final-drc']
        self.assertEqual(len(final_steps), 1)
        for name in ('imported.kicad_pcb', 'imported.routes-only.ses', 'imported.routes-only.json',
                     'routes.ses', 'import-process.json', 'pre-refill.kicad_pcb',
                     'refill-drc.json', 'refill-drc-binding.json', 'refill-drc-process.json'):
            (run / name).unlink()
        shutil.rmtree(run / 'refill')
        del data['protected_route_import']
        data.update(strategy='native_validated_zone_net_pruning', baseline='C-prototype',
                    adapter='both', engine_profile='tuned',
                    steps=[dict(row, phase='incumbent') for row in inc['steps']] + final_steps,
                    wall_seconds=4, child_cpu_seconds=2, monitor_cpu_seconds=0.2, total_cpu_seconds=2.4)
        preset = case.root / 'settings.json'
        preset.write_text(json.dumps(dict(pref.DEFAULTS, adapter='both', profile='tuned', scoring_preference=scoring)))
        case.captured = pref.load(preset)
        snapshot = run / 'pruning-preferences.json'
        snapshot.write_bytes(pref.snapshot(case.captured))
        data.update(pruning_preferences_policy=s.PRUNING_PREFERENCES_POLICY,
                    pruning_preferences=dict(file=snapshot.name, sha256=p.sha(snapshot),
                                             effective=s.pruning_preferences(case.captured)))
        if scoring is not None:
            marker = run / 'pruning-scoring.json'
            p.save_json(marker, dict(schema=1, strategy=data['strategy'], incumbent_scoring_variant=scoring))
            data.update(incumbent_scoring_variant=scoring,
                        incumbent_receipt_sha256=p.sha(incumbent / 'result.json'),
                        incumbent_scoring_contract=dict(file=marker.name, sha256=p.sha(marker)))
        case.save_receipt()
        return case

    def mutate(self, case, mutation):
        paths = {
            'preferences': case.run / 'pruning-preferences.json',
            'native-report': case.native,
            'source-project': case.source.with_suffix('.kicad_pro'),
            'source-rules': case.source.with_suffix('.kicad_dru'),
            'candidate-project': case.candidate.with_suffix('.kicad_pro'),
            'candidate-rules': case.candidate.with_suffix('.kicad_dru'),
            'snapshot-project': (case.run / 'snapshot' / case.source.name).with_suffix('.kicad_pro'),
            'snapshot-rules': (case.run / 'snapshot' / case.source.name).with_suffix('.kicad_dru'),
            'native-input-project': (case.run / 'final-drc-input' / case.source.name).with_suffix('.kicad_pro'),
            'receipt': case.receipt,
        }
        target = paths[mutation]
        if mutation.endswith('rules'):
            target.write_text('(version 1)\n')
        elif mutation.endswith('project'):
            target.write_text('{"board":{"design_settings":{"rules":{"min_clearance":0.001}}}}')
        elif mutation == 'native-report':
            record = f.read_json(target); record['included_severities'] = []
            p.save_json(target, record)
        elif mutation == 'receipt':
            record = f.read_json(target); record['engine_profile'] = 'standard'
            p.save_json(target, record)
        else:
            target.write_bytes(target.read_bytes() + b' ')

    def late_inventory(self, case, mutation, triggered):
        inventory = p.tree_hash
        def late(path):
            value = inventory(path)
            if Path(path) == case.run / 'code' and not triggered:
                triggered.append(True)
                self.mutate(case, mutation)
            return value
        return late

    def publish(self, case, remaining=lambda: 100):
        # Compile the producer's actual closures so this regression follows
        # future final-freshness changes instead of duplicating their behavior.
        tree = ast.parse((ROOT / 'autorouter/strategy.py').read_text())
        producer = next(row for row in tree.body if isinstance(row, ast.FunctionDef) and row.name == 'prune')
        closures = [row for row in producer.body if isinstance(row, ast.FunctionDef)
                    and row.name in ('original_fresh', 'stable')]
        self.assertEqual(len(closures), 2)
        owner = {}; capture_destination(owner, case.run)
        env = dict(owned_destination=owned_destination, owner=owner, pref=pref, captured=case.captured,
                   report=case.data, output=case.run, source=case.source, p=p, c=c, _check_original=s._check_original)
        exec(compile(ast.fix_missing_locations(ast.Module(body=closures, type_ignores=[])),
                     str(ROOT / 'autorouter/strategy.py'), 'exec'), env)
        # Fixed accounting isolates freshness; the already consistent synthetic
        # records do not establish task timing or native compute.
        return f.publish(case.run, case.data, env['stable'], lambda: None, remaining,
                         owned=lambda: owned_destination(owner))

    def test_default_and_explicit_scoring_roots_remain_current(self):
        for scoring in (None, 'via_high'):
            with self.subTest(scoring=scoring):
                case = self.fixture(scoring)
                self.assertTrue(p.check_result(case.receipt)['current'])
                before = p.tree_hash(case.root)
                self.assertTrue(p.check_result(case.receipt)['current'])
                self.assertEqual(p.tree_hash(case.root), before)

    def test_each_late_material_mutation_rejects_full_readback(self):
        for mutation in ('preferences', 'native-report', 'source-project', 'source-rules', 'candidate-project',
                         'candidate-rules', 'snapshot-project', 'snapshot-rules', 'native-input-project', 'receipt'):
            with self.subTest(mutation=mutation):
                case = self.fixture(); triggered = []
                with patch.object(p, 'tree_hash', self.late_inventory(case, mutation, triggered)):
                    with self.assertRaises(p.Rejected):
                        p.check_result(case.receipt)
                self.assertTrue(triggered)

    def test_publication_preserves_positive_and_invalidates_each_late_mutation(self):
        case = self.fixture()
        self.assertTrue(self.publish(case)['accepted'])
        self.assertTrue(f.read_json(case.receipt)['accepted'])
        for mutation in ('preferences', 'native-report', 'source-project', 'source-rules', 'candidate-project',
                         'candidate-rules', 'snapshot-project', 'snapshot-rules', 'native-input-project', 'receipt'):
            with self.subTest(mutation=mutation):
                case = self.fixture(); triggered = []
                with patch.object(p, 'tree_hash', self.late_inventory(case, mutation, triggered)):
                    report = self.publish(case)
                self.assertTrue(triggered)
                self.assertFalse(report['accepted'])
                self.assertFalse(f.read_json(case.receipt)['accepted'])
                self.assertTrue(list(case.run.glob('invalidated-result-*')))

    def test_late_publication_budget_expiry_invalidates(self):
        case = self.fixture()
        report = self.publish(case, remaining=lambda: 0)
        self.assertFalse(report['accepted'])
        self.assertFalse(f.read_json(case.receipt)['accepted'])
        self.assertIn('budget exceeded', report['reason'])

    def test_preference_markers_cannot_hide_unrecognized_root_strategy(self):
        case = self.fixture()
        del case.data['strategy']; case.save_receipt()
        with self.assertRaises(p.Rejected):
            p.check_result(case.receipt)


if __name__ == '__main__':
    unittest.main()
