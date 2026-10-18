"""Narrow original edge-rule DSN correction; native acceptance remains mandatory.

The caller must independently exclude custom-rule companions. These two input
byte strings cannot establish that a separate .kicad_dru file is absent.
"""
import copy
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR
import json
import re
from . import adapter as a, sexpr as sx

POLICY = 'native-rectangular-edge-v1'
CLASS = 'kicadedge'
NAMED_POLICY = 'known-named-inherited-edge-prototype-v1'
_ENGINE_CLASSES = {'default', 'kicad_default', 'null', 'wire', 'smd', 'via', 'pin', 'area',
                   CLASS, 'board_edge'}


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


def _named_scope(projectbytes):
    """Reuse the source whitelist; never resolve net patterns or Native parents."""
    from . import netclass as nc
    # The shared class whitelist intentionally accepts only JSON int/float.
    # The main parser separately keeps the original edge decimal exact.
    project = json.loads(_bytes(projectbytes), object_pairs_hook=_pairs,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite project value')))
    try:
        policy = nc.qualify_project(project)
    except ValueError:
        policy = nc.qualify_parent_project(project)
    if policy['mode'] not in ('literal_two_class', nc.PARENT_POLICY):
        raise ValueError('known named class policy required')
    composite = False
    try:
        nc.qualify_parent_project(project)
        composite = True
    except ValueError:
        pass
    classes = {}
    for row in project['net_settings']['classes']:
        name = row['name']
        if name != 'Default' and name.casefold() in _ENGINE_CLASSES:
            raise ValueError('source class collides with an engine clearance namespace')
        classes[name] = {key: a._atom_number(Decimal(nc._millimetres_to_nm(row[source])) / 1000)
                         for key, source in (('width_um', 'track_width'), ('clearance_um', 'clearance'))}
    return {'policy': NAMED_POLICY, 'source_policy': policy['mode'], 'source_classes': classes,
            'allow_default_composites': composite}


def _check_named_scope(scope):
    from . import netclass as nc
    if (type(scope) is not dict or set(scope) != {'policy', 'source_policy', 'source_classes', 'allow_default_composites'}
            or scope['policy'] != NAMED_POLICY or scope['source_policy'] not in ('literal_two_class', nc.PARENT_POLICY)
            or type(scope['allow_default_composites']) is not bool or type(scope['source_classes']) is not dict
            or not 2 <= len(scope['source_classes']) <= 16 or 'Default' not in scope['source_classes']):
        raise ValueError('unknown named edge scope')
    names = scope['source_classes']
    if len({name.casefold() for name in names if type(name) is str}) != len(names):
        raise ValueError('ambiguous named edge namespace')
    for name, row in names.items():
        if (type(name) is not str or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}', name) is None
                or name != 'Default' and name.casefold() in _ENGINE_CLASSES
                or type(row) is not dict or set(row) != {'width_um', 'clearance_um'}
                or any(type(value) is not str or _number(value) <= 0 for value in row.values())):
            raise ValueError('unqualified named edge class parameters')
    if scope['source_policy'] == 'literal_two_class' and len(names) != 2:
        raise ValueError('literal named edge scope needs two classes')
    return names


def _named_rules(classes, scope):
    """Keep class rows/rules untouched; their fresh matrix rows inherit the edge.

    Eager named edge pairs would create matrix rows before Network's normal
    initialization, changing nonedge clearances and default item assignments.
    Actual full-load matrix/item checks remain a separate qualification gate.
    """
    from . import netclass as nc
    configured = _check_named_scope(scope)
    if not 1 <= len(classes) <= 31:
        raise ValueError('bounded known DSN class inventory required')
    names = set(); rules = []
    for cls in classes:
        if len(cls) < 3 or type(cls[1]) is not str:
            raise ValueError('malformed named DSN class')
        name = sx.unquote(cls[1])
        if name in names: raise ValueError('duplicate named DSN class')
        names.add(name)
        if name == 'kicad_default':
            source = configured['Default']
        elif name in configured and name != 'Default':
            source = configured[name]
        elif scope['allow_default_composites']:
            source = nc._parent_class({'class': name}, configured)
        else:
            raise ValueError('unknown or unqualified named DSN class identity')
        if (name == 'Default' or any(type(node) is not str and
                (not isinstance(node, list) or not node or node[0] not in {'rule', 'circuit'}) for node in cls[2:])):
            raise ValueError('unqualified named DSN class override')
        rule, circuit = sx.one(cls, 'rule'), sx.one(cls, 'circuit')
        if rule is None or len(rule) != 3 or circuit is None or len(circuit) != 2:
            raise ValueError('exact class width/clearance and via circuit required')
        nc._children_only(rule, {'width', 'clearance'})
        via = sx.one(circuit, 'use_via')
        if via is None or len(via) != 2 or type(via[1]) is not str:
            raise ValueError('unknown named DSN circuit override')
        for key, expected in (('width', source['width_um']), ('clearance', source['clearance_um'])):
            actual = sx.one(rule, key)
            if actual is None or len(actual) != 2 or type(actual[1]) is not str or _number(actual[1]) != _number(expected):
                raise ValueError('named DSN class differs from source parameters')
        rules.append(rule)
    if 'kicad_default' not in names:
        raise ValueError('exact KiCad default DSN class required')
    return rules, sorted(names)


def derive_context(boardbytes, projectbytes, *, experimental_named_classes=False):
    """Return eligible original scope or an explicit unchanged-path reason."""
    if type(experimental_named_classes) is not bool:
        raise ValueError('explicit experimental named edge Boolean required')
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
    named_scope = None
    if names != ['Default'] or settings.get('netclass_assignments') not in (None,{}) or settings.get('netclass_patterns') not in (None,[]):
        if not experimental_named_classes:
            return skip('outside Default-only unassigned project scope')
        try:
            named_scope = _named_scope(projectbytes)
            _check_named_scope(named_scope)
        except (ValueError, TypeError, KeyError):
            return skip('outside qualified named edge class scope')
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
    if named_scope is not None and any(_number(row['clearance_um']) > edge * 1000
                                      for row in named_scope['source_classes'].values()):
        return skip('named class clearance exceeds exact inherited edge scope')
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
    if named_scope is not None:
        context.update(named_class_scope=named_scope,
                       reason='prototype known named classes with exact inherited rectangular edge')
    return context


def correct(dsnbytes, context):
    """Encode original edge clearance; fractional bounds may move only inward."""
    text = _bytes(dsnbytes)
    keys={'schema','policy','applicable','reason','source_sha256','requires_no_custom_rule_companion'}
    geometry={'rect_um','source_edge_sha256','requested_clearance_um','original_min_copper_edge_clearance_mm'}
    optional=geometry|{'named_class_scope'}
    digest=lambda value:isinstance(value,str) and len(value)==64 and set(value)<=set('0123456789abcdef')
    if (not isinstance(context,dict) or not keys<=context.keys() or context.keys()-keys-optional
            or type(context['schema']) is not int or context['schema'] != 1 or context['policy'] != POLICY
            or type(context['applicable']) is not bool or context['requires_no_custom_rule_companion'] is not True
            or not isinstance(context['reason'],str) or not 0<len(context['reason'])<=4096
            or not isinstance(context['source_sha256'],dict) or set(context['source_sha256'])!={'board','project'}
            or not all(digest(value) for value in context['source_sha256'].values())):
        raise ValueError('unknown edge context')
    if context['applicable'] and (not (keys|geometry) <= context.keys() or not digest(context['source_edge_sha256'])
            or not isinstance(context['rect_um'],list) or len(context['rect_um'])!=4): raise ValueError('incomplete edge context')
    named_scope=context.get('named_class_scope')
    if 'named_class_scope' in context:
        configured=_check_named_scope(named_scope)
        if (not context['applicable'] or any(_number(row['clearance_um']) > _number(context['requested_clearance_um'])
                                            for row in configured.values())):
            raise ValueError('outside exact inherited named edge scope')
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
    if boundary is None or len(boundary) != 2:
        raise ValueError('one unclassified boundary required')
    if named_scope is None:
        if len(classes) != 1 or len(classes[0])<2 or classes[0][1] != 'kicad_default':
            raise ValueError('one default DSN class required')
        class_rules=[sx.one(classes[0],'rule')];class_names=None
    else:
        class_rules,class_names=_named_rules(classes,named_scope)
    nodes = list(_walk(tree))
    if any(len([node for node in nodes if node[0]==key]) != 1 for key in ('unit','resolution')):
        raise ValueError('nested or duplicate DSN units')
    if any(node[0] in {'clearance_class','layer_rule','class_class'} or
           any(isinstance(atom,str) and sx.unquote(atom) == CLASS for atom in node) for node in nodes):
        raise ValueError('existing or reserved edge clearance namespace')
    if any(node[0] == 'rule' and node is not rule and not any(node is item for item in class_rules) for node in nodes):
        raise ValueError('unknown DSN rule scope')
    if any(node[0] == 'class' and not any(node is item for item in classes) for node in nodes):
        raise ValueError('unknown named DSN item class')
    if rule is None or len(rule)!=4 or len(sx.children(rule,'clearance')) != 2 or any(item is None or len(item)!=3 for item in class_rules):
        raise ValueError('normal default and SMD matrix required')
    for ruleset in (rule,*class_rules):
        width=sx.one(ruleset,'width')
        if width is None or len(width)!=2 or _number(width[1])<=0: raise ValueError('positive DSN rule width required')
    clearances = sx.children(rule,'clearance')
    if len(clearances[0]) != 2 or len(clearances[1]) != 3 or clearances[1][2] != ['type','smd_smd']:
        raise ValueError('unknown default/SMD clearance type')
    for node in nodes:
        if node[0] == 'clearance':
            if not any(node is item for item in [*clearances,*(entry for cls in class_rules for entry in sx.children(cls,'clearance'))]): raise ValueError('unknown clearance scope')
            if len(node) != 2 and node is not clearances[1]: raise ValueError('unknown typed clearance')
            if _number(node[1]) < 0: raise ValueError('negative DSN clearance')
    shape = boundary[1]; expected = list(map(_number,context['rect_um']))
    if expected[0]>=expected[2] or expected[1]>=expected[3]: raise ValueError('invalid original rectangle context')
    precision = _number(sx.one(tree,'resolution')[2])
    if precision != precision.to_integral_value(): raise ValueError('integer DSN export precision required')
    fractional=any(value*precision != (value*precision).to_integral_value() for value in expected)
    corners = {(expected[0],expected[1]),(expected[0],expected[3]),(expected[2],expected[1]),(expected[2],expected[3])}
    if shape[:2] == ['rect','pcb'] and len(shape) == 6:
        x1,y1,x2,y2 = map(_number,shape[2:]); actual = {(x1,y1),(x1,y2),(x2,y1),(x2,y2)}
    elif shape[:2] == ['path','pcb'] and len(shape) == 13 and _number(shape[2]) == 0:
        coords = list(map(_number,shape[3:])); points = list(zip(coords[::2],coords[1::2])); actual = set(points[:-1])
        if points[0] != points[-1] or len(actual) != 4 or any((x1==x2)==(y1==y2) for (x1,y1),(x2,y2) in zip(points,points[1:])):
            raise ValueError('DSN boundary is not a closed axis-aligned rectangle')
    else: raise ValueError('zero-width rectangular pcb boundary required')
    if len(actual)!=4:raise ValueError('DSN boundary is a degenerate rectangle')
    inward=None;replacement=None
    if not fractional:
        if actual != corners: raise ValueError('DSN boundary differs from original corners')
    else:
        # Native10 can round rectangular export bounds by up to the observed
        # half micrometre. This is a guarded input domain, not a rounding-law
        # claim or permission to expand the original board. The replacement is
        # independently derived from exact source coordinates, always inward.
        parser=sx.one(tree,'parser',[])
        if (precision!=10 or sx.one(parser,'host_version')!=['host_version','"10.0.0"']
                or sx.one(parser,'host_cad')!=['host_cad','"KiCad\'s Pcbnew"']
                or any(v*1000!=(v*1000).to_integral_value() for v in expected)):
            raise ValueError('fractional source export precision is outside qualified Native10 scope')
        bounds=[min(x for x,y in actual),min(y for x,y in actual),max(x for x,y in actual),max(y for x,y in actual)]
        if actual!={(bounds[0],bounds[1]),(bounds[0],bounds[3]),(bounds[2],bounds[1]),(bounds[2],bounds[3])}:
            raise ValueError('DSN boundary is not a complete rectangle')
        if any(abs(got-want)>Decimal('0.5') for got,want in zip(bounds,expected)):
            raise ValueError('fractional Native rectangle exceeds observed export discrepancy domain')
        rounded=[(v*precision).to_integral_value(rounding=ROUND_CEILING if i<2 else ROUND_FLOOR)/precision for i,v in enumerate(expected)]
        if rounded[0]>=rounded[2] or rounded[1]>=rounded[3]:raise ValueError('inward export rectangle has no area')
        if not (rounded[0]>=expected[0] and rounded[1]>=expected[1] and rounded[2]<=expected[2] and rounded[3]<=expected[3]):
            raise ValueError('export rectangle would expand original design')
        replacement=copy.deepcopy(shape);offset=2 if shape[0]=='rect' else 3
        for i,value in enumerate(shape[offset:]):
            axis=i%2;v=_number(value)
            if v==bounds[axis]:replacement[offset+i]=a._atom_number(rounded[axis])
            elif v==bounds[axis+2]:replacement[offset+i]=a._atom_number(rounded[axis+2])
            else:raise ValueError('ambiguous fractional rectangle side')
        if replacement[0]=='rect':
            x1,y1,x2,y2=map(_number,replacement[2:]);emitted={(x1,y1),(x1,y2),(x2,y1),(x2,y2)}
        else:
            values=list(map(_number,replacement[3:]));emitted=set(zip(values[::2],values[1::2]))
        if emitted!={(rounded[0],rounded[1]),(rounded[0],rounded[3]),(rounded[2],rounded[1]),(rounded[2],rounded[3])}:
            raise ValueError('emitted fractional boundary differs from source-derived rectangle')
        inward={'policy':'source-bound-inward-dsn-grid-v1','grid_um':a._atom_number(1/precision),
            'source_bounds_um':[a._atom_number(v) for v in expected],
            'observed_export_bounds_um':[a._atom_number(v) for v in bounds],
            'output_bounds_um':[a._atom_number(v) for v in rounded],
            'observed_input_discrepancy_guard_um':'0.5','native_host_version':'10.0.0',
            'input_boundary_ast_sha256':a._digest(sx.dump(shape).encode()),
            'output_boundary_ast_sha256':a._digest(sx.dump(replacement).encode()),
            'output_within_original_boundary':True,'native_design_modified':False}
    value = context['requested_clearance_um']
    if _number(value) != _number(context['original_min_copper_edge_clearance_mm'])*1000 or _number(value) <= 0:
        raise ValueError('edge context changes original minimum')
    changed = copy.deepcopy(tree); target = sx.one(sx.one(changed,'structure'),'boundary')
    if replacement is not None:target[1]=replacement
    target.append(['clearance_class',CLASS]); added = ['rule',*[['clearance',value,['type',pair]] for pair in
        ('default_'+CLASS,'smd_'+CLASS,CLASS+'_'+CLASS)]]
    sx.one(changed,'structure').append(added)
    restored = copy.deepcopy(changed); restored_boundary=sx.one(sx.one(restored,'structure'),'boundary');restored_boundary.pop();sx.one(restored,'structure').pop()
    if replacement is not None:restored_boundary[1]=copy.deepcopy(shape)
    encoded = a._dump_dsn(changed).encode()
    if restored != tree or len(encoded)>sx.MAX_BYTES or a._parse_dsn(encoded.decode()) != changed:
        raise ValueError('edge-only semantic reconstruction failed')
    record.update(applied=True,reason='exact original edge minimum encoded for default/SMD/self pairs',
        output_sha256=a._digest(encoded),source_edge_sha256=context['source_edge_sha256'],
        original_min_copper_edge_clearance_mm=context['original_min_copper_edge_clearance_mm'],
        requested_clearance_um=value,clearance_class=CLASS,exact_edge_only_ast_edit=True)
    if named_scope is not None:
        record.update(named_class_scope=copy.deepcopy(named_scope), dsn_class_identities=class_names,
                      native_class_mapping_required=True, loaded_named_matrix_qualified=False)
    if inward is not None:
        record['inward_boundary']=inward
        record['reason']='original edge minimum encoded on source-contained inward grid rectangle'
    return encoded, record
