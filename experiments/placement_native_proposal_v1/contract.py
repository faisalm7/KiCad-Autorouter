"""Pure source/observation/translation checks for one narrow Native probe.

Integer nanometres are authoritative. Only unrotated front footprints with one
symmetric rectangular courtyard and zero/one centred circular PTH pad qualify.
The complete source AST remains authoritative outside selected XY coordinates
and the existing explicitly derived top-level zone fill projection.
"""
import copy
from decimal import Decimal
import hashlib
import uuid

from autorouter import sexpr as sx, pipeline as p, board_floor as g
from autorouter import placement_transform as pt, routing_scope as rs
from experiments.constrained_placement_v1 import constraints as constraints

SELECTED = ('953eb9d9-83f3-5938-a1a1-ab40cf790dcb', 'f4913284-f8a5-5128-b764-06e77958c4a1')
REGION_NM = (7_000_000, 7_000_000, 31_000_000, 13_000_000)
MAX_BYTES = 1024 * 1024
APPLICATION_POLICIES = ('native-save-v1', 'source-translation-v1')
DEFAULT_SCOPE = 'single-pad-unrouted-v1'
MULTIPAD_SCOPE = 'multipad-preserve-v1'
ROUTE_GAP_NM = 300_000


def application_policy(value='native-save-v1'):
    need(type(value) is str and value in APPLICATION_POLICIES, 'Explicit supported application policy required')
    return value


def need(test, message):
    if not test:
        raise ValueError(message)


def scope_options(*, scope=DEFAULT_SCOPE, selected=None, region_nm=None):
    need(type(scope) is str and scope in (DEFAULT_SCOPE, MULTIPAD_SCOPE), 'Unsupported placement scope')
    if scope == DEFAULT_SCOPE:
        selected = SELECTED if selected is None else selected
        region_nm = REGION_NM if region_nm is None else region_nm
    need(type(selected) in (list, tuple) and 1 <= len(selected) <= 16, 'Explicit bounded selected UUIDs required')
    need(all(type(value) is str and str(uuid.UUID(value)) == value for value in selected)
         and len(set(selected)) == len(selected), 'Unique canonical selected UUIDs required')
    need(type(region_nm) in (list, tuple) and len(region_nm) == 4
         and all(type(value) is int and abs(value) <= 2_000_000_000 for value in region_nm)
         and region_nm[0] < region_nm[2] and region_nm[1] < region_nm[3], 'Explicit integer-nm rectangle required')
    return dict(scope=scope, selected=list(selected), region_nm=list(region_nm))


def atom(node, name):
    row = sx.one(node, name)
    need(row is not None and len(row) == 2, 'Exact ' + name + ' required')
    return sx.unquote(row[1])


def uid(node):
    value = atom(node, 'uuid')
    need(str(uuid.UUID(value)) == value, 'Canonical UUID required')
    return value


def point(node, name):
    row = sx.one(node, name)
    need(row is not None and len(row) == 3, 'Exact unrotated ' + name + ' required')
    return [pt.nm(v, 1000000) for v in row[1:]]


def rectangle(node):
    a, b = point(node, 'start'), point(node, 'end')
    need(a[0] < b[0] and a[1] < b[1], 'Positive ordered rectangle required')
    return a + b


def read_board(raw):
    need(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, 'Bounded PCB bytes required')
    tree = sx.parse(raw.decode('utf-8'))
    need(tree[0] == 'kicad_pcb', 'PCB required')
    return tree


def inspect_board(raw, *, allow_routes=False, scope=DEFAULT_SCOPE):
    need(scope in (DEFAULT_SCOPE, MULTIPAD_SCOPE), 'Unsupported placement scope')
    tree = read_board(raw)
    layers = [sx.unquote(n[1]) for n in sx.one(tree, 'layers')[1:]
              if type(n) is list and sx.unquote(n[1]).endswith('.Cu')]
    need(layers == ['F.Cu', 'B.Cu'], 'Exact two outer copper layers required')
    names, resolve = g.source_net_identity(tree)
    need(not sx.children(tree, 'group') and not sx.children(tree, 'module'), 'Groups/legacy modules unsupported')
    edges = [n for n in tree if type(n) is list and sx.one(n, 'layer') is not None
             and atom(n, 'layer') == 'Edge.Cuts']
    need(len(edges) == 1 and edges[0][0] == 'gr_rect', 'Exactly one gr_rect outline; no cutouts')
    edge = edges[0]; outline = rectangle(edge)
    edge_row = dict(uuid=uid(edge), bounds_nm=outline,
                    stroke_nm=pt.nm(atom(sx.one(edge, 'stroke'), 'width'), 1000000))
    drawings = [n for n in tree if type(n) is list and str(n[0]).startswith('gr_')]
    need(drawings == edges, 'Additional board drawings are outside this fixture scope')
    need(scope == MULTIPAD_SCOPE or allow_routes or not p.routes(tree), 'Derived placement task must have no route items')
    rows, ids, pad_ids = [], set(), set()
    for fp in sx.children(tree, 'footprint'):
        identity = uid(fp); need(identity not in ids, 'Duplicate footprint UUID'); ids.add(identity)
        need(len(rows) < 16, 'Footprint population exceeded')
        allowed = {'layer', 'uuid', 'at', 'property', 'path', 'attr', 'fp_rect', 'pad', 'embedded_fonts', 'locked'}
        need(all(type(n) is list and n and n[0] in allowed for n in fp[2:]), 'Unsupported footprint geometry/field')
        need(atom(fp, 'layer') == 'F.Cu', 'Front, unflipped footprints only')
        at = point(fp, 'at')
        refs = [n for n in sx.children(fp, 'property') if sx.unquote(n[1]) == 'Reference']
        need(len(refs) == 1, 'One reference property required')
        courts = sx.children(fp, 'fp_rect'); need(len(courts) == 1, 'One rectangular courtyard required')
        court = courts[0]
        need(atom(court, 'layer') == 'F.CrtYd' and atom(court, 'fill') == 'none', 'Unfilled front courtyard required')
        local = rectangle(court)
        need(local[0] == -local[2] and local[1] == -local[3], 'Courtyard must be centred on footprint anchor')
        width = pt.nm(atom(sx.one(court, 'stroke'), 'width'), 1000000)
        need(0 <= width <= 100000 and width % 2 == 0, 'Bounded even-nanometre courtyard stroke required')
        world = [local[i] + at[i % 2] for i in range(4)]
        pads = []
        for pad in sx.children(fp, 'pad'):
            need((scope == MULTIPAD_SCOPE and len(pads) < 8 or not pads)
                 and pad[2:4] == ['thru_hole', 'circle'], 'Bounded circular PTH pads required')
            pad_fields = {'at', 'size', 'drill', 'layers', 'net', 'pinfunction', 'pintype', 'uuid'}
            need(all(type(n) is list and n and n[0] in pad_fields for n in pad[4:]),
                 'Unsupported pad geometry/field')
            pid = uid(pad); need(pid not in pad_ids and pid not in ids, 'Duplicate pad UUID'); pad_ids.add(pid)
            offset = point(pad, 'at')
            need(scope == MULTIPAD_SCOPE or offset == [0, 0], 'Centred unrotated pads only')
            size = point(pad, 'size'); need(size[0] == size[1] and size[0] > 0, 'Positive circular pad required')
            drill = pt.nm(atom(pad, 'drill'), 1000000)
            need(0 < drill < size[0], 'Positive circular drill smaller than pad required')
            need(sx.one(pad, 'layers') == ['layers', '"*.Cu"', '"*.Mask"'], 'Through-hole outer copper/mask layers required')
            net = resolve(sx.one(pad, 'net'))
            need(type(net) is str and net in names, 'Exact source net identity required')
            need(2 * abs(offset[0]) + size[0] <= local[2] - local[0]
                 and 2 * abs(offset[1]) + size[1] <= local[3] - local[1], 'Entire pad must fit courtyard')
            number = sx.unquote(pad[1])
            need(scope == DEFAULT_SCOPE or number and all(row['number'] != number for row in pads), 'Unique nonempty pad numbers required')
            row = dict(uuid=pid, number=number, net=net,
                       position_nm=[at[i] + offset[i] for i in range(2)], size_nm=size, drill_nm=[drill, drill])
            if scope == MULTIPAD_SCOPE:row['offset_nm'] = offset
            pads.append(row)
        rows.append(dict(uuid=identity, reference=sx.unquote(refs[0][2]), position_nm=at,
                         angle=0, side='front', locked=p.locked(fp),
                         courtyard=dict(uuid=uid(court), bounds_nm=world, stroke_nm=width), pads=sorted(pads,key=lambda row:row['uuid'])))
    need(3 <= len(rows) <= 16 and not ids.intersection(pad_ids), 'Bounded unique footprint/pad identities required')
    need(len(pad_ids) <= 32, 'Native pad population exceeded')
    zones = pt.source_zones(tree)
    for zone in zones:
        need(zone['is_rule_area'] is False, 'Keepouts/rule areas unsupported by this first Native probe')
        need(zone['holes'] == [0] and zone['arc_count'] == 0, 'Single straight hole-free copper zone required')
    result = dict(schema=1, outline=edge_row, footprints=sorted(rows, key=lambda r: r['uuid']), zones=zones,
                  route_count=len(p.routes(tree)), source_board_sha256=hashlib.sha256(raw).hexdigest())
    if scope == MULTIPAD_SCOPE:
        routes = []
        need(len(p.routes(tree)) <= 64, 'Preserved segment population exceeded')
        for route in rs._route_map(tree).values():
            identity = uid(route)  # Keep source canonical UUID spelling; the shared map uses compact keys.
            need(route[0] == 'segment', 'Vias and arcs unsupported by multipad-preserve-v1')
            allowed = {'start','end','width','layer','net','uuid','locked'}
            need(all(type(n) is list and n and n[0] in allowed for n in route[1:]), 'Unsupported segment field')
            start, end = point(route,'start'), point(route,'end')
            width = pt.nm(atom(route,'width'),1000000); layer = atom(route,'layer')
            net = resolve(sx.one(route,'net'))
            need(start != end and 0 < width <= 10_000_000 and layer in ('F.Cu','B.Cu'), 'Bounded straight copper segment required')
            need(net and any(pad['net'] == net for row in rows for pad in row['pads']), 'Segment needs a named net with actual pad witnesses')
            routes.append(dict(uuid=identity,kind='segment',net=net,start_nm=start,end_nm=end,width_nm=width,layer=layer,locked=p.locked(route)))
        result.update(scope=scope,routes=sorted(routes,key=lambda row:row['uuid']))
    return result


def derive_unrouted(raw):
    tree = read_board(raw); inspect_board(raw, allow_routes=True)
    removed = [dict(kind=n[0], uuid=uid(n), locked=p.locked(n),
                    ast_sha256=hashlib.sha256(sx.dump(n).encode()).hexdigest()) for n in p.routes(tree)]
    task = [sx.clone(n) for n in tree if not (type(n) is list and n and n[0] in p.ROUTES)]
    data = (sx.dump(task) + '\n').encode()
    need(read_board(data) == task, 'Exact route-removal reconstruction differs')
    inspect_board(data)
    return data, dict(kind='explicit-new-unrouted-derived-task', original_board_sha256=hashlib.sha256(raw).hexdigest(),
                     derived_board_sha256=hashlib.sha256(data).hexdigest(), removed_routes=removed,
                     all_other_AST_fields_identical=True, original_mutated=False)


def check_ordinary_zone(expected, observed):
    """Keep inactive native defaults visible; never reinterpret an actual rule area."""
    need(type(observed) is dict and set(observed) == pt.ROW_FIELDS, 'Complete native zone observation required')
    need(observed['is_rule_area'] is False and observed['placement_enabled'] is False,
         'Native keepout/placement rule unsupported')
    flags = observed['disallow']
    need(type(flags) is dict and set(flags) == set(pt.FLAGS)
         and all(type(value) is bool for value in flags.values()), 'Exact native zone flags required')
    need(all(observed.get(key) == value and type(observed.get(key)) is type(value)
             for key, value in expected.items()), 'Native/source zone geometry differs')
    # KiCad keeps these defaults even on ordinary pours. The source parser also
    # treats them as rule constraints only when a keepout/placement exists.
    # Native observations and the complete immutable AST are preserved separately.
    return observed


def facts_from_observation(observation, *, selected=None, region_nm=None, scope=DEFAULT_SCOPE):
    options = scope_options(scope=scope,selected=selected,region_nm=region_nm)
    selected, region_nm = options['selected'], options['region_nm']
    need((observation.get('scope',DEFAULT_SCOPE)) == scope, 'Observation placement scope differs')
    need(set(selected) <= {r['uuid'] for r in observation['footprints']}, 'Selected stable UUID absent')
    components = []
    for row in observation['footprints']:
        court = row['courtyard']; x0, y0, x1, y1 = court['bounds_nm']; stroke = court['stroke_nm']
        box = [(x0 - stroke / 2) / 1e6, (y0 - stroke / 2) / 1e6,
               (x1 + stroke / 2) / 1e6, (y1 + stroke / 2) / 1e6]
        region = region_nm if row['uuid'] in selected else observation['outline']['bounds_nm']
        components.append(dict(id=row['uuid'], position_mm=[n / 1e6 for n in row['position_nm']],
            size_mm=[box[2] - box[0], box[3] - box[1]], rotation_deg=0, side='front', locked=row['locked'],
            pads=[dict(id=pad['uuid'], net=pad['net'], offset_mm=[n/1e6 for n in pad.get('offset_nm',[0,0])]) for pad in row['pads']],
            allowed_region_mm=[n / 1e6 for n in region], allowed_rotations_deg=[0], allowed_sides=['front']))
    # Keep every original copper zone; the selected region is explicitly disjoint
    # from every zone outline, so this probe never assumes an absent copper pour.
    for zone in observation['zones']:
        box = pt.bbox(zone['outlines_nm'][0])
        need(region_nm[2] < box[0] or box[2] < region_nm[0] or region_nm[3] < box[1] or box[3] < region_nm[1],
             'Selected movement region intersects preserved zone envelope')
    tracks = []
    if scope == DEFAULT_SCOPE:
        need(observation['route_count'] == 0, 'No existing route items in derived task')
    else:
        need(observation['route_count'] == len(observation['routes']), 'Preserved route census differs')
        for route in observation['routes']:
            radius = (route['width_nm'] + 1) // 2 + ROUTE_GAP_NM
            box = [min(route['start_nm'][i],route['end_nm'][i])-radius for i in range(2)] + [max(route['start_nm'][i],route['end_nm'][i])+radius for i in range(2)]
            need(region_nm[2] < box[0] or box[2] < region_nm[0] or region_nm[3] < box[1] or box[3] < region_nm[1],
                 'Selected region intersects clearance-expanded preserved segment bounds')
            tracks.append(dict(id=route['uuid'],net=route['net'],pad_ids=sorted(pad['uuid'] for row in observation['footprints'] for pad in row['pads'] if pad['net']==route['net'])))
    facts = dict(schema=1, board=dict(kind='rectangle', bounds_mm=[n / 1e6 for n in observation['outline']['bounds_nm']], cutouts=[]),
                 components=components, selected=list(selected), fixed_components=[r['uuid'] for r in observation['footprints'] if r['uuid'] not in selected],
                 groups=[], tracks=tracks, keepouts=[], clearance_mm=ROUTE_GAP_NM/1e6)
    facts = constraints.prepare(facts)
    constraints.validate_alternative(facts, constraints.original_alternative(facts))
    return facts


def quantized_translation(facts, candidate):
    constraints.validate_alternative(facts, candidate)
    result = copy.deepcopy(candidate)
    moves = {}
    for row in result['transforms']:
        need(row['rotation_deg'] == 0 and row['side'] == 'front', 'Translation-only proposal required')
        target = [int((Decimal(str(row[k])) * 1000000).to_integral_value()) for k in ('x_mm', 'y_mm')]
        row['x_mm'], row['y_mm'] = (v / 1e6 for v in target)
        if row['component_id'] in facts['selected']:
            moves[row['component_id']] = target
    constraints.validate_alternative(facts, result)
    return result, moves


def translated_tree(raw, moves, *, scope=DEFAULT_SCOPE, selected=None, region_nm=None):
    options = scope_options(scope=scope,selected=selected,region_nm=region_nm)
    need(type(moves) is dict and set(moves) == set(options['selected']), 'Exact prospectively selected UUIDs required')
    tree = read_board(raw); known = set()
    for fp in sx.children(tree, 'footprint'):
        identity = uid(fp)
        if identity not in moves:
            continue
        need(not p.locked(fp), 'Locked footprint translation refused')
        need(type(moves[identity]) is list and len(moves[identity]) == 2
             and all(type(n) is int and abs(n) <= 2_000_000_000 for n in moves[identity]), 'Integer nm translation required')
        at = sx.one(fp, 'at'); need(len(at) == 3, 'Unrotated footprint required')
        for i, value in enumerate(moves[identity], 1):
            text = format(Decimal(value) / 1000000, 'f')
            at[i] = text.rstrip('0').rstrip('.') if '.' in text else text
        known.add(identity)
    need(known == set(moves), 'Unknown translated footprint UUID')
    return tree


def validate_moves(observation, moves, *, scope=DEFAULT_SCOPE, selected=None, region_nm=None):
    """Independently check integer translations against captured source facts."""
    options = scope_options(scope=scope,selected=selected,region_nm=region_nm)
    need(type(moves) is dict and set(moves) == set(options['selected']), 'Exact prospectively selected UUIDs required')
    facts = facts_from_observation(observation,**options)
    alternative = constraints.original_alternative(facts)
    for row in alternative['transforms']:
        if row['component_id'] in moves:
            target = moves[row['component_id']]
            need(type(target) is list and len(target) == 2
                 and all(type(n) is int and abs(n) <= 2_000_000_000 for n in target), 'Integer nm translation required')
            row['x_mm'], row['y_mm'] = (n / 1e6 for n in target)
    constraints.validate_alternative(facts, alternative)
    return alternative


def check_translation(source_raw, candidate_raw, moves, *, scope=DEFAULT_SCOPE, selected=None, region_nm=None):
    options = scope_options(scope=scope,selected=selected,region_nm=region_nm)
    validate_moves(inspect_board(source_raw,scope=scope), moves,**options)
    expected = p._without_derived_fill(translated_tree(source_raw, moves,**options))
    actual = p._without_derived_fill(read_board(candidate_raw))
    need(actual == expected, 'Native serialization changed fields beyond selected translations/derived fill')
    return dict(exact_immutable_AST=True, allowed_changes=['selected footprint XY', 'derived top-level zone fill'],
                candidate_sha256=hashlib.sha256(candidate_raw).hexdigest())


def transplant_refill(preimage_raw, native_refill_raw):
    """Copy only shared derived-fill fields from a retained separate Native copy."""
    preimage, refilled = read_board(preimage_raw), read_board(native_refill_raw)
    before_ids = [uid(zone) for zone in sx.children(preimage, 'zone')]
    after_ids = [uid(zone) for zone in sx.children(refilled, 'zone')]
    need(len(set(before_ids)) == len(before_ids) and len(set(after_ids)) == len(after_ids)
         and set(before_ids) == set(after_ids), 'Refill zone identities differ')
    rebuilt = p.transplant_fill(preimage, refilled)
    need(p._without_derived_fill(rebuilt) == p._without_derived_fill(preimage),
         'Refill transplant changed source fields')
    return (sx.dump(rebuilt) + '\n').encode()


def check_refill_reconstruction(preimage_raw, native_refill_raw, candidate_raw):
    need(candidate_raw == transplant_refill(preimage_raw, native_refill_raw),
         'Candidate differs from exact retained refill reconstruction')
    return dict(policy='derived-zone-fill-only', exact_reconstruction=True,
                preimage_sha256=hashlib.sha256(preimage_raw).hexdigest(),
                native_output_sha256=hashlib.sha256(native_refill_raw).hexdigest(),
                candidate_sha256=hashlib.sha256(candidate_raw).hexdigest())
