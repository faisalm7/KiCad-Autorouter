"""Compact-reference pure review, using retained rows without native execution."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;D=R/'experiments/pic_mixed_transport_probe_v1'
sys.dont_write_bytecode=True;sys.path.insert(0,str(R));sys.path.insert(0,str(D))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={n:sha(D/n) for n in ('worker.py','driver.py','test_draft.py','PROTOCOL.json','README.md')}
original_review=json.loads((H/'manifest.json').read_text());assert all(sha(H/n)==v['sha256'] for n,v in original_review['files'].items())
spec=importlib.util.spec_from_file_location('compact_review_test',D/'test_draft.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
basis=R/'evidence/pic-custom-observation-002';custom=json.loads((basis/'custom-pads.json').read_text());context=json.loads((basis/'observation.json').read_text())
source=R/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb'
notes=t.mapping.source_notes(t.sx.read(source),json.loads(source.with_suffix('.kicad_pro').read_text()))
methods=['test_load_observation_does_not_call_unsupported_drc','test_load_observation_binding_and_scope','test_actual_clearance_sidecar_keeps_existing_context_bound']
with patch.object(t,'HERE',H):
 for method in methods:
  obj=t.Pure(method);obj.custom=custom;obj.context=context;obj.notes=notes;getattr(obj,method)()
actual=json.loads((R/'.runs/pic-mixed-transport-probe-004/clearance-initialization.json').read_text())
clear={'scope':t.worker.OBSERVATION_SCOPE,'initialization_qualified':False,'pairwise_rules_qualified':False,'drc_report_executed':False,'api_types':actual['pre_initialization_api_types'],'rows':actual['pre_initialization']}
saved={s:copy.deepcopy(clear) for s in ('before_export','after_export')}
compact=copy.deepcopy(custom);bulky=copy.deepcopy(custom)
for s in saved:
 compact['observation_'+s]['clearance_observation']=t.worker.observation_reference(saved[s]);bulky['observation_'+s]['clearance_observation']=clear
size=lambda x:len((json.dumps(x,indent=2)+'\n').encode())
assert size(bulky)>1048576>size(compact)
assert len((json.dumps(saved,sort_keys=True)+'\n').encode())<2*1024**2
assert t.driver.verify_load_observations(compact,saved,context,notes)==clear
results=[{'case':'retained_rows_compact_positive','rejected':False}]
def rehash(c,s):
 for stage in s:c['observation_'+stage]['clearance_observation']=t.worker.observation_reference(s[stage])
cases=['wrong_hash','reference_false_as_zero','reference_true','sidecar_false_as_zero_rehash','sidecar_true_rehash','class_rows_rehashed','terminal_removed_rehashed','sidecar_changed_no_rehash','after_export_own_rehashed','unknown_field_rehashed']
for case in cases:
 c=copy.deepcopy(compact);s=copy.deepcopy(saved)
 if case=='wrong_hash':c['observation_before_export']['clearance_observation']['observation_sha256']='0'*64
 elif case=='reference_false_as_zero':c['observation_before_export']['clearance_observation']['initialization_qualified']=0
 elif case=='reference_true':c['observation_after_export']['clearance_observation']['pairwise_rules_qualified']=True
 elif case in ('sidecar_false_as_zero_rehash','sidecar_true_rehash'):
  for v in s.values():v['drc_report_executed']=0 if case=='sidecar_false_as_zero_rehash' else True
  rehash(c,s)
 elif case=='class_rows_rehashed':
  for v in s.values():v['rows'][0]['netclass']='FORGED'
  rehash(c,s)
 elif case=='terminal_removed_rehashed':
  for v in s.values():v['rows'].pop()
  rehash(c,s)
 elif case=='sidecar_changed_no_rehash':s['before_export']['rows'][0]['net']='FORGED'
 elif case=='after_export_own_rehashed':s['after_export']['rows'][0]['own'][0]['value_nm']=999;rehash(c,s)
 elif case=='unknown_field_rehashed':
  for v in s.values():v['initialized']=True
  rehash(c,s)
 try:t.driver.verify_load_observations(c,s,context,notes)
 except (ValueError,KeyError,TypeError) as exc:results.append({'case':case,'rejected':True,'error':str(exc)})
 else:raise AssertionError('unexpected pass '+case)
assert all(sha(D/n)==h for n,h in pins.items())
assert all(sha(H/n)==v['sha256'] for n,v in original_review['files'].items())
result={'schema':1,'passed':True,'source_pins':pins,'prior_manifest_sha256':sha(H/'manifest.json'),'existing_methods':methods,'cases':results,
 'composition_bytes':{'bulky':size(bulky),'compact':size(compact),'context_limit':1048576,'sidecar':len((json.dumps(saved,sort_keys=True)+'\n').encode()),'sidecar_limit':2097152},
 'scope':'Synthetic two-stage composition of retained actual004 rows and original002 geometry; not a new native execution or successful export.',
 'source_and_prior_review_unchanged':True,'native_jobs':0,'jvm_jobs':0,'remaining_blockers':[]}
(H/'compact-probe-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'methods':len(methods),'cases':len(results),'bytes':result['composition_bytes']}))
