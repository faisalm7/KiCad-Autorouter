"""Retain complete failed repair regression and its follow-up source controls."""
from pathlib import Path
import ast,datetime,hashlib,json,pstats,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
notes=ROOT/'evidence/runtime051-review-regression-001-notes';target=ROOT/'evidence/runtime051-review-regression-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
read=lambda q:json.loads(Path(q).read_bytes())
b=ROOT/'.runs/runtime051-ir-review-regression-001';plan=read(b/'protocol.json');outer=read(b/'enclosure/result.json');producer=Path(outer['child_receipt']);child=read(producer);route_path=Path(child['selected_route_receipt']);route=read(route_path);review_path=route_path.parent.parent/'review/review.json';review=read(review_path)
assert outer['passed'] is False and child['workflow_delivered'] is False and child['outcome']=='unqualified_failure'
assert route['accepted'] is True and len(route['trials'])==18
assert read(producer.parent/'review.log')=={'status':'rejected','reason':'review copy exceeded 30-second wall or full CPU ceiling'}
assert [route['native'][k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,42,0]
profile=ROOT/'.runs/runtime051-improve-review-profile-001';assert read(profile/'execution.json')['inputs_tools_unchanged']
stats=pstats.Stats(str(profile/'review.pstats'));rows=[]
for (filename,line,function),(primitive,calls,self_time,cumulative,callers) in stats.stats.items():
 rows.append(dict(file=Path(filename).name,line=line,function=function,primitive_calls=primitive,calls=calls,self_seconds=self_time,cumulative_seconds=cumulative))
facts=dict(schema=1,kind='instrumented051-review-profile-facts',total_calls=stats.total_calls,primitive_calls=stats.prim_calls,instrumented_seconds=stats.total_tt,largest_cumulative=sorted(rows,key=lambda r:r['cumulative_seconds'],reverse=True)[:50],syntax=[r for r in rows if r['file']=='sexpr.py'],profile_sha256=p.sha(profile/'review.pstats'),profile_local_only=True,scope='Separate instrumentation of retained051 failed review, not normal timing/acceptance or a new route. JSON rejects despite profiler exit0; first central and limited later guards measured before unchanged30s ceiling.')
p.save_json(profile/'facts.json',facts)
queue=[]
for name in ('protocol.json','frozen.json','tools-defaults.json','tools-defaults-process.json','enclosure/command.log','enclosure/process.json','enclosure/result.json'):
 if (b/name).is_file():queue.append((b/name,Path('single-regression')/name))
for name in ('review.log','review.process.json'):queue.append((producer.parent/name,Path('failure')/name))
full=ROOT/'.runs/full-integration-201'
assert read(full/'execution.json')['passed'] is True
for name in ('protocol.json','execution.json','command.log'):queue.append((full/name,Path('integration/full201')/name))
runtime=ROOT/'.runs/runtime-directory-051/runtime'
for name in ('runtime-distribution.json','RUNTIME_README.txt'):queue.append((runtime/name,Path('runtime')/name))
for name in ('preparation.json','venv-process.json','venv.log'):queue.append((runtime.parent/name,Path('runtime/preparation')/name))
for name in ('protocol.json','execution.json','command.log','facts.json'):queue.append((profile/name,Path('profile')/name))
for name in ('run-full-integration-201.py','full-integration-201-controller.log','full-integration-201-time.log','prepare-runtime051-001.py','prepare-runtime051-001.log','prepare-runtime051-001-time.log','freeze-runtime051-review-regression-001.py','freeze-runtime051-review-regression-001.log','freeze-runtime051-review-regression-001-time.log','runtime051-ir-review-regression-001-controller.log','runtime051-ir-review-regression-001-time.log','profile-runtime051-improve-review-001.py','profile-runtime051-improve-review-001.log','profile-runtime051-improve-review-001-time.log','native7-parent-import-order-001.log','native7-parent-import-order-001-time.log','native7-parent-import-order-002.log','native7-parent-import-order-002-time.log','native7-parent-import-order-003.log','native7-parent-import-order-003-time.log','native7-replay-source-review-001.json','run-native7-replay-targeted-001.py','native7-replay-targeted-001.log','native7-replay-targeted-001-time.log'):
 queue.append((ROOT/'.runs'/name,Path('controllers-and-costs')/name))
for name in ('execution.json','command.log'):queue.append((ROOT/'.runs/native7-replay-targeted-001'/name,Path('targeted')/name))
queue.append((Path(__file__),Path('administration')/Path(__file__).name))
for path,name in queue:retain(path,name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='runtime051-review-scaling-repair-failed-regression-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,source_head=plan['source_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'],full201=dict(passed=True,complete_cost=cost(ROOT/'.runs/full-integration-201-time.log')),build=dict(complete_cost=cost(ROOT/'.runs/prepare-runtime051-001-time.log')),preparation=dict(complete_cost=cost(ROOT/'.runs/freeze-runtime051-review-regression-001-time.log')),single_fresh_exposed_IR_Improve=dict(delivered=False,attempt_qualified=False,complete_cost=cost(ROOT/'.runs/runtime051-ir-review-regression-001-time.log'),outer_complete_wall_seconds=outer['complete_wall_seconds'],outer_complete_full_CPU_seconds=outer['complete_full_CPU_seconds'],route_receipt_sha256=p.sha(route_path),review_receipt_sha256=p.sha(review_path),candidate_sha256=route['candidate_sha256'],Native_counts=[0,0,42,0],trials=18,review_wall_seconds=review['wall_seconds'],review_CPU_seconds=review['total_cpu_seconds'],review_CLI_wall_seconds=read(producer.parent/'review.process.json')['wall_seconds'],failure='review copy exceeded30second wall/fullCPU cap',unranked_partial_metrics=route['metrics']),profile=facts,profile_complete_cost=cost(ROOT/'.runs/profile-runtime051-improve-review-001-time.log'),followup='Pure syntax memo retained but insufficient. Source follow-up removes redundant early selected7 private child replay while both mandatory import checks remain, prohibits direct pruning-parent imports, and consolidates final guard reconstruction with fresh late Context/tools/source/owner/code/settings/parent-sidecar and final all-root PRL. No acceptance cap increase/privatechild result cache. New full/runtime Native/GUI qualification required; no051 result promotion.',costs='All complete external events counted once; nested samples overlap. Targeted failed001/imported duplicate-test discovery and corrected002 retained. Research, authoring, AIreview and curation additional/partly unmetered, notzero.',frozen050_comparison_unchanged=True,not_a_comparison=True,actual_GUI=False,human_review=False,raw_scope='Only owned code/logs and factual metadata/hashes retained publicly. Foreign CAD/DSN/SES/plots/full findings and binaryprofiles remain on thisMac/outside010. No new restoration or disk-failure protection claim.',source_sha256={str(q.relative_to(ROOT)):p.sha(q) for q in [ROOT/'autorouter/strategy.py',ROOT/'autorouter/pipeline.py',ROOT/'tests/test_native7_parent_import_order.py',ROOT/'tests/test_native7_guard_reconstruction.py']},files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,delivered=False,project_complete=False)))
