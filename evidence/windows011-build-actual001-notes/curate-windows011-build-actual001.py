"""Retain the actual fixed Windows build using the existing text/cost helpers."""
import ast,base64,datetime,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
notes=ROOT/'evidence/windows011-build-actual001-notes';packet=ROOT/'evidence/windows011-build-actual001.json'
assert not notes.exists() and not packet.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
functions=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='retain']
assert len(functions)==1;exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'))
base=ROOT/'.runs/windows011-build-actual001';head='8b7a35b574c587cdd223c1df4cee88cb4f1a6e6a'
r=f.read_json(base/'readiness.json');outer=f.read_json(base/'enclosure.json');job=f.read_json(base/'job.json');status=f.read_json(base/'status003.json')
assert status['headSha']==head and status['conclusion']=='success' and status['status']=='completed'
assert job['labels']==['windows-2022'] and job['conclusion']=='success' and job['runner_group_name']=='GitHub Actions'
assert [s['conclusion'] for s in job['steps']]==['success']*len(job['steps'])
assert all(j['conclusion']=='skipped' for j in status['jobs'] if j['name']!='windows-guard-build')
assert r['passed'] is outer['passed'] is True and r['errors']==[]
assert all(r[k] is False for k in ('accepted','Windows_support','Native_admitted','Native_executed','actual_policy_operations','actual_profile_operations','socket_tests_performed','installer_executed'))
assert r['expected_source_sha']==outer['expected_source_sha']==head
assert r['protocol_sha256']==outer['expected_protocol_sha256']=='47719c1f482aa5c124796af7083076a49b959ee968f760ad9aecd234c3b32900'
plan=json.loads(subprocess.check_output(['git','show',head+':scripts/windows_native_slice/persistent_guard_build_protocol.json']))
assert plan['source_files_sha256']==r['source_files_sha256']
for name,pin in plan['source_files_sha256'].items():assert hashlib.sha256(subprocess.check_output(['git','show',head+':'+name])).hexdigest()==pin
c=r['compiler_process'];assert c['status']=='success' and c['exit_code']==0 and c['cleanup_complete'] is True
assert c['compiler_output']['validated'] is True and c['compiler_output']['role']=='persistent-sid-guard' and c['compiler_output']['validation_after_job_reaped'] is True
assert c['limits']['seconds']==30 and c['limits']['log']==256*1024 and c['os_job_memory_limit'] is True
assert c['compiler_finalization']['zero_active_processes_verified'] is True
assert outer['controller_reaped'] is True and outer['timed_out'] is False
abi=r['NULL_ABI'];assert abi['passed'] is True and abi['INFO_bytes']==196 and len(abi['exports_bound'])==12 and len(abi['outcomes'])==14
assert all(x['passed'] is True and x['actual']==x['expected'] for x in abi['outcomes'])
assert abi['valid_owner_created'] is False and abi['valid_SID_supplied'] is False and abi['actual_policy_operations'] is False
chunks=[]
for line in (base/'actions.log').read_text().splitlines():
 at=line.find('{')
 if at<0:continue
 try:d=json.loads(line[at:])
 except ValueError:continue
 if isinstance(d,dict) and d.get('kind')=='compiler-log-base64-chunk':chunks.append(d)
assert [d['index'] for d in chunks]==list(range(len(chunks)))
raw=b''.join(base64.b64decode(d['data'],validate=True) for d in chunks)
assert raw==(base/'compile-guard.log').read_bytes() and len(raw)==r['compiler_log']['bytes']
assert hashlib.sha256(raw).hexdigest()==r['compiler_log']['sha256']==c['log_sha256'] and not r['compiler_log']['truncated']
review=ROOT/'.runs/windows011-build-result-review-001.json';assert review.is_file()
sources=[base/name for name in ('pre-dispatch.json','dispatch.stdout.log','dispatch.stderr.log','status001.json','status002.json','status003.json','actions.log','readiness.json','enclosure.json','job.json','compile-guard.log')]
sources += [review,Path(__file__),ROOT/'.runs/freeze-windows011-build-readiness-001-command.log',ROOT/'.runs/freeze-windows011-build-readiness-001-time.log']
raws=[io.read_bytes(q,4*1024**2) for q in sources];assert sum(map(len,raws))<16*1024**2 and len(sources)<2000
for raw in raws:assert b'\0' not in raw;raw.decode('utf8')
for q in sources:retain(q,Path(q.name))
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='Windows011-actual-fixed-DLL-build-and-NULL-ABI-only',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 project_complete=False,source_head=head,protocol_sha256=r['protocol_sha256'],source_files_sha256=r['source_files_sha256'],
 CI=dict(run_id=39206502674,url=status['url'],job_id=job['id'],runner_labels=job['labels'],status='completed',conclusion='success',
         started_at=job['started_at'],completed_at=job['completed_at'],job_elapsed_seconds=23,all_other_modes_skipped=True,
         artifact_uploads=0,cache_uploads=0,incremental_spending=0),
 build_passed=True,NULL_ABI_passed=True,actual_Windows=True,actual_policy_operations=False,actual_profile_operations=False,
 Native_executed=False,Native_admitted=False,Windows_support=False,accepted=False,
 observations=dict(DLL_bytes=c['compiler_output']['bytes'],DLL_sha256=c['compiler_output']['sha256'],SDK=r['compiler_tools'],
                   C_warnings_suppressed=False,Job_cleanup_complete=True,compiler_processes=c['process_count'],ABI_exports=12,NULL_refusal_cases=14,INFO_bytes=196),
 costs=dict(compiler_wall_seconds=c['wall_seconds'],compiler_full_job_CPU_seconds=c['full_job_cpu_seconds'],
            Python_wall_seconds_before_report=r['wall_seconds_before_report'],Python_CPU_seconds_before_report=r['controller_CPU_seconds_before_report'],
            external_enclosure_wall_seconds_before_exit=outer['wall_seconds_before_exit'],exited_Python_process_CPU_seconds=outer['controller_process_CPU_seconds'],
            whole_external_PowerShell_job_CPU_seconds=None,freeze_wall_seconds=0.15,freeze_CPU_seconds=0.09),
 accounting='23second hosted job timestamps include checkout/setup. Python and compiler figures are nested, not additive wall runtimes. Compiler includes exited descendants; exitedPythonCPU is separate. CompletePowerShell/CI CPU and authoring/research/AI review are unknown, notzero. No routing-runtime or speed claim.',
 review=dict(path=str(review.relative_to(ROOT)),sha256=p.sha(review),scope='Separate AI actual-source/result readback, not human review.'),
 limits='Only fixed C compile/AMD64 DLL load/export/signature/INFO-layout and14NULL refusals. No valid owner, freshSID, policy, profile, socket, denial, filesystem lowbox, cancellation/crash/reuse, KiCad installer or Native ran.00910060 failure is unchanged. DLL raw bytes were not uploaded/retained from runner; only actual pinned identity and source/build evidence remain.',
 next='Implement/review host journal/tombstones and retained actual Job/process callbacks before a finite real-policy/lifetime canary; do not repeat installer or admit Windows Native. Next ABI sharing source is an unexecuted draft after8b7, not this run.',
 backup_scope='Small sanitized actualCI logs/results/source references intended for audited Git checkpoint; not fullraw artifact backup/restoration. Mac035 preparedGUI and newer fullraw remainMac-only outside008/010.',
 files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
p.save_json(packet,record)
print(json.dumps(dict(build_passed=True,NULL_ABI_passed=True,Native_admitted=False,files=len(files),bytes=total)))
