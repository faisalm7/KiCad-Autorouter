"""One fixed rectangular front-copper tie on two excluded routing nets."""
from . import board_floor, placement_transform as geometry, sexpr as sx


def _numbers(node, key, count, *, unrotated=False):
    fields = sx.one(node, key, [])[1:]
    if unrotated and len(fields) == count + 1 and geometry.nm(fields[-1], 1_000_000) == 0:
        fields = fields[:-1]
    if len(fields) != count:
        raise ValueError('expected an unrotated ' + key + ' entry')
    return [geometry.nm(atom, 1_000_000) for atom in fields]


def _bridge_rectangle(bridge):
    stroke = sx.one(bridge, 'stroke', [])
    points = sx.one(bridge, 'pts', [])[1:]
    if (geometry.atom(bridge, 'fill') != 'yes' or _numbers(stroke, 'width', 1) != [0]
            or len(points) != 4 or any(type(point) is not list or len(point) != 3 or point[0] != 'xy'
                                       for point in points)):
        raise ValueError('the bridge needs one filled, zero-stroke rectangle')
    corners = geometry.simple([[geometry.nm(atom, 1_000_000) for atom in point[1:]] for point in points])
    x0, y0, x1, y1 = geometry.bbox(corners)
    if {tuple(point) for point in corners} != {(x0, y0), (x0, y1), (x1, y0), (x1, y1)}:
        raise ValueError('the bridge needs an axis-aligned rectangle')
    return [x0, y0, x1, y1]


def _intersects(a, b):
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def _tie_geometry(board, footprint):
    from .layer_policy import _two_copper_table

    if sx.one(board, 'version') != ['version', '20260206']:
        raise ValueError('the tie requires the modern 20260206 PCB format')
    _two_copper_table(board)
    if geometry.atom(footprint, 'layer') != 'F.Cu' or sx.children(footprint, 'zone'):
        raise ValueError('the tie must be on front copper without footprint zones')
    x, y = _numbers(footprint, 'at', 2, unrotated=True)
    pads = sx.children(footprint, 'pad')
    numbers = geometry.atom(footprint, 'net_tie_pad_groups').split(',')
    if (len(numbers) != 2 or len(set(numbers)) != 2 or any(not 1 <= len(n) <= 16 or n.startswith('0')
            or not n.isascii() or not n.isdecimal() for n in numbers)):
        raise ValueError('the tie needs one group of two distinct numbered pads')
    if len(pads) != 2 or any(len(pad) < 4 or type(pad[1]) is not str for pad in pads):
        raise ValueError('the tie footprint needs exactly two pads')
    if set(numbers) != {sx.unquote(pad[1]) for pad in pads}:
        raise ValueError('the tie group must cover both footprint pads')

    _, net_name = board_floor.source_net_identity(board)
    nets, rectangles = [], []
    for pad in pads:
        if (pad[2:4] != ['smd', 'rect'] or sx.one(pad, 'layers') != ['layers', '"F.Cu"', '"F.Mask"']
                or any(type(field) is not list or not field or field[0] not in
                       {'at', 'size', 'layers', 'net', 'pinfunction', 'pintype', 'uuid'} for field in pad[4:])):
            raise ValueError('the tie requires plain unrotated front rectangular SMD pads')
        px, py = _numbers(pad, 'at', 2, unrotated=True)
        width, height = _numbers(pad, 'size', 2)
        if min(width, height) <= 0:
            raise ValueError('the tie pad dimensions must be positive')
        # Double the coordinates to keep all half-nanometre edges exact.
        rectangles.append([2 * px - width, 2 * py - height, 2 * px + width, 2 * py + height])
        nets.append(net_name(sx.one(pad, 'net')))
    if not all(nets) or len(set(nets)) != 2:
        raise ValueError('the tie pads must retain two distinct original nets')

    copper = [item for item in footprint[2:] if type(item) is list and item
              and sx.one(item, 'layer') is not None and geometry.atom(item, 'layer').endswith('.Cu')
              and item[0] != 'layer']
    if (len(copper) != 1 or copper[0][0] != 'fp_poly' or geometry.atom(copper[0], 'layer') != 'F.Cu'
            or any(sx.one(item, 'layers') is not None for item in footprint[2:]
                   if type(item) is list and item and item[0] != 'pad')):
        raise ValueError('the tie needs exactly one front-copper bridge polygon')
    bridge = _bridge_rectangle(copper[0])
    doubled = [coordinate * 2 for coordinate in bridge]
    if _intersects(*rectangles) or any(not _intersects(doubled, pad) for pad in rectangles):
        raise ValueError('the bridge must overlap both separate pad interiors')
    if any(net_name(sx.one(zone, 'net'), owner=zone) in nets for zone in sx.children(board, 'zone')):
        raise ValueError('copper zones on the tied nets are outside this scope')
    return sorted(nets), [bridge[0] + x, bridge[1] + y, bridge[2] + x, bridge[3] + y]


def describe(board):
    """Return the source-derived protected tie, or explain why it is unsupported."""
    ties = [fp for fp in sx.children(board, 'footprint') if sx.children(fp, 'net_tie_pad_groups')]
    if not ties:
        return None
    if len(ties) != 1:
        raise ValueError('only one fixed two-pad net tie is supported')
    footprint = ties[0]
    refs = [sx.unquote(row[2]) for row in sx.children(footprint, 'property')
            if len(row) >= 3 and all(type(atom) is str for atom in row[1:3]) and sx.unquote(row[1]) == 'Reference']
    reference = refs[0] if len(refs) == 1 else ''
    if not reference or len(reference) > 48 or any(not char.isprintable() for char in reference):
        raise ValueError('the net tie needs one valid reference')
    try:
        nets, bounds = _tie_geometry(board, footprint)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'net tie {reference}: {exc}') from exc
    return {'reference': reference, 'nets': nets, 'bridge_bounds_nm': bounds}


def transport(directory, task, tie):
    """Check the raw export partition and the Native obstacle before adapter replay."""
    from . import native_connected
    from .floor_route import read_json
    from .placement_clearance import read_bytes

    nets, _, terminals = native_connected._index(task)
    native_connected._dsn_members(read_bytes(directory / 'native.dsn', 20 * 1024**2), nets, terminals)
    obstacles = read_json(directory / 'obstacles.json')
    expected = {'kind': 'PCB_SHAPE', 'layer': 'F.Cu',
                'bbox_mm': [value / 1_000_000 for value in tie['bridge_bounds_nm']]}
    if type(obstacles) is not list or obstacles.count(expected) != 1:
        raise ValueError(f"net tie {tie['reference']}: the Native bridge keepout is missing or differs")
    return {**tie, 'native_terminal_count': len(terminals)}
