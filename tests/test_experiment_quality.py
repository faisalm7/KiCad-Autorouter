"""Ensure a labelled ablation cannot accept a substituted strategy policy."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('experiment_quality',Path(__file__).resolve().parents[1]/'scripts/experiment_quality.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)

class ProtocolControls(unittest.TestCase):
 def test_wrong_or_missing_policy_refuses_otherwise_valid_receipt(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp);(out/'incumbent').mkdir()
   incumbent={'adapter':'both','engine_profile':'tuned','scope':'whole_board_unlocked_routing','accepted':True}
   (out/'incumbent/result.json').write_text(json.dumps(incumbent))
   result=dict(incumbent,status='routing_accepted',wall_seconds=1,total_cpu_seconds=1,incumbent_baseline='B2_tuned',incumbent={'receipt':str(out/'incumbent/result.json')})
   arm=e.FEEDBACK_ARMS[-1]
   for policy,expected in [(None,False),('single',False),('feedback',True)]:
    with self.subTest(policy=policy),patch.object(e.p,'check_result',return_value={'current':True}):
     result['proposal_policy']=policy
     row=e.summarize(arm,out,result,1,1)
     self.assertEqual(row['accepted'],expected)
     self.assertEqual(row['protocol_contract_verified'],expected)
 def test_no_comparison_uses_rejected_candidate_length(self):
  rows=[{'id':name,'accepted':False,'length_mm':0} for name in ('B1','B2','C_single','C_feedback')]
  result=e.comparisons(rows)
  self.assertEqual(len(result),5)
  self.assertTrue(all(not r['comparable_valid_candidates'] and 'length_delta_mm' not in r for r in result))
 def test_feedback_compares_directly_with_single(self):
  base={'accepted':True,'length_mm':100,'vias':2,'invocation_wall_seconds':110,'invocation_cpu_seconds':100}
  rows=[dict(base,id=name) for name in ('B1','B2','C_single','C_feedback')]
  rows[-1]['length_mm']=90
  contrast=next(r for r in e.comparisons(rows) if r['baseline']=='C_single')
  self.assertEqual(contrast['system'],'C_feedback')
  self.assertEqual(contrast['length_delta_mm'],-10)

if __name__=='__main__':unittest.main()
