"""Independent R2 final-snapshot controls; synthetic stages only."""
from pathlib import Path
import json,sys,unittest
review=Path(__file__).resolve().parent;snap=review/'snapshot-003'
sys.path[:0]=[str(snap),str(snap/'tests')]
import test_board_floor_policy as fixture
from autorouter import pipeline as p,sexpr as sx
class Controls(unittest.TestCase):
 def setUp(self):
  self.case=fixture.FloorReceipt('test_complete_synthetic_floor_receipt');self.case.setUp();self.addCleanup(self.case.doCleanups)
 def test_full_receipt(self):self.assertTrue(self.case.check()['current'])
 def test_missing_ses_rehashed_inventory(self):
  (self.case.out/'routes.ses').unlink();self.case.save()
  with self.assertRaisesRegex(p.Rejected,'SES'):self.case.check()
 def test_missing_import_rehashed_inventory(self):
  (self.case.out/'imported.kicad_pcb').unlink();self.case.save()
  with self.assertRaisesRegex(p.Rejected,'import'):self.case.check()
 def test_arbitrary_refill_process_consistent_step(self):
  path=self.case.out/'refill-drc-process.json';data=json.loads(path.read_text());data['argv']=['/usr/bin/true'];path.write_text(json.dumps(data))
  next(s for s in self.case.data['steps'] if s['name']=='refill-drc')['argv']=data['argv'];self.case.save()
  with self.assertRaisesRegex(p.Rejected,'provenance'):self.case.check()
 def test_import_changed_final_candidate_unchanged(self):
  path=self.case.out/'imported.kicad_pcb';tree=sx.read(path);sx.one(sx.children(tree,'segment')[0],'width')[1]='0.2';sx.write(path,tree);self.case.save()
  with self.assertRaisesRegex(p.Rejected,'binding'):self.case.check()
if __name__=='__main__':unittest.main(verbosity=2)
