from pathlib import Path
import copy,hashlib,json,sys
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
from experiments.pic_mixed_transport_probe_v1 import routing_checks as c
from autorouter import pipeline as p
src=root/'evidence/pic-corrected-adapter-routing-001'
original=json.loads((src/'observations.json').read_text())
expected=json.loads((src/'routing-expectations.json').read_text())
receipt=json.loads((src/'summary.json').read_text())['routing_adapter']
retained=json.loads((root/'evidence/pic-selective-area-observation-002/observations.json').read_text())
value=copy.deepcopy(original)
for key in ('settings_loaded','settings_enabled','settings_final'):
 config=json.loads(value[key]['configuration_json']);config['scoring'].update(via_costs=25,plane_via_costs=3)
 value[key]['configuration_json']=json.dumps(config)
value['case']['argv']+=p.engine_scoring_settings('via_low')['argv']
results=[]
for name in ('unchanged_default','declared_low','prefix_removed','extra_flag','wrong_cost','wrong_mode'):
 v=copy.deepcopy(original if name=='unchanged_default' else value);mode=None if name=='unchanged_default' else 'via_low'
 if name=='prefix_removed':v['case']['argv']=v['case']['argv'][-2:]
 if name=='extra_flag':v['case']['argv'].insert(0,'--router.scoring.via_costs=999')
 if name=='wrong_cost':
  for key in ('settings_loaded','settings_enabled','settings_final'):
   config=json.loads(v[key]['configuration_json']);config['scoring']['via_costs']=50;v[key]['configuration_json']=json.dumps(config)
 if name=='wrong_mode':mode='via_default'
 try:r=c.compare(v,expected,retained,adapter_receipt=receipt,scoring_variant=mode);results.append({'case':name,'accepted_checker':True,'routing_accepted':r['routing_accepted']})
 except Exception as e:results.append({'case':name,'accepted_checker':False,'exception':type(e).__name__+': '+str(e)})
print(json.dumps({'synthetic_mutations_of_retained_data_not_solver_evidence':True,'checker_sha256':hashlib.sha256(Path(c.__file__).read_bytes()).hexdigest(),'results':results},indent=2))
