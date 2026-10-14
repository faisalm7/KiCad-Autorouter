from pathlib import Path
import resource,sys,time
START=time.monotonic();r=resource.getrusage(resource.RUSAGE_SELF);ch=resource.getrusage(resource.RUSAGE_CHILDREN);CPU0=r.ru_utime+r.ru_stime+ch.ru_utime+ch.ru_stime
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import json
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
out=ROOT/'.runs/roller-export-alias-native-003-execution';out.mkdir()
head=p.tool_manifest()['git_head'];protocol=f.read_json(ROOT/'experiments/roller_export_alias_v1/CONTINUATION_PROTOCOL.json');priorwall=protocol['prior_active_wall_seconds'];priorcpu=protocol['prior_full_cpu_seconds'];cap=60.
assert protocol['wrapper_sha256']==p.sha(Path(__file__)) and protocol['launcher_sha256']==p.sha(ROOT/'.runs/launch-roller-export-alias-native-003.py')
process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/launch-roller-export-alias-native-003.py')],cwd=out,log=out/'command.log',timeout=cap-max(priorwall,priorcpu),max_log_bytes=128*1024,max_workdir_bytes=32*1024**2,max_group_rss_bytes=2*1024**3)
record={'schema':1,'process':process,'whole_new_wall_seconds':time.monotonic()-START,'whole_new_full_cpu_seconds':h.cpu_seconds()-CPU0,'git_head':head,'controller_sha256':p.sha(Path(__file__)),'launcher_sha256':p.sha(ROOT/'.runs/launch-roller-export-alias-native-003.py'),'protocol_sha256':p.sha(ROOT/'experiments/roller_export_alias_v1/CONTINUATION_PROTOCOL.json'),'log_sha256':p.sha(out/'command.log'),'prior_reported_active_wall_seconds':priorwall,'prior_reported_full_cpu_seconds':priorcpu,'scope':'Complete current parent+child imports/startup/bindings/import/refill/fullSCH/candidate/publication/readback. Add reported retained originalbaseline and failed001/002 wholecaptures; historical scopes/unknown older labhelper startup retained, calendar gap disclosed. No routingquality/speedup or wholehistoricalexact-runtime claim; current completeforeground bounded.'}
record.update(combined_known_active_wall_seconds=priorwall+record['whole_new_wall_seconds'],combined_known_full_cpu_seconds=priorcpu+record['whole_new_full_cpu_seconds']);record['within60']=max(record['combined_known_active_wall_seconds'],record['combined_known_full_cpu_seconds'])<=cap
candidate=ROOT/'.runs/roller-export-alias-native-003'
if (candidate/'result.json').is_file():
 data=f.read_json(candidate/'result.json')
 if not record['within60'] and data.get('controls_passed'):
  data.update(status='outer_budget_exceeded',controls_passed=False)
  f.publish(candidate,data,lambda:(_ for _ in ()).throw(p.Rejected('complete currentforeground plus prior reported costs exceeds60')),lambda:data.update(controls_passed=False,accepted=False),lambda:0)
p.save_json(out/'execution.json',record)
if max(priorwall+time.monotonic()-START,priorcpu+h.cpu_seconds()-CPU0)>cap:
 record.update(within60=False,final_publication_crossed_cap=True);p.save_json(out/'execution.json',record)
 data=f.read_json(candidate/'result.json');data.update(status='outer_budget_exceeded',controls_passed=False)
 f.publish(candidate,data,lambda:(_ for _ in ()).throw(p.Rejected('final outer publication crosses60')),lambda:data.update(controls_passed=False,accepted=False),lambda:0)
print(json.dumps({k:record[k] for k in ('whole_new_wall_seconds','whole_new_full_cpu_seconds','combined_known_active_wall_seconds','combined_known_full_cpu_seconds','within60')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and record['within60'] else 2)
