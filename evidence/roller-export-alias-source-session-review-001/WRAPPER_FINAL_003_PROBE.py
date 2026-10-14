"""Exact final wrapper AST after imports; pure whole lifecycle/ownership seams.
All source hashes/paths and files are owned fixtures. No native/JVM/Git/subprocess.
"""
import ast,hashlib,json,sys,uuid
from pathlib import Path
from types import SimpleNamespace
ROOT0=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT0));sys.dont_write_bytecode=True
from autorouter import pipeline as realp,floor_route as f,handoff as realh
OWN=Path(__file__).resolve().parent;source=(OWN/'WRAPPER_FINAL_003.py').read_text();tree=ast.parse(source)
index=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='out' for t in n.targets))
suffix=ast.Module(body=tree.body[index:],type_ignores=[]);program=compile(ast.fix_missing_locations(suffix),'final-wrapper-exact-lifecycle','exec');rows=[]
labels=('final_normal','final_execution_write_oserror','final_execution_write_keyboardinterrupt','final_late_cap_corrective_write_oserror','final_postchild_hash_keyboardinterrupt','final_postchild_hash_oserror','final_runner_postchild_keyboardinterrupt','final_preexisting_candidate','final_preexisting_outer','final_partial_write_oserror','final_wrapper_drift','final_launcher_drift','final_protocol_drift','final_tool_drift')
for label in labels:
 root=OWN/'final-003'/label/'root';runs=root/'.runs';runs.mkdir(parents=True);out=runs/'roller-export-alias-native-003-execution';candidate=runs/'roller-export-alias-native-003';original=None;original_path=None
 if label=='final_preexisting_candidate':
  candidate.mkdir();original_path=candidate/'result.json';realp.save_json(original_path,{'accepted':False,'controls_passed':True,'status':'controls_passed','sentinel':'existing evidence must remain intact'});original=original_path.read_bytes()
 if label=='final_preexisting_outer':
  out.mkdir();original_path=out/'sentinel.txt';original_path.write_text('preexisting outer evidence');original=original_path.read_bytes()
 control=runs/'run-roller-export-alias-native-003.py';control.write_text(source);launcher=runs/'launch-roller-export-alias-native-003.py';launcher.write_text('# owned no-execution fixture\n')
 prodir=root/'experiments/roller_export_alias_v1';prodir.mkdir(parents=True);realp.save_json(prodir/'CONTINUATION_PROTOCOL.json',{'wrapper_sha256':realp.sha(control),'launcher_sha256':realp.sha(launcher),'prior_active_wall_seconds':23.6264327490062,'prior_full_cpu_seconds':18.575416})
 writes=[];clock=[];sigcalls=[];ran=[]
 def sha(path):
  if ran and label=='final_postchild_hash_keyboardinterrupt':raise KeyboardInterrupt('injected post-child controller hash cancellation')
  if ran and label=='final_postchild_hash_oserror':raise OSError('injected post-child controller hash failure')
  return realp.sha(path)
 def save(path,value):
  writes.append(str(path.relative_to(root)))
  if label=='final_partial_write_oserror':
   realp.save_json(path.with_name(path.name+'.partial'),value);raise OSError('injected execution partial-write failure')
  if label=='final_execution_write_oserror':raise OSError('injected outer receipt write failure')
  if label=='final_execution_write_keyboardinterrupt':raise KeyboardInterrupt('injected outer receipt write cancellation')
  if label=='final_late_cap_corrective_write_oserror' and path.name=='execution-rejection.json':raise OSError('injected corrective outer write failure')
  realp.save_json(path,value)
 def run(*args,**kwargs):
  ran.append(1);candidate.mkdir();realp.save_json(candidate/'result.json',{'accepted':False,'controls_passed':True,'status':'controls_passed'});(out/'command.log').write_text('owned synthetic child, no native execution\n')
  if label=='final_wrapper_drift':control.write_text(source+'\n# changed after initial binding\n')
  if label=='final_launcher_drift':launcher.write_text('# changed launcher after initial binding\n')
  if label=='final_protocol_drift':
   q=f.read_json(prodir/'CONTINUATION_PROTOCOL.json');q['changed']='after native';realp.save_json(prodir/'CONTINUATION_PROTOCOL.json',q)
  if label=='final_runner_postchild_keyboardinterrupt':raise KeyboardInterrupt('injected runner return after child positive')
  return {'status':'success','exit_code':0}
 def now():
  clock.append(0);return 37. if label=='final_late_cap_corrective_write_oserror' and len(clock)>2 else 1.
 old={2:'old-sigint',15:'old-sigterm'}
 def signal(sig,handler):
  previous=old[sig];old[sig]=handler;sigcalls.append((sig,str(handler)));return previous
 env={'Path':Path,'__file__':str(control),'ROOT':root,'START':0.,'CPU0':0.,'BOOTSTRAP_WALL_ALLOWANCE':1.,'time':SimpleNamespace(monotonic=now),'h':SimpleNamespace(real_path=realh.real_path,cpu_seconds=lambda:1.,capture_destination=realh.capture_destination,owned_destination=realh.owned_destination),'p':SimpleNamespace(sha=sha,save_json=save,Rejected=realp.Rejected,tool_manifest=lambda:{'git_head':'changed-after-native' if ran and label=='final_tool_drift' else 'owned-synthetic-head'}),'f':f,'json':json,'uuid':uuid,'run':run,'signal':SimpleNamespace(SIGINT=2,SIGTERM=15,signal=signal)}
 failure=None
 try:exec(program,env)
 except BaseException as e:failure=type(e).__name__+': '+str(e)
 current=f.read_json(candidate/'result.json') if (candidate/'result.json').exists() else None;archives=list(candidate.glob('invalidated-result-*.json')) if candidate.exists() else []
 positives=[x for x in archives if f.read_json(x).get('controls_passed') is True]
 preserved=original_path is not None and original_path.read_bytes()==original
 assert old=={2:'old-sigint',15:'old-sigterm'}
 if label=='final_normal':assert failure=='SystemExit: 0' and current['controls_passed'] is True and not archives
 elif label.startswith('final_preexisting'):
  assert failure and failure.startswith('Rejected: fresh outer and native candidate outputs required') and not ran and not sigcalls and preserved
 else:
  assert failure and current['controls_passed'] is False and len(positives)==1
  if 'keyboardinterrupt' in label:assert failure.startswith('KeyboardInterrupt:')
  if label=='final_late_cap_corrective_write_oserror':assert failure.startswith('Rejected: final outer publication crosses60')
  if label.endswith('_drift'):assert failure.startswith('Rejected: initial outer source/tool/protocol bindings changed')
  assert not (out/'execution.json').exists() and not (out/'execution.json.partial').exists()
 rows.append({'label':label,'exception':failure,'run_fixture_calls':len(ran),'canonical_controls_passed':None if current is None else current['controls_passed'],'archived_original_positive_count':len(positives),'preexisting_bytes_preserved':preserved if original_path else None,'original_signal_handlers_restored':True,'signal_calls':len(sigcalls),'outer_receipt_exists':(out/'execution.json').exists(),'outer_rejection_exists':(out/'execution-rejection.json').exists(),'archived_outer_index_count':len(list(out.glob('invalidated-*-execution.json*'))),'writes_attempted':writes})
result={'schema':1,'native_execution':False,'subprocess_execution':False,'source_wrapper_sha256':hashlib.sha256(source.encode()).hexdigest(),'exact_postimport_ast_sha256':hashlib.sha256(ast.dump(suffix,include_attributes=False).encode()).hexdigest(),'rows':rows};(OWN/'WRAPPER_FINAL_003_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':'final_lifecycle_checks_passed','source_wrapper_sha256':result['source_wrapper_sha256'],'controls':len(rows),'native_execution':False}))
