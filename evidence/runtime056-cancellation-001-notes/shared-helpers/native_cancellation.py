#!/usr/bin/env python3
"""Real engine-stage SIGINT/SIGTERM control on the project-owned smoke fixture.

Signals only the specifically spawned routing CLI PID. Native/engine execution
is real; run only in a quiet slot after other routing experiments finish.
"""

from __future__ import annotations

import argparse
import ctypes
import errno
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autorouter import config as c, pipeline as p


MAX_LOG_BYTES = 2_000_000
MAX_OUTPUT_BYTES = 512 * 1024**2


class _DarwinBSDInfo(ctypes.Structure):
    # Apple xnu bsd/sys/proc_info.h, PROC_PIDTBSDINFO (3), 136 bytes.
    # Text/credential fields are ABI padding here; never returned or inspected.
    _fields_ = [(name, ctypes.c_uint32) for name in (
        'flags', 'status', 'xstatus', 'pid', 'ppid', 'uid', 'gid', 'ruid',
        'rgid', 'svuid', 'svgid', 'reserved')]+[
        ('unused_text', ctypes.c_char * 48),
        ('nfiles', ctypes.c_uint32), ('pgid', ctypes.c_uint32),
        ('jobc', ctypes.c_uint32), ('tdev', ctypes.c_uint32),
        ('tpgid', ctypes.c_uint32), ('nice', ctypes.c_int32),
        ('start_seconds', ctypes.c_uint64), ('start_microseconds', ctypes.c_uint64)]


def owned_process_metadata(*, parent_pid: int | None = None,
                           pgid: int | None = None) -> list[dict[str, int]]:
    """Bounded Darwin PID/parent/group snapshot for a caller-owned selector.

    Supply exactly one known parent PID or process group. This is metadata,
    not ownership authentication or a persistent absence guarantee. No process
    commands, environments, global process census or signals are accessed.
    macOS denies setuid /bin/ps inside sandbox-exec; public unprivileged libproc
    leaves that sandbox intact. Apple proc_listchildpids/proc_listpgrppids return
    PID counts; PROC_PIDTBSDINFO returns the full 136-byte struct or zero/error.
    Source: apple-oss-distributions/xnu bsd/sys/proc_info.h and
    libsyscall/wrappers/libproc/libproc.c. A saturated or incomplete snapshot
    rejects; only an ESRCH exit race may omit an enumerated process.
    """
    if ((parent_pid is None) == (pgid is None)
            or any(value is not None and (type(value) is not int or not 0 < value < 2**31)
                   for value in (parent_pid, pgid))):
        raise ValueError('exactly one positive pid_t parent_pid or pgid required')
    if sys.platform != 'darwin':
        raise RuntimeError('owned process metadata requires Darwin libproc')
    if ctypes.sizeof(_DarwinBSDInfo) != 136:
        raise RuntimeError('unsupported Darwin BSD process metadata ABI')
    library = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
    listing = library.proc_listchildpids if parent_pid is not None else library.proc_listpgrppids
    listing.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
    listing.restype = ctypes.c_int
    library.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    library.proc_pidinfo.restype = ctypes.c_int
    selector = parent_pid if parent_pid is not None else pgid
    pids = (ctypes.c_int * 4096)()
    ctypes.set_errno(0)
    count = listing(selector, pids, ctypes.sizeof(pids))
    error = ctypes.get_errno()
    if count < 0 or (error and not (count == 0 and error == errno.ESRCH)):
        raise OSError(error or errno.EIO, 'libproc could not list selected owned processes')
    if count >= len(pids):
        raise RuntimeError('owned processes exceed bounded PID inventory')
    selected = list(pids)[:count]
    if any(pid <= 0 for pid in selected) or len(set(selected)) != len(selected):
        raise RuntimeError('invalid or duplicate owned-process PID inventory')
    rows = []
    for pid in selected:
        info = _DarwinBSDInfo()
        ctypes.set_errno(0)
        size = library.proc_pidinfo(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info))
        error = ctypes.get_errno()
        if size == 0 and error == errno.ESRCH:
            continue
        if size != ctypes.sizeof(info) or error:
            raise OSError(error or errno.EIO, 'libproc returned incomplete owned-process metadata')
        row = {'pid': int(info.pid), 'ppid': int(info.ppid), 'pgid': int(info.pgid)}
        if (row['pid'] != pid or not 0 < row['pid'] < 2**31
                or not 0 <= row['ppid'] < 2**31 or not 0 < row['pgid'] < 2**31
                or (parent_pid is not None and row['ppid'] != parent_pid)
                or (pgid is not None and row['pgid'] != pgid)):
            raise RuntimeError('owned-process identity or selector changed during snapshot')
        rows.append(row)
    return sorted(rows, key=lambda row: row['pid'])


def process_metadata(*, parent_pid=None, pgid=None):
    """Read bounded owned PID lineage/group metadata; never commands or env."""
    if ((parent_pid is None)==(pgid is None)
            or any(type(value) is not int or value<=0 for value in (parent_pid,pgid) if value is not None)):
        raise ValueError('exactly one positive owned parent PID or process group required')
    if sys.platform=='darwin':
        return owned_process_metadata(parent_pid=parent_pid,pgid=pgid)
    result = subprocess.run(["/bin/ps", "-axo", "pid=,ppid=,pgid="],
                            stdin=subprocess.DEVNULL, capture_output=True, text=True,
                            timeout=2, check=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
    if len(result.stdout) > 1_000_000:
        raise RuntimeError("process metadata exceeds control bound")
    rows = []
    for line in result.stdout.splitlines():
        pid, parent, group = map(int, line.split())
        if parent_pid is not None and parent!=parent_pid or pgid is not None and group!=pgid:continue
        rows.append({"pid": pid, "ppid": parent, "pgid": group})
    return rows


def output_bytes(root):
    total = 0
    for parent, directories, files in os.walk(root, followlinks=False):
        directories[:] = [name for name in directories if not (Path(parent) / name).is_symlink()]
        for name in files:
            item = (Path(parent) / name).lstat()
            if stat.S_ISREG(item.st_mode):
                total += item.st_size
                if total > MAX_OUTPUT_BYTES:
                    raise RuntimeError("control output exceeds 512 MiB polling bound")
    return total


def control(out, cancel_signal=signal.SIGINT):
    if cancel_signal not in (signal.SIGINT,signal.SIGTERM):raise ValueError('unsupported control signal')
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    source = c.ROOT / "fixtures/smoke/smoke.kicad_pcb"
    route_out = out / "route"
    log = out / "cli.log"
    report = {"schema": 1, "status": "incomplete", "passed": False,
              "control": "real CLI "+signal.Signals(cancel_signal).name+" during owned engine execution",
              "source": str(source), "signals": [], "output": str(out),
              "limitations": "Only engine-stage cancellation is tested. Interstage cancellation, editor cancellation and OS crashes are not qualified. PID/group absence is an immediate observation, not a persistent monitor."}
    child = None
    owned_engine = None
    frozen = None
    before = None

    def signal_cli(signum):
        if child is not None and child.poll() is None:
            # An unreaped Popen child has not had its PID recycled.
            os.kill(child.pid, signum)
            report["signals"].append({"pid": child.pid, "signal": signal.Signals(signum).name,
                                      "elapsed_seconds": time.monotonic() - started})

    def wait_cli(until):
        while child.poll() is None and time.monotonic() < until:
            time.sleep(0.05)
        return child.poll() is not None

    try:
        p.check_storage()
        before = p.tree_hash(source.parent)
        frozen = p.tool_manifest()
        report.update(source_hashes=before, tools=frozen, script_sha256=p.sha(Path(__file__)))
        argv = [sys.executable, "-m", "autorouter", "route", str(source),
                "--output", str(route_out), "--seconds", "120"]
        report["argv"] = argv
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
        with log.open("xb", buffering=0) as stream:
            child = subprocess.Popen(argv, cwd=c.ROOT, env=env, stdin=subprocess.DEVNULL,
                                     stdout=stream, stderr=subprocess.STDOUT,
                                     start_new_session=True, close_fds=True, shell=False)
            report["cli_pid"] = child.pid
            p.save_json(out / "control.json", report)
            engine_log = route_out / "engine.log"
            startup_deadline = started + 60
            next_guard = started
            while child.poll() is None and time.monotonic() < startup_deadline:
                if time.monotonic() >= next_guard:
                    if log.stat().st_size > MAX_LOG_BYTES:
                        raise RuntimeError("CLI log exceeds control bound")
                    output_bytes(out)
                    next_guard = time.monotonic() + 0.25
                # A nonempty log demonstrates the actual engine ran, whereas
                # mere file creation precedes runner.Popen and is insufficient.
                if engine_log.is_file() and engine_log.stat().st_size > 0 and not (route_out / "engine-process.json").exists():
                    candidates = [row for row in process_metadata(parent_pid=child.pid)
                                  if row["ppid"] == child.pid and row["pid"] == row["pgid"]]
                    if len(candidates) == 1 and child.poll() is None:
                        owned_engine = candidates[0]
                        report["observed_owned_engine"] = owned_engine
                        report["engine_log_bytes_at_signal"] = engine_log.stat().st_size
                        report["engine_observed_elapsed_seconds"] = time.monotonic() - started
                        signal_cli(cancel_signal)
                        break
                time.sleep(0.01)
            if owned_engine is None:
                raise RuntimeError("did not observe a running engine before CLI exit/startup deadline")
            if not wait_cli(time.monotonic() + 15):
                raise RuntimeError("CLI did not finish within 15 seconds after requested cancellation")
        report["cli_exit_code"] = child.returncode
        receipt_path = route_out / "result.json"
        engine_receipt_path = route_out / "engine-process.json"
        result = json.loads(receipt_path.read_text())
        engine = json.loads(engine_receipt_path.read_text())
        report["route_receipt"] = {"path": str(receipt_path), "sha256": p.sha(receipt_path)}
        report["engine_receipt"] = {"path": str(engine_receipt_path), "sha256": p.sha(engine_receipt_path), "data": engine}
        report["route_status"] = result.get("status")
        report["route_accepted"] = result.get("accepted")
        report["source_unchanged"] = p.tree_hash(source.parent) == before
        report["tools_and_code_unchanged"] = p.tool_manifest() == frozen
        remaining = [row for row in process_metadata(pgid=owned_engine["pgid"]) if row["pgid"] == owned_engine["pgid"]]
        report["remaining_owned_engine_group"] = remaining
        report["checks"] = {
            "cli_rejected": child.returncode == 2 and result.get("accepted") is False,
            "engine_pid_bound": engine.get("pid") == owned_engine["pid"],
            "engine_cancelled_by_requested_signal": engine.get("status") == "cancelled" and engine.get("cancel_signal") == signal.Signals(cancel_signal).name,
            "runner_cleanup_complete": engine.get("cleanup_complete") is True,
            "engine_group_absent": not remaining,
            "source_unchanged": report["source_unchanged"],
            "tools_and_code_unchanged": report["tools_and_code_unchanged"],
        }
        report["passed"] = all(report["checks"].values())
        report["status"] = "passed" if report["passed"] else "failed"
    except KeyboardInterrupt:
        report.update(status="cancelled", passed=False, reason="control interrupted")
    except Exception as exc:
        report.update(status="failed", passed=False, reason=type(exc).__name__ + ": " + str(exc))
    finally:
        if child is not None and child.poll() is None:
            # Signal only our CLI; its runner owns termination of native worker
            # groups. Allow that bounded cleanup before the final own-PID fallback.
            signal_cli(cancel_signal)
            if not wait_cli(time.monotonic() + 5):
                signal_cli(signal.SIGTERM)
                if not wait_cli(max(time.monotonic() + 5, started + 130)):
                    signal_cli(signal.SIGKILL)
                    child.wait(timeout=5)
            report["cli_exit_code"] = child.returncode
        if before is not None:
            try:
                report["source_unchanged"] = p.tree_hash(source.parent) == before
                if not report["source_unchanged"]:
                    report.update(status="failed", passed=False)
            except Exception as exc:
                report["source_check_error"] = str(exc)
                report.update(status="failed", passed=False)
        if owned_engine is not None:
            try:
                remaining = [row for row in process_metadata(pgid=owned_engine["pgid"]) if row["pgid"] == owned_engine["pgid"]]
                report["remaining_owned_engine_group"] = remaining
                if remaining:
                    report.update(status="cleanup_unproven", passed=False)
            except Exception as exc:
                report.update(status="cleanup_unproven", passed=False, cleanup_check_error=str(exc))
        report["wall_seconds"] = time.monotonic() - started
        if log.is_file():
            report["cli_log_sha256"] = p.sha(log)
        try:
            report["output_bytes"] = output_bytes(out)
        except Exception as exc:
            report.update(status="failed", passed=False, output_size_error=str(exc))
        p.save_json(out / "control.json", report)
    print(json.dumps({"status": report["status"], "passed": report["passed"], "control": str(out / "control.json")}), flush=True)
    return 0 if report["passed"] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="new directory under this checkout's .runs")
    parser.add_argument("--signal",choices=['SIGINT','SIGTERM'],default='SIGINT',help='signal only the CLI spawned by this control')
    args = parser.parse_args()
    out = Path(args.output).resolve()
    if c.ROOT / ".runs" not in out.parents:
        parser.error("output must be a new directory under this checkout's .runs")
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        return control(out,getattr(signal,args.signal))
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == "__main__":
    raise SystemExit(main())
