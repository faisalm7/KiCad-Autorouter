"""One bounded GUI-job observation via existing owned metadata helpers; no signals."""
from pathlib import Path
import sys,time,json,datetime,os
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from scripts.native_cancellation import process_metadata,output_bytes
from autorouter import pipeline as p
W=R/'.runs/runtime-directory-057/runtime/.runs/gui-session090/jobs/autorouter-gui-acd41daddca34560a4ea0e29f2d83629'
O=R/'.runs/gui090-active-engine-001';assert not O.exists();O.mkdir(mode=0o700)
assert dict(pid=16012,ppid=15915,pgid=15914) in process_metadata(parent_pid=15915)
started=time.monotonic();observed=None
while time.monotonic()-started<25:
 log=W/'route/engine.log'
 if log.is_file() and log.stat().st_size and not (W/'route/engine-process.json').exists():
  parents=[x for x in process_metadata(parent_pid=16012) if x['pid']==x['pgid']]
  if len(parents)==1:
   engines=[x for x in process_metadata(parent_pid=parents[0]['pid']) if x['pid']==x['pgid']]
   if len(engines)==1:
    output_bytes(W);observed=dict(GUI=dict(pid=16012,ppid=15915,pgid=15914),CLI=parents[0],engine=engines[0],engine_log_bytes=log.stat().st_size,engine_log_sha256=p.sha(log));break
 time.sleep(.01)
record=dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workspace=str(W),observed=observed,wall_seconds=time.monotonic()-started,helper_sha256=p.sha(R/'scripts/native_cancellation.py'),actual_GUI_cancel=False,scope='Single <=25s foreground control observation; existing bounded lineage/log/size readers only. No process signalled, Native/engine spawned, persistent monitor or cancellation/algorithm-entry claim.')
p.save_json(O/'observation.json',record);print(json.dumps(record),flush=True)
raise SystemExit(0 if observed else 2)
