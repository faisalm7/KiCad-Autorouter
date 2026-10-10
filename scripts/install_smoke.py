#!/usr/bin/env python3
"""Fresh local checkout/venv test using verified cached and installed tools.

This is a finite installation smoke test, not a new development checkout or a
fresh-Mac qualification. Run after other native/engine experiments have ended.
The source checkout must be clean and committed. No network is required.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import stat
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autorouter import config as c, pipeline as p
from autorouter.runner import run


MAX_BYTES = 512 * 1024**2
TOTAL_SECONDS = 600.0
NETWORK_DENIAL = ["/usr/bin/sandbox-exec", "-p", "(version 1)(allow default)(deny network*)"]


class Cancelled(Exception):
    pass


def directory_bytes(root):
    total = 0
    for parent, directories, files in os.walk(root, followlinks=False):
        directories[:] = [name for name in directories if not (Path(parent) / name).is_symlink()]
        for name in files:
            metadata = (Path(parent) / name).lstat()
            if stat.S_ISREG(metadata.st_mode):
                total += metadata.st_size
                if total > MAX_BYTES:
                    raise RuntimeError("installation scratch exceeds 512 MiB logical file ceiling")
    return total


def tracked_inventory(root, listing):
    inventory, total = {}, 0
    for relative in listing.split("\0"):
        if not relative:
            continue
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or any((root / Path(*path.parts[:i])).is_symlink() for i in range(1, len(path.parts) + 1)):
            raise RuntimeError("unsafe tracked path")
        absolute = root / path
        if not absolute.is_file():
            raise RuntimeError("tracked file missing: " + relative)
        total += absolute.stat().st_size
        if total > 128 * 1024**2 or len(inventory) >= 10000:
            raise RuntimeError("tracked source inventory exceeds installation test bound")
        inventory[relative] = p.sha(absolute)
    return inventory


def install_test(out):
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = {"schema": 1, "status": "incomplete", "passed": False,
              "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "source_checkout": str(c.ROOT), "output": str(out), "commands": [], "actions": [],
              "limits": {"wall_seconds": TOTAL_SECONDS, "scratch_bytes": MAX_BYTES, "log_bytes_per_command": 2_000_000,
                         "memory_guard": "4 GiB direct process-group polling; native pipeline applies its own per-worker guards"},
              "qualification": "Fresh local clone and Python venv on the existing Mac, not fresh OS/application installation. Official verified JAR cache and installed KiCad/Java/Python are reused. No pip dependencies or downloads.",
              "concurrency": "One installation command at a time; lead must keep other native/engine experiments idle."}
    env = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(name, None)
    env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PIP_NO_INDEX="1",
               GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_TERMINAL_PROMPT="0")
    template = out / "empty-git-template"
    template.mkdir()
    env["GIT_TEMPLATE_DIR"] = str(template)
    for key, name in (("KICAD_CONFIG_HOME", "kicad-config"), ("KICAD_CACHE_HOME", "kicad-cache"), ("KICAD_DOCUMENTS_HOME", "kicad-documents")):
        directory = out / name
        (directory / ("10.0" if key == "KICAD_CONFIG_HOME" else "kicad/10.0")).mkdir(parents=True)
        env[key] = str(directory)

    def command(name, argv, cwd, timeout=60):
        remaining = TOTAL_SECONDS - (time.monotonic() - started)
        if remaining <= 0:
            raise RuntimeError("installation test wall budget exhausted")
        directory_bytes(out)
        log = out / (f"{len(report['commands']):02d}-" + name + ".log")
        result = run([str(arg) for arg in argv], cwd=cwd, log=log,
                     timeout=min(timeout, remaining), env=env, max_workdir_bytes=MAX_BYTES)
        result.update(name=name, cwd=str(cwd), log_sha256=p.sha(log) if log.is_file() else None)
        report["commands"].append(result)
        p.save_json(out / "result.json", report)
        directory_bytes(out)
        if result["status"] == "cancelled":
            raise Cancelled(name + " cancelled")
        if result["status"] != "success" or result["exit_code"] != 0:
            raise RuntimeError(name + ": " + result["status"] + " exit=" + str(result["exit_code"]))
        return log.read_text()

    def git(name, root, *args):
        # Monitor only this bounded scratch directory, not the durable source's
        # intentionally larger dependency/data/evidence caches.
        return command(name, ["git", "-C", root, "-c", "core.hooksPath=/dev/null", *args], out)

    try:
        if platform.system() != "Darwin" or sys.version_info[:2] != (3, 11):
            raise RuntimeError("installation test requires this Mac and Python 3.11")
        p.check_storage()
        if git("source-status", c.ROOT, "status", "--porcelain=v1", "--untracked-files=all").strip():
            raise RuntimeError("commit all source checkout changes before installation test")
        head = git("source-head", c.ROOT, "rev-parse", "HEAD").strip()
        branch = git("source-branch", c.ROOT, "symbolic-ref", "--short", "HEAD").strip()
        listing = git("source-files", c.ROOT, "ls-files", "-z")
        original = tracked_inventory(c.ROOT, listing)
        report.update(git_head=head, source_branch=branch, python={"version": sys.version, "path": sys.executable,
                      "sha256": p.sha(Path(sys.executable).resolve())})
        p.save_json(out / "source-tracked.json", original)
        report["source_inventory_sha256"] = p.sha(out / "source-tracked.json")
        if c.JAR.is_symlink() or c.JAR.parent.is_symlink() or not c.JAR.is_file() or p.sha(c.JAR) != c.JAR_SHA256:
            raise RuntimeError("existing official JAR cache is absent, symlinked or not pinned")
        report["cached_dependency"] = {"path": str(c.JAR), "sha256": c.JAR_SHA256, "bytes": c.JAR.stat().st_size,
                                       "mode": "copy verified official release asset; acquisition not retested"}

        checkout = out / "checkout"
        command("clone", ["git", "-c", "core.hooksPath=/dev/null", "clone", "--no-local", "--no-hardlinks",
                          "--no-checkout", "--no-tags", "--single-branch", "--branch", branch, str(c.ROOT), str(checkout)], out)
        git("checkout-pinned-head", checkout, "checkout", "--quiet", "--detach", head)
        if git("clone-head", checkout, "rev-parse", "HEAD").strip() != head:
            raise RuntimeError("clone HEAD differs from frozen source")
        clone_listing = git("clone-files", checkout, "ls-files", "-z")
        if tracked_inventory(checkout, clone_listing) != original:
            raise RuntimeError("cloned tracked files differ from source inventory")
        if git("clone-initial-status", checkout, "status", "--porcelain=v1", "--untracked-files=all").strip():
            raise RuntimeError("new clone is not clean")

        venv = checkout / ".venv"
        command("venv", [sys.executable, "-m", "venv", "--copies", "--without-pip", str(venv)], checkout)
        python = venv / "bin/python"
        environment = json.loads(command("venv-identity", [python, "-c",
            "import json,sys; print(json.dumps({'version':sys.version,'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix}))"], checkout))
        if Path(environment["prefix"]).resolve() != venv.resolve() or environment["prefix"] == environment["base_prefix"]:
            raise RuntimeError("command did not use the fresh virtual environment")
        report["venv"] = environment
        destination = checkout / ".tools" / c.JAR.name
        destination.parent.mkdir()
        with c.JAR.open("rb") as source, destination.open("xb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
            target.flush()
            os.fsync(target.fileno())
        if p.sha(destination) != c.JAR_SHA256 or destination.stat().st_ino == c.JAR.stat().st_ino:
            raise RuntimeError("dependency copy did not verify as an independent file")
        report["actions"].append({"action": "copy_cached_engine", "source": str(c.JAR), "destination": str(destination), "sha256": p.sha(destination), "hardlinked": False})
        command("setup-engine-offline", [*NETWORK_DENIAL, python, "scripts/setup_engine.py"], checkout)
        report["doctor"] = json.loads(command("doctor", [*NETWORK_DENIAL, python, "-m", "autorouter", "doctor"], checkout))
        if report["doctor"].get("ready") is not True:
            raise RuntimeError("fresh-checkout doctor is not ready")
        command("tests", [*NETWORK_DENIAL, python, "-m", "unittest", "discover", "-s", "tests", "-v"], checkout, timeout=180)
        fixture = checkout / "fixtures/smoke/smoke.kicad_pcb"
        fixture_hashes = p.tree_hash(fixture.parent)
        native_output = checkout / ".runs/install-native-smoke"
        command("route", [*NETWORK_DENIAL, python, "-m", "autorouter", "route", fixture,
                          "--output", native_output, "--seconds", "120"], checkout, timeout=150)
        receipt = native_output / "result.json"
        result = json.loads(receipt.read_text())
        if result.get("accepted") is not True or result.get("tools", {}).get("git_head") != head:
            raise RuntimeError("native route did not accept the frozen checkout candidate")
        report["check_result"] = json.loads(command("check-result", [*NETWORK_DENIAL, python, "-m", "autorouter", "check-result", receipt], checkout))
        if report["check_result"].get("current") is not True:
            raise RuntimeError("native result receipt failed current-file validation")
        if p.tree_hash(fixture.parent) != fixture_hashes:
            raise RuntimeError("native smoke modified its source fixture")
        report["native"] = {key: result.get(key) for key in ("status", "accepted", "metrics", "native", "wall_seconds", "total_cpu_seconds", "candidate_sha256", "native_report_sha256", "tools")}
        report["native_receipt"] = {"path": str(receipt), "sha256": p.sha(receipt)}
        if tracked_inventory(checkout, clone_listing) != original or tracked_inventory(c.ROOT, listing) != original:
            raise RuntimeError("tracked source changed during installation test")
        for name, directory in (("clone-final-status", checkout), ("source-final-status", c.ROOT)):
            if git(name, directory, "status", "--porcelain=v1", "--untracked-files=all").strip():
                raise RuntimeError("checkout is no longer clean: " + str(directory))
            if git(name + "-head", directory, "rev-parse", "HEAD").strip() != head:
                raise RuntimeError("checkout HEAD changed during installation test")
        report.update(status="passed", passed=True, tracked_source_unchanged=True, cloned_tracked_files_unchanged=True)
    except (Cancelled, KeyboardInterrupt) as exc:
        report.update(status="cancelled", passed=False, reason=str(exc) or "interrupted between commands")
    except Exception as exc:
        report.update(status="failed", passed=False, reason=type(exc).__name__ + ": " + str(exc))
    report["wall_seconds"] = time.monotonic() - started
    report["command_cpu_seconds"] = sum((step.get("cpu_seconds") or 0) + (step.get("monitor_cpu_seconds") or 0) for step in report["commands"])
    try:
        report["scratch_bytes"] = directory_bytes(out)
    except Exception as exc:
        report.update(status="failed", passed=False, final_size_error=str(exc))
    if report["wall_seconds"] > TOTAL_SECONDS:
        report.update(status="timeout", passed=False)
    p.save_json(out / "result.json", report)
    print(json.dumps({"status": report["status"], "passed": report["passed"], "result": str(out / "result.json")}), flush=True)
    return 0 if report["passed"] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=".runs/installation-001", help="new directory under this checkout's .runs")
    args = parser.parse_args()
    out = Path(args.output).resolve()
    if c.ROOT / ".runs" not in out.parents:
        parser.error("output must be a new directory under this checkout's .runs")
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        return install_test(out)
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == "__main__":
    raise SystemExit(main())
