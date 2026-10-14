import time
START=time.monotonic()
import json,sys,resource,subprocess,copy
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
OUT=Path(__file__).parent
def forbidden(*args,**kwargs):raise AssertionError('No Native/Git/subprocess in postfix control')
subprocess.run=forbidden;subprocess.Popen=forbidden
paths=[ROOT/'.runs/analog-filter-b2-high-only-001/trial/result.json',ROOT/'.runs/analog-filter-native-paired-complete-sch-001/run/C_feedback/result.json']
real_read=f.read_json;real_bytes=pc.read_bytes
controls=[]
before={str(path):p.sha(path) for path in paths}
source_before={n:p.sha(ROOT/n) for n in ['autorouter/pipeline.py','autorouter/strategy.py','tests/test_pruning_scoring.py']}
def run_observation(path,data):
 raw=(json.dumps(data,indent=2)+'\n').encode()
 def observed_read(target):return copy.deepcopy(data) if Path(target)==path else real_read(target)
 def observed_bytes(target,limit=20*1024**2):return raw if Path(target)==path else real_bytes(target,limit)
 try:
  with patch.object(f,'read_json',side_effect=observed_read),patch.object(pc,'read_bytes',side_effect=observed_bytes):
   checked=p.check_result(path)
  return {'passed':True,'candidate_sha256':checked['candidate_sha256']}
 except p.Rejected as exc:return {'passed':False,'reason':str(exc)}
original=real_read(paths[0])
for label in ('via_high',None,'via_low'):
 changed=copy.deepcopy(original);changed['scoring_variant']=label
 result=run_observation(paths[0],changed);result['case']='HIGH scoring label '+repr(label);controls.append(result)
 assert result['passed'] is (label=='via_high')
legacy=real_read(paths[1]);result=run_observation(paths[1],legacy);result['case']='genuine legacy Analog C';controls.append(result);assert result['passed'] is True
changed=copy.deepcopy(legacy);del changed['strategy'];result=run_observation(paths[1],changed);result['case']='legacy Analog C strategy removed';controls.append(result)
assert result['passed'] is False and 'recognized strategy' in result['reason']
assert before=={str(path):p.sha(path) for path in paths}
ru=resource.getrusage(resource.RUSAGE_SELF);ch=resource.getrusage(resource.RUSAGE_CHILDREN)
result={'kind':'requested actual HIGH labels and legacy-strategy postfix control','controls':controls,'actual_receipt_hashes':before,'disk_native_evidence_unchanged':True,'new_native_execution':False,'validation_not_mocked':True,'source_sha256_at_probe_start':source_before,'source_sha256_at_probe_end':{n:p.sha(ROOT/n) for n in source_before},'observed_wall_seconds':time.monotonic()-START,'lifetime_self_CPU_seconds':ru.ru_utime+ru.ru_stime,'child_CPU_seconds':ch.ru_utime+ch.ru_stime,'bootstrap_allowance_seconds':1,'packet_emission_allowance_seconds':1,'scope':'Development review only; receipt observations changed in memory, all source/Native/code/report/process checks ran normally. No Native gain or fresh HIGH-C proof.'}
(OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
