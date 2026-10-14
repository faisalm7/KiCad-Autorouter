import time
START=time.monotonic()
import json,sys,hashlib,resource,subprocess,copy
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
OUT=Path(__file__).parent;path=ROOT/'.runs/analog-filter-b2-high-only-001/trial/result.json'
def forbidden(*args,**kwargs):raise AssertionError('No native/Git/subprocess allowed')
subprocess.run=forbidden;subprocess.Popen=forbidden
original=f.read_json(path);before=pc.inventory(path.parent,max_bytes=32*1024**2,max_files=1000,max_entries=2000,with_directories=True)
assert original['scoring_variant']=='via_high'
controls=[];real_read=f.read_json;real_bytes=pc.read_bytes
for label in ('via_high',None,'via_low'):
 data=copy.deepcopy(original);data['scoring_variant']=label
 raw=(json.dumps(data,indent=2)+'\n').encode()
 def observed_read(target):return copy.deepcopy(data) if Path(target)==path else real_read(target)
 def observed_bytes(target,limit=20*1024**2):return raw if Path(target)==path else real_bytes(target,limit)
 try:
  with patch.object(f,'read_json',side_effect=observed_read),patch.object(pc,'read_bytes',side_effect=observed_bytes):
   checked=p.check_result(path)
  controls.append({'edited_scoring_label':label,'central_check_passed':True,'candidate_sha256':checked['candidate_sha256']})
 except p.Rejected as exc:controls.append({'edited_scoring_label':label,'central_check_passed':False,'reason':str(exc)})
assert controls[0]['central_check_passed'] is True
assert before==pc.inventory(path.parent,max_bytes=32*1024**2,max_files=1000,max_entries=2000,with_directories=True)
ru=resource.getrusage(resource.RUSAGE_SELF);ch=resource.getrusage(resource.RUSAGE_CHILDREN)
result={'kind':'actual retained HIGH evidence with receipt-label-only observation mutation','controls':controls,'actual_engine_scoring':original['engine_budget']['scoring'],'actual_engine_score_flags':[x for x in original['engine_budget']['argv'] if 'router.scoring' in x],'actual_receipt_sha256':p.sha(path),'actual_evidence_unchanged':True,'new_native_execution':False,'validation_not_mocked':True,'seam':'Only observed receipt JSON/raw bytes replaced in memory; all original board/project/source/code/native/report/process/metric files and central validator ran unchanged. No Native approval simulation.','pipeline_sha256':p.sha(ROOT/'autorouter/pipeline.py'),'strategy_sha256':p.sha(ROOT/'autorouter/strategy.py'),'tests_sha256':p.sha(ROOT/'tests/test_pruning_scoring.py'),'wall_seconds':time.monotonic()-START,'lifetime_self_CPU_seconds':ru.ru_utime+ru.ru_stime,'waited_child_CPU_seconds':ch.ru_utime+ch.ru_stime,'bootstrap_allowance_seconds':1,'emission_allowance_seconds':1,'cost_scope':'Development correctness review, not future route/benchmark budget. Early code reads/import bootstrap/packet emission separate; no native/JVM/GET/Git/full suite.'}
(OUT/'before-fix.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
