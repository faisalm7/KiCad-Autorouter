"""Narrow original edge-rule DSN correction; native acceptance remains mandatory.

The caller must independently exclude custom-rule companions. These two input
byte strings cannot establish that a separate .kicad_dru file is absent.
"""
import copy
from decimal import Decimal, InvalidOperation
import json
from . import adapter as a, sexpr as sx

POLICY = 'native-rectangular-edge-v1'
CLASS = 'kicadedge'


def _bytes(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= sx.MAX_BYTES:
        raise ValueError('bounded nonempty bytes required')
    return raw.decode('utf-8')


def _number(value):
    if isinstance(value, bool): raise ValueError('finite numeric edge dimension required')
    try: result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError): raise ValueError('invalid edge dimension') from None
    if not result.is_finite() or abs(result) > Decimal('1000000000'):
        raise ValueError('finite bounded edge dimension required')
    return result


def _walk(node):
    if isinstance(node, list):
        if node: yield node
        for child in node: yield from _walk(child)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('duplicate project key: '+key)
        result[key] = value
    return result


def derive_context(boardbytes, projectbytes):
    """Return eligible original scope or an explicit unchanged-path reason."""
    board = sx.parse(_bytes(boardbytes))
    project = json.loads(_bytes(projectbytes), object_pairs_hook=_pairs, parse_float=Decimal,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite project value')))
    if not board or board[0] != 'kicad_pcb' or not isinstance(project, dict):
        raise ValueError('native board and project roots required')
    context = dict(schema=1, policy=POLICY, applicable=False, reason='scope not checked',
        source_sha256={'board':a._digest(boardbytes),'project':a._digest(projectbytes)},
        requires_no_custom_rule_companion=True)
    def skip(reason): context['reason'] = reason; return context
    settings = project.get('net_settings', {})
    if not isinstance(settings, dict): raise ValueError('malformed net settings')
    classes = settings.get('classes', [])
    if not isinstance(classes, list) or any(not isinstance(row, dict) for row in classes):
        raise ValueError('malformed source classes')
    names = [row.get('name') for row in classes]
    if any(not isinstance(name,str) for name in names) or len(set(name.casefold() for name in names)) != len(names):
        raise ValueError('ambiguous source class namespace')
    if names != ['Default'] or settings.get('netclass_assignments') not in (None,{}) or settings.get('netclass_patterns') not in (None,[]):
        return skip('outside Default-only unassigned project scope')
    project_board = project.get('board', {})
    if not isinstance(project_board,dict): raise ValueError('malformed project board settings')
    design = project_board.get('design_settings', {})
    if not isinstance(design,dict): raise ValueError('malformed project design settings')
    rules = design.get('rules', {})
    if not isinstance(rules,dict): raise ValueError('malformed project rules')
    if design.get('custom_rules') not in (None,[],{},'') or any(node[0] in {'rule','rules'} for node in _walk(board)):
        return skip('embedded custom rules outside rectangular edge scope')
    if 'min_copper_edge_clearance' not in rules: return skip('explicit original edge minimum unavailable')
    value = rules['min_copper_edge_clearance']
    if not isinstance(value,(int,Decimal)) or isinstance(value,bool): raise ValueError('numeric original edge minimum required')
    edge = _number(value)
    if edge < 0: raise ValueError('negative original edge minimum')
    context['original_min_copper_edge_clearance_mm'] = a._atom_number(edge)
    context['requested_clearance_um'] = a._atom_number(edge*1000)
    if edge == 0: return skip('original edge minimum is zero; no added DSN rule')
    # The root setup/stackup contains repeated layer definitions, not a
    # geometry layer selector. Only that exact container is exempt; its
    # descendants and all actual geometry retain duplicate-singleton checks.
    stackup=sx.one(sx.one(board,'setup',[]),'stackup')
    edges = [node for node in _walk(board) if node is not stackup
             and sx.one(node,'layer') == ['layer','"Edge.Cuts"']]
    if len(edges) != 1 or edges[0] not in board or edges[0][0] != 'gr_rect':
        return skip('requires one root Edge.Cuts rectangle and no other edge geometry')
    rectangle = edges[0]
    for key in {'start','end','stroke','fill','layer','uuid','tstamp','locked'}: sx.one(rectangle,key)
    if any(not node or node[0] not in {'start','end','stroke','fill','layer','uuid','tstamp','locked'} for node in rectangle[1:] if isinstance(node,list)):
        return skip('unsupported or rotated rectangle metadata')
    start, end = sx.one(rectangle,'start'), sx.one(rectangle,'end')
    if start is None or end is None or len(start) != 3 or len(end) != 3: raise ValueError('malformed original rectangle')
    x1,y1,x2,y2 = map(_number, [*start[1:],*end[1:]])
    if x1 == x2 or y1 == y2: raise ValueError('original rectangle has no area')
    bounds = [min(x1,x2),-max(y1,y2),max(x1,x2),-min(y1,y2)]
    context.update(applicable=True, reason='original Default-only root rectangular edge scope',
        rect_um=[a._atom_number(value*1000) for value in bounds],
        source_edge_sha256=a._digest(sx.dump(rectangle).encode()),
        requested_clearance_um=a._atom_number(edge*1000))
    return context


def correct(dsnbytes, context):
    """Add only a boundary class and its exact original default/SMD/self pairs."""
    text = _bytes(dsnbytes)
    keys={'schema','policy','applicable','reason','source_sha256','requires_no_custom_rule_companion'}
    optional={'rect_um','source_edge_sha256','requested_clearance_um','original_min_copper_edge_clearance_mm'}
    digest=lambda value:isinstance(value,str) and len(value)==64 and set(value)<=set('0123456789abcdef')
    if (not isinstance(context,dict) or not keys<=context.keys() or context.keys()-keys-optional
            or type(context['schema']) is not int or context['schema'] != 1 or context['policy'] != POLICY
            or type(context['applicable']) is not bool or context['requires_no_custom_rule_companion'] is not True
            or not isinstance(context['reason'],str) or not 0<len(context['reason'])<=4096
            or not isinstance(context['source_sha256'],dict) or set(context['source_sha256'])!={'board','project'}
            or not all(digest(value) for value in context['source_sha256'].values())):
        raise ValueError('unknown edge context')
    if context['applicable'] and (context.keys()!=keys|optional or not digest(context['source_edge_sha256'])
            or not isinstance(context['rect_um'],list) or len(context['rect_um'])!=4): raise ValueError('incomplete edge context')
    record = dict(schema=1, policy=POLICY, applied=False, reason=context['reason'],
        source_sha256=copy.deepcopy(context['source_sha256']), input_sha256=a._digest(dsnbytes),
        output_sha256=a._digest(dsnbytes), native_project_modified=False, routing_accepted=False,
        requires_no_custom_rule_companion=True,context_sha256=a._digest(json.dumps(context,sort_keys=True,separators=(',',':')).encode()))
    record.update({key:context[key] for key in optional if key in context})
    if not context['applicable']: return dsnbytes, record
    tree = a._parse_dsn(text); a._check_units(tree)
    # Reject duplicate declarations even where the existing unit reader permits
    # repeated identical values; no ambiguous namespace is silently overridden.
    if len(sx.children(tree,'unit')) != 1 or len(sx.children(tree,'resolution')) != 1:
        raise ValueError('ambiguous DSN units')
    structure, network = sx.one(tree,'structure'), sx.one(tree,'network')
    if structure is None or network is None: raise ValueError('DSN structure and network required')
    boundary, rule = sx.one(structure,'boundary'), sx.one(structure,'rule')
    classes = sx.children(network,'class')
    if boundary is None or len(boundary) != 2 or len(classes) != 1 or len(classes[0])<2 or classes[0][1] != 'kicad_default':
        raise ValueError('one unclassified boundary and default DSN class required')
    class_rule = sx.one(classes[0],'rule')
    nodes = list(_walk(tree))
    if any(len([node for node in nodes if node[0]==key]) != 1 for key in ('unit','resolution')):
        raise ValueError('nested or duplicate DSN units')
    if any(node[0] in {'clearance_class','layer_rule','class_class'} or
           any(isinstance(atom,str) and sx.unquote(atom) == CLASS for atom in node) for node in nodes):
        raise ValueError('existing or reserved edge clearance namespace')
    if any(node[0] == 'rule' and node is not rule and node is not class_rule for node in nodes):
        raise ValueError('unknown DSN rule scope')
    if any(node[0] == 'class' and node is not classes[0] for node in nodes):
        raise ValueError('unknown named DSN item class')
    if rule is None or len(rule)!=4 or len(sx.children(rule,'clearance')) != 2 or class_rule is None or len(class_rule)!=3:
        raise ValueError('normal default and SMD matrix required')
    for ruleset in (rule,class_rule):
        width=sx.one(ruleset,'width')
        if width is None or len(width)!=2 or _number(width[1])<=0: raise ValueError('positive DSN rule width required')
    clearances = sx.children(rule,'clearance')
    if len(clearances[0]) != 2 or len(clearances[1]) != 3 or clearances[1][2] != ['type','smd_smd']:
        raise ValueError('unknown default/SMD clearance type')
    for node in nodes:
        if node[0] == 'clearance':
            if not any(node is item for item in [*clearances,*sx.children(class_rule,'clearance')]): raise ValueError('unknown clearance scope')
            if len(node) != 2 and node is not clearances[1]: raise ValueError('unknown typed clearance')
            if _number(node[1]) < 0: raise ValueError('negative DSN clearance')
    shape = boundary[1]; expected = list(map(_number,context['rect_um']))
    if expected[0]>=expected[2] or expected[1]>=expected[3]: raise ValueError('invalid original rectangle context')
    precision = _number(sx.one(tree,'resolution')[2])
    if precision != precision.to_integral_value(): raise ValueError('integer DSN export precision required')
    if any(value*precision != (value*precision).to_integral_value() for value in expected):
        raise ValueError('source rectangle not exact at export precision')
    corners = {(expected[0],expected[1]),(expected[0],expected[3]),(expected[2],expected[1]),(expected[2],expected[3])}
    if shape[:2] == ['rect','pcb'] and len(shape) == 6:
        x1,y1,x2,y2 = map(_number,shape[2:]); actual = {(x1,y1),(x1,y2),(x2,y1),(x2,y2)}
    elif shape[:2] == ['path','pcb'] and len(shape) == 13 and _number(shape[2]) == 0:
        coords = list(map(_number,shape[3:])); points = list(zip(coords[::2],coords[1::2])); actual = set(points[:-1])
        if points[0] != points[-1] or len(actual) != 4 or any((x1==x2)==(y1==y2) for (x1,y1),(x2,y2) in zip(points,points[1:])):
            raise ValueError('DSN boundary is not a closed axis-aligned rectangle')
    else: raise ValueError('zero-width rectangular pcb boundary required')
    if actual != corners: raise ValueError('DSN boundary differs from original corners')
    value = context['requested_clearance_um']
    if _number(value) != _number(context['original_min_copper_edge_clearance_mm'])*1000 or _number(value) <= 0:
        raise ValueError('edge context changes original minimum')
    changed = copy.deepcopy(tree); target = sx.one(sx.one(changed,'structure'),'boundary')
    target.append(['clearance_class',CLASS]); added = ['rule',*[['clearance',value,['type',pair]] for pair in
        ('default_'+CLASS,'smd_'+CLASS,CLASS+'_'+CLASS)]]
    sx.one(changed,'structure').append(added)
    restored = copy.deepcopy(changed); sx.one(sx.one(restored,'structure'),'boundary').pop(); sx.one(restored,'structure').pop()
    encoded = a._dump_dsn(changed).encode()
    if restored != tree or len(encoded)>sx.MAX_BYTES or a._parse_dsn(encoded.decode()) != changed:
        raise ValueError('edge-only semantic reconstruction failed')
    record.update(applied=True,reason='exact original edge minimum encoded for default/SMD/self pairs',
        output_sha256=a._digest(encoded),source_edge_sha256=context['source_edge_sha256'],
        original_min_copper_edge_clearance_mm=context['original_min_copper_edge_clearance_mm'],
        requested_clearance_um=value,clearance_class=CLASS,exact_edge_only_ast_edit=True)
    return encoded, record
