"""Relocated complete real schema5 evidence used only as a consistency-test fixture.
Board/DRC/engine payloads are copied unchanged; path declarations and dependent
readback hashes are rebased for scratch ownership. No worker or Git process runs,
and no newly executed native result or route quality is claimed.
"""
from pathlib import Path
import ast,copy,hashlib,json,shutil,sys,subprocess
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as pc,placement_strategy as ps,floor_route as f,sexpr as sx
old=ROOT/'.runs/placement-pruning-controls-004/run/C';old_data=f.read_json(old/'result.json');old_source=Path(old_data['source']);scratch=HERE/'schema5-scratch';scratch.mkdir();target=scratch/'C';source=scratch/'source'/old_source.name
old_before=pc.inventory(old,max_bytes=ps.LIMIT,max_files=ps.MAX_FILES,max_entries=ps.MAX_FILES*2,with_directories=True);source_before=pc.inventory(old_source.parent,with_directories=True)
shutil.copytree(old,target);shutil.copytree(old_source.parent,source.parent)
replacements=((str(old),str(target)),(str(old_source.parent),str(source.parent)))
def relocate(value):
 if isinstance(value,str):
  for before,after in replacements:value=value.replace(before,after)
  return value
 if isinstance(value,list):return [relocate(x) for x in value]
 if isinstance(value,dict):return {relocate(k):relocate(v) for k,v in value.items()}
 return value
for path in target.rglob('*.json'):
 value=f.read_json(path);rebased=relocate(value)
 if rebased!=value:p.save_json(path,rebased)

def final_audit(folder):
 path=folder/'floor-final-audit.json';value=f.read_json(path);value['native_context_sha256']=p.sha(folder/'floor-final-context.json');p.save_json(path,value)
inc=target/'incumbent';data=f.read_json(inc/'result.json');hashes=pc.inventory(source.parent);task=sx.read(inc/'floor-export-input'/source.name)
guided,contract=f.policy_contract(pc.read_bytes(inc/'native.dsn'),f.read_json(inc/'floor-export-context.json'),pc.read_bytes(source.with_suffix('.kicad_pro')),task,hashes)
assert guided==pc.read_bytes(inc/'floor-guided.dsn')
p.save_json(inc/'floor-policy.json',contract);outputs,composition=pc.derive_chain(inc,source.name,hashes)
for name,payload in outputs.items():assert payload==pc.read_bytes(inc/name)
p.save_json(inc/'placement-policy.json',composition);final_audit(inc)
data['floor_policy']['sha256']=p.sha(inc/'floor-policy.json');data['placement_policy']['sha256']=p.sha(inc/'placement-policy.json');data['floor_evidence_hashes']=f.evidence_inventory(inc);p.save_json(inc/'result.json',data)
root_data=f.read_json(target/'result.json')
for row in root_data['trials']:
 folder=target/'trials'/f"{row['index']:04d}";final_audit(folder)
 # Each trial metadata copy must match the root row after path relocation.
 assert row==f.read_json(folder/'trial.json')
final_audit(target);root_data['incumbent_receipt_sha256']=p.sha(inc/'result.json');root_data['pruning_evidence_hashes']=ps.evidence_inventory(target);p.save_json(target/'result.json',root_data)
text=(ROOT/'autorouter/pipeline.py').read_text();node=copy.deepcopy(next(x for x in ast.parse(text).body if isinstance(x,ast.FunctionDef) and x.name=='tool_manifest'));node.name='review_tool_manifest'
assignment=next(x for x in node.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='git_head' for t in x.targets));assignment.value=ast.Constant('review-no-git')
namespace=dict(vars(p));exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(ROOT/'autorouter/pipeline.py'),'exec'),namespace);identity=namespace['review_tool_manifest']
real=p._check_result_uncached;calls=[]
def check(path):calls.append(str(path));return real(path)
def forbidden(*args,**kwargs):raise RuntimeError('review forbids child process execution')
receipt=target/'result.json';before=pc.inventory(target,max_bytes=ps.LIMIT,max_files=ps.MAX_FILES,max_entries=ps.MAX_FILES*2);directories_before=pc.inventory(target,max_bytes=ps.LIMIT,max_files=ps.MAX_FILES,max_entries=ps.MAX_FILES*2,with_directories=True)
with patch.object(p,'tool_manifest',identity),patch.object(p,'_check_result_uncached',check),patch.object(subprocess,'run',side_effect=forbidden),patch.object(subprocess,'Popen',side_effect=forbidden),p.validation_readback_session():
 first=p.check_result(receipt);cold_calls=len(calls);second=p.check_result(receipt);hit_calls=len(calls);assert first==second and hit_calls==cold_calls
 (target/'trials/9999').mkdir()
 file_inventory_unchanged=pc.inventory(target,max_bytes=ps.LIMIT,max_files=ps.MAX_FILES,max_entries=ps.MAX_FILES*2)==before
 directory_inventory_changed=pc.inventory(target,max_bytes=ps.LIMIT,max_files=ps.MAX_FILES,max_entries=ps.MAX_FILES*2,with_directories=True)!=directories_before
 try:p.check_result(receipt)
 except Exception as exc:rejected=True;error=type(exc).__name__+': '+str(exc)
 else:rejected=False;error=None
 entries_cleared=not p._readback_session.get()['entries'];after_calls=len(calls)
assert rejected and file_inventory_unchanged and directory_inventory_changed and after_calls>hit_calls and entries_cleared
assert old_before==pc.inventory(old,max_bytes=ps.LIMIT,max_files=ps.MAX_FILES,max_entries=ps.MAX_FILES*2,with_directories=True);assert source_before==pc.inventory(old_source.parent,with_directories=True)
result={'scope':__doc__,'pipeline_sha256':hashlib.sha256(text.encode()).hexdigest(),'original_receipt_sha256':p.sha(old/'result.json'),'scratch_receipt_sha256':p.sha(receipt),'first_result':first,'cold_full_check_calls':cold_calls,'unchanged_second_full_check_calls':hit_calls,'after_empty_trial_full_check_calls':after_calls,'file_inventory_unchanged':file_inventory_unchanged,'directory_inventory_changed':directory_inventory_changed,'empty_trial_rejected':rejected,'error':error,'session_entries_cleared':entries_cleared,'original_run_and_source_unchanged':True,'scratch_contains_deliberate_invalid_empty_trial':True}
p.save_json(HERE/'schema5-empty-trial-001.json',result);print(json.dumps(result))
