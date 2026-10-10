"""Bounded identity observations only; no custom-pad/routing acceptance policy."""
import copy
from decimal import Decimal
from autorouter import sexpr as sx,board_floor as g,pipeline as p,netclass
from autorouter.adapter import _check_units

SEVERITIES={'footprint_symbol_field_mismatch':'warning','missing_tuning_profile':'warning',
            'text_on_edge_cuts':'error','track_on_post_machined_layer':'error'}

def source_notes(board,project):
    if sx.one(board,'version')!=['version','20260206']:raise ValueError('pinned original format differs')
    pads=g.task_pads(board);custom=[];footprints=[]
    for fp in sx.children(board,'footprint'):
        refs=[r for r in sx.children(fp,'property') if sx.unquote(r[1])=='Reference']
        footprints.append({'uuid':sx.unquote(sx.one(fp,'uuid')[1]),'reference':sx.unquote(refs[0][2]),
                           'at':copy.deepcopy(sx.one(fp,'at')),'layer':sx.unquote(sx.one(fp,'layer')[1])})
        for pad in sx.children(fp,'pad'):
            if len(pad)>3 and pad[3]=='custom':
                uid=sx.unquote(sx.one(pad,'uuid')[1])
                custom.append({'uuid':uid,**pads[uid],'pad_ast':copy.deepcopy(pad),
                    'footprint_uuid':sx.unquote(sx.one(fp,'uuid')[1]),'footprint_at':copy.deepcopy(sx.one(fp,'at')),
                    'footprint_layer':copy.deepcopy(sx.one(fp,'layer'))})
    if len(pads)!=247 or len(custom)!=2 or len(sx.children(board,'footprint'))!=63 or len(p.routes(board))!=376:
        raise ValueError('pinned original census differs')
    severities=project['board']['design_settings']['rule_severities']
    if any(severities.get(k)!=v for k,v in SEVERITIES.items()):raise ValueError('original severity intent differs')
    return {'source_pads_identity':pads,'source_nonempty_nets':sorted(g.source_net_identity(board)[0]),
        'source_route_ids':sorted(sx.unquote(sx.one(r,'uuid')[1]) for r in p.routes(board)),
        'custom_pads':sorted(custom,key=lambda row:row['uuid']),'source_footprints':footprints,
        'source_design_settings':copy.deepcopy(project['board']['design_settings']),
        'source_net_settings':copy.deepcopy(project['net_settings']),'new_severity_intent':dict(SEVERITIES),
        'severity_observation':'Source configuration only. Native effective severity/provider execution and schematic field parity are not qualified.',
        'geometry_qualified':False,'routing_accepted':False}

def floor_identity(native,notes,project):
    pads=native['pads'];observed={}
    for row in pads:
        if row['uuid'] in observed:raise ValueError('duplicate native pad UUID')
        observed[row['uuid']]={k:row[k] for k in ('reference','number','net','copper_layers')}
    if observed!=notes['source_pads_identity']:raise ValueError('native original terminal identities differ')
    if sorted(r['uuid'] for r in native['routes'])!=notes['source_route_ids']:raise ValueError('native route identities differ')
    if sorted(r['name'] for r in native['nets'])!=notes['source_nonempty_nets']:raise ValueError('native net identities differ')
    netclass.audit_native({'schema':1,'native_version':native['native_version'],'units':native['units'],'nets':native['nets']},project)

def custom_identity(observation,native,notes):
    if (observation.get('same_loaded_board') is not True or observation.get('routing_accepted') is not False
            or observation.get('geometry_qualified') is not False or observation.get('board_saved') is not False):
        raise ValueError('custom observation scope differs')
    before=observation['observation_before_export'];after=observation['observation_after_export']
    if before!=after:raise ValueError('native export did not restore observed pad state')
    if (type(before.get('schema')) is not int or before['schema']!=1 or before.get('total_pad_count')!=247
            or before.get('routing_accepted') is not False or before.get('geometry_qualified') is not False):
        raise ValueError('custom observation census/schema differs')
    actual=before['pads'];expected={r['uuid']:r for r in notes['custom_pads']}
    if len(actual)!=len(expected) or {r['uuid'] for r in actual}!=set(expected):raise ValueError('custom UUID census differs')
    allpads={r['uuid']:r for r in native['pads']}
    terminal_rows=before['all_terminals'];footprint_rows=before['all_footprints']
    if len(terminal_rows)!=len(allpads) or len({r['uuid'] for r in terminal_rows})!=len(terminal_rows):raise ValueError('custom callback full terminal census differs')
    for terminal in terminal_rows:
        if terminal['uuid'] not in allpads or any(terminal[k]!=allpads[terminal['uuid']][k] for k in ('reference','number','net','netcode','copper_layers','position_nm')):
            raise ValueError('custom callback full terminal mapping differs')
    fps={r['uuid']:r for r in notes['source_footprints']}
    if len(footprint_rows)!=len(fps) or len({r['uuid'] for r in footprint_rows})!=len(fps):raise ValueError('custom callback footprint census differs')
    for fp in footprint_rows:
        if fp['uuid'] not in fps or any(fp[k]!=fps[fp['uuid']][k] for k in ('reference','layer')):raise ValueError('custom callback footprint identity differs')
    for row in actual:
        original=expected[row['uuid']];floor=allpads[row['uuid']]
        if any(row[k]!=original[k] for k in ('reference','number','net','copper_layers','footprint_uuid')):
            raise ValueError('custom original identity differs')
        if any(row[k]!=floor[k] for k in ('netcode','position_nm')):raise ValueError('custom/floor same-load identity differs')
        if row.get('shape')!='custom' or row.get('anchor')!='rect' or row.get('attribute')!='smd':raise ValueError('custom shape/anchor/attribute differs')
        pad=original['pad_ast'];size=sx.one(pad,'size')
        nm=[int(Decimal(atom)*1000000) for atom in size[1:]]
        if row['size_nm']!=nm or row['drill_nm']!=[0,0] or row['offset_nm']!=[0,0]:raise ValueError('custom anchor/drill/offset differs')
        for key in ('merged_local','transformed_world','effective_world'):
            shape=row[key]
            if shape.get('arc_count')!=0 or len(shape.get('outlines',[]))!=1 or shape['outlines'][0].get('holes')!=[]:
                raise ValueError('custom native polygon topology differs')
            outline=shape['outlines'][0]['outline'];points=outline['points_nm']
            if outline.get('closed') is not True or not 3<=len(points)<=32 or shape['total_vertices']!=len(points):raise ValueError('custom polygon structure differs')
            if any(not isinstance(pt,list) or len(pt)!=2 or any(type(v) is not int or abs(v)>10**10 for v in pt) for pt in points):
                raise ValueError('custom polygon coordinates differ')
    return copy.deepcopy(actual)

def dsn_correspondence(raw,native,custom):
    tree=sx.parse(raw.decode());_check_units(tree)
    library=sx.one(tree,'library');placement=sx.one(tree,'placement');network=sx.one(tree,'network')
    if any(x is None for x in (library,placement,network)):raise ValueError('missing DSN context')
    def unique(nodes,label):
        result={}
        for node in nodes:
            name=sx.unquote(node[1])
            if name in result:raise ValueError('duplicate DSN '+label)
            result[name]=node
        return result
    images=unique(sx.children(library,'image'),'image');stacks=unique(sx.children(library,'padstack'),'padstack')
    placed={}
    for component in sx.children(placement,'component'):
        image_id=sx.unquote(component[1])
        if image_id not in images:raise ValueError('unknown DSN image')
        pins={}
        for pin in sx.children(images[image_id],'pin'):
            atoms=[x for x in pin[2:] if isinstance(x,str)]
            if len(atoms)!=3:raise ValueError('ambiguous DSN pin')
            number=sx.unquote(atoms[0]);stack=sx.unquote(pin[1])
            if number in pins or stack not in stacks:raise ValueError('duplicate pin/unknown padstack')
            pins[number]=pin
        for place in sx.children(component,'place'):
            ref=sx.unquote(place[1])
            if ref in placed:raise ValueError('duplicate DSN placement')
            placed[ref]=(image_id,place,pins)
    expected={}
    for pad in native['pads']:
        if pad['netcode']<=0 or not pad['copper_layers']:continue
        token=pad['reference']+'-'+pad['number']
        if token in expected:raise ValueError('ambiguous native connected pin')
        if pad['reference'] not in placed or pad['number'] not in placed[pad['reference']][2]:raise ValueError('native pin missing from DSN placement')
        expected[token]=pad
    exported={}
    for net in sx.children(network,'net'):
        pins=sx.one(net,'pins')
        if pins is None:raise ValueError('missing DSN net terminals')
        for atom in pins[1:]:
            token=sx.unquote(atom)
            if token in exported or token not in expected or expected[token]['net']!=sx.unquote(net[1]):raise ValueError('DSN/native terminal mismatch')
            exported[token]=expected[token]['uuid']
    if set(exported)!=set(expected):raise ValueError('missing DSN terminal')
    rows=[]
    for row in custom:
        image,place,pins=placed[row['reference']];pin=pins[row['number']];stack=stacks[sx.unquote(pin[1])]
        shapes=sx.children(stack,'shape')
        if not shapes or any(len(shape)!=2 or shape[1][0]!='polygon' for shape in shapes):raise ValueError('custom DSN shape is not polygon')
        for shape in shapes:
            polygon=shape[1]
            if len(polygon)<9 or (len(polygon)-3)%2 or Decimal(polygon[2])!=0:raise ValueError('custom DSN polygon form differs')
        rows.append({'uuid':row['uuid'],'reference':row['reference'],'number':row['number'],'net':row['net'],
            'image_id':image,'placement_ast':copy.deepcopy(place),'pin_ast':copy.deepcopy(pin),'padstack_ast':copy.deepcopy(stack)})
    return {'terminal_count':len(exported),'custom_pads':rows,'routing_accepted':False,'geometry_qualified':False,
            'interpretation':'Exact retained identity/AST observation. DSN hull is not native copper; back-side export flips and pin transforms are not geometrically qualified.'}
