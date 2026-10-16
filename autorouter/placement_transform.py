"""Pure diagnostic: remove only exactly attributed all-allowed placement keepouts.

No I/O, native calls, routing acceptance, or upstream floor-guidance validation.
Caller audits raw->floor-guided first, then this transform, then both adapter.
"""
from __future__ import annotations
import copy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import PurePosixPath
import re
import unicodedata
from autorouter import sexpr as sx, board_floor as g
from autorouter.adapter import _parse_dsn, _dump_dsn, _check_units

POLICY='placement-area-diagnostic-v1'
FLAGS=('tracks','vias','pads','copperpour','footprints')
LAYERS={'F.Cu','B.Cu'}
KINDS={'keepout','wire_keepout','via_keepout'}
LIMITS={'project_files':2000,'project_bytes':32*1024*1024,'zones':64,'points_per_outline':128,'dsn_keepouts':256}
ZONE_FIELDS={'net','net_name','layer','layers','uuid','name','hatch','priority','connect_pads','min_thickness','filled_areas_thickness','keepout','placement','fill','polygon','filled_polygon','fill_segments','locked'}
ROW_FIELDS={'uuid','name','parent','is_rule_area','placement_enabled','placement_source_type','placement_source','disallow','layers','outlines_nm','holes','arc_count','outline_closed'}

def sha(value):return hashlib.sha256(value).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def fail(message):raise ValueError(message)

def inventory(files):
    if not isinstance(files,dict) or not 1<=len(files)<=LIMITS['project_files']:fail('complete bounded byte inventory required')
    total=0;folded=set()
    for name,value in files.items():
        path=PurePosixPath(name)
        if not isinstance(name,str) or path.is_absolute() or '..' in path.parts or str(path)!=name or not isinstance(value,bytes):fail('canonical relative source byte files required')
        normalized=unicodedata.normalize('NFD',name).casefold()
        if normalized in folded:fail('casefold/normalization-colliding project paths unsupported')
        folded.add(normalized)
        if path.suffix.casefold()=='.kicad_dru':fail('custom rules unsupported')
        total+=len(value)
    if total>LIMITS['project_bytes']:fail('project byte ceiling')
    return {key:sha(value) for key,value in sorted(files.items())}

def nm(atom,scale):
    if not isinstance(atom,str):fail('numeric atom required')
    try:value=Decimal(atom)*scale
    except InvalidOperation:fail('invalid coordinate')
    if not value.is_finite() or value!=value.to_integral_value() or abs(value)>2_000_000_000:fail('inexact or out-of-range native coordinate')
    return int(value)

def orientation(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def between(a,b,p):return orientation(a,b,p)==0 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1])
def intersect(a,b,c,d):
    q=[orientation(a,b,c),orientation(a,b,d),orientation(c,d,a),orientation(c,d,b)]
    return (q[0]*q[1]<0 and q[2]*q[3]<0) or any((q[i]==0 and between(*segment)) for i,segment in enumerate(((a,b,c),(a,b,d),(c,d,a),(c,d,b))))

def simple(points):
    if not isinstance(points,list) or not 3<=len(points)<=LIMITS['points_per_outline']:fail('bounded single polygon required')
    if any(not isinstance(p,list) or len(p)!=2 or any(type(v)is not int or abs(v)>2_000_000_000 for v in p) for p in points):fail('integer points required')
    if len({tuple(p) for p in points})!=len(points):fail('duplicate polygon point')
    edges=list(zip(points,points[1:]+points[:1]));area=sum(a[0]*b[1]-a[1]*b[0] for a,b in edges)
    if area==0:fail('degenerate polygon')
    for i,(a,b) in enumerate(edges):
        # Collinear turns unsupported, avoiding retraced or ambiguous iterator geometry.
        if orientation(points[i-1],a,b)==0:fail('collinear polygon turn unsupported')
        for j,(c,d) in enumerate(edges[i+1:],i+1):
            if j==i+1 or (i==0 and j==len(edges)-1):continue
            if intersect(a,b,c,d):fail('self-intersecting polygon')
    return points

def bbox(points):return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
def overlap(a,b):return not(a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1])

def atom(node,key,default=None):
    n=sx.one(node,key)
    if n is None:
        if default is not None:return default
        fail('missing '+key)
    if len(n)!=2 or not isinstance(n[1],str):fail('malformed '+key)
    return sx.unquote(n[1])

def rectangle(board):
    layers=sx.one(board,'layers')
    if layers is None:fail('source layer table required')
    copper=[sx.unquote(n[1]) for n in layers[1:] if isinstance(n,list) and len(n)>1 and sx.unquote(n[1]).endswith('.Cu')]
    if len(copper)!=2 or set(copper)!=LAYERS:fail('two canonical copper layers required')
    def has_edge(node):
        return isinstance(node,list) and ((len(node)==2 and node[0]=='layer' and isinstance(node[1],str) and sx.unquote(node[1])=='Edge.Cuts') or any(has_edge(n) for n in node))
    if any(has_edge(fp) for fp in sx.children(board,'footprint')):fail('footprint board-edge geometry unsupported')
    edges=[]
    for node in board[1:]:
        if not isinstance(node,list):continue
        selector=sx.one(node,'layer')
        if selector is None:continue
        if len(selector)!=2 or not isinstance(selector[1],str):fail('malformed source layer selector')
        if sx.unquote(selector[1])!='Edge.Cuts':continue
        if node[0]!='gr_line':fail('only four line outer rectangle supported')
        points=[]
        for key in ('start','end'):
            part=sx.one(node,key)
            if part is None or len(part)!=3:fail('edge endpoints required')
            points.append(tuple(nm(v,1000000) for v in part[1:]))
        if points[0]==points[1] or (points[0][0]!=points[1][0] and points[0][1]!=points[1][1]):fail('axis aligned nonzero edge required')
        edges.append(tuple(sorted(points)))
    if len(edges)!=4 or len(set(edges))!=4:fail('exactly four distinct edges required; cutouts unsupported')
    vertices={p for edge in edges for p in edge};xs={p[0] for p in vertices};ys={p[1] for p in vertices}
    if len(vertices)!=4 or len(xs)!=2 or len(ys)!=2:fail('one outer rectangle required')
    if any(sum(p in edge for edge in edges)!=2 for p in vertices):fail('closed rectangular edge chain required')
    return sorted(edges)

def boundary(tree,edges):
    structure=sx.one(tree,'structure');node=sx.one(structure or [],'boundary')
    if node is None or len(node)!=2 or not isinstance(node[1],list):fail('one exact DSN boundary required')
    path=node[1]
    if len(path)!=13 or path[:3]!=['path','pcb','0']:fail('one closed rectangular DSN boundary required')
    points=[[nm(path[i],1000),-nm(path[i+1],1000)] for i in range(3,len(path),2)]
    if points[0]!=points[-1]:fail('unclosed DSN boundary')
    simple(points[:-1]);observed=sorted(tuple(sorted((tuple(a),tuple(b)))) for a,b in zip(points,points[1:]))
    if observed!=edges:fail('DSN/source outer rectangle mismatch')

def source_zones(board, *, copper_layers=None):
    # Explicit pour caller only; normal placement remains exactly F/B.
    allowed = LAYERS
    if copper_layers is not None:
        if copper_layers != ('F.Cu','In1.Cu','In2.Cu','B.Cu'):
            fail('explicit canonical four-copper context required')
        allowed = set(copper_layers)
    if not isinstance(board,list) or board[0]!='kicad_pcb':fail('native source board required')
    if sx.children(board,'module'):fail('legacy module footprint alias unsupported')
    for fp in sx.children(board,'footprint'):
        if sx.children(fp,'zone'):fail('footprint zones unsupported')
    zones=sx.children(board,'zone')
    if len(zones)>LIMITS['zones']:fail('zone population ceiling')
    rows=[];ids=set()
    for z in zones:
        if any(not isinstance(n,list) or not n or n[0] not in ZONE_FIELDS for n in z[1:]):fail('unknown zone source field')
        # Only saved fill may repeat; every other source attribute is a singleton.
        for key in ZONE_FIELDS-{'filled_polygon','fill_segments'}:sx.one(z,key)
        uid=atom(z,'uuid')
        if re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',uid) is None or uid in ids:fail('unique native zone UUID required')
        ids.add(uid);layer=sx.one(z,'layer');layers=sx.one(z,'layers')
        if (layer is None)==(layers is None):fail('exactly one zone layer selector required')
        if layer is not None and len(layer)!=2:fail('singular layer needs one atom')
        ls=[sx.unquote(x) for x in (layer or layers)[1:]]
        if not ls or len(set(ls))!=len(ls) or not set(ls)<=allowed:fail('unsupported or duplicate zone layers')
        polygon=sx.one(z,'polygon');pts=sx.one(polygon,'pts') if polygon else None
        if polygon is None or len(polygon)!=2 or pts is None or any(not isinstance(pt,list) or len(pt)!=3 or pt[0]!='xy' for pt in pts[1:]):fail('one XY polygon without arcs/holes required')
        points=simple([[nm(pt[1],1000000),nm(pt[2],1000000)] for pt in pts[1:]])
        ko=sx.one(z,'keepout');place=sx.one(z,'placement');is_rule=ko is not None or place is not None
        row={'uuid':uid,'name':atom(z,'name',''),'parent':'board','is_rule_area':is_rule,'layers':sorted(ls),'outlines_nm':[points],'holes':[0],'arc_count':0,'outline_closed':[True]}
        if is_rule:
            if ko is None or len(ko)!=6 or any(not isinstance(n,list) or len(n)!=2 or n[0] not in FLAGS or n[1] not in {'allowed','not_allowed'} for n in ko[1:]) or {n[0] for n in ko[1:]}!=set(FLAGS):fail('all five explicit unique keepout fields required')
            row['disallow']={key:atom(ko,key)=='not_allowed' for key in FLAGS}
            if place is None or len(place)!=3 or {n[0] for n in place[1:] if isinstance(n,list) and n}!={'enabled','sheetname'}:fail('explicit enabled and SHEETNAME placement required')
            enabled=atom(place,'enabled')
            if enabled not in {'yes','no'}:fail('placement enabled boolean required')
            row.update(placement_enabled=enabled=='yes',placement_source_type='SHEETNAME',placement_source=atom(place,'sheetname'))
        rows.append(row)
    return rows

def native_binding(original,native_input,board_name,obs,raw):
    original_hashes=inventory(original);input_hashes=inventory(native_input)
    if '/' in board_name or not board_name.endswith('.kicad_pcb'):fail('board basename required')
    project_name=board_name[:-10]+'.kicad_pro'
    if board_name not in original or project_name not in original or set(original)!=set(native_input):fail('complete same-basename project required')
    if any(original[name]!=native_input[name] for name in original if name!=board_name):fail('native input project constraints changed')
    source=sx.parse(original[board_name].decode());task=sx.parse(native_input[board_name].decode())
    if sx.children(source,'module') or sx.children(task,'module'):fail('legacy module footprint alias unsupported')
    if task!=source and task!=g.task_from_source(source):fail('native input must be exact original or exact existing stripped task')
    edges=rectangle(source)
    expected={'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','board_sha256':sha(native_input[board_name]),'project_sha256':sha(native_input[project_name]),'dsn_sha256':sha(raw),'input_hashes_before':input_hashes,'input_hashes_after':input_hashes,'board_saved':False,'footprint_rulearea_count':0,'footprint_zone_count':0}
    if any(obs.get(k)!=v or type(obs.get(k))is not type(v) for k,v in expected.items()):fail('native observation/input/hash/schema binding differs')
    if not isinstance(obs.get('source'),str) or PurePosixPath(obs['source']).name!=board_name or not PurePosixPath(obs['source']).is_absolute() or '..' in PurePosixPath(obs['source']).parts:fail('native board source identity differs')
    rows=source_zones(task);native_rows=obs.get('zones')
    if not isinstance(native_rows,list) or len(native_rows)!=len(rows):fail('native zone census mismatch')
    byid={}
    for row in native_rows:
        if not isinstance(row,dict) or set(row)!=ROW_FIELDS:fail('missing/unknown native zone fields')
        if not isinstance(row['uuid'],str) or row['uuid'] in byid:fail('duplicate/invalid native zone UUID')
        if row['placement_source_type'] not in {'SHEETNAME','COMPONENT_CLASS','GROUP_PLACEMENT','DESIGN_BLOCK'} or not isinstance(row['placement_source'],str):fail('unknown native placement source enum')
        if any(type(row[k])is not bool for k in ('is_rule_area','placement_enabled')):fail('native zone booleans required')
        if not isinstance(row['disallow'],dict) or set(row['disallow'])!=set(FLAGS) or any(type(v)is not bool for v in row['disallow'].values()):fail('native disallow booleans required')
        if type(row['arc_count'])is not int or row['arc_count']!=0 or row['holes']!=[0] or any(type(v)is not int for v in row['holes']) or row['outline_closed']!=[True] or any(type(v)is not bool for v in row['outline_closed']):fail('unsupported native holes/arcs/open contour')
        if not isinstance(row['outlines_nm'],list) or len(row['outlines_nm'])!=1:fail('single native outline required')
        simple(row['outlines_nm'][0]);byid[row['uuid']]=row
    if set(byid)!={r['uuid'] for r in rows}:fail('native zone identity mismatch')
    for row in rows:
        observed=byid[row['uuid']]
        for key,value in row.items():
            actual=sorted(observed[key]) if key=='layers' else observed[key]
            if actual!=value:fail('source/native zone discrepancy: '+key)
    return rows,edges,{'original_project_sha256':original_hashes,'native_input_sha256':input_hashes,'observation_sha256':sha(canonical(obs))}

def keepouts(tree):
    structure=sx.one(tree,'structure')
    if structure is None:fail('DSN structure required')
    result=[]
    for index,node in enumerate(structure[1:],1):
        if not isinstance(node,list) or not node or 'keepout' not in node[0]:continue
        if node[0] not in KINDS or len(node)!=3 or node[1]!='""' or not isinstance(node[2],list):fail('unknown keepout identity/geometry')
        polygon=node[2]
        if len(polygon)<11 or polygon[0]!='polygon' or polygon[1] not in LAYERS|{'signal'} or nm(polygon[2],1000)!=0 or (len(polygon)-3)%2:fail('simple closed zero-width keepout polygon required')
        points=[[nm(polygon[i],1000),-nm(polygon[i+1],1000)] for i in range(3,len(polygon),2)]
        if points[0]!=points[-1]:fail('native exported closed polygon required')
        simple(points[:-1]);result.append({'index':index,'node':node,'layer':polygon[1],'points':points[:-1],'bbox':bbox(points[:-1])})
    if len(result)>LIMITS['dsn_keepouts']:fail('keepout population ceiling')
    # Unsupported image-local keepouts cannot hide attribution collisions.
    lib=sx.one(tree,'library')
    for image in sx.children(lib or [],'image'):
        if any(isinstance(n,list) and n and 'keepout' in n[0] for n in image):fail('image keepouts unsupported in initial diagnostic')
    return result

def transform(original_files,native_input_files,board_name,observation,raw_dsn,guided_dsn):
    """Return transformed bytes+receipt; all inputs are immutable caller byte snapshots."""
    rows,edges,binding=native_binding(original_files,native_input_files,board_name,observation,raw_dsn)
    raw=_parse_dsn(raw_dsn.decode());guided=_parse_dsn(guided_dsn.decode());_check_units(raw);_check_units(guided)
    boundary(raw,edges);boundary(guided,edges)
    for tree in (raw,guided):
        if sx.one(sx.one(tree,'parser'),'host_version')!=['host_version','"10.0.0"']:fail('DSN pinned native host version differs')
    raw_keep=keepouts(raw);entries=keepouts(guided)
    if [r['node'] for r in raw_keep]!=[r['node'] for r in entries]:fail('upstream guidance changed keepout census')
    # Under the rectangle/no-image-keepout scope, every structure keepout must
    # originate in a board rule area. Do not silently bless an unexplained extra.
    attributed=set()
    for row in rows:
        if not row['is_rule_area']:continue
        flags=row['disallow'];kind=('keepout' if flags['tracks']==flags['vias'] else 'wire_keepout' if flags['tracks'] else 'via_keepout')
        for layer in row['layers']:
            matches=[e for e in entries if e['node'][0]==kind and e['layer']==layer and e['points']==row['outlines_nm'][0]]
            if len(matches)!=1 or matches[0]['index'] in attributed:fail('complete typed rule-area export census not bijective')
            attributed.add(matches[0]['index'])
    if attributed!={e['index'] for e in entries}:fail('unexplained extra DSN structure keepout')
    eligible=[r for r in rows if r['is_rule_area'] and r['placement_enabled'] and not any(r['disallow'].values())]
    if not eligible:fail('no eligible enabled all-allowed placement areas')
    removed=[];indices=set()
    for row in eligible:
        points=row['outlines_nm'][0];box=bbox(points)
        for layer in row['layers']:
            matches=[entry for entry in entries if entry['node'][0]=='keepout' and entry['layer']==layer and entry['points']==points]
            if len(matches)!=1 or matches[0]['index'] in indices:fail('placement keepout must match bijectively')
            match=matches[0]
            for other in rows:
                if other['uuid']!=row['uuid'] and other['is_rule_area'] and layer in other['layers'] and overlap(box,bbox(other['outlines_nm'][0])):fail('overlapping rule-area provenance unsupported')
            for other in entries:
                if other['index']!=match['index'] and other['layer'] in {layer,'signal'} and overlap(box,other['bbox']):fail('overlapping/duplicate exported keepout provenance unsupported')
            indices.add(match['index']);removed.append({'source_zone_uuid':row['uuid'],'layer':layer,'structure_index':match['index'],'entry':copy.deepcopy(match['node'])})
    output=copy.deepcopy(guided);structure=sx.one(output,'structure');structure[:]=[n for i,n in enumerate(structure) if i not in indices]
    result=_dump_dsn(output).encode();reparsed=_parse_dsn(result.decode())
    if reparsed!=output:fail('output AST roundtrip differs')
    receipt={'schema':1,'policy':POLICY,'order':'raw -> externally audited floor guidance -> this placement transform -> both adapter',**binding,
             'raw_dsn_sha256':sha(raw_dsn),'guided_input_sha256':sha(guided_dsn),'output_sha256':sha(result),'removed':removed,
             'removed_count':len(removed),'kept_keepout_count':len(entries)-len(removed),'source_zone_count':len(rows),
             'unmatched_entries_ast_identical':True,'routing_accepted':False,'native_qualification':False,
             'scope':'bounded pure interchange attribution only; caller authenticates same-load process/tool provenance, upstream guidance and final native acceptance',
             'limits':dict(LIMITS)}
    return result,receipt
