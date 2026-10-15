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


class FailedPrefixContinuationControls(unittest.TestCase):
 def prepared(self,root):
  from experiments.universal_shift_recovery_v1 import pruning_readback as shared
  source=root/'source'/'board.kicad_pcb';source.parent.mkdir();source.write_text('authored guard fixture; not Native')
  old=dict(passed=False,source_current=False,reason='Rejected: normal DRC retained worker population differs from steps',final_charged_results=[])
  (root/'old.json').write_text(json.dumps(old));(root/'original.json').write_text(json.dumps(dict(parity_native=dict(warnings=81,ignored_checks=list(range(5))))))
  spec=dict(status='frozen',kind='universal-preparation950-v1',pins={},source=str(source),source_hashes=p.tree_hash(source.parent),prior_execution='old.json',prior_execution_sha256=p.sha(root/'old.json'),prior_state={k:old[k] for k in ('passed','source_current','reason')},prior_rows=[],original_receipt='original.json')
  return shared,spec,old
 def test_exact_failed_prefix_can_be_carried_without_becoming_a_pass(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();shared,spec,old=self.prepared(root)
   with patch.object(shared,'ROOT',root),patch.object(p,'preflight',return_value='not-native'),patch.object(p,'native_accepted',return_value=True):
    self.assertEqual(shared.inputs(spec)[1],'not-native')
   self.assertIs(old['passed'],False)
 def test_changed_typed_state_reason_rows_or_digest_refuse(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();shared,spec,old=self.prepared(root)
   for key,value in [('passed',0),('source_current',0),('passed',True),('reason','other failure'),('final_charged_results',[{}])]:
    with self.subTest(key=key,value=value):
     changed={**old,key:value};(root/'old.json').write_text(json.dumps(changed));attempt=copy.deepcopy(spec);attempt['prior_execution_sha256']=p.sha(root/'old.json')
     with patch.object(shared,'ROOT',root),self.assertRaisesRegex(p.Rejected,'failed750 prefix changed'):shared.inputs(attempt)
   (root/'old.json').write_text(json.dumps(old));attempt=copy.deepcopy(spec);attempt['prior_execution_sha256']='0'*64
   with patch.object(shared,'ROOT',root),self.assertRaisesRegex(p.Rejected,'failed750 prefix changed'):shared.inputs(attempt)
 def test_old_positive_prefix_protocol_cannot_accept_failure(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();shared,spec,old=self.prepared(root);spec['kind']='universal-native-reserve750-v1'
   with patch.object(shared,'ROOT',root),self.assertRaisesRegex(p.Rejected,'completed B2 prefix changed'):shared.inputs(spec)
