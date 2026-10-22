"""Retain source repair and targeted results; not Native/build qualification."""
from pathlib import Path
import ast,hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv,placement_clearance as io
from scripts.report_current_comparison import complete_cost
notes=ROOT/'evidence/native7-return-publication-repair-001-notes';target=ROOT/'evidence/native7-return-publication-repair-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='retain'];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper),'exec'),globals())
queue={Path(__file__):'administration/retain.py',ROOT/'.runs/return-session-main-change-001.patch':'source/change.patch',ROOT/'.runs/return-session-source-recommendation-001.json':'review/recommendation.json',ROOT/'.runs/return-session-integrated-source-review-001.json':'review/integrated-source.json'}
costs=[]
for label,count,passed in [('return-session-targeted-001',106,False),('return-session-targeted-002',106,True),('return-session-targeted-native7-001',158,False),('return-session-targeted-correction-001',24,True)]:
 log=ROOT/'.runs'/(label+'-time.log');raw=log.read_text()
 assert 'Ran '+str(count)+' tests in ' in raw and ('\nOK\n' in raw)==passed
 if label=='return-session-targeted-001':assert 'FAILED (failures=2, errors=1)' in raw
 if label=='return-session-targeted-native7-001':assert 'FAILED (errors=6)' in raw and raw.count('ValueError: shipped single Improve parent contract differs')==6
 costs.append(dict(run=label,passed=passed,Native=False,complete_cost=complete_cost(log)))
 for suffix in ('.log','-time.log'):queue[ROOT/'.runs'/(label+suffix)]='tests/'+label+suffix
source_names=['autorouter/pipeline.py','autorouter/strategy.py','autorouter/_improve_context.py','autorouter/floor_route.py','tests/test_publication_readback_scope.py','tests/test_strategy.py','tests/test_native7_improve_child_context.py','tests/test_native7_improve_parent.py','tests/test_native7_context_reuse.py','tests/test_native7_improve_single.py','tests/test_pruning_scoring.py','tests/test_improve_readback_identity.py']
source_pins={name:p.sha(ROOT/name) for name in source_names}
review=json.loads((ROOT/'.runs/return-session-integrated-source-review-001.json').read_bytes())
pins={q:p.sha(q) for q in queue}
for q,name in queue.items():retain(q,Path(name))
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material))
result=dict(schema=1,kind='working-source-native7-Improve-publication-return-repair-v1',accepted=False,production_admitted=False,project_complete=False,Native_qualification=False,actual_GUI=False,new_runtime_built=False,human_review=False,source_base_checkpoint='7a715a4dc10ecb9e6376dac4051093adf271268f',source_sha256=source_pins,
 failure='evidence/runtime058-natural-expiry-001.json',diagnostic='evidence/runtime058-return-timing-001.json',
 change='Only Native7 Improve publication opts into existing scoped Context construction/S-expression parse reuse. All three stable callbacks, one full parent/privatechild/trial stored reader, original/tool/material/Native/Default/selection/PRL guards remain. No accepted-result cache, changed original constraint or new execution authority.',
 cleanup='Readback scope enters inside shared publish try and exits before final wall/fullCPU acceptance caps/final_check; cleanup errors/cancellation take existing owned archive/negative path. Destination owner and exact report/canonical receipt equality rechecked after exit. ContextVar token resets even when cache clearing raises.',
 scheduling=dict(old_reserve_seconds=25,new_reserve_seconds=40,global_route_caps_unchanged=True,shared_constant='autorouter._improve_context.RESERVE_SECONDS',native90_work_limit_seconds=50,mechanism='Withhold work time for actual proof/native publication rather than raising job budget. Measured scoped proof worker28.381s plus observed final Native steps2.940s motivated40s planning reserve; not a universal bound or native success. Less time remains for incumbent/search/trials.'),
 tests=costs,focused_controls='All publication proof callbacks still run in-session; post-exit expiry of wall or CPU, cleanup RuntimeError/KeyboardInterrupt, receipt/report mutation, output replacement and token-reset failures tested with authored files. Six current scope controls pass. Existing private Context/Budget, native7 lineage, material/PRL/cache/selection/source/preference controls retain their explicit Native mocks or authored fixtures; no new Native claim.',
 failed_test_administration='First106-run had2 outdated adaptive95 work-limit expectations and1 legacy test import needing project-test path. Corrected106 passes after80 expectations and child-only PYTHONPATH=tests. Native7-targeted158 had6 errors solely from temporary migration of historical reporter fixture25→40; kept reporter/versioned25 test unchanged and reran that module plus the expanded scope module24pass. Remaining152 tests in that run passed; no Native executed. Raw failures/costs preserved; no hidden rerun or weakened production checks.',
 compatibility='Historical058/25 runtime and its eighteen-arm report/protocols remain immutable. Current comparison reporter/freezer still pin25 and must be consciously migrated/versioned before any new40-policy benchmark; not used to qualify this source repair. Two mocked-reader fixtures now save authored canonical result.json for the new identity intake; central guard not weakened.',
 remaining='Full integration, new immutable runtime, fresh Native90 return and canonical/archived controls, native/install/actualGUI qualification required. No broader completion/electrical/cleanup/Windows/independent install/release claim.',
 review_scope='AI source review only; not Native execution or human PCB review.',accounting='All test costs listed separately including failures. Timing diagnostics and source/AI/authoring/curation are additional; unknown overhead not zero. Nested costs are not added to external complete exits.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
assert all(p.sha(q)==pin for q,pin in pins.items()) and all(p.sha(ROOT/name)==pin for name,pin in source_pins.items())
p.save_json(target,result);print(json.dumps(dict(files=len(files),bytes=total,receipt_sha256=p.sha(target))))
