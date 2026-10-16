"""Prospective same-BOARD net-tie observations; no acceptance or policy change.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2026 KiCad-Autorouter contributors.
No pcbnew import, board load/save/refill, engine, or I/O at import time. The
caller supplies pinned Native10.0.0 and owns process/source/tool bindings.
"""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import uuid

from autorouter import board_floor, padless_alias, padless_alias_native, sexpr as sx
from autorouter.floor_context import canonical_path
from autorouter.placement_clearance import read_bytes
from experiments.pic_custom_observer_v1.mapping import dsn_correspondence

POLICY = 'experimental-net-tie-contact-observer-v1'
MAX_SOURCE = 2 * 1024**2
MAX_DSN = 20 * 1024**2
CAPS = {'footprints': 64, 'pads': 256, 'tie_footprints': 2,
        'groups_per_footprint': 1, 'pads_per_group': 3, 'bridges': 3}
OFFICIAL_SEMANTICS = {
    'url': 'https://gitlab.com/kicad/code/kicad/-/blob/10.0.0/pcbnew/footprint.cpp',
    'functions': ['MapPadNumbersToNetTieGroups', 'GetNetTiePads'],
    'interpretation': 'Group index starts at zero; ungrouped pads map to -1. '
                      'GetNetTiePads returns every member, INCLUDING the queried pad.',
}


class Unsupported(ValueError):
    """Missing observations/geometry are a refused prerequisite, never a pass."""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('ascii')


def bounded(values, cap, label):
    rows = []
    for value in values:
        if len(rows) >= cap:
            raise Unsupported(label + ' census cap')
        rows.append(value)
    return rows


def one(node, key):
    rows = sx.children(node, key)
    if len(rows) != 1:
        raise Unsupported('exactly one ' + key + ' required')
    return rows[0]


def atom(node, key):
    row = one(node, key)
    if len(row) != 2 or not isinstance(row[1], str):
        raise Unsupported('scalar ' + key + ' required')
    return sx.unquote(row[1])


def ident(node):
    value = atom(node, 'uuid')
    if str(uuid.UUID(value)) != value:
        raise Unsupported('canonical source UUID required')
    return value


def nm(value):
    value = Decimal(value) * 1000000
    if not value.is_finite() or value != value.to_integral_value() or abs(value) > 10**10:
        raise Unsupported('bounded exact nanometre coordinate required')
    return int(value)


def xy(value):
    return [int(value.x), int(value.y)]


def rectangle(points):
    """Accept only an ordered, axis-aligned four-corner rectangle, not a bbox."""
    points = [list(p) for p in points]
    if len(points) == 5 and points[0] == points[-1]:
        points.pop()
    if (len(points) != 4 or any(len(p) != 2 or any(type(v) is not int or abs(v) > 10**10
                                                for v in p) for p in points)):
        raise Unsupported('four exact rectangle corners required')
    xs = sorted({p[0] for p in points}); ys = sorted({p[1] for p in points})
    if len(xs) != 2 or len(ys) != 2 or {tuple(p) for p in points} != {(x, y) for x in xs for y in ys}:
        raise Unsupported('axis-aligned rectangle required')
    for a, b in zip(points, points[1:] + points[:1]):
        if (a[0] == b[0]) == (a[1] == b[1]):
            raise Unsupported('rectangle perimeter order required')
    return [xs[0], ys[0], xs[1], ys[1]]


def source_context(raw):
    if type(raw) is not bytes or not raw or len(raw) > MAX_SOURCE:
        raise Unsupported('bounded exact source bytes required')
    tree = sx.parse(raw.decode('utf-8'))
    if tree[0] != 'kicad_pcb' or sx.one(tree, 'version') not in (
            ['version', '20241229'], ['version', '20260206']) or sx.children(tree, 'module'):
        raise Unsupported('scoped modern source board required')
    _, resolve = board_floor.source_net_identity(tree)
    fps = {}; pads = {}; ties = []; seen = set(); bridge_count = 0
    for fp in bounded(sx.children(tree, 'footprint'), CAPS['footprints'], 'source footprints'):
        fid = ident(fp)
        refs = [p for p in sx.children(fp, 'property') if len(p) > 2 and sx.unquote(p[1]) == 'Reference']
        if fid in seen or len(refs) != 1:
            raise Unsupported('unique UUID and Reference property required')
        seen.add(fid); ref = sx.unquote(refs[0][2]); fp_pads = {}
        for pad in sx.children(fp, 'pad'):
            pid = ident(pad)
            if pid in seen or len(pad) < 4 or not isinstance(pad[1], str):
                raise Unsupported('unique source pad UUID/number required')
            seen.add(pid)
            row = {'uuid': pid, 'parent_uuid': fid, 'reference': ref,
                   'number': sx.unquote(pad[1]), 'net': resolve(sx.one(pad, 'net'))}
            pads[pid] = row; fp_pads[pid] = (pad, row)
            if len(pads) > CAPS['pads']:
                raise Unsupported('source pad census cap')
        groups = sx.children(fp, 'net_tie_pad_groups')
        fps[fid] = {'uuid': fid, 'reference': ref, 'pad_count': len(fp_pads)}
        if not groups:
            continue
        if len(groups) != 1 or len(groups[0]) != 2 or not isinstance(groups[0][1], str):
            raise Unsupported('one explicit group per tie footprint required')
        text = sx.unquote(groups[0][1])
        if re.fullmatch(r'[1-9][0-9]*(,[1-9][0-9]*){1,2}', text) is None:
            raise Unsupported('simple explicit two/three-pad group required')
        numbers = text.split(',')
        if len(set(numbers)) != len(numbers) or sorted(r['number'] for _, r in fp_pads.values()) != sorted(numbers):
            raise Unsupported('group must cover unique existing footprint pads exactly')
        layer = atom(fp, 'layer')
        if layer not in ('F.Cu', 'B.Cu') or sx.children(fp, 'zone'):
            raise Unsupported('single outer-copper tie without footprint zones required')
        tie_pads = []
        for pad, row in fp_pads.values():
            at = one(pad, 'at'); size = one(pad, 'size'); layers = one(pad, 'layers')
            if (pad[2:4] != ['smd', 'rect'] or len(at) not in (3, 4) or len(size) != 3
                    or sx.children(pad, 'drill') or sx.children(pad, 'primitives')
                    or [sx.unquote(v) for v in layers[1:]] != [layer, layer.replace('.Cu', '.Mask')]
                    or not row['net']):
                raise Unsupported('plain rectangular single-layer connected SMD tie pad required')
            tie_pads.append({**row, 'local_position_nm': [nm(v) for v in at[1:3]],
                             'size_nm': [nm(v) for v in size[1:]], 'layer': layer})
        if len({r['net'] for r in tie_pads}) != len(tie_pads):
            raise Unsupported('each tie member must retain a distinct source net')
        bridges = []
        for item in fp[2:]:
            if not isinstance(item, list) or sx.one(item, 'layer') != ['layer', json.dumps(layer)]:
                continue
            if item[0] == 'pad':
                continue
            if (item[0] != 'fp_poly' or atom(item, 'fill') != 'yes'
                    or atom(one(item, 'stroke'), 'width') != '0'):
                raise Unsupported('only zero-stroke filled rectangle bridge copper supported')
            pts = one(item, 'pts')
            if any(not isinstance(p, list) or len(p) != 3 or p[0] != 'xy' for p in pts[1:]):
                raise Unsupported('plain source bridge corners required')
            points = [[nm(v) for v in p[1:]] for p in pts[1:]]; bounds = rectangle(points)
            bid = ident(item)
            if bid in seen:
                raise Unsupported('unique source bridge UUID required')
            seen.add(bid); bridge_count += 1
            bridges.append({'uuid': bid, 'local_points_nm': points, 'local_bounds_nm': bounds,
                            'source_ast_sha256': digest((sx.dump(item) + '\n').encode())})
        if len(bridges) != len(tie_pads) - 1 or bridge_count > CAPS['bridges']:
            raise Unsupported('bounded two/three-pad rectangular bridge count required')
        ties.append({'uuid': fid, 'reference': ref, 'layer': layer,
                     'group_strings': [text], 'pads': sorted(tie_pads, key=lambda r: r['number']),
                     'bridges': sorted(bridges, key=lambda r: r['uuid']),
                     'source_ast_sha256': digest((sx.dump(fp) + '\n').encode())})
    if len(ties) != CAPS['tie_footprints'] or sorted(len(r['pads']) for r in ties) != [2, 3]:
        raise Unsupported('exactly one two-pad and one three-pad tie required')
    return {'source_sha256': digest(raw), 'footprints': sorted(fps.values(), key=lambda r: r['uuid']),
            'pads': sorted(pads.values(), key=lambda r: r['uuid']),
            'ties': sorted(ties, key=lambda r: r['uuid'])}


def native_rectangle(item, layer, pcbnew):
    poly = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(poly, layer, 0, 1, pcbnew.ERROR_INSIDE)
    if int(poly.ArcCount()) != 0 or poly.OutlineCount() != 1 or poly.HoleCount(0) != 0:
        raise Unsupported('single hole-free arcless Native rectangle required')
    line = poly.COutline(0)
    if not line.IsClosed() or int(line.PointCount()) not in (4, 5):
        raise Unsupported('closed Native rectangle required')
    points = [xy(line.CPoint(i)) for i in range(line.PointCount())]
    return {'points_nm': points, 'bounds_nm': rectangle(points)}


def overlap(a, b):
    bounds = [max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])]
    if bounds[2] - bounds[0] <= 4 or bounds[3] - bounds[1] <= 4:
        return None
    # Twice-coordinates retain an exact rational midpoint. The >4nm interior
    # exceeds the requested 1nm polygon error; this is contact, not clearance.
    return {'overlap_bounds_nm': bounds,
            'twice_witness_nm': [bounds[0] + bounds[2], bounds[1] + bounds[3]]}


def observe(board, pcbnew, raw_source):
    """No load/save or source mutation; all APIs operate on the supplied BOARD."""
    if pcbnew.GetBuildVersion() != '10.0.0' or board.GetCopperLayerCount() != 2:
        raise Unsupported('exact Native10.0.0 two-copper-layer scope required')
    source = source_context(raw_source)
    native_fps = bounded(board.GetFootprints(), CAPS['footprints'], 'Native footprints')
    by_fp = {padless_alias_native.uid(fp): fp for fp in native_fps}
    if len(by_fp) != len(native_fps):
        raise Unsupported('duplicate Native footprint UUID')
    source_fps = {r['uuid']: r for r in source['footprints']}
    if set(by_fp) != set(source_fps):
        raise Unsupported('complete source/Native footprint population differs')
    native_pads = bounded(board.GetPads(), CAPS['pads'], 'Native pads')
    by_pad = {}; rows = []
    for pad in native_pads:
        pid = padless_alias_native.uid(pad); fp = pad.GetParentFootprint()
        row = {'uuid': pid, 'parent_uuid': padless_alias_native.uid(fp),
               'reference': str(fp.GetReference()), 'number': str(pad.GetNumber()),
               'net': str(pad.GetNetname()), 'netcode': int(pad.GetNetCode()),
               'copper_layers': [name for lid, name in ((pcbnew.F_Cu, 'F.Cu'), (pcbnew.B_Cu, 'B.Cu'))
                                 if pad.IsOnLayer(lid)]}
        if pid in by_pad or bool(row['net']) != (row['netcode'] > 0):
            raise Unsupported('unique consistent Native pad identity required')
        by_pad[pid] = pad; rows.append(row)
    if sorted([{k: r[k] for k in ('uuid', 'parent_uuid', 'reference', 'number', 'net')}
               for r in rows], key=lambda r: r['uuid']) != source['pads']:
        raise Unsupported('complete source/Native terminal identity differs')
    expected_ties = {r['uuid']: r for r in source['ties']}
    ties = []
    for fid, fp in by_fp.items():
        if str(fp.GetReference()) != source_fps[fid]['reference']:
            raise Unsupported('source/Native reference differs')
        if bool(fp.IsNetTie()) != (fid in expected_ties):
            raise Unsupported('source/Native net-tie census differs')
        if fid not in expected_ties:
            continue
        wanted = expected_ties[fid]
        # No raw-pointer/ctypes/string-repr fallback. Container usability is a
        # Native prerequisite; method names in a SWIG stub alone do not prove it.
        try:
            strings = [str(v) for v in bounded(fp.GetNetTiePadGroups(), 1, 'Native groups')]
            mapping = fp.MapPadNumbersToNetTieGroups()
            items = bounded(mapping.items(), 3, 'Native group map')
            native_map = {str(key): int(value) for key, value in items}
        except (AttributeError, TypeError) as exc:
            raise Unsupported('Native group strings/map container unavailable; no inferred replacement') from exc
        if strings != wanted['group_strings'] or native_map != {r['number']: 0 for r in wanted['pads']}:
            raise Unsupported('source strings/Native strings/group-index map differ')
        layer = pcbnew.F_Cu if wanted['layer'] == 'F.Cu' else pcbnew.B_Cu
        pad_shapes = []; codes = []; membership = []
        expected_ids = sorted(r['uuid'] for r in wanted['pads'])
        for row in wanted['pads']:
            pad = by_pad[row['uuid']]
            actual = sorted(padless_alias_native.uid(p) for p in
                            bounded(fp.GetNetTiePads(pad), 3, 'Native tied pads'))
            if actual != expected_ids or row['uuid'] not in actual:
                raise Unsupported('Native full group (including self) UUID membership differs')
            membership.append({'queried_pad_uuid': row['uuid'], 'returned_pad_uuids': actual})
            if (pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or pad.GetShape(layer) != pcbnew.PAD_SHAPE_RECT
                    or xy(pad.GetSize(layer)) != row['size_nm'] or xy(pad.GetOffset(layer)) != [0, 0]
                    or xy(pad.GetDrillSize()) != [0, 0]
                    or xy(pad.GetFPRelativePosition()) != row['local_position_nm']
                    or [name for lid, name in ((pcbnew.F_Cu, 'F.Cu'), (pcbnew.B_Cu, 'B.Cu'))
                        if pad.IsOnLayer(lid)] != [wanted['layer']]):
                raise Unsupported('source/Native tie-pad geometry differs')
            codes.append(int(pad.GetNetCode()))
            pad_shapes.append({**row, 'netcode': int(pad.GetNetCode()),
                               'position_nm': xy(pad.GetPosition()),
                               'geometry': native_rectangle(pad, layer, pcbnew)})
        if len(set(codes)) != len(codes) or min(codes) <= 0:
            raise Unsupported('Native tie member net codes are not distinct positive identities')
        graphics = {padless_alias_native.uid(g): g for g in fp.GraphicalItems()
                    if g.IsOnLayer(layer)}
        if set(graphics) != {r['uuid'] for r in wanted['bridges']}:
            raise Unsupported('complete Native tie copper-graphic census differs')
        bridges = []; reached = {r['uuid']: set() for r in pad_shapes}
        for row in wanted['bridges']:
            item = graphics[row['uuid']]
            if (not isinstance(item, pcbnew.PCB_SHAPE) or item.GetShape() != pcbnew.SHAPE_T_POLY
                    or not item.IsFilled() or item.GetWidth() != 0
                    or int(item.GetPolyShape().ArcCount()) != 0):
                raise Unsupported('plain filled zero-stroke Native polygon bridge required')
            geometry = native_rectangle(item, layer, pcbnew)
            a = row['local_bounds_nm']; b = geometry['bounds_nm']
            if sorted([a[2]-a[0], a[3]-a[1]]) != sorted([b[2]-b[0], b[3]-b[1]]):
                raise Unsupported('source/Native rectangular bridge dimensions differ')
            contacts = []
            for pad in pad_shapes:
                witness = overlap(b, pad['geometry']['bounds_nm'])
                if witness:
                    contacts.append({'pad_uuid': pad['uuid'], 'net': pad['net'], **witness})
            if len(contacts) != 2:
                raise Unsupported('each bridge must contact exactly two group pads by positive area')
            left, right = [r['pad_uuid'] for r in contacts]
            reached[left].add(right); reached[right].add(left)
            bridges.append({**row, 'geometry': geometry, 'contacts': contacts})
        visited = set(); todo = [expected_ids[0]]
        while todo:
            current = todo.pop()
            if current not in visited:
                visited.add(current); todo.extend(reached[current] - visited)
        if visited != set(expected_ids):
            raise Unsupported('Native bridge-contact graph does not connect the full declared group')
        ties.append({**wanted, 'native_group_strings': strings, 'native_group_map': native_map,
                     'get_net_tie_pads': membership, 'pads': pad_shapes, 'bridges': bridges})
    # Reuse the current qualified observation, including all non-tie copper,
    # fields, routes, areas and fills, for equality around the same-load export.
    whole = padless_alias_native.observe(board, pcbnew)
    return {'schema': 1, 'policy': POLICY, 'native_version': pcbnew.GetBuildVersion(),
            'source_sha256': source['source_sha256'], 'official_semantics': OFFICIAL_SEMANTICS,
            'footprints': source['footprints'], 'pads': sorted(rows, key=lambda r: r['uuid']),
            'ties': sorted(ties, key=lambda r: r['uuid']),
            'whole_board_observation_sha256': digest(canonical(whole)),
            'native_rectangle_contact_observed': True,
            'shape_semantics': 'TransformShapeToPolygon(clearance=0,error=1nm,ERROR_INSIDE); '
                               'only arcless four-corner rectangles; positive-area midpoint witnesses',
            'board_saved': False, 'clearance_qualified': False, 'qualified': False,
            'accepted': False, 'routing_accepted': False, 'production_admitted': False}


def dsn_membership(raw, source_raw, observation, export_record):
    """Pure readback of exact raw DSN identities; no bridge/SES equivalence claim."""
    if type(raw) is not bytes or not raw or len(raw) > MAX_DSN:
        raise Unsupported('bounded raw Native DSN required')
    source = source_context(source_raw)
    if (observation['source_sha256'] != source['source_sha256']
            or export_record['source_sha256'] != source['source_sha256']
            or export_record['dsn_sha256'] != digest(raw)):
        raise Unsupported('exact source/observation/DSN binding differs')
    tree, _ = padless_alias.dsn_aliases(raw, source_raw, export_record['binding'])
    correspondence = dsn_correspondence(raw, {'pads': observation['pads']}, [])
    library = one(tree, 'library'); placement = one(tree, 'placement'); network = one(tree, 'network')
    images = {sx.unquote(n[1]): n for n in sx.children(library, 'image')}
    stacks = {sx.unquote(n[1]): n for n in sx.children(library, 'padstack')}
    if len(stacks) != len(sx.children(library, 'padstack')):
        raise Unsupported('duplicate DSN padstack identity')
    nets = {}; terminals = {}; placed = {}
    for net in sx.children(network, 'net'):
        name = sx.unquote(net[1])
        if name in nets:
            raise Unsupported('duplicate DSN net identity')
        pins = [sx.unquote(v) for v in one(net, 'pins')[1:]]
        nets[name] = sorted(pins)
        for token in pins:
            if token in terminals:
                raise Unsupported('DSN terminal in more than one net')
            terminals[token] = name
    for component in sx.children(placement, 'component'):
        image = images[sx.unquote(component[1])]
        for place in sx.children(component, 'place'):
            placed[sx.unquote(place[1])] = (image, place)
    rows = []
    for tie in observation['ties']:
        image, place = placed[tie['reference']]; pins = []
        for pad in tie['pads']:
            token = pad['reference'] + '-' + pad['number']
            if terminals.get(token) != pad['net']:
                raise Unsupported('tie DSN pin moved to a different/merged net')
            matches = [n for n in sx.children(image, 'pin')
                       if sx.unquote([v for v in n[2:] if isinstance(v, str)][0]) == pad['number']]
            if len(matches) != 1:
                raise Unsupported('exact tie DSN pin required')
            pin = matches[0]
            pins.append({'pad_uuid': pad['uuid'], 'number': pad['number'], 'net': pad['net'],
                         'network_token': token, 'pin_ast': pin,
                         'padstack_ast': stacks[sx.unquote(pin[1])]})
        rows.append({'footprint_uuid': tie['uuid'], 'reference': tie['reference'],
                     'placement_ast': place, 'image_ast': image, 'pads': pins})
    return {'source_sha256': source['source_sha256'], 'dsn_sha256': digest(raw),
            'terminal_count': correspondence['terminal_count'], 'nets': nets, 'ties': rows,
            'distinct_terminal_net_membership_observed': True,
            'bridge_copper_dsn_fidelity_qualified': False, 'ses_qualified': False,
            'clearance_qualified': False, 'qualified': False, 'accepted': False,
            'routing_accepted': False, 'production_admitted': False}


def observe_and_export(board, source, output, pcbnew, *, mapping, before):
    """Use after shared native.netclasses(), on that exact already-loaded BOARD.

    Writes only the shared fresh export artifacts. Caller freezes/supplies the
    complete input packet and retains this returned record via its bounded Job.
    """
    source = canonical_path(Path(source)); output = canonical_path(Path(output))
    if canonical_path(Path(str(board.GetFileName()))) != source:
        raise Unsupported('exact loaded source filename required')
    raw = read_bytes(source, MAX_SOURCE); pro = read_bytes(source.with_suffix('.kicad_pro'))
    if (before != (digest(raw), digest(pro)) or mapping.get('native_version') != '10.0.0'
            or mapping.get('board_sha256') != before[0] or mapping.get('project_sha256') != before[1]
            or mapping.get('board_saved') is not False):
        raise Unsupported('shared same-load class/input binding required')
    first = observe(board, pcbnew, raw)
    exported = padless_alias.export_board(board, source, output, pcbnew,
                                          mapping=mapping, before=before)
    last = observe(board, pcbnew, raw)
    if first != last or read_bytes(source, MAX_SOURCE) != raw or read_bytes(source.with_suffix('.kicad_pro')) != pro:
        raise Unsupported('same-load Native state/source changed during export')
    dsn = dsn_membership(read_bytes(output, MAX_DSN), raw, first, exported)
    return {'schema': 1, 'policy': POLICY, 'source': str(source), 'output': str(output),
            'source_sha256': digest(raw), 'project_sha256': digest(pro),
            'same_loaded_board': True, 'before_export': first, 'after_export': last,
            'export': exported, 'dsn_membership': dsn,
            'board_saved': bool(exported['observation']),
            'board_save_scope': 'shared exporter may save external alias observation sidecars only; source never saved',
            'qualified': False, 'accepted': False, 'routing_accepted': False,
            'clearance_qualified': False, 'production_admitted': False}
