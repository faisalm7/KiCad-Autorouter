"""Freeze independent tools, source and positive prerequisites before Native controls."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
def load(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
preparation=ROOT/'.runs/runtime033-ordinary-native-invalid-preparation-001.json'
assert sha(preparation)=='f2c8806fb046b3963e8f12a4a4051a1b24ec2955151a55f9e822c6d971966d2c'
review=ROOT/'.runs/runtime033-ordinary-native-invalid-source-review-001.json'
assert sha(review)=='7ff5e5f442c0c51b36d7de087815a558e942c169ecdce3bbc71cc90ca6cf1764'
plan=load(preparation)['proposed_contract']
query=ROOT/'.runs/runtime033-method-material-002/tools-defaults.json'
assert sha(query)=='57fb2818b484a8381016eafc1c9e6eab3cdeab989062ff8686a0f4c97973eb21'
plan['tools']=load(query)['tools']
plan['enclosure_sha256']=sha(ROOT/'.runs/enclose-native7-independent-control-004.py')
runtime=Path(plan['runtime']);original=ROOT/'.runs/qualify-runtime033-ordinary-native-invalid-001.py'
assert sha(original)==plan['controller_sha256']==plan['helper_sha256']
assert sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']
assert plan['tools']['source_provenance']['manifest_sha256']==plan['runtime_manifest_sha256']
assert shutil.disk_usage(ROOT).free>2*1024**3
for label in ('whole4Cu','partial2Cu'):
 item=plan[label+'_positive']
 for name in ('protocol','execution','result','route','export'):
  assert sha(Path(item[name+'_path']))==item[name+'_sha256']
 assert load(Path(item['execution_path']))['controls_passed'] is True
for rel in ('full-integration-176','install-distribution-native-006'):
 assert load(ROOT/'.runs'/rel/'execution.json')['passed'] is True
child=Path(plan['controller']);out=Path(plan['output']);base=ROOT/'.runs/runtime033-ordinary-native-invalid-001'
assert not child.exists() and not out.exists() and not base.exists()
shutil.copyfile(original,child);assert sha(child)==plan['controller_sha256']
base.mkdir();path=base/'protocol.json'
path.write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(protocol=str(path),sha256=sha(path),output=str(out),Native_executed=False)))
