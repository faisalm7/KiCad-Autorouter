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
 def test_fixed_ardujoy_snapshot_requires_complete_exact_notice_tree(self):
  from experiments.licensed_acquisition_v4 import native_snapshot
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'.cache') as tmp:
   root=Path(tmp);base=root/'.runs/ardujoy-original-native-001/original/Ardujoy_HW';base.mkdir(parents=True)
   files={'Ardujoy_HW/Ardujoy_HW.kicad_pcb':b'board','Ardujoy_HW/Ardujoy_HW.kicad_pro':b'rules','Ardujoy_HW/_licenses/LICENSE.creator':b'notice','README.md':b'outer notice'}
   for name,raw in files.items():
    if name.startswith('Ardujoy_HW/'):
     path=base/name.removeprefix('Ardujoy_HW/');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
   with patch.object(e.c,'ROOT',root),patch.object(native_snapshot,'capture',return_value=files):
    board,family=e.selected_source('ardujoy-c64');self.assertEqual(board,base/'Ardujoy_HW.kicad_pcb');self.assertIn('development-exposed',family)
    (base/'_licenses/LICENSE.creator').write_bytes(b'changed notice')
    with self.assertRaisesRegex(e.p.Rejected,'exact original'):e.selected_source('ardujoy-c64')
    (base/'_licenses/LICENSE.creator').write_bytes(files['Ardujoy_HW/_licenses/LICENSE.creator']);(base/'extra.kicad_pro').write_bytes(b'extra')
    with self.assertRaisesRegex(e.p.Rejected,'exact original'):e.selected_source('ardujoy-c64')
 def test_wrong_or_missing_policy_refuses_otherwise_valid_receipt(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/".cache") as tmp:
   out=Path(tmp);(out/'incumbent').mkdir()
   incumbent={'adapter':'both','engine_profile':'tuned','scope':'whole_board_unlocked_routing','accepted':True}
   (out/'incumbent/result.json').write_text(json.dumps(incumbent))
   result=dict(incumbent,status='routing_accepted',wall_seconds=1,total_cpu_seconds=1,incumbent_baseline='B2_tuned',incumbent={'receipt':str(out/'incumbent/result.json')})
   arm=e.FEEDBACK_ARMS[-1]
   for policy,expected in [(None,False),('single',False),('feedback',True)]:
    with self.subTest(policy=policy),patch.object(e.p,'check_result',return_value={'current':True}):
     result['proposal_policy']=policy
     (out/'result.json').write_text(json.dumps(result))
     row=e.summarize(arm,out,result,1,1)
     self.assertEqual(row['accepted'],expected)
     self.assertEqual(row['protocol_contract_verified'],expected)
 def test_placement_pruning_summary_uses_explicit_new_contract(self):
  from autorouter import placement_strategy as ps
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'.cache') as tmp:
   out=Path(tmp);(out/'incumbent').mkdir();marker=out/'pruning-contract.json';e.p.save_json(marker,ps.contract())
   inc={'schema':4,'input_policy':'placement-search-v1','adapter':'both','engine_profile':'tuned','scoring_variant':'via_default','scope':'whole_board_unlocked_routing','accepted':True}
   e.p.save_json(out/'incumbent/result.json',inc)
   result={'schema':5,'input_policy':ps.POLICY,'strategy':ps.STRATEGY,'baseline':'C-prototype','adapter':'both','engine_profile':'tuned','scoring_variant':'via_default',
    'scope':'whole_board_unlocked_routing','proposal_policy':'feedback','accepted':True,'status':'routing_accepted','wall_seconds':1.,'total_cpu_seconds':1.,
    'incumbent_receipt_sha256':e.p.sha(out/'incumbent/result.json'),'pruning_contract':{'file':marker.name,'sha256':e.p.sha(marker)}}
   arm={'id':'C_feedback','adapter':'both','engine_profile':'tuned','operation':'placement_prune','input_policy':ps.POLICY,'strategy':ps.STRATEGY}
   e.p.save_json(out/'result.json',result)
   with patch.object(e.p,'check_result',return_value={'current':True}):
    row=e.summarize(arm,out,result,1.,1.);self.assertTrue(row['accepted'])
    changed=copy.deepcopy(result);changed['incumbent_receipt_sha256']='wrong';e.p.save_json(out/'result.json',changed)
    self.assertFalse(e.summarize(arm,out,changed,1.,1.)['accepted'])
 def test_returned_result_and_readback_must_bind_same_receipt(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'.cache') as tmp:
   out=Path(tmp);result={'adapter':'both','engine_profile':'standard','scope':'whole_board_unlocked_routing','accepted':True,'status':'routing_accepted','wall_seconds':1,'total_cpu_seconds':1}
   arm={'id':'B1','adapter':'both','engine_profile':'standard','operation':'route'}
   e.p.save_json(out/'result.json',dict(result,total_cpu_seconds=2))
   with patch.object(e.p,'check_result',return_value={'current':True}) as call:
    row=e.summarize(arm,out,result,1,1);self.assertFalse(row['accepted']);call.assert_not_called()
   e.p.save_json(out/'result.json',result)
   def late(_):e.p.save_json(out/'result.json',dict(result,total_cpu_seconds=2))
   with patch.object(e.p,'check_result',side_effect=late):self.assertFalse(e.summarize(arm,out,result,1,1)['accepted'])
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
