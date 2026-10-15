from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
old=R/'.runs/current-installation033-review-001';out=R/'.runs/current-installation034-review-001'
assert (out/'audit.py').is_file() and (out/'run.py').is_file()
pins={}
for name in f.read_json(old/'input-pins.json')['files_sha256']:
 if 'current-installation032-review-001' in name:continue
 name=name.replace('installation033','installation034').replace('installation-033','installation-034')
 assert (R/name).is_file(),name
 pins[name]=p.sha(R/name)
plan=f.read_json(R/'.runs/installation034-preparation-001/protocol.json');pins.update(plan['source_sha256']);pins.update(plan['controller_sha256']);pins['.runs/current-installation033-review-001/audit.py']=p.sha(old/'audit.py')
p.save_json(out/'input-pins.json',dict(kind='installation034-reader-inputs-v1',git_head=plan['git_head'],files_sha256=pins,scope='Current034 complete installed reader; actual fixed current test count/selected focus planned=ran, zero supplements. No new Native/test execution by reader.'))
