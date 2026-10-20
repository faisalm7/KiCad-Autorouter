"""One pure perimeter-stub hypothesis, not contact or clearance evidence.

The caller binds the original project/targets and uses routing_task(original,
'whole_board_unlocked_routing') before this function. A partial Route validates
the seeded input only; its result still needs validation against the immutable
original, with only original protected routes and all seeds treated as generated
copper. No reference route, Native finding, board name or electrical net meaning
is an input to selection. No files, Native tools or routing engine are used here.
"""
from __future__ import annotations

import copy
import hashlib
import uuid

from autorouter import board_floor as g, chain_proposals as cp, pipeline as p, sexpr as sx

POLICY = 'source-orthogonal-perimeter-escape-seed-v1'
NAMESPACE = uuid.UUID('25e7aa5e-2746-4c2d-9180-5607d3d95220')
MAX_SEGMENTS = 256
MAX_FOOTPRINTS = 512
MAX_PADS = 8192
PAD_FIELDS = {'at', 'size', 'layers', 'net', 'uuid', 'roundrect_rratio',
              'pinfunction', 'pintype', 'property'}
TARGETS = {'width_nm', 'clearance_nm', 'via_diameter_nm', 'via_drill_nm'}


def _hash(tree):
    return hashlib.sha256((sx.dump(tree) + '\n').encode()).hexdigest()


def _ids(tree):
    seen, count = set(), 0
    def visit(node, depth=0):
        nonlocal count
        count += 1
        if count > 100000 or depth > 64:
            raise ValueError('bounded source AST required')
        if type(node) is str:
            return
        if type(node) is not list or not node or type(node[0]) is not str:
            raise ValueError('source AST requires lists and string atoms')
        if node[0] == 'uuid':
            value = _id(node)
            if value in seen:
                raise ValueError('duplicate source UUID')
            seen.add(value)
        for child in node[1:]:
            visit(child, depth + 1)
    visit(tree)
    return seen


def _id(node):
    if type(node) is not list or len(node) != 2 or type(node[1]) is not str:
        raise ValueError('one exact UUID required')
    value = sx.unquote(node[1])
    parsed = uuid.UUID(value)
    if not parsed.int or value != str(parsed):
        raise ValueError('canonical nonzero UUID required')
    return value


def _mm(value):
    whole, fraction = divmod(abs(value), 1000000)
    return ('-' if value < 0 else '') + str(whole) + ('.' + str(fraction).zfill(6).rstrip('0') if fraction else '')


def _at(node):
    if node is None or len(node) not in (3, 4):
        raise ValueError('exact position and optional angle required')
    angle = cp.nm(node[3]) if len(node) == 4 else 0
    return cp.xy(node), angle


def _layers(task):
    rows = sx.one(task, 'layers')
    if rows is None:
        raise ValueError('source layer table required')
    ids, names, copper = set(), set(), []
    for row in rows[1:]:
        if type(row) is not list or len(row) != 3 or any(type(v) is not str for v in row):
            raise ValueError('canonical layer declarations required')
        name = sx.unquote(row[1])
        if row[0] in ids or name in names:
            raise ValueError('duplicate layer identity')
        ids.add(row[0]); names.add(name)
        if name.endswith('.Cu') or row[2] != 'user':
            copper.append((row[0], name, row[2]))
    if copper != [('0', 'F.Cu', 'signal'), ('2', 'B.Cu', 'signal')]:
        raise ValueError('canonical two-copper signal layers required')


def _geometry(pad):
    if (len(pad) < 4 or pad[2] != 'smd' or pad[3] not in ('rect', 'roundrect')
            or any(type(n) is not list or not n or n[0] not in PAD_FIELDS for n in pad[4:])):
        raise ValueError('ordinary SMD geometry without overrides required')
    layers = sx.one(pad, 'layers')
    if (layers is None or any(type(v) is not str for v in layers[1:])
            or [sx.unquote(v) for v in layers[1:] if sx.unquote(v).endswith('.Cu') or sx.unquote(v) == '*.Cu'] != ['F.Cu']
            or any(sx.unquote(v) not in {'F.Cu', 'F.Mask', 'F.Paste'} for v in layers[1:])
            or len(set(layers[1:])) != len(layers[1:])):
        raise ValueError('single front copper SMD pad required')
    position, angle = _at(sx.one(pad, 'at'))
    size = sx.one(pad, 'size')
    if size is None or len(size) != 3:
        raise ValueError('one exact pad size required')
    size = cp.xy(size)
    if min(size) <= 0 or angle % 90000000:
        raise ValueError('positive orthogonal pad geometry required')
    ratio = sx.one(pad, 'roundrect_rratio')
    if pad[3] == 'roundrect':
        if ratio is None or len(ratio) != 2 or not 0 <= cp.nm(ratio[1]) <= 500000:
            raise ValueError('ordinary roundrect ratio required')
    elif ratio is not None:
        raise ValueError('rectangle ratio override refused')
    return position, size[::-1] if angle % 180000000 else size


def generate(task, original_protected, targets):
    """Return a detached tree and non-admitting metadata; refuse cap truncation."""
    if type(task) is not list or not task or task[0] != 'kicad_pcb' or type(original_protected) is not list:
        raise ValueError('task AST and explicit original protected list required')
    source_ids = _ids(task)
    task, protected = copy.deepcopy(task), copy.deepcopy(original_protected)
    if (p.routes(task) != protected or any(type(n) is not list or not n or n[0] not in p.ROUTES or not p.locked(n) for n in protected)):
        raise ValueError('all removable reference routing must be stripped')
    if any(sx.children(z, key) for z in sx.children(task, 'zone') for key in p.DERIVED_ZONE):
        raise ValueError('derived task fill must be stripped')
    _layers(task)
    if type(targets) is not dict or set(targets) != TARGETS:
        raise ValueError('exact unchanged target dimension map required')
    targets = targets.copy()
    if (any(type(v) is not int or not 0 < v <= 2147483647 for v in targets.values())
            or targets['via_drill_nm'] >= targets['via_diameter_nm'] or targets['via_diameter_nm'] % 2):
        raise ValueError('positive bounded exact target dimensions required')
    footprints = sx.children(task, 'footprint')
    if len(footprints) > MAX_FOOTPRINTS or sum(len(sx.children(fp, 'pad')) for fp in footprints) > MAX_PADS:
        raise ValueError('source package/pad census exceeded')
    _, resolve = g.source_net_identity(task)
    terminals, connected = {}, {}
    for fp in footprints:
        fid = _id(sx.one(fp, 'uuid'))
        for pad in sx.children(fp, 'pad'):
            pid = _id(sx.one(pad, 'uuid'));net = resolve(sx.one(pad, 'net'))
            layers = sx.one(pad, 'layers', [])
            copper = any(sx.unquote(v) in {'F.Cu', 'B.Cu', '*.Cu'} for v in layers[1:] if type(v) is str)
            if net and copper:
                if len(pad) < 2 or type(pad[1]) is not str or not sx.unquote(pad[1]):
                    raise ValueError('connected real terminal number required')
                terminal = (fid, sx.unquote(pad[1]))
                terminals.setdefault(net, set()).add(terminal)
                if terminal in connected and connected[terminal] != net:
                    raise ValueError('one terminal assigned conflicting nets')
                connected[terminal] = net
    generated, seeds, skips = [], [], []
    for fp in footprints:
        fid = _id(sx.one(fp, 'uuid'))
        def skip(reason, pid=None):
            skips.append(dict(footprint_uuid=fid, pad_uuid=pid, reason=reason))
        if sx.one(fp, 'layer') != ['layer', '"F.Cu"']:
            skip('footprint_not_front'); continue
        if any(sx.children(fp, key) for key in ('clearance', 'zone_connect', 'net_tie_pad_groups', 'padstack')):
            skip('footprint_override_or_net_tie'); continue
        try:
            center, angle = _at(sx.one(fp, 'at'))
            if angle != 0:
                raise ValueError('zero footprint rotation required')
            pads = [(pad, resolve(sx.one(pad, 'net'))) for pad in sx.children(fp, 'pad')]
            pads = [(pad, net) for pad, net in pads if net and any(sx.unquote(v) in {'F.Cu', 'B.Cu', '*.Cu'} for v in sx.one(pad, 'layers', [])[1:])]
            if not 8 <= len(pads) <= 64:
                skip('connected_pad_population_outside_8_64'); continue
            geometry = [(pad, net, *_geometry(pad)) for pad, net in pads]
        except (ValueError, IndexError, TypeError):
            skip('package_geometry_or_orientation_unsupported'); continue
        low = [min(row[2][i] for row in geometry) for i in (0, 1)]
        high = [max(row[2][i] for row in geometry) for i in (0, 1)]
        for pad, net, local, size in sorted(geometry, key=lambda row: _id(sx.one(row[0], 'uuid'))):
            pid = _id(sx.one(pad, 'uuid'))
            if len(terminals[net]) < 2:
                skip('net_has_fewer_than_two_real_terminals', pid); continue
            if abs(local[0]) == abs(local[1]):
                skip('center_or_ambiguous_outward_axis', pid); continue
            axis = 0 if abs(local[0]) > abs(local[1]) else 1
            sign = 1 if local[axis] > 0 else -1
            if local[axis] != (high[axis] if sign > 0 else low[axis]) or size[axis] <= size[1-axis]:
                skip('not_elongated_aligned_perimeter_pad', pid); continue
            if size[axis] % 2 or targets['width_nm'] > size[1-axis]:
                skip('noninteger_half_extent_or_width_exceeds_pad', pid); continue
            length = size[axis] // 2 + targets['clearance_nm'] + targets['via_diameter_nm'] // 2
            start = tuple(center[i] + local[i] for i in (0, 1))
            end = tuple(start[i] + (sign * length if i == axis else 0) for i in (0, 1))
            if any(abs(v) > 10**12 for v in (*start, *end)):
                raise ValueError('generated coordinate exceeds exact source bounds')
            identity = str(uuid.uuid5(NAMESPACE, '|'.join(map(str, (POLICY, pid, net, *start, *end, targets['width_nm'])))))
            if identity in source_ids:
                raise ValueError('generated UUID collides with source identity')
            source_ids.add(identity)
            segment = ['segment', ['start', *map(_mm, start)], ['end', *map(_mm, end)],
                       ['width', _mm(targets['width_nm'])], ['layer', '"F.Cu"'],
                       copy.deepcopy(sx.one(pad, 'net')), ['uuid', '"' + identity + '"']]
            generated.append(segment)
            seeds.append(dict(pad_uuid=pid, footprint_uuid=fid, segment_uuid=identity,
                              start_nm=list(start), end_nm=list(end), width_nm=targets['width_nm']))
            if len(generated) > MAX_SEGMENTS:
                raise ValueError('seed population exceeds256; no prefix accepted')
    result = copy.deepcopy(task)
    result.extend(generated)
    if p.immutable(result) != p.immutable(task) or p.routes(result) != protected + generated:
        raise ValueError('seed changed immutable geometry or original protected routes')
    return result, dict(schema=1, policy=POLICY, accepted=False, routing_accepted=False,
        contact_or_clearance_proven=False, original_source_and_targets_binding_required=True,
        input_task_sha256=_hash(task), output_task_sha256=_hash(result),
        protected_routes_sha256=_hash(protected), protected_count=len(protected),
        targets=targets, generated_count=len(generated), seeds=seeds, skips=skips)
