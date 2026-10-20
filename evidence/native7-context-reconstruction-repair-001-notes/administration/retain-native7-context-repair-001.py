"""Retain reconstruction-only Context repair; existing bounded curation helpers."""
from pathlib import Path
import ast,datetime,hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
notes=ROOT/'evidence/native7-context-reconstruction-repair-001-notes';target=ROOT/'evidence/native7-context-reconstruction-repair-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
failed=json.loads((ROOT/'.runs/native7-context-existing-targeted-001/execution.json').read_bytes())
passed=json.loads((ROOT/'.runs/native7-context-existing-targeted-002/execution.json').read_bytes())
assert failed['process']['exit_code']==1 and passed['process']['exit_code']==0 and passed['source_current']
focused=(ROOT/'.runs/native7-context-reuse-targeted-001-time.log').read_text()
count=int(re.search(r'Ran (\d+) tests?',focused).group(1));assert '\nOK\n' in focused
queue=[]
for number in ('001','002'):
 for suffix in ('.py',):queue.append((ROOT/'.runs'/('run-native7-context-existing-targeted-'+number+suffix),Path('controllers')/('run-existing-'+number+suffix)))
 for suffix in ('.log','-time.log'):queue.append((ROOT/'.runs'/('native7-context-existing-targeted-'+number+suffix),Path('controls')/('existing-'+number+suffix)))
 for name in ('command.log','execution.json'):queue.append((ROOT/'.runs'/('native7-context-existing-targeted-'+number)/name,Path('controls')/('existing'+number)/name))
for name in ('native7-context-reuse-targeted-001.log','native7-context-reuse-targeted-001-time.log','native7-context-reconstruction-review-001.json','native7-context-independent-source-review-001.json'):
 queue.append((ROOT/'.runs'/name,Path('controls')/name))
queue.append((Path(__file__),Path('administration')/Path(__file__).name))
for path,name in queue:retain(path,name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='selected7-operation-local-Context-reconstruction-repair-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,demonstrated_failure='Fresh053 delivered no candidate after Native-valid18-trial IR route because repeated review proof work exceeded unchanged30s ceiling. Historical failure remains immutable.',change='Reuse only reconstructed private Context definition inside one existing validation_readback_session, bounded8. Keep original captured parent owner/inode. Every use checks exact constructor request, current owned source/snapshot/code/preferences/tools and source support, effective shape, sidecar seal, Context record and late exact owner. Current module/callable/policy and critical Context method identities bind reuse. Exceptions/private-reader failures/nested failure/cancel/outer exit clear entries.',unchanged='Every full child, trial, selection, Native, Default, source, process, material and final all-root PRL reader still executes at its original callsites. No parent/privatechild accepted-result memo, disk cache, execution Budget, cap increase, board-specific policy or fallback.',targeted=dict(existing_tests=138,existing_passed=True,existing_complete_cost=cost(ROOT/'.runs/native7-context-existing-targeted-002-time.log'),focused_tests=count,focused_passed=True,focused_complete_cost=cost(ROOT/'.runs/native7-context-reuse-targeted-001-time.log')),failed_control=dict(tests=138,errors=1,complete_cost=cost(ROOT/'.runs/native7-context-existing-targeted-001-time.log'),failure='Forged marker still refused but new intake raised KeyError before domain admission. Restored original exact shape admission before reuse intake; existing regression then passes. No Native executed or positive result published.'),qualification='Source and software regression controls only. Full204 then fresh runtime054 installed delivery required before broader Native/install/GUI qualification; no053 promotion or unchanged retry.',Native_executed=False,actual_GUI=False,human_review=False,costs='Complete external events counted once. Research, authoring, AI source review and curation additional/partly unmetered, not zero. Unit controls do not establish actual delivery, routing quality or new family coverage.',backup_scope='Audited owned source and compact evidence only; later raw stays Mac-only/outside010. Full restoration remains capacity-blocked; no repeat/deletion/limit increase.',source_sha256={str(q.relative_to(ROOT)):p.sha(q) for q in (ROOT/'autorouter/pipeline.py',ROOT/'autorouter/strategy.py',ROOT/'tests/test_native7_context_reuse.py')},files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,project_complete=False)))
