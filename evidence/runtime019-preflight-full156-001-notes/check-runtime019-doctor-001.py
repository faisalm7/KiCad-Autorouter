"""One actual installed CLI readiness check, with the existing bounded runner."""
from pathlib import Path
import json,os,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
runtime=ROOT/'.runs/runtime-directory-019/runtime';out=ROOT/'.runs/runtime019-doctor-001';out.mkdir()
code='import sys,runpy;sys.path.insert(0,'+repr(str(runtime))+');sys.argv=["autorouter","doctor"];runpy.run_module("autorouter",run_name="__main__")'
env={k:v for k,v in os.environ.items()if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}}
process=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B','-c',code],cwd=out,log=out/'command.log',timeout=60,max_log_bytes=128*1024,max_workdir_bytes=1024*1024,max_group_rss_bytes=512*1024**2,env=env)
row=f.read_json(out/'command.log');assert process['exit_code']==0 and process['status']=='success'and process['cleanup_complete']and not process['log_truncated']and row['ready']is True
p.save_json(out/'execution.json',dict(schema=1,passed=True,accepted=False,actual_installed_doctor=True,report_sha256=p.sha(out/'command.log'),process=process,scope='Actual healthy019installedCLI doctor/tool version probes only, not Native board routing/validation or missing-Java execution qualification. Missing/failing tools are authored regression controls separately.'))
print(json.dumps(dict(passed=True,ready=row['ready'],workspace=row['workspace'],actual_GUI=False)))
