"""Retain the second, final policy attempt: an actual compile failure only."""
import ast,base64,datetime,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
notes=ROOT/'evidence/windows011-policy-attempt002-compile-failure-001-notes'
packet=ROOT/'evidence/windows011-policy-attempt002-compile-failure-001.json'
assert not notes.exists() and not packet.exists()
base=ROOT/'.runs/windows011-lifetime-actual002';head='b89b032427246702284e1dea915a8054fd215cfc'
r=f.read_json(base/'readiness.json');outer=f.read_json(base/'enclosure.json');job=f.read_json(base/'job.json');status=f.read_json(base/'status002.json')
assert status['headSha']==head and status['status']=='completed' and status['conclusion']=='failure'
assert job['labels']==['windows-2022'] and job['conclusion']=='failure' and job['runner_group_name']=='GitHub Actions'
assert all(j['conclusion']=='skipped' for j in status['jobs'] if j['name']!='windows-guard-build')
assert r['passed'] is outer['passed'] is False and r['stage']==outer['stage']=='sid-canary'
assert r['expected_source_sha']==outer['expected_source_sha']==head
assert r['protocol_sha256']==outer['expected_protocol_sha256']=='434d2a04edb496336e700f1259e3c257cd38e42c3dec3e455a25872f9ffef414'
plan=json.loads(subprocess.check_output(['git','show',head+':scripts/windows_native_slice/persistent_guard_lifetime_protocol002.json']))
for name,pin in plan['source_files_sha256'].items():assert hashlib.sha256(subprocess.check_output(['git','show',head+':'+name])).hexdigest()==pin
assert r['NULL_ABI'] is None
assert all(r[k] is False for k in ('accepted','Windows_support','Native_admitted','Native_executed','actual_policy_operations','actual_profile_operations','socket_tests_performed','installer_executed'))
c=r['compiler_process'];assert c['exit_code']==2 and c['status']=='budget_exceeded' and c['cleanup_complete'] is True
assert c['limits']['seconds']==30 and c['process_count']==3 and outer['controller_reaped'] is True and outer['timed_out'] is False
assert c['authoring']['guard_source_sha256']=='082ba80972f0484547897608bfffcd7f16d050b9e4aabe7e409bf6455e73d702'
chunks=[]
for line in (base/'actions.log').read_text().splitlines():
 at=line.find('{')
 if at<0:continue
 try:d=json.loads(line[at:])
 except ValueError:continue
 if isinstance(d,dict) and d.get('kind')=='compiler-log-base64-chunk':chunks.append(d)
assert [d['index'] for d in chunks]==list(range(len(chunks)))
raw=b''.join(base64.b64decode(d['data'],validate=True) for d in chunks)
assert raw==(base/'compile-guard.log').read_bytes() and len(raw)==r['compiler_log']['bytes']==324
assert hashlib.sha256(raw).hexdigest()==c['log_sha256']==r['compiler_log']['sha256']=='564f5714427deb35ace5998e531cdad6535c1c5974dfe22416e7f64b30dd337c'
assert b'C4389' in raw and b'C2220' in raw and not r['compiler_log']['truncated']
review=ROOT/'.runs/windows011-lifetime-actual002-cast-review-001.json'
assert p.sha(review)=='bc0c0459f28440d258e079d8fec00a0a79555468bdcbc7d20163e2f544491c67'
v=f.read_json(review);assert v['actual']['source_commit']==head
sources=[base/name for name in ('pre-dispatch.json','dispatch.stdout.log','dispatch.stderr.log','status001.json','status002.json','actions.log','readiness.json','enclosure.json','job.json','compile-guard.log')]+[review,Path(__file__)]
raws=[io.read_bytes(q,4*1024**2) for q in sources];assert sum(map(len,raws))<16*1024**2 and len(sources)<2000
for raw in raws:assert b'\0' not in raw and not re.search(rb'key-[0-9a-f]{32}(?![0-9a-f])',raw);raw.decode('utf8')
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
refs={};files=[];material=[];total=0
defs=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='retain']
assert len(defs)==1;exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'))
for q in sources:retain(q,Path('controllers-reviews-logs')/q.name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='Windows011-second-final-policy-attempt-compile-failure',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,
 source_head=head,protocol_sha256=r['protocol_sha256'],source_files_sha256=plan['source_files_sha256'],
 CI=dict(run_id=39210366235,url=status['url'],job_id=job['id'],runner_labels=job['labels'],status='completed',conclusion='failure',run_elapsed_seconds=51,job_elapsed_seconds=47,control_step_seconds=33,all_other_modes_skipped=True,artifact_uploads=0,cache_uploads=0,incremental_spending=0),
 build_passed=False,NULL_ABI_passed=False,actual_Windows=True,actual_policy_operations=False,actual_profile_operations=False,Native_executed=False,Native_admitted=False,Windows_support=False,accepted=False,
 observations=v['actual'],costs=v['costs'],efficiency_finding=v['nonblocking_efficiency_finding'],
 decision='Both real-policy011 attempts failed; this two-attempt protocol is closed. No third real-policy attempt. A distinct build-null-only regression may check the reviewed DWORD cast without owner/profile/policy/socket/Native execution.',
 previous_actual001='evidence/windows011-lifetime-actual002.json (public alias of first actual run39208796011, not this second execution)',
 correction=dict(source_path='scripts/windows_native_slice/persistent_sid_guard.c',source_sha256=v['cast_review']['new_source_sha256'],scope=v['cast_review']['assessment'],runtime_qualified=False),
 review=dict(path=str(review.relative_to(ROOT)),sha256=p.sha(review),scope='Separate AI exact raw/source readback. No execution or human review.'),
 accounting='Compiler Job and exited controller CPU are distinct; measured subtotal0.75s. Nested report CPU is not added. WholeCI/PowerShell, authoring/research/AI review and curation are additional or unknown, not zero. No routing or speed claim.',
 backup_scope='Essential small source/log/result references intended for audited Git. No DLL/state/profile/policy was created by this execution. Newer full Mac raw and prepared GUI remain Mac-only outside008/010; this is not a restoration.',
 files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
p.save_json(packet,record);print(json.dumps(dict(files=len(files),bytes=total,build_passed=False,policy_protocol_closed=True)))
