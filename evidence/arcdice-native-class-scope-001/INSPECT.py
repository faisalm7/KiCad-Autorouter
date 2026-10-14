"""Read-only ArcDice source/primary census; no native or pattern evaluator."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as pc,sexpr as sx
BASE=ROOT/'.runs/new-family-source-leads-002/source/VorosEgyes/ArcDice';BOARD=BASE/'hardware/ArcDice.kicad_pcb'
before=pc.inventory(BASE);project=json.loads(pc.read_bytes(BOARD.with_suffix('.kicad_pro')));tree=sx.read(BOARD);sch=sx.read(BOARD.with_suffix('.kicad_sch'))
def walk(node):
 if isinstance(node,list):
  if node and isinstance(node[0],str):yield node
  for x in node:yield from walk(x)
try:p.preflight(BOARD)
except p.Rejected as exc:preflight={'accepted':False,'reason':str(exc)}
else:raise AssertionError('previously unqualified class scope unexpectedly admitted')
classes=[]
for cls in project['net_settings']['classes']:
 dimensions={name:cls[name] for name in ('clearance','track_width','via_diameter','via_drill')}
 missing=[key for key in ('microvia_diameter','microvia_drill','diff_pair_width','diff_pair_gap','wire_width','bus_width') if key not in cls]
 classes.append({'name':cls['name'],'priority':cls['priority'],'transported_dimensions_mm':dimensions,'missing_other_defaultable_fields':missing,'tuning_profile':cls['tuning_profile']})
source=json.loads(pc.read_bytes(ROOT/'.runs/pic-severity-scope-review-001/source-receipt.json'));export=json.loads(pc.read_bytes(ROOT/'.runs/support-scope-review-001/source-receipt.json'));fr=json.loads(pc.read_bytes(ROOT/'.runs/pic-clearance-api-001/network-receipt.json'));pinned=[]
for receipt,parent,wanted in [(source,ROOT/'.runs/pic-severity-scope-review-001/source',{'common/project/net_settings.cpp','include/netclass.h'}),(export,ROOT/'.runs/support-scope-review-001/source',{'pcbnew/specctra_import_export/specctra_export.cpp'}),(fr,ROOT/'.runs/pic-clearance-api-001',{'source/Network.java'})]:
 for row in receipt['files']:
  if row['path'] not in wanted:continue
  file=parent/row['path'];raw=pc.read_bytes(file)
  assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
  pinned.append({'path':str(file.relative_to(ROOT)),'url':row['url'],'bytes':row['bytes'],'sha256':row['sha256'],'new_network_read':False})
assert len(pinned)==4
wrapper=Path('/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/pcbnew.py');raw=wrapper.read_bytes();text=raw.decode();methods={name:('def '+name+'(') in text for name in ['GetConstituentNetclasses','GetTrackWidthParent','GetClearanceParent','GetViaDiameterParent','GetViaDrillParent','GetPriority']};assert all(methods.values())
results={'schema':1,'scope':'Source/static pinned primary evidence only, no native/JVM/network/Git','source_commit':'5908d99db1ef98b5996b380c75e5aee8bb8caaa6','source_files':before,'current_preflight':preflight,'counts':{'footprints':len(sx.children(tree,'footprint')),'pads':sum(len(sx.children(fp,'pad')) for fp in sx.children(tree,'footprint')),'segments':len(sx.children(tree,'segment')),'vias':len(sx.children(tree,'via')),'zones':len(sx.children(tree,'zone')),'locked_routes':sum(p.locked(r) for r in p.routes(tree)),'root_keepouts':sum(sx.one(z,'keepout') is not None for z in sx.children(tree,'zone')),'footprint_zones':sum(len(sx.children(fp,'zone')) for fp in sx.children(tree,'footprint')),'schematic_netclass_flag_nodes':sum(n[0] in ('netclass_flag','netclass','net_class') for n in walk(sch))},'classes':classes,'patterns':project['net_settings']['netclass_patterns'],'explicit_class_assignments':project['net_settings']['netclass_assignments'],'original_dimension_floors_mm':{key:project['board']['design_settings']['rules'][key] for key in ['min_track_width','min_clearance','min_via_diameter','min_through_hole_diameter','min_via_annular_width','min_hole_clearance','min_copper_edge_clearance']},'tuning_profile_definitions':project['tuning_profiles'],'local_dimension_override_nodes':dict(Counter(n[0] for n in walk(tree) if n[0] in ['clearance','solder_mask_margin','solder_paste_margin','zone_connect','thermal_bridge_width','thermal_gap'])),'cached_primary':pinned,'installed_static_wrapper':{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'declared_methods':methods,'native_call_proven':False},'current_code_sha256':{name:p.sha(ROOT/name) for name in ['autorouter/netclass.py','autorouter/native.py','autorouter/pipeline.py','autorouter/routing_scope.py']},'native_qualified':False,'routing_accepted':False,'electrical_physical_validation':False}
assert pc.inventory(BASE)==before
print(json.dumps(results,indent=2))
