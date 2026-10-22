"""Finish the partial metadata retention; no Native or routing repetition."""
from pathlib import Path
import ast,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv,placement_clearance as io
from scripts.report_current_comparison import complete_cost
notes=ROOT/'evidence/runtime058-natural-expiry-001-notes';target=ROOT/'evidence/runtime058-natural-expiry-001.json'
assert notes.is_dir() and not target.exists()
index=notes/'files.json';old=json.loads(index.read_bytes());old_pin=p.sha(index)
refs={};files=list(old['files']);material=list(old['material']);total=sum(row['bytes'] for row in files)
for row in files:
 assert p.sha(ROOT/row['path'])==row['sha256'];refs[row['sha256']]=row['path']
for row in material:
 assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='retain']
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper),'exec'),globals())
b=ROOT/'.runs/runtime058-natural-expiry-001';control=json.loads((b/'control-result.json').read_bytes());execution=json.loads((b/'execution.json').read_bytes());child=Path(control['child_receipt']);c=json.loads(child.read_bytes());route=Path(control['route_receipt']);r=json.loads(route.read_bytes())
assert p.sha(child)==control['child_sha256'] and p.sha(route)==control['route_sha256'] and p.sha(b/'execution.json')==control['execution_sha256']
assert r['accepted'] is False and r['status']=='timeout' and [row['stage'] for row in c['processes']]==['preview','route']
for q,name in [(Path(__file__),'administration/completion002.py'),(index,'administration/partial-index001.json'),(ROOT/'.runs/retain-runtime058-natural-expiry-001-time.log','administration/failed-retention001-time.log'),(ROOT/'.runs/retain-runtime058-natural-expiry-001.log','administration/failed-retention001.log')]:retain(q,Path(name))
idx=notes/'files-completed002.json';assert not idx.exists()
p.save_json(idx,dict(schema=1,files=files,material=material))
producer=ROOT/'.runs/retain-runtime058-natural-expiry-001.py'
nodes=[n for n in ast.parse(producer.read_bytes()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='summary' for t in n.targets)]
assert len(nodes)==1
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(producer)+'::summary-only','exec'),globals())
summary['curation_continuation']=dict(partial_index_sha256=old_pin,original_partial_files_preserved=True,failed_complete_cost=complete_cost(ROOT/'.runs/retain-runtime058-natural-expiry-001-time.log'),reason='Missing math import in administrative cost parser after payload/index had been written; this continuation verifies and reuses those bytes. No Native or routing rerun.',completion_controller_sha256=p.sha(Path(__file__)))
assert p.sha(index)==old_pin and all(p.sha(ROOT/row['path'])==row['sha256'] for row in files)
assert p.sha(route)==control['route_sha256'] and p.sha(child)==control['child_sha256']
p.save_json(target,summary)
print(json.dumps(dict(files=len(files),bytes=total,receipt_sha256=p.sha(target),Native=False,engine=False)))
