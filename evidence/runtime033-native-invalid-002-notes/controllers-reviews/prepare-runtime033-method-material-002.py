"""One independent installed-tool/default query through existing bounded runner."""
from pathlib import Path
import json,sys,time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,gui
from autorouter.runner import run
out=ROOT/'.runs/runtime033-method-material-002';out.mkdir()
runtime=ROOT/'.runs/runtime-directory-033/runtime';manifest=runtime/'runtime-distribution.json'
assert p.sha(manifest)=='115c881aa04a34bf642c57d5af312fe692d1aff013bed095caa3856a614f3987'
query=('import sys,json;from pathlib import Path;sys.path.insert(0,'+repr(str(runtime))+');'
 'from autorouter import pipeline as p,config as c,preferences as pref,comparison as cmp;'
 'assert c.ROOT==Path('+repr(str(runtime))+') and c.NATIVE_VERSION=="10.0.7";'
 'print(json.dumps(dict(tools=p.tool_manifest(),defaults=dict(pref.DEFAULTS),comparison_policy=cmp.POLICY)))')
process=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B','-c',query],cwd=out,env=gui.child_environment(),log=out/'tools-defaults.json',timeout=20,max_log_bytes=128*1024,max_group_rss_bytes=512*1024**2,max_workdir_bytes=1024**2)
p.save_json(out/'process.json',process)
assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated']
data=f.read_json(out/'tools-defaults.json');assert data['tools']['git_head']=='a476a0a0647bc51889d291e3e6e2598f4ec24370'
assert data['tools']['source_provenance']['manifest_sha256']==p.sha(manifest)
p.save_json(out/'preparation.json',dict(schema=1,passed=True,controller_sha256=p.sha(Path(__file__)),runtime_manifest_sha256=p.sha(manifest),tools_defaults_sha256=p.sha(out/'tools-defaults.json'),sampled_wall_seconds=time.monotonic()-START,sampled_CPU_seconds=cpu()-CPU0,scope='Independent installed module/tool/default query only. No routing/Native PCB/GUI/comparison run. Research/preparation cost additional to future method budgets; complete exit externally timed.'))
print(json.dumps(dict(passed=True,output=str(out))))
