"""Bounded same-BOARD metadata observation; no production support admission."""
import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,signal,stat,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
DRAFT=ROOT/'.runs/inner-pour-four-layer-draft-001';BASE=ROOT/'.runs/inner-pour-metadata-native-001'
CASES=('explicit_net0','explicit_net0_island0','omitted_net_island0')
MANIFEST='4761aa22478dae733c14328c099c36273eecf0b319f29266185393f3b202e7c9'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module

def native(output,source):
 # Explicitly load only the frozen instrumentation. The current product's
 # observer is two-layer-only; this is never a production validator callback.
 from autorouter import placement_clearance as io
 before=io.inventory(source.parent);record=dict(schema=1,observation_complete=False,qualified=False,accepted=False,input_hashes_before=before)
 try:
  import autorouter
  modules={}
  for name in ('placement_transform','floor_context','pour_rule_area'):
   path=DRAFT/'patch-tree/autorouter'/(name+'.py');module=load('autorouter.'+name,path);setattr(autorouter,name,module);modules[str(path)]=sha(path)
  helper=load('frozen_pour_metadata_observer',DRAFT/'observe_semantics.py');modules[str(DRAFT/'observe_semantics.py')]=sha(DRAFT/'observe_semantics.py')
  import pcbnew
  if pcbnew.GetBuildVersion()!='10.0.0':raise ValueError('pinned native version differs')
  captured=(sha(source),sha(source.with_suffix('.kicad_pro')))
  board=pcbnew.LoadBoard(str(source))
  if not board:raise ValueError('native load failed')
  observed=helper.observe(board,source,captured,pcbnew)
  if modules!={name:sha(name)for name in modules}:raise ValueError('instrumentation changed during same-board observation')
  record.update(observation_complete=True,observation=observed,instrumentation_sha256=modules,
                actual_native_python=str(Path(sys.executable).resolve()),loaded_pcbnew=str(Path(pcbnew._pcbnew.__file__).resolve()),loaded_pcbnew_sha256=sha(pcbnew._pcbnew.__file__))
 except Exception as exc:
  record['error']=type(exc).__name__+': '+str(exc);traceback.print_exc()
 record['input_hashes_after']=io.inventory(source.parent)
 if record['input_hashes_after']!=before:record.update(observation_complete=False,error='Native modified input')
 with output.open('x')as stream:json.dump(record,stream,indent=2,allow_nan=False);stream.write('\n')
 print(json.dumps({'observation_complete':record['observation_complete'],'qualified':False,'error':record.get('error')}))
 return 0 if record['observation_complete']else 2

if len(sys.argv)>1 and sys.argv[1]=='--native':
 raise SystemExit(native(Path(sys.argv[2]),Path(sys.argv[3])))

from autorouter import pipeline as p,floor_route as f,config as c,handoff as h,local_settings as ls,placement_clearance as io,provenance as pv
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as existing
from experiments.placement_handoff_native_v1.driver import copy_bytes
LIMITS=dict(wall_seconds=30,full_CPU_seconds=30,worker_timeout_seconds=27,aggregate_bytes=20*1024**2,group_RSS_bytes=2*1024**3,log_bytes=256*1024,finalization_reserve_seconds=2)
def draft_current():
 if sha(DRAFT/'manifest.json')!=MANIFEST:raise p.Rejected('frozen draft manifest changed')
 manifest=f.read_json(DRAFT/'manifest.json')
 if any(sha(DRAFT/name)!=row['sha256']or(DRAFT/name).stat().st_size!=row['bytes']for name,row in manifest['files'].items()):raise p.Rejected('frozen instrumentation/recipe changed')

def prepare():
 draft_current();BASE.mkdir();(BASE/'sources').mkdir();recipe=load('frozen_owned_pour_recipe',DRAFT/'owned_control.py');sources={}
 for name in CASES:
  path=BASE/'sources'/name;copy_bytes(recipe.files(name),path);sources[name]=p.tree_hash(path)
 plan=dict(schema=1,kind='three-case-four-copper-metadata-only',source_head=pv.git_head(ROOT),tools=p.tool_manifest(),driver_sha256=sha(__file__),draft_manifest_sha256=MANIFEST,cases=list(CASES),sources=sources,stem=recipe.fixture.STEM,limits=LIMITS,qualified=False,accepted=False,save=False,refill=False,export=False,drc=False,routing=False,
           scope='Owned exposed diagnostic; explicit frozen draft instrumentation, same BOARD per source. Getter equivalence is not saved-fill equivalence, native routing acceptance or HFE admission.',preparation_wall_seconds=time.monotonic()-START,preparation_CPU_seconds=cpu()-CPU0)
 p.save_json(BASE/'protocol.json',plan);print(json.dumps({'prepared':True,'protocol_sha256':sha(BASE/'protocol.json'),'native_executed':False}))

def context(plan,pin):
 draft_current()
 if sha(BASE/'protocol.json')!=pin or plan['source_head']!=pv.git_head(ROOT)or plan['tools']!=p.tool_manifest()or plan['driver_sha256']!=sha(__file__)or plan['limits']!=LIMITS or plan['cases']!=list(CASES):raise p.Rejected('frozen metadata-only source/tool/protocol context changed')
 if any(p.tree_hash(BASE/'sources'/name)!=plan['sources'][name]for name in CASES):raise p.Rejected('frozen complete source changed')

def worker(plan,pin):
 context(plan,pin);out=BASE/'execution/worker';out.mkdir();owner={};h.capture_destination(owner,out);rows=[]
 remaining=lambda:min(25-(time.monotonic()-START),25-(cpu()-CPU0))
 for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:(_ for _ in()).throw(KeyboardInterrupt()))
 try:
  for name in CASES:
   context(plan,pin)
   if remaining()<=1:rows.append(dict(case=name,observation_complete=False,status='not_attempted_budget'));continue
   job=existing.BoundJob(out/name,remaining(),remaining,protect_local_settings=True)
   for key in ('PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'):job.env.pop(key,None)
   copy_bytes(io.inventory(BASE/'sources'/name,contents=True),job.out/'input');source=job.out/'input'/(plan['stem']+'.kicad_pcb');before=p.tree_hash(source.parent)
   copy_bytes({Path(n).name:io.read_bytes(ROOT/n,1024**2)for n in plan['tools']['implementation_sha256']},job.out/'code')
   output=job.out/'metadata.json';argv=[c.PYTHON,'-B',Path(__file__),'--native',output,source]
   process=ls.protected_step(job,'metadata-read',argv,allowed=(0,2));binding=dict(input=str(source),before=before,saved=False,local_settings_policy=ls.JOB_POLICY)
   p.save_json(job.out/'metadata-binding.json',binding);ls.check_event(job.out,binding,process)
   raw=f.read_json(output);complete=raw.get('observation_complete')is True and process['exit_code']==0
   if before!=plan['sources'][name]or p.tree_hash(source.parent)!=before or raw['input_hashes_before']!=before or raw['input_hashes_after']!=before:raise p.Rejected('copied/source project changed')
   if complete:
    f.process_check(job.out,{'steps':job.steps},'metadata-read',[*f.SANDBOX,*map(str,argv)])
    if raw['qualified']is not False or raw['accepted']is not False or Path(raw['loaded_pcbnew']).resolve()!=c.PCBNEW.resolve()or raw['loaded_pcbnew_sha256']!=sha(c.PCBNEW):raise p.Rejected('native module/diagnostic-only binding differs')
   rows.append(dict(case=name,observation_complete=complete,raw=raw,report=str(output),report_sha256=sha(output),process=process,binding=binding))
  completed=len(rows)==3 and all(row['observation_complete']for row in rows)
  result=dict(schema=1,qualified=False,accepted=False,status='completed'if completed else'incomplete',observation_complete=completed,protocol_sha256=pin,source_head=plan['source_head'],cases=rows,save=False,refill=False,export=False,drc=False,routing=False)
  if completed:
   obs=[row['raw']['observation']for row in rows]
   projection=lambda item:[{k:row[k]for k in('uuid','native_netcode','native_netname','native_island_mode')}for row in item['areas']]
   result['hypotheses']=dict(all_native_area_contexts_equal=obs[0]['area_context']==obs[1]['area_context']==obs[2]['area_context'],explicit_and_omitted_island0_metadata_equal=projection(obs[1])==projection(obs[2]),default_and_explicit_island0_metadata_equal=projection(obs[0])==projection(obs[1]),all_areas_native_NoNet=all(row['native_netcode']==0 and row['native_netname']==''for item in obs for row in item['areas']))
 except (Exception,KeyboardInterrupt)as exc:
  result=dict(schema=1,qualified=False,accepted=False,status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',observation_complete=False,protocol_sha256=pin,cases=rows,error=type(exc).__name__+': '+str(exc))
 witness=existing.material(out);result['completed_evidence']=witness
 def stable():
  h.owned_destination(owner);context(plan,pin)
  if existing.material(out)!=witness:raise p.Rejected('completed metadata evidence changed')
  for row in rows:
   if 'report'in row:
    if sha(row['report'])!=row['report_sha256']:raise p.Rejected('native metadata report changed')
    ls.check_event(Path(row['report']).parent,row['binding'],row['process'])
 def account():
  result.update(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
  if remaining()<=0:result.update(status='budget_exceeded',observation_complete=False)
 f.publish(out,result,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
 print(json.dumps({k:result.get(k)for k in('status','observation_complete','hypotheses','error','wall_seconds','full_CPU_seconds')}))
 return 0 if result['observation_complete']else 2

def execute(plan,pin):
 context(plan,pin);out=BASE/'execution';out.mkdir()
 fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
 with os.fdopen(fd,'r+')as lock:
  info=os.fstat(lock.fileno())
  if not stat.S_ISREG(info.st_mode)or info.st_nlink!=1:raise p.Rejected('ordinary shared quality lane required')
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',__file__,'--worker',pin],cwd=out,log=out/'command.log',timeout=LIMITS['worker_timeout_seconds'],max_log_bytes=LIMITS['log_bytes'],max_workdir_bytes=LIMITS['aggregate_bytes'],max_group_rss_bytes=LIMITS['group_RSS_bytes'])
  child=out/'worker/result.json';data=f.read_json(child)if child.exists()else None
  complete=bool(data and data.get('observation_complete')is True and process['status']=='success'and process['exit_code']==0 and process['cleanup_complete']and not process['log_truncated'])
  context(plan,pin);record=dict(schema=1,qualified=False,accepted=False,observation_complete=complete,process=process,child_sha256=sha(child)if child.exists()else None,protocol_sha256=pin,wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
  if max(record['wall_seconds'],record['full_CPU_seconds'])>30:record['observation_complete']=False
  p.save_json(out/'execution.json',record);print(json.dumps({'observation_complete':record['observation_complete'],'status':process['status'],'exit_code':process['exit_code']}))
  return 0 if record['observation_complete']else 2

if __name__=='__main__':
 if sys.argv[1]=='--prepare':prepare()
 else:
  plan=f.read_json(BASE/'protocol.json');pin=sha(BASE/'protocol.json')
  if sys.argv[1]=='--worker':
   if sys.argv[2]!=pin:raise p.Rejected('explicit current protocol pin required')
   raise SystemExit(worker(plan,pin))
  if sys.argv[1]!='--run':raise p.Rejected('fixed prepare/run/worker mode required')
  raise SystemExit(execute(plan,pin))
