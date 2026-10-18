"""One frozen API attempt; central production helpers own all routing proof.

This child is run only by a finite shared enclosure. Functional completion,
completed-negative consistency and actual cancellation are distinct controls.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(v.ru_utime+v.ru_stime for v in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,comparison as cmp,handoff as h,review_export as ex,provenance as pv
ap=argparse.ArgumentParser();ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
plan=f.read_json(a.protocol);assert p.sha(a.protocol)==a.protocol_sha256
assert c.ROOT==ROOT and Path(sys.prefix).resolve()==ROOT/'.venv' and p.sha(Path(__file__))==plan['child_sha256']
assert p.sha(ROOT/pv.MANIFEST)==plan['runtime_manifest_sha256'] and p.tool_manifest()==plan['tools']
assert plan['profile'] in ('standard','tuned') and plan['mode'] in ('completed','cancel')
source=Path(plan['source']);out=Path(plan['output']);assert not out.exists() and out.parent==ROOT/'.runs' and out.name.startswith(cmp.PREFIX)
assert p.tree_hash(source.parent)==plan['source_hashes'];out.mkdir();owner={};h.capture_destination(owner,out)
authority=cmp.Context(source,out/'route',plan['profile'],plan['route_seconds'],plan['tools'],plan['source_hashes']);ctx=dict(comparison_context=authority)
route=p.route(source,out/'route',seconds=plan['route_seconds'],adapter='both',engine_profile=plan['profile'],**ctx)
if plan['mode']=='cancel':
 print(json.dumps({'mode':'cancel','status':route.get('status'),'accepted':route.get('accepted')}));raise SystemExit(2)
record=dict(schema=1,accepted=False,status='failed',production_admitted=False,controls_passed=False,actual_GUI=False,project_complete=False,protocol_sha256=a.protocol_sha256,route_sha256=p.sha(out/'route/result.json'),route_status=route.get('status'),route_accepted=route.get('accepted'),native=route.get('native'),source_drc=route.get('source_drc'),complete_external_exit_required=True)
try:
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
 authority.check();assert p.sha(a.protocol)==a.protocol_sha256
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
