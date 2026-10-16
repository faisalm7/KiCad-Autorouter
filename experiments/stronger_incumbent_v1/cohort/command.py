"""Existing bounded runner around one frozen experimental command."""
from pathlib import Path
import argparse,json,os,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
DRIVER=Path(__file__).with_name('driver.py')
PROTOCOL=ROOT/'.runs/stronger-incumbent-cohort-preparation-001/protocol.json'
PROJECTS=('sonde','nus-usb-led','push-button-led','ds18b20')
STAGES={project+'--'+name:(project,name) for project in PROJECTS for name in ('B2_stronger','C_stronger')}
ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['prepare',*STAGES,'read','report'],required=True);ap.add_argument('--source-head',required=True);a=ap.parse_args()
OUT=ROOT/'.runs/stronger-incumbent-cohort-enclosures-001'/a.stage;OUT.mkdir(parents=True)
mode='run' if a.stage in STAGES else a.stage
args=[str(DRIVER),'--mode',mode,'--source-head',a.source_head]
if mode=='prepare':args+=['--control-sha256',p.sha(ROOT/'evidence/global-min-width-native-qualified-001.json'),'--source-gates-sha256',p.sha(ROOT/'evidence/stronger-cohort-original-gates-001.json')]
else:args+=['--protocol-sha256',p.sha(PROTOCOL)]
if mode=='run':
 project,name=STAGES[a.stage];args+=['--project',project,'--arm',name]
print(json.dumps({'invocation':dict(argv=args,cwd=str(OUT),executable=str(ROOT/'.venv/bin/python'),controller_sha256=p.sha(DRIVER))}),flush=True)
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',LANG='C',LC_ALL='C')
process=run([str(ROOT/'.venv/bin/python'),'-B',*args],cwd=OUT,log=OUT/'command.log',timeout={'prepare':60,'run':240,'read':90,'report':30}[mode],max_log_bytes=256*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=8*1024**2,env=env)
record=dict(schema=1,stage=a.stage,source_head=a.source_head,driver_sha256=p.sha(DRIVER),wrapper_sha256=p.sha(Path(__file__)),process=process,log_sha256=p.sha(OUT/'command.log') if (OUT/'command.log').is_file() else None)
p.save_json(OUT/'execution.json',record)
passed=process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False
print(json.dumps(dict(stage=a.stage,passed=passed,status=process['status'],exit_code=process['exit_code'],cleanup_complete=process['cleanup_complete'])),flush=True)
raise SystemExit(0 if passed else 130 if process['status']=='cancelled' or process['exit_code']==130 and process['cleanup_complete'] is True else 2)
