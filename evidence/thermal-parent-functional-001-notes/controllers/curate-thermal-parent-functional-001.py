"""Retain completed controls with existing bounded text/index pattern; no Native."""
from pathlib import Path
import json,hashlib,datetime,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
START=time.monotonic();NOTES=ROOT/'evidence/thermal-parent-functional-001-notes';assert not NOTES.exists()
refs={};references=[];rows=[];material=[];new_bytes=0
for name in ('evidence/interf-installed023-comparison-001.json','evidence/runtime026-interf-native7-prerequisite-001.json','evidence/thermal-native-identity-components-001.json','evidence/gui-runtime026-072-native-controls-001.json','evidence/thermal-parent-development-001.json'):
 q=ROOT/name;j=f.read_json(q);references.append(dict(path=name,sha256=p.sha(q)))
 for row in j.get('files',[]):refs.setdefault(row['sha256'],row['path'])
 if j.get('files_index'):
  q=ROOT/j['files_index']['path'];assert p.sha(q)==j['files_index']['sha256'];idx=f.read_json(q)
  for row in idx.get('files',[]):refs.setdefault(row['sha256'],row['path'])
  for row in idx.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
def retain(path,relative):
 global new_bytes
 assert path.is_file() and not path.is_symlink();raw=io.read_bytes(path,4*1024**2);digest=hashlib.sha256(raw).hexdigest();public=refs.get(digest)
 if public is None:
  assert b'\0' not in raw;raw.decode('utf-8');dest=NOTES/relative;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(raw)
  public=str(dest.relative_to(ROOT));refs[digest]=public;rows.append(dict(path=public,bytes=len(raw),sha256=digest));new_bytes+=len(raw)
  assert new_bytes<32*1024**2 and len(rows)<2500
 else:assert p.sha(ROOT/public)==digest
 material.append(dict(original=str(path.relative_to(ROOT)),retained=public,bytes=len(raw),sha256=digest))
skip={'code','kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}
def tree(path,relative):
 for name in io.inventory(path,max_bytes=64*1024**2):
  rel=Path(name)
  if set(rel.parts)&skip or rel.name.startswith('.'):continue
  retain(path/name,relative/name)
def complete(path):
 lines=[line.split() for line in path.read_text().splitlines() if line.split() and line.split()[0] in ('real','user','sys')];assert len(lines)==3 and all(len(row)==2 for row in lines);d=dict(lines);assert set(d)=={'real','user','sys'}
 return dict(wall_seconds=float(d['real']),CPU_seconds=round(float(d['user'])+float(d['sys']),2),resolution_seconds=.01)
runtime=ROOT/'.runs/runtime-directory-028/runtime';base=ROOT/'.runs/thermal-parent-normal-controls-002';plan=f.read_json(base/'protocol.json')
assert p.sha(base/'protocol.json')=='4bed8d527b823c770c61133f3248ddcd636cddee8769f5c5045773b239ac27c4'
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']
assert io.inventory(Path(plan['source']).parent)==plan['source_hashes']
full=f.read_json(ROOT/'.runs/full-integration-169/execution.json');assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete']
review=ROOT/'.runs/thermal-parent-installed-result-review-001.json';assert review.is_file()
positive=[]
for label,out,timing in [('native7',runtime/'.runs/thermal-parent-functional-002','.runs/thermal-parent-native7-delivery-002-time.log'),('legacy0',ROOT/'.runs/thermal-parent-legacy0-functional-001','.runs/thermal-parent-legacy0-delivery-001-time.log')]:
 child=f.read_json(out/'result.json');route=f.read_json(Path(child['route_receipt']));exp=f.read_json(Path(child['export_receipt']));outer=f.read_json(base/(label+'-enclosure')/'execution.json')
 assert child['workflow_delivered'] and child['source_originals_unchanged'] and route['accepted'] and exp['export_accepted'] and outer['process']['cleanup_complete']
 assert p.sha(Path(child['route_receipt']))==child['route_sha256'] and p.sha(Path(child['export_receipt']))==child['export_sha256']
 cost=complete(ROOT/timing);assert max(cost['wall_seconds'],cost['CPU_seconds'])<=360
 positive.append(dict(case=label,native_version='10.0.7' if label=='native7' else '10.0.0',incumbent_profile=plan['cases'][label]['incumbent_profile'],workflow_delivered=True,actual_GUI=False,Native=child['native'],candidate_sha256=child['candidate_sha256'],route_receipt_sha256=child['route_sha256'],export_receipt_sha256=child['export_sha256'],whole_project_drc_clean=route['whole_project_drc_clean'],recovery_needed=child['recovery_needed'],complete_cost=cost))
 tree(out,Path('positive')/label)
for label in ('001','002'):tree(runtime/('.runs/thermal-parent-cancel7-'+label),Path('cancellation')/label)
tree(runtime/'.runs/thermal-parent-lineage-faults-001',Path('faults'))
fault=f.read_json(runtime/'.runs/thermal-parent-lineage-faults-001/result.json');assert fault['controls_passed'] and fault['source_and_final_job_bytes_unchanged'] and len(fault['cases'])==9
cancel=f.read_json(runtime/'.runs/thermal-parent-cancel7-002/result.json');assert cancel['controls_passed']
for name in ('thermal-parent-normal-controls-001','thermal-parent-normal-controls-002','thermal-parent-cancel7-001','thermal-parent-cancel7-002','thermal-parent-lineage-faults-001','full-integration-169'):
 tree(ROOT/'.runs'/name,Path('enclosures')/name)
for name in ('setup.json','setup-process.json','doctor.log','venv.log'):
 q=ROOT/'.runs/runtime-directory-028'/name
 if q.is_file():retain(q,Path('integration/runtime028')/name)
retain(runtime/'runtime-distribution.json',Path('integration/runtime028/manifest.json'))
controllers=('prepare-runtime028.py','run-full-integration-169.py','run-thermal-parent-delivery-001.py','run-thermal-parent-delivery-002.py','enclose-thermal-parent-delivery-001.py','enclose-thermal-parent-delivery-002.py','cancel-thermal-parent-native7-001.py','cancel-thermal-parent-native7-002.py','enclose-thermal-parent-cancel7-001.py','enclose-thermal-parent-cancel7-002.py','owned-child-path-observer-001.py','thermal-parent-lineage-faults-001.py','enclose-thermal-parent-lineage-faults-001.py')
for name in controllers:retain(ROOT/'.runs'/name,Path('controllers')/name)
for pattern in ('thermal-parent-native7-delivery-00*.log','thermal-parent-legacy0-delivery-001*.log','thermal-parent-cancel7-00*.log','thermal-parent-lineage-faults-001*.log','owned-child-path-observer-precheck-001*.log','runtime028-prepare-001*.log','full-integration-169*.log'):
 for q in sorted((ROOT/'.runs').glob(pattern)):retain(q,Path('logs')/q.name)
for name in ('thermal-parent-delivery-driver-review-001.json','thermal-parent-cancel-driver-review-001.json','thermal-parent-installed-result-review-001.json'):
 retain(ROOT/'.runs'/name,Path('reviews')/name)
retain(Path(__file__),Path('controllers')/Path(__file__).name)
p.save_json(NOTES/'files.json',dict(schema=1,files=rows,material=material))
record=dict(schema=1,kind='integrated-selected-native-thermal-parent-functional-qualification',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,actual_GUI=False,human_review=False,source_head=plan['source_head'],engineering_runtime='028',manifest_sha256=plan['runtime_manifest_sha256'],qualified_GUI_runtime='026 unchanged;028 GUI pending',protocol_sha256=p.sha(base/'protocol.json'),source_rights=plan['source_rights'],source_hashes=plan['source_hashes'],positive_deliveries=positive,scope='Fresh own incumbent, normal recover CLI, rendered review/software acceptance intent, own120second export and checked delivery. One exposed Interf family. Not actualGUI/WorkflowRoute, an equal-budget baseline comparison, broad superiority, electrical suitability, or release qualification.',policy='Selected7 standard/B1 incumbent; selected0 completion-only. Fixedwhole/allsource layers/native/both only. Existing measured narrow roundPTH savedfill thermal bridge; no new contact/default/GUI/otheradvanced admission.',full169=dict(passed=True,tests=2095,skips=1,unittest_seconds=298.569,complete_cost=complete(ROOT/'.runs/full-integration-169-time.log'),execution_sha256=p.sha(ROOT/'.runs/full-integration-169/execution.json')),preparation=dict(installed_doctor=True,complete_cost=complete(ROOT/'.runs/runtime028-prepare-001-time.log')),failed_attempts=[dict(case='delivery001',Native_executed=False,reason='Harness missing output parent; failedbeforeoutput/engine, preserved.',complete_cost=complete(ROOT/'.runs/thermal-parent-native7-delivery-001-time.log')),dict(case='cancel001',Native_executed=True,control_passed=False,cancellation_requested=False,reason='ps observer EPERM inside unchanged sandbox; actualrepair completedaccepted/noexport. Not a cancellation pass.',complete_cost=complete(ROOT/'.runs/thermal-parent-cancel7-001-time.log'))],observer_prerequisite=dict(Native_executed=False,passed=True,complete_cost=complete(ROOT/'.runs/owned-child-path-observer-precheck-001-time.log'),scope='Unprivileged libproc ownchild path query in identical networkdenial sandbox, no security/global changes.'),cancellation=dict(passed=True,complete_cost=complete(ROOT/'.runs/thermal-parent-cancel7-002-time.log'),phase='Owned repair trial01 Native refill CLI launch/start; observed worker lifetime about.030seconds',requested_signal='SIGINT',actual_exit_code=-15,handled_CLI_exit=2,cleanup_complete=True,parent_accepted=False,repair_validation_passed=False,exported=False,limitations='One observedphase. No completedrefill, SIGINTonly, allphase, permanentdescendant or GUI cancellation claim.'),fault_controls=dict(passed=True,cases=9,cold_and_cached_refusals=18,Native_executed=False,source_and_final_job_bytes_unchanged=True,complete_cost=complete(ROOT/'.runs/thermal-parent-lineage-faults-001-time.log'),limitations='Jobowned evidence/rule copies only; exactbuffers restored. Not fresh Native invaliddesign or hostilewriter protection.'),accounting='All external complete exit wall/fullCPU costs charged, including failedattempts. Stored child/outer costs are nested, notadditional. Fullsuite, preparation, cancellation and readback controls are additional to each delivery. Research, authoring, independentAIreview and curation costs are additional and incompletely instrumented; unknown is not zero. No historical comparison accounting rewritten.',decision='Narrow CLI0/7 recovery/delivery controls pass. Retain B1default and026GUI-qualified instance.028 GUI/current installation qualification stillpending. No broader completion/speed/cleanup/electrical or Windows support claim. Next fix bounded distribution installation blocker, qualify actual native installedworkflow and current GUI; unrelated-family/B0/B1/B2 comparison remains unmet.',new_raw_full_backup=False,references=references,files=rows,files_index=dict(path=str((NOTES/'files.json').relative_to(ROOT)),sha256=p.sha(NOTES/'files.json')),curation_wall_seconds_before_publication=time.monotonic()-START)
p.save_json(ROOT/'evidence/thermal-parent-functional-001.json',record)
print(json.dumps(dict(files=len(rows),bytes=new_bytes,material=len(material),workflow_deliveries=len(positive),accepted=False)))
