"""Finite selected CLI review/intent/export/check workflow, shared runner only."""
from pathlib import Path
import json,os,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,handoff as h,review_export as e
from autorouter.runner import run
clone=ROOT;python=ROOT/'.venv/bin/python';receipt=ROOT/'.runs/nus-native-paired-002/run/C_feedback/result.json'
p.check_result(receipt);route=f.read_json(receipt);tools=p.tool_manifest()
inputs={str(receipt.parent):e.witness(receipt.parent),str(Path(route['source']).parent):e.witness(Path(route['source']).parent)}
out=ROOT/'.runs/nus-complete-schematic-workflow-002';out.mkdir();owner={};h.capture_destination(owner,out)
def tracked():
 if p.tool_manifest()!=tools:raise p.Rejected('workflow tool/code/HEAD changed')
 for path,expected in inputs.items():
  if e.witness(Path(path))!=expected:raise p.Rejected('original source/routing evidence changed')
tracked();start=time.monotonic();cpu0=time.process_time()+f.child_cpu();limit=180
record={'schema':1,'kind':'complete-schematic-review-export-cli-v1','status':'failed','accepted':False,'controls_passed':False,'commands':[],'budget_seconds':limit,'cpu_budget_seconds':limit,'git_head':tools['git_head'],'controller_sha256':p.sha(Path(__file__)),'human_pcb_approval_observed':False,'new_solver_execution':False,'input_receipt_sha256':p.sha(receipt),'original_inputs':inputs,'scope':'Actual local CLI reviewcopy+fourplots+typedacceptintent+freshnativeexport+proofcheck+rejection. Existing selected positive reused. Additional workflow cost; no routing repeat, physical/GUI/human qualification.'}
remaining=lambda:max(0,min(limit-(time.monotonic()-start),limit-(time.process_time()+f.child_cpu()-cpu0)))
review=clone/'.runs/nus-complete-schematic-workflow-review-002';intent=clone/'.runs/nus-complete-schematic-workflow-intent-002';export=clone/'.runs/nus-complete-schematic-workflow-export-002';rejection=clone/'.runs/nus-complete-schematic-workflow-reject-002'
commands=[('review-copy',['review-copy',str(receipt),'--render','--output',str(review)]),('accept-intent',['review-choice',str(review/'review.json'),'--choice','accept','--output',str(intent)]),('export',['review-export',str(intent/'choice.json'),'--seconds','120','--output',str(export)]),('check',['review-export-check',str(export/'export.json')]),('reject-intent',['review-choice',str(review/'review.json'),'--choice','reject','--output',str(rejection)])]
env=os.environ.copy()
for key in ('PYTHONHOME','PYTHONPATH','GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'):env.pop(key,None)
env.update(PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
try:
 for name,args in commands:
  tracked();h.owned_destination(owner)
  process=run([*f.SANDBOX,str(python),'-B','-m','autorouter',*args],cwd=out,log=out/(name+'.log'),timeout=min(125,remaining()),env=env,max_log_bytes=256*1024,max_workdir_bytes=512*1024**2,max_group_rss_bytes=2*1024**3)
  p.save_json(out/(name+'-process.json'),process)
  record['commands'].append({'name':name,'process':process,'log_sha256':p.sha(out/(name+'.log')) if (out/(name+'.log')).exists() else None})
  if process['status']!='success' or process['exit_code']!=0 or process['cleanup_complete'] is not True:raise p.Rejected('complete-schematic '+name+' failed: '+process['status'])
  if remaining()<=0:raise p.Rejected('complete-schematic workflow cumulative budget exhausted')
 proof=f.read_json(export/'export.json');review_data=f.read_json(review/'review.json');choice=f.read_json(rejection/'choice.json')
 assert proof['export_accepted'] and proof['native']['opens']==0 and proof['native']['blocking']==0 and proof['native']['warnings']==10 and proof['schematic_parity']=='checked by final native DRC' and not proof['whole_project_drc_clean'] and choice['choice']=='reject' and not choice['routing_accepted']
 tracked();record.update(status='completed',controls_passed=True,candidate_sha256=proof['candidate_sha256'],native_report_sha256=proof['native_report_sha256'],native=proof['native'],metrics=proof['metrics'],export_proof_sha256=p.sha(export/'export.json'),export_path=str(export/'export.json'),plots=review_data['preview']['files'],source_and_routing_unchanged=True)
except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,reason=type(exc).__name__+': '+str(exc))
record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu0);record['within_budget']=max(record['wall_seconds'],record['total_cpu_seconds'])<=limit
if not record['within_budget']:record.update(status='budget_exceeded',controls_passed=False)
h.owned_destination(owner);p.save_json(out/'result.json',record);tracked();h.owned_destination(owner)
if remaining()<=0:record.update(status='budget_exceeded',controls_passed=False);p.save_json(out/'result.json',record)
print(f.canonical({k:record[k] for k in ('status','controls_passed','wall_seconds','total_cpu_seconds')}));raise SystemExit(0 if record['controls_passed'] else 2)
