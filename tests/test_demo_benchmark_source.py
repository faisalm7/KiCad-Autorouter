"""Read-only fixed-demo selection; synthetic transport, no native proof."""
import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p
from scripts import experiment_quality as q

class DemoBenchmarkSource(unittest.TestCase):
 def setUp(self):
  temp=tempfile.TemporaryDirectory(dir=p.c.ROOT/'tests');self.addCleanup(temp.cleanup);self.root=Path(temp.name)
  self.demo=self.root/'.data/led-demo-001/project';self.demo.mkdir(parents=True)
  self.payloads={n:('synthetic '+n).encode() for n in ('LICENSE','README.md','PushButtonLed.kicad_pcb','PushButtonLed.kicad_pro','PushButtonLed.kicad_sch')}
  for n,raw in self.payloads.items():(self.demo/n).write_bytes(raw)
  self.verified={'files':{n:{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for n,raw in self.payloads.items()}}
 def test_fresh_selection_preserves_source_and_never_writes_a_staging_directory(self):
  before=p.tree_hash(self.demo);replacement=self.root/'.runs/led-demo-benchmark-source';replacement.mkdir(parents=True);(replacement/'PushButtonLed.kicad_pcb').write_bytes(b'owner')
  with patch.object(q.c,'ROOT',self.root),patch('scripts.fetch_led_demo.verify_project',return_value=self.verified):
   board,_=q.selected_source('push-button-led')
  self.assertEqual(board,self.demo/'PushButtonLed.kicad_pcb');self.assertEqual(p.tree_hash(self.demo),before);self.assertEqual(list(replacement.iterdir()),[replacement/'PushButtonLed.kicad_pcb']);self.assertEqual((replacement/'PushButtonLed.kicad_pcb').read_bytes(),b'owner')
 def test_changed_capture_rejects_without_any_staging_write(self):
  calls=[]
  def changed(path):
   calls.append(path)
   if len(calls)==1:(path/'PushButtonLed.kicad_pro').write_bytes(b'changed')
   return self.verified
  with patch.object(q.c,'ROOT',self.root),patch('scripts.fetch_led_demo.verify_project',side_effect=changed),self.assertRaisesRegex(p.Rejected,'changed during benchmark'):
   q.selected_source('push-button-led')
  self.assertFalse((self.root/'.runs').exists())
 def test_existing_canonical_snapshot_cannot_fall_back_to_demo_if_corrupt(self):
  original=self.root/'.runs/push-button-led-original-native-001/original';original.mkdir(parents=True)
  with patch.object(q.c,'ROOT',self.root),patch('experiments.licensed_acquisition_v7.native_snapshot.capture',return_value=self.payloads),patch('scripts.fetch_led_demo.verify_project',side_effect=AssertionError('fallback')),self.assertRaisesRegex(p.Rejected,'exact original notice-bearing'):
   q.selected_source('push-button-led')

if __name__=='__main__':unittest.main()
