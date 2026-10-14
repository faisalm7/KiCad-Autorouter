#!/usr/bin/env python3
"""Predeclared sequential development comparison; never a holdout evaluation.

Run only after committing the exact implementation and this protocol script.
Every arm gets the same 120-second wall and measured-CPU acceptance ceilings.
This process runs at most one engine at a time; the operator must keep other
native experiments idle. A kernel lock prevents two copies of this script.
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autorouter import config as c, pipeline as p
from autorouter.strategy import prune


BUDGET = 120.0
ARMS = (
    {"id": "B0", "adapter": "none", "engine_profile": "standard", "operation": "route"},
    {"id": "B1", "adapter": "both", "engine_profile": "standard", "operation": "route"},
    {"id": "B2", "adapter": "both", "engine_profile": "tuned", "operation": "route"},
    {"id": "C", "adapter": "both", "engine_profile": "tuned", "operation": "prune", "proposal_policy": "single"},
)
FEEDBACK_ARMS = (*ARMS[:3],
    {**ARMS[3], "id": "C_single"},
    {**ARMS[3], "id": "C_feedback", "proposal_policy": "feedback"},
)
SCRIPT = Path(__file__).resolve()
PROJECTS = {"sonde": "kicad-sonde-xilinx", "interf_u": "kicad-interf-u", "multichannel": "kicad-multichannel", "ardujoy-c64":"eduardofv-ArdujoyC64", "nus-usb-led":"nushackers-hsp-pcb-intro", "push-button-led":"gurusaeth12-push-button-led-kicad", "arcdice":"VorosEgyes-ArcDice"}
SUPPORT = (SCRIPT, c.ROOT / "toolchain.lock.json", c.ROOT / "data/sources.json",
           c.ROOT/'scripts/fetch_led_demo.py',
           c.ROOT/'experiments/arcdice_native_class_v1/source.py',
           c.ROOT/'experiments/licensed_acquisition_v4/native_snapshot.py',
           c.ROOT/'experiments/licensed_acquisition_v4/protocol.json',
           c.ROOT/'experiments/licensed_acquisition_v5/native_snapshot.py',
           c.ROOT/'experiments/licensed_acquisition_v5/protocol.json',
           c.ROOT/'experiments/licensed_acquisition_v7/native_snapshot.py',
           c.ROOT/'experiments/licensed_acquisition_v7/protocol.json',
           c.ROOT/'experiments/licensed_acquisition_v1/fetch.py')


def total_process_cpu():
    parent = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return parent.ru_utime + parent.ru_stime + children.ru_utime + children.ru_stime


def selected_source(name):
    if name=='arcdice':
        demo=c.ROOT/'.data/arcdice-demo-001'
        if demo.exists() or demo.is_symlink():
            from scripts.fetch_led_demo import verify_project
            raw=demo/'project';base=demo/'native-project'
            raw_check=verify_project(raw,profile_id='arcdice')
            packet_check=verify_project(base,profile_id='arcdice',native_packet=True)
            if (p.tree_hash(base)!={n:v['sha256'] for n,v in packet_check['files'].items()}
                    or verify_project(raw,profile_id='arcdice')!=raw_check
                    or verify_project(base,profile_id='arcdice',native_packet=True)!=packet_check):
                raise p.Rejected('portable ArcDice source changed during read-only selection')
            return base/'hardware/ArcDice.kicad_pcb','VorosEgyes-ArcDice-development-exposed'
        from experiments.arcdice_native_class_v1 import source
        files=source.capture()
        base=c.ROOT/'.runs/arcdice-original-native-001/original'
        expected={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}
        if p.tree_hash(base)!=expected:raise p.Rejected('exact original notice-bearing ArcDice snapshot required')
        return base/'hardware/ArcDice.kicad_pcb','VorosEgyes-ArcDice-development-exposed'
    if name=='push-button-led':
        base=c.ROOT/'.runs/push-button-led-original-native-001/original'
        if base.exists():
            from experiments.licensed_acquisition_v7 import native_snapshot
            files=native_snapshot.capture()
        else:
            # A fresh public checkout can reproduce the fixed source without
            # the ignored research cache or the other development boards.
            from scripts.fetch_led_demo import verify_project
            demo=c.ROOT/'.data/led-demo-001/project';verified=verify_project(demo)
            files={n:(demo/n).read_bytes() for n in verified['files']}
            if any(hashlib.sha256(raw).hexdigest()!=verified['files'][n]['sha256'] for n,raw in files.items()) or verify_project(demo)!=verified:
                raise p.Rejected('fixed demo changed during benchmark capture')
            # Original LICENSE/README already reside beside the native files.
            # Select them read-only; selection never stages or overwrites files.
            base=demo
        expected={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}
        if p.tree_hash(base)!=expected:raise p.Rejected('exact original notice-bearing LED snapshot required')
        return base/'PushButtonLed.kicad_pcb','PushButtonLED-development-exposed-support-control'
    if name=='nus-usb-led':
        from experiments.licensed_acquisition_v5 import native_snapshot
        files=native_snapshot.capture()
        base=c.ROOT/'.runs/nus-original-native-001/original/src'
        expected={name.removeprefix('src/'):hashlib.sha256(raw).hexdigest()
                  for name,raw in files.items() if name.startswith('src/')}
        if p.tree_hash(base)!=expected:raise p.Rejected('exact original notice-bearing NUS snapshot required')
        return base/'usb_led.kicad_pcb','NUS-USB-LED-power-only-development-exposed'
    if name=='ardujoy-c64':
        from experiments.licensed_acquisition_v4 import native_snapshot
        files=native_snapshot.capture()
        base=c.ROOT/'.runs/ardujoy-original-native-001/original/Ardujoy_HW'
        expected={name.removeprefix('Ardujoy_HW/'):hashlib.sha256(raw).hexdigest()
                  for name,raw in files.items() if name.startswith('Ardujoy_HW/')}
        if p.tree_hash(base)!=expected:raise p.Rejected('exact original notice-bearing Ardujoy snapshot required')
        return base/'Ardujoy_HW.kicad_pcb','ArdujoyC64-ATtiny84-joystick-development-exposed'
    manifest = json.loads((c.ROOT / "data/sources.json").read_text())
    project = next(row for row in manifest["projects"] if row["project_id"] == PROJECTS[name])
    entries=project["boards"]
    if name=="multichannel":
        if {Path(x["board"]).name for x in entries}!={"multichannel_mixer.kicad_pcb","multichannel_mixer-unrouted.kicad_pcb"}:
            raise p.Rejected("multichannel source population differs")
        entries=[x for x in entries if Path(x["board"]).name=="multichannel_mixer.kicad_pcb"]
    if project["split"] != "development" or len(entries) != 1:
        raise p.Rejected("only the predeclared single-board development projects are supported")
    entry = entries[0]
    if entry["same_basename_project"] is not True:
        raise p.Rejected("native project binding is required")
    base = (c.ROOT / ".data" / project["destination"]).resolve()
    if c.ROOT / ".data/boards" not in base.parents:
        raise p.Rejected("manifest project escaped the acquired corpus")
    board = base / Path(entry["board"]).name
    expected = {str(Path(row["destination"]).relative_to(project["destination"])): row["sha256"]
                for row in manifest["files"] if row.get("project_id") == project["project_id"]}
    if not expected or p.tree_hash(base) != expected:
        raise p.Rejected("complete acquired source inventory differs from licensed manifest")
    if not board.is_file():
        raise p.Rejected("selected source board is missing")
    return board, project["family"]


def freeze(board):
    tools = p.tool_manifest()
    files = dict(tools["implementation_sha256"])
    files.update({str(path.relative_to(c.ROOT)): p.sha(path) for path in SUPPORT})
    for relative, digest in files.items():
        committed = subprocess.run(["git", "show", tools["git_head"] + ":" + relative],
                                   cwd=c.ROOT, capture_output=True, check=True).stdout
        if hashlib.sha256(committed).hexdigest() != digest:
            raise p.Rejected("commit exact experiment sources before running: " + relative)
    return {"tools": tools, "source_hashes": p.tree_hash(board.parent), "files_sha256": files}


def verify_freeze(frozen, board):
    if p.tree_hash(board.parent) != frozen["source_hashes"]:
        raise p.Rejected("experiment source changed")
    if p.tool_manifest() != frozen["tools"]:
        raise p.Rejected("experiment implementation, tools, or Git HEAD changed")
    for relative, digest in frozen["files_sha256"].items():
        if p.sha(c.ROOT / relative) != digest:
            raise p.Rejected("experiment protocol/configuration changed: " + relative)


def cancelled(result):
    return result.get("status") == "cancelled" or any(step.get("status") == "cancelled" for step in result.get("steps", []))


def finite_nonnegative(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0


def summarize(arm, directory, result, invocation_wall, invocation_cpu):
    native, metrics = result.get("native", {}), result.get("metrics", {})
    row = {**arm, "status": result.get("status", "invocation_error"),
           "accepted_in_receipt": result.get("accepted") is True, "accepted": False,
           "reason": result.get("reason"), "cancelled": cancelled(result),
           "opens": native.get("opens"), "blocking": native.get("blocking"),
           "warnings": native.get("warnings"), "exclusions": native.get("exclusions"),
           "length_mm": metrics.get("track_length_mm"), "vias": metrics.get("vias"),
           "wall_seconds": result.get("wall_seconds"),
           "parent_cpu_seconds": result.get("parent_cpu_seconds"),
           "child_cpu_seconds": result.get("child_cpu_seconds"),
           "monitor_cpu_seconds": result.get("monitor_cpu_seconds"),
           "total_cpu_seconds": result.get("total_cpu_seconds"),
           "peak_child_rss_bytes": result.get("peak_child_rss_bytes"),
           "peak_polled_group_rss_bytes": max([step.get("sampled_peak_group_rss_bytes") or 0 for step in result.get("steps", [])] + [0]),
           "invocation_wall_seconds": invocation_wall, "invocation_cpu_seconds": invocation_cpu,
           "candidate_sha256": result.get("candidate_sha256"),
           "native_report_sha256": result.get("native_report_sha256"),
           "result": str(directory / "result.json"),
           "result_sha256": p.sha(directory / "result.json") if (directory / "result.json").is_file() else None}
    values = (row["wall_seconds"], row["total_cpu_seconds"], invocation_wall, invocation_cpu)
    row["within_equal_budgets"] = all(finite_nonnegative(value) and value <= BUDGET for value in values)
    row["protocol_contract_verified"] = (
        result.get("adapter") == arm["adapter"]
        and result.get("engine_profile") == arm["engine_profile"]
        and result.get("scope") == "whole_board_unlocked_routing")
    if arm["operation"] == "prune":
        row["protocol_contract_verified"] = row["protocol_contract_verified"] and result.get("proposal_policy") == arm["proposal_policy"]
    if arm["operation"] == "prune" and row["accepted_in_receipt"]:
        incumbent_path = directory / "incumbent/result.json"
        try:
            incumbent = json.loads(incumbent_path.read_text())
            row["protocol_contract_verified"] = row["protocol_contract_verified"] and (
                result.get("incumbent_baseline") == "B2_tuned"
                and result.get("incumbent", {}).get("receipt") == str(incumbent_path)
                and incumbent.get("adapter") == arm["adapter"]
                and incumbent.get("engine_profile") == arm["engine_profile"]
                and incumbent.get("scope") == "whole_board_unlocked_routing"
                and incumbent.get("accepted") is True)
        except (OSError, ValueError):
            row["protocol_contract_verified"] = False
    if arm["operation"] == "placement_prune":
        from autorouter import placement_strategy as ps,floor_route as f
        try:
            incumbent_path=directory/'incumbent/result.json';incumbent=f.read_json(incumbent_path)
            row['protocol_contract_verified']=row['protocol_contract_verified'] and (
                arm.get('input_policy')==ps.POLICY and arm.get('strategy')==ps.STRATEGY
                and result.get('proposal_policy')=='feedback' and ps.recognize(result,directory)
                and incumbent.get('schema')==4 and incumbent.get('input_policy')=='placement-search-v1'
                and incumbent.get('accepted') is True and incumbent.get('engine_profile')==arm['engine_profile']
                and result.get('pruning_allocation')==arm.get('pruning_allocation')
                and (ps.receipt_allocation(result)==ps.LEGACY_ALLOCATION or (
                    arm.get('pruning_allocation_contract')==ps.contract(ps.STANDARD_ALLOCATION)
                    and ps.check_incumbent_allocation(result,incumbent)==ps.STANDARD_ALLOCATION))
                and incumbent.get('scoring_variant')=='via_default'
                and result.get('incumbent_receipt_sha256')==p.sha(incumbent_path))
        except (OSError,ValueError,p.Rejected):row['protocol_contract_verified']=False
    row["receipt_verified"] = False
    if row["accepted_in_receipt"]:
        try:
            from autorouter.floor_route import read_json,canonical
            receipt=directory/'result.json'
            if canonical(read_json(receipt))!=canonical(result):raise p.Rejected('returned result differs from retained receipt')
            p.check_result(receipt)
            if p.sha(receipt)!=row['result_sha256'] or canonical(read_json(receipt))!=canonical(result):raise p.Rejected('receipt changed during summary readback')
            row["receipt_verified"] = True
        except Exception as exc:
            row["receipt_verification_error"] = type(exc).__name__ + ": " + str(exc)
    row["accepted"] = row["protocol_contract_verified"] and row["receipt_verified"] and row["within_equal_budgets"] and not row["cancelled"]
    return row


def observations(directory, result, row):
    observed = []
    if row['operation']=='placement_prune':
        for item in [result.get('incumbent_observation'),*result.get('trials',[])]:
            if not item:continue
            wall,cpu=item.get('elapsed_seconds'),item.get('observed_full_cpu_seconds')
            observed.append({'kind':'validated_incumbent' if 'index' not in item else 'pruning_trial',
                'trial':item.get('index'),'elapsed_seconds':wall,'observed_cpu_seconds':cpu,'status':item.get('status'),
                'native_accepted':item.get('completed') is True and item.get('accepted') is True,
                'metrics':item.get('metrics'),'candidate_sha256':item.get('candidate_sha256'),
                'within_budgets_when_observed':all(finite_nonnegative(value) and value<=BUDGET for value in (wall,cpu)),
                'final_delivery_accepted':row['accepted'],
                'meaning':'charged native observation; final budget, freshness and native delivery remain authoritative'})
        return observed
    if row["operation"] == "prune":
        for relative in result.get("checkpoints", []):
            path = directory / relative
            if path.is_symlink() or path.resolve().parent != (directory / "checkpoints").resolve():
                raise p.Rejected("checkpoint escaped experiment arm")
            checkpoint = json.loads(path.read_text())
            wall, cpu = checkpoint.get("elapsed_seconds"), checkpoint.get("observed_cpu_seconds")
            observed.append({"kind": checkpoint["kind"], "checkpoint": relative,
                             "checkpoint_sha256": p.sha(path), "elapsed_seconds": wall,
                             "observed_cpu_seconds": cpu, "metrics": checkpoint["metrics"],
                             "candidate_sha256": checkpoint["candidate_sha256"],
                             "within_budgets_when_observed": all(finite_nonnegative(value) and value <= BUDGET for value in (wall, cpu)),
                             "final_delivery_accepted": row["accepted"],
                             "meaning": "validated incumbent observation; does not override final budget/cancellation/receipt outcome"})
    elif row["accepted_in_receipt"]:
        observed.append({"kind": "final_result_only", "elapsed_seconds": row["invocation_wall_seconds"],
                         "observed_cpu_seconds": row["invocation_cpu_seconds"],
                         "metrics": result.get("metrics"), "final_delivery_accepted": row["accepted"],
                         "meaning": "final completion upper bound only; earlier native success times unobserved"})
    return observed


def comparisons(rows):
    by_id = {row["id"]: row for row in rows}
    result = []
    pairs = [(baseline, system) for system in ("C", "C_single", "C_feedback")
             if system in by_id for baseline in ("B1", "B2")]
    if "C_single" in by_id and "C_feedback" in by_id:
        pairs.append(("C_single", "C_feedback"))
    for baseline, system in pairs:
        left, right = by_id.get(baseline), by_id.get(system)
        comparable = bool(left and right and left["accepted"] and right["accepted"])
        item = {"baseline": baseline, "system": system, "comparable_valid_candidates": comparable}
        if comparable:
            item.update(length_delta_mm=right["length_mm"] - left["length_mm"],
                        via_delta=right["vias"] - left["vias"],
                        wall_delta_seconds=right["invocation_wall_seconds"] - left["invocation_wall_seconds"],
                        cpu_delta_seconds=right["invocation_cpu_seconds"] - left["invocation_cpu_seconds"])
        result.append(item)
    return result


def experiment(out, project_name="sonde", feedback_ablation=False):
    arms = FEEDBACK_ARMS if feedback_ablation else ARMS
    batch_started, batch_cpu_started = time.monotonic(), total_process_cpu()
    out.mkdir(parents=True, exist_ok=False)
    summary = {"schema": 1, "status": "incomplete", "protocol": "protocol.json", "results": [],
               "claims_limit": "One exposed development family and one predeclared trial per arm; no population superiority, algorithmic novelty, or confirmatory significance claim."}
    try:
        p.check_storage()
        board, family = selected_source(project_name)
        frozen = freeze(board)
        for relative in frozen["files_sha256"]:
            destination = out / "frozen-code" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(c.ROOT / relative, destination)
            if p.sha(destination) != frozen["files_sha256"][relative]:
                raise p.Rejected("code changed while copying frozen experiment sources")
        protocol = {"schema": 1, "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "split": "development-exposed", "family": family, "source": str(board),
                    "license": "CC-BY-SA-4.0; exact pinned source and license files in frozen source inventory and data/sources.json",
                    "freeze": frozen, "arms": arms, "arm_order": [arm["id"] for arm in arms],
                    "feedback_ablation": feedback_ablation,
                    "feedback_prediction": "Native-warning-guided compound deletion may remove redundant stubs rejected by single deletion; every follow-up consumes the same trial and total wall/CPU budgets. It may displace better proposals and lose quality; compare C_feedback directly with C_single.",
                    "wall_budget_per_arm_seconds": BUDGET, "cpu_budget_per_arm_seconds": BUDGET,
                    "cpu_enforcement": "measured post-completion acceptance cap, not OS CPU preemption; self plus reaped-child invocation CPU also checked",
                    "concurrency": 1, "external_concurrency": "operator must keep other routing/native experiments idle",
                    "host_contention": "One project heavy worker. Existing desktop/background contention is uncontrolled; 1/5/15-minute host load averages recorded at each arm begin/end.",
                    "editor_policy": "Lead closes KiCad PCB Editor before measured runs; this script does not control or verify the editor.",
                    "task": "remove unlocked routing; preserve original zones, rules, geometry, protected copper and terminal mapping",
                    "primary": "zero native opens/blocking/exclusions, immutable constraints and final receipt binding, within both budgets",
                    "secondary": ["native track length", "native via count", "warnings", "wall", "parent+child+monitor CPU", "direct-child and polled group RSS"],
                    "ablation": "B2 is C without pruning, using identical adapter, tuned engine profile, implementation and validator; C pays for its own B2 incumbent and reserves 15 seconds wall/CPU for final validation",
                    "B2_limit": "one predeclared tuned profile, not an exhaustive parameter/restart optimum",
                    "prediction": "pruning may reduce track-length proxy while retaining the independently rerun tuned incumbent via count and warning set; fewer trials may fit after the more expensive incumbent; no fixed final length or two-via result is promised",
                    "observations": "C records actual native-validated incumbent checkpoints; baseline arms provide final observation only. No interpolated success curves.",
                    "claims_limit": summary["claims_limit"]}
        p.save_json(out / "protocol.json", protocol)
        summary["protocol_sha256"] = p.sha(out / "protocol.json")
        p.save_json(out / "summary.json", summary)
        for arm in arms:
            verify_freeze(frozen, board)
            directory = out / arm["id"]
            host_load_begin = list(os.getloadavg())
            started, cpu_started = time.monotonic(), total_process_cpu()
            invocation_started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
            try:
                result = (prune(board, directory, BUDGET, proposal_policy=arm["proposal_policy"]) if arm["operation"] == "prune" else
                          p.route(board, directory, BUDGET, False, arm["adapter"], arm["engine_profile"]))
            except KeyboardInterrupt:
                result = {"status": "cancelled", "accepted": False, "reason": "interrupted invocation"}
            except Exception as exc:
                result = {"status": "invocation_error", "accepted": False, "reason": type(exc).__name__ + ": " + str(exc)}
            invocation_finished_monotonic = time.monotonic()
            invocation_finished_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
            wall, cpu = invocation_finished_monotonic - started, total_process_cpu() - cpu_started
            host_load_end = list(os.getloadavg())
            p.save_json(out / (arm["id"] + "-invocation.json"), {"wall_seconds": wall, "cpu_seconds": cpu,
                        "status": result.get("status"), "reason": result.get("reason"),
                        "started_utc": invocation_started_utc, "finished_utc": invocation_finished_utc,
                        "started_monotonic": started, "finished_monotonic": invocation_finished_monotonic,
                        "host_load_average_1_5_15_minutes_begin": host_load_begin,
                        "host_load_average_1_5_15_minutes_end": host_load_end})
            row = summarize(arm, directory, result, wall, cpu)
            row.update(host_load_average_1_5_15_minutes_begin=host_load_begin,
                       host_load_average_1_5_15_minutes_end=host_load_end)
            summary["results"].append(row)
            try:
                verify_freeze(frozen, board)
                row["freeze_unchanged"] = True
                if not row["cancelled"] and result.get("status") != "invocation_error" and (result.get("tools") != frozen["tools"] or result.get("source_hashes") != frozen["source_hashes"]):
                    raise p.Rejected("arm receipt not bound to experiment source/tool/code freeze")
                row["observations"] = observations(directory, result, row)
            except Exception as exc:
                row.update(accepted=False, freeze_unchanged=False, protocol_error=type(exc).__name__ + ": " + str(exc))
                summary["status"] = "invalidated"
                break
            print(json.dumps(row), flush=True)
            p.save_json(out / "summary.json", summary)
            if row["cancelled"]:
                summary["status"] = "cancelled"
                break
            if result.get("status") == "invocation_error":
                summary["status"] = "invocation_error"
                break
        else:
            summary["status"] = "completed"
    except KeyboardInterrupt:
        summary["status"] = "cancelled"
    except Exception as exc:
        summary.update(status="invalidated", reason=type(exc).__name__ + ": " + str(exc))
    summary["batch_wall_seconds"] = time.monotonic() - batch_started
    summary["batch_cpu_seconds"] = total_process_cpu() - batch_cpu_started
    summary["shared_freeze_and_summary_overhead_wall_seconds"] = summary["batch_wall_seconds"] - sum(row["invocation_wall_seconds"] for row in summary["results"])
    summary["shared_freeze_and_summary_overhead_cpu_seconds"] = summary["batch_cpu_seconds"] - sum(row["invocation_cpu_seconds"] for row in summary["results"])
    summary["comparisons"] = comparisons(summary["results"]) if summary["status"] == "completed" else []
    summary["protocol_complete_and_unchanged"] = summary["status"] == "completed"
    p.save_json(out / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "summary": str(out / "summary.json")}), flush=True)
    return 0 if summary["status"] == "completed" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="new directory under this checkout's .runs")
    parser.add_argument("--project", choices=tuple(PROJECTS), default="sonde")
    parser.add_argument("--feedback-ablation", action="store_true", help="predeclared five arms: B0, B1, B2, C_single, C_feedback")
    args = parser.parse_args()
    out = Path(args.output).resolve()
    if c.ROOT / ".runs" not in out.parents:
        parser.error("output must be a new directory under " + str(c.ROOT / ".runs"))
    lock_path = c.ROOT / ".runs/quality-experiment.lock"
    lock_path.parent.mkdir(exist_ok=True)
    if lock_path.is_symlink():
        parser.error("experiment lock must not be a symlink")
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        with lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return experiment(out, args.project, args.feedback_ablation)
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == "__main__":
    raise SystemExit(main())
