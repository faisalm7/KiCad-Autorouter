"""Fresh current B2low200 and actual own-low C200, all prior450 costs retained."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,copy,fcntl
R=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx,handoff as h
from autorouter.runner import run
from experiments.native_paired_v1 import observations as obs
from experiments.universal_shift_recovery_v1 import pruning_readback as shared
PROTOCOL=R/'.runs/universal-native-reserve750-001-protocol.json';spec=f.read_json(PROTOCOL);PIN=p.sha(PROTOCOL)
O=R/'.runs/universal-native-reserve750-001';assert O.resolve()==O and not any(x.is_symlink() for x in (O,*O.parents));O.mkdir();owner={};h.capture_destination(owner,O)
record=dict(schema=1,kind='current-native-reserve750-paired-v1',passed=False,source_current=False,accepted=False,production_admitted=False,tools=spec['tools'],protocol_sha256=PIN,processes=[],observations=[],publication_allowance_seconds=4,startup_allowance_seconds=1)
materials={};receipts={};data_by_id={}
def need(v,why):obs.require(v,why)
def inv(path):return pc.inventory(path,max_bytes=512*1024**2,max_files=10000,max_entries=20000,with_directories=True)
def stable():
 need(p.tool_manifest()==spec['tools'] and p.sha(PROTOCOL)==PIN,'currenttools/protocol changed');shared.inputs(spec);h.owned_destination(owner)
 for ident,data in data_by_id.items():shared.metadata(data)
 for folder,material in materials.items():need(inv(folder)==material,'completed Native material changed')
 for path,pin in receipts.items():need(p.sha(path)==pin,'completed receipt changed')
try:
 need(spec['kind']=='universal-native-reserve750-v1' and spec['status']=='frozen','wrong unfrozen protocol')
 source,original,baseline=shared.inputs(spec);stable()
 lock=R/'.runs/quality-experiment.lock';need(not lock.is_symlink(),'lock alias')
 with lock.open('a') as held:
  fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for ident,args in [('B2_long_low',['route',str(source),'--seconds','200','--adapter','both','--profile','tuned','--scoring-preference','via_low']),('C_feedback',['improve',str(source),'--seconds','200','--proposal-policy','feedback','--scoring-preference','via_low'])]:
   stable();folder=O/ident
   process=run([*f.SANDBOX,str(R/'.venv/bin/python'),'-B',str(R/'experiments/universal_shift_recovery_v1/cli_entry.py'),*args,'--output',str(folder)],cwd=O,log=O/(ident+'.log'),timeout=min(215,max(.001,508-(time.monotonic()-START))),max_log_bytes=4*1024**2,max_workdir_bytes=512*1024**2,max_group_rss_bytes=2*1024**3)
   record['processes'].append(dict(id=ident,process=process));path=folder/'result.json';pin=p.sha(path);data=f.read_json(path);materials[folder]=inv(folder);receipts[path]=pin;data_by_id[ident]=data
   need(data['tools']==spec['tools'] and data['source']==str(source) and data['source_hashes']==spec['source_hashes'],'actual source/runtime differs')
   need(data['budget_seconds']==data['cpu_budget_seconds']==200,'actual individual budget differs')
   need(process['status'] in ('success','nonzero_exit') and type(process['exit_code']) is int and process['exit_code']==(0 if data['accepted'] else 2) and process['cleanup_complete'] is True and process['log_truncated'] is False,'method process incomplete')
   if ident=='B2_long_low':
    need(data['scope']=='whole_board_unlocked_routing' and data['adapter']=='both' and data['engine_profile']=='tuned' and data['scoring_variant']=='via_low','stronger B2 configuration differs')
    workers=obs.workers(folder,data,source,spec['source_hashes'],original);proof=None
    if (folder/'final-drc.json').is_file() and data.get('candidate_sha256'):
     p.check_engine_profile_record(data,folder)
     proof=obs.candidate(folder,data,source,original,spec['source_hashes'],baseline,resource_error=obs.resource_failure(folder,data))
    valid=bool(data['accepted'] and proof and proof['full_shared_candidate_readback'] and proof['unchanged_original_warning_signatures'] and p.native_accepted(data['native']))
    if data['accepted']:need(p.check_result(path)['current'] is True,'accepted B2 stale')
    check=dict(passed=True,candidate_valid=valid,workers=workers,final_observations=[proof] if proof else [])
   else:
    need(data['finalization_reserve_seconds']==data['finalization_cpu_reserve_seconds']==25,'new native reservation missing')
    check=shared.check(folder,data,spec)
   record['observations'].append(dict(id=ident,result=str(path),result_sha256=pin,checks=check))
   stable()
 stable();record.update(passed=True,source_current=True)
except BaseException as exc:record.update(passed=False,source_current=False,reason=type(exc).__name__+': '+str(exc))
wall=time.monotonic()-START;full=cpu()-CPU0;record.update(wall_seconds=wall,full_cpu_seconds=full,controller_sha256=p.sha(Path(__file__)))
raws={row['id']:(row['process'].get('wall_seconds'),row['process'].get('cpu_seconds')) for row in record['processes']}
rows=copy.deepcopy(spec['prior_rows']);known=all(type(v) in (int,float) and v>=0 for pair in raws.values() for v in pair)
if known and wall>=sum(v[0] for v in raws.values()) and full>=sum(v[1] for v in raws.values()):
 sw=wall-sum(v[0] for v in raws.values());sc=full-sum(v[1] for v in raws.values());record.update(shared_wall_seconds=sw,shared_full_cpu_seconds=sc)
 for row in rows:
  ident='B2_long_low' if row['id']=='B2_portfolio' else row['id'];a,b=raws.get(ident,(0,0));row.update(charged_wall_seconds=row['charged_wall_seconds']+sw+5+a,charged_cpu_seconds=row['charged_cpu_seconds']+sc+5+b)
  observation=next((x for x in record['observations'] if x['id']==ident),None)
  row['new_run_accepted']=bool(observation and observation['checks']['candidate_valid']);row['previous_accepted']=row['accepted']
  if record['passed'] and row['new_run_accepted']:
   d=data_by_id[ident];n=d['native'];m=d['metrics']
   if not row['accepted'] or (m['vias'],m['track_length_mm'])<=(row['vias'],row['length_mm']):
    row.update(accepted=True,status=d['status'],result=observation['result'],result_sha256=observation['result_sha256'],candidate_sha256=d['candidate_sha256'],native_report_sha256=d['native_report_sha256'],length_mm=m['track_length_mm'],vias=m['vias'],**{k:n[k] for k in ('opens','blocking','warnings','exclusions')})
  row['within_cumulative750_wall_full_cpu_caps']=max(row['charged_wall_seconds'],row['charged_cpu_seconds'])<=750
  row['accepted']=bool(record['passed'] and row['accepted'] and row['within_cumulative750_wall_full_cpu_caps'])
else:record.update(passed=False,source_current=False,reason=record.get('reason','invalid enclosing accounting'))
if max(wall,full)+5>510:record.update(passed=False,source_current=False,reason=record.get('reason','whole510-second cap exceeded'))
if not record['passed']:
 for row in rows:row['accepted']=False
record['final_charged_results']=rows;p.save_json(O/'execution.json',record);epin=p.sha(O/'execution.json')
try:
 stable()
 need(f.canonical(f.read_json(O/'execution.json'))==f.canonical(record) and p.sha(O/'execution.json')==epin,'published final receipt changed')
 need(time.monotonic()-START<=wall+4 and cpu()-CPU0<=full+4,'publication allowance exceeded')
except BaseException as exc:
 record.update(passed=False,source_current=False,reason=type(exc).__name__+': '+str(exc))
 for row in record['final_charged_results']:row['accepted']=False
 p.save_json(O/'execution.json',record)
print(json.dumps({k:record.get(k) for k in ('passed','source_current','reason','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
