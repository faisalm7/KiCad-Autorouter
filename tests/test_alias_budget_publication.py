"""Late diagnostic cap transitions must invalidate the canonical positive."""
import tempfile,unittest
from pathlib import Path
from autorouter import floor_route as f
from experiments.roller_export_alias_v1 import driver

class DiagnosticPublication(unittest.TestCase):
 def test_late_cap_clears_disk_positive_and_preserves_prior_index(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp).resolve();record={'accepted':False,'status':'controls_passed','controls_passed':True};calls=[]
   def account():
    calls.append(1)
    if len(calls)>=2:record.update(status='budget_exceeded',controls_passed=False)
    if record['status']!='controls_passed':record['controls_passed']=False
   driver.finalize_controls(out,record,lambda:None,account,lambda:1,lambda:None)
   self.assertFalse(f.read_json(out/'result.json')['controls_passed'])
   old=list(out.glob('invalidated-result-*.json'));self.assertEqual(len(old),1)
   self.assertTrue(f.read_json(old[0])['controls_passed'])
 def test_in_budget_actual_positive_is_retained(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp).resolve();record={'accepted':False,'status':'controls_passed','controls_passed':True}
   driver.finalize_controls(out,record,lambda:None,lambda:None,lambda:1,lambda:None)
   self.assertTrue(f.read_json(out/'result.json')['controls_passed']);self.assertFalse(list(out.glob('invalidated-result-*.json')))

if __name__=='__main__':unittest.main()
