"""Thin sequential supervisor; all Native semantics stay in existing helpers."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,fcntl
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
from scripts import experiment_quality as q
specpath=ROOT/'.runs/ir-native-connected-baseline-protocol-001.json';pin=p.sha(specpath);spec=f.read_json(specpath)
out=ROOT/'.runs/ir-native-connected-baseline-execution-001';out.mkdir()
def stable():
 assert spec['status']=='frozen' and p.sha(specpath)==pin and p.tool_manifest()==spec['tools']
 q.verify_freeze(spec['freeze'],Path(spec['source']))
 if 'preflight_pin' in globals():assert p.sha(preflight_path)==preflight_pin
 for n,d in spec['pins'].items():assert p.sha(ROOT/n)==d,n
 assert p.sha(ROOT/'experiments/ir_native_connected_baseline_v1/actor.py')==spec['actor_sha256']
 assert p.sha(Path(__file__))==spec['outer_sha256'] and p.sha(ROOT/'.runs/read-ir-native-connected-baseline-001.py')==spec['reader_sha256']
prior=f.read_json(ROOT/spec['prior_execution']);assert prior['passed'] is True and prior['source_current'] is True and prior['final_charged_results']==spec['prior_rows']
preflight_path=ROOT/'.runs/ir-native-connected-baseline-preflight-001/execution.json';preflight_pin=p.sha(preflight_path);preflight=f.read_json(preflight_path);assert preflight['passed'] and preflight['protocol_sha256']==pin
control=f.read_json(ROOT/spec['control_execution']);assert control['source_current'] and control['process']['status']=='success' and control['process']['exit_code']==0 and control['process']['cleanup_complete']
assert max(r['charged_wall_seconds'] for r in spec['prior_rows'] if r['id']=='B2_portfolio')+95+10+25+5<=300
record=dict(schema=1,status='incomplete',accepted=False,production_qualified=False,protocol_sha256=pin,tools=spec['tools'],process=None,source_current=False)
invwall=invcpu=0.;process=None;error=None
try:
 stable();lock=ROOT/'.runs/quality-experiment.lock';assert not lock.is_symlink()
 with lock.open('a') as held:
  fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
  before=time.monotonic();beforecpu=cpu()
  process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'experiments/ir_native_connected_baseline_v1/actor.py'),'--run-native','--output',str(ROOT/'.runs/ir-native-connected-baseline-001'),'--protocol',str(specpath),'--protocol-sha256',pin],cwd=out,log=out/'command.log',timeout=94,max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
  invwall=time.monotonic()-before;invcpu=cpu()-beforecpu
 stable();actor=ROOT/'.runs/ir-native-connected-baseline-001';record.update(result_sha256=p.sha(actor/'result.json') if (actor/'result.json').is_file() else None,material=f.evidence_inventory(actor),classifier_material=p.tree_hash(ROOT/'.runs/ir-native-connected-classifier-001') if (ROOT/'.runs/ir-native-connected-classifier-001').exists() else None)
 stable()
 assert (p.sha(actor/'result.json') if (actor/'result.json').is_file() else None)==record['result_sha256'] and f.evidence_inventory(actor)==record['material']
 assert (p.tree_hash(ROOT/'.runs/ir-native-connected-classifier-001') if (ROOT/'.runs/ir-native-connected-classifier-001').exists() else None)==record['classifier_material']
 record.update(status='completed',source_current=True)
except (Exception,KeyboardInterrupt) as exc:error=type(exc).__name__+': '+str(exc);record.update(status='failed',error=error)
wall,full=time.monotonic()-START,cpu()-CPU0
commonwall=wall-invwall+control['wall_seconds']+2+preflight['wall_seconds']+1;commoncpu=full-invcpu+control['full_cpu_seconds']+2+preflight['full_cpu_seconds']+1
assert commonwall>=0 and commoncpu>=0
record.update(process=process,wall_seconds=wall,full_cpu_seconds=full,invocation_wall_seconds=invwall,invocation_cpu_seconds=invcpu,common_wall_seconds=commonwall,common_cpu_seconds=commoncpu,bootstrap_and_outer_publication_allowance_seconds=3,reader_publication_allowance_seconds=2,within_actor_and_common_caps=max(invwall,invcpu)<=95 and max(commonwall,commoncpu)<=10,preflight_sha256=preflight_pin,controller_sha256=p.sha(Path(__file__)),log_sha256=p.sha(out/'command.log') if (out/'command.log').is_file() else None)
p.save_json(out/'execution.json',record);print(json.dumps({k:record.get(k) for k in ('status','source_current','error','wall_seconds','full_cpu_seconds','invocation_wall_seconds','invocation_cpu_seconds','common_wall_seconds','common_cpu_seconds','within_actor_and_common_caps')}));raise SystemExit(0 if record['status']=='completed' and record['within_actor_and_common_caps'] else 2)
