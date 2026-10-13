"""Isolate failed-trial feedback lineage using real owned files and synthetic native predicates.
Incumbent check_result, final_freshness and final candidate native stage are mocked.
No native process or whole accepted receipt is claimed.
"""
from pathlib import Path
import importlib.util,json,sys,tempfile,copy,hashlib
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx,strategy as s
spec=importlib.util.spec_from_file_location('autorouter._feedback_probe',HERE/'placement_strategy-before.py');ps=importlib.util.module_from_spec(spec);spec.loader.exec_module(ps)
original=sx.parse('(kicad_pcb (zone (net "GND")) (segment (start 0 0) (end 1 0) (width 0.5) (layer "F.Cu") (net "GND") (uuid "owned-A")) (segment (start 1 0) (end 2 0) (width 0.5) (layer "F.Cu") (net "GND") (uuid "owned-B")))')
native={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':[]};metrics={'track_length_mm':2.,'vias':0}
results=[]
for variant in ('incomplete_quality_feedback','incomplete_failed_feedback','incomplete_without_feedback'):
 with tempfile.TemporaryDirectory(dir=HERE) as tmp:
  out=Path(tmp);basis=out/'incumbent';basis.mkdir();best=basis/'candidate/fixture.kicad_pcb';best.parent.mkdir();sx.write(best,original)
  folder=out/'trials/0000';folder.mkdir(parents=True);failed=folder/'candidate/fixture.kicad_pcb';failed.parent.mkdir()
  proposal=next(x for x in s.proposals(original,{'"GND"'},[],False) if x['route_ids']==[s.route_id(p.routes(original)[0])])
  sx.write(failed,ps.deletion(best,proposal,{'"GND"'}))
  trigger=dict(native,warnings=1,findings=[{'type':'track_dangling','severity':'warning','items':[{'uuid':'owned-B'}]}])
  row={'index':0,'parent':str(best),'parent_sha256':p.sha(best),'proposal':proposal,'accepted':False,'completed':False,'assigned_seconds':12.,'wall_seconds':0.,'total_cpu_seconds':0.,'steps':[], 'candidate':str(failed),'status':'failed' if variant=='incomplete_failed_feedback' else 'quality_rejected','native':trigger}
  p.save_json(folder/'trial.json',row);rows=[row]
  if variant!='incomplete_without_feedback':
   decision=s.feedback_proposal(sx.read(failed),proposal,trigger,native,{'"GND"'},[])
   assert decision['proposed']
   folder1=out/'trials/0001';folder1.mkdir()
   row1=dict(row,index=1,proposal=dict(decision['proposal'],parent_trial=0),candidate=str(folder1/'candidate/fixture.kicad_pcb'),status='failed',native=native)
   p.save_json(folder1/'trial.json',row1);rows.append(row1)
  candidate=out/'candidate/fixture.kicad_pcb';candidate.parent.mkdir();sx.write(candidate,original)
  incstep={'name':'incumbent-stage','cwd':str(basis),'cpu_seconds':1.,'monitor_cpu_seconds':0.,'wall_seconds':1.,'cleanup_complete':True,'status':'success'}
  finalstep=dict(incstep,name='final-drc',cwd=str(out))
  inc={'schema':4,'input_policy':'placement-search-v1','engine_profile':'tuned','scoring_variant':'via_default','source':'owned-source','source_hashes':{},'tools':{},'budget_seconds':30.,'candidate':str(best),'native':native,'metrics':metrics,'steps':[incstep],'source_drc':{},'task_sha256':'owned-task'}
  p.save_json(basis/'result.json',inc);p.save_json(out/'pruning-contract.json',ps.contract())
  data={'schema':5,'input_policy':ps.POLICY,'strategy':ps.STRATEGY,'baseline':'C-prototype','adapter':'both','engine_profile':'tuned','scoring_variant':'via_default','scope':'whole_board_unlocked_routing','proposal_policy':'feedback','pruning_contract':{'file':'pruning-contract.json','sha256':p.sha(out/'pruning-contract.json')},'source':'owned-source','source_hashes':{},'tools':{},'incumbent_receipt_sha256':p.sha(basis/'result.json'),'incumbent_assigned_seconds':30.,'budget_seconds':60.,'trials':rows,'selected_parent':str(best),'selected_parent_sha256':p.sha(best),'improvements':0,'source_drc':{},'task_sha256':'owned-task','steps':[incstep,finalstep]}
  with patch.object(p,'netclass_policy',return_value=None),patch.object(p,'check_result',return_value=True),patch.object(ps,'final_freshness'),patch.object(ps,'check_candidate_stage',return_value=(candidate,native,metrics)):
   try:ps.check_pruning_result(out,data,original,candidate,[])
   except Exception as exc:accepted=False;error=type(exc).__name__+': '+str(exc)
   else:accepted=True;error=None
  results.append({'variant':variant,'lineage_checker_passes':accepted,'error':error,'trigger_completed':row['completed'],'trigger_native_steps':len(row['steps']),'feedback_trial_present':len(rows)==2})
(HERE/'feedback-parent-001.json').write_text(json.dumps({'scope':__doc__,'snapshot_sha256':p.sha(HERE/'placement_strategy-before.py'),'results':results},indent=2)+'\n')
print(json.dumps(results))
