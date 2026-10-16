"""Shared bounded process runner; no new Native verifier."""
from pathlib import Path
import argparse,json,os,sys
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
from autorouter.runner import run
ap=argparse.ArgumentParser();ap.add_argument('project',choices=['push-button-led','nus-usb-led']);a=ap.parse_args()
CLONE=ROOT/'.runs/installation-050/checkout';work=CLONE/'.runs/competent-portfolio005'/a.project;work.mkdir(parents=True)
driver=ROOT/'.runs/installed-competent-portfolio005.py';pin=p.sha(driver);args=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(CLONE/'.venv/bin/python'),'-B',str(driver),'--project',a.project,'--work',str(work)]
process=run(args,cwd=work,log=work/'command.log',timeout=230,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3,max_log_bytes=256*1024,env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}})
child=work/'child/result.json';data=json.loads(child.read_bytes()) if child.is_file() else None
passed=bool(data and data.get('status')=='completed' and data.get('workflow_delivered') is True and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False and pin==p.sha(driver))
p.save_json(work/'execution.json',dict(schema=1,accepted=False,workflow_delivered=passed,driver_sha256=pin,child_sha256=p.sha(child) if child.is_file() else None,process=process,log_sha256=p.sha(work/'command.log')))
print(json.dumps(dict(project=a.project,workflow_delivered=passed,status=process['status'],exit_code=process['exit_code'],cleanup_complete=process['cleanup_complete'])))
raise SystemExit(130 if process['status']=='cancelled' or process.get('exit_code')==130 else 0 if passed else 2)
