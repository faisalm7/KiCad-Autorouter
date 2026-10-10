"""Actual scratch Git backups plus adversarial archive restoration controls."""
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from scripts import backup


class BackupTests(unittest.TestCase):
    def setUp(self):
        scratch = backup.ROOT / ".cache" / "backup-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        backup.git(self.root, "init", "--quiet")
        backup.git(self.root, "config", "user.name", "Backup Test")
        backup.git(self.root, "config", "user.email", "backup-test@example.invalid")
        (self.root / ".gitignore").write_text(".local-backups/\n.runs/\n.data/\n.local-reference/\n.tools/\n")
        (self.root / "autorouter").mkdir()
        (self.root / "autorouter" / "__main__.py").write_text("print('usage: restored-test')\n")
        backup.git(self.root, "add", ".gitignore", "autorouter/__main__.py")
        backup.git(self.root, "commit", "--quiet", "-m", "fixture")
        for scope in backup.SCOPES:
            (self.root / scope).mkdir()
        (self.root / ".runs" / "literal ; $(ignored).json").write_text('{"native": "evidence"}')
        (self.root / ".data" / "board.bin").write_bytes(b"\0\xffdata")
        (self.root / ".local-reference" / "history.md").write_text("Private historical notes")
        (self.root / ".tools").mkdir()
        (self.root / ".tools" / "excluded").write_text("not in archive")

    def test_full_git_and_non_git_restore_with_cli_smoke(self):
        backup.git(self.root, "branch", "other")
        backup.git(self.root, "tag", "fixture-tag")
        receipt = backup.create(self.root)
        verification = backup.verify(receipt, self.root)
        data = json.loads(verification.read_text())
        self.assertTrue(data["verified"])
        self.assertTrue(data["all_refs_restored"])
        self.assertEqual(data["non_git_files_verified"], 3)
        restored = Path(data["restore_directory"])
        self.assertEqual(backup.inventory(restored / "non-git"), backup.inventory(self.root))
        self.assertFalse((restored / "non-git" / ".tools").exists())
        self.assertIn("disk-failure", data["limitation"])
        again = backup.verify(receipt, self.root)
        self.assertNotEqual(verification, again)
        self.assertTrue(restored.exists())

    def test_uncommitted_source_is_not_omitted_silently(self):
        (self.root / "new-source.py").write_text("unfinished")
        with self.assertRaisesRegex(backup.BackupError, "Commit/audit"):
            backup.create(self.root)

    def test_source_symlink_refused_without_following_it(self):
        (self.root / ".runs" / "outside").symlink_to(self.root / "autorouter")
        with self.assertRaisesRegex(backup.BackupError, "Symlink"):
            backup.inventory(self.root)

    def test_hardlink_refused(self):
        os.link(self.root / ".data" / "board.bin", self.root / ".data" / "linked")
        with self.assertRaisesRegex(backup.BackupError, "Hard-linked"):
            backup.inventory(self.root)

    def test_credentials_refused_by_name_and_private_key_content(self):
        secret = self.root / ".runs" / ".env"
        secret.write_text("do not include")
        with self.assertRaisesRegex(backup.BackupError, "Credential-like"):
            backup.inventory(self.root)
        secret.unlink()
        (self.root / ".runs" / "innocent.log").write_text("-----BEGIN PRIVATE KEY-----")
        with self.assertRaisesRegex(backup.BackupError, "Possible credential"):
            backup.inventory(self.root)

    def test_size_limit_before_snapshot(self):
        with patch.object(backup, "LIMIT", 3):
            with self.assertRaisesRegex(backup.BackupError, "ceiling"):
                backup.create(self.root)

    def test_compressed_writer_limit(self):
        output = io.BytesIO()
        with patch.object(backup, "LIMIT", 3):
            writer = backup.LimitedWriter(output)
            writer.write(b"abc")
            with self.assertRaises(backup.BackupError):
                writer.write(b"d")
        self.assertEqual(output.getvalue(), b"abc")

    def test_corrupt_artifact_refused(self):
        receipt = backup.create(self.root)
        with (receipt.parent / "non-git.tar.gz").open("ab") as stream:
            stream.write(b"corrupt")
        with self.assertRaisesRegex(backup.BackupError, "hash mismatch"):
            backup.verify(receipt, self.root)

    def test_backup_directory_symlink_refused(self):
        (self.root / ".local-backups").symlink_to(self.root / ".tools", target_is_directory=True)
        with self.assertRaisesRegex(backup.BackupError, "symlink"):
            backup.backups_directory(self.root)

    def test_exclusive_receipt_write_preserves_original(self):
        path = self.root / ".runs" / "receipt.json"
        backup.exclusive_json(path, {"original": True})
        with self.assertRaises(FileExistsError):
            backup.exclusive_json(path, {"replacement": True})
        self.assertEqual(json.loads(path.read_text()), {"original": True})

    def test_archive_attacks_rejected_before_destination_created(self):
        manifest = backup.inventory(self.root)
        for index, (name, kind, link) in enumerate([
            ("../escape", tarfile.REGTYPE, ""),
            ("/absolute", tarfile.REGTYPE, ""),
            (".tools/forbidden", tarfile.REGTYPE, ""),
            (".runs/link", tarfile.SYMTYPE, "../../elsewhere"),
            (".runs/link", tarfile.LNKTYPE, ".data/board.bin"),
            (".runs/fifo", tarfile.FIFOTYPE, ""),
        ]):
            with self.subTest(name=name, kind=kind):
                archive = self.root / ".runs" / f"bad-{index}.tgz"
                with tarfile.open(archive, "w:gz") as stream:
                    item = tarfile.TarInfo(name)
                    item.type, item.linkname = kind, link
                    stream.addfile(item)
                destination = self.root / f"never-created-{index}"
                with self.assertRaises(backup.BackupError):
                    backup.restore_archive(archive, destination, manifest)
                self.assertFalse(destination.exists())

    def test_restore_collision_preserves_existing_file(self):
        receipt = backup.create(self.root)
        data = json.loads(receipt.read_text())
        destination = self.root / ".runs" / "existing"
        destination.mkdir()
        (destination / "keep").write_text("original")
        with self.assertRaisesRegex(backup.BackupError, "collision"):
            backup.restore_archive(receipt.parent / "non-git.tar.gz", destination, data["inventory"])
        self.assertEqual((destination / "keep").read_text(), "original")

    def test_file_hash_mismatch_detected_during_restore(self):
        receipt = backup.create(self.root)
        manifest = json.loads(receipt.read_text())["inventory"]
        manifest["files"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(backup.BackupError, "file hash mismatch"):
            backup.restore_archive(receipt.parent / "non-git.tar.gz", self.root / "bad-restore", manifest)

    def test_detached_head_unreachable_from_named_refs_is_restored(self):
        backup.git(self.root, "checkout", "--quiet", "--detach")
        (self.root / "detached-source.txt").write_text("only detached HEAD")
        backup.git(self.root, "add", "detached-source.txt")
        backup.git(self.root, "commit", "--quiet", "-m", "detached change")
        receipt = backup.create(self.root)
        verification = backup.verify(receipt, self.root)
        restored = Path(json.loads(verification.read_text())["restore_directory"])
        self.assertEqual((restored / "checkout" / "detached-source.txt").read_text(), "only detached HEAD")


if __name__ == "__main__":
    unittest.main()
