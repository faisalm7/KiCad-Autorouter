"""Retain the failed real-policy attempt, including actual own state bytes."""
import ast,datetime,hashlib,json,subprocess,sys
from pathlib import Path,PureWindowsPath
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
notes=ROOT/'evidence/windows011-lifetime-actual001-notes';packet=ROOT/'evidence/windows011-lifetime-actual001.json'
assert not notes.exists() and not packet.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
defs=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='retain'];exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'))
base=ROOT/'.runs/windows011-lifetime-actual001';head='acdffee4276074cea454d940cbc2e018f6130944'
r=f.read_json(base/'readiness.json');c=f.read_json(base/'canary.json');outer=f.read_json(base/'enclosure.json');job=f.read_json(base/'job.json');status=f.read_json(base/'status002.json')
assert status['headSha']==head and status['status']=='completed' and status['conclusion']=='failure'
assert job['labels']==['windows-2022'] and job['conclusion']=='failure'
assert all(j['conclusion']=='skipped' for j in status['jobs'] if j['name']!='windows-guard-build')
assert r['passed'] is c['passed'] is outer['passed'] is False and r['NULL_ABI']['passed'] is True
assert all(r[k] is False for k in ('accepted','Windows_support','Native_admitted','Native_executed','installer_executed'))
assert outer['controller_reaped'] is True and not outer['timed_out']
assert r['expected_source_sha']==outer['expected_source_sha']==head and r['protocol_sha256']==outer['expected_protocol_sha256']=='0d99695a49d131656ac460e30e8ce9db998317e939c7899d5c95f9cc322fcdeb'
raw_plan=subprocess.check_output(['git','show',head+':scripts/windows_native_slice/persistent_guard_lifetime_protocol.json']);assert hashlib.sha256(raw_plan).hexdigest()==r['protocol_sha256'];plan=json.loads(raw_plan)
for name,pin in plan['source_files_sha256'].items():assert hashlib.sha256(subprocess.check_output(['git','show',head+':'+name])).hexdigest()==pin
assert c['cases']==[] and c['cleanup']['cleanup_complete'] is False and c['cleanup']['persistent_removal_verified'] is False
assert c['owned_server_thread_reaped'] is True and len(c['independently_positive_connections_before'])==2
assert all(x['connected'] is True and x['payload_bytes_sent']==0 for x in c['independently_positive_connections_before'])
state=r['persistent_guard'];info=state['last_live_C_info']
assert state['phase']=='orphan' and state['poisoned'] and state['abandoned'] and not state['verified_removal_observed']
assert info['jobs']==info['processes']==0 and info['policy_may_exist']==1 and info['abort_error']==0
assert any('1307' in value for value in state['errors']) and r['state_material']['complete'] is True
for row in r['state_material']['files']:
 path=base/'state'/row['name'];assert p.sha(path)==row['sha256'] and path.stat().st_size==row['bytes'] and row['matches_last_complete_write']
assert len(r['state_material']['files'])==9
context_path=next((base/'state').glob('context-*.json'));context=f.read_json(context_path)
pins={PureWindowsPath(name).name:pin for name,pin in context['source_pins'].items()}
assert pins=={**{Path(name).name:pin for name,pin in plan['source_files_sha256'].items()},'persistent-sid-guard.dll':r['DLL']['sha256']}
witness=dict(source_head=head,protocol_sha256=r['protocol_sha256'],source_files_sha256=plan['source_files_sha256'])
assert hashlib.sha256(json.dumps(witness,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')).hexdigest()==context['live_witness_sha256']
journal_path=next((base/'state').glob('name-*.jsonl'));prefix=b'';events=[]
for line in journal_path.read_bytes().splitlines(keepends=True):
 row=json.loads(line);assert row['seq']==len(events) and row['previous_sha256']==hashlib.sha256(prefix).hexdigest();prefix+=line;events.append(row['event'])
assert events==['RESERVED','PREPARED','CONTEXT','ORPHAN','ABANDONED'] and hashlib.sha256(prefix).hexdigest()==state['journal']['sha256']
processes=[r['compiler_process'],c['DNS_process'],*c['builds']]
assert all(q['status']=='success' and q['cleanup_complete'] is True for q in processes)
cpu=sum(q['full_job_cpu_seconds'] for q in processes)+outer['controller_process_CPU_seconds'];assert cpu==2.28125
review=ROOT/'.runs/windows011-owner1307-bounded-review-001.json';assert review.is_file()
sources=[q for q in base.iterdir() if q.is_file()]+list((base/'state').iterdir())+[review,Path(__file__)]
raws=[io.read_bytes(q,4*1024**2) for q in sources];assert sum(map(len,raws))<16*1024**2 and len(sources)<2000
for raw in raws:assert b'\0' not in raw;raw.decode('utf8')
for q in sources:retain(q,Path('state' if q.parent.name=='state' else 'logs-results-reviews')/q.name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='Windows011-actual001-real-policy-refusal-owner1307',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 project_complete=False,source_head=head,protocol_sha256=r['protocol_sha256'],source_files_sha256=plan['source_files_sha256'],
 CI=dict(id=39208796011,url=status['url'],status='completed',conclusion='failure',job_started_at=job['started_at'],job_completed_at=job['completed_at'],job_elapsed_seconds=25,runner='windows-2022',all_other_modes_skipped=True,artifacts_uploaded=0,caches_uploaded=0,incremental_spending=0),
 control_passed=False,changed_C_build_NULL_ABI_passed=True,Native_executed=False,Native_admitted=False,Windows_support=False,accepted=False,
 result='Actual WinError1307 invalid requested owner during PG_Arm; ownership becameORPHAN, no contained job/process launched. No denial/cancel/routing result exists.',
 observed=dict(host_state_files=9,host_state_bytes=6217,journal_events=events,context_and_raw_state_bound=True,actual_profile_creation_S_OK=True,sealed_scope=True,host_TCP_positives=2,contained_cases=0,C_jobs=0,C_processes=0,abort_error=0,policy_may_exist=1,policy_presence='unknown; conservative flag is not presence or absence proof',profile_and_ACL_cleanup='refused',owned_server_reaped=True,controller_reaped=True),
 source_interpretation='The source requestsSYSTEM owner without enabling owner-assignment privilege. Error1307 identifies rejected ownership; exact add API/object stage and actual remaining policy presence were not independently retained. Proposed actualTokenOwner+OWNER_RIGHTS correction is not yet executed.',
 costs=dict(enclosure_wall_seconds_before_exit=outer['wall_seconds_before_exit'],controller_wall_seconds_before_report=r['wall_seconds_before_report'],exited_controller_CPU_seconds=outer['controller_process_CPU_seconds'],
   separate_setup_Job_CPU_seconds=[q['full_job_cpu_seconds'] for q in processes],measured_controller_plus_separate_setup_CPU_subtotal=cpu,whole_CI_PowerShell_CPU_seconds=None,
   nested_canary_controller_CPU_seconds=c['controller_CPU_seconds_before_report']),
 accounting='All DLL/DNS/two probe builds included. CanarycontrollerCPU is nested in completePythonCPU, not added twice. Job25seconds includes checkout/setup; wall spans nest. WholeCI/PowerShell and authoring/research/AIreview/curationCPU unknown, notzero. No routing or speed claim.',
 review=dict(path=str(review.relative_to(ROOT)),sha256=p.sha(review),scope='Separate AI failure/raw-state/source and bounded primary-doc review; no humanreview or newexecution.'),
 next='At mostone predeclared corrective finite attempt after reviewed actualTokenOwner(SYSTEM/BAonly)+explicitOWNER_RIGHTSdenyWD/WO/exact3ACE. No privilege enabling, fallback, Native or mutation-resistance claim. Otherwise defer concreteblocker.',
 backup_scope='Actual own state/log bytes retained for auditedGit. Runner profile/policy/ACL objects deliberately retained on failure, not exported/restored or claimed cleaned; VM lifetime and wholeCPU remainprovider scope. Mac035GUI/preparedraw unaffected.',
 files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
p.save_json(packet,record);print(json.dumps(dict(control_passed=False,owner_error=1307,raw_state_files=9,files=len(files),bytes=total)))
