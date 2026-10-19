"""Retain completed actual controls with existing bounded text/index helpers."""
from pathlib import Path
import json,sys,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
notes=ROOT/'evidence/runtime030-native-workflow-qualification-001-notes';assert not notes.exists();refs={};files=[];material=[];total=0
for name in ('evidence/install-distribution-native-001.json','evidence/thermal-parent-functional-001.json','evidence/gui-runtime026-072-native-controls-001.json','evidence/runtime026-installed-CLI-001.json'):
 j=f.read_json(ROOT/name)
 for r in j.get('files',[]):refs.setdefault(r['sha256'],r['path'])
 if j.get('files_index'):
  q=ROOT/j['files_index']['path'];assert p.sha(q)==j['files_index']['sha256'];idx=f.read_json(q)
  for r in idx.get('files',[]):refs.setdefault(r['sha256'],r['path'])
  for r in idx.get('material',[]):refs.setdefault(r['sha256'],r['retained'])
def retain(q,name):
 global total
 raw=io.read_bytes(q,4*1024**2);sha=hashlib.sha256(raw).hexdigest();target=refs.get(sha)
 if target is None:
  assert b'\0' not in raw;raw.decode('utf-8');dest=notes/name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(raw)
  target=str(dest.relative_to(ROOT));refs[sha]=target;files.append(dict(path=target,bytes=len(raw),sha256=sha));total+=len(raw);assert total<16*1024**2 and len(files)<2000
 else:assert p.sha(ROOT/target)==sha
 material.append(dict(original=str(q.relative_to(ROOT)),retained=target,bytes=len(raw),sha256=sha))
def tree(q,name):
 for rel in io.inventory(q,max_bytes=64*1024**2):
  if set(Path(rel).parts)&{'kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:continue
  retain(q/rel,name/rel)
def cost(q):
 rows=[line.split() for line in q.read_text().splitlines() if line.split() and line.split()[0] in ('real','user','sys')];assert len(rows)==3 and all(len(r)==2 for r in rows);d=dict(rows)
 return dict(wall_seconds=float(d['real']),CPU_seconds=round(float(d['user'])+float(d['sys']),2))

review=ROOT/'.runs/runtime030-native-delivery-result-review-001.json';assert review.is_file()
runtime=ROOT/'.runs/runtime-directory-030/runtime';manifest=runtime/'runtime-distribution.json';assert p.sha(manifest)=='308b644b34ca62ca4252a1cd9b583d7df037eb34da902be36d8076a64716e111'
full=f.read_json(ROOT/'.runs/full-integration-172/execution.json');install=f.read_json(ROOT/'.runs/install-distribution-native-003/execution.json');assert full['passed'] and install['passed']
tree(ROOT/'.runs/full-integration-172',Path('integration/full172'));tree(ROOT/'.runs/install-distribution-native-003',Path('installation/enclosure'))
retain(ROOT/'.runs/runtime-directory-030/result.json',Path('installation/result.json'));retain(manifest,Path('runtime/runtime-distribution.json'));retain(runtime/'RUNTIME_README.txt',Path('runtime/RUNTIME_README.txt'))
for cmd in f.read_json(ROOT/'.runs/runtime-directory-030/result.json')['commands']:
 retain(Path(cmd['log']),Path('installation/logs')/Path(cmd['log']).name)
tree(runtime/'.runs/install-native-smoke',Path('installation/native-smoke'));tree(ROOT/'.runs/runtime-directory-030/source-fixture',Path('installation/source-fixture'))
rows=[]
for label,folder in [('standard','runtime030-comparison-standard_positive-001'),('tuned','runtime030-comparison-tuned_variant-001'),('ordinary_whole','runtime030-ordinary-whole4Cu-001'),('ordinary_partial','runtime030-ordinary-partial2Cu-001'),('invalid001','runtime030-comparison-native-invalid-controls-001'),('invalid002','runtime030-comparison-native-invalid-controls-002')]:
 base=ROOT/'.runs'/folder;plan=f.read_json(base/'protocol.json');child=Path(plan['output']);tree(base,Path('enclosures')/label);tree(child,Path('cases')/label)
 ex=f.read_json(base/'enclosure/result.json') if label in ('standard','tuned','invalid001','invalid002') else f.read_json(base/'execution.json')
 data=f.read_json(child/'result.json');native=data.get('native')
 rows.append(dict(case=label,enclosing_control_passed=ex.get('passed',ex.get('controls_passed')),child_status=data['status'],child_passed=data.get('passed',data.get('workflow_delivered',data.get('control_passed'))),complete_cost=cost(ROOT/'.runs'/(folder+'-time.log')),source_or_fixture_sha256=plan.get('source_hashes',plan.get('fixture_sha256')),output_receipt_sha256=p.sha(child/'result.json'),Native=native,scope=plan['scope']))
# All useful source controllers, failed preparation and independent review costs.
controllers=['run-full-integration-172.py','full-suite-local-root-019.py','run-install-distribution-native-003.py','prepare-runtime030-native-control-material-001.py','freeze-runtime030-comparison-positive-plans-001.py','enclose-runtime030-comparison-001.py','enclose-runtime030-independent-control-001.py','enclose-runtime030-ordinary-workflow-001.py','qualify-comparison-delivery-001.py','qualify-runtime030-comparison-native-invalid-001.py','qualify-runtime030-comparison-native-invalid-002.py','native7-comparison-native-control-preparation-001.json','runtime030-comparison-native-invalid-preparation-001.json','runtime030-native-invalid-controller-repair-review-001.json','runtime030-native-delivery-result-review-001.json','runtime029-gui073-toolbar-access-state-004.json','runtime030-native-controls-preparation-001.log','runtime030-native-controls-preparation-001-time.log','freeze-runtime030-comparison-positive-plans-001.log','freeze-runtime030-comparison-positive-plans-001-time.log','full-integration-172-time-001.log','full-integration-172-controller-001.log','install-distribution-native-003-time-001.log','install-distribution-native-003-controller-001.log']
for name in controllers:retain(ROOT/'.runs'/name,Path('controllers-reviews-logs')/name)
for name in ['runtime030-comparison-standard_positive-001','runtime030-comparison-tuned_variant-001','runtime030-ordinary-whole4Cu-001','runtime030-ordinary-partial2Cu-001','runtime030-comparison-native-invalid-controls-001','runtime030-comparison-native-invalid-controls-002']:
 for suffix in ['-controller.log','-time.log']:retain(ROOT/'.runs'/(name+suffix),Path('controllers-reviews-logs')/(name+suffix))
tree(ROOT/'.runs/runtime030-native-controls-preparation-001',Path('preparation'));tree(ROOT/'.runs/install-distribution-native-002',Path('installation/unexecuted002'))
# Retained review envelope only; never inspect the historical .runs tree.
tree(ROOT/'.runs/runtime030-native-delivery-readback-001',Path('independent-readback'))
for path in [ROOT/'.runs/runtime030-native-delivery-readback-001-time.log',ROOT/'.runs/runtime030-native-delivery-readback-001-controller.log']:
 if path.is_file():retain(path,Path('independent-readback')/path.name)
retain(ROOT/'scripts/qualify_runtime_workflow.py',Path('controllers-reviews-logs/qualify_runtime_workflow.py'));retain(Path(__file__),Path('controllers-reviews-logs')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
summary=dict(schema=1,kind='runtime030-native-workflow-qualification-with-failures',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,actual_GUI=False,human_review=False,source_head='a658e62c71204f7242a66c695f22a1b3e2263482',runtime_manifest_sha256=p.sha(manifest),runtime_modules=46,runtime_immutable_files=51,full172=dict(passed=True,tests=2125,skips=1,complete_cost=cost(ROOT/'.runs/full-integration-172-time-001.log')),full171_failure='evidence/native7-comparison-integration-repair-001.json',installation=dict(passed=True,mode='distribution',Native_version='10.0.7',complete_cost=cost(ROOT/'.runs/install-distribution-native-003-time-001.log'),scope='Actual copied venv/doctor/owned Native Route/check, no suppliedSCH; not cleanOS/relocation/GUI/Windows.'),controls=rows,original_and_native='Every delivered ordinary/comparison Route/export retains own actual selected7 Native/refill/allseverity/fullSCH/original/protected proof. Whole ordinary has6warnings, notwholeDRCclean. Comparison controls carry production_admittedFalse and ordinary consumers refuse.',invalid_controls='001 failed before a Native mutation due to controller literal named-net assumption on an unchanged numbered-net board.002 reuses existing net identity/conversion helpers; actual addedshort0opens/3blocking/0warnings/0exclusions and protectedwidth+1nm0allNative but invariantrefused before moreNative. Both attempts and costs retained, no productconstraint change.',comparison_scope='Owned unflagged2Cu standard/tuned API functional controls,120route and30-60fresh export within180wholecaps. Not a new fairB0/B1/B2/C evaluation, independentfamily gain, speedup, GUI or production admission. Flagged schematic classes, B0/portfolio and advanced combinations remain unsupported by comparison API; ordinarycorrectedB1 default unchanged.',review='Independent installed current readback with existing central APIs; AI review, not human PCB review. See exact bounded execution and report.',accounting='All complete exits include conversions/engine/validation/delivery/readback/publication. Shared preparation0.39wall0.33CPU and freeze0.10wall0.08CPU actual events retained once; conservative4s planning allowance charged to each API envelope is not actual measured runtime. Full171failure/targetedrepairs earlierpacket and research/authoring/review/curation costs additional; interactivewholeCPU unknown, notzero.',GUI_gate='026lastGUIqualified;029GUI073prepared, lastactualreport Maclocked after earlier coordinate-onlynoWindowsAvailable.030notGUIqualified; no oldproofpromotion or new unlockloop.',remaining=['Own completed-negative and actualenginecancel API qualification before faircomparison','Fresh fair current installed B0/B1/competentB2/C and broader independent licensed development/untouched frozenpolicy confirmation','Current actualGUI, Windows equivalent safeguards/native slice, new-target restoration headroom, authorized human/physical/cleanup validation and separate formalpublication approval'],backup_scope='Essential owned source/proof intended for auditedGit; downloadedtools/venv/caches omitted. Later fullraw remains Mac-only outside010. Not a fullrawbackup/restoration or releasecompletion.',source_rights='Projectowned unchanged generated fixtures/core under retainedrepositoryGPLlicense. No privateinputs or downloadedengine/apps published.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(ROOT/'evidence/runtime030-native-workflow-qualification-001.json',summary);print(json.dumps(dict(files=len(files),bytes=total,material=len(material),project_complete=False)))
