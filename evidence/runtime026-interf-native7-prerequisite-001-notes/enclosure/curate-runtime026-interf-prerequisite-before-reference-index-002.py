"""Retain one rejected Native7 prerequisite using existing readers/copy pattern."""
from pathlib import Path
import json,sys,hashlib,time,datetime
root=Path(__file__).resolve().parents[1];runtime=root/'.runs/runtime-directory-026/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io,sexpr as sx,thermal
start=time.monotonic();base=root/'.runs/runtime026-interf-prerequisite-001';plan=f.read_json(base/'protocol.json');execution=f.read_json(base/'execution.json');out=runtime/'.runs/native7-interf-prerequisite-001';child=f.read_json(out/'result.json');w=Path(child['workspace']);data=f.read_json(w/'route/result.json');route=w/'route';source=Path(plan['source'])
assert execution['sources_unchanged'] and execution['process']['cleanup_complete'] and execution['passed'] is False
assert data['status']=='drc_rejected' and data['accepted'] is False and data['schematic_parity']=='checked by final native DRC'
assert data['tools']==p.tool_manifest() and p.tree_hash(source.parent)==p.tree_hash(route/'snapshot')==plan['source_hashes']
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']=='5371d08ccf5a0ae2e0c4024f752baca28f034c3b3cb50ade308e8e5e12e36fe5'
original=sx.read(source);candidate=Path(data['candidate']);protected=p.protected_for_record(data,original)
assert p.sha(candidate)==data['candidate_sha256'] and p.immutable(sx.read(candidate))==p.immutable(original) and all(x in p.routes(sx.read(candidate)) for x in protected)
expected=dict(data['source_hashes']);expected[candidate.name]=p.sha(route/'pre-refill.kicad_pcb')
refill=f.check_drc_stage(route,data,'refill-drc',route/'refill'/candidate.name,route/'refill'/candidate.name,True,expected,sandboxed=False)
expected[candidate.name]=data['candidate_sha256'];native=f.check_drc_stage(route,data,'final-drc',candidate,route/'final-drc-input'/candidate.name,False,expected,schematic_parity=True,sandboxed=False)
assert native==data['native'] and [native[k] for k in ('opens','blocking','warnings','exclusions')]==[0,1,22,0] and thermal.sole_thermal(native) is not None
assert not (w/'export').exists() and not (w/'choice').exists()
notes=root/'evidence/runtime026-interf-native7-prerequisite-001-notes';assert not notes.exists();refs={};references=[]
for name in ('evidence/interf-installed023-comparison-001.json','evidence/runtime026-installed-CLI-001.json','evidence/runtime026-installed-partial-CLI-001.json'):
 q=root/name;old=f.read_json(q);references.append(dict(path=name,sha256=p.sha(q)))
 for row in old['files']:refs.setdefault(row['sha256'],row['path'])
rows=[];material=[];count=0
def copy(path,relative):
 global count
 raw=io.read_bytes(path,4*1024**2);digest=hashlib.sha256(raw).hexdigest();public=refs.get(digest)
 if public is None:
  assert b'\0' not in raw;raw.decode('utf-8');dest=notes/relative;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as s:s.write(raw)
  public=str(dest.relative_to(root));refs[digest]=public;rows.append(dict(path=public,bytes=len(raw),sha256=digest));count+=len(raw);assert count<32*1024**2 and len(rows)<2000
 else:assert p.sha(root/public)==digest
 material.append(dict(original=str(path.relative_to(root)),retained=public,bytes=len(raw),sha256=digest))
skip={'code','kicad-cache','kicad-config','kicad-documents','engine-config','tmp'}
for name in io.inventory(out,max_bytes=32*1024**2):
 rel=Path(name)
 if set(rel.parts)&skip or rel.name.startswith('.'):continue
 copy(out/name,Path('workflow')/name)
for name in plan['source_hashes']:copy(source.parent/name,Path('source')/name)
for name in ('protocol.json','execution.json','process.json','settings.json','command.log'):copy(base/name,Path('enclosure')/name)
for name in ('runtime026-interf-prerequisite-001-time.log','runtime026-interf-prerequisite-002-time.log','runtime026-interf-prerequisite-002.log','run-runtime026-interf-prerequisite-initial-syntax-failure-001.py','run-runtime026-interf-prerequisite-001.py','normal1007-thermal-prerequisite-assessment-001.json','curate-runtime026-interf-prerequisite-001-time.log','curate-runtime026-interf-prerequisite-initial-reader-call-001.py'):
 copy(root/'.runs'/name,Path('enclosure')/name)
copy(Path(__file__),Path('controllers')/Path(__file__).name)
index=dict(schema=1,files=rows,material=material);notes.mkdir(parents=True,exist_ok=True);(notes/'files.json').write_text(json.dumps(index,indent=2)+'\n')
record=dict(schema=1,kind='runtime026-ordinary-native7-B1-solethermal-prerequisite',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,delivered=False,project_complete=False,actual_GUI=False,human_review=False,production_thermal_admitted=False,runtime_source='1117de080524072046a61522845facd5d4c68575',runtime_manifest_sha256=plan['runtime_manifest_sha256'],protocol_sha256=p.sha(base/'protocol.json'),source_hashes=plan['source_hashes'],original_source_unchanged=True,original_nonrouting_design_unchanged=True,protected_count=len(protected),candidate_sha256=data['candidate_sha256'],native_report_sha256=data['native_report_sha256'],native=native,source_drc=data['source_drc'],schematic_parity=data['schematic_parity'],metrics=data['metrics'],existing_shared_DRC_readbacks=['refill-drc','final-drc'],current_positive_result=False,workflow_failure=child['error'],complete_wall_seconds=59.58,complete_CPU_seconds=80.29,initial_controller_syntax_failure_wall_seconds=.01,initial_controller_syntax_failure_CPU_seconds=0,all_steps_cleanup_complete=all(s['cleanup_complete'] for s in data['steps']),budget_scope=plan['budget_scope'],decision='Solethermal persists on7 under unchanged B1. A bounded nonadmitting worker/profile-binding component prerequisite is justified; no algorithm/rule/geometry tuning or normal7thermal admission yet. Preserve all22warnings and source2repairablethermalfindings. This is not a freshB0/B2/Ccomparison, gain claim or infeasibility proof.',accounting='Complete external wall/CPU retained, including startup/conversion/engine/validation/negative delivery. Parent sampled59.542/80.257 are nested, not additional. Initial syntax failure .01/0 before any protocol/Native retained separately. Research/authoring/AIreview/curation are additional and incompletely instrumented.',source_rights=plan['source_rights'],references=references,files=rows,files_index=dict(path=str((notes/'files.json').relative_to(root)),sha256=p.sha(notes/'files.json')),curation_wall_seconds_before_publication=time.monotonic()-start,new_raw_full_backup=False,initial_curation_refusal='Shared DRC reader was initially called with sandboxed=True while ordinary producer records exact unsandboxed pinnedNative argv. Rejected before any curation output. Corrected call sandboxed=False matches original ordinary contract; no process/data/Native validation changed.0.52wall0.42CPU retained separately.')
p.save_json(root/'evidence/runtime026-interf-native7-prerequisite-001.json',record);print(json.dumps(dict(files=len(rows),bytes=count,accepted=False,native=[native[k] for k in ('opens','blocking','warnings','exclusions')],source_unchanged=True)))
