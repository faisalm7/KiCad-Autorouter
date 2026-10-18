"""Freeze the reviewed startup-environment axis without rebuilding033."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
def read(q):return json.loads(q.read_bytes())
prep=ROOT/'.runs/runtime033-clean-environment-preparation-001.json'
assert sha(prep)=='534379dd82437efc1af6ed7e3788b23327d71858b22e0f7609fa3c40cabe80f6'
review=ROOT/'.runs/runtime033-clean-environment-source-review-001.json'
assert sha(review)=='0481125a3f0dfecacc75fce6db9df16f82911c80224502e786a048467ce35b72'
plan=read(prep)['caller_protocol_fields_without_tools_NOT_A_FROZEN_PROTOCOL']
assert sha(Path(plan['controller']))==plan['controller_sha256']=='e9f8821a18df0586b25d5330c8d1558ba6e6c4e74eda2883f8126030a60c853d'
query=Path(plan['tools_defaults_path']);assert sha(query)==plan['tools_defaults_sha256']
plan['tools']=read(query)['tools']
runtime=Path(plan['runtime']);assert sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']
matrix=ROOT/'.runs/runtime033-interf-current-comparison-001'
for arm in read(matrix/'population.json')['population']:
 assert read(matrix/arm/'enclosure/result.json')['passed'] is True
assert shutil.disk_usage(ROOT).free>2*1024**3
assert not Path(plan['output']).exists()
base=ROOT/'.runs/runtime033-clean-environment-001';assert not base.exists();base.mkdir()
path=base/'protocol.json';path.write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(protocol=str(path),sha256=sha(path),Native_executed=False,output=plan['output'])))
