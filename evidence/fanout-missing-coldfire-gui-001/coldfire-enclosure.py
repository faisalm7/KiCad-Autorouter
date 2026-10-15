"""One bounded original-only diagnostic command, no source repair or routing."""
from pathlib import Path
import argparse,sys,os
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
MODULE=ROOT/'.runs/coldfire-native-diagnostic-support-001/driver.py'
PROTOCOL=ROOT/'.runs/coldfire-original-native1000-preparation-001/protocol.json'
HEAD='da255bfb15cc5881af7d591dc59c4fd5f6b27afe'
a=argparse.ArgumentParser();a.add_argument('--mode',choices=['prepare','run','read'],required=True);args=a.parse_args()
OUT=ROOT/'.runs/coldfire-command-execution-001'/args.mode;OUT.mkdir(parents=True)
argv=[str(ROOT/'.venv/bin/python'),'-B',str(MODULE),'--mode',args.mode,'--source-head',HEAD]
if args.mode!='prepare':argv+=['--protocol-sha256',p.sha(PROTOCOL)]
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',LANG='C',LC_ALL='C')
process=run(argv,cwd=OUT,log=OUT/'command.log',timeout=60 if args.mode=='prepare' else 120,max_log_bytes=256*1024,max_group_rss_bytes=2*1024**3,max_workdir_bytes=8*1024**2,env=env)
p.save_json(OUT/'execution.json',dict(schema=1,accepted=False,source_head=HEAD,mode=args.mode,process=process,controller_sha256=p.sha(Path(__file__)),module_sha256=p.sha(MODULE),log_sha256=p.sha(OUT/'command.log') if (OUT/'command.log').is_file() else None,scope='Original-only diagnostic execution; exit0 completes observation and does not qualify support/routing/physical correctness. Complete child exit observed; own whole process externally timed.'))
print(f.canonical({k:process[k] for k in ['status','exit_code','cleanup_complete','wall_seconds','cpu_seconds','monitor_cpu_seconds']}))
raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'] else 2)
