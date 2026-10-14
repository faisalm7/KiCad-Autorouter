from pathlib import Path
import resource,sys,time
START=time.monotonic();CPU0=0.;BOOTSTRAP_WALL_ALLOWANCE=1. # Lifetime CPU; conservative unobserved launch-wall charge.
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import json,signal
def interrupted(*_):raise KeyboardInterrupt
previous_handlers={sig:signal.signal(sig,interrupted) for sig in (signal.SIGINT,signal.SIGTERM)}
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
out=ROOT/'.runs/roller-export-alias-native-003-execution';out.mkdir()
head=p.tool_manifest()['git_head'];protocol=f.read_json(ROOT/'experiments/roller_export_alias_v1/CONTINUATION_PROTOCOL.json');priorwall=protocol['prior_active_wall_seconds'];priorcpu=protocol['prior_full_cpu_seconds'];cap=60.
assert protocol['wrapper_sha256']==p.sha(Path(__file__)) and protocol['launcher_sha256']==p.sha(ROOT/'.runs/launch-roller-export-alias-native-003.py')
process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/launch-roller-export-alias-native-003.py')],cwd=out,log=out/'command.log',timeout=cap-max(priorwall,priorcpu)-BOOTSTRAP_WALL_ALLOWANCE,max_log_bytes=128*1024,max_workdir_bytes=32*1024**2,max_group_rss_bytes=2*1024**3)
record={'schema':1,'process':process,'whole_new_wall_seconds':time.monotonic()-START+BOOTSTRAP_WALL_ALLOWANCE,'post_bootstrap_wall_seconds':time.monotonic()-START,'bootstrap_wall_allowance_seconds':BOOTSTRAP_WALL_ALLOWANCE,'whole_new_full_cpu_seconds':h.cpu_seconds()-CPU0,'git_head':head,'controller_sha256':p.sha(Path(__file__)),'launcher_sha256':p.sha(ROOT/'.runs/launch-roller-export-alias-native-003.py'),'protocol_sha256':p.sha(ROOT/'experiments/roller_export_alias_v1/CONTINUATION_PROTOCOL.json'),'log_sha256':p.sha(out/'command.log'),'prior_reported_active_wall_seconds':priorwall,'prior_reported_full_cpu_seconds':priorcpu,'scope':'Current post-bootstrap foreground wall plus explicit1second launch allowance; lifetime SELF+waitedCHILD CPU including imports. Bindings/import/refill/fullSCH/candidate/publication/readback included. This is a conservative wall charge, not a measured exact bootstrap wall duration. Add reported retained originalbaseline and failed001/002 wholecaptures; historical scopes/unknown older labhelper startup retained, calendar gap disclosed. No routingquality/speedup or wholehistoricalexact-runtime claim; current completeforeground bounded.'}
record.update(combined_known_active_wall_seconds=priorwall+record['whole_new_wall_seconds'],combined_known_full_cpu_seconds=priorcpu+record['whole_new_full_cpu_seconds']);record['within60']=max(record['combined_known_active_wall_seconds'],record['combined_known_full_cpu_seconds'])<=cap
candidate=ROOT/'.runs/roller-export-alias-native-003';owner={};h.capture_destination(owner,out);candidate_owner={}
def invalidate(exc):
 if (candidate/'result.json').is_file():
  h.capture_destination(candidate_owner,candidate);h.owned_destination(candidate_owner)
  data=f.read_json(candidate/'result.json')
  if data.get('controls_passed') is True:
   data.update(status='outer_invalidated',controls_passed=False,accepted=False,reason=type(exc).__name__+': '+str(exc))
   f.publish(candidate,data,lambda:(_ for _ in ()).throw(p.Rejected(data['reason'])),lambda:data.update(controls_passed=False,accepted=False),lambda:0,owned=lambda:h.owned_destination(candidate_owner))
try:
 if not record['within60']:raise p.Rejected('complete foreground plus prior reported costs exceeds60')
 h.owned_destination(owner);p.save_json(out/'execution.json',record)
 if f.read_json(out/'execution.json')!=record:raise p.Rejected('outer execution changed after publication')
 if max(priorwall+time.monotonic()-START+BOOTSTRAP_WALL_ALLOWANCE,priorcpu+h.cpu_seconds()-CPU0)>cap:raise p.Rejected('final outer publication crosses60')
 if process['status']=='success' and process['exit_code']==0:
  h.capture_destination(candidate_owner,candidate);h.owned_destination(candidate_owner)
  data=f.read_json(candidate/'result.json')
  if data.get('status')!='controls_passed' or data.get('controls_passed') is not True:raise p.Rejected('successful child lacks canonical positive control')
except (Exception,KeyboardInterrupt) as exc:
 # Invalidate the canonical child positive before attempting any diagnostic
 # outer write. A missing/failed outer receipt cannot leave positive controls.
 invalidate(exc)
 record.update(outer_publication_valid=False,reason=type(exc).__name__+': '+str(exc))
 try:h.owned_destination(owner);p.save_json(out/'execution-rejection.json',record)
 except (Exception,KeyboardInterrupt):pass
 raise
finally:
 for sig,handler in previous_handlers.items():signal.signal(sig,handler)
print(json.dumps({k:record[k] for k in ('whole_new_wall_seconds','whole_new_full_cpu_seconds','combined_known_active_wall_seconds','combined_known_full_cpu_seconds','within60')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and record['within60'] else 2)
