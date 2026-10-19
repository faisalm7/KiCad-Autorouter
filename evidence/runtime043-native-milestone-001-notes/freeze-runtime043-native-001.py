"""Freeze finite new-runtime regression inputs; existing shared controller unchanged."""
from pathlib import Path
import os,json,sys,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
from autorouter.runner import run
runtime=R/'.runs/runtime-directory-043/runtime';M='6fdfe60bcbe6aecc2c950a6917b22d8e591f5ae3078eca5a52ae051a1aac5aa3';H='6ec7ad2344ed060d5e0971965ef05bd9de68925d'
assert p.sha(runtime/'runtime-distribution.json')==M and shutil.disk_usage(R).free>4*1024**3
out=R/'.runs/runtime043-native-qualification-001';assert not out.exists();out.mkdir(mode=0o700)
env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME') and not k.startswith('KICAD_')};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
commands=[('doctor',[str(runtime/'.venv/bin/python'),'-B','-m','autorouter','doctor']),('tools-defaults',[str(runtime/'.venv/bin/python'),'-B','-c','import json;from autorouter import pipeline as p,preferences as pref;print(json.dumps(dict(tools=p.tool_manifest(),defaults=dict(pref.DEFAULTS)),sort_keys=True))'])]
for name,command in commands:
 process=run([*f.SANDBOX,*command],cwd=runtime,env=env,log=out/(name+'.json'),timeout=30,max_log_bytes=512*1024,max_workdir_bytes=256*1024**2,max_group_rss_bytes=2*1024**3);p.save_json(out/(name+'-process.json'),process)
 assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated']
assert f.read_json(out/'doctor.json')['ready'] is True
tools=f.read_json(out/'tools-defaults.json')['tools'];assert tools['git_head']==H and tools['kicad']=='10.0.7' and tools['source_provenance']['manifest_sha256']==M
sourceplan=f.read_json(R/'.runs/runtime043-native-regression-source-plan-001.json');assert sourceplan['source_head']==H
driver=R/'scripts/qualify_runtime_workflow.py';enclosure=R/'.runs/enclose-runtime030-ordinary-workflow-002.py';assert p.sha(enclosure)=='69d87dee41f94fe9e479e505093914325ed653cbb0cd58c9545272afefc1d59c'
rows=[]
for row in sourceplan['cases']:
 source=Path(row['source']);assert pc.inventory(source.parent)==row['source_hashes']
 folder=out/row['case'];folder.mkdir();p.save_json(folder/'settings.json',row['settings']);target=runtime/'.runs'/('ordinary-'+row['case']+'-001');assert not target.exists()
 plan=dict(row,schema=1,kind='runtime043-six-stage-ordinary-CLI',runtime=str(runtime),runtime_manifest_sha256=M,source_head=H,output=str(target),tools=tools,settings_sha256=p.sha(folder/'settings.json'),driver_sha256=p.sha(driver),enclosure_sha256=p.sha(enclosure),scope='Fresh043actualsixstageCLI after exact7fractionaledge correction. Standard/B1 default, exactoriginalrules/protected/scope/source/fullSCH/nativefinal and CPU wall allmandatory. Existing42results not transferred; originalcontrolfixtures reused withoutedits. Not GUI/comparative/human/physical qualification.')
 if row['expected_counts'] is None:plan.update(warning_policy='retain_all_native_findings',expected_exclusions=0)
 p.save_json(folder/'protocol.json',plan);rows.append({'case':row['case'],'protocol':str(folder/'protocol.json'),'protocol_sha256':p.sha(folder/'protocol.json')})
p.save_json(out/'frozen.json',{'schema':1,'kind':'prospective-runtime043-native-regression-eight-cases-v1','source_head':H,'runtime_manifest_sha256':M,'source_plan_sha256':p.sha(R/'.runs/runtime043-native-regression-source-plan-001.json'),'controller_sha256':p.sha(Path(__file__)),'protocols':rows,'executed':False,'scope':'Finite supervised sequential8cases; each has fresh result/ownNativeproof and completeouteraccounting; no automaticrepeat/tuning or historicalreportsubstitution.'});print(json.dumps({'frozen':len(rows),'doctor_ready':True,'manifest_sha256':M}))
