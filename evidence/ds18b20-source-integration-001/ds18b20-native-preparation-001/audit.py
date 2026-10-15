import time,resource
START=time.monotonic()
def cpu():
 a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
 return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import sys,json,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
real_popen=subprocess.Popen
def readonly(argv,*args,**kwargs):
 if argv!=['git','rev-parse','HEAD'] or Path(kwargs.get('cwd','')).resolve()!=ROOT:raise AssertionError('reader permits only shared read-only git HEAD')
 return real_popen(argv,*args,**kwargs)
subprocess.Popen=readonly
from autorouter import pipeline as p,floor_route as f
from experiments.original_project_native_v1.readback import check
from experiments.original_project_native_v1 import driver
from scripts.fetch_led_demo import capture_native_source
out=Path(__file__).resolve().parent;record={'schema':1,'passed':False,'accepted':False,'new_native_execution':False,'new_jvm_execution':False,'new_gets':0}
try:
 protocol=ROOT/'.runs/ds18b20-original-preparation-001/input-pins.json';protocol_pin=p.sha(protocol);plan=f.read_json(protocol)
 inputs=out/'input-pins.json';inputs_pin=p.sha(inputs);pins=f.read_json(inputs)
 assert pins['kind']=='ds18b20-original-native-reader-inputs-v1' and pins['status']=='frozen_for_lead_readback' and plan['status']=='frozen_for_lead_execution'
 assert all(p.sha(ROOT/name)==digest for name,digest in pins['files_sha256'].items())
 assert p.tool_manifest()==plan['tools']
 base=ROOT/'.runs/ds18b20-original-native-001';receipt=base/'result.json';data=f.read_json(receipt);material=driver.completed_evidence(base)
 assert data['project']=='ds18b20' and data['protect_local_settings'] is True and data['source_file_count']==6 and data['source_bytes']==124777
 record['checks']=check(base,data)
 # Shared tool callback first; all completed bytes/source/protocol are last.
 assert p.tool_manifest()==plan['tools']
 assert driver.completed_evidence(base)==material and p.sha(protocol)==protocol_pin and p.sha(inputs)==inputs_pin
 assert all(p.sha(ROOT/name)==digest for name,digest in pins['files_sha256'].items())
 assert all(p.sha(ROOT/name)==digest for name,digest in plan['code_sha256'].items())
 assert all(p.sha(ROOT/name)==digest for name,digest in plan['retained_inputs_sha256'].items())
 _,source=capture_native_source('ds18b20',root=ROOT)
 assert {name:hashlib.sha256(raw).hexdigest() for name,raw in source.items()}==plan['native_packet']['files_sha256']
 record['passed']=True
except BaseException as exc:record['error']=type(exc).__name__+': '+str(exc)
wall,full=time.monotonic()-START,cpu()-CPU0
record.update(reader_sha256=p.sha(ROOT/'experiments/original_project_native_v1/readback.py'),actor_sha256=p.sha(Path(__file__)),wall_seconds=wall,full_cpu_seconds=full,bootstrap_emission_allowance_seconds=2,charged_wall_seconds=wall+2,charged_full_cpu_seconds=full+2)
if max(wall,full)+2>60:record['passed']=False
p.save_json(out/'result.json',record);print(json.dumps({k:record.get(k)for k in ('passed','error','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed']else 2)
