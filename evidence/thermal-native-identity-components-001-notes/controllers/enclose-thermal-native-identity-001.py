"""Existing bounded runner around one frozen component control, never an adopter."""
from pathlib import Path
import sys,os,json,time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
label=sys.argv[1];assert label in ('legacy0','native7','invalid7')
base=ROOT/'.runs/thermal-native-identity-controls-001';protocol=base/'protocol.json';plan=f.read_json(protocol);case=plan['cases'][label];enclosure=base/(label+'-enclosure');enclosure.mkdir();runtime=Path(case['runtime']);out=Path(case['output']);assert not out.exists()
argv=[*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B',str(ROOT/'.runs/run-thermal-native-identity-component-001.py'),'--runtime',str(runtime),'--protocol',str(protocol),'--protocol-sha256',p.sha(protocol),'--case',label]
env={k:v for k,v in os.environ.items() if not k.startswith('KICAD_') and k not in ('PYTHONPATH','PYTHONHOME')};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
result=run(argv,cwd=enclosure,env=env,log=enclosure/'command.log',timeout=135,max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=256*1024**2);p.save_json(enclosure/'process.json',result)
receipt=out/'component-result.json';child=f.read_json(receipt) if receipt.is_file() else None
record=dict(schema=1,case=label,accepted=False,production_admitted=False,component_passed=bool(child is not None and child['component_passed'] and result['status']=='success' and result['exit_code']==0 and result['cleanup_complete'] and max(time.monotonic()-START,cpu()-CPU0)<=135),process=result,child_receipt=str(receipt),child_receipt_sha256=p.sha(receipt) if child else None,status=child.get('status') if child else None,reason=child.get('reason') if child else None,protocol_sha256=p.sha(protocol),whole_wall_seconds=time.monotonic()-START,whole_full_CPU_seconds=cpu()-CPU0)
p.save_json(enclosure/'execution.json',record);print(json.dumps({k:v for k,v in record.items() if k!='process'}));raise SystemExit(0 if record['component_passed'] else 2)
