"""Bounded source-only geometry/API review. No pcbnew import or native work."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import sexpr as sx
HERE=Path(__file__).resolve().parent;source=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb';project=source.with_suffix('.kicad_pro');tree=sx.read(source)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def hull(points):
 points=sorted(set(points));lo=[];hi=[]
 for target,seq in [(lo,points),(hi,reversed(points))]:
  for x in seq:
   while len(target)>1 and cross(target[-2],target[-1],x)<=0:target.pop()
   target.append(x)
 return lo[:-1]+hi[:-1]
def contains(poly,q):
 inside=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if cross(a,b,q)==0 and min(a[0],b[0])<=q[0]<=max(a[0],b[0]) and min(a[1],b[1])<=q[1]<=max(a[1],b[1]):return True
  if (a[1]>q[1])!=(b[1]>q[1]) and q[0]<(b[0]-a[0])*(q[1]-a[1])/(b[1]-a[1])+a[0]:inside=not inside
 return inside
def area(poly):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])))/2
pads=[]
for fp in sx.children(tree,'footprint'):
 for pad in sx.children(fp,'pad'):
  if pad[3]!='custom':continue
  poly=sx.one(sx.one(pad,'primitives'),'gr_poly');pts=[tuple(F(x) for x in n[1:]) for n in sx.one(poly,'pts')[1:]];outline=hull(pts)
  row={'pad_uuid':sx.unquote(sx.one(pad,'uuid')[1]),'number':sx.unquote(pad[1]),'net':sx.unquote(sx.one(pad,'net')[1]),'native_observed':False,'polygon_area_mm2_exact':str(area(pts)),'convex_hull_area_mm2_exact':str(area(outline)),'convex_hull_exact':[[str(v) for v in x] for x in outline], 'anchor_0_3mm_corners_inside_original_polygon':all(contains(pts,q) for q in [(F(x),F(y)) for x in ['-.15','.15'] for y in ['-.15','.15']])}
  if row['number']=='2':
   q=(F('-.4'),F(0));row['notch_counterexample']={'local_mm':['-0.4','0'],'inside_export_hull_model':contains(outline,q),'inside_original_polygon':contains(pts,q),'inside_anchor':False};assert contains(outline,q) and not contains(pts,q)
  pads.append(row)
receipt=json.loads((ROOT/'.runs/support-scope-review-001/source-receipt.json').read_bytes());pinned=ROOT/'.runs/support-scope-review-001/source'
paths=['pcbnew/pad.cpp','pcbnew/specctra_import_export/specctra_export.cpp','pcbnew/drc/drc_item.cpp','pcbnew/drc/drc_test_provider_misc.cpp','pcbnew/drc/drc_test_provider_disallow.cpp','pcbnew/pcbnew_jobs_handler.cpp','pcbnew/board_design_settings.cpp']
refs={name:{'sha256':h(pinned/name),'url':'https://gitlab.com/kicad/code/kicad/-/blob/'+receipt['commit']+'/'+name} for name in paths}
bindings=Path('/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/pcbnew.py')
settings=json.loads(project.read_bytes());severities=settings['board']['design_settings']['rule_severities'];four=['footprint_symbol_field_mismatch','missing_tuning_profile','text_on_edge_cuts','track_on_post_machined_layer']
report={'schema':1,'native_jobs':0,'engine_jobs':0,'network_calls':0,'pcbnew_imported':False,'source_board_sha256':h(source),'source_project_sha256':h(project),'cached_primary_source_commit':receipt['commit'],'references':refs,'installed_python_binding':{'path':str(bindings),'sha256':h(bindings),'legacy_accessor_trap':'GetCustomShapeAsPolygon(layer=UNDEFINED_LAYER) ignores layer and calls MergePrimitivesAsPolygon(F_Cu, polygon_set), lines15820–15824. Explicit per-copper-layer MergePrimitivesAsPolygon and TransformShapeToPolygon APIs are declared; declarations are not runtime qualification.'},'pads':pads,'original_four_severity_values':{k:severities[k] for k in four},'original_netclass_tuning_profiles':{x['name']:x.get('tuning_profile') for x in settings['net_settings']['classes']},'scope':'Static rational geometry only. Exported hull adds a false-contact region to concave pad2; native geometry/DSN correspondence and connectivity remain unobserved. No production gate changes.'}
path=HERE/'source-review-001.json';assert not path.exists();path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
