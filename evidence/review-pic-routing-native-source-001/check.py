"""Narrow saved-byte and mock-native readback; no owned native/JVM processes."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
from experiments.pic_mixed_transport_probe_v1 import driver,routing_checks,routing_native,ses_checks
OUT=Path(__file__).parent

def pin(path):
 raw=path.read_bytes();return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def main():
 files=['driver.py','routing_checks.py','routing_native.py','ses_checks.py','ROUTING_NATIVE_PROTOCOL.json']
 pins={n:pin(Path(driver.__file__).parent/n) for n in files}
 snapshot=OUT/'snapshot-001';snapshot.mkdir()
 for n in files:(snapshot/n).write_bytes((Path(driver.__file__).parent/n).read_bytes())
 cache=ROOT/'.runs/pic-selective-routing-001';before=driver.inventory(cache)
 summary=json.loads((cache/'summary.json').read_text());protocol=json.loads((Path(driver.__file__).parent/'ROUTING_NATIVE_PROTOCOL.json').read_text())
 assert pin(cache/'summary.json')==protocol['basis']['.runs/pic-selective-routing-001/summary.json']
 assert all(before.get(k)==v for k,v in summary['frozen_evidence'].items())
 observed=json.loads((cache/'observations.json').read_text());expected=json.loads((cache/'routing-expectations.json').read_text());retained=json.loads((cache/'selective-basis-observations.json').read_text())
 failure=None
 try:routing_checks.compare(observed,expected,retained)
 except ValueError as exc:failure='ValueError: '+str(exc)
 assert failure=='ValueError: exact integer engine point required'
 relaxed=routing_checks.compare(observed,expected,retained,native_diagnostic=True)
 assert relaxed['geometry_verified'] is False and relaxed['routing_accepted'] is False and relaxed['cancel_control'] is False
 original=sx.read(cache/'observe-input'/driver.original.SOURCE.name);task=copy.deepcopy(original)
 task[:]=[n for n in task if not isinstance(n,list) or not n or n[0] not in p.ROUTES]
 _,proposal=ses_checks.audit((cache/'raw.ses').read_bytes(),(cache/'unrouted.dsn').read_bytes(),expected,task,generated=True,proposal_only=True)
 assert proposal['safe_structure'] is True and proposal['generated_engine_to_ses_exact'] is False and proposal['proposal_only'] is True
 negatives={}
 for name,args in [('with_geometry',{'geometry':observed['final_geometry'],'generated':True,'proposal_only':True}),('without_generated',{'proposal_only':True})]:
  try:ses_checks.audit((cache/'raw.ses').read_bytes(),(cache/'unrouted.dsn').read_bytes(),expected,task,**args)
  except ValueError as exc:negatives[name]=str(exc)
  else:raise AssertionError(name)
 prior=ROOT/'.runs/review-pic-routing-controller-001/reproduce_boundary_v3.py';spec=importlib.util.spec_from_file_location('prior_falsifier',prior);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 call=routing_native.execute;actual_result={}
 def diagnostic(*args,**kwargs):
  args=list(args);args[3]={'safe_structure':True,'generated_engine_to_ses_exact':False,'retained_routing_failure':failure}
  result=call(*args,**kwargs,diagnostic_only=True);actual_result.update(result);return result
 with patch.object(routing_native,'execute',diagnostic):boundary=module.run(OUT/'mock-clean','none')
 assert boundary['returned'] and boundary['error'] is None
 assert actual_result['native_routing_scope_passed'] is True and actual_result['candidate_emitted'] is True
 assert all(actual_result[k] is False for k in ('routing_accepted','production_support_qualified','completed'))
 assert actual_result['original_preflight_reasons']
 assert driver.inventory(cache)==before
 assert all(pin(Path(driver.__file__).parent/n)==v for n,v in pins.items())
 result={'schema':1,'native_executed':False,'jvm_executed':False,'source_pins':pins,'cache_summary':pin(cache/'summary.json'),
 'cache_file_count':len(before),'cache_unchanged':True,'strict_failure':failure,'diagnostic_comparison':relaxed,
 'proposal_summary':{k:proposal[k] for k in ('safe_structure','exact_custom_polygons','placements','ses_paths','ses_segments','ses_vias','generated_engine_to_ses_exact','proposal_only')},
 'proposal_negative_controls':negatives,'mock_native_positive':boundary,
 'mock_native_verdict':{k:actual_result[k] for k in ('candidate_emitted','native_routing_scope_passed','routing_accepted','production_support_qualified','completed','original_preflight_reasons')},
 'scope':'Saved-byte checks and real-file mock native. Actual new native run is still unexecuted by this review.'}
 (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
