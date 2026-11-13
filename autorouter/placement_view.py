"""Deterministic, passive SVG for bounded captured placement geometry.

This renderer checks display input shape and size only. It performs no constraint
or Native validation, grants no approval, and cannot write files or start work.
The caller supplies qualified observations and validates every proposed pose.
"""
from html import escape
import math


def _need(condition, message):
    if not condition:
        raise ValueError('Placement view: ' + message)


def _label(value, maximum=128):
    _need(type(value) is str and len(value) <= maximum, 'bounded text required')
    _need(all(c in '\t\n\r' or 0x20 <= ord(c) <= 0xD7FF or 0xE000 <= ord(c) <= 0xFFFD
              or 0x10000 <= ord(c) <= 0x10FFFF for c in value), 'invalid XML text')
    return value


def _nm(value, *, positive=False):
    _need(type(value) is int and abs(value) <= 2_000_000_000
          and (not positive or value > 0), 'bounded integer nanometres required')
    return value


def _array(value, maximum, minimum=0):
    _need(type(value) in (list, tuple) and minimum <= len(value) <= maximum, 'bounded geometry list required')
    return value


def _point(value):
    return tuple(_nm(n) for n in _array(value, 2, 2))


def _rect(value):
    result = tuple(_nm(n) for n in _array(value, 4, 4))
    _need(result[0] < result[2] and result[1] < result[3], 'nonempty rectangle required')
    return result


def _row(value):
    _need(type(value) is dict, 'geometry object required')
    return value


def _identifier(value, seen):
    value = _label(value)
    _need(value and value not in seen, 'nonempty unique geometry identity required')
    seen.add(value)
    return value


def _fmt(value):
    # Keep tiny positive geometry visible in the SVG data instead of rounding
    # a valid nanometre width to literal zero at a large board scale.
    return '0' if value == 0 else format(value, '.12g')


def _mm(value):
    # Integer arithmetic keeps nanometre labels exact, including negative XY.
    sign = '-' if value < 0 else ''
    whole, fraction = divmod(abs(value), 1_000_000)
    return sign + str(whole) + (('.' + str(fraction).zfill(6).rstrip('0')) if fraction else '')


def render(observation, moves_nm, selected_ids, region_nm, *, title='Placement draft',
           state='Geometry draft — Native validation required'):
    """Return self-contained SVG; coordinates retain KiCad's downward Y axis.

    Bounds: 16 footprints, 32 pads, 64 straight segments, 32 ordinary zones,
    1024 zone vertices, integer-nm positions within +/-2 metres. Only selected
    anchors receive translations. Pad centres and courtyard bounds receive the
    same delta; source copper and fixed geometry are never transformed.
    """
    title, state = _label(title, 160), _label(state, 180)
    observation = _row(observation)
    outline = _rect(_row(observation['outline'])['bounds_nm'])
    region = _rect(region_nm)
    selected = [_label(item) for item in _array(selected_ids, 16, 1)]
    _need(all(selected) and len(selected) == len(set(selected)), 'unique selected IDs required')
    _need(type(moves_nm) is dict and len(moves_nm) == len(selected) and set(moves_nm) == set(selected),
          'exact selected translation map required')
    moves = {key: _point(value) for key, value in moves_nm.items()}
    footprints, seen, pad_seen, artwork = [], set(), set(), []
    extents = [outline, region]
    for original in _array(observation['footprints'], 16, 1):
        row = _row(original); identity = _identifier(row['uuid'], seen)
        if row.get('artwork_only') is True:
            _need(identity not in selected and row['pads'] == [] and row['courtyard'] is None
                  and row.get('placement_eligible') is False, 'immutable artwork cannot be moved')
            artwork.append(_label(row['reference']))
            continue  # Passive artwork is not a physical placement obstacle.
        position = _point(row['position_nm']); court = _rect(_row(row['courtyard'])['bounds_nm'])
        _need(type(row.get('angle')) is int and row['angle'] in (0, 90, 180, 270)
              and row.get('side') == 'front' and type(row.get('locked')) is bool,
              'front, fixed cardinal footprint display required')
        target = moves.get(identity, position)
        delta = (target[0] - position[0], target[1] - position[1])
        proposed = tuple(court[i] + delta[i % 2] for i in range(4))
        _rect(proposed)
        pads = []
        for original_pad in _array(row['pads'], 8):
            pad = _row(original_pad); pid = _identifier(pad['uuid'], pad_seen)
            _need(len(pad_seen) <= 32, 'pad population exceeded')
            centre = _point(pad['position_nm']); size = _point(pad['size_nm']); drill = _point(pad['drill_nm'])
            kind, shape, angle = pad.get('kind', 'thru_hole'), pad.get('shape', 'circle'), pad.get('angle', 0)
            _need(type(angle) is int and angle in (0, 90, 180, 270), 'cardinal pad angle required')
            _need(min(size) > 0, 'positive pad size required')
            if kind == 'thru_hole':
                _need(shape in ('circle', 'rect') and 0 < drill[0] == drill[1] < min(size),
                      'circular-drill PTH pad required')
            else:
                _need(kind == 'smd' and shape in ('rect', 'roundrect') and drill == (0, 0),
                      'ordinary rectangular SMD pad required')
            if shape == 'circle': _need(size[0] == size[1], 'circular pad size required')
            ratio = pad.get('roundrect_rratio', None if shape == 'roundrect' else 0)
            if ratio is None and shape != 'roundrect': ratio = 0
            _need(type(ratio) in (int, float) and math.isfinite(ratio) and 0 <= ratio <= .5,
                  'bounded roundrect ratio required')
            _need(shape != 'roundrect' or ratio > 0, 'positive roundrect ratio required')
            _need(shape == 'roundrect' or ratio == 0, 'unexpected rounded corners')
            moved = _point([centre[i] + delta[i] for i in range(2)])
            pads.append(dict(id=pid, centre=centre, moved=moved, size=size, drill=drill[0],
                             shape=shape, angle=angle, radius=min(size)*ratio,
                             number=_label(pad['number']), net=_label(pad['net'])))
            display_size = size[::-1] if angle in (90, 270) else size
            for x, y in (centre, moved):
                extents.append((x - display_size[0] / 2, y - display_size[1] / 2,
                                x + display_size[0] / 2, y + display_size[1] / 2))
        footprints.append(dict(id=identity, reference=_label(row['reference']), position=position,
            target=target, court=court, proposed=proposed, locked=row['locked'], pads=sorted(pads, key=lambda p:p['id'])))
        extents.extend((court, proposed))
    _need(set(selected) <= seen and not seen.intersection(pad_seen), 'unknown/ambiguous selected identity')
    routes, route_seen = [], set()
    for original in _array(observation.get('routes', []), 64):
        row = _row(original); identity = _identifier(row['uuid'], route_seen)
        _need(row['kind'] == 'segment' and row['layer'] in ('F.Cu', 'B.Cu') and type(row['locked']) is bool,
              'straight copper segments required')
        start, end = _point(row['start_nm']), _point(row['end_nm']); width = _nm(row['width_nm'], positive=True)
        _need(start != end, 'nonempty copper segment required')
        routes.append(dict(id=identity, start=start, end=end, width=width, layer=row['layer'],
                           locked=row['locked'], net=_label(row['net'])))
        extents.append((min(start[0],end[0])-width/2, min(start[1],end[1])-width/2,
                        max(start[0],end[0])+width/2, max(start[1],end[1])+width/2))
    _need(type(observation.get('route_count')) is int and observation['route_count'] == len(routes), 'route population differs')
    zones, zone_seen, vertices = [], set(), 0
    for original in _array(observation['zones'], 32):
        row = _row(original); identity = _identifier(row['uuid'], zone_seen)
        outlines = _array(row['outlines_nm'], 1, 1)
        _need(row['is_rule_area'] is False and row['holes'] == [0] and row['arc_count'] == 0
              and row['outline_closed'] == [True], 'ordinary straight hole-free zone required')
        points = [_point(point) for point in _array(outlines[0], 256, 3)]
        vertices += len(points); _need(vertices <= 1024, 'zone vertex population exceeded')
        zones.append(dict(id=identity, points=points))
        extents.append((min(p[0] for p in points), min(p[1] for p in points),
                        max(p[0] for p in points), max(p[1] for p in points)))

    left, top = min(b[0] for b in extents), min(b[1] for b in extents)
    right, bottom = max(b[2] for b in extents), max(b[3] for b in extents)
    scale = min(920 / (right - left), 460 / (bottom - top))
    origin_x = 40 + (920 - (right-left)*scale)/2
    origin_y = 120 + (460 - (bottom-top)*scale)/2
    x = lambda value: origin_x + (value-left)*scale
    y = lambda value: origin_y + (value-top)*scale
    height = 692 + 25 * len(selected)
    result = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="' + str(height)
              + '" viewBox="0 0 1000 ' + str(height) + '" font-family="sans-serif">']

    def element(tag, attrs, text=None):
        attributes = ' '.join(str(key).replace('_','-') + '="' + escape(str(value), quote=True) + '"'
                              for key, value in attrs.items())
        result.append('<' + tag + (' ' + attributes if attributes else '') + ('/>' if text is None
                      else '>' + escape(text) + '</' + tag + '>'))

    def label(px, py, text, **attrs):
        element('text', dict(x=_fmt(px), y=_fmt(py), font_size=13, fill='#202c3a', **attrs), text)

    def box(bounds, role, **attrs):
        element('rect', dict(x=_fmt(x(bounds[0])), y=_fmt(y(bounds[1])), width=_fmt((bounds[2]-bounds[0])*scale),
            height=_fmt((bounds[3]-bounds[1])*scale), data_role=role, **attrs))

    element('title', {}, title)
    element('desc', {}, 'KiCad coordinates: X right, Y down. Display only; no validation, approval or execution authority.')
    element('rect', dict(width=1000, height=height, fill='#ffffff'))
    label(30, 32, title[:100], font_weight='bold')
    label(30, 56, state[:110])
    label(30, 78, 'Blue: proposed selected   Gray dashed: original   Slate: fixed   Orange: preserved copper')
    label(30, 99, 'Green: zone outline   Blue dashed: allowed region   Coordinates: mm, X right / Y down')
    if artwork:
        label(30, 598, 'Immutable non-copper artwork retained, omitted from physical diagram: ' + ', '.join(artwork)[:60],
              data_role='immutable-artwork-note')
    for zone in sorted(zones, key=lambda z:z['id']):
        element('polygon', dict(points=' '.join(_fmt(x(px))+','+_fmt(y(py)) for px,py in zone['points']),
            fill='#dcecdf', fill_opacity='.55', stroke='#5b8668', stroke_width=1,
            data_role='zone', data_zone=zone['id']))
    box(outline, 'board-outline', fill='none', stroke='#243342', stroke_width=2)
    box(region, 'allowed-region', fill='none', stroke='#548ec7', stroke_width=1.5, stroke_dasharray='7 4')
    for route in sorted(routes, key=lambda r:r['id']):
        element('line', dict(x1=_fmt(x(route['start'][0])), y1=_fmt(y(route['start'][1])),
            x2=_fmt(x(route['end'][0])), y2=_fmt(y(route['end'][1])), stroke='#bd7426',
            stroke_width=_fmt(route['width']*scale), stroke_linecap='round', data_role='preserved-segment',
            data_route=route['id'], data_layer=route['layer'], data_locked=str(route['locked']).lower(),
            data_width_nm=route['width'], data_start_nm=','.join(map(str,route['start'])), data_end_nm=','.join(map(str,route['end']))))

    def footprint(fp, *, ghost=False):
        chosen = fp['id'] in moves
        bounds = fp['court'] if ghost else fp['proposed']
        color = '#9aa3ad' if ghost else '#176cba' if chosen else '#526273'
        role = 'original-selected' if ghost else 'proposed-selected' if chosen else 'fixed'
        attrs = dict(fill='none' if ghost else '#edf5fc' if chosen else '#edf0f3',
                     stroke=color, stroke_width=1.4, data_footprint=fp['id'])
        if ghost: attrs['stroke_dasharray'] = '5 4'
        box(bounds, role, **attrs)
        for pad in fp['pads']:
            centre = pad['centre'] if ghost else pad['moved']
            attrs = dict(fill='none' if ghost else '#d6b96b', stroke=color, stroke_width=1,
                data_role=role+'-pad', data_pad=pad['id'], data_centre_nm=','.join(map(str,centre)),
                data_shape=pad['shape'], data_angle=pad['angle'])
            if pad['shape'] == 'circle':
                element('circle', dict(attrs, cx=_fmt(x(centre[0])), cy=_fmt(y(centre[1])),
                    r=_fmt(pad['size'][0]*scale/2)))
            else:
                element('rect', dict(attrs, x=_fmt(x(centre[0])-pad['size'][0]*scale/2),
                    y=_fmt(y(centre[1])-pad['size'][1]*scale/2), width=_fmt(pad['size'][0]*scale),
                    height=_fmt(pad['size'][1]*scale), rx=_fmt(pad['radius']*scale),
                    transform='rotate('+str(-pad['angle'])+' '+_fmt(x(centre[0]))+' '+_fmt(y(centre[1]))+')'))
            if not ghost and pad['drill']:
                element('circle', dict(cx=_fmt(x(centre[0])), cy=_fmt(y(centre[1])), r=_fmt(pad['drill']*scale/2),
                    fill='#ffffff', stroke=color, stroke_width='.6', data_role=role+'-drill', data_pad=pad['id']))
        if not ghost:
            label(x(bounds[0])+3, y(bounds[1])-4, fp['reference'][:24] + (' [locked]' if fp['locked'] else ''),
                  data_role='component-label', data_footprint=fp['id'])

    ordered = sorted(footprints, key=lambda fp:fp['id'])
    for fp in ordered:
        if fp['id'] in moves: footprint(fp, ghost=True)
    for fp in ordered:
        footprint(fp)
        if fp['id'] in moves and fp['position'] != fp['target']:
            a,b = (x(fp['position'][0]),y(fp['position'][1])),(x(fp['target'][0]),y(fp['target'][1]))
            dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy); ux,uy=dx/length,dy/length
            arrow, half = min(7,length/2), min(3,length/3)
            element('line', dict(x1=_fmt(a[0]),y1=_fmt(a[1]),x2=_fmt(b[0]),y2=_fmt(b[1]),
                stroke='#176cba',stroke_width=1.2,data_role='movement',data_footprint=fp['id']))
            element('polygon', dict(points=' '.join(_fmt(px)+','+_fmt(py) for px,py in
                (b,(b[0]-arrow*ux+half*uy,b[1]-arrow*uy-half*ux),
                 (b[0]-arrow*ux-half*uy,b[1]-arrow*uy+half*ux))),fill='#176cba'))
    label(30, 618, 'Selected component / UUID', font_weight='bold')
    label(440, 618, 'Original X, Y (mm)', font_weight='bold')
    label(690, 618, 'Proposed X, Y (mm)', font_weight='bold')
    for index, fp in enumerate(fp for fp in ordered if fp['id'] in moves):
        py = 644 + 25*index
        label(30,py,fp['reference'][:24]+' / '+fp['id'][:36],data_role='coordinate-label')
        label(440,py,', '.join(_mm(n) for n in fp['position']),data_role='original-xy',data_footprint=fp['id'])
        label(690,py,', '.join(_mm(n) for n in fp['target']),data_role='proposed-xy',data_footprint=fp['id'])
    label(30,height-24,'Display only. Geometry drafts require independent constraints and Native checks; no route or approval is granted.')
    result.append('</svg>')
    rendered = '\n'.join(result) + '\n'
    _need(len(rendered.encode('utf-8')) <= 512*1024, 'SVG byte limit exceeded')
    return rendered
