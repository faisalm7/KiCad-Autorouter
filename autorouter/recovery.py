"""Experimental full-budget completion plus one geometry-derived thermal repair.

The original project remains immutable. Every delivery receives fresh native
validation; unsupported recovery leaves an explicitly rejected result.
"""
from __future__ import annotations
import copy
import datetime
import json
import math
from pathlib import Path
import resource
import signal
import shutil
import time
import uuid
from . import config as c, pipeline as p, sexpr as sx

FINAL_RESERVE = 15.0
RECOVERY_RESERVE = 40.0
THERMAL_PARENT_POLICY = 'native-thermal-parent-selection-v1'


def child_cpu():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime + usage.ru_stime


def recover(source, output, seconds=120):
    """Keep cancellation active between native stages and final receipt writes."""
    p.require_native_scope(purpose='thermal-recovery',scope='whole_board_unlocked_routing',
                           guidance='native',layers='source_all',profile='standard',adapter='both')
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        for sig in previous:
            signal.signal(sig, interrupted)
        return _recover(source, output, seconds)
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def _recover(source, output, seconds):
    from .thermal import parent_profile
    profile=parent_profile()
    started, parent_start, child_start = time.monotonic(), time.process_time(), child_cpu()
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 90 <= seconds <= 900:
        raise p.Rejected("thermal recovery budget must be 90–900 seconds")
    from .local_settings import canonical
    canonical(Path(source).absolute());canonical(Path(output).absolute())
    source, output = Path(source).resolve(strict=True), Path(output).resolve()
    if source.parent == output or source.parent in output.parents:
        raise p.Rejected("output must be outside source project")
    job = p.Job(output, seconds, protect_local_settings=True)
    job.started, job.deadline, job.cpu_started = started, started + seconds, parent_start
    report = {"schema": 1, "status": "rejected", "accepted": False, "baseline": "C-prototype",
              "strategy": "native_validated_thermal_bridge", "adapter": "both",
              "engine_profile": profile, "scope": "whole_board_unlocked_routing",
              "thermal_parent_policy": THERMAL_PARENT_POLICY,
              "source": str(source), "budget_seconds": seconds, "cpu_budget_seconds": seconds,
              "cpu_budget_enforcement": "cooperative assignment and postcompletion acceptance cap; no OS total-CPU quota",
              "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "physical_electrical_validation": False, "schematic_parity": "not checked",
              "novel_routing_algorithm_claim": False, "reference_routes_used_for_selection": False,
              "recovery_reserve_seconds": RECOVERY_RESERVE, "finalization_reserve_seconds": FINAL_RESERVE,
              "repair": None}
    frozen = False

    def total_cpu():
        return time.process_time() - parent_start + child_cpu() - child_start

    def remaining(reserve=0):
        return max(0.0, min(started + seconds - time.monotonic(), seconds - total_cpu()) - reserve)

    def stable():
        if not frozen:
            return
        if p.tree_hash(source.parent) != hashes or p.tree_hash(output / "snapshot") != hashes:
            raise p.Rejected("original source or frozen snapshot changed")
        if p.tool_manifest() != report["tools"]:
            raise p.Rejected("code/tool/HEAD freeze changed during recovery")

    def cancelled():
        return any(s.get("status") == "cancelled" or s.get("cleanup_complete") is not True for s in job.steps)

    def account():
        steps = job.steps
        report.update(steps=steps, wall_seconds=time.monotonic()-started,
                      parent_cpu_seconds=time.process_time()-parent_start,
                      child_cpu_seconds=sum(s.get("cpu_seconds") or 0 for s in steps),
                      monitor_cpu_seconds=sum(s.get("monitor_cpu_seconds") or 0 for s in steps),
                      peak_child_rss_bytes=max([s.get("max_rss_bytes") or 0 for s in steps] + [0]))
        # Count short metadata processes too, without double-counting the native
        # children already represented by their individual wait4 receipts.
        report["control_child_cpu_seconds"] = max(0.0, child_cpu()-child_start-report["child_cpu_seconds"]-report["monitor_cpu_seconds"])
        report["total_cpu_seconds"] = sum(report[k] for k in ("parent_cpu_seconds", "child_cpu_seconds", "monitor_cpu_seconds", "control_child_cpu_seconds"))
        report["resource_limitations"] = "Sequential Mac workers; full parent plus waited-child CPU includes metadata, acquisition, failed trials and final checks. Process-group RSS and disk guards poll and may overshoot. Detached/unwaited descendant CPU is not qualified. Final receipt writes are included in acceptance caps."
        report["resource_accounting_point"] = "Stored totals precede final receipt publication and freshness recheck; acceptance caps include both. Enclosing experimental arms charge the entire invocation."
        if cancelled():
            report.update(accepted=False, status="cancelled")
        elif report["wall_seconds"] > seconds or report["total_cpu_seconds"] > seconds:
            report.update(accepted=False, status="budget_exceeded")
        if not report["accepted"]:
            report["whole_project_drc_clean"] = False

    try:
        p.check_storage(active_root=output)
        hashes = p.tree_hash(source.parent)
        original = p.preflight(source)
        protected = copy.deepcopy([r for r in p.routes(original) if p.locked(r)])
        report.update(source_hashes=hashes, tools=p.tool_manifest())
        shutil.copytree(source.parent, output / "snapshot")
        (output / "code").mkdir()
        for relative, expected in report["tools"]["implementation_sha256"].items():
            dest = output / "code" / Path(relative).name
            shutil.copy2(c.ROOT / relative, dest)
            if p.sha(dest) != expected:
                raise p.Rejected("implementation changed during snapshot")
        frozen = True
        stable()
        assigned = remaining(RECOVERY_RESERVE)
        report["incumbent_assigned_seconds"] = assigned
        incumbent = p.route(source, output / "incumbent", assigned, False, "both", profile)
        job.steps.extend(dict(step, phase="incumbent") for step in incumbent.get("steps", []))
        report.update(incumbent={"receipt":str(output / "incumbent/result.json"),
                                  "receipt_sha256":p.sha(output / "incumbent/result.json"),
                                  "status":incumbent["status"], "accepted":incumbent["accepted"]},
                      source_drc=incumbent.get("source_drc"), task_sha256=incumbent.get("task_sha256"))
        if cancelled():
            raise KeyboardInterrupt
        stable()
        if incumbent["accepted"]:
            p.check_result(output / "incumbent/result.json")
            selected = Path(incumbent["candidate"])
            selected_hash = incumbent["candidate_sha256"]
            report["recovery_needed"] = False
        else:
            if incumbent["status"] != "drc_rejected" or not incumbent.get("candidate"):
                raise p.Rejected("fresh incumbent did not reach an eligible native DRC outcome")
            from .thermal import attempt_repair
            repair = attempt_repair(job, original, Path(incumbent["candidate"]), hashes, protected,
                                    incumbent["native"], report_path=output / "incumbent/final-drc.json",
                                    binding_path=output / "incumbent/final-drc-binding.json",
                                    remaining_seconds=lambda: remaining(FINAL_RESERVE), out=output / "recovery")
            report.update(recovery_needed=True, repair=repair)
            if cancelled():
                raise KeyboardInterrupt
            stable()
            if repair.get("validation_passed") is not True or not repair.get("candidate"):
                raise p.Rejected("bounded thermal recovery found no native-valid candidate: " + str(repair.get("unsupported_reason") or repair.get("status")))
            selected = Path(repair["candidate"])
            selected_hash = repair["candidate_sha256"]
        if remaining() < 8:
            raise p.Rejected("final native validation reserve exhausted")
        p.verify_candidate_files(selected, hashes, selected_hash)
        candidate = output / "candidate" / source.name
        shutil.copytree(selected.parent, candidate.parent)
        final_hash, native = p.validate_candidate(job, original, candidate, hashes, protected)
        report['schematic_parity']=p.parity_declaration(source,hashes)
        # The retained geometric certificate applies only to the exact selected
        # fill and copper. A different refill requires a new certificate.
        if final_hash != selected_hash:
            raise p.Rejected("final emitted candidate differs from validated selection")
        job.native("metrics", "metrics", candidate, output / "metrics.json")
        p.verify_candidate_files(candidate, hashes, final_hash)
        stable()
        valid = p.native_accepted(native)
        report.update(candidate=str(candidate), candidate_sha256=final_hash,
                      native_report_sha256=p.sha(output / "final-drc.json"), native=native,
                      metrics=json.loads((output / "metrics.json").read_text()), invariants_unchanged=True,
                      native_rejection_reasons=p.native_rejection_reasons(native), accepted=valid,
                      status="routing_accepted" if valid else "drc_rejected",
                      whole_project_drc_clean=valid and native["warnings"] == 0)
    except KeyboardInterrupt:
        report.update(accepted=False, status="cancelled", reason="interrupted recovery")
    except Exception as exc:
        report.update(accepted=False, status="rejected", reason=type(exc).__name__ + ": " + str(exc))

    def preserve_partial():
        partial = output / "result.json.partial"
        if partial.exists():
            partial.rename(output / ("interrupted-result-" + uuid.uuid4().hex + ".partial"))

    try:
        preserve_partial()
        stable()
        account()
        p.save_json(output / "result.json", report)
        if report["accepted"]:
            p.check_result(output / "result.json")
        stable()
        account()
        p.save_json(output / "result.json", report)
        if report["accepted"]:
            p.check_result(output / "result.json")
        stable()
        if remaining() <= 0:
            account()
            p.save_json(output / "result.json", report)
    except (Exception, KeyboardInterrupt) as exc:
        preserve_partial()
        receipt = output / "result.json"
        if receipt.exists():
            receipt.rename(output / ("invalidated-result-" + uuid.uuid4().hex + ".json"))
        report.update(accepted=False, status="cancelled" if isinstance(exc, KeyboardInterrupt) else "invalidated",
                      reason=type(exc).__name__ + ": " + str(exc))
        account()
        p.save_json(output / "result.json", report)
    return report
