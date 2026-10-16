"""Actual installed preview/direct-route refusal of the unchanged counterexample."""
import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import json,os,sys,signal
def cancelled(signum,frame):raise KeyboardInterrupt('termination requested')
signal.signal(signal.SIGTERM,cancelled)
ROOT=Path(__file__).resolve().parents[1];RUNTIME=ROOT/'.runs/runtime-directory-008/runtime'
sys.path.insert(0,str(RUNTIME));sys.path.append(str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,config as c,handoff as h,placement_clearance as io
from autorouter.runner import run
from experiments.hfe_original_native_v1.driver import material
assert c.ROOT==RUNTIME and Path(sys.prefix).resolve()==RUNTIME/'.venv'
out=ROOT/'.runs/runtime008-schematic-class-refusal-001';out.mkdir();owner={};h.capture_destination(owner,out)
source=ROOT/'.runs/schematic-class-false-accept-001/source/owned-four-copper-forced-inner.kicad_pcb'
prior=f.read_json(source.parent.parent/'protocol.json');before=p.tree_hash(source.parent);assert before==prior['source_hashes']
tools=p.tool_manifest();driverpin=p.sha(__file__);record=dict(schema=1,status='failed',controls_passed=False,accepted=False,native_executed=None,JVM_executed=None,source_hashes=before,tools=tools,scope='Same four-file owned CRITICAL-SCH/POWER-PCB counterexample; actual installed preview and direct route must refuse before Native/JVM. Previous006 accepted record preserved; no source repair or routing quality claim.')
remaining=lambda:min(28-(time.monotonic()-START),28-(cpu()-CPU0))
env={k:v for k,v in os.environ.items()if k not in('PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN')}
try:
 processes=[]
 for name,tail in (('preview',['preview',str(source)]),('route',['route',str(source),'--output',str(out/'route'),'--seconds','30','--adapter','both'])):
  proc=run([*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B','-m','autorouter',*tail],cwd=RUNTIME,log=out/(name+'.log'),timeout=max(.001,remaining()-2),max_log_bytes=256*1024,max_workdir_bytes=256*1024**2,max_group_rss_bytes=2*1024**3,env=env)
  processes.append(proc);value=f.read_json(out/(name+'.log'))
  assert proc['status']=='nonzero_exit' and proc['exit_code']==2 and proc['cleanup_complete']is True and proc['log_truncated']is False
  reason=value.get('reason',value.get('error',''))
  assert 'schematic class intent not qualified' in reason and 'netclass_flag unsupported' in reason
  record[name]=dict(process=proc,CLI_result=value,log_sha256=p.sha(out/(name+'.log')))
 route=f.read_json(out/'route/result.json')
 assert route['accepted']is False and route['status']=='unsupported' and route['steps']==[] and not(out/'route/candidate').exists()
 assert 'schematic class intent not qualified' in route['reason']
 try:p.check_result(out/'route/result.json')
 except p.Rejected as exc:refusal=str(exc)
 else:raise AssertionError('unsupported route receipt accepted')
 record.update(status='controls_passed',controls_passed=True,native_executed=False,JVM_executed=False,route_receipt_sha256=p.sha(out/'route/result.json'),route_status=route['status'],native_steps=[],current_result_refusal=refusal,source_unchanged=True)
except(Exception,KeyboardInterrupt)as exc:
 record.update(status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',error=type(exc).__name__+': '+str(exc),controls_passed=False)
witness=material(out);record['completed_evidence']=witness
def stable():
 h.owned_destination(owner)
 if p.tree_hash(source.parent)!=before or p.tool_manifest()!=tools or p.sha(__file__)!=driverpin or material(out)!=witness:raise p.Rejected('refusal control source/runtime/evidence changed')
def account():
 record.update(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
 if remaining()<=0:record.update(status='budget_exceeded',controls_passed=False)
 if record['status']!='controls_passed':record['controls_passed']=False
f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
print(json.dumps({k:record.get(k)for k in('status','controls_passed','error','reason','wall_seconds','full_CPU_seconds')}))
raise SystemExit(0 if record['status']=='controls_passed'and record['controls_passed']else 2)
