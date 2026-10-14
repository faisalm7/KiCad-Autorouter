from pathlib import Path
import sys,time,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=ROOT/'.runs/full-integration-025';out.mkdir()
tools=p.tool_manifest();start=time.monotonic();cpu=time.process_time()+f.child_cpu()
process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/full-suite-local-root-019.py')],cwd=out,log=out/'command.log',timeout=180,max_log_bytes=384*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
record={'schema':1,'git_head':tools['git_head'],'tools':tools,'process':process,'wall_seconds':time.monotonic()-start,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,'controller_sha256':p.sha(Path(__file__)),'log_sha256':p.sha(out/'command.log'),'scope':'Full current root suite at committed parent-class production integration and DSN-incumbent lineage repair. Real native CLI controls are separate. Actual new native qualification is separate; same root discover(tests) through a project-owned launch adapter. Outer2MiB bound covers log directory; existing fixture-specific/temp limits remain, not a global filesystem sandbox. Native Sonde comparison is separate real integration evidence; test counts do not establish routing quality.'}
assert p.tool_manifest()==tools
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('git_head','wall_seconds','full_cpu_seconds')}));print(json.dumps({k:process[k] for k in ('status','exit_code','cleanup_complete')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] else 2)
