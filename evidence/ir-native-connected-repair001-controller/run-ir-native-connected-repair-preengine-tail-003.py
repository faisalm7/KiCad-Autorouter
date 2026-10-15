from pathlib import Path
import sys,time,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
O=R/'.runs/ir-native-connected-repair-preengine-tail-003';O.mkdir();tools=p.tool_manifest();start=time.monotonic();cpu=time.process_time()+f.child_cpu()
command=[str(R/'.venv/bin/python'),'-B',str(R/'.runs/read-ir-native-connected-repair-preengine-tail-003.py')]
process=run(command,cwd=O,log=O/'command.log',timeout=60,max_log_bytes=256*1024,max_workdir_bytes=512*1024**2,max_group_rss_bytes=2*1024**3)
record=dict(schema=1,tools=tools,process=process,wall_seconds=time.monotonic()-start,full_cpu_seconds=time.process_time()+f.child_cpu()-cpu,source_current=p.tool_manifest()==tools)
p.save_json(O/'execution.json',record);print(json.dumps({k:record[k] for k in ('wall_seconds','full_cpu_seconds','source_current')}));print(json.dumps({k:process[k] for k in ('status','exit_code','cleanup_complete')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and record['source_current'] else 2)
