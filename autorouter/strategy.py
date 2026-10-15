"""Experimental C prototype: delete redundant zone-net routing after tuned B2.

This is native-validated postprocessing, not a claimed new routing algorithm.
Only original zone net identifiers select proposals; original unlocked reference
routes and net-name heuristics never select or score a deletion. All accepted
trials and the final candidate undergo the same full native validation as B2.
"""

from __future__ import annotations

import copy
import datetime
import hashlib
import json
import math
from pathlib import Path
import shutil
import time

from . import config as c, pipeline as p, sexpr as sx


# Historical placement contracts consume this legacy value; keep their
# stored allocations reproducible. Native pruning owns its separate reserve.
FINAL_RESERVE_SECONDS = 15.0
# Actual 77-footprint/full-schematic/class validation plus publication overran
# the former 15-second tail. All total wall/CPU acceptance caps remain strict.
NATIVE_FINAL_RESERVE_SECONDS = 25.0
MIN_TRIAL_SECONDS = 4.0
MAX_TRIAL_SECONDS = 12.0
MAX_TRIALS = 32
MAX_FEEDBACK_DEPTH = 2
MAX_FEEDBACK_ADDED_ROUTES = 8
PRUNING_PREFERENCES_POLICY = "native-pruning-preferences-v1"


class Cancelled(p.Rejected):
    pass


def zone_net_ids(original):
    """Return native net atoms from copper-zone definitions, excluding keepouts."""
    result = set()
    for zone in sx.children(original, "zone"):
        if sx.one(zone, "keepout") is not None:
            continue
        net = sx.one(zone, "net")
        if net is not None and len(net) == 2 and net[1] != "0" and sx.unquote(net[1]):
            result.add(net[1])
    return result


def route_id(route):
    return hashlib.sha256(sx.dump(route).encode("utf-8")).hexdigest()


def eligible_routes(tree, nets, protected):
    result = []
    for route in p.routes(tree):
        net = sx.one(route, "net")
        if net is not None and len(net) == 2 and net[1] in nets and not p.locked(route) and route not in protected:
            result.append(route)
    return result


def delete_routes(tree, identifiers, nets, protected):
    """Delete only explicitly eligible candidate routes; never unlock copper."""
    allowed = {route_id(route) for route in eligible_routes(tree, nets, protected)}
    requested = set(identifiers)
    if not requested or not requested <= allowed:
        raise p.Rejected("deletion includes protected, absent, or non-zone-net routing")
    result = copy.deepcopy(tree)
    result[:] = [node for node in result if not (isinstance(node, list) and node and node[0] in p.ROUTES and route_id(node) in requested)]
    if any(route not in p.routes(result) for route in protected):
        raise p.Rejected("deletion changed protected route")
    return result


def _length(route):
    if route[0] != "segment":
        return 0.0
    start, end = sx.one(route, "start"), sx.one(route, "end")
    values = [float(value) for point in (start, end) for value in point[1:3]]
    if len(values) != 4 or not all(math.isfinite(value) for value in values):
        raise p.Rejected("unusable route geometry in proposal ranking")
    return math.hypot(values[2] - values[0], values[3] - values[1])


def proposals(tree, nets, protected, grouped):
    eligible = eligible_routes(tree, nets, protected)
    if grouped:
        return [{"kind": "whole_zone_net", "net": net,
                 "route_ids": [route_id(route) for route in eligible if sx.one(route, "net")[1] == net]}
                for net in sorted(nets) if any(sx.one(route, "net")[1] == net for route in eligible)]
    individual = [route for route in eligible if route[0] in ("segment", "via")]
    individual.sort(key=lambda route: (-_length(route), route_id(route)))
    return [{"kind": "individual_" + route[0], "net": sx.one(route, "net")[1],
             "route_ids": [route_id(route)], "ranking_length_mm": _length(route)} for route in individual]


def _valid(native):
    return p.native_accepted(native)


def _warning_signatures(native):
    return {json.dumps({"type": finding["type"], "items": sorted(item.get("uuid", "") for item in finding["items"])}, sort_keys=True)
            for finding in native["findings"] if finding["severity"] == "warning"}


def feedback_proposal(failed_tree, proposal, native, incumbent_native, nets, protected):
    """Suggest a bounded compound move; native warnings never authorize acceptance.

    Only new track_dangling findings may drive a follow-up. Their item UUIDs must
    identify unique, eligible remaining tracks on this proposal's zone net. The
    resulting cumulative deletion is applied to the unchanged best candidate,
    not to arbitrary paths or geometry from a report. This is a proposal only.
    """
    def refused(reason):
        return {"proposed": False, "reason": reason}

    try:
        if any(type(native[key]) is not int or native[key] < 0 for key in ("opens", "blocking", "exclusions")) or not _valid(native):
            return refused("native connectivity or blocking checks failed")
        depth = proposal.get("feedback_depth", 0)
        added_count = proposal.get("feedback_added_routes", 0)
        if type(depth) is not int or type(added_count) is not int or depth < 0 or added_count < 0:
            return refused("invalid feedback accounting")
        if depth >= MAX_FEEDBACK_DEPTH:
            return refused("feedback depth exhausted")
        old_ids = proposal["route_ids"]
        if (not isinstance(old_ids, list) or not old_ids or any(not isinstance(x, str) for x in old_ids)
                or len(old_ids) != len(set(old_ids))):
            return refused("invalid cumulative deletion")
        if proposal["net"] not in nets:
            return refused("proposal is not on an eligible zone net")
        if set(old_ids) & {route_id(route) for route in p.routes(failed_tree)}:
            return refused("failed candidate does not reflect preceding deletion")
        incumbent_signatures = _warning_signatures(incumbent_native)
        new_warnings = [finding for finding in native["findings"]
                        if finding["severity"] == "warning"
                        and not _warning_signatures({"findings": [finding]}) <= incumbent_signatures]
        if not new_warnings:
            return refused("no new warning to repair")
        if any(finding["type"] != "track_dangling" for finding in new_warnings):
            return refused("new warning kind is not eligible for cleanup")

        # Index every native object, including pads/zones/footprints, so a UUID
        # shared with a nonroute object cannot be mistaken for an owned track.
        uuid_items = {}
        pending = [failed_tree]
        while pending:
            node = pending.pop()
            if not isinstance(node, list):
                continue
            tags = sx.children(node, "uuid")
            for tag in tags:
                if len(tag) != 2 or not isinstance(tag[1], str) or not sx.unquote(tag[1]):
                    return refused("malformed candidate UUID")
                uuid_items.setdefault(sx.unquote(tag[1]), []).append(node)
            pending.extend(value for value in node if isinstance(value, list))

        eligible = {route_id(route): route for route in eligible_routes(failed_tree, nets, protected)
                    if route[0] in {"segment", "arc"}}
        selected, selected_uuids = set(), set()
        for warning in new_warnings:
            items = warning["items"]
            if not isinstance(items, list) or not items:
                return refused("warning has no exact item references")
            for item in items:
                identifier = item.get("uuid") if isinstance(item, dict) else None
                if not isinstance(identifier, str) or not identifier or identifier in selected_uuids:
                    return refused("missing or repeated warning UUID")
                matches = uuid_items.get(identifier, [])
                if len(matches) != 1:
                    return refused("warning UUID is absent or ambiguous")
                route = matches[0]
                rid = route_id(route)
                if rid not in eligible or sx.one(route, "net")[1] != proposal["net"]:
                    return refused("warning references protected, nonroute or other-net copper")
                selected.add(rid)
                selected_uuids.add(identifier)
        if not selected or selected & set(old_ids):
            return refused("cleanup makes no new eligible deletion")
        added_count += len(selected)
        if added_count > MAX_FEEDBACK_ADDED_ROUTES:
            return refused("feedback route cap exhausted")
        return {"proposed": True, "proposal": {
            "kind": "native_warning_cleanup", "net": proposal["net"],
            "route_ids": sorted(set(old_ids) | selected),
            "feedback_depth": depth + 1, "feedback_added_routes": added_count,
            "root_kind": proposal.get("root_kind", proposal["kind"]),
            "added_route_uuids": sorted(selected_uuids),
            "trigger_warning_signatures": sorted(_warning_signatures({"findings": new_warnings})),
        }}
    except (KeyError, TypeError, ValueError, IndexError, AttributeError):
        return refused("malformed feedback inputs")


def _quality(metrics):
    length, vias = metrics.get("track_length_mm"), metrics.get("vias")
    if isinstance(length, bool) or not isinstance(length, (int, float)) or not math.isfinite(length) or length < 0:
        raise p.Rejected("invalid native track-length metric")
    if isinstance(vias, bool) or not isinstance(vias, int) or vias < 0:
        raise p.Rejected("invalid native via metric")
    return float(length), vias


def _improves(metrics, incumbent_metrics, native, incumbent_native):
    length, vias = _quality(metrics)
    old_length, old_vias = _quality(incumbent_metrics)
    return (length <= old_length + 1e-9 and vias <= old_vias
            and (length < old_length - 1e-9 or vias < old_vias)
            and _warning_signatures(native) <= _warning_signatures(incumbent_native))


def _remaining(deadline, reserve=0.0):
    return max(0.0, deadline - time.monotonic() - reserve)


def _steps(job, phase):
    return [dict(step, phase=phase) for step in job.steps]


def _cancelled(steps):
    return any(step.get("status") == "cancelled" for step in steps)


def _check_original(source, snapshot, expected):
    if p.tree_hash(source.parent) != expected or p.tree_hash(snapshot) != expected:
        raise p.Rejected("source or frozen snapshot changed during pruning")


def pruning_preferences(captured=None, overrides=None):
    """Use shared presets, retaining the strategy's actual supported scope."""
    from . import preferences as pref
    effective = pref.resolve(captured, overrides)
    return pruning_scope(effective)


def pruning_scope(effective):
    """Do not silently replace saved unsupported task constraints."""
    from . import preferences as pref
    effective = pref.validate(effective)
    required = {'scope': 'whole_board_unlocked_routing', 'adapter': 'both',
                'profile': 'tuned', 'guidance': 'native', 'layers': 'source_all'}
    if any(effective[name] != value for name, value in required.items()):
        raise p.Rejected('native pruning presets require whole-board/native/tuned/both/source_all; use route for other scopes')
    if not 30 <= effective['seconds'] <= 900:
        raise p.Rejected('pruning budget must be 30–900 seconds')
    return effective


def check_pruning_preferences(directory, data):
    """Bind captured choices to this root and its fresh scoring contract."""
    from . import preferences as pref
    from .placement_clearance import read_bytes
    directory = Path(directory)
    path = directory/'pruning-preferences.json'
    code = directory/'code/strategy.py'
    required = False
    if code.exists() or code.is_symlink():
        raw_code = read_bytes(code, 1024*1024)
        pin = data.get('tools', {}).get('implementation_sha256', {}).get('autorouter/strategy.py')
        if hashlib.sha256(raw_code).hexdigest() != pin:
            raise p.Rejected('captured pruning implementation changed')
        required = b'PRUNING_PREFERENCES_POLICY' in raw_code
    if not required and 'pruning_preferences' not in data and not path.exists() and not path.is_symlink():
        return None  # Legacy receipts keep their actual, narrower evidence.
    binding = data.get('pruning_preferences')
    if (data.get('pruning_preferences_policy') != PRUNING_PREFERENCES_POLICY
            or not isinstance(binding, dict) or set(binding) != {'file', 'sha256', 'effective'}
            or binding['file'] != path.name):
        raise p.Rejected('missing or malformed pruning preferences binding')
    raw = read_bytes(path, pref.MAX_SNAPSHOT_BYTES)
    if hashlib.sha256(raw).hexdigest() != binding['sha256']:
        raise p.Rejected('pruning preferences snapshot changed')
    effective = pref.readback(raw, binding['effective'])
    pruning_scope(effective)
    expected = {'scope': effective['scope'], 'adapter': effective['adapter'],
                'engine_profile': effective['profile'], 'budget_seconds': effective['seconds'],
                'cpu_budget_seconds': effective['seconds']}
    if (any(data.get(name) != value for name, value in expected.items())
            or data.get('incumbent_scoring_variant') != effective['scoring_preference']):
        raise p.Rejected('pruning result differs from captured preferences')
    return effective


def check_incumbent_scoring(directory, data):
    """Bind an explicitly chosen scoring preset to the fresh charged solve."""
    from . import floor_route as f
    check_pruning_preferences(directory, data)
    path=Path(directory)/'incumbent/result.json';inc=f.read_json(path)
    marker=Path(directory)/'pruning-scoring.json'
    variant=data.get('incumbent_scoring_variant')
    p.engine_scoring_settings(variant)
    if (data.get('strategy')!='native_validated_zone_net_pruning'
            or inc.get('scoring_variant')!=variant or inc.get('engine_profile')!='tuned'
            or inc.get('adapter')!='both' or inc.get('scope')!='whole_board_unlocked_routing'
            or inc.get('source')!=data['source'] or inc.get('source_hashes')!=data['source_hashes']
            or inc.get('tools')!=data['tools'] or inc.get('input_policy') not in (None,'native')):
        raise p.Rejected('pruning scoring differs from its fresh incumbent')
    if variant is not None:
        contract=f.read_json(marker)
        if (data.get('incumbent_receipt_sha256')!=p.sha(path)
                or data.get('incumbent_scoring_contract')!={'file':marker.name,'sha256':p.sha(marker)}
                or contract!={'schema':1,'strategy':data['strategy'],'incumbent_scoring_variant':variant}):
            raise p.Rejected('explicit pruning incumbent contract changed')
    elif ('incumbent_receipt_sha256' in data or 'incumbent_scoring_contract' in data or marker.exists() or marker.is_symlink()):
        raise p.Rejected('explicit pruning scoring marker missing')
    expected=[dict(step,phase='incumbent') for step in inc['steps']]
    if expected!=[step for step in data['steps'] if step.get('phase')=='incumbent']:
        raise p.Rejected('fresh pruning incumbent workers differ')
    p.check_engine_profile_record(inc,path.parent)
    p.check_result(path)


def prune(source, output, seconds=120, *, proposal_policy="single", incumbent_scoring=None,
          settings_path=None, preference_overrides=None):
    """Run tuned B2 plus greedy pruning within one wall/CPU budget, retaining trials.

    A 25-second reserve is withheld from B2/trials for final emission and native
    checks. It is a planning reserve, not a promise that slow native tooling will
    finish. Exhausting the global budget always rejects the root result.
    """
    started, cpu_started = time.monotonic(), time.process_time()
    p.engine_scoring_settings(incumbent_scoring)  # Preserve legacy typed rejection before output.
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 30 <= seconds <= 900:
        raise p.Rejected("pruning budget must be 30–900 seconds")
    from . import preferences as pref
    from .handoff import capture_destination, owned_destination
    captured = pref.load(settings_path) if settings_path is not None else None
    if settings_path is not None or preference_overrides is not None:
        if seconds != 120 or incumbent_scoring is not None:
            raise p.Rejected('pass pruning settings overrides through preference_overrides, not mixed arguments')
        overrides = preference_overrides
        if captured is None:
            overrides = {'adapter': 'both', 'profile': 'tuned', **(overrides or {})}
        effective = pruning_preferences(captured, overrides)
        seconds, incumbent_scoring = effective['seconds'], effective['scoring_preference']
    else:
        overrides = {'adapter': 'both', 'profile': 'tuned', 'seconds': seconds,
                     'scoring_preference': incumbent_scoring}
        effective = pruning_preferences(None, overrides)
    preference_bytes = pref.snapshot(captured, overrides)
    pref.check_fresh(captured)
    p.engine_scoring_settings(incumbent_scoring)
    if not isinstance(proposal_policy, str) or proposal_policy not in {"single", "feedback", "chains"}:
        raise p.Rejected("unknown pruning proposal policy")
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 30 <= seconds <= 900:
        raise p.Rejected("pruning budget must be 30–900 seconds")
    from .local_settings import canonical
    canonical(Path(source).absolute());canonical(Path(output).absolute())
    source = Path(source).resolve(strict=True)
    output = Path(output).resolve()
    if source.parent == output or source.parent in output.parents:
        raise p.Rejected("output must be outside source project")
    deadline = started + seconds
    final_job = p.Job(output, seconds, protect_local_settings=True)
    owner = {}; capture_destination(owner, output)
    final_job.started, final_job.deadline, final_job.cpu_started = started, deadline, cpu_started
    (output / "checkpoints").mkdir()
    (output / "trials").mkdir()
    report = {"schema": 1, "status": "rejected", "accepted": False, "baseline": "C-prototype",
              "strategy": "native_validated_zone_net_pruning", "adapter": "both",
              "proposal_policy": proposal_policy,
              "feedback_max_depth": MAX_FEEDBACK_DEPTH,
              "feedback_max_added_routes": MAX_FEEDBACK_ADDED_ROUTES,
              "engine_profile": "tuned", "incumbent_baseline": "B2_tuned",
              "novel_routing_algorithm_claim": False, "reference_routes_used_for_selection": False,
              "scope": "whole_board_unlocked_routing", "source": str(source),
              "budget_seconds": seconds, "cpu_budget_seconds": seconds,
              "cpu_budget_enforcement": "post-stage accounting and post-completion acceptance cap; not OS CPU preemption",
              "finalization_reserve_seconds": NATIVE_FINAL_RESERVE_SECONDS,
              "finalization_cpu_reserve_seconds": NATIVE_FINAL_RESERVE_SECONDS,
              "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "physical_electrical_validation": False, "schematic_parity": "not checked",
              "trials": [], "checkpoints": [], "steps": [], "improvements": 0}
    preference_path = output/'pruning-preferences.json'
    preference_path.write_bytes(preference_bytes)
    report['pruning_preferences_policy'] = PRUNING_PREFERENCES_POLICY
    report['pruning_preferences'] = {'file': preference_path.name,
        'sha256': p.sha(preference_path), 'effective': effective}
    if incumbent_scoring is not None:
        report['incumbent_scoring_variant']=incumbent_scoring
        marker=output/'pruning-scoring.json'
        p.save_json(marker,{'schema':1,'strategy':report['strategy'],'incumbent_scoring_variant':incumbent_scoring})
        report['incumbent_scoring_contract']={'file':marker.name,'sha256':p.sha(marker)}
    all_steps = []

    def original_fresh(source, snapshot, expected):
        pref.check_fresh(captured)
        _check_original(source, snapshot, expected)

    def cpu_used(extra_steps=()):
        return (time.process_time() - cpu_started
                + sum((step.get("cpu_seconds") or 0) + (step.get("monitor_cpu_seconds") or 0)
                      for step in [*all_steps, *extra_steps]))

    def remaining_work_budget():
        return max(0.0, min(_remaining(deadline, NATIVE_FINAL_RESERVE_SECONDS),
                            seconds - cpu_used() - NATIVE_FINAL_RESERVE_SECONDS))

    def checkpoint(kind, best, metrics, extra=None):
        entry = {"index": len(report["checkpoints"]), "kind": kind,
                 "elapsed_seconds": time.monotonic() - started,
                 "observed_cpu_seconds": cpu_used(final_job.steps),
                 "candidate": str(best), "candidate_sha256": p.sha(best),
                 "metrics": metrics, "improvements": report["improvements"]}
        if extra:
            entry.update(extra)
        name = f"checkpoints/{entry['index']:04d}.json"
        p.save_json(output / name, entry)
        report["checkpoints"].append(name)

    try:
        p.check_storage()
        source_hashes = p.tree_hash(source.parent)
        original = p.preflight(source,task_scope=(effective['scope'],effective['guidance'],effective['layers']))
        protected = copy.deepcopy([route for route in p.routes(original) if p.locked(route)])
        nets = zone_net_ids(original)
        report["source_hashes"] = source_hashes
        report['schematic_parity']=p.parity_declaration(source,source_hashes)
        report["zone_net_ids"] = sorted(nets)
        report["protected_routes"] = len(protected)
        report["tools"] = p.tool_manifest()
        code = output / "code"
        code.mkdir()
        for relative, expected in report["tools"]["implementation_sha256"].items():
            shutil.copy2(c.ROOT / relative, code / Path(relative).name)
            if p.sha(code / Path(relative).name) != expected:
                raise p.Rejected("implementation changed during code snapshot")
        snapshot = output / "snapshot"
        shutil.copytree(source.parent, snapshot)
        original_fresh(source, snapshot, source_hashes)
        incumbent_seconds = remaining_work_budget()
        if incumbent_seconds < 5:
            raise p.Rejected("insufficient budget for incumbent and finalization reserve")
        if incumbent_scoring is None:
            incumbent = p.route(source, output / "incumbent", incumbent_seconds, False, "both", "tuned")
        else:
            incumbent = p.route(source, output / "incumbent", incumbent_seconds, False, "both", "tuned",scoring_variant=incumbent_scoring)
            report['incumbent_receipt_sha256']=p.sha(output/'incumbent/result.json')
        all_steps.extend(dict(step, phase="incumbent") for step in incumbent.get("steps", []))
        report["incumbent"] = {"receipt": str(output / "incumbent/result.json"),
                               "status": incumbent["status"], "accepted": incumbent["accepted"],
                               "metrics": incumbent.get("metrics"), "wall_seconds": incumbent["wall_seconds"]}
        report["source_drc"] = incumbent.get("source_drc")
        report["task_sha256"] = incumbent.get("task_sha256")
        if _cancelled(incumbent.get("steps", [])):
            raise Cancelled("incumbent cancelled")
        if not incumbent["accepted"]:
            report["status"] = "incumbent_rejected"
            raise p.Rejected("B2 incumbent rejected: " + str(incumbent.get("reason", incumbent["status"])))
        p.check_result(output / "incumbent/result.json")
        from .netclass import PARENT_POLICY
        source_policy=p.netclass_policy(source)
        if source_policy is not None and source_policy['mode']==PARENT_POLICY:
            report['netclass_parent_dsn_basis']=p.parent_dsn_basis(output)
        original_fresh(source, snapshot, source_hashes)
        best = Path(incumbent["candidate"])
        best_metrics, best_native = incumbent["metrics"], incumbent["native"]
        _quality(best_metrics)
        report["incumbent_metrics"] = copy.deepcopy(best_metrics)
        checkpoint("incumbent_validated", best, best_metrics)

        preparation_exhausted = False

        def attempt(proposal):
            nonlocal best, best_metrics, best_native, preparation_exhausted
            if preparation_exhausted or len(report["trials"]) >= MAX_TRIALS or remaining_work_budget() < MIN_TRIAL_SECONDS:
                return False
            original_fresh(source, snapshot, source_hashes)
            p.check_storage()
            # Source/storage inspection consumes the same wall and CPU budget.
            allowance = min(MAX_TRIAL_SECONDS, remaining_work_budget())
            if allowance < MIN_TRIAL_SECONDS:
                preparation_exhausted = True
                return False
            trial_id = f"trial-{len(report['trials']):04d}"
            trial_job = p.Job(output / "trials" / trial_id,
                              allowance, protect_local_settings=True)
            trial_job.deadline = min(trial_job.deadline, deadline - NATIVE_FINAL_RESERVE_SECONDS)
            candidate = trial_job.out / "candidate" / source.name
            record = {"id": trial_id, "proposal": proposal, "status": "rejected", "accepted": False,
                      "started_elapsed_seconds": time.monotonic() - started,
                      "base_candidate_sha256": p.sha(best)}
            try:
                shutil.copytree(best.parent, candidate.parent)
                sx.write(candidate, delete_routes(sx.read(candidate), proposal["route_ids"], nets, protected))
                if min(remaining_work_budget(), trial_job.deadline - time.monotonic()) < MIN_TRIAL_SECONDS:
                    preparation_exhausted = True
                    raise p.Rejected("insufficient trial budget after preparation")
                digest, native = p.validate_candidate(trial_job, original, candidate, source_hashes, protected)
                original_fresh(source, snapshot, source_hashes)
                record.update(candidate_sha256=digest, native=native,
                              native_report_sha256=p.sha(trial_job.out / "final-drc.json"))
                if not _valid(native):
                    record["status"] = "drc_rejected"
                    record["native_rejection_reasons"] = p.native_rejection_reasons(native)
                else:
                    trial_job.native("metrics", "metrics", candidate, trial_job.out / "metrics.json")
                    metrics = json.loads((trial_job.out / "metrics.json").read_text())
                    p.verify_candidate_files(candidate, source_hashes, digest)
                    original_fresh(source, snapshot, source_hashes)
                    record["metrics"] = metrics
                    if time.monotonic() > trial_job.deadline:
                        record["status"] = "timeout"
                    elif cpu_used(trial_job.steps) > seconds - NATIVE_FINAL_RESERVE_SECONDS:
                        record["status"] = "cpu_reserve_exhausted"
                    elif _improves(metrics, best_metrics, native, best_native):
                        record["accepted"], record["status"] = True, "improvement_validated"
                        best, best_metrics, best_native = candidate, metrics, native
                        report["improvements"] += 1
                    else:
                        record["status"] = "quality_rejected"
            except Exception as exc:
                record["reason"] = type(exc).__name__ + ": " + str(exc)
            finally:
                record["steps"] = _steps(trial_job, trial_id)
                all_steps.extend(record["steps"])
                record["finished_elapsed_seconds"] = time.monotonic() - started
                record["finished_observed_cpu_seconds"] = cpu_used()
                p.save_json(trial_job.out / "result.json", record)
                report["trials"].append({"id": trial_id, "receipt": str(trial_job.out / "result.json"),
                                         "status": record["status"], "accepted": record["accepted"]})
            if _cancelled(trial_job.steps):
                raise Cancelled("pruning trial cancelled")
            original_fresh(source, snapshot, source_hashes)
            checkpoint("trial_completed", best, best_metrics,
                       {"trial": trial_id, "trial_status": record["status"]})
            return record

        for grouped in ((True, "chains", False) if proposal_policy == "chains" else (True, False)):
            if grouped == "chains":
                from .chain_proposals import build
                from .placement_clearance import read_bytes
                raw = read_bytes(best)
                base_pin = hashlib.sha256(raw).hexdigest()
                batch = build(sx.parse(raw.decode('utf-8')), nets, protected)
                if p.sha(best) != base_pin:
                    raise p.Rejected("incumbent changed during chain proposal generation")
                report.setdefault("chain_proposal_batches", []).append(dict(batch, base_candidate_sha256=base_pin))
                pending = batch["proposals"]
            else:
                pending = proposals(sx.read(best), nets, protected, grouped)
            for proposal in pending:
                # A previous whole-net success may already have removed a route.
                available = {route_id(route) for route in eligible_routes(sx.read(best), nets, protected)}
                if not set(proposal["route_ids"]) <= available:
                    continue
                record = attempt(proposal)
                if not record:
                    break
                if proposal_policy in {"feedback", "chains"}:
                    # A failed native-valid singleton may leave redundant stubs.
                    # Every cleanup is another charged, fully validated attempt.
                    # Never use feedback from a stale board or altered report.
                    for _ in range(MAX_FEEDBACK_DEPTH):
                        if record["status"] != "quality_rejected":
                            break
                        failed_dir = output / "trials" / record["id"]
                        failed = failed_dir / "candidate" / source.name
                        original_fresh(source, snapshot, source_hashes)
                        p.verify_candidate_files(best, source_hashes, record["base_candidate_sha256"])
                        p.verify_candidate_files(failed, source_hashes, record["candidate_sha256"])
                        if p.sha(failed_dir / "final-drc.json") != record["native_report_sha256"]:
                            raise p.Rejected("native report changed before feedback proposal")
                        failed_tree = sx.read(failed)
                        decision = feedback_proposal(failed_tree, record["proposal"], record["native"],
                                                     best_native, nets, protected)
                        p.verify_candidate_files(failed, source_hashes, record["candidate_sha256"])
                        decision["parent_trial"] = record["id"]
                        decision["failed_candidate_sha256"] = record["candidate_sha256"]
                        decision["native_report_sha256"] = record["native_report_sha256"]
                        decision["base_candidate_sha256"] = record["base_candidate_sha256"]
                        if decision["proposed"]:
                            decision["proposal"]["parent_trial"] = record["id"]
                        p.save_json(failed_dir / "feedback-decision.json", decision)
                        if not decision["proposed"]:
                            break
                        p.verify_candidate_files(best, source_hashes, record["base_candidate_sha256"])
                        record = attempt(decision["proposal"])
                        if not record:
                            break

        original_fresh(source, snapshot, source_hashes)
        report["best_observed_metrics"] = best_metrics
        report["best_observed_candidate"] = str(best)
        report["finalization_started_elapsed_seconds"] = time.monotonic() - started
        if _remaining(deadline) < 12.0:
            raise p.Rejected("insufficient reserved time for final native validation")
        if seconds - cpu_used() < 12.0:
            raise p.Rejected("insufficient reserved CPU for final native validation")
        candidate = output / "candidate" / source.name
        shutil.copytree(best.parent, candidate.parent)
        final_hash, native = p.validate_candidate(final_job, original, candidate, source_hashes, protected)
        final_job.native("metrics", "metrics", candidate, output / "metrics.json")
        metrics = json.loads((output / "metrics.json").read_text())
        _quality(metrics)
        p.verify_candidate_files(candidate, source_hashes, final_hash)
        original_fresh(source, snapshot, source_hashes)
        for relative, expected in report["tools"]["implementation_sha256"].items():
            if p.sha(c.ROOT / relative) != expected:
                raise p.Rejected("implementation changed during pruning")
        if metrics != best_metrics or not _warning_signatures(native) <= _warning_signatures(best_native):
            raise p.Rejected("final native quality differs from validated incumbent")
        report.update(candidate=str(candidate), candidate_sha256=final_hash,
                      native_report_sha256=p.sha(output / "final-drc.json"), native=native,
                      metrics=metrics, invariants_unchanged=True,
                      native_rejection_reasons=p.native_rejection_reasons(native),
                      whole_project_drc_clean=_valid(native) and native["warnings"] == 0,
                      accepted=_valid(native), status="routing_accepted" if _valid(native) else "drc_rejected")
        checkpoint("final_validated", candidate, metrics)
    except Cancelled as exc:
        report.update(accepted=False, status="cancelled", reason=str(exc))
    except KeyboardInterrupt:
        report.update(accepted=False, status="cancelled", reason="interrupted between native stages")
    except Exception as exc:
        report["accepted"] = False
        if report["status"] != "incumbent_rejected":
            report["status"] = "rejected"
        report["reason"] = type(exc).__name__ + ": " + str(exc)
    all_steps.extend(_steps(final_job, "finalization"))
    report["steps"] = all_steps
    report["child_cpu_seconds"] = sum(step.get("cpu_seconds") or 0 for step in all_steps)
    report["monitor_cpu_seconds"] = sum(step.get("monitor_cpu_seconds") or 0 for step in all_steps)
    report["peak_child_rss_bytes"] = max([step.get("max_rss_bytes") or 0 for step in all_steps] + [0])
    report["resource_limitations"] = "Global wall and measured-CPU acceptance budgets include B2, every failed trial, final native validation and monitor CPU. CPU is checked after stages/completion, not preempted by the OS. Process-group and workdir polling guards can overshoot; no process-tree memory quota or full orphan CPU accounting is claimed. Stored totals precede the last receipt write; both caps are checked after it."

    def account():
        report["wall_seconds"] = time.monotonic() - started
        report["parent_cpu_seconds"] = time.process_time() - cpu_started
        report["total_cpu_seconds"] = report["parent_cpu_seconds"] + report["child_cpu_seconds"] + report["monitor_cpu_seconds"]
        if report["wall_seconds"] > seconds:
            report.update(accepted=False, status="timeout")
        elif report["total_cpu_seconds"] > seconds:
            report.update(accepted=False, status="cpu_limit")

    def stable():
        owned_destination(owner)
        pref.check_fresh(captured)
        if report.get('source_hashes') and (output/'snapshot').is_dir():
            original_fresh(source, output/'snapshot', report['source_hashes'])
        for relative, digest in report.get('tools', {}).get('implementation_sha256', {}).items():
            if p.sha(c.ROOT/relative) != digest:
                raise p.Rejected('implementation changed during pruning publication')

    from .floor_route import publish
    publish(output, report, stable, account,
            lambda: min(deadline-time.monotonic(), seconds-cpu_used()),
            owned=lambda: owned_destination(owner))
    return report
