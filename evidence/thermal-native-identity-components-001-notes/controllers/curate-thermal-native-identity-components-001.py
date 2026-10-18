"""Existing bounded text-copy/index pattern for completed component evidence."""
from pathlib import Path
import sys,json,hashlib,datetime,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
START=time.monotonic();notes=ROOT/'evidence/thermal-native-identity-components-001-notes';assert not notes.exists();refs={};references=[]
for name in ('evidence/interf-installed023-comparison-001.json','evidence/runtime026-interf-native7-prerequisite-001.json','evidence/gui-runtime026-072-native-controls-001.json','evidence/thermal-native-identity-targeted-001.json'):
 q=ROOT/name;old=f.read_json(q);references.append(dict(path=name,sha256=p.sha(q)))
 for row in old.get('files',[]):refs.setdefault(row['sha256'],row['path'])
 if old.get('files_index'):
  index=ROOT/old['files_index']['path'];assert p.sha(index)==old['files_index']['sha256']
  for row in f.read_json(index).get('material',[]):refs.setdefault(row['sha256'],row['retained'])
rows=[];material=[];count=0
skip={'code','kicad-cache','kicad-config','kicad-documents','engine-config','tmp'}
def retain(path,relative):
 global count
 raw=io.read_bytes(path,4*1024**2);digest=hashlib.sha256(raw).hexdigest();public=refs.get(digest)
 if public is None:
  assert b'\0' not in raw;raw.decode('utf-8');dest=notes/relative;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(raw)
  public=str(dest.relative_to(ROOT));refs[digest]=public;rows.append(dict(path=public,bytes=len(raw),sha256=digest));count+=len(raw);assert count<32*1024**2 and len(rows)<2500
 else:assert p.sha(ROOT/public)==digest
 material.append(dict(original=str(path.relative_to(ROOT)),retained=public,bytes=len(raw),sha256=digest))
def tree(path,relative):
 for name in io.inventory(path,max_bytes=32*1024**2):
  rel=Path(name)
  if set(rel.parts)&skip or rel.name.startswith('.'):continue
  retain(path/name,relative/name)
base=ROOT/'.runs/thermal-native-identity-controls-001';plan=f.read_json(base/'protocol.json');runtime=ROOT/'.runs/runtime-directory-027/runtime';engineering=f.read_json(ROOT/'.runs/runtime-directory-027/setup.json');full=f.read_json(ROOT/'.runs/full-integration-168/execution.json')
assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete'] and p.sha(runtime/'runtime-distribution.json')==plan['engineering_runtime_manifest_sha256']
for label in ('legacy0','native7','invalid7','cancel7'):
 q=ROOT/('.runs/thermal-native-identity-'+label+'-readback-001.json');assert f.read_json(q)['readback_passed'];retain(q,Path('readbacks')/q.name)
for label,folder in [('legacy0',Path(plan['cases']['legacy0']['output'])),('native7',Path(plan['cases']['native7']['output'])),('invalid001',Path(plan['cases']['invalid7']['output'])),('invalid002',runtime/'.runs/thermal-identity-invalid7-002'),('invalid003',runtime/'.runs/thermal-identity-invalid7-003'),('cancel7',Path(plan['cases']['cancel7']['output']))]:
 tree(folder,Path('cases')/label)
for directory in ('thermal-native-identity-controls-001','thermal-native-identity-controls-invalid-002','thermal-native-identity-controls-invalid-003'):
 folder=ROOT/'.runs'/directory
 # Component0 has already been copied above. Enclosures and protocols are small.
 for name in io.inventory(folder,max_bytes=32*1024**2):
  rel=Path(name)
  if 'legacy0-case' in rel.parts:continue
  retain(folder/name,Path('enclosures')/directory/name)
for name in ('run-thermal-native-identity-component-001.py','run-thermal-native-identity-component-invalid-002.py','run-thermal-native-identity-component-invalid-003.py','enclose-thermal-native-identity-001.py','enclose-thermal-native-identity-invalid-002.py','enclose-thermal-native-identity-invalid-003.py','prepare-thermal-identity-invalid002.py','prepare-thermal-identity-invalid003.py','readback-thermal-native-identity-components-001.py','prepare-runtime027.py','run-full-integration-168.py'):
 retain(ROOT/'.runs'/name,Path('controllers')/name)
for name in ('thermal-native-identity-legacy0-001.log','thermal-native-identity-legacy0-001-time.log','thermal-native-identity-native7-001.log','thermal-native-identity-native7-001-time.log','thermal-native-identity-invalid7-001.log','thermal-native-identity-invalid7-001-time.log','thermal-native-identity-invalid7-002.log','thermal-native-identity-invalid7-002-time.log','thermal-native-identity-invalid7-003.log','thermal-native-identity-invalid7-003-time.log','thermal-native-identity-cancel7-001-time.log','prepare-thermal-identity-invalid002.log','prepare-thermal-identity-invalid002-time.log','prepare-thermal-identity-invalid003.log','prepare-thermal-identity-invalid003-time.log','runtime027-prepare-001.log','runtime027-prepare-001-time.log'):
 retain(ROOT/'.runs'/name,Path('logs')/name)
for folder in ('full-integration-168','runtime-directory-027'):
 names=('protocol.json','execution.json','command.log') if folder.startswith('full') else ('setup.json','setup-process.json')
 for name in names:
  q=ROOT/'.runs'/folder/name
  if q.is_file():retain(q,Path('integration')/folder/name)
retain(runtime/'runtime-distribution.json',Path('integration/runtime027-manifest.json'));retain(Path(__file__),Path('controllers')/Path(__file__).name)
index=dict(schema=1,files=rows,material=material);p.save_json(notes/'files.json',index)
costs=[dict(case=k,complete_wall_seconds=w,complete_CPU_seconds=c) for k,w,c in [('legacy0',14.35,11.86),('native7',12.92,11.78),('invalid001',.77,.71),('invalid002',3.62,2.09),('invalid003',5.03,4.09),('cancel7',3.63,2.91)]]
record=dict(schema=1,kind='selected-native-thermal-identity-component-controls',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,routing_accepted=False,production_admitted=False,delivered=False,project_complete=False,actual_GUI=False,human_review=False,source_head=plan['source_head'],engineering_runtime_manifest_sha256=plan['engineering_runtime_manifest_sha256'],qualified_product_runtime='026 unchanged',protocol_sha256=p.sha(base/'protocol.json'),source_hashes=plan['source_hashes'],positive_components_verified=['10.0.0','10.0.7'],prevalidation_counts=[0,1,22,0],positive_trial_counts=[0,0,22,0],positive_trial_count_each=1,positive_bounded_proposal_count_each=4,original_nonrouting_and_protected_preserved=True,source_originals_unchanged=True,shared_retained_DRC_readbacks=12,invalid003=dict(qualified=True,counts=[1,1,22,0],removed_unprotected_route_count=2,net='/8MH-OUT',source_design_invalid=False,geometry_or_trials_executed=False,repair_status='unsupported'),cancel=dict(native_DRC_observed=True,phase='final-drc',requested_signal='SIGINT',actual_exit_code=-15,cleanup_complete=True,overall_accepted=False,repair_executed=False,Control_C_and_enclosing130_reap='lead tool observation only; separate durable worker receipt and complete exit log retained'),failed_controls=[dict(case='invalid001',qualified=False,Native_executed=False,reason='Harness called nonexistent sx.atom; no steps, preserved.'),dict(case='invalid002',qualified=False,Native_refill_executed=True,reason='Native reassigned wrong-net segment; existing route-identity guard refused before planned final eligibility control. No new rawNative critical outcome; no geometry/trials.')],harness_limitation='Frozen outer controllers allow135s enclosing status although protocol charges120s including finalization. All actual complete exits are independently below120; no result inferred from the looser future pass gate. Correct before reuse; do not alter retained controllers or rerun completed cases.',complete_case_costs=costs,case_cost_sum=dict(wall_seconds=round(sum(x['complete_wall_seconds'] for x in costs),2),CPU_seconds=round(sum(x['complete_CPU_seconds'] for x in costs),2)),full168=dict(passed=True,tests=2085,skips=1,unittest_seconds=295.880,complete_wall_seconds=297.13,complete_CPU_seconds=285.92,execution_sha256=p.sha(ROOT/'.runs/full-integration-168/execution.json')),engineering_preparation=dict(prepared=True,installed_doctor=True,complete_wall_seconds=3.04,complete_CPU_seconds=2.02,source_head=plan['source_head'],manifest_sha256=plan['engineering_runtime_manifest_sha256'],scope='Fixed path existing-Mac engineering copy only; no GUI, normal thermal parent, export or product admission.'),accounting='Every case complete exit measured. Stored inner/outer sampled totals are nested, not additional. Harness prep .32/.30 and .49/.46 logs retained; initial prep assertion before output/Native was observed but uninstrumented, nonzero authoring cost unknown. Research, source authoring, AI review and curation are additional and incompletely instrumented. No quality, speed, baseline comparison or unrelated-family claim.',decision='Identity prerequisite supports the existing narrow saved-fill/round-PTH mechanism on7. All public7recover/completion/advanced receipt guards remain closed. Next minimal integration must separately qualify exact normal parent/child lineage, negative and cancellation handling, fresh final delivery and export before admission. Contact7 and default/GUI promotion remain unsupported; B1default and immutable026 unchanged.',source_rights=plan['source_rights'],references=references,files=rows,files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')),new_raw_full_backup=False,curation_wall_seconds_before_publication=time.monotonic()-START)
p.save_json(ROOT/'evidence/thermal-native-identity-components-001.json',record);print(json.dumps(dict(files=len(rows),bytes=count,material=len(material),accepted=False,counts=[0,0,22,0])))
