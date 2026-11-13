"""Independent rectangular constraint authority; imports no placement engine.

Input is explicit synthetic/source-derived facts, never a KiCad file. Dimensions
and pad offsets use the captured zero-degree orientation; rotations are clockwise
quarter turns. Every alternative carries transforms only, bound to all original
facts. Native geometry, pad-shape clearances and electrical validity are unproved.
"""
import copy
import hashlib
import json
import math
from decimal import Context, Decimal, localcontext

MIN_EXTENT_MM = 0.000001  # One nanometre; smaller proxy rectangles are unsupported.
FIXED_CONTEXT_POLICY = 'unchanged-fixed-context-v1'
PRESERVED_COPPER = 'preserved-copper-envelope'
RIGID_TRANSLATION_POLICY = 'rigid-selected-translation-v1'
# Proposer proxy arithmetic only. Final actual integer-nm checks are independent.
RIGID_PROXY_TOLERANCE_NM = Decimal('0.000001')


class Refused(ValueError):
    pass


def encoded(value):
    try:
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    except (ValueError, TypeError, RecursionError) as exc:
        raise Refused('Finite JSON facts required') from exc
    if len(raw) > 256 * 1024:
        raise Refused('Fact/alternative byte limit exceeded')
    return raw


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def fields(value, names, where):
    if type(value) is not dict or set(value) != set(names.split()):
        raise Refused(where + ': unsupported or missing fields')


def number(value, where):
    # Range-check integers before math.isfinite tries to convert them to float.
    if type(value) not in (int, float) or abs(value) > 10000 or not math.isfinite(value):
        raise Refused(where + ': bounded finite number required')
    return value


def identifier(value, where):
    if type(value) is not str or not value or len(value) > 128 or any(ord(c) < 32 for c in value):
        raise Refused(where + ': stable nonempty identifier required')
    return value


def sequence(value, maximum, where, minimum=0):
    if type(value) is not list or not minimum <= len(value) <= maximum:
        raise Refused(where + ': bounded explicit list required')
    return value


def distinct(value, where):
    if len(value) != len(set(value)):
        raise Refused(where + ': duplicate identity/value')


def rect(value, where):
    sequence(value, 4, where, 4)
    for x in value:
        number(x, where)
    if value[2] - value[0] < MIN_EXTENT_MM or value[3] - value[1] < MIN_EXTENT_MM:
        raise Refused(where + ': rectangle extents must be at least one nanometre')
    return value


def pose(component):
    return dict(component_id=component['id'], x_mm=component['position_mm'][0],
                y_mm=component['position_mm'][1], rotation_deg=component['rotation_deg'],
                side=component['side'])


def bounds(component, transform):
    w, h = component['size_mm']
    if transform['rotation_deg'] in (90, 270):
        w, h = h, w
    x, y = transform['x_mm'], transform['y_mm']
    box = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    if box[0] >= box[2] or box[1] >= box[3]:
        raise Refused('Numerically collapsed component rectangle')
    return box


def inside(inner, outer, margin=0):
    return (inner[0] >= outer[0] + margin and inner[1] >= outer[1] + margin
            and inner[2] <= outer[2] - margin and inner[3] <= outer[3] - margin)


def separated(a, b, gap):
    return (a[2] + gap <= b[0] or b[2] + gap <= a[0]
            or a[3] + gap <= b[1] or b[3] + gap <= a[1])


def immovable(facts):
    # Deliberately conservative: every component on a tracked net is fixed,
    # including terminals beyond the track's explicitly supplied pad witnesses.
    tracked_nets = {t['net'] for t in facts['tracks']}
    selected, fixed = set(facts['selected']), set(facts['fixed_components'])
    return {c['id'] for c in facts['components'] if c['locked'] or c['id'] in fixed
            or c['id'] not in selected or any(p['net'] in tracked_nets for p in c['pads'])}


def prepare(value):
    """Validate a bounded explicit contract and detach it from caller objects."""
    encoded(value)
    facts = copy.deepcopy(value)
    if type(facts) is not dict:
        raise Refused('facts: explicit object required')
    context = type(facts.get('schema')) is int and facts['schema'] == 2
    annotations = context and 'annotation_context' in facts
    fields(facts, 'schema board components selected fixed_components groups tracks keepouts clearance_mm'
           + (' fixed_context_policy' if context else '')
           + (' annotation_context' if annotations else ''), 'facts')
    if type(facts['schema']) is not int or facts['schema'] not in (1, 2):
        raise Refused('Unsupported fact schema')
    if context and facts['fixed_context_policy'] != FIXED_CONTEXT_POLICY:
        raise Refused('Unsupported fixed context policy')
    fields(facts['board'], 'kind bounds_mm cutouts', 'board')
    if facts['board']['kind'] != 'rectangle' or facts['board']['cutouts'] != []:
        raise Refused('Polygon outlines and cutouts are unsupported')
    rect(facts['board']['bounds_mm'], 'board bounds')
    groups = sequence(facts['groups'], 1, 'rigid groups')
    gap = number(facts['clearance_mm'], 'clearance')
    if not 0 <= gap <= 10:
        raise Refused('Clearance must be between zero and ten millimetres')
    components = sequence(facts['components'], 32, 'components', 3)
    ids, pads, pad_ids = [], {}, []
    for c in components:
        fields(c, 'id position_mm size_mm rotation_deg side locked pads allowed_region_mm allowed_rotations_deg allowed_sides', 'component')
        ids.append(identifier(c['id'], 'component id'))
        for field in ('position_mm', 'size_mm'):
            sequence(c[field], 2, field, 2)
            for x in c[field]:
                number(x, field)
        if min(c['size_mm']) < MIN_EXTENT_MM:
            raise Refused('Component rectangle extents must be at least one nanometre')
        if type(c['locked']) is not bool:
            raise Refused('Explicit component lock required')
        if type(c['rotation_deg']) is not int or c['rotation_deg'] not in (0, 90, 180, 270):
            raise Refused('Only exact quarter-turn orientations are supported')
        if c['side'] not in ('front', 'back'):
            raise Refused('Unknown component side')
        rotations = sequence(c['allowed_rotations_deg'], 4, 'allowed rotations', 1)
        if any(type(r) is not int or r not in (0, 90, 180, 270) for r in rotations):
            raise Refused('Unsupported allowed orientation')
        distinct(rotations, 'allowed rotations')
        sides = sequence(c['allowed_sides'], 2, 'allowed sides', 1)
        if any(type(s) is not str or s not in ('front', 'back') for s in sides):
            raise Refused('Unsupported allowed side')
        distinct(sides, 'allowed sides')
        if c['side'] not in sides:
            raise Refused('Side changes are unsupported; current side must be allowed')
        rect(c['allowed_region_mm'], 'allowed region')
        for pad in sequence(c['pads'], 64, 'pads'):
            fields(pad, 'id net offset_mm', 'pad')
            pid = identifier(pad['id'], 'pad id'); pad_ids.append(pid)
            if pad['net'] is not None:
                identifier(pad['net'], 'net id')
            sequence(pad['offset_mm'], 2, 'pad offset', 2)
            for x in pad['offset_mm']:
                number(x, 'pad offset')
            if (abs(pad['offset_mm'][0]) > c['size_mm'][0] / 2
                    or abs(pad['offset_mm'][1]) > c['size_mm'][1] / 2):
                raise Refused('Pad centre outside supplied component rectangle')
            pads[pid] = pad
    distinct(ids, 'components'); distinct(pad_ids, 'pads')
    if len(pad_ids) > 256:
        raise Refused('Total pad limit exceeded')
    for field, minimum in (('selected', 1), ('fixed_components', 0)):
        values = sequence(facts[field], 32, field, minimum)
        for name in values:
            identifier(name, field)
        distinct(values, field)
        if not set(values) <= set(ids):
            raise Refused(field + ': unknown component')
    track_ids = []
    for track in sequence(facts['tracks'], 256, 'tracks'):
        fields(track, 'id net pad_ids', 'track')
        track_ids.append(identifier(track['id'], 'track id'))
        identifier(track['net'], 'track net')
        for pid in sequence(track['pad_ids'], 256, 'track pad witnesses', 1):
            identifier(pid, 'track pad witness')
            if pid not in pads or pads[pid]['net'] != track['net']:
                raise Refused('Track incidence/net differs from actual pad identity')
        distinct(track['pad_ids'], 'track pad witnesses')
    distinct(track_ids, 'tracks')
    keepout_ids = []
    for keepout in sequence(facts['keepouts'], 96 if context else 32, 'keepouts'):
        fields(keepout, 'id kind bounds_mm sides', 'keepout')
        keepout_ids.append(identifier(keepout['id'], 'keepout id'))
        if keepout['kind'] != 'rectangle' and not (context and keepout['kind'] == PRESERVED_COPPER):
            raise Refused('Only rectangular keepouts are supported')
        rect(keepout['bounds_mm'], 'keepout rectangle')
        sides = sequence(keepout['sides'], 2, 'keepout sides', 1)
        if any(type(s) is not str or s not in ('front', 'back') for s in sides):
            raise Refused('Unknown keepout side')
        distinct(sides, 'keepout sides')
    distinct(keepout_ids, 'keepouts')
    if groups:
        group = groups[0]
        fields(group, 'policy members', 'rigid group')
        if type(group['policy']) is not str or group['policy'] != RIGID_TRANSLATION_POLICY:
            raise Refused('Unsupported rigid group policy')
        members = sequence(group['members'], 16, 'rigid group members', 2)
        for member in members:
            identifier(member, 'rigid group member')
        distinct(members, 'rigid group members')
        if members != facts['selected']:
            raise Refused('Rigid group must contain the exact ordered selected components')
        if set(members) & immovable(facts):
            raise Refused('Rigid group contains a fixed/locked/unselected/tracked component')
    if not immovable(facts):
        raise Refused('This selected-placement scope requires a fixed/unselected anchor')
    if annotations:
        from autorouter import placement_annotations
        try:
            captured = placement_annotations.validate(facts['annotation_context'])
        except ValueError as exc:
            raise Refused('Native annotation context: ' + str(exc)) from exc
        board = [Decimal(str(n))*1000000 for n in facts['board']['bounds_mm']]
        if board != captured['outline_nm']:
            raise Refused('Native annotation board differs')
        movable = set(facts['selected']) - immovable(facts)
        if not movable <= set(captured['movable_owners']):
            raise Refused('Native annotation movable owners differ')
        for component in facts['components']:
            if component['id'] in movable:
                anchor = [Decimal(str(n))*1000000 for n in component['position_mm']]
                if anchor != captured['footprint_anchors_nm'][component['id']]:
                    raise Refused('Native annotation source anchor differs')
    return facts


def original_alternative(facts):
    return dict(schema=1, source_sha256=digest(facts),
                transforms=[pose(c) for c in sorted(facts['components'], key=lambda c: c['id'])])


def validate_alternative(source, alternative):
    """Return detached transforms only after independently checking every constraint."""
    return _alternative_validator(source)(alternative)


def _alternative_validator(source):
    """Prepare one private detached snapshot for a single bounded search.

    This closure is never shared globally or across source checks. Every call
    still checks all transforms, geometry and annotation moves. The public
    validator deliberately constructs a fresh closure on every invocation.
    """
    facts = prepare(source)
    source_sha256 = digest(facts)
    components = {c['id']: c for c in facts['components']}
    fixed = immovable(facts)
    def validate(alternative):
        return _validate_prepared_alternative(facts, source_sha256, components, fixed, alternative)
    return validate


def _validate_prepared_alternative(facts, source_sha256, components, fixed, alternative):
    fields(alternative, 'schema source_sha256 transforms', 'alternative')
    if type(alternative['schema']) is not int or alternative['schema'] != 1 or alternative['source_sha256'] != source_sha256:
        raise Refused('Alternative source binding differs')
    rows = sequence(alternative['transforms'], len(components), 'transforms', len(components))
    seen = set(); rectangles = []
    grouped = set(facts['groups'][0]['members']) if facts['groups'] else set()
    group_delta = None
    for t in rows:
        fields(t, 'component_id x_mm y_mm rotation_deg side', 'transform')
        cid = identifier(t['component_id'], 'transform component')
        if cid not in components or cid in seen:
            raise Refused('Missing, duplicate or unknown transformed component')
        seen.add(cid); c = components[cid]
        number(t['x_mm'], 'x'); number(t['y_mm'], 'y')
        if type(t['rotation_deg']) is not int or t['rotation_deg'] not in c['allowed_rotations_deg']:
            raise Refused('Disallowed orientation: ' + cid)
        if t['side'] != c['side'] or t['side'] not in c['allowed_sides']:
            raise Refused('Side flips are unsupported: ' + cid)
        if cid in grouped:
            if t['rotation_deg'] != c['rotation_deg']:
                raise Refused('Rigid group orientation changed: ' + cid)
            with localcontext(Context(prec=50)):
                delta = [(Decimal(str(t[key]))-Decimal(str(c['position_mm'][i])))*1000000
                         for i, key in enumerate(('x_mm', 'y_mm'))]
                if group_delta is None:
                    group_delta = delta
                elif any((a-b).copy_abs() > RIGID_PROXY_TOLERANCE_NM for a, b in zip(delta, group_delta)):
                    raise Refused('Rigid group relative position changed: ' + cid)
        if cid in fixed and t != pose(c):
            raise Refused('Fixed/locked/unselected/tracked component moved: ' + cid)
        box = bounds(c, t); gap = facts['clearance_mm']
        # Schema2 preserves the exact fixed baseline. A fixed courtyard proxy
        # outside the outline, or an inherited fixed/fixed proxy overlap, is not
        # authority to alter a fixed part or admit a new moving conflict. Actual
        # source/candidate Native checks and original AST protection are separate.
        preserved_fixed = facts['schema'] == 2 and cid in fixed
        if not preserved_fixed and not inside(box, facts['board']['bounds_mm'], gap):
            raise Refused('Component outside rectangular board: ' + cid)
        baseline_board_region = preserved_fixed and c['allowed_region_mm'] == facts['board']['bounds_mm']
        if not baseline_board_region and not inside(box, c['allowed_region_mm']):
            raise Refused('Component outside allowed region: ' + cid)
        for k in facts['keepouts']:
            inherited_copper = preserved_fixed and k['kind'] == PRESERVED_COPPER
            if not inherited_copper and t['side'] in k['sides'] and not separated(box, k['bounds_mm'], gap):
                raise Refused('Component intersects rectangular keepout: ' + cid)
        for other, side, other_box in rectangles:
            inherited_pair = preserved_fixed and other in fixed
            if not inherited_pair and side == t['side'] and not separated(box, other_box, gap):
                raise Refused('Component rectangles overlap: ' + other + '/' + cid)
        rectangles.append((cid, t['side'], box))
    if 'annotation_context' in facts:
        from autorouter import placement_annotations
        moves = {t['component_id']: [int((Decimal(str(t[k]))*1000000).to_integral_value())
                    for k in ('x_mm', 'y_mm')] for t in rows if t['component_id'] not in fixed}
        try:
            placement_annotations.check_moves(facts['annotation_context'], moves)
        except ValueError as exc:
            raise Refused('Native annotation prefilter: ' + str(exc)) from exc
    return copy.deepcopy(alternative)
