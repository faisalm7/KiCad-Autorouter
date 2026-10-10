#!/usr/bin/env python3
"""One sequential KRT capability experiment; no generalized comparison claim."""
import argparse
import copy
import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autorouter import config as c, sexpr as sx
from autorouter.pipeline import (Job, Rejected, ROUTES, DERIVED_ZONE, check_storage,
                                immutable, locked, preflight, routes, save_json,
                                sha, tool_manifest, transplant_routes, tree_hash,
                                validate_candidate)
from scripts.setup_krt import PACKAGES, SOURCE as KRT, VENV


def pretty(node, depth=0):
    """Preserve every atom while exposing KiCad-style line starts to KRT."""
    if isinstance(node, str):
        return node
    if not any(isinstance(n, list) for n in node):
        return sx.dump(node)
    result = "("
    for i, value in enumerate(node):
        if isinstance(value, list):
            result += "\n" + "\t" * (depth + 1) + pretty(value, depth + 1)
        else:
            result += (" " if i else "") + value
    return result + "\n" + "\t" * depth + ")"


def environment(job):
    env = {k: v for k, v in job.env.items() if not k.startswith("KICAD_") and k not in ("PYTHONPATH", "PYTHONHOME", "REDO_MANIFEST")}
    for key in ("KICAD_CONFIG_HOME", "KICAD_CACHE_HOME", "KICAD_DOCUMENTS_HOME"):
        env[key] = job.env[key]
    env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
               NUMEXPR_NUM_THREADS="1", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
               KICAD_RIP_PREEXISTING="0", KICAD_FINALIZE_RIP="0",
               KICAD_CLI=str(c.CLI), KICAD_PYTHON=str(c.PYTHON))
    temporary = job.out / "tmp"
    temporary.mkdir()
    env["TMPDIR"] = str(temporary)
    job.env = env


def child_job(root, name, deadline, report):
    remaining = deadline - time.monotonic()
    diagnostic = remaining < 15
    job = Job(root / name, 60 if diagnostic else remaining)
    environment(job)
    if diagnostic:
        report["diagnostic_budget_added_seconds"] += 60
        report["comparative_budget_eligible"] = False
    return job, diagnostic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(c.ROOT / ".runs/krt-spike-001"))
    parser.add_argument("--pretty-input", action="store_true", help="Use semantically identical conventional newlines and record parser-only probe")
    args = parser.parse_args()
    started, cpu_started = time.monotonic(), time.process_time()
    output = Path(args.output).resolve()
    if output.parent != c.ROOT / ".runs":
        raise Rejected("Output must be a new direct child of .runs")
    check_storage()
    source = c.ROOT / ".runs/sonde-stock-002/snapshot/sonde xilinx.kicad_pcb"
    prior = json.loads((c.ROOT / ".runs/sonde-stock-002/result.json").read_text())
    before = tree_hash(source.parent)
    if before != prior["source_hashes"]:
        raise Rejected("Prior source snapshot is stale")
    original = preflight(source)
    manifest = tool_manifest()
    job = Job(output, 120)
    job.started, job.deadline, job.cpu_started = started, started + 120, cpu_started
    environment(job)
    all_jobs = [job]
    code = output / "code"
    code.mkdir()
    for path in (c.ROOT / "autorouter").glob("*.py"):
        shutil.copy2(path, code / path.name)
    shutil.copy2(__file__, code / "experiment_krt.py")
    shutil.copy2(c.ROOT / "scripts/setup_krt.py", code / "setup_krt.py")
    report = {"schema": 1, "experiment": "KRT 0.23.0 sonde development capability spike",
              "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "source": str(source), "source_hashes": before, "budget_seconds": 120,
              "comparative_budget_eligible": True, "diagnostic_budget_added_seconds": 0,
              "general_superiority_established": False, "tools": manifest,
              "implementation_sha256": {p.name: sha(p) for p in code.iterdir()},
              "physical_electrical_validation": False, "schematic_parity": "not checked",
              "settings": {"escalation": "off", "drc_writeback": False, "fab_tier": "standard",
                           "max_iterations": 100000, "max_ripup": 3,
                           "pretty_input": args.pretty_input},
              "environment_overrides": {k: v for k, v in job.env.items() if k.startswith("KICAD_") or k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "TMPDIR")}}
    try:
        report["krt_binary_sha256"] = sha(KRT / "rust_router/grid_router.so")
        if report["krt_binary_sha256"] != PACKAGES[1][2]:
            raise Rejected("KRT extension differs from pin")
        report["krt_source_sha256"] = tree_hash(KRT)
        shutil.copytree(source.parent, output / "snapshot")
        shutil.copytree(source.parent, output / "task-input")
        shutil.copytree(source.parent, output / "raw-output")
        task = copy.deepcopy(original)
        task[:] = [n for n in task if not isinstance(n, list) or not n or n[0] not in ROUTES or locked(n)]
        for zone in sx.children(task, "zone"):
            zone[:] = [n for n in zone if not isinstance(n, list) or not n or n[0] not in DERIVED_ZONE]
        protected = copy.deepcopy(routes(task))
        board = output / "task-input" / source.name
        sx.write(board, task)
        if args.pretty_input:
            single_line = output / "parser-single-line.kicad_pcb"
            shutil.copy2(board, single_line)
            board.write_text(pretty(task) + "\n")
            if sx.read(board) != task or sx.read(single_line) != task:
                raise Rejected("Pretty formatting changed semantic tree")
            probe = output / "parser-probe.py"
            probe.write_text("import json, sys\nfrom pathlib import Path\nsys.path.insert(0, sys.argv[1])\nfrom kicad_parser import parse_kicad_pcb\nresult = {}\nfor name, path in zip(('single_line', 'pretty'), sys.argv[2:4]):\n    pcb = parse_kicad_pcb(path)\n    result[name] = {'zones': len(pcb.zones), 'footprints': len(pcb.footprints), 'pads': sum(len(p) for p in pcb.pads_by_net.values()), 'nets': len(pcb.nets)}\nPath(sys.argv[4]).write_text(json.dumps(result, indent=2) + '\\n')\nprint(json.dumps(result))\n")
            report["implementation_sha256"]["parser-probe.py"] = sha(probe)
            job.step("parser-probe", ["/usr/bin/sandbox-exec", "-p", "(version 1)(allow default)(deny network*)",
                                      VENV / "bin/python", probe, KRT / "py_router", single_line, board, output / "parser-probe.json"])
            report["parser_probe"] = json.loads((output / "parser-probe.json").read_text())
            report["parser_probe"]["semantic_trees_equal"] = True
            if report["parser_probe"]["pretty"]["zones"] != len(sx.children(task, "zone")):
                raise Rejected("Pretty input still does not expose all zones to KRT")
        task_before = tree_hash(board.parent)
        report["task_sha256"] = sha(board)
        raw = output / "raw-output" / source.name
        raw.unlink()  # Only the newly copied placeholder; original is untouched.
        argv = ["/usr/bin/sandbox-exec", "-p", "(version 1)(allow default)(deny network*)",
                VENV / "bin/python", KRT / "py_router/route.py", board, "--output", raw,
                "--nets", "*", "--layers", "F.Cu", "B.Cu", "--no-fix-drc-settings",
                "--escalation", "off", "--fab-tier", "standard", "--strict-sizes",
                "--keep-input-copper", "--no-stub-layer-swap", "--max-iterations", "100000",
                "--max-ripup", "3", "--json-out", output / "engine-stats.json"]
        engine_error = None
        try:
            engine_result = job.step("engine", argv, allowed=(0, 1, 2, 3))
            if engine_result["exit_code"] != 0:
                engine_error = "nonzero_exit: " + str(engine_result["exit_code"])
        except Exception as exc:
            engine_error = str(exc)
        report["engine_error"] = engine_error
        report["task_input_unchanged"] = tree_hash(board.parent) == task_before
        if not report["task_input_unchanged"]:
            report["task_input_after"] = tree_hash(board.parent)
        report["raw"] = {"exists": raw.is_file(), "accepted": False}
        if raw.is_file():
            raw_tree = sx.read(raw)
            raw_hashes = tree_hash(raw.parent)
            expected = dict(before)
            expected[source.name] = sha(raw)
            report["raw"].update(candidate=str(raw), candidate_sha256=sha(raw),
                                 immutable_equal=immutable(raw_tree) == immutable(original),
                                 project_files_equal=raw_hashes == expected,
                                 protected_equal=all(n in routes(raw_tree) for n in protected),
                                 route_items=len(routes(raw_tree)), project_hashes=raw_hashes)
            raw_job, diagnostic = child_job(output, "raw-validation", job.deadline, report)
            all_jobs.append(raw_job)
            report["raw"]["native_diagnostic_extra_budget"] = diagnostic
            try:
                native = raw_job.drc("native-diagnostic", raw)
                report["raw"]["native"] = native
                report["raw"]["native_report_sha256"] = sha(raw_job.out / "native-diagnostic.json")
                report["raw"]["accepted"] = bool(report["raw"]["immutable_equal"] and report["raw"]["project_files_equal"] and report["raw"]["protected_equal"] and not native["opens"] and not native["blocking"] and not native["exclusions"] and engine_error is None and report["task_input_unchanged"])
            except Exception as exc:
                report["raw"]["native_error"] = type(exc).__name__ + ": " + str(exc)
            # A separately recorded adapter experiment, never replacing raw output.
            adapted_job, diagnostic = child_job(output, "route-transfer-validation", job.deadline, report)
            all_jobs.append(adapted_job)
            candidate_dir = adapted_job.out / "candidate"
            shutil.copytree(source.parent, candidate_dir)
            candidate = candidate_dir / source.name
            sx.write(candidate, transplant_routes(task, raw_tree))
            adapted = {"label": "KRT routes-only transfer onto pristine task",
                       "candidate": str(candidate), "accepted": False,
                       "diagnostic_extra_budget": diagnostic,
                       "includes_entire_raw_attempt_cost": True}
            report["route_transfer"] = adapted
            try:
                final_hash, native = validate_candidate(adapted_job, original, candidate, before, protected)
                adapted.update(candidate_sha256=final_hash, native=native,
                               native_report_sha256=sha(adapted_job.out / "final-drc.json"))
                adapted_job.native("metrics", "metrics", candidate, adapted_job.out / "metrics.json")
                adapted["metrics"] = json.loads((adapted_job.out / "metrics.json").read_text())
                adapted["accepted"] = not native["opens"] and not native["blocking"] and not native["exclusions"] and engine_error is None and report["task_input_unchanged"]
            except Exception as exc:
                adapted["reason"] = type(exc).__name__ + ": " + str(exc)
        else:
            report["raw"]["reason"] = "engine emitted no candidate"
        report["source_unchanged"] = tree_hash(source.parent) == before
        report["snapshot_unchanged"] = tree_hash(output / "snapshot") == before
        if not report["source_unchanged"] or not report["snapshot_unchanged"]:
            raise Rejected("Source or preserved snapshot changed")
    except Exception as exc:
        report["error"] = type(exc).__name__ + ": " + str(exc)
    report["steps"] = [step for j in all_jobs for step in j.steps]
    report["wall_seconds"] = time.monotonic() - started
    report["parent_cpu_seconds"] = time.process_time() - cpu_started
    report["child_cpu_seconds"] = sum(s.get("cpu_seconds") or 0 for s in report["steps"])
    report["monitor_cpu_seconds"] = sum(s.get("monitor_cpu_seconds") or 0 for s in report["steps"])
    report["total_cpu_seconds"] = report["parent_cpu_seconds"] + report["child_cpu_seconds"] + report["monitor_cpu_seconds"]
    report["peak_child_rss_bytes"] = max([s.get("max_rss_bytes") or 0 for s in report["steps"]] + [0])
    if report["wall_seconds"] > 120:
        report["comparative_budget_eligible"] = False
    report["interpretation"] = "Single exposed development family; capability/diagnostic result only. Raw engine and route-only adapter outcomes are distinct."
    save_json(output / "result.json", report)
    print(json.dumps({k: v for k, v in report.items() if k in ("error", "engine_error", "wall_seconds", "total_cpu_seconds", "comparative_budget_eligible", "source_unchanged", "snapshot_unchanged")}, indent=2))
    for name in ("raw", "route_transfer"):
        r = report.get(name, {})
        native = r.get("native", {})
        print(json.dumps({"variant": name, "accepted": r.get("accepted"), "immutable_equal": r.get("immutable_equal"), "opens": native.get("opens"), "blocking": native.get("blocking"), "reason": r.get("reason", r.get("native_error"))}, indent=2))


if __name__ == "__main__":
    main()
