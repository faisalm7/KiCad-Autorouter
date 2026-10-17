"""Independently preserve one legacy error constraint; no Native claim.

Pure parsed-source qualification. The caller owns original bytes, all remaining
support gates, exact candidate invariants, Native validation and receipt binding.
"""
import hashlib
import re
from decimal import Decimal, InvalidOperation

from autorouter import board_floor as g, sexpr as sx

POLICY = 'legacy-zone-ordinary-pad-witness-v1'
KEY = 'zone_has_empty_net'


def qualify(board, project):
    """Return a rederivable sufficient witness, or refuse with ValueError.

    Only numeric original nets, explicit root zone layers (or the qualified
    two-layer F&B.Cu selector), ordinary copper SMD
    pads and centered round-drill PTH pads are within this initial scope. NPTH
    pads never supply a witness. A pass does not claim Native enforces KEY.
    """
    def require(ok, reason):
        if not ok: raise ValueError('legacy zone witness: ' + reason)

    require(type(project) is dict, 'project object required')
    board_settings = project.get('board')
    require(type(board_settings) is dict, 'board settings object required')
    settings = board_settings.get('design_settings')
    require(type(settings) is dict and type(settings.get('rule_severities')) is dict
            and type(settings['rule_severities'].get(KEY)) is str
            and settings['rule_severities'][KEY] == 'error', 'literal error setting required')
    require(type(board) is list and board and board[0] == 'kicad_pcb', 'board AST required')
    require(not sx.children(board, 'module'), 'legacy module ownership unqualified')

    def field(node, key, count=None, required=True):
        value = sx.one(node, key)
        require(value is not None or not required, 'missing ' + key)
        if value is not None:
            require(count is None or len(value) == count, 'malformed ' + key)
        return value

    seen = set()
    def identity(node):
        value = field(node, 'uuid', 2)[1]
        require(type(value) is str, 'UUID atom required')
        value = sx.unquote(value)
        require(re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', value)
                and value.replace('-', '') != '0' * 32, 'canonical nonzero UUID required')
        return value.lower()

    def walk(node, parent=None):
        require(type(node) is list and node and type(node[0]) is str, 'malformed AST node')
        if node[0] in {'footprint', 'pad', 'zone'}:
            require((node[0] == 'footprint' and parent is board)
                    or (node[0] == 'pad' and parent is not None and parent[0] == 'footprint')
                    or (node[0] == 'zone' and parent is board), 'unqualified pad/zone ownership')
            identity(node)
        if sx.children(node, 'uuid'):
            uid = identity(node)
            # KiCad8 dimension annotations retain their owner's UUID. This is
            # not another pad/zone identity; exact annotation AST stays frozen.
            owner_text=(node[0]=='gr_text' and parent is not None and parent[0]=='dimension'
                        and uid==identity(parent))
            if not owner_text:
                require(uid not in seen, 'duplicate UUID')
                seen.add(uid)
        for child in node[1:]:
            if type(child) is list: walk(child, node)
            else: require(type(child) is str, 'AST atom required')
    walk(board)

    declared = sx.children(board, 'net')
    require(declared and any(n == ['net', '0', '""'] for n in declared), 'numeric net table with net0 required')
    _, resolve = g.source_net_identity(board)  # Checks every reference and code/name conflict.
    table = {n[1]: sx.unquote(n[2]) for n in declared}
    layer_table = field(board, 'layers')
    layer_names, layer_ids, copper = set(), set(), set()
    for row in layer_table[1:]:
        require(type(row) is list and len(row) in (3, 4) and all(type(v) is str for v in row)
                and re.fullmatch(r'0|[1-9][0-9]*', row[0]), 'malformed layer declaration')
        name = sx.unquote(row[1])
        require(name not in layer_names and row[0] not in layer_ids, 'duplicate layer identity')
        layer_names.add(name); layer_ids.add(row[0])
        if name.endswith('.Cu'):
            require(re.fullmatch(r'(?:F|B|In[1-9][0-9]*)\.Cu', name)
                    and row[2] in {'signal', 'power', 'mixed'}, 'unqualified copper layer')
            copper.add(name)
        else: require(row[2] == 'user', 'unqualified noncopper layer')
    require({'F.Cu', 'B.Cu'} <= copper and len(copper) in (2, 4), 'two/four declared copper layers required')

    def selectors(node, pad=False):
        single = field(node, 'layer', required=False)
        multiple = field(node, 'layers', required=False)
        require((single is None) != (multiple is None) and (not pad or single is None), 'one layer selector required')
        values = (single or multiple)[1:]
        require(values and all(type(v) is str for v in values), 'layer atoms required')
        values = [sx.unquote(v) for v in values]
        require(len(set(values)) == len(values) and (single is None or len(values) == 1), 'duplicate/malformed layer selector')
        if not pad and multiple is not None and values==['F&B.Cu']:
            require(copper=={'F.Cu','B.Cu'}, 'F&B.Cu zone selector requires two outer copper layers')
            return ['F.Cu','B.Cu']
        allowed = layer_names | ({'*.Cu', '*.Mask', '*.Paste'} if pad else set())
        require(set(values) <= allowed, 'layer alias or undeclared layer unqualified')
        return values

    witnesses = {}
    for fp in sx.children(board, 'footprint'):
        require(not sx.children(fp, 'net_tie_pad_groups'), 'net ties unqualified')
        for pad in sx.children(fp, 'pad'):
            require(len(pad) >= 4 and all(type(v) is str for v in pad[:4])
                    and pad[2] in {'smd', 'thru_hole', 'np_thru_hole'}
                    and pad[3] in {'rect', 'circle', 'oval', 'roundrect'}, 'ordinary pad type/shape required')
            require(not any((isinstance(n, list) and n and n[0] in {'padstack', 'primitives', 'options', 'remove_unused_layers', 'keep_end_layers', 'chamfer', 'chamfer_ratio'}
                             and n!=['remove_unused_layers','no'])
                            or n in ('remove_unused_layers', 'keep_end_layers') for n in pad[4:]), 'unqualified padstack modifier')
            net = field(pad, 'net', required=False)
            name = resolve(net, owner=pad)
            layers = selectors(pad, pad=True)
            size = field(pad, 'size', 3)
            size_nm = [g.decimal_nm(v, 1000000) for v in size[1:]]
            require(pad[3] != 'circle' or size_nm[0] == size_nm[1], 'nonsquare circle pad unqualified')
            if pad[3] == 'roundrect':
                ratio = field(pad, 'roundrect_rratio', 2)[1]
                try: ratio = Decimal(ratio)
                except (InvalidOperation, TypeError): raise ValueError('legacy zone witness: malformed roundrect ratio') from None
                require(ratio.is_finite() and 0 <= ratio <= Decimal('.5'), 'roundrect ratio outside ordinary scope')
            if not name or pad[2] == 'np_thru_hole': continue
            pad_copper = copper if '*.Cu' in layers else set(layers) & copper
            if not pad_copper: continue
            drill_nm = None
            if pad[2] == 'smd':
                require('*.Cu' not in layers and len(pad_copper) == 1 and sx.one(pad, 'drill') is None, 'ordinary single-copper SMD required')
            else:
                drill = field(pad, 'drill', 2)
                drill_nm = g.decimal_nm(drill[1], 1000000)
                require(pad_copper == copper and all(n > drill_nm for n in size_nm), 'PTH requires all copper and positive centered annulus')
            row = {'pad_uuid': identity(pad), 'footprint_uuid': identity(fp), 'net_code': net[1],
                   'net_name': name, 'pad_type': pad[2], 'copper_layers': sorted(pad_copper),
                   'size_nm': size_nm, 'drill_nm': drill_nm}
            witnesses.setdefault(net[1], []).append(row)

    zones = []
    for zone in sx.children(board, 'zone'):
        require(sx.one(zone, 'keepout') is None and sx.one(zone, 'placement') is None, 'root rule-area intent unqualified')
        layers = selectors(zone)
        net = field(zone, 'net')
        name = resolve(net, owner=zone)
        net_name = field(zone, 'net_name', 2)
        require(sx.unquote(net_name[1]) == name and net[1] in table, 'zone code/name conflict')
        if not set(layers) & copper: continue
        row = {'zone_uuid': identity(zone), 'net_code': net[1], 'net_name': name,
               'copper_layers': sorted(set(layers) & copper), 'net0_exempt': net[1] == '0'}
        if net[1] != '0':
            require(witnesses.get(net[1]), 'positive copper-zone net lacks an ordinary copper pad witness')
            row['pad_witness'] = sorted(witnesses[net[1]], key=lambda p: p['pad_uuid'])[0]
        zones.append(row)
    from autorouter import pipeline as p
    basis = (sx.dump(p.immutable(board)) + '\n').encode()
    return {'schema': 1, 'policy': POLICY, 'original_rule': {'key': KEY, 'severity': 'error'},
            'basis': 'exact-existing-immutable-board-AST', 'basis_sha256': hashlib.sha256(basis).hexdigest(),
            'native_enforcement_claimed': False, 'zones': sorted(zones, key=lambda z: z['zone_uuid'])}
