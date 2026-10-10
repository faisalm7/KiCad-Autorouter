"""Real subprocess controls; these do not qualify native routing correctness."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from autorouter.runner import run


ROOT = Path(__file__).resolve().parents[1]


class RunnerTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / ".cache" / "runner-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)
        self.log = self.cwd / "worker.log"

    def run_python(self, code, **kwargs):
        return run([sys.executable, "-c", code], cwd=self.cwd, log=self.log, timeout=kwargs.pop("timeout", 3), **kwargs)

    def assert_dead(self, pid):
        until = time.monotonic() + 2
        while time.monotonic() < until:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.02)
        self.fail(f"test child {pid} is still present after process-group cleanup")

    def test_success_with_literal_arguments_and_resource_receipt(self):
        literal = "space ; $(touch should-not-exist) ' \""
        result = run([sys.executable, "-c", "import sys; print(sys.argv[1]); sum(i*i for i in range(200000))", literal], cwd=self.cwd, log=self.log, timeout=3)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(self.log.read_text().strip(), literal)
        self.assertFalse((self.cwd / "should-not-exist").exists())
        self.assertGreater(result["cpu_seconds"], 0)
        self.assertGreater(result["max_rss_bytes"], 0)
        self.assertTrue(result["cleanup_complete"])
        json.dumps(result)

    def test_nonzero_exit_is_not_success(self):
        result = self.run_python("import sys; print('failed'); sys.exit(7)")
        self.assertEqual(result["status"], "nonzero_exit")
        self.assertEqual(result["exit_code"], 7)

    def test_missing_executable_is_explicit(self):
        result = run([str(self.cwd / "absent")], cwd=self.cwd, log=self.log, timeout=3)
        self.assertEqual(result["status"], "spawn_error")
        self.assertIn("FileNotFoundError", result["error"])

    def test_existing_log_is_preserved_and_worker_not_started(self):
        self.log.write_text("prior evidence")
        result = self.run_python("from pathlib import Path; Path('must-not-exist').touch()")
        self.assertNotEqual(result["status"], "success")
        self.assertEqual(self.log.read_text(), "prior evidence")
        self.assertFalse((self.cwd / "must-not-exist").exists())

    def test_invalid_bounds_do_not_launch_worker(self):
        for timeout in (0, -1, float("inf"), float("nan"), True):
            with self.subTest(timeout=timeout):
                result = self.run_python("raise RuntimeError", timeout=timeout)
                self.assertEqual(result["status"], "invalid_request")
                self.assertFalse(self.log.exists())

    def test_invalid_argument_receipt_is_json_serializable(self):
        result = run([Path("not-a-string")], cwd=self.cwd, log=self.log, timeout=3)
        self.assertEqual(result["status"], "invalid_request")
        json.dumps(result)

    def test_startup_and_output_collection_count_against_timeout(self):
        result = self.run_python("pass", timeout=0.000001)
        self.assertEqual(result["status"], "timeout")

    def test_log_overflow_fails_and_remains_capped(self):
        result = self.run_python("import os; os.write(1, b'x'*200000)", max_log_bytes=1024)
        self.assertEqual(result["status"], "log_limit")
        self.assertTrue(result["log_truncated"])
        self.assertEqual(result["log_bytes"], 1024)
        self.assertEqual(self.log.stat().st_size, 1024)

    def test_exact_log_bound_can_succeed(self):
        result = self.run_python("import os; os.write(1, b'x'*1024)", max_log_bytes=1024)
        self.assertEqual(result["status"], "success")
        self.assertFalse(result["log_truncated"])

    def test_timeout_kills_parent_and_descendant_that_ignore_term(self):
        code = """
import os, signal, subprocess, sys, time
from pathlib import Path
signal.signal(signal.SIGTERM, signal.SIG_IGN)
p = subprocess.Popen([sys.executable, '-c', 'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)'])
Path('pids.json').write_text(__import__('json').dumps([os.getpid(), p.pid]))
time.sleep(30)
"""
        result = self.run_python(code, timeout=0.5)
        self.assertEqual(result["status"], "timeout")
        self.assertLess(result["wall_seconds"], 5)
        for pid in json.loads((self.cwd / "pids.json").read_text()):
            self.assert_dead(pid)

    def test_sigint_cancels_and_cleans_process_group(self):
        # Signal only a disposable supervisor, never the unittest process.
        worker = "import os,subprocess,sys,time,json; from pathlib import Path; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); Path('pids.json').write_text(json.dumps([os.getpid(),p.pid])); time.sleep(30)"
        supervisor = """
import json, pathlib, sys
from autorouter.runner import run
directory = pathlib.Path(sys.argv[1])
result = run([sys.executable, '-c', sys.argv[2]], cwd=directory, log=directory/'inner.log', timeout=20)
(directory/'result.json').write_text(json.dumps(result))
"""
        proc = subprocess.Popen([sys.executable, "-c", supervisor, str(self.cwd), worker], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            until = time.monotonic() + 3
            while not (self.cwd / "pids.json").exists() and time.monotonic() < until:
                time.sleep(0.02)
            self.assertTrue((self.cwd / "pids.json").exists())
            os.kill(proc.pid, signal.SIGINT)
            stdout, stderr = proc.communicate(timeout=5)
            self.assertEqual(proc.returncode, 0, (stdout, stderr))
            result = json.loads((self.cwd / "result.json").read_text())
            self.assertEqual(result["status"], "cancelled")
            self.assertEqual(result["cancel_signal"], "SIGINT")
            for pid in json.loads((self.cwd / "pids.json").read_text()):
                self.assert_dead(pid)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=3)

    def test_normal_exit_may_not_leave_a_descendant(self):
        result = self.run_python("import subprocess,sys; from pathlib import Path; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); Path('descendant.pid').write_text(str(p.pid))")
        self.assertEqual(result["status"], "descendants_left_running")
        self.assert_dead(int((self.cwd / "descendant.pid").read_text()))

    def test_parent_signal_handlers_are_restored(self):
        previous = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
        self.assertEqual(self.run_python("pass")["status"], "success")
        self.assertEqual(previous, {s: signal.getsignal(s) for s in previous})

    def test_memory_guard_kills_only_owned_process_group(self):
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"], start_new_session=True)
        try:
            code = "import subprocess,sys,json,time; from pathlib import Path; p=subprocess.Popen([sys.executable,'-c','import time; data=bytearray(64*1024*1024); time.sleep(10)']); Path('child.pid').write_text(str(p.pid)); p.wait()"
            result = self.run_python(code, max_group_rss_bytes=48 * 1024**2)
            self.assertEqual(result["status"], "memory_limit")
            self.assertGreater(result["sampled_peak_group_rss_bytes"], 48 * 1024**2)
            self.assertGreater(result["monitor_cpu_seconds"], 0)
            self.assertFalse(result["resource_guards"]["os_enforced"])
            self.assert_dead(result["pid"])
            self.assert_dead(int((self.cwd / "child.pid").read_text()))
            self.assertIsNone(unrelated.poll())
        finally:
            unrelated.terminate()
            unrelated.wait(timeout=3)

    def test_disk_guard_stops_worker_after_small_bounded_write(self):
        result = self.run_python("from pathlib import Path; import time; Path('large.bin').write_bytes(b'x'*(512*1024)); time.sleep(10)", max_workdir_bytes=128 * 1024)
        self.assertEqual(result["status"], "disk_limit")
        self.assertGreater(result["sampled_peak_workdir_bytes"], 128 * 1024)
        self.assertEqual((self.cwd / "large.bin").stat().st_size, 512 * 1024)
        self.assert_dead(result["pid"])

    def test_final_disk_check_catches_write_before_immediate_exit(self):
        # Repeat a small bounded control to exercise Darwin's last-member exit
        # race, which can transiently return EPERM to killpg before wait4 is ready.
        for number in range(8):
            with self.subTest(number=number):
                directory = self.cwd / str(number)
                directory.mkdir()
                result = run([sys.executable, "-c", "from pathlib import Path; Path('large.bin').write_bytes(b'x'*(64*1024))"], cwd=directory, log=directory / "worker.log", timeout=3, max_workdir_bytes=32 * 1024)
                self.assertEqual(result["status"], "disk_limit", result)
                self.assertTrue(result["cleanup_complete"], result)

    def test_preexisting_disk_excess_prevents_launch(self):
        (self.cwd / "existing.bin").write_bytes(b"x" * 2048)
        result = self.run_python("from pathlib import Path; Path('must-not-launch').touch()", max_workdir_bytes=1024)
        self.assertEqual(result["status"], "disk_limit")
        self.assertNotIn("pid", result)
        self.assertFalse((self.cwd / "must-not-launch").exists())

    def test_disk_scan_does_not_follow_file_or_directory_symlinks(self):
        outside_temp = tempfile.TemporaryDirectory(dir=self.cwd.parent)
        self.addCleanup(outside_temp.cleanup)
        outside = Path(outside_temp.name)
        (outside / "large.bin").write_bytes(b"x" * 65536)
        (self.cwd / "linked-dir").symlink_to(outside, target_is_directory=True)
        (self.cwd / "linked-file").symlink_to(outside / "large.bin")
        result = self.run_python("pass", max_workdir_bytes=1024)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["sampled_peak_workdir_bytes"], 0)

    def test_optional_guards_can_be_disabled(self):
        result = self.run_python("pass", max_group_rss_bytes=None, max_workdir_bytes=None)
        self.assertEqual(result["status"], "success")
        self.assertIsNone(result["sampled_peak_group_rss_bytes"])
        self.assertIsNone(result["sampled_peak_workdir_bytes"])
        self.assertEqual(result["monitor_cpu_seconds"], 0)

    def test_invalid_resource_bounds_prevent_launch(self):
        for option in ("max_group_rss_bytes", "max_workdir_bytes"):
            for value in (0, -1, True, 1.5):
                with self.subTest(option=option, value=value):
                    result = self.run_python("raise RuntimeError", **{option: value})
                    self.assertEqual(result["status"], "invalid_request")
                    self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
