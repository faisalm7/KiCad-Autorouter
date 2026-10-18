"""Pure selection/JSON controls; no executable, pcbnew or Native qualification."""
import copy
from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from autorouter import config as c


HASHES7 = (
    '0b9d96dbdac9517e7d85833f926fee07a563549ffe2c55670147bff3f562d01f',
    'fd8c2fa5393bebb9be6789dab8583acee6c5cff90d42696e8c1dbcabe02ec39f',
    '610ae51927809192be637d0de03c32d006332638e2272cbf11a553fe65c75f6e',
)
ROLES = ('kicad_cli', 'kicad_python', 'pcbnew')
SUFFIXES = ('MacOS/kicad-cli', 'Frameworks/Python.framework/Versions/3.9/bin/python3.9',
            'Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/_pcbnew.so')


class NativeProfileControls(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads((c.ROOT / 'toolchain.lock.json').read_text())
        self.lock.pop('native_profiles', None)
        profile = {role: {'path': '/nonexistent/Owned7.app/Contents/' + suffix,
                         'sha256': digest, 'bytes': size}
                   for role, suffix, digest, size in zip(ROLES, SUFFIXES, HASHES7,
                                                        (2104624, 152656, 96205200))}
        self.lock['native_profiles'] = {'10.0.7': profile}
        self.source = Path(c.__file__).read_text()
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        (self.root / 'autorouter').mkdir()
        self.write_lock()

    def write_lock(self, value=None):
        (self.root / 'toolchain.lock.json').write_text(json.dumps(self.lock if value is None else value))

    def manifest(self, **changes):
        value = dict(schema=2, kind='runtime-directory-v1', root=str(self.root), native_version='10.0.7')
        value.update(changes)
        (self.root / 'runtime-distribution.json').write_text(json.dumps(value))

    def load(self):
        module = types.ModuleType('owned_native_profile_fixture')
        module.__file__ = str(self.root / 'autorouter/config.py')
        exec(compile(self.source, module.__file__, 'exec'), module.__dict__)
        return module

    def test_default_and_explicit_profiles_are_fresh_pure_pin_copies(self):
        before = copy.deepcopy(self.lock)
        default = c.native_selection(self.lock)
        self.assertEqual(default, {'version': '10.0.0', 'tools': {role: self.lock['tools'][role] for role in ROLES}})
        self.assertEqual(c.native_selection(self.lock, '10.0.0'), default)
        selected = c.native_selection(self.lock, '10.0.7')
        self.assertEqual(selected['tools'], self.lock['native_profiles']['10.0.7'])
        selected['tools']['pcbnew']['path'] = 'changed return value'
        self.assertEqual(self.lock, before)
        without_profile = copy.deepcopy(self.lock); del without_profile['native_profiles']
        self.assertEqual(c.native_selection(without_profile), default)
        with self.assertRaises(ValueError): c.native_selection(without_profile, '10.0.7')

    def test_unknown_empty_bool_or_unpinned_versions_refuse(self):
        for version in ('', True, False, 1, '10.0.8', '10.0.7 '):
            with self.subTest(version=version), self.assertRaises(ValueError):
                c.native_selection(self.lock, version)
        for version in ('10.0.7', '', True, None):
            value = copy.deepcopy(self.lock); value['kicad'] = version
            with self.subTest(default=version), self.assertRaises(ValueError): c.native_selection(value)

    def test_profiles_and_role_records_are_closed_and_hashes_are_role_specific(self):
        mutations = (
            lambda x: x.update(native_profiles={}),
            lambda x: x['native_profiles'].update({'10.0.8': {}}),
            lambda x: x['native_profiles']['10.0.7'].pop('pcbnew'),
            lambda x: x['native_profiles']['10.0.7'].update(java={}),
            lambda x: x['native_profiles']['10.0.7']['pcbnew'].update(extra=True),
            lambda x: x['native_profiles']['10.0.7']['pcbnew'].update(sha256=HASHES7[0]),
            lambda x: x['tools']['pcbnew'].update(sha256=HASHES7[2]),
            lambda x: x['tools'].update(shell={}),
            lambda x: x['tools'].pop('java'),
            lambda x: x['tools'].pop('freerouting'),
        )
        for mutate in mutations:
            value = copy.deepcopy(self.lock); mutate(value)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError): c.native_selection(value)
        for size in (True, False, 0, -1, 1.5, '10', 128 * 1024**2 + 1):
            value = copy.deepcopy(self.lock); value['native_profiles']['10.0.7']['pcbnew']['bytes'] = size
            with self.subTest(size=size), self.assertRaises(ValueError): c.native_selection(value)

    def test_absolute_canonical_suffix_and_shared_app_bundle_are_required(self):
        for path in ('relative/MacOS/kicad-cli', '/bad//Owned.app/Contents/MacOS/kicad-cli',
                     '/bad/../Owned.app/Contents/MacOS/kicad-cli', '//host/Owned.app/Contents/MacOS/kicad-cli',
                     '/bad/Owned/Contents/MacOS/kicad-cli', '/bad/Owned.app/Contents/MacOS/other',
                     '/other/Owned.app/Contents/MacOS/kicad-cli', '/bad/Owned.app/Contents/MacOS/kicad-cli\n'):
            value = copy.deepcopy(self.lock); value['native_profiles']['10.0.7']['kicad_cli']['path'] = path
            with self.subTest(path=path), self.assertRaises(ValueError): c.native_selection(value, '10.0.7')

    def test_startup_default_v1_and_explicit_v2_bind_role_globals(self):
        default = self.load()
        self.assertEqual(default.NATIVE_VERSION, '10.0.0')
        self.manifest(schema=1); p = self.root / 'runtime-distribution.json'
        value = json.loads(p.read_text()); del value['native_version']; p.write_text(json.dumps(value))
        self.assertEqual(self.load().NATIVE_VERSION, '10.0.0')
        self.manifest(); selected = self.load()
        self.assertEqual(selected.NATIVE_VERSION, '10.0.7')
        self.assertEqual(selected.KICAD, Path('/nonexistent/Owned7.app/Contents'))
        self.assertEqual([str(selected.CLI), str(selected.PYTHON), str(selected.PCBNEW)],
                         [self.lock['native_profiles']['10.0.7'][role]['path'] for role in ROLES])
        self.assertEqual(selected.current_native_selection(), c.native_selection(self.lock, '10.0.7'))

    def test_manifest_schema_version_and_identity_never_silently_fallback(self):
        changes = ({'schema': True}, {'schema': 1.0}, {'schema': 3}, {'schema': 1},
                   {'native_version': ''}, {'native_version': None}, {'native_version': True},
                   {'native_version': '10.0.8'}, {'root': '/different'}, {'kind': 'other'})
        for change in changes:
            self.manifest(**change)
            with self.subTest(change=change), self.assertRaises(ValueError): self.load()
        self.manifest(); p = self.root / 'runtime-distribution.json'; value = json.loads(p.read_text())
        del value['native_version']; p.write_text(json.dumps(value))
        with self.assertRaises(ValueError): self.load()

    def test_duplicate_nonfinite_empty_oversize_and_symlink_json_refuse(self):
        lockpath = self.root / 'toolchain.lock.json'; manifestpath = self.root / 'runtime-distribution.json'
        for path, raw in ((lockpath, b'{"kicad":"10.0.0","kicad":"10.0.0"}'),
                          (lockpath, b'{}'), (lockpath, b''), (lockpath, b' ' * (64 * 1024 + 1)),
                          (manifestpath, b'{"schema":1,"schema":1}'),
                          (manifestpath, b'{"value":NaN}'), (manifestpath, b'{}'),
                          (manifestpath, b' ' * (256 * 1024 + 1))):
            self.write_lock(); manifestpath.unlink(missing_ok=True); path.write_bytes(raw)
            with self.subTest(path=path.name, raw=raw[:40]), self.assertRaises(ValueError): self.load()
        for path in (lockpath, manifestpath):
            self.write_lock(); self.manifest()
            target = path.with_suffix('.saved'); path.rename(target); path.symlink_to(target)
            with self.subTest(symlink=path.name), self.assertRaises(ValueError): self.load()
            path.unlink(); target.rename(path)

    def test_current_read_rejects_selected_pins_manifest_or_cached_global_drift(self):
        for change in ('bytes', 'path', 'hash', 'manifest', 'global_version', 'global_cli'):
            self.write_lock(); self.manifest(); loaded = self.load()
            if change in ('bytes', 'path', 'hash'):
                value = copy.deepcopy(self.lock); profile = value['native_profiles']['10.0.7']
                if change == 'bytes': profile['pcbnew']['bytes'] += 1
                elif change == 'hash': profile['pcbnew']['sha256'] = '0' * 64
                else:
                    for role in ROLES: profile[role]['path'] = profile[role]['path'].replace('/nonexistent/', '/elsewhere/')
                self.write_lock(value)
            elif change == 'manifest': self.manifest(native_version='10.0.0')
            elif change == 'global_version': loaded.NATIVE_VERSION = '10.0.0'
            else: loaded.CLI = loaded.CLI.with_name('other')
            with self.subTest(change=change), self.assertRaises(ValueError): loaded.current_native_selection()
        self.write_lock(); self.manifest(native_version='10.0.0'); loaded = self.load()
        (self.root / 'runtime-distribution.json').unlink()
        with self.assertRaises(ValueError): loaded.current_native_selection()

    def test_fifo_and_hardlinked_selection_files_refuse(self):
        path = self.root / 'toolchain.lock.json'; saved = path.with_suffix('.saved')
        for kind in ('fifo', 'hardlink'):
            path.rename(saved)
            if kind == 'fifo': os.mkfifo(path)
            else: os.link(saved, path)
            with self.subTest(kind=kind), self.assertRaises(ValueError): self.load()
            path.unlink(); saved.rename(path)

    def test_named_file_replacement_during_descriptor_read_refuses(self):
        loaded = self.load(); path = self.root / 'toolchain.lock.json'; raw = path.read_bytes()
        original_fdopen = os.fdopen
        @contextmanager
        def replaced_after_read(*args, **kwargs):
            with original_fdopen(*args, **kwargs) as stream: yield stream
            path.unlink(); path.write_bytes(raw)
        with patch.object(os, 'fdopen', side_effect=replaced_after_read), self.assertRaisesRegex(ValueError, 'changed during read'):
            loaded._strict_json(path, 64 * 1024)


if __name__ == '__main__': unittest.main()
