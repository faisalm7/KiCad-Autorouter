"""Exact wrapper final suffix, synthetic positive child, injected I/O/cancel.
No native/JVM/Git/subprocess. All outputs remain in this owned review tree.
"""
import ast,hashlib,json,sys
from pathlib import Path
from types import SimpleNamespace
ROOT0=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT0));sys.dont_write_bytecode=True
from autorouter import pipeline as realp,floor_route as f
OWN=Path(__file__).resolve().parent
source=(OWN/'WRAPPER_BEFORE_FIX.py').read_text();tree=ast.parse(source)
# Exact source suffix starting at its native process-return record assignment.
index=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='record' for t in n.targets))
suffix=ast.Module(body=tree.body[index:],type_ignores=[]);program=compile(ast.fix_missing_locations(suffix),'frozen-wrapper-003-tail','exec')
rows=[]
for label in ('execution_write_oserror','execution_write_keyboardinterrupt','late_cap_corrective_execution_write_oserror'):
 case=OWN/label;root=case/'root';out=root/'.runs/roller-export-alias-native-003-execution';out.mkdir(parents=True)
 candidate=root/'.runs/roller-export-alias-native-003';candidate.mkdir();realp.save_json(candidate/'result.json',{'accepted':False,'controls_passed':True,'status':'controls_passed'})
 writes=[];clock=[]
 def save(path,value):
  writes.append(str(path.relative_to(root)))
  if label=='execution_write_keyboardinterrupt':raise KeyboardInterrupt('injected outer execution-write cancellation')
  if label=='execution_write_oserror' or label.startswith('late_cap') and len(writes)==2:raise OSError('injected outer execution-write failure')
  realp.save_json(path,value)
 def now():
  clock.append(0)
  return 37. if label.startswith('late_cap') and len(clock)>1 else 1.
 fakep=SimpleNamespace(sha=lambda _:'owned-synthetic-hash',save_json=save,Rejected=realp.Rejected)
 env={'Path':Path,'__file__':str(OWN/'WRAPPER_BEFORE_FIX.py'),'ROOT':root,'out':out,'START':0.,'time':SimpleNamespace(monotonic=now),'h':SimpleNamespace(cpu_seconds=lambda:1.),'CPU0':0.,'process':{'status':'success','exit_code':0},'head':'synthetic-head','priorwall':23.6264327490062,'priorcpu':18.575416,'cap':60.,'p':fakep,'f':f,'json':json}
 failure=None
 try:exec(program,env)
 except BaseException as e:failure=type(e).__name__+': '+str(e)
 data=f.read_json(candidate/'result.json');assert failure and data['controls_passed'] is True
 rows.append({'label':label,'exception':failure,'writes_attempted':writes,'canonical_controls_passed_after_exception':data['controls_passed'],'outer_receipt_exists':(out/'execution.json').exists(),'in_memory_within60':env.get('record',{}).get('within60')})
result={'schema':1,'native_execution':False,'subprocess_execution':False,'source_wrapper_sha256':hashlib.sha256(source.encode()).hexdigest(),'exact_suffix_ast_sha256':hashlib.sha256(ast.dump(suffix,include_attributes=False).encode()).hexdigest(),'rows':rows}
(OWN/'WRAPPER_FAILURE_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
