"""Shared ordinary workflow v2: exact owned controls or all-warning development report.

Native acceptance, original rules/protection, final/source/material and same final
Route/export counts remain mandatory. A separately frozen development plan can
report all warnings without guessing their future count; opens/blocking must be0
and exclusion count remains explicit. Existing exact-count control mode unchanged.
"""
import argparse
from pathlib import Path
import sys,os,time,resource,json
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
parser=argparse.ArgumentParser();parser.add_argument('--protocol',type=Path,required=True);args=parser.parse_args();protocol=args.protocol;plan=f.read_json(protocol);base=protocol.parent;pin=p.sha(protocol);assert p.sha(Path(__file__))==plan['enclosure_sha256'];assert p.sha(ROOT/'scripts/qualify_runtime_workflow.py')==plan['driver_sha256']
runtime=Path(plan['runtime']);out=Path(plan['output']);assert not out.exists();manifest=runtime/'runtime-distribution.json';assert p.sha(manifest)==plan['runtime_manifest_sha256'];settings_path=base/'settings.json';assert p.sha(settings_path)==plan['settings_sha256'];folder=base/'enclosure';folder.mkdir()
env={k:v for k,v in os.environ.items() if not k.startswith('KICAD_') and k not in ('PYTHONPATH','PYTHONHOME')};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B',str(ROOT/'scripts/qualify_runtime_workflow.py'),'--runtime',str(runtime),'--source',plan['source'],'--output',str(out),'--method','route','--settings',str(settings_path)],cwd=folder,env=env,log=folder/'command.log',timeout=255,max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=512*1024**2);p.save_json(folder/'process.json',process)
receipt=out/'result.json';child=f.read_json(receipt) if receipt.is_file() else None;error=None;counts=None;protected=None
try:
 assert child and child['workflow_delivered'] and child['settings']==plan['settings'];w=Path(child['workspace']);r=f.read_json(w/'route/result.json');ex=f.read_json(w/'export/export.json')
 counts=[r['native'][k] for k in ('opens','blocking','warnings','exclusions')]
 assert counts==[ex['native'][k] for k in ('opens','blocking','warnings','exclusions')]
 expected=plan['expected_counts']
 if expected is None:
  assert plan['warning_policy']=='retain_all_native_findings' and counts[:2]==[0,0]
  assert type(plan['expected_exclusions']) is int and counts[3]==plan['expected_exclusions']
 else:assert counts==expected
 assert r['schematic_parity']==ex['schematic_parity']=='checked by final native DRC';assert r['source_hashes']==ex['source_hashes']==plan['source_hashes']
 assert r['candidate_sha256']==ex['candidate_sha256'];assert r['budget_seconds']==plan['budgets']['route'];assert ex['budget_seconds']==plan['budgets']['export']
 from autorouter import sexpr as sx
 orig=sx.read(Path(plan['source']));items=p.protected_for_record(r,orig);protected=len(items);assert protected==plan['expected_protected_count'];assert r['scope']==plan['settings']['scope']
 assert all(p.immutable(sx.read(Path(d['candidate'])))==p.immutable(orig) and all(v in p.routes(sx.read(Path(d['candidate']))) for v in items) for d in (r,ex))
except (Exception,KeyboardInterrupt) as exc:error=type(exc).__name__+': '+str(exc)
wall=time.monotonic()-START;cost=cpu()-CPU0;stable=p.sha(manifest)==plan['runtime_manifest_sha256'] and p.sha(settings_path)==plan['settings_sha256'] and p.sha(protocol)==pin and p.sha(Path(__file__))==plan['enclosure_sha256'] and p.sha(ROOT/'scripts/qualify_runtime_workflow.py')==plan['driver_sha256'] and p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
passed=bool(child and error is None and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and stable and max(wall,cost)<=240)
record=dict(schema=1,kind='current-runtime030-ordinary-CLI',controls_passed=passed,workflow_delivered=bool(child and child['workflow_delivered']),accepted=False,project_complete=False,actual_GUI=False,human_review=False,process=process,child_receipt=str(receipt),child_sha256=p.sha(receipt) if child else None,protocol_sha256=pin,complete_wall_seconds=wall,complete_full_CPU_seconds=cost,Native_counts=counts,protected_count=protected,error=error,scope=plan['scope'])
p.save_json(base/'execution.json',record);print(json.dumps({k:v for k,v in record.items() if k!='process'}));raise SystemExit(0 if passed else 2)
