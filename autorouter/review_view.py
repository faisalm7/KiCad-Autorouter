"""Copper changes, findings and Native plots for disposable review projects."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from html import escape
from pathlib import Path
import hashlib
import json
import math
import re
import shutil
import xml.etree.ElementTree as element_tree
from . import config as c, floor_route as f, pipeline as p, placement_clearance as pc, sexpr as sx
from . import local_settings as ls


KICAD_DOCTYPE = re.compile(rb'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\s+"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">')
WARNING_TITLES = {
    'lib_footprint_issues': 'Footprint library issues',
    'lib_footprint_mismatch': 'Footprint differs from library',
    'footprint_symbol_field_mismatch': 'Footprint and schematic fields differ',
    'connection_width': 'Copper connection width',
    'text_height': 'Text height',
}


def finding_groups(native, source):
    """Match exact, unconsumed source warnings. Absence is not evidence of a new issue."""
    source = source if isinstance(source, dict) else {}
    baseline = source.get('findings', [])
    inherited = Counter(f.canonical(row) for row in baseline if isinstance(row, dict)
                        and row.get('severity') == 'warning' and not row.get('excluded')) if isinstance(baseline, list) else Counter()
    groups = defaultdict(list)
    findings = native.get('findings', [])
    for row in findings if isinstance(findings, list) else ():
        if not isinstance(row, dict):
            continue
        origin = 'KiCad error' if row.get('severity') == 'error' else 'Other finding'
        if row.get('excluded') or row.get('severity') == 'exclusion':
            origin = 'Excluded by project settings'
        elif row.get('severity') == 'warning':
            identity = f.canonical(row)
            if inherited[identity]:
                origin = 'Already in the saved input'
                inherited[identity] -= 1
            else:
                origin = 'Source match unconfirmed'
        reason = str(row.get('type', 'other'))
        title = WARNING_TITLES.get(reason, reason.replace('_', ' ').capitalize())
        groups[(origin, title)].append(row)
    return groups


def findings_html(native, source):
    parts = []
    for (origin, title), rows in finding_groups(native, source).items():
        items = []
        for row in rows:
            description = escape(str(row.get('description', title)))
            locations = []
            for item in row.get('items') or []:
                if isinstance(item, dict):
                    text = str(item.get('description', 'Board item'))
                    pos = item.get('pos')
                    if isinstance(pos, dict) and all(type(pos.get(key)) in (float, int) for key in ('x', 'y')):
                        text += f" at {pos['x']:.3f}, {pos['y']:.3f} mm"
                    locations.append(escape(text))
            if locations:
                description += '<br><small>' + '<br>'.join(locations) + '</small>'
            items.append('<li>' + description + '</li>')
        parts.append(f'<details><summary>{escape(title)} <strong>{len(rows)}</strong> '
                     f'<small>{escape(origin)}</small></summary><ul>{"".join(items)}</ul></details>')
    if not parts:
        return '<p>No individual findings in this receipt. See the counts and saved details.</p>'
    return ''.join(parts)


def route_changes(before, after):
    """Partition exact route records as multisets, preserving duplicate counts."""
    source = p.routes(before)
    target = p.routes(after)
    remaining = Counter(map(f.canonical, source))
    retained, added = [], []
    for row in target:
        key = f.canonical(row)
        if remaining[key]:
            retained.append(row)
            remaining[key] -= 1
        else:
            added.append(row)
    removed = []
    for row in source:
        key = f.canonical(row)
        if remaining[key]:
            removed.append(row)
            remaining[key] -= 1
    return {'retained': retained, 'added': added, 'removed': removed}


def _coordinates(row, key, size):
    values = sx.one(row, key, [])[1:]
    numbers = tuple(float(value) for value in values)
    if len(numbers) != size or any(not math.isfinite(value) or abs(value) > 2000 for value in numbers):
        raise ValueError('Out-of-range drawing geometry')
    return numbers


def _line_or_arc(row):
    start, end = (_coordinates(row, key, 2) for key in ('start', 'end'))
    points = [start, end]
    if row[0] in ('arc', 'gr_arc'):
        # Compute the circumcircle through the saved start, midpoint and end.
        mid = _coordinates(row, 'mid', 2)
        bx, by = mid[0] - start[0], mid[1] - start[1]
        cx, cy = end[0] - start[0], end[1] - start[1]
        cross = bx * cy - by * cx
        if abs(cross) < 1e-12:
            raise ValueError('Degenerate drawing arc')
        b2, c2 = bx * bx + by * by, cx * cx + cy * cy
        offset_x, offset_y = (cy * b2 - by * c2) / (2 * cross), (bx * c2 - cx * b2) / (2 * cross)
        radius = math.hypot(offset_x, offset_y)
        large = (bx * (cx - bx) + by * (cy - by)) < 0
        sweep = cross > 0
        angle = math.atan2(-offset_y, -offset_x)
        direction = 1 if sweep else -1
        extent = (direction * (math.atan2(cy - offset_y, cx - offset_x) - angle)) % math.tau
        points.extend((start[0] + offset_x + radius * math.cos(quarter),
                       start[1] + offset_y + radius * math.sin(quarter))
                      for quarter in (0, math.pi / 2, math.pi, math.pi * 1.5)
                      if (direction * (quarter - angle)) % math.tau < extent)
        path = f'M {start[0]} {start[1]} A {radius} {radius} 0 {int(large)} {int(sweep)} {end[0]} {end[1]}'
    else:
        path = f'M {start[0]} {start[1]} L {end[0]} {end[1]}'
    return points, path


def _route_shape(row, layers):
    if row[0] == 'via':
        x, y = _coordinates(row, 'at', 2)
        size, = _coordinates(row, 'size', 1)
        radius = size / 2
        # Via spans follow the stack order, including inner layers.
        first, last = (layers.index(sx.unquote(name)) for name in sx.one(row, 'layers', [])[1:])
        span = layers[min(first, last):max(first, last) + 1]
        return span, [(x - radius, y - radius), (x + radius, y + radius)], f'<circle cx="{x}" cy="{y}" r="{radius}"/>'
    layer, = sx.one(row, 'layer', [])[1:]
    layer = sx.unquote(layer)
    width, = _coordinates(row, 'width', 1)
    points, path = _line_or_arc(row)
    half = width / 2
    extents = [(x + side * half, y + side * half) for x, y in points for side in (-1, 1)]
    return (layer,), extents, f'<path d="{path}" stroke-width="{width}"/>'


WORKSPACE_COLORS = {'protected': '#7354a4', 'retained': '#687b8c',
                    'added': '#087f68', 'removed': '#b95023'}
REFERENCE_LIMIT = 24
PAD_MARKER_LIMIT = 256
WORKSPACE_ITEM_LIMIT = 2048
FINDING_LIMIT = 128
FINDING_ITEM_LIMIT = 8
WORKSPACE_SVG_LIMIT = 2 * 1024**2


@dataclass(frozen=True)
class BoardPoint:
    xy: tuple
    layers: tuple
    identity: str = ''
    label: str = ''
    detail: str = ''
    net: str = ''
    hit: tuple = ()
    drawing: str = ''
    drill: float = 0


@dataclass(frozen=True)
class BoardDrawing:
    bounds: tuple
    anchors: tuple
    cutouts: tuple = ()
    edge_paths: tuple = ()
    pads: tuple = ()
    footprints: tuple = ()
    partial_pad_context: bool = False


def _edge_chain_drawing(edges):
    """Draw a closed line/arc chain as strokes, without inferring a board area."""
    from .placement_transform import bbox, nm

    if not 3 <= len(edges) <= 32 or any(row[0] not in ('gr_line', 'gr_arc') for row in edges):
        raise ValueError('Unsupported saved edge drawing')
    adjacency = defaultdict(set)
    extents, paths = [], []
    for row in edges:
        start, end = (tuple(nm(value, 1_000_000) for value in sx.one(row, key, [])[1:])
                      for key in ('start', 'end'))
        if start == end or end in adjacency[start]:
            raise ValueError('Repeated or degenerate edge')
        adjacency[start].add(end)
        adjacency[end].add(start)
        points, path = _line_or_arc(row)
        if any(abs(value) > 2000 for point in points for value in point):
            raise ValueError('Out-of-range edge drawing')
        extents.extend(points)
        paths.append(path)
    if any(len(neighbours) != 2 for neighbours in adjacency.values()):
        raise ValueError('Edge chain is not closed')
    pending, seen = [next(iter(adjacency))], set()
    while pending:
        point = pending.pop()
        if point not in seen:
            seen.add(point)
            pending.extend(adjacency[point] - seen)
    if seen != set(adjacency):
        raise ValueError('Separate contours need a qualified drawing')
    return tuple(bbox(extents)), tuple(paths)


def _display_uuid(row):
    from .routing_scope import _uuid

    try:
        return _uuid(row)[1].lower()
    except p.Rejected:
        return ''


def _display_text(value, limit=96):
    if type(value) is not str:
        return ''
    clean = ''.join(char if char.isprintable() else ' ' for char in value[:limit])
    return ' '.join(clean.split())


def _net_reader(board):
    from .board_floor import source_net_identity

    try:
        _, resolve = source_net_identity(board)
    except (ValueError, TypeError, KeyError, IndexError):
        return lambda _: ''  # Geometry remains useful without a known net.
    def read(node):
        try:
            name = resolve(sx.one(node, 'net'), owner=node)
        except (ValueError, TypeError, KeyError, IndexError):
            return ''
        return name if type(name) is str and len(name) <= 256 and name.isprintable() else ''

    return read


def _pad_layers(pad, layers):
    row = sx.one(pad, 'layers', [])
    selectors = [sx.unquote(value) for value in row[1:]]
    if len(set(selectors)) != len(selectors) or sx.one(pad, 'padstack') is not None:
        return ()
    if pad[2:4] in (['smd', 'rect'], ['smd', 'roundrect']):
        if set(selectors) == {'F.Cu', 'F.Mask', 'F.Paste'}:
            return ('F.Cu',) if 'F.Cu' in layers else ()
    if (pad[2:4] in (['thru_hole', 'circle'], ['thru_hole', 'rect'], ['thru_hole', 'roundrect'], ['thru_hole', 'oval'])
            and set(selectors) == {'*.Cu', '*.Mask'}
            and sx.one(pad, 'remove_unused_layers') in (None, ['remove_unused_layers', 'no'])):
        return tuple(layers)
    return ()


def _courtyard(part, anchor, rotation):
    from experiments.placement_native_proposal_v1 import ordinary

    shapes = [row for row in part[2:] if type(row) is list and row and sx.one(row, 'layer') == ['layer', '"F.CrtYd"']]
    if not 1 <= len(shapes) <= 16:
        return ''
    try:
        primitives = [ordinary.context_primitive(row, anchor, rotation, fixed_courtyard=True)
                      if row[0] == 'fp_circle' else ordinary.primitive(row, anchor, rotation) for row in shapes]
        court = ordinary.courtyard(primitives, circular=True)
    except (ValueError, TypeError, IndexError, KeyError):
        return ''
    attrs = 'data-role="courtyard" stroke="#7e91a1" stroke-width="0.055" fill="none"'
    paths = []
    for row in court['primitives']:
        if row['kind'] == 'fp_circle':
            x, y = (value / 1_000_000 for value in row['center_nm'])
            ex, ey = (value / 1_000_000 for value in row['end_nm'])
            paths.append(f'<circle {attrs} cx="{x}" cy="{y}" r="{math.dist((x, y), (ex, ey))}"/>')
            continue
        x, y, ex, ey = (value / 1_000_000 for value in (*row['start_nm'], *row['end_nm']))
        if row['kind'] == 'fp_rect':
            paths.append(f'<rect {attrs} x="{min(x, ex)}" y="{min(y, ey)}" '
                         f'width="{abs(ex - x)}" height="{abs(ey - y)}"/>')
        else:
            paths.append(f'<path {attrs} d="M {x} {y} L {ex} {ey}"/>')
    return ''.join(paths)


def _pad_shape(pad, centre, anchor, rotation):
    from experiments.placement_native_proposal_v1.ordinary import pad_row

    try:
        # Copper geometry can be rendered independently of the net label.
        shape = pad_row(pad, anchor, rotation, lambda _: '', {''}, tht=True)
    except (ValueError, TypeError, IndexError, KeyError):
        return (), '', 0
    x, y = centre
    width, height = (value / 1_000_000 for value in shape['size_nm'])
    drill = shape['drill_nm'][0] / 2_000_000
    attrs = 'data-role="pad-shape" fill="#d3ad69" stroke="#967745" stroke-width="0.035"'
    if shape['shape'] == 'circle':
        return ('circle', width / 2), f'<circle {attrs} cx="{x}" cy="{y}" r="{width / 2}"/>', drill
    angle = -shape['angle']
    radius = min(width, height) * (shape['roundrect_rratio'] or 0)
    hit = ('rect', width / 2, height / 2, angle, radius)
    drawing = (f'<rect {attrs} x="{x - width / 2}" y="{y - height / 2}" width="{width}" height="{height}" '
               f'rx="{radius}" transform="rotate({angle} {x} {y})"/>')
    return hit, drawing, drill


def _part_points(part, ref, xy, layers, bounds, net_for, *, show_pads):
    from experiments.placement_native_proposal_v1.ordinary import at, world

    side, = sx.one(part, 'layer', [])[1:]
    side = sx.unquote(side)
    ref = _display_text(ref, 32) or 'Component'
    uid = _display_uuid(sx.one(part, 'uuid'))
    pads = sx.children(part, 'pad')
    try:
        pose = at(part) if side == 'F.Cu' else None
    except (ValueError, TypeError, IndexError):
        pose = None
    courtyard = _courtyard(part, *pose) if pose is not None else ''
    footprint = None
    if side in layers and len(xy) == 2 and all(bounds[i] <= xy[i] <= bounds[i + 2] for i in range(2)):
        detail = f'{side} · ' + ('Courtyard outline' if courtyard else 'Position marker')
        if p.locked(part):
            detail += ' · Locked'
        footprint = BoardPoint(xy, (side,), uid, ref, detail, drawing=courtyard)
    if not show_pads or pose is None:
        return footprint, (), bool(pads)
    anchor, rotation = pose
    points = []
    for pad in pads:
        try:
            visible = _pad_layers(pad, layers)
            if visible:
                centre = tuple(value / 1_000_000 for value in world(at(pad)[0], anchor, rotation))
                if all(bounds[i] <= centre[i] <= bounds[i + 2] for i in range(2)):
                    hit, drawing, drill = _pad_shape(pad, centre, anchor, rotation)
                    label = f'{ref} pad {_display_text(sx.unquote(pad[1]), 24)}'
                    detail = ('Through-hole' if pad[2] == 'thru_hole' else 'Surface mount') if drawing else 'Centre marker · Shape omitted'
                    points.append(BoardPoint(centre, visible, _display_uuid(sx.one(pad, 'uuid')),
                                             label, detail, net_for(pad), hit, drawing, drill))
        except (ValueError, TypeError, IndexError, KeyError):
            continue
    return footprint, tuple(points), len(points) != len(pads)


def _workspace_context(board, *, layers=(), net_for=None):
    """Show saved edge geometry and part anchors in the passive view."""
    from . import placement_transform
    from experiments.placement_native_proposal_v1.contract import rectangle

    def on_outline(row):
        layer = sx.one(row, 'layer')
        return layer is not None and len(layer) == 2 and sx.unquote(layer[1]) == 'Edge.Cuts'

    try:
        edges = [row for row in board if isinstance(row, list) and row and on_outline(row)]
        cuts = [row for row in edges if row[0] == 'gr_circle']
        outer = [row for row in edges if row[0] != 'gr_circle']
        parts = sx.children(board, 'footprint')
        if any(on_outline(row) for part in parts for row in part[2:] if isinstance(row, list) and row):
            return None
        cutouts, paths = (), ()
        if len(outer) == 1 and outer[0][0] == 'gr_rect':
            exact_bounds = rectangle(outer[0])
            if cuts:
                from experiments.placement_native_proposal_v1 import ordinary

                holes = ordinary.circular_cutout_rows(cuts, exact_bounds, ordinary.stroke(outer[0]))
                cutouts = tuple(tuple(value / 1_000_000 for value in (*row['center_nm'], row['radius_nm']))
                                for row in holes)
        elif not cuts and len(edges) == 4 and all(row[0] == 'gr_line' for row in edges):
            chain = placement_transform.rectangular_edge_chain(board)
            exact_bounds = placement_transform.bbox([point for edge in chain for point in edge])
        elif not cuts and any(row[0] == 'gr_arc' for row in outer):
            bounds, paths = _edge_chain_drawing(outer)
        else:
            return None
        if not paths:
            bounds = tuple(value / 1_000_000 for value in exact_bounds)
        anchors = []
        pads, footprints = [], []
        partial = bool(layers and len(parts) > REFERENCE_LIMIT)
        if len(parts) <= REFERENCE_LIMIT:
            show_pads = bool(layers) and sum(len(sx.children(part, 'pad')) for part in parts) <= PAD_MARKER_LIMIT
            partial = bool(layers and not show_pads)
            if layers and net_for is None:
                net_for = _net_reader(board)
            for part in parts:
                ref = next((sx.unquote(row[2]) for row in sx.children(part, 'property')
                            if len(row) >= 3 and sx.unquote(row[1]) == 'Reference'), '')
                xy = tuple(float(value) for value in sx.one(part, 'at', [])[1:3])
                if (0 < len(ref) <= 16 and ref.isprintable() and len(xy) == 2
                        and all(bounds[i] <= xy[i] <= bounds[i + 2] for i in range(2))):
                    anchors.append((*xy, ref))
                if layers:
                    try:
                        feature, markers, omitted = _part_points(part, ref, xy, layers, bounds,
                                                                 net_for, show_pads=show_pads)
                    except (ValueError, TypeError, IndexError):
                        partial = True
                        continue
                    if feature is not None:
                        footprints.append(feature)
                    pads.extend(markers)
                    partial |= omitted
        return BoardDrawing(bounds, tuple(anchors), cutouts, paths, tuple(pads), tuple(footprints), partial)
    except (ValueError, TypeError, KeyError, IndexError):
        return None


def _route_point(row, layers, group, net_for, *, saved):
    kind = 'via' if row[0] == 'via' else 'track'
    role = 'Saved copper' if saved else {
        'retained': 'Retained copper', 'protected': 'Protected copper', 'added': 'New copper', 'removed': 'Removed copper',
    }[group]
    if p.locked(row):
        role += ' · Locked'
    hit, drill = (), 0
    if kind == 'via':
        xy = _coordinates(row, 'at', 2)
        (width,) = _coordinates(row, 'size', 1)
        if width > 0:
            hit = ('circle', width / 2)
        # A missing or unsupported drill leaves the via outline visible.
        try:
            (hole,) = _coordinates(row, 'drill', 1)
            if group != 'removed' and 0 < hole < width:
                drill = hole / 2
        except (TypeError, ValueError, IndexError):
            pass
        if not drill and group != 'removed':
            role += ' · Drill not shown'
    elif row[0] == 'segment':
        start, end = (_coordinates(row, key, 2) for key in ('start', 'end'))
        xy = tuple((start[i] + end[i]) / 2 for i in range(2))
        (width,) = _coordinates(row, 'width', 1)
        hit = ('line', start, end, max(0, width / 2))
    else:
        xy = _coordinates(row, 'mid', 2)
        role += ' · Arc midpoint marker'
    detail = f'{role} · {xy[0]:.3f}, {xy[1]:.3f} mm'
    return kind, BoardPoint(xy, tuple(layers), _display_uuid(sx.one(row, 'uuid')),
                            detail=detail, net=net_for(row), hit=hit, drill=drill)


def _project_items(points, scale, tx, ty):
    points = points[:WORKSPACE_ITEM_LIMIT]
    identities = Counter(point.identity for _, point in points)
    order = Counter()
    result = []
    for i, (kind, point) in enumerate(points, 1):
        order[kind] += 1
        identity = point.identity if point.identity and identities[point.identity] == 1 else f'{kind}:{i}'
        label = point.label or f'{kind.capitalize()} {order[kind]}' + (f' · {point.net}' if point.net else '')
        x, y = point.xy
        result.append({'id': identity, 'label': label, 'detail': point.detail, 'kind': kind, 'net': point.net,
                       'point': (x * scale + tx, y * scale + ty), '_hit': point.hit})
    return tuple(result)


def routing_diagrams(changes, layers, *, workspace=False, board_context=None, net_for=None, saved=False):
    """Show the route diff at a common scale. Native plots retain full copper."""
    if sum(map(len, changes.values())) > 8000:
        return {}, 'This board is too large for the route diagrams. Compare the KiCad plots below.'
    shapes = {layer: defaultdict(list) for layer in layers}
    routes_by_layer = {layer: [] for layer in layers}
    net_for = net_for or (lambda _: '')
    points = []
    try:
        for group, routes in changes.items():
            for row in routes:
                on_layers, extents, drawing = _route_shape(row, layers)
                points.extend(extents)
                item = _route_point(row, on_layers, group, net_for, saved=saved) if workspace else None
                for layer in on_layers:
                    shapes[layer][group].append(drawing)
                    if item is not None:
                        routes_by_layer[layer].append(item)
    except (ValueError, TypeError, KeyError, IndexError):
        return {}, 'Some route geometry cannot be drawn here. Compare the exact KiCad plots below.'
    if board_context is not None:
        bounds = board_context.bounds
        points.extend((bounds[:2], bounds[2:]))
    if not points:
        return {}, 'There are no routed tracks or vias to draw.'
    x, y = zip(*points)
    margin = max(max(x) - min(x), max(y) - min(y), 1) * .06 + 1
    width = max(x)-min(x)+2*margin
    height = max(y)-min(y)+2*margin
    left, top = min(x) - margin, min(y) - margin
    view_box = f'{left} {top} {width} {height}'
    diagrams = {}
    for layer in layers:
        if workspace:
            size = (840, max(1, round(840 * height / width))) if width >= height else (max(1, round(840 * width / height)), 840)
            routes = ''.join(f'<g stroke="{WORKSPACE_COLORS[group]}" stroke-width="0.16"'
                           + (' stroke-dasharray="0.55 0.4"' if group == 'removed' else '')
                           + f'>{"".join(shapes[layer][group])}</g>'
                           for group in ('removed', 'retained', 'protected', 'added'))
            # A common board-to-SVG transform keeps pad and finding marks on
            # the same geometry at every layer and canvas size.
            scale = min(size[0] / width, size[1] / height)
            tx = (size[0] - width * scale) / 2 - left * scale
            ty = (size[1] - height * scale) / 2 - top * scale
            outline, courts, pads, labels = '', '', '', ''
            items = []
            drills = [point for _, point in routes_by_layer[layer] if point.drill]
            if board_context is not None:
                if board_context.edge_paths:
                    outline = ''.join(f'<path d="{path}" stroke="#7c8d9e" stroke-width="{1.8/scale}" '
                                      'data-role="board-edge"/>' for path in board_context.edge_paths)
                else:
                    x0, y0, x1, y1 = bounds
                    outline = (f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" '
                               f'fill="#edf2f6" stroke="#7c8d9e" stroke-width="{1.8/scale}"/>')
                    outline += ''.join(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="#fff" stroke="#7c8d9e" '
                                       f'stroke-width="{1.4/scale}" data-role="board-cutout"/>'
                                       for x, y, radius in board_context.cutouts)
                # The reference and its location are useful on the other side;
                # the qualified courtyard is drawn only on its own side.
                visible_parts = board_context.footprints
                visible_pads = [item for item in board_context.pads if layer in item.layers]
                courts = ''.join(item.drawing for item in visible_parts if layer in item.layers)
                pads = ''.join(item.drawing or f'<circle data-role="pad-centre" cx="{item.xy[0]}" cy="{item.xy[1]}" '
                               f'r="{3.8/scale}" fill="#c1a16f" fill-opacity=".7"/>' for item in visible_pads)
                drills.extend(item for item in visible_pads if item.drill)
                items.extend(('component', item) for item in visible_parts)
                items.extend(('pad', item) for item in visible_pads)
                for px, py, ref in board_context.anchors:
                    cx, cy = px * scale + tx, py * scale + ty
                    labels += (f'<circle cx="{cx}" cy="{cy}" r="2.7" fill="#435568"/>'
                               f'<text x="{cx+5}" y="{cy-5}" font-size="15" fill="#36495c">{escape(ref)}</text>')
            holes = ''.join(f'<circle data-role="drill" cx="{item.xy[0]}" cy="{item.xy[1]}" '
                            f'r="{item.drill}" fill="white"/>' for item in drills)
            items.extend(routes_by_layer[layer])
            body = f'<g transform="matrix({scale} 0 0 {scale} {tx} {ty})">{outline}{courts}{pads}{routes}{holes}</g>{labels}'
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" height="{size[1]}" '
                   f'viewBox="0 0 {size[0]} {size[1]}" fill="none" stroke-linecap="round">{body}</svg>')
            if len(svg.encode('utf-8')) > WORKSPACE_SVG_LIMIT:
                return {}, 'Route drawing exceeds the workspace size limit. Compare the KiCad plots below.'
            diagrams[layer] = {'svg': svg, 'size': size, 'mm_to_svg': (scale, tx, ty),
                               'items': _project_items(items, scale, tx, ty),
                               'items_omitted': max(0, len(items) - WORKSPACE_ITEM_LIMIT)}
        else:
            body = ''.join(f'<g class="{group}">{"".join(shapes[layer][group])}</g>'
                           for group in ('removed', 'retained', 'added'))
            diagrams[layer] = (f'<svg viewBox="{view_box}" role="img" aria-label="{escape(layer)} route changes" '
                               f'fill="none" stroke-linejoin="round" stroke-linecap="round">{body}</svg>')
    return diagrams, ''


def _workspace_drawing(board, changes, layers, *, saved=False):
    net_for = _net_reader(board)
    context = _workspace_context(board, layers=layers, net_for=net_for)
    if saved and context is None:
        return context, {}, 'The saved board outline cannot be drawn here.'
    drawings, note = routing_diagrams(changes, layers, workspace=True, board_context=context,
                                      net_for=net_for, saved=saved)
    return context, drawings, note


def _drawing_note(context, diagrams, *, saved=False):
    notes = []
    if context is None:
        notes.append('Board outline and part geometry are unavailable in this view.')
    else:
        if any(not footprint.drawing for footprint in context.footprints):
            notes.append('Parts without a supported courtyard use position markers.')
        if context.partial_pad_context:
            notes.append('Some pad centres are omitted.')
        if any(not pad.drawing for pad in context.pads):
            notes.append('Some pads show only a centre marker.')
    if any(scene['items_omitted'] for scene in diagrams.values()):
        notes.append(f'The item list shows up to {WORKSPACE_ITEM_LIMIT} items per layer.')
    notes.append('View zone fill in KiCad.' if saved else 'See Detailed report for pad shapes and zone fill.')
    return ' '.join(notes)


def saved_workspace(inspection):
    """Passive geometry for the exact inspected saved board, with no authority."""
    raw = pc.read_bytes(Path(inspection['source']), 8 * 1024 * 1024)
    if hashlib.sha256(raw).hexdigest() != inspection['source_sha256']:
        raise p.Rejected('Saved board changed before drawing. Refresh the inspection.')
    tree = sx.parse(raw.decode('utf-8'))
    layers = [sx.unquote(row[1]) for row in sx.one(tree, 'layers', [])[1:]
              if isinstance(row, list) and len(row) >= 3 and sx.unquote(row[1]).endswith('.Cu')]
    if len(layers) not in (2, 4) or len(layers) != len(set(layers)) or 'F.Cu' not in layers:
        context, diagrams, note = None, {}, 'This saved layer stack cannot be drawn here.'
    else:
        context, diagrams, note = _workspace_drawing(tree, {'retained': p.routes(tree)}, layers, saved=True)
    return {'diagrams': diagrams, 'note': note, 'caption': 'Saved board', 'counts': None,
            'context_note': _drawing_note(context, diagrams, saved=True), 'findings': (), 'findings_omitted': 0}


def saved_board_front(inspection):
    return saved_workspace(inspection)['diagrams'].get('F.Cu')


def _finding_ids(row):
    items = row.get('items')
    if type(items) is not list or not 1 <= len(items) <= FINDING_ITEM_LIMIT:
        return ()
    identities = tuple(_display_uuid(['uuid', item.get('uuid')]) if type(item) is dict else ''
                       for item in items)
    return identities if all(identities) and len(set(identities)) == len(identities) else ()


def _finding_anchors(board, context, layers, wanted):
    if not wanted:
        return {}
    # Count matches even in objects we cannot draw. An ambiguous UUID may
    # never select the one drawable item that happens to share it.
    matches, remaining = Counter(), [board]
    while remaining:
        node = remaining.pop()
        if node[0] == 'uuid' and len(node) >= 2 and type(node[1]) is str and len(node[1]) in (36, 38):
            identity = sx.unquote(node[1]).lower()
            if identity in wanted:
                matches[identity] += 1
        remaining.extend(child for child in node[1:] if type(child) is list and child)
    unique = {identity for identity in wanted if matches[identity] == 1}
    anchors = {point.identity: point for point in (*context.footprints, *context.pads)
               if point.identity in unique} if context is not None else {}
    for route in p.routes(board):
        try:
            identity = _display_uuid(sx.one(route, 'uuid'))
            if identity not in unique:
                continue
            visible, _, _ = _route_shape(route, layers)
            point = _coordinates(route, 'at' if route[0] == 'via' else 'start', 2)
        except (ValueError, TypeError, IndexError):
            continue
        anchors[identity] = BoardPoint(point, tuple(visible), identity)
    return anchors


def _workspace_findings(board, context, diagrams, route):
    native = route.get('native') or route.get('saved_native_findings') or route.get('final_drc')
    rows = native.get('findings') if type(native) is dict else None
    if type(rows) is not list:
        return (), 0
    identities = [_finding_ids(row) if type(row) is dict else () for row in rows[:FINDING_LIMIT]]
    wanted = {identity for group in identities for identity in group}
    layers = tuple(diagrams)
    anchors = _finding_anchors(board, context, layers, wanted) if layers else {}
    findings = []
    for index, group in enumerate(identities):
        row = rows[index] if type(rows[index]) is dict else {}
        description = row.get('description')
        if type(description) is not str or not description.strip():
            description = 'KiCad finding'
        printable = ''.join(char if char.isprintable() else ' ' for char in description[:160])
        label = f"{index + 1}. " + ' '.join(printable.split())
        points = tuple(anchors[identity] for identity in group) if all(identity in anchors for identity in group) else ()
        visible = tuple(layer for layer in layers if any(layer in point.layers for point in points))
        findings.append({'index': index, 'label': label, 'layers': visible, 'points': points})
    return tuple(findings), max(0, len(rows) - FINDING_LIMIT)


def _with_overlay(scene, marks):
    svg = scene['svg'][:-len('</svg>')] + ''.join(marks) + '</svg>'
    return {**scene, 'svg': svg} if len(svg.encode('utf-8')) <= WORKSPACE_SVG_LIMIT else scene


def _highlight(scene, points, role):
    marks = (f'<circle data-role="{role}" cx="{x}" cy="{y}" r="10" fill="none" stroke="#fff" stroke-width="6"/>'
             f'<circle cx="{x}" cy="{y}" r="10" fill="none" stroke="#176cba" stroke-width="2.8"/>'
             for x, y in points)
    return _with_overlay(scene, marks)


def finding_scene(render, layer, index=None):
    """Return the checked review layer with an optional passive board marker."""
    scene = render['diagrams'][layer]
    if index is None or type(index) is not int or not 0 <= index < len(render['findings']):
        return scene
    row = render['findings'][index]
    if layer not in row['layers']:
        return scene
    scale, tx, ty = scene['mm_to_svg']
    points = [(point.xy[0] * scale + tx, point.xy[1] * scale + ty)
              for point in row['points'] if layer in point.layers]
    return _highlight(scene, points, 'finding-location')


def _item_distance(item, point, transform):
    scale, tx, ty = transform
    cx, cy = item['point']
    shape = item['_hit']
    x, y = (point[0] - cx) / scale, (point[1] - cy) / scale
    if not shape:
        return math.hypot(x, y) * scale
    kind = shape[0]
    if kind == 'circle':
        return max(0, math.hypot(x, y) - shape[1]) * scale
    if kind == 'line':
        start, end, half_width = shape[1:]
        dx, dy = end[0] - start[0], end[1] - start[1]
        px, py = (point[0] - tx) / scale - start[0], (point[1] - ty) / scale - start[1]
        fraction = min(1, max(0, (px * dx + py * dy) / (dx * dx + dy * dy))) if dx or dy else 0
        return max(0, math.hypot(px - fraction * dx, py - fraction * dy) - half_width) * scale
    half_width, half_height, angle, radius = shape[1:]
    local_x, local_y = {0: (x, y), -90: (-y, x), -180: (-x, -y), -270: (y, -x)}[angle]
    dx, dy = abs(local_x) - half_width + radius, abs(local_y) - half_height + radius
    outside = math.hypot(max(0, dx), max(0, dy)) + min(0, max(dx, dy)) - radius
    return max(0, outside) * scale


def pick_item(scene, point, tolerance):
    """Pick one visible item in SVG units, deferring an ambiguous hit."""
    items = scene.get('items', ())
    if not items:
        return None
    width, height = scene['size']
    if (type(point) not in (tuple, list) or len(point) != 2
            or any(type(value) not in (int, float) or not 0 <= value <= extent
                   for value, extent in zip(point, (width, height)))
            or type(tolerance) not in (int, float) or not 0 <= tolerance <= max(width, height)):
        return None
    matches = []
    for item in items:
        distance = _item_distance(item, point, scene['mm_to_svg'])
        if distance <= tolerance:
            # Copper can terminate under a pad. Prefer a pad actually hit
            # over the route endpoint; nearby pad markers get no preference.
            rank = (0 if item['kind'] == 'pad' and item['_hit'] else
                    1 if item['_hit'] else 2) if distance <= 1e-8 else 3
            matches.append((rank, distance, item['id']))
    if not matches:
        return None
    matches.sort()
    rank, distance, identity = matches[0]
    if len(matches) > 1 and matches[1][0] == rank and matches[1][1] - distance <= .5:
        return None
    return identity


def inspect_item(scene, identity):
    """Highlight one display identity, leaving the unselected scene intact."""
    for item in scene.get('items', ()):
        if item['id'] == identity:
            return _highlight(scene, (item['point'],), 'inspected-item')
    return scene


def inspect_net(scene, name):
    """Trace straight copper and mark other displayed items of one exact net."""
    marks = []
    for item in scene.get('items', ()):
        if not name or item['net'] != name:
            continue
        attrs = 'data-role="inspected-net-item" stroke="#176cba" stroke-width="2.4" fill="none"'
        hit = item.get('_hit', ())
        if hit and hit[0] == 'line':
            scale, tx, ty = scene['mm_to_svg']
            (x1, y1), (x2, y2) = hit[1:3]
            marks.append(f'<path {attrs} d="M {x1 * scale + tx} {y1 * scale + ty} '
                         f'L {x2 * scale + tx} {y2 * scale + ty}"/>')
        else:
            x, y = item['point']
            marks.append(f'<circle {attrs} cx="{x}" cy="{y}" r="5"/>')
    return _with_overlay(scene, marks) if marks else scene


def workspace_changes(directory, source_board, review, route):
    """Draw a passive view of the same captured boards as the rendered review."""
    board = Path(review['board'])
    project = Path(directory) / 'project'
    if board.parent != project or board.suffix != '.kicad_pcb':
        raise p.Rejected('Workspace review board identity differs.')
    before_bytes = pc.read_bytes(Path(directory) / 'before' / source_board.name, 8 * 1024 * 1024)
    after_bytes = pc.read_bytes(board, 8 * 1024 * 1024)
    if (hashlib.sha256(before_bytes).hexdigest() != review['source_project_hashes'][source_board.name]
            or hashlib.sha256(after_bytes).hexdigest() != review['candidate_sha256']):
        raise p.Rejected('Workspace review boards changed.')
    candidate_digest = review['candidate_sha256']
    if ('candidate_sha256' in route and route['candidate_sha256'] != candidate_digest
            or 'verified_candidate_sha256' in review and review['verified_candidate_sha256'] != candidate_digest):
        raise p.Rejected('Workspace review candidate differs from the checked routing receipt.')
    before, after = (sx.parse(data.decode('utf-8')) for data in (before_bytes, after_bytes))
    changes = route_changes(before, after)
    protected = Counter(f.canonical(row) for row in p.protected_for_record(route, before))
    changes['protected'] = []
    keep = []
    for row in changes['retained']:
        key = f.canonical(row)
        if protected[key]:
            changes['protected'].append(row)
            protected[key] -= 1
        else:
            keep.append(row)
    if +protected:
        raise p.Rejected('Workspace review does not show every protected track or via.')
    changes['retained'] = keep
    layers = review['preview']['layers']
    context, diagrams, note = _workspace_drawing(after, changes, layers)
    caption = 'Copper changes, parts and pads' if context and context.pads else (
        'Copper changes and part locations' if context and context.anchors else (
            'Board outline and route changes' if context else 'Tracks and vias only · board detail in report'))
    context_note = _drawing_note(context, diagrams)
    bound = route.get('candidate_sha256') == candidate_digest
    findings, omitted = _workspace_findings(after, context, diagrams if bound else {}, route)
    return {'diagrams': diagrams, 'note': note, 'caption': caption,
            'counts': {key: len(rows) for key, rows in changes.items()},
            'context_note': context_note, 'findings': findings, 'findings_omitted': omitted}


def display_svg(raw):
    """Remove only KiCad's observed standard declaration, without DTD loading."""
    without_declaration = re.sub(rb'\A(?:\xef\xbb\xbf)?<\?xml\s+[^?]*\?>', b'', raw, count=1)
    if b'<?' in without_declaration:
        raise p.Rejected('SVG processing instructions are unsupported')
    if b'<!ENTITY' in raw.upper():
        raise p.Rejected('external SVG declarations are unsupported')
    clean, count = KICAD_DOCTYPE.subn(b'', raw)
    if count > 1 or b'<!DOCTYPE' in clean.upper():
        raise p.Rejected('external SVG declarations are unsupported')
    return clean


def svg_bytes(path):
    raw = pc.read_bytes(path, 8 * 1024 * 1024)
    # Native plots are displayed as images, not inserted into the HTML DOM.
    # Reject active content or linked resources even if a plot is replaced.
    root = element_tree.fromstring(display_svg(raw))
    if root.tag != '{http://www.w3.org/2000/svg}svg':
        raise p.Rejected('native plot is not SVG')
    for node in root.iter():
        if node.tag.split('}')[-1] in {'script', 'foreignObject', 'image', 'use', 'style', 'animate', 'animateMotion', 'animateTransform', 'set', 'discard'}:
            raise p.Rejected('active or linked SVG content is unsupported')
        for key, value in node.attrib.items():
            if key.split('}')[-1].lower().startswith('on') or 'href' in key.lower() or 'url(' in value.lower():
                raise p.Rejected('linked SVG attribute is unsupported')
    return raw


def write_bound(path, raw):
    expected = hashlib.sha256(raw).hexdigest()
    path.write_bytes(raw)
    if p.sha(path) != expected:
        raise p.Rejected('preview output differs from intended bytes')
    return expected


def check_experimental_preview(destination, preview, native_toolchain=None, experimental_schematic_parity=False, *, comparison_context=None):
    """Replay existing SVG process/PRL proofs using only caller-selected tools."""
    if native_toolchain is None and comparison_context is None:
        _preview_request(destination,preview)
        return
    return _check_preview(destination,preview,native_toolchain,experimental_schematic_parity,
                          comparison_context=comparison_context)


def check_native_preview(destination, preview):
    """Replay normal SVG proofs against the current pinned native plotter.

    This supplies no routing or delivery authority. The caller must have
    checked its exact original receipt and complete review material first.
    """
    return _check_preview(destination,preview)


def _preview_request(destination, preview, native_toolchain=None, experimental_schematic_parity=False, *, comparison_context=None):
    from . import handoff as h
    h.application_kwargs(native_toolchain, experimental_schematic_parity, comparison_context)
    h.check_delivery_context(preview, native_toolchain, experimental_schematic_parity, comparison_context=comparison_context)
    from . import comparison as cmp
    cmp.delivery_path(Path(destination).absolute(),comparison_context,'review')
    if comparison_context is None and type(preview.get('html')) is str and cmp.marked(Path(preview['html']).parent):
        raise p.Rejected('comparison preview origin requires its caller context')


def _check_preview(destination, preview, native_toolchain=None, experimental_schematic_parity=False, *, comparison_context=None):
    from . import handoff as h, comparison as cmp
    _preview_request(destination,preview,native_toolchain,experimental_schematic_parity,
                     comparison_context=comparison_context)
    plotter=native_toolchain.cli if native_toolchain is not None else c.CLI
    if native_toolchain is not None:plotter_sha=native_toolchain.cli_sha256
    elif comparison_context is not None:plotter_sha=comparison_context.tools['files'][str(plotter)]
    else:
        pin=p.selected_tool_pins()['kicad_cli']
        if (c.resolve_tool_path(pin['path'])!=plotter or p.sha(plotter)!=pin['sha256']
                or plotter.stat().st_size!=pin['bytes']):
            raise p.Rejected('normal preview requires the current pinned plotter')
        plotter_sha=pin['sha256']
    destination = h.real_path(destination)
    before = pc.inventory(destination / 'before')
    boards = ([comparison_context.source.name] if comparison_context is not None else
        [name for name in before if Path(name).suffix == '.kicad_pcb'])
    if comparison_context is not None and before!=comparison_context.source_hashes:raise p.Rejected('comparison preview original source differs')
    if len(boards) != 1 or Path(boards[0]).name != boards[0]:
        raise p.Rejected('experimental preview needs one exact original PCB')
    board = boards[0]; tree = sx.read(destination / 'before' / board)
    layers = [sx.unquote(x[1]) for x in sx.one(tree, 'layers')[1:]
              if isinstance(x, list) and len(x) > 2 and re.fullmatch(r'(F|B|In[0-9]+)\.Cu', sx.unquote(x[1]))]
    if (len(layers) not in (2, 4) or len(set(layers)) != len(layers)
            or preview.get('layers') != layers or preview.get('plotter') != str(plotter)
            or preview.get('plotter_sha256') != plotter_sha):
        raise p.Rejected('experimental preview layers or caller plotter differ')
    root = destination / 'plot-work'; pairs = []; names = []; required = {'preview.html'}
    for layer in layers:
        for label in ('before', 'after'):
            name = label + '-' + layer; names.append(name)
            source = destination / ('before' if label == 'before' else 'project') / board
            work = root / (name + '-input'); target = root / 'native-plots' / (name + '.svg')
            required.update(str(path.relative_to(destination)) for path in (root / (name + '-input-binding.json'),
                root / (name + '-process.json'), root / (name + '.log'), target, root / 'plots' / (name + '.svg')))
            binding = f.read_json(root / (name + '-input-binding.json'))
            if (binding.get('source') != str(source) or binding.get('input') != str(work / board)
                    or binding.get('saved') is not False or binding.get('local_settings_policy') != ls.JOB_POLICY
                    or binding.get('before') != pc.inventory(source.parent)
                    or binding.get('after') != pc.inventory(work)
                    or preview.get('input_trees', {}).get(str(work.relative_to(destination))) != binding['after']):
                raise p.Rejected('experimental preview input binding changed')
            required.update(str((work / key).relative_to(destination)) for key in binding['after'])
            p.check_drc_project(binding['before'], binding['after'], board)
            argv = [*f.SANDBOX, str(plotter), 'pcb', 'export', 'svg', '--mode-single',
                    '--layers', layer + ',Edge.Cuts', '--fit-page-to-board', '--exclude-drawing-sheet',
                    '--output', str(target), str(work / board)]
            process = f.process_check(root, preview, name, argv)
            if (process.get('local_settings_policy') != ls.JOB_POLICY
                    or process.get('log') != str(root / (name + '.log'))
                    or process.get('log_truncated') is not False
                    or len(pc.read_bytes(root / (name + '.log'), 512 * 1024)) != process.get('log_bytes')):
                raise p.Rejected('experimental preview process/log binding changed')
            ls.check_event(root, binding, process)
            pairs.append((binding, process))
    if ([step.get('name') for step in preview.get('steps', [])] != names
            or set(preview.get('input_trees', {})) != {str((root / (name + '-input')).relative_to(destination)) for name in names}):
        raise p.Rejected('experimental preview stage census differs')
    if (set(preview.get('files', {})) != required or preview.get('html') != str(destination / 'preview.html')
            or preview.get('native_validation_performed') is not False or preview.get('zone_refill_performed') is not False):
        raise p.Rejected('experimental preview proof file census differs')
    p.experimental_native_version(native_toolchain)
    if comparison_context is not None:cmp.require_context(comparison_context)
    elif native_toolchain is None and p.sha(plotter)!=plotter_sha:
        raise p.Rejected('normal preview plotter changed during readback')
    # Flags and link counts are not byte hashes. Recheck after the last tool read.
    for binding, process in pairs:
        ls.check_event(root, binding, process)
    return [(root, binding, process) for binding, process in pairs]


def render(destination, source, candidate, report, remaining, material, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Called inside handoff's existing bounded freshness/publication transaction."""
    destination = Path(destination)
    from . import handoff as h
    ctx = h.delivery_kwargs(native_toolchain, experimental_schematic_parity)
    app=h.application_kwargs(native_toolchain,experimental_schematic_parity,comparison_context)
    from . import comparison as cmp
    cmp.delivery_path(destination,comparison_context,'review')
    if comparison_context is None and any(cmp.marked(Path(path).parent) for path in (source,candidate)):
        raise p.Rejected('comparison render inputs require their caller context')
    if comparison_context is not None and any(h.real_path(path)!=destination/folder/comparison_context.source.name
            for path,folder in ((source,'before'),(candidate,'project'))):
        raise p.Rejected('comparison render inputs differ from exact review copies')
    if comparison_context is not None or cmp.marked(destination,report):
        h.review_policy(report,comparison_context.output if comparison_context is not None else destination,**app)
    if native_toolchain is None:
        pin = p.selected_tool_pins()['kicad_cli']
        plotter = c.CLI
        if (c.resolve_tool_path(pin['path']) != plotter or p.sha(plotter) != pin['sha256']
                or plotter.stat().st_size != pin['bytes']):
            raise p.Rejected('pinned KiCad plotter changed')
    else:
        plotter = native_toolchain.cli
        pin = {'sha256': native_toolchain.cli_sha256}
    tree = sx.read(source)
    layers = [sx.unquote(x[1]) for x in sx.one(tree, 'layers')[1:]
              if isinstance(x, list) and len(x) > 2 and re.fullmatch(r'(F|B|In[0-9]+)\.Cu', sx.unquote(x[1]))]
    if len(layers) not in (2, 4) or len(layers) != len(set(layers)):
        raise p.Rejected('review plots require two or four distinct copper layers')
    job = f.FloorJob(destination / 'plot-work', remaining(), remaining, protect_local_settings=True, **ctx)
    plots = job.out / 'plots'; plots.mkdir()
    native_plots = job.out / 'native-plots'; native_plots.mkdir()
    rows = []; frozen = {}; input_trees = {}
    def stable():
        material()
        for directory, expected in input_trees.items():
            if pc.inventory(directory) != expected:
                raise p.Rejected('completed preview input file set changed')
        for name, expected in frozen.items():
            if p.sha(destination / name) != expected:
                raise p.Rejected('completed preview stage changed')
    for layer in layers:
        images = []
        for label, board in [('before', source), ('after', candidate)]:
            name = label + '-' + layer
            work = job.out / (name + '-input')
            before = pc.inventory(board.parent)
            pc.copy_project(board.parent, work)
            if pc.inventory(work) != before:
                raise p.Rejected('native plot input copy differs')
            target = native_plots / (name + '.svg')
            process = ls.protected_step(job, name, [plotter, 'pcb', 'export', 'svg', '--mode-single',
                     '--layers', layer + ',Edge.Cuts', '--fit-page-to-board', '--exclude-drawing-sheet',
                     '--output', target, work / board.name])
            after = pc.inventory(work)
            p.check_drc_project(before, after, board.name)
            input_trees[work] = after
            for relative, digest in after.items():
                frozen[str((work / relative).relative_to(destination))] = digest
            binding = job.out / (name + '-input-binding.json')
            payload = {'source': str(board), 'input': str(work / board.name), 'before': before, 'after': after,
                       'saved': False, 'local_settings_policy': ls.JOB_POLICY}
            ls.check_event(job.out, payload, process)
            frozen[str(binding.relative_to(destination))] = write_bound(binding, (json.dumps(payload, indent=2) + '\n').encode())
            native_raw = svg_bytes(target)
            frozen[str(target.relative_to(destination))] = hashlib.sha256(native_raw).hexdigest()
            display = plots / target.name
            frozen[str(display.relative_to(destination))] = write_bound(display, display_svg(native_raw))
            for path in (job.out / (label + '-' + layer + '.log'),
                         job.out / (label + '-' + layer + '-process.json')):
                frozen[str(path.relative_to(destination))] = p.sha(path)
            stable()
            images.append('<figure><figcaption>' + ('Routing input' if label == 'before' else 'Candidate') +
                          '</figcaption><img alt="' + escape(label + ' ' + layer, quote=True) +
                          '" src="plot-work/plots/' + target.name + '"></figure>')
        rows.append('<section><h2>' + escape(layer) + '</h2><div class="pair">' + ''.join(images) + '</div></section>')
    native = report.get('final_drc', report.get('native', {}))
    source_native = report.get('source_drc')
    if not isinstance(source_native, dict):
        source_native = {}
    metrics = report.get('metrics', {})
    summary = {key: native.get(key) for key in ('opens', 'blocking', 'warnings', 'exclusions')}
    ignored = native.get('ignored_checks')
    length = metrics.get('track_length_mm')
    summary_rows = [('Open connections', summary['opens']), ('Blocking findings', summary['blocking']),
                    ('Warnings', summary['warnings']), ('Exclusions', summary['exclusions']),
                    ('Ignored checks', len(ignored) if isinstance(ignored, list) else None),
                    ('Saved input opens', source_native.get('opens')),
                    ('Candidate track length', format(length, '.6f') + ' mm' if type(length) in (int, float) else None),
                    ('Candidate vias', metrics.get('vias'))]
    saved_summary = ('<section><h2>Saved routing-check summary</h2>'
                     '<p>KiCad counts opens after zone refill on the saved input and the candidate. '
                     'The PCB Editor may show a different count before its zones are refilled.</p>'
                     '<dl class="saved-summary">') + ''.join(
        '<dt>' + escape(label) + '</dt><dd>' + escape(str(value) if value is not None else 'Not recorded') + '</dd>'
        for label, value in summary_rows) + '</dl></section>'
    candidate_tree = sx.read(candidate)
    changes = route_changes(tree, candidate_tree)
    diagrams, drawing_note = routing_diagrams(changes, layers)
    legend = (('added', 'Added or changed'), ('retained', 'Retained'), ('removed', 'Removed or replaced'))
    routing = ('<section id="changes"><h2>Copper changes</h2><ul class="legend">'
               + ''.join(f'<li class="key-{key}">{label} <strong>{len(changes[key])}</strong></li>'
                         for key, label in legend)
               + '</ul><p>Counts compare exact track and via records with the saved routing input. '
               'Pads and zone fill are separate and appear in the full KiCad plots. '
               'For placement tasks, review component moves in Copperpath.</p>'
               + (f'<p>{escape(drawing_note)}</p>' if drawing_note else '')
               + '<div class="pair">' + ''.join(f'<figure><figcaption>{escape(layer)}</figcaption>{svg}</figure>'
                                                 for layer, svg in diagrams.items()) + '</div></section>')
    zone_fill_counts = [sum(len(sx.children(zone, field)) for zone in sx.children(board_tree, 'zone')
                            for field in p.DERIVED_ZONE) for board_tree in (tree, candidate_tree)]
    # The receipt schema is checked centrally by handoff; keep absent fields
    # explicit rather than inventing zero findings for another policy.
    details = escape(json.dumps({'saved_native_findings': summary,
                                'findings': native.get('findings', 'See original receipt'),
                                'candidate_metrics': metrics,
                                'ignored_checks': native.get('ignored_checks', 'See original receipt')}, indent=2))
    html = ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\'; style-src \'unsafe-inline\'">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Routing review</title>'
            '<style>body{font:16px/1.5 system-ui;margin:clamp(1rem,3vw,2.5rem) auto;padding:0 1rem;max-width:1140px;color:#17212b;background:#f7f8fa}'
            'h1,h2{line-height:1.2;margin:.5rem 0}p{max-width:80ch;margin:.55rem 0 1rem}section,details{margin:1.15rem 0}'
            '.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.75rem}'
            'figure,details{margin:0;padding:.75rem;background:white;border:1px solid #ccd2db;border-radius:8px}'
            'img,svg{width:100%;height:auto;display:block}figcaption{font-weight:650;margin-bottom:.4rem}'
            'pre{white-space:pre-wrap;overflow-wrap:anywhere}small{color:#4f6072}details{margin:.5rem 0}'
            'details li{margin:.45rem 0}summary{overflow-wrap:anywhere}'
            '.legend{display:flex;flex-wrap:wrap;gap:.5rem 1.2rem;margin:.75rem 0;padding:0;list-style:none}'
            '.legend li{border-left:.3rem solid;padding-left:.5rem}.key-added{color:#07695a}'
            '.key-retained{color:#54687c}.key-removed{color:#9c4823}'
            '.added{stroke:#007662}.retained{stroke:#74879a}.removed{stroke:#b95023;stroke-dasharray:.55 .4}'
            'svg circle{stroke-width:.16;fill:white}.legend strong{margin-left:.25rem}'
            '.saved-summary{display:grid;grid-template-columns:max-content 1fr;gap:.25rem 1rem}'
            '.saved-summary dt{font-weight:600}.saved-summary dd{margin:0}summary{cursor:pointer}'
            '@media(max-width:700px){.pair{grid-template-columns:1fr}}</style>'
            '<h1>Routing review</h1><p>' + escape(candidate.name) + '</p>'
            '<nav><a href="#changes">Copper changes</a> · <a href="#findings">Findings</a> · '
            '<a href="#full-copper">Full KiCad plots</a></nav>' + saved_summary + routing +
            '<section id="findings"><h2>Findings</h2>'
            '<p>Review every warning before accepting. A source match means the same finding was recorded by the saved input check. '
            'That check may cover fewer rules than the final check.</p>' + findings_html(native, source_native) + '</section>' +
            '<details id="full-copper"><summary>Full KiCad plots with pads and zone fill</summary>'
            f'<p>Saved zone fill records: {zone_fill_counts[0]} in the input and {zone_fill_counts[1]} in the candidate. '
            'The plotting step preserves the saved fills and runs no new checks. In particular, plotting does not refill zones or perform DRC.</p>' +
            ''.join(rows) + '</details>' +
            '<p>Use the separate review project for a closer look in KiCad. Close it before accepting or rejecting. Edits require fresh validation. '
            'Recorded routing acceptance is not electrical or manufacturing approval.</p>' +
            '<details id="saved-details"><summary>All saved findings, ignored checks and candidate metrics (structured details)</summary><pre>' + details +
            '</pre></details></html>')
    frozen['preview.html'] = write_bound(destination / 'preview.html', html.encode())
    stable()
    if p.sha(plotter) != pin['sha256']:
        raise p.Rejected('KiCad plotter changed during rendering')
    result = {'plotter': str(plotter), 'plotter_sha256': pin['sha256'], 'layers': layers, 'steps': job.steps,
            'html': str(destination / 'preview.html'), 'native_validation_performed': False,
            'zone_refill_performed': False, 'rendered_input_routes': len(p.routes(tree)),
            'display_derivation': 'Exact native SVG bytes with only the observed standard SVG1.1 DOCTYPE removed; raw native plots retained separately. No external DTD or entity is loaded.',
            'input_trees': {str(directory.relative_to(destination)): expected for directory, expected in input_trees.items()},
            'files': frozen}

    if native_toolchain is not None or comparison_context is not None:
        result.update(h.delivery_record(**app))
        check_experimental_preview(destination, result, **app)
    return result
