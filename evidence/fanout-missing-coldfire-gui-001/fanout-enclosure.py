"""Bound one reviewed fresh Native operation; preserve actual child exit costs."""
from pathlib import Path
import argparse,time,resource,sys,os
START=time.monotonic()
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
from experiments.fanout_baseline_v1 import native_control as owned,pair
parser=argparse.ArgumentParser();parser.add_argument('--label',choices=['native-prepare','native-run','pair-prepare','ir-stock45','ir-NONE'],required=True);parser.add_argument('--source-head',required=True);args=parser.parse_args()
label=args.label;OUT=ROOT/'.runs/fanout-command-receipts-002'/label;OUT.mkdir(parents=True)
module=Path(owned.__file__) if label.startswith('native-') else Path(pair.__file__)
argv=[str(ROOT/'.venv/bin/python'),'-B',str(module),'--mode','prepare' if label.endswith('prepare') else 'run','--source-head',args.source_head]
if label=='native-run':argv+=['--protocol-sha256',p.sha(owned.PROTOCOL)]
if label=='pair-prepare':argv+=['--control-sha256',p.sha(pair.CONTROL)]
if label.startswith('ir-'):argv+=['--protocol-sha256',p.sha(pair.PROTOCOL),'--project','ir-obstacle','--arm',label[3:]]
timeout=60 if label.endswith('prepare') else 180 if label=='native-run' else 240
env={k:v for k,v in os.environ.items() if k not in {'PYTHONHOME','PYTHONPATH'}};env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',LANG='C',LC_ALL='C')
proc=run(argv,cwd=OUT,log=OUT/'command.log',timeout=timeout,max_log_bytes=256*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=8*1024**2,env=env)
record=dict(schema=1,label=label,source_git_head=args.source_head,process=proc,controller_sha256=p.sha(Path(__file__)),module_sha256=p.sha(module),log_sha256=p.sha(OUT/'command.log') if (OUT/'command.log').is_file() else None,scope='Actual enclosing command exit observed by shared runner, not inner worker or pre-publication sample. Complete external /usr/bin/time log separately captures this envelope exit. Existing command Native/scratch/lane/time guards retained; accepted remains false for this execution receipt.',accepted=False)
p.save_json(OUT/'execution.json',record);print(f.canonical({k:proc[k] for k in ['status','exit_code','cleanup_complete','wall_seconds','cpu_seconds','monitor_cpu_seconds']}));raise SystemExit(0 if proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] and not proc['log_truncated'] else 2)
