"""Actual current separate-project workflow, original source immutable, no live apply."""
import time,resource
START=time.monotonic();u=resource.getrusage(resource.RUSAGE_SELF);ch=resource.getrusage(resource.RUSAGE_CHILDREN);CPU0=u.ru_utime+u.ru_stime+ch.ru_utime+ch.ru_stime
from pathlib import Path
import sys,os,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=ROOT/'.runs/pruning-preferences-workflow-001';out.mkdir();receipt=ROOT/'.runs/native-pruning-preferences-cli-002/candidate-run/result.json';data=f.read_json(receipt);source=p.tree_hash(Path(data['source']).parent);tools=p.tool_manifest();steps=[]
env={k:v for k,v in os.environ.items()if k not in {'PYTHONPATH','PYTHONHOME'}};env.update(PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1')
commands=[('review-copy',['review-copy',str(receipt),'--render','--output',str(out/'review')]),
 ('accept-intent',['review-choice',str(out/'review/review.json'),'--choice','accept','--output',str(out/'accept-intent')]),
 ('fresh-export',['review-export',str(out/'accept-intent/choice.json'),'--seconds','120','--output',str(out/'export')]),
 ('check-export',['review-export-check',str(out/'export/export.json')]),
 ('reject-intent',['review-choice',str(out/'review/review.json'),'--choice','reject','--output',str(out/'reject-intent')])]
for name,args in commands:
 process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B','-m','autorouter',*args],cwd=out,env=env,log=out/(name+'.log'),timeout=150,max_log_bytes=128*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
 steps.append(dict(name=name,process=process,log_sha256=p.sha(out/(name+'.log'))));p.save_json(out/'progress.json',steps)
 if process['status']!='success' or process['exit_code']!=0 or not process['cleanup_complete']:break
assert p.tree_hash(Path(data['source']).parent)==source and p.tool_manifest()==tools
u=resource.getrusage(resource.RUSAGE_SELF);ch=resource.getrusage(resource.RUSAGE_CHILDREN)
record=dict(schema=1,passed=len(steps)==5 and all(x['process']['status']=='success' and x['process']['exit_code']==0 and x['process']['cleanup_complete']for x in steps),steps=steps,source_hashes=source,tools=tools,receipt_sha256=p.sha(receipt),controller_sha256=p.sha(Path(__file__)),wall_seconds=time.monotonic()-START,full_cpu_seconds=u.ru_utime+u.ru_stime+ch.ru_utime+ch.ru_stime-CPU0,human_PCB_approval=False,live_editor_apply=False,
 scope='ActualCLI test intent andfreshNative separateproject export/currentpruning preference receipt, four2Cuplots. Allcosts retained; no reroutingcomparison/GUI/physicalapproval. Originalsource/candidate/rules remainunchanged.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k]for k in ('passed','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
