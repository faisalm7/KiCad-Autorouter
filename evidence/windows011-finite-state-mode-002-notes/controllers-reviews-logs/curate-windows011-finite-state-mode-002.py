"""Correct unpublished hidden retention paths; reuse the exact frozen protocols."""
import ast,datetime,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
notes=ROOT/'evidence/windows011-finite-state-mode-002-notes';packet=ROOT/'evidence/windows011-finite-state-mode-002.json'
assert not notes.exists() and not packet.exists()
old=f.read_json(ROOT/'evidence/windows011-finite-state-mode-001.json');index=ROOT/old['files_index']['path'];assert p.sha(index)==old['files_index']['sha256']
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
refs={};files=[];material=[];total=0
defs=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')]
exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'))
sources=[]
for row in f.read_json(index)['material']:
 q=ROOT/row['original'];assert p.sha(q)==p.sha(ROOT/row['retained'])==row['sha256'];sources.append(q)
sources += [ROOT/'evidence/windows011-finite-state-mode-001.json',index,Path(__file__),
 ROOT/'.runs/freeze-windows011-finite-state-mode-001-command.log',ROOT/'.runs/freeze-windows011-finite-state-mode-001-time.log']
raw=[io.read_bytes(q,4*1024**2) for q in sources];assert sum(map(len,raw))<16*1024**2 and len(sources)<2000
for data in raw:assert b'\0' not in data;data.decode('utf8')
for q in sources:
 name=Path('controllers-reviews-logs')/q.name
 if q==index:name=Path('prior-unpublished-files-index.json')
 retain(q,name)
for row in old['protocols']:assert p.sha(ROOT/row['path'])==row['sha256']
assert all(p.sha(ROOT/name)==pin for name,pin in old['source_files_sha256'].items())
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(old);record['recorded_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
record['curation_correction']='First unpublished001 freeze succeeded, but public destinations containing .runs were Git-ignored. No001commit/push/CI occurred.002 preserves all exact originals and priorrecord with nonhidden destinations; protocols/source/tests/CI are not repeated or weakened. First001 rawdirectory remains onMac.'
record['first_freeze_cost']=cost(ROOT/'.runs/freeze-windows011-finite-state-mode-001-time.log')
record['files_index']=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
p.save_json(packet,record);print(json.dumps(dict(files=len(files),bytes=total,protocols_unchanged=True,CI_dispatched=False)))
