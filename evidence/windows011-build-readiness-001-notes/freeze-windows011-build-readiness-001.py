"""Freeze the no-policy Windows build gate and retain bounded source reviews."""
import ast, datetime, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
notes=ROOT/'evidence/windows011-build-readiness-001-notes'
packet=ROOT/'evidence/windows011-build-readiness-001.json'
protocol=ROOT/'scripts/windows_native_slice/persistent_guard_build_protocol.json'
assert not any(q.exists() for q in (notes,packet,protocol))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
functions=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')]
assert len(functions)==2
refs={};files=[];material=[];total=0
exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'))
names=('persistent_guard_build.py','persistent_guard_build.ps1','persistent_sid_guard.c','windows_process.py',
       'appcontainer_canary.py','appcontainer_launch.py','appcontainer_probe.c','appcontainer_dns.py','appcontainer_diagnostic.ps1')
pins={('scripts/windows_native_slice/'+name):p.sha(ROOT/'scripts/windows_native_slice'/name) for name in names}
review=ROOT/'.runs/windows011-readiness-independent-review-001.json'
assert review.is_file();review_data=f.read_json(review)
plan=dict(schema=1,kind='windows011-build-null-ABI-readiness-v1',
          source_base_head='580793ac6087021bf9567f764df5b9f55bfab9db',source_files_sha256=pins,
          accepted=False,Native_admitted=False,Windows_support=False,
          purpose='Compile the one fixed owned C DLL and exercise14NULL-only ABI refusals. No validSID/owner, policy, profile, sockets, installer or Native.',
          bounds=dict(CI_minutes=3,whole_controller_seconds=150,parent_enclosure_seconds=170,compiler_job_seconds=30,
                      compiler_job_memory_bytes=2*1024**3,compiler_log_bytes=256*1024,artifact_uploads=0,cache_uploads=0),
          external_source_pin='The audited future commit SHA must be supplied separately as workflow input, equal to GITHUB_SHA/detached HEAD. This protocol cannot pin its containing commit without a hash cycle.',
          resource_policy='One standard windows-2022 public-repository job, contents:read, pinned checkout, no persisted credentials, no dependencies/installers/downloaded boards or new spending.',
          prospective_only=True)
p.save_json(protocol,plan)
sources=[review,ROOT/'.runs/windows011-independent-source-review-001.json',ROOT/'.runs/windows011-independent-C-review-001.json',
 ROOT/'.runs/windows011-C-guard-interface-001.json',ROOT/'.runs/windows011-C-v1-retained-001.c',ROOT/'.runs/windows011-C-v2-retained-001.c',Path(__file__)]
for number in ('001','002'):
 for suffix in ('command','time'):sources.append(ROOT/'.runs'/('windows011-compiler-targeted-'+number+'-'+suffix+'.log'))
# The shared retention limits stay unchanged. Preflight every exact input first.
raws=[io.read_bytes(q,4*1024**2) for q in sources]
assert sum(map(len,raws))<16*1024**2 and len(sources)<2000
for raw in raws:assert b'\0' not in raw;raw.decode('utf8')
for q in sources:retain(q,Path(q.name))
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='Windows011-prospective-build-readiness-with-source-fixes',
 recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,
 compiled=False,CI_dispatched=False,actual_policy_operations=False,actual_profile_operations=False,
 Native_executed=False,Native_admitted=False,Windows_support=False,
 source_base_head=plan['source_base_head'],source_files_sha256=pins,
 frozen_protocol=dict(path=str(protocol.relative_to(ROOT)),sha256=p.sha(protocol)),
 current_C=dict(path='scripts/windows_native_slice/persistent_sid_guard.c',sha256=pins['scripts/windows_native_slice/persistent_sid_guard.c'],
                bytes=(ROOT/'scripts/windows_native_slice/persistent_sid_guard.c').stat().st_size,ABI=1,INFO_bytes=196),
 historical_ABI='The retained original interface receipt pins397-lineb8c03d, not current409-linef2276f. Export signatures/196-byte layout are unchanged; current source pins above supersede only that source metadata.',
 source_fixes=['Retained process duplicate must pass GetProcessId before clearing pending-create. Generic signalled handles cannot stand for process death; failure remains poisoned with duplicate owned.',
               'Object ownerSYSTEM/groupBuiltinAdministrators are explicitly set/read alongside original protected exact2ACE DACL. No privilege enabling/fallback; actual BFE ownership may refuse.'],
 prospective_order=['Exclusively reserve never-reused profile name before profile creation.',
                    'CreateProfile must returnS_OK and actual fresh baseSID; PG_Create then generates fiveGUIDs.',
                    'Durably persist actualSID+keys+source/controller/DLL/tool pins BEFORE any PG_Arm or launch.',
                    'Unknown/crashed ownership retains remaining deny/profile/state forever; never later adopt/remove/reuse.'],
 contract_limits='Journal/tombstone and typed retained runner callbacks are NOT implemented. filterId/effectiveWeight are not exported or claimed collected. This build gate never supplies a validSID/owner or changes policy.',
 targeted_pure_controls={n:dict(passed=True,tests=31,cost=cost(ROOT/'.runs'/('windows011-compiler-targeted-'+n+'-time.log'))) for n in ('001','002')},
 review=dict(kind='Separate AI source review, not human review or Windows execution',readiness_sha256=p.sha(review),C_review_sha256=p.sha(ROOT/'.runs/windows011-independent-C-review-001.json')),
 remaining=['Actual fixed build/NULL ABI readiness','Host-only durable journal/tombstone and exact profile/source/DLL/tool binding',
            'Typed pending-create/poison and actual retained Job/process callbacks through final removal',
            'Native Windows positive/explicit denial parent+child IPv4/IPv6 TCP/UDP/inbound and lowbox mutation-refusal controls',
            'Observed normal/cancel/controller-death/reuse/assignment failure behavior and final exact object absence or retained orphan',
            'Actual KiCad export/routing/import/refill/validation/cancel/candidate export with equivalent safeguards'],
 Mac='Immutable runtime035 source7edc7229/manifest8f0c455d unchanged; full178/install008/ordinary/invalidNative complete, actualGUI076 pending. No Mac rebuild or completed trial repeated.',
 costs='Two targeted local runs are additional to all historical routing. Source authoring/research/AI review/freeze/interactive/CI CPU not independently measured and notzero. No routing speed/effectiveness claim.',
 backup_scope='Essential source/review/text for audited development checkpoint only. Newer fullraw and preparedGUI remainMac-only outside008/010; no restoration or backup-system change.',
 files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
assert all(p.sha(ROOT/name)==pin for name,pin in pins.items())
p.save_json(packet,record)
print(json.dumps(dict(protocol_sha256=p.sha(protocol),files=len(files),bytes=total,compiled=False,Native_admitted=False)))
