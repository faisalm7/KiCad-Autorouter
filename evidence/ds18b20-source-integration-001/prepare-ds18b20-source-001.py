"""Freeze existing source-fetch/original-refill/shared-reader helpers; no Native."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from scripts import fetch_led_demo as demo
from experiments.original_project_native_v1 import driver
phase=sys.argv[1];assert phase in ('fetch','original','readback')
assert not subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=normal'],cwd=ROOT)
tools=p.tool_manifest();cfg=demo.fixed_profile('ds18b20');prep=ROOT/'.runs/ds18b20-original-preparation-001'
code={**tools['implementation_sha256'],**{n:p.sha(ROOT/n) for n in (*demo.ARC_MATERIAL,'experiments/original_project_native_v1/driver.py','experiments/original_project_native_v1/readback.py','experiments/original_project_native_v1/local_settings.py','experiments/placement_handoff_native_v1/driver.py','scripts/experiment_quality.py')}}
def save(path,value):
 assert not path.exists();p.save_json(path,value)
def pins(names):return {n:p.sha(ROOT/n) for n in names}
if phase=='fetch':
 prep.mkdir();controllers=ROOT/'.local-backups/ds18b20-native-preparation-001'
 for label in ('fetch','original-native','original-native-readback'):
  name='run-ds18b20-'+label+'-001.py';target=ROOT/'.runs'/name;assert not target.exists();shutil.copyfile(controllers/name,target)
 reader=ROOT/'.runs/ds18b20-original-native-readback-001';reader.mkdir();shutil.copyfile(controllers/'audit.py',reader/'audit.py')
 command=[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/fetch_led_demo.py'),'--project','ds18b20','--fetch','--output',cfg['default_output']]
 save(prep/'fetch-input-pins.json',dict(schema=1,status='frozen_for_lead_execution',kind='ds18b20-source-fetch-v1',tools=tools,git_head=tools['git_head'],code_sha256=code,wrapper_sha256=p.sha(ROOT/'.runs/run-ds18b20-fetch-001.py'),command=command,profile=cfg))
elif phase=='original':
 acquisition=f.read_json(ROOT/cfg['default_output']/'result.json');outer=f.read_json(ROOT/'.runs/ds18b20-fetch-execution-001/execution.json')
 assert acquisition['status']=='acquired_unqualified' and acquisition['source_files_exact'] is True and acquisition['new_network_requests']==5 and outer['passed'] is True and outer['source_current'] is True
 base,files=demo.capture_native_source('ds18b20',root=ROOT);assert len(files)==6 and sum(map(len,files.values()))==124777
 command=[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'experiments/original_project_native_v1/driver.py'),'--project','ds18b20','--output',str(ROOT/'.runs/ds18b20-original-native-001'),'--run-native','--protect-local-settings']
 save(prep/'input-pins.json',dict(schema=1,status='frozen_for_lead_execution',kind='ds18b20-original-native-preparation-v1',project='ds18b20',source_repository=cfg['repository'],source_commit=cfg['commit'],source_prl_present=True,protect_local_settings=True,tools=tools,git_head=tools['git_head'],code_sha256=code,retained_inputs_sha256=pins([cfg['default_output']+'/result.json','.runs/ds18b20-fetch-execution-001/execution.json','.runs/full-integration-089/execution.json']),controllers_sha256=pins(['.runs/run-ds18b20-original-native-001.py','.runs/run-ds18b20-original-native-readback-001.py']),command=command,native_packet={'path':str(base.relative_to(ROOT)),'files_sha256':{n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()},'file_count':6,'bytes':124777},originals={'file_count':5,'bytes':119518},scope='Untouched original fivefiles plus one exactREADME notice copy, savedrefill/fullSCH/immutable geometry/alloriginalroutes/PRL/rules/ignoredchecks. No solver/routing/admission/title/ancestry/electrical/physical claim. Existing90s inner/107s outer bounds.'))
else:
 out=ROOT/'.runs/ds18b20-original-native-001';data=f.read_json(out/'result.json');assert data['status']=='observed'
 reader=ROOT/'.runs/ds18b20-original-native-readback-001'
 names=[str((out/n).relative_to(ROOT)) for n in driver.completed_evidence(out)['files']]
 names+=['.runs/ds18b20-original-native-001/result.json','.runs/ds18b20-original-native-execution-001/execution.json','.runs/ds18b20-original-preparation-001/input-pins.json',str((reader/'audit.py').relative_to(ROOT))]
 save(reader/'input-pins.json',dict(schema=1,kind='ds18b20-original-native-reader-inputs-v1',status='frozen_for_lead_readback',files_sha256=pins(names)))
print(json.dumps({'phase':phase,'git_head':tools['git_head'],'native_executed':False}))
