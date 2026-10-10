"""Bounded, synchronous POSIX worker execution without a shell.

The worker gets its own process group; cancellation kills that group, including
ordinary descendants. This is not a hostile-code sandbox: a descendant that
deliberately creates a new session can escape it. SIGKILL of this supervisor also
cannot run cleanup. Normal routing must not daemonize or detach subprocesses.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any


RESOURCE_POLL_SECONDS = 0.25
_RESOURCE_SCAN_SECONDS = 1.0


def _workdir_bytes(root: Path, limit: int) -> int:
    """Count regular-file logical sizes without following directory symlinks.

    Return early after the bound is crossed: this is an observed lower bound,
    not a full size inventory. File additions/deletions can race this snapshot.
    Descriptor-relative O_NOFOLLOW also refuses a directory swapped for a link.
    """
    total = entries = 0
    started = time.monotonic()
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW

    def scan(directory_fd: int, depth: int) -> None:
        nonlocal total, entries
        if depth > 64:
            raise RuntimeError("workdir scan exceeded directory-depth bound")
        with os.scandir(directory_fd) as iterator:
            for entry in iterator:
                entries += 1
                if entries > 100_000 or time.monotonic() - started > _RESOURCE_SCAN_SECONDS:
                    raise RuntimeError("workdir scan exceeded time or entry bound")
                try:
                    info = entry.stat(follow_symlinks=False)
                except FileNotFoundError:
                    continue
                if stat.S_ISREG(info.st_mode):
                    total += info.st_size
                elif stat.S_ISDIR(info.st_mode):
                    try:
                        child_fd = os.open(entry.name, flags, dir_fd=directory_fd)
                    except (FileNotFoundError, NotADirectoryError):
                        continue
                    try:
                        scan(child_fd, depth + 1)
                    finally:
                        os.close(child_fd)
                if total > limit:
                    return

    root_fd = os.open(root, flags)
    try:
        scan(root_fd, 0)
    finally:
        os.close(root_fd)
    return total


def _group_rss_bytes(pgid: int, cwd: Path) -> tuple[int, float]:
    """Read only pid/pgid/RSS metadata; sum the worker's group, never other groups.

    ps RSS uses KiB on Darwin and Linux. Shared pages can be double-counted by a
    sum, and short-lived peaks can be missed. wait4 accounts for the ps helper's
    own CPU separately from the worker. A temporary unlinked file avoids pipe
    deadlock without storing process names, command lines, or environments.
    """
    with tempfile.TemporaryFile(dir=cwd) as listing:
        scanner = subprocess.Popen(
            ["/bin/ps", "-axo", "pid=,pgid=,rss="],
            stdin=subprocess.DEVNULL,
            stdout=listing,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            shell=False,
            env={"LC_ALL": "C", "PATH": "/usr/bin:/bin"},
        )
        until = time.monotonic() + _RESOURCE_SCAN_SECONDS
        timed_out = False
        usage = None
        try:
            while scanner.returncode is None:
                pid, status, observed = os.wait4(scanner.pid, os.WNOHANG)
                if pid:
                    scanner.returncode = os.waitstatus_to_exitcode(status)
                    usage = observed
                    break
                if time.monotonic() > until:
                    timed_out = True
                    break
                time.sleep(0.005)
        finally:
            if scanner.returncode is None:
                scanner.kill()  # Only this specifically created metadata helper.
                scanner.wait(timeout=1)
        if timed_out or scanner.returncode != 0 or usage is None:
            raise RuntimeError("process-group RSS measurement failed or timed out")
        if listing.tell() > 4 * 1024 * 1024:
            raise RuntimeError("process metadata exceeded measurement bound")
        listing.seek(0)
        total = 0
        for line in listing:
            columns = line.split()
            if len(columns) != 3:
                raise RuntimeError("unexpected process RSS metadata")
            _pid, group, rss = map(int, columns)
            if group == pgid:
                total += rss * 1024
        return total, usage.ru_utime + usage.ru_stime


def run(
    argv: list[str],
    *,
    cwd: Path,
    log: Path,
    timeout: float,
    max_log_bytes: int = 2_000_000,
    env: dict[str, str] | None = None,
    max_group_rss_bytes: int | None = 4 * 1024**3,
    max_workdir_bytes: int | None = 512 * 1024**2,
) -> dict[str, Any]:
    """Run one worker and return a JSON-serializable receipt, including failures.

    ``success`` means only an exit code of zero within the execution bounds. It
    does not establish routing correctness. Logs combine stdout and stderr and
    are created exclusively, never replaced. Their parent directory must exist.
    SIGINT/SIGTERM become ``cancelled`` when called on Python's main thread;
    off-main-thread callers retain their application's signal handling.

    CPU and RSS are collected with wait4 for this child, not process-wide
    RUSAGE_CHILDREN deltas. Child CPU can include descendants the child waited
    for, but orphaned descendants are not reliably accounted for. RSS is the
    kernel-reported peak (bytes on Darwin, KiB converted to bytes on Linux),
    not the simultaneous sum of process-tree memory. Optional RSS/workdir bounds
    are polled guards, not OS-enforced quotas. They can overshoot between scans;
    RSS counts the worker's own process group, and disk counts regular files only
    below cwd without following symlinks. None disables a guard. Poll overhead
    remains in wall time, ps CPU is returned as monitor_cpu_seconds, and the
    original cpu_seconds/max_rss_bytes meanings are unchanged.
    """
    started = time.monotonic()
    supervisor_started = time.process_time()
    result: dict[str, Any] = {
        "status": "invalid_request",
        "exit_code": None,
        "wall_seconds": 0.0,
        "cpu_seconds": None,
        "max_rss_bytes": None,
        "supervisor_cpu_seconds": 0.0,
        "monitor_cpu_seconds": 0.0,
        "sampled_peak_group_rss_bytes": None,
        "sampled_peak_workdir_bytes": None,
        "resource_guards": {
            "max_group_rss_bytes": max_group_rss_bytes if isinstance(max_group_rss_bytes, (int, type(None))) else repr(max_group_rss_bytes),
            "max_workdir_bytes": max_workdir_bytes if isinstance(max_workdir_bytes, (int, type(None))) else repr(max_workdir_bytes),
            "poll_interval_seconds": RESOURCE_POLL_SECONDS,
            "os_enforced": False,
            "limitations": "Polling can overshoot; group RSS can double-count shared pages and miss peaks; workdir logical sizes exclude symlinks and stop counting after the bound is crossed.",
        },
        "argv": [arg if isinstance(arg, str) else repr(arg) for arg in argv] if isinstance(argv, list) else repr(argv),
        "log": str(log),
        "log_bytes": 0,
        "log_truncated": False,
        "cleanup_complete": True,
        "resource_accounting": {
            "method": "wait4 child rusage",
            "cpu_scope": "direct child plus descendants accounted for by child wait",
            "rss_scope": "kernel peak, not simultaneous process-tree total",
            "native_rss_unit": "bytes" if sys.platform == "darwin" else "KiB" if sys.platform.startswith("linux") else "unknown",
            "memory_limit_enforced": False,
        },
    }
    process: subprocess.Popen[bytes] | None = None
    log_file = None
    selector = selectors.DefaultSelector()
    handlers: dict[int, Any] = {}
    cancelled: list[int] = []
    reaped = False
    stopping_at: float | None = None
    killed = False
    eof = False
    next_resource_poll = started
    checked_exit_disk = False

    def cancel(signum: int, _frame: Any) -> None:
        if not cancelled:
            cancelled.append(signum)

    def signal_group(signum: int) -> None:
        if process is not None:
            until = time.monotonic() + 0.1
            while True:
                try:
                    os.killpg(process.pid, signum)
                    return
                except ProcessLookupError:
                    return
                except PermissionError:
                    # Darwin can report EPERM during the last-member exit
                    # race before wait4 is ready. Bound retries to 100 ms;
                    # never hide a persistent live-group permission failure.
                    reap()
                    if time.monotonic() >= until:
                        raise
                    time.sleep(0.002)

    def reap() -> None:
        nonlocal reaped
        if process is None or reaped:
            return
        pid, status, usage = os.wait4(process.pid, os.WNOHANG)
        if pid:
            reaped = True
            process.returncode = os.waitstatus_to_exitcode(status)
            result["exit_code"] = process.returncode
            result["cpu_seconds"] = usage.ru_utime + usage.ru_stime
            result["max_rss_bytes"] = int(usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024))

    def group_exists() -> bool:
        if process is None:
            return False
        try:
            os.killpg(process.pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # signal 0 with EPERM establishes existence, not successful cleanup.
            return True

    def stop(status: str) -> None:
        nonlocal stopping_at
        if stopping_at is None:
            result["status"] = status
            stopping_at = time.monotonic()
            signal_group(signal.SIGTERM)

    try:
        if (
            not isinstance(argv, list)
            or not argv
            or any(not isinstance(arg, str) or "\0" in arg for arg in argv)
            or not argv[0]
        ):
            raise ValueError("argv must be a nonempty list of NUL-free strings")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be a finite positive number of seconds")
        if isinstance(max_log_bytes, bool) or not isinstance(max_log_bytes, int) or max_log_bytes <= 0:
            raise ValueError("max_log_bytes must be a positive integer")
        for name, bound in (("max_group_rss_bytes", max_group_rss_bytes), ("max_workdir_bytes", max_workdir_bytes)):
            if bound is not None and (isinstance(bound, bool) or not isinstance(bound, int) or bound <= 0):
                raise ValueError(name + " must be a positive integer or None")
        if env is not None and (not isinstance(env, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in env.items())):
            raise ValueError("env must be a string-to-string dictionary or None")
        if sys.platform != "darwin" and not sys.platform.startswith("linux"):
            raise ValueError("qualified resource units are available only on Darwin and Linux")
        cwd = Path(cwd).resolve(strict=True)
        if not cwd.is_dir():
            raise ValueError("cwd must be an existing directory")
        log = Path(log).absolute()
        result["cwd"] = str(cwd)
        result["log"] = str(log)
        if max_workdir_bytes is not None:
            initial_bytes = _workdir_bytes(cwd, max_workdir_bytes)
            result["sampled_peak_workdir_bytes"] = initial_bytes
            if initial_bytes > max_workdir_bytes:
                result["status"] = "disk_limit"
                return result
        # O_EXCL also refuses existing symlinks. No truncation of prior evidence.
        log_file = log.open("xb", buffering=0)
        if threading.current_thread() is threading.main_thread():
            for signum in (signal.SIGINT, signal.SIGTERM):
                handlers[signum] = signal.getsignal(signum)
                signal.signal(signum, cancel)
        result["signal_cancellation_enabled"] = bool(handlers)
        result["status"] = "spawn_error"
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
            shell=False,
        )
        result["pid"] = process.pid
        result["status"] = "running"
        assert process.stdout is not None
        os.set_blocking(process.stdout.fileno(), False)
        selector.register(process.stdout, selectors.EVENT_READ)
        while True:
            now = time.monotonic()
            reap()
            if cancelled:
                result["cancel_signal"] = signal.Signals(cancelled[0]).name
                stop("cancelled")
            # The budget includes process startup and final output collection.
            # Observing an exit after the deadline is conservatively a timeout.
            if now - started >= timeout:
                stop("timeout")
            if stopping_at is None and (now >= next_resource_poll or reaped and not checked_exit_disk):
                if not reaped and max_group_rss_bytes is not None:
                    rss, cpu = _group_rss_bytes(process.pid, cwd)
                    result["monitor_cpu_seconds"] += cpu
                    result["sampled_peak_group_rss_bytes"] = max(result["sampled_peak_group_rss_bytes"] or 0, rss)
                    if rss > max_group_rss_bytes:
                        stop("memory_limit")
                if max_workdir_bytes is not None:
                    disk = _workdir_bytes(cwd, max_workdir_bytes)
                    result["sampled_peak_workdir_bytes"] = max(result["sampled_peak_workdir_bytes"] or 0, disk)
                    if disk > max_workdir_bytes:
                        stop("disk_limit")
                checked_exit_disk = reaped
                now = time.monotonic()
                next_resource_poll = now + RESOURCE_POLL_SECONDS
                if now - started >= timeout:
                    stop("timeout")
            if reaped and stopping_at is None and group_exists():
                # Even a zero-exit worker may not leave a daemon behind.
                stop("descendants_left_running")
            if stopping_at is not None and not killed and now - stopping_at >= 0.2:
                signal_group(signal.SIGKILL)
                killed = True
            if reaped and eof and (stopping_at is None or not group_exists()):
                break
            if stopping_at is not None and now - stopping_at > 3.0:
                result["cleanup_complete"] = reaped and eof and not group_exists()
                result["cleanup_error"] = "worker reap or output closure exceeded cleanup bound"
                break
            for key, _events in selector.select(0.025):
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    eof = True
                    continue
                remaining = max_log_bytes - result["log_bytes"]
                kept = chunk[:remaining]
                while kept:
                    written = log_file.write(kept)
                    if written is None or written <= 0:
                        raise OSError("log write made no progress")
                    result["log_bytes"] += written
                    kept = kept[written:]
                if len(chunk) > remaining:
                    result["log_truncated"] = True
                    stop("log_limit")
        if result["status"] == "running":
            result["status"] = "success" if result["exit_code"] == 0 else "nonzero_exit"
    except (ValueError, TypeError) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        if process is not None:
            result["status"] = "runner_error"
    except KeyboardInterrupt:
        result["status"] = "cancelled"
        result["cancel_signal"] = "SIGINT"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        if process is not None:
            result["status"] = "runner_error"
    finally:
        # Exceptions while reading/writing still terminate and reap our worker.
        if process is not None and (not reaped or group_exists()):
            try:
                signal_group(signal.SIGKILL)
                until = time.monotonic() + 3.0
                while (not reaped or group_exists()) and time.monotonic() < until:
                    reap()
                    if not reaped or group_exists():
                        time.sleep(0.01)
                if not reaped or group_exists():
                    result["cleanup_complete"] = False
                    result["cleanup_error"] = "direct child not reaped or process group still present after SIGKILL"
            except Exception as exc:
                result["cleanup_complete"] = False
                result["cleanup_error"] = f"{type(exc).__name__}: {exc}"
        if process is not None and process.stdout is not None:
            process.stdout.close()
        selector.close()
        if log_file is not None:
            try:
                log_file.close()
            except OSError as exc:
                result["status"] = "runner_error"
                result["error"] = f"{type(exc).__name__}: {exc}"
        for signum, handler in handlers.items():
            signal.signal(signum, handler)
        if cancelled and result["status"] in ("running", "success"):
            result["status"] = "cancelled"
            result["cancel_signal"] = signal.Signals(cancelled[0]).name
        if not result["cleanup_complete"] and result["status"] == "success":
            result["status"] = "runner_error"
        result["wall_seconds"] = time.monotonic() - started
        result["supervisor_cpu_seconds"] = time.process_time() - supervisor_started
    return result
