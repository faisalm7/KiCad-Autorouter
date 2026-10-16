"""Real filesystem controls for archive-independent runtime storage bounds."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import pipeline as p

class ActiveStorageTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name).resolve()
        self.job=self.root/'jobs'/'active';self.job.mkdir(parents=True)
    def guard(self,**kwargs):
        with patch.object(p.c,'ROOT',self.root):return p.check_storage(active_root=self.job,**kwargs)
    def test_runtime_only_traverses_active_job_even_with_unreadable_historical_scope(self):
        (self.job/'evidence').mkdir();(self.job/'evidence'/'native.json').write_bytes(b'12345')
        # A global archive audit rejects this directory link. Active work must
        # neither inspect nor depend on the retained research tree beside it.
        (self.root/'.runs').symlink_to(self.root/'missing',target_is_directory=True)
        seen=[];real=p._workdir_bytes
        def scan(root,*args,**kwargs):seen.append(root);return real(root,*args,**kwargs)
        with patch.object(p,'_workdir_bytes',side_effect=scan):self.assertEqual(self.guard(),5)
        self.assertEqual(seen,[self.job])
    def test_missing_fresh_output_checks_headroom_without_creating_it(self):
        fresh=self.root/'fresh'/'new'
        with patch.object(p.c,'ROOT',self.root):self.assertEqual(p.check_storage(active_root=fresh),0)
        self.assertFalse(fresh.exists())
    def test_active_ceiling_and_sparse_file_still_fail_closed(self):
        with (self.job/'oversized').open('wb') as stream:stream.truncate(18*1024**3+1)
        self.assertLess((self.job/'oversized').stat().st_blocks*512,1024**2)
        with self.assertRaisesRegex(p.Rejected,'active job'):self.guard()
    def test_active_root_replacement_and_scan_error_are_not_missing_scope_waivers(self):
        with patch.object(p,'_workdir_bytes',side_effect=FileNotFoundError('replaced after lstat')):
            with self.assertRaisesRegex(p.Rejected,'scan failed'):self.guard()
        target=self.root/'target';target.mkdir();alias=self.root/'alias';alias.symlink_to(target,target_is_directory=True)
        with self.assertRaises(p.Rejected):p.check_storage(active_root=alias)
    def test_active_volume_and_checkout_headroom_are_both_checked(self):
        usage=type('Usage',(),{'free':4*1024**3})()
        low=type('Usage',(),{'free':2*1024**3-1})()
        for values in ([low],[usage,low]):
            with self.subTest(values=len(values)),patch.object(p.shutil,'disk_usage',side_effect=values),self.assertRaisesRegex(p.Rejected,'headroom'):self.guard()
    def test_archive_root_and_filesystem_root_are_not_individual_jobs(self):
        for root in (self.root,self.root/'.runs',self.root/'.tools',self.root/'.data',Path('/')):
            with self.subTest(root=root),patch.object(p.c,'ROOT',self.root),self.assertRaisesRegex(p.Rejected,'individual job'):p.check_storage(active_root=root)
    def test_nested_material_growth_is_measured_again_on_every_call(self):
        self.assertEqual(self.guard(),0)
        (self.job/'trial').mkdir();(self.job/'trial'/'native.json').write_bytes(b'123')
        self.assertEqual(self.guard(),3)
        (self.job/'trial'/'native.json').write_bytes(b'1234567')
        self.assertEqual(self.guard(),7)

if __name__=='__main__':unittest.main()
