"""Existing enclosure around one production controller in the actual runtime."""
from pathlib import Path
import sys,os,json,time,resource
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
method='improve'
case=ROOT/'.runs/runtime-directory-007';runtime=case/'runtime';setup=json.loads((ROOT/'.runs/runtime-directory-003/setup.json').read_text());assert p.tree_hash(Path(setup['source']).parent)==setup['source_hashes']
out=runtime/'.runs'/('enclosure-'+method+'-2cu');out.mkdir();driver=ROOT/'scripts/qualify_runtime_workflow.py';pin=p.sha(driver)
argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(runtime/'.venv/bin/python'),'-B',str(driver),'--runtime',str(runtime),'--source',setup['source'],'--output',str(runtime/'.runs'/('qualification-'+method+'-2cu')),'--method',method]
process=run(argv,cwd=runtime,log=out/'command.log',timeout=235,max_log_bytes=128*1024,max_workdir_bytes=256*1024**2,max_group_rss_bytes=4*1024**3,env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}})
child=runtime/'.runs'/('qualification-'+method+'-2cu')/'result.json';data=json.loads(child.read_bytes()) if child.exists() else None
passed=bool(data and data.get('workflow_delivered') is True and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False and pin==p.sha(driver))
record=dict(schema=1,accepted=False,workflow_delivered=passed,actual_GUI=False,method=method,process=process,driver_sha256=pin,source_hashes=setup['source_hashes'],same_source_unchanged=p.tree_hash(Path(setup['source']).parent)==setup['source_hashes'],child_sha256=p.sha(child) if child.exists() else None)
p.save_json(out/'execution.json',record);print(json.dumps(dict(method=method,workflow_delivered=passed,status=process['status'],exit_code=process['exit_code'])))
raise SystemExit(0 if passed else 2)
