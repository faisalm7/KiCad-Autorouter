"""Independent small real-file/mocked-boundary publication controls; no native."""
import hashlib,importlib.util,json,sys
from pathlib import Path
from unittest import mock
module_path=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(exist_ok=False)
sys.path.insert(0,str(module_path.parent))
spec=importlib.util.spec_from_file_location('review_pic_controller',module_path);d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
rows=[]
for name in ['unchanged','canonical_during_final_size','budget_during_final_size','returned_record_during_final_size']:
 folder=out/name;folder.mkdir();record={'schema':1,'status':'observations_complete','observations_complete':True,'routing_accepted':False,'geometry_qualified':False};state={'injected':False,'available':1.0};real_size=d.size
 def size(path):
  if name!='unchanged' and (folder/'summary.json').exists() and not state['injected']:
   state['injected']=True
   if name=='canonical_during_final_size':
    raw=d.read(folder/'summary.json');raw['geometry_qualified']=True;d.p.save_json(folder/'summary.json',raw)
   elif name=='budget_during_final_size':state['available']=0.0
   else:record['geometry_qualified']=True
  return real_size(path)
 with mock.patch.object(d,'size',side_effect=size):result=d.publish(folder,record,lambda:None,lambda:None,lambda:state['available'])
 canonical=d.read(folder/'summary.json') if (folder/'summary.json').exists() else None
 row={'case':name,'injected':state['injected'],'available_at_return':state['available'],'returned':result,'canonical':canonical,'returned_equals_canonical':result==canonical,'native_jobs':0,'engine_jobs':0,'caps_simulated':True}
 row['expected_safety_outcome']=result['observations_complete'] if name=='unchanged' else not result['observations_complete'] and (canonical is None or canonical.get('observations_complete') is False)
 rows.append(row)
summary={'schema':1,'module_sha256':hashlib.sha256(module_path.read_bytes()).hexdigest(),'results':rows,'all_expected':all(x['expected_safety_outcome'] for x in rows),'scope':'Small real output files and mocked final size/budget boundary; no native execution or timed cap qualification.'}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
