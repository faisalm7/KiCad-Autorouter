"""Pure lifecycle checks with retained rows; no native/JVM or fresh export evidence."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;D=ROOT/'experiments/pic_mixed_transport_probe_v1'
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT));sys.path.insert(0,str(D))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={n:sha(D/n) for n in ('worker.py','driver.py','test_draft.py','PROTOCOL.json','README.md')}
spec=importlib.util.spec_from_file_location('mixed_lifecycle_test',D/'test_draft.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
methods=['test_load_observation_does_not_call_unsupported_drc','test_load_observation_binding_and_scope','test_rejected_netcode_type_retained_without_drc']
with patch.object(t,'HERE',HERE):
 for method in methods:getattr(t.Pure(method),method)()
state=json.loads((ROOT/'.runs/pic-mixed-transport-probe-004/clearance-initialization.json').read_text())
context=json.loads((ROOT/'evidence/pic-custom-observation-002/observation.json').read_text())
source=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb'
notes=t.mapping.source_notes(t.sx.read(source),json.loads(source.with_suffix('.kicad_pro').read_text()))
clear={'scope':t.worker.OBSERVATION_SCOPE,'initialization_qualified':False,'pairwise_rules_qualified':False,'drc_report_executed':False,
 'api_types':copy.deepcopy(state['pre_initialization_api_types']),'rows':copy.deepcopy(state['pre_initialization'])}
saved={stage:copy.deepcopy(clear) for stage in ('before_export','after_export')}
custom={'observation_'+stage:{'clearance_observation':copy.deepcopy(clear)} for stage in saved}
assert t.driver.verify_load_observations(custom,saved,context,notes)==clear
results=[{'case':'retained_actual_rows_synthetic_two_stage_positive','rejected':False}]
changes={
 'false_flag_integer_zero':lambda c,s:c['observation_before_export']['clearance_observation'].update(initialization_qualified=0),
 'false_flag_true':lambda c,s:c['observation_after_export']['clearance_observation'].update(drc_report_executed=True),
 'missing_sidecar_stage':lambda c,s:s.pop('after_export'),
 'sidecar_row_mismatch':lambda c,s:s['before_export']['rows'][0].update(net='FORGED'),
 'all_stage_wrong_class':lambda c,s:[v['rows'][0].update(netclass='FORGED') for v in [c['observation_before_export']['clearance_observation'],c['observation_after_export']['clearance_observation'],*s.values()]],
 'after_export_own_change':lambda c,s:[v['rows'][0]['own'][0].update(value_nm=999) for v in [c['observation_after_export']['clearance_observation'],s['after_export']]],
 'extra_initialized_claim':lambda c,s:[v.update(initialized=True) for v in [c['observation_before_export']['clearance_observation'],c['observation_after_export']['clearance_observation'],*s.values()]],
 'missing_original_terminal':lambda c,s:[v['rows'].pop() for v in [c['observation_before_export']['clearance_observation'],c['observation_after_export']['clearance_observation'],*s.values()]],
}
for name,mutate in changes.items():
 c=copy.deepcopy(custom);s=copy.deepcopy(saved);mutate(c,s)
 try:t.driver.verify_load_observations(c,s,context,notes)
 except (ValueError,KeyError,TypeError) as exc:results.append({'case':name,'rejected':True,'error':str(exc)})
 else:raise AssertionError(name+' unexpectedly passed')
assert all(sha(D/n)==p for n,p in pins.items())
result={'schema':1,'passed':True,'source_pins':pins,'methods':methods,'cases':results,
 'scope':'Actual retained pre-call rows reused in synthetic two-stage contracts. No export/initialization/native behavior newly established.',
 'original004_sidecar_sha256':sha(ROOT/'.runs/pic-mixed-transport-probe-004/clearance-initialization.json'),
 'prior_context_sha256':sha(ROOT/'evidence/pic-custom-observation-002/observation.json'),'native_jobs':0,'jvm_jobs':0,'remaining_blockers':[]}
(HERE/'probe-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'existing_methods':len(methods),'independent_cases':len(results)}))
