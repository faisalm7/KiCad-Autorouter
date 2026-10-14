"""Exact diagnostic finalization suffix; synthetic evidence, no native claim."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast,hashlib,json,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from experiments.original_project_native_v1 import driver as d
source=Path(d.__file__).read_text();(HERE/'driver-before-publication-fix-002.py').write_text(source)
function=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='experiment')
tail=next(n.finalbody for n in function.body if isinstance(n,ast.Try) and n.finalbody)
compiled=compile(ast.Module(body=tail,type_ignores=[]),str(d.__file__),'exec')
out=HERE/'publication-case-002';out.mkdir();original=out/'original';original.mkdir();files={'owned.txt':b'authored original'};(original/'owned.txt').write_bytes(files['owned.txt']);before=d.p.tree_hash(original)
jobdir=out/'job';jobdir.mkdir();proof=jobdir/'class-observation.json';proof.write_text('{"authored":true}\n');oldsha=d.p.sha(proof)
owner={};d.h.capture_destination(owner,out);start=time.monotonic();cpu0=time.process_time()+d.f.child_cpu()
record={'schema':1,'status':'observed','accepted':False,'native_routing_scope_accepted':True,'helper_sha256':d.p.sha(Path(d.__file__)),'class_observation_sha256':oldsha,'budget_seconds':90.,'cpu_budget_seconds':90.,'production_support_qualified':False}
env={'Path':Path,'__file__':d.__file__,'record':record,'job':SimpleNamespace(steps=[]),'owner':owner,'out':out,'before':before,'files':files,'snapshot':SimpleNamespace(capture=lambda:dict(files)),'started':start,'cpu0':cpu0,'SECONDS':90.,'LIMIT':d.LIMIT,'h':d.h,'p':d.p,'f':d.f,'time':time,'remaining':lambda:90.-(time.monotonic()-start),'size':lambda:sum(len(v) for v in d.io.inventory(out,contents=True,max_bytes=d.LIMIT,max_files=2048,max_entries=4096).values())}
real=d.p.save_json;calls=[]
def mutate_after_publication(path,value):
 real(path,value);calls.append(path)
 if len(calls)==1:proof.write_text('{"altered_after_validation":true}\n')
with patch.object(d.p,'save_json',side_effect=mutate_after_publication):exec(compiled,env)
canonical=d.f.read_json(out/'result.json')
assert canonical['status']=='observed' and canonical['native_routing_scope_accepted'] is True and canonical['class_observation_sha256']!=d.p.sha(proof)
print(json.dumps({'schema':1,'scope':'Synthetic exact finalization suffix; no native/Git/network; no actual class proof fabricated','canonical_status':canonical['status'],'canonical_native_scope_claim':canonical['native_routing_scope_accepted'],'stored_proof_sha256':canonical['class_observation_sha256'],'actual_proof_sha256':d.p.sha(proof),'stale_hash_rejected':False,'driver_sha256':hashlib.sha256(source.encode()).hexdigest(),'finding':'Late class-observation mutation is invisible to stable() and canonical observed status survives'},indent=2))
