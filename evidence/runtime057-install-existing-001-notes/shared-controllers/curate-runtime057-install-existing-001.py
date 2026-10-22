"""DRAFT ONLY: retain two completed057 fresh-root controls, never execute Native.

Identity/prerequisite port of056 curator; unchanged030 retain/tree and approved
report own_final/complete_cost. Refuse until both current actual slices finish.
No old056 execution/failure/scope narrative is current057 qualification.
"""
from pathlib import Path
import ast, datetime, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io, provenance as pv, sexpr as sx
from scripts import report_current_comparison as shared
assert p.sha(Path(shared.__file__))=='0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e'
notes=ROOT/'evidence/runtime057-install-existing-001-notes';target=ROOT/'evidence/runtime057-install-existing-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
HEAD='ac1a48c3b25b2217e0f8252e0e6da21905f144a4'
SOURCE_MANIFEST='9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e'
NEW_MANIFEST='b1d7066dff94e331f967afa89a4c0b3e2cfa10067324c3216996b31476898c51'
old=ROOT/'evidence/runtime057-native-milestone-001.json'
assert p.sha(old)=='37620250ac71559915a80873be8d9cfc36c4d65853fd337fa5537e0eac904eb9'
prior=f.read_json(old);assert prior['source_head']==HEAD and prior['runtime_manifest_sha256']==SOURCE_MANIFEST
index=ROOT/prior['files_index']['path']
assert p.sha(index)==prior['files_index']['sha256']
for row in f.read_json(index)['files']:refs.setdefault(row['sha256'],row['path'])
for row in f.read_json(index)['material']:refs.setdefault(row['sha256'],row['retained'])
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::retain','exec'),globals())
base=ROOT/'.runs/runtime057-install-existing-qualification-001';prepared=f.read_json(base/'preparation.json')
assert p.sha(base/'preparation.json')=='64a555603f104f670e53459d05c72f2a86385ff79223adeef6bb7340f32f1d9b'
runtime=Path(prepared['runtime']);source_runtime=Path(prepared['source_runtime'])
assert runtime==ROOT/'.runs/runtime057 fresh install 001' and source_runtime==ROOT/'.runs/runtime-directory-057/runtime'
assert prepared['source_head']==HEAD and prepared['source_manifest_sha256']==SOURCE_MANIFEST and prepared['runtime_manifest_sha256']==NEW_MANIFEST
assert prepared['installation_record_is_authoritative'] is False and prepared['doctor_ready'] is True and prepared['python_version']=='3.11.9'
for path,pin in prepared['prerequisite_sha256'].items():assert p.sha(Path(path))==pin
assert p.sha(source_runtime/pv.MANIFEST)==SOURCE_MANIFEST
assert p.sha(runtime/'.runs/install-existing-runtime-001.json')==prepared['installation_receipt_sha256']
old_manifest=f.read_json(source_runtime/pv.MANIFEST);manifest=f.read_json(runtime/pv.MANIFEST)
assert manifest==dict(old_manifest,root=str(runtime)) and p.sha(runtime/pv.MANIFEST)==prepared['runtime_manifest_sha256']==NEW_MANIFEST
implementation={n:v for n,v in manifest['immutable_files_sha256'].items() if n.startswith('autorouter/')}
assert pv._runtime_identity(runtime,implementation)==prepared['tools']['source_provenance']
assert [r['case'] for r in prepared['protocols']]==['ordinary-alias2Cu','via-high-partial2Cu']
rows=[]
for row in prepared['protocols']:
    label=row['case'];protocol=Path(row['protocol']);assert p.sha(protocol)==row['protocol_sha256']
    plan=f.read_json(protocol);execution=f.read_json(protocol.parent/'execution.json');output=Path(plan['output'])
    assert protocol==base/label/'protocol.json' and plan['runtime']==str(runtime) and plan['source_head']==HEAD and plan['runtime_manifest_sha256']==NEW_MANIFEST
    assert plan['tools']==prepared['tools'] and plan['budgets']==dict(route=90,export=90)
    assert output==runtime/'.runs'/(label+'-001')
    assert plan['settings']==dict(schema=1,scope='partial_completion',seconds=90,adapter='both',profile='standard',guidance='native',layers='source_all',scoring_preference=None if label=='ordinary-alias2Cu' else 'via_high')
    assert execution['controls_passed'] is True and execution['workflow_delivered'] is True and execution['error'] is None
    assert execution['protocol_sha256']==row['protocol_sha256'] and execution['protected_count']==4 and execution['Native_counts']==[0,0,0,0]
    assert max(execution['complete_wall_seconds'],execution['complete_full_CPU_seconds'])<=240
    process=execution['process'];assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False
    child_path=Path(execution['child_receipt']);assert child_path==output/'result.json' and p.sha(child_path)==execution['child_sha256']
    child=f.read_json(child_path);assert child['workflow_delivered'] is True and child['actual_GUI'] is False and child['human_review'] is False
    assert child['tools']==prepared['tools'] and child['settings']==plan['settings'] and child['source_hashes']==plan['source_hashes']
    assert io.inventory(Path(plan['source']).parent)==plan['source_hashes']
    workspace=Path(child['workspace']);assert workspace.parent==output
    route_path=workspace/'route/result.json';export_path=workspace/'export/export.json'
    route=f.read_json(route_path);exported=f.read_json(export_path)
    route_proof=shared.own_final(route_path,export=False,plan=plan,allowed=[output],accepted=True)
    export_proof=shared.own_final(export_path,export=True,plan=plan,allowed=[output],accepted=True)
    assert route['candidate_sha256']==exported['candidate_sha256']==child['candidate_sha256']
    assert route['scope']=='partial_completion' and route['engine_profile']=='standard' and route['adapter']=='both'
    assert route['scoring_variant']==plan['settings']['scoring_preference']
    original=sx.read(Path(plan['source']));protected=p.protected_for_record(route,original);assert len(protected)==4
    for result in (route,exported):
        candidate=Path(result['candidate']);p.verify_candidate_files(candidate,plan['source_hashes'],result['candidate_sha256'])
        tree_data=sx.read(candidate);assert p.immutable(tree_data)==p.immutable(original) and all(item in p.routes(tree_data) for item in protected)
    assert [r['stage'] for r in child['processes']]==['preview','route','review','choice','export','verify_export']
    for stage in child['processes']:assert stage['process']['exit_code']==0 and stage['process']['cancel_requested'] is False and stage['process']['log_truncated'] is False
    suffix='ordinary' if label=='ordinary-alias2Cu' else 'high'
    rows.append(dict(case=label,workflow_delivered=True,actual_GUI=False,scoring_preference=route['scoring_variant'],Native_counts=[0,0,0,0],protected_count=4,candidate_sha256=route['candidate_sha256'],own_final=dict(route=route_proof,export=export_proof),complete_external_cost=shared.complete_cost(ROOT/'.runs'/('runtime057-install-existing-'+suffix+'-001-time.log'))))
    tree(output,Path('cases')/label)
tree(base,Path('qualification'))
for path,name in ((runtime/pv.MANIFEST,'runtime-distribution.json'),(runtime/'.runs/install-existing-runtime-001.json','install-existing-runtime-001.json'),(runtime/'.venv/pyvenv.cfg','pyvenv.cfg')):
    retain(path,Path('installation')/name)
for name in ('prepare-runtime057-fresh-install-001.py','prepare-runtime057-fresh-install-001.log','prepare-runtime057-fresh-install-001-time.log',
    'runtime057-install-existing-copy-001.log','runtime057-install-existing-copy-001-time.log','runtime057-install-existing-venv-001.log','runtime057-install-existing-venv-001-time.log',
    'runtime057-install-existing-ordinary-001.log','runtime057-install-existing-ordinary-001-time.log','runtime057-install-existing-ordinary-command-001.txt',
    'runtime057-install-existing-high-001.log','runtime057-install-existing-high-001-time.log','runtime057-install-existing-high-command-001.txt'):
    retain(ROOT/'.runs'/name,Path('administration')/name)
for path in (ROOT/'scripts/prepare_runtime.py',ROOT/'scripts/qualify_runtime_workflow.py',ROOT/'.runs/enclose-runtime044-workflow-001.py',Path(__file__)):
    retain(path,Path('shared-controllers')/path.name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='runtime057-fresh-root-two-Native-CLI-private-environment-slices-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    project_complete=False,accepted=False,actual_GUI=False,human_review=False,workflow_CLI=True,workflow_delivered=True,
    source_head=prepared['source_head'],runtime=str(runtime),runtime_manifest_sha256=prepared['runtime_manifest_sha256'],
    original_runtime_manifest_sha256=prepared['source_manifest_sha256'],immutable_files=54,immutable_map_build_lock_version_unchanged=True,
    installation_record_is_authoritative=False,private_environment=prepared['private_environment'],rows=rows,
    copy_cost=shared.complete_cost(ROOT/'.runs/runtime057-install-existing-copy-001-time.log'),venv_cost=shared.complete_cost(ROOT/'.runs/runtime057-install-existing-venv-001-time.log'),preparation_query_doctor_cost=shared.complete_cost(ROOT/'.runs/prepare-runtime057-fresh-install-001-time.log'),
    scope='Two actual six-stage installed CLI slices at a new root containing spaces, private HOME/TMP/minimalPATH, exact original54-file population/build/source/engine. Source/protected4/Native/fullSCH/Default/fieldPRL/own-candidate checks remain mandatory. SameMac/account/existing3.11.9base/external dependencies; not all-combination transfer, GUI/cleanOS/account/relocation/standalone/Windows/quality/human/electrical or release qualification.',
    execution_bounds='Original90s route/export allocations; each shared enclosure retains240s wall/fullCPU acceptance and255s runner bound. No cap increase or aggregate future quota.',
    accounting='Complete external exits retained once; nested samples overlap. Copy/venv/query/doctor/curation and prior qualification/comparison/authoring/AIreview additional, unmetered costs unknown notzero.',
    rights='Owned generated source/projects/candidates/reports and project code only, reused by hash where already retained. No foreign CAD, tools/JAR/venv binaries or private inputs published. New raw remains Mac-only/outside010; no new full restoration.',
    files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,cases=len(rows),workflow_delivered=True,actual_GUI=False)))
