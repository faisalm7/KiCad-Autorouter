"""Preserve one actual pre-engine Sonde interchange refusal; no execution replay."""
from pathlib import Path
import ast,datetime,hashlib,json,resource,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
notes=ROOT/'evidence/runtime039-sonde-layer-refusal-001-notes';output=ROOT/'evidence/runtime039-sonde-layer-refusal-001.json'
assert not notes.exists() and not output.exists()
refs={};files=[];material=[];total=0;dependencies=[]
for name in ['runtime039-native-floor-schema-milestone-001','runtime039-clean-environment-001','gui-runtime039-079-hierarchy-high-budget-001']:
    path=ROOT/'evidence'/(name+'.json');record=json.loads(path.read_bytes());index=record['files_index']
    assert p.sha(ROOT/index['path'])==index['sha256'];data=json.loads((ROOT/index['path']).read_bytes())
    for row in data.get('files',[]):refs.setdefault(row['sha256'],row['path'])
    for row in data.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
    dependencies.append(dict(path=str(path.relative_to(ROOT)),sha256=p.sha(path),files_index=index))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
functions=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree','cost')]
assert [n.name for n in functions]==['retain','tree','cost']
exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'),globals())
base=ROOT/'.runs/runtime039-ordinary-sonde-whole-001';plan=json.loads((base/'protocol.json').read_bytes());out=Path(plan['output']);runtime=Path(plan['runtime'])
execution=json.loads((base/'execution.json').read_bytes());result=json.loads((out/'result.json').read_bytes());workspace=Path(result['workspace'])
route=json.loads((workspace/'route/result.json').read_bytes())
assert workspace==out/'autorouter-gui-13845a29f67d43f1b020ee7c58e501cd'
assert plan['source_head']=='57542e996f2b6e7704acd408ac99f6c72e70adc5'
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']=='ef7ea961238bf9d3e48e531dc3dcbd06700ac2fe5a270466e3d9365b81a6c728'
assert plan['source']==route['source']==result['source']
assert plan['source_hashes']==route['source_hashes']==result['source_hashes']
assert all(p.sha(Path(plan['source']).parent/name)==sha for name,sha in plan['source_hashes'].items())
assert len(plan['source_hashes'])==16 and sum((Path(plan['source']).parent/name).stat().st_size for name in plan['source_hashes'])==plan['source_bytes']
assert execution['controls_passed'] is False and execution['workflow_delivered'] is False
assert execution['child_sha256']==p.sha(out/'result.json') and execution['protocol_sha256']==p.sha(base/'protocol.json')
assert result['workflow_delivered'] is False and result['accepted'] is False
assert route['status']=='rejected' and route['accepted'] is False
assert route['reason']=='ValueError: unqualified copper layer type or alias'
assert route['budget_seconds']==plan['settings']['seconds']==90 and plan['budgets']==dict(route=90,export=90)
assert result['route_receipt_sha256']==p.sha(workspace/'route/result.json')
assert route.get('candidate_sha256') is None and result['native'] is None
assert [s['name'] for s in route['steps']]==['source-drc','export']
assert route['steps'][0]['status']=='nonzero_exit' and route['steps'][0]['exit_code']==5
assert route['steps'][1]['status']=='success' and route['steps'][1]['exit_code']==0
assert all(s['cleanup_complete'] is True and s['log_truncated'] is False for s in route['steps'])
assert [row['stage'] for row in result['processes']]==['preview','route']
assert [row['process']['exit_code'] for row in result['processes']]==[0,2]
assert all(row['process']['cancel_requested'] is False and row['process']['log_truncated'] is False for row in result['processes'])
assert not any((workspace/name).exists() for name in ['review','choice','export'])
assert [route['source_drc'][key] for key in ['opens','blocking','warnings','exclusions']]==[0,0,1,0]
assert len(route['source_drc']['findings'])==1 and route['source_drc']['findings'][0]['type']=='lib_footprint_mismatch'
assert all('--schematic-parity' not in s['argv'] for s in route['steps'])
assert p.sha(workspace/'route/native.dsn')==route['native_dsn_sha256']
assert execution['process']['cleanup_complete'] is True and execution['process']['log_truncated'] is False
assert p.sha(ROOT/'.runs/enclose-runtime030-ordinary-workflow-002.py')==plan['enclosure_sha256']
assert p.sha(ROOT/'scripts/qualify_runtime_workflow.py')==plan['driver_sha256']
for notice in plan['rights']['notices']:assert p.sha(ROOT/notice['path'])==notice['sha256']
queue=[]
def add(path,name):
    path=Path(path);assert path.is_file() and ROOT in path.parents;queue.append((path,Path(name)))
def add_tree(path,name):
    for rel in io.inventory(path,max_bytes=64*1024**2):
        if set(Path(rel).parts)&{'kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:continue
        add(path/rel,Path(name)/rel)
add_tree(base,Path('attempt/enclosure-and-protocol'));add_tree(out,Path('attempt/workflow'))
for name in plan['source_hashes']:add(Path(plan['source']).parent/name,Path('original-source')/name)
for name in ['runtime039-ordinary-sonde-whole-001-controller.log','runtime039-ordinary-sonde-whole-001-time.log','enclose-runtime030-ordinary-workflow-002.py']:
    add(ROOT/'.runs'/name,Path('controllers-logs')/name)
add(ROOT/'scripts/qualify_runtime_workflow.py','controllers-logs/qualify_runtime_workflow.py');add(runtime/'runtime-distribution.json','runtime/runtime-distribution.json')
add(helper,'curation/retention-helper030.py');add(Path(__file__),'curation/curate-runtime039-sonde-layer-refusal-001.py')
known=set(refs);planned_bytes=0;planned_files=0
for path,name in queue:
    raw=io.read_bytes(path,4*1024**2);sha=hashlib.sha256(raw).hexdigest()
    if sha not in known:
        assert b'\0' not in raw;raw.decode('utf-8');known.add(sha);planned_bytes+=len(raw);planned_files+=1
assert planned_bytes<16*1024**2-8192 and planned_files<1999,(planned_bytes,planned_files)
for path,name in queue:retain(path,name)
scope='''One frozen current039 normal whole90/export90 attempt on existing exposed Sonde ran once. Static Preview returned0. Route CLI returned2 and the wrapper/whole workflow failed; no accepted candidate, review, intent or export followed. The actual Native source DRC ran and reported0opens/0blocking/1warning/0exclusions (lib_footprint_mismatch), returning5 under exit-code-violations. The actual Native DSN/class export worker then succeeded0. A subsequent interchange capability guard refused "unqualified copper layer type or alias" before any engine/import/final-candidate validation. All worker logs/journals, Native outputs and wrapper AssertionError are preserved. This is a capability/interchange refusal, not a Native DRC routing failure, source-invalid classification, hidden exclusion, infeasibility finding or solved-board regression result.

The raw rejected Route initializes schematic_parity to "checked by final native DRC". That policy string was not fulfilled: there is no final-drc step and neither executed Native step used --schematic-parity. The packet makes NO final/full-schematic validation or candidate acceptance claim for this failed attempt. Source Native’s1warning without schematic checking differs from historical final26warnings; historical counts remain leads, never a current pass or prediction. Expected opens/repairable copper/source metadata and hard source conflicts are not conflated.

Original16file Sonde inventory and bytes remain unchanged. Exact source/project/schematic/library tables/footprints/notices and failed-job snapshots are retained or exact-content referenced. The source is KiCad/kicad-source-mirror commit69cafb907ebc09e7722a2a464b1d466fc2e3608d as frozen in protocol, CC-BY-SA-4.0, with original LICENSE.README attribution and full CC-BY-SA licence retained. Protocol geometry_payload_publicationfalse described its preparation-time action; this explicitly authorized proof curation now retains the necessary licensed Sonde text geometry with those notices. No new data acquisition or rights assumption is introduced.

The complete external failure cost is2.95wall/2.35CPU; outer2.895023wall/2.317625CPU, workflow/CLI/source-DRC/export samples are nested and must not be added twice. Research/authoring/preparation/independent diagnosis/curation costs are additional or unmetered/unknown, not zero. The historical current-runtime030 wrapper kind is a retained helper-schema label; actual039 source/runtime/manifest are explicit and bound. No protocol/result rewriting or tuning/rerun is performed.

No Native/engine/test/production reader was rerun by curation. Current prepared NUS input/output is NOT inspected/copied/published. No downloaded tools/apps/venvs, private boards or unrelated browser content are included. New raw work remains on this Mac outside older raw backups. This is exposed development support coverage only, not an independent family/holdout, fair comparative study, broad routing-quality/speed/electrical/GUI/Windows/cleanOS/relocation/restoration/formal-release claim. The original task remains uncompleted on this source.
'''
scope_path=notes/'SCOPE.md';scope_path.open('x').write(scope);raw=scope_path.read_bytes();sha=hashlib.sha256(raw).hexdigest();total+=len(raw)
files.append(dict(path=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha));material.append(dict(original='authored:SCOPE.md',retained=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
assert total<16*1024**2 and len(files)<2000
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material));u=resource.getrusage(resource.RUSAGE_SELF)
summary=dict(schema=1,kind='runtime039-sonde-pre-engine-layer-interchange-refusal',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,workflow_delivered=False,project_complete=False,actual_GUI=False,human_review=False,source_head=plan['source_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'],native_version='10.0.7',
    classification='Capability/interchange refusal after successful Native DSN export, before engine; not Native DRC routing failure or source-invalid classification.',
    original_source=plan['source'],source_hashes=plan['source_hashes'],source_files=16,source_bytes=plan['source_bytes'],source_unchanged_now=True,settings=plan['settings'],declared_budgets=plan['budgets'],protocol_sha256=p.sha(base/'protocol.json'),workflow_receipt_sha256=p.sha(out/'result.json'),route_receipt_sha256=p.sha(workspace/'route/result.json'),workspace=str(workspace),
    workflow=dict(status=result['status'],error=result['error'],controls_passed=False,preview_exit0=True,Route_exit2=True,stages=result['processes'],wrapper_error=execution['error']),
    actual_Native=dict(source_DRC=route['source_drc'],source_DRC_exit_code=5,export_worker_status='success',export_worker_exit_code=0,native_DSN_sha256=route['native_dsn_sha256'],workers=route['steps']),
    rejection=dict(status=route['status'],reason=route['reason'],engine_executed=False,import_executed=False,final_DRC_executed=False,accepted_candidate=False,review_choice_export_created=False),
    unfulfilled_failed_receipt_policy=dict(raw_schematic_parity=route['schematic_parity'],actual_full_schematic_check_executed=False,meaning='Initialization/policy metadata only on this failed receipt, not actual final Native/fullSCH proof.'),
    historical_counts_NOT_current_or_prediction=plan['historical_counts_NOT_acceptance_or_prediction'],historical_scope=plan['historical_count_scope'],
    complete_cost=cost(ROOT/'.runs/runtime039-ordinary-sonde-whole-001-time.log'),outer_complete_sample=dict(wall_seconds=execution['complete_wall_seconds'],CPU_seconds=execution['complete_full_CPU_seconds']),route_nested_sample=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']),accounting='All nested Native/CLI/outer samples are included by complete external exit; do not add twice. Preparation/research/authoring/diagnosis/curation additional; unmetered unknown, not zero.',
    rights=plan['rights'],rights_scope='Necessary licensed Sonde text payload and exact CC-BY-SA/source notices retained under this task; frozen preparation metadata geometry-publicationfalse is historical. No NUS payload inspected or copied.',
    limits='One actual exposed development support refusal only; no source-invalid/routing-failure/infeasibility/accepted Native/fullSCH candidate or general gain/speed/fair-comparison/GUI/electrical/platform/release claim.',dependencies=dependencies,
    retention=dict(helper=str(helper.relative_to(ROOT)),helper_sha256=p.sha(helper),functions=['retain','tree','cost'],max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,new_payload_files=len(files),new_payload_bytes=total,material_rows=len(material),counts_exclude_index_summary=True),curation_sample=dict(wall_seconds=time.monotonic()-START,CPU_seconds=(u.ru_utime+u.ru_stime)-(CPU0.ru_utime+CPU0.ru_stime),complete_external_unknown=True),files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
p.save_json(output,summary)
for row in files:
    raw=io.read_bytes(ROOT/row['path'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),index_sha256=p.sha(index),new_files=len(files),new_bytes=total,material_rows=len(material),accepted=False)))
