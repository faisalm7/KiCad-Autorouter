"""Actual Mac scratch metadata and focused refusal controls; no historical scans."""
import base64
import ctypes
import hashlib
import gzip
import io
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import retirement_metadata as rm


@unittest.skipUnless(sys.platform == 'darwin', 'Actual macOS ACL/xattr qualification')
class RetirementMetadataTests(unittest.TestCase):
    def setUp(self):
        base = Path(__file__).resolve().parents[1] / '.cache/retirement-metadata-tests'
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base)
        self.home = Path(self.temp.name)
        self.identity = (self.home.stat().st_dev, self.home.stat().st_ino)
        self.addCleanup(self.cleanup_owned_fixture)
        self.source = self.home / 'source'
        self.source.mkdir(mode=0o750)
        (self.source / 'sub').mkdir(mode=0o700)
        self.program = self.source / 'sub' / 'executable with spaces'
        self.payload = b'#!/bin/sh\nexit 0\n'
        self.program.write_bytes(self.payload)
        self.program.chmod(0o751)
        self.record = self.home / 'supplement.json.gz'

    def cleanup_owned_fixture(self):
        # Only this test's newly created tiny directory, never a historical path.
        s = self.home.lstat()
        if not stat.S_ISDIR(s.st_mode) or (s.st_dev, s.st_ino) != self.identity:
            raise RuntimeError('Owned test fixture replaced; retained')
        self.temp.cleanup()

    def catalog(self):
        # Small fixture only. Production capture accepts the existing catalog.
        files, dirs = {}, {}
        for parent, children, names in os.walk(self.source, followlinks=False):
            p = Path(parent)
            dirs[p.relative_to(self.source).as_posix()] = rm._stamp(p.lstat())
            for name in names:
                q = p / name
                files[q.relative_to(self.source).as_posix()] = {
                    'stat': rm._stamp(q.lstat()),
                    'sha256': hashlib.sha256(q.read_bytes()).hexdigest()}
        return files, dirs

    def set_attribute(self, path, name, raw):
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            value = ctypes.create_string_buffer(raw)
            rm._checked(rm._native().fsetxattr(fd, name.encode(), value, len(raw), 0, 0), path, name)
        finally:
            os.close(fd)

    def capture(self):
        files, dirs = self.catalog()
        return rm.capture(self.source, files, dirs, self.record), files, dirs

    def test_actual_mode_acl_xattrs_resource_fork_and_flags_recover(self):
        import pwd
        user = pwd.getpwuid(os.getuid()).pw_name
        subprocess.run(['/bin/chmod', '+a', f'user:{user} allow read,write', str(self.program)], check=True)
        os.chflags(self.program, stat.UF_HIDDEN)
        normal = 'org.kicad.autorouter.retirement-test'
        fork = 'com.apple.ResourceFork'
        self.set_attribute(self.program, normal, b'normal\x00\xffattribute')
        self.set_attribute(self.program, fork, b'actual resource fork\x00\xff')
        self.set_attribute(self.source / 'sub', normal, b'directory attribute')
        result, files, dirs = self.capture()
        self.assertTrue(result['readback_verified'])
        self.assertEqual(stat.S_IMODE(self.record.stat().st_mode), 0o600)
        record = rm.read_record(self.record, result['sha256'])
        row = record['members']['sub/executable with spaces']
        self.assertIn('allow:read,write', row['acl'])
        self.assertEqual(base64.b64decode(row['xattrs_base64'][fork]), b'actual resource fork\x00\xff')
        self.assertEqual(row['identity']['flags'], stat.UF_HIDDEN)
        self.assertEqual(row['identity']['uid'], os.getuid())
        # Observe actual writes, while performing them through the real libc.
        native = rm._native()
        written = []
        class ObservedNative:
            def __getattr__(self, name):
                return getattr(native, name)
            def fsetxattr(self, fd, name, *args):
                written.append(os.fsdecode(name))
                return native.fsetxattr(fd, name, *args)
        with patch.object(rm, '_native', return_value=ObservedNative()):
            restored = rm.recover_small(self.record, result['sha256'], self.home / 'recovered',
                                        {'sub/executable with spaces': self.payload})
        self.assertTrue(restored['verified'])
        self.assertFalse(restored['provenance_replayed'])
        self.assertNotIn(rm.PROVENANCE, written)
        self.assertIn(normal, written)
        self.assertIn(fork, written)
        target = self.home / 'recovered/sub/executable with spaces'
        self.assertEqual(subprocess.run([str(target)], check=False).returncode, 0)
        self.assertEqual(target.read_bytes(), self.payload)
        self.assertTrue(rm.verify_current(self.source, self.record, result['sha256']))
        # Readable provenance, when assigned by macOS, is preserved as bytes.
        with self.program.open('rb') as stream:
            attrs = rm._xattrs(stream.fileno(), self.program)
        self.assertEqual(row['xattrs_base64'].get(rm.PROVENANCE), attrs.get(rm.PROVENANCE))

    def test_hardlink_information_captured_and_new_fixture_links_recovered(self):
        os.link(self.program, self.source / 'linked')
        result, files, dirs = self.capture()
        record = rm.read_record(self.record, result['sha256'])
        a, b = (record['members'][name]['identity'] for name in ['linked', 'sub/executable with spaces'])
        self.assertEqual((a['dev'], a['ino'], a['nlink']), (b['dev'], b['ino'], 2))
        rm.recover_small(self.record, result['sha256'], self.home / 'recovered',
                         {'linked': self.payload, 'sub/executable with spaces': self.payload})
        self.assertEqual((self.home / 'recovered/linked').stat().st_ino,
                         (self.home / 'recovered/sub/executable with spaces').stat().st_ino)
        self.assertTrue(rm.verify_current(self.source, self.record, result['sha256']))

    def test_resource_fork_cap_identifies_exact_path_and_attribute(self):
        self.set_attribute(self.program, 'com.apple.ResourceFork', b'x' * 100)
        with patch.object(rm, 'MAX_ATTRIBUTE_BYTES', 64):
            with self.assertRaises(rm.MetadataError) as error:
                self.capture()
        self.assertIn(str(self.program), str(error.exception))
        self.assertIn('com.apple.ResourceFork', str(error.exception))
        self.assertFalse(self.record.exists())

    def test_total_attribute_cap_identifies_affected_path_and_attribute(self):
        self.set_attribute(self.program, 'org.retirement.payload', b'x' * 100)
        with patch.object(rm, 'MAX_TOTAL_ATTRIBUTE_BYTES', 80):
            with self.assertRaisesRegex(rm.MetadataError, 'total xattr payload') as error:
                self.capture()
        self.assertIn(str(self.program), str(error.exception))
        self.assertIn('org.retirement.payload', str(error.exception))

    def test_unreadable_attribute_refuses_exact_path_and_attribute(self):
        attribute = 'org.retirement.unreadable'
        self.set_attribute(self.program, attribute, b'actual scratch data')
        native = rm._native()
        class DeniedNative:
            def __getattr__(self, name):
                return getattr(native, name)
            def fgetxattr(self, fd, name, *args):
                if os.fsdecode(name) == attribute:
                    ctypes.set_errno(13)
                    return -1
                return native.fgetxattr(fd, name, *args)
        with patch.object(rm, '_native', return_value=DeniedNative()):
            with self.assertRaises(rm.MetadataError) as error:
                self.capture()
        self.assertIn(str(self.program), str(error.exception))
        self.assertIn(attribute, str(error.exception))
        self.assertFalse(self.record.exists())

    def test_changed_catalog_identity_refuses(self):
        files, dirs = self.catalog()
        self.program.chmod(0o700)
        with self.assertRaisesRegex(rm.MetadataError, 'changed after content catalog'):
            rm.capture(self.source, files, dirs, self.record)

    def test_unlisted_child_refuses_even_when_root_stamp_is_current(self):
        files, dirs = self.catalog()
        (self.source / 'extra').write_bytes(b'uncovered')
        dirs['.'] = rm._stamp(self.source.lstat())
        with self.assertRaisesRegex(rm.MetadataError, 'catalog members'):
            rm.capture(self.source, files, dirs, self.record)

    def test_leaf_symlink_not_followed(self):
        files, dirs = self.catalog()
        self.program.unlink()
        self.program.symlink_to(self.record)
        dirs['sub'] = rm._stamp((self.source / 'sub').lstat())
        with self.assertRaises(OSError):
            rm.capture(self.source, files, dirs, self.record)
        self.assertFalse(self.record.exists())

    def test_root_and_output_parent_symlinks_not_followed(self):
        files, dirs = self.catalog()
        alias = self.home / 'alias'
        alias.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(OSError):
            rm.capture(alias, files, dirs, self.record)
        other = self.home / 'other'
        other.symlink_to(self.home, target_is_directory=True)
        with self.assertRaises(OSError):
            rm.capture(self.source, files, dirs, other / 'supplement.json')

    def test_record_cannot_be_inside_source_or_replaced(self):
        files, dirs = self.catalog()
        with self.assertRaisesRegex(rm.MetadataError, 'outside captured root'):
            rm.capture(self.source, files, dirs, self.source / 'record.json')
        self.capture()
        original = self.record.read_bytes()
        with self.assertRaises(FileExistsError):
            rm.capture(self.source, files, dirs, self.record)
        self.assertEqual(self.record.read_bytes(), original)

    def test_changed_supplement_and_current_metadata_refuse(self):
        result, files, dirs = self.capture()
        self.set_attribute(self.program, 'org.retirement.changed', b'after capture')
        with self.assertRaises(rm.MetadataError):
            rm.verify_current(self.source, self.record, result['sha256'])
        with self.record.open('ab') as stream:
            stream.write(b' ')
        with self.assertRaisesRegex(rm.MetadataError, 'SHA256 differs'):
            rm.read_record(self.record, result['sha256'])

    def test_output_is_compact_gzip_and_writer_cap_is_enforced_before_write(self):
        result, _, _ = self.capture()
        self.assertEqual(self.record.read_bytes()[:2], b'\x1f\x8b')
        self.assertEqual(len(gzip.decompress(self.record.read_bytes())), result['decoded_bytes'])
        stream = io.BytesIO()
        writer = rm._RecordWriter(stream, self.record)
        with patch.object(rm, 'MAX_COMPRESSED_RECORD_BYTES', 3):
            writer.write(b'abc')
            with self.assertRaisesRegex(rm.MetadataError, 'compressed supplement'):
                writer.write(b'd')
        self.assertEqual(stream.getvalue(), b'abc')

    def test_catalog_change_during_metadata_capture_is_detected(self):
        collect = rm._metadata
        def change(fd, path):
            result = collect(fd, path)
            if path == self.program:
                self.set_attribute(self.program, 'org.retirement.race', b'changed')
            return result
        with patch.object(rm, '_metadata', side_effect=change):
            with self.assertRaisesRegex(rm.MetadataError, 'changed during metadata capture'):
                self.capture()
        self.assertFalse(self.record.exists())

    def test_recovery_refuses_existing_destination_and_wrong_fixture_content(self):
        result, _, _ = self.capture()
        with self.assertRaises(FileExistsError):
            rm.recover_small(self.record, result['sha256'], self.source,
                             {'sub/executable with spaces': self.payload})
        with self.assertRaisesRegex(rm.MetadataError, 'fixture content'):
            rm.recover_small(self.record, result['sha256'], self.home / 'bad-recovery',
                             {'sub/executable with spaces': b'wrong'})
        self.assertEqual(self.program.read_bytes(), self.payload)


class MetadataCollectionTests(unittest.TestCase):
    def test_non_mac_collection_does_not_require_posix_account_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('metadata_non_mac_collection', __file__)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'pwd': None}), patch.object(sys, 'platform', 'win32'):
            spec.loader.exec_module(module)
        self.assertTrue(module.RetirementMetadataTests.__unittest_skip__)


if __name__ == '__main__':
    unittest.main()
