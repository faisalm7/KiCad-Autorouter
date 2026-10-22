"""DRAFT ONLY: retain two completed058 fresh-root controls, never execute Native.

Identity/prerequisite port of057 curator; unchanged030 retain/tree and approved
report own_final/complete_cost. Refuse until both current actual slices finish.
No old057 execution/failure/scope narrative is current058 qualification.
"""
from pathlib import Path
import argparse, ast, datetime, hashlib, json, os, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io, provenance as pv, sexpr as sx
from scripts import report_current_comparison as shared
# Original samples are never replaced by later retention reads.
pins={};inventories={};copies=[]
def capture(path,expected=None):
    path=Path(path);digest=hashlib.sha256(io.read_bytes(path,4*1024**2)).hexdigest()
    if expected is not None:assert digest==expected,str(path)
    if path in pins:assert digest==pins[path],str(path)
    else:pins[path]=digest
    return digest
def capture_tree(path):
    path=Path(path);value=io.inventory(path,max_bytes=64*1024**2,with_directories=True)
    if path in inventories:assert value==inventories[path],str(path)
    else:inventories[path]=value
    return value
def cost(path):
    capture(path);value=shared.complete_cost(path)
    assert value['time_log_sha256']==pins[Path(path)] and Path(value['source'])==Path(path)
    capture(path);return value
def live_fence():
    # Runtime identity may read callbacks/material; sample saved bytes afterward.
    assert pv._runtime_identity(source_runtime,implementation)==source_identity
    assert pv._runtime_identity(runtime,implementation)==runtime_identity
    for path,digest in pins.items():assert hashlib.sha256(io.read_bytes(path,4*1024**2)).hexdigest()==digest,str(path)
    for path,value in inventories.items():assert io.inventory(path,max_bytes=64*1024**2,with_directories=True)==value,str(path)
capture(Path(__file__))
capture(Path(shared.__file__),'0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e')
notes=ROOT/'evidence/runtime058-install-existing-001-notes';target=ROOT/'evidence/runtime058-install-existing-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(target)
refs={};files=[];material=[];total=0
HEAD='8f5e96b88dd22cd25919bb71ce47711612994efa'
SOURCE_MANIFEST='4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74'
ap=argparse.ArgumentParser(description=__doc__)
for flag in ('destination-manifest-sha256','installation-receipt-sha256','preparation-sha256',
        'native-milestone-sha256','ordinary-execution-sha256','high-execution-sha256'):
    ap.add_argument('--'+flag,required=True)
ap.add_argument('--native-milestone',type=Path,required=True)
args=ap.parse_args()
assert all(type(value) is str and pv._DIGEST.fullmatch(value) for name,value in vars(args).items() if name!='native_milestone')
NEW_MANIFEST=args.destination_manifest_sha256
old=pv.canonical(args.native_milestone)
assert old.parent==ROOT/'evidence' and old.name.startswith('runtime058-native-milestone-') and old.suffix=='.json'
capture(old,args.native_milestone_sha256)
prior=f.read_json(old);assert prior['source_head']==HEAD and prior['runtime_manifest_sha256']==SOURCE_MANIFEST
index=ROOT/prior['files_index']['path']
capture(index,prior['files_index']['sha256'])
for row in f.read_json(index)['files']:refs.setdefault(row['sha256'],row['path'])
for row in f.read_json(index)['material']:refs.setdefault(row['sha256'],row['retained'])
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
capture(helper,'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1')
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::retain','exec'),globals())
base=ROOT/'.runs/runtime058-install-existing-qualification-001'
capture(base/'preparation.json',args.preparation_sha256);prepared=f.read_json(base/'preparation.json')
capture_tree(base)
runtime=Path(prepared['runtime']);source_runtime=Path(prepared['source_runtime'])
assert runtime==ROOT/'.runs/runtime058 fresh install 001' and source_runtime==ROOT/'.runs/runtime-directory-058/runtime'
assert prepared['source_head']==HEAD and prepared['source_manifest_sha256']==SOURCE_MANIFEST and prepared['runtime_manifest_sha256']==NEW_MANIFEST
assert prepared['installation_record_is_authoritative'] is False and prepared['doctor_ready'] is True and prepared['python_version']=='3.11.9'
for path,pin in prepared['prerequisite_sha256'].items():capture(Path(path),pin)
capture(source_runtime/pv.MANIFEST,SOURCE_MANIFEST)
assert prepared['installation_receipt_sha256']==args.installation_receipt_sha256
capture(runtime/'.runs/install-existing-runtime-001.json',args.installation_receipt_sha256)
capture(runtime/pv.MANIFEST,NEW_MANIFEST)
old_manifest=f.read_json(source_runtime/pv.MANIFEST);manifest=f.read_json(runtime/pv.MANIFEST)
assert manifest==dict(old_manifest,root=str(runtime)) and p.sha(runtime/pv.MANIFEST)==prepared['runtime_manifest_sha256']==NEW_MANIFEST
implementation={n:v for n,v in manifest['immutable_files_sha256'].items() if n.startswith('autorouter/')}
runtime_identity=prepared['tools']['source_provenance']
source_identity=pv._runtime_identity(source_runtime,implementation)
assert pv._runtime_identity(runtime,implementation)==runtime_identity
assert [r['case'] for r in prepared['protocols']]==['ordinary-alias2Cu','via-high-partial2Cu']
rows=[]
for row in prepared['protocols']:
    label=row['case'];protocol=Path(row['protocol']);capture(protocol,row['protocol_sha256'])
    plan=f.read_json(protocol);execution_path=protocol.parent/'execution.json'
    capture(execution_path,args.ordinary_execution_sha256 if label=='ordinary-alias2Cu' else args.high_execution_sha256)
    execution=f.read_json(execution_path);output=Path(plan['output']);capture_tree(output)
    assert protocol==base/label/'protocol.json' and plan['runtime']==str(runtime) and plan['source_head']==HEAD and plan['runtime_manifest_sha256']==NEW_MANIFEST
    assert plan['tools']==prepared['tools'] and plan['budgets']==dict(route=90,export=90)
    assert output==runtime/'.runs'/(label+'-001')
    assert plan['settings']==dict(schema=1,scope='partial_completion',seconds=90,adapter='both',profile='standard',guidance='native',layers='source_all',scoring_preference=None if label=='ordinary-alias2Cu' else 'via_high')
    assert execution['controls_passed'] is True and execution['workflow_delivered'] is True and execution['error'] is None
    assert execution['protocol_sha256']==row['protocol_sha256'] and execution['protected_count']==4 and execution['Native_counts']==[0,0,0,0]
    assert max(execution['complete_wall_seconds'],execution['complete_full_CPU_seconds'])<=240
    process=execution['process'];assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False
    child_path=Path(execution['child_receipt']);assert child_path==output/'result.json';capture(child_path,execution['child_sha256'])
    child=f.read_json(child_path);assert child['workflow_delivered'] is True and child['actual_GUI'] is False and child['human_review'] is False
    assert child['tools']==prepared['tools'] and child['settings']==plan['settings'] and child['source_hashes']==plan['source_hashes']
    assert io.inventory(Path(plan['source']).parent)==plan['source_hashes']
    assert capture_tree(Path(plan['source']).parent)[0]==plan['source_hashes']
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
    rows.append(dict(case=label,workflow_delivered=True,actual_GUI=False,scoring_preference=route['scoring_variant'],Native_counts=[0,0,0,0],protected_count=4,candidate_sha256=route['candidate_sha256'],own_final=dict(route=route_proof,export=export_proof),complete_external_cost=cost(ROOT/'.runs'/('runtime058-install-existing-'+suffix+'-001-time.log'))))
    copies.append((tree,output,Path('cases')/label))
copies.append((tree,base,Path('qualification')))
for path,name in ((runtime/pv.MANIFEST,'runtime-distribution.json'),(runtime/'.runs/install-existing-runtime-001.json','install-existing-runtime-001.json'),(runtime/'.venv/pyvenv.cfg','pyvenv.cfg')):
    capture(path);copies.append((retain,path,Path('installation')/name))
for name in ('prepare-runtime058-fresh-install-001.py','prepare-runtime058-fresh-install-001.log','prepare-runtime058-fresh-install-001-time.log',
    'runtime058-install-existing-copy-001.log','runtime058-install-existing-copy-001-time.log','runtime058-install-existing-venv-001.log','runtime058-install-existing-venv-001-time.log',
    'runtime058-install-existing-ordinary-001.log','runtime058-install-existing-ordinary-001-time.log','runtime058-install-existing-ordinary-command-001.txt',
    'runtime058-install-existing-high-001.log','runtime058-install-existing-high-001-time.log','runtime058-install-existing-high-command-001.txt'):
    path=ROOT/'.runs'/name;capture(path);copies.append((retain,path,Path('administration')/name))
for path in (ROOT/'scripts/prepare_runtime.py',ROOT/'scripts/qualify_runtime_workflow.py',ROOT/'.runs/enclose-runtime044-workflow-001.py',Path(__file__)):
    capture(path);copies.append((retain,path,Path('shared-controllers')/path.name))
copy_cost=cost(ROOT/'.runs/runtime058-install-existing-copy-001-time.log')
venv_cost=cost(ROOT/'.runs/runtime058-install-existing-venv-001-time.log')
preparation_cost=cost(ROOT/'.runs/prepare-runtime058-fresh-install-001-time.log')
live_fence()  # All proof/cost/source samples exist before any public copy.
for operation,path,name in copies:operation(path,name)
live_fence()
for row in material:
    capture(ROOT/row['original'],row['sha256']);capture(ROOT/row['retained'],row['sha256'])
live_fence()
index_data=dict(schema=1,files=files,material=material)
index_pin=hashlib.sha256((json.dumps(index_data,indent=2)+'\n').encode()).hexdigest()
summary=dict(schema=1,kind='runtime058-fresh-root-two-Native-CLI-private-environment-slices-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    project_complete=False,accepted=False,actual_GUI=False,human_review=False,workflow_CLI=True,workflow_delivered=True,
    source_head=prepared['source_head'],runtime=str(runtime),runtime_manifest_sha256=prepared['runtime_manifest_sha256'],
    original_runtime_manifest_sha256=prepared['source_manifest_sha256'],immutable_files=54,immutable_map_build_lock_version_unchanged=True,
    installation_record_is_authoritative=False,private_environment=prepared['private_environment'],rows=rows,
    copy_cost=copy_cost,venv_cost=venv_cost,preparation_query_doctor_cost=preparation_cost,
    scope='Two actual six-stage installed CLI slices at a new root containing spaces, private HOME/TMP/minimalPATH, exact original54-file population/build/source/engine. Source/protected4/Native/fullSCH/Default/fieldPRL/own-candidate checks remain mandatory. SameMac/account/existing3.11.9base/external dependencies; not all-combination transfer, GUI/cleanOS/account/relocation/standalone/Windows/quality/human/electrical or release qualification.',
    execution_bounds='Original90s route/export allocations; each shared enclosure retains240s wall/fullCPU acceptance and255s runner bound. No cap increase or aggregate future quota.',
    accounting='Complete external exits retained once; nested samples overlap. Copy/venv/query/doctor/curation and prior qualification/comparison/authoring/AIreview additional, unmetered costs unknown notzero.',
    rights='Owned generated source/projects/candidates/reports and project code only, reused by hash where already retained. No foreign CAD, tools/JAR/venv binaries or private inputs published. New raw remains Mac-only/outside010; no new full restoration.',
    files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=index_pin))
summary_pin=hashlib.sha256((json.dumps(summary,indent=2)+'\n').encode()).hexdigest()
live_fence();p.save_json(notes/'files.json',index_data);capture(notes/'files.json',index_pin);live_fence()
live_fence();p.save_json(target,summary);capture(target,summary_pin);live_fence()
print(json.dumps(dict(files=len(files),bytes=total,cases=len(rows),workflow_delivered=True,actual_GUI=False)))
