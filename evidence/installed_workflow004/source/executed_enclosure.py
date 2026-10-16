"""Existing process enclosure around one actual installed workflow diagnostic."""
from pathlib import Path
import argparse,json,sys,os
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
from autorouter.runner import run
ap=argparse.ArgumentParser();ap.add_argument('project',choices=['push-button-led','nus-usb-led']);ap.add_argument('method',choices=['route','improve']);a=ap.parse_args()
out=ROOT/'.runs/installed-gui-workflow-diagnostic-004'/a.project/a.method;out.mkdir(parents=True)
driver=ROOT/'.runs/installed-gui-workflow-diagnostic-004.py';pin=p.sha(driver);python=ROOT/'.runs/installation-050/checkout/.venv/bin/python'
argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(python),'-B',str(driver),'--project',a.project,'--method',a.method,'--output',str(out/'child')]
process=run(argv,cwd=out,log=out/'command.log',timeout=230,max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3,env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}})
child=out/'child/result.json';data=json.loads(child.read_bytes()) if child.is_file() else None
passed=bool(data and data.get('workflow_delivered') is True and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False and pin==p.sha(driver))
p.save_json(out/'execution.json',dict(schema=1,accepted=False,workflow_delivered=passed,process=process,driver_sha256=pin,child_sha256=p.sha(child) if child.is_file() else None,log_sha256=p.sha(out/'command.log')))
print(json.dumps(dict(project=a.project,method=a.method,workflow_delivered=passed,status=process['status'],exit_code=process['exit_code'],cleanup_complete=process['cleanup_complete'])))
raise SystemExit(130 if process['status']=='cancelled' or process.get('exit_code')==130 else 0 if passed else 2)
