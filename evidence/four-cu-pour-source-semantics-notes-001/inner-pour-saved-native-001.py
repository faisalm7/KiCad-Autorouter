"""Bounded saved-refill continuation of the frozen three-case metadata probe.
No production admission, engine run, source normalization or final acceptance.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import fcntl,importlib.util,json,os,signal,stat,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('previous_metadata',ROOT/'.runs/inner-pour-metadata-native-001.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from autorouter import pipeline as p,floor_route as f,config as c,handoff as h,local_settings as ls,placement_clearance as io,sexpr as sx
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as existing
from experiments.placement_handoff_native_v1.driver import copy_bytes
BASE=ROOT/'.runs/inner-pour-saved-native-001'
LIMITS=dict(wall_seconds=90,full_CPU_seconds=90,worker_timeout_seconds=85,aggregate_bytes=32*1024**2,group_RSS_bytes=2*1024**3,log_bytes=256*1024,finalization_reserve_seconds=2)
def context(plan,pin):
 m.context(plan['metadata_protocol'],plan['metadata_protocol_sha256'])
 if p.sha(BASE/'protocol.json')!=pin or p.sha(__file__)!=plan['driver_sha256']or plan['limits']!=LIMITS:raise p.Rejected('saved probe context changed')
def prepare():
 prior=f.read_json(m.BASE/'protocol.json');priorpin=p.sha(m.BASE/'protocol.json');m.context(prior,priorpin)
 observed=f.read_json(m.BASE/'execution/worker/result.json')
 if observed.get('observation_complete')is not True or observed.get('protocol_sha256')!=priorpin:raise p.Rejected('completed metadata prerequisite missing')
 BASE.mkdir();plan=dict(schema=1,kind='same-three-cases-saved-refill-observation',driver_sha256=p.sha(__file__),metadata_protocol=prior,metadata_protocol_sha256=priorpin,metadata_result_sha256=p.sha(m.BASE/'execution/worker/result.json'),limits=LIMITS,qualified=False,accepted=False,scope='Saved refill under original rules; reuse immutable prepared sources and same read-only metadata callback. Record transplant failures, do not bypass them. No engine, support admission or HFE claim.',preparation_wall_seconds=time.monotonic()-START,preparation_CPU_seconds=cpu()-CPU0)
 p.save_json(BASE/'protocol.json',plan);print(json.dumps({'prepared':True,'native_executed':False,'protocol_sha256':p.sha(BASE/'protocol.json')}))
def worker(plan,pin):
 context(plan,pin);out=BASE/'execution/worker';out.mkdir();owner={};h.capture_destination(owner,out);rows=[]
 remaining=lambda:min(83-(time.monotonic()-START),83-(cpu()-CPU0))
 for sig in(signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:(_ for _ in()).throw(KeyboardInterrupt()))
 try:
  for name in m.CASES:
   context(plan,pin)
   if remaining()<=2:rows.append(dict(case=name,status='not_attempted_budget'));continue
   row=dict(case=name,observation_complete=False);rows.append(row)
   job=existing.BoundJob(out/name,remaining(),remaining,protect_local_settings=True)
   copy_bytes(io.inventory(m.BASE/'sources'/name,contents=True),job.out/'saved');board=job.out/'saved'/(plan['metadata_protocol']['stem']+'.kicad_pcb');before=p.tree_hash(board.parent);original=sx.read(board)
   copy_bytes({Path(n).name:io.read_bytes(ROOT/n,1024**2)for n in plan['metadata_protocol']['tools']['implementation_sha256']},job.out/'code')
   native=job.drc('saved-refill',board,save=True,schematic_parity=True)
   replay=f.check_drc_stage(job.out,{'steps':job.steps},'saved-refill',board,board,True,before,schematic_parity=True)
   if native!=replay:raise p.Rejected('shared saved-refill replay differs')
   saved=sx.read(board);after=p.tree_hash(board.parent);areas=[z for z in sx.children(saved,'zone')if sx.one(z,'keepout')is not None]
   row.update(native=native,raw_native=existing.raw_stage(job,'saved-refill'),before=before,after=after,saved_board_sha256=p.sha(board),saved_area_metadata=[dict(uuid=sx.one(z,'uuid'),net=sx.one(z,'net'),net_name=sx.one(z,'net_name'),fill=sx.one(z,'fill'))for z in areas],steps=job.steps)
   try:
    transplanted=p.transplant_fill(original,saved)
    row['transplant']=dict(succeeded=True,original_nonfill_preserved=p.immutable(original)==p.immutable(transplanted),original_routes_preserved=p.routes(original)==p.routes(transplanted))
   except Exception as exc:row['transplant']=dict(succeeded=False,error=type(exc).__name__+': '+str(exc))
   output=job.out/'metadata-after-save.json';argv=[c.PYTHON,'-B',m.__file__,'--native',output,board]
   process=ls.protected_step(job,'metadata-after-save',argv,allowed=(0,2));binding=dict(input=str(board),before=after,saved=False,local_settings_policy=ls.JOB_POLICY)
   p.save_json(job.out/'metadata-after-save-binding.json',binding);ls.check_event(job.out,binding,process)
   raw=f.read_json(output);complete=raw.get('observation_complete')is True and process['exit_code']==0
   if p.tree_hash(board.parent)!=after or raw['input_hashes_before']!=after or raw['input_hashes_after']!=after:raise p.Rejected('saved metadata read changed input')
   if complete:
    f.process_check(job.out,{'steps':job.steps},'metadata-after-save',[*f.SANDBOX,*map(str,argv)])
    if raw['qualified']is not False or raw['accepted']is not False or Path(raw['loaded_pcbnew']).resolve()!=c.PCBNEW.resolve()or raw['loaded_pcbnew_sha256']!=p.sha(c.PCBNEW):raise p.Rejected('metadata native binding differs')
   row.update(observation_complete=True,metadata_callback_complete=complete,metadata=raw,metadata_sha256=p.sha(output),metadata_binding=binding,metadata_process=process)
  complete=len(rows)==3 and all(row.get('observation_complete')is True for row in rows)
  result=dict(schema=1,status='completed'if complete else'incomplete',observation_complete=complete,qualified=False,accepted=False,cases=rows,protocol_sha256=pin)
 except(Exception,KeyboardInterrupt)as exc:result=dict(schema=1,status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',observation_complete=False,qualified=False,accepted=False,cases=rows,protocol_sha256=pin,error=type(exc).__name__+': '+str(exc))
 witness=existing.material(out);result['completed_evidence']=witness
 def stable():
  h.owned_destination(owner);context(plan,pin)
  if existing.material(out)!=witness:raise p.Rejected('completed saved evidence changed')
  for row in rows:
   if row.get('observation_complete'):
    jobdir=out/row['case'];board=jobdir/'saved'/(plan['metadata_protocol']['stem']+'.kicad_pcb')
    if f.check_drc_stage(jobdir,{'steps':row['steps']},'saved-refill',board,board,True,row['before'],schematic_parity=True)!=row['native']:raise p.Rejected('late saved Native replay changed')
    if p.sha(jobdir/'metadata-after-save.json')!=row['metadata_sha256']:raise p.Rejected('saved metadata changed')
    ls.check_event(jobdir,row['metadata_binding'],row['metadata_process']);ls.check_normal_policy(jobdir,{'steps':row['steps']},max_bytes=existing.LIMIT,max_files=2048)
 def account():
  result.update(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
  if remaining()<=0:result.update(status='budget_exceeded',observation_complete=False)
 f.publish(out,result,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
 print(json.dumps({k:result.get(k)for k in('status','observation_complete','error','wall_seconds','full_CPU_seconds')}))
 return 0 if result['observation_complete']else 2
def execute(plan,pin):
 context(plan,pin);out=BASE/'execution';out.mkdir();fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
 with os.fdopen(fd,'r+')as lock:
  info=os.fstat(lock.fileno())
  if not stat.S_ISREG(info.st_mode)or info.st_nlink!=1:raise p.Rejected('ordinary shared quality lane required')
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',__file__,'--worker',pin],cwd=out,log=out/'command.log',timeout=85,max_log_bytes=LIMITS['log_bytes'],max_workdir_bytes=LIMITS['aggregate_bytes'],max_group_rss_bytes=LIMITS['group_RSS_bytes'])
  child=out/'worker/result.json';data=f.read_json(child)if child.exists()else None;context(plan,pin)
  complete=bool(data and data.get('observation_complete')is True and process['status']=='success'and process['exit_code']==0 and process['cleanup_complete']and not process['log_truncated'])
  record=dict(schema=1,qualified=False,accepted=False,observation_complete=complete,process=process,child_sha256=p.sha(child)if child.exists()else None,protocol_sha256=pin,wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
  if max(record['wall_seconds'],record['full_CPU_seconds'])>90:record['observation_complete']=False
  p.save_json(out/'execution.json',record);print(json.dumps({'observation_complete':record['observation_complete'],'status':process['status'],'exit_code':process['exit_code']}))
  return 0 if record['observation_complete']else 2
if __name__=='__main__':
 if sys.argv[1]=='--prepare':prepare()
 else:
  plan=f.read_json(BASE/'protocol.json');pin=p.sha(BASE/'protocol.json')
  if sys.argv[1]=='--worker':
   if sys.argv[2]!=pin:raise p.Rejected('explicit saved protocol pin required')
   raise SystemExit(worker(plan,pin))
  if sys.argv[1]!='--run':raise p.Rejected('fixed prepare/run/worker mode required')
  raise SystemExit(execute(plan,pin))
