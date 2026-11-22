"""Whole draft GUI import, pure text helper only; no wx/process/Native/model."""
from pathlib import Path
import unittest
from autorouter import gui
TARGET=Path(__file__).resolve().parents[1]/'autorouter/gui.py'

class OpenRefusalText(unittest.TestCase):
 def test_actual_sidecar_error_keeps_exact_reason_and_requires_new_task(self):
  reason='Could not open retained project: composed candidate sidecars or file set differ from original'
  text=gui.open_refusal_text('export',ValueError(reason))
  self.assertTrue(text.endswith('Technical detail: '+reason))
  for required in ('checked opening has stopped','fresh task','ordinary assistant session','Explicitly choose','Source','Preview','save and close its editors','Place components','new draft','New review','explicit acceptance','fresh Native validation','Prior approval does not transfer','no constraint or check is waived'):
   self.assertIn(required,text)
  self.assertIn('cannot revalidate an edited export in place',text)
  self.assertNotIn('source shown above',text)
 def test_known_freshness_checks_and_case_variants_are_explained(self):
  reasons=['Checked export changed while opening. Start a fresh preview; retained files were not reaccepted.',
   'Checked export local settings disappeared while opening.',
   'Composed candidate changed during the final origin check.',
   'export changed during final readback','export changed after final tool checks',
   'export changed during final placement origin check','export changed during placement origin check',
   'export project changed','COMPOSED CANDIDATE SIDECARS OR FILE SET DIFFER FROM THE ORIGINAL']
  for reason in reasons:
   with self.subTest(reason=reason):
    text=gui.open_refusal_text('export',reason)
    self.assertIn('no longer matches its recorded checks',text);self.assertTrue(text.endswith(reason))
 def test_unrelated_or_constraint_failures_remain_exact(self):
  reasons=['export changed original geometry or validated route copper','export protected copper changed',
   'export native tool pin changed','export inputs/runtime/evidence changed','Fresh original-rule Native export refused.',
   'Could not open retained project: permission denied','Inspection was cancelled. No project was opened.']
  for reason in reasons:
   with self.subTest(reason=reason):self.assertEqual(gui.open_refusal_text('export',ValueError(reason)),reason)
 def test_nonexport_openings_keep_original_semantics(self):
  reason='composed candidate sidecars or file set differ from original'
  for kind in ('preview','review','source','open_export','EXPORT',None):
   with self.subTest(kind=kind):self.assertEqual(gui.open_refusal_text(kind,reason),reason)
 def test_editor_change_is_a_possibility_not_a_new_acceptance(self):
  text=gui.open_refusal_text('export','export project changed')
  self.assertIn('KiCad may update',text);self.assertIn('even if the PCB is unchanged',text)
  self.assertIn('Earlier approval does not accept those changes.',text)
  self.assertNotIn('Your PCB is unchanged',text)
  self.assertEqual(gui.open_refusal_text('export',None),'None')
 def test_workspace_restarts_with_fresh_inspection_and_review(self):
  for reason in ('export project changed','export inputs/runtime/evidence changed'):
   text=gui.open_refusal_text('export',reason,restart_copy=True)
   for advice in ('Save and close','Start from this copy','fresh inspection','Review and approve'):
    self.assertIn(advice,text)
   self.assertTrue(text.endswith(reason))
 def test_whole_module_is_the_product_source(self):
  self.assertEqual(Path(gui.__file__).resolve(),TARGET)

if __name__=='__main__':unittest.main(verbosity=2)
