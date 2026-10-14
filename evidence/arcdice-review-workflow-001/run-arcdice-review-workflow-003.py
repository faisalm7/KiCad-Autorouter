from pathlib import Path
import json,sys,time,os
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,review_export as e
from autorouter.runner import run
out=ROOT/'.runs/arcdice-review-workflow-003';out.mkdir()
receipt=ROOT/'.runs/arcdice-native-paired-complete-sch-003/run/C_feedback/result.json';data=f.read_json(receipt)
inputs={str(x):e.witness(x) for x in (receipt.parent,Path(data['source']).parent)}
tools=p.tool_manifest();start=time.monotonic();cpu=time.process_time()+f.child_cpu();steps=[]
commands=[['review-choice',str(ROOT/'.runs/arcdice-review-workflow-002/review/review.json'),'--choice','accept','--output',str(out/'intent')],['review-export',str(out/'intent/choice.json'),'--seconds','120','--output',str(out/'export')],['review-export-check',str(out/'export/export.json')],['review-choice',str(ROOT/'.runs/arcdice-review-workflow-002/review/review.json'),'--choice','reject','--output',str(out/'rejection')]]
for i,args in enumerate(commands):
 remaining=min(180-(time.monotonic()-start),180-(time.process_time()+f.child_cpu()-cpu))
 assert remaining>0
 result=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B','-m','autorouter',*args],cwd=out,log=out/('command-'+str(i)+'.log'),env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1'),timeout=min(120,remaining),max_log_bytes=384*1024,max_workdir_bytes=48*1024**2,max_group_rss_bytes=2*1024**3)
 # Same shared resource guards on the isolated output tree; original full input evidence remains unchanged.
 steps.append({'argv':args,'process':result});p.save_json(out/('process-'+str(i)+'.json'),steps[-1])
 assert result['status']=='success' and result['exit_code']==0 and result['cleanup_complete'],result
 assert p.tool_manifest()==tools and all(e.witness(Path(x))==w for x,w in inputs.items())
export=f.read_json(out/'export/export.json');native=export['native']
assert [native[k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,26,0]
assert f.read_json(out/'rejection/choice.json')['choice']=='reject'
record={'schema':1,'status':'completed','controls_passed':True,'new_routing_executed':False,'steps':steps,'tools':tools,'original_routing_receipt_sha256':p.sha(receipt),'source_and_routing_preserved':True,'inputs':inputs,'export_sha256':p.sha(out/'export/export.json'),'candidate_sha256':export['candidate_sha256'],'native':native,'metrics':export['metrics'],'wall_seconds':time.monotonic()-start,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,'controller_sha256':p.sha(Path(__file__)),'scope':'Actual four continuation CLI commands; readyreview/nativeplots from002 retained and never rerun for newlyqualified parent/pruning board: native before/after plots, acceptintent, fresh native separate project export/check and rejectintent. No solverrerun/liveoverwrite/PCBapproval/GUI/human/physical claim. Additionalworkflow qualification cost separatefromfrozenroutingcomparisons. Corrected sourceenvironment retains requiredMac variables; outputtree48MiB polling guard active. 001emptyenvironmentrender failure and002stdout logoverflow preserved; existingreadyreview/nativeplots reused; no completed Native/workflow/engine rerun.'}
assert max(record['wall_seconds'],record['full_cpu_seconds'])<180
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('status','wall_seconds','full_cpu_seconds','candidate_sha256','metrics')}))
