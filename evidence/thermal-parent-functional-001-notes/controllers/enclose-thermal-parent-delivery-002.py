"""Shared bounded runner for exactly one frozen functional delivery."""
from pathlib import Path
import sys,os,time,resource,json
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
label=sys.argv[1];assert label in ('native7','legacy0');base=ROOT/'.runs/thermal-parent-normal-controls-002';protocol=base/'protocol.json';protocol_pin=p.sha(protocol);plan=f.read_json(protocol);assert p.sha(Path(__file__))==plan['enclosure_sha256'];case=plan['cases'][label];runtime=Path(case['runtime']);out=Path(case['output']);assert not out.exists();folder=base/(label+'-enclosure');folder.mkdir()
argv=[*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B',str(ROOT/'.runs/run-thermal-parent-delivery-002.py'),'--runtime',str(runtime),'--protocol',str(protocol),'--protocol-sha256',p.sha(protocol),'--case',label]
env={k:v for k,v in os.environ.items() if not k.startswith('KICAD_') and k not in ('PYTHONPATH','PYTHONHOME')};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run(argv,cwd=folder,env=env,log=folder/'command.log',timeout=plan['whole_budget_seconds']+15,max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=512*1024**2);p.save_json(folder/'process.json',process)
receipt=out/'result.json';child=f.read_json(receipt) if receipt.is_file() else None;wall=time.monotonic()-START;cost=cpu()-CPU0
stable=p.sha(protocol)==protocol_pin and p.sha(Path(__file__))==plan['enclosure_sha256']
record=dict(schema=1,case=label,accepted=False,project_complete=False,workflow_delivered=bool(child is not None and child['workflow_delivered'] and child['status']=='completed' and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and stable and max(wall,cost)<=plan['whole_budget_seconds']),process=process,child_receipt=str(receipt),child_receipt_sha256=p.sha(receipt) if child else None,status=child.get('status') if child else None,reason=child.get('reason') if child else None,route_reason=child.get('route_reason') if child else None,protocol_sha256=p.sha(protocol),complete_wall_seconds=wall,complete_full_CPU_seconds=cost)
p.save_json(folder/'execution.json',record);print(json.dumps({k:v for k,v in record.items() if k!='process'}));raise SystemExit(0 if record['workflow_delivered'] else 2)
