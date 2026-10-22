"""DRAFT: one normal installed EEPROM Improve90 workflow; no retry or GUI.

The unchanged six-stage qualifier/encloser owns Native/current/source/protection
acceptance. This wrapper only freezes its inputs, dispatches once, and describes
the retained clock/proposal evidence. A refused or inconclusive attempt stays so.
"""
from pathlib import Path
import argparse,fcntl,json,math,os,resource,shutil,stat,sys,time
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
RUNTIME=ROOT/'.runs/runtime-directory-058/runtime';sys.path.insert(0,str(RUNTIME))
from autorouter import pipeline as p,floor_route as f,handoff as h,gui,preferences as pref,provenance as pv,strategy as s,sexpr as sx
from autorouter.runner import run
ap=argparse.ArgumentParser();ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
assert a.execute,'DRAFT: an explicit --execute is required; no implicit preparation/run'
protocol=a.protocol.absolute();assert p.sha(protocol)==a.protocol_sha256;plan=f.read_json(protocol)
assert plan['controller_sha256']==p.sha(Path(__file__))
assert plan['runtime']==str(RUNTIME) and plan['source_head']=='8f5e96b88dd22cd25919bb71ce47711612994efa'
assert plan['runtime_manifest_sha256']=='4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74'
base=ROOT/'.runs/runtime058-natural-expiry-001';out=RUNTIME/'.runs/native7-natural-expiry-eeprom-001'
assert plan['execution_base']==str(base) and plan['output']==str(out)
assert plan['method']=='improve' and plan['budgets']==dict(route=90,export=90)
assert plan['settings']==dict(pref.DEFAULTS,profile='tuned',seconds=90)
assert plan['expected_counts'] is None and plan['expected_exclusions']==0 and plan['expected_protected_count']==0
assert plan['warning_policy']=='retain_all_native_findings' and sys.platform=='darwin'
encloser=ROOT/'.runs/enclose-runtime044-workflow-001.py';source=Path(plan['source'])
def fresh():
 assert p.sha(protocol)==a.protocol_sha256 and p.sha(Path(__file__))==plan['controller_sha256']
 assert p.sha(RUNTIME/pv.MANIFEST)==plan['runtime_manifest_sha256'] and p.tool_manifest()==plan['tools']
 assert p.tree_hash(source.parent)==plan['source_hashes']
 for name,pin in plan['prerequisite_sha256'].items():assert p.sha(Path(name))==pin,name
fresh();assert not os.path.lexists(base) and not os.path.lexists(out)
frozen=f.read_json(Path(plan['wait_for_eighteen_children']))
rows=[row for arms in frozen['protocols'].values() for row in arms.values()];assert len(rows)==18
assert all((Path(row['path']).parent/'enclosure/result.json').is_file() for row in rows),'wait for all18 terminal receipts; no concurrent control'
assert shutil.disk_usage(ROOT).free>=3*1024**3
fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
with os.fdopen(fd,'r+') as lane:
 info=os.fstat(lane.fileno());assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_uid==os.getuid()
 fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
 fresh();base.mkdir(mode=0o700);owner={};h.capture_destination(owner,base)
 p.save_json(base/'settings.json',plan['settings']);assert p.sha(base/'settings.json')==plan['settings_sha256']
 p.save_json(base/'protocol.json',plan);captured_protocol=p.sha(base/'protocol.json')
 process=run(['/usr/bin/time','-lp',str(ROOT/'.venv/bin/python'),'-B',str(encloser),'--protocol',str(base/'protocol.json')],
  cwd=base,env=gui.child_environment(),log=base/'complete-command-and-time.log',timeout=270,
  max_log_bytes=256*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=4*1024**2)
 p.save_json(base/'process.json',process)
 record=dict(schema=1,kind='one-normal-Improve90-natural-time-control-v1',accepted=False,project_complete=False,actual_GUI=False,human_review=False,
  protocol_sha256=a.protocol_sha256,executed_protocol_sha256=captured_protocol,controller_sha256=plan['controller_sha256'],
  process_sha256=p.sha(base/'process.json'),complete_log_sha256=p.sha(base/'complete-command-and-time.log'),
  safe_best_delivery=False,natural_time_admission_stop_supported=False,literal_work_limit_observed=False,strict_expiry_and_reserved_return_passed=False,
  interpretation='One exposed EEPROM/software intent control only; no exact-incumbent, no-better, electrical, GUI, human or general speed claim. Failed/inconclusive evidence is retained without retry.')
 witnesses={}
 def bound(path):
  path=Path(path);pin=p.sha(path);data=f.read_json(path);assert p.sha(path)==pin
  witnesses[str(path)]=pin;return data
 try:
  fresh();assert h.owned_destination(owner)==base and p.sha(base/'protocol.json')==captured_protocol
  execution_path=base/'execution.json';execution=bound(execution_path);record['execution_sha256']=witnesses[str(execution_path)]
  child_path=Path(execution['child_receipt']);child=bound(child_path);assert witnesses[str(child_path)]==execution['child_sha256']
  work=Path(child['workspace']);route_path=work/'route/result.json';route=bound(route_path)
  record.update(child_receipt=str(child_path),child_sha256=witnesses[str(child_path)],route_receipt=str(route_path),route_sha256=witnesses[str(route_path)])
  assert route['proposal_policy']=='single' and route['budget_seconds']==route['cpu_budget_seconds']==90
  assert route['source_hashes']==plan['source_hashes'] and route['tools']==plan['tools']
  trials=[bound(row['receipt']) for row in route['trials']]
  trial_pins={row['receipt']:witnesses[row['receipt']] for row in route['trials']}
  checkpoints=[bound(work/'route'/name) for name in route['checkpoints']]
  completed=[row for row in checkpoints if row['kind']=='trial_completed']
  assert trials and completed and len(trials)==len(completed)
  original=sx.read(source);protected=p.protected_for_record(route,original);assert len(protected)==0
  best=Path(route['best_observed_candidate']);best_pin=p.sha(best)
  attempted={tuple(sorted(row['proposal']['route_ids'])) for row in trials}
  pending=[q for q in s.proposals(sx.read(best),s.zone_net_ids(original),protected,False) if tuple(sorted(q['route_ids'])) not in attempted]
  # Whole-net attempts do not count as attempts of their individual children.
  finalization=route['finalization_started_elapsed_seconds'];last=trials[-1];last_checkpoint=completed[-1]
  observed=max(finalization,last['finished_observed_cpu_seconds'],last_checkpoint['observed_cpu_seconds'])
  assert all(type(n) in (int,float) and math.isfinite(n) and n>=0 for n in (finalization,observed))
  under_trial_cap=0<len(trials)<s.MAX_TRIALS==32
  admission_stop=under_trial_cap and bool(pending) and observed>=90-s.NATIVE_FINAL_RESERVE_SECONDS-s.MIN_TRIAL_SECONDS
  literal=admission_stop and observed>=90-s.NATIVE_FINAL_RESERVE_SECONDS
  stage=[row for row in child['processes'] if row['stage']=='route'];assert len(stage)==1
  complete_route_return=stage[0]['process']['wall_seconds'];tail=complete_route_return-finalization
  safe=bool(execution['controls_passed'] and execution['workflow_delivered'] and child['workflow_delivered']
   and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'])
  record.update(safe_best_delivery=safe,natural_time_admission_stop_supported=admission_stop,literal_work_limit_observed=literal,
   strict_expiry_and_reserved_return_passed=bool(safe and literal and 0<=tail<=25 and complete_route_return<=90),
   trial_count=len(trials),improvements=route['improvements'],pending_unattempted_singletons=len(pending),
   finalization_started_elapsed_seconds=finalization,last_trial_observed_cpu_seconds=last['finished_observed_cpu_seconds'],
   last_trial_checkpoint_observed_cpu_seconds=last_checkpoint['observed_cpu_seconds'],
   complete_route_CLI_wall_seconds=complete_route_return,complete_route_return_tail_seconds=tail,
   trial_receipt_sha256=trial_pins,checkpoint_sha256={name:witnesses[str(work/'route'/name)] for name in route['checkpoints']},
   best_observed_candidate_sha256=best_pin,Native_counts=execution['Native_counts'],protected_count=execution['protected_count'],
   own_proof_authority='Unchanged qualifier performed current full parent/export readers and fresh background export inspection; this postprocessing performs no Native or replacement acceptance.')
  assert p.sha(best)==best_pin
  for name,pin in trial_pins.items():assert p.sha(Path(name))==pin
  assert p.sha(route_path)==record['route_sha256'] and p.sha(child_path)==record['child_sha256'] and p.sha(execution_path)==record['execution_sha256']
 except (Exception,KeyboardInterrupt) as exc:record.update(strict_expiry_and_reserved_return_passed=False,error=type(exc).__name__+': '+str(exc))
 try:
  fresh();assert h.owned_destination(owner)==base and p.sha(base/'protocol.json')==captured_protocol
  for name,pin in witnesses.items():assert p.sha(Path(name))==pin
 except BaseException as exc:record.update(strict_expiry_and_reserved_return_passed=False,freshness_error=type(exc).__name__+': '+str(exc))
 record.update(sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,
  complete_external_time_required=True,cost_scope='Combined enclosure time includes all nested six-stage children; wrapper exit is additional. Never add overlapping samples. Existing240s acceptance/255s child/270s dispatch caps retained; outer acceptance requires complete external wall/fullCPU<=300. CPU/RSS/storage are existing sampled guards, not OS quotas.')
 if max(record['sampled_wall_seconds'],record['sampled_full_CPU_seconds'])>299:record['strict_expiry_and_reserved_return_passed']=False
 p.save_json(base/'control-result.json',record)
 try:
  fresh();assert h.owned_destination(owner)==base and p.sha(base/'protocol.json')==captured_protocol
  for name,pin in witnesses.items():assert p.sha(Path(name))==pin
 except BaseException as exc:
  record.update(strict_expiry_and_reserved_return_passed=False,publication_freshness_error=type(exc).__name__+': '+str(exc));p.save_json(base/'control-result.json',record)
 print(json.dumps({k:record[k] for k in ('safe_best_delivery','natural_time_admission_stop_supported','literal_work_limit_observed','strict_expiry_and_reserved_return_passed')}))
 raise SystemExit(0 if record['strict_expiry_and_reserved_return_passed'] else 2)
