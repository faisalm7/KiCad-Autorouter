"""Retain failed full210 and its authored fixture correction, never Native."""
from pathlib import Path
import ast,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv,placement_clearance as io
from scripts.report_current_comparison import complete_cost
notes=ROOT/'evidence/native7-return-full210-fixture-failure-001-notes';target=ROOT/'evidence/native7-return-full210-fixture-failure-001.json';assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='retain'];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper),'exec'),globals())
base=ROOT/'.runs/full-integration-210';ex=json.loads((base/'execution.json').read_bytes());assert ex['passed'] is False and ex['sources_unchanged'] is True and ex['process']['cleanup_complete'] is True and ex['process']['exit_code']==1 and not ex['process']['log_truncated']
assert p.sha(base/'command.log')==ex['log_sha256'];raw=(base/'command.log').read_text();assert 'Ran 2609 tests' in raw and 'FAILED (errors=1, skipped=1)' in raw and "p.check_result('unused'" in raw
focused=ROOT/'.runs/return-session-explicit-fixture-001-time.log';text=focused.read_text();assert 'Ran 10 tests' in text and '\nOK\n' in text
queue={Path(__file__):'administration/retain.py',ROOT/'.runs/run-full-integration-210.py':'full/controller.py',ROOT/'.runs/full-suite-local-root-019.py':'full/discovery.py',ROOT/'tests/test_experimental_route_context.py':'correction/test_experimental_route_context.py'}
for name in ('execution.json','protocol.json','command.log'):queue[base/name]='full/'+name
for name in ('full-integration-210.log','full-integration-210-time.log','return-session-explicit-fixture-001.log','return-session-explicit-fixture-001-time.log'):queue[ROOT/'.runs'/name]='administration/'+name
pins={q:p.sha(q) for q in queue}
for q,name in queue.items():retain(q,Path(name))
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material))
result=dict(schema=1,kind='full210-failed-canonical-input-fixture-corrected-v1',accepted=False,project_complete=False,Native_qualification=False,new_runtime_built=False,source_head='50f63338a67cdbdb81e0392fff7dda5dceaf5b4d',full210=dict(passed=False,tests=2609,errors=1,skipped=1,sources_unchanged=True,complete_cost=complete_cost(ROOT/'.runs/full-integration-210-time.log')),failure='ExperimentalRouteContext.test_explicit_reader_bypasses_production_cache passed literal unused to a mocked reader; the new mandatory canonical receipt intake correctly refuses before reaching the mock.',fix='Only the authored unit fixture now saves a real canonical result.json and asserts its Path reaches the explicit mocked reader. Production guards unchanged; no receipt or Native authority invented.',targeted=dict(passed=True,tests=10,Native=False,complete_cost=complete_cost(focused)),next_gate='Fresh full211 required before preparing runtime059; no full integration or Native pass inferred from focused tests.',limits='Full unit/integration fixture suite is not real routing/Native/GUI qualification; all failed output, costs and prior source packet preserved. No original source project modified.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
assert all(p.sha(q)==pin for q,pin in pins.items());p.save_json(target,result);print(json.dumps(dict(files=len(files),bytes=total,receipt_sha256=p.sha(target))))
