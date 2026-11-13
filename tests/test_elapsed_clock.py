"""Clock-provider controls, not Native PCB or actual suspend qualification."""

import ctypes
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import runner


ROOT = Path(__file__).resolve().parents[1]


class ElapsedClock(unittest.TestCase):
    def setUp(self):
        runner._elapsed_source.cache_clear()
        self.addCleanup(runner._elapsed_source.cache_clear)

    def posix(self, platform, name, values):
        read = Mock(side_effect=values)
        clocks = SimpleNamespace(clock_gettime=read, monotonic=Mock(return_value=100.0),
                                 time=Mock(side_effect=[9000.0, 1000.0]), **{name: 17})
        return patch.object(runner, 'sys', SimpleNamespace(platform=platform)), patch.object(runner, 'time', clocks), read, clocks

    def test_darwin_advances_across_simulated_sleep_while_awake_clock_stalls(self):
        platform, clocks, read, stub = self.posix('darwin', 'CLOCK_MONOTONIC_RAW', [100.0, 701.0])
        with platform, clocks:
            started = runner.elapsed_time(); deadline = started + 60
            self.assertGreater(runner.elapsed_time(), deadline)
            stub.monotonic.assert_not_called(); stub.time.assert_not_called()
        self.assertEqual(read.call_args_list, [unittest.mock.call(17), unittest.mock.call(17)])

    def test_linux_uses_boottime_without_consulting_raw_or_calendar(self):
        platform, clocks, read, stub = self.posix('linux', 'CLOCK_BOOTTIME', [31.0, 3631.0])
        with platform, clocks:
            self.assertEqual(runner.elapsed_time(), 31.0)
            self.assertEqual(runner.elapsed_time(), 3631.0)
        self.assertEqual(read.call_count, 2)

    def test_windows_native_signature_and_millisecond_conversion_are_cached(self):
        read = Mock(side_effect=[1000, 1000, 61000])
        loader = Mock(return_value=SimpleNamespace(GetTickCount64=read))
        api = SimpleNamespace(WinDLL=loader, c_ulonglong=ctypes.c_ulonglong)
        with patch.object(runner, 'sys', SimpleNamespace(platform='win32')), patch.object(runner, 'ctypes', api):
            self.assertEqual([runner.elapsed_time() for _ in range(3)], [1.0, 1.0, 61.0])
        loader.assert_called_once_with('kernel32', use_last_error=True)
        self.assertEqual(read.argtypes, [])
        self.assertIs(read.restype, ctypes.c_ulonglong)
        self.assertEqual(read.call_count, 3)

    def test_unsupported_platform_has_no_fallback(self):
        clocks = SimpleNamespace(monotonic=Mock(), time=Mock())
        with patch.object(runner, 'sys', SimpleNamespace(platform='unsupported')), patch.object(runner, 'time', clocks):
            with self.assertRaisesRegex(RuntimeError, 'unsupported'):
                runner.elapsed_time()
            clocks.monotonic.assert_not_called(); clocks.time.assert_not_called()

    def test_missing_or_wrong_native_api_refuses_without_fallback(self):
        for clocks in (SimpleNamespace(), SimpleNamespace(CLOCK_MONOTONIC_RAW=True, clock_gettime=Mock()),
                       SimpleNamespace(CLOCK_MONOTONIC_RAW=4, clock_gettime=None)):
            runner._elapsed_source.cache_clear()
            with self.subTest(clocks=clocks), patch.object(runner, 'sys', SimpleNamespace(platform='darwin')), \
                    patch.object(runner, 'time', clocks), self.assertRaisesRegex(RuntimeError, 'unavailable'):
                runner.elapsed_time()
        with patch.object(runner, 'sys', SimpleNamespace(platform='win32')), \
                patch.object(runner, 'ctypes', SimpleNamespace()), self.assertRaisesRegex(RuntimeError, 'unavailable'):
            runner.elapsed_time()

    def test_failed_native_read_does_not_switch_clock_or_reuse_old_value(self):
        platform, clocks, read, stub = self.posix('darwin', 'CLOCK_MONOTONIC_RAW', [10.0, OSError('clock unavailable')])
        with platform, clocks:
            self.assertEqual(runner.elapsed_time(), 10.0)
            with self.assertRaisesRegex(RuntimeError, 'read failed'):
                runner.elapsed_time()
        self.assertEqual(read.call_count, 2)

    def test_nonfinite_negative_and_untyped_values_refuse(self):
        for value in (math.inf, -math.inf, math.nan, -0.001, True, '10', None, 10**1000):
            with self.subTest(value=str(value)[:40]), patch.object(runner, '_elapsed_source', return_value=(lambda: value, 1.0)), \
                    self.assertRaisesRegex(RuntimeError, 'read failed'):
                runner.elapsed_time()
        with patch.object(runner, '_elapsed_source', return_value=(lambda: 0.0, 1.0)):
            self.assertEqual(runner.elapsed_time(), 0.0)

    @unittest.skipUnless(sys.platform == 'darwin', 'actual Mac clock control')
    def test_actual_mac_root_python_reads_the_native_raw_clock(self):
        before = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
        first = runner.elapsed_time(); second = runner.elapsed_time()
        after = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
        self.assertLessEqual(before, first)
        self.assertLessEqual(first, second)
        self.assertLessEqual(second, after)

    @unittest.skipUnless(sys.platform == 'darwin', 'actual Mac bundled-Python clock control')
    def test_actual_kicad_python39_shares_native_boot_clock_basis(self):
        python = ROOT / '.tools/kicad-10.0.7-local-001/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9'
        if not python.is_file():
            self.skipTest('isolated KiCad10.0.7 Python3.9 unavailable; native read remains unqualified')
        code = """
import json,sys,time
from autorouter.runner import elapsed_time
before=time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
first=elapsed_time();second=elapsed_time()
after=time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
assert before <= first <= second <= after
print(json.dumps(dict(version=list(sys.version_info[:2]),first=first,second=second)))
"""
        env = {key: value for key, value in os.environ.items() if key not in ('PYTHONPATH', 'PYTHONHOME')}
        env.update(PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
        before = runner.elapsed_time()
        result = subprocess.run([str(python), '-B', '-c', code], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=10)
        after = runner.elapsed_time()
        self.assertEqual(result.returncode, 0, result.stderr[:2000])
        self.assertLess(len(result.stdout), 4096)
        observed = json.loads(result.stdout)
        self.assertEqual(observed['version'], [3, 9])
        self.assertLessEqual(before, observed['first'])
        self.assertLessEqual(observed['second'], after)


if __name__ == '__main__':
    unittest.main()
