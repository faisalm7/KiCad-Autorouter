"""Finite active-session test of existing CliJob.cancel at an owned repair worker."""
from pathlib import Path
import argparse,json,sys,time,resource,threading,importlib.util
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];ap=argparse.ArgumentParser();ap.add_argument('--runtime',required=True);ap.add_argument('--protocol',required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args();runtime=Path(a.runtime);sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,gui,floor_route as f
assert c.ROOT==runtime and c.NATIVE_VERSION=='10.0.7' and Path(sys.prefix).resolve()==runtime/'.venv'
protocol=Path(a.protocol);assert p.sha(protocol)==a.protocol_sha256;plan=f.read_json(protocol);assert p.sha(Path(__file__))==plan['controller_sha256'];observer_path=ROOT/'.runs/owned-child-path-observer-001.py';assert p.sha(observer_path)==plan['observer_sha256'];spec=importlib.util.spec_from_file_location('owned_child_path_observer',observer_path);observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer);source=Path(plan['source']);out=Path(plan['output']);assert p.tool_manifest()==plan['tools'] and p.tree_hash(source.parent)==plan['source_hashes'];p.check_storage(active_root=out);out.mkdir();route=out/'route';job=gui.CliJob();stop=threading.Event();observed={};calls=0
# No monitor survives this finite test: stop/join below precede publication.
def monitor():
 global calls
 log=route/'recovery/trial-01/refill-drc.log'
 try:
  while not stop.wait(.05) and time.monotonic()-START<190:
   if not log.exists():continue
   if calls>=20:break
   calls+=1
   with job._lock:parent=job.process.pid if job.process is not None else None
   if parent is None:continue
   if (route/'recovery/trial-01/refill-drc-process.json').exists():break
   rows=observer.owned_paths(parent)
   for row in rows:
    if row['executable']==str(c.CLI.resolve()):
     observed.update(**row,phase='repair/trial-01/refill-drc',elapsed_wall_seconds=time.monotonic()-START)
     job.cancel();observed['cancel_requested_once']=True;return
 except BaseException as exc:observed['monitor_error']=type(exc).__name__+': '+str(exc)
thread=threading.Thread(target=monitor,name='bounded-owned-repair-cancel');thread.start();process=None;error=None
try:
 process=job.run([str(runtime/'.venv/bin/python'),'-B','-m','autorouter','recover',str(source),'--seconds','180','--output',str(route)],out/'recover.log',timeout=200)
except BaseException as exc:error=type(exc).__name__+': '+str(exc)
finally:stop.set();thread.join(5)
assert not thread.is_alive(),'finite monitor failed to join'
receipt=route/'result.json';r=f.read_json(receipt) if receipt.is_file() else None;repairpath=route/'recovery/repair.json';repair=f.read_json(repairpath) if repairpath.is_file() else None
steps=r.get('steps',[]) if r else [];cancelled=[s for s in steps if s.get('status')=='cancelled'];matched=[s for s in cancelled if s.get('name')=='refill-drc' and s.get('cwd')==str(route/'recovery/trial-01')];clean=bool(steps and all(s.get('cleanup_complete') is True for s in steps));stable=p.tool_manifest()==plan['tools'] and p.tree_hash(source.parent)==plan['source_hashes'] and p.sha(protocol)==a.protocol_sha256
passed=bool(observed.get('cancel_requested_once') and process is not None and process['cancel_requested'] is True and process['exit_code']==2 and r is not None and r.get('accepted') is False and r.get('status')=='cancelled' and len(matched)==1 and matched[0].get('pid')==observed.get('pid') and clean and stable and not (out/'export').exists() and repair is not None and repair.get('validation_passed') is False and repair.get('candidate') is None and max(time.monotonic()-START,cpu()-CPU0)+2<=220)
report=dict(schema=1,kind='actual-integrated-owned-repair-Native-cancellation',accepted=False,project_complete=False,controls_passed=passed,actual_GUI=False,human_review=False,protocol_sha256=a.protocol_sha256,process=process,observation=observed,metadata_query_calls=calls,monitor_joined=not thread.is_alive(),error=error,route_receipt=str(receipt),route_receipt_sha256=p.sha(receipt) if r else None,route_status=r.get('status') if r else None,route_accepted=r.get('accepted') if r else None,actual_cancelled_steps=cancelled,all_steps_cleanup_complete=clean,source_originals_unchanged=stable,repair_status=repair.get('status') if repair else None,repair_validation_passed=repair.get('validation_passed') if repair else None,sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True,scope='One finite active-session test. Existing CliJob.cancel sends SIGINT to its current CLI; existing Native runner owns child termination/reaping. Only an owned livechild CLI executable at the incomplete trial-refill log and the exact matching cancelled-step PID qualifies. No Nativepause, stalePIDkill, externaldaemon, backgroundmonitoraftertest, allphase/SIGINT-only/permanentdescendant/human/GUI/benchmarkclaim.')
p.save_json(out/'result.json',report);print(json.dumps({k:report[k] for k in ('controls_passed','route_status','repair_status','sampled_wall_seconds','sampled_full_CPU_seconds')}));raise SystemExit(0 if passed else 2)
