"""Freeze seven unchanged current regression tasks for changed syntax runtime."""
from pathlib import Path
import copy,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,provenance as pv,gui
from autorouter.runner import run
from scripts import freeze_current_comparison as shared
HEAD='38e193cdf94a814ee50baacb786e7f64214f02b8'
runtime=ROOT/'.runs/runtime-directory-055/runtime';out=ROOT/'.runs/runtime055-native-qualification-001';manifest=runtime/'runtime-distribution.json'
assert pv.git_head(ROOT)==HEAD and not out.exists() and shutil.disk_usage(ROOT).free>4*1024**3
full=f.read_json(ROOT/'.runs/full-integration-205/execution.json');assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete'] and not full['process']['log_truncated']
prepared=f.read_json(ROOT/'.runs/runtime-directory-055/preparation.json');assert prepared['prepared'] and prepared['source_head']==HEAD and prepared['manifest_sha256']==p.sha(manifest)
repair=f.read_json(ROOT/'.runs/runtime055-ir-review-regression-001/enclosure/result.json');assert repair['passed'] and repair['status']=='completed'
out.mkdir(mode=0o700);query,query_pins=shared.query_runtime(runtime,out);tools=query['tools']
assert tools['source_provenance']['git_head']==HEAD and tools['source_provenance']['manifest_sha256']==p.sha(manifest)
doctor=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B','-m','autorouter','doctor'],cwd=runtime,env=gui.child_environment(),log=out/'doctor.json',timeout=90,max_log_bytes=512*1024,max_group_rss_bytes=1024**3,max_workdir_bytes=128*1024**2)
p.save_json(out/'doctor-process.json',doctor);assert doctor['status']=='success' and doctor['exit_code']==0 and doctor['cleanup_complete'] and not doctor['log_truncated'];assert f.read_json(out/'doctor.json')['ready'] is True
prior=f.read_json(ROOT/'.runs/runtime050-native-qualification-001/frozen.json');assert len(prior['protocols'])==7
rows=[];encloser=ROOT/'.runs/enclose-runtime044-workflow-001.py';driver=ROOT/'scripts/qualify_runtime_workflow.py'
for row in prior['protocols']:
    old=Path(row['protocol']);assert p.sha(old)==row['protocol_sha256']
    plan=copy.deepcopy(f.read_json(old));assert plan['source_head']=='aa0072c6b3d8090de2603e5ecb42a95968fb873b' and p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
    name=plan['case'];folder=out/name;folder.mkdir();p.save_json(folder/'settings.json',plan['settings']);output=runtime/'.runs'/(name+'-001');assert not output.exists()
    plan.update(kind='runtime055-six-stage-route-or-improve-CLI',runtime=str(runtime),runtime_manifest_sha256=p.sha(manifest),source_head=HEAD,output=str(output),tools=tools,settings_sha256=p.sha(folder/'settings.json'),driver_sha256=p.sha(driver),enclosure_sha256=p.sha(encloser),scope='Fresh installed053 actual Request/Workflow/CliJob six-stage Native/fullSCH/original/protected delivery after one-complete-read review/choice lifecycle repair. Seven unchanged owned tasks; every warning and ignored check retained. No actual GUI, unrelated routing-quality/completion, Windows, cleanOS or release claim.')
    path=folder/'protocol.json';p.save_json(path,plan);rows.append(dict(case=name,method=plan['method'],protocol=str(path),protocol_sha256=p.sha(path)))
p.save_json(out/'frozen.json',dict(schema=1,source_head=HEAD,runtime_manifest_sha256=p.sha(manifest),controller_sha256=p.sha(Path(__file__)),enclosure_sha256=p.sha(encloser),driver_sha256=p.sha(driver),protocols=rows,executed=False,scope='All seven regression protocols frozen before dispatch. Existing six-stage qualifier and bounded enclosure unchanged. Every final retains own Native proof; sequential workers. Runtime050 results stay immutable.'))
print(json.dumps(dict(runtime=str(runtime),manifest_sha256=p.sha(manifest),frozen_cases=[r['case'] for r in rows],executed=False)))
