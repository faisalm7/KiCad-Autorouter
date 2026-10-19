"""033 clean-environment retention pattern, current039 actual proof only."""
from pathlib import Path
import ast,datetime,hashlib,json,resource,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
notes=ROOT/'evidence/runtime039-clean-environment-001-notes';output=ROOT/'evidence/runtime039-clean-environment-001.json'
assert not notes.exists() and not output.exists()
refs={};files=[];material=[];total=0;dependencies=[]
for name in ['runtime039-native-floor-schema-milestone-001','gui-runtime039-079-hierarchy-high-budget-001',
    'gui-runtime039-079-recovery-no-repair-001','gui-runtime039-079-ordinary-controls-001','gui-runtime039-079-positive-reject-001',
    'runtime033-clean-environment-001']:
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
base=ROOT/'.runs/runtime039-clean-environment-001';plan=json.loads((base/'protocol.json').read_bytes());out=Path(plan['output']);runtime=Path(plan['runtime'])
outer=json.loads((base/'enclosure/result.json').read_bytes());result=json.loads((out/'result.json').read_bytes());workflow=json.loads((out/'workflow/result.json').read_bytes());workspace=Path(result['workspace'])
assert plan['source_head']==result['source_head']=='57542e996f2b6e7704acd408ac99f6c72e70adc5'
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']==result['runtime_manifest_sha256']=='ef7ea961238bf9d3e48e531dc3dcbd06700ac2fe5a270466e3d9365b81a6c728'
assert outer['passed'] is True and result['controls_passed'] is True and result['workflow_delivered'] is True and workflow['workflow_delivered'] is True
assert outer['protocol_sha256']==result['protocol_sha256']==p.sha(base/'protocol.json')
assert p.sha(out/'result.json')==outer['child_sha256'] and Path(outer['child_receipt'])==out/'result.json'
assert result['doctor']['ready'] is True and result['Native_counts']==[0,0,0,0] and result['all_four_original_routes_preserved'] is True
assert result['explicit_child_environment']==plan['child_environment']
assert plan['child_environment']['PATH']=='/usr/bin:/bin:/usr/sbin:/sbin'
assert plan['child_environment']['HOME']==str(out/'home') and plan['child_environment']['TMPDIR']==str(out/'tmp')+'/'
assert result['base_prefix']==plan['base_prefix']=='/Users/faisal/.pyenv/versions/3.11.9'
assert result['source']==workflow['source']==plan['source'] and result['source_hashes']==workflow['source_hashes']==plan['source_hashes']
assert all(p.sha(Path(plan['source']).parent/name)==sha for name,sha in plan['source_hashes'].items())
assert workspace.parent==out/'workflow' and workspace.name.startswith('autorouter-gui-')
assert [row['stage'] for row in workflow['processes']]==['preview','route','review','choice','export','verify_export']
for row in workflow['processes']:
    process=row['process'];assert process['exit_code']==0 and process['cancel_requested'] is False and process['log_truncated'] is False
for process in [outer['process']]+[row['process'] for row in result['processes']]:
    assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False
route=json.loads((workspace/'route/result.json').read_bytes());export=json.loads((workspace/'export/export.json').read_bytes())
assert route['accepted'] is True and route['invariants_unchanged'] is True and route['status']=='routing_accepted'
assert route['budget_seconds']==export['budget_seconds']==plan['settings']['seconds']==90
assert len(route['protected_route_import']['matches'])==plan['protected_routes']==4
assert result['route_receipt_sha256']==p.sha(workspace/'route/result.json') and result['export_receipt_sha256']==p.sha(workspace/'export/export.json')
assert export['export_accepted'] is True and export['applied'] is False and export['original_geometry_and_routing_unchanged'] is True
assert route['candidate_sha256']==export['candidate_sha256']==result['candidate_sha256']==p.sha(Path(export['candidate']))==p.sha(Path(route['candidate']))
assert export['inputs']['receipt_sha256']==p.sha(workspace/'route/result.json')
for record in [route,export]:
    assert all(record['native'][key]==0 for key in ['opens','blocking','warnings','exclusions'])
    assert record['schematic_parity']=='checked by final native DRC'
    assert all(s['cleanup_complete'] is True and s['log_truncated'] is False for s in record['steps'])
    assert '--schematic-parity' in [s for s in record['steps'] if s['name']=='final-drc'][-1]['argv']
assert p.sha(workspace/'route/final-drc.json')==route['native_report_sha256']
assert p.sha(workspace/'export/validation/final-drc.json')==export['native_report_sha256']
for key in ['controller','driver_path','enclosure_path','tools_defaults_path','query_process_path','query_preparation_path']:
    hashkey={'controller':'controller_sha256','driver_path':'driver_sha256','enclosure_path':'enclosure_sha256','tools_defaults_path':'tools_defaults_sha256','query_process_path':'query_process_sha256','query_preparation_path':'query_preparation_sha256'}[key]
    assert p.sha(Path(plan[key]))==plan[hashkey]

queue=[]
def add(path,name):
    path=Path(path);assert path.is_file() and ROOT in path.parents;queue.append((path,Path(name)))
def add_tree(path,name):
    for rel in io.inventory(path,max_bytes=64*1024**2):
        if set(Path(rel).parts)&{'kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:continue
        add(path/rel,Path(name)/rel)
add_tree(base,Path('outer-enclosure'))
# Retain the actual doctor/CLI/Native proof, not generated HOME/TMP caches/preferences.
for path in out.iterdir():
    if path.is_file():add(path,Path('case')/path.name)
for name in ['workflow','enclosure']:add_tree(out/name,Path('case')/name)
for name in ['qualify-runtime039-clean-environment-001.py','runtime039-clean-environment-preparation-001.json','run-runtime039-clean-environment-001.py',
    'runtime039-clean-environment-001-controller.log','runtime039-clean-environment-001-time.log']:
    add(ROOT/'.runs'/name,Path('controllers-preparation')/name)
for key in ['driver_path','enclosure_path','tools_defaults_path','query_process_path','query_preparation_path']:
    path=Path(plan[key]);add(path,Path('controllers-prerequisites')/path.name)
add(runtime/'.venv/pyvenv.cfg','dependencies/pyvenv.cfg');add(runtime/'runtime-distribution.json','runtime/runtime-distribution.json')
add(helper,'curation/retention-helper030.py');add(ROOT/'.runs/curate-runtime033-clean-environment-001.py','curation/retention-pattern033.py');add(Path(__file__),'curation/curate-runtime039-clean-environment-001.py')
known=set(refs);planned_bytes=0;planned_files=0
for path,name in queue:
    raw=io.read_bytes(path,4*1024**2);sha=hashlib.sha256(raw).hexdigest()
    if sha not in known:
        assert b'\0' not in raw;raw.decode('utf-8');known.add(sha);planned_bytes+=len(raw);planned_files+=1
assert planned_bytes<16*1024**2-8192 and planned_files<1999,(planned_bytes,planned_files)
for path,name in queue:retain(path,name)

scope='''This packet retains completed runtime039 doctor plus six real installed CLI stages under a fresh job-owned HOME/TMP and explicit minimal PATH, on the SAME Mac/account/fixed runtime and existing dependencies. It uses the existing isolatedKiCad10.0.7/Java and /Users/faisal/.pyenv/versions/3.11.9 base. This is a startup/configuration-isolation axis, NOT cleanOS/new-account/dependency acquisition, filesystem-read denial, relocation, standalone installation, GUI or a new routing family.

Own actual Route/export Native/refill/full-schematic/original-rules/invariant/four-protected-items proof and final candidate/report/source hashes are retained. Doctor ready, preview/route/review/choice/export/verify_export all returned0 without cancellation/truncation, and the existing background inspection target was checked. Runner/Native records separately show cleanup. CliJob rows do not independently certify descendants. The original source remains unchanged and the final candidate hash is bound by Route and fresh export. No KiCad GUI opening or post-editor changes occurred in this control.

The existing parent invoked the shared inner enclosure and existing workflow driver under network denial, bounded300whole wall/fullCPU, inner255watchdog/240wall/fullCPU,90route/90export,768MiB aggregate output and4GiB polled groupRSS. The outer runner's2MiB cwd guard covers its own enclosure directory; the parent’s768MiB aggregate limit covers the separate child output. Polling may overshoot and process accounting has the stored stated limitations. Final stored current readbacks/source/runtime/material and shared PRL metadata fences were part of that actual run, not rerun by curation.

Complete external36.27wall/33.71CPU includes doctor/workflow/conversion/routing/validation/delivery/final publication/readback and parent/child exits. Outer sampled36.185466wall/33.644541CPU and nested doctor/workflow/Native/stage samples are retained separately and must not be added again. Source authoring/preparation/independent review/curation costs are additional; unmetered costs are unknown, not zero. Preparatory assessment/protocol/source pins are retained; no failed invocation was omitted from these current inputs.

Only generated job-owned HOME/TMP/cache/preference payloads are omitted; exact explicit environment and bound limits are retained. No downloaded tools/apps/venvs or Python executable binaries are copied; pyvenv.cfg and executable hashes are retained. Source/code is project-owned with repository LICENSE and prior fixture/settings licence provenance via exact evidence references. No private board or unrelated browser data is published. New raw artifacts remain on this Mac outside older raw backups. No Native/engine/test/production reader was rerun by curation and no broad routing-quality/speed/platform/human/electrical/restoration/release-completion claim is made.
'''
scope_path=notes/'SCOPE.md';scope_path.open('x').write(scope);raw=scope_path.read_bytes();sha=hashlib.sha256(raw).hexdigest();total+=len(raw)
files.append(dict(path=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha));material.append(dict(original='authored:SCOPE.md',retained=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
assert total<16*1024**2 and len(files)<2000
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material));u=resource.getrusage(resource.RUSAGE_SELF)
summary=dict(schema=1,kind='runtime039-existing-dependency-minimal-environment-actual-six-stage-qualification-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,accepted=False,production_admitted=False,actual_GUI=False,human_review=False,passed=True,workflow_delivered=True,
    source_head=plan['source_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'],native_version='10.0.7',protocol_sha256=p.sha(base/'protocol.json'),child_receipt_sha256=p.sha(out/'result.json'),outer_receipt_sha256=p.sha(base/'enclosure/result.json'),
    complete_cost=cost(ROOT/'.runs/runtime039-clean-environment-001-time.log'),outer_complete_sample=dict(wall_seconds=outer['complete_wall_seconds'],CPU_seconds=outer['complete_full_CPU_seconds']),
    settings=plan['settings'],protected_original_items=4,Native_counts=[0,0,0,0],ignored_checks=route['native']['ignored_checks'],full_schematic_parity=route['schematic_parity'],original_design_and_source_unchanged=True,
    candidate_sha256=result['candidate_sha256'],route_receipt_sha256=p.sha(workspace/'route/result.json'),export_receipt_sha256=p.sha(workspace/'export/export.json'),workspace=str(workspace),source=plan['source'],source_hashes=plan['source_hashes'],doctor_ready=True,six_CLI_stages=workflow['processes'],background_inspection=workflow['background_inspection'],
    explicit_child_environment=plan['child_environment'],base_prefix=plan['base_prefix'],python_version=result['python_version'],limits=plan['limits'],
    same_product='Exact stable039/fixed path, no rebuild. Actual doctor plus six CLI stages and background inspection target; own fresh Native/fullSCH/original/protected4 Route and export.',
    boundaries='Same Mac/user/base Python and existing isolated KiCad/Java dependencies. Fresh HOME/TMP/minimal PATH; NOT cleanOS/account/dependency acquisition, relocation, standalone, GUI or new-family/effectiveness qualification.',
    accounting='Complete external costs authoritative; all outer/inner/Native/stage samples nest and are not additive. Preparation/authoring/review/curation additional; unmetered unknown, not zero.',
    source_rights='Project-owned generated fixture/code and prior settings/fixture licence provenance through exact retained references. No private input/tool/app binaries.',backup_scope='Essential bounded sanitized proof only; newer full raw remains Mac-only outside older raw backups, no full restoration/release completion.',dependencies=dependencies,
    retention=dict(helper=str(helper.relative_to(ROOT)),helper_sha256=p.sha(helper),pattern033_sha256=p.sha(ROOT/'.runs/curate-runtime033-clean-environment-001.py'),functions=['retain','tree','cost'],max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,new_payload_files=len(files),new_payload_bytes=total,material_rows=len(material),counts_exclude_index_summary=True,generated_HOME_TMP_cache_payloads_excluded=True),curation_sample=dict(wall_seconds=time.monotonic()-START,CPU_seconds=(u.ru_utime+u.ru_stime)-(CPU0.ru_utime+CPU0.ru_stime),complete_external_unknown=True),files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
p.save_json(output,summary)
for row in files:
    raw=io.read_bytes(ROOT/row['path'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),index_sha256=p.sha(index),new_files=len(files),new_bytes=total,material_rows=len(material),passed=True,project_complete=False)))
