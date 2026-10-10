"""Offline direct geometry and exact selected-copy audit, no native execution."""
from pathlib import Path
from decimal import Decimal
import sys,json
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
HERE=Path(__file__).resolve().parent;RUN=ROOT/'.runs/placement-routing-fixture-002';PUBLIC=ROOT/'evidence/placement-routing-fixture-002'
r=json.loads((RUN/'result.json').read_text());b=Path(r['candidate']);t=sx.read(b);source=sx.read(Path(r['source']));zones=sx.children(t,'zone');assert zones==sx.children(source,'zone') and len(zones)==1
pts=[[Decimal(x) for x in n[1:]] for n in sx.one(sx.one(zones[0],'polygon'),'pts')[1:]];assert set(map(tuple,pts))=={(Decimal(20),Decimal(19)),(Decimal(30),Decimal(19)),(Decimal(30),Decimal(21)),(Decimal(20),Decimal(21))}
tr=[x for x in p.routes(t) if x[0]=='segment' and sx.one(x,'net')==['net','"SIGNAL_B"']];assert len(tr)==1
seg=tr[0];a=[Decimal(x) for x in sx.one(seg,'start')[1:]];z=[Decimal(x) for x in sx.one(seg,'end')[1:]];w=Decimal(sx.one(seg,'width')[1]);assert sx.one(seg,'layer')==['layer','"F.Cu"'] and a[1]==z[1]==20 and min(a[0],z[0])<20 and max(a[0],z[0])>30 and w==Decimal('0.3')
assert Decimal(19)<Decimal(20)-w/2 and Decimal(20)+w/2<Decimal(21)
files=json.loads((PUBLIC/'files.json').read_text());assert set(p.tree_hash(PUBLIC))-{'files.json','SCOPE.md'}==set(files)
for name,row in files.items():
 path=PUBLIC/name;assert path.read_bytes()==(RUN/name).read_bytes() and p.sha(path)==row['sha256'] and path.stat().st_size==row['bytes']
result={'schema':1,'passed':True,'native_executed':False,'candidate_sha256':p.sha(b),'actual_segment_uuid':sx.unquote(sx.one(seg,'uuid')[1]),'net':'SIGNAL_B','layer':'F.Cu','start_mm':list(map(str,a)),'end_mm':list(map(str,z)),'width_mm':str(w),'allowed_area_interior_crossing_mm':'10','track_edge_vertical_margin_mm':'0.85','meaning':'The accepted actual route uses the interior of the retained unrestricted area. This exercises the removed interchange obstacle, without proving necessity or a paired improvement.','public_selected_files':len(files),'public_selected_bytes':sum(v['bytes'] for v in files.values()),'all_public_selected_bytes_equal_retained_actual':True}
with (HERE/'crossing-public-copy.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result,indent=2))
