"""Existing bounded text-copy/index pattern; no installer/Native/test rerun."""
from pathlib import Path
import json,sys,hashlib,datetime,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,floor_route as f
START=time.monotonic();notes=ROOT/'evidence/install-distribution-native-001-notes';assert not notes.exists();rows=[];material=[];refs={};total=0
for name in ('evidence/thermal-parent-functional-001.json','evidence/runtime026-installed-CLI-001.json','evidence/install-distribution-development-001.json'):
 j=f.read_json(ROOT/name)
 for r in j.get('files',[]):refs.setdefault(r['sha256'],r['path'])
 if j.get('files_index'):
  q=ROOT/j['files_index']['path'];assert p.sha(q)==j['files_index']['sha256'];idx=f.read_json(q)
  for r in idx.get('files',[]):refs.setdefault(r['sha256'],r['path'])
  for r in idx.get('material',[]):refs.setdefault(r['sha256'],r['retained'])
def retain(path,relative):
 global total
 raw=io.read_bytes(path,4*1024**2);digest=hashlib.sha256(raw).hexdigest();target=refs.get(digest)
 if target is None:
  assert b'\0' not in raw;raw.decode('utf-8');dest=notes/relative;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(raw)
  target=str(dest.relative_to(ROOT));refs[digest]=target;rows.append(dict(path=target,bytes=len(raw),sha256=digest));total+=len(raw);assert total<16*1024**2 and len(rows)<2000
 else:assert p.sha(ROOT/target)==digest
 material.append(dict(original=str(path.relative_to(ROOT)),retained=target,bytes=len(raw),sha256=digest))
def tree(path,relative):
 for name in io.inventory(path,max_bytes=32*1024**2):
  if set(Path(name).parts)&{'code','kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:continue
  retain(path/name,relative/name)
def complete(path):
 rows=[line.split() for line in path.read_text().splitlines() if line.split() and line.split()[0] in ('real','user','sys')];assert len(rows)==3 and all(len(row)==2 for row in rows);d=dict(rows)
 return dict(wall_seconds=float(d['real']),CPU_seconds=round(float(d['user'])+float(d['sys']),2),resolution_seconds=.01)
base=ROOT/'.runs/install-distribution-native-001';out=ROOT/'.runs/runtime-directory-029';runtime=out/'runtime';outer=f.read_json(base/'execution.json');result=f.read_json(out/'result.json');full=f.read_json(ROOT/'.runs/full-integration-170/execution.json');review=ROOT/'.runs/install-distribution-native-result-review-001.json'
assert outer['passed'] and outer['process']['cleanup_complete'] and result['passed'] and p.sha(out/'result.json')==outer['child_receipt_sha256'] and full['passed'] and full['sources_unchanged'] and review.is_file()
for folder,label in [(base,Path('enclosure')),(out/'source-fixture',Path('fixture')),(runtime/'.runs/install-native-smoke',Path('native')), (ROOT/'.runs/full-integration-170',Path('integration/full170'))]:tree(folder,label)
for name in ('result.json','source-tracked.json'):retain(out/name,Path('installation')/name)
retain(runtime/'runtime-distribution.json',Path('installation/runtime029-manifest.json'))
observations=sorted(out.glob('source-git-*.json'));assert len(observations)==556
for q in observations:retain(q,Path('git-observations')/q.name)
for name in ('run-install-distribution-native-001.py','run-full-integration-170.py','install-distribution-native-001.log','install-distribution-native-001-time.log','full-integration-170-enclosure.log','full-integration-170-time.log','install-distribution-implementation-handoff-001.json','install-distribution-native-result-review-001.json'):
 retain(ROOT/'.runs'/name,Path('controllers-and-logs')/name)
retain(Path(__file__),Path('controllers-and-logs')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=rows,material=material))
native=f.read_json(runtime/'.runs/install-native-smoke/result.json')
summary=dict(schema=1,kind='actual-archive-independent-distribution-installation-qualification',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,accepted=False,project_complete=False,actual_GUI=False,human_review=False,source_head=result['git_head'],runtime='029',runtime_manifest_sha256=result['source_provenance']['manifest_sha256'],selected_native_version=result['native_version'],selected_product_files=result['installed_tracked_files'],complete_tracked_archive_census=False,history_fetch=False,engine_acquisition_retested=False,binary_redistribution_qualified=False,actual_commands=[v['name'] for v in result['commands']],whole_cost=complete(ROOT/'.runs/install-distribution-native-001-time.log'),stored_outer_costs_nested=dict(wall=outer['complete_wall_seconds'],CPU=outer['complete_full_CPU_seconds']),scratch_bytes=result['scratch_bytes'],source_unchanged=True,runtime_unchanged=True,original_native_design_invariants=native['invariants_unchanged'],Native_source_counts=[native['source_drc'][k] for k in ('opens','blocking','warnings','exclusions')],Native_final_counts=[native['native'][k] for k in ('opens','blocking','warnings','exclusions')],schematic_parity=native['schematic_parity'],whole_project_drc_clean=native['whole_project_drc_clean'],candidate_sha256=native['candidate_sha256'],cleanup_complete=True,Git_observations=dict(count=556,wrapped=True,process_receipts_retained=True,raw_logs='ExactrawlogsremaininMac-ownedoutput, includingNUL/binary ls-tree. Their hashes/args/resources and independent actualreadback retained; selectedsource reproducedfromcommittedHEAD. Not a complete rawbackup.'),full170=dict(passed=True,tests=2099,skips=1,unittest_seconds=301.459,source_pins_unchanged=True,complete_cost=complete(ROOT/'.runs/full-integration-170-time.log'),execution_sha256=p.sha(ROOT/'.runs/full-integration-170/execution.json')),scope='Fresh fixed-path productruntime/venv, doctor, ownfixtureRoute/check on existingMac/apps/cache. Source2expectedopens→0,0blocking/0warnings; no nativeschematic supplied. This is an installation/functional smoke, not sixstage/GUI/cleanOS/relocation/Windows or generalrouting improvement.',source_rights='Projectownedfixture/runtime underretainedrepositoryGPLlicense. Enginecopiedonlylocally fromexistingpinnedofficialcache; formalpackage/binaryredistributionunqualified.',review='IndependentAI result/source reviews, nothumanreview; no Native rerun.',decision='Installationblocker closedwithinrecordedexistingMacscope. Nextboundedacceptedincumbent branch/currentGUI073 qualification uses029;026GUI and028repairproofs remainseparate. No oldGUIpromotion.',accounting='Externalcompletewall/fullwaitedCPU includes556Gitobservations and allinstall/Native commands and finalpublicationchecks. Storedinner/outercostsnested, notadditional. Full170 and allresearch/authoring/AIreview/curationadditional; unknowninteractivecostnotzero.',new_raw_full_backup=False,files=rows,files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')),curation_wall_seconds_before_publication=time.monotonic()-START)
p.save_json(ROOT/'evidence/install-distribution-native-001.json',summary);print(json.dumps(dict(files=len(rows),bytes=total,material=len(material),passed=True)))
