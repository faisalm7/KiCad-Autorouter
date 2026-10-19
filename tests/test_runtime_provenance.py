"""Owned tiny Git fixtures; no native tools, downloads, GUI or project Git writes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from autorouter import provenance as pv
from scripts import prepare_runtime as build


class RuntimeProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.source = self.base / "source with spaces ' $(literal)"
        self.source.mkdir()
        for relative in (*pv.FIXED_FILES, 'autorouter/__init__.py',
                         'autorouter/provenance.py', 'autorouter/worker.py'):
            path = self.source / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('# owned fixture ' + relative + '\n').encode())
        self.engine = b'owned fake JAR bytes, never executed\n'
        lock = {'tools': {'freerouting': {'path': pv.ENGINE_PATH,
            'sha256': hashlib.sha256(self.engine).hexdigest(), 'bytes': len(self.engine)}}}
        (self.source / 'toolchain.lock.json').write_text(json.dumps(lock))
        self.git('init', '-q')
        self.git('add', '--', *sorted(pv.owned_snapshot(self.source)))
        self.git('-c', 'user.name=Owned test fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'Owned runtime fixture')
        self.head = pv.git_head(self.source)
        self.output = self.base / 'new runtime'

    def git(self, *arguments):
        return subprocess.run(['git', '-C', str(self.source), *arguments], check=True,
                              capture_output=True, timeout=5).stdout

    def implementation(self, root=None):
        root = self.output if root is None else root
        return {name: pv.file_digest(root / name)[0] for name in pv.module_paths(root)}

    def prepare(self, *, engine=False, output=None):
        return build.prepare(self.source, self.output if output is None else output,
                             copy_local_engine=engine)

    def identity(self):
        return pv.source_identity(self.output, self.implementation())

    def rewrite(self, mutate):
        path = self.output / pv.MANIFEST
        record = json.loads(path.read_text()); mutate(record)
        path.write_text(json.dumps(record))

    def refused(self, function):
        with self.assertRaises((ValueError, OSError)):
            function()

    def test_curated_population_manifest_and_fresh_identity(self):
        # Unrelated archive contents are neither copied nor censused.
        archive = self.source / 'evidence'; archive.mkdir()
        (archive / 'excluded').write_bytes(b'untracked research fixture')
        result = self.prepare()
        identity = self.identity()
        self.assertEqual(identity, result['source_provenance'])
        self.assertEqual(identity['kind'], pv.KIND)
        self.assertEqual(identity['git_head'], self.head)
        self.assertEqual(identity['build_source']['kind'], 'git-checkout')
        self.assertEqual(identity['manifest_sha256'],
                         hashlib.sha256((self.output / pv.MANIFEST).read_bytes()).hexdigest())
        expected = set(pv.owned_snapshot(self.source)) | {pv.README, pv.MANIFEST}
        actual = {str(path.relative_to(self.output)) for path in self.output.rglob('*') if path.is_file()}
        self.assertEqual(actual, expected)
        self.assertFalse(result['standalone']); self.assertFalse(result['published'])
        self.assertFalse((self.output / '.venv').exists())
        self.assertFalse((self.output / '.git').exists())

    def test_explicit_native_profile_is_closed_v2_and_copies_exact_source(self):
        from autorouter import config as c
        lock=json.loads((c.ROOT/'toolchain.lock.json').read_text())
        (self.source/'toolchain.lock.json').write_text(json.dumps(lock))
        self.git('add','toolchain.lock.json')
        self.git('-c','user.name=Owned test fixture','-c','user.email=fixture@example.invalid',
                 'commit','-qm','Owned profile fixture')
        source_bytes=pv.owned_snapshot(self.source)
        result=build.prepare(self.source,self.output,native_version='10.0.7')
        record=json.loads((self.output/pv.MANIFEST).read_text())
        self.assertEqual((record['schema'],record['native_version']),(2,'10.0.7'))
        self.assertEqual(result['source_provenance']['native_version'],'10.0.7')
        for relative,raw in source_bytes.items():
            self.assertEqual((self.output/relative).read_bytes(),raw)
        original=(self.output/pv.MANIFEST).read_bytes()
        changes=[lambda r:r.update(schema=1),lambda r:r.pop('native_version'),
                 lambda r:r.update(native_version=True),lambda r:r.update(native_version='10.0.8'),
                 lambda r:r.update(schema=3)]
        for change in changes:
            (self.output/pv.MANIFEST).write_bytes(original)
            self.rewrite(change);self.refused(self.identity)
        (self.output/pv.MANIFEST).write_bytes(original)
        self.assertEqual(self.identity()['native_version'],'10.0.7')

    def test_unavailable_profile_refuses_before_creating_runtime(self):
        self.refused(lambda:build.prepare(self.source,self.output,native_version='10.0.7'))
        self.assertFalse(self.output.exists())

    def test_missing_extra_changed_files_and_implementation_census_refuse(self):
        self.prepare()
        for target in ('autorouter/worker.py', 'toolchain.lock.json', 'scripts/install_gui.py', 'LICENSE', pv.README):
            with self.subTest(target=target):
                path = self.output / target; original = path.read_bytes()
                path.write_bytes(original + b'changed')
                self.refused(self.identity)
                path.unlink(); self.refused(self.identity); path.write_bytes(original)
        for extra in ('autorouter/new.py', 'autorouter/__pycache__/x', 'scripts/extra.py', 'evidence/x',
                      '.git/x', 'research/x', 'data/x', 'experiments/x', '.tools/extra'):
            with self.subTest(extra=extra):
                path = self.output / extra; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'not in immutable population'); self.refused(self.identity)
                path.unlink()
                if path.parent not in (self.output, self.output / 'autorouter', self.output / 'scripts'):
                    path.parent.rmdir()
        self.refused(lambda: pv.source_identity(self.output, {}))
        self.assertEqual(self.identity()['git_head'], self.head)

    def test_linked_special_and_escaping_paths_refuse(self):
        self.prepare()
        path = self.output / 'autorouter/worker.py'; original = path.read_bytes()
        outside = self.base / 'outside'; outside.write_bytes(original)
        for kind in ('symlink', 'hardlink', 'fifo'):
            with self.subTest(kind=kind):
                path.unlink()
                if kind == 'symlink': path.symlink_to(outside)
                elif kind == 'hardlink': os.link(outside, path)
                else: os.mkfifo(path)
                self.refused(self.identity)
                path.unlink(); path.write_bytes(original)
        folder = self.output / 'scripts'; moved = self.output / 'retained-scripts'
        folder.rename(moved); folder.symlink_to(moved, target_is_directory=True)
        self.refused(self.identity); folder.unlink(); moved.rename(folder)
        alias = self.base / 'alias'; alias.symlink_to(self.output, target_is_directory=True)
        self.refused(lambda: pv.source_identity(alias, self.implementation()))
        self.rewrite(lambda record: record['immutable_files_sha256'].update({'../escape.py': 'a' * 64}))
        self.refused(self.identity)

    def test_manifest_missing_malformed_duplicate_or_invalid_build_source_refuses(self):
        self.prepare(); manifest = self.output / pv.MANIFEST; original = manifest.read_bytes()
        cases = [b'', b'{', b'[]', b'{"schema":1,"schema":1}',
                 b'{"schema":NaN}', b'[' * 2000 + b']' * 2000,
                 b' ' * (pv.MAX_MANIFEST_BYTES + 1)]
        for raw in cases:
            with self.subTest(raw=raw[:50]):
                manifest.write_bytes(raw); self.refused(self.identity)
        manifest.unlink(); self.refused(self.identity); manifest.write_bytes(original)
        changes = [lambda r: r.update(schema=True), lambda r: r.update(kind='git-checkout'),
            lambda r: r.update(unexpected=True), lambda r: r.update(build_source=None),
            lambda r: r['build_source'].update(git_head='not-a-commit'),
            lambda r: r['build_source'].update(kind='ancestor-git'),
            lambda r: r['build_source']['files_sha256'].pop('autorouter/worker.py'),
            lambda r: r['build_source']['files_sha256'].update({'autorouter/worker.py': 'a' * 64}),
            lambda r: r.update(mutable_directories=['.runs', '.venv', 'data'])]
        for index, change in enumerate(changes):
            with self.subTest(change=index):
                manifest.write_bytes(original); self.rewrite(change); self.refused(self.identity)
        manifest.write_bytes(original)
        link = self.base / 'manifest-link'; os.link(manifest, link)
        self.refused(self.identity); link.unlink()
        self.assertEqual(self.identity()['kind'], pv.KIND)

    def test_no_ancestor_git_fallback_and_relocation_refuses(self):
        nested = self.source / 'runtime artifact'
        self.prepare(output=nested)
        implementation = self.implementation(nested)
        identity = pv.source_identity(nested, implementation)
        self.assertEqual(identity['kind'], pv.KIND)
        original = (nested / pv.MANIFEST).read_bytes()
        (nested / pv.MANIFEST).unlink()
        self.refused(lambda: pv.source_identity(nested, implementation))
        (nested / pv.MANIFEST).write_bytes(original)
        moved = self.base / 'moved runtime'; nested.rename(moved)
        self.refused(lambda: pv.source_identity(moved, implementation))

    def test_source_identity_preserves_dirty_behavior_but_builder_requires_head(self):
        path = self.source / 'autorouter/worker.py'; path.write_bytes(b'# intentional dirty source\n')
        identity = pv.source_identity(self.source, self.implementation(self.source))
        self.assertEqual(identity, {'kind': 'git-checkout', 'git_head': self.head,
                                   'build_source': None, 'manifest_sha256': None})
        self.refused(self.prepare); self.assertFalse(self.output.exists())
        # A staged change with worktree bytes restored also fails the clean gate.
        self.git('add', 'autorouter/worker.py')
        path.write_bytes(b'# owned fixture autorouter/worker.py\n')
        self.refused(self.prepare); self.assertFalse(self.output.exists())

    def test_build_requires_exact_source_and_new_destination_without_overwrite(self):
        self.prepare(); before = (self.output / pv.MANIFEST).read_bytes()
        self.refused(self.prepare)
        self.assertEqual((self.output / pv.MANIFEST).read_bytes(), before)
        existing = self.base / 'existing-empty'; existing.mkdir()
        self.refused(lambda: self.prepare(output=existing)); self.assertEqual(list(existing.iterdir()), [])
        alias = self.base / 'alias'; alias.symlink_to(self.base, target_is_directory=True)
        self.refused(lambda: self.prepare(output=alias / 'escaping'))
        self.assertFalse((self.base / 'escaping').exists())
        subdir = self.source / 'nested source'; subdir.mkdir()
        self.refused(lambda: build.prepare(subdir, self.base / 'not-created'))
        self.assertFalse((self.base / 'not-created').exists())

    def test_untracked_new_module_and_linked_selected_source_refuse(self):
        extra = self.source / 'autorouter/untracked.py'; extra.write_bytes(b'# new module\n')
        self.refused(self.prepare); self.assertFalse(self.output.exists()); extra.unlink()
        path = self.source / 'autorouter/worker.py'
        link = self.base / 'source-hardlink'; os.link(path, link)
        self.refused(self.prepare); self.assertFalse(self.output.exists()); link.unlink()
        self.git('update-index', '--assume-unchanged', 'autorouter/worker.py')
        path.write_bytes(b'# concealed dirty source\n')
        self.refused(self.prepare); self.assertFalse(self.output.exists())

    def test_deleted_committed_module_never_shrinks_head_population(self):
        path = self.source / 'autorouter/worker.py'; original = path.read_bytes()
        path.unlink()
        self.refused(self.prepare); self.assertFalse(self.output.exists())
        self.git('update-index', '--force-remove', 'autorouter/worker.py')
        self.refused(self.prepare); self.assertFalse(self.output.exists())
        path.write_bytes(original); self.git('add', 'autorouter/worker.py')
        self.git('update-index', '--assume-unchanged', 'autorouter/worker.py')
        path.unlink()
        self.refused(self.prepare); self.assertFalse(self.output.exists())

    def test_local_engine_explicit_copy_pin_changes_and_tools_population(self):
        engine = self.source / pv.ENGINE_PATH; engine.parent.mkdir(); engine.write_bytes(self.engine)
        result = self.prepare(engine=True)
        self.assertTrue(result['local_engine_copied'])
        self.assertEqual((self.output / pv.ENGINE_PATH).read_bytes(), self.engine)
        self.assertEqual(self.identity()['kind'], pv.KIND)
        target = self.output / pv.ENGINE_PATH; target.write_bytes(self.engine + b'changed')
        self.refused(self.identity); target.write_bytes(self.engine)
        extra = self.output / '.tools/extra'; extra.write_bytes(b'extra')
        self.refused(self.identity); extra.unlink()
        link = self.base / 'engine-hardlink'; os.link(target, link)
        self.refused(self.identity); link.unlink()
        target.unlink(); self.refused(self.identity)
        engine.write_bytes(b'wrong local engine')
        self.refused(lambda: self.prepare(engine=True, output=self.base / 'bad-engine'))
        self.assertFalse((self.base / 'bad-engine').exists())

    def test_only_declared_real_mutable_directories_are_unattested(self):
        self.prepare()
        for name in pv.MUTABLE_DIRECTORIES:
            folder = self.output / name; folder.mkdir()
            (folder / 'caller-state').write_bytes(b'current user state')
        self.assertEqual(self.identity()['kind'], pv.KIND)
        state = self.output / '.runs/caller-state'; state.write_bytes(b'changed state')
        self.assertEqual(self.identity()['kind'], pv.KIND)
        shutil.rmtree(self.output / '.venv')
        (self.output / '.venv').symlink_to(self.base, target_is_directory=True)
        self.refused(self.identity); (self.output / '.venv').unlink()
        (self.output / '.venv').write_bytes(b'not a directory'); self.refused(self.identity)

    def test_actual_cli_refusal_returns_nonzero_without_creating_output(self):
        existing = self.base / 'existing'; existing.mkdir()
        result = subprocess.run([sys.executable, '-B', str(Path(build.__file__)), '--source',
            str(self.source), '--output', str(existing)], capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b'Runtime preparation refused:', result.stderr)
        self.assertEqual(list(existing.iterdir()), [])


    def existing_runtime(self, *, selected=False, extra_module=False):
        # Real small manifest populations, not filler files for a special count.
        if extra_module:
            (self.source / 'autorouter/extra_owned.py').write_bytes(b'def owned_identity(value):\n    return value\n')
        if selected:
            lock_path = Path(build.__file__).resolve().parents[1] / 'toolchain.lock.json'
            lock = json.loads(lock_path.read_text())
            lock['tools']['freerouting'] = {'path': pv.ENGINE_PATH,
                'sha256': hashlib.sha256(self.engine).hexdigest(), 'bytes': len(self.engine)}
            (self.source / 'toolchain.lock.json').write_text(json.dumps(lock))
        if selected or extra_module:
            self.git('add', '--', *sorted(pv.owned_snapshot(self.source)))
            self.git('-c', 'user.name=Owned test fixture', '-c', 'user.email=fixture@example.invalid',
                     'commit', '-qm', 'Owned artifact population or profile')
        engine = self.source / pv.ENGINE_PATH
        engine.parent.mkdir(exist_ok=True); engine.write_bytes(self.engine)
        build.prepare(self.source, self.output, copy_local_engine=True,
                      native_version='10.0.7' if selected else None)
        return hashlib.sha256((self.output / pv.MANIFEST).read_bytes()).hexdigest()

    def test_install_existing_changes_only_root_and_excludes_prior_mutable_state(self):
        previous_population = None
        for label, selected, extra in (('legacy', False, False), ('selected', True, False),
                                       ('added-module', False, True)):
            with self.subTest(label=label):
                self.output = self.base / (label + ' artifact')
                pin = self.existing_runtime(selected=selected, extra_module=extra)
                original_raw = (self.output / pv.MANIFEST).read_bytes()
                original = json.loads(original_raw)
                source_payloads = {name: (self.output / name).read_bytes()
                                   for name in original['immutable_files_sha256']}
                if extra:
                    self.assertEqual(set(source_payloads) - previous_population,
                                     {'autorouter/extra_owned.py'})
                    self.assertTrue(previous_population < set(source_payloads))
                previous_population = set(source_payloads)
                for relative in ('.runs/jobs/old-result', '.runs/old-launcher/entry.py',
                                 '.venv/bin/python'):
                    path = self.output / relative; path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b'excluded mutable state')
                destination = self.base / ('installed ' + label)
                with mock.patch.object(pv, '_git', side_effect=AssertionError('No Git for artifact installs')):
                    result = build.install_existing(self.output, destination, expected_manifest_sha256=pin)
                manifest = json.loads((destination / pv.MANIFEST).read_text())
                self.assertEqual(manifest, {**original, 'root': str(destination)})
                self.assertEqual(set(manifest['immutable_files_sha256']), set(source_payloads))
                for name, raw in source_payloads.items():
                    self.assertEqual((destination / name).read_bytes(), raw)
                    self.assertEqual((self.output / name).read_bytes(), raw)
                self.assertEqual((destination / pv.ENGINE_PATH).read_bytes(), self.engine)
                actual = {str(path.relative_to(destination)) for path in destination.rglob('*')
                          if path.is_file()}
                self.assertEqual(actual, set(source_payloads) | {pv.MANIFEST, pv.ENGINE_PATH,
                                                              build.INSTALL_RECEIPT})
                receipt = json.loads((destination / build.INSTALL_RECEIPT).read_text())
                self.assertEqual(receipt['immutable_files'], len(source_payloads))
                self.assertEqual(receipt['source_manifest_sha256'], pin)
                self.assertEqual(receipt['destination_manifest_sha256'],
                    hashlib.sha256((destination / pv.MANIFEST).read_bytes()).hexdigest())
                self.assertEqual(receipt['installer']['sha256'],
                    hashlib.sha256(Path(build.__file__).read_bytes()).hexdigest())
                self.assertEqual(result['installation_receipt_sha256'],
                    hashlib.sha256((destination / build.INSTALL_RECEIPT).read_bytes()).hexdigest())
                self.assertFalse(receipt['record_is_authoritative'])
                self.assertFalse(receipt['native_qualification_performed'])
                self.assertFalse((destination / '.venv').exists())
                self.assertEqual((self.output / pv.MANIFEST).read_bytes(), original_raw)
                self.assertNotEqual(result['source_provenance']['manifest_sha256'], pin)

    def test_install_existing_requires_exact_manifest_pin_and_local_engine(self):
        pin = self.existing_runtime(); destination = self.base / 'not created'
        for invalid in (None, True, 'A' * 64, 'a' * 63, '0' * 64):
            with self.subTest(pin=invalid):
                self.refused(lambda: build.install_existing(self.output, destination,
                                                            expected_manifest_sha256=invalid))
                self.assertFalse(destination.exists())
        # Even a valid runtime without its local engine refuses this mode.
        no_engine = self.base / 'without engine'
        build.prepare(self.source, no_engine)
        empty_pin = hashlib.sha256((no_engine / pv.MANIFEST).read_bytes()).hexdigest()
        self.refused(lambda: build.install_existing(no_engine, destination,
                                                    expected_manifest_sha256=empty_pin))
        self.assertFalse(destination.exists())
        self.assertEqual(pin, hashlib.sha256((self.output / pv.MANIFEST).read_bytes()).hexdigest())

    def test_install_existing_refuses_moved_changed_and_prohibited_source_entries(self):
        pin = self.existing_runtime(); destination = self.base / 'not created'
        moved = self.base / 'already moved'; self.output.rename(moved)
        self.refused(lambda: build.install_existing(moved, destination, expected_manifest_sha256=pin))
        self.assertFalse(destination.exists()); moved.rename(self.output)
        target = self.output / 'autorouter/worker.py'; original = target.read_bytes()
        target.write_bytes(original + b'changed')
        self.refused(lambda: build.install_existing(self.output, destination, expected_manifest_sha256=pin))
        self.assertFalse(destination.exists()); target.write_bytes(original)
        for relative in ('autorouter/extra.py', 'scripts/launcher.py', 'launcher.py', '.tools/extra'):
            with self.subTest(relative=relative):
                path = self.output / relative; path.write_bytes(b'not in immutable manifest')
                self.refused(lambda: build.install_existing(self.output, destination,
                                                            expected_manifest_sha256=pin))
                self.assertFalse(destination.exists()); path.unlink()

    def test_install_existing_refuses_links_special_inputs_and_destination_collisions(self):
        pin = self.existing_runtime(); destination = self.base / 'not created'
        outside = self.base / 'outside'; outside.write_bytes(self.engine)
        for relative in ('autorouter/worker.py', pv.ENGINE_PATH, pv.MANIFEST):
            path = self.output / relative; original = path.read_bytes()
            for kind in ('symlink', 'hardlink', 'fifo'):
                with self.subTest(relative=relative, kind=kind):
                    path.unlink(); outside.write_bytes(original)
                    if kind == 'symlink': path.symlink_to(outside)
                    elif kind == 'hardlink': os.link(outside, path)
                    else: os.mkfifo(path)
                    self.refused(lambda: build.install_existing(self.output, destination,
                                                                expected_manifest_sha256=pin))
                    self.assertFalse(destination.exists()); path.unlink(); path.write_bytes(original)
        destination.mkdir()
        self.refused(lambda: build.install_existing(self.output, destination, expected_manifest_sha256=pin))
        self.assertEqual(list(destination.iterdir()), [])
        alias = self.base / 'alias'; alias.symlink_to(self.base, target_is_directory=True)
        self.refused(lambda: build.install_existing(self.output, alias / 'escape',
                                                    expected_manifest_sha256=pin))
        self.assertFalse((self.base / 'escape').exists())
        for nested in (self.output / '.runs/new-runtime', self.output / 'new-runtime'):
            nested.parent.mkdir(exist_ok=True)
            self.refused(lambda: build.install_existing(self.output, nested, expected_manifest_sha256=pin))
            self.assertFalse(nested.exists())

    def test_install_existing_late_source_mutation_never_returns_success(self):
        pin = self.existing_runtime(); destination = self.base / 'partial retained'
        writer = build._write_runtime
        def mutate_after_copy(*args):
            result = writer(*args)
            (self.output / 'autorouter/worker.py').write_bytes(b'# late source change\n')
            return result
        with mock.patch.object(build, '_write_runtime', side_effect=mutate_after_copy):
            self.refused(lambda: build.install_existing(self.output, destination,
                                                        expected_manifest_sha256=pin))
        self.assertTrue(destination.exists())
        self.assertFalse((destination / build.INSTALL_RECEIPT).exists())
        self.assertNotEqual((self.output / 'autorouter/worker.py').read_bytes(),
                            (destination / 'autorouter/worker.py').read_bytes())

    def test_install_existing_missing_late_manifest_has_no_git_fallback(self):
        pin = self.existing_runtime(); destination = self.base / 'retained missing-source-manifest'
        writer = build._write_runtime
        def remove_after_copy(*args):
            result = writer(*args)
            (self.output / pv.MANIFEST).unlink()
            return result
        with mock.patch.object(build, '_write_runtime', side_effect=remove_after_copy), \
                mock.patch.object(pv, '_git', side_effect=AssertionError('No Git fallback')):
            self.refused(lambda: build.install_existing(self.output, destination,
                                                        expected_manifest_sha256=pin))
        self.assertTrue(destination.exists())
        self.assertFalse((destination / build.INSTALL_RECEIPT).exists())

    def test_install_existing_post_receipt_faults_refuse_and_retain_non_authoritative_record(self):
        pin = self.existing_runtime()
        source_file = self.output / 'autorouter/worker.py'; original = source_file.read_bytes()
        chmod = Path.chmod
        for fault in ('source', 'destination', 'receipt'):
            with self.subTest(fault=fault):
                destination = self.base / ('post-receipt-' + fault)
                receipt_path = destination / build.INSTALL_RECEIPT
                mutated = []
                def after_receipt(path, *args, **kwargs):
                    result = chmod(path, *args, **kwargs)
                    if path == receipt_path:
                        if fault == 'source':
                            source_file.write_bytes(b'# changed after receipt')
                        elif fault == 'destination':
                            (destination / 'autorouter/worker.py').write_bytes(b'# changed output')
                        else:
                            record = json.loads(receipt_path.read_text())
                            record['injected_change'] = True
                            receipt_path.write_text(json.dumps(record))
                        mutated.append(fault)
                    return result
                with mock.patch.object(Path, 'chmod', new=after_receipt):
                    self.refused(lambda: build.install_existing(self.output, destination,
                                                                expected_manifest_sha256=pin))
                self.assertEqual(mutated, [fault])
                self.assertTrue(receipt_path.is_file())
                receipt = json.loads(receipt_path.read_text())
                self.assertFalse(receipt['record_is_authoritative'])
                self.assertTrue(receipt['receipt_may_remain_on_refusal'])
                self.assertFalse(receipt['native_qualification_performed'])
                self.assertFalse({'accepted', 'completed', 'native_qualified'} & receipt.keys())
                source_file.write_bytes(original)
                # Refused partial destinations are retained and never overwritten.
                self.refused(lambda: build.install_existing(self.output, destination,
                                                            expected_manifest_sha256=pin))
                self.assertTrue(receipt_path.is_file())

    def test_install_existing_cli_refuses_build_flags_and_requires_explicit_mode(self):
        for flags in (['--install-existing', '--copy-local-engine'],
                      ['--install-existing', '--native-version', '10.0.7'],
                      ['--expected-manifest-sha256', 'a' * 64], ['--install-existing']):
            with self.subTest(flags=flags):
                destination = self.base / 'cli not created'
                result = subprocess.run([sys.executable, '-B', str(Path(build.__file__)),
                    '--source', str(self.output), '--output', str(destination), *flags],
                    capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 2)
                self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
