"""Pure selected-net task and preservation checks; never routing acceptance.

Names are exact native identities. Source bytes, not normalized serialization,
bind a request. Native DRC, original rules and final candidate checks remain the
caller's responsibility. No files, engines or settings are accessed here.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid

from . import pipeline as p, sexpr as sx

POLICY = 'selected-nets-v1'
MAX_NAMES = 64
MAX_NAME_BYTES = 1024


def validate_names(names):
    """Return a fresh ordered list; do not trim, rename or case-fold nets."""
    if (type(names) is not list or not 1 <= len(names) <= MAX_NAMES
            or any(type(name) is not str or not name.strip() or name == '0'
                   or len(name.encode('utf-8')) > MAX_NAME_BYTES
                   or any(ord(char) < 32 or ord(char) == 127 for char in name)
                   for name in names)
            or len(set(names)) != len(names)):
        raise ValueError('explicit unique nonempty native net names required (max64)')
    return list(names)


def _board(tree):
    if type(tree) is not list or not tree or tree[0] != 'kicad_pcb':
        raise p.Rejected('selected scope requires a PCB AST')


def _one(node, key):
    try:
        return sx.one(node, key)
    except ValueError as exc:
        raise p.Rejected('ambiguous selected-scope field: ' + key) from exc


def _name(atom):
    if type(atom) is not str or (atom.startswith('"') and not atom.endswith('"')):
        raise p.Rejected('malformed native net atom')
    name = sx.unquote(atom)
    if (len(name.encode('utf-8')) > MAX_NAME_BYTES
            or any(ord(char) < 32 or ord(char) == 127 for char in name)):
        raise p.Rejected('malformed native net name')
    return name


def _net_mapping(tree):
    _board(tree)
    table = sx.children(tree, 'net')
    codes, names = {}, set()
    if table:
        for row in table:
            if (len(row) != 3 or type(row[1]) is not str
                    or re.fullmatch(r'0|[1-9][0-9]*', row[1]) is None
                    or row[1] in codes):
                raise p.Rejected('ambiguous legacy net table')
            name = _name(row[2])
            if row[1] == '0':
                if name:
                    raise p.Rejected('legacy net0 must be unnamed')
            elif not name.strip() or name in names:
                raise p.Rejected('ambiguous legacy net name')
            if name:
                names.add(name)
            codes[row[1]] = name or None
        # A terminal's legacy name must agree with its declared native code.
        for fp in sx.children(tree, 'footprint'):
            for pad in sx.children(fp, 'pad'):
                row = _one(pad, 'net')
                if row is not None and (len(row) != 3 or type(row[1]) is not str or row[1] not in codes
                                        or _name(row[2]) != (codes[row[1]] or '')):
                    raise p.Rejected('terminal differs from legacy net table')
        return 'legacy_table', codes, names
    # Modern formats carry names on terminals/routes, without a numeric table.
    nodes = [*p.routes(tree), *(pad for fp in sx.children(tree, 'footprint')
                              for pad in sx.children(fp, 'pad'))]
    for node in nodes:
        row = _one(node, 'net')
        if row is None:
            continue
        if len(row) != 2:
            raise p.Rejected('ambiguous modern net identity')
        name = _name(row[1])
        if name.strip() and name != '0':
            names.add(name)
    return 'modern_names', {}, names


def _net_name(route, mapping):
    mode, codes, _ = mapping
    row = _one(route, 'net')
    if row is None:
        return None
    if len(row) != 2 or type(row[1]) is not str:
        raise p.Rejected('ambiguous route net identity')
    if mode == 'legacy_table':
        # Unknown or net0 routing is protected, never assigned by guessing.
        return codes.get(row[1])
    name = _name(row[1])
    return name if name.strip() and name != '0' else None


def _locked(route):
    row = _one(route, 'locked')
    count = route.count('locked')
    if (count > 1 or (count and row is not None)
            or row not in (None, ['locked'], ['locked', 'yes'])):
        raise p.Rejected('ambiguous original route lock')
    return p.locked(route)


def _uuid(row):
    if row is None or len(row) != 2 or type(row[1]) is not str:
        raise p.Rejected('route requires a valid unique UUID')
    raw = sx.unquote(row[1])
    try:
        parsed = uuid.UUID(raw)
    except (ValueError, AttributeError) as exc:
        raise p.Rejected('route requires a valid unique UUID') from exc
    if parsed.int == 0 or str(parsed) != raw.lower():
        raise p.Rejected('route requires a canonical nonzero UUID')
    return parsed.hex, raw


def _immutable_uuid_ids(tree):
    result = set()
    def walk(node):
        if type(node) is list:
            if node and node[0] == 'uuid':
                identity, _ = _uuid(node)
                result.add(identity)
            for child in node:
                walk(child)
    walk(p.immutable(tree))
    return result


def _route_map(tree):
    result = {}
    immutable_ids = _immutable_uuid_ids(tree)
    for route in p.routes(tree):
        identity, _ = _uuid(_one(route, 'uuid'))
        if identity in result or identity in immutable_ids:
            raise p.Rejected('route UUID duplicated or collides with immutable geometry')
        _locked(route)
        result[identity] = route
    return result


def _context(tree, names):
    selected = validate_names(names)
    mapping = _net_mapping(tree)
    if not set(selected) <= mapping[2]:
        raise p.Rejected('selected net is unknown in original native identities')
    routes = _route_map(tree)
    protected = {identity: route for identity, route in routes.items()
                 if _net_name(route, mapping) not in selected or _locked(route)}
    return selected, mapping, routes, protected


def protected_routes(tree, names):
    """Capture every nonselected/unnamed route and locked selected route."""
    _, _, _, protected = _context(tree, names)
    return copy.deepcopy(list(protected.values()))


def task(tree, names):
    """Remove only selected unlocked routes and derived zone fill."""
    _, _, _, protected = _context(tree, names)
    result = copy.deepcopy(tree)
    result[:] = [node for node in result if not (
        type(node) is list and node and node[0] in p.ROUTES
        and _uuid(_one(node, 'uuid'))[0] not in protected)]
    for zone in sx.children(result, 'zone'):
        zone[:] = [node for node in zone if not (
            type(node) is list and node and node[0] in p.DERIVED_ZONE)]
    if p.immutable(result) != p.immutable(tree):
        raise p.Rejected('selected task changed immutable original geometry')
    return result


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _protected_records(mapping, protected):
    return [{'uuid': _uuid(_one(route, 'uuid'))[1], 'kind': route[0],
             'net_name': _net_name(route, mapping), 'locked': _locked(route),
             'record_sha256': _sha(sx.dump(route).encode())}
            for route in protected.values()]


def bind(source_bytes, names):
    """Bind exact captured source bytes and the exact ordered net selection."""
    if type(source_bytes) is not bytes or not 0 < len(source_bytes) <= sx.MAX_BYTES:
        raise ValueError('bounded nonempty original PCB bytes required')
    original = sx.parse(source_bytes.decode('utf-8'))
    selected, mapping, routes, protected = _context(original, names)
    record = {'schema': 1, 'policy': POLICY, 'requested_names': selected,
              'source_sha256': _sha(source_bytes), 'source_net_mapping': mapping[0],
              'task_sha256': _sha((sx.dump(task(original,selected))+'\n').encode()),
              'original_route_count': len(routes), 'protected_count': len(protected),
              'protected_routes': _protected_records(mapping, protected)}
    record['binding_sha256'] = _sha(json.dumps(record, sort_keys=True,
        separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode())
    return record


def audit(original, candidate, names):
    """Check selected scope; success establishes no native/routing acceptance."""
    selected, mapping, _, protected = _context(original, names)
    _board(candidate)
    if p.immutable(candidate) != p.immutable(original):
        raise p.Rejected('selected scope changed immutable original geometry')
    after = _route_map(candidate)
    for identity, route in protected.items():
        if after.get(identity) != route:
            raise p.Rejected('protected route missing or full record changed')
    generated = []
    for identity, route in after.items():
        if identity in protected:
            continue
        name = _net_name(route, mapping)
        if name is None or name not in selected:
            raise p.Rejected('new or changed route uses nonselected or unknown net')
        if _locked(route):
            raise p.Rejected('selected scope added a route lock')
        generated.append({'uuid': _uuid(_one(route, 'uuid'))[1],
                          'kind': route[0], 'net_name': name})
    return {'schema': 1, 'policy': POLICY, 'scope_passed': True,
            'routing_accepted': False, 'native_validation_performed': False,
            'requested_names': selected, 'protected_count': len(protected),
            'protected_routes': _protected_records(mapping, protected),
            'selected_route_count': len(generated), 'selected_routes': generated}
