"""Freeze the reviewed state prototype; preserve failed controls and raw source."""
import ast,datetime,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
notes=ROOT/'evidence/windows011-finite-state-mode-001-notes';packet=ROOT/'evidence/windows011-finite-state-mode-001.json'
assert not notes.exists() and not packet.exists()
review=ROOT/'.runs/windows011-finite-state-mode-review-001.json';assert review.is_file()
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
refs={};files=[];material=[];total=0
defs=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')]
assert len(defs)==2;exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'))
base=ROOT/'scripts/windows_native_slice'
names=('persistent_guard_build.py','persistent_guard_build.ps1','persistent_sid_guard.c','windows_process.py',
       'appcontainer_canary.py','appcontainer_launch.py','appcontainer_probe.c','appcontainer_dns.py','appcontainer_diagnostic.ps1')
protocols=[]
for filename,kind,group in (
 ('persistent_guard_build_protocol002.json','windows011-build-null-ABI-readiness-v1',names),
 ('persistent_guard_lifetime_protocol.json','windows011-persistent-SID-finite-canary-v1',names+('persistent_guard_state.py',))):
 target=base/filename;assert not target.exists()
 plan=dict(schema=1,kind=kind,source_base_head='580793ac6087021bf9567f764df5b9f55bfab9db',
  source_files_sha256={'scripts/windows_native_slice/'+name:p.sha(base/name) for name in group},
  prospective_only=True,Native_admitted=False,Windows_support=False,
  last_actual_build='evidence/windows011-build-actual001.json',last_verified_checkpoint='ca3261f2b93ae801458dd9ef94cdd051321be1ce',
  purpose='Fixed shared SDK build/NULL ABI; explicit sid-canary additionally tests durable ownership and existing parent/child IPv4TCP normal+cancel. No installer or Native.',
  bounds=dict(CI_minutes=3,controller_seconds=150,enclosure_seconds=170,each_compiler_seconds=30,normal_probe_seconds=15,cancel_probe_seconds=10,cancel_after_seconds=2,
              Job_memory_bytes=2*1024**3,per_log_bytes=256*1024,controller_stdout_bytes=1024**2,artifact_uploads=0,cache_uploads=0),
  predeclared_decision='One finite real-policy attempt after audited push/readback and public/no-active-CI preflight. A second corrective attempt needs a concrete source defect; otherwise retain/defer exact blocker. No installer loop, network fallback or Native admission.',
  unqualified=['IPv6','UDP','inbound','controller-death','reused identity refusal on actualWindows','lowbox state/policy mutation refusal','power-loss/BFE-off/boot','nonadmin installation','actual KiCad/JVM routing/cancel/export'],
  external_source_pin='Future audited fullcommit and this protocolSHA supplied through workflow input; exactGITHUB_SHA/detachedHEAD/source pins checked without a self-hash cycle.')
 p.save_json(target,plan);protocols.append(dict(path=str(target.relative_to(ROOT)),sha256=p.sha(target),kind=kind))
sources=[review,ROOT/'.runs/windows011-retained-hooks-review-001.json',ROOT/'.runs/windows011-state-authoring-001.json',
 ROOT/'.runs/windows011-state-authored-v1-001.py',Path(__file__)]
for stem in ('windows011-retained-hooks-targeted-001','windows011-retained-hooks-targeted-002','windows011-retained-hooks-targeted-003',
 'windows011-finite-canary-targeted-001','windows011-state-targeted-001','windows011-state-targeted-002','windows011-state-targeted-003',
 'windows011-profile-cleanup-condition-reversal-001'):
 for suffix in ('command','time'):sources.append(ROOT/'.runs'/(stem+'-'+suffix+'.log'))
for name in ('appcontainer_launch.py','result.json'):sources.append(ROOT/'.runs/windows011-profile-cleanup-condition-reversal-001'/name)
raw=[io.read_bytes(q,4*1024**2) for q in sources];assert sum(map(len,raw))<16*1024**2 and len(sources)<2000
for data in raw:assert b'\0' not in data;data.decode('utf8')
for q in sources:retain(q,Path(q.parent.name)/q.name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='Windows011-reviewed-unexecuted-finite-state-and-custody-mode',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 project_complete=False,CI_dispatched=False,actual_policy_operations=False,actual_profile_operations=False,Native_executed=False,Native_admitted=False,Windows_support=False,
 protocols=protocols,source_files_sha256={name:p.sha(ROOT/name) for name in plan['source_files_sha256']},
 source_review_sha256=p.sha(review),
 changes=['Exact live C owner plus host-only bounded flush journal/tombstones, no saved-state cleanup/adoption/reuse.',
          'BeginCreate before CreateProcess; actualhandle capture before fallible witnesses/policy reads; token/source/policy beforeResume; external errors poison.',
          'Live sealed retained-Job-zero+actual-created-process-signalled/exact-policy-absence proof before normal cleanup. Persistent ACL/identity failures retain profile; default branch unchanged.',
          'Actual own state bytes retained as bounded base64 log chunks, partial differs explicitly from lastcompletewrite; no previousowner census for export.',
          'Shared original compiler/Job/enclosure/DNS/probe/normal+cancel path, explicit finite stage, unchanged resourcecaps.'],
 pure_controls=dict(last_passed=True,tests=42,skips=1,last_cost=cost(ROOT/'.runs/windows011-state-targeted-003-time.log'),
  earlier_failed='state-targeted001 has2ASTtest-helper StopIteration errors, then002fixpasses; notWindows/routing failure',
  counterfactual='One-condition reversal produces3expected profile-retention failures; not an archived historical or actualWindows run.'),
 historical_scope='Actual001 at8b7 qualifies only originalf227C/build/NULL ABI. Current C capture order, shared ABI, state and callbacks remainunexecuted; do not promote oldresult.',
 evidence_limits='Source/AI review/purefaultcontrols only. All actualWindows policy/ACL/flush/denial/lifetime behavior remains unqualified until finiteCI; all missing protocols/external releasegates stayvisible. No Macproduct code/immutable035 changed.',
 accounting='All target/failure/time logs retained; authoring/research/AI review/freeze and wholeCI CPU unmeasured, notzero. No routing improvement or speed claim.',
 backup_scope='Audited essential owned source/control text only, notfullraw backup/restoration. Prepared035GUI/nojobs and completed035Native preserved.',
 files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
p.save_json(packet,record);print(json.dumps(dict(protocols=protocols,files=len(files),bytes=total,Native_admitted=False)))
