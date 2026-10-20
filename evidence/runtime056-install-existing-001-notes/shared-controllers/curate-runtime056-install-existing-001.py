"""Retain owned fresh-root controls with shared retention and own-final readers."""
from pathlib import Path
import ast, datetime, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io, provenance as pv, sexpr as sx
from scripts import report_current_comparison as shared
assert p.sha(Path(shared.__file__))=='0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e'
notes=ROOT/'evidence/runtime056-install-existing-001-notes';target=ROOT/'evidence/runtime056-install-existing-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
old=ROOT/'evidence/runtime056-native-milestone-001.json';prior=f.read_json(old);index=ROOT/prior['files_index']['path']
assert p.sha(index)==prior['files_index']['sha256']
for row in f.read_json(index)['files']:refs.setdefault(row['sha256'],row['path'])
for row in f.read_json(index)['material']:refs.setdefault(row['sha256'],row['retained'])
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::retain','exec'),globals())
base=ROOT/'.runs/runtime056-install-existing-qualification-001';prepared=f.read_json(base/'preparation.json')
assert p.sha(base/'preparation.json')=='851c6b36a415c8c9ce4a38a44960a0f5f7c404237d69b898eb50dae7a833caa1'
runtime=Path(prepared['runtime']);source_runtime=Path(prepared['source_runtime'])
old_manifest=f.read_json(source_runtime/pv.MANIFEST);manifest=f.read_json(runtime/pv.MANIFEST)
assert manifest==dict(old_manifest,root=str(runtime)) and p.sha(runtime/pv.MANIFEST)==prepared['runtime_manifest_sha256']
implementation={n:v for n,v in manifest['immutable_files_sha256'].items() if n.startswith('autorouter/')}
assert pv._runtime_identity(runtime,implementation)==prepared['tools']['source_provenance']
assert [r['case'] for r in prepared['protocols']]==['ordinary-alias2Cu','via-high-partial2Cu']
rows=[]
for row in prepared['protocols']:
    label=row['case'];protocol=Path(row['protocol']);assert p.sha(protocol)==row['protocol_sha256']
    plan=f.read_json(protocol);execution=f.read_json(protocol.parent/'execution.json');output=Path(plan['output'])
    assert execution['controls_passed'] is True and execution['workflow_delivered'] is True and execution['error'] is None
    assert execution['protocol_sha256']==row['protocol_sha256'] and execution['protected_count']==4 and execution['Native_counts']==[0,0,0,0]
    process=execution['process'];assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False
    child_path=Path(execution['child_receipt']);assert p.sha(child_path)==execution['child_sha256']
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
    rows.append(dict(case=label,workflow_delivered=True,actual_GUI=False,scoring_preference=route['scoring_variant'],Native_counts=[0,0,0,0],protected_count=4,candidate_sha256=route['candidate_sha256'],own_final=dict(route=route_proof,export=export_proof),complete_external_cost=shared.complete_cost(ROOT/'.runs'/('runtime056-install-existing-'+suffix+'-001-time.log'))))
    tree(output,Path('cases')/label)
tree(base,Path('qualification'))
for path,name in ((runtime/pv.MANIFEST,'runtime-distribution.json'),(runtime/'.runs/install-existing-runtime-001.json','install-existing-runtime-001.json'),(runtime/'.venv/pyvenv.cfg','pyvenv.cfg')):
    retain(path,Path('installation')/name)
for name in ('prepare-runtime056-fresh-install-001.py','prepare-runtime056-fresh-install-001.log','prepare-runtime056-fresh-install-001-time.log',
    'runtime056-install-existing-copy-001.log','runtime056-install-existing-copy-001-time.log','runtime056-install-existing-venv-001.log','runtime056-install-existing-venv-001-time.log',
    'runtime056-install-existing-ordinary-001.log','runtime056-install-existing-ordinary-001-time.log','runtime056-install-existing-high-001.log','runtime056-install-existing-high-001-time.log'):
    retain(ROOT/'.runs'/name,Path('administration')/name)
for path in (ROOT/'scripts/prepare_runtime.py',ROOT/'scripts/qualify_runtime_workflow.py',ROOT/'.runs/enclose-runtime044-workflow-001.py',Path(__file__)):
    retain(path,Path('shared-controllers')/path.name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='runtime056-fresh-root-two-Native-CLI-private-environment-slices-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    project_complete=False,accepted=False,actual_GUI=False,human_review=False,workflow_CLI=True,workflow_delivered=True,
    source_head=prepared['source_head'],runtime=str(runtime),runtime_manifest_sha256=prepared['runtime_manifest_sha256'],
    original_runtime_manifest_sha256=prepared['source_manifest_sha256'],immutable_files=54,immutable_map_build_lock_version_unchanged=True,
    installation_record_is_authoritative=False,private_environment=prepared['private_environment'],rows=rows,
    copy_cost=shared.complete_cost(ROOT/'.runs/runtime056-install-existing-copy-001-time.log'),venv_cost=shared.complete_cost(ROOT/'.runs/runtime056-install-existing-venv-001-time.log'),preparation_query_doctor_cost=shared.complete_cost(ROOT/'.runs/prepare-runtime056-fresh-install-001-time.log'),
    scope='Two actual six-stage installed CLI slices at a new root containing spaces, private HOME/TMP/minimalPATH, exact original54-file population/build/source/engine. Source/protected4/Native/fullSCH/Default/fieldPRL/own-candidate checks remain mandatory. SameMac/account/existing3.11.9base/external dependencies; not all-combination transfer, GUI/cleanOS/account/relocation/standalone/Windows/quality/human/electrical or release qualification.',
    protocol_description_limit='Copied plans preserve historical11-case scope prose, including900batch/270outer text. Those phrases are not authority for this two-case execution. Actual unchanged shared encloser admits each case only<=240wall/fullCPU with255runner cap; original90route/export allocations unchanged. No900aggregate or270enclosure qualification is claimed.',
    accounting='Complete external exits retained once; nested samples overlap. Copy/venv/query/doctor/curation and prior qualification/comparison/authoring/AIreview additional, unmetered costs unknown notzero.',
    rights='Owned generated source/projects/candidates/reports and project code only, reused by hash where already retained. No foreign CAD, tools/JAR/venv binaries or private inputs published. New raw remains Mac-only/outside010; no new full restoration.',
    files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,cases=len(rows),workflow_delivered=True,actual_GUI=False)))
