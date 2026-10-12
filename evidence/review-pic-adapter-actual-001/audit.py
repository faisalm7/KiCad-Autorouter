"""One offline saved-evidence readback; no native/JVM/engine invocation."""
import copy, hashlib, importlib.util, json, math, sys
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter.placement_clearance import inventory, read_bytes
from autorouter.adapter import _parse_dsn
from experiments.pic_mixed_transport_probe_v1 import routing_adapter, routing_checks, transport
RUN=ROOT/'.runs/pic-corrected-adapter-routing-001';OUT=Path(__file__).parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()
load=lambda path:json.loads(read_bytes(path,16*1024*1024))
inv=lambda path:inventory(path,max_bytes=64*1024*1024,max_files=2000,max_entries=4000)
before=inv(RUN);summary=load(RUN/'summary.json');runtime=load(RUN/'runtime.json')
original=ROOT/'.data/boards/kicad-pic-programmer';source_before=inv(original)
assert source_before==runtime['original']==inv(RUN/'observe-input')
assert all(before[p]==v for p,v in summary['frozen_evidence'].items())
obs=load(RUN/'observations.json');basis=load(RUN/'selective-basis-observations.json');context=load(RUN/'cached-native/context.json')
receipt=load(RUN/'routing-adapter.json');expected=load(RUN/'routing-expectations.json')
assert routing_adapter.verify(read_bytes(RUN/'stripped-unrouted.dsn'),read_bytes(RUN/'unrouted.dsn'),context,receipt)
# Reproduce the historical pure comparison, then intercept only its final equality
# to record both already-validated projections. This is diagnosis, not acceptance.
spec=importlib.util.spec_from_file_location('captured_routing_checks',RUN/'code/experiments/pic_mixed_transport_probe_v1/routing_checks.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
try:old.adapter_projection(obs['case']['state_after_selective'],basis['case']['state_after_selective'],receipt)
except ValueError as e:historical_error=str(e)
else:raise AssertionError('historical mismatch not reproduced')
assert historical_error=='corrected adapter changed other imported constraints'
projected=[]
with patch.object(old.s,'equal',side_effect=lambda a,b,label:projected.append((copy.deepcopy(a),copy.deepcopy(b),label))):
 old.adapter_projection(obs['case']['state_after_selective'],basis['case']['state_after_selective'],receipt)
assert len(projected)==1
new,prior,_=projected[0]
assert {k:v for k,v in new.items() if k!='nets'}=={k:v for k,v in prior.items() if k!='nets'}
mapping=[]
for name in sorted(n['name'] for n in prior['nets']):
 a=next(n for n in prior['nets'] if n['name']==name);b=next(n for n in new['nets'] if n['name']==name)
 assert {k:v for k,v in a.items() if k!='number'}=={k:v for k,v in b.items() if k!='number'}
 mapping.append({'name':name,'prior_number':a['number'],'current_number':b['number']})
assert len(mapping)==111 and len({x['current_number'] for x in mapping})==111
assert [x for x in mapping if x['prior_number']!=x['current_number']]==[
 {'name':'GND','prior_number':1,'current_number':2},{'name':'VCC','prior_number':2,'current_number':1}]
def pin_membership(state):
 return sorted((p['reference'],p['number'],tuple(p['nets'])) for p in state['pins'])
assert pin_membership(obs['case']['state_after_selective'])==pin_membership(basis['case']['state_after_selective'])
assert len(pin_membership(obs['case']['state_after_selective']))==240
for name in ('stripped-unrouted.dsn','unrouted.dsn'):
 assert transport.placed_pins(_parse_dsn(read_bytes(RUN/name).decode()))==expected['dsn_pins']
corrected=routing_checks.compare(obs,expected,basis,adapter_receipt=receipt)
assert corrected['lifecycle_verified'] and corrected['geometry_verified'] and not corrected['routing_accepted']
g=obs['final_geometry'];classes={};points=0;rational=[]
for trace in g['traces']:
 assert len(trace['corners_board_exact'])==len(trace['corner_classes'])==len(trace['corners_board_integer'])
 for k,point,exact in zip(trace['corner_classes'],trace['corners_board_integer'],trace['corners_board_exact']):
  classes[k]=classes.get(k,0)+1;points+=1
  assert set(exact)=={'x','y','z'} and all(isinstance(x,str) for x in exact.values())
  x,y,z=[int(exact[n]) for n in ('x','y','z')]
  assert z>0 and max(abs(x).bit_length(),abs(y).bit_length(),z.bit_length())<=4096 and math.gcd(math.gcd(abs(x),abs(y)),z)==1
  if k.endswith('IntPoint'):assert [x,y]==point and z==1
  else:rational.append(exact)
assert not rational and g['trace_count']==176 and g['via_count']==0
assert obs['writer']['state_after_ses']==obs['final_state'] and obs['writer']['route_geometry_after_ses']==g
assert obs['writer']['ses']['sha256']==sha(read_bytes(RUN/'raw.ses'))
steps=[]
for step in summary['steps']:
 saved=load(RUN/(step['name']+'-process.json'))
 assert saved=={k:v for k,v in step.items() if k!='name'}
 assert step['exit_code']==0 and step['status']=='success' and step['cleanup_complete'] and not step['log_truncated']
 steps.append({k:step[k] for k in ('name','status','exit_code','wall_seconds','cpu_seconds','cleanup_complete')})
assert [x['name'] for x in steps]==['compile','import']
assert summary['status']=='failed' and summary['observations_complete'] is False and summary['routing_accepted'] is False
assert summary['native_process_executed'] is False and summary['routing_executed'] is True and summary['ses_executed'] is True
assert before==inv(RUN) and source_before==inv(original)
report={'historical_status':summary['status'],'historical_error_reproduced':historical_error,'frozen_evidence_files':len(summary['frozen_evidence']),'full_run_files':len(before),'original_project_files':len(source_before),'full_run_original_unchanged':True,'git_head':runtime['git']['head'],'comparison_correction':'Cross-import only: remove ephemeral net number and sort by exact unique name; all other projected fields equal. Preserve post-routing same-instance IDs/numbers.','raw_mapping':mapping,'changed_numbers':[x for x in mapping if x['prior_number']!=x['current_number']], 'terminal_membership_equal':True,'dsn_placed_pins':240,'assigned_pins':236,'other_observed_nonrouting_state_equal':True,'corrected_shared_readback':corrected,'new_checker_sha256':sha(read_bytes(ROOT/'experiments/pic_mixed_transport_probe_v1/routing_checks.py')),'captured_checker_sha256':before['code/experiments/pic_mixed_transport_probe_v1/routing_checks.py'],'initial_census':obs['case']['state_after_selective']['census'],'final_census':obs['final_state']['census'],'adapter_obstacles':obs['final_state']['adapter_obstacle_count'],'exact_corner_count':points,'corner_classes':classes,'rational_corners':rational,'rational_capture_scope':'All actual points are IntPoint with exact z=1. Same-package class compiled, but this run does not exercise actual RationalPoint capture.','parser_warnings':obs['case']['parser_warnings'],'routing':obs['routing'],'steps':steps,'stored_cost':{k:summary[k] for k in ('wall_seconds','total_cpu_seconds','accounting_point')},'writer_unchanged':True,'bindings':{p:before[p] for p in ('summary.json','observations.json','runtime.json','unrouted.dsn','stripped-unrouted.dsn','routing-adapter.json','raw.ses')},'scope':'Offline evidence/checker diagnosis only. Historical failed receipt unchanged. No fresh native validation or routing acceptance.'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:report[k] for k in ('changed_numbers','frozen_evidence_files','full_run_files','corrected_shared_readback','exact_corner_count','corner_classes','stored_cost')},indent=2))
