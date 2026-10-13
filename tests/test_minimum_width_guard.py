"""Original-rule neckdown policy controls; no native-routing qualification."""
from pathlib import Path
import json,tempfile,unittest
from autorouter import pipeline as p

class OriginalWidthGuard(unittest.TestCase):
 def test_current_guard_cannot_be_stripped_or_replace_numeric_minimum_with_bool(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp).resolve();board=root/'board.kicad_pcb';board.with_suffix('.kicad_pro').write_text(json.dumps({'board':{'design_settings':{'rules':{'min_track_width':1}}}}))
   self.assertIsNone(p.check_minimum_width_record({'adapter':'none'},root))
   data={'source':str(board),'adapter':'both','engine_budget':{'strict_class_targets':True},'minimum_width_guard':p.minimum_width_guard(board,'both')}
   self.assertIsNotNone(p.check_minimum_width_record(data,root))
   data['minimum_width_guard']['min_track_width_mm']=True
   with self.assertRaises(p.Rejected):p.check_minimum_width_record(data,root)
   del data['minimum_width_guard'];(root/'code').mkdir();(root/'code/pipeline.py').write_bytes((Path(p.__file__)).read_bytes())
   with self.assertRaisesRegex(p.Rejected,'requires original width guard'):p.check_minimum_width_record(data,root)
   (root/'code/pipeline.py').write_text('historical pipeline with no width guard function\n')
   self.assertIsNone(p.check_minimum_width_record(data,root))
 def test_positive_original_minimum_binds_unchanged_rules_and_stock_is_separate(self):
  with tempfile.TemporaryDirectory() as tmp:
   board=Path(tmp)/'board.kicad_pcb';project=board.with_suffix('.kicad_pro')
   project.write_text(json.dumps({'board':{'design_settings':{'rules':{'min_track_width':.65}}}}));raw=project.read_bytes()
   self.assertIsNone(p.minimum_width_guard(board,'none'))
   guard=p.minimum_width_guard(board,'both');self.assertEqual(guard['min_track_width_mm'],.65);self.assertEqual(guard['original_project_sha256'],p.sha(project))
   self.assertEqual(project.read_bytes(),raw)
   for profile in ('standard','tuned','completion-only'):
    settings=p.engine_profile_settings(profile,60,strict_class_targets=guard is not None)
    self.assertIn('--router.automatic_neckdown=false',settings['argv']);self.assertIn('--router.fanout.enabled=false',settings['argv'])
 def test_missing_zero_and_malformed_minimum_are_distinct(self):
  with tempfile.TemporaryDirectory() as tmp:
   board=Path(tmp)/'board.kicad_pcb';project=board.with_suffix('.kicad_pro');project.write_text('{}')
   self.assertIsNone(p.minimum_width_guard(board,'both'))
   for value in (0,-1,True,'0.65',float('nan')):
    project.write_text(json.dumps({'board':{'design_settings':{'rules':{'min_track_width':value}}}}))
    if value==0 and type(value) is int:self.assertIsNone(p.minimum_width_guard(board,'both'))
    else:
     with self.assertRaises(p.Rejected):p.minimum_width_guard(board,'both')

if __name__=='__main__':unittest.main()
