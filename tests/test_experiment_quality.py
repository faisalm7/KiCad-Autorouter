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
 def test_fixed_universal_shift_source_preserves_prl_orphan_and_all_notices(self):
  from scripts import fetch_led_demo as demo
  # Authored bytes exercise selection only; they are not Native evidence.
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'.cache') as tmp:
   base=Path(tmp);prefix='KiCad/Interface Board/'
   files={'LICENSE':b'creator license','README.md':b'creator readme',prefix+'.kicad_sch':b'orphan schematic',
    prefix+'USR_LED_Board.kicad_pcb':b'original board',prefix+'USR_LED_Board.kicad_pro':b'original rules',
    prefix+'USR_LED_Board.kicad_sch':b'flat schematic',prefix+'USR_LED_Board.kicad_prl':b'complete local settings',
    prefix+'_licenses/creator/LICENSE':b'creator license',prefix+'_licenses/creator/README.md':b'creator readme'}
   for name,raw in files.items():
    path=base/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
   before=e.p.tree_hash(base)
   with patch.object(demo,'capture_native_source',return_value=(base,files)) as capture:
    board,family=e.selected_source('universal-shift-interface')
    capture.assert_called_once_with('universal-shift-interface',root=e.c.ROOT)
    self.assertEqual(board,base/(prefix+'USR_LED_Board.kicad_pcb'));self.assertIn('development-exposed',family);self.assertIn('ancestry-unverified',family)
    self.assertEqual(e.p.tree_hash(base),before);self.assertEqual(e.PROJECTS['universal-shift-interface'],'universal-shift-interface')
    for name in (prefix+'USR_LED_Board.kicad_prl',prefix+'.kicad_sch','LICENSE',prefix+'_licenses/creator/README.md'):
     with self.subTest(changed=name):
      (base/name).write_bytes(b'changed')
      with self.assertRaisesRegex(e.p.Rejected,'exact fixed Universal Shift'):e.selected_source('universal-shift-interface')
      (base/name).write_bytes(files[name])
    extra=base/(prefix+'substitute.kicad_pcb');extra.write_bytes(b'candidate')
    with self.assertRaisesRegex(e.p.Rejected,'exact fixed Universal Shift'):e.selected_source('universal-shift-interface')
    extra.unlink();(base/(prefix+'.kicad_sch')).unlink()
    with self.assertRaisesRegex(e.p.Rejected,'exact fixed Universal Shift'):e.selected_source('universal-shift-interface')
 def test_universal_shift_selection_propagates_fixed_capture_refusal_without_fallback(self):
  from scripts import fetch_led_demo as demo
  with patch.object(demo,'capture_native_source',side_effect=e.p.Rejected('original acquisition proof stale')) as capture:
   with self.assertRaisesRegex(e.p.Rejected,'original acquisition proof stale'):e.selected_source('universal-shift-interface')
   capture.assert_called_once_with('universal-shift-interface',root=e.c.ROOT)
 def test_fixed_ir_source_requires_exact_original_notice_packet(self):
  from scripts import fetch_led_demo as demo
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'.cache') as tmp:
   base=Path(tmp);files={'KiCad/IR_Sensor.kicad_pcb':b'original','KiCad/IR_Sensor.kicad_pro':b'rules','KiCad/IR_Sensor.kicad_sch':b'schematic','KiCad/_licenses/creator/LICENSE':b'notice'}
   for name,raw in files.items():
    path=base/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
   with patch.object(demo,'capture_native_source',return_value=(base,files)):
    board,family=e.selected_source('ir-obstacle');self.assertEqual(board,base/'KiCad/IR_Sensor.kicad_pcb');self.assertIn('development-exposed',family)
    (base/'KiCad/_licenses/creator/LICENSE').write_bytes(b'changed')
    with self.assertRaisesRegex(e.p.Rejected,'exact fixed IR'):e.selected_source('ir-obstacle')
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
 def test_fixed_nus_snapshot_binds_original_notices_even_after_failed_diagnostic(self):
  from experiments.licensed_acquisition_v5 import native_snapshot
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'.cache') as tmp:
   root=Path(tmp);base=root/'.runs/nus-original-native-001/original/src';base.mkdir(parents=True)
   files={'src/usb_led.kicad_pcb':b'board','src/usb_led.kicad_pro':b'rules','src/_licenses/creator/LICENSE.md':b'notice','LICENSE.md':b'outer notice'}
   for name,raw in files.items():
    if name.startswith('src/'):
     path=base/name.removeprefix('src/');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
   with patch.object(e.c,'ROOT',root),patch.object(native_snapshot,'capture',return_value=files):
    board,family=e.selected_source('nus-usb-led');self.assertEqual(board,base/'usb_led.kicad_pcb');self.assertIn('development-exposed',family)
    (base/'_licenses/creator/LICENSE.md').write_bytes(b'changed notice')
    with self.assertRaisesRegex(e.p.Rejected,'exact original'):e.selected_source('nus-usb-led')
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
