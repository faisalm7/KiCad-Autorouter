"""One frozen v2 stock/scored API attempt; shared helpers own all routing proof.

This child is run only by a finite shared enclosure. Functional completion,
completed-negative consistency and actual cancellation are distinct controls.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(v.ru_utime+v.ru_stime for v in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,sys,json,math
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,comparison as cmp,handoff as h,review_export as ex,provenance as pv
ap=argparse.ArgumentParser();ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
plan=f.read_json(a.protocol);assert p.sha(a.protocol)==a.protocol_sha256
assert c.ROOT==ROOT and c.NATIVE_VERSION=='10.0.7' and plan['runtime']==str(ROOT) and Path(sys.prefix).resolve()==ROOT/'.venv' and p.sha(Path(__file__))==plan['child_sha256']
assert Path(sys.executable)==ROOT/'.venv/bin/python' and plan['tools']['git_head']==plan['source_head']
assert plan['kind']=='native7-comparison-v2-route-functional-v1'
assert cmp.POLICY==plan['comparison_route_policy']=='selected-native7-fixed-comparison-v2'
assert cmp.DELIVERY_POLICY==plan['comparison_delivery_policy']=='selected-native7-fixed-comparison-delivery-v2'
assert p.sha(ROOT/pv.MANIFEST)==plan['runtime_manifest_sha256'] and p.tool_manifest()==plan['tools']
assert plan['profile'] in ('standard','tuned') and plan['mode'] in ('completed','cancel')
assert (plan['adapter'],plan['profile'],plan['scoring_variant']) in (('none','standard',None),('both','standard',None),('both','tuned',None),*[('both','tuned',s) for s in ('via_default','via_low','via_high')])
assert type(plan['route_seconds']) in (int,float) and math.isfinite(plan['route_seconds']) and 5<=plan['route_seconds']<=900
assert type(plan['whole_wall_full_cpu_seconds']) in (int,float) and math.isfinite(plan['whole_wall_full_cpu_seconds']) and 60<=plan['whole_wall_full_cpu_seconds']<=900
if plan['mode']=='cancel':assert (plan['adapter'],plan['profile'],plan['scoring_variant'],plan['route_seconds'],plan['whole_wall_full_cpu_seconds'])==('both','tuned','via_low',420,220)
source=Path(plan['source']);out=Path(plan['output']);assert not out.exists() and out.parent==ROOT/'.runs' and out.name.startswith(cmp.PREFIX)
assert p.tree_hash(source.parent)==plan['source_hashes'];out.mkdir();owner={};h.capture_destination(owner,out)
authority=cmp.Context(source,out/'route',plan['profile'],plan['route_seconds'],plan['tools'],plan['source_hashes'],adapter=plan['adapter'],scoring_variant=plan['scoring_variant']);ctx=dict(comparison_context=authority)
route=p.route(source,out/'route',seconds=plan['route_seconds'],adapter=plan['adapter'],engine_profile=plan['profile'],scoring_variant=plan['scoring_variant'],**ctx)
assert route.get('source')==str(source) and route.get('source_hashes')==plan['source_hashes'] and route.get('tools')==plan['tools']
assert (route.get('adapter'),route.get('engine_profile'),route.get('scoring_variant'))==(plan['adapter'],plan['profile'],plan['scoring_variant'])
assert cmp.check_record(out/'route',route,authority)
if plan['mode']=='cancel':
 print(json.dumps({'mode':'cancel','status':route.get('status'),'accepted':route.get('accepted')}));raise SystemExit(2)
record=dict(schema=1,accepted=False,status='failed',production_admitted=False,controls_passed=False,actual_GUI=False,project_complete=False,protocol_sha256=a.protocol_sha256,route_sha256=p.sha(out/'route/result.json'),route_status=route.get('status'),route_accepted=route.get('accepted'),native=route.get('native'),source_drc=route.get('source_drc'),complete_external_exit_required=True,adapter=plan['adapter'],profile=plan['profile'],scoring_variant=plan['scoring_variant'],route_seconds=plan['route_seconds'],whole_wall_full_cpu_seconds=plan['whole_wall_full_cpu_seconds'])
try:
 if plan['adapter']=='none':
  native=pv.read_bytes(out/'route/native.dsn',20*1024**2);task=pv.read_bytes(out/'route/task.dsn',20*1024**2)
  record['stock_adapter_observation']=dict(native_dsn_sha256=p.sha(out/'route/native.dsn'),task_dsn_sha256=p.sha(out/'route/task.dsn'),native_dsn_equals_task_dsn=native==task,scope='Stock engine/adapter none in shared fidelity pipeline; not untouched official workflow')
  assert native==task and not any(key in route for key in ('adapter_transformations','pour_dsn_correction','native_edge_correction','native_edge_admission_policy','minimum_width_guard'))
 if route.get('accepted') is True:
  record['route_readback']=p.check_result(out/'route/result.json',**ctx)
  h.review_copy(out/'route/result.json',out/'review',render=True,**ctx)
  h.review_choice(out/'review/review.json',out/'choice','accept',**ctx)
  ex.export(out/'choice/choice.json',out/'export',seconds=120,**ctx)
  record['export_readback']=ex.check_export(out/'export/export.json',**ctx)
  record['outcome']='validated_delivery';record['controls_passed']=True
 else:
  record['negative_readback']=p.check_rejected_routing_attempt(out/'route/result.json',**ctx)
  record['outcome']='validated_completed_negative';record['controls_passed']=True
 # Ordinary admission stays closed irrespective of the outcome.
 try:p.check_result(out/'route/result.json')
 except p.Rejected as exc:record['default_refusal']=str(exc)
 else:raise p.Rejected('ordinary checker admitted comparison attempt')
 authority.check();assert p.sha(a.protocol)==a.protocol_sha256 and p.tool_manifest()==plan['tools'] and p.tree_hash(source.parent)==plan['source_hashes']
 record['status']='completed'
except (Exception,KeyboardInterrupt) as exc:record.update(controls_passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc))
record['completed_evidence']=f.evidence_inventory(out)
def remaining():return min(plan['whole_wall_full_cpu_seconds']-2-(time.monotonic()-START),plan['whole_wall_full_cpu_seconds']-2-(cpu()-CPU0))
def fresh():
 h.owned_destination(owner);authority.check()
 assert p.sha(a.protocol)==a.protocol_sha256 and p.sha(Path(__file__))==plan['child_sha256'] and p.sha(ROOT/pv.MANIFEST)==plan['runtime_manifest_sha256']
 assert f.evidence_inventory(out)==record['completed_evidence']
def terminal_check():
 fresh()
 if record['controls_passed']:
  if record['outcome']=='validated_delivery':ex.check_export(out/'export/export.json',**ctx)
  else:p.check_rejected_routing_attempt(out/'route/result.json',**ctx)
def account():
 record.update(sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0)
 if remaining()<=0:record.update(controls_passed=False,status='budget_exceeded')
 if record['status']!='completed':record['controls_passed']=False
f.publish(out,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=terminal_check)
print(json.dumps({k:record.get(k) for k in ('controls_passed','outcome','error','sampled_wall_seconds','sampled_full_CPU_seconds')}));raise SystemExit(0 if record['controls_passed'] and record['status']=='completed' else 2)
