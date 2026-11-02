"""A known synthetic credential-test copy must not weaken backup rejection."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('backup_floor_fixture',ROOT/'scripts/backup.py')
backup=importlib.util.module_from_spec(spec);spec.loader.exec_module(backup)
REL='.runs/board-floor-production-draft-001/tests/test_backup.py'
DIGEST='868a83286a3795d0735b91e23d229d6ac4321b2b96fed83c641ff411879fb05b'

class ExactBackupFixture(unittest.TestCase):
    def check_inventory(self,relative,suffix=b''):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/relative;path.parent.mkdir(parents=True)
            path.write_bytes((ROOT/'tests/test_backup.py').read_bytes()+suffix)
            return backup.inventory(root)
    def test_exact_reviewed_copy_is_preserved(self):
        data=self.check_inventory(REL)
        self.assertEqual(data['files'][0]['path'],REL)
        self.assertEqual(data['files'][0]['sha256'],DIGEST)
    def test_changed_fixture_content_still_rejects(self):
        with self.assertRaisesRegex(backup.BackupError,'Possible credential'):
            self.check_inventory(REL,b'\n')
    def test_identical_content_elsewhere_still_rejects(self):
        with self.assertRaisesRegex(backup.BackupError,'Possible credential'):
            self.check_inventory('.runs/unreviewed/test_backup.py')
