"""Existing small controls with scratch redirected to this review; no native/JVM."""
from pathlib import Path
import hashlib,importlib.util,json,sys
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;D=R/'experiments/pic_mixed_transport_probe_v1';RUN=R/'.runs/pic-mixed-transport-probe-003'
sys.dont_write_bytecode=True;sys.path.insert(0,str(R));sys.path.insert(0,str(D));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={n:sha(D/n) for n in ('worker.py','driver.py','test_draft.py')}
assert pins=={'worker.py':'d497772fb704bae69e86801211a3af0ddefa8f5211fd3ba4ee8acaf040a3bc6c','driver.py':'f48dfe05cd37bd54f9f5b67ac123fa19044130d9dba4e3344ff93b6c59249fd5','test_draft.py':'b65371429f0b14fdddda85c64e92bf3b226a8f923c2680b1e4a84a4a79c88cbd'}
spec=importlib.util.spec_from_file_location('scoped_mixed_test003',D/'test_draft.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
methods=['test_wxstring_labels_and_placeholder_order_match_context_convention','test_rejected_netcode_type_retained_before_initialization','test_assigned_net_metadata_fails_closed']
with patch.object(t,'HERE',H):
 for name in methods:getattr(t.Pure(name),name)()
class WxString:
 def __init__(self,text):self.text=text
 def __str__(self):return self.text
board,pcb,pads,nets,*_=t.Pure(methods[0]).clearance_fixture();board.GetNetsByName=lambda:{WxString('N'):nets['N'],WxString('VCC'):nets['VCC']}
old=RUN/'code/experiments/pic_mixed_transport_probe_v1/worker.py';spec=importlib.util.spec_from_file_location('old_type_worker003',old);oldworker=importlib.util.module_from_spec(spec);spec.loader.exec_module(oldworker)
try:oldworker.clearances(board,pcb)
except ValueError as exc:old_error=str(exc)
else:raise AssertionError('old compound guard must reject synthetic proxy key')
assert old_error=='native net identity type differs'
api=[];rows=t.worker.clearances(board,pcb,api_types=api);assert len(rows)==247 and all(x['raw_return_types']['key']=='WxString' for x in api)
assert all(sha(D/n)==pin for n,pin in pins.items())
result={'schema':1,'passed':True,'scope':'Pure correction review. WxString test objects are hypothetical controls, not inferred actual003 types.','source_pins':pins,'failed003_worker_sha256':sha(old),'existing_methods_passed':methods,'same_control_old_error':old_error,'same_control_fixed_rows':len(rows),'raw_proxy_types_captured':True,'strict_rejected_netcode_types':['bool','float','str'],'source_same_context_guards_retained':True,'source_unchanged_during_controls':True,'native_jobs':0,'jvm_jobs':0,'remaining_blockers':[]}
(H/'probe-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'methods':3,'old_error':old_error,'fixed_rows':len(rows)},indent=2))
