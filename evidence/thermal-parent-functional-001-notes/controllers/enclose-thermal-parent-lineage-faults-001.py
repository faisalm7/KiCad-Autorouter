from pathlib import Path
import sys,time,resource,json
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,gui
from autorouter.runner import run
base=ROOT/'.runs/thermal-parent-lineage-faults-001';protocol=base/'protocol.json';pin=p.sha(protocol);plan=f.read_json(protocol);assert p.sha(Path(__file__))==plan['enclosure_sha256'];folder=base/'enclosure';folder.mkdir();runtime=Path(plan['runtime'])
argv=[*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B',str(ROOT/'.runs/thermal-parent-lineage-faults-001.py'),'--runtime',str(runtime),'--protocol',str(protocol),'--protocol-sha256',pin]
process=run(argv,cwd=folder,env=gui.child_environment(),log=folder/'command.log',timeout=255,max_log_bytes=512*1024,max_group_rss_bytes=2*1024**3,max_workdir_bytes=128*1024**2);p.save_json(folder/'process.json',process);receipt=Path(plan['output'])/'result.json';r=f.read_json(receipt) if receipt.is_file() else None;wall=time.monotonic()-START;cost=cpu()-CPU0
record=dict(schema=1,accepted=False,Native_executed=False,controls_passed=bool(r is not None and r['controls_passed'] and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and max(wall,cost)<=240 and p.sha(protocol)==pin),process=process,child_receipt=str(receipt),child_sha256=p.sha(receipt) if r else None,protocol_sha256=pin,complete_wall_seconds=wall,complete_full_CPU_seconds=cost)
p.save_json(base/'execution.json',record);print(json.dumps({k:v for k,v in record.items() if k!='process'}));raise SystemExit(0 if record['controls_passed'] else 2)
