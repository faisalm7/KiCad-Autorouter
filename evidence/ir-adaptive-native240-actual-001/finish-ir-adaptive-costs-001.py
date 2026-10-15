import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,importlib.util,copy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
source=ROOT/'.runs/adaptive-native-controller-002.py';s=importlib.util.spec_from_file_location('qualified_adaptive_controller',source);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
planpath=ROOT/'.runs/ir-adaptive-002-post-cost-protocol-001.json';plan=m.f.read_json(planpath);planpin=m.p.sha(planpath);out=ROOT/'.runs/ir-adaptive-002-final-costs-001.json';assert not out.exists()
assert plan['schema']==1 and plan['postprocess_wall_full_cpu_cap_seconds']==15 and plan['controller_sha256']==m.p.sha(Path(__file__)) and plan['adaptive_controller_sha256']==m.p.sha(source)
path,spec,pin=m.read_spec(Path(plan['original_protocol']));failure=m.f.read_json(plan['failed_prelaunch'])
assert failure['conservative_charge']['wall_seconds']==2 and failure['conservative_charge']['full_cpu_seconds']==20 and failure['full_cpu_seconds'] is None and failure['new_reader_execution'] is False
qualpath=Path(spec['paths']['qualification'])/'execution.json';readpath=Path(spec['paths']['read'])/'result.json';qual=m.f.read_json(qualpath);result=m.f.read_json(readpath)
assert qual['passed'] is True and qual['result_sha256']==m.p.sha(readpath) and result['status']=='completed' and result['comparison_eligible'] is True
pins={name:m.p.sha(name) for name in [str(path),str(qualpath),str(readpath),plan['failed_prelaunch'],str(source),str(Path(__file__))]}
rows=copy.deepcopy(qual['final_charged_results'])
for row in rows:
 row['charged_wall_seconds']+=2+15
 row['charged_cpu_seconds']+=20+15
rows=m.apply_delivered_caps(rows,spec['limits']['delivered'],True)
record=dict(schema=1,passed=False,original_protocol_sha256=pin,post_protocol_sha256=planpin,pins=pins,failed_prelaunch_allowance=failure['conservative_charge'],postprocess_charged_upper_bound_seconds=15,final_charged_results=rows,comparisons=m.comparisons(rows),new_native_execution=False,new_engine_execution=False,new_reader_execution=False,scope='Monotone additional common cost adjustment only. Original qualified reader/enclosure immutable; all six rows pay failedprelaunch2wall/20CPU allowance (actualCPUunknown) plus this whole15wall/fullCPU bounded postprocess. Actual source/material/PRL freshness rechecked using existing helper. No Native or engine repeats.')
def stable():
 assert m.p.sha(planpath)==planpin and all(m.p.sha(name)==digest for name,digest in pins.items())
 m.stable(path,spec,pin,new_workers=result['workers'])
 root=Path(spec['paths']['native']);outer=m.f.read_json(root/'execution.json');current=m.inventory(root)
 assert m.f.canonical(({n:v for n,v in current[0].items() if n!='execution.json'},current[1]))==m.f.canonical(outer['material'])
 assert max(time.monotonic()-START,cpu()-CPU0)<=15
try:
 with m.pure_reader_guard(audit=True):
  stable();record.update(passed=True,actual_wall_seconds=time.monotonic()-START,actual_full_cpu_seconds=cpu()-CPU0)
  m.p.save_json(out,record);expected=m.f.canonical(record);stable()
  assert m.f.canonical(m.f.read_json(out))==expected
  assert max(time.monotonic()-START,cpu()-CPU0)<=15
except (Exception,KeyboardInterrupt) as exc:
 record.update(passed=False,comparisons=[],reason=type(exc).__name__+': '+str(exc))
 for row in rows:
  row['accepted']=False
  for observation in row.get('observations',[]):observation['final_delivery_accepted']=False
 m.p.save_json(out,record)
print(json.dumps({k:record[k] for k in ('passed','comparisons')}));raise SystemExit(0 if record['passed'] else 2)
