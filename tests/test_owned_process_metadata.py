"""Mocked libproc ABI/error controls only; no Native or process signals."""
import ctypes
import errno
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from scripts import native_cancellation as runner


class OwnedProcessMetadata(unittest.TestCase):
    def library(self, *, pids=(102, 101), count=None, list_error=0, metadata=None):
        metadata=metadata or {101:(101,77,101),102:(102,77,101)}
        def listing(selector, buffer, size):
            self.assertEqual(selector, self.selector)
            self.assertEqual(size, 4096*ctypes.sizeof(ctypes.c_int))
            for index,pid in enumerate(pids):buffer[index]=pid
            ctypes.set_errno(list_error)
            return len(pids) if count is None else count
        def info(pid, flavor, arg, buffer, size):
            self.assertEqual((flavor,arg,size),(3,0,136))
            value=metadata[pid]
            if isinstance(value, tuple):
                record=ctypes.cast(buffer,ctypes.POINTER(runner._DarwinBSDInfo)).contents
                record.pid,record.ppid,record.pgid=value
                return 136
            returned,error=value['size'],value['errno'];ctypes.set_errno(error);return returned
        return SimpleNamespace(proc_listchildpids=Mock(side_effect=listing),
            proc_listpgrppids=Mock(side_effect=listing),proc_pidinfo=Mock(side_effect=info))

    def call(self, library, **selector):
        self.selector=next(iter(selector.values()))
        with patch.object(runner.sys,'platform','darwin'),patch.object(runner.ctypes,'CDLL',return_value=library):
            return runner.owned_process_metadata(**selector)

    def test_exact_parent_selector_returns_sorted_pid_fields_only(self):
        library=self.library();rows=self.call(library,parent_pid=77)
        self.assertEqual(rows,[{'pid':101,'ppid':77,'pgid':101},{'pid':102,'ppid':77,'pgid':101}])
        library.proc_listchildpids.assert_called_once();library.proc_listpgrppids.assert_not_called()
        self.assertEqual(library.proc_pidinfo.call_count,2)

    def test_exact_group_selector_uses_one_bsd_snapshot_per_selected_pid(self):
        library=self.library();rows=self.call(library,pgid=101)
        self.assertEqual([row['pid'] for row in rows],[101,102])
        library.proc_listpgrppids.assert_called_once();library.proc_listchildpids.assert_not_called()
        self.assertEqual(library.proc_pidinfo.call_count,2)
        self.assertEqual(ctypes.sizeof(runner._DarwinBSDInfo),136)
        self.assertEqual(runner._DarwinBSDInfo.start_seconds.offset,120)

    def test_selector_is_exact_plain_positive_pid_t_without_library_access(self):
        bad=[{},dict(parent_pid=1,pgid=1)]
        bad += [{name:value} for name in ('parent_pid','pgid') for value in (True,False,0,-1,1.0,'1',2**31)]
        with patch.object(runner.ctypes,'CDLL') as load:
            for selector in bad:
                with self.subTest(selector=selector),self.assertRaises(ValueError):
                    runner.owned_process_metadata(**selector)
            load.assert_not_called()

    def test_other_platform_has_no_ps_or_all_process_fallback(self):
        with patch.object(runner.sys,'platform','linux'),patch.object(runner.ctypes,'CDLL') as load,patch.object(runner.subprocess,'Popen') as popen:
            with self.assertRaisesRegex(RuntimeError,'requires Darwin'):runner.owned_process_metadata(parent_pid=77)
            load.assert_not_called();popen.assert_not_called()

    def test_listing_permission_errors_or_negative_counts_fail_closed(self):
        for count,error in ((0,errno.EPERM),(0,errno.EACCES),(-1,errno.EIO),(-1,0),(1,errno.EPERM)):
            with self.subTest(count=count,error=error),self.assertRaises(OSError):
                self.call(self.library(pids=(101,),count=count,list_error=error),parent_pid=77)

    def test_empty_or_exited_selector_is_an_empty_snapshot(self):
        for error in (0,errno.ESRCH):
            self.assertEqual(self.call(self.library(pids=(),list_error=error),pgid=101),[])

    def test_saturated_invalid_and_duplicate_inventory_refuses(self):
        for pids,count in (((101,),4096),((101,),4097),((0,),None),((-1,),None),((101,101),None)):
            with self.subTest(pids=pids,count=count),self.assertRaises(RuntimeError):
                self.call(self.library(pids=pids,count=count),parent_pid=77)

    def test_incomplete_or_permission_denied_bsd_info_is_not_absence(self):
        for size,error in ((0,0),(135,0),(-1,0),(0,errno.EPERM),(0,errno.EACCES),(136,errno.EPERM)):
            library=self.library(pids=(101,),metadata={101:{'size':size,'errno':error}})
            with self.subTest(size=size,error=error),self.assertRaises(OSError):self.call(library,pgid=101)

    def test_esrch_race_omits_only_the_exited_pid(self):
        library=self.library(metadata={101:(101,77,101),102:{'size':0,'errno':errno.ESRCH}})
        self.assertEqual(self.call(library,parent_pid=77),[{'pid':101,'ppid':77,'pgid':101}])

    def test_pid_selector_changes_and_invalid_identity_refuse(self):
        for selector,row in ((dict(parent_pid=77),(999,77,101)),(dict(parent_pid=77),(101,78,101)),
                             (dict(pgid=101),(101,77,102)),(dict(pgid=101),(101,2**31,101)),
                             (dict(parent_pid=77),(101,77,0))):
            with self.subTest(selector=selector,row=row),self.assertRaises(RuntimeError):
                self.call(self.library(pids=(101,),metadata={101:row}),**selector)

    def test_library_error_is_not_silently_empty(self):
        with patch.object(runner.sys,'platform','darwin'),patch.object(runner.ctypes,'CDLL',side_effect=OSError(errno.EPERM,'denied')):
            with self.assertRaises(OSError):runner.owned_process_metadata(parent_pid=77)


if __name__=='__main__':unittest.main()
