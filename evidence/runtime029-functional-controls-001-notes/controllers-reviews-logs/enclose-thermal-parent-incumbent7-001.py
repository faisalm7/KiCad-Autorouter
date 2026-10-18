"""Shared delivery driver, one fixed accepted-incumbent branch qualification."""
from pathlib import Path
import sys,os,time,resource,json
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx
from autorouter.runner import run
base=ROOT/'.runs/thermal-parent-incumbent7-controls-001';protocol=base/'protocol.json';pin=p.sha(protocol);plan=f.read_json(protocol);assert p.sha(Path(__file__))==plan['enclosure_sha256'];case=plan['cases']['native7'];runtime=Path(case['runtime']);out=Path(case['output']);assert not out.exists();folder=base/'enclosure';folder.mkdir()
argv=[*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B',str(ROOT/'.runs/run-thermal-parent-delivery-002.py'),'--runtime',str(runtime),'--protocol',str(protocol),'--protocol-sha256',pin,'--case','native7']
env={k:v for k,v in os.environ.items() if not k.startswith('KICAD_') and k not in ('PYTHONPATH','PYTHONHOME')};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run(argv,cwd=folder,env=env,log=folder/'command.log',timeout=375,max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=512*1024**2);p.save_json(folder/'process.json',process)
receipt=out/'result.json';child=f.read_json(receipt) if receipt.is_file() else None;checks={};error=None
try:
 assert child and child['workflow_delivered'] and child['source_originals_unchanged']
 route=f.read_json(Path(child['route_receipt']));inc=f.read_json(Path(route['incumbent']['receipt']));export=f.read_json(Path(child['export_receipt']))
 checks.update(incumbent_accepted=inc['accepted'] is True,recovery_not_needed=route['recovery_needed'] is False,no_repair=route.get('repair') is None and not (Path(child['route_receipt']).parent/'recovery').exists(),exact_incumbent_selected=route['candidate_sha256']==inc['candidate_sha256']==export['candidate_sha256'])
 original=sx.read(Path(plan['source']));protected=[v for v in p.routes(original) if p.locked(v)];checks['protected_count']=len(protected);checks['expected_protected_count']=len(protected)==plan['expected_protected_count']
 for label,data in [('incumbent',inc),('parent',route),('export',export)]:
  board=sx.read(Path(data['candidate']));checks[label+'_original_and_protected']=p.immutable(board)==p.immutable(original) and all(v in p.routes(board) for v in protected)
  checks[label+'_counts']=[data['native'][k] for k in ('opens','blocking','warnings','exclusions')]==plan['expected_counts']
  checks[label+'_full_schematic']=data['schematic_parity']=='checked by final native DRC'
 assert all(v is True for k,v in checks.items() if k!='protected_count')
except (Exception,KeyboardInterrupt) as exc:error=type(exc).__name__+': '+str(exc)
stable=p.sha(protocol)==pin and p.sha(Path(__file__))==plan['enclosure_sha256'];wall=time.monotonic()-START;cost=cpu()-CPU0
passed=bool(child and error is None and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and stable and max(wall,cost)<=360)
record=dict(schema=1,kind='actual-selected7-accepted-incumbent-delivery',controls_passed=passed,workflow_delivered=bool(child and child.get('workflow_delivered')),accepted=False,project_complete=False,actual_GUI=False,human_review=False,checks=checks,error=error,process=process,child_receipt=str(receipt),child_sha256=p.sha(receipt) if child else None,protocol_sha256=pin,complete_wall_seconds=wall,complete_full_CPU_seconds=cost,scope='One own exposed whole4Cu B1-success fixture, no-repair/verifiedincumbent branch with protected10 and each final original/Native/fullSCH proof. Not repairbranch protected qualification, addedcompletion or comparison.')
p.save_json(base/'execution.json',record);print(json.dumps({k:v for k,v in record.items() if k!='process'}));raise SystemExit(0 if passed else 2)
