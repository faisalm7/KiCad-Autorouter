"""Exact-rational source geometry hypothesis, not an actual native/DSN result."""
from pathlib import Path
from fractions import Fraction as F
import json,math,hashlib,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import sexpr as sx
source=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb';tree=sx.read(source)
fp=next(x for x in sx.children(tree,'footprint') if any(q[1:3]==['"Reference"','"JP1"'] for q in sx.children(x,'property')))
polys=[]
for pad in sx.children(fp,'pad'):
 xy=[F(x) for x in sx.one(pad,'at')[1:3]];poly=sx.one(sx.one(pad,'primitives'),'gr_poly');polys.append([(F(p[1])+xy[0],F(p[2])+xy[1]) for p in sx.one(poly,'pts')[1:]])
p,q=polys
# The concave pad's source-derived hull is exactly this rectangle. Clip convex pad1 by its left boundary.
left=min(x for x,y in q);clipped=[]
for a,b in zip(p,p[1:]+p[:1]):
 ia=a[0]>=left;ib=b[0]>=left
 if ia:clipped.append(a)
 if ia!=ib:
  t=(left-a[0])/(b[0]-a[0]);clipped.append((left,a[1]+t*(b[1]-a[1])))
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def dist2(x,a,b):
 v=(b[0]-a[0],b[1]-a[1]);w=(x[0]-a[0],x[1]-a[1]);t=max(F(0),min(F(1),(v[0]*w[0]+v[1]*w[1])/(v[0]**2+v[1]**2)));return (x[0]-a[0]-t*v[0])**2+(x[1]-a[1]-t*v[1])**2
area=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(clipped,clipped[1:]+clipped[:1])))/2
minimum=min([dist2(x,a,b) for x in p for a,b in zip(q,q[1:]+q[:1])]+[dist2(x,a,b) for x in q for a,b in zip(p,p[1:]+p[:1])])
# Explicit source notch/triangle branches are parallel and ordered by a 0.3mm horizontal gap for every common y.
assert all(F('.275')-F(2)/3*abs(y)+F('.3')==F('.575')-F(2)/3*abs(y) for y in [F('-.75'),F(0),F('.75')])
assert area==F('0.06') and minimum==F(81,1300)
report={'schema':1,'source_board_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Source-only exact geometry hypothesis; native exporter observation remains pending. No execution or production changes.','pad1_net':'VCC','pad2_net':'/pic_sockets/VCC_PIC','pad1_rightmost_fp_x_mm':'.275','pad2_hull_leftmost_fp_x_mm':'.075','hull_overlap_polygon_fp_mm':[[str(v) for v in z] for z in clipped],'hull_overlap_area_mm2_exact':str(area),'native_copper_source_polygons_disjoint':True,'source_polygon_minimum_edge_distance_squared_mm2_exact':str(minimum),'source_polygon_minimum_edge_distance_mm':math.sqrt(minimum),'footprint_original_clearance_mm':sx.one(fp,'clearance')[1],'claim_limits':['Convex hulls overlap in source-derived placed geometry, but actual DSN flip/rotation/layer correspondence must be observed.','A source polygon distance is not a KiCad DRC result or independent rule evaluation; native tolerances and original settings remain authoritative.','No prediction of routing failure, no engine run and no custom-pad adapter proposed before measurement.']}
out=Path(__file__).parent/'hull-overlap-001.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
