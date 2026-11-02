"""Prevent accidental repeated full archives; fixtures create no real backup."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import backup


class CapturePolicy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / '.runs')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.prior = self.root / '.local-backups/checkpoint-fixture/receipt.json'
        self.prior.parent.mkdir(parents=True)
        self.prior.write_text('{}')

    def call(self, args):
        err, out = io.StringIO(), io.StringIO()
        with patch.object(backup, 'ROOT', self.root), patch('sys.argv', ['backup.py', *args]), \
             patch.object(backup, 'create', return_value=self.prior) as create, \
             patch.object(backup, 'verify', return_value=self.root / 'proof.json') as verify, \
             patch.object(backup, 'checkpoint', return_value=self.root / 'integrity.json') as checkpoint, \
             contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            code = backup.main()
        return code, create, verify, checkpoint, err.getvalue()

    def test_existing_checkpoint_refuses_implicit_full_before_any_capture(self):
        code, create, verify, checkpoint, error = self.call([])
        self.assertEqual(code, 2)
        for operation in (create, verify, checkpoint): operation.assert_not_called()
        self.assertIn('--incremental', error)
        self.assertIn('Existing checkpoints retained', error)

    def test_explicit_incremental_uses_parent_and_integrity_path(self):
        code, create, verify, checkpoint, error = self.call(['--incremental', str(self.prior)])
        self.assertEqual(code, 0, error)
        create.assert_called_once_with(parent=str(self.prior))
        verify.assert_not_called()
        checkpoint.assert_called_once_with(self.prior)

    def test_explicit_full_requires_nonempty_bounded_milestone_reason(self):
        for reason in ('', ' ' * 3, 'x' * 513):
            with self.subTest(reason_length=len(reason)):
                code, create, verify, checkpoint, error = self.call(['--full', reason])
                self.assertEqual(code, 2)
                create.assert_not_called()
        code, create, verify, checkpoint, error = self.call(['--full', 'reviewed milestone fixture'])
        self.assertEqual(code, 0, error)
        verify.assert_called_once_with(self.prior)
        checkpoint.assert_not_called()

    def test_retained_slot_blocks_verification_before_archive_reads(self):
        slot = self.root / '.local-backups/verification-workspace'
        slot.mkdir()
        (slot / 'unfinished').write_text('unique work retained')
        for operation in (backup.verify, backup.checkpoint):
            with self.subTest(operation=operation.__name__), patch.object(backup, 'load_chain') as load:
                with self.assertRaisesRegex(backup.scratch.ScratchError, 'Existing verification slot'):
                    operation(self.prior, self.root)
                load.assert_not_called()
        self.assertEqual((slot / 'unfinished').read_text(), 'unique work retained')


if __name__ == '__main__': unittest.main()
