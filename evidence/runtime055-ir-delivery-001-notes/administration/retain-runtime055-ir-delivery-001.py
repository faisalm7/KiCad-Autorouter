"""Retain fresh delivered repair regression, not a stitched comparison."""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
notes=ROOT/'evidence/runtime055-ir-delivery-001-notes';target=ROOT/'evidence/runtime055-ir-delivery-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
read=lambda q:json.loads(q.read_bytes());base=ROOT/'.runs/runtime055-ir-review-regression-001';plan=read(base/'protocol.json');outer=read(base/'enclosure/result.json');producer=Path(outer['child_receipt']);child=read(producer)
assert outer['passed'] and outer['status']=='completed' and child['workflow_delivered'] and child['outcome']=='validated_delivery' and child['controls_passed']
routepath=Path(child['selected_route_receipt']);workspace=routepath.parent.parent;route=read(routepath);export=read(workspace/'export/export.json');review=read(workspace/'review/review.json');choice=read(workspace/'choice/choice.json')
assert route['accepted'] and export['export_accepted'] and route['candidate_sha256']==export['candidate_sha256'] and len(route['trials'])==18
counts=[route['native'][k] for k in ('opens','blocking','warnings','exclusions')];assert counts==[export['native'][k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,42,0]
assert review['status']=='ready_for_manual_review' and choice['choice_recorded'] and choice['choice']=='accept' and not choice['human_pcb_approval_observed']
assert route['schematic_parity']==export['schematic_parity']=='checked by final native DRC'
assert p.tree_hash(Path(plan['source']).parent)==plan['source_hashes'] and route['source_hashes']==export['source_hashes']==plan['source_hashes']
processes={}
for q in producer.parent.glob('*.process.json'):
 data=read(q);assert data['exit_code']==0
 processes[q.name]=dict(wall_seconds=data['wall_seconds'],exit_code=0,sha256=p.sha(q))
queue=[]
for name in ('protocol.json','frozen.json','tools-defaults.json','tools-defaults-process.json','enclosure/command.log','enclosure/process.json','enclosure/result.json'):queue.append((base/name,Path('single-regression')/name))
for q in producer.parent.glob('*.process.json'):queue.append((q,Path('stage-processes')/q.name))
full=ROOT/'.runs/full-integration-205';assert read(full/'execution.json')['passed']
for name in ('protocol.json','execution.json','command.log'):queue.append((full/name,Path('integration/full205')/name))
runtime=ROOT/'.runs/runtime-directory-055/runtime'
for name in ('runtime-distribution.json','RUNTIME_README.txt'):queue.append((runtime/name,Path('runtime')/name))
for name in ('preparation.json','venv-process.json','venv.log'):queue.append((runtime.parent/name,Path('runtime/preparation')/name))
for name in ('run-full-integration-205.py','full-integration-205-controller.log','full-integration-205-time.log','prepare-runtime055-001.py','prepare-runtime055-001.log','prepare-runtime055-001-time.log','freeze-runtime055-review-regression-001.py','freeze-runtime055-review-regression-001.log','freeze-runtime055-review-regression-001-time.log','runtime055-ir-review-regression-001-controller.log','runtime055-ir-review-regression-001-time.log'):
 queue.append((ROOT/'.runs'/name,Path('controllers-and-costs')/name))
queue.append((Path(__file__),Path('administration')/Path(__file__).name))
for path,name in queue:retain(path,name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='runtime055-single-fresh-exposed-IR-Improve-delivery-repair-regression-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,workflow_delivered=True,attempt_qualified=True,project_complete=False,actual_GUI=False,human_review=False,source_head=plan['source_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'],full205=dict(passed=True,tests=2563,skips=1,complete_cost=cost(ROOT/'.runs/full-integration-205-time.log')),build=dict(complete_cost=cost(ROOT/'.runs/prepare-runtime055-001-time.log')),preparation=dict(complete_cost=cost(ROOT/'.runs/freeze-runtime055-review-regression-001-time.log')),single_fresh_exposed_IR_Improve=dict(delivered=True,complete_cost=cost(ROOT/'.runs/runtime055-ir-review-regression-001-time.log'),outer_complete_wall_seconds=outer['complete_wall_seconds'],outer_complete_full_CPU_seconds=outer['complete_full_CPU_seconds'],route_receipt_sha256=p.sha(routepath),review_receipt_sha256=p.sha(workspace/'review/review.json'),choice_receipt_sha256=p.sha(workspace/'choice/choice.json'),export_receipt_sha256=p.sha(workspace/'export/export.json'),candidate_sha256=route['candidate_sha256'],Native_counts=counts,trials=18,review_wall_seconds=review['wall_seconds'],review_CPU_seconds=review['total_cpu_seconds'],choice_wall_seconds=choice['wall_seconds'],choice_CPU_seconds=choice['total_cpu_seconds'],metrics=route['metrics'],stages=processes),scope='Fresh single repair regression on already exposed IR source, unchanged420/450/600/export120 constraints and30s review/choice ceilings. Actual product Request/Workflow/CliJob Route/render/choice/fresh Native export/checked-path delivery. This repairs delivery in this control; it is not a rerun or repair of frozen050 cohort, fair new comparison, untouched confirmation, family gain or electrical/cleanup superiority. All42warnings remain and two original ignored checks stay visible.',remaining='Seven owned Native regressions, current actual GUI/installation and invalid/cancellation/freshness controls still required for changed build. Broader customization/families and fair final policy evaluation, Windows equivalent isolation, restoration capacity and independent engineer/physical evidence remain unmet.',frozen050_comparison_unchanged=True,failures051_to054_unchanged=True,not_a_comparison=True,costs='All conversion/attempt/selection/validation/delivery/readback inside complete308.82wall291.69CPU exit counted once; nested samples overlap. Earlier failed attempts, full suites, builds, source research/authoring/AI review/profiles/GUI/install/curation additional and partly unmetered, not zero. No source/policy change during this run.',raw_scope='Owned code/logs and factual metadata/hashes only in Git. Foreign CAD/DSN/SES/plots/full Native findings remain local under recorded development permission. New raw Mac-only/outside010; no full raw backup/restoration or disk-failure protection claimed.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,delivered=True,project_complete=False)))
