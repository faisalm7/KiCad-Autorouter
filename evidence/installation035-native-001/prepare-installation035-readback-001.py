from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
old=R/'.runs/current-installation034-review-001';out=R/'.runs/current-installation035-review-001'
assert (out/'audit.py').is_file() and (out/'run.py').is_file()
pins={}
for name in f.read_json(old/'input-pins.json')['files_sha256']:
 if 'current-installation033-review-001' in name:continue
 name=name.replace('installation034','installation035').replace('installation-034','installation-035')
 assert (R/name).is_file(),name
 pins[name]=p.sha(R/name)
plan=f.read_json(R/'.runs/installation035-preparation-001/protocol.json');pins.update(plan['source_sha256']);pins.update(plan['controller_sha256']);pins['.runs/current-installation034-review-001/audit.py']=p.sha(old/'audit.py')
for suffix in ('execution.json','protocol.json','fixture-preparation.json','population.json','tests.log'):
 name='.runs/installation035-missing-policy-followup-001/'+suffix;pins[name]=p.sha(R/name)
for name in ('.runs/run-installation035-missing-policy-001.py','evidence/default-tuning-native-001/code/pipeline.py'):
 pins[name]=p.sha(R/name)
p.save_json(out/'input-pins.json',dict(kind='installation035-reader-inputs-v1',git_head=plan['git_head'],files_sha256=pins,scope='Current035 complete installed reader; actual fixed current test count/selected focus planned=ran, one declared67060B owned historical source test supplement. No new Native/test execution by reader.'))
