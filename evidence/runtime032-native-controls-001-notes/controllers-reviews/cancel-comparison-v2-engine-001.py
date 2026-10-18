"""Finite active-session cancellation of one v2 both/tuned/via_low420 owned engine.

Existing process/publication limits remain unchanged. No GUI/all-phase or
SIGINT-only claim; execute only through a separately frozen shared enclosure.
"""
from pathlib import Path
import argparse,json,sys,time,resource,threading,importlib.util,math
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];ap=argparse.ArgumentParser();ap.add_argument('--runtime',required=True);ap.add_argument('--protocol',required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args();runtime=Path(a.runtime);sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,gui,floor_route as f,handoff as h,comparison as cmp,provenance as pv
assert c.ROOT==runtime and c.NATIVE_VERSION=='10.0.7' and Path(sys.prefix).resolve()==runtime/'.venv'
assert Path(sys.executable)==runtime/'.venv/bin/python'
protocol=Path(a.protocol);assert p.sha(protocol)==a.protocol_sha256;plan=f.read_json(protocol);assert p.sha(Path(__file__))==plan['controller_sha256'];observer_path=ROOT/'.runs/owned-child-path-observer-001.py';assert p.sha(observer_path)==plan['observer_sha256'];spec=importlib.util.spec_from_file_location('owned_child_path_observer',observer_path);observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer);source=Path(plan['source']);out=Path(plan['output']);assert p.sha(Path(plan['child']))==plan['child_sha256'] and p.sha(Path(plan['child_protocol']))==plan['child_protocol_sha256'];assert p.tool_manifest()==plan['tools'] and p.tree_hash(source.parent)==plan['source_hashes'] and p.sha(runtime/pv.MANIFEST)==plan['runtime_manifest_sha256'];p.check_storage(active_root=out);out.mkdir();owner={};h.capture_destination(owner,out);route=Path(plan['route_parent'])/'route';job=gui.CliJob();stop=threading.Event();observed={};calls=0
# No monitor survives this finite test: stop/join below precede publication.
def monitor():
 global calls
 log=route/'engine.log'
 try:
  while not stop.wait(.05) and time.monotonic()-START<190:
   if not log.exists():continue
   if calls>=20:break
   calls+=1
   with job._lock:parent=job.process.pid if job.process is not None else None
   if parent is None:continue
   if (route/'engine-process.json').exists():break
   rows=observer.owned_paths(parent)
   for row in rows:
    if row['executable']==str(c.JAVA.resolve()):
     observed.update(**row,phase='engine-launch-or-running',elapsed_wall_seconds=time.monotonic()-START)
     job.cancel();observed['cancel_requested_once']=True;return
 except BaseException as exc:observed['monitor_error']=type(exc).__name__+': '+str(exc)
assert plan['runtime']==str(runtime) and plan['source_head']==plan['tools']['git_head']
assert p.sha(runtime/pv.MANIFEST)==plan['runtime_manifest_sha256']
assert cmp.POLICY==plan['comparison_route_policy']=='selected-native7-fixed-comparison-v2'
assert cmp.DELIVERY_POLICY==plan['comparison_delivery_policy']=='selected-native7-fixed-comparison-delivery-v2'
assert plan['kind']=='actual-owned-comparison-v2-engine-cancellation-functional-control'
assert plan['whole_wall_full_cpu_seconds']==230
child_plan=f.read_json(Path(plan['child_protocol']))
assert child_plan['source']==str(source) and child_plan['source_hashes']==plan['source_hashes'] and child_plan['tools']==plan['tools']
assert child_plan['runtime']==str(runtime) and child_plan['output']==plan['route_parent'] and child_plan['mode']=='cancel'
assert child_plan['profile']==plan['profile']=='tuned' and child_plan['route_seconds']==plan['route_seconds']==420
assert child_plan['adapter']==plan['adapter']=='both' and child_plan['scoring_variant']==plan['scoring_variant']=='via_low'
assert child_plan['kind']=='native7-comparison-v2-route-functional-v1' and child_plan['whole_wall_full_cpu_seconds']==220
assert child_plan['child_sha256']==plan['child_sha256']
for field in ('source_head','runtime_manifest_sha256','comparison_route_policy','comparison_delivery_policy'):
 assert child_plan[field]==plan[field]
assert Path(plan['route_parent']).parent==runtime/'.runs'
thread=threading.Thread(target=monitor,name='bounded-owned-engine-cancel');thread.start();process=None;error=None
try:
 process=job.run([str(runtime/'.venv/bin/python'),'-B',plan['child'],'--protocol',plan['child_protocol'],'--protocol-sha256',plan['child_protocol_sha256']],out/'route-child.log',timeout=200)
except BaseException as exc:error=type(exc).__name__+': '+str(exc)
finally:stop.set();thread.join(5)
assert not thread.is_alive(),'finite monitor failed to join'
receipt=route/'result.json';r=f.read_json(receipt) if receipt.is_file() else None;repair=None
steps=r.get('steps',[]) if r else [];cancelled=[s for s in steps if s.get('status')=='cancelled'];matched=[s for s in cancelled if s.get('name')=='engine' and s.get('cwd')==str(route)];clean=bool(steps and all(s.get('cleanup_complete') is True for s in steps));stable=p.tool_manifest()==plan['tools'] and p.tree_hash(source.parent)==plan['source_hashes'] and p.sha(protocol)==a.protocol_sha256
authority=cmp.Context(source,route,'tuned',420,plan['tools'],plan['source_hashes'],adapter=plan['adapter'],scoring_variant=plan['scoring_variant'])
record_bound=bool(r is not None and r.get('source')==str(source) and r.get('source_hashes')==plan['source_hashes'] and r.get('tools')==plan['tools'] and r.get('engine_profile')==plan['profile'] and r.get('adapter')==plan['adapter'] and r.get('scoring_variant')==plan['scoring_variant'] and r.get('budget_seconds')==r.get('cpu_budget_seconds')==420 and cmp.check_record(route,r,authority))
journal_bound=bool(len(matched)==1 and (route/'engine-process.json').is_file() and f.read_json(route/'engine-process.json')==matched[0])
def cancelled_profile_check(data):
 if not isinstance(data,dict) or type(data.get('engine_budget')) is not dict:return False
 if (data.get('adapter'),data.get('engine_profile'),data.get('scoring_variant'))!=(plan['adapter'],plan['profile'],plan['scoring_variant']):return False
 budget=data['engine_budget'];assigned=budget.get('remaining_outer_wall_seconds_at_assignment')
 if type(assigned) not in (int,float) or not math.isfinite(assigned) or not 0<assigned<=420:return False
 strict=p.netclass_policy(source) is not None or p.minimum_width_guard(source,plan['adapter']) is not None
 try:expected=p.engine_profile_settings(plan['profile'],assigned,strict_class_targets=strict,scoring_variant=plan['scoring_variant'])
 except p.Rejected:return False
 expected.update(outer_task_wall_budget_seconds=420,outer_task_cpu_budget_seconds=420)
 workers=[step for step in data.get('steps',[]) if step.get('name')=='engine']
 if budget!=expected or len(workers)!=1:return False
 worker=workers[0]
 return (worker.get('status')=='cancelled' and type(worker.get('exit_code')) is int and worker['exit_code']!=0
     and worker.get('cleanup_complete') is True and worker.get('cwd')==str(route)
     and type(worker.get('pid')) is int and worker['pid']>0 and worker['pid']==observed.get('pid')
     and worker.get('argv')==p.engine_argv(route,expected['argv'],profile=plan['profile'])
     and (route/'engine-process.json').is_file() and f.read_json(route/'engine-process.json')==worker)
profile_bound=bool(record_bound and journal_bound and cancelled_profile_check(r))
passed=bool(record_bound and journal_bound and profile_bound and observed.get('cancel_requested_once') and process is not None and process['cancel_requested'] is True and process['exit_code']==2 and r is not None and r.get('accepted') is False and r.get('status')=='cancelled' and len(matched)==1 and matched[0].get('pid')==observed.get('pid') and clean and stable and not (out/'export').exists() and r.get('production_admitted') is False and not (Path(plan['route_parent'])/'export').exists() and max(time.monotonic()-START,cpu()-CPU0)+2<=220)
report=dict(schema=1,kind='actual-v2-scored-comparison-owned-engine-cancellation',accepted=False,production_admitted=False,project_complete=False,controls_passed=passed,actual_GUI=False,human_review=False,protocol_sha256=a.protocol_sha256,process=process,observation=observed,metadata_query_calls=calls,monitor_joined=not thread.is_alive(),error=error,route_receipt=str(receipt),route_receipt_sha256=p.sha(receipt) if r else None,route_status=r.get('status') if r else None,route_accepted=r.get('accepted') if r else None,actual_cancelled_steps=cancelled,all_steps_cleanup_complete=clean,source_originals_unchanged=stable,sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True,scope='One finite active-session test. Existing CliJob.cancel sends SIGINT to its current CLI; existing Native runner owns child termination/reaping. Only an owned livechild Java executable at the incomplete engine log and the exact matching cancelled-step PID qualifies. No Nativepause, stalePIDkill, externaldaemon, backgroundmonitoraftertest, allphase/SIGINT-only/permanentdescendant/human/GUI/benchmarkclaim.')
report.update(caller_context_bound=record_bound,cancelled_engine_journal_bound=journal_bound,cancelled_engine_profile_bound=profile_bound,adapter=plan['adapter'],profile=plan['profile'],scoring_variant=plan['scoring_variant'],route_seconds=plan['route_seconds'],source_head=plan['source_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'])
report['status']='completed' if passed else 'failed'
material=f.evidence_inventory(Path(plan['route_parent']))
assert material.get('route/result.json')==report['route_receipt_sha256']
def remaining():return min(218-(time.monotonic()-START),218-(cpu()-CPU0))
def fresh():
 h.owned_destination(owner)
 assert p.sha(Path(__file__))==plan['controller_sha256'] and p.sha(protocol)==a.protocol_sha256 and p.sha(observer_path)==plan['observer_sha256']
 assert p.sha(Path(plan['child']))==plan['child_sha256'] and p.sha(Path(plan['child_protocol']))==plan['child_protocol_sha256']
 assert p.tool_manifest()==plan['tools'] and p.tree_hash(source.parent)==plan['source_hashes'] and p.sha(runtime/pv.MANIFEST)==plan['runtime_manifest_sha256']
 current=f.read_json(receipt)
 assert cmp.check_record(route,current,authority)
 assert cancelled_profile_check(current)
 assert f.evidence_inventory(Path(plan['route_parent']))==material
 assert p.sha(receipt)==report['route_receipt_sha256']
 assert not thread.is_alive()
def account():
 report.update(sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0)
 if remaining()<=0:report.update(controls_passed=False,status='budget_exceeded')
 if report['status']!='completed':report.update(controls_passed=False,source_originals_unchanged=False)
report['completed_evidence']=material
f.publish(out,report,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=fresh)
print(json.dumps({k:report[k] for k in ('controls_passed','route_status','sampled_wall_seconds','sampled_full_CPU_seconds')}));raise SystemExit(0 if report['controls_passed'] and report['status']=='completed' else 2)
