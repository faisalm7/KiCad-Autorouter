"""Existing shared runner/publication provide complete outer exit accounting."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from autorouter.gui import child_environment
ap=argparse.ArgumentParser();ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);args=ap.parse_args()
assert args.protocol==ROOT/'.runs/runtime042-install-existing-qualification-001/protocol.json'
assert type(args.protocol_sha256)is str and re.fullmatch('[0-9a-f]{64}',args.protocol_sha256)
assert args.protocol.is_absolute() and h.real_path(args.protocol)==args.protocol and p.sha(args.protocol)==args.protocol_sha256
plan=f.read_json(args.protocol);runtime=Path(plan['runtime']);child=Path(plan['controller']);manifest=runtime/'runtime-distribution.json'
assert type(plan['schema'])is int and plan['schema']==1 and plan['kind']=='runtime042-install-existing-clean-environment-v1'
assert runtime==ROOT/'.runs/runtime042 fresh install 001' and h.real_path(runtime)==runtime
assert child==ROOT/'.runs/qualify-runtime042-install-existing-environment-001.py' and h.real_path(child)==child
assert plan['source_head']=='82aaa3b750007ef2ffaafd367ffcb718aa93865e'
assert type(plan['runtime_manifest_sha256'])is str and re.fullmatch('[0-9a-f]{64}',plan['runtime_manifest_sha256'])
assert p.sha(child)==plan['controller_sha256'] and p.sha(manifest)==plan['runtime_manifest_sha256']
assert Path(plan['output'])==runtime/'.runs/clean-env-partial-delivery-001'
assert plan['limits']['whole_wall_full_CPU_seconds']==300 and plan['limits']['aggregate_bytes']==768*1024**2
out=args.protocol.parent/'enclosure';out.mkdir();owner={};h.capture_destination(owner,out)
process=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B',str(child),'--protocol',str(args.protocol),'--protocol-sha256',args.protocol_sha256],cwd=out,env=child_environment(),log=out/'command.log',timeout=max(.001,300-(time.monotonic()-START)),max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=2*1024**2)
p.save_json(out/'process.json',process)
delivery=Path(plan['output']);receipt=delivery/'result.json';data=f.read_json(receipt) if receipt.is_file() else None
material=f.evidence_inventory(delivery) if delivery.is_dir() else None
record=dict(schema=1,external_complete_exit_required=True,accounting_point='Outer samples include child exit and publication work so far; separately retain actual complete external wall/fullCPU through final process exit. Installation/venv preparation costs are additional.',passed=bool(data and data.get('status')=='completed' and data.get('controls_passed')is True and data.get('workflow_delivered')is True and data.get('accepted')is False and data.get('production_admitted')is False and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete']is True and process['log_truncated']is False),accepted=False,project_complete=False,actual_GUI=False,protocol_sha256=args.protocol_sha256,child_receipt=str(receipt),child_sha256=p.sha(receipt) if data else None,process=process,completed_material=material,guard_scope='Outer2MiB cwd guards enclosure logs; reviewed parent guards entire fresh HOME/TMP/workflow subtree768MiB during each command and every later material replay. Polling can overshoot; not an OS quota.')
record['status']='completed' if record['passed'] else 'failed'
def remaining():return min(300-(time.monotonic()-START),300-(cpu()-CPU0))
def fresh():
 h.owned_destination(owner)
 assert p.sha(args.protocol)==args.protocol_sha256 and p.sha(child)==plan['controller_sha256'] and p.sha(manifest)==plan['runtime_manifest_sha256']
 assert p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
 assert (p.sha(receipt) if receipt.is_file() else None)==record['child_sha256']
 assert (f.evidence_inventory(delivery) if delivery.is_dir() else None)==material
def account():
 record.update(complete_wall_seconds=time.monotonic()-START,complete_full_CPU_seconds=cpu()-CPU0)
 if remaining()<=0:record.update(passed=False,status='budget_exceeded')
f.publish(out,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=fresh)
print({key:record[key] for key in ('passed','status','complete_wall_seconds','complete_full_CPU_seconds')})
raise SystemExit(0 if record['passed'] and record['status']=='completed' else 2)
