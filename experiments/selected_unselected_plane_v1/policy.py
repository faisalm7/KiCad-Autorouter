"""Pure literal-plane selection prototype; never Native or acceptance evidence."""
from decimal import Decimal, InvalidOperation
import hashlib
import json

from autorouter import adapter, board_floor, layer_policy, routing_scope as rs, sexpr as sx

POLICY = 'selected-unselected-native-plane-v1'
MAX_BYTES = 2 * 1024**2
MAX_CONTEXT_BYTES = 256 * 1024
MAX_PLANES = 256
MAX_NETS = 4096
MAX_VERTICES = 4096
MAX_COORD_UM = Decimal(2000000)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _bytes(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError('bounded nonempty source and DSN bytes required')


def _canonical(value):
    pending = [(value, 0)]; nodes = 0; size = 0
    while pending:
        item, depth = pending.pop(); nodes += 1
        if nodes > 32768 or depth > 16:
            raise ValueError('plane context exceeds bound')
        if type(item) is str:
            size += len(item.encode())
        elif type(item) in (dict, list):
            if len(item) > 32768:
                raise ValueError('plane context exceeds bound')
            if type(item) is dict:
                if any(type(key) is not str for key in item):
                    raise ValueError('bounded JSON plane context required')
                pending.extend((part, depth+1) for pair in item.items() for part in pair)
            else: pending.extend((part, depth+1) for part in item)
        elif type(item) not in (int, bool, type(None)) or type(item) is int and item.bit_length() > 128:
            raise ValueError('bounded JSON plane context required')
        if size > MAX_CONTEXT_BYTES:
            raise ValueError('plane context exceeds bound')
    try:
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode()
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError('bounded JSON plane context required') from exc
    if len(raw) > MAX_CONTEXT_BYTES:
        raise ValueError('plane context exceeds bound')
    return raw


def _name(atom):
    name = rs._name(atom)
    if not name.strip():
        raise ValueError('named source plane net required')
    return name


def _plane(row, layers):
    if (type(row) is not list or len(row) != 3 or row[0] != 'plane'
            or type(row[1]) is not str or type(row[2]) is not list):
        raise ValueError('one literal polygon per direct Native plane required')
    shape = row[2]
    if (len(shape) < 9 or len(shape) % 2 != 1 or shape[0] != 'polygon'
            or any(type(atom) is not str for atom in shape)
            or shape[1] not in layers or (len(shape)-3)//2 > MAX_VERTICES):
        raise ValueError('bounded declared-layer plane polygon required')
    try:
        values = [Decimal(atom) for atom in shape[2:]]
    except InvalidOperation as exc:
        raise ValueError('finite literal plane coordinates required') from exc
    if (any(not value.is_finite() for value in values) or values[0] != 0
            or any(value.copy_abs() > MAX_COORD_UM for value in values[1:])):
        raise ValueError('zero-width finite bounded plane polygon required')
    return _name(row[1]), sx.unquote(shape[1])


def _derive(source, dsn, names):
    _bytes(source); _bytes(dsn)
    selection = rs.bind(source, names)
    board = sx.parse(source.decode('utf-8'))
    if sx.one(board, 'version') not in (['version', '20241229'], ['version', '20260206']):
        raise ValueError('prototype requires existing20241229/20260206 source syntax')
    layer_policy._two_copper_table(board)
    source_names, resolve = board_floor.source_net_identity(board)
    tree = adapter._parse_dsn(dsn.decode('utf-8')); adapter._check_units(tree)
    # Reuse the current exact class/net/pin grammar and selection census without
    # applying its class split here. This helper only changes direct planes.
    rs.partition_dsn(dsn, names)
    net_rows = sx.children(sx.one(tree, 'network'), 'net')
    if not 1 <= len(net_rows) <= MAX_NETS:
        raise ValueError('bounded DSN net census required')
    net_names = [_name(row[1]) for row in net_rows]
    if len(set(net_names)) != len(net_names) or set(net_names) != source_names:
        raise ValueError('complete source and DSN net census differs')
    structure = sx.one(tree, 'structure')
    if structure is None:
        raise ValueError('DSN structure required')
    layers = sx.children(structure, 'layer')
    if (len(layers) != 2 or any(len(row) != 4 or row[1] not in ('F.Cu', 'B.Cu')
            or sx.one(row, 'type') != ['type', 'signal']
            or sx.one(row, 'property') != ['property', ['index', str(i)]]
            for i, row in enumerate(layers)) or [row[1] for row in layers] != ['F.Cu', 'B.Cu']):
        raise ValueError('existing Native two-copper DSN layer identity required')
    zones = []
    source_zones = sx.children(board, 'zone')
    if len(source_zones) > MAX_PLANES:
        raise ValueError('source zone census exceeds bound')
    for index, zone in enumerate(source_zones):
        name = resolve(sx.one(zone, 'net'))
        named = sx.one(zone, 'net_name')
        layer = sx.one(zone, 'layer')
        if (not name or name not in source_names or layer is None or len(layer) != 2
                or sx.unquote(layer[1]) not in ('F.Cu', 'B.Cu')
                or named is not None and (len(named) != 2 or _name(named[1]) != name)):
            raise ValueError('coherent named source zone and layer required')
        zones.append(dict(ordinal=index, net_name=name, layer=sx.unquote(layer[1]),
                          zone_ast_sha256=_sha(sx.dump(zone).encode())))
    planes = sx.children(structure, 'plane')
    if len(planes) > MAX_PLANES:
        raise ValueError('plane census exceeds bound')
    zone_nets = {(row['net_name'], row['layer']) for row in zones}
    rows = []
    for index, plane in enumerate(planes):
        name, layer = _plane(plane, ('F.Cu', 'B.Cu'))
        if name not in source_names or name not in net_names or (name, layer) not in zone_nets:
            raise ValueError('plane has no coherent source zone/net/layer witness')
        rows.append(dict(ordinal=index, net_name=name, layer=layer,
                         action='omit' if name in selection['requested_names'] else 'retain',
                         plane_ast_sha256=_sha(sx.dump(plane).encode())))
    context = dict(schema=1, policy=POLICY, source_sha256=_sha(source), dsn_sha256=_sha(dsn),
                   selection_binding=selection, source_zone_census=zones, planes=rows,
                   native_export_verified=False, original_design_validated=False,
                   routing_accepted=False)
    _canonical(context)
    return context, tree


def capture(source, dsn, names):
    """Describe literal inputs only; no file reads, exports, engines or approval."""
    return _derive(source, dsn, names)[0]


def apply(source, dsn, names, context):
    """Rebind all inputs, then omit only explicitly selected direct planes.

    This preview is not a complete adapter, trusted Native export or admissible
    routing task. Production integration must independently rederive its context
    from actual source/export receipts in both existing readback hooks.
    """
    expected, tree = _derive(source, dsn, names)
    if _canonical(context) != _canonical(expected):
        raise ValueError('plane context changed or belongs to different inputs/selection')
    structure = sx.one(tree, 'structure')
    result = sx.clone(tree); changed = sx.one(result, 'structure')
    actions = iter(expected['planes'])
    changed[:] = [node for node in changed if not (
        type(node) is list and node and node[0] == 'plane' and next(actions)['action'] == 'omit')]
    retained = [node for node, row in zip(sx.children(structure, 'plane'), expected['planes'])
                if row['action'] == 'retain']
    if sx.children(changed, 'plane') != retained:
        raise ValueError('retained plane order or literal AST differs')
    encoded = adapter._dump_dsn(result).encode()
    _bytes(encoded)
    if adapter._parse_dsn(encoded.decode()) != result:
        raise ValueError('plane preview roundtrip differs')
    return encoded, dict(expected, output_sha256=_sha(encoded))
