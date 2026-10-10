#!/usr/bin/env python3
"""Real engine-stage SIGTERM control on the project-owned floor fixture.

Signals only the specifically spawned routing CLI PID. Native/engine execution
is real; run only in a quiet slot after other routing experiments finish.
"""

from __future__ import annotations

import argparse
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


def process_metadata():
    """Read PID lineage/group metadata only; never process arguments or env."""
    result = subprocess.run(["/bin/ps", "-axo", "pid=,ppid=,pgid="],
                            stdin=subprocess.DEVNULL, capture_output=True, text=True,
                            timeout=2, check=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
    if len(result.stdout) > 1_000_000:
        raise RuntimeError("process metadata exceeds control bound")
    rows = []
    for line in result.stdout.splitlines():
        pid, parent, group = map(int, line.split())
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


def control(out):
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    source = c.ROOT / "tests/fixtures/board-floor/fixture.kicad_pcb"
    route_out = out / "route"
    log = out / "cli.log"
    report = {"schema": 1, "status": "incomplete", "passed": False,
              "control": "real CLI SIGTERM during owned engine execution",
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
                "--output", str(route_out), "--seconds", "60", "--adapter", "both", "--profile", "completion-only", "--guidance", "board-floors-v1"]
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
                    candidates = [row for row in process_metadata()
                                  if row["ppid"] == child.pid and row["pid"] == row["pgid"]]
                    if len(candidates) == 1 and child.poll() is None:
                        owned_engine = candidates[0]
                        report["observed_owned_engine"] = owned_engine
                        report["engine_log_bytes_at_signal"] = engine_log.stat().st_size
                        report["engine_observed_elapsed_seconds"] = time.monotonic() - started
                        signal_cli(signal.SIGTERM)
                        break
                time.sleep(0.01)
            if owned_engine is None:
                raise RuntimeError("did not observe a running engine before CLI exit/startup deadline")
            if not wait_cli(time.monotonic() + 15):
                raise RuntimeError("CLI did not finish within 15 seconds after SIGTERM")
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
        remaining = [row for row in process_metadata() if row["pgid"] == owned_engine["pgid"]]
        report["remaining_owned_engine_group"] = remaining
        report["checks"] = {
            "cli_rejected": child.returncode == 2 and result.get("accepted") is False,
            "engine_pid_bound": engine.get("pid") == owned_engine["pid"],
            "engine_cancelled_by_sigint": engine.get("status") == "cancelled" and engine.get("cancel_signal") == "SIGTERM",
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
            signal_cli(signal.SIGTERM)
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
                remaining = [row for row in process_metadata() if row["pgid"] == owned_engine["pgid"]]
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
    args = parser.parse_args()
    out = Path(args.output).resolve()
    if c.ROOT / ".runs" not in out.parents:
        parser.error("output must be a new directory under this checkout's .runs")
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGTERM)}
    try:
        return control(out)
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == "__main__":
    raise SystemExit(main())
