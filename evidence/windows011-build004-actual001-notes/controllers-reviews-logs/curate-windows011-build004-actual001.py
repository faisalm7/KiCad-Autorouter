"""Close the single compile/NULL regression using shared bounded retention."""
import ast,base64,datetime,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
notes=ROOT/'evidence/windows011-build004-actual001-notes';packet=ROOT/'evidence/windows011-build004-actual001.json';assert not notes.exists() and not packet.exists()
base=ROOT/'.runs/windows011-build004-actual001';r=f.read_json(base/'readiness.json');outer=f.read_json(base/'enclosure.json');job=f.read_json(base/'job.json');status=f.read_json(base/'status003.json')
review=ROOT/'.runs/windows011-build004-result-review-001.json';assert p.sha(review)=='9d9f9fbdfca47f62fbf56df44a0a43e967a0ffc518c2bb44a44990a3eabf2d41';v=f.read_json(review)
head='72db8d41c8d389f8c3b6f80fb22535bd9962c93c';pin='1e77ac76423031bfc606a35d02ee69bb84f596679250e85d33c2eb046e4ac3ae'
assert status['headSha']==r['expected_source_sha']==outer['expected_source_sha']==head
assert r['protocol_sha256']==outer['expected_protocol_sha256']==pin
assert status['status']=='completed' and status['conclusion']==job['conclusion']=='success' and job['labels']==['windows-2022']
assert all(j['conclusion']=='skipped' for j in status['jobs'] if j['name']!='windows-guard-build')
assert r['passed'] is outer['passed'] is True and r['errors']==[] and r['stage']==outer['stage']=='build-null'
assert r['NULL_ABI']['passed'] and len(r['NULL_ABI']['outcomes'])==14 and len(r['NULL_ABI']['exports_bound'])==12
assert all(row['passed'] and row['actual']==row['expected'] for row in r['NULL_ABI']['outcomes'])
assert all(r[k] is False for k in v['false_boundary_flags'])
c=r['compiler_process'];assert c['status']=='success' and c['exit_code']==0 and c['cleanup_complete'] and c['compiler_output']['validated'] and c['compiler_output']['validation_after_job_reaped']
assert c['compiler_finalization']['zero_active_processes_verified'] and outer['controller_reaped'] and not outer['timed_out']
for name,sha in r['source_files_sha256'].items():assert hashlib.sha256(subprocess.check_output(['git','show',head+':'+name])).hexdigest()==sha
assert hashlib.sha256((base/'compile-guard.log').read_bytes()).hexdigest()==r['compiler_log']['sha256']==c['log_sha256']=='304300cb9ea40720d0f5192d5e220ae040114f89df6b3bd64ae73ebfe150ece8'
sources=[base/name for name in ('pre-dispatch.json','dispatch.stdout.log','dispatch.stderr.log','status001.json','status002.json','status003.json','actions.log','readiness.json','enclosure.json','job.json','compile-guard.log')]+[review,ROOT/'.runs/dispatch-windows011-build004-001.py',Path(__file__)]
raws=[io.read_bytes(q,4*1024**2) for q in sources];assert sum(map(len,raws))<16*1024**2 and len(sources)<2000
for raw in raws:assert b'\0' not in raw and not re.search(rb'key-[0-9a-f]{32}(?![0-9a-f])',raw);raw.decode('utf8')
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
refs={};files=[];material=[];total=0
defs=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='retain'];exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'))
for q in sources:retain(q,Path('controllers-reviews-logs')/q.name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(packet,dict(schema=1,kind='Windows011-build004-actual-compile-NULL-only-regression',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,source_head=head,protocol_sha256=pin,source_files_sha256=r['source_files_sha256'],CI=v['run'],
 build_passed=True,NULL_ABI_passed=True,accepted=False,Windows_support=False,Native_admitted=False,Native_executed=False,actual_policy_operations=False,actual_profile_operations=False,socket_tests_performed=False,
 observations=v['compile_and_cleanup'],NULL_ABI=v['NULL_ABI'],costs=v['costs'],SDK=r['compiler_tools'],review=dict(path=str(review.relative_to(ROOT)),sha256=p.sha(review),scope='Separate AI exact source/result/log readback; not human PCB review.'),
 decision=v['experiment_disposition'],remaining_unqualified=v['remaining_unqualified'],
 accounting='HostedJob20s/enclosure8.829134s; distinct compiler+exitedcontroller CPU subtotal1.359375s. Nested wall/CPU are not added twice. WholeCI/PowerShell/authoring/research/AI review/curation extra or unknown, not zero. No routing/speed claim. Standardpublicrunner/logonlyfree policy freshly verified; actual billing API not queried.',
 backup_scope='Essential source/CI log/report references for audited Git, no binary artifact/cache uploaded. Ephemeral DLL bytes not retained locally. Mac raw/preparedGUI and newer experiment artifacts remain Mac-only outside008/010; no restoration claim.',
 files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
print(json.dumps(dict(files=len(files),bytes=total,build_passed=True,NULL_ABI_passed=True,Windows_support=False)))
