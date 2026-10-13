"""Finite installed CLI review/intent/export/check workflow, shared runner only."""
from pathlib import Path
import json,os,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,handoff as h,review_export as e
from autorouter.runner import run
installation=ROOT/'.runs/installation-016';report=f.read_json(installation/'result.json');assert report['passed'] and report['status']=='passed'
clone=installation/'checkout';python=clone/'.venv/bin/python';receipt=clone/'.runs/install-nus-route-016/result.json'
out=ROOT/'.runs/installation-016-review-export';out.mkdir();owner={};h.capture_destination(owner,out)
# Reuse the installer's exact tracked-byte inventory; ignored native/venv state
# is preserved separately rather than treated as tracked source.
expected=f.read_json(installation/'source-tracked.json')
def tracked():
 for rel,digest in expected.items():
  if p.sha(clone/rel)!=digest or p.sha(ROOT/rel)!=digest:raise p.Rejected('installed or source tracked bytes changed')
tracked();start=time.monotonic();cpu0=time.process_time()+f.child_cpu();limit=180
record={'schema':1,'kind':'installed-review-export-cli-v1','status':'failed','accepted':False,'controls_passed':False,'commands':[],'budget_seconds':limit,'cpu_budget_seconds':limit,'installation_head':report['git_head'],'controller_sha256':p.sha(Path(__file__)),'human_pcb_approval_observed':False,'new_solver_execution':True,'scope':'Actual freshvenv installed CLI reviewcopy+fourplots+typedacceptintent+freshnativeexport+proofcheck+rejection. One fresh installed NUS route qualifies complete-schematic packaging; installation/workflow cost only, no new comparative experiment, no physical/GUI/freshMac qualification.'}
remaining=lambda:max(0,min(limit-(time.monotonic()-start),limit-(time.process_time()+f.child_cpu()-cpu0)))
review=clone/'.runs/install-review-export-016';intent=clone/'.runs/install-intent-016';export=clone/'.runs/install-export-016';rejection=clone/'.runs/install-reject-016'
commands=[('route',['route',str(ROOT/'.runs/nus-original-native-001/original/src/usb_led.kicad_pcb'),'--adapter','both','--seconds','120','--output',str(receipt.parent)]),('check-route',['check-result',str(receipt)]),('review-copy',['review-copy',str(receipt),'--render','--output',str(review)]),('accept-intent',['review-choice',str(review/'review.json'),'--choice','accept','--output',str(intent)]),('export',['review-export',str(intent/'choice.json'),'--seconds','120','--output',str(export)]),('check',['review-export-check',str(export/'export.json')]),('reject-intent',['review-choice',str(review/'review.json'),'--choice','reject','--output',str(rejection)])]
env=os.environ.copy()
for key in ('PYTHONHOME','PYTHONPATH','GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'):env.pop(key,None)
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
try:
 for name,args in commands:
  tracked();h.owned_destination(owner)
  process=run([*f.SANDBOX,str(python),'-B','-m','autorouter',*args],cwd=clone,log=out/(name+'.log'),timeout=min(125,remaining()),env=env,max_log_bytes=256*1024,max_workdir_bytes=512*1024**2,max_group_rss_bytes=2*1024**3)
  record['commands'].append({'name':name,'process':process,'log_sha256':p.sha(out/(name+'.log'))})
  if process['status']!='success' or process['exit_code']!=0 or process['cleanup_complete'] is not True:raise p.Rejected('installed '+name+' failed: '+process['status'])
  if remaining()<=0:raise p.Rejected('installed workflow cumulative budget exhausted')
 proof=f.read_json(export/'export.json');review_data=f.read_json(review/'review.json');choice=f.read_json(rejection/'choice.json')
 assert proof['export_accepted'] and proof['native']['opens']==0 and proof['native']['blocking']==0 and proof['native']['warnings']==10 and proof['schematic_parity']=='checked by final native DRC' and not proof['whole_project_drc_clean'] and choice['choice']=='reject' and not choice['routing_accepted']
 tracked();record.update(status='completed',controls_passed=True,candidate_sha256=proof['candidate_sha256'],native_report_sha256=proof['native_report_sha256'],native=proof['native'],metrics=proof['metrics'],export_proof_sha256=p.sha(export/'export.json'),export_path=str(export/'export.json'),plots=review_data['preview']['files'],source_and_installed_tracked_unchanged=True)
except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,reason=type(exc).__name__+': '+str(exc))
record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu0);record['within_budget']=max(record['wall_seconds'],record['total_cpu_seconds'])<=limit
if not record['within_budget']:record.update(status='budget_exceeded',controls_passed=False)
h.owned_destination(owner);p.save_json(out/'result.json',record);tracked();h.owned_destination(owner)
if remaining()<=0:record.update(status='budget_exceeded',controls_passed=False);p.save_json(out/'result.json',record)
print(f.canonical({k:record[k] for k in ('status','controls_passed','wall_seconds','total_cpu_seconds')}));raise SystemExit(0 if record['controls_passed'] else 2)
