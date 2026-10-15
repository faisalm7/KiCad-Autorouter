"""One bounded new B2 continuation plus mandatory pure post-worker semantic/material check."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,fcntl,copy
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,local_settings as ls,config as c
from autorouter.runner import run
from experiments.universal_shift_recovery_v1 import b2 as actor
PROTOCOL=actor.PROTOCOL;spec=f.read_json(PROTOCOL);PIN=p.sha(PROTOCOL)
OUT=Path(spec['output']).parent
assert OUT==ROOT/'.runs/universal-B2-missing450-001' and OUT.resolve()==OUT and not any(x.is_symlink() for x in (OUT,*OUT.parents))
assert spec['status']=='frozen' and spec['tools']==p.tool_manifest()
OUT.mkdir();record=dict(schema=1,kind='universal-B2-missing450-enclosing-v1',passed=False,source_current=False,accepted=False,production_admitted=False,candidate_valid=False,publication_allowance_seconds=2,startup_allowance_seconds=1,protocol_sha256=PIN,tools=p.tool_manifest(),process=None)
def need(value,reason):
 if not value:raise p.Rejected(reason)
def inv(path):return pc.inventory(path,max_bytes=512*1024**2,max_files=4000,max_entries=8000,with_directories=True)
try:
 need(p.tool_manifest()==spec['tools'],'tools/checkpoint differ');actor.inputs(spec)
 lock=ROOT/'.runs/quality-experiment.lock';need(not lock.is_symlink(),'lock alias')
 with lock.open('a') as held:
  fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
  record['process']=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(actor.__file__)),'--output',spec['output']],cwd=OUT,log=OUT/'command.log',timeout=max(.001,238-(time.monotonic()-START)),max_log_bytes=128*1024,max_workdir_bytes=512*1024**2,max_group_rss_bytes=2*1024**3)
 base=Path(spec['output']);material=inv(base);receipt=base/'result.json';rpin=p.sha(receipt);data=f.read_json(receipt)
 need(data['tools']==spec['tools'] and data['protocol_sha256']==PIN and data['accepted'] is False and data['production_admitted'] is False,'worker scope/source differs')
 need(f.canonical(f.read_json(receipt))==f.canonical(data),'parsed worker receipt differs')
 record['checks']=actor.check(base,data,spec)
 need(p.tool_manifest()==spec['tools'] and p.sha(PROTOCOL)==PIN,'tools/protocol changed');actor.inputs(spec)
 actor.metadata(data)
 need(inv(base)==material and p.sha(receipt)==rpin,'worker material changed during final callbacks')
 process=record['process'];need(process['status']=='success' and type(process['exit_code']) is int and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False,'worker incomplete')
 need(data['status']=='completed' and data['method_qualified'] is True,'B2 continuation unqualified')
 record.update(passed=True,source_current=True,candidate_valid=record['checks']['candidate_valid'],actor_result_sha256=rpin,actor_material=material,new_observation=data['final_observation'],new_metrics=data.get('metrics'))
except BaseException as exc:record.update(passed=False,candidate_valid=False,reason=type(exc).__name__+': '+str(exc))
wall=time.monotonic()-START;full=cpu()-CPU0;record.update(wall_seconds=wall,full_cpu_seconds=full,controller_sha256=p.sha(Path(__file__)))
process=record['process'] or {};raw_wall=process.get('wall_seconds');raw_cpu=process.get('cpu_seconds')
# Whole-process cost already includes supervisor/monitor CPU; subtract actual child
# only. Remaining nonnegative cost is charged to every retained comparison arm.
rows=copy.deepcopy(spec['prior_rows'])
if type(raw_wall) in (int,float) and type(raw_cpu) in (int,float) and raw_wall>=0 and raw_cpu>=0 and wall>=raw_wall and full>=raw_cpu:
 sw=wall-raw_wall;sc=full-raw_cpu
 record.update(raw_B2_wall_seconds=raw_wall,raw_B2_full_cpu_seconds=raw_cpu,shared_wall_seconds=sw,shared_full_cpu_seconds=sc)
 for row in rows:
  row.update(charged_wall_seconds=row['charged_wall_seconds']+sw+3+(raw_wall if row['id']=='B2_portfolio' else 0),charged_cpu_seconds=row['charged_cpu_seconds']+sc+3+(raw_cpu if row['id']=='B2_portfolio' else 0))
  row['accepted']=record['passed'] and record['candidate_valid'] if row['id']=='B2_portfolio' else row['accepted']
  if row['id']=='B2_portfolio' and row['accepted']:
   choices=[(i,t) for i,t in enumerate(data['trials']) if t['observation']['candidate_valid']]
   _,chosen=min(choices,key=lambda pair:(pair[1]['observation']['final_candidate']['metrics']['vias'],pair[1]['observation']['final_candidate']['metrics']['track_length_mm'],pair[0]))
   actual=f.read_json(ROOT/chosen['result']);native=actual['native'];metrics=actual['metrics']
   row.update(status=actual['status'],selected_variant=chosen['id'],result=str(ROOT/chosen['result']),result_sha256=chosen['result_sha256'],candidate_sha256=actual['candidate_sha256'],native_report_sha256=actual['native_report_sha256'],length_mm=metrics['track_length_mm'],vias=metrics['vias'],**{k:native[k] for k in ('opens','blocking','warnings','exclusions')})
  row['within_cumulative450_wall_full_cpu_caps']=max(row['charged_wall_seconds'],row['charged_cpu_seconds'])<=450
  row['accepted']=row['accepted'] and row['within_cumulative450_wall_full_cpu_caps']
else:record.update(passed=False,candidate_valid=False,reason=record.get('reason','invalid nonnegative enclosing cost'))
if max(wall,full)+3>240:
 record.update(passed=False,candidate_valid=False,reason=record.get('reason','complete continuation240-second publication cap exceeded'))
 for row in rows:row['accepted']=False
record['final_charged_results']=rows
p.save_json(OUT/'execution.json',record)
execution_pin=p.sha(OUT/'execution.json')
try:
 need(f.canonical(f.read_json(OUT/'execution.json'))==f.canonical(record) and p.sha(OUT/'execution.json')==execution_pin,'published probe execution differs')
 need(time.monotonic()-START<=record['wall_seconds']+2 and cpu()-CPU0<=record['full_cpu_seconds']+2,'final publication exceeded allowance')
except BaseException as exc:
 record.update(passed=False,candidate_valid=False,reason=type(exc).__name__+': '+str(exc))
 for row in record['final_charged_results']:row['accepted']=False
 p.save_json(OUT/'execution.json',record)
print(json.dumps({k:record.get(k) for k in ('passed','candidate_valid','reason','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
