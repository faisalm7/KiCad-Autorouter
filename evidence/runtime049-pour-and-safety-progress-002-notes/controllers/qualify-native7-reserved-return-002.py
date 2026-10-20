"""One natural short-budget CLI control; no delays, mocks or relaxed acceptance.

The disclosed40s CLI budget is below the GUI's90s minimum. It may fail to
observe incumbent return; retain that result without tuning/retrying this run.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,hashlib,json,math,sys
ap=argparse.ArgumentParser();ap.add_argument('--protocol',required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
protocol=Path(a.protocol);raw=protocol.read_bytes();assert hashlib.sha256(raw).hexdigest()==a.protocol_sha256
plan=json.loads(raw);runtime=Path(plan['runtime']);sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,config as c,floor_route as f,gui,strategy as s,sexpr as sx,handoff as h,local_settings as local
assert c.ROOT==runtime and Path(sys.prefix).resolve()==runtime/'.venv'
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256'] and p.sha(Path(__file__))==plan['controller_sha256']
assert plan['method_seconds']==40 and plan['required_return_reserve_seconds']==25
source=h.real_path(plan['source']);hashes=p.tree_hash(source.parent);assert hashes==plan['source_hashes'];tools=p.tool_manifest()
out=h.real_path(plan['output'],existing=False);assert out.parent==runtime/'.runs' and out.name.startswith('native7-comparison-control-') and not out.exists()
assert source.parent!=out and source.parent not in out.parents and out not in source.parent.parents
out.mkdir(mode=0o700);owner={};h.capture_destination(owner,out);method=out/'method'
record=dict(schema=1,status='failed',accepted=False,production_admitted=False,control_passed=False,project_complete=False,actual_GUI=False,human_review=False,source=str(source),source_hashes=hashes,tools=tools,method_seconds=40,whole_wall_full_CPU_seconds=120,scope='One naturally short-budget actual single-Improve CLI control. No artificial waits/mocks/CPU contention or GUI-minimum change; an unobserved return is not a pass. This control does not perform review/export or a family comparison.')
try:
 job=gui.CliJob();log=out/'method.log'
 process=job.run([str(runtime/'.venv/bin/python'),'-B','-m','autorouter','improve',str(source),'--seconds','40','--output',str(method)],log,timeout=55)
 record['process']=process;path=method/'result.json';data=f.read_json(path);record.update(parent_receipt=str(path),parent_sha256=p.sha(path),parent_status=data['status'],parent_accepted=data['accepted'],parent_reason=data.get('reason'),improvements=data.get('improvements'),trials=data.get('trials'))
 assert process['exit_code']==0 and not process['cancel_requested'] and not process['log_truncated'],'Actual short-budget method did not deliver a candidate'
 assert data['accepted'] and data['status']=='routing_accepted' and data['budget_seconds']==data['cpu_budget_seconds']==40
 parent_pin=p.sha(path);method_material=f.evidence_inventory(method)
 checked=p.check_result(path);assert checked['current'] and checked['applied'] is False
 assert checked['candidate']==data['candidate'] and checked['candidate_sha256']==data['candidate_sha256']
 assert parent_pin==record['parent_sha256']==p.sha(path) and f.evidence_inventory(method)==method_material
 incumbent=f.read_json(method/'incumbent/result.json');assert incumbent['accepted'] and data['improvements']==0,'No natural incumbent-return event observed'
 assert data['candidate_sha256']==incumbent['candidate_sha256'] and data['best_observed_candidate']==incumbent['candidate']
 elapsed=data['finalization_started_elapsed_seconds'];record['finalization_started_elapsed_seconds']=elapsed
 assert type(elapsed) in (int,float) and math.isfinite(elapsed) and 0<=elapsed<=data['wall_seconds']<=40
 record['wall_work_headroom_seconds_at_finalization']=40-25-elapsed
 record['work_expiry_at_finalization_observed']=elapsed>=40-25
 assert elapsed>=40-25-s.MIN_TRIAL_SECONDS,'Natural work-reserve pressure was not observed'
 assert data['finalization_reserve_seconds']==data['finalization_cpu_reserve_seconds']==25
 assert max(data['wall_seconds'],data['total_cpu_seconds'])<=40
 candidate=Path(data['candidate']);original=sx.read(source);protected=p.protected_for_record(data,original)
 assert p.sha(candidate)==data['candidate_sha256'] and p.immutable(sx.read(candidate))==p.immutable(original)
 assert all(item in p.routes(sx.read(candidate)) for item in protected) and data['schematic_parity']=='checked by final native DRC'
 record.update(candidate_sha256=data['candidate_sha256'],Native_counts=[data['native'][k] for k in ('opens','blocking','warnings','exclusions')],protected_count=len(protected))
 packets=s.native7_packets(method,data)
 assert p.tree_hash(source.parent)==hashes and p.tool_manifest()==tools and protocol.read_bytes()==raw
 assert p.sha(Path(__file__))==plan['controller_sha256'] and p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']
 assert h.owned_destination(owner)==out
 assert p.sha(path)==parent_pin and f.evidence_inventory(method)==method_material
 local.check_final_events(packets,c.CLI)
 record.update(control_passed=True,status='completed')
except (Exception,KeyboardInterrupt) as exc:record['error']=type(exc).__name__+': '+str(exc)
record.update(wall_seconds=time.monotonic()-START,total_cpu_seconds=cpu()-CPU0,external_exit_required=True)
if max(record['wall_seconds'],record['total_cpu_seconds'])+2>120:record.update(control_passed=False,status='budget_exceeded')
p.save_json(out/'result.json',record);print(json.dumps(dict(control_passed=record['control_passed'],status=record['status'],error=record.get('error'))));raise SystemExit(0 if record['control_passed'] else 2)
