"""Lead-only bounded shared DS18B20 retained reader; no new Native or solver."""
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
from experiments.original_project_native_v1 import driver
from scripts.fetch_led_demo import capture_native_source
reader=ROOT/'.runs/ds18b20-original-native-readback-001/audit.py';inputs=reader.parent/'input-pins.json'
pins=f.read_json(inputs);inputs_pin=p.sha(inputs);assert pins['status']=='frozen_for_lead_readback'
protocol=ROOT/'.runs/ds18b20-original-preparation-001/input-pins.json';plan=f.read_json(protocol)
tools=p.tool_manifest();assert tools==plan['tools'] and all(p.sha(ROOT/name)==digest for name,digest in pins['files_sha256'].items())
out=ROOT/'.runs/ds18b20-original-native-readback-execution-001';out.mkdir()
process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(reader)],cwd=out,log=out/'command.log',timeout=max(.001,58-(time.monotonic()-START)),max_log_bytes=2_000_000,max_workdir_bytes=16*1024**2,max_group_rss_bytes=4*1024**3)
error=None
try:
 assert p.tool_manifest()==tools
 assert p.sha(inputs)==inputs_pin and all(p.sha(ROOT/name)==digest for name,digest in pins['files_sha256'].items())
 assert all(p.sha(ROOT/name)==digest for name,digest in plan['code_sha256'].items())
 assert all(p.sha(ROOT/name)==digest for name,digest in plan['retained_inputs_sha256'].items())
 base=ROOT/'.runs/ds18b20-original-native-001';observed=f.read_json(base/'result.json')
 assert hashlib.sha256(f.canonical(driver.completed_evidence(base)).encode()).hexdigest()==observed['completed_evidence_sha256']
 _,source=capture_native_source('ds18b20',root=ROOT)
 assert {name:hashlib.sha256(raw).hexdigest() for name,raw in source.items()}==plan['native_packet']['files_sha256']
 current=True
except Exception as exc:current=False;error=type(exc).__name__+': '+str(exc)
checks=f.read_json(reader.parent/'result.json') if (reader.parent/'result.json').is_file() else None
wall,full=time.monotonic()-START,cpu()-CPU0;within=max(wall,full)+2<=60
passed=bool(current and checks and checks['passed'] is True and within and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and not process['log_truncated'])
record=dict(schema=1,passed=passed,process=process,source_current=current,error=error,tools=tools,reader_sha256=p.sha(reader),controller_sha256=p.sha(Path(__file__)),input_pins_sha256=inputs_pin,log_sha256=p.sha(out/'command.log'),result_sha256=p.sha(reader.parent/'result.json') if checks else None,wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2,whole_delivery_within_budget=within,scope='Generic shared original-refill readback of retained DS18B20 original001. Only exact read-only Git HEAD is permitted in the audit; no Native/JVM/network/tests rerun. First-line whole outer wall/fullCPU and two-second publication allowance; preparation inspection unmeasured.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('passed','source_current','wall_seconds','full_cpu_seconds','error')}));raise SystemExit(0 if passed else 2)
