"""One bounded GND feedback completion; no old classifier or engine replay."""
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
protocol=ROOT/'.runs/ir-native-connected-repair-protocol-001.json';spec=f.read_json(protocol);pin=p.sha(protocol);out=ROOT/'.runs/ir-native-connected-repair-execution-001';out.mkdir();actor=ROOT/'.runs/ir-native-connected-repair-001';prepath=ROOT/'.runs/ir-native-connected-repair-preflight-001/execution.json';pre=f.read_json(prepath);prepin=p.sha(prepath)
def stable():
 assert p.tool_manifest()==spec['tools'] and p.sha(protocol)==pin and p.sha(prepath)==prepin and pre['passed'] and pre['protocol_sha256']==pin
 q.verify_freeze(spec['freeze'],Path(spec['source']))
 for n,d in spec['pins'].items():assert p.sha(ROOT/n)==d,n
 for n,d in spec['retained_material'].items():assert p.tree_hash(ROOT/n)==d,n
 assert p.sha(Path(__file__))==spec['outer_sha256'] and p.sha(ROOT/'.runs/read-ir-native-connected-repair-001.py')==spec['reader_sha256'] and p.sha(ROOT/'.runs/ir-native-connected-repair-actor-001.py')==spec['actor_sha256']
record=dict(schema=1,status='incomplete',accepted=False,production_qualified=False,source_current=False,tools=spec['tools'],protocol_sha256=pin,preflight_sha256=prepin,process=None)
try:
 stable();lock=ROOT/'.runs/quality-experiment.lock';assert not lock.is_symlink()
 with lock.open('a') as held:
  fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
  record['process']=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/ir-native-connected-repair-actor-001.py'),'--run-native','--output',str(actor),'--protocol',str(protocol),'--protocol-sha256',pin],cwd=out,log=out/'command.log',timeout=max(.001,61-(time.monotonic()-START)),max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
 record.update(material=f.evidence_inventory(actor),result_sha256=p.sha(actor/'result.json') if (actor/'result.json').is_file() else None)
 stable();assert f.evidence_inventory(actor)==record['material'] and (p.sha(actor/'result.json') if (actor/'result.json').is_file() else None)==record['result_sha256'];record.update(status='completed',source_current=True)
except (Exception,KeyboardInterrupt) as exc:record.update(status='failed',error=type(exc).__name__+': '+str(exc))
wall,full=time.monotonic()-START,cpu()-CPU0;record.update(wall_seconds=wall,full_cpu_seconds=full,within_budget=max(wall,full)<=63,publication_allowance_seconds=2,controller_sha256=p.sha(Path(__file__)),log_sha256=p.sha(out/'command.log') if (out/'command.log').exists() else None)
p.save_json(out/'execution.json',record);print(json.dumps({k:record.get(k) for k in ('status','source_current','error','wall_seconds','full_cpu_seconds','within_budget')}));raise SystemExit(0 if record['status']=='completed' and record['within_budget'] else 2)
