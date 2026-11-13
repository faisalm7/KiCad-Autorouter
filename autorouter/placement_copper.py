"""Opt-in affected-net copper planning for a separate placement candidate.

Pure source work only: no file writes, approvals, routing or Native execution.
The default placement path is unchanged. Every incident net is rerouted as a
whole; a locked or explicitly protected incident net/route refuses this scope.
Unrelated copper is immutable. Existing source-contract limits apply, including
refusal of unknown-net source copper, vias and arcs. Final original-project,
protected-copper and actual Native acceptance remain the caller's responsibility.
"""
from __future__ import annotations

import copy
import hashlib
import uuid

from . import routing_scope as rs, sexpr as sx, board_floor
from experiments.placement_native_proposal_v1 import contract as c
from experiments.constrained_placement_v1 import constraints

POLICY = 'placement-affected-nets-v1'
KIND = 'autorouter.placement-copper-plan.v1'


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _uuids(value, *, maximum, empty=False):
    if (type(value) is not list or not (0 if empty else 1) <= len(value) <= maximum
            or any(type(item) is not str for item in value) or len(set(value)) != len(value)):
        raise ValueError('Explicit bounded unique UUID list required')
    try:
        valid = all(str(uuid.UUID(item)) == item and uuid.UUID(item).int != 0 for item in value)
    except (ValueError, AttributeError) as exc:
        raise ValueError('Canonical nonzero UUIDs required') from exc
    if not valid:
        raise ValueError('Canonical nonzero UUIDs required')
    return list(value)


def _observe(raw, scope=None):
    # Reuse the same deterministic source admission order as placement_intent.
    if scope is not None:
        if type(scope) is not str or scope not in (c.MULTIPAD_SCOPE, c.ORDINARY_SCOPE, c.CONTEXT_SCOPE, c.THT_SCOPE):
            raise ValueError('Explicit supported copper-plan placement scope required')
        return c.inspect_board(raw, scope=scope)
    try:
        return c.inspect_board(raw, scope=c.MULTIPAD_SCOPE)
    except ValueError:
        try:
            return c.inspect_board(raw, scope=c.ORDINARY_SCOPE)
        except ValueError:
            return c.inspect_fixed_context(raw)


def _encoded(value):
    encoded = constraints.encoded(value)
    pending = [value]
    while pending:
        item = pending.pop()
        if type(item) is dict:
            if any(type(key) is not str for key in item):
                raise ValueError('Plan requires string JSON object keys')
            pending.extend(item.values())
        elif type(item) is list:
            pending.extend(item)
        elif item is not None and type(item) not in (str, int, bool):
            raise ValueError('Plan requires exact JSON data types')
    return encoded


def _record(route, mapping):
    return dict(uuid=c.uid(route), kind=route[0], net_name=rs._net_name(route, mapping),
                locked=rs._locked(route), record_sha256=_sha(sx.dump(route).encode()),
                ast=copy.deepcopy(route))


def propose(source_bytes, selected, *, protected_names=None, protected_route_ids=None, scope=None):
    """Describe affected copper without authorizing its removal or placement.

    Names and UUIDs are exact source identities, never inferred electrical roles.
    Protection lists may be omitted or empty; unknown entries are refused rather
    than ignored. Geometry/region feasibility is checked by the translation audit.
    """
    selected = _uuids(selected, maximum=16)
    tree = c.read_board(source_bytes)
    observation = _observe(source_bytes, scope)
    by_id = {row['uuid']: row for row in observation['footprints']}
    if not set(selected) <= set(by_id):
        raise ValueError('Selected stable UUID absent from source')
    selected_rows = []
    names = set()
    for identity in selected:
        row = by_id[identity]
        if row['locked'] or row.get('placement_eligible', True) is not True:
            raise ValueError('Selected footprint is locked or ineligible: ' + row['reference'])
        if not row['pads'] or any(not pad['net'] for pad in row['pads']):
            raise ValueError('Every selected footprint pad needs an exact named net')
        incident = sorted({pad['net'] for pad in row['pads']})
        rs.validate_names(incident)
        names.update(incident)
        selected_rows.append(dict(uuid=identity, reference=row['reference'], incident_names=incident,
            pads=[dict(uuid=pad['uuid'], number=pad['number'], net_name=pad['net']) for pad in row['pads']]))
    names = rs.validate_names(sorted(names))
    protected_names = [] if protected_names is None else protected_names
    if type(protected_names) is not list:
        raise ValueError('Explicit protected native net-name list required')
    protected_names = rs.validate_names(protected_names) if protected_names else []
    protected_route_ids = _uuids([] if protected_route_ids is None else protected_route_ids,
                                maximum=64, empty=True)
    mapping = rs._net_mapping(tree)
    if not set(protected_names) <= mapping[2]:
        raise ValueError('Protected net name absent from source')
    if c.fixed_context_scope(observation['scope']):
        _, resolve = board_floor.source_net_identity(tree)
        protected_pours = {resolve(sx.one(zone, 'net')) for zone in sx.children(tree, 'zone')} & set(protected_names)
        if protected_pours:
            raise ValueError('Protected net copper-zone fill cannot be guaranteed by this placement scope: '
                             + ', '.join(sorted(protected_pours)))
    routes = rs._route_map(tree)
    if not {uuid.UUID(value).hex for value in protected_route_ids} <= set(routes):
        raise ValueError('Protected route UUID absent from source')
    if set(names) & set(protected_names):
        raise ValueError('Selected footprint touches an explicitly protected net')
    removed, protected = [], []
    for route in routes.values():
        record = _record(route, mapping)
        if record['net_name'] in names:
            if record['locked'] or record['uuid'] in protected_route_ids:
                raise ValueError('Incident copper is locked or explicitly protected: ' + record['uuid'])
            removed.append(record)
        else:
            protected.append(record)
    binding = rs.bind(source_bytes, names)
    task_bytes = (sx.dump(rs.task(tree, names)) + '\n').encode()
    if binding['task_sha256'] != _sha(task_bytes) or binding['protected_count'] != len(protected):
        raise ValueError('Affected-copper partition differs from shared selected-net binding')
    record = dict(schema=1, kind=KIND, policy=POLICY, source_sha256=_sha(source_bytes),
        source_scope=observation['scope'], selected=selected, selected_components=selected_rows,
        incident_names=names, protected_names=list(protected_names), protected_route_ids=protected_route_ids,
        original_route_count=len(routes), removed_routes=removed, protected_routes=protected,
        routing_scope_binding=binding, task_sha256=_sha(task_bytes),
        approval_granted=False, execution_authorized=False, routing_accepted=False,
        native_validation_performed=False)
    record['plan_sha256'] = _sha(_encoded(record))
    return record


def _checked_plan(source_bytes, plan):
    if type(plan) is not dict:
        raise ValueError('Explicit affected-copper plan required')
    captured = _encoded(plan)
    expected = propose(source_bytes, plan.get('selected'), protected_names=plan.get('protected_names'),
                       protected_route_ids=plan.get('protected_route_ids'), scope=plan.get('source_scope'))
    if captured != _encoded(expected):
        raise ValueError('Affected-copper plan/source changed; create a fresh plan')
    return expected


def _prepared(source_bytes, plan):
    checked = _checked_plan(source_bytes, plan)
    task = rs.task(c.read_board(source_bytes), checked['incident_names'])
    data = (sx.dump(task) + '\n').encode()
    if _sha(data) != checked['task_sha256']:
        raise ValueError('Prepared affected-copper task differs from plan')
    return data, checked


def prepare(source_bytes, plan):
    """Return a separate exact selected-net task; original bytes are untouched.

    This function grants no execution or user-approval authority. A caller must
    separately obtain any required approval before writing or using these bytes.
    """
    return _prepared(source_bytes, plan)[0]


def _pose(source_bytes, plan, moves, *, scope, region_nm):
    prepared, checked = _prepared(source_bytes, plan)
    if any(c.fixed_context_scope(value) for value in (scope, checked['source_scope'])) and scope != checked['source_scope']:
        raise ValueError('Placement scope differs from the exact reviewed copper plan')
    options = c.scope_options(scope=scope, selected=checked['selected'], region_nm=region_nm)
    c.validate_moves(c.inspect_board(prepared, scope=scope), moves, **options)
    return prepared, c.translated_tree(prepared, moves, **options), options, checked


def _audit_record(source_bytes, candidate_bytes, plan, moves, options, stage):
    return dict(schema=1, policy=POLICY, stage=stage, audit_passed=True,
        source_sha256=_sha(source_bytes), candidate_sha256=_sha(candidate_bytes), plan_sha256=plan['plan_sha256'],
        placement_options=copy.deepcopy(options), moves_nm=copy.deepcopy(moves),
        approval_granted=False, execution_authorized=False, routing_accepted=False,
        native_validation_performed=False)


def audit_translation(source_bytes, candidate_bytes, plan, moves, *, scope, region_nm):
    """Check only planned copper removal, selected XY and derived zone refill."""
    moves = copy.deepcopy(moves)
    prepared, captured = _prepared(source_bytes, plan)
    if any(c.fixed_context_scope(value) for value in (scope, captured['source_scope'])) and scope != captured['source_scope']:
        raise ValueError('Placement scope differs from the exact reviewed copper plan')
    options = c.scope_options(scope=scope, selected=captured['selected'], region_nm=region_nm)
    checked = c.check_translation(prepared, candidate_bytes, moves, **options)
    return dict(_audit_record(source_bytes, candidate_bytes, captured, moves, options, 'translation'),
                translation=checked)


def audit_routed(source_bytes, candidate_bytes, plan, moves, *, scope, region_nm):
    """Check posed task through selected-net preservation; not DRC acceptance."""
    moves = copy.deepcopy(moves)
    _, posed, options, captured = _pose(source_bytes, plan, moves, scope=scope, region_nm=region_nm)
    checked = rs.audit(posed, c.read_board(candidate_bytes), captured['incident_names'])
    return dict(_audit_record(source_bytes, candidate_bytes, captured, moves, options, 'routed'),
                routing_scope=checked)
