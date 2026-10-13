"""Pure, narrow pour-only area qualification and DSN obstacle correction.

No native calls, filesystem writes, routing acceptance or fill verification.
Caller authenticates source/export provenance and performs native validation.
"""
from __future__ import annotations
import copy
import hashlib
import re
from autorouter import sexpr as sx, placement_transform as pt
from autorouter.adapter import _parse_dsn, _dump_dsn, _check_units

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

def _geometry(zone):
    # Reuse the existing exact XY/nanometre/simple-polygon parser. Only a local
    # metadata copy receives the absent/short disabled-placement default.
    z=copy.deepcopy(zone);placement=sx.one(z,'placement')
    if placement is None:z.append(['placement',['enabled','no'],['sheetname','""']])
    elif len(placement)==2 and placement[1]==['enabled','no']:placement.append(['sheetname','""'])
    return pt.source_zones(['kicad_pcb',z])[0]

def _metadata(zone):
    if any(not isinstance(n,list) or not n or not isinstance(n[0],str) or n[0] not in AREA_FIELDS for n in zone[1:]):fail('unknown restricted-zone field')
    for key in AREA_FIELDS:sx.one(zone,key)
    if sx.one(zone,'net')!=['net','0']:fail('pour-only area requires explicit net 0')
    if sx.one(zone,'net_name') is not None and _atom(zone,'net_name')!='':fail('pour-only area requires empty net name')
    placement=sx.one(zone,'placement')
    if placement is not None:
        if (len(placement) not in (2,3) or any(not isinstance(n,list) or len(n)!=2
                or not isinstance(n[0],str) or n[0] not in {'enabled','sheetname'} for n in placement[1:])
                or sx.one(placement,'enabled')!=['enabled','no']):fail('placement must be absent or explicitly disabled')
        if sx.one(placement,'sheetname') is not None:_atom(placement,'sheetname')
    layer=sx.one(zone,'layer');layers=sx.one(zone,'layers')
    if (layer is None)==(layers is None):fail('exactly one explicit F/B.Cu layer selector required')
    selector=layer or layers
    if (layer is not None and len(layer)!=2) or any(not isinstance(v,str) for v in selector[1:]):fail('explicit layer atoms required')
    values=[sx.unquote(v) for v in selector[1:]]
    if not values or len(set(values))!=len(values) or not set(values)<=LAYERS:fail('explicit unique F/B.Cu selectors required')
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
        if any(not isinstance(n,list) or len(n)!=2 or not isinstance(n[0],str) or n[0] not in keys or pt.nm(n[1],1000000)<0 for n in fill[1:]):fail('unknown rule-area fill fields')
        for key in keys:sx.one(fill,key)

def qualify(board):
    """Return only eligible root pour-only records; leave all-allowed intent alone.

    Ordinary copper zones are not rule areas. Other restrictions, restricted
    footprint areas, enabled placement, net bindings and unknown source fields
    reject. This is source-form qualification, never a native acceptance.
    """
    if not isinstance(board,list) or not board or board[0]!='kicad_pcb':fail('native board AST required')
    if sx.children(board,'module'):fail('legacy module alias unsupported')
    zones=sx.children(board,'zone')
    if len(zones)>pt.LIMITS['zones']:fail('zone population ceiling')
    eligible=[]
    for owner in [board]+sx.children(board,'footprint'):
        for zone in sx.children(owner,'zone'):
            if sx.one(zone,'keepout') is None and sx.one(zone,'placement') is None:continue
            flags=_flags(zone)
            restricted={k for k,v in flags.items() if v=='not_allowed'}
            if not restricted:continue  # Existing unrestricted intent is unchanged.
            if owner is not board:fail('footprint restricted rule areas unsupported')
            if restricted!={'copperpour'}:fail('only copper-pour prohibition is qualified')
            _metadata(zone);row=_geometry(zone)
            uid=row['uuid']
            if UUID.fullmatch(uid) is None or sum(n==['uuid','"'+uid+'"'] or n==['uuid',uid] for n in _walk(board))!=1:fail('unique source area UUID required')
            table=sx.one(board,'layers')
            declared=[] if table is None else [sx.unquote(n[1]) for n in table[1:] if isinstance(n,list) and len(n)>1 and isinstance(n[1],str)]
            if any(declared.count(layer)!=1 for layer in row['layers']):fail('area layer must be uniquely declared F/B.Cu')
            row['source_zone_ast_sha256']=sha(sx.dump(zone).encode());eligible.append(row)
    return eligible

def _ring(points):
    # Exact ring equivalence is used only to reject ambiguous attribution;
    # removal still requires the source's ordered points, not a guessed export.
    points=tuple(tuple(p) for p in points)
    return min(seq[i:]+seq[:i] for seq in (points,points[::-1]) for i in range(len(seq)))

def _entries(tree):
    structure=sx.one(tree,'structure')
    if structure is None:fail('DSN structure required')
    entries=[]
    for index,node in enumerate(structure[1:],1):
        if not isinstance(node,list) or not node:continue
        if not isinstance(node[0],str):fail('malformed DSN structure item')
        if 'keepout' not in node[0]:continue
        if node[0] not in pt.KINDS or len(node)!=3 or not isinstance(node[1],str) or not isinstance(node[2],list):fail('unknown keepout identity/geometry')
        polygon=node[2]
        if (len(polygon)<11 or polygon[0]!='polygon' or not isinstance(polygon[1],str) or polygon[1] not in LAYERS|{'signal'}
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
    tree=_parse_dsn(raw_dsn_bytes.decode('utf-8'));_check_units(tree);entries=_entries(tree)
    structure=sx.one(tree,'structure');declared=[n[1] for n in sx.children(structure,'layer') if len(n)>1 and isinstance(n[1],str)]
    # Every root source rule area participates in collision detection, including
    # unchanged all-allowed areas. Copper zones never exported as keepouts do not.
    other=[]
    for zone in sx.children(board,'zone'):
        if sx.one(zone,'keepout') is not None or sx.one(zone,'placement') is not None:
            row=_geometry(zone);other.append(row)
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
