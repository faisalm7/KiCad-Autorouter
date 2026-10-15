"""Software regression: rejected trials must bind declared engine settings too."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p
from experiments.universal_shift_recovery_v1 import b2

class MissingBaselineSettingControls(unittest.TestCase):
 def rejected_trial(self,folder):
  engine=p.engine_profile_settings('tuned',80,scoring_variant='via_default')
  engine.update(outer_task_wall_budget_seconds=90,outer_task_cpu_budget_seconds=90)
  process=dict(name='engine',argv=p.engine_argv(folder,engine['argv']),cwd=str(folder),status='success',exit_code=0,cleanup_complete=True)
  (folder/'engine-process.json').write_text(json.dumps(process))
  source=folder/'original.kicad_pcb';source.with_suffix('.kicad_pro').write_text('{}')
  data=dict(source=str(source),source_hashes={},scope='whole_board_unlocked_routing',adapter='both',engine_profile='tuned',budget_seconds=90,cpu_budget_seconds=90,status='rejected',accepted=False,scoring_variant='via_default',engine_budget=engine,steps=[process])
  return source,data
 def assert_mislabelling_rejected(self,variant):
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d).resolve();source,data=self.rejected_trial(folder);data['scoring_variant']=variant
   # This unit isolates engine-setting binding; no Native/process validation claim.
   with patch.object(b2.obs,'workers',return_value=[]):
    with self.assertRaisesRegex(p.Rejected,'engine profile'):b2.observe(folder,data,source,None,{},None)
 def test_rejected_low_cannot_relabel_default_engine(self):self.assert_mislabelling_rejected('via_low')
 def test_rejected_high_cannot_relabel_default_engine(self):self.assert_mislabelling_rejected('via_high')
 def test_unmodified_rejected_trial_settings_are_verified(self):
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d).resolve();source,data=self.rejected_trial(folder)
   with patch.object(b2.obs,'workers',return_value=[]):result=b2.observe(folder,data,source,None,{},None)
   self.assertTrue(result['engine_profile_verified']);self.assertFalse(result['candidate_valid'])
