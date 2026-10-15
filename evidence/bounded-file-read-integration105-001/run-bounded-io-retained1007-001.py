"""Measure the real shared checker on frozen Native bytes; no Native rerun."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,os,subprocess
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from experiments.native_schematic_transport_v1 import readback as old
O=R/'.runs/bounded-io-retained1007-001';PROOF=R/'.runs/kicad-1007-bundle-qualification-001/result.json'

def authority():
 if p.sha(PROOF)!='26564ecd90268e463760270902d302445d9b0e6859105d3ed06e5976a8989c73':raise p.Rejected('fixed caller authority changed')
 return p.ExperimentalNativeToolchain.from_record(f.read_json(PROOF)['experimental_native_toolchain'])

def worker():
 plan=f.read_json(O/'plan.json');nt=authority();out=O/'reader';out.mkdir();owner={};h.capture_destination(owner,out)
 real_run,real_popen=subprocess.run,subprocess.Popen;active=False
 safe=['git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','rev-parse','HEAD']
 def readonly(argv,*args,**kw):
  nonlocal active
  assert argv==['git','rev-parse','HEAD'] and not args and set(kw)=={'cwd','capture_output','text','check'} and Path(kw['cwd'])==R and all(kw[k] is True for k in ['capture_output','text','check']) and not active
  active=True
  try:return real_run(safe,**kw)
  finally:active=False
 def popen(argv,*args,**kw):
  assert active and argv==safe and not args and Path(kw['cwd'])==R
  return real_popen(argv,**kw)
 subprocess.run=readonly;subprocess.Popen=popen
 prior,root,archive=old.reference();tools=p.tool_manifest(native_toolchain=nt)
 assert tools==plan['tools'] and p.sha(Path(__file__))==plan['controller_sha256']
 data=f.read_json(archive);checked=p.check_result(archive,native_toolchain=nt,experimental_schematic_parity=True)
 refused=[]
 for path,options in [(archive,{}),(archive.parent/'result.json',dict(native_toolchain=nt,experimental_schematic_parity=True))]:
  try:p.check_result(path,**options)
  except p.Rejected:refused.append(True)
 assert refused==[True,True] and checked['current'] is True
 record=dict(schema=1,accepted=False,passed=True,status='completed',new_native_execution=False,new_jvm_execution=False,
  checker_tools=tools,shared_readback=checked,archived_receipt_sha256=p.sha(archive),candidate_sha256=data['candidate_sha256'],
  default_and_invalidated_refused=True,completed_material=f.evidence_inventory(out),
  scope='New performance measurement of unchanged retained002 Native evidence under the actual shared observed-size IO helper. Original failures/producer states unchanged; no Native/JVM/test/network, no current installation or routing gain claim.')
 def remaining():return min(28-(time.monotonic()-START),28-(cpu()-CPU0))
 def stable():
  h.owned_destination(owner);old.reference()
  if p.tool_manifest(native_toolchain=nt)!=tools or f.evidence_inventory(out)!=record['completed_material']:raise p.Rejected('current checker/material changed')
  p.check_experimental_local_settings(archive.parent,data,nt)
 def account():
  record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
  if remaining()<=0:record.update(status='budget_exceeded')
  record['passed']=record['status']=='completed'
 f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
 saved=f.read_json(out/'result.json');print(json.dumps({k:saved[k] for k in ['passed','status','wall_seconds','full_cpu_seconds']}));return 0 if saved['passed'] and saved['status']=='completed' else 2

def outer():
 O.mkdir();owner={};h.capture_destination(owner,O);nt=authority();old.reference();tools=p.tool_manifest(native_toolchain=nt)
 plan=dict(tools=tools,controller_sha256=p.sha(Path(__file__)),limits=dict(whole_wall_full_cpu_seconds=60,child_seconds=30,group_rss_bytes=1024**3,scratch_bytes=16*1024**2,log_bytes=64*1024))
 p.save_json(O/'plan.json',plan);planpin=p.sha(O/'plan.json')
 process=run([*f.SANDBOX,str(R/'.venv/bin/python'),'-B',str(Path(__file__)),'--worker'],cwd=O,log=O/'command.log',timeout=max(.001,min(30,58-(time.monotonic()-START))),max_log_bytes=64*1024,max_workdir_bytes=16*1024**2,max_group_rss_bytes=1024**3)
 path=O/'reader/result.json';child=f.read_json(path) if path.exists() else None;childpin=p.sha(path) if child else None;logpin=p.sha(O/'command.log')
 if child and f.evidence_inventory(path.parent)!=child['completed_material']:raise p.Rejected('postchild material differs')
 good=bool(child and child.get('passed') is True and child.get('status')=='completed' and child.get('checker_tools')==tools and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
 record=dict(schema=1,accepted=False,passed=good,status='completed' if good else 'failed',tools=tools,process=process,child=child,child_sha256=childpin,plan_sha256=planpin,limits=plan['limits'],new_native_execution=False,new_jvm_execution=False)
 def remaining():return min(58-(time.monotonic()-START),58-(cpu()-CPU0))
 def stable():
  h.owned_destination(owner);old.reference()
  if p.tool_manifest(native_toolchain=nt)!=tools or p.sha(O/'plan.json')!=planpin or p.sha(Path(__file__))!=plan['controller_sha256'] or p.sha(O/'command.log')!=logpin:raise p.Rejected('measurement authority/material changed')
  if child and (p.sha(path)!=childpin or f.canonical(f.read_json(path))!=f.canonical(child) or f.evidence_inventory(path.parent)!=child['completed_material']):raise p.Rejected('published child changed')
  if good:
   _,_,archive=old.reference();p.check_experimental_local_settings(archive.parent,f.read_json(archive),nt)
 def account():
  record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
  if remaining()<=0:record.update(status='budget_exceeded')
  record['passed']=good and record['status']=='completed'
 f.publish(O,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
 saved=f.read_json(O/'result.json');print(json.dumps({k:saved[k] for k in ['passed','status','wall_seconds','full_cpu_seconds']}));return 0 if saved['passed'] and saved['status']=='completed' else 2

if __name__=='__main__':raise SystemExit(worker() if sys.argv[1:]==['--worker'] else outer())
