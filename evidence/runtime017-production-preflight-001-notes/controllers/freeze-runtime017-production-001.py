"""Freeze the reviewed0174Cu qualifier; reuse actual metadata, no Native/JVM work."""
from pathlib import Path
import hashlib,importlib.util,json,resource,sys,time
START=time.monotonic()
def cpu():return sum(row.ru_utime+row.ru_stime for row in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
BASE=ROOT/'.runs/runtime-directory-017';draft=BASE/'production-delivery-protocol-draft-001.json';plan=f.read_json(draft)
assert plan['status']=='draft-not-executable'
assert p.sha(draft)=='b4e8906da2522e797986700f7a10245b6ac1eaf8a93bf62b2866d52322d5d461'
outer=ROOT/'.runs/run-runtime017-production-001.py';child=ROOT/'.runs/qualify-runtime017-production-001.py'
assert p.sha(outer)==plan['outer_controller_sha256']=='c8474903c6cbfd66b09965474383be8193b4b1156574cd7facdbb3664719a72f'
assert p.sha(child)==plan['child_sha256']=='efbc44db006baff9606dfc4d0e73ee564a2db218f333490f3e3c228ae200b0d9'
spec=importlib.util.spec_from_file_location('reviewed017enclosure',outer);enclosure=importlib.util.module_from_spec(spec);spec.loader.exec_module(enclosure)
shared=enclosure.shared_helpers();assert shared.selected_tools(p.tool_manifest())==shared.selected_tools(plan['coordinator_tools'])
assert shared.coordinator_python_context()==plan['coordinator_python']
assert sys.version_info[:2]==(3,11)
full=f.read_json(ROOT/'.runs/full-integration-153/execution.json');assert full['process']['exit_code']==0 and full['process']['cleanup_complete'] is True
assert full['tools']['implementation_sha256']==p.tool_manifest()['implementation_sha256']
review=ROOT/'.runs/runtime017-production-source-review-001.json';reviewrow=f.read_json(review)
assert reviewrow.get('material_findings')==[] and reviewrow.get('Native_executed') is False
for path,digest in plan['prerequisite_sha256'].items():assert p.sha(Path(path))==digest,path
prior=f.read_json(ROOT/'.runs/runtime-directory-016/production-delivery-protocol-001.json')
assert plan['fixture_files']==prior['fixture_files'] and plan['fixture_sha256']==prior['fixture_sha256'] and plan['settings']==prior['settings']
for name,text in plan['fixture_files'].items():assert hashlib.sha256(text.encode()).hexdigest()==plan['fixture_sha256'][name]
runtime=Path(plan['runtime']);manifest=f.read_json(runtime/'runtime-distribution.json')
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']
for name,digest in manifest['build_source']['files_sha256'].items():assert p.sha(runtime/name)==digest,name
for path,digest in plan['runtime_tools']['files'].items():assert p.sha(Path(path))==digest,path
assert shared.python_file_context(runtime/'.venv/bin/python')=={key:plan['runtime_python'][key]for key in('path','resolved_path','sha256','bytes')}
plan['status']='frozen';plan['prerequisite_sha256'].update({str(review):p.sha(review),str(ROOT/'.runs/full-integration-153/execution.json'):p.sha(ROOT/'.runs/full-integration-153/execution.json')})
plan['source_review']=str(review);plan['preparation_costs']=dict(sample_wall_seconds=time.monotonic()-START,sample_full_cpu_seconds=cpu()-CPU0,Native_executed=False,JVM_executed=False,scope='Static freeze and exclusive child copy only; complete external preparation cost separately measured, authoring/review/control costs separate.')
target=runtime/'.runs'/plan['installed_child_name']
with target.open('xb')as stream:stream.write(child.read_bytes())
protocol=BASE/'production-delivery-protocol-frozen-001.json'
with protocol.open('x')as stream:json.dump(plan,stream,indent=2,allow_nan=False);stream.write('\n')
assert enclosure.frozen(protocol,p.sha(protocol),shared)==plan
print(json.dumps(dict(frozen=True,protocol=str(protocol),sha256=p.sha(protocol),Native_executed=False,JVM_executed=False)))
