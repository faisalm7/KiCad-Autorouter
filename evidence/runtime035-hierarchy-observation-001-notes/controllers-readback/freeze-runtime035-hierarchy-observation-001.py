"""PREPARED ONLY: freeze one existing-source, non-admitting hierarchy probe.

Run later with the exact035 interpreter after lead source review and serial
Native lane availability. Requires actual full178/install008/ordinary whole002,
partial001 and critical-invalid001 passes. GUI is an explicitly separate unmet
gate, not a technical dependency or a qualification supplied by this probe.
No Native or routing executes in this freezer; all readback/startup cost is
separate retained preparation work. Never overwrite a failed preparation.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import hashlib,importlib.util,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'.runs/runtime-directory-035/runtime'
HEAD='7edc7229ea905e6734bf6cec8ff926a92e6a8613'
MANIFEST='8f0c455d7db2beb64e23283081fe788cfc26ee4d49cd95c8fd152b8e45ccb677'
HELPER='qualify-runtime035-hierarchy-observation-001.py'
HELPER_SHA='ad4f7d25ea6b9f168fcbb153cfdb59197c51be3efb883e0b48b16c30266fbd04'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert Path(sys.executable).absolute()==RUNTIME/'.venv/bin/python' and Path(sys.prefix).resolve()==RUNTIME/'.venv' and sys.prefix!=sys.base_prefix
sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,review_export as ex,local_settings as local
assert p.c.ROOT==RUNTIME and p.c.NATIVE_VERSION=='10.0.7' and sha(RUNTIME/'runtime-distribution.json')==MANIFEST
tools=p.tool_manifest();assert tools['git_head']==HEAD and tools['source_provenance']['manifest_sha256']==MANIFEST
original=ROOT/'.runs'/HELPER;child=RUNTIME/'.runs'/HELPER
base=ROOT/'.runs/runtime035-hierarchy-observation-001'
output=RUNTIME/'.runs/native7-comparison-control-runtime035-hierarchy-001'
assert sha(original)==HELPER_SHA and not child.exists() and not base.exists() and not output.exists()
assert shutil.disk_usage(ROOT).free>2*1024**3
pins={};packets=[];pairs=[]
def pinned(path):
    path=Path(path);assert path.is_absolute() and path.resolve(strict=True)==path and path.is_relative_to(ROOT)
    pins[str(path)]=sha(path);return f.read_json(path)
def completed(process):
    assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False

full=pinned(ROOT/'.runs/full-integration-178/execution.json');assert full['passed'] is True and full['sources_unchanged'] is True
fullplan=pinned(ROOT/'.runs/full-integration-178/protocol.json')
assert all(fullplan['source_sha256'][name]==value for name,value in tools['implementation_sha256'].items())
installed=pinned(ROOT/'.runs/install-distribution-native-008/execution.json');assert installed['passed'] is True and installed['source_unchanged'] is True
installplan_path=ROOT/'.runs/install-distribution-native-008/protocol.json';installplan=pinned(installplan_path)
assert installed['protocol_sha256']==sha(installplan_path) and installed['child_receipt']==str(ROOT/'.runs/runtime-directory-035/result.json')
installed_child=pinned(Path(installed['child_receipt']))
assert sha(Path(installed['child_receipt']))==installed['child_receipt_sha256'] and installed_child['passed'] is True and installed_child['git_head']==HEAD and installed_child['native_version']=='10.0.7'
positives=[]
for label,attempt,counts in (('whole4Cu','002',[0,0,6,0]),('partial2Cu','001',[0,0,0,0])):
    folder=ROOT/'.runs'/('runtime035-ordinary-'+label+'-'+attempt)
    caller=pinned(folder/'protocol.json');execution=pinned(folder/'execution.json')
    assert caller['runtime']==str(RUNTIME) and caller['source_head']==HEAD and caller['runtime_manifest_sha256']==MANIFEST
    assert execution['controls_passed'] is True and execution['workflow_delivered'] is True and execution['error'] is None
    assert execution['protocol_sha256']==sha(folder/'protocol.json');completed(execution['process'])
    result=pinned(Path(execution['child_receipt']));assert sha(execution['child_receipt'])==execution['child_sha256']
    assert result['status']=='completed' and result['workflow_delivered'] is True and result['tools']==tools and result['settings']==caller['settings']
    workspace=Path(result['workspace']);assert workspace.resolve()==workspace and workspace.parent==Path(caller['output']) and workspace.name.startswith('autorouter-gui-')
    route=workspace/'route/result.json';export=workspace/'export/export.json';r=pinned(route);e=pinned(export)
    assert r['source']==caller['source'] and r['source_hashes']==caller['source_hashes'] and p.tree_hash(Path(caller['source']).parent)==caller['source_hashes']
    assert r['tools']==e['tools']==tools and r['accepted'] is True and e['export_accepted'] is True and e['original_geometry_and_routing_unchanged'] is True
    assert [r['native'][key] for key in ('opens','blocking','warnings','exclusions')]==[e['native'][key] for key in ('opens','blocking','warnings','exclusions')]==counts
    with p.validation_readback_session():assert p.check_result(route)['current'] is True and ex.check_export(export)['current'] is True
    packets.extend(((route.parent,r),(workspace/'export/validation',e)))
    preview=f.read_json(workspace/'review/review.json')['preview'];plot=workspace/'review/plot-work'
    for step in preview['steps']:
        process=f.process_check(plot,preview,step['name'],step['argv']);pairs.append((plot,f.read_json(plot/(step['name']+'-input-binding.json')),process))
    positives.append(dict(protocol=str(folder/'protocol.json'),execution=str(folder/'execution.json'),result=execution['child_receipt'],route=str(route),export=str(export),source=caller['source'],source_hashes=caller['source_hashes']))

invalidpath=ROOT/'.runs/runtime035-ordinary-native-invalid-001/protocol.json';invalidplan=pinned(invalidpath)
assert sha(invalidpath)=='dabdf57c288ca987d79aa6572dfc580e8ee28b4e62daf54ec8661c8a1bb6058b'
invalid=pinned(invalidpath.parent/'enclosure/result.json');completed(invalid['process'])
assert invalid['passed'] is True and invalid['status']=='completed' and invalid['protocol_sha256']==sha(invalidpath)
assert invalidplan['runtime']==str(RUNTIME) and invalidplan['source_head']==HEAD and invalidplan['runtime_manifest_sha256']==MANIFEST
invalidchild=pinned(Path(invalid['child_receipt']))
assert invalid['child_sha256']==sha(invalid['child_receipt'])=='a6a00e7b4d83bdefa0ea7e663fb0c5f469ce08a6ac01e5f7e5c73b0d910ac050'
assert invalidchild['control_passed'] is True and invalidchild['status']=='completed' and invalidchild['accepted'] is False and invalidchild['tools']==tools
assert len(invalidchild['cases'])==2 and all(case['control_observed'] is True for case in invalidchild['cases'])

# Import only the exact reviewed administration file's definitions; its main
# execution branch is not run. Runtime imports precede external inventory code.
spec=importlib.util.spec_from_file_location('_prepared_hierarchy_observation',original)
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
expected,rights=helper.source_contract();source=helper.SOURCE;source_hashes={name:item['sha256'] for name,item in expected['files'].items()}
closure=helper.closure(source.parent)
for path,pin in helper.FIXED.items():pins[str(ROOT/path)]=pin
assert p.tree_hash(source.parent)==source_hashes and p.tool_manifest()==tools and sha(original)==HELPER_SHA
for path,pin in pins.items():assert sha(path)==pin
for item in positives:assert p.tree_hash(Path(item['source']).parent)==item['source_hashes']
assert sha(RUNTIME/'runtime-distribution.json')==MANIFEST and shutil.disk_usage(ROOT).free>2*1024**3
plan=dict(schema=1,kind=helper.KIND,runtime=str(RUNTIME),source_head=HEAD,runtime_manifest_sha256=MANIFEST,tools=tools,
    controller=str(child),controller_sha256=HELPER_SHA,controller_args=[],pass_key='control_passed',
    enclosure_sha256=helper.FIXED['.runs/enclose-native7-independent-control-004.py'],output=str(output),whole_wall_full_cpu_seconds=180,
    source=str(source),source_hashes=source_hashes,source_inventory=expected,source_rights=rights,source_closure=closure,
    observation_worker_sha256=hashlib.sha256(helper.WORKER.encode()).hexdigest(),prerequisite_files=pins,ordinary_positive_prerequisites=positives,
    limits=dict(native_worker_wall_seconds=30,child_wall_full_CPU_seconds=178,publication_reserve_seconds=15,max_native_worker_log_bytes=2000000,max_worker_RSS_bytes=4*1024**3,max_worker_scratch_bytes=512*1024**2),
    accepted=False,comparison_eligible=False,support_admitted=False,production_admitted=False,actual_GUI=False,
    GUI_gate='Separate actual035 GUI qualification remains unmet unless its own future evidence establishes it; this diagnostic neither depends on nor supplies it.',
    prerequisite_failure_scope='Critical-invalid first outer invocation omitted --protocol-sha256 and failed argparse before Native; separately retained001 logs, corrected invocation002 supplies the actual passing prerequisite. No artifact overwritten or first-attempt claim.',
    preparation=dict(freezer_sha256=sha(Path(__file__)),wall_seconds_before_publication=time.monotonic()-START,full_CPU_seconds_before_publication=cpu()-CPU0,scope='Read-only metadata/central qualification prerequisite readbacks only; no Native. Lead complete external freeze timing is additional.'),
    scope='One exposed licensed mixer hierarchy Native observability diagnostic, repeatedCH1–4. No engine/source writer, ordinary hierarchy guard change, routing acceptance, class-support admission, new population or quality gain. Raw unknowns drive revise/defer only.')
# Existing shared final flags follow all tool/source/hash callbacks. Freeze
# publication/copy below touches only fresh administration paths, not inputs.
local.check_final_events(packets,p.c.CLI,pairs=pairs)
base.mkdir()
with child.open('xb') as stream:stream.write(original.read_bytes())
assert sha(child)==HELPER_SHA
path=base/'protocol.json'
with path.open('x') as stream:json.dump(plan,stream,sort_keys=True,indent=2);stream.write('\n')
print(json.dumps(dict(protocol=str(path),protocol_sha256=sha(path),output=str(output),Native_executed=False,
    run_after_review=[str(RUNTIME/'.venv/bin/python'),'-B',str(ROOT/'.runs/enclose-native7-independent-control-004.py'),'--protocol',str(path),'--protocol-sha256',sha(path)])))
