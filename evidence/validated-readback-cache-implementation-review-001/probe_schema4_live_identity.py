"""Actual retained schema4 readback/cache/function-default/parser identity control.
The existing tool_manifest body runs with only its Git HEAD lookup replaced by
a fixed review marker. No native/JVM/Git process or original file mutation runs.
"""
from pathlib import Path
import ast,copy,hashlib,json,re,sys,subprocess
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as pc,sexpr as sx
text=(ROOT/'autorouter/pipeline.py').read_text();node=copy.deepcopy(next(x for x in ast.parse(text).body if isinstance(x,ast.FunctionDef) and x.name=='tool_manifest'));node.name='review_tool_manifest'
assignment=next(x for x in node.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='git_head' for t in x.targets));assignment.value=ast.Constant('review-no-git')
namespace=dict(vars(p));exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(ROOT/'autorouter/pipeline.py'),'exec'),namespace);identity=namespace['review_tool_manifest']
receipt=ROOT/'.runs/placement-pruning-controls-002/run/tuned/result.json';source=Path(json.loads(receipt.read_text())['source']);before_run=pc.inventory(receipt.parent,max_bytes=100*1024**2,with_directories=True);before_source=pc.inventory(source.parent,with_directories=True)
real=p._check_result_uncached;calls=[]
def checked(path):calls.append(str(path));return real(path)
def forbidden(*args,**kwargs):raise RuntimeError('review forbids child processes')
old_defaults=p.native_rejection_reasons.__defaults__;old_token=sx.TOKEN
try:
 with patch.object(p,'tool_manifest',identity),patch.object(p,'_check_result_uncached',checked),patch.object(subprocess,'run',side_effect=forbidden),patch.object(subprocess,'Popen',side_effect=forbidden),p.validation_readback_session():
  first=p.check_result(receipt);cold_calls=len(calls);second=p.check_result(receipt);hit_calls=len(calls);assert first==second and cold_calls==hit_calls==1
  p.native_rejection_reasons.__defaults__=('review unused default',)
  p.check_result(receipt);default_calls=len(calls);assert default_calls==2
  p.native_rejection_reasons.__defaults__=old_defaults;p.check_result(receipt);restored_calls=len(calls);assert restored_calls==3
  sx.TOKEN=re.compile(r'(?!)')
  try:p.check_result(receipt)
  except Exception as exc:parser_rejected=True;parser_error=type(exc).__name__+': '+str(exc)
  else:parser_rejected=False;parser_error=None
  parser_calls=len(calls);cleared=not p._readback_session.get()['entries']
finally:
 p.native_rejection_reasons.__defaults__=old_defaults;sx.TOKEN=old_token
assert parser_rejected and parser_calls>restored_calls and cleared
assert before_run==pc.inventory(receipt.parent,max_bytes=100*1024**2,with_directories=True);assert before_source==pc.inventory(source.parent,with_directories=True)
result={'scope':__doc__,'pipeline_sha256':hashlib.sha256(text.encode()).hexdigest(),'receipt_sha256':p.sha(receipt),'first_result':first,'cold_full_checks':cold_calls,'unchanged_second_full_checks':hit_calls,'changed_function_default_full_checks':default_calls,'restored_default_full_checks':restored_calls,'changed_parser_full_checks':parser_calls,'changed_parser_rejected':parser_rejected,'parser_error':parser_error,'exception_clears_entries':cleared,'original_run_source_unchanged':True,'all_policy_objects_restored':sx.TOKEN is old_token and p.native_rejection_reasons.__defaults__==old_defaults}
p.save_json(HERE/'schema4-live-identity-001.json',result);print(json.dumps(result))
