"""Prepare the next committed runtime with existing product builders; no routing."""
from pathlib import Path
import os,sys,time,resource,subprocess,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv
from autorouter.runner import run
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
full_path=ROOT/'.runs/full-integration-161/execution.json';full=json.loads(full_path.read_text());plan=json.loads((full_path.parent/'protocol.json').read_text())
assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete']
tools=p.tool_manifest();assert tools['implementation_sha256']==plan['tools']['implementation_sha256']
CASE=ROOT/'.runs/runtime-directory-021';CASE.mkdir(exist_ok=False);runtime=CASE/'runtime'
env={k:v for k,v in os.environ.items()if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
steps=[]
def step(name,argv,bound,workdir=CASE):
 result=run([str(x)for x in argv],cwd=workdir,env=env,log=CASE/(name+'.log'),timeout=bound,max_group_rss_bytes=1024**3,max_workdir_bytes=256*1024**2)
 steps.append(dict(name=name,**result));p.save_json(CASE/(name+'-process.json'),result)
 if result['status']!='success' or result['exit_code']!=0 or not result['cleanup_complete']:raise RuntimeError(name+' failed')
record=dict(schema=1,prepared=False,installed_doctor=False,actual_GUI=False,routing_executed=False,published=False,source_head=tools['git_head'],source_tools=tools,full161_sha256=p.sha(full_path),processes=steps)
try:
 step('build',[ROOT/'.venv/bin/python','-B',ROOT/'scripts/prepare_runtime.py','--output',runtime,'--copy-local-engine'],60)
 step('venv',[ROOT/'.venv/bin/python','-B','-m','venv','--copies','--without-pip',runtime/'.venv'],20)
 step('doctor',[runtime/'.venv/bin/python','-B','-m','autorouter','doctor'],30,workdir=runtime)
 record.update(prepared=True,installed_doctor=True,manifest_sha256=p.sha(runtime/pv.MANIFEST),runtime=str(runtime),immutable_module_count=len(tools['implementation_sha256']))
 assert p.tool_manifest()==tools
except BaseException as exc:
 record.update(error=type(exc).__name__+': '+str(exc));raise
finally:
 record.update(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
 p.save_json(CASE/'setup.json',record)
print(json.dumps({k:record[k]for k in ('prepared','installed_doctor','source_head','manifest_sha256','wall_seconds','full_CPU_seconds')}))
