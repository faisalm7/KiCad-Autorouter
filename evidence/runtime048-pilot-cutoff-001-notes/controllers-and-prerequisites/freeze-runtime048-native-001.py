"""Prospective finite product regressions; reuse the six-stage driver/encloser.
No Native result is installed by this preparation. Every failure is retained.
"""
from pathlib import Path
import os,json,sys,shutil,copy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
from autorouter.runner import run
H='e49a8d7c5f1423c9a82241e5ab58592cd5f119ac';runtime=R/'.runs/runtime-directory-048/runtime'
prepared=f.read_json(runtime.parent/'preparation.json');assert prepared['prepared'] and prepared['source_head']==H
M=prepared['manifest_sha256'];assert p.sha(runtime/'runtime-distribution.json')==M and shutil.disk_usage(R).free>4*1024**3
full=f.read_json(R/'.runs/full-integration-197/execution.json');assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete']
out=R/'.runs/runtime048-native-qualification-001';out.mkdir(mode=0o700)
env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME') and not k.startswith('KICAD_')};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
for name,command in [('doctor',[str(runtime/'.venv/bin/python'),'-B','-m','autorouter','doctor']),('tools-defaults',[str(runtime/'.venv/bin/python'),'-B','-c','import json;from autorouter import pipeline as p,preferences as pref;print(json.dumps(dict(tools=p.tool_manifest(),defaults=dict(pref.DEFAULTS)),sort_keys=True))'])]:
 process=run([*f.SANDBOX,*command],cwd=runtime,env=env,log=out/(name+'.json'),timeout=30,max_log_bytes=512*1024,max_workdir_bytes=256*1024**2,max_group_rss_bytes=2*1024**3);p.save_json(out/(name+'-process.json'),process)
 assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated']
assert f.read_json(out/'doctor.json')['ready'];tools=f.read_json(out/'tools-defaults.json')['tools'];assert tools['git_head']==H and tools['source_provenance']['manifest_sha256']==M and tools['kicad']=='10.0.7'
old=f.read_json(R/'.runs/runtime043-native-regression-source-plan-001.json');sources={row['case']:row for row in old['cases']}
area=f.read_json(R/'.runs/native7-improve-rule-area-controls-001/prepared.json');pour=next(row for row in area['cases'] if row['case']=='pour-only')
selected=[('improve-fractional','improve',sources['fractional-owned']),('improve-floor2Cu','improve',sources['floor-2Cu']),('improve-pour-only','improve',dict(pour,settings=sources['fractional-owned']['settings'],expected_counts=None,expected_protected_count=1,budgets=dict(route=90,export=90))),('ordinary-alias2Cu','route',sources['alias2Cu']),('ordinary-whole4Cu','route',sources['whole4Cu']),('ordinary-hierarchy2Cu','route',sources['hierarchy-whole2Cu'])]
driver=R/'scripts/qualify_runtime_workflow.py';enclosure=R/'.runs/enclose-runtime044-workflow-001.py';rows=[]
for name,method,basis in selected:
 source=Path(basis['source']);assert pc.inventory(source.parent)==basis['source_hashes'];folder=out/name;folder.mkdir();settings=copy.deepcopy(basis['settings']);settings['profile']='tuned' if method=='improve' else 'standard'
 p.save_json(folder/'settings.json',settings);target=runtime/'.runs'/(name+'-001');assert not target.exists()
 plan=dict(basis,schema=1,kind='runtime048-six-stage-route-or-improve-CLI',case=name,method=method,runtime=str(runtime),runtime_manifest_sha256=M,source_head=H,output=str(target),tools=tools,settings=settings,settings_sha256=p.sha(folder/'settings.json'),driver_sha256=p.sha(driver),enclosure_sha256=p.sha(enclosure),scope='Fresh installed045 product regression. Equal unchanged source rules/protected/scope/fullSCH/current final Native required. Single Improve is optional postprocessing, not a broad routing-quality or GUI claim. Existing043 results are not transferred; all attempted outcomes retained.')
 if plan['expected_counts'] is None:plan.update(warning_policy='retain_all_native_findings',expected_exclusions=0)
 p.save_json(folder/'protocol.json',plan);rows.append(dict(case=name,method=method,protocol=str(folder/'protocol.json'),protocol_sha256=p.sha(folder/'protocol.json')))
p.save_json(out/'frozen.json',dict(schema=1,source_head=H,runtime_manifest_sha256=M,controller_sha256=p.sha(Path(__file__)),enclosure_sha256=p.sha(enclosure),driver_sha256=p.sha(driver),protocols=rows,executed=False,scope='Six sequential finite actual installed workflow qualifications; no automatic retries or policy changes. These owned/exposed controls are not independent or untouched comparison boards. Follow any demonstrated failure with labelled development correction and fresh new-build qualification.'))
print(json.dumps(dict(frozen=len(rows),doctor_ready=True,manifest_sha256=M)))
