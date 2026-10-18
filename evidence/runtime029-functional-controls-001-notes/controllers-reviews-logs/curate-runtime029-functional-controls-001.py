"""Retain completed actual controls with existing bounded text/index helpers."""
from pathlib import Path
import json,sys,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
notes=ROOT/'evidence/runtime029-functional-controls-001-notes';assert not notes.exists();refs={};files=[];material=[];total=0
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
  if set(Path(rel).parts)&{'code','kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:continue
  retain(q/rel,name/rel)
def cost(q):
 rows=[line.split() for line in q.read_text().splitlines() if line.split() and line.split()[0] in ('real','user','sys')];assert len(rows)==3 and all(len(r)==2 for r in rows);d=dict(rows)
 return dict(wall_seconds=float(d['real']),CPU_seconds=round(float(d['user'])+float(d['sys']),2))
runtime=ROOT/'.runs/runtime-directory-029/runtime';inc=f.read_json(ROOT/'.runs/thermal-parent-incumbent7-controls-002/execution.json');default=f.read_json(ROOT/'.runs/runtime029-default-CLI-001/execution.json');bad=f.read_json(ROOT/'.runs/thermal-parent-incumbent7-controls-001/execution.json')
assert inc['controls_passed'] and default['workflow_delivered'] and not default['controls_passed'] and not bad['workflow_delivered']
for label,base in [('unsupported4Cu',ROOT/'.runs/thermal-parent-incumbent7-controls-001'),('incumbent2Cu',ROOT/'.runs/thermal-parent-incumbent7-controls-002'),('ordinary4Cu',ROOT/'.runs/runtime029-default-CLI-001')]:tree(base,Path('enclosures')/label)
for label,path in [('unsupported4Cu',runtime/'.runs/thermal-parent-incumbent-functional-001'),('incumbent2Cu',runtime/'.runs/thermal-parent-incumbent-functional-002'),('ordinary4Cu',runtime/'.runs/production-default-delivery-001')]:tree(path,Path('cases')/label)
for name in ('enclose-thermal-parent-incumbent7-001.py','enclose-thermal-parent-incumbent7-002.py','enclose-runtime029-default-001.py','run-thermal-parent-delivery-002.py','thermal-parent-incumbent-source-assessment-001.json','thermal-parent-incumbent-result-review-001.json','runtime029-default-result-review-001.json','thermal-parent-incumbent7-001.log','thermal-parent-incumbent7-001-time.log','thermal-parent-incumbent7-002.log','thermal-parent-incumbent7-002-time.log','runtime029-default-CLI-001.log','runtime029-default-CLI-001-time.log'):
 retain(ROOT/'.runs'/name,Path('controllers-reviews-logs')/name)
retain(ROOT/'scripts/qualify_runtime_workflow.py',Path('controllers-reviews-logs/qualify_runtime_workflow.py'));retain(Path(__file__),Path('controllers-reviews-logs')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
a=f.read_json(Path(inc['child_receipt']));b=f.read_json(Path(default['child_receipt']));wa=Path(a['route_receipt']);wb=Path(b['workspace'])/'route/result.json';ra=f.read_json(wa);rb=f.read_json(wb)
record=dict(schema=1,kind='runtime029-current-functional-controls-with-failures',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,actual_GUI=False,human_review=False,source_head='a71a39725539061bc33bce687caf712f77e1f529',runtime_manifest_sha256=p.sha(runtime/'runtime-distribution.json'),controls=[dict(case='recovery0014Cu',frozen_control_passed=False,workflow_delivered=False,Native_executed=False,classification='Unsupportedclassflaggedrecovery, notinvalidsource/routingfailure. OrdinaryRoute hasindependentclassauthority; guardnotbypassed, originalflags/rulesunchanged.',complete_cost=cost(ROOT/'.runs/thermal-parent-incumbent7-001-time.log')),dict(case='recovery0022Cu',frozen_control_passed=True,workflow_delivered=True,recovery_needed=False,repair_executed=False,selected_incumbent_hash_unchanged=True,Native_counts=[0,0,0,0],protected_count=1,full_schematic=True,original_preserved=True,candidate_sha256=ra['candidate_sha256'],complete_cost=cost(ROOT/'.runs/thermal-parent-incumbent7-002-time.log')),dict(case='ordinary_default0014Cu',frozen_control_passed=False,workflow_delivered=True,actual_product_policy='Unchangedshippedpref.DEFAULTS seconds120/correctedstandard/both/whole/allsource, actualexport120',frozen_oracle_error='Outerassertincorrectlyexpected90export. Producthelpercorrectlyused gui.export_validation_seconds(120)==120; all6stagesandownNativeproofpassed. Frozenprotocol/oracle/executionstayfailed; no rerouteorrewrittenpass.',independent_posthoc_readback_passed=True,Native_counts=[0,0,6,0],protected_count=10,full_schematic=True,original_preserved=True,candidate_sha256=rb['candidate_sha256'],whole_project_drc_clean=False,complete_cost=cost(ROOT/'.runs/runtime029-default-CLI-001-time.log'))],population='Threecontrols/twoownedsourcetypes retained, includingunsupported4Cu recovery andfaileddefaultoracle. Notindependentdevelopmentfamilies, acomparison oradditionalcompletionclaim. No selection-baseddenominator orstitchedunattendedwinner.',review='SeparateindependentAI reviewsusedexistingcentral/stage readers, noNative reruns; nothumanreview. No materialNative/original gaprequiresreroutingthedefault solelytofixauthoringoracle.',scope='Actualcurrent029CLI recoveredacceptedincumbent(noRepair)2Cu andobservedordinarydefault4Cu sixstagedeliveries. EachfinalhasownNative/fullSCH/original/protectedproof. Flaggedclassesremainunsupportedforrecovery; repairbranchprotection/generalWindows/GUI/electrical/cleanupgains notqualified.',decision='ProceedtofreshactualGUI073; keep026GUI and028repairproof distinct. Actualdefaultdelivered120+120isposthocverified, notpassed frozen90protocol. Broaderfairbaselinecomparison/untouchedfamilies/human/recoverycapacity remainunmet.',source_rights='Projectowned unchanged fixtures; retainedrepositoryGPLlicense; no privateinputs ordownloadedenginepublished.',new_raw_full_backup=False,accounting='Everycompleteexitcostretained, including001refusal anddefaultoraclefailedcommand. Sourceassessment/authoring/AIreviews/curation/preparation/full170/installer costsadditional, incompletelyinstrumented. Noqualityclaimfromtestcounts.',files=files,files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(ROOT/'evidence/runtime029-functional-controls-001.json',record);print(json.dumps(dict(files=len(files),bytes=total,material=len(material),accepted=False)))
