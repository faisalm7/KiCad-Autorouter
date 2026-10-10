"""Pure source/receipt/publication falsifiers; no compiler, Java, network or CAD."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import tempfile
import types
import unittest
from unittest import mock

HERE = Path(__file__).absolute().parent
spec = importlib.util.spec_from_file_location('padstack_probe_driver', HERE / 'driver.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)


def observed():
    return {'schema': 1, 'scope': 'owned_padstack_import_only', 'units': 'micrometres', 'routing_executed': False,
            'native_executed': False, 'coordinate_transform': [1, 0, 0], 'cases': [
                {'case': name, 'status': 'observed', 'parser_return': True, 'padstack_count': 1,
                 'board_layer_count': 2, 'padstack_name': name, 'input_sha256': d.sha(d.fixtures()[name + '.dsn']),
                 'layers': {layer: None if shape is None else {'class': 'app.freerouting.geometry.planar.IntBox', **copy.deepcopy(shape)}
                            for layer, shape in d.expected()[name].items()}} for name in d.IDS]}


class Controls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=HERE, prefix='test-scratch-'); self.out = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def record(self):
        return {'status': 'completed', 'observations_complete': True, 'expected_observations_match': True,
                'routing_accepted': False, 'custom_pad_support_qualified': False}
    def account(self): pass
    def remaining(self): return 59.0
    def test_fixed_source_polygon_area_and_five_distinct_scopes(self):
        self.assertEqual(d.area(d.CONCAVE), 1350000); self.assertEqual(d.area(d.HULL), 1725000)
        self.assertEqual(d.area(d.CONVEX), 1875000); self.assertEqual(len(d.fixtures()), 5)
        self.assertLess(sum(map(len, d.fixtures().values())), 4096)
        self.assertNotEqual(d.fixtures()['sameAB.dsn'], d.fixtures()['sameBA.dsn'])
        self.assertIn(b'(rect B.Cu', d.fixtures()['distinct.dsn'])
    def test_protocol_exact_static_expectations(self):
        protocol = d.decode(d.content(HERE / 'PROTOCOL.json'))
        self.assertEqual(protocol['expected'], d.expected()); self.assertEqual(protocol['case_ids'], list(d.IDS))
        self.assertEqual(protocol['input_sha256'], {k: d.sha(v) for k, v in d.fixtures().items()})
    def test_positive_and_falsified_hypothesis_distinct(self):
        self.assertTrue(all(x['expected_observation_matches'] for x in d.validate(observed())))
        value = observed(); value['cases'][1]['layers']['F.Cu']['strict_inside']['notch'] = False
        rows = d.validate(value); self.assertFalse(rows[1]['expected_observation_matches'])
        self.assertTrue(rows[0]['expected_observation_matches'])
    def test_wrong_input_and_case_count_reject(self):
        for mutate in (lambda x: x['cases'][1].update(input_sha256='0' * 64), lambda x: x['cases'].pop(),
                       lambda x: x['cases'][0].update(padstack_count=True), lambda x: x.update(routing_executed=True)):
            value = observed(); mutate(value)
            with self.assertRaises(ValueError): d.validate(value)
    def test_numeric_boolean_nonfinite_and_unknown_layer_reject(self):
        for mutate in (lambda x: x['cases'][0]['layers']['F.Cu'].update(area_um2=True),
                       lambda x: x['cases'][0]['layers']['F.Cu'].update(area_um2=float('nan')),
                       lambda x: x['cases'][0]['layers'].update(Other=None),
                       lambda x: x['cases'][0]['layers']['F.Cu']['strict_inside'].update(origin=1)):
            value = observed(); mutate(value)
            with self.assertRaises(ValueError): d.validate(value)
    def test_parser_failure_is_not_empty_geometry(self):
        value = observed(); value['cases'][0] = {'case': 'convex', 'status': 'failed', 'error': 'actual parser failed'}
        with self.assertRaisesRegex(ValueError, 'not observed'): d.validate(value)
    def test_ring_order_not_geometric_change(self):
        value = observed(); points = value['cases'][1]['layers']['F.Cu']['corners_um']; points.reverse()
        self.assertTrue(all(x['expected_observation_matches'] for x in d.validate(value)))
    def test_bounded_files_and_symlink_reject(self):
        p = self.out / 'file'; p.write_bytes(b'1234')
        with self.assertRaises(ValueError): d.content(p, 3)
        (self.out / 'link').symlink_to(p)
        with self.assertRaises(ValueError): d.inventory(self.out)
    def test_strict_json(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}'):
            with self.assertRaises(ValueError): d.decode(raw)
    def test_positive_publication(self):
        result = d.publish(self.out, self.record(), lambda: None, self.account, self.remaining)
        self.assertTrue(result['observations_complete']); self.assertEqual(d.decode(d.content(self.out / 'summary.json')), result)
    def test_final_material_canonical_mutation_rejects(self):
        calls = 0
        def stable():
            nonlocal calls
            calls += 1
            if calls == 2:
                value = d.decode(d.content(self.out / 'summary.json')); value['routing_accepted'] = True; d.write(self.out / 'summary.json', value)
        result = d.publish(self.out, self.record(), stable, self.account, self.remaining)
        self.assertFalse(result['observations_complete']); self.assertFalse(result['routing_accepted'])
        self.assertTrue(list(self.out.glob('invalidated-*')))
    def test_final_material_in_memory_and_cap_reject(self):
        record = self.record(); calls = 0
        def stable():
            nonlocal calls
            calls += 1
            if calls == 2: record['custom_pad_support_qualified'] = True
        result = d.publish(self.out, record, stable, self.account, self.remaining)
        self.assertFalse(result['custom_pad_support_qualified'])
        other = self.out / 'cap'; other.mkdir(); expired = False
        def remaining():
            if expired: raise TimeoutError('final cap')
            return 59
        def late():
            nonlocal expired
            if (other / 'summary.json').exists(): expired = True
        result = d.publish(other, self.record(), late, self.account, remaining)
        self.assertFalse(result['observations_complete'])
    def test_signals_after_positive_and_handler_restoration(self):
        for sig in (signal.SIGINT, signal.SIGTERM):
            out = self.out / str(sig); out.mkdir(); old = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
            def stable():
                if (out / 'summary.json').exists(): os.kill(os.getpid(), sig)
            with d.cancellation(): result = d.publish(out, self.record(), stable, self.account, self.remaining)
            self.assertEqual(result['status'], 'cancelled'); self.assertFalse(result['observations_complete'])
            self.assertEqual(old, {s: signal.getsignal(s) for s in old})
    def test_failed_corrective_write_leaves_no_canonical_positive(self):
        original = d.write; calls = 0
        def write(path, record):
            nonlocal calls
            calls += 1
            if calls > 1: raise OSError('disk error')
            return original(path, record)
        def stable():
            if (self.out / 'summary.json').exists(): raise KeyboardInterrupt('after positive')
        with mock.patch.object(d, 'write', side_effect=write): result = d.publish(self.out, self.record(), stable, self.account, self.remaining)
        self.assertFalse(result['observations_complete']); self.assertFalse((self.out / 'summary.json').exists())
    def test_whole_flow_stage_capture_and_late_source_falsifiers(self):
        for variant in ('unchanged', 'after_parse', 'late_source', 'late_observation',
                        'late_input', 'late_class', 'late_process'):
            with self.subTest(variant=variant):
                root = self.out / variant; root.mkdir(); (root / '.runs').mkdir()
                helper = root / 'experiments/pic_padstack_import_probe_v1'; helper.mkdir(parents=True)
                for name in d.HELPERS: (helper / name).write_bytes((HERE / name).read_bytes())
                (root / 'autorouter').mkdir()
                for name in ('runner.py', '__init__.py'): (root / 'autorouter' / name).write_bytes(b'owned mock runtime source')
                (root / 'toolchain.lock.json').write_bytes(b'{}')
                (root / '.git/refs/heads/rebuild').mkdir(parents=True)
                (root / '.git/HEAD').write_text('ref: refs/heads/rebuild/local-test\n')
                (root / '.git/refs/heads/rebuild/local-test').write_text('1' * 40 + '\n')
                protocol = d.decode(d.content(helper / 'PROTOCOL.json'))
                (root / 'tools').mkdir()
                for name in protocol['tools']:
                    path = root / 'tools' / name; path.write_bytes(b'tool')
                    protocol['tools'][name] = {'path': str(path), 'bytes': 4, 'sha256': d.sha(b'tool')}
                d.write(helper / 'PROTOCOL.json', protocol); batch = root / '.runs/output'
                def git(argv, **kwargs):
                    self.assertEqual(argv[:2], ['git', 'show'])
                    return types.SimpleNamespace(stdout=(root / argv[2].split(':', 1)[1]).read_bytes())
                def worker(argv, *, cwd, log, **kwargs):
                    self.assertEqual(argv[:3], d.SANDBOX)
                    log.write_bytes(b'PURE MOCK STAGE; no Java executed\n')
                    if log.name == 'compile.log': (batch / 'classes/PadstackImportProbe.class').write_bytes(b'fake compiled artifact')
                    else: d.write(batch / 'observations.json', observed())
                    return {'status': 'success', 'exit_code': 0, 'cleanup_complete': True, 'pid': 123, 'argv': argv, 'log': str(log)}
                actual_validate = d.validate; actual_content = d.content; mutated = False
                def validate(value):
                    result = actual_validate(value)
                    if variant == 'after_parse':
                        raw = d.decode(actual_content(batch / 'observations.json')); raw['cases'][1]['input_sha256'] = '0' * 64; d.write(batch / 'observations.json', raw)
                    return result
                def content(path, *args, **kwargs):
                    nonlocal mutated
                    if variant == 'late_source' and Path(path) == root / 'tools/java' and (batch / 'summary.json').exists() and not mutated:
                        (helper / 'driver.py').write_bytes(b'changed after positive summary'); mutated = True
                    targets = {'late_observation': 'observations.json', 'late_input': 'inputs/concave.dsn',
                               'late_class': 'classes/PadstackImportProbe.class', 'late_process': 'import-process.json'}
                    if variant in targets and Path(path) == root / '.git/refs/heads/rebuild/local-test' and (batch / 'summary.json').exists() and not mutated:
                        target = batch / targets[variant]
                        target.write_bytes(target.read_bytes() + b'\n'); mutated = True
                    return actual_content(path, *args, **kwargs)
                with mock.patch.object(d, 'ROOT', root), mock.patch.object(d, 'HERE', helper), mock.patch.object(d.sys, 'executable', str(root / 'tools/python')), \
                     mock.patch.object(d.subprocess, 'run', side_effect=git), mock.patch.object(d.runner, 'run', side_effect=worker), \
                     mock.patch.object(d, 'validate', side_effect=validate), mock.patch.object(d, 'content', side_effect=content):
                    result = d.experiment(batch)
                self.assertEqual(result['observations_complete'], variant == 'unchanged')
                self.assertFalse(result['routing_accepted']); self.assertFalse(result['custom_pad_support_qualified'])
                self.assertEqual(d.decode(actual_content(batch / 'summary.json'))['observations_complete'], variant == 'unchanged')


if __name__ == '__main__': unittest.main(verbosity=2)
