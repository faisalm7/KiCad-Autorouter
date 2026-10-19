"""Publish diagnostic filename aliases after a synthetic-key false positive.

Raw native logs and the rejected local commit remain unchanged. Only the five
actual CoCreateGuid-owned policy filename tokens are aliased in public copies.
"""
import ast,datetime,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
notes=ROOT/'evidence/windows011-lifetime-actual002-notes';packet=ROOT/'evidence/windows011-lifetime-actual002.json'
stage=ROOT/'.runs/windows011-lifetime-public002-material';assert not any(q.exists() for q in (notes,packet,stage))
old=f.read_json(ROOT/'evidence/windows011-lifetime-actual001.json');idx=ROOT/old['files_index']['path'];assert p.sha(idx)==old['files_index']['sha256']
raw_index=f.read_json(idx);known=set(f.read_json(ROOT/'.runs/windows011-lifetime-actual001/readiness.json')['persistent_guard']['last_live_C_info']['keys'])
pattern=re.compile(rb'key-([0-9a-f]{32})(?![0-9a-f])')
def alias(raw):
 def replace(match):
  assert match[1].decode() in known,'Not a generated policy identifier; refuse public transformation'
  return b'policy-guid-'+match[1]
 return pattern.sub(replace,raw)
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
refs={};files=[];material=[];total=0
defs=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='retain'];exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'))
mapping=[]
for row in raw_index['files']:
 raw_path=ROOT/row['path'];raw=io.read_bytes(raw_path,4*1024**2);assert hashlib.sha256(raw).hexdigest()==row['sha256']
 rel=alias(str(raw_path.relative_to(ROOT/'evidence/windows011-lifetime-actual001-notes')).encode()).decode();derived=alias(raw)
 q=stage/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(derived);retain(q,Path(rel))
 mapping.append(dict(public_path=str((notes/rel).relative_to(ROOT)),raw_path_alias=alias(str(raw_path.relative_to(ROOT)).encode()).decode(),raw_sha256=row['sha256'],public_sha256=hashlib.sha256(derived).hexdigest(),raw_bytes=len(raw),public_bytes=len(derived),generated_filename_tokens_aliased=len(pattern.findall(raw))))
for q in (Path(__file__),ROOT/'.runs/windows011-owner1307-push-protection-001.json'):
 raw=io.read_bytes(q,4*1024**2);derived=alias(raw);target=stage/'publication'/q.name;target.parent.mkdir(exist_ok=True);target.write_bytes(derived);retain(target,Path('publication')/q.name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(old);record['recorded_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
record['kind']='Windows011-actual001-real-policy-refusal-public-alias002'
record['publication']={'reason':'GitHubGH013pushprotection matched generated policy filename tokens to Mailgun API-key syntax. All55matched tokens in4newtextfiles were checked against actual five C-created policyGUIDs. No override/bypass or remote publication occurred.',
 'transform':'Only generated key-GUID filename token becomes policy-guid-GUID in public text/path aliases. GUID values, source hashes, warnings/failures/numericmetrics and actualCpolicy remain unchanged. Raw filename/text tokens can be reconstructed from this rule for hash checking; these identifiers are not API credentials.',
 'rejected_commit_retained_local':'236eb077647fb6de67fe4ee7bb690b9fa50fcb29','local_ref':'refs/local-checkpoints/windows011-owner1307-push-rejected-001',
 'raw_logs_state_and_prior_packet':'Remain unchanged onthisMac under .runs/windows011-lifetime-actual001 and evidence/windows011-lifetime-actual001*. Public derivedfiles are not falsely labelledbyte-identical rawlogs.',
 'mapping':mapping}
record['review']['raw_receipt_Mac_only']=True
record['files_index']=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))
payload=json.dumps(record,indent=2)+'\n';assert not pattern.search(payload.encode());packet.write_text(payload)
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
print(json.dumps(dict(public_files=len(files),bytes=total,raw_originals_unchanged=True,push_protection_override=False)))
