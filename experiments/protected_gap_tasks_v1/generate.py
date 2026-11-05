"""Prospective deterministic geometric development tasks; no Native authority.

The fixed mask is chosen before outcomes. Retained protected routing and zone
intent are algorithm inputs; removed routing and the full reference-solution PCB
stay outside the fresh derived project and its byte-exact sidecars.
This does not establish electrical suitability, difficulty or family independence.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat

from autorouter import board_floor as floor, handoff as h, pipeline as p
from autorouter import placement_clearance as pc, sexpr as sx
from scripts.backup import require_headroom

POLICY = 'protected-gap-netgroup-half-v1'
SEED = 'protected-gap-v1-20261105'
PROJECT_BYTES = 32 * 1024**2


def _sha(tree):
    return hashlib.sha256(sx.dump(tree).encode()).hexdigest()


def derive(original):
    """Return a derived AST and compact mask facts without changing the input."""
    if type(original) is not list or not original or original[0] != 'kicad_pcb':
        raise ValueError('original KiCad PCB AST required')
    _, resolve = floor.source_net_identity(original)
    groups = {}
    for route in p.routes(original):
        if route[0] not in ('segment', 'via'):
            raise ValueError('protected-gap draft supports original segment/via records only')
        nets = sx.children(route, 'net')
        if len(nets) != 1:
            raise ValueError('one validated original route net required')
        name = resolve(nets[0], owner=route)
        if not name:
            raise ValueError('nonzero original route net required')
        lock_nodes = sx.children(route, 'locked')
        if (len(lock_nodes) > 1 or route.count('locked') > 1 or ('locked' in route and lock_nodes)
                or any(node not in (['locked'], ['locked', 'yes']) for node in lock_nodes)):
            raise ValueError('unqualified original lock marker')
        groups.setdefault(name, []).append(route)
    excluded = sorted(name for name, rows in groups.items() if any(p.locked(row) for row in rows))
    ranked = sorted((name for name in groups if name not in excluded),
        key=lambda name: (hashlib.sha256((SEED+'\0'+name).encode()).hexdigest(), name))
    if not ranked:
        raise ValueError('no eligible originally unlocked netgroups')
    removed = ranked[:(len(ranked)+1)//2]
    removed_set = set(removed)
    # Existing partial-completion projection preserves routing and clears only
    # derived top-level zone fill. No routing scope or product policy is changed.
    task = p.routing_task(original, 'partial_completion')
    task[:] = [row for row in task if not (isinstance(row, list) and row and row[0] in p.ROUTES
        and resolve(sx.one(row, 'net'), owner=row) in removed_set)]
    for row in p.routes(task):
        if not p.locked(row):
            row.append(['locked', 'yes'])
    expected = []
    for row in p.routes(original):
        if resolve(sx.one(row, 'net'), owner=row) not in removed_set:
            retained = sx.clone(row)
            if not p.locked(retained):
                retained.append(['locked', 'yes'])
            expected.append(retained)
    if not expected:
        raise ValueError('protected-gap task requires retained protected routing')
    if (p.immutable(task) != p.immutable(original) or p.routes(task) != expected
            or any(sx.children(zone, name) for zone in sx.children(task, 'zone') for name in p.DERIVED_ZONE)
            or not all(p.locked(row) for row in p.routes(task))):
        raise ValueError('protected-gap geometry, retention or derived-fill invariant differs')
    facts = dict(schema=1, policy=POLICY, seed=SEED,
        eligible_groups_ranked=ranked, excluded_original_locked_groups=excluded,
        removed_groups=removed, group_route_counts={name: len(rows) for name, rows in sorted(groups.items())},
        original_route_count=len(p.routes(original)), original_locked_route_count=sum(p.locked(row) for row in p.routes(original)),
        removed_route_count=sum(len(groups[name]) for name in removed), retained_route_count=len(expected),
        newly_locked_route_count=sum(not p.locked(row) for name, rows in groups.items() if name not in removed_set for row in rows),
        immutable_ast_sha256=_sha(p.immutable(original)), original_route_ast_sha256=_sha(p.routes(original)),
        derived_route_ast_sha256=_sha(expected), Native_demand_qualified=False,
        initial_opens=None, difficulty_established=False, family_independence_established=False,
        electrical_suitability_established=False, removed_route_geometry_in_algorithm_inputs=False,
        full_reference_solution_PCB_in_algorithm_inputs=False,
        retained_protected_reference_geometry_is_input=True)
    return task, facts


def generate(source, output, expected_source_hashes):
    """Make one fresh owned task; preserve partial outputs after any failure.

    Caller supplies a reviewed complete source inventory. This is a data working
    copy, not a metadata restoration or a routing/Native validation receipt.
    """
    source = h.real_path(source)
    output = h.real_path(output, existing=False)
    parent = output.parent
    if (source.suffix != '.kicad_pcb' or not parent.is_dir() or parent.stat().st_uid != os.getuid()
            or os.path.lexists(output) or source.parent == output or source.parent in output.parents
            or output in source.parents):
        raise p.Rejected('fresh owned nonoverlapping task output required')
    captured, directories = pc.inventory(source.parent, contents=True, max_bytes=PROJECT_BYTES, with_directories=True)
    before = {name: floor.sha(raw) for name, raw in captured.items()}
    if type(expected_source_hashes) is not dict or before != expected_source_hashes:
        raise p.Rejected('exact reviewed source inventory required')
    if source.name not in captured or source.with_suffix('.kicad_pro').name not in captured:
        raise p.Rejected('original PCB and project required')
    for name in captured:
        path = Path(name)
        if name != source.name and (path.suffix.lower() in {'.kicad_pcb', '.brd', '.dsn', '.ses', '.zip', '.tar', '.gz', '.tgz', '.bak'}
                or '.kicad_pcb-bak' in path.name.lower()):
            raise p.Rejected('reference routing/archives outside task inputs required: '+name)
    original = sx.parse(captured[source.name].decode())
    task, facts = derive(original)
    payload = (sx.dump(task)+'\n').encode()
    if len(payload) > PROJECT_BYTES:
        raise p.Rejected('derived PCB exceeds project bound')
    # Forecast the complete working copy, rewritten PCB, compact record and
    # minimum per-entry allocation. No clone/compression savings are assumed.
    peak = sum(map(len, captured.values())) + len(payload) + 1024**2 + 4096*(len(captured)+len(directories)+8)
    space = require_headroom(parent, peak, 'one protected-gap geometric task')
    p.check_storage(active_root=output)
    output.mkdir(mode=0o700)
    owner = {}; h.capture_destination(owner, output)
    destination = output/'project'
    copied = pc.copy_project(source.parent, destination, max_bytes=PROJECT_BYTES)
    if copied != before or h.owned_destination(owner) != output:
        raise p.Rejected('task copy source or ownership differs')
    target = destination/source.name
    info = target.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
        raise p.Rejected('exclusive owned task PCB required')
    sx.write(target, task)
    after = pc.inventory(destination, max_bytes=PROJECT_BYTES)
    expected = dict(before); expected[source.name] = floor.sha(payload)
    if (after != expected or pc.inventory(source.parent, max_bytes=PROJECT_BYTES) != before
            or sx.read(target) != task or h.owned_destination(owner) != output):
        raise p.Rejected('source, sidecar or generated task bytes changed')
    facts.update(source=str(source), source_hashes=before, task_source=str(target), task_hashes=after,
        peak_space_forecast=space, algorithm_input_directory=str(destination),
        task_scope='whole_board_unlocked_routing', Native_executed=False, ready_for_comparison=False,
        remaining_gates=['Original and derived Native validation with real refill; expected opens are not source conflicts.',
            'No new blocking findings and exact original-design/protected-route checks.',
            'Prospective all-arm freezer/protocol with equal budgets and no removed reference geometry.'])
    raw = (json.dumps(facts, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
    if len(raw) > 1024**2:
        raise p.Rejected('compact task provenance ceiling')
    with (h.owned_destination(owner)/'provenance.json').open('xb') as stream:
        stream.write(raw)
    return facts
