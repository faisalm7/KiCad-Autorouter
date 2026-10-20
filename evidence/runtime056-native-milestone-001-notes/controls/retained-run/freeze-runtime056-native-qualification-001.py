"""Freeze four new search-cost controls and seven unchanged regressions; shared workflow only."""
from pathlib import Path
import copy,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,provenance as pv,gui
from autorouter.runner import run
from scripts import freeze_current_comparison as shared
HEAD='a03b5e8b6ae523d9f099cf211815900053629fe3'
runtime=ROOT/'.runs/runtime-directory-056/runtime';out=ROOT/'.runs/runtime056-native-qualification-001';manifest=runtime/'runtime-distribution.json'
assert pv.git_head(ROOT)==HEAD and not out.exists() and shutil.disk_usage(ROOT).free>4*1024**3
full=f.read_json(ROOT/'.runs/full-integration-206/execution.json');assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete'] and not full['process']['log_truncated']
prepared=f.read_json(ROOT/'.runs/runtime-directory-056/preparation.json');assert prepared['prepared'] and prepared['source_head']==HEAD and prepared['manifest_sha256']==p.sha(manifest)
out.mkdir(mode=0o700);query,query_pins=shared.query_runtime(runtime,out);tools=query['tools']
assert tools['source_provenance']['git_head']==HEAD and tools['source_provenance']['manifest_sha256']==p.sha(manifest)
doctor=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B','-m','autorouter','doctor'],cwd=runtime,env=gui.child_environment(),log=out/'doctor.json',timeout=90,max_log_bytes=512*1024,max_group_rss_bytes=1024**3,max_workdir_bytes=128*1024**2)
p.save_json(out/'doctor-process.json',doctor);assert doctor['status']=='success' and doctor['exit_code']==0 and doctor['cleanup_complete'] and not doctor['log_truncated'];assert f.read_json(out/'doctor.json')['ready'] is True
prior=f.read_json(ROOT/'.runs/runtime055-native-qualification-002/frozen.json');assert len(prior['protocols'])==7
plans={}
for row in prior['protocols']:
 old=Path(row['protocol']);assert p.sha(old)==row['protocol_sha256']
 plan=f.read_json(old);assert plan['source_head']=='38e193cdf94a814ee50baacb786e7f64214f02b8' and p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
 plans[plan['case']]=plan
new=[('via-high-whole2Cu','ordinary-npth2Cu','whole_board_unlocked_routing',1),('via-high-partial2Cu','ordinary-alias2Cu','partial_completion',4),('via-high-whole4Cu','ordinary-whole4Cu','whole_board_unlocked_routing',10),('via-high-partial4Cu','ordinary-whole4Cu','partial_completion',10)]
entries=[]
for name,old,scope,protected in new:
 plan=copy.deepcopy(plans[old]);plan['case']=name;plan['settings']['scope']=scope;plan['settings']['scoring_preference']='via_high';plan['expected_protected_count']=protected
 plan['qualification_role']='New explicit high search-cost support control; no routing-quality/completion comparison.'
 entries.append(plan)
for plan in plans.values():
 plan=copy.deepcopy(plan);plan['qualification_role']='Unchanged default-score current regression after shared admission/negative-reader signature changes.';entries.append(plan)
rows=[];encloser=ROOT/'.runs/enclose-runtime044-workflow-001.py';driver=ROOT/'scripts/qualify_runtime_workflow.py'
for plan in entries:
 name=plan['case'];folder=out/name;folder.mkdir();p.save_json(folder/'settings.json',plan['settings']);output=runtime/'.runs'/(name+'-001');assert not output.exists()
 plan.update(kind='runtime056-six-stage-route-or-improve-CLI',runtime=str(runtime),runtime_manifest_sha256=p.sha(manifest),source_head=HEAD,output=str(output),tools=tools,settings_sha256=p.sha(folder/'settings.json'),driver_sha256=p.sha(driver),enclosure_sha256=p.sha(encloser),scope='Fresh installed056 actual Request/Workflow/CliJob six-stage Native/fullSCH/original/protected delivery. Explicit high-cost controls plus seven unchanged default-score owned regressions. Exact original dimensions, warnings, ignored checks, budgets and constraints retained. 900s complete batch wall/CPU ceiling; each unchanged case240s, enclosure270s. No GUI, comparison, unrelated breadth, electrical, Windows, cleanOS or release claim.')
 path=folder/'protocol.json';p.save_json(path,plan);rows.append(dict(case=name,method=plan['method'],protocol=str(path),protocol_sha256=p.sha(path)))
p.save_json(out/'frozen.json',dict(schema=1,source_head=HEAD,runtime_manifest_sha256=p.sha(manifest),controller_sha256=p.sha(Path(__file__)),enclosure_sha256=p.sha(encloser),driver_sha256=p.sha(driver),protocols=rows,executed=False,whole_batch_seconds=900,scope='Four fixed via_high whole/partial2/4Cu controls first, then seven unchanged current regressions, frozen before any execution. Shared qualifier/enclosure unchanged. Stop on first failure; all unexecuted protocols remain visible. No result-selected policy/default/source changes or comparison claims.'))
print(json.dumps(dict(runtime=str(runtime),manifest_sha256=p.sha(manifest),frozen_cases=[r['case'] for r in rows],executed=False)))
