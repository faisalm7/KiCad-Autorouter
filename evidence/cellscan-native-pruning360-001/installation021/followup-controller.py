"""Current installed source controls, shared bounded runner, sequential native lane."""
import time,resource
START=time.monotonic();u=resource.getrusage(resource.RUSAGE_SELF);c=resource.getrusage(resource.RUSAGE_CHILDREN);CPU0=u.ru_utime+u.ru_stime+c.ru_utime+c.ru_stime
from pathlib import Path
import os,sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=ROOT/'.runs/installation021-followup-001';out.mkdir();installed=ROOT/'.runs/installation-021-current965/checkout'
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
commands=[('targeted-tests',[str(installed/'.venv/bin/python'),'-B','-m','unittest','tests.test_native_edge','tests.test_native_edge_record','tests.test_portfolio_allocation','tests.test_portfolio_completed_resume','-q']),
    ('native-edge-controls',[str(installed/'.venv/bin/python'),'-B',str(installed/'scripts/native_edge_controls.py'),'--valid',str(installed/'.runs/install-native-smoke/candidate/smoke.kicad_pcb'),'--output',str(installed/'.runs/installed-edge-controls-001')])]
results=[]
for name,argv in commands:
    process=run([*f.SANDBOX,*argv],cwd=installed,log=out/(name+'.log'),timeout=60,env=env,max_log_bytes=128*1024,max_workdir_bytes=512*1024**2,max_group_rss_bytes=4*1024**3)
    results.append(dict(name=name,process=process,log_sha256=p.sha(out/(name+'.log'))))
    p.save_json(out/'progress.json',results)
    if process['status']!='success' or process['exit_code']!=0 or not process['cleanup_complete']:break
u=resource.getrusage(resource.RUSAGE_SELF);c=resource.getrusage(resource.RUSAGE_CHILDREN)
record=dict(schema=1,passed=len(results)==2 and all(x['process']['status']=='success' and x['process']['exit_code']==0 and x['process']['cleanup_complete'] for x in results),results=results,
    wall_seconds=time.monotonic()-START,full_cpu_seconds=u.ru_utime+u.ru_stime+c.ru_utime+c.ru_stime-CPU0,controller_sha256=p.sha(Path(__file__)),installed_head='965796670d2835e185938d52ef694333e5752356',
    scope='Current actual installed venv/modules under network denial. Software edge/portfolio controls plus owned original-rule native positive/edge-negative/rule-tamper controls. No comparative routing, complete schematic, fresh OS or physical claim.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k]for k in ('passed','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
