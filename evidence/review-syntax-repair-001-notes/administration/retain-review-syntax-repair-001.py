"""Retain owned performance diagnosis and initial syntax repair controls only."""
from pathlib import Path
import ast,datetime,hashlib,json,pstats,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
notes=ROOT/'evidence/review-syntax-repair-001-notes';target=ROOT/'evidence/review-syntax-repair-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
b=ROOT/'.runs/runtime050-improve-review-profile-003';read=lambda q:json.loads(q.read_bytes())
assert read(b/'command.log')=={'status':'rejected','reason':'review copy exceeded 30-second wall or full CPU ceiling'}
assert read(b/'execution.json')['inputs_tools_unchanged'] is True
stats=pstats.Stats(str(b/'review.pstats'))
rows=[]
for (filename,line,function),(primitive,calls,self_time,cumulative,callers) in stats.stats.items():
    rows.append(dict(file=Path(filename).name,line=line,function=function,primitive_calls=primitive,calls=calls,self_seconds=self_time,cumulative_seconds=cumulative))
facts=dict(schema=1,kind='instrumented-original050-review-profile-facts',total_calls=stats.total_calls,primitive_calls=stats.prim_calls,instrumented_seconds=stats.total_tt,largest_cumulative=sorted(rows,key=lambda r:r['cumulative_seconds'],reverse=True)[:40],largest_self=sorted(rows,key=lambda r:r['self_seconds'],reverse=True)[:15],profile_sha256=p.sha(b/'review.pstats'),profile_local_only=True,actual_product_status='rejected',profiler_process_exit_zero_is_not_delivery=True,scope='Instrumentation overhead additional. First central check exhausted unchanged30s observed cap; this is not normal timing or a new routing attempt. Original cohort remains failed/not-delivered.')
p.save_json(b/'facts.json',facts)
queue=[]
for number in ('001','002','003'):
    for suffix in ('.py','.log','-time.log'):
        queue.append((ROOT/'.runs'/('profile-runtime050-improve-review-'+number+suffix),Path('profile/controllers')/('profile-'+number+suffix)))
for number in ('001','003'):
    folder=ROOT/'.runs'/('runtime050-improve-review-profile-'+number)
    for name in ('execution.json','protocol.json','command.log'):
        if (folder/name).is_file():queue.append((folder/name,Path('profile')/number/name))
queue.append((b/'facts.json',Path('profile/facts.json')))
for name in ('runtime050-improve-review-failure-source-review-001.json','runtime050-parent-reuse-test-review-001.json','sexpr-memo-source-review-001.json','run-sexpr-memo-targeted-003.py'):
    queue.append((ROOT/'.runs'/name,Path('review-and-controls')/name))
for number in ('001','002','003'):
    for suffix in ('.log','-time.log'):
        queue.append((ROOT/'.runs'/('sexpr-memo-targeted-'+number+suffix),Path('review-and-controls')/('targeted-'+number+suffix)))
for name in ('command.log','execution.json'):queue.append((ROOT/'.runs/sexpr-memo-targeted-003'/name,Path('review-and-controls/targeted003')/name))
queue.append((Path(__file__),Path('administration')/Path(__file__).name))
for path,name in queue:retain(path,name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='review-syntax-repair-development-checkpoint-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,old_product='runtime050',frozen_comparison='evidence/runtime050-default-improve-development-001.json',frozen_comparison_unchanged=True,profile=facts,actual_profile_complete_cost=cost(ROOT/'.runs/profile-runtime050-improve-review-003-time.log'),failed_preparations=[dict(attempt='profile001',outcome='disk guard refused before launch; cwd counted installedruntime',cost=cost(ROOT/'.runs/profile-runtime050-improve-review-001-time.log')),dict(attempt='profile002',outcome='controller syntax error before launch',cost=cost(ROOT/'.runs/profile-runtime050-improve-review-002-time.log')),dict(attempt='targeted002',outcome='nonexistent test module detected before controller creation; logged nonexistentcontroller failure',cost=cost(ROOT/'.runs/sexpr-memo-targeted-002-time.log'))],targeted=dict(passed=True,tests=103,complete_cost=cost(ROOT/'.runs/sexpr-memo-targeted-003-time.log'),earlier_seven_tests_cost=cost(ROOT/'.runs/sexpr-memo-targeted-001-time.log')),change='Operation-local pure S-expression syntax memo; immutable stored tree and independent caller lists; bounded8MiB rawinputs/250000nodes/64entries. File reads and semantic/context/owner/Native/PRL checks all rerun. Native7 parent/privatechild reuse exclusions unchanged. No cap increase.',qualification='Source change only; full integration, new numbered runtime Native/install/GUI qualification remain required. No new delivered routing or comparison gain inferred.',additional_cost='Research, authoring, AIreview and curation additional/partly unmetered, notzero. Profile self/cumulative entries overlap and must not be summed.',backup_scope='Owned source/metadata intended for auditedGit. Binaryprofile and later raw remain on thisMac/outside010; no restoration repeat or new diskfailure protection.',source_sha256={str(q.relative_to(ROOT)):p.sha(q) for q in [ROOT/'autorouter/sexpr.py',ROOT/'autorouter/pipeline.py',ROOT/'tests/test_sexpr_memo.py']},files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,project_complete=False)))
