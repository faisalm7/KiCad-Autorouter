"""Pure, narrow pour-only area qualification and DSN obstacle correction.

No native calls, filesystem writes, routing acceptance or fill verification.
Caller authenticates source/export provenance and performs native validation.
"""
from __future__ import annotations
import copy
import hashlib
import re
from autorouter import config as c, sexpr as sx, placement_transform as pt
from autorouter.adapter import _parse_dsn, _dump_dsn, _check_units
from autorouter.floor_context import AREA_LIMITS

POLICY='root-pour-only-dsn-v1'
FLAGS=pt.FLAGS
LAYERS=pt.LAYERS
AREA_FIELDS=pt.ZONE_FIELDS-{'filled_polygon','fill_segments'}
UUID=re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')

def fail(message):raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def _atom(node,key):return pt.atom(node,key)
def _walk(node):
    if not isinstance(node,list):return
    yield node
    for child in node[1:]:
        if isinstance(child,list):yield from _walk(child)

def _flags(zone):
    ko=sx.one(zone,'keepout')
    if (ko is None or len(ko)!=6 or any(not isinstance(n,list) or len(n)!=2
            or not isinstance(n[0],str) or not isinstance(n[1],str)
            or n[0] not in FLAGS or n[1] not in {'allowed','not_allowed'} for n in ko[1:])
            or {n[0] for n in ko[1:]}!=set(FLAGS)):
        fail('all five explicit unique keepout flags required')
    return {n[0]:n[1] for n in ko[1:]}

def source_layers(board):
    """Only the existing two-layer path or exact qualified modern four-copper."""
    table=sx.one(board,'layers',[])
    names=[sx.unquote(row[1]) for row in table[1:]
           if isinstance(row,list) and len(row)>2 and isinstance(row[1],str)
           and (sx.unquote(row[1]).endswith('.Cu') or row[2] in {'signal','power','mixed','jumper'})]
    if len(names)==4:
        from .netclass import four_copper_source_layers
        return tuple(four_copper_source_layers(board))
    # Preserve the established two-layer source qualification unchanged.
    return ('F.Cu','B.Cu')


def _geometry(zone,layers=('F.Cu','B.Cu')):
    # Reuse the existing exact XY/nanometre/simple-polygon parser. Only a local
    # metadata copy receives the absent/short disabled-placement default.
    z=copy.deepcopy(zone);placement=sx.one(z,'placement')
    if placement is None:z.append(['placement',['enabled','no'],['sheetname','""']])
    elif len(placement)==2 and placement[1]==['enabled','no']:placement.append(['sheetname','""'])
    return pt.source_zones(['kicad_pcb',z],**({'copper_layers':layers} if len(layers)==4 else {}))[0]

def _metadata(zone,layers=('F.Cu','B.Cu')):
    if any(not isinstance(n,list) or not n or not isinstance(n[0],str) or n[0] not in AREA_FIELDS for n in zone[1:]):fail('unknown restricted-zone field')
    for key in AREA_FIELDS:sx.one(zone,key)
    if len(layers)==4:
        if sx.one(zone,'net') is not None:fail('four-copper pour-only area requires omitted net; numeric net 0 transport remains unsupported')
    elif sx.one(zone,'net')!=['net','0']:fail('pour-only area requires explicit net 0')
    if sx.one(zone,'net_name') is not None and _atom(zone,'net_name')!='':fail('pour-only area requires empty net name')
    placement=sx.one(zone,'placement')
    if placement is not None:
        if (len(placement) not in (2,3) or any(not isinstance(n,list) or len(n)!=2
                or not isinstance(n[0],str) or n[0] not in {'enabled','sheetname'} for n in placement[1:])
                or sx.one(placement,'enabled')!=['enabled','no']):fail('placement must be absent or explicitly disabled')
        if sx.one(placement,'sheetname') is not None:_atom(placement,'sheetname')
    layer=sx.one(zone,'layer');multi=sx.one(zone,'layers')
    if (layer is None)==(multi is None):fail('exactly one explicit copper layer selector required')
    selector=layer or multi
    if (layer is not None and len(layer)!=2) or any(not isinstance(v,str) for v in selector[1:]):fail('explicit layer atoms required')
    values=[sx.unquote(v) for v in selector[1:]]
    if not values or len(set(values))!=len(values) or not set(values)<=set(layers):fail('explicit unique declared copper selectors required')
    for key in ('name','uuid'):
        if sx.one(zone,key) is not None:_atom(zone,key)
    hatch=sx.one(zone,'hatch')
    if hatch is not None:
        if len(hatch)!=3 or hatch[1] not in {'none','edge','full'} or pt.nm(hatch[2],1000000)<0:fail('unknown hatch fields')
    connect=sx.one(zone,'connect_pads')
    if connect is not None:
        if len(connect) not in (1,2) or (len(connect)==2 and (not isinstance(connect[1],list)
                or len(connect[1])!=2 or connect[1][0]!='clearance'
                or pt.nm(connect[1][1],1000000)<0)):fail('unknown connect_pads fields')
    for key in ('min_thickness',):
        if sx.one(zone,key) is not None and pt.nm(_atom(zone,key),1000000)<0:fail('negative '+key)
    for key in ('filled_areas_thickness','locked'):
        if sx.one(zone,key) is not None and _atom(zone,key) not in {'yes','no'}:fail('unknown '+key)
    if sx.one(zone,'priority') is not None and re.fullmatch(r'[0-9]+',_atom(zone,'priority')) is None:fail('integer priority required')
    fill=sx.one(zone,'fill')
    if fill is not None:
        keys={'thermal_gap','thermal_bridge_width'}
        if len(layers)==4:keys.add('island_removal_mode')
        for n in fill[1:]:
            if not isinstance(n,list) or len(n)!=2 or not isinstance(n[0],str) or n[0] not in keys:fail('unknown rule-area fill fields')
            if n[0]=='island_removal_mode':
                if n!=['island_removal_mode','0']:fail('only observed island-removal mode 0 is supported')
            elif pt.nm(n[1],1000000)<0:fail('negative rule-area fill value')
        for key in keys:sx.one(fill,key)
    if len(layers)==4 and (fill is None or sx.one(fill,'island_removal_mode')!=['island_removal_mode','0']):fail('four-copper pour-only area requires explicit island-removal mode 0')

def qualify(board):
    """Return only eligible root pour-only records; leave all-allowed intent alone.

    Ordinary copper zones are not rule areas. Other restrictions, restricted
    footprint areas, enabled placement, net bindings and unknown source fields
    reject. This is source-form qualification, never a native acceptance.
    """
    if not isinstance(board,list) or not board or board[0]!='kicad_pcb':fail('native board AST required')
    if sx.children(board,'module'):fail('legacy module alias unsupported')
    zones=sx.children(board,'zone')
    eligible=[]
    for owner in [board]+sx.children(board,'footprint'):
        for zone in sx.children(owner,'zone'):
            if sx.one(zone,'keepout') is None and sx.one(zone,'placement') is None:continue
            flags=_flags(zone)
            restricted={k for k,v in flags.items() if v=='not_allowed'}
            if not restricted:continue  # Existing unrestricted intent is unchanged.
            if owner is not board:fail('footprint restricted rule areas unsupported')
            if restricted!={'copperpour'}:fail('only copper-pour prohibition is qualified')
            layers=source_layers(board);_metadata(zone,layers);row=_geometry(zone,layers)
            uid=row['uuid']
            if UUID.fullmatch(uid) is None or sum(n==['uuid','"'+uid+'"'] or n==['uuid',uid] for n in _walk(board))!=1:fail('unique source area UUID required')
            table=sx.one(board,'layers')
            declared=[] if table is None else [sx.unquote(n[1]) for n in table[1:] if isinstance(n,list) and len(n)>1 and isinstance(n[1],str)]
            if any(declared.count(layer)!=1 for layer in row['layers']):fail('area layer must be uniquely declared copper')
            row['source_zone_ast_sha256']=sha(sx.dump(zone).encode());eligible.append(row)
    if eligible and len(zones)>AREA_LIMITS['zones']:fail('zone population ceiling')
    if eligible and any(sx.children(fp,'zone') for fp in sx.children(board,'footprint')):fail('footprint zones outside pour-only native audit scope')
    return eligible

def _ring(points):
    # Exact ring equivalence is used only to reject ambiguous attribution;
    # removal still requires the source's ordered points, not a guessed export.
    points=tuple(tuple(p) for p in points)
    return min(seq[i:]+seq[:i] for seq in (points,points[::-1]) for i in range(len(seq)))

def _entries(tree,layers=('F.Cu','B.Cu')):
    structure=sx.one(tree,'structure')
    if structure is None:fail('DSN structure required')
    entries=[]
    for index,node in enumerate(structure[1:],1):
        if not isinstance(node,list) or not node:continue
        if not isinstance(node[0],str):fail('malformed DSN structure item')
        if 'keepout' not in node[0]:continue
        if node[0] not in pt.KINDS or len(node)!=3 or not isinstance(node[1],str) or not isinstance(node[2],list):fail('unknown keepout identity/geometry')
        polygon=node[2]
        if (len(polygon)<11 or polygon[0]!='polygon' or not isinstance(polygon[1],str) or polygon[1] not in set(layers)|{'signal'}
                or pt.nm(polygon[2],1000)!=0 or (len(polygon)-3)%2):fail('closed zero-width polygon keepout required')
        points=[[pt.nm(polygon[i],1000),-pt.nm(polygon[i+1],1000)] for i in range(3,len(polygon),2)]
        if points[0]!=points[-1]:fail('native closed keepout polygon required')
        points=pt.simple(points[:-1])
        entries.append({'index':index,'node':node,'layer':polygon[1],'points':points,'ring':_ring(points)})
    if len(entries)>pt.LIMITS['dsn_keepouts']:fail('DSN keepout population ceiling')
    root_nodes={id(entry['node']) for entry in entries}
    for node in _walk(tree):
        if node and isinstance(node[0],str) and 'keepout' in node[0] and id(node) not in root_nodes:fail('non-root keepout provenance unsupported')
    return entries

def correct(source_board_bytes,raw_dsn_bytes):
    """Return corrected bytes and pure attribution; never alters either input."""
    if not isinstance(source_board_bytes,bytes) or not isinstance(raw_dsn_bytes,bytes):fail('immutable source/DSN bytes required')
    if len(raw_dsn_bytes)>sx.MAX_BYTES:fail('DSN byte ceiling')
    board=sx.parse(source_board_bytes.decode('utf-8'));areas=qualify(board)
    base={'schema':1,'policy':POLICY,'source_board_sha256':sha(source_board_bytes),'input_dsn_sha256':sha(raw_dsn_bytes),
          'native_observation_verified':False,'native_fill_verified':False,'routing_accepted':False}
    if not areas:return raw_dsn_bytes,dict(base,output_sha256=sha(raw_dsn_bytes),removed=[],removed_count=0,untargeted_ast_identical=True)
    layers=source_layers(board)
    tree=_parse_dsn(raw_dsn_bytes.decode('utf-8'));_check_units(tree);entries=_entries(tree,layers)
    structure=sx.one(tree,'structure');declared=[n[1] for n in sx.children(structure,'layer') if len(n)>1 and isinstance(n[1],str)]
    # Every root source rule area participates in collision detection, including
    # unchanged all-allowed areas. Copper zones never exported as keepouts do not.
    other=[]
    for zone in sx.children(board,'zone'):
        if sx.one(zone,'keepout') is not None or sx.one(zone,'placement') is not None:
            row=_geometry(zone,layers);other.append(row)
    removed=[];indices=set()
    for area in areas:
        points=area['outlines_nm'][0];ring=_ring(points)
        for layer in area['layers']:
            if declared.count(layer)!=1:fail('explicit unique source/DSN layer required')
            if sum(layer in row['layers'] and _ring(row['outlines_nm'][0])==ring for row in other)!=1:fail('colliding source area attribution')
            candidates=[e for e in entries if e['layer'] in {layer,'signal'} and e['ring']==ring]
            if len(candidates)!=1:fail('generic exported keepout must match bijectively')
            entry=candidates[0]
            if (entry['layer']!=layer or entry['node'][:2]!=['keepout','""']
                    or entry['points']!=points or entry['index'] in indices):fail('only exact ordered native generic keepout is removable')
            indices.add(entry['index']);removed.append({'source_zone_uuid':area['uuid'],'source_zone_ast_sha256':area['source_zone_ast_sha256'],
                'layer':layer,'structure_index':entry['index'],'entry':copy.deepcopy(entry['node'])})
    output=copy.deepcopy(tree);st=sx.one(output,'structure');st[:]=[n for i,n in enumerate(st) if i not in indices]
    result=_dump_dsn(output).encode('utf-8')
    if _parse_dsn(result.decode('utf-8'))!=output:fail('output AST roundtrip differs')
    receipt=dict(base,output_sha256=sha(result),removed=removed,removed_count=len(removed),kept_keepout_count=len(entries)-len(removed),
                 untargeted_ast_identical=True,source_areas=areas,scope='Pure exact source/export attribution only; native fill and acceptance required separately.')
    return result,receipt

AUDIT_POLICY='root-pour-only-saved-fill-v1'
FOUR_AUDIT_POLICY='root-four-copper-pour-only-saved-fill-v1'

def fill_matrix(board,areas):
    """Complete source-declared area × ordinary root zone × copper-layer matrix."""
    copper_layers=source_layers(board)
    result=[];zones=sx.children(board,'zone');ids=[_atom(z,'uuid') for z in zones]
    if len(set(ids))!=len(ids):fail('unique root zone UUIDs required for pour audit')
    for area in areas:
        for zone in zones:
            if sx.one(zone,'keepout') is not None or sx.one(zone,'placement') is not None:continue
            layer=sx.one(zone,'layer');layers=sx.one(zone,'layers')
            if (layer is None)==(layers is None):fail('explicit ordinary zone layer selector required')
            selector=layer or layers
            if (layer is not None and len(layer)!=2) or any(not isinstance(v,str) for v in selector[1:]):fail('explicit ordinary zone layer atoms required')
            names=[sx.unquote(v) for v in selector[1:]]
            if not names or len(set(names))!=len(names) or not set(names)<=set(copper_layers):fail('ordinary pour audit zone layers require explicit declared copper')
            if sx.children(zone,'fill_segments'):fail('legacy fill segments outside pour audit scope')
            for name in copper_layers:
                if name not in names:continue
                filled=[]
                for node in sx.children(zone,'filled_polygon'):
                    ln=sx.one(node,'layer')
                    if ln is None or len(ln)!=2 or not isinstance(ln[1],str):fail('explicit saved fill layer required')
                    if len(copper_layers)==4 and sx.unquote(ln[1]) not in names:fail('saved fill outside declared zone layers')
                    if sx.unquote(ln[1])==name:filled.append(node)
                result.append({'area_uuid':area['uuid'],'zone_uuid':_atom(zone,'uuid'),'layer':name,
                    'applicable':name in area['layers'],'stored_fill_node_count':len(filled),
                    'stored_fill_nodes_sha256':sha(sx.dump(filled).encode())})
    return result

def verify_native_record(record,candidate):
    """Bound local readback, not fresh native geometry or JSON authentication."""
    from pathlib import Path
    from autorouter.placement_clearance import read_bytes
    from autorouter.floor_route import canonical
    path=Path(candidate);raw=read_bytes(path);tree=sx.parse(raw.decode());areas=qualify(tree)
    if not areas:fail('pour audit requires original qualified areas')
    layers=source_layers(tree);four=len(layers)==4
    expected={'schema':2 if four else 1,'policy':FOUR_AUDIT_POLICY if four else AUDIT_POLICY,'native_version':c.NATIVE_VERSION,'source':str(path),
        'board_sha256':sha(raw),'project_sha256':sha(read_bytes(path.with_suffix('.kicad_pro'))),
        'board_saved':False,'source_areas':areas,'passed':True}
    if four:
        expected['copper_layers']=[dict(id=code,name=name,type='signal',index=i) for i,(code,name) in enumerate(zip((0,4,6,2),layers))]
        expected['native_area_nets']=[dict(uuid=row['uuid'],netcode=0,netname='',island_removal_mode=0) for row in areas]
    if set(record)!=set(expected)|{'native_areas','fill_checks','native_zone_uuids'}:fail('missing/unknown pour audit fields')
    if any(canonical(record.get(k))!=canonical(v) for k,v in expected.items()):fail('pour audit source/policy/hash differs')
    expected_native=[{k:v for k,v in row.items() if k!='source_zone_ast_sha256'} for row in areas]
    if canonical(record['native_areas'])!=canonical(expected_native):fail('native pour area flags/geometry differ')
    ids=sorted(_atom(z,'uuid') for z in sx.children(tree,'zone'))
    if record['native_zone_uuids']!=ids:fail('native root zone census differs')
    matrix=fill_matrix(tree,areas);checks=record['fill_checks']
    if not isinstance(checks,list) or len(checks)!=len(matrix):fail('pour audit observation matrix incomplete')
    for expected_row,row in zip(matrix,checks):
        if not isinstance(row,dict) or set(row)!=set(expected_row)|{'native_fill_outline_count','intersection','passed'}:fail('pour observation fields differ')
        if any(canonical(row.get(k))!=canonical(v) for k,v in expected_row.items()):fail('pour observation/source fill differs')
        if type(row['native_fill_outline_count'])is not int or row['native_fill_outline_count']!=expected_row['stored_fill_node_count']:fail('native stored fill census differs')
        if type(row['passed'])is not bool or row['passed']is not True:fail('saved native fill intersects prohibited area')
        if not isinstance(row['intersection'],list):fail('native intersection geometry missing')
        if expected_row['applicable'] and row['intersection']:fail('stored fill intrusion in pour-only area')
    return True
