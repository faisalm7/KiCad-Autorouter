"""Actual filesystem controls for the full storage guard and shared fd scan."""
import math
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import pipeline as p, runner as r


class StorageScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()

    def tree(self):
        data=self.root/'.data';data.mkdir();nested=data/'nested';nested.mkdir()
        (nested/'plain').write_bytes(b'123456789')
        os.link(nested/'plain',nested/'hardlink')
        (data/'.hidden').write_bytes(b'1234567')
        with (data/'sparse').open('wb') as handle:handle.truncate(65536)
        (data/'file-link').symlink_to(nested/'plain')
        (data/'directory-link').symlink_to(nested,target_is_directory=True)
        (data/'dangling').symlink_to(data/'missing')
        (data/'cycle').symlink_to(data/'cycle')
        (self.root/'.runs').mkdir();(self.root/'.runs'/'artifact').write_bytes(b'abc')
        return data

    def test_full_scan_matches_legacy_logical_count_with_file_links_and_hardlinks(self):
        self.tree()
        legacy=sum(x.stat().st_size for name in ('.data','.tools','.runs')
                   for x in (self.root/name).rglob('*') if x.is_file())
        with patch.object(p.c,'ROOT',self.root):self.assertEqual(p.check_storage(),legacy)
        self.assertEqual(legacy,65536+9*3+7+3)

    def test_runner_default_still_excludes_all_symlinks(self):
        data=self.tree()
        self.assertEqual(r._workdir_bytes(data,100000),65536+9*2+7)
        self.assertEqual(r._workdir_bytes(data,100000,count_file_symlinks=True),65536+9*3+7)

    def test_actual_aggregate_sparse_overflow_rejects_without_allocating_payload(self):
        (self.root/'.data').mkdir();(self.root/'.runs').mkdir()
        with (self.root/'.data'/'sparse').open('wb') as handle:handle.truncate(10*1024**3)
        (self.root/'.runs'/'extra').write_bytes(b'x')
        self.assertLess((self.root/'.data'/'sparse').stat().st_blocks*512,1024**2)
        with patch.object(p.c,'ROOT',self.root),self.assertRaisesRegex(p.Rejected,'10 GiB'):
            p.check_storage()

    def test_disk_headroom_remains_enforced(self):
        self.tree()
        with patch.object(p.c,'ROOT',self.root),patch.object(p.shutil,'disk_usage',return_value=type('Usage',(),{'free':2*1024**3-1})()),self.assertRaisesRegex(p.Rejected,'headroom'):
            p.check_storage()

    def test_missing_optional_roots_are_allowed_but_existing_scope_failure_rejects(self):
        with patch.object(p.c,'ROOT',self.root):self.assertEqual(p.check_storage(),0)
        (self.root/'.runs').mkdir()
        with patch.object(p.c,'ROOT',self.root),patch.object(p,'_workdir_bytes',side_effect=FileNotFoundError('nested replaced')),self.assertRaisesRegex(p.Rejected,'size scan failed'):
            p.check_storage()

    def test_root_directory_link_is_refused(self):
        other=self.root/'other';other.mkdir();(other/'large').write_bytes(b'abcdef')
        (self.root/'.runs').symlink_to(other,target_is_directory=True)
        with patch.object(p.c,'ROOT',self.root),self.assertRaises(p.Rejected):p.check_storage()

    def test_time_entry_and_depth_limits_fail_closed(self):
        data=self.tree()
        with self.assertRaisesRegex(RuntimeError,'entry bound'):r._workdir_bytes(data,100000,max_entries=1)
        with patch.object(r.time,'monotonic',side_effect=[0,2]),self.assertRaisesRegex(RuntimeError,'time or entry'):
            r._workdir_bytes(data,100000,max_seconds=1)
        deep=self.root/'deep';deep.mkdir();child=deep
        for i in range(65):child=child/'d';child.mkdir()
        (child/'file').write_bytes(b'x')
        with self.assertRaisesRegex(RuntimeError,'depth'):r._workdir_bytes(deep,100000,max_seconds=10)

    def test_descriptor_scan_does_not_follow_directory_replaced_with_a_link(self):
        scan=self.root/'scan';scan.mkdir();child=scan/'child';child.mkdir()
        target=self.root/'target';target.mkdir();(target/'private-control').write_bytes(b'1234')
        native_open=r.os.open
        replaced=[]
        def opened(path,flags,*args,**kwargs):
            if path=='child' and kwargs.get('dir_fd') is not None and not replaced:
                child.rmdir();child.symlink_to(target,target_is_directory=True);replaced.append(True)
            return native_open(path,flags,*args,**kwargs)
        with patch.object(r.os,'open',side_effect=opened):
            try:observed=r._workdir_bytes(scan,100000,count_file_symlinks=True)
            except OSError:observed=0
        self.assertTrue(replaced);self.assertEqual(observed,0)

    def test_invalid_scan_configuration_rejects(self):
        for kw in ({'max_entries':True},{'max_entries':0},{'max_seconds':math.nan},
                   {'max_seconds':True},{'count_file_symlinks':1}):
            with self.subTest(kw=kw),self.assertRaises(ValueError):r._workdir_bytes(self.root,100,**kw)


if __name__=='__main__':unittest.main()
