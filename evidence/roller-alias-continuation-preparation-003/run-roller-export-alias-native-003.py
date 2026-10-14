"""Finite owned continuation; invalidate child controls on any outer failure."""
from pathlib import Path
import resource,sys,time
START=time.monotonic();CPU0=0.;BOOTSTRAP_WALL_ALLOWANCE=1.
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import json,signal,uuid
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
out=h.real_path(ROOT/'.runs/roller-export-alias-native-003-execution',existing=False)
candidate=h.real_path(ROOT/'.runs/roller-export-alias-native-003',existing=False)
# Preexisting evidence is never owned by this invocation or invalidated.
if out.exists() or candidate.exists():raise p.Rejected('fresh outer and native candidate outputs required')
out.mkdir();owner={};h.capture_destination(owner,out);candidate_owner={};launched=False
record={'schema':1,'outer_publication_valid':False};previous_handlers={};cap=60.;process=None

def invalidate(exc):
 if launched and candidate.exists():
  if not candidate_owner:h.capture_destination(candidate_owner,candidate)
  h.owned_destination(candidate_owner)
  if (candidate/'result.json').is_file():
   data=f.read_json(candidate/'result.json')
   if data.get('controls_passed') is True:
    data.update(status='outer_invalidated',controls_passed=False,accepted=False,reason=type(exc).__name__+': '+str(exc))
    f.publish(candidate,data,lambda:(_ for _ in ()).throw(p.Rejected(data['reason'])),lambda:data.update(controls_passed=False,accepted=False),lambda:0,owned=lambda:h.owned_destination(candidate_owner))

def interrupted(*_):raise KeyboardInterrupt
try:
 for sig in (signal.SIGINT,signal.SIGTERM):previous_handlers[sig]=signal.signal(sig,interrupted)
 initial_tools=p.tool_manifest();head=initial_tools['git_head'];protocol=f.read_json(ROOT/'experiments/roller_export_alias_v1/CONTINUATION_PROTOCOL.json');priorwall=protocol['prior_active_wall_seconds'];priorcpu=protocol['prior_full_cpu_seconds']
 if protocol['wrapper_sha256']!=p.sha(Path(__file__)) or protocol['launcher_sha256']!=p.sha(ROOT/'.runs/launch-roller-export-alias-native-003.py'):raise p.Rejected('prospective wrapper differs')
 initial_bindings={Path(__file__):protocol['wrapper_sha256'],ROOT/'.runs/launch-roller-export-alias-native-003.py':protocol['launcher_sha256'],ROOT/'experiments/roller_export_alias_v1/CONTINUATION_PROTOCOL.json':p.sha(ROOT/'experiments/roller_export_alias_v1/CONTINUATION_PROTOCOL.json')}
 def stable_sources():
  if p.tool_manifest()!=initial_tools or any(p.sha(path)!=digest for path,digest in initial_bindings.items()) or f.read_json(ROOT/'experiments/roller_export_alias_v1/CONTINUATION_PROTOCOL.json')!=protocol:raise p.Rejected('initial outer source/tool/protocol bindings changed')
 launched=True
 process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/launch-roller-export-alias-native-003.py')],cwd=out,log=out/'command.log',timeout=cap-max(priorwall,priorcpu)-BOOTSTRAP_WALL_ALLOWANCE,max_log_bytes=128*1024,max_workdir_bytes=32*1024**2,max_group_rss_bytes=2*1024**3)
 if candidate.exists():h.capture_destination(candidate_owner,candidate)
 # All post-child measurement, hashes, ownership, writes and checks are inside
 # the failure boundary. Cancellation must not strand a canonical positive.
 record.update(process=process,whole_new_wall_seconds=time.monotonic()-START+BOOTSTRAP_WALL_ALLOWANCE,post_bootstrap_wall_seconds=time.monotonic()-START,bootstrap_wall_allowance_seconds=BOOTSTRAP_WALL_ALLOWANCE,whole_new_full_cpu_seconds=h.cpu_seconds()-CPU0,git_head=head,controller_sha256=p.sha(Path(__file__)),launcher_sha256=p.sha(ROOT/'.runs/launch-roller-export-alias-native-003.py'),protocol_sha256=p.sha(ROOT/'experiments/roller_export_alias_v1/CONTINUATION_PROTOCOL.json'),log_sha256=p.sha(out/'command.log'),prior_reported_active_wall_seconds=priorwall,prior_reported_full_cpu_seconds=priorcpu,scope='Post-bootstrap current foreground wall plus explicit1second launch allowance; lifetime SELF+waitedCHILD CPU including imports. Bindings/import/refill/fullSCH/candidate/publication/readback included. Known retained originalbaseline and failed001/002captures added, historical scopes/olderunmeasuredstartup and calendar gap visible. Conservative wall charge, no exactbootstrap/fullhistoricaltime/speedup/routingqualityclaim.')
 record.update(combined_known_active_wall_seconds=priorwall+record['whole_new_wall_seconds'],combined_known_full_cpu_seconds=priorcpu+record['whole_new_full_cpu_seconds']);record['within60']=max(record['combined_known_active_wall_seconds'],record['combined_known_full_cpu_seconds'])<=cap
 if not record['within60']:raise p.Rejected('currentforeground plus reportedprior costs exceeds60')
 stable_sources();record['outer_publication_valid']=True;h.owned_destination(owner);p.save_json(out/'execution.json',record)
 if f.read_json(out/'execution.json')!=record:raise p.Rejected('outer execution changed after publication')
 stable_sources()
 if max(priorwall+time.monotonic()-START+BOOTSTRAP_WALL_ALLOWANCE,priorcpu+h.cpu_seconds()-CPU0)>cap:raise p.Rejected('final outer publication crosses60')
 if process['status']=='success' and process['exit_code']==0:
  h.owned_destination(candidate_owner);data=f.read_json(candidate/'result.json')
  if data.get('status')!='controls_passed' or data.get('controls_passed') is not True:raise p.Rejected('successful child lacks canonical positive control')
except (Exception,KeyboardInterrupt) as exc:
 # Correct the owned child index before any potentially failing outer write.
 invalidate(exc);record.update(outer_publication_valid=False,reason=type(exc).__name__+': '+str(exc))
 for name in ('execution.json','execution.json.partial'):
  file=out/name
  if file.exists():
   h.owned_destination(owner)
   if file.is_symlink() or not file.is_file():raise p.Rejected('unsafe outer publication artifact')
   file.rename(out/('invalidated-'+uuid.uuid4().hex+'-'+name))
 try:h.owned_destination(owner);p.save_json(out/'execution-rejection.json',record)
 except (Exception,KeyboardInterrupt):pass
 raise
finally:
 for sig,handler in previous_handlers.items():signal.signal(sig,handler)
print(json.dumps({k:record[k] for k in ('whole_new_wall_seconds','whole_new_full_cpu_seconds','combined_known_active_wall_seconds','combined_known_full_cpu_seconds','within60')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and record['within60'] else 2)
