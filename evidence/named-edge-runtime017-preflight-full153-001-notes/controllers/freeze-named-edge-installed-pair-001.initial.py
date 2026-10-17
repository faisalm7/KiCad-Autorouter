"""Freeze two exact installed arms using existing bounded metadata workers."""
from pathlib import Path
import json,sys,hashlib,time,resource,os
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,provenance as pv
from autorouter.runner import run
start=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
cpu0=cpu();base=ROOT/'.runs/named-edge-installed-pair-001';metadata=base/'metadata-001';metadata.mkdir()
full=f.read_json(ROOT/'.runs/full-integration-153/execution.json')
assert full['process']['exit_code']==0 and full['process']['status']=='success' and full['process']['cleanup_complete'] is True
assert full['tools']['implementation_sha256']==p.tool_manifest()['implementation_sha256']
plan=f.read_json(base/'PROTOCOL.draft-001.json');child=base/'qualify-installed-arm.py';outer=base/'run-installed-arm.py'
raw=child.read_bytes();plan['child_sha256']=p.sha(child);plan['outer_controller_sha256']=p.sha(outer)
processes=[];env={key:value for key,value in os.environ.items()if key not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}}
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
def query(name,argv,cwd):
    result=run([*f.SANDBOX,*map(str,argv)],cwd=cwd,log=metadata/(name+'.json'),timeout=15,max_log_bytes=128*1024,
        max_workdir_bytes=1024*1024,max_group_rss_bytes=512*1024**2,env=env)
    processes.append(result);assert result['exit_code']==0 and result['cleanup_complete'] and not result['log_truncated'],result
    return f.read_json(metadata/(name+'.json'))
coordinator_python=(ROOT/'.venv/bin/python').resolve(strict=True)
coordinator=query('coordinator',[coordinator_python,'-B',outer,'--coordinator-metadata'],ROOT)
plan.update(coordinator_tools=coordinator['coordinator_tools'],coordinator_python=coordinator['coordinator_python'])
for name in ('016','017'):
    arm=plan['arms'][name];runtime=Path(arm['runtime']);target=runtime/'.runs'/plan['installed_child_name']
    with target.open('xb') as stream:stream.write(raw)
    arm['python_context']=query('python'+name,[runtime/'.venv/bin/python','-B',target,'--python-metadata'],runtime)
    arm['runtime_manifest_sha256']=p.sha(runtime/'runtime-distribution.json')
    arm['runtime_tools']=query('tools'+name,[runtime/'.venv/bin/python','-B','-c',
        'import json;from autorouter import pipeline as p;print(json.dumps(p.tool_manifest()))'],runtime)
    assert arm['python_context']['sha256']==plan['coordinator_python']['sha256']
    assert arm['python_context']['version']==plan['coordinator_python']['version']
assert plan['reviewed_implementation_changes']==['autorouter/pipeline.py']
plan['status']='frozen';plan['blockers']=[]
plan['full_integration_qualification']=dict(path=str(ROOT/'.runs/full-integration-153/execution.json'),sha256=p.sha(ROOT/'.runs/full-integration-153/execution.json'),source_head=full['git_head'])
plan['prerequisite_sha256'].update({str(ROOT/'.runs/full-integration-153/execution.json'):p.sha(ROOT/'.runs/full-integration-153/execution.json'),
    str(base/'receipt-controls-002-time.log'):p.sha(base/'receipt-controls-002-time.log')})
plan['metadata_processes']=processes
plan['preparation_costs']=dict(wall_seconds=time.monotonic()-start,full_cpu_seconds=cpu()-cpu0,
    Native_executed=False,JVM_executed=False,scope='Actual same-Python/source/tool metadata and exclusive child-script copying only; build/authoring/review/tests and actual later arm costs remain separate.')
plan['reproduction_coordinator_python']=str(coordinator_python)
target=base/'PROTOCOL.frozen-001.json'
with target.open('x') as stream:json.dump(plan,stream,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps(dict(frozen=True,path=str(target),sha256=p.sha(target),coordinator_python=str(coordinator_python),wall_seconds=time.monotonic()-start,full_cpu_seconds=cpu()-cpu0)))
