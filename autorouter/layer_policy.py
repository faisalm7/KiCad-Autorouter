"""New-route layer restriction; pure checks, not native acceptance.

The caller supplies captured regular-file bytes and trusted task choices. No
filesystem reads, settings mutation, or routing execution occur here.
"""
from __future__ import annotations

import hashlib
import json
import math
import re

MAX_BOARD_BYTES = 32 * 1024 * 1024
MAX_DSN_BYTES = 20 * 1024 * 1024
NAMES = ('F.Cu', 'B.Cu')
SCOPES = ('whole_board_unlocked_routing', 'partial_completion')
# Exact noncopper declarations observed in the qualified 20260206 owned fixture.
# Unknown IDs/names remain unsupported instead of inferring copper from a label.
NONCOPPER = dict(zip(
    '9 11 13 15 5 7 1 3 17 19 21 23 25 27 31 29 35 33 39 41 43 45'.split(),
    'F.Adhes B.Adhes F.Paste B.Paste F.SilkS B.SilkS F.Mask B.Mask Dwgs.User Cmts.User Eco1.User Eco2.User Edge.Cuts Margin F.CrtYd B.CrtYd F.Fab B.Fab User.1 User.2 User.3 User.4'.split()))
POLICY = 'new-route-layers-v1'


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _parse(raw, *, dsn=False):
    if type(raw) is not bytes or not 0 < len(raw) <= (MAX_DSN_BYTES if dsn else MAX_BOARD_BYTES):
        raise ValueError('bounded nonempty captured bytes required')
    from autorouter import sexpr as sx
    if dsn:
        from autorouter.adapter import _parse_dsn
        return _parse_dsn(raw.decode('utf-8'))
    return sx.parse(raw.decode('utf-8'))


def validate_request(allowed_names, *, scope, engine_profile, guidance_policy):
    """Validate explicit names only. The legacy source_all path does not call us."""
    if (type(allowed_names) is not list or not 1 <= len(allowed_names) <= 2
            or any(type(n) is not str or n not in NAMES for n in allowed_names)
            or len(set(allowed_names)) != len(allowed_names)):
        raise ValueError('explicit unique F.Cu/B.Cu layer list required')
    if type(scope) is not str or scope not in SCOPES:
        raise ValueError('unqualified layer restriction scope')
    if engine_profile != 'completion-only' or guidance_policy != 'native':
        raise ValueError('explicit layers require native completion-only routing')
    return list(allowed_names)


def _source_layers(tree):
    from autorouter import sexpr as sx
    # Only the format used in actual layer-mask initialization evidence so far.
    if not tree or tree[0] != 'kicad_pcb' or sx.one(tree, 'version') != ['version', '20260206']:
        raise ValueError('layer restriction requires qualified 20260206 format')
    return _two_copper_table(tree)


def _two_copper_table(tree, *, noncopper=NONCOPPER):
    """Shared literal table check; callers independently qualify the format.

    This does not broaden the layer-restriction policy above. The prospective
    hierarchy comparator has a separate explicit version census and no routing
    admission. Neither caller rewrites a source version to reuse this check.
    """
    from autorouter import sexpr as sx
    layers = sx.one(tree, 'layers')
    if layers is None:
        raise ValueError('missing source layer table')
    names, ids, copper = [], [], []
    for row in layers[1:]:
        if (type(row) is not list or len(row) not in (3, 4)
                or any(type(atom) is not str for atom in row)
                or not row[0].isdigit() or str(int(row[0])) != row[0]):
            raise ValueError('malformed source layer declaration')
        name = sx.unquote(row[1])
        if row[0] in ids or name in names:
            raise ValueError('duplicate source layer identity')
        ids.append(row[0]); names.append(name)
        if name.endswith('.Cu') or row[2] in {'signal', 'power', 'mixed', 'jumper'}:
            if row[2] != 'signal' or len(row) != 3:
                raise ValueError('unqualified copper layer type or alias')
            copper.append([row[0], name])
        elif noncopper.get(row[0]) != name or row[2] != 'user':
            raise ValueError('unqualified noncopper layer identity; cannot exclude hidden copper')
    if (copper != [['0', 'F.Cu'], ['2', 'B.Cu']]
            or [[row[0], sx.unquote(row[1])] for row in layers[1:3]] != copper):
        raise ValueError('requires exact two-layer physical F.Cu/B.Cu source order')
    setup = sx.one(tree, 'setup', [])
    stackup = sx.one(setup, 'stackup')
    if stackup is not None:
        found = []
        for row in sx.children(stackup, 'layer'):
            if len(row) < 2 or type(row[1]) is not str:
                raise ValueError('malformed stackup layer')
            name = sx.unquote(row[1]); kind = sx.one(row, 'type')
            if name.endswith('.Cu') or (kind and len(kind) == 2 and sx.unquote(kind[1]) == 'copper'):
                if kind != ['type', '"copper"'] and kind != ['type', 'copper']:
                    raise ValueError('unqualified stackup copper type')
                found.append(name)
        if found != list(NAMES):
            raise ValueError('stackup copper order differs from source layer table')
    return copper


def _dsn_layers(tree):
    from autorouter import sexpr as sx
    structure = sx.one(tree, 'structure')
    if structure is None:
        raise ValueError('missing DSN structure')
    rows = sx.children(structure, 'layer')
    if len(rows) != 2:
        raise ValueError('requires exactly two exported DSN layers')
    result = []
    for i, row in enumerate(rows):
        if (len(row) != 4 or type(row[1]) is not str
                or sx.one(row, 'type') != ['type', 'signal']
                or sx.one(row, 'property') != ['property', ['index', str(i)]]):
            raise ValueError('unqualified DSN signal layer/index declaration')
        result.append(sx.unquote(row[1]))
    if result != list(NAMES):
        raise ValueError('DSN signal order differs from source physical order')
    return result


def bind(source_bytes, exported_dsn_bytes, engine_dsn_bytes, allowed_names, *,
         scope, engine_profile, guidance_policy):
    """Reparse all bytes; bind original physical order and both actual DSNs."""
    allowed = validate_request(allowed_names, scope=scope, engine_profile=engine_profile,
                               guidance_policy=guidance_policy)
    copper = _source_layers(_parse(source_bytes))
    exported = _dsn_layers(_parse(exported_dsn_bytes, dsn=True))
    engine = _dsn_layers(_parse(engine_dsn_bytes, dsn=True))
    mask = [name in allowed for name in engine]
    return {'schema': 1, 'policy': POLICY, 'scope': scope, 'engine_profile': engine_profile,
            'guidance_policy': guidance_policy, 'requested_names': allowed,
            'source_copper_layers': copper, 'exported_signal_layers': exported,
            'engine_signal_layers': engine, 'routable': mask,
            'engine_argument': '--router.layers.routable=' + ','.join(str(v).lower() for v in mask),
            'source_sha256': _sha(source_bytes), 'native_dsn_sha256': _sha(exported_dsn_bytes),
            'task_dsn_sha256': _sha(engine_dsn_bytes)}


def _route_id(route):
    from autorouter import sexpr as sx
    node = sx.one(route, 'uuid')
    if node is None or len(node) != 2 or type(node[1]) is not str or not sx.unquote(node[1]):
        raise ValueError('route needs a unique nonempty UUID')
    return sx.unquote(node[1])


def _route_grammar(route):
    """Known field shapes only; native checks still decide geometric legality."""
    from autorouter import sexpr as sx
    required = {
        'segment': {'start': 2, 'end': 2, 'width': 1, 'layer': 1, 'net': 1, 'uuid': 1},
        'arc': {'start': 2, 'mid': 2, 'end': 2, 'width': 1, 'layer': 1, 'net': 1, 'uuid': 1},
        'via': {'at': 2, 'size': 1, 'drill': 1, 'layers': 2, 'net': 1, 'uuid': 1},
    }.get(route[0])
    if required is None:
        raise ValueError('unqualified route kind')
    fields, bare_lock = {}, False
    for field in route[1:]:
        if field == 'locked' and not bare_lock and 'locked' not in fields:
            bare_lock = True
            continue
        if (type(field) is not list or not field or type(field[0]) is not str
                or field[0] in fields or field[0] not in set(required) | {'locked'}):
            raise ValueError('unknown, duplicate or malformed route field')
        key = field[0]
        if key == 'locked':
            if bare_lock or field not in (['locked'], ['locked', 'yes']):
                raise ValueError('ambiguous route lock field')
        elif len(field) != required[key] + 1 or any(type(atom) is not str for atom in field[1:]):
            raise ValueError('malformed route field arity: ' + key)
        fields[key] = field
    if not set(required) <= set(fields):
        raise ValueError('missing required route field')
    for key in ('net', 'uuid'):
        if not sx.unquote(fields[key][1]):
            raise ValueError('empty route identity: ' + key)
    # Bound atom parsing, finite coordinates and positive dimensions; no distance,
    # annulus, arc geometry, clearance or native connectivity is inferred here.
    for key in set(fields) & {'start', 'mid', 'end', 'at', 'width', 'size', 'drill'}:
        for atom in fields[key][1:]:
            if (len(atom) > 64 or re.fullmatch(r'[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][-+]?[0-9]+)?', atom) is None
                    or not math.isfinite(float(atom))
                    or (key in {'width', 'size', 'drill'} and float(atom) <= 0)):
                raise ValueError('invalid numeric route atom: ' + key)


def _route_layers(route):
    from autorouter import sexpr as sx
    _route_grammar(route)
    if route[0] in {'segment', 'arc'}:
        layer = sx.one(route, 'layer')
        if (layer is None or len(layer) != 2 or type(layer[1]) is not str
                or sx.one(route, 'layers') is not None or sx.unquote(layer[1]) not in NAMES):
            raise ValueError('unqualified segment/arc copper layer')
        return [sx.unquote(layer[1])]
    layers = sx.one(route, 'layers')
    if (route[0] != 'via' or any(type(atom) is str and atom != 'locked' for atom in route[1:])
            or sx.one(route, 'layer') is not None or layers is None or len(layers) != 3
            or any(type(n) is not str for n in layers[1:])
            or [sx.unquote(n) for n in layers[1:]] != list(NAMES)
            or any(sx.one(route, key) is not None for key in ('type', 'blind', 'micro'))):
        raise ValueError('only ordinary through-via F.Cu/B.Cu span qualified')
    return list(NAMES)


def _route_map(tree):
    from autorouter.pipeline import routes
    result = {}
    for route in routes(tree):
        _route_layers(route)
        uid = _route_id(route)
        if uid in result:
            raise ValueError('duplicate route UUID')
        result[uid] = route
    return result


def audit_candidate(source_bytes, candidate_bytes, exported_dsn_bytes, engine_dsn_bytes,
                    binding, *, allowed_names, scope, engine_profile, guidance_policy):
    """Audit layer scope only; this never authorizes acceptance or native claims.

    Expected choices must come from captured preferences/task configuration,
    not from the untrusted binding being checked. Protected exemptions are
    derived from original routing and scope, never from a supplied UUID list.
    """
    from autorouter import sexpr as sx
    from autorouter.pipeline import immutable, locked
    expected = bind(source_bytes, exported_dsn_bytes, engine_dsn_bytes, allowed_names,
                    scope=scope, engine_profile=engine_profile, guidance_policy=guidance_policy)
    if type(binding) is not dict or _canonical(binding) != _canonical(expected):
        raise ValueError('layer binding differs from original bytes or task choices')
    original, candidate = _parse(source_bytes), _parse(candidate_bytes)
    if immutable(candidate) != immutable(original):
        raise ValueError('immutable source geometry or layers changed')
    _source_layers(candidate)
    before, after = _route_map(original), _route_map(candidate)
    protected = {}
    for uid, route in before.items():
        lock = sx.one(route, 'locked')
        if lock not in (None, ['locked'], ['locked', 'yes']) or route.count('locked') > 1 or ('locked' in route and lock is not None):
            raise ValueError('ambiguous original route protection')
        if scope == 'partial_completion' or locked(route):
            protected[uid] = route
    for uid, route in protected.items():
        if after.get(uid) != route:
            raise ValueError('protected original route changed or missing')
    generated, exemptions = [], []
    for uid, route in after.items():
        names = _route_layers(route)
        row = {'uuid': uid, 'kind': route[0], 'layers': names}
        if uid in protected:
            row['outside_allowed_names'] = [name for name in names if name not in allowed_names]
            row['reason'] = 'exact protected original route'
            exemptions.append(row)
        else:
            if any(name not in allowed_names for name in names):
                raise ValueError('new route uses disallowed copper layer: ' + uid)
            generated.append(row)
    return {'schema': 1, 'policy': POLICY, 'layer_scope_passed': True,
            'routing_accepted': False, 'native_validation_performed': False,
            'binding_sha256': _sha(_canonical(expected)), 'candidate_sha256': _sha(candidate_bytes),
            'new_routes': generated, 'protected_exemptions': exemptions}
