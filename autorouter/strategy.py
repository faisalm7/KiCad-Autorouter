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
ADAPTIVE_POLICY = "charged-first-single-sequence-v1"
STRONG_INCUMBENT_POLICY = "free-angle-clearance20-v1"
STRONG_WIDTH_INCUMBENT_POLICY = "free-angle-clearance20-global-width-v2"
STRONG_INCUMBENT_POLICIES = (STRONG_INCUMBENT_POLICY, STRONG_WIDTH_INCUMBENT_POLICY)


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


def _chain_context(job, best):
    """Reuse the pinned read-only Native geometry observer on a complete copy."""
    from . import floor_route as floor
    before = p.tree_hash(best.parent)
    local = job.out / 'candidate' / best.name
    shutil.copytree(best.parent, local.parent)
    if p.tree_hash(local.parent) != before:
        raise p.Rejected('chain geometry input copy differs')
    path = job.out / 'floor-final-context.json'
    job.step('floor-final', floor.context_argv('final', local, path))
    from .placement_clearance import read_bytes
    raw = read_bytes(path)
    context = json.loads(raw)
    context_pin = hashlib.sha256(raw).hexdigest()
    floor.context_binding(context, local, before, 'final')
    if p.sha(path) != context_pin or p.tree_hash(best.parent) != before or p.tree_hash(local.parent) != before:
        raise p.Rejected('chain geometry input changed')
    return context, context_pin


def _chain_context_inventory(folder):
    from .placement_clearance import inventory
    files, directories = inventory(folder, with_directories=True)
    return {'files': files, 'directories': list(directories)}


def _chain_context_fresh(directory, data):
    directory=Path(directory);folder=directory/'chain-context';record=data.get('chain_pad_context')
    if record is None:
        if folder.exists() or folder.is_symlink():raise p.Rejected('chain context binding missing')
        return
    if (type(record) is not dict or set(record)!={'file','sha256','inventory'}
        or record['file']!='chain-context/floor-final-context.json'
        or p.sha(directory/record['file'])!=record['sha256']
        or _chain_context_inventory(folder)!=record['inventory']):
        raise p.Rejected('chain context changed')


def _adaptive_key(base, proposal):
    ids = proposal.get('route_ids')
    if (type(base) is not str or len(base) != 64 or type(ids) is not list or not ids
            or len(ids) != len(set(ids)) or any(type(value) is not str for value in ids)):
        raise p.Rejected('malformed adaptive attempt identity')
    return base, tuple(sorted(ids))


def _adaptive_trial_native(directory, data, record):
    """Check a bound completed retained Native outcome; never run Native here."""
    from . import floor_route as f
    from .placement_clearance import read_bytes
    if (record.get('status') not in {'improvement_validated', 'drc_rejected', 'quality_rejected'}
            or 'reason' in record or _cancelled(record.get('steps', []))):
        return False
    guard = record.get('adaptive_trial_guard', {})
    numbers = [guard.get('wall_deadline_elapsed_seconds'), guard.get('work_cpu_limit_seconds'),
               record.get('finished_elapsed_seconds'), record.get('finished_observed_cpu_seconds')]
    if (any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in numbers)
            or numbers[2] > numbers[0] or numbers[3] > numbers[1]
            or numbers[0] > data['budget_seconds'] - NATIVE_FINAL_RESERVE_SECONDS
            or numbers[1] != data['cpu_budget_seconds'] - NATIVE_FINAL_RESERVE_SECONDS):
        return False
    if any(step.get('status') not in {'success', 'nonzero_exit'} for step in record.get('steps', [])):
        return False
    folder = Path(directory) / 'trials' / record['id']
    candidate = folder / 'candidate' / Path(data['source']).name
    p.verify_candidate_files(candidate, data['source_hashes'], record['candidate_sha256'])
    before = dict(data['source_hashes']); before[candidate.name] = p.sha(folder / 'pre-refill.kicad_pcb')
    refill = folder / 'refill' / candidate.name
    f.check_drc_stage(folder, record, 'refill-drc', refill, refill, True, before, sandboxed=False)
    rebuilt = p.transplant_fill(sx.read(folder / 'pre-refill.kicad_pcb'), sx.read(refill))
    if (sx.dump(rebuilt) + '\n').encode() != read_bytes(candidate):
        raise p.Rejected('adaptive trial differs from saved refill reconstruction')
    native = f.check_drc_stage(folder, record, 'final-drc', candidate,
        folder / 'final-drc-input' / candidate.name, False, p.tree_hash(candidate.parent),
        schematic_parity=candidate.with_suffix('.kicad_sch').name in data['source_hashes'], sandboxed=False)
    if (p.sha(folder / 'final-drc.json') != record['native_report_sha256']
            or f.canonical(native) != f.canonical(record['native'])
            or record.get('accepted') is not (record['status'] == 'improvement_validated')
            or (record['status'] == 'drc_rejected') == _valid(native)):
        raise p.Rejected('adaptive Native outcome identity/status differs')
    if record['status'] != 'drc_rejected':
        if f.read_json(folder / 'metrics.json') != record.get('metrics'):
            raise p.Rejected('adaptive metric receipt differs')
        f.process_check(folder, record, 'metrics', [str(c.PYTHON),
            str(c.ROOT / 'autorouter/native.py'), 'metrics', str(candidate), str(folder / 'metrics.json')])
        _quality(record['metrics'])
    return True


def _adaptive_branch_fresh(directory, data):
    from . import floor_route as f
    directory = Path(directory); path = directory / 'adaptive-branch.json'
    if data.get('proposal_policy') != 'adaptive':
        if 'adaptive_branch' in data or path.exists() or path.is_symlink():
            raise p.Rejected('adaptive branch on another proposal policy')
        return None
    if data.get('adaptive_branch') != {'file':path.name, 'sha256':p.sha(path)}:
        raise p.Rejected('adaptive branch binding missing or changed')
    branch = f.read_json(path)
    material = branch.get('material')
    if type(material) is not dict or not 1 <= len(material) <= MAX_TRIALS + 1:
        raise p.Rejected('adaptive prefix material census missing')
    allowed = {'incumbent'} | {'trials/trial-%04d' % i for i in range(MAX_TRIALS)}
    if not set(material) <= allowed:
        raise p.Rejected('adaptive prefix material escaped bounded owned paths')
    for name, expected in material.items():
        if _chain_context_inventory(directory / name) != expected:
            raise p.Rejected('adaptive prefix evidence changed: ' + name)
    if data.get('adaptive_branch') != {'file':path.name, 'sha256':p.sha(path)}:
        raise p.Rejected('adaptive branch changed during prefix inventory')
    return branch


def check_adaptive_policy(directory, data):
    """Pure replay of the charged probe decision; full final Native stays separate."""
    from . import floor_route as f
    from .placement_clearance import read_bytes
    directory = Path(directory); branch = _adaptive_branch_fresh(directory, data)
    if branch is None: return None
    keys = {'schema','policy','before_probe_trials','probe_trials','entry_candidate','entry_sha256',
            'after_candidate','after_sha256','outcome','continuation','reason','probe_remaining_seconds',
            'chain_remaining_seconds','material'}
    if set(branch) != keys or branch['schema'] != 1 or branch['policy'] != ADAPTIVE_POLICY:
        raise p.Rejected('adaptive decision schema differs')
    rows = data.get('trials'); before = branch['before_probe_trials']; ids = branch['probe_trials']
    if (type(rows) is not list or len(rows) > MAX_TRIALS or type(before) is not int
            or not 0 <= before <= len(rows) or type(ids) is not list
            or len(ids) > 1 + MAX_FEEDBACK_DEPTH
            or ids != ['trial-%04d' % i for i in range(before, before + len(ids))]
            or before + len(ids) > len(rows)):
        raise p.Rejected('adaptive probe sequence census differs')
    records = []; seen = set()
    for i, row in enumerate(rows):
        trial_id = 'trial-%04d' % i; receipt = directory / 'trials' / trial_id / 'result.json'
        record = f.read_json(receipt)
        if (type(record.get('accepted')) is not bool
                or record['accepted'] is not (record['status']=='improvement_validated')):
            raise p.Rejected('adaptive trial acceptance/status differs')
        if row != {'id':trial_id,'receipt':str(receipt),'status':record['status'],'accepted':record['accepted']} or record['id'] != trial_id:
            raise p.Rejected('adaptive trial index differs from retained receipt')
        key = _adaptive_key(record['base_candidate_sha256'], record['proposal'])
        if key in seen: raise p.Rejected('duplicate adaptive attempt on the same incumbent')
        seen.add(key); records.append(record)
    prefix = before + len(ids)
    if set(branch['material']) != {'incumbent'} | {'trials/trial-%04d' % i for i in range(prefix)}:
        raise p.Rejected('adaptive decision omits prefix material')
    incumbent = f.read_json(directory / 'incumbent/result.json')
    best = directory / 'incumbent/candidate' / Path(data['source']).name
    if incumbent.get('candidate') != str(best): raise p.Rejected('adaptive incumbent path differs')
    p.verify_candidate_files(best, data['source_hashes'], incumbent['candidate_sha256'])
    best_metrics, best_native = incumbent['metrics'], incumbent['native']
    original = sx.read(directory / 'snapshot' / best.name)
    nets = zone_net_ids(original); protected = [r for r in p.routes(original) if p.locked(r)]
    prior_keys = set(); sequence_complete = True
    entry_best = None
    for i, record in enumerate(records[:prefix]):
        if i == before:
            entry_best = best
            if (branch['entry_candidate'] != str(best.relative_to(directory)) or branch['entry_sha256'] != p.sha(best)):
                raise p.Rejected('adaptive probe entry incumbent differs')
            ranked = [proposal for proposal in proposals(sx.read(best), nets, protected, False)
                      if _adaptive_key(p.sha(best), proposal) not in prior_keys]
            if not ranked or record['proposal'] != ranked[0]:
                raise p.Rejected('adaptive probe was not the highest ranked untried singleton')
        proposal = record['proposal']
        if record['base_candidate_sha256'] != p.sha(best):
            raise p.Rejected('adaptive trial does not use the current incumbent')
        if i < before and not (proposal['kind'] == 'whole_zone_net' or proposal.get('root_kind') == 'whole_zone_net'):
            raise p.Rejected('adaptive probe did not immediately follow the whole-net phase')
        if i > before:
            parent = records[i-1]; failed = directory / 'trials' / parent['id'] / 'candidate' / best.name
            decision = feedback_proposal(sx.read(failed), parent['proposal'], parent['native'], best_native, nets, protected)
            decision.update(parent_trial=parent['id'], failed_candidate_sha256=parent['candidate_sha256'],
                            native_report_sha256=parent['native_report_sha256'], base_candidate_sha256=parent['base_candidate_sha256'])
            if decision['proposed']: decision['proposal']['parent_trial'] = parent['id']
            retained = f.read_json(directory / 'trials' / parent['id'] / 'feedback-decision.json')
            if (parent['status'] != 'quality_rejected' or not decision['proposed'] or retained != decision
                    or proposal != decision['proposal']): raise p.Rejected('adaptive feedback lineage differs')
        complete = _adaptive_trial_native(directory, data, record)
        if complete:
            preimage = directory / 'trials' / record['id'] / 'pre-refill.kicad_pcb'
            expected = delete_routes(sx.read(best), proposal['route_ids'], nets, protected)
            if (sx.dump(expected) + '\n').encode() != read_bytes(preimage):
                raise p.Rejected('adaptive trial deletion differs from its bound incumbent')
        if complete and record['status']=='quality_rejected' and _improves(record['metrics'],best_metrics,record['native'],best_native):
            raise p.Rejected('adaptive quality rejection hides an improving trial')
        if i >= before: sequence_complete = sequence_complete and complete
        if record['accepted']:
            if not complete or not _improves(record['metrics'], best_metrics, record['native'], best_native):
                raise p.Rejected('adaptive accepted trial does not improve its incumbent')
            best = directory / 'trials' / record['id'] / 'candidate' / best.name
            best_metrics, best_native = record['metrics'], record['native']
        prior_keys.add(_adaptive_key(record['base_candidate_sha256'], proposal))
    if entry_best is None:
        entry_best = best
        if branch['entry_candidate'] != str(best.relative_to(directory)) or branch['entry_sha256'] != p.sha(best):
            raise p.Rejected('adaptive no-probe entry differs')
    if branch['after_candidate'] != str(best.relative_to(directory)) or branch['after_sha256'] != p.sha(best):
        raise p.Rejected('adaptive sequence result incumbent differs')
    if not ids:
        reason = branch['reason']; remaining = branch['probe_remaining_seconds']
        ranked = [proposal for proposal in proposals(sx.read(best), nets, protected, False)
                  if _adaptive_key(p.sha(best), proposal) not in prior_keys]
        if reason == 'no_untried_singleton':
            if ranked: raise p.Rejected('adaptive no-probe claim hides an available singleton')
        elif reason == 'insufficient_work_budget':
            if type(remaining) not in (int,float) or not math.isfinite(remaining) or not 0 <= remaining < MIN_TRIAL_SECONDS:
                raise p.Rejected('adaptive no-budget skip is not bound')
        elif reason == 'preparation_exhausted':
            if not (type(remaining) in (int,float) and math.isfinite(remaining) and 0 <= remaining < MIN_TRIAL_SECONDS) and not (before and records[before-1].get('reason','').endswith('insufficient trial budget after preparation')):
                raise p.Rejected('adaptive preparation skip lacks a retained exhausted attempt')
        elif reason == 'trial_cap':
            if before != MAX_TRIALS: raise p.Rejected('adaptive trial-cap skip differs')
        else: raise p.Rejected('unknown adaptive no-probe reason')
        outcome, continuation = 'no_probe', 'stop'
    else:
        last = records[prefix-1]
        if last['status'] == 'quality_rejected' and last['proposal'].get('feedback_depth',0) < MAX_FEEDBACK_DEPTH:
            decision_path = directory / 'trials' / last['id'] / 'feedback-decision.json'
            decision = f.read_json(decision_path)
            expected = feedback_proposal(sx.read(decision_path.parent / 'candidate' / best.name), last['proposal'], last['native'], best_native, nets, protected)
            expected.update(parent_trial=last['id'],failed_candidate_sha256=last['candidate_sha256'],native_report_sha256=last['native_report_sha256'],base_candidate_sha256=last['base_candidate_sha256'])
            if expected['proposed']: expected['proposal']['parent_trial']=last['id']
            if decision != expected: raise p.Rejected('adaptive terminal feedback decision differs')
            if decision['proposed']: sequence_complete = False
        if not sequence_complete: outcome, continuation = 'incomplete', 'stop'
        elif p.sha(best) != branch['entry_sha256']: outcome, continuation = 'improved', 'feedback_singles'
        elif last['status'] in {'drc_rejected','quality_rejected'}: outcome, continuation = 'completed_rejection', 'chains_then_singles'
        else: raise p.Rejected('adaptive terminal status is inconsistent')
    reasons={'improved':{'completed_sequence_improved'},
             'completed_rejection':{'completed_native_sequence_rejected'},
             'incomplete':{'incomplete_native_sequence','insufficient_work_budget','preparation_exhausted','trial_cap','duplicate_attempt'}}
    if outcome in reasons and branch['reason'] not in reasons[outcome]:
        raise p.Rejected('adaptive branch reason differs from its outcome')
    if (branch['outcome'],branch['continuation']) != (outcome,continuation):
        raise p.Rejected('adaptive branch classification differs from the completed sequence')
    if continuation == 'stop' and len(records) != prefix:
        raise p.Rejected('adaptive stop decision has subsequent trials')
    remaining = branch['chain_remaining_seconds']
    if continuation == 'chains_then_singles':
        if type(remaining) not in (int,float) or not math.isfinite(remaining) or remaining < 0:
            raise p.Rejected('adaptive chain allocation sample missing')
    elif remaining is not None: raise p.Rejected('adaptive non-chain branch claims a chain allocation')
    _adaptive_branch_fresh(directory, data)
    return branch


def check_chain_context(directory, data):
    """Shared receipt readback for the optional geometry-backed proposal batch."""
    from . import floor_route as f, chain_proposals as cp
    directory=Path(directory)
    adaptive=check_adaptive_policy(directory,data)
    _chain_context_fresh(directory,data)
    record=data.get('chain_pad_context')
    if record is None:
        if adaptive is not None:
            chosen=adaptive['continuation']=='chains_then_singles'
            skip=('insufficient remaining work budget' if chosen else 'adaptive '+adaptive['outcome'])
            if (data.get('chain_context_skipped')!=skip or chosen and adaptive['chain_remaining_seconds']>=MIN_TRIAL_SECONDS
                    or any(f.read_json(Path(row['receipt']))['proposal']['kind']=='endpoint_chain' for row in data['trials'])):
                raise p.Rejected('adaptive chain context missing without a bound branch skip')
        if data.get('proposal_policy')=='chains' and data.get('chain_context_skipped') not in {
                'insufficient remaining work budget','no grouped zone routing opportunity'}:
            raise p.Rejected('chain context missing without declared skip')
        if data.get('chain_proposal_batches'):raise p.Rejected('chain batches have no bound context')
        return
    if data.get('proposal_policy')!='chains' and (adaptive is None or adaptive['continuation']!='chains_then_singles'):
        raise p.Rejected('chain context on another proposal policy')
    folder=directory/'chain-context';context_path=folder/'floor-final-context.json'
    context=f.read_json(context_path);local=folder/'candidate'/Path(data['source']).name
    f.context_binding(context,local,p.tree_hash(local.parent),'final')
    f.process_check(folder,data,'floor-final',f.context_argv('final',local,context_path))
    tree=sx.read(local)
    batch=cp.build(tree,zone_net_ids(tree),[r for r in p.routes(tree) if p.locked(r)],native_pads=context['pads'])
    if adaptive is not None and p.sha(local)!=adaptive['after_sha256']:
        raise p.Rejected('adaptive chain context differs from the probe result incumbent')
    expected=dict(batch,base_candidate_sha256=p.sha(local))
    if data.get('chain_proposal_batches')!=[expected]:raise p.Rejected('chain context proposal replay differs')
    _chain_context_fresh(directory,data)


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


def _incumbent_route_options(policy, scoring, settings_path=None, preference_overrides=None):
    """One private, already-qualified stock configuration; no public preset."""
    if policy is None:return None
    if (type(policy) is not str or policy not in STRONG_INCUMBENT_POLICIES or scoring != 'via_default'
            or settings_path is not None or preference_overrides is not None):
        raise p.Rejected('stronger incumbent requires literal policy/via_default and no preferences')
    options=dict(_fanout_enabled=False, _optimizer_enabled=False, _engine_clearance_margin_nm=20000)
    if policy==STRONG_WIDTH_INCUMBENT_POLICY:options['_engine_global_width_policy']=p.ENGINE_GLOBAL_WIDTH_POLICY
    return options


def _incumbent_policy_contract(directory, incumbent, policy=STRONG_INCUMBENT_POLICY):
    contract=dict(schema=1, policy=policy, profile='tuned-free-angle',
        adapter='both', scope='whole_board_unlocked_routing', guidance='native', layers='source_all',
        scoring_variant='via_default', fanout_enabled=False, optimizer_enabled=False, clearance_margin_nm=20000,
        incumbent=dict(file='incumbent/result.json', sha256=p.sha(Path(directory)/'incumbent/result.json'),
            assigned_seconds=incumbent.get('budget_seconds'), engine_angle_binding=incumbent.get('engine_angle_binding')))
    if policy==STRONG_WIDTH_INCUMBENT_POLICY:
        contract.update(global_width_policy=incumbent.get('engine_global_width_policy'),minimum_width_guard=incumbent.get('minimum_width_guard'))
    return contract


def check_incumbent_policy(directory, data, incumbent=None):
    """Parent-only reciprocal binding; full child engine/Native checks remain shared."""
    from . import floor_route as f
    from .placement_clearance import read_bytes
    directory=Path(directory);path=directory/'pruning-incumbent-policy.json'
    incumbent=f.read_json(directory/'incumbent/result.json') if incumbent is None else incumbent
    child_marked=(incumbent.get('engine_profile')=='tuned-free-angle' or any(key in incumbent for key in
        ('engine_fanout_override','engine_optimizer_override','engine_planning_clearance_margin_nm','engine_angle_binding','engine_global_width_policy')))
    if not (child_marked or 'incumbent_policy' in data or 'incumbent_policy_binding' in data or path.exists() or path.is_symlink()):return None
    policy=data.get('incumbent_policy')
    binding=data.get('incumbent_policy_binding')
    if (type(data.get('incumbent_policy')) is not str or policy not in STRONG_INCUMBENT_POLICIES
            or type(binding) is not dict or set(binding)!={'file','sha256'} or binding.get('file')!=path.name
            or data.get('incumbent_baseline')!='B2_free_angle_clearance20' or data.get('engine_profile')!='tuned'
            or data.get('incumbent_scoring_variant')!='via_default'
            or any(key in data for key in ('engine_budget','engine_fanout_override','engine_optimizer_override','engine_planning_clearance_margin_nm','engine_angle_binding','engine_global_width_policy'))
            or any((directory/name).exists() or (directory/name).is_symlink() for name in ('engine-angle.json','engine-free-angle.dsn','engine-process.json'))):
        raise p.Rejected('missing or malformed parent-only stronger incumbent policy')
    raw=read_bytes(path,8192)
    if hashlib.sha256(raw).hexdigest()!=binding['sha256'] or f.read_json(path)!=_incumbent_policy_contract(directory,incumbent,policy):
        raise p.Rejected('stronger incumbent receipt/configuration contract changed')
    assigned=incumbent.get('budget_seconds')
    if (type(assigned) not in (int,float) or not math.isfinite(assigned) or assigned<5
            or assigned>data['budget_seconds']-NATIVE_FINAL_RESERVE_SECONDS
            or incumbent.get('cpu_budget_seconds')!=assigned or incumbent.get('engine_profile')!='tuned-free-angle'
            or incumbent.get('scoring_variant')!='via_default' or incumbent.get('engine_fanout_override') is not False
            or incumbent.get('engine_optimizer_override') is not False
            or type(incumbent.get('engine_planning_clearance_margin_nm')) is not int or incumbent['engine_planning_clearance_margin_nm']!=20000
            or data.get('finalization_reserve_seconds')!=NATIVE_FINAL_RESERVE_SECONDS or data.get('finalization_cpu_reserve_seconds')!=NATIVE_FINAL_RESERVE_SECONDS):
        raise p.Rejected('stronger incumbent assigned budget or qualified private configuration differs')
    if policy==STRONG_WIDTH_INCUMBENT_POLICY:
        if p.check_engine_global_width_policy(incumbent)!=p.ENGINE_GLOBAL_WIDTH_POLICY:
            raise p.Rejected('stronger width incumbent lacks exact original global width policy')
    elif ('engine_global_width_policy' in incumbent or incumbent.get('engine_budget',{}).get('strict_class_targets') is not False):
        raise p.Rejected('original stronger incumbent requires non-strict native class/width targets')
    preferences=f.read_json(directory/'pruning-preferences.json')
    expected={'adapter':'both','profile':'tuned','seconds':data['budget_seconds'],'scoring_preference':'via_default'}
    if preferences.get('preset') is not None or preferences.get('overrides')!=expected:
        raise p.Rejected('stronger incumbent cannot adopt external/alternate preferences')
    return policy


def check_incumbent_scoring(directory, data):
    """Bind an explicitly chosen scoring preset to the fresh charged solve."""
    from . import floor_route as f
    check_chain_context(directory, data)
    check_pruning_preferences(directory, data)
    path=Path(directory)/'incumbent/result.json';inc=f.read_json(path)
    policy=check_incumbent_policy(directory,data,inc)
    marker=Path(directory)/'pruning-scoring.json'
    variant=data.get('incumbent_scoring_variant')
    p.engine_scoring_settings(variant)
    if (data.get('strategy')!='native_validated_zone_net_pruning'
            or inc.get('scoring_variant')!=variant or inc.get('engine_profile')!=('tuned-free-angle' if policy else 'tuned')
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
    if policy is not None:
        check_incumbent_policy(directory,data)
        from .local_settings import check_normal_policy
        check_normal_policy(path.parent,inc,max_bytes=128*1024**2,max_files=2048)


def prune(source, output, seconds=120, *, proposal_policy="single", incumbent_scoring=None,
          settings_path=None, preference_overrides=None, _incumbent_policy=None):
    """Run tuned B2 plus greedy pruning within one wall/CPU budget, retaining trials.

    A 25-second reserve is withheld from B2/trials for final emission and native
    checks. It is a planning reserve, not a promise that slow native tooling will
    finish. Exhausting the global budget always rejects the root result.
    """
    started, cpu_started = time.monotonic(), time.process_time()
    incumbent_options=_incumbent_route_options(_incumbent_policy,incumbent_scoring,settings_path,preference_overrides)
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
    if not isinstance(proposal_policy, str) or proposal_policy not in {"single", "feedback", "chains", "adaptive"}:
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
    if incumbent_options is not None:
        report.update(incumbent_policy=_incumbent_policy,incumbent_baseline='B2_free_angle_clearance20')
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
        if incumbent_options is not None:
            if _incumbent_policy==STRONG_WIDTH_INCUMBENT_POLICY:p.global_width_source_guard(source)
            elif p.netclass_policy(source) is not None or p.minimum_width_guard(source,'both') is not None:
                raise p.Rejected('stronger incumbent requires derived non-strict native class/width targets')
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
        if incumbent_options is not None:
            incumbent = p.route(source,output/'incumbent',incumbent_seconds,False,'both','tuned-free-angle',
                scoring_variant='via_default',**incumbent_options)
            report['incumbent_receipt_sha256']=p.sha(output/'incumbent/result.json')
            policy_path=output/'pruning-incumbent-policy.json'
            p.save_json(policy_path,_incumbent_policy_contract(output,incumbent,_incumbent_policy))
            report['incumbent_policy_binding']={'file':policy_path.name,'sha256':p.sha(policy_path)}
        elif incumbent_scoring is None:
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
        adaptive_seen = set()
        last_attempt_skip = None

        def attempt(proposal):
            nonlocal best, best_metrics, best_native, preparation_exhausted, last_attempt_skip
            last_attempt_skip = None
            if preparation_exhausted or len(report["trials"]) >= MAX_TRIALS or remaining_work_budget() < MIN_TRIAL_SECONDS:
                last_attempt_skip = ('trial_cap' if len(report['trials']) >= MAX_TRIALS else
                    'preparation_exhausted' if preparation_exhausted else 'insufficient_work_budget')
                return False
            key = _adaptive_key(p.sha(best), proposal) if proposal_policy == 'adaptive' else None
            if key is not None and key in adaptive_seen:
                last_attempt_skip = 'duplicate_attempt'
                return False
            original_fresh(source, snapshot, source_hashes)
            p.check_storage()
            # Source/storage inspection consumes the same wall and CPU budget.
            allowance = min(MAX_TRIAL_SECONDS, remaining_work_budget())
            if allowance < MIN_TRIAL_SECONDS:
                preparation_exhausted = True
                last_attempt_skip = 'insufficient_work_budget'
                return False
            if key is not None: adaptive_seen.add(key)
            trial_id = f"trial-{len(report['trials']):04d}"
            trial_job = p.Job(output / "trials" / trial_id,
                              allowance, protect_local_settings=True)
            trial_job.deadline = min(trial_job.deadline, deadline - NATIVE_FINAL_RESERVE_SECONDS)
            candidate = trial_job.out / "candidate" / source.name
            record = {"id": trial_id, "proposal": proposal, "status": "rejected", "accepted": False,
                      "started_elapsed_seconds": time.monotonic() - started,
                      "base_candidate_sha256": p.sha(best)}
            if proposal_policy == "adaptive":
                record["adaptive_trial_guard"] = {"wall_deadline_elapsed_seconds":min(seconds-NATIVE_FINAL_RESERVE_SECONDS,trial_job.deadline-started),
                    "work_cpu_limit_seconds":seconds-NATIVE_FINAL_RESERVE_SECONDS}
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

        def adaptive_sequence(record):
            complete = record is not False
            for _ in range(MAX_FEEDBACK_DEPTH):
                if not record or record["status"] != "quality_rejected":
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
                next_record = attempt(decision["proposal"])
                if not next_record:
                    complete = False
                    break
                record = next_record
            return record, complete

        def adaptive_chains():
            from .chain_proposals import build
            from .placement_clearance import read_bytes
            decision['chain_remaining_seconds'] = remaining_work_budget()
            if decision['chain_remaining_seconds'] < MIN_TRIAL_SECONDS:
                report['chain_context_skipped']='insufficient remaining work budget'
                return []
            context_job = p.Job(output / 'chain-context', min(8.0, remaining_work_budget()), protect_local_settings=True)
            try:
                context, context_pin = _chain_context(context_job, best)
            finally:
                all_steps.extend(_steps(context_job, 'chain-context'))
            context_path = context_job.out / 'floor-final-context.json'
            report['chain_pad_context']={'file':str(context_path.relative_to(output)), 'sha256':context_pin,
                                         'inventory':_chain_context_inventory(context_job.out)}
            raw = read_bytes(best)
            base_pin = hashlib.sha256(raw).hexdigest()
            if context['input_hashes_before'] != p.tree_hash(best.parent):
                raise p.Rejected('chain native pad context differs from incumbent')
            batch = build(sx.parse(raw.decode('utf-8')), nets, protected, native_pads=context['pads'])
            _chain_context_fresh(output, report)
            if p.sha(best) != base_pin:
                raise p.Rejected("incumbent changed during chain proposal generation")
            report.setdefault("chain_proposal_batches", []).append(dict(batch, base_candidate_sha256=base_pin))
            pending = batch["proposals"]
            return pending


        if proposal_policy == 'adaptive':
            # Whole-net work and each feedback cleanup remain fully charged.
            for proposal in proposals(sx.read(best), nets, protected, True):
                record = attempt(proposal)
                if not record: break
                adaptive_sequence(record)
            before_probe = len(report['trials']); entry = best
            decision = dict(schema=1,policy=ADAPTIVE_POLICY,before_probe_trials=before_probe,
                probe_trials=[],entry_candidate=str(entry.relative_to(output)),entry_sha256=p.sha(entry),
                after_candidate=str(entry.relative_to(output)),after_sha256=p.sha(entry),
                outcome='no_probe',continuation='stop',reason='no_untried_singleton',
                probe_remaining_seconds=remaining_work_budget(),chain_remaining_seconds=None)
            ranked = [proposal for proposal in proposals(sx.read(best), nets, protected, False)
                      if _adaptive_key(p.sha(best),proposal) not in adaptive_seen]
            if ranked:
                record = attempt(ranked[0])
                if record:
                    terminal, sequence_finished = adaptive_sequence(record)
                    decision['probe_trials']=[row['id'] for row in report['trials'][before_probe:]]
                    sequence=[json.loads(Path(row['receipt']).read_text()) for row in report['trials'][before_probe:]]
                    completed=sequence_finished and all(_adaptive_trial_native(output,report,row) for row in sequence)
                    if not completed:
                        decision.update(outcome='incomplete',reason=last_attempt_skip or 'incomplete_native_sequence')
                    elif p.sha(best)!=decision['entry_sha256']:
                        decision.update(outcome='improved',continuation='feedback_singles',reason='completed_sequence_improved')
                    elif terminal['status'] in {'drc_rejected','quality_rejected'}:
                        decision.update(outcome='completed_rejection',continuation='chains_then_singles',reason='completed_native_sequence_rejected')
                    else: raise p.Rejected('unclassified adaptive probe result')
                else:
                    decision.update(reason=last_attempt_skip,probe_remaining_seconds=remaining_work_budget())
            decision.update(after_candidate=str(best.relative_to(output)),after_sha256=p.sha(best))
            if decision['continuation']=='chains_then_singles':
                for proposal in adaptive_chains():
                    available={route_id(route) for route in eligible_routes(sx.read(best),nets,protected)}
                    if not set(proposal['route_ids'])<=available: continue
                    record=attempt(proposal)
                    if not record:
                        if last_attempt_skip == 'duplicate_attempt': continue
                        break
                    adaptive_sequence(record)
            else: report['chain_context_skipped']='adaptive '+decision['outcome']
            if decision['continuation'] in {'feedback_singles','chains_then_singles'}:
                while True:
                    # Rerank from each genuinely current incumbent. A failed
                    # deletion may retry only after its base candidate changes.
                    pending=[proposal for proposal in proposals(sx.read(best),nets,protected,False)
                             if _adaptive_key(p.sha(best),proposal) not in adaptive_seen]
                    if not pending: break
                    record=attempt(pending[0])
                    if not record: break
                    adaptive_sequence(record)
            prefix=before_probe+len(decision['probe_trials'])
            decision['material']={name:_chain_context_inventory(output/name) for name in
                ['incumbent',*('trials/trial-%04d'%i for i in range(prefix))]}
            p.save_json(output/'adaptive-branch.json',decision)
            report['adaptive_branch']={'file':'adaptive-branch.json','sha256':p.sha(output/'adaptive-branch.json')}
        else:
            for grouped in ((True, "chains", False) if proposal_policy == "chains" else (True, False)):
                if grouped == "chains":
                    from .chain_proposals import build
                    from .placement_clearance import read_bytes
                    if remaining_work_budget() < MIN_TRIAL_SECONDS:
                        report['chain_context_skipped']='insufficient remaining work budget'
                        continue
                    context_job = p.Job(output / 'chain-context', min(8.0, remaining_work_budget()), protect_local_settings=True)
                    try:
                        context, context_pin = _chain_context(context_job, best)
                    finally:
                        all_steps.extend(_steps(context_job, 'chain-context'))
                    context_path = context_job.out / 'floor-final-context.json'
                    report['chain_pad_context']={'file':str(context_path.relative_to(output)), 'sha256':context_pin,
                                                 'inventory':_chain_context_inventory(context_job.out)}
                    raw = read_bytes(best)
                    base_pin = hashlib.sha256(raw).hexdigest()
                    if context['input_hashes_before'] != p.tree_hash(best.parent):
                        raise p.Rejected('chain native pad context differs from incumbent')
                    batch = build(sx.parse(raw.decode('utf-8')), nets, protected, native_pads=context['pads'])
                    _chain_context_fresh(output, report)
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
        if report.get('accepted'):
            _chain_context_fresh(output,report)
            _adaptive_branch_fresh(output,report)
            if incumbent_options is not None:
                check_incumbent_scoring(output,report)
                from .local_settings import check_normal_policy
                check_normal_policy(output,report,max_bytes=128*1024**2,max_files=2048)

    from .floor_route import publish
    publish(output, report, stable, account,
            lambda: min(deadline-time.monotonic(), seconds-cpu_used()),
            owned=lambda: owned_destination(owner))
    return report
