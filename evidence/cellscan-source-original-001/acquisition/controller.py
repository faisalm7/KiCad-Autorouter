from pathlib import Path
import time,sys,json
START=time.monotonic();CPU0=time.process_time()
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
CPU0+=f.child_cpu()
spec=f.read_json(ROOT/'.runs/cellscan-fetch-protocol-001.json')
assert all(p.sha(ROOT/n)==pin for n,pin in spec['code_sha256'].items())
out=ROOT/'.runs/cellscan-source-fetch-001';out.mkdir()
process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/fetch_led_demo.py'),'--project','cellscan','--fetch'],cwd=out,log=out/'command.log',timeout=315,max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
record={'schema':1,'process':process,'wall_seconds':time.monotonic()-START,'full_cpu_seconds':time.process_time()+f.child_cpu()-CPU0,'protocol_sha256':p.sha(ROOT/'.runs/cellscan-fetch-protocol-001.json'),'controller_sha256':p.sha(Path(__file__)),'git_head':p.tool_manifest()['git_head'],'scope':'Actual fixed6publicGET/raw1299230B/native8notice packet via existing helpers, no source execution/normalization/Native/engine; oldcap5/2MiB unchanged, thisfixedprofile6/4MiB. Outer sampling beforeimports through worker exit; controller/source300wall/CPU cap includes publication. DataSource is new exposed lead; no pedigree/production/quality/physical claim.'}
assert all(p.sha(ROOT/n)==pin for n,pin in spec['code_sha256'].items())
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('git_head','wall_seconds','full_cpu_seconds')}));print(json.dumps({k:process[k] for k in ('status','exit_code','cleanup_complete')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 else 2)
