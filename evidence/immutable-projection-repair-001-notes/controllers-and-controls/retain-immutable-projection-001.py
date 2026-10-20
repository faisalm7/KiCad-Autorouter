"""Retain owned pure projection controls using the existing bounded curator."""
from pathlib import Path
import ast,datetime,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
notes=ROOT/'evidence/immutable-projection-repair-001-notes';target=ROOT/'evidence/immutable-projection-repair-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
result=json.loads((ROOT/'.runs/derived-copy-control-001/result.json').read_bytes())
assert result['passed'] and result['same_exact_output'] and result['source_unchanged'] and result['Native_executed'] is False
assert result['pipeline_sha256']==p.sha(ROOT/'autorouter/pipeline.py')
log=(ROOT/'.runs/immutable-projection-targeted-001-time.log').read_text();assert 'Ran 7 tests' in log and '\nOK\n' in log
for name in ('check-derived-copy-001.py','derived-copy-control-001.log','derived-copy-control-001-time.log','immutable-projection-targeted-001.log','immutable-projection-targeted-001-time.log','immutable-projection-source-review-001.json'):
 retain(ROOT/'.runs'/name,Path('controllers-and-controls')/name)
retain(ROOT/'.runs/derived-copy-control-001/result.json',Path('synthetic/result.json'))
retain(Path(__file__),Path('administration')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='pure-derived-fill-projection-development-checkpoint-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,change='Remove only root routes and direct root-zone derived fill before deepcopy for immutable comparison; discard old direct derived fill before transplant deepcopy. Retained intent is independently copied; refill route/net identity still runs first. No Native, semantic or authority checks skipped; no bounds raised.',mechanism='Instrumented051 profile showed repeated immutable/transplant deepcopies of fill that was immediately discarded. This general pure projection avoids copying discarded geometry, independent of board names or route scores.',targeted=dict(passed=True,tests=7,complete_cost=cost(ROOT/'.runs/immutable-projection-targeted-001-time.log'),scope='Exact prior-function output oracle, unknown/nested fields, all root route kinds, input immutability, disjoint output lists, lost-zone and route/net/UUID/kind/missing-route refusals. Some fill-equivalence controls explicitly stub only the identity seam; real identity refusals also run.'),synthetic=dict(result=result,complete_cost=cost(ROOT/'.runs/derived-copy-control-001-time.log'),scope='Owned synthetic AST only, not actual board/job speed or Native validation. Generated large AST stays local; reproducible controller retained.'),qualification='Combine with already checkpointed fixed-bound LRU syntax change before full203 and new runtime053. Full integration and actual installed delivery still required. No promotion/retry/stitch of050/051/052 results.',actual_GUI=False,Native_executed=False,human_review=False,costs='Measured complete exits counted once. Research, authoring, AI review and curation additional/partly unmetered, not zero. Profile cumulative entries overlap.',backup_scope='Owned source and small evidence checkpoint only. Later raw stays Mac-only/outside010; no full restoration repeated or disk-failure protection claimed.',source_sha256={str(q.relative_to(ROOT)):p.sha(q) for q in (ROOT/'autorouter/pipeline.py',ROOT/'autorouter/sexpr.py',ROOT/'tests/test_immutable_projection.py')},files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,project_complete=False)))
