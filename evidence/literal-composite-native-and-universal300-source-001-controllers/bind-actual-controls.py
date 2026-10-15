from pathlib import Path
import json,shutil,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
D=Path(__file__).parent;T=D/'.runs/universal-shift-interface-native-paired300-002-protocol.template.json';s=f.read_json(T)
sourcecopy=R/'.runs/literal-composite-source-support-001/new-netclass.py';assert not sourcecopy.exists();shutil.copyfile(R/'autorouter/netclass.py',sourcecopy)
gate=s['netclass_delta']['control'];result=f.read_json(R/gate['result']);outer=f.read_json(R/gate['execution']);readback='.runs/literal-composite-native-controls-readback-001/execution.json';review=f.read_json(R/readback)
assert result['controls_passed'] is True and outer['passed'] is True and review['passed'] is True
material=pc.inventory((R/gate['result']).parent,max_bytes=64*1024**2,max_files=3000,max_entries=6000,with_directories=True)
assert f.canonical(material[0])==f.canonical(outer['actor_material'])
gate.update(result_sha256=p.sha(R/gate['result']),execution_sha256=p.sha(R/gate['execution']),readback_execution=readback,readback_execution_sha256=p.sha(R/readback),source_hashes=result['source_hashes'],shared_checks=result['shared_checks'],positive_native=result['positive_native'],negative_saved_native=result['negative_saved_native'],material=material)
gate.pop('source_before',None)
gate['pins']={str(((R/gate['result']).parent/name).relative_to(R)):pin for name,pin in material[0].items()}
for name in [gate['execution'],readback,'experiments/literal_composite_controls_v1/run.py','.runs/run-literal-composite-native-controls-001.py','.runs/read-literal-composite-native-controls-001.py',*outer['source_pins']]:gate['pins'][name]=p.sha(R/name)
s['netclass_delta']['implementation_sha256']['new']=p.sha(R/'autorouter/netclass.py');s['netclass_delta']['captured_source']['new']=str(sourcecopy.relative_to(R))
s['new_prerequisites_charge']=[1+outer['wall_seconds']+2+review['wall_seconds']+2,1+outer['full_cpu_seconds']+2+review['full_cpu_seconds']+2]
assert max(max(row['charged_wall_seconds'],row['charged_cpu_seconds']) for row in s['prior_matrix']['rows'])+max(s['new_prerequisites_charge'])+180<=300
T.write_text(json.dumps(s,indent=2)+'\n')
for source in (D/'.runs').iterdir():
 if source.suffix=='.py':
  dest=R/'.runs'/source.name;assert not dest.exists();shutil.copyfile(source,dest)
print(json.dumps(dict(control_files=len(material[0]),gate_pins=len(gate['pins']),new_charge=s['new_prerequisites_charge'],status=s['status'])))
