"""Independent bounded publication falsifier. No native or engine jobs."""
import hashlib,importlib.util,json,sys
from pathlib import Path
from unittest import mock
module_path=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('review_native_controller',module_path);d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
results=[]
for name in ['unchanged','canonical_during_final_size','budget_during_final_size']:
 folder=out/name;folder.mkdir();record={'schema':1,'status':'completed','controls_passed':True,'routing_accepted':False,'gui_qualified':False};state={'injected':False,'available':1.0};real_size=d.size
 def size(path):
  if name!='unchanged' and (folder/'summary.json').exists() and not state['injected']:
   state['injected']=True
   if name=='canonical_during_final_size':
    raw=d.read(folder/'summary.json');raw['routing_accepted']=True;d.p.save_json(folder/'summary.json',raw)
   else:state['available']=0.0
  return real_size(path)
 with mock.patch.object(d,'size',side_effect=size):result=d.publish(folder,record,lambda:None,lambda:None,lambda:state['available'])
 canonical=d.read(folder/'summary.json') if (folder/'summary.json').exists() else None
 row={'case':name,'injected':state['injected'],'available_at_return':state['available'],'returned_controls_passed':result['controls_passed'],'canonical':canonical,'returned_equals_canonical':result==canonical,'native_jobs':0,'engine_jobs':0,'caps_simulated':True}
 row['expected_safety_outcome']=result['controls_passed'] if name=='unchanged' else not result['controls_passed'] and (canonical is None or canonical.get('controls_passed') is False)
 results.append(row)
summary={'schema':1,'module_sha256':hashlib.sha256(module_path.read_bytes()).hexdigest(),'results':results,'all_expected':all(x['expected_safety_outcome'] for x in results),'scope':'Real small output files and mocked final size/budget boundary; no native execution or timed cap qualification.'}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
