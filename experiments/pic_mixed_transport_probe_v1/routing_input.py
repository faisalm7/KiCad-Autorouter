"""Finite, reversible removal of retained PIC routing; no solver or acceptance.

The caller must freeze the source/project and native observation provenance. Hashes
here provide mutable-evidence consistency, not authentication or fresh validation.
Only the already observed 339 path wires / six vias are removed. Native original
coordinates are never rewritten to compensate for known DSN quantization.
"""
import copy
import json
from collections import Counter

from autorouter import pipeline as p, sexpr as sx
from autorouter.adapter import _check_units, _dump_dsn, _parse_dsn
from experiments.custom_pad_area_probe_v1.derive import exact_one
from experiments.pic_mixed_transport_probe_v1 import ses_checks as c, transport

MAX_INPUT = 1024 * 1024
MAX_FACTS = 4 * 1024 * 1024
LAYERS = ['top_layer', 'bottom_layer']


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _raw(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_INPUT:
        raise ValueError('bounded nonempty input bytes required')
    return raw.decode('utf-8')


def _field(node, key, size):
    child = exact_one(node, key)
    if len(child) != size or any(type(x) is not str for x in child):
        raise ValueError('malformed ' + key)
    return child[1:]


def _nm(atom):
    value = c.number(atom) * 1000000
    if value != value.to_integral_value():
        raise ValueError('native integer nanometres required')
    return int(value)


def _native(native_raw, context, expected):
    board = sx.parse(_raw(native_raw))
    if (board[0] != 'kicad_pcb' or context.get('context_schema') != 1
            or type(context.get('context_schema')) is not int
            or context.get('native_version') != '10.0.0'
            or context.get('units') != 'integer nanometres' or context.get('mode') != 'export'
            or context.get('board_saved') is not False
            or context.get('board_sha256') != transport.sha(native_raw)
            or context.get('dsn_sha256') != expected['source_dsn_sha256']
            or context.get('input_hashes_before') != context.get('input_hashes_after')
            or not context.get('input_hashes_before')):
        raise ValueError('native source/context binding differs')
    routes = p.routes(board)
    if Counter(r[0] for r in routes) != {'segment': 370, 'via': 6} or len(sx.children(board, 'zone')) != 1:
        raise ValueError('finite native route/zone population differs')
    names = [n['name'] for n in context['nets']]
    if len(names) != 111 or len(set(names)) != 111 or set(names) != set(expected['nets']):
        raise ValueError('native net population differs')
    rows = []
    for route in routes:
        if p.locked(route) or 'locked' in route or sx.children(route, 'locked'):
            raise ValueError('protected or unqualified locked native routing')
        keys = ({'start', 'end', 'width', 'layer', 'net', 'uuid'} if route[0] == 'segment'
                else {'at', 'size', 'drill', 'layers', 'capping', 'covering', 'plugging', 'filling', 'net', 'uuid'})
        c.children_only(route, keys, 1)
        if len(route) != len(keys) + 1 or {n[0] for n in route[1:]} != keys:
            raise ValueError('native route grammar differs')
        row = {'uuid': sx.unquote(_field(route, 'uuid', 2)[0]),
               'net': sx.unquote(_field(route, 'net', 2)[0]), 'kind': route[0]}
        if not row['uuid'] or row['net'] not in names:
            raise ValueError('native route identity differs')
        if route[0] == 'segment':
            row.update(width_nm=_nm(_field(route, 'width', 2)[0]),
                       start_nm=list(map(_nm, _field(route, 'start', 3))),
                       end_nm=list(map(_nm, _field(route, 'end', 3))),
                       layer=sx.unquote(_field(route, 'layer', 2)[0]))
            if row['layer'] not in ('F.Cu', 'B.Cu') or row['start_nm'] == row['end_nm']:
                raise ValueError('native segment layer/geometry differs')
        else:
            for key in ('capping', 'filling'):
                if sx.one(route, key) != [key, 'no']: raise ValueError('unqualified native via treatment')
            for key in ('covering', 'plugging'):
                if sx.one(route, key) != [key, ['front', 'no'], ['back', 'no']]:
                    raise ValueError('unqualified native via treatment')
            layers = list(map(sx.unquote, _field(route, 'layers', 3)))
            row.update(width_nm=_nm(_field(route, 'size', 2)[0]),
                       position_nm=list(map(_nm, _field(route, 'at', 3))),
                       drill_nm=_nm(_field(route, 'drill', 2)[0]), via_type=4, layers=layers)
            if layers != ['F.Cu', 'B.Cu'] or not 0 < row['drill_nm'] < row['width_nm']:
                raise ValueError('ordinary through-via required')
        if row['width_nm'] <= 0: raise ValueError('positive native route width required')
        rows.append(row)
    if len({r['uuid'] for r in rows}) != 376 or canonical(sorted(rows, key=lambda r:r['uuid'])) != canonical(sorted(context['routes'], key=lambda r:r['uuid'])):
        raise ValueError('exact native route observation differs')
    return {'segments': 370, 'vias': 6, 'locked': 0, 'zones': 1}


def derive(mixed_raw, expected, native_raw, context):
    """Return (new DSN bytes, reversible receipt); never mutate caller inputs."""
    text = _raw(mixed_raw)
    if any(len(canonical(x).encode()) > MAX_FACTS for x in (expected, context)):
        raise ValueError('native/expected facts bound')
    if (type(expected.get('schema')) is not int or expected['schema'] != 1
            or expected.get('derived_dsn_sha256') != transport.sha(mixed_raw)
            or expected.get('layer_order') != LAYERS
            or expected.get('unchanged_original_wire_count') != 339
            or expected.get('unchanged_original_via_count') != 6
            or expected.get('unchanged_original_plane_count') != 1):
        raise ValueError('mixed derivation identity/census differs')
    if any(type(expected[key]) is not int for key in ('unchanged_original_wire_count', 'unchanged_original_via_count', 'unchanged_original_plane_count')):
        raise ValueError('typed mixed population required')
    native = _native(native_raw, context, expected)
    original = _parse_dsn(text)
    _check_units(original)
    if original[0] != 'pcb' or sx.one(original, 'resolution') != ['resolution', 'um', '10']:
        raise ValueError('finite DSN root/resolution differs')
    tree = copy.deepcopy(original)
    wiring = exact_one(tree, 'wiring'); structure = exact_one(tree, 'structure')
    network = exact_one(tree, 'network'); library = exact_one(tree, 'library')
    if [sx.unquote(n[1]) for n in sx.children(structure, 'layer')] != LAYERS or len(sx.children(structure, 'plane')) != 1:
        raise ValueError('original layer/plane population differs')
    net_names = [sx.unquote(n[1]) for n in sx.children(network, 'net')]
    if len(net_names) != 111 or len(set(net_names)) != 111 or set(net_names) != set(expected['nets']):
        raise ValueError('DSN net population differs')
    pins = transport.placed_pins(tree)
    if len(pins) != 240 or sum(bool(n['nets']) for n in pins) != 236 or canonical(pins) != canonical(expected['dsn_pins']):
        raise ValueError('complete placed DSN terminal mapping differs')
    stacks = {sx.unquote(s[1]): s for s in sx.children(library, 'padstack')}
    if len(stacks) != len(sx.children(library, 'padstack')): raise ValueError('duplicate padstack')
    areas = expected['areas']
    if len(areas) != 2 or len({a['uuid'] for a in areas}) != 2: raise ValueError('two distinct native bodies required')
    bodies = [['wire', ['polygon', a['layer'], '0', *[str(v) for point in a['ring_um'] for v in point]],
               ['net', json.dumps(a['net'])], ['type', 'protect']] for a in areas]
    kept = []; ledger = []; counts = Counter()
    for index, node in enumerate(wiring[1:], 1):
        if not isinstance(node, list) or not node: raise ValueError('unknown wiring member')
        if node[0] == 'wire':
            if sx.children(node, 'polygon'):
                if node not in bodies or node in kept: raise ValueError('unbound/duplicate protected body')
                kept.append(node); continue
            c.children_only(node, {'path', 'net', 'type'}, 1)
            if len(node) != 4: raise ValueError('route path grammar differs')
            path = exact_one(node, 'path')
            if len(path) < 7 or any(type(x) is not str for x in path): raise ValueError('route path grammar differs')
            net = sx.unquote(_field(node, 'net', 2)[0])
            if net not in net_names: raise ValueError('unknown path net')
            c.segments(net, sx.unquote(path[1]), c.number(path[2]), c.pairs(path[3:]))
            kind = 'path_wire'
        elif node[0] == 'via':
            c.children_only(node, {'net', 'type'}, 4)
            if len(node) != 6 or any(type(x) is not str for x in node[:4]): raise ValueError('route via grammar differs')
            name = sx.unquote(node[1]); net = sx.unquote(_field(node, 'net', 2)[0])
            if name not in stacks or net not in net_names: raise ValueError('unknown via padstack/net')
            c.number(node[2]); c.number(node[3])
            shape_map = c.library(['library', stacks[name]], 1)  # Circular two-layer stack, unchanged.
            if any(diameter <= 0 or center != (0, 0) for shapes in shape_map.values() for diameter, center in shapes.values()):
                raise ValueError('positive centered via stack required')
            kind = 'via'
        else: raise ValueError('unqualified ordinary wiring member')
        if _field(node, 'type', 2) != ['route']: raise ValueError('protected/fixed ordinary DSN route')
        ledger.append({'index': index, 'kind': kind, 'node': copy.deepcopy(node)})
        counts[kind] += 1
    if counts != {'path_wire': 339, 'via': 6} or kept != bodies:
        raise ValueError('finite removable/protected DSN population differs')
    wiring[1:] = kept
    result = _dump_dsn(tree).encode()
    if len(result) > MAX_INPUT or _parse_dsn(result.decode()) != tree: raise ValueError('unrouted DSN roundtrip differs')
    receipt = {'schema': 1, 'mode': 'pic_fully_unrouted_v1',
               'mixed_dsn_sha256': transport.sha(mixed_raw), 'unrouted_dsn_sha256': transport.sha(result),
               'native_board_sha256': transport.sha(native_raw),
               'expected_sha256': transport.sha(canonical(expected).encode()),
               'native_context_sha256': transport.sha(canonical(context).encode()),
               'original_ast_sha256': transport.sha(canonical(original).encode()),
               'native_routes': native, 'removed': dict(counts), 'ledger': ledger,
               'preserved_protected_bodies': 2, 'preserved_planes': 1,
               'remaining_ordinary_routes': 0, 'routing_executed': False, 'routing_accepted': False}
    if restore(result, receipt) != original: raise ValueError('reverse removal changed original AST')
    return result, receipt


def restore(unrouted_raw, receipt):
    """Reconstruct AST for comparison; receipt is not a trusted original source."""
    text = _raw(unrouted_raw)
    if len(canonical(receipt).encode()) > MAX_FACTS: raise ValueError('removal receipt bound')
    if (type(receipt.get('schema')) is not int or receipt['schema'] != 1
            or receipt.get('mode') != 'pic_fully_unrouted_v1'
            or receipt.get('unrouted_dsn_sha256') != transport.sha(unrouted_raw)):
        raise ValueError('unrouted receipt identity differs')
    tree = _parse_dsn(text); wiring = exact_one(tree, 'wiring')
    ledger = receipt['ledger']
    if type(ledger) is not list or len(ledger) != 345: raise ValueError('removal ledger population differs')
    last = 0
    for entry in ledger:
        index = entry['index']
        if type(index) is not int or not last < index <= len(wiring): raise ValueError('removal ledger order/index differs')
        if entry['kind'] not in ('path_wire', 'via') or not isinstance(entry['node'], list): raise ValueError('removal ledger entry differs')
        wiring.insert(index, copy.deepcopy(entry['node'])); last = index
    if transport.sha(canonical(tree).encode()) != receipt['original_ast_sha256']:
        raise ValueError('reconstructed original AST differs')
    return tree


def verify(mixed_raw, expected, native_raw, context, unrouted_raw, receipt):
    """Re-derive all obligations from captured inputs; caller owns fresh provenance."""
    derived, wanted = derive(mixed_raw, expected, native_raw, context)
    if derived != unrouted_raw or canonical(wanted) != canonical(receipt):
        raise ValueError('unrouted derivation/receipt differs')
    return True
