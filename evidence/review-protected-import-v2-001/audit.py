"""Actual retained import and receipt controls; no native rerun."""
from pathlib import Path
import copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
OUT=Path(__file__).resolve().parent
LOCKED=ROOT/'.runs/preferences-native-locked-001';PARTIAL=ROOT/'.runs/preferences-native-partial-002'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
pins={n:sha(ROOT/n) for n in ('autorouter/pipeline.py','tests/test_protected_import.py')}
source_dirs=[Path(json.loads((d/'result.json').read_text())['source']).parent for d in (LOCKED,PARTIAL)]
pre={str(d):p.tree_hash(d) for d in (LOCKED,PARTIAL,*source_dirs)}
original=sx.read(LOCKED/'snapshot/smoke.kicad_pcb');imported=sx.read(LOCKED/'imported.kicad_pcb');protected=p.routes(original)
V1='exact_non_uuid_v1';V2='exact_non_uuid_lock_position_v2';cases=[]
def case(name,call,expected):
 try:value=call();passed=True;error=None
 except Exception as exc:passed=False;error=type(exc).__name__+': '+str(exc);value=None
 cases.append({'case':name,'accepted':passed,'expected':expected,'error':error})
 assert passed==expected,(name,passed,error)
 return value
case('actual_locked_v1_remains_rejected',lambda:p.transplant_routes(original,imported,protected=protected),False)
audit={'imported_sha256':sha(LOCKED/'imported.kicad_pcb')}
result=case('actual_locked_v2_reconstructs',lambda:p.transplant_routes(original,imported,protected=protected,audit=audit,policy=V2),True)
assert len(protected)==2 and all(n in p.routes(result) for n in protected)
assert all(x['original_uuid']==x['imported_uuid'] for x in audit['matches'])
strip=lambda r:[n for n in r if not isinstance(n,list) or not n or n[0] not in ('locked','uuid')]
assert [strip(n) for n in p.routes(result)]==[strip(p.convert_route_nets(n,imported,original)) for n in p.routes(imported)]
assert p.immutable(result)==p.immutable(original)
scratch=OUT/'copied-files';scratch.mkdir(exist_ok=False)
(scratch/'imported.kicad_pcb').write_bytes((LOCKED/'imported.kicad_pcb').read_bytes());sx.write(scratch/'candidate.kicad_pcb',result)
binding={'protected_route_import':audit}
check=lambda data:p.check_protected_import(scratch,data,original,scratch/'candidate.kicad_pcb',protected)
case('v2_copied_file_binding',lambda:check(binding),True)
for policy in (V1,'unknown',None):
 altered=copy.deepcopy(binding);altered['protected_route_import']['policy']=policy
 case('reject_policy_'+str(policy),lambda altered=altered:check(altered),False)
for mutation in ('remove_lock','false_lock','duplicate_lock','other_field_order','normalized_duplicate'):
 altered=copy.deepcopy(imported);r=next(r for r in p.routes(altered) if sx.one(r,'uuid')==sx.one(protected[0],'uuid'))
 if mutation=='remove_lock':r.remove(sx.one(r,'locked'))
 elif mutation=='false_lock':sx.one(r,'locked')[1]='no'
 elif mutation=='duplicate_lock':r.append(['locked','yes'])
 elif mutation=='other_field_order':r.remove(sx.one(r,'width'));r.append(['width','0.25'])
 else:
  dup=copy.deepcopy(r);dup.remove(sx.one(dup,'locked'));dup.insert(1,['locked','yes']);sx.one(dup,'uuid')[1]='"duplicate"';altered.append(dup)
 case(mutation,lambda altered=altered:p.transplant_routes(original,altered,protected=protected,policy=V2),False)
case('actual_accepted_partial_v1_central_readback',lambda:p.check_result(PARTIAL/'result.json'),True)
assert pre=={str(d):p.tree_hash(d) for d in (LOCKED,PARTIAL,*source_dirs)}
assert pins=={n:sha(ROOT/n) for n in pins}
(OUT/'audit.json').write_text(json.dumps({'scope':'Pure saved-file/native-evidence reconstruction and central receipt readback; no fresh native/JVM/routing/network.','source_pins':pins,'actual_locked_result_sha256':sha(LOCKED/'result.json'),'actual_locked_board_sha256':sha(LOCKED/'snapshot/smoke.kicad_pcb'),'actual_locked_import_sha256':sha(LOCKED/'imported.kicad_pcb'),'actual_partial_v1_receipt_sha256':sha(PARTIAL/'result.json'),'actual_locked_failure':json.loads((LOCKED/'result.json').read_text())['reason'],'original_and_evidence_unchanged':True,'exact_original_locked_nodes_restored':True,'remaining_nonuuid_nonlock_atoms_and_order_unchanged':True,'reconciliation':audit,'cases':cases,'all_passed':True},indent=2)+'\n')
print(json.dumps({'cases':len(cases),'all_passed':True,'source_pins':pins}))
