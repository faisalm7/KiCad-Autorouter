"""Actual offline CLI preset workflow on an unchanged complete licensed LED project."""
import time,resource
START=time.monotonic();u=resource.getrusage(resource.RUSAGE_SELF);ch=resource.getrusage(resource.RUSAGE_CHILDREN);CPU0=u.ru_utime+u.ru_stime+ch.ru_utime+ch.ru_stime
from pathlib import Path
import json,sys,os
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
from scripts import experiment_quality as q
out=ROOT/'.runs/native-pruning-preferences-cli-001';out.mkdir();board=q.selected_source('push-button-led')[0]
source=p.tree_hash(board.parent);tools=p.tool_manifest();preset=out/'settings.json';commands=[]
env={k:v for k,v in os.environ.items()if k not in {'PYTHONPATH','PYTHONHOME'}};env['PYTHONPATH']=str(ROOT);env['PYTHONDONTWRITEBYTECODE']='1'
for name,args in [('settings-init',['settings-init','--purpose','improve','--output',str(preset)]),
 ('improve',['improve',str(board),'--settings',str(preset),'--seconds','60','--scoring-preference','via_high','--proposal-policy','feedback','--output',str(out/'candidate-run')]),
 ('check-result',['check-result',str(out/'candidate-run/result.json')])]:
 process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B','-m','autorouter',*args],cwd=out,env=env,log=out/(name+'.log'),timeout=120,max_log_bytes=128*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
 commands.append(dict(name=name,process=process,log_sha256=p.sha(out/(name+'.log'))));p.save_json(out/'progress.json',commands)
 if process['status']!='success' or process['exit_code']!=0 or not process['cleanup_complete']:break
assert p.tree_hash(board.parent)==source and p.tool_manifest()==tools
u=resource.getrusage(resource.RUSAGE_SELF);ch=resource.getrusage(resource.RUSAGE_CHILDREN)
record=dict(schema=1,passed=len(commands)==3 and all(x['process']['status']=='success' and x['process']['exit_code']==0 for x in commands),commands=commands,source=str(board),source_hashes=source,tools=tools,controller_sha256=p.sha(Path(__file__)),wall_seconds=time.monotonic()-START,full_cpu_seconds=u.ru_utime+u.ru_stime+ch.ru_utime+ch.ru_stime-CPU0,scope='New actual CLI/preset/scoring qualification, not a repeated routing comparison. Complete licensed original LED unchanged; fresh ownHigh incumbent and finalNative/fullSCH/originalrules. Offline/networkdenied; all costs retained, no geometric superiority claim.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k]for k in ('passed','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
