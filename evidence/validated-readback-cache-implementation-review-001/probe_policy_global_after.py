"""Actual complete schema5 receipt, in-process policy change, no native/tool/Git launch.
Tool/code hashes use the existing tool_manifest body; only Git HEAD lookup is
replaced by a fixed marker to obey read-only review boundaries. Original files
remain unchanged. This is a cache-vs-full-check counterexample, not a new DRC.
"""
from pathlib import Path
import ast,copy,hashlib,json,sys,subprocess
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as pc
text=(ROOT/'autorouter/pipeline.py').read_text();tree=ast.parse(text);node=copy.deepcopy(next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='tool_manifest'))
node.name='review_tool_manifest'
assignment=next(x for x in node.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='git_head' for t in x.targets));assignment.value=ast.Constant('review-no-git')
namespace=dict(vars(p));exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(ROOT/'autorouter/pipeline.py'),'exec'),namespace);identity=namespace['review_tool_manifest']
receipt=ROOT/'.runs/placement-pruning-controls-004/run/C/result.json';source=Path(json.loads(receipt.read_text())['source'])
before_run=pc.inventory(receipt.parent,max_bytes=512*1024**2,max_files=16000,max_entries=32000,with_directories=True);before_source=pc.inventory(source.parent,with_directories=True)
real=p._check_result_uncached;calls=[]
def checked(path):calls.append(str(path));return real(path)
def forbidden(*args,**kwargs):raise RuntimeError('review forbids child processes')
old=set(p.CRITICAL_FINDINGS)
try:
 with patch.object(p,'tool_manifest',identity),patch.object(p,'_check_result_uncached',checked),patch.object(subprocess,'run',side_effect=forbidden),patch.object(subprocess,'Popen',side_effect=forbidden),p.validation_readback_session():
  first=p.check_result(receipt);cold_calls=len(calls)
  p.CRITICAL_FINDINGS.add('missing_courtyard')
  try:cached=p.check_result(receipt);hit_accepted=True;hit_error=None
  except Exception as exc:cached=None;hit_accepted=False;hit_error=type(exc).__name__+': '+str(exc)
  after_hit_calls=len(calls)
  try:real(receipt);full_accepted=True;full_error=None
  except Exception as exc:full_accepted=False;full_error=type(exc).__name__+': '+str(exc)
finally:
 p.CRITICAL_FINDINGS.clear();p.CRITICAL_FINDINGS.update(old)
assert before_run==pc.inventory(receipt.parent,max_bytes=512*1024**2,max_files=16000,max_entries=32000,with_directories=True)
assert before_source==pc.inventory(source.parent,with_directories=True)
result={'scope':__doc__,'pipeline_sha256':hashlib.sha256(text.encode()).hexdigest(),'receipt_sha256':p.sha(receipt),'first_result':first,'cold_full_check_calls':cold_calls,'full_check_calls_after_policy_change':after_hit_calls,'cached_after_policy_change_accepts':hit_accepted,'cached_error':hit_error,'uncached_after_policy_change_accepts':full_accepted,'uncached_error':full_error,'original_run_source_unchanged':True,'policy_restored':p.CRITICAL_FINDINGS==old}
(HERE/'policy-global-002.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
