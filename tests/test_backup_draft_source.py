"""The one retained public-source exception never authorizes other content."""
import unittest
from scripts import backup


class AuditedDraftSourceTests(unittest.TestCase):
    def test_exact_audited_path_and_hash_only(self):
        path = '.runs/padstack-policy-draft-001/stage/tests/test_backup.py'
        digest = '39fffc805691665b89433577a633ddc6929b5d0aba13f75c1a66db8ca03cd97a'
        self.assertTrue(backup.audited_nonsecret_test_source(path, digest))
        for changed_path, changed_hash in (
            (path, '0' * 64),
            (path.replace('-001/', '-002/'), digest),
            (path + '.key', digest),
            ('.runs/unrelated.py', digest),
            ('.runs/unrelated.py', None),
        ):
            self.assertFalse(backup.audited_nonsecret_test_source(changed_path, changed_hash))
