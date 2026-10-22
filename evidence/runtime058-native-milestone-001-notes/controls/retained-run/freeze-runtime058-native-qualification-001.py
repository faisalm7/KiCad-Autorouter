"""DRAFT: rebind the same eleven tasks after export stable-guard replay repair.

Lead executes only after full209 and actual runtime058 preparation succeed.
The future manifest is read from those receipts, never assumed here.
"""
from pathlib import Path
import copy,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,provenance as pv,gui
from autorouter.runner import run
from scripts import freeze_current_comparison as shared
HEAD='8f5e96b88dd22cd25919bb71ce47711612994efa'
runtime=ROOT/'.runs/runtime-directory-058/runtime';out=ROOT/'.runs/runtime058-native-qualification-001';manifest=runtime/'runtime-distribution.json'
assert pv.git_head(ROOT)==HEAD and not out.exists() and shutil.disk_usage(ROOT).free>4*1024**3
full=f.read_json(ROOT/'.runs/full-integration-209/execution.json')
assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete'] and not full['process']['log_truncated']
prepared=f.read_json(ROOT/'.runs/runtime-directory-058/preparation.json')
assert prepared['prepared'] and prepared['source_head']==HEAD and prepared['manifest_sha256']==p.sha(manifest)
prior_path=ROOT/'.runs/runtime057-native-qualification-001/frozen.json'
assert p.sha(prior_path)=='ffb15deb4ead2725095dab6e745ad119bba721c3cc5ac594115cbfc6544d1733'
prior=f.read_json(prior_path);assert len(prior['protocols'])==11
out.mkdir(mode=0o700);query,query_pins=shared.query_runtime(runtime,out);tools=query['tools']
assert tools['source_provenance']['git_head']==HEAD and tools['source_provenance']['manifest_sha256']==p.sha(manifest)
doctor=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B','-m','autorouter','doctor'],cwd=runtime,env=gui.child_environment(),log=out/'doctor.json',timeout=90,max_log_bytes=512*1024,max_group_rss_bytes=1024**3,max_workdir_bytes=128*1024**2)
p.save_json(out/'doctor-process.json',doctor)
assert doctor['status']=='success' and doctor['exit_code']==0 and doctor['cleanup_complete'] and not doctor['log_truncated'] and f.read_json(out/'doctor.json')['ready'] is True
rows=[];encloser=ROOT/'.runs/enclose-runtime044-workflow-001.py';driver=ROOT/'scripts/qualify_runtime_workflow.py'
for previous in prior['protocols']:
    old=Path(previous['protocol']);assert p.sha(old)==previous['protocol_sha256']
    plan=copy.deepcopy(f.read_json(old));assert plan['source_head']=='ac1a48c3b25b2217e0f8252e0e6da21905f144a4'
    assert p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
    name=plan['case'];folder=out/name;folder.mkdir();p.save_json(folder/'settings.json',plan['settings'])
    output=runtime/'.runs'/(name+'-001');assert not output.exists()
    plan.update(kind='runtime058-six-stage-route-or-improve-CLI',runtime=str(runtime),runtime_manifest_sha256=p.sha(manifest),source_head=HEAD,output=str(output),tools=tools,settings_sha256=p.sha(folder/'settings.json'),driver_sha256=p.sha(driver),enclosure_sha256=p.sha(encloser),source_protocol_sha256=previous['protocol_sha256'],qualification_role='Unchanged fixed task after general export stable-guard replay repair; no new routing policy, constraints or dimensions.',scope='Fresh installed058 Request/Workflow/CliJob six-stage Native/fullSCH/original/protected delivery after general export stable-guard replay repair. Same eleven source/settings/scope/profile/cost/budget controls, all warnings and ignored checks retained.900s complete batch wall/CPU; each shared enclosure acceptance240s, child runner255s, thin dispatcher270s maximum. No actual GUI/comparison/new family/electrical/Windows/cleanOS/release claim.')
    path=folder/'protocol.json';p.save_json(path,plan);rows.append(dict(case=name,method=plan['method'],protocol=str(path),protocol_sha256=p.sha(path)))
p.save_json(out/'frozen.json',dict(schema=1,source_head=HEAD,runtime_manifest_sha256=p.sha(manifest),controller_sha256=p.sha(Path(__file__)),enclosure_sha256=p.sha(encloser),driver_sha256=p.sha(driver),prior_frozen_sha256=p.sha(prior_path),protocols=rows,executed=False,whole_batch_seconds=900,scope='Eleven existing task definitions rebound and frozen before execution. Shared Native/workflow acceptance unchanged; stop on first failure and retain every unexecuted row. No result-selected tuning or old receipt transfer.'))
print(json.dumps(dict(runtime=str(runtime),manifest_sha256=p.sha(manifest),cases=[r['case'] for r in rows],executed=False)))
