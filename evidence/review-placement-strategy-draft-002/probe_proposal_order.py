"""Isolate deterministic proposal replay with real failed trial files; native predicates are mocked.
No native process or whole accepted receipt is claimed. This checks provenance,
not whether any altered schedule produces an invalid final board.
"""
from pathlib import Path
import importlib.util,json,sys,tempfile,copy
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx,strategy as s
spec=importlib.util.spec_from_file_location('autorouter._order_probe',HERE/'placement_strategy-after.py');ps=importlib.util.module_from_spec(spec);spec.loader.exec_module(ps)
original=sx.parse('(kicad_pcb (zone (net "GND")) (segment (start 0 0) (end 1 0) (width 0.5) (layer "F.Cu") (net "GND") (uuid "owned-A")) (segment (start 1 0) (end 3 0) (width 0.5) (layer "F.Cu") (net "GND") (uuid "owned-B")))')
native={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':[]};metrics={'track_length_mm':3.,'vias':0}
grouped=s.proposals(original,{'"GND"'},[],True);individual=s.proposals(original,{'"GND"'},[],False)
results=[]
for variant,schedule in (('whole_then_longest',grouped+[individual[0]]),('individual_before_whole',[individual[0]]+grouped),('duplicate_base_attempt',[individual[0],individual[0]])):
 with tempfile.TemporaryDirectory(dir=HERE) as tmp:
  out=Path(tmp);basis=out/'incumbent';basis.mkdir();best=basis/'candidate/fixture.kicad_pcb';best.parent.mkdir();sx.write(best,original)
  rows=[]
  for i,proposal in enumerate(schedule):
   folder=out/'trials'/f'{i:04d}';folder.mkdir(parents=True)
   row={'index':i,'parent':str(best),'parent_sha256':p.sha(best),'proposal':proposal,'accepted':False,'completed':False,'assigned_seconds':12.,'wall_seconds':0.,'total_cpu_seconds':0.,'steps':[], 'candidate':str(folder/'candidate/fixture.kicad_pcb'),'status':'failed','error':'owned synthetic interruption before native'}
   p.save_json(folder/'trial.json',row);rows.append(row)
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
  results.append({'variant':variant,'lineage_checker_passes':accepted,'error':error,'proposal_kinds':[r['proposal']['kind'] for r in rows],'route_ids':[r['proposal']['route_ids'] for r in rows]})
(HERE/'proposal-order-001.json').write_text(json.dumps({'scope':__doc__,'snapshot_sha256':p.sha(HERE/'placement_strategy-after.py'),'results':results},indent=2)+'\n')
print(json.dumps(results))
