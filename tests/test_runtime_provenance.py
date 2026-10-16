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


if __name__ == '__main__':
    unittest.main()
