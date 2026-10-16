"""Compact incremental metadata controls; small scratch chains only, no Native."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from scripts import backup

spec = importlib.util.spec_from_file_location('compact_backup_fixture', Path(__file__).with_name('test_backup.py'))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def manifest(directories, files=()):
    rows = [{'path': name, 'size': len(raw), 'sha256': backup.hashlib.sha256(raw).hexdigest()}
            for name, raw in sorted(files)]
    return {'scopes': list(backup.SCOPES),
            'absent_scopes': [name for name in backup.SCOPES if name not in directories],
            'directories': list(directories), 'files': rows,
            'total_file_bytes': sum(row['size'] for row in rows)}


class CompactDeltaInventoryTests(unittest.TestCase):
    def test_legacy_default_and_explicit_policy_preserve_all_target_directories(self):
        # Legacy output shape/order is unchanged, including the absent marker.
        current = manifest(['.runs', '.runs/z', '.runs/a'], [('.runs/a/f', b'old')])
        expected = {**current, 'files': [], 'total_file_bytes': 0}
        legacy = backup.delta_inventory(current, current)
        self.assertNotIn('directory_policy', legacy)
        self.assertEqual(legacy['inventory'], expected)
        explicit = backup.delta_inventory(current, current, directory_policy=backup.DELTA_DIRECTORIES_LEGACY)
        self.assertEqual(explicit, dict(legacy, directory_policy=backup.DELTA_DIRECTORIES_LEGACY))
        backup.check_manifest(explicit['inventory'])

    def test_noop_keeps_only_live_roots_without_repeating_old_empty_branches(self):
        current = manifest(['.runs', '.runs/empty', '.runs/old', '.runs/old/deep', '.data'],
                           [('.runs/old/deep/f', b'old')])
        original = copy.deepcopy(current)
        delta = backup.delta_inventory(current, current, directory_policy=backup.DELTA_DIRECTORIES_COMPACT)
        self.assertEqual(delta['inventory']['directories'], ['.data', '.runs'])
        self.assertEqual(delta['inventory']['absent_scopes'], ['.local-reference'])
        self.assertEqual(delta['inventory']['files'], [])
        self.assertEqual(delta['deleted_files'], [])
        self.assertEqual(delta['deleted_directories'], [])
        self.assertEqual(current, original)
        backup.check_manifest(delta['inventory'])

    def test_changed_nested_files_and_new_empty_directories_include_all_ancestors(self):
        old = manifest(['.runs', '.runs/branch', '.runs/branch/deep', '.runs/untouched', '.data'],
                       [('.runs/branch/deep/f', b'old'), ('.runs/untouched/f', b'stable')])
        current = manifest(old['directories'] + ['.data/new', '.data/new/empty', '.runs/branch/new'],
                           [('.runs/branch/deep/f', b'changed'), ('.runs/untouched/f', b'stable'),
                            ('.runs/branch/new/f', b'new')])
        saved = copy.deepcopy((old, current))
        delta = backup.delta_inventory(old, current, directory_policy=backup.DELTA_DIRECTORIES_COMPACT)
        self.assertEqual(delta['inventory']['directories'],
                         ['.data', '.data/new', '.data/new/empty', '.runs', '.runs/branch',
                          '.runs/branch/deep', '.runs/branch/new'])
        self.assertEqual([row['path'] for row in delta['inventory']['files']],
                         ['.runs/branch/deep/f', '.runs/branch/new/f'])
        self.assertNotIn('.runs/untouched', delta['inventory']['directories'])
        self.assertEqual((old, current), saved)
        backup.check_manifest(delta['inventory'])

    def test_scope_absence_and_nested_deletions_remain_exact(self):
        old = manifest(['.runs', '.runs/remove', '.runs/remove/empty', '.local-reference'],
                       [('.runs/remove/f', b'remove'), ('.local-reference/f', b'remove')])
        current = manifest(['.runs', '.data'])
        delta = backup.delta_inventory(old, current, directory_policy=backup.DELTA_DIRECTORIES_COMPACT)
        self.assertEqual(delta['inventory']['directories'], ['.data', '.runs'])
        self.assertEqual(delta['deleted_files'], ['.local-reference/f', '.runs/remove/f'])
        self.assertEqual(delta['deleted_directories'], ['.local-reference', '.runs/remove', '.runs/remove/empty'])
        self.assertEqual(delta['inventory']['absent_scopes'], ['.local-reference'])
        backup.check_manifest(delta['inventory'])

    def test_unknown_directory_policy_is_refused_before_deriving_a_delta(self):
        current = manifest(['.runs'])
        for value in ('unknown', '', True, 1, [], {}):
            with self.subTest(value=value), self.assertRaisesRegex(backup.BackupError, 'directory policy'):
                backup.delta_inventory(current, current, directory_policy=value)


class CompactDeltaChainTests(unittest.TestCase):
    setUp = fixture.BackupTests.setUp

    def base(self):
        (self.root / '.runs/unchanged/deep').mkdir(parents=True)
        (self.root / '.runs/unchanged/deep/f').write_text('retained')
        (self.root / '.runs/old-empty').mkdir()
        full = backup.create(self.root)
        backup.verify(full, self.root)
        return full

    def write(self, path, value):
        path.write_text(json.dumps(value, sort_keys=True) + '\n')

    def test_individually_valid_receipts_still_obey_aggregate_chain_bound(self):
        full = self.base()
        (self.root / '.runs/new.txt').write_text('retained delta')
        latest = backup.create(self.root, parent=full)
        sizes = [path.stat().st_size for path in (full, latest)]
        pins = [backup.digest(path) for path in (full, latest)]
        with patch.object(backup, 'MAX_RECEIPT_BYTES', max(sizes)):
            with patch.object(backup, 'MAX_CHAIN_RECEIPT_BYTES', sum(sizes)-1):
                with self.assertRaisesRegex(backup.BackupError, 'Chain receipt-memory bound'):
                    backup.load_chain(latest, self.root)
            with patch.object(backup, 'MAX_CHAIN_RECEIPT_BYTES', sum(sizes)):
                self.assertEqual(len(backup.load_chain(latest, self.root)), 2)
        self.assertEqual([backup.digest(path) for path in (full, latest)], pins)

    def test_actual_legacy_then_compact_chain_restores_full_target_and_keeps_base(self):
        full = self.base()
        original = {path.name: path.read_bytes() for path in full.parent.iterdir() if path.is_file()}
        # Exercise an actual schema2 legacy archive/receipt, not a reader mock.
        derive = backup.delta_inventory
        with patch.object(backup, 'delta_inventory', side_effect=lambda old, new, **kw: derive(old, new)):
            legacy = backup.create(self.root, parent=full)
        self.assertNotIn('directory_policy', json.loads(legacy.read_text())['delta'])
        (self.root / '.runs/unchanged/deep/f').write_text('changed')
        (self.root / '.runs/new-empty/deep').mkdir(parents=True)
        (self.root / '.data/board.bin').unlink()
        (self.root / '.local-reference/history.md').unlink()
        (self.root / '.local-reference').rmdir()
        latest = backup.create(self.root, parent=legacy)
        data = json.loads(latest.read_text())
        self.assertEqual(data['delta']['directory_policy'], backup.DELTA_DIRECTORIES_COMPACT)
        self.assertEqual(data['inventory'], backup.inventory(self.root))
        self.assertNotIn('.runs/old-empty', data['delta']['inventory']['directories'])
        self.assertIn('.runs/new-empty/deep', data['delta']['inventory']['directories'])
        self.assertEqual(data['delta']['deleted_files'], ['.data/board.bin', '.local-reference/history.md'])
        self.assertEqual(data['delta']['deleted_directories'], ['.local-reference'])
        checkpoint = json.loads(backup.checkpoint(latest, self.root).read_text())
        self.assertTrue(checkpoint['integrity_checked'])
        result = json.loads(backup.verify(latest, self.root).read_text())
        restored = Path(result['restore_directory']) / 'non-git'
        self.assertTrue(result['verified'])
        self.assertEqual(result['chain_length'], 3)
        self.assertEqual(backup.inventory(restored), data['inventory'])
        self.assertTrue((restored / '.runs/old-empty').is_dir())
        self.assertTrue((restored / '.runs/new-empty/deep').is_dir())
        self.assertEqual((restored / '.runs/unchanged/deep/f').read_text(), 'changed')
        for name, raw in original.items(): self.assertEqual((full.parent / name).read_bytes(), raw)
        self.assertTrue(json.loads(backup.verify(legacy, self.root).read_text())['verified'])

    def test_actual_compact_receipt_fits_scaled_bound_that_legacy_repetition_exceeds(self):
        # A small real analogue of full006's demonstrated metadata-only failure.
        for index in range(40): (self.root / ('.runs/retained-empty-%03d' % index)).mkdir()
        full = self.base()
        latest = backup.create(self.root, parent=full)
        data = json.loads(latest.read_text())
        legacy = copy.deepcopy(data)
        legacy['delta'] = backup.delta_inventory(json.loads(full.read_text())['inventory'], data['inventory'])
        encoded = (json.dumps(legacy, indent=2, sort_keys=True) + '\n').encode()
        finite = max(full.stat().st_size, latest.stat().st_size)
        self.assertGreater(len(encoded), finite)
        counterfactual = latest.parent / 'legacy-counterfactual.json'
        counterfactual.write_bytes(encoded)
        with patch.object(backup, 'MAX_RECEIPT_BYTES', finite):
            self.assertEqual(len(backup.load_chain(latest, self.root)), 2)
            with self.assertRaisesRegex(backup.BackupError, 'size bounds'):
                backup.read_json(counterfactual)

    def test_unknown_null_missing_or_legacy_downgrade_cannot_hide_compact_omissions(self):
        full = self.base()
        latest = backup.create(self.root, parent=full)
        original = json.loads(latest.read_text())
        for value in ('unknown', None, True, [], backup.DELTA_DIRECTORIES_LEGACY, 'missing'):
            data = copy.deepcopy(original)
            if value == 'missing': data['delta'].pop('directory_policy')
            else: data['delta']['directory_policy'] = value
            self.write(latest, data)
            with self.subTest(value=value), self.assertRaises(backup.BackupError):
                backup.load_chain(latest, self.root)
        self.write(latest, original)
        self.assertEqual(len(backup.load_chain(latest, self.root)), 2)

    def test_omitted_empty_dir_or_ancestor_and_extra_old_branch_fail_recomputation(self):
        full = self.base()
        (self.root / '.runs/new-empty/deep').mkdir(parents=True)
        (self.root / '.runs/unchanged/deep/f').write_text('changed')
        latest = backup.create(self.root, parent=full)
        original = json.loads(latest.read_text())
        for name in ('.runs/new-empty/deep', '.runs/new-empty', '.runs/unchanged'):
            data = copy.deepcopy(original)
            data['delta']['inventory']['directories'].remove(name)
            self.write(latest, data)
            with self.subTest(omitted=name), self.assertRaisesRegex(backup.BackupError, 'accounting'):
                backup.load_chain(latest, self.root)
        data = copy.deepcopy(original)
        data['delta']['inventory']['directories'].append('.runs/old-empty')
        data['delta']['inventory']['directories'].sort()
        self.write(latest, data)
        with self.assertRaisesRegex(backup.BackupError, 'accounting'):
            backup.load_chain(latest, self.root)

    def test_rehashed_archive_cannot_omit_required_new_empty_directory(self):
        full = self.base()
        (self.root / '.runs/new-empty/deep').mkdir(parents=True)
        latest = backup.create(self.root, parent=full)
        data = json.loads(latest.read_text())
        archive = latest.parent / 'non-git.tar.gz'
        archive.rename(archive.with_suffix('.held'))
        incomplete = copy.deepcopy(data['delta']['inventory'])
        incomplete['directories'].remove('.runs/new-empty/deep')
        backup.make_archive(self.root, archive, incomplete)
        data['archive'].update(size=archive.stat().st_size, sha256=backup.digest(archive))
        self.write(latest, data)
        with self.assertRaisesRegex(backup.BackupError, 'exactly match inventory'):
            backup.load_chain(latest, self.root)


if __name__ == '__main__': unittest.main()
