import sys,time,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
START=time.monotonic();CPU0=time.process_time()+f.child_cpu();out=Path(__file__).parent/'late-witness-controls-001';out.mkdir()
process=run([str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).parent/'test-late-witnesses.py')],cwd=out,log=out/'command.log',timeout=30,max_log_bytes=128*1024,max_workdir_bytes=1024**2,max_group_rss_bytes=512*1024**2)
r=dict(process=process,wall_seconds=time.monotonic()-START,full_cpu_seconds=time.process_time()+f.child_cpu()-CPU0,new_native_execution=False)
p.save_json(out/'execution.json',r);print(json.dumps(r));raise SystemExit(0 if process['status']=='success' else 2)
