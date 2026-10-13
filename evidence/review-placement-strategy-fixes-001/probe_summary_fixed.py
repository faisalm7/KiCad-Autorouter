"""Real policy-aware summary control; synthetic receipts and mocked native consistency checker.
No native validation or fully accepted routing receipt is claimed.
"""
from pathlib import Path
import json,sys,tempfile,copy
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_strategy as ps
from scripts import experiment_quality as q
arm={'id':'C_feedback','adapter':'both','engine_profile':'tuned','operation':'placement_prune','proposal_policy':'feedback','input_policy':ps.POLICY,'strategy':ps.STRATEGY};results=[]
for variant in ('correct_contract','wrong_strategy','wrong_incumbent_hash','old_operation'):
 with tempfile.TemporaryDirectory(dir=HERE) as tmp:
  out=Path(tmp);basis=out/'incumbent';basis.mkdir();p.save_json(basis/'result.json',{'schema':4,'input_policy':'placement-search-v1','adapter':'both','engine_profile':'tuned','scoring_variant':'via_default','scope':'whole_board_unlocked_routing','accepted':True})
  p.save_json(out/'pruning-contract.json',ps.contract())
  result={'schema':5,'input_policy':ps.POLICY,'strategy':ps.STRATEGY,'baseline':'C-prototype','adapter':'both','engine_profile':'tuned','scoring_variant':'via_default','scope':'whole_board_unlocked_routing','proposal_policy':'feedback','accepted':True,'status':'routing_accepted','incumbent_receipt_sha256':p.sha(basis/'result.json'),'incumbent_assigned_seconds':45.,'pruning_contract':{'file':'pruning-contract.json','sha256':p.sha(out/'pruning-contract.json')},'native':{'opens':0,'blocking':0,'warnings':96,'exclusions':0},'metrics':{'track_length_mm':100.,'vias':0},'wall_seconds':30.,'total_cpu_seconds':30.}
  selected=copy.deepcopy(arm)
  if variant=='wrong_strategy':result['strategy']='wrong'
  if variant=='wrong_incumbent_hash':result['incumbent_receipt_sha256']='0'*64
  if variant=='old_operation':selected['operation']='prune'
  p.save_json(out/'result.json',result)
  with patch.object(p,'check_result',return_value={'synthetic':True}):row=q.summarize(selected,out,result,31.,31.)
  results.append({'variant':variant,**{key:row[key] for key in ('accepted_in_receipt','receipt_verified','within_equal_budgets','protocol_contract_verified','accepted')}})
(HERE/'summary-fixed-001.json').write_text(json.dumps({'scope':__doc__,'current_source_sha256':p.sha(ROOT/'scripts/experiment_quality.py'),'results':results},indent=2)+'\n');print(json.dumps(results))
