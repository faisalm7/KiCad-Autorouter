"""Existing incremental helper and already-restored full base; all writers idle."""
from pathlib import Path
import sys,time,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=ROOT/'.local-backups/runtime010-milestone-incremental-execution-002';out.mkdir(mode=0o700)
parent=ROOT/'.local-backups/checkpoint-20261015T181606Z-b9d396079eb4422f9ba8aee6b1a85b28/receipt.json'
start=time.monotonic();cpu=time.process_time()+f.child_cpu()
process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/backup.py'),'--incremental',str(parent)],cwd=out,log=out/'command.log',timeout=600,max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=4*1024**3)
record={'schema':1,'process':process,'wall_seconds':time.monotonic()-start,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,'controller_sha256':p.sha(Path(__file__)),'log_sha256':p.sha(out/'command.log'),'git_head':p.tool_manifest()['git_head'],'parent_full_receipt':str(parent),'parent_sha256':p.sha(parent),'scope':'New runtime010 target after actual byte refusal001; finite12.25GiB/100MiBreceipt correction checkpoint8250c18e, unchanged350000files/192MiBchain/scopes/security. Direct already-restored full base. Captures010/061/full143/prospectiveNetTie plus all009negative/history and failure/capacity evidence. All Native/JVM/GUI/fullsuite/CI and writers idle. Actual delta integrity only; new-target full restoration requires disk headroom and is pending. Completed008/007restorations not repeated. Mac-only by owner choice.'}
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('git_head','wall_seconds','full_cpu_seconds')}));print(json.dumps({k:process[k] for k in ('status','exit_code','cleanup_complete')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 else 2)
