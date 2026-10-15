"""Actual filesystem publisher fault controls; no Native or routing evidence."""
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from autorouter import floor_route as f,pipeline as p
from experiments.native_components_v1 import controls as c,fixtures
class NativeComponentDeliveryControls(unittest.TestCase):
 def test_late_publisher_invalidation_cannot_keep_passed_true(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'.cache') as tmp:
   out=Path(tmp);source=out/'source.txt';source.write_text('original')
   record={'status':'completed','accepted':False,'passed':True};real=p.save_json;changed=[]
   def write(path,data):
    real(path,data)
    if not changed:source.write_text('mutated');changed.append(True)
   def stable():
    if source.read_text()!='original':raise p.Rejected('actual late source mutation after write')
   with patch.object(p,'save_json',side_effect=write):f.publish(out,record,stable,lambda:c.account_delivery(record,0.1,0.1),lambda:10)
   self.assertEqual(record['status'],'invalidated');self.assertFalse(record['passed']);self.assertFalse(f.read_json(out/'result.json')['passed'])
   self.assertTrue(list(out.glob('invalidated-result-*')))
 def test_completed_control_changes_are_not_adopted_as_final_material(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'.cache') as tmp:
   out=Path(tmp);source=out/'final-drc.json';source.write_text('qualified original')
   complete={out:c.completed_inventory(out)};c.check_completed(complete)
   source.write_text('tampered');
   with self.assertRaisesRegex(p.Rejected,'completed component control changed'):c.check_completed(complete)
   source.write_text('qualified original');(out/'added-empty-directory').mkdir()
   with self.assertRaisesRegex(p.Rejected,'completed component control changed'):c.check_completed(complete)
 def test_short_control_requires_the_intended_contact_finding(self):
  def report(kind,ids):return {'opens':0,'blocking':1,'warnings':0,'exclusions':0,'ignored_checks':[], 'findings':[{'type':kind,'severity':'error','items':[{'uuid':v} for v in ids]}]}
  intended=[fixtures.uid('short').strip('"'),fixtures.uid('B').strip('"')]
  self.assertTrue(c.intended_short_observed(report('shorting_items',intended)))
  self.assertFalse(c.intended_short_observed(report('track_width',intended[:1])))
  self.assertFalse(c.intended_short_observed(report('shorting_items',['unrelated','other'])))
  excluded=report('shorting_items',intended);excluded['findings'][0]['excluded']=True
  self.assertFalse(c.intended_short_observed(excluded))
