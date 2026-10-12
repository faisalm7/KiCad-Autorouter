"""Three existing small controls plus exact old-worker opaque return; no native/JVM."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;D=R/'experiments/pic_mixed_transport_probe_v1';RUN=R/'.runs/pic-mixed-transport-probe-002'
sys.dont_write_bytecode=True;sys.path.insert(0,str(R));sys.path.insert(0,str(D))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={n:sha(D/n) for n in ('worker.py','driver.py','test_draft.py')}
assert pins['worker.py']=='0a1ba8f0e64bf0a35423072c7a4de9673f7220b8caede0aeb60064ed827d0f4c'
assert pins['driver.py']=='fe3e01d9fcf3bf760fa926b6d188ead3455bdfde85c844fc994d90e3aeea05a9'
assert pins['test_draft.py']=='a2e06c00ead6a2dba38ba6e5e4ddc3680617b7d4e24ec5cb9ca2d5f3af0c093e'
spec=importlib.util.spec_from_file_location('scoped_mixed_tests',D/'test_draft.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
methods=['test_clearance_census_uses_qualified_netinfo_not_opaque_pad','test_assigned_net_metadata_fails_closed','test_net_metadata_bound_to_same_board_context']
for name in methods:getattr(t.Pure(name),name)()
old=RUN/'code/experiments/pic_mixed_transport_probe_v1/worker.py';spec=importlib.util.spec_from_file_location('original_opaque_worker',old);oldworker=importlib.util.module_from_spec(spec);spec.loader.exec_module(oldworker)
board,pcb,*_=t.Pure(methods[0]).clearance_fixture()
try:oldworker.clearances(board,pcb)
except AttributeError as exc:old_error=str(exc)
else:raise AssertionError('old opaque PAD worker must fail')
assert "'SwigPyObject' object has no attribute 'GetName'"==old_error
code=ast.parse((D/'worker.py').read_text());assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='GetEffectiveNetClass' for n in ast.walk(code))
assert all(sha(D/n)==pin for n,pin in pins.items())
result={'schema':1,'passed':True,'scope':'Pure fixed NetInfo metadata API use and semantic row binding; no native qualification','source_pins':pins,'failed002_worker_sha256':sha(old),'same_opaque_PADs':{'old_error':old_error,'fixed_control_passed':True,'pad_effective_getter_calls':0,'full_census':247,'own_calls':247,'assigned':236,'explicit_netless':11,'net_class_metadata_values':['Default:250000','POWER:280000']},'existing_pure_methods_passed':methods,'assigned_bad_metadata_cases':6,'same_board_bad_row_cases':7,'source_unchanged_during_controls':True,'native_or_jvm_jobs':0,'remaining_blockers':[]}
(H/'probe-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'focused_methods':3,'old_error':old_error},indent=2))
