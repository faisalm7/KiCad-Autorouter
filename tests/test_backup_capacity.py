"""Bounded capacity arithmetic and small-file guards; no archive/Git/native work."""
import io,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts import backup

class BackupCapacity(unittest.TestCase):
    def manifest(self,size):
        return {'scopes':list(backup.SCOPES),'directories':['.runs'],
                'files':[{'path':'.runs/evidence.bin','size':size,'sha256':'0'*64}],
                'total_file_bytes':size}
    def test_exact_finite_capacity_and_existing_population(self):
        self.assertEqual(backup.LIMIT,9*1024**3);self.assertEqual(backup.MAX_FILES,280000)
        self.assertEqual(backup.MAX_RECEIPT_BYTES,80*1024**2)
        self.assertEqual(backup.MAX_CHAIN_RECEIPT_BYTES,192*1024**2)
        self.assertEqual(backup.SCOPES,('.runs','.data','.local-reference'))
    def test_previous_one_gib_inventory_still_valid(self):
        for size in (0,1017693214,1024**3):
            with self.subTest(size=size):self.assertEqual(backup.check_manifest(self.manifest(size))[0]['.runs/evidence.bin']['size'],size)
    def test_previous_range_and_exact_new_boundary_without_allocation(self):
        for size in (1024**3+1,2*1024**3,2*1024**3+1,3*1024**3,4*1024**3,4*1024**3+1,5*1024**3,backup.LIMIT):
            with self.subTest(size=size):backup.check_manifest(self.manifest(size))
        with self.assertRaises(backup.BackupError):backup.check_manifest(self.manifest(backup.LIMIT+1))
    def test_stream_guard_rejects_first_byte_over_new_boundary(self):
        output=io.BytesIO();writer=backup.LimitedWriter(output);writer.size=backup.LIMIT-1
        self.assertEqual(writer.write(b'x'),1);self.assertEqual(writer.size,backup.LIMIT)
        with self.assertRaisesRegex(backup.BackupError,'configured byte ceiling'):writer.write(b'y')
        self.assertEqual(output.getvalue(),b'x')
    def test_file_count_guard_unchanged_at_scaled_boundary(self):
        manifest=self.manifest(0);manifest['files'].append({'path':'.runs/other.bin','size':0,'sha256':'0'*64})
        with patch.object(backup,'MAX_FILES',1),self.assertRaises(backup.BackupError):backup.check_manifest(manifest)
    def test_invalid_manifest_bytes_still_reject(self):
        for size in (-1,True,1.5):
            with self.subTest(size=size),self.assertRaises(backup.BackupError):backup.check_manifest(self.manifest(size))
        manifest=self.manifest(4);manifest['total_file_bytes']=3
        with self.assertRaises(backup.BackupError):backup.check_manifest(manifest)
    def test_actual_small_inventory_still_stops_before_large_snapshot(self):
        scratch=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(dir=scratch)as name:
            root=Path(name);(root/'.runs').mkdir();(root/'.runs/data.txt').write_bytes(b'abcd')
            with patch.object(backup,'LIMIT',3),self.assertRaisesRegex(backup.BackupError,'ceiling'):backup.inventory(root)
            value=backup.inventory(root);self.assertEqual(value['total_file_bytes'],4)
    def test_scope_credentials_and_traversal_guards_remain(self):
        for name in ('/outside','.runs/../escape','.tools/engine.jar','.runs/.env','.runs/x.key'):
            with self.subTest(name=name),self.assertRaises(backup.BackupError):backup.validate_name(name)
    def test_actual_installation_suffix_exception_is_exact_path_and_public_hash(self):
        name='.runs/installation-021-current965/checkout/tests/test_backup.py'
        digest='39fffc805691665b89433577a633ddc6929b5d0aba13f75c1a66db8ca03cd97a'
        self.assertTrue(backup.audited_nonsecret_test_source(name,digest))
        for path,pin in ((name,'0'*64),(name.replace('021','022'),digest),
                         (name.replace('test_backup.py','other.py'),digest)):
            with self.subTest(path=path,pin=pin):
                self.assertFalse(backup.audited_nonsecret_test_source(path,pin))

if __name__=='__main__':unittest.main()
