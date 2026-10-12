"""Reuse legacy adversarial controls, plus finite-profile/shared-material checks."""
from pathlib import Path
import importlib.util
import json
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = Path(__file__).absolute().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from experiments.licensed_acquisition_v1 import fetch as f
from experiments.licensed_acquisition_v1 import test_fetch as legacy


class SharedProfileControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=HERE, prefix='test-scratch-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / '.git').mkdir()
        (self.root / '.git/HEAD').write_text('0' * 40)
        (self.root / '.data').mkdir()
        (self.root / '.data/original').write_bytes(b'original')
        (self.root / '.runs').mkdir()
        self.here = self.root / f.profile('v2')['directory']
        for name, source in f.material_paths(ROOT, HERE, 'v2').items():
            target = f.material_paths(self.root, self.here, 'v2')[name]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        self.recorded = {path.relative_to(self.root).as_posix(): path.read_bytes()
                         for path in f.material_paths(self.root, self.here, 'v2').values()}
        self.plan, self.original, self.rows = f.load(self.here, 'v2')
        self.baseline = f.inventory(self.root / '.data')
        self.out = self.root / '.runs/output'

    def git(self, root, args):
        if args == ['rev-parse', 'HEAD']:
            return b'0' * 40
        return self.recorded[args[1].split(':', 1)[1]]

    def transport(self, row, rec, path, allowance, remaining):
        remaining()
        raw = b'data'
        path.write_bytes(raw)
        rec.update(received_bytes=len(raw), response_sha256=f.sha(raw))
        return raw

    def run_small(self):
        row = dict(self.rows[0], bytes=4,
                   git_blob_sha1=f.hashlib.sha1(b'blob 4\0data').hexdigest(), sha256=None)
        runtime = f.committed(self.root, self.here, 'v2')
        return f.acquire(self.root, self.here, self.out, self.plan, self.baseline,
                         [row], runtime, time.monotonic(), self.transport, 'v2')

    def test_exact_v2_profile_and_full_scope(self):
        self.assertEqual((len(self.rows), sum(r['bytes'] for r in self.rows)), (14, 2163350))
        self.assertEqual((self.original['file_count'], self.original['bytes']), (345, 37408570))
        self.assertEqual(self.original['bytes'] + self.plan['planned_bytes'], 39571920)
        self.assertEqual({r['mode'] for r in self.rows}, {'100644'})
        self.assertEqual(sum(r['sha256'] is not None for r in self.rows), 3)
        self.assertIn('paw3395_pcb.pretty/PAW3395.kicad_mod', {r['source_path'] for r in self.rows})
        with self.assertRaisesRegex(ValueError, 'scope'):
            f.validate_protocol(self.plan, self.original)
        with self.assertRaisesRegex(ValueError, 'protocol pin'):
            f.load(self.here)

    def test_wrapper_selects_only_v2_without_cli_profile(self):
        spec = importlib.util.spec_from_file_location('__main__', HERE / 'fetch.py')
        with mock.patch.object(f, 'main') as main:
            spec.loader.exec_module(importlib.util.module_from_spec(spec))
        main.assert_called_once_with('v2', HERE)

    def test_committed_includes_both_shared_files(self):
        with mock.patch.object(f, 'git', side_effect=self.git):
            runtime = f.committed(self.root, self.here, 'v2')
        self.assertEqual(set(runtime['files']), set(f.MATERIAL) | {'shared/fetch.py', 'shared/test_fetch.py'})
        for name in ('fetch.py', 'test_fetch.py'):
            self.assertEqual(runtime['files']['shared/' + name], f.sha((ROOT / f.profile()['directory'] / name).read_bytes()))
        with self.assertRaisesRegex(ValueError, 'promoted'):
            f.committed(self.root, self.here, 'v1')

    def test_v2_positive_preserves_legacy_directory(self):
        with mock.patch.object(f, 'git', side_effect=self.git):
            record = self.run_small()
        self.assertEqual(record['status'], 'acquired_unqualified')
        self.assertEqual(record['protocol_sha256'], f.profile('v2')['protocol_sha256'])
        self.assertTrue((self.root / '.data/expansion005/paw3395/.gitignore').is_file())
        self.assertFalse((self.root / '.data/expansion004').exists())
        self.assertEqual((self.root / '.data/original').read_bytes(), b'original')
        self.assertFalse(record['dependency_closure_verified'])

    def test_shared_files_changed_during_last_git_show(self):
        for changed in ('fetch.py', 'test_fetch.py'):
            with self.subTest(changed=changed):
                target = self.root / f.profile()['directory'] / changed
                original = target.read_bytes()
                def late(root, args):
                    returned = self.git(root, args)
                    if args[0] == 'show' and args[1].endswith('/licensed_acquisition_v1/test_fetch.py'):
                        target.write_bytes(b'changed shared source')
                    return returned
                with mock.patch.object(f, 'git', side_effect=late), self.assertRaisesRegex(ValueError, 'after metadata'):
                    f.committed(self.root, self.here, 'v2')
                target.write_bytes(original)

    def test_shared_file_changed_during_final_head_witness(self):
        calls = 0
        actual = f.git_identity
        def witness(root):
            nonlocal calls
            value = actual(root)
            calls += 1
            if calls == 2:
                (self.root / f.profile()['directory'] / 'fetch.py').write_bytes(b'changed at final HEAD witness')
            return value
        with mock.patch.object(f, 'git', side_effect=self.git), mock.patch.object(f, 'git_identity', side_effect=witness), self.assertRaisesRegex(ValueError, 'after metadata'):
            f.committed(self.root, self.here, 'v2')

    def test_final_head_witness_cannot_rebase_data_or_response(self):
        for case in ('original', 'acquired', 'response'):
            with self.subTest(case=case):
                fixture = SharedProfileControls()
                fixture.setUp()
                try:
                    calls = 0
                    fired = False
                    actual = f.git_identity
                    def witness(root):
                        nonlocal calls, fired
                        value = actual(root)
                        receipt = fixture.out / 'receipt.json'
                        if receipt.exists() and json.loads(receipt.read_bytes()).get('status') == 'acquired_unqualified':
                            calls += 1
                            # The final material() witness follows committed()'s two samples.
                            if calls == 3:
                                target = {'original': fixture.root / '.data/original',
                                          'acquired': fixture.root / '.data/expansion005/paw3395/.gitignore',
                                          'response': fixture.out / 'response-000.bin'}[case]
                                target.write_bytes(b'changed')
                                fired = True
                        return value
                    with mock.patch.object(f, 'git', side_effect=fixture.git), mock.patch.object(f, 'git_identity', side_effect=witness):
                        with self.assertRaises(ValueError):
                            fixture.run_small()
                    self.assertTrue(fired)
                    saved = json.loads((fixture.out / 'receipt.json').read_bytes())
                    self.assertEqual(saved['status'], 'failed')
                    self.assertFalse(saved['original_inputs_unchanged'])
                    self.assertTrue((fixture.out / 'receipt.invalidated.json').is_file())
                finally:
                    fixture.doCleanups()

    def test_final_output_scan_shared_and_profile_material(self):
        targets = ('shared/fetch.py', 'shared/test_fetch.py', 'fetch.py', 'protocol.json')
        for index, name in enumerate(targets):
            with self.subTest(name=name):
                self.out = self.root / '.runs' / ('output-' + str(index))
                # Reusing the controller with a fresh synthetic baseline includes prior outcomes.
                self.baseline = f.inventory(self.root / '.data')
                if (self.root / '.data/expansion005').exists():
                    # Each earlier failed case acquired only this disposable four-byte fake file.
                    previous = self.root / '.data/expansion005'
                    previous.rename(self.root / '.data' / ('preserved-failure-' + str(index)))
                    self.baseline = f.inventory(self.root / '.data')
                target = f.material_paths(self.root, self.here, 'v2')[name]
                original = target.read_bytes()
                actual = f.inventory
                changed = False
                def scan(path, *args, **kwargs):
                    nonlocal changed
                    if path == self.out and not changed:
                        target.write_bytes(b'changed during publication scan')
                        changed = True
                    return actual(path, *args, **kwargs)
                with mock.patch.object(f, 'git', side_effect=self.git), mock.patch.object(f, 'inventory', side_effect=scan), self.assertRaises(ValueError):
                    self.run_small()
                self.assertTrue(changed)
                self.assertEqual(json.loads((self.out / 'receipt.json').read_text())['status'], 'failed')
                target.write_bytes(original)


def load_tests(loader, tests, pattern):
    tests.addTests(loader.loadTestsFromTestCase(legacy.Controls))
    return tests


if __name__ == '__main__':
    unittest.main(verbosity=2)
