"""Reuse bounded retention for the changed-core installation/ordinary milestone."""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
notes=ROOT/'evidence/runtime033-ordinary-install-001-notes';assert not notes.exists()
refs={};files=[];material=[];total=0
for name in ('runtime032-native-controls-001','runtime032-negative-portfolio-002','runtime030-native-workflow-qualification-001','runtime022-thermal-export-control-001'):
 data=f.read_json(ROOT/('evidence/'+name+'.json'));index=ROOT/data['files_index']['path'];assert p.sha(index)==data['files_index']['sha256'];idx=f.read_json(index)
 for row in idx.get('files',[])+idx.get('material',[]):refs.setdefault(row['sha256'],row.get('path',row.get('retained')))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
functions=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree','cost')];assert len(functions)==3
exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'))
runtime=ROOT/'.runs/runtime-directory-033/runtime';manifest=runtime/'runtime-distribution.json';assert p.sha(manifest)=='115c881aa04a34bf642c57d5af312fe692d1aff013bed095caa3856a614f3987'
for name in ('full-integration-176','install-distribution-native-006'):
 data=f.read_json(ROOT/'.runs'/name/'execution.json');assert data['passed']
 tree(ROOT/'.runs'/name,Path('integration-install')/name)
retain(ROOT/'.runs/runtime-directory-033/result.json',Path('installation/result.json'))
retain(manifest,Path('runtime/runtime-distribution.json'));retain(runtime/'RUNTIME_README.txt',Path('runtime/RUNTIME_README.txt'))
tree(runtime/'.runs/install-native-smoke',Path('installation/native-smoke'));tree(ROOT/'.runs/runtime-directory-033/source-fixture',Path('installation/source-fixture'))
for command in f.read_json(ROOT/'.runs/runtime-directory-033/result.json')['commands']:retain(Path(command['log']),Path('installation/logs')/Path(command['log']).name)
controls=[]
for label in ('whole4Cu','partial2Cu'):
 name='runtime033-ordinary-'+label+'-001';base=ROOT/'.runs'/name;plan=f.read_json(base/'protocol.json');out=Path(plan['output']);execution=f.read_json(base/'execution.json');assert execution['controls_passed']
 tree(base,Path('enclosures')/label);tree(out,Path('cases')/label)
 controls.append(dict(case=label,passed=True,complete_cost=cost(ROOT/'.runs'/(name+'-time.log')),Native_counts=execution['Native_counts'],protected_count=execution['protected_count'],source_hashes=plan['source_hashes'],settings=plan['settings'],output_receipt_sha256=p.sha(out/'result.json'),protocol_sha256=p.sha(base/'protocol.json')))
 for suffix in ('-time.log','-controller.log'):retain(ROOT/'.runs'/(name+suffix),Path('logs')/(name+suffix))
for name in ('run-full-integration-176.py','full-integration-176-time-001.log','full-integration-176-controller-001.log','run-install-distribution-native-006.py','freeze-install-distribution-native-006.py','freeze-install-distribution-native-006-001.log','install-distribution-native-006-time-001.log','install-distribution-native-006-controller-001.log','ordinary-standard-negative-targeted-001.log','ordinary-standard-negative-targeted-001-time.log','ordinary-standard-negative-review-001.json','current-method-controller-review-001.json','enclose-native7-independent-control-004.py'):
 retain(ROOT/'.runs'/name,Path('controllers-reviews')/name)
retain(ROOT/'scripts/qualify_current_method.py',Path('controllers-reviews/qualify_current_method.py'));retain(Path(__file__),Path('controllers-reviews')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='runtime033-changed-core-full-install-and-ordinary-six-stage-native-milestone',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,accepted=False,actual_GUI=False,human_review=False,source_head='a476a0a0647bc51889d291e3e6e2598f4ec24370',runtime_manifest_sha256=p.sha(manifest),runtime_modules=46,runtime_immutable_files=51,
 full176=dict(passed=True,tests=2182,skips=1,complete_cost=cost(ROOT/'.runs/full-integration-176-time-001.log'),scope='Frozen product/modules/tests/admin sources in full176 protocol. The later new current-method controller is source-reviewed but not executed or implicitly covered by this full suite.'),installation=dict(passed=True,complete_cost=cost(ROOT/'.runs/install-distribution-native-006-time-001.log'),scope='Fresh distribution/copiedvenv/doctor/actual Native Route/check on owned fixture with no supplied schematic. Existing Mac/tools/cache/fixedpath, not cleanOS/relocation/standalone/GUI/Windows.'),controls=controls,
 implementation='Explicit ordinary_profile standard|tuned for non-admitting completed-negative diagnostics; defaulttuned/Contextauthority/positive/export/nativecapability guards unchanged.66targeted controls and independentAIreview retained. New033 ordinary positive workflow Native controls pass; actual ordinary standard negative still pending.',
 Native_and_original='Each delivered ordinary Route/export has own selected10.0.7 refill/connectivity/allseverity/fullSCH/original-rule/semantic/protected proof. Whole0opens0blocking6warnings0exclusions/protected10; partial0all/protected4. Both original ignored checks remain visible. Scope acceptance is not wholeprojectcleanliness or electrical/physical validation.',
 comparison='032stock/scored/portfolio/cancel/invalid actual controls retain exact32scope. Failednegative001 and successfulsamebudget002 remain preserved. No automatic promotion to033 or fairmatrix. New scripts/qualify_current_method.py2610e817 source review/syntax only; copied frozen payload and actual installed default/CLI optimizer vsbaseline qualifications remain to run. Cdefault is B1-equivalent default, Cthermal optional; rejected thermal parent without final proof remains method_not_delivered, not baseline routerfailure.',
 source_rights='Project-owned generated board/schematic geometry under repositoryGPL. Unchanged official KiCad demo project/settings retain CC-BY-SA-4.0 source/notices via earlier linked packets/SOURCE_LEDGER. No private input, local-reference, downloadedengine/app or bulkdataset included.',
 costs='Complete exits for each event retained, not nested samples. Preparation/freezing/research/authoring/independentreview/curation extra, unknowninteractiveCPU notzero. No routing gain/speedup/generalization claim from correctness tests or these fixtures.',
 remaining=['Own actual ordinary standard negative/current frozenmethod comparison and newfinal Native controls where relevant','CurrentGUI026lastactual/029preparednotpromoted; Windows009failedisolation/Native slice','Fair broader unrelatedlicensed development/untouchedpolicyconfirmation; actualengineercleanup/physicalreview','CleanOS-relocation-standalone; newtargetrestoreheadroom; separateformalpublicationapproval'],
 backup_scope='Essential source/proof for auditedGitbackup only; newerfullraw remains onMacoutside008/010. No new full restoration or release completion.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(ROOT/'evidence/runtime033-ordinary-install-001.json',record)
print(json.dumps(dict(files=len(files),bytes=total,material=len(material),passed=True,project_complete=False)))
