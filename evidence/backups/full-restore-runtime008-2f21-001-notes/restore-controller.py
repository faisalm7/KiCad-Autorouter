"""Existing incremental helper and already-restored full base; all writers idle."""
from pathlib import Path
import sys,time,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=ROOT/'.local-backups/runtime008-new-full-restoration-execution-001';out.mkdir(mode=0o700)
parent=ROOT/'.local-backups/checkpoint-20261016T184713Z-03592b87ace045b48763a483a647e7d7/receipt.json'
start=time.monotonic();cpu=time.process_time()+f.child_cpu()
process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/backup.py'),'--verify',str(parent)],cwd=out,log=out/'command.log',timeout=1100,max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=4*1024**3)
record={'schema':1,'process':process,'wall_seconds':time.monotonic()-start,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,'controller_sha256':p.sha(Path(__file__)),'log_sha256':p.sha(out/'command.log'),'git_head':p.tool_manifest()['git_head'],'target_retained_receipt':str(parent),'parent_sha256':p.sha(parent),'scope':'One full restoration of NEW runtime008345265file/12715839152B target captured2f21e0be, using the existing350000file-directory/12GiB/98MiBreceipt/192MiBaggregate guarded helper. Original restore-verified full base directly, chain2. Qualifies finite count correction; completed007 restoration not repeated. Native/JVM/GUI/CI idle. All source/evidence retained. On-Mac only by owner choice; no cleanOS/relocated Native/GUI/electrical claim.'}
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('git_head','wall_seconds','full_cpu_seconds')}));print(json.dumps({k:process[k] for k in ('status','exit_code','cleanup_complete')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 else 2)
