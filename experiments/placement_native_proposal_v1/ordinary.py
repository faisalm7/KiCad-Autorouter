"""Bounded ordinary front-footprint observations; no Native or file mutation.

Only two-pad SMD footprints with centred rectangular courtyards are movable.
All other admitted footprints are fixed conservative courtyard obstacles. This
is a source contract, not evidence that a board passed Native qualification.
"""
from decimal import Decimal, InvalidOperation
import hashlib

from autorouter import sexpr as sx, pipeline as p, board_floor as g
from autorouter import placement_transform as pt, routing_scope as rs
from . import contract as c

PASSIVE_LAYERS = {'F.SilkS', 'B.SilkS', 'F.Fab', 'B.Fab', 'Dwgs.User',
                  'Cmts.User', 'Eco1.User', 'Eco2.User'} | {'User.' + str(i) for i in range(1, 10)}


def fields(node, allowed, *, start=1, repeated=()):
    c.need(all(type(n) is list and n and n[0] in allowed for n in node[start:]),
           'Unsupported ' + str(node[0]) + ' geometry/field')
    for name in allowed - set(repeated):
        sx.one(node, name)


def angle(value):
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError('Exact cardinal angle required')
    c.need(number.is_finite() and abs(number) <= 360 and number % 90 == 0,
           'Exact bounded cardinal angle required')
    return int(number) % 360


def at(node):
    row = sx.one(node, 'at')
    c.need(row is not None and len(row) in (3, 4), 'Exact XY and optional cardinal angle required')
    return [pt.nm(v, 1000000) for v in row[1:3]], angle(row[3]) if len(row) == 4 else 0


def world(point, anchor, rotation):
    x, y = point
    dx, dy = {0: (x, y), 90: (y, -x), 180: (-x, -y), 270: (-y, x)}[rotation]
    result = [anchor[0] + dx, anchor[1] + dy]
    c.need(all(abs(n) <= 2_000_000_000 for n in result), 'World coordinate out of range')
    return result


def locked(node):
    value = sx.one(node, 'locked')
    c.need(value is None or value in (['locked'], ['locked', 'yes'], ['locked', 'no']), 'Explicit supported lock value required')
    return p.locked(node)


def stroke(node):
    row = sx.one(node, 'stroke')
    c.need(row is not None, 'Explicit stroke required')
    fields(row, {'width', 'type'})
    width = pt.nm(c.atom(row, 'width'), 1000000)
    c.need(0 <= width <= 1_000_000 and c.atom(row, 'type') in ('default', 'solid'),
           'Bounded solid stroke required')
    return width


def primitive(node, anchor=(0, 0), rotation=0):
    c.need(node[0] in ('fp_line', 'fp_rect', 'gr_line', 'gr_rect'), 'Only straight line/rectangle graphics supported')
    fields(node, {'start', 'end', 'stroke', 'fill', 'layer', 'uuid', 'locked'})
    a, b = c.point(node, 'start'), c.point(node, 'end')
    c.need(a != b, 'Nonzero graphic required')
    fill = sx.one(node, 'fill')
    c.need(fill is None or c.atom(node, 'fill') in ('none', 'solid', 'no', 'yes'), 'Unsupported graphic fill')
    if node[0].endswith('rect'):
        c.need(a[0] < b[0] and a[1] < b[1], 'Positive ordered graphic rectangle required')
    else:
        c.need(fill is None, 'Line cannot have fill')
    return dict(uuid=c.uid(node), kind=node[0], layer=c.atom(node, 'layer'),
                start_nm=world(a, anchor, rotation), end_nm=world(b, anchor, rotation),
                local_start_nm=a, local_end_nm=b, stroke_nm=stroke(node),
                fill=({'none': 'none', 'no': 'none', 'solid': 'solid', 'yes': 'solid'}[c.atom(node, 'fill')]
                      if fill is not None else None), locked=locked(node))


def text(node, anchor=(0, 0), rotation=0):
    start = 3 if node[0] in ('property', 'fp_text') else 2
    fields(node, {'at', 'layer', 'uuid', 'effects', 'hide', 'unlocked', 'render_cache', 'locked'}, start=start)
    layer = c.atom(node, 'layer')
    c.need(layer in PASSIVE_LAYERS, 'Text on non-passive layer unsupported')
    position, direction = at(node)
    effects = sx.one(node, 'effects')
    if effects is not None:
        fields(effects, {'font', 'justify', 'hide'})
        font = sx.one(effects, 'font')
        if font is not None:
            fields(font, {'face', 'size', 'thickness', 'bold', 'italic', 'line_spacing'})
        justify = sx.one(effects, 'justify')
        c.need(justify is None or all(v in ('left', 'right', 'top', 'bottom', 'mirror') for v in justify[1:]),
               'Unsupported text justification')
    cache = sx.one(node, 'render_cache')
    if cache is not None:
        c.need(len(cache) >= 3 and all(type(poly) is list and len(poly) == 2 and poly[0] == 'polygon'
               and type(poly[1]) is list and poly[1][0] == 'pts'
               and all(type(xy) is list and len(xy) == 3 and xy[0] == 'xy'
                       and all(type(v) is str for v in xy[1:]) for xy in poly[1][1:]) for poly in cache[3:]),
               'Unsupported text render cache')
        for poly in cache[3:]:
            for xy in poly[1][1:]:
                for value in xy[1:]: pt.nm(value, 1000000)
    identity = c.uid(node) if sx.one(node, 'uuid') is not None else None
    return dict(uuid=identity, kind=node[0], layer=layer, position_nm=world(position, anchor, rotation),
                offset_nm=position, angle=direction, text=sx.unquote(node[start - 1]),
                name=sx.unquote(node[1]) if node[0] == 'property' else None,
                text_kind=sx.unquote(node[1]) if node[0] == 'fp_text' else None,
                ast_sha256=hashlib.sha256(sx.dump(node).encode()).hexdigest())


def models(fp):
    result = []
    for node in sx.children(fp, 'model'):
        fields(node, {'offset', 'scale', 'rotate', 'hide', 'opacity'}, start=2)
        c.need(type(node[1]) is str, 'Model path declaration required')
        for key in ('offset', 'scale', 'rotate'):
            row = sx.one(node, key)
            c.need(row is not None and len(row) == 2 and type(row[1]) is list
                   and len(row[1]) == 4 and row[1][0] == 'xyz', 'Explicit model transform required')
            for value in row[1][1:]:
                try: number = Decimal(value)
                except (InvalidOperation, TypeError): raise ValueError('Finite model transform required')
                c.need(number.is_finite() and abs(number) <= 2_000_000, 'Bounded model transform required')
        result.append(dict(path=sx.unquote(node[1]), ast_sha256=hashlib.sha256(sx.dump(node).encode()).hexdigest()))
    return result


def courtyard(primitives):
    c.need(1 <= len(primitives) <= 16, 'One bounded closed front courtyard required')
    c.need(all(row['layer'] == 'F.CrtYd' and row['stroke_nm'] <= 100000
               and row['fill'] in (None, 'none') for row in primitives), 'Bounded unfilled front courtyard required')
    if len(primitives) == 1 and primitives[0]['kind'] == 'fp_rect':
        a, b = primitives[0]['local_start_nm'], primitives[0]['local_end_nm']
        points = [a, [b[0], a[1]], b, [a[0], b[1]]]
        rectangular = True
    else:
        c.need(all(row['kind'] == 'fp_line' for row in primitives), 'Courtyard must be one rectangle or closed line polygon')
        links = {}
        edges = set()
        for row in primitives:
            a, b = tuple(row['local_start_nm']), tuple(row['local_end_nm'])
            edge = tuple(sorted((a, b)))
            c.need(edge not in edges, 'Duplicate courtyard edge')
            edges.add(edge)
            links.setdefault(a, []).append(b); links.setdefault(b, []).append(a)
        c.need(len(links) == len(primitives) and all(len(v) == 2 for v in links.values()), 'Closed courtyard polygon required')
        first = min(links); points = [list(first)]; previous = None; current = first
        while True:
            choices = [n for n in sorted(links[current]) if n != previous]
            following = choices[0]
            if following == first: break
            c.need(list(following) not in points, 'Disconnected courtyard polygon')
            points.append(list(following)); previous, current = current, following
        c.need(len(points) == len(primitives), 'Disconnected courtyard polygon')
        pt.simple(points)
        rectangular = (len(points) == 4 and len({v[0] for v in points}) == 2
                       and len({v[1] for v in points}) == 2
                       and all(a[0] == b[0] or a[1] == b[1] for a, b in zip(points, points[1:] + points[:1])))
    local_bounds = pt.bbox(points)
    centered = local_bounds[0] == -local_bounds[2] and local_bounds[1] == -local_bounds[3]
    # Cardinal rotations map these exact rectangle extrema to the world bbox.
    world_points = [row[key] for row in primitives for key in ('start_nm', 'end_nm')]
    return dict(bounds_nm=pt.bbox(world_points), local_bounds_nm=local_bounds,
                stroke_nm=max(row['stroke_nm'] for row in primitives), rectangular=rectangular,
                centered=centered, primitives=sorted(primitives, key=lambda row: row['uuid']))


def pad_row(pad, anchor, rotation, resolve, names):
    c.need(pad[2:4] in (['thru_hole', 'circle'], ['thru_hole', 'rect'], ['smd', 'rect'], ['smd', 'roundrect']),
           'Only declared circular/rectangular PTH or rectangular/roundrect SMD pads supported')
    fields(pad, {'at', 'size', 'drill', 'layers', 'net', 'pinfunction', 'pintype', 'uuid',
                 'roundrect_rratio', 'remove_unused_layers', 'keep_end_layers'}, start=4)
    offset, direction = at(pad); size = c.point(pad, 'size')
    c.need(all(0 < n <= 100_000_000 for n in size), 'Bounded positive pad size required')
    layer_node = sx.one(pad, 'layers')
    c.need(layer_node is not None and all(type(v) is str for v in layer_node[1:]), 'Explicit pad layers required')
    layers = [sx.unquote(v) for v in layer_node[1:]]
    c.need(len(set(layers)) == len(layers), 'Duplicate pad layers')
    is_smd = pad[2] == 'smd'
    c.need(set(layers) == ({'F.Cu', 'F.Paste', 'F.Mask'} if is_smd else {'*.Cu', '*.Mask'}), 'Exact supported pad layers required')
    drill = [0, 0]
    if is_smd:
        c.need(sx.one(pad, 'drill') is None, 'SMD drill unsupported')
    else:
        d = pt.nm(c.atom(pad, 'drill'), 1000000)
        c.need(0 < d < min(size), 'Positive circular drill smaller than pad required')
        drill = [d, d]
        c.need(pad[3] != 'circle' or size[0] == size[1], 'Circular pad dimensions differ')
    ratio = None
    if pad[3] == 'roundrect':
        try: number = Decimal(c.atom(pad, 'roundrect_rratio'))
        except InvalidOperation: raise ValueError('Finite roundrect ratio required')
        c.need(number.is_finite() and 0 < number <= Decimal('0.5'), 'Bounded roundrect ratio required')
        ratio = float(number)
        c.need(Decimal(str(ratio)) == number, 'Exactly represented roundrect ratio required')
    else:
        c.need(sx.one(pad, 'roundrect_rratio') is None, 'Roundrect ratio on other pad shape unsupported')
    flags = {}
    for name in ('remove_unused_layers', 'keep_end_layers'):
        row = sx.one(pad, name)
        c.need(row is None or (not is_smd and row in ([name], [name, 'yes'], [name, 'no'])), 'Only explicit PTH layer-removal flags supported')
        flags[name] = row is not None and row != [name, 'no']
    net = resolve(sx.one(pad, 'net'))
    c.need(type(net) is str and net in names, 'Exact source net identity required')
    return dict(uuid=c.uid(pad), number=sx.unquote(pad[1]), net=net, position_nm=world(offset, anchor, rotation),
                offset_nm=offset, angle=direction, kind=pad[2], shape=pad[3], roundrect_rratio=ratio,
                size_nm=size, drill_nm=drill, layers=layers, **flags)


def inspect(raw):
    tree = c.read_board(raw)
    fields(tree, {'version', 'generator', 'generator_version', 'general', 'paper', 'title_block', 'layers',
                  'setup', 'net', 'footprint', 'gr_line', 'gr_rect', 'gr_text', 'segment', 'zone', 'embedded_fonts'},
           repeated={'net', 'footprint', 'gr_line', 'gr_rect', 'gr_text', 'segment', 'zone'})
    layer_table = sx.one(tree, 'layers')
    c.need(layer_table is not None, 'Layer table required')
    layers = [sx.unquote(n[1]) for n in layer_table[1:] if type(n) is list and len(n) > 1 and sx.unquote(n[1]).endswith('.Cu')]
    c.need(layers == ['F.Cu', 'B.Cu'], 'Exact two outer copper layers required')
    names, resolve = g.source_net_identity(tree)
    identities = set()
    def claim(identity):
        c.need(identity not in identities, 'Duplicate native item UUID'); identities.add(identity)
    edge_nodes = [n for n in tree[1:] if type(n) is list and sx.one(n, 'layer') is not None and c.atom(n, 'layer') == 'Edge.Cuts']
    if len(edge_nodes) == 1 and edge_nodes[0][0] == 'gr_rect':
        bounds = c.rectangle(edge_nodes[0])
    else:
        segments = pt.rectangle(tree)
        bounds = pt.bbox([list(point) for edge in segments for point in edge])
    outline_rows = [primitive(n) for n in edge_nodes]
    c.need(all(row['fill'] in (None, 'none') for row in outline_rows), 'Unfilled board outline required')
    for row in outline_rows: claim(row['uuid'])
    outline = dict(kind='rectangle', bounds_nm=bounds, stroke_nm=max(row['stroke_nm'] for row in outline_rows),
                   primitives=sorted(outline_rows, key=lambda row: row['uuid']))
    board_graphics = []
    for node in tree[1:]:
        if type(node) is not list or not str(node[0]).startswith('gr_') or node in edge_nodes: continue
        row = text(node) if node[0] == 'gr_text' else primitive(node)
        c.need(row['layer'] in PASSIVE_LAYERS, 'Board graphic on non-passive layer unsupported')
        c.need(row['uuid'] is not None, 'Board graphic UUID required'); claim(row['uuid']); board_graphics.append(row)
    rows = []
    for fp in sx.children(tree, 'footprint'):
        c.need(len(rows) < 16, 'Footprint population exceeded')
        fields(fp, {'layer', 'uuid', 'at', 'property', 'path', 'attr', 'fp_rect', 'fp_line', 'fp_text',
                    'pad', 'embedded_fonts', 'locked', 'descr', 'tags', 'sheetname', 'sheetfile', 'model'},
               start=2, repeated={'property', 'fp_rect', 'fp_line', 'fp_text', 'pad', 'model'})
        identity = c.uid(fp); claim(identity)
        c.need(c.atom(fp, 'layer') == 'F.Cu', 'Front unflipped footprints only')
        anchor, rotation = at(fp)
        attr = sx.one(fp, 'attr')
        c.need(attr is None or all(v in ('smd', 'through_hole', 'board_only', 'exclude_from_pos_files', 'exclude_from_bom') for v in attr[1:]), 'Unsupported footprint attribute')
        refs = [n for n in sx.children(fp, 'property') if len(n) >= 3 and sx.unquote(n[1]) == 'Reference']
        c.need(len(refs) == 1, 'One reference property required')
        graphics, courts, metadata_properties = [], [], []
        for node in fp[2:]:
            if node[0] not in ('fp_rect', 'fp_line', 'fp_text', 'property'): continue
            if node[0] == 'property' and len(node) == 3:
                c.need(all(type(v) is str for v in node[1:]), 'Scalar property declaration required')
                metadata_properties.append(dict(name=sx.unquote(node[1]), value=sx.unquote(node[2])))
                continue
            row = text(node, anchor, rotation) if node[0] in ('property', 'fp_text') else primitive(node, anchor, rotation)
            if row['uuid'] is not None: claim(row['uuid'])
            if row['layer'] == 'F.CrtYd': courts.append(row)
            else:
                c.need(row['layer'] in PASSIVE_LAYERS, 'Footprint graphic on non-passive layer unsupported'); graphics.append(row)
        court = courtyard(courts)
        pads = [pad_row(n, anchor, rotation, resolve, names) for n in sx.children(fp, 'pad')]
        c.need(len(pads) <= 8 and len({row['number'] for row in pads}) == len(pads)
               and all(row['number'] for row in pads), 'Bounded unique nonempty pad numbers required')
        for row in pads:
            claim(row['uuid'])
            x, y = row['position_nm']; width, height = row['size_nm']
            if row['angle'] % 180: width, height = height, width
            box = court['bounds_nm']
            c.need(2 * box[0] <= 2 * x - width and 2 * x + width <= 2 * box[2]
                   and 2 * box[1] <= 2 * y - height and 2 * y + height <= 2 * box[3], 'Entire pad must fit conservative courtyard envelope')
        reasons = []
        if locked(fp): reasons.append('locked footprint')
        if len(pads) != 2 or any(pad['kind'] != 'smd' for pad in pads): reasons.append('only two-pad SMD footprints are movable')
        if not court['rectangular'] or not court['centered']: reasons.append('movement requires centred rectangular courtyard')
        rows.append(dict(uuid=identity, reference=sx.unquote(refs[0][2]), position_nm=anchor, angle=rotation,
                         side='front', locked=locked(fp), placement_eligible=not reasons, fixed_reasons=reasons,
                         courtyard=court, graphics=graphics, metadata_properties=metadata_properties, models=models(fp), pads=sorted(pads, key=lambda row: row['uuid'])))
    c.need(1 <= len(rows) <= 16 and sum(len(row['pads']) for row in rows) <= 32, 'Bounded footprint/pad population required')
    zones = pt.source_zones(tree)
    for zone in zones:
        claim(zone['uuid'])
        c.need(zone['is_rule_area'] is False and zone['holes'] == [0] and zone['arc_count'] == 0, 'Keepouts/cutouts/arcs unsupported')
    routes = []
    c.need(len(p.routes(tree)) <= 64, 'Preserved segment population exceeded')
    for route in rs._route_map(tree).values():
        c.need(route[0] == 'segment', 'Vias and arcs unsupported')
        fields(route, {'start', 'end', 'width', 'layer', 'net', 'uuid', 'locked'})
        identity = c.uid(route); claim(identity)
        a, b = c.point(route, 'start'), c.point(route, 'end')
        width = pt.nm(c.atom(route, 'width'), 1000000); layer = c.atom(route, 'layer'); net = resolve(sx.one(route, 'net'))
        c.need(a != b and 0 < width <= 10000000 and layer in ('F.Cu', 'B.Cu'), 'Bounded straight copper segment required')
        c.need(net and any(pad['net'] == net for row in rows for pad in row['pads']), 'Segment needs named net with actual pad witnesses')
        routes.append(dict(uuid=identity, kind='segment', net=net, start_nm=a, end_nm=b, width_nm=width, layer=layer, locked=locked(route)))
    return dict(schema=1, scope=c.ORDINARY_SCOPE, outline=outline, footprints=sorted(rows, key=lambda row: row['uuid']),
                graphics=board_graphics, zones=zones, routes=sorted(routes, key=lambda row: row['uuid']),
                route_count=len(routes), source_board_sha256=hashlib.sha256(raw).hexdigest())
