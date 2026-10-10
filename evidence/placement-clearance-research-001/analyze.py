"""Read-only saved-geometry arithmetic, never a native DRC substitute."""
from pathlib import Path
import collections,hashlib,json,math,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import sexpr as sx
from autorouter.adapter import _parse_dsn
OUT=Path(__file__).resolve().parent;RUN=ROOT/'.runs/placement-routing-pair-001/arm-1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def vec(node,key):return tuple(map(float,sx.one(node,key)[1:]))
def uid(node):return sx.unquote(sx.one(node,'uuid')[1])
def diff(a,b):return (a[0]-b[0],a[1]-b[1])
def dot(a,b):return a[0]*b[0]+a[1]*b[1]
def nearest(point,a,b):
 ab=diff(b,a);t=max(0.,min(1.,dot(diff(point,a),ab)/dot(ab,ab)))if dot(ab,ab)else 0.
 q=(a[0]+t*ab[0],a[1]+t*ab[1]);return math.dist(point,q),q,t
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def segdist(a,b,c,d):
 ab=diff(b,a);cd=diff(d,c);den=cross(ab,cd)
 if den:
  t=cross(diff(c,a),cd)/den;u=cross(diff(c,a),ab)/den
  if 0<=t<=1 and 0<=u<=1:return 0.
 return min(nearest(a,c,d)[0],nearest(b,c,d)[0],nearest(c,a,b)[0],nearest(d,a,b)[0])
def edges(points):return list(zip(points,points[1:]+points[:1]))
def primitive_check():
 assert math.isclose(nearest((1,1),(0,0),(2,0))[0],1)
 assert segdist((0,0),(2,2),(0,2),(2,0))==0
 assert math.isclose(segdist((0,0),(1,0),(2,1),(3,1)),math.sqrt(2))
primitive_check()
record=json.loads((RUN/'result.json').read_text());source=Path(record['source']);candidate=Path(record['candidate']);project=source.with_suffix('.kicad_pro')
watched=[RUN/'result.json',RUN/'final-drc.json',RUN/'native.dsn',RUN/'task.dsn',RUN/'floor-policy.json',source,candidate,project,ROOT/'autorouter/sexpr.py',ROOT/'autorouter/adapter.py',Path(__file__)]
watched +=[p for p in source.parent.rglob('*')if p.is_file()]
before={str(p.relative_to(ROOT)):sha(p)for p in watched}
assert sha(candidate)==record['candidate_sha256'];assert sha(RUN/'native.dsn')==record['chain']['native_dsn_sha256'];assert sha(RUN/'task.dsn')==record['chain']['task_dsn_sha256'];assert sha(RUN/'final-drc.json')==record['native_report_sha256']
original=sx.read(source);final=sx.read(candidate);dsn=_parse_dsn((RUN/'native.dsn').read_text());task=_parse_dsn((RUN/'task.dsn').read_text())
findings=[f for f in record['native']['findings']if f['type']=='clearance'];assert len(findings)==2
pad_ids=set.intersection(*[{x['uuid']for x in f['items']}for f in findings]);assert len(pad_ids)==1;pad_id=next(iter(pad_ids))
matched=[(fp,pad)for fp in sx.children(original,'footprint')for pad in sx.children(fp,'pad')if uid(pad)==pad_id];assert len(matched)==1;fp,pad=matched[0]
assert pad[3]=='roundrect';w,h=vec(pad,'size');r=min(w,h)*float(sx.one(pad,'roundrect_rratio')[1]);fpx,fpy,angle=vec(fp,'at');px,py,pangle=vec(pad,'at');assert pangle==angle==90
center=(fpx+py,fpy-px);assert center==(105.4,108.4)
ref=next(sx.unquote(x[2])for x in sx.children(fp,'property')if sx.unquote(x[1])=='Reference')
place=[(component,p)for component in sx.children(sx.one(dsn,'placement'),'component')for p in sx.children(component,'place')if sx.unquote(p[1])==ref];assert len(place)==1;component,placement=place[0]
image=next(x for x in sx.children(sx.one(dsn,'library'),'image')if x[1]==component[1])
pins=[]
for pin in sx.children(image,'pin'):
 if any(isinstance(x,list)for x in pin[2:]):continue
 x,y=map(float,pin[-2:]);global_center=(float(placement[2])-y,-float(placement[3])-x)
 if math.dist((global_center[0]/1000,global_center[1]/1000),center)<1e-9:pins.append(pin)
assert len(pins)==1;pin=pins[0]
stack=next(x for x in sx.children(sx.one(dsn,'library'),'padstack')if x[1]==pin[1]);same=next(x for x in sx.children(sx.one(task,'library'),'padstack')if x[1]==pin[1]);assert stack==same
polygon=next(x[1]for x in sx.children(stack,'shape')if x[1][0]=='polygon'and x[1][1]=='B.Cu');assert polygon[2]=='0'
local=list(zip(map(float,polygon[3::2]),map(float,polygon[4::2])));assert local[0]==local[-1];local=local[:-1]
poly=[(center[0]-y/1000,center[1]-x/1000)for x,y in local]
hx=h/2-r;hy=w/2-r;core=[(center[0]-hx,center[1]-hy),(center[0]+hx,center[1]-hy),(center[0]+hx,center[1]+hy),(center[0]-hx,center[1]+hy)]
segments={uid(x):x for x in sx.children(final,'segment')};results=[]
for finding in findings:
 ident=next(x['uuid']for x in finding['items']if x['uuid']!=pad_id);seg=segments[ident];a=vec(seg,'start');b=vec(seg,'end');width=float(sx.one(seg,'width')[1])
 true_gap=min(segdist(a,b,c,d)for c,d in edges(core))-r-width/2
 polygon_gap=min(segdist(a,b,c,d)for c,d in edges(poly))-width/2
 results.append({'uuid':ident,'start_mm':a,'end_mm':b,'width_mm':width,'native_report_description':finding['description'],'analytic_roundrect_clearance_mm':true_gap,'saved_dsn_polygon_clearance_mm':polygon_gap,'clearance_difference_um':1000*(polygon_gap-true_gap)})
# Exact edge support deficits for this convex saved32-vertex polygon.
area=sum(cross(a,b)for a,b in edges(local));assert area!=0
if area<0:local.reverse()
turns=[cross(diff(b,a),diff(c,b))for a,b,c in zip(local,local[1:]+local[:1],local[2:]+local[:2])];assert all(x>0 for x in turns)
deficits=[]
for a,b in edges(local):
 e=diff(b,a);length=math.hypot(*e);normal=(e[1]/length,-e[0]/length)
 native_support=(w*500-r*1000)*abs(normal[0])+(h*500-r*1000)*abs(normal[1])+r*1000
 deficits.append(native_support-dot(a,normal))
project_data=json.loads(project.read_text());error=project_data['board']['design_settings']['rules']['max_error']*1e6
rounded=[]
for size in sorted({(*vec(p,'size'),float(sx.one(p,'roundrect_rratio')[1]))for f in sx.children(original,'footprint')for p in sx.children(f,'pad')if p[3]=='roundrect'}):
 width,height,ratio=size;radius=min(width,height)*ratio*1e6;extra=math.floor(radius*(1-math.cos(math.pi/36))+.5);expanded=radius+extra
 n=max(16,math.floor(360/math.degrees(2*math.acos(1-error/expanded))+.5));sagitta=expanded*(1-math.cos(math.pi/n))
 rounded.append({'size_mm':[width,height],'ratio':ratio,'radius_nm':radius,'fixed36_compensation_nm':extra,'expanded_radius_nm':expanded,'actual_full_circle_segments':n,'long_chord_angle_deg':360/n,'ideal_long_chord_sagitta_nm':sagitta,'ideal_remaining_inward_deficit_nm':max(0,sagitta-extra),'estimate_with_2nm_generation_and_10nm_DSN_vertex_allowance_nm':max(0,sagitta-extra)+12})
report={'kind':'saved geometry analytic diagnosis, not new native validation','inputs_sha256':before,'native_executed':False,'pad_uuid':pad_id,'footprint_reference':ref,'source_pad':pad,'source_footprint_at':sx.one(fp,'at'),'global_center_mm':center,'global_size_mm':[h,w],'round_radius_mm':r,'dsn_padstack':stack[1],'dsn_pin':pin,'dsn_polygon_vertex_count':len(local),'padstack_preserved_raw_to_engine_task':True,'dsn_polygon_local_um':local,'simple_strictly_convex_saved_target_polygon':True,'max_saved_edge_support_inward_deficit_um':max(deficits),'tracks':results,'project_max_error_nm':error,'source_roundrect_shapes':rounded,'source_pad_shape_census':dict(collections.Counter(p[3]for f in sx.children(original,'footprint')for p in sx.children(f,'pad'))),'dsn_padstack_primitive_census':dict(collections.Counter(x[1][0]for p in sx.children(sx.one(dsn,'library'),'padstack')for x in sx.children(p,'shape'))),'limits':['Per-edge target support deficit is directly calculated on the saved convex polygon; full exporter/import/engine reliability is not certified.','Other rounded-shape numbers are source-formula estimates with declared vertex rounding allowances, not native geometry validation.','No claim that increasing engine clearance completes remaining open connections.']}
assert all(sha(ROOT/name)==digest for name,digest in before.items());report['all_watched_inputs_unchanged']=True
(OUT/'analysis.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:report[k]for k in ('max_saved_edge_support_inward_deficit_um','tracks','source_roundrect_shapes','source_pad_shape_census','dsn_padstack_primitive_census')},indent=2))
