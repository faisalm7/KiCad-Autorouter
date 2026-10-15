"""One bounded assigned pure alias-policy/fixture batch; no Native/JVM/Git."""
import time,resource
START=time.monotonic()
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import os,sys,json
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'.runs/literal-composite-targeted-001';HERE.mkdir()
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
out=HERE/'output';out.mkdir()
names=['test_literal_composite','test_netclass','test_netclass_unused','test_netclass_parent_policy','test_netclass_pipeline','test_netclass_parent_pipeline']
files=[str(x.relative_to(ROOT)) for x in (ROOT/'autorouter').glob('*.py')]+['tests/'+n+'.py' for n in names]+['tests/normal_prl_fixture.py','tests/test_fixed_placement_session.py','scripts/backup.py']
pins={name:p.sha(ROOT/name) for name in files}
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}};env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
code='''import sys,unittest,json,subprocess
sys.path[:0]=PATHS
def denied(*a,**k):raise AssertionError('Assigned pure batch forbids Native/JVM/Git/subprocess execution')
subprocess.run=denied;subprocess.Popen=denied
suite=unittest.defaultTestLoader.loadTestsFromNames(NAMES)
result=unittest.TextTestRunner(verbosity=2).run(suite)
with open('summary.json','w') as stream:json.dump(dict(methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped)),stream)
raise SystemExit(not result.wasSuccessful())
'''.replace('PATHS',repr([str(ROOT),str(ROOT/'tests')])).replace('NAMES',repr(names))
process=run([str(ROOT/'.venv/bin/python'),'-B','-c',code],cwd=out,env=env,log=out/'tests.log',timeout=30,
    max_log_bytes=256*1024,max_workdir_bytes=16*1024**2,max_group_rss_bytes=1024**3)
after={name:p.sha(ROOT/name) for name in files};current=after==pins
record=dict(schema=1,process=process,source_sha256=pins,source_after_sha256=after,source_current=current,modules=names,
    controller_sha256=p.sha(__file__),log_sha256=p.sha(out/'tests.log'),summary=json.loads((out/'summary.json').read_text()) if (out/'summary.json').exists() else None,
    wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,
    scope='Authored synthetic reader/fixture consistency controls only; subprocess spawning denied inside test child. No Native/JVM/Git/network or routing validation claim.')
p.save_json(out/'execution.json',record)
print(json.dumps({k:record[k] for k in ('source_current','summary','wall_seconds','full_cpu_seconds')}))
print(json.dumps({k:process[k] for k in ('status','exit_code','cleanup_complete')}))
raise SystemExit(0 if current and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete']is True else 2)
