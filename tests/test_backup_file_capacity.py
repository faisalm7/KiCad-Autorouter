"""A finite file ceiling still constrains capture and restoration manifests."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import backup

class FileCapacityControls(unittest.TestCase):
    def test_capture_and_restore_both_reject_one_file_over_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'.runs').mkdir()
            for name in ('one','two'):(root/'.runs'/name).write_text(name)
            with patch.object(backup,'MAX_FILES',2):
                manifest=backup.inventory(root)
                self.assertEqual(len(backup.check_manifest(manifest)[0]),2)
            with patch.object(backup,'MAX_FILES',1):
                with self.assertRaisesRegex(backup.BackupError,'ceiling'):backup.inventory(root)
                with self.assertRaisesRegex(backup.BackupError,'size'):backup.check_manifest(manifest)
