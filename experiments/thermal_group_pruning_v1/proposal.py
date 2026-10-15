"""Pure experimental deletion proposal; NEVER a thermal/electrical certificate.

The caller must bind the retained real report/worker/project bytes, preserve its
prior costs, and freshly validate the final candidate against original rules.
Only exact route endpoints and an observed pad centre choose this proposal.
"""
import hashlib
import json
import re
from fractions import Fraction

from autorouter import (board_floor as g, floor_route as f, pipeline as p,
                        routing_scope as rs, sexpr as sx, strategy as s,
                        thermal_contact as contact, thermal_geometry as geom)

POLICY = 'native-thermal-endpoint-component-deletion-v1'
MAX_ELIGIBLE = 128
MAX_COORD_NM = 10**12


def _require(condition, reason):
    if not condition:
        raise p.Rejected('thermal group proposal: ' + reason)


def _nm(atom):
    _require(type(atom) is str and len(atom) <= 64 and re.fullmatch(
        r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?', atom), 'ordinary numeric coordinate required')
    exponent = re.split('[eE]', atom)
    _require(len(exponent) == 1 or abs(int(exponent[1])) <= 12, 'coordinate exponent exceeds bound')
    value = Fraction(atom) * 1_000_000
    _require(value.denominator == 1 and abs(value.numerator) <= MAX_COORD_NM, 'coordinate must be bounded integer nanometres')
    return value.numerator


def _point(value):
    _require(type(value) is list and len(value) == 2 and all(
        type(v) is int and abs(v) <= MAX_COORD_NM for v in value), 'bounded Native integer point required')
    return tuple(value)


def _hash(tree):
    raw = (sx.dump(tree) + '\n').encode()
    _require(len(raw) <= sx.MAX_BYTES, 'AST byte ceiling exceeded')
    return hashlib.sha256(raw).hexdigest()


def derive(original, warm, base, scene, finding):
    """Return (pruned AST, replayable proposal), without file/process access.

    Warm must be the exact canonically saved board observed by the Native scene.
    Project/report/worker raw hashes remain mandatory caller-side bindings.
    """
    try:
        return _derive(original, warm, base, scene, finding)
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        raise p.Rejected('thermal group proposal: malformed observation or AST: ' + str(exc)) from exc


def _derive(original, warm, base, scene, finding):
    for tree in (original, warm, base):
        _require(type(tree) is list and tree and tree[0] == 'kicad_pcb', 'PCB AST required')
    _require(p.immutable(warm) == p.immutable(original) == p.immutable(base), 'original geometry/rules changed')
    warm_hash, base_hash = _hash(warm), _hash(base)
    _require(type(scene) is dict and type(scene.get('schema')) is int and scene['schema'] == 1
             and scene.get('kind') == 'native thermal geometry observations only'
             and scene.get('native_version') == '10.0.0' and scene.get('mode') == contact.POLICY
             and scene.get('units') == 'integer nanometres unless explicitly named otherwise'
             and scene.get('status') == 'observations_complete' and type(scene.get('api_error_count')) is int
             and scene['api_error_count'] == 0 and scene.get('source_unchanged') is True
             and scene.get('board_saved') is False and scene.get('board_sha256') == warm_hash
             and all(scene.get(key) is False for key in ('refill_executed', 'drc_executed', 'solver_executed'))
             and type(scene.get('project_sha256')) is str
             and re.fullmatch('[0-9a-f]{64}', scene['project_sha256']), 'bound complete Native observation required')
    _require(f.canonical(scene.get('finding')) == f.canonical(finding), 'actual thermal finding differs')
    layer, _ = contact.report_layer(scene)
    _require(scene.get('reported_layer') == layer, 'reported layer differs')
    owners = geom.uuid_index(original, sx)
    pad_id, zone_id = scene['target_pad_uuid'], scene['zone_uuid']
    for identity in (pad_id, zone_id):
        rs._uuid(['uuid', json.dumps(identity)])
    _require(pad_id != zone_id and {item['uuid'] for item in finding['items']} == {pad_id, zone_id}, 'finding pad/zone identities differ')
    _require(len(owners.get(pad_id, [])) == len(owners.get(zone_id, [])) == 1, 'pad/zone identity ambiguous')
    pad, zone = owners[pad_id][0], owners[zone_id][0]
    _require(pad[0] == 'pad' and zone[0] == 'zone' and zone in sx.children(original, 'zone')
             and sx.one(zone, 'keepout') is None, 'typed original pad/copper zone required')
    footprint = [fp for fp in sx.children(original, 'footprint') if pad in sx.children(fp, 'pad')]
    _require(len(footprint) == 1, 'original footprint identity ambiguous')
    fp_id = sx.unquote(sx.one(footprint[0], 'uuid')[1])
    _, resolve = g.source_net_identity(original)
    name = resolve(sx.one(pad, 'net'))
    _require(name and name == resolve(sx.one(zone, 'net')) == scene['net_name'], 'original pad/zone/Native net differs')
    atom = sx.one(zone, 'net')[1]
    _require(atom in s.zone_net_ids(original) and type(scene.get('net_code')) is int and scene['net_code'] > 0, 'eligible original zone net required')
    if sx.children(original, 'net'):
        _require(str(scene['net_code']) == atom == sx.one(pad, 'net')[1], 'Native numeric net differs')
    zone_layers = sx.one(zone, 'layers')
    zone_layers = zone_layers[1:] if zone_layers is not None else [sx.one(zone, 'layer')[1]]
    zone_layers = [sx.unquote(value) for value in zone_layers]
    _require(len(set(zone_layers)) == len(zone_layers) and set(zone_layers) <= {'F.Cu', 'B.Cu'}
             and layer in zone_layers and scene.get('zone_copper_layers') == zone_layers, 'original/Native zone layers differ')
    pads = scene['pads']
    _require(type(pads) is list and 1 <= len(pads) <= 512 and all(type(row) is dict for row in pads), 'bounded Native pads required')
    _require(len({row['uuid'] for row in pads}) == len(pads), 'duplicate Native pad identity')
    observed = [row for row in pads if row['uuid'] == pad_id]
    _require(len(observed) == 1, 'Native target pad missing')
    observed = observed[0]
    _require(observed.get('footprint_uuid') == fp_id and observed.get('pad_number') == sx.unquote(pad[1])
             and observed.get('logical_terminal') == [fp_id, sx.unquote(pad[1])]
             and type(observed.get('net_code')) is int and observed['net_code'] == scene['net_code']
             and observed.get('net_name') == name, 'Native terminal identity/net differs')
    position = _point(observed['position_nm'])
    _require(_point(scene['target_position_nm']) == position, 'Native target centre differs')
    layers = [row for row in observed['layers'] if row.get('canonical') == layer]
    _require(len(layers) == 1 and layers[0].get('on_layer') is True and layers[0].get('flash_layer') is True, 'Native target not on reported layer')
    report_pos = next(item['pos'] for item in finding['items'] if item['uuid'] == pad_id)
    _require(all(type(report_pos[k]) in (int, float) for k in ('x', 'y'))
             and tuple(_nm(str(report_pos[k])) for k in ('x', 'y')) == position, 'report/Native centre differs')
    before = rs.audit(warm, base, [name])
    protected = rs.protected_routes(warm, [name])
    eligible = s.eligible_routes(base, {atom}, protected)
    _require(1 <= len(eligible) <= MAX_ELIGIBLE, 'eligible route count outside bound')
    endpoints = []
    fields = {'start', 'end', 'width', 'layer', 'net', 'uuid'}
    for route in eligible:
        _require(route[0] == 'segment' and len(route) == 7 and all(type(n) is list and n for n in route[1:])
                 and {n[0] for n in route[1:]} == fields, 'ordinary eligible segments only')
        values = {key: sx.one(route, key) for key in fields}
        _require(all(len(values[k]) == (3 if k in ('start', 'end') else 2) for k in fields), 'segment field arity differs')
        route_layer = sx.unquote(values['layer'][1])
        _require(route_layer in {'F.Cu', 'B.Cu'} and resolve(values['net']) == name and _nm(values['width'][1]) > 0, 'segment layer/net/width differs')
        points = [tuple(_nm(value) for value in values[k][1:]) for k in ('start', 'end')]
        _require(points[0] != points[1], 'zero-length eligible segment')
        endpoints.append({(name, route_layer, point) for point in points})
    remaining = set(range(len(eligible))); components = []
    while remaining:
        seed = min(remaining, key=lambda i: s.route_id(eligible[i]))
        group = {seed}; remaining.remove(seed); points = set(endpoints[seed])
        pending = True
        while pending:
            pending = False
            for index in sorted(remaining):
                if points & endpoints[index]:
                    group.add(index); remaining.remove(index); points.update(endpoints[index]); pending = True
        components.append((group, points))
    anchored = [group for group, points in components if (name, layer, position) in points]
    _require(len(anchored) == 1, 'exact unique anchored component required')
    kept = sorted(s.route_id(eligible[i]) for i in anchored[0])
    deleted = sorted(s.route_id(route) for route in eligible if s.route_id(route) not in kept)
    _require(deleted, 'no other eligible component to delete')
    result = s.delete_routes(base, deleted, {atom}, protected)
    after = rs.audit(warm, result, [name])
    _require(after['protected_routes'] == before['protected_routes'], 'protected copper changed')
    return result, {'policy': POLICY, 'kind': 'delete_nonthermal_endpoint_components', 'net': atom,
        'net_name': name, 'layer': layer, 'pad_uuid': pad_id, 'zone_uuid': zone_id, 'anchor_nm': list(position),
        'warm_ast_sha256': warm_hash, 'base_ast_sha256': base_hash, 'result_ast_sha256': _hash(result),
        'scene_canonical_sha256': hashlib.sha256(f.canonical(scene).encode()).hexdigest(),
        'kept_route_ids': kept, 'deleted_route_ids': deleted,
        'components': sorted([sorted(s.route_id(eligible[i]) for i in group) for group, _ in components]),
        'protected_audit_before': before, 'protected_audit_after': after,
        'native_validation_performed': False, 'routing_accepted': False, 'electrical_certificate': False}
