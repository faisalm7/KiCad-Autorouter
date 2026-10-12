"""Read retained evidence only; no native execution or candidate writes."""
import copy,json,hashlib
from pathlib import Path
from autorouter import pipeline as p,sexpr as s
from autorouter.adapter import _parse_dsn
ROOT=Path.cwd();OUT=ROOT/'.runs/preferences-protected-diagnosis-001';RUN=ROOT/'.runs/preferences-native-partial-001'
result=json.loads((RUN/'result.json').read_text());source=Path(result['source'])
sha=lambda raw:hashlib.sha256(raw).hexdigest()
paths=[source,RUN/'result.json',RUN/'snapshot'/source.name,RUN/'candidate'/source.name,RUN/'imported.kicad_pcb',RUN/'native.dsn',RUN/'task.dsn',RUN/'routes.ses',RUN/'export-process.json',RUN/'import-process.json',RUN/'engine-process.json',RUN/'source-drc.json',RUN/'routing-preferences.json']
paths += [RUN/'code'/n for n in ('pipeline.py','native.py','sexpr.py','adapter.py')]
before={str(x.relative_to(ROOT)):sha(x.read_bytes()) for x in paths}
original=s.read(source);imported=s.read(RUN/'imported.kicad_pcb');candidate=s.read(RUN/'candidate'/source.name)
protected=p.routes(original); imported_routes=[p.convert_route_nets(r,imported,original) for r in p.routes(imported)]
without_uuid=lambda r:[n for n in r if not (isinstance(n,list) and n and n[0]=='uuid')]
rows=[];matched=[]
for route in protected:
 matches=[i for i,r in enumerate(imported_routes) if without_uuid(r)==without_uuid(route)]
 assert len(matches)==1 and matches[0] not in matched;index=matches[0];matched.append(index)
 rows.append({'original':route,'imported':imported_routes[index],'only_changed_field':'uuid','exact_non_uuid_AST_equal':True,'imported_index':index})
task=copy.deepcopy(original)
for z in s.children(task,'zone'):z[:]=[n for n in z if not (isinstance(n,list) and n and n[0] in p.DERIVED_ZONE)]
assert sha((s.dump(task)+'\n').encode())==result['task_sha256']
assert p.transplant_routes(task,imported)==candidate
assert p.immutable(candidate)==p.immutable(original)
assert p.tree_hash(source.parent)==result['source_hashes']==p.tree_hash(RUN/'snapshot')
assert len(protected)==2 and len(imported_routes)==5
for name in ('export','import','engine'):
 proc=json.loads((RUN/(name+'-process.json')).read_text())
 assert proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] is True
assert not (RUN/'final-drc.json').exists() and not (RUN/'refill').exists()
rawdsn=_parse_dsn((RUN/'native.dsn').read_text());taskdsn=_parse_dsn((RUN/'task.dsn').read_text())
wiring=s.one(rawdsn,'wiring');assert wiring==s.one(taskdsn,'wiring')
ses=s.read(RUN/'routes.ses');nets=s.children(s.one(s.one(ses,'routes'),'network_out'),'net')
protected_ses=[]
for net in nets:
 for wire in s.children(net,'wire'):
  if s.one(wire,'type')==['type','protect']:protected_ses.append({'net':s.unquote(net[1]),'wire':wire})
assert len(protected_ses)==2
for row in rows:
 net=s.unquote(s.one(row['original'],'net')[1]);wire=next(x['wire'] for x in protected_ses if x['net']==net)
 path=s.one(wire,'path');route=row['original']
 # SES resolution is um/10: original millimetres multiply by 10000; y is reversed.
 from decimal import Decimal
 wanted=[Decimal(s.one(route,'start')[1])*10000,-Decimal(s.one(route,'start')[2])*10000,Decimal(s.one(route,'end')[1])*10000,-Decimal(s.one(route,'end')[2])*10000]
 assert path[1]=='F.Cu' and Decimal(path[2])==Decimal(s.one(route,'width')[1])*10000 and list(map(Decimal,path[3:]))==wanted
hypothesis=p.transplant_routes(task,imported)
for route in p.routes(hypothesis):
 for original_route in protected:
  if without_uuid(route)==without_uuid(original_route):route[:]=copy.deepcopy(original_route)
assert all(route in p.routes(hypothesis) for route in protected)
assert p.immutable(hypothesis)==p.immutable(original) and len(p.routes(hypothesis))==5
assert before=={str(x.relative_to(ROOT)):sha(x.read_bytes()) for x in paths}
report={'schema':1,'scope':'Offline actual failed-run diagnosis; hypothetical reconstruction is not native validated.',
 'head':result['tools']['git_head'],'hashes':before,'source_inventory_unchanged':True,'task_reconstructed_hash_matches':True,
 'candidate_equals_existing_transplant':True,'immutable_candidate_equals_original':True,'native_dsn_task_wiring_equal':True,
 'protected_ses':protected_ses,'protected_route_matches':rows,'routes':{'source':2,'imported':5,'candidate':5,'hypothetical':5},
 'first_failure':result['reason'],'final_refill_or_DRC_attempted':False,'original_run_accepted':False,
 'observed_only_protected_route_difference':'Both UUIDs changed; every other AST atom matches exactly after net conversion.',
 'hypothesis_exact_original_route_AST_present':True,'hypothesis_native_validated':False,
 'scope_limit':'No new board, routing, JVM, source changes or acceptance decision; source/native guard remains unchanged.'}
(OUT/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'observed_uuid_only_changes':len(rows),'original_source_unchanged':True,'native_revalidation':False}))
