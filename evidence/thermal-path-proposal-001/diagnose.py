"""Read-only pure diagnosis; no native imports or board edits."""
import hashlib,json,math,time
from fractions import Fraction
from pathlib import Path
import copper_path as c
ROOT=Path(__file__).resolve().parent
GEOMETRY=ROOT.parent/'native-export-001/geometry.json'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def minimum_segment(a,b,cc,d):
    if c.intersects(a,b,cc,d):return Fraction(0)
    return min(Fraction(*c.point_segment_sq(p,x,y)) for p,x,y in ((a,cc,d),(b,cc,d),(cc,a,b),(d,a,b)))
def drill_census(g):
    holes=[];errors=[]
    for p in g['pads']:
        h=p['effective_hole'];diameter=h['width_nm']
        if diameter<=0:continue
        if h['start_nm']!=h['end_nm'] or not p['drill_is_round'] or diameter%2:
            errors.append({'uuid':p['uuid'],'reason':'noninteger-radius/slot/nonround drill'});continue
        holes.append({'kind':'pad','uuid':p['uuid'],'net_code':p['net_code'],'logical_terminal':p['logical_terminal'],'center':h['start_nm'],'radius':diameter//2})
    layers=[l['id'] for l in g['layers']]
    for v in g['vias']:
        if not set(layers).intersection(v['layer_membership']):continue
        if v['drill_nm']<=0 or v['drill_nm']%2:errors.append({'uuid':v['uuid'],'reason':'via drill unavailable'});continue
        holes.append({'kind':'via','uuid':v['uuid'],'net_code':v['net_code'],'center':v['position_nm'],'radius':v['drill_nm']//2})
    return holes,errors

def exact_pad(p,layer_id):
    rows=[l for l in p['layers'] if l['id']==layer_id]
    if len(rows)!=1:return None
    l=rows[0];h=p['effective_hole'];size=l['size_nm']
    if not (p['is_pth'] and p['drill_is_round'] and l['on_layer'] and l['flash_layer'] and l['shape_is_circle'] and size[0]==size[1] and l['offset_nm']==[0,0] and p['position_nm']==l['shape_position_nm']==h['start_nm']==h['end_nm']):return None
    if not 0<h['width_nm']<size[0] or h['width_nm']%2 or size[0]%2:return None
    return {'uuid':p['uuid'],'terminal':p['logical_terminal'],'net_code':p['net_code'],'center':p['position_nm'],'outer_radius':size[0]//2,'drill_radius':h['width_nm']//2}

def analyze(g):
    holes,errors=drill_census(g);margin=max(1,g['native_max_error_nm']);bodies=[]
    for body in g['bodies']:
        if not body['selected']:continue
        poly=body['outer_nm'];pairs=list(c.edges(poly));cross=[];closest=None
        for i,(a,b) in enumerate(pairs):
            for j,(cc,d) in enumerate(pairs[i+1:],i+1):
                if j==i+1 or (i==0 and j==len(poly)-1):continue
                q=minimum_segment(a,b,cc,d)
                if q==0:cross.append([i,j])
                if closest is None or q<closest[0]:closest=(q,i,j,a,b,cc,d)
        rows=[]
        for hole in holes:
            q,edge_index=min((Fraction(*c.point_segment_sq(hole['center'],a,b)),i) for i,(a,b) in enumerate(pairs))
            inside=c.inside(hole['center'],poly);r=hole['radius']
            relation=('boundary_or_margin_ambiguous' if q<=(r+margin)**2 else 'strict_interior' if inside else 'strict_exterior')
            rows.append({'uuid':hole['uuid'],'kind':hole['kind'],'center_inside_parity':inside,'nearest_edge_index':edge_index,'distance_squared_nm2':[q.numerator,q.denominator],'distance_nm_approx':math.sqrt(float(q)),'circle_boundary_gap_nm_approx':math.sqrt(float(q))-r,'classification':relation})
        q,i,j,a,b,cc,d=closest
        bodies.append({'native_outline_index':body['native_outline_index'],'native_self_intersecting':body['native_self_intersecting'],'vertex_count':len(poly),'nonadjacent_pair_count':len(poly)*(len(poly)-3)//2,'exact_crossings_or_touches':cross,'nearest_nonadjacent_edges':{'indices':[i,j],'segments':[[a,b],[cc,d]],'distance_squared_nm2':[q.numerator,q.denominator],'distance_nm_approx':math.sqrt(float(q))},'drills':rows,'classification_counts':{key:sum(r['classification']==key for r in rows) for key in ('strict_exterior','strict_interior','boundary_or_margin_ambiguous')},'whole_body_certificate_qualified':False,'reasons':['native nanometre collision interpretation does not certify a simple copper body','at least one physical drill lacks the declared positive boundary margin']})
    return {'schema':1,'status':'whole_body_certificate_unsupported','proposal_scene_qualified':False,'native_executed':False,'solver_executed':False,'margin_nm':margin,'margin_policy':'max(native polygon maximum error, 1 nm); fixed before path attempt','physical_holes':holes,'drill_census_errors':errors,'body_diagnoses':bodies}

if __name__=='__main__':
    started=time.monotonic();watched={str(p.relative_to(ROOT.parent/'native-export-001')):digest(p) for p in (ROOT.parent/'native-export-001').rglob('*') if p.is_file()}
    g=json.loads(GEOMETRY.read_text());result=analyze(g)
    result['geometry_sha256']=digest(GEOMETRY);result['script_sha256']=digest(Path(__file__));result['copper_path_sha256']=digest(ROOT/'copper_path.py')
    result['probe_files_unchanged']=all(digest(ROOT.parent/'native-export-001'/p)==sha for p,sha in watched.items());result['probe_files']=watched;result['wall_seconds']=time.monotonic()-started
    with (ROOT/'diagnosis.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'status':result['status'],'physical_holes':len(result['physical_holes']),'bodies':[{k:b[k] for k in ('native_outline_index','classification_counts','nearest_nonadjacent_edges')} for b in result['body_diagnoses']],'probe_files_unchanged':result['probe_files_unchanged'],'wall_seconds':result['wall_seconds']},indent=2))
