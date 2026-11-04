"""Owned executable metadata controls; the tiny real child is not KiCad proof."""
import ctypes
import errno
import os
from pathlib import Path
import select
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import native_cancellation as control

REAL_OBSERVATIONS = []


class OwnedExecutableMetadata(unittest.TestCase):
    row = {'pid': 101, 'ppid': 77, 'pgid': 101}

    def call(self, *, snapshots=None, path=b'/owned/native', returned=None, error=0):
        def read(pid, buffer, size):
            self.assertEqual((pid, size), (101, 4096))
            if path: ctypes.memmove(buffer, path, len(path))
            ctypes.set_errno(error)
            return len(path) if returned is None else returned
        library = SimpleNamespace(proc_pidpath=Mock(side_effect=read))
        with patch.object(control.sys, 'platform', 'darwin'), \
                patch.object(control.os, 'getpid', return_value=77), \
                patch.object(control, 'owned_process_metadata', side_effect=snapshots or [[self.row], [self.row]]) as lineage, \
                patch.object(control.ctypes, 'CDLL', return_value=library):
            result = control.owned_executable_metadata(101, parent_pid=77, pgid=101)
        return result, library, lineage

    def test_exact_image_is_bracketed_by_owned_lineage_only(self):
        result, library, lineage = self.call()
        self.assertEqual(result, {**self.row, 'executable': '/owned/native'})
        self.assertEqual(lineage.call_count, 2)
        lineage.assert_called_with(parent_pid=77)
        library.proc_pidpath.assert_called_once()
        self.assertTrue(control.pinned_owned_executable(result, pid=101, parent_pid=77,
                                                       pgid=101, expected_path='/owned/native'))

    def test_wrong_or_noncaller_parent_never_reads_metadata(self):
        with patch.object(control.os, 'getpid', return_value=77), \
                patch.object(control, 'owned_process_metadata') as lineage, \
                patch.object(control.ctypes, 'CDLL') as library:
            for args in ((101, 78, 101), (True, 77, 101), (0, 77, 101),
                         (101, 77, False), (2**31, 77, 101)):
                with self.subTest(args=args), self.assertRaises(ValueError):
                    control.owned_executable_metadata(args[0], parent_pid=args[1], pgid=args[2])
            lineage.assert_not_called(); library.assert_not_called()

    def test_absent_exact_child_never_queries_unrelated_pid(self):
        result, library, lineage = self.call(snapshots=[[{'pid': 102, 'ppid': 77, 'pgid': 102}]])
        self.assertIsNone(result); library.proc_pidpath.assert_not_called()
        self.assertEqual(lineage.call_count, 1)

    def test_wrong_group_parent_duplicate_or_changed_snapshot_refuses(self):
        wrong = ({**self.row, 'pgid': 102}, {**self.row, 'ppid': 78})
        for rows in ([wrong[0]], [wrong[1]], [self.row, self.row]):
            with self.subTest(rows=rows), self.assertRaisesRegex(RuntimeError, 'lineage'):
                self.call(snapshots=[rows])
        with self.assertRaisesRegex(RuntimeError, 'lineage'):
            self.call(snapshots=[[self.row], [{**self.row, 'pgid': 102}]])

    def test_exit_between_snapshots_or_esrch_during_path_is_not_positive(self):
        self.assertIsNone(self.call(snapshots=[[self.row], []])[0])
        self.assertIsNone(self.call(path=b'', returned=0, error=errno.ESRCH)[0])

    def test_path_api_permission_zero_unknown_and_error_after_bytes_refuse(self):
        for returned, error in ((0, errno.EPERM), (0, errno.EACCES), (0, 0),
                                (-1, errno.EIO), (13, errno.EPERM)):
            with self.subTest(returned=returned, error=error), self.assertRaises(OSError):
                self.call(returned=returned, error=error)

    def test_truncated_unterminated_inconsistent_or_invalid_path_refuses(self):
        for path, returned in ((b'x' * 4096, 4096), (b'x' * 4095, 4095),
                               (b'/ok\0hidden', 10), (b'/ok', 4),
                               (b'relative', None), (b'/a/../b', None),
                               (b'/a//b', None), (b'/bad\xff', None)):
            with self.subTest(path=path[:20], returned=returned), self.assertRaises(RuntimeError):
                self.call(path=path, returned=returned)

    def test_library_or_lineage_errors_are_not_absence(self):
        with patch.object(control.os, 'getpid', return_value=77), \
                patch.object(control.sys, 'platform', 'darwin'), \
                patch.object(control, 'owned_process_metadata', return_value=[self.row]), \
                patch.object(control.ctypes, 'CDLL', side_effect=OSError(errno.EPERM, 'denied')):
            with self.assertRaises(OSError):
                control.owned_executable_metadata(101, parent_pid=77, pgid=101)
        with patch.object(control.os, 'getpid', return_value=77), \
                patch.object(control.sys, 'platform', 'linux'), \
                patch.object(control.ctypes, 'CDLL') as library:
            with self.assertRaisesRegex(RuntimeError, 'requires Darwin'):
                control.owned_executable_metadata(101, parent_pid=77, pgid=101)
            library.assert_not_called()

    def test_pure_gate_rejects_launcher_wrong_image_and_wrong_identity(self):
        good = {**self.row, 'executable': '/owned/native'}
        bad = [None, {}, {**good, 'executable': '/usr/bin/sandbox-exec'},
               {**good, 'executable': '/owned/other'}, {**good, 'pid': 102},
               {**good, 'ppid': 78}, {**good, 'pgid': 102},
               {**good, 'pid': True}, {**good, 'extra': 'unknown'}]
        with patch.object(Path, 'resolve', side_effect=AssertionError('pure gate has no filesystem reads')):
            for record in bad:
                with self.subTest(record=record):
                    self.assertFalse(control.pinned_owned_executable(record, pid=101, parent_pid=77,
                                                                    pgid=101, expected_path='/owned/native'))

    @unittest.skipUnless(sys.platform == 'darwin', 'real libproc requires macOS')
    def test_actual_owned_python_image_in_same_no_network_sandbox(self):
        argv = ['/usr/bin/sandbox-exec', '-p', '(version 1)(allow default)(deny network*)',
                sys.executable, '-B', '-u', '-c',
                "import sys; print('ready', flush=True); sys.stdin.readline()"]
        child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True, text=True)
        try:
            self.assertTrue(select.select([child.stdout], [], [], 5)[0], 'tiny child readiness timeout')
            self.assertEqual(child.stdout.readline(), 'ready\n')
            self.assertIsNone(child.poll())
            record = control.owned_executable_metadata(child.pid, parent_pid=os.getpid(), pgid=child.pid)
            self.assertIsNotNone(record)
            REAL_OBSERVATIONS.append(record)
            expected = str(Path(sys.executable).resolve(strict=True))
            self.assertTrue(control.pinned_owned_executable(record, pid=child.pid,
                parent_pid=os.getpid(), pgid=child.pid, expected_path=expected), record)
        finally:
            if child.poll() is None:
                try: child.communicate('\n', timeout=5)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    try: child.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        child.kill(); child.wait(timeout=2)
            for stream in (child.stdin, child.stdout, child.stderr):
                if stream is not None: stream.close()
        self.assertEqual(child.returncode, 0)


if __name__ == '__main__': unittest.main()
