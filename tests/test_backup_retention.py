"""Small actual Git/tar reconstruction and new-owned scratch retention guards."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import backup, verification_scratch as scratch

spec = importlib.util.spec_from_file_location('retention_backup_fixture', Path(__file__).with_name('test_backup.py'))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class ManagedBackup(unittest.TestCase):
    setUp = fixture.BackupTests.setUp

    def test_default_full_restoration_removes_only_new_verified_copy(self):
        old = self.root / '.local-backups/restore-historical'
        old.mkdir(parents=True); (old / 'unique').write_bytes(b'preserved old work')
        receipt = backup.create(self.root)
        before = {p.name: p.read_bytes() for p in receipt.parent.iterdir() if p.is_file()}
        with patch.object(scratch, 'active_users', return_value=[]):
            proof = backup.verify(receipt, self.root)
            second = backup.verify(receipt, self.root)
        for name, value in before.items(): self.assertEqual((receipt.parent / name).read_bytes(), value)
        for path in (proof, second):
            data = json.loads(path.read_text())
            self.assertTrue(data['verified'])
            self.assertEqual(data['workspace_policy'], 'new-owned-disposable')
            self.assertFalse(Path(data['restore_directory']).exists())
            removed = json.loads(Path(data['workspace_removal_receipt']).read_text())
            self.assertTrue(removed['removed'])
            self.assertEqual(removed['success_record'], str(path))
        self.assertEqual((old / 'unique').read_bytes(), b'preserved old work')

    def test_removed_full_copy_is_not_a_dependency_of_new_delta(self):
        full = backup.create(self.root)
        with patch.object(scratch, 'active_users', return_value=[]):
            base_proof = backup.verify(full, self.root)
            self.assertFalse(Path(json.loads(base_proof.read_text())['restore_directory']).exists())
            (self.root / '.runs/new-evidence').write_text('new successful or failed evidence')
            delta = backup.create(self.root, parent=full)
            integrity = backup.checkpoint(delta, self.root)
            final = backup.verify(delta, self.root)
        self.assertTrue(json.loads(integrity.read_text())['integrity_checked'])
        self.assertFalse(Path(json.loads(integrity.read_text())['scratch_directory']).exists())
        self.assertTrue(json.loads(final.read_text())['full_restoration_tested'])
        self.assertEqual(backup.load_chain(delta, self.root)[-1]['path'], delta)

    def test_explicit_required_pin_retains_inspectable_fixture_and_is_declared(self):
        receipt = backup.create(self.root)
        proof = backup.verify(receipt, self.root, pinned_reason='required small fixture inspection')
        data = json.loads(proof.read_text())
        self.assertEqual(data['workspace_policy'], 'pinned-required')
        self.assertTrue(Path(data['restore_directory']).is_dir())
        self.assertEqual(data['pinned_reason'], 'required small fixture inspection')
        for reason in ('', ' ', True):
            with self.subTest(reason=reason), self.assertRaises(backup.BackupError):
                backup.verify(receipt, self.root, pinned_reason=reason)

    def test_unique_work_after_success_is_retained_and_blocks_next_job(self):
        receipt = backup.create(self.root)
        publish = backup.publish_check
        def late(path, result, stable):
            publish(path, result, stable)
            (Path(result['restore_directory']) / 'unique-late-evidence').write_text('do not delete')
        with patch.object(backup, 'publish_check', side_effect=late), patch.object(scratch, 'active_users', return_value=[]):
            with self.assertRaisesRegex(backup.BackupError, 'cleanup refused'):
                backup.verify(receipt, self.root)
        retained = self.root / '.local-backups/verification-workspace'
        self.assertEqual((retained / 'unique-late-evidence').read_text(), 'do not delete')
        with self.assertRaisesRegex(scratch.ScratchError, 'slot retained'):
            backup.verify(receipt, self.root)

    def test_restored_git_ignored_file_or_unique_object_cannot_be_covered_blindly(self):
        receipt = backup.create(self.root)
        proof = backup.verify(receipt, self.root, pinned_reason='inspect only small fixture')
        checkout = Path(json.loads(proof.read_text())['restore_directory']) / 'checkout'
        data = json.loads(receipt.read_text()); config = backup.digest(checkout / '.git/config')
        generated = backup._generated_git_metadata(checkout)
        (checkout / '.runs').mkdir(); (checkout / '.runs/unique').write_text('later work')
        with self.assertRaisesRegex(backup.BackupError, 'Unique or modified'):
            backup._checkout_expected(checkout, data, config, generated)
        (checkout / '.runs/unique').unlink(); (checkout / '.runs').rmdir()
        # Actual unreachable object creation, not a mocked fsck result.
        subprocess.run(['git', 'hash-object', '-w', '--stdin'], cwd=checkout, input=b'unique uncommitted object', check=True, capture_output=True)
        with self.assertRaisesRegex(backup.BackupError, 'metadata changed|Unreachable/unique'):
            backup._checkout_expected(checkout, data, config, generated)

    def test_canonical_git_metadata_added_by_smoke_is_never_blindly_covered(self):
        receipt = backup.create(self.root)
        run = backup.subprocess.run
        def smoke(command, **kwargs):
            result = run(command, **kwargs)
            if len(command) >= 4 and command[:4] == [sys.executable, '-B', '-m', 'autorouter']:
                extra = Path(kwargs['cwd']) / '.git/objects/pack' / ('pack-' + '0' * 40 + '.rev')
                extra.write_bytes(b'unique later metadata')
            return result
        with patch.object(backup.subprocess, 'run', side_effect=smoke), patch.object(scratch, 'active_users', return_value=[]):
            with self.assertRaisesRegex(backup.BackupError, 'metadata changed'):
                backup.verify(receipt, self.root)
        extra = self.root / '.local-backups/verification-workspace/checkout/.git/objects/pack' / ('pack-' + '0' * 40 + '.rev')
        self.assertEqual(extra.read_bytes(), b'unique later metadata')

    def test_git_config_symlink_is_refused_before_any_git_reader(self):
        receipt = backup.create(self.root)
        proof = backup.verify(receipt, self.root, pinned_reason='small no-follow fixture inspection')
        checkout = Path(json.loads(proof.read_text())['restore_directory']) / 'checkout'
        config_hash = backup.digest(checkout / '.git/config')
        generated = backup._generated_git_metadata(checkout)
        outside = self.root / 'unrelated-config'; outside.write_text('must not read')
        (checkout / '.git/config').unlink(); (checkout / '.git/config').symlink_to(outside)
        with patch.object(backup, 'git', side_effect=AssertionError('Git reader must not run')):
            with self.assertRaises(scratch.ScratchError):
                backup._checkout_expected(checkout, json.loads(receipt.read_text()), config_hash, generated)
        self.assertEqual(outside.read_text(), 'must not read')

    def test_orphan_reverse_index_before_metadata_capture_is_preserved(self):
        receipt = backup.create(self.root)
        capture = backup._generated_git_metadata
        injected = []
        def changed(checkout):
            extra = checkout / '.git/objects/pack' / ('pack-' + '0' * 40 + '.rev')
            extra.write_bytes(b'unique before metadata capture'); injected.append(extra)
            return capture(checkout)
        with patch.object(backup, '_generated_git_metadata', side_effect=changed):
            with self.assertRaisesRegex(backup.BackupError, 'reverse-index'):
                backup.verify(receipt, self.root)
        self.assertEqual(injected[0].read_bytes(), b'unique before metadata capture')
        self.assertTrue((self.root / '.local-backups/verification-workspace').is_dir())

    def test_peak_budget_accounts_for_stage_directory_accumulation_without_allocating_it(self):
        receipt = backup.create(self.root)
        with patch.object(scratch, 'active_users', return_value=[]): backup.verify(receipt, self.root)
        (self.root / '.runs/new').mkdir(); (self.root / '.runs/new/evidence').write_text('new')
        delta = backup.create(self.root, parent=receipt)
        chain = backup.load_chain(delta, self.root)
        plan = backup.restore_space_plan(self.root, chain)
        self.assertGreaterEqual(plan['peak_temporary_bytes'], backup.manifest_allocation(chain[-1]['receipt']['inventory']))
        self.assertEqual(plan['required_free_bytes'], plan['peak_temporary_bytes'] + backup.SPACE_RESERVE)
        usage = backup.shutil.disk_usage(self.root)
        with patch.object(backup.shutil, 'disk_usage', return_value=usage._replace(free=backup.SPACE_RESERVE + 100)):
            self.assertEqual(backup.require_headroom(self.root, 100, 'small')['required_free_bytes'], backup.SPACE_RESERVE + 100)
            with self.assertRaisesRegex(backup.BackupError, 'Insufficient headroom'):
                backup.require_headroom(self.root, 101, 'small')

    def test_self_contained_bundle_recovery_does_not_require_original_git_objects(self):
        receipt = backup.create(self.root)
        original = self.root / '.git'; retained = self.root / 'original-git-held-for-fixture'
        original.rename(retained)
        try:
            with patch.object(scratch, 'active_users', return_value=[]): proof = backup.verify(receipt, self.root)
            data = json.loads(proof.read_text())
            self.assertTrue(data['verified'])
            self.assertEqual(data['git_import_space_plan']['operation'], 'Git bundle import')
            self.assertEqual(data['space_plan']['operation'], 'full restoration')
            self.assertFalse(original.exists())
            self.assertFalse(Path(data['restore_directory']).exists())
        finally:
            retained.rename(original)

    def test_second_space_gate_precedes_checkout_and_payload_materialization(self):
        receipt = backup.create(self.root); require = backup.require_headroom
        def gate(root, peak_bytes, operation):
            if operation == 'full restoration': raise backup.BackupError('deliberate second-stage headroom refusal')
            return require(root, peak_bytes, operation)
        with patch.object(backup, 'require_headroom', side_effect=gate):
            with self.assertRaisesRegex(backup.BackupError, 'second-stage headroom refusal'):
                backup.verify(receipt, self.root)
        work = self.root / '.local-backups/verification-workspace'
        self.assertTrue((work / 'checkout/.git/objects/pack').is_dir())
        self.assertFalse((work / 'checkout/autorouter').exists())
        self.assertFalse((work / 'non-git').exists())


class ScratchControls(unittest.TestCase):
    def setUp(self):
        base = backup.ROOT / '.cache/retention-tests'; base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def prepare(self):
        lease = scratch.claim(self.root, 'small fixture')
        (lease.path / 'payload').write_bytes(b'independently retained bytes')
        expected = {'files': {'payload': {'size': 28, 'sha256': backup.digest(lease.path / 'payload')}}, 'directories': []}
        self.assertEqual((lease.path / 'payload').stat().st_size, 28)
        proof = lease.records / (lease.token + '-proof.json')
        proof.write_text(json.dumps({'verified': True}))
        return lease, expected, proof

    def dispose(self, lease, expected, proof, **kwargs):
        return scratch.dispose(lease, expected, success_record=proof,
                               reconstruction={'source': 'actual fixture outside scratch'}, **kwargs)

    def test_single_slot_and_valid_removal_leave_compact_records(self):
        lease, expected, proof = self.prepare()
        with self.assertRaisesRegex(scratch.ScratchError, 'slot retained'): scratch.claim(self.root, 'second')
        with patch.object(scratch, 'active_users', return_value=[]): removed = self.dispose(lease, expected, proof)
        self.assertTrue(removed.is_file()); self.assertTrue(proof.is_file()); self.assertFalse(lease.path.exists())
        self.assertEqual(json.loads(removed.read_text())['logical_bytes'], 28)

    def test_unknown_and_modified_files_are_not_deleted(self):
        for kind in ('extra', 'modified'):
            with self.subTest(kind=kind):
                root = self.root / kind; root.mkdir()
                lease = scratch.claim(root, 'refusal fixture')
                payload = lease.path / 'payload'; payload.write_bytes(b'original')
                expected, _ = scratch.manifest(lease.path)
                proof = lease.records / 'proof.json'; proof.write_text('{"verified":true}')
                if kind == 'extra': (lease.path / 'unique').write_bytes(b'new failed evidence')
                else: payload.write_bytes(b'modified')
                with patch.object(scratch, 'active_users', return_value=[]), self.assertRaisesRegex(scratch.ScratchError, 'Unique/modified'):
                    self.dispose(lease, expected, proof)
                self.assertTrue(payload.is_file())

    def test_active_and_dependency_required_files_are_not_deleted(self):
        lease, expected, proof = self.prepare()
        with patch.object(scratch, 'active_users', return_value=['123']), self.assertRaisesRegex(scratch.ScratchError, 'Active process'):
            self.dispose(lease, expected, proof)
        with patch.object(scratch, 'active_users', return_value=[]), self.assertRaisesRegex(scratch.ScratchError, 'required recovery'):
            self.dispose(lease, expected, proof, required_paths=[lease.path / 'payload'])
        with patch.object(scratch, 'active_users', return_value=[]), self.assertRaisesRegex(scratch.ScratchError, 'required recovery'):
            self.dispose(lease, expected, proof, required_paths=[lease.path.parent])
        self.assertTrue((lease.path / 'payload').is_file())

    def test_symlink_dependency_alias_refuses_deletion(self):
        lease, expected, proof = self.prepare()
        alias = self.root / 'outside-alias'; alias.symlink_to(lease.path, target_is_directory=True)
        with patch.object(scratch, 'active_users', return_value=[]), self.assertRaisesRegex(scratch.ScratchError, 'Symlink'):
            self.dispose(lease, expected, proof, required_paths=[alias / 'payload'])
        self.assertTrue((lease.path / 'payload').is_file())

    def test_empty_directory_replacement_after_coverage_is_not_deleted(self):
        lease = scratch.claim(self.root, 'directory identity fixture')
        (lease.path / 'empty').mkdir()
        expected, _ = scratch.manifest(lease.path)
        proof = lease.records / 'proof.json'; proof.write_text('{"verified":true}')
        publish = scratch._json
        def replace(path, result):
            publish(path, result)
            if path.name.endswith('-covered.json'):
                (lease.path / 'empty').rename(lease.path / 'earlier-empty')
                (lease.path / 'empty').mkdir()
        with patch.object(scratch, '_json', side_effect=replace), patch.object(scratch, 'active_users', return_value=[]):
            with self.assertRaisesRegex(scratch.ScratchError, 'directory identity changed'):
                self.dispose(lease, expected, proof)
        self.assertTrue((lease.path / 'empty').is_dir())
        self.assertTrue((lease.path / 'earlier-empty').is_dir())

    def test_symlink_out_of_scope_forged_and_failed_proof_refused(self):
        lease, expected, proof = self.prepare()
        proof.write_text('{"verified":false}')
        with self.assertRaisesRegex(scratch.ScratchError, 'Successful verification'): self.dispose(lease, expected, proof)
        proof.write_text('{"verified":true}')
        outside = self.root / 'original'; outside.write_text('original remains')
        (lease.path / 'payload').unlink(); (lease.path / 'payload').symlink_to(outside)
        with self.assertRaises(scratch.ScratchError): self.dispose(lease, expected, proof)
        self.assertEqual(outside.read_text(), 'original remains')
        forged = scratch.Lease(self.root, lease.records, lease.token, lease.device, lease.inode, os.getpid())
        with self.assertRaisesRegex(scratch.ScratchError, 'creating process'): self.dispose(forged, expected, proof)
        with self.assertRaises(scratch.ScratchError): scratch.claim(self.root / '.local-backups/verification-workspace', 'nested')

    def test_mutation_by_late_callback_is_detected_before_any_deletion(self):
        lease, expected, proof = self.prepare()
        def mutate(): (lease.path / 'payload').write_text('new work')
        with patch.object(scratch, 'active_users', return_value=[]), self.assertRaisesRegex(scratch.ScratchError, 'changed before disposal'):
            self.dispose(lease, expected, proof, stable=mutate)
        self.assertEqual((lease.path / 'payload').read_text(), 'new work')

    def test_success_record_mutation_by_callback_refuses_all_deletion(self):
        lease, expected, proof = self.prepare()
        def mutate(): proof.write_text('{"verified":false}')
        with patch.object(scratch, 'active_users', return_value=[]), self.assertRaisesRegex(scratch.ScratchError, 'record changed'):
            self.dispose(lease, expected, proof, stable=mutate)
        self.assertEqual((lease.path / 'payload').read_bytes(), b'independently retained bytes')

    @unittest.skipUnless(sys.platform in ('darwin', 'linux'), 'actual process probe qualified on Mac/POSIX only')
    def test_actual_open_process_file_is_detected(self):
        lease, expected, proof = self.prepare()
        child = subprocess.Popen([sys.executable, '-B', '-c',
            'import sys,time; f=open(sys.argv[1],"rb"); print("open",flush=True); time.sleep(20)', str(lease.path / 'payload')],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), 'open')
            self.assertIn(str(child.pid), scratch.active_users(lease.path))
            with self.assertRaisesRegex(scratch.ScratchError, 'Active process'):
                self.dispose(lease, expected, proof)
        finally:
            child.terminate(); child.communicate(timeout=5)


if __name__ == '__main__': unittest.main()
