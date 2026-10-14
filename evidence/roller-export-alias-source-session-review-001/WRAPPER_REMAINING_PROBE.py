"""Material remaining pre-try/ownership seams in frozen first wrapper fix."""
import ast,json,sys,hashlib
from pathlib import Path
from types import SimpleNamespace
ROOT0=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT0));sys.dont_write_bytecode=True
from autorouter import pipeline as realp,floor_route as f,handoff as realh
OWN=Path(__file__).resolve().parent;source=(OWN/'WRAPPER_AFTER_FIX.py').read_text();tree=ast.parse(source);index=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='record' for t in n.targets));program=compile(ast.fix_missing_locations(ast.Module(body=tree.body[index:],type_ignores=[])),'first-fixed-wrapper-tail','exec');rows=[]
for label in ('pretry_hash_keyboardinterrupt','preexisting_child_output_nonzero_then_outer_write_failure'):
 root=OWN/label/'root';out=root/'.runs/roller-export-alias-native-003-execution';out.mkdir(parents=True);candidate=root/'.runs/roller-export-alias-native-003';candidate.mkdir()
 original={'accepted':False,'controls_passed':True,'status':'controls_passed','preexisting_marker':'preserve-me' if label.startswith('preexisting') else None};realp.save_json(candidate/'result.json',original);before=hashlib.sha256((candidate/'result.json').read_bytes()).hexdigest();signal_calls=[]
 def sha(_):
  if label.startswith('pretry'):raise KeyboardInterrupt('injected post-child/pre-try hash cancellation')
  return 'owned-synthetic-hash'
 def save(path,value):raise OSError('injected outer execution-write failure')
 env={'Path':Path,'__file__':str(OWN/'WRAPPER_AFTER_FIX.py'),'ROOT':root,'out':out,'START':0.,'BOOTSTRAP_WALL_ALLOWANCE':1.,'time':SimpleNamespace(monotonic=lambda:1.),'h':SimpleNamespace(cpu_seconds=lambda:1.,capture_destination=realh.capture_destination,owned_destination=realh.owned_destination),'CPU0':0.,'process':{'status':'nonzero_exit','exit_code':2} if label.startswith('preexisting') else {'status':'success','exit_code':0},'head':'synthetic','priorwall':23.6264327490062,'priorcpu':18.575416,'cap':60.,'p':SimpleNamespace(sha=sha,save_json=save,Rejected=realp.Rejected),'f':f,'json':json,'previous_handlers':{15:'owned-old-handler'},'signal':SimpleNamespace(signal=lambda *x:signal_calls.append(x))}
 failure=None
 try:exec(program,env)
 except BaseException as e:failure=type(e).__name__+': '+str(e)
 after=f.read_json(candidate/'result.json');same=hashlib.sha256((candidate/'result.json').read_bytes()).hexdigest()==before
 if label.startswith('pretry'):assert after['controls_passed'] is True and not signal_calls
 else:assert after['controls_passed'] is False and not same
 rows.append({'label':label,'exception':failure,'canonical_controls_passed':after['controls_passed'],'original_result_bytes_preserved':same,'restored_signal_handler_calls':len(signal_calls),'archived_positive_count':sum(f.read_json(p).get('controls_passed') is True for p in candidate.glob('invalidated-result-*.json'))})
result={'schema':1,'native_execution':False,'source_wrapper_sha256':hashlib.sha256(source.encode()).hexdigest(),'rows':rows};(OWN/'WRAPPER_REMAINING_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
