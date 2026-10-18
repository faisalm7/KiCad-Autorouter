"""One current ordinary default workflow via the existing shared qualifier."""
from pathlib import Path
import sys,os,time,resource,json
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
base=ROOT/'.runs/runtime029-default-CLI-001';protocol=base/'protocol.json';plan=f.read_json(protocol);pin=p.sha(protocol);assert p.sha(Path(__file__))==plan['enclosure_sha256'];assert p.sha(ROOT/'scripts/qualify_runtime_workflow.py')==plan['driver_sha256']
runtime=Path(plan['runtime']);out=Path(plan['output']);assert not out.exists();folder=base/'enclosure';folder.mkdir()
env={k:v for k,v in os.environ.items() if not k.startswith('KICAD_') and k not in ('PYTHONPATH','PYTHONHOME')};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B',str(ROOT/'scripts/qualify_runtime_workflow.py'),'--runtime',str(runtime),'--source',plan['source'],'--output',str(out),'--method','route','--settings',str(base/'default-settings.json')],cwd=folder,env=env,log=folder/'command.log',timeout=255,max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=512*1024**2);p.save_json(folder/'process.json',process)
receipt=out/'result.json';child=f.read_json(receipt) if receipt.is_file() else None;error=None;counts=None;protected=None
try:
 assert child and child['workflow_delivered'] and child['settings']==plan['settings'];w=Path(child['workspace']);r=f.read_json(w/'route/result.json');ex=f.read_json(w/'export/export.json')
 counts=[r['native'][k] for k in ('opens','blocking','warnings','exclusions')];assert counts==plan['expected_counts']==[ex['native'][k] for k in ('opens','blocking','warnings','exclusions')]
 assert r['schematic_parity']==ex['schematic_parity']=='checked by final native DRC';assert r['source_hashes']==ex['source_hashes']==plan['source_hashes']
 assert r['candidate_sha256']==ex['candidate_sha256'];assert ex['budget_seconds']==90
 from autorouter import sexpr as sx
 orig=sx.read(Path(plan['source']));items=[v for v in p.routes(orig) if p.locked(v)];protected=len(items);assert protected==10
 assert all(p.immutable(sx.read(Path(d['candidate'])))==p.immutable(orig) and all(v in p.routes(sx.read(Path(d['candidate']))) for v in items) for d in (r,ex))
except (Exception,KeyboardInterrupt) as exc:error=type(exc).__name__+': '+str(exc)
wall=time.monotonic()-START;cost=cpu()-CPU0;stable=p.sha(protocol)==pin and p.sha(Path(__file__))==plan['enclosure_sha256'] and p.sha(ROOT/'scripts/qualify_runtime_workflow.py')==plan['driver_sha256'] and p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
passed=bool(child and error is None and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and stable and max(wall,cost)<=240)
record=dict(schema=1,kind='current-runtime029-default-whole-CLI',controls_passed=passed,workflow_delivered=bool(child and child['workflow_delivered']),accepted=False,project_complete=False,actual_GUI=False,human_review=False,process=process,child_receipt=str(receipt),child_sha256=p.sha(receipt) if child else None,protocol_sha256=pin,complete_wall_seconds=wall,complete_full_CPU_seconds=cost,Native_counts=counts,protected_count=protected,error=error,scope='One currentbuild defaultpolicy/default120budget ordinary whole4Cu/flatclass/protected10 fixture sixstage/native export90; not comparison, addedcompletion, GUI or physicalreview.')
p.save_json(base/'execution.json',record);print(json.dumps({k:v for k,v in record.items() if k!='process'}));raise SystemExit(0 if passed else 2)
