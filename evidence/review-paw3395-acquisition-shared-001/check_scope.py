"""Read frozen profile/tree and source ASTs only; no network or payload execution."""
from pathlib import Path
import ast, hashlib,json
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
s=HERE/'snapshot';old=ROOT/'.runs/paw3395-acquisition-shared-001/before/fetch.py'
cur=s/'experiments/licensed_acquisition_v1/fetch.py'
plan=json.loads((s/'experiments/licensed_acquisition_v2/protocol.json').read_bytes())
basis={}
for name,meta in plan['metadata_basis'].items():
 p=ROOT/name;raw=p.read_bytes();assert meta=={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},name;basis[name]=meta
raw=(ROOT/'.runs/next-family-priority-001/metadata/tree.json').read_bytes();tree=json.loads(raw)
assert tree['truncated'] is False
blobs={x['path']:(x['mode'],x['sha'],x['size']) for x in tree['tree'] if x['type']=='blob'}
project=plan['projects'][0];declared={x['source_path']:(x['mode'],x['git_blob_sha1'],x['bytes']) for x in project['files']}
assert blobs==declared and len(blobs)==14 and sum(x[2] for x in blobs.values())==2163350
assert project['tree_sha1']==tree['sha'] and project['omitted_paths']==[]
def funcs(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a,b=funcs(old),funcs(cur)
unchanged=['sha','safe','contained','bounded','decode','inventory','git','git_identity','payload','alarm','NoRedirect','fetch_one','write_json','publish','cancellation']
assert all(a[n]==b[n] for n in unchanged)
result={'passed':True,'scope':'Static frozen source/tree comparison only; no downloaded geometry or closure qualification',
 'protocol_sha256':hashlib.sha256((s/'experiments/licensed_acquisition_v2/protocol.json').read_bytes()).hexdigest(),
 'full_tree_blobs':len(blobs),'bytes':sum(x[2] for x in blobs.values()),'unmodified_legacy_function_asts':unchanged,
 'metadata_basis':basis,'tree_sha256':hashlib.sha256(raw).hexdigest(),
 'constraints':'64MiB aggregate,10MiB per project/network,300s wall,14 requests,4096 entries/2048 files; v1 default retains33-file protocol. No arbitrary profile/manifest CLI.'}
(HERE/'scope.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
