"""Shared bounded supervisor for the new original-LED diagnostic only."""
from pathlib import Path
import time,sys
START=time.monotonic();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import json
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from experiments.licensed_acquisition_v1 import fetch as shared
out=h.real_path(ROOT/'.runs/push-button-led-original-native-001-execution',existing=False);candidate=h.real_path(ROOT/'.runs/push-button-led-original-native-001',existing=False)
if out.exists() or candidate.exists():raise p.Rejected('exclusive fresh diagnostic outputs required')
out.mkdir();owner={};h.capture_destination(owner,out);record={'schema':1,'accepted':False,'status':'incomplete'}
with shared.cancellation():
 tools=p.tool_manifest();initial={Path(__file__):p.sha(Path(__file__)),ROOT/'.runs/launch-push-button-led-original-native-001.py':p.sha(ROOT/'.runs/launch-push-button-led-original-native-001.py'),ROOT/'experiments/original_project_native_v1/driver.py':p.sha(ROOT/'experiments/original_project_native_v1/driver.py')}
 def stable():
  h.owned_destination(owner)
  if p.tool_manifest()!=tools or any(p.sha(path)!=digest for path,digest in initial.items()):raise p.Rejected('original diagnostic supervisor source/tool bindings changed')
 try:
  process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/launch-push-button-led-original-native-001.py')],cwd=out,log=out/'command.log',timeout=90,max_log_bytes=256*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
  record.update(status='completed',process=process,tools=tools,initial_source_sha256={str(k):v for k,v in initial.items()},charged_wall_seconds=time.monotonic()-START+1,lifetime_full_cpu_seconds=h.cpu_seconds(),scope='New original-LED savedrefill/fullsingleSCH observation; noengine/new modern source only. LifetimeSELF+CHILDCPU, post-bootstrapwall+explicit1second allowance, separate90s cap; historical source research/cache preparation separate.',result_sha256=p.sha(candidate/'result.json'))
  stable();assert max(record['charged_wall_seconds'],record['lifetime_full_cpu_seconds'])<=90
  p.save_json(out/'execution.json',record);stable()
  assert f.read_json(out/'execution.json')==record and max(time.monotonic()-START+1,h.cpu_seconds())<=90
 except (Exception,KeyboardInterrupt) as exc:
  if candidate.exists() and (candidate/'result.json').is_file():
   owned={};h.capture_destination(owned,candidate);data=f.read_json(candidate/'result.json');data.update(status='outer_invalidated',native_routing_scope_accepted=False,accepted=False,error=type(exc).__name__+': '+str(exc))
   f.publish(candidate,data,lambda:(_ for _ in ()).throw(p.Rejected(data['error'])),lambda:None,lambda:0,owned=lambda:h.owned_destination(owned))
  raise
print(json.dumps({k:record[k] for k in ('status','charged_wall_seconds','lifetime_full_cpu_seconds')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 else 2)
