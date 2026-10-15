"""Lead-only frozen DS18B20 original diagnostic; no solver or support admission."""
import time,resource
START=time.monotonic()
def cpu():
 return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
from scripts.fetch_led_demo import capture_native_source
protocol=ROOT/'.runs/ds18b20-original-preparation-001/input-pins.json';protocol_pin=p.sha(protocol);plan=f.read_json(protocol)
assert plan['kind']=='ds18b20-original-native-preparation-v1' and plan['status']=='frozen_for_lead_execution'
assert plan['retained_inputs_sha256'] and plan['git_head'] and plan['tools']
tools=p.tool_manifest();assert tools==plan['tools'] and tools['git_head']==plan['git_head']
command=[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'experiments/original_project_native_v1/driver.py'),'--project','ds18b20','--output',str(ROOT/'.runs/ds18b20-original-native-001'),'--run-native','--protect-local-settings']
assert command==plan['command'] and p.sha(Path(__file__))==plan['controllers_sha256']['.runs/run-ds18b20-original-native-001.py']
def stable():
 assert p.tool_manifest()==tools and p.sha(protocol)==protocol_pin
 assert all(p.sha(ROOT/name)==digest for name,digest in plan['code_sha256'].items())
 assert all(p.sha(ROOT/name)==digest for name,digest in plan['retained_inputs_sha256'].items())
 folder,files=capture_native_source('ds18b20',root=ROOT)
 assert folder==ROOT/plan['native_packet']['path']
 assert {n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}==plan['native_packet']['files_sha256']
 assert sum(map(len,files.values()))==plan['native_packet']['bytes']==124777
 assert len(files)==plan['native_packet']['file_count']==6 and plan['originals']['file_count']==5 and plan['originals']['bytes']==119518
 assert plan['source_prl_present'] is True and plan['protect_local_settings'] is True
 assert 'D18BS20.kicad_prl' in files and files['_licenses/creator/README.md']==files['README.md']
 return True
stable()
out=ROOT/'.runs/ds18b20-original-native-execution-001';out.mkdir()
process=run(command,cwd=out,log=out/'command.log',timeout=max(.001,105-(time.monotonic()-START)),max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
error=None
try:current=stable()
except Exception as exc:current=False;error=type(exc).__name__+': '+str(exc)
wall,full=time.monotonic()-START,cpu()-CPU0
passed=current and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and not process['log_truncated'] and max(wall,full)+2<=107
record=dict(schema=1,passed=passed,process=process,git_head=tools['git_head'],tools=tools,protocol_sha256=protocol_pin,protocol_and_source_current=current,error=error,controller_sha256=p.sha(Path(__file__)),log_sha256=p.sha(out/'command.log'),wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2,whole_delivery_within_budget=max(wall,full)+2<=107,scope=plan['scope'])
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('passed','protocol_and_source_current','wall_seconds','full_cpu_seconds','error')}));raise SystemExit(0 if passed else 2)
