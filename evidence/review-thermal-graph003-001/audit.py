"""Independent exact path and saved-input audit; no draft predicates or native execution."""
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
import collections, hashlib, json, math, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p, sexpr as sx
DRAFT=ROOT/'.runs/thermal-generalization-draft-001'
PROBE=DRAFT/'native-export-001';QUAL=DRAFT/'qualification-001'
OUT=Path(__file__).resolve().parent
checks=[];failures=[];paths=[]
def require(ok,name):
    checks.append(name)
    if not ok:failures.append(name)
def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def nm(value):
    n=Decimal(value)*1_000_000
    assert n==n.to_integral_value()
    return int(n)
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def boundary(p,a,b):return cross(a,b,p)==0 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1])
def intersect(a,b,c,d):
    values=cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b)
    return (values[0]*values[1]<0 and values[2]*values[3]<0) or any(v==0 and boundary(q,x,y) for v,q,x,y in ((values[0],c,a,b),(values[1],d,a,b),(values[2],a,c,d),(values[3],b,c,d)))
def point_distance_sq(point,a,b):
    dx=b[0]-a[0];dy=b[1]-a[1];den=dx*dx+dy*dy
    dot=(point[0]-a[0])*dx+(point[1]-a[1])*dy
    if den==0 or dot<=0:return Fraction((point[0]-a[0])**2+(point[1]-a[1])**2)
    if dot>=den:return Fraction((point[0]-b[0])**2+(point[1]-b[1])**2)
    t=Fraction(dot,den)
    return (point[0]-a[0]-t*dx)**2+(point[1]-a[1]-t*dy)**2
def edge_distance_sq(a,b,c,d):
    if intersect(a,b,c,d):return Fraction(0)
    return min(point_distance_sq(a,c,d),point_distance_sq(b,c,d),point_distance_sq(c,a,b),point_distance_sq(d,a,b))
def inside(point,poly):
    winding=0
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if boundary(point,a,b):return False
        if a[1]<=point[1]<b[1] and cross(a,b,point)>0:winding+=1
        elif b[1]<=point[1]<a[1] and cross(a,b,point)<0:winding-=1
    return winding!=0

summary=read(PROBE/'summary.json');g=read(PROBE/'geometry.json');result=read(QUAL/'path-attempt-003.json')
r=read(summary['receipt']);candidate=Path(r['candidate']);source=Path(r['source']);tree=sx.read(candidate)
require(sha(PROBE/'geometry.json')==result['geometry_sha256']==summary['geometry_sha256'],'geometry hashes consistent')
require(sha(QUAL/'attempt_graph_v3.py')==result['script_sha256'] and sha(QUAL/'copper_path.py')==result['copper_path_sha256'],'exact generating code retained')
require(sha(summary['receipt'])==summary['receipt_sha256'],'original receipt still bound')
require(p.tree_hash(source.parent)==summary['source_files']==r['source_hashes'],'current full original source unchanged')
require(p.tree_hash(candidate.parent)==summary['candidate_files'],'current full failed candidate unchanged')
require(sha(candidate)==g['board_sha256']==summary['candidate_sha256']==r['candidate_sha256'],'current candidate board bound')
require(sha(candidate.with_suffix('.kicad_pro'))==g['project_sha256'],'current original project bound')
require(p.immutable(tree)==p.immutable(sx.read(source)),'original immutable geometry preserved')
for file,digest in summary['watched_hashes'].items():require(sha(file)==digest,'current watched file '+Path(file).name)
require(sha(Path(summary['receipt']).parent/'final-drc.json')==r['native_report_sha256'],'current baseline native report hash')
native=p.parse_report(Path(summary['receipt']).parent/'final-drc.json',source.name)
require(native==r['native'] and native['opens']==native['exclusions']==0 and native['blocking']==1,'single native thermal baseline')
require(g['finding'] in native['findings'] and g['finding']['type']=='starved_thermal','exported exact thermal finding bound')
binding=read(Path(summary['receipt']).parent/'final-drc-binding.json')
require(binding['before']==summary['candidate_files'] and p.tree_hash(Path(binding['input']).parent)==binding['after'],'retained final DRC input binding')
require(g['api_error_count']==0 and g['native_max_error_nm']==10000 and g['layers']==[{'id':2,'canonical':'B.Cu','board_name':'bottom_copper'}],'native observation scope')
require(result['wall_seconds']<=result['caps']['seconds'] and result['operations_used']<=result['caps']['operations'],'reported bounded diagnostic cost')
require(not result['native_executed'] and not result['routing_accepted'] and not result['proposal_scene_qualified'],'diagnostic flags remain unqualified')

# Independently reconstruct all pad centers/drills directly from saved S-expressions.
observed_pads={row['uuid']:row for row in g['pads']};pad_records={};holes=[]
for fp in sx.children(tree,'footprint'):
    at=sx.one(fp,'at');fx,fy=map(nm,at[1:3]);angle=int(at[3]) if len(at)>3 else 0
    require(angle%90==0 and sx.unquote(sx.one(fp,'layer')[1])=='F.Cu','supported exact footprint transform '+sx.unquote(sx.one(fp,'uuid')[1]))
    co,si={0:(1,0),90:(0,-1),180:(-1,0),270:(0,1)}[angle%360]
    for pad in sx.children(fp,'pad'):
        uid=sx.unquote(sx.one(pad,'uuid')[1]);at=sx.one(pad,'at');x,y=map(nm,at[1:3]);center=[fx+co*x-si*y,fy+si*x+co*y]
        row=observed_pads[uid];terminal=[sx.unquote(sx.one(fp,'uuid')[1]),sx.unquote(pad[1])]
        require(row['position_nm']==center and row['logical_terminal']==terminal,'native pad center/logical identity '+uid)
        drill=sx.one(pad,'drill');width=nm(drill[1]) if drill else 0
        require(not drill or (len(drill)==2 and drill[1]!='oval'),'ordinary concentric physical pad drill '+uid)
        require(row['effective_hole']=={'start_nm':center,'end_nm':center,'width_nm':width},'native physical pad hole '+uid)
        if width:holes.append({'uuid':uid,'center':center,'radius':Fraction(width,2)})
        pad_records[uid]={'tree':pad,'row':row,'center':center,'terminal':terminal,'drill':width}
require(set(pad_records)==set(observed_pads),'complete native pad population')
observed_vias={row['uuid']:row for row in g['vias']};vias=sx.children(tree,'via')
require({sx.unquote(sx.one(v,'uuid')[1]) for v in vias}==set(observed_vias),'complete native via population')
for via in vias:
    uid=sx.unquote(sx.one(via,'uuid')[1]);center=list(map(nm,sx.one(via,'at')[1:3]));drill=nm(sx.one(via,'drill')[1]);row=observed_vias[uid]
    require(row['position_nm']==center and row['drill_nm']==drill and row['via_type']==4 and row['layer_membership']==[2],'native through-via hole '+uid)
    holes.append({'uuid':uid,'center':center,'radius':Fraction(drill,2)})
require(len(holes)==352==result['physical_hole_count'],'all 352 physical holes independently reconstructed')
zones=[z for z in sx.children(tree,'zone') if sx.unquote(sx.one(z,'uuid')[1])==g['zone_uuid']]
require(len(zones)==1 and int(sx.one(zones[0],'net')[1])==g['net_code'],'target zone identity/net')
filled=sx.children(zones[0],'filled_polygon');bodies={b['native_outline_index']:b for b in g['bodies']}
require(len(filled)==len(bodies)==27,'complete native saved outline population')
for i,fill in enumerate(filled):
    points=[list(map(nm,xy[1:3])) for xy in sx.children(sx.one(fill,'pts'),'xy')]
    require(points==bodies[i]['outer_nm'] and sx.unquote(sx.one(fill,'layer')[1])=='B.Cu','native contour exactly saved polygon '+str(i))

def path_checks(polyline,outline,pad,margin,label):
    poly=bodies[outline]['outer_nm'];legs=list(zip(polyline,polyline[1:])) or [(polyline[0],polyline[0])]
    for i,(a,b) in enumerate(legs):
        distances=[edge_distance_sq(a,b,c,d) for c,d in zip(poly,poly[1:]+poly[:1])]
        require(inside(a,poly) and inside(b,poly) and min(distances)>margin**2,label+'/positive contour clearance leg '+str(i))
        clearance=[(point_distance_sq(h['center'],a,b),h) for h in holes]
        require(all(dist>(h['radius']+margin)**2 for dist,h in clearance),label+'/all physical drills leg '+str(i))
        paths.append({'path':label,'leg':i,'boundary_clearance_nm_approx':math.sqrt(float(min(distances))),
                      'minimum_drill_clearance_nm_approx':min(math.sqrt(float(dist))-float(h['radius']) for dist,h in clearance)})
    size=list(map(nm,sx.one(pad['tree'],'size')[1:3]));endpoint=polyline[-1];squared=sum((endpoint[i]-pad['center'][i])**2 for i in range(2))
    require(pad['tree'][2:4]==['thru_hole','circle'] and size[0]==size[1] and 0<pad['drill']<size[0],label+'/exact PTH annulus')
    require((Fraction(pad['drill'],2)+margin)**2<squared<(Fraction(size[0],2)-margin)**2,label+'/endpoint strictly in annulus')

for i,row in enumerate(result['path_certificate_candidates']):
    margin=row['copper_path_margin_nm'];target=[x for x in pad_records.values() if x['terminal']==row['target_logical_terminal']];other=[x for x in pad_records.values() if x['terminal']==row['other_logical_terminal']]
    require(len(target)==len(other)==1 and target[0]['terminal']!=other[0]['terminal'],'proposal'+str(i)+'/unique distinct logical terminals')
    require(target[0]['row']['uuid']==g['target_pad_uuid'] and target[0]['row']['net_code']==other[0]['row']['net_code']==row['net_code']==g['net_code'],'proposal'+str(i)+'/terminal net identity')
    require(row['source_copper_path_nm'][0]==row['start_nm'] and row['destination_copper_path_nm'][0]==row['end_nm'],'proposal'+str(i)+'/bridge joins both certified paths')
    require(row['width_nm']==g['class']['width_nm']==500000 and margin==10000 and row['layer']=='B.Cu','proposal'+str(i)+'/original class width/layer/margin')
    path_checks(row['source_copper_path_nm'],row['source_outline_index'],target[0],margin,'proposal'+str(i)+'/source')
    path_checks(row['destination_copper_path_nm'],row['destination_outline_index'],other[0],margin,'proposal'+str(i)+'/destination')
    require(all(point_distance_sq(h['center'],row['start_nm'],row['end_nm'])>(h['radius']+margin)**2 for h in holes),'proposal'+str(i)+'/bridge centerline clears all drills')
    require(abs(math.dist(row['start_nm'],row['end_nm'])-row['length_nm'])<1e-6,'proposal'+str(i)+'/length correct')
require(len(result['path_certificate_candidates'])==4,'four bounded proposals')
report={'passed':not failures,'check_count':len(checks),'failures':failures,'checks':checks,'paths':paths,
        'geometry_sha256':sha(PROBE/'geometry.json'),'proposals_sha256':sha(QUAL/'path-attempt-003.json'),
        'script_sha256':sha(Path(__file__)),'native_executed':False,
        'scope':'Independent exact-rational saved-geometry path proof, all physical holes reconstructed from board; fresh native repair not yet performed',
        'limits':['10um centerline corridor proves positive-width copper existence only, not 0.5mm clearance throughout existing fill or ampacity.',
                  'New bridge capsule versus other copper/keepouts/edges/constraints still requires native validation.',
                  'Final refill must preserve certified filled geometry exactly, otherwise this witness is stale.',
                  'Actual source/candidate/report bindings were rechecked here; historical boolean binding alone is insufficient.',
                  'Native whole-body self-intersection flag remains true; proof concerns only explicitly checked paths.']}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks':len(checks),'failures':failures,'minimum_boundary_nm':min(x['boundary_clearance_nm_approx'] for x in paths),'minimum_drill_nm':min(x['minimum_drill_clearance_nm_approx'] for x in paths)}))
sys.exit(1 if failures else 0)
