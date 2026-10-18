"""One bounded installed arm at a time; shared controller does all qualification."""
import argparse, json, os, resource, sys, time
from pathlib import Path
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as pc
from autorouter.runner import run
ap=argparse.ArgumentParser();ap.add_argument('--arm',required=True);args=ap.parse_args()
base=ROOT/'.runs/interf-installed021-comparison-001';protocol=base/'protocol.json';plan=json.loads(protocol.read_text());assert args.arm in plan['arms']
case=base/(args.arm+'-enclosure');case.mkdir();runtime=Path(plan['runtime']);out=runtime/'.runs/interf-installed021-comparison-001'/args.arm
out.parent.mkdir(exist_ok=True);p.check_storage(active_root=out)
source=Path(plan['source']);assert pc.inventory(source.parent)==plan['source_hashes']
argv=[*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B',str(ROOT/'scripts/qualify_installed_workflow.py'),'--runtime',str(runtime),'--protocol',str(protocol),'--protocol-sha256',p.sha(protocol),'--output',str(out),'--arm',args.arm]
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run(argv,cwd=runtime,env=env,log=case/'command.log',timeout=250,max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=512*1024**2)
p.save_json(case/'process.json',process)
child=json.loads((out/'result.json').read_text()) if (out/'result.json').is_file() else None
wall=time.monotonic()-START;fullcpu=cpu()-CPU0
stable=pc.inventory(source.parent)==plan['source_hashes'] and all(p.sha(ROOT/name)==pin for name,pin in plan['administration_files_sha256'].items())
delivered=bool(child is not None and child.get('accepted') is True and child.get('workflow_delivered') is True and child.get('status')=='completed' and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and max(wall,fullcpu)<=240 and stable)
record=dict(schema=1,arm=args.arm,delivered=delivered,project_complete=False,actual_GUI=False,process=process,child_receipt=str(out/'result.json'),child_receipt_sha256=p.sha(out/'result.json') if child else None,child_status=child.get('status') if child else None,child_reason=child.get('reason') if child else None,
 protocol_sha256=p.sha(protocol),whole_wall_seconds=wall,whole_full_cpu_seconds=fullcpu,within_whole240_budget=max(wall,fullcpu)<=240,sources_unchanged=stable,method_wall_seconds=child.get('method_wall_seconds') if child else None,method_full_cpu_seconds=child.get('method_full_cpu_seconds') if child else None,
 native=child.get('native') if child else None,route_attempt=child.get('route_attempt') if child else None,metrics=child.get('metrics') if child else None)
p.save_json(case/'execution.json',record);print(json.dumps({k:v for k,v in record.items() if k not in ('process','native','route_attempt')}));raise SystemExit(0 if delivered else 2)
