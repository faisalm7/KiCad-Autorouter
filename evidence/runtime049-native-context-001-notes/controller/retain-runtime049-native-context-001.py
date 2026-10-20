"""Retain additional small049 context/map/DSN receipts using the shared text helper.
No Native, solver, production reader, CAD copying or acceptance claim.
"""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='retain'];assert len(nodes)==1
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::retain','exec'),globals())
notes=ROOT/'evidence/runtime049-native-context-001-notes';output=ROOT/'evidence/runtime049-native-context-001.json';assert not notes.exists() and not output.exists()
refs={};files=[];material=[];total=0
packet=ROOT/'evidence/runtime049-native-milestone-002.json';assert p.sha(packet)=='a2030b472e0c15a6a32e40a6ae0968f863e98a1bde5e9537825f109f1876b646'
d=json.loads(packet.read_text())
for row in d['cases']:
 for label,proof in row['own_finals'].items():
  directory=Path(proof['own_final']['output']).parent
  for name in ('improve-child-context.json','export-netclasses.json','pour-dsn-correction.json'):
   path=directory/name
   if path.is_file():retain(path,Path('cases')/row['case']/label/name)
retain(Path(__file__),Path('controller')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(output,dict(schema=1,kind='runtime049-small-native-context-retention-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=d['source_head'],runtime_manifest_sha256=d['runtime_manifest_sha256'],milestone=dict(path=str(packet.relative_to(ROOT)),sha256=p.sha(packet)),Native_executed=False,acceptance_authority=False,actual_GUI=False,scope='Additive retention of actual owning-root child-context,initial export map and pour-DSN correction JSON found during bounded review. Selected Native proof plus these JSON is still not self-contained full-reader replay: CAD/interchange and complete raw remain Mac-only/outside010. No prior evidence overwritten.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(path=str(output),sha256=p.sha(output),files=len(files),bytes=total)))
