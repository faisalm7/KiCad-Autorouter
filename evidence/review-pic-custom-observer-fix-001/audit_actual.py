"""Read-only actual native shape and DSN grammar audit; no pcbnew import/process."""
import hashlib,importlib.util,json,sys
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from autorouter import sexpr as sx,adapter as a,placement_clearance as io
RUN=ROOT/'.runs/pic-custom-observation-001';SOURCE=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('review_mapping',HERE/'mapping-proposed.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
before=io.inventory(RUN,max_bytes=20*1024**2,max_files=512,max_entries=1024);source_before=io.inventory(SOURCE.parent)
raw=(RUN/'native.dsn').read_text();native=json.loads((RUN/'observation.json').read_text());custom=json.loads((RUN/'custom-pads.json').read_text());notes=m.source_notes(sx.read(SOURCE),json.loads(SOURCE.with_suffix('.kicad_pro').read_text()));rows=m.custom_identity(custom,native,notes)
control=[]
variants={'actual':raw,'missing_quote_declaration':raw.replace('(string_quote ")',''), 'duplicate_quote_declaration':raw.replace('(string_quote ")','(string_quote ") (string_quote ")'),'comment_only_declaration':raw.replace('(string_quote ")','; (string_quote ")'),'reserved_sentinel':raw+'; '+a._QUOTE_SENTINEL,'unterminated_string':raw+' \"unterminated','unmatched_close':raw+')','wrong_units':raw.replace('(unit um)','(unit mm)')}
for name,text in variants.items():
 try:result=m.dsn_correspondence(text.encode(),native,rows);accepted=True;error=None
 except Exception as exc:accepted=False;error=type(exc).__name__+': '+str(exc)
 expected=name=='actual';assert accepted is expected,(name,error)
 control.append({'case':name,'accepted_for_observation':accepted,'expected':expected,'error':error,'input_sha256':hashlib.sha256(text.encode()).hexdigest()})
def ring(points):
 p=[tuple(v) for v in points]
 if p[0]==p[-1]:p.pop()
 return min(tuple(p[i:]+p[:i]) for p in (p,list(reversed(p))) for i in range(len(p)))
def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
def hull(points):
 points=sorted(set(map(tuple,points)));lo=[];hi=[]
 for pt in points:
  while len(lo)>=2 and cross(lo[-2],lo[-1],pt)<=0:lo.pop()
  lo.append(pt)
 for pt in reversed(points):
  while len(hi)>=2 and cross(hi[-2],hi[-1],pt)<=0:hi.pop()
  hi.append(pt)
 return lo[:-1]+hi[:-1]
def area2(points):return abs(sum(x[0]*y[1]-y[0]*x[1] for x,y in zip(points,points[1:]+points[:1])))
correspondence=m.dsn_correspondence(raw.encode(),native,rows);observations=[]
for row,dsn in zip(rows,correspondence['custom_pads']):
 original=next(x for x in notes['custom_pads'] if x['uuid']==row['uuid']);poly=sx.one(sx.one(original['pad_ast'],'primitives'),'gr_poly')
 source_pts=[[int(Decimal(v)*1000000) for v in x[1:]] for x in sx.one(poly,'pts')[1:]]
 local=row['merged_local']['outlines'][0]['outline']['points_nm'];world=row['transformed_world']['outlines'][0]['outline']['points_nm'];effective=row['effective_world']['outlines'][0]['outline']['points_nm']
 assert ring(source_pts)==ring(local);assert row['orientation_degrees']==0 and row['offset_nm']==[0,0]
 assert ring([[p[i]+row['position_nm'][i] for i in (0,1)] for p in local])==ring(world)==ring(effective)
 poly=sx.one(dsn['padstack_ast'],'shape')[1];dsnpts=[[int(Decimal(poly[i+j])*1000) for j in (0,1)] for i in range(3,len(poly),2)]
 assert ring(dsnpts)==ring(hull(local))
 observations.append({'uuid':row['uuid'],'number':row['number'],'net':row['net'],'native_layer':row['copper_layers'],'native_pad_position_nm':row['position_nm'],'source_ring_equals_native_local':True,'native_world_equals_zero_rotation_local_plus_position':True,'native_effective_equals_world':True,'native_local_vertices':len(local),'native_area_nm2_times2':area2(local),'dsn_padstack_layer':poly[1],'dsn_pin_ast':dsn['pin_ast'],'dsn_placement_ast':dsn['placement_ast'],'dsn_polygon_equals_local_convex_hull':True,'dsn_unique_vertices':len(ring(dsnpts)),'dsn_area_nm2_times2':area2(list(ring(dsnpts))),'native_to_DSN_world_transform_qualified':False})
assert before==io.inventory(RUN,max_bytes=20*1024**2,max_files=512,max_entries=1024) and source_before==io.inventory(SOURCE.parent)
record={'schema':1,'native_jobs':0,'engine_jobs':0,'raw_run_unchanged':True,'source_unchanged':True,'raw_dsn_sha256':sha(RUN/'native.dsn'),'custom_record_sha256':sha(RUN/'custom-pads.json'),'parser_controls':control,'shape_observations':observations,'scope':'Actual saved native observations and raw export, re-read offline. Only original zero-angle geometry was checked. Local hull comparison does not qualify arbitrary back-side DSN transforms, native copper connectivity or DRC clearance. No original native DRC stage ran in001.'}
(HERE/'geometry-parser-audit-001.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
