"""Lead-only first fixed DS18B20 acquisition after checkpoint/backup/restore release."""
import time,resource
START=time.monotonic()
def cpu():
 return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
protocol=ROOT/'.runs/ds18b20-original-preparation-001/fetch-input-pins.json';protocol_pin=p.sha(protocol);plan=f.read_json(protocol)
assert plan['status']=='frozen_for_lead_execution' and plan['kind']=='ds18b20-source-fetch-v1'
tools=p.tool_manifest();assert tools==plan['tools'] and tools['git_head']==plan['git_head']
assert p.sha(Path(__file__))==plan['wrapper_sha256']
assert all(p.sha(ROOT/name)==digest for name,digest in plan['code_sha256'].items())
controller=ROOT/'scripts/fetch_led_demo.py';out=ROOT/'.runs/ds18b20-fetch-execution-001';out.mkdir()
# The fixed source helper requires its project-relative destination argument.
argv=[str(ROOT/'.venv/bin/python'),'-B',str(controller),'--project','ds18b20','--fetch','--output','.data/ds18b20-demo-001']
assert argv==plan['command']
process=run(argv,cwd=out,log=out/'command.log',timeout=max(.001,318-(time.monotonic()-START)),max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=1024**3)
current=(p.tool_manifest()==tools and p.sha(protocol)==protocol_pin and p.sha(Path(__file__))==plan['wrapper_sha256'] and all(p.sha(ROOT/name)==digest for name,digest in plan['code_sha256'].items()))
wall,full=time.monotonic()-START,cpu()-CPU0;within=max(wall,full)+2<=320
passed=current and within and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and not process['log_truncated']
record=dict(schema=1,passed=passed,process=process,source_current=current,tools=tools,protocol_sha256=protocol_pin,controller_sha256=p.sha(controller),wrapper_sha256=p.sha(Path(__file__)),wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2,whole_delivery_within_budget=within,scope='First exact DS18B20 fiveoriginal119518B acquisition including PRL and fullREADME/flatSCH; one exactREADME notice copy yields6nativefiles124777B. Explicit publisher designgrant retained; no standaloneLICENSE invented. FiveGET/119523B,300internalwallCPU/2MiB output. No cachefallback/models/scripts/Native/engine or publicCAD redistribution. Research cost overruns/unknownCPU retained; no support/ancestry/function claim.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('passed','source_current','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if passed else 2)
