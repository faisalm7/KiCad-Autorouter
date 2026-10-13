#!/usr/bin/env python3
"""Fresh local checkout/venv test using verified cached and installed tools.

This is a finite installation smoke test, not a new development checkout or a
fresh-Mac qualification. Run after other native/engine experiments have ended.
The source checkout must be clean and committed. No network is required.
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import re
import shutil
import signal
import stat
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autorouter import config as c, pipeline as p, placement_clearance as pc
from autorouter.runner import run


MAX_BYTES = 512 * 1024**2
# Current retained source/evidence is 16,624 files / 302,098,185 bytes.
# Preserve it under finite 18,000-file / 320 MiB source bounds; installation
# scratch remains 512 MiB. No native acceptance or secret/path guard changes.
SOURCE_MAX_BYTES = 320 * 1024**2
SOURCE_MAX_FILES = 18000
TOTAL_SECONDS = 600.0
NETWORK_DENIAL = ["/usr/bin/sandbox-exec", "-p", "(version 1)(allow default)(deny network*)"]


class Cancelled(Exception):
    pass


GUIDANCE = ("native", "placement-clearance-v1")
PLACEMENT_FIXTURE = "evidence/placement-area-native-001/allowed_placement/candidate/fixture.kicad_pcb"


def qualification(guidance):
    if guidance == "native":
        return {"guidance": guidance, "fixture": "fixtures/smoke/smoke.kicad_pcb",
                "directory": "install-native-smoke", "argv": ["--seconds", "120"]}
    if guidance == "placement-clearance-v1":
        return {"guidance": guidance, "fixture": PLACEMENT_FIXTURE,
                "directory": "install-placement-smoke", "argv": ["--seconds", "60", "--adapter", "both",
                    "--profile", "completion-only", "--guidance", guidance]}
    raise ValueError("unsupported installation qualification")


def bootstrap_runs(checkout):
    """Create the ignored scratch root required by real clean-clone tests."""
    checkout = Path(checkout)
    if not checkout.is_dir() or any(path.is_symlink() for path in (checkout, *checkout.parents)):
        raise RuntimeError("clone must be a real directory")
    runs = checkout / ".runs"
    runs.mkdir(exist_ok=False)  # A tracked/preexisting path must never be reused.
    return {"action": "bootstrap_clone_scratch", "path": str(runs), "created": True}


def git_identity(root, head, branch=None):
    """Read only this ordinary local checkout's bounded HEAD/ref/index witness.

    Git status remains the clean-check authority. This witness detects a later
    HEAD/ref/index change during another owned Git observation, not authentication
    against a concurrent actor able to replace every piece of evidence.
    """
    gitdir = Path(root) / ".git"
    if gitdir.is_symlink() or not gitdir.is_dir() or not re.fullmatch(r"[0-9a-f]{40}", head):
        raise RuntimeError("ordinary pinned local Git directory required")
    raw = pc.read_bytes(gitdir / "HEAD", 4096)
    if branch is None:
        if raw != (head + "\n").encode():
            raise RuntimeError("detached clone HEAD changed")
        reference = None
    else:
        reference = "refs/heads/" + branch
        if not re.fullmatch(r"[A-Za-z0-9_./-]+", reference) or any(part in ("", ".", "..") for part in reference.split("/")):
            raise RuntimeError("unsupported bounded source branch reference")
        if raw != ("ref: " + reference + "\n").encode():
            raise RuntimeError("source symbolic HEAD changed")
        loose = gitdir / reference
        if loose.exists() or loose.is_symlink():
            if pc.read_bytes(loose, 4096) != (head + "\n").encode():
                raise RuntimeError("source loose branch commit changed")
            resolved = head
        else:
            rows = pc.read_bytes(gitdir / "packed-refs", 2_000_000).decode("ascii").splitlines()
            matches = [row.split()[0] for row in rows if len(row.split()) == 2 and row.split()[1] == reference]
            if len(matches) != 1:
                raise RuntimeError("source branch missing or ambiguous in packed refs")
            resolved = matches[0]
        if resolved != head:
            raise RuntimeError("source branch commit changed")
    if pc.read_bytes(gitdir / "HEAD", 4096) != raw:
        raise RuntimeError("Git HEAD changed during witness read")
    return {"head_sha256": hashlib.sha256(raw).hexdigest(), "resolved_commit": head,
            "symbolic_ref": reference,
            "index_sha256": hashlib.sha256(pc.read_bytes(gitdir / "index", 32 * 1024**2)).hexdigest()}


def total_cpu():
    values = [resource.getrusage(kind) for kind in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)]
    return sum(value.ru_utime + value.ru_stime for value in values)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def read_json(path):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite JSON value: " + value)
    return json.loads(pc.read_bytes(path, 2_000_000), object_pairs_hook=pairs, parse_constant=invalid)


def preserve_publication(path):
    """Remove the canonical name before correction; preserve every old byte."""
    for original in (path, path.with_suffix(path.suffix + ".partial")):
        if original.exists() or original.is_symlink():
            index = 0
            while True:
                destination = original.with_name(original.name + ".invalidated-" + str(index))
                if not destination.exists() and not destination.is_symlink():
                    os.rename(original, destination)
                    break
                index += 1


def publish_result(out, report, stable, account, writer=None):
    """Canonical success survives only strict readback, freshness and final caps.

    The stored sample precedes final checks. Those checks and final write are
    included in the post-write acceptance cap, not in the earlier stored sample.
    """
    writer = writer or p.save_json
    path = out / "result.json"
    try:
        if path.with_suffix(path.suffix + ".partial").exists():
            preserve_publication(path)
        if report.get("passed") is True:
            stable()
        account()
        expected = canonical(report)
        writer(path, report)
        if canonical(read_json(path)) != expected:
            raise RuntimeError("installation receipt changed during publication")
        if report.get("passed") is True:
            stable()
        if canonical(read_json(path)) != expected:
            raise RuntimeError("installation receipt changed during final freshness check")
        account()  # Post-write bound check; do not pretend this is the stored sample.
    except (Exception, KeyboardInterrupt) as exc:
        preserve_publication(path)
        report.update(status="cancelled" if isinstance(exc, (Cancelled, KeyboardInterrupt)) else "failed",
                      passed=False, reason=type(exc).__name__ + ": " + str(exc))
        try:
            writer(path, report)
            if canonical(read_json(path)) != canonical(report):
                raise RuntimeError("failure publication did not verify")
        except (Exception, KeyboardInterrupt):
            # A failed rewrite must not leave a canonical success or partial.
            preserve_publication(path)
            raise
    return report


def verify_native_contract(result, selected, fixture, head):
    if result.get("accepted") is not True or result.get("tools", {}).get("git_head") != head:
        raise RuntimeError("native route did not accept the frozen checkout candidate")
    if result.get("source") != str(fixture):
        raise RuntimeError("native receipt source differs from selected fixture")
    if selected["guidance"] == "placement-clearance-v1":
        expected = {"schema": 3, "input_policy": selected["guidance"], "adapter": "both",
                    "engine_profile": "completion-only", "scoring_variant": "via_default",
                    "scope": "whole_board_unlocked_routing", "budget_seconds": 60.0,
                    "cpu_budget_seconds": 60.0, "planning_parameters": pc.parameters()}
        if any(canonical(result.get(key)) != canonical(value) for key, value in expected.items()):
            raise RuntimeError("placement installation contract differs")
    elif result.get("input_policy", "native") != "native":
        raise RuntimeError("legacy smoke unexpectedly used a different guidance policy")


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
        metadata = absolute.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError("tracked file is not regular: " + relative)
        if len(inventory) >= SOURCE_MAX_FILES:
            raise RuntimeError(f"tracked source file ceiling exceeded: {len(inventory) + 1} > {SOURCE_MAX_FILES} files at {relative}")
        if metadata.st_size > SOURCE_MAX_BYTES - total:
            raise RuntimeError(f"tracked source byte ceiling exceeded: {total + metadata.st_size} > {SOURCE_MAX_BYTES} bytes at {relative}")
        raw = pc.read_bytes(absolute, SOURCE_MAX_BYTES - total)
        total += len(raw)
        if total > SOURCE_MAX_BYTES:
            raise RuntimeError(f"tracked source byte ceiling exceeded: {total} > {SOURCE_MAX_BYTES} bytes at {relative}")
        inventory[relative] = hashlib.sha256(raw).hexdigest()
    return inventory


def install_test(out, guidance="native"):
    selected = qualification(guidance)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    cpu_started = total_cpu()
    stable = lambda: None
    report = {"schema": 2, "selected_qualification": selected, "status": "incomplete", "passed": False,
              "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "source_checkout": str(c.ROOT), "output": str(out), "commands": [], "actions": [],
              "limits": {"wall_seconds": TOTAL_SECONDS, "scratch_bytes": MAX_BYTES, "source_bytes": SOURCE_MAX_BYTES, "source_files": SOURCE_MAX_FILES, "log_bytes_per_command": 2_000_000,
                         "memory_guard": "4 GiB direct process-group polling; native pipeline applies its own per-worker guards"},
              "qualification": "Fresh local clone and Python venv on the existing Mac, not fresh OS/application installation. Official verified JAR cache and installed KiCad/Java/Python are reused. No pip dependencies or downloads.",
              "concurrency": "Shared project experiment lock; one installation command at a time. Lead keeps all other native/engine experiments idle.",
              "accounting_point": "Stored wall/CPU sample precedes final publication/freshness checks; the 600-second wall acceptance cap includes those final operations. CPU is observed, not an installation CPU cap."}
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
        argv = [str(arg) for arg in argv]
        if argv[:len(NETWORK_DENIAL)] != NETWORK_DENIAL:
            argv = [*NETWORK_DENIAL, *argv]
        result = run(argv, cwd=cwd, log=log,
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
                      "resolved_path": str(Path(sys.executable).resolve()), "sha256": p.sha(Path(sys.executable).resolve())})
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
        venv_files = {str(path): p.sha(path) for path in (python, venv / "pyvenv.cfg")}
        report["venv_files_sha256"] = venv_files
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
        report["actions"].append(bootstrap_runs(checkout))
        command("tests", [*NETWORK_DENIAL, python, "-m", "unittest", "discover", "-s", "tests", "-v"], checkout, timeout=180)
        fixture = checkout / selected["fixture"]
        fixture_hashes = p.tree_hash(fixture.parent)
        native_output = checkout / ".runs" / selected["directory"]
        command("route", [*NETWORK_DENIAL, python, "-m", "autorouter", "route", fixture,
                          "--output", native_output, *selected["argv"]], checkout, timeout=150)
        receipt = native_output / "result.json"
        native_inventory = pc.evidence_inventory(native_output)
        result = read_json(receipt)
        verify_native_contract(result, selected, fixture, head)
        report["check_result"] = json.loads(command("check-result", [*NETWORK_DENIAL, python, "-m", "autorouter", "check-result", receipt], checkout))
        if report["check_result"].get("current") is not True:
            raise RuntimeError("native result receipt failed current-file validation")
        if pc.evidence_inventory(native_output) != native_inventory:
            raise RuntimeError("native evidence changed during result check")
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
        identities = {str(directory): git_identity(directory, head, source_branch)
                      for directory, source_branch in ((c.ROOT, branch), (checkout, None))}
        report["git_identity_witnesses"] = identities
        final_logs = {step["log"]: step["log_sha256"] for step in report["commands"]}
        final_logs[str(out / "source-tracked.json")] = report["source_inventory_sha256"]
        freshness_index = 0

        def stable_material():
            for directory, source_branch in ((c.ROOT, branch), (checkout, None)):
                if git_identity(directory, head, source_branch) != identities[str(directory)]:
                    raise RuntimeError("Git HEAD/ref/index witness changed")
            if tracked_inventory(checkout, clone_listing) != original or tracked_inventory(c.ROOT, listing) != original:
                raise RuntimeError("tracked source changed during publication")
            if pc.evidence_inventory(native_output) != native_inventory or p.tree_hash(fixture.parent) != fixture_hashes:
                raise RuntimeError("native evidence or fixture changed during publication")
            for tool, digest in result["tools"]["files"].items():
                if p.sha(Path(tool)) != digest:
                    raise RuntimeError("native tool changed during publication")
            if str(Path(report["python"]["path"]).resolve()) != report["python"]["resolved_path"]:
                raise RuntimeError("original Python interpreter path changed")
            python_files = {report["python"]["resolved_path"]: report["python"]["sha256"]}
            for filename, digest in {**python_files, **venv_files, **final_logs}.items():
                if hashlib.sha256(pc.read_bytes(filename, 128 * 1024**2)).hexdigest() != digest:
                    raise RuntimeError("installation interpreter, metadata or command log changed")
            if p.sha(c.JAR) != c.JAR_SHA256:
                raise RuntimeError("original dependency cache changed")
        def stable():
            nonlocal freshness_index
            stable_material()
            # These observations have separate raw logs/receipts: do not mutate
            # the installation receipt while checking it after publication.
            for directory in (c.ROOT, checkout):
                for args, expected in ((["status", "--porcelain=v1", "--untracked-files=all"], ""), (["rev-parse", "HEAD"], head)):
                    remaining = TOTAL_SECONDS - (time.monotonic() - started)
                    if remaining <= 0:
                        raise RuntimeError("installation final freshness budget exhausted")
                    log = out / ("freshness-" + str(freshness_index) + ".log")
                    freshness_index += 1
                    step = run([*NETWORK_DENIAL, "git", "-C", str(directory), "-c", "core.hooksPath=/dev/null", *args],
                               cwd=out, log=log, timeout=min(30, remaining), env=env, max_workdir_bytes=MAX_BYTES)
                    p.save_json(log.with_suffix(".json"), {**step, "cwd": str(out), "log_sha256": p.sha(log)})
                    if step["status"] == "cancelled":
                        raise Cancelled("final Git freshness check cancelled")
                    if step["status"] != "success" or step["exit_code"] != 0 or log.read_text().strip() != expected:
                        raise RuntimeError("final Git status/HEAD no longer matches clean frozen source")
            # Git is an owned subprocess too: no data read before its final
            # observation may stand in for unchanged data after it returns.
            stable_material()
    except (Cancelled, KeyboardInterrupt) as exc:
        report.update(status="cancelled", passed=False, reason=str(exc) or "interrupted between commands")
    except Exception as exc:
        report.update(status="failed", passed=False, reason=type(exc).__name__ + ": " + str(exc))
    def account():
        report["wall_seconds"] = time.monotonic() - started
        report["total_cpu_seconds"] = total_cpu() - cpu_started
        report["command_cpu_seconds"] = sum((step.get("cpu_seconds") or 0) + (step.get("monitor_cpu_seconds") or 0) for step in report["commands"])
        report["scratch_bytes"] = directory_bytes(out)
        if report["wall_seconds"] > TOTAL_SECONDS:
            raise RuntimeError("installation wall budget exhausted")
    publish_result(out, report, stable, account)
    print(json.dumps({"status": report["status"], "passed": report["passed"], "result": str(out / "result.json")}), flush=True)
    return 0 if report["passed"] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=".runs/installation-001", help="new directory under this checkout's .runs")
    parser.add_argument("--guidance", choices=GUIDANCE, default="native", help="select exactly one native fixture qualification")
    args = parser.parse_args()
    raw = Path(args.output).absolute()
    if ".." in raw.parts or any(path.is_symlink() for path in (raw, *raw.parents)):
        parser.error("output must not use symlinks or parent traversal")
    out = raw.resolve()
    if c.ROOT / ".runs" not in out.parents:
        parser.error("output must be a new directory under this checkout's .runs")
    (c.ROOT / ".runs").mkdir(exist_ok=True)
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        with (c.ROOT / ".runs/quality-experiment.lock").open("a+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError("another project experiment holds the shared lock")
            return install_test(out, args.guidance)
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == "__main__":
    raise SystemExit(main())
