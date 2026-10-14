"""Read-only fixed benchmark selection, independent of ignored actual corpus."""
import tempfile,unittest
from pathlib import Path
from unittest import mock
from scripts import experiment_quality as q
from autorouter import pipeline as p
from experiments.arcdice_native_class_v1 import source

class ArcDiceSelection(unittest.TestCase):
 def test_pinned_full_source_selected_without_staging(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp).resolve();base=root/'.runs/arcdice-original-native-001/original';base.mkdir(parents=True)
   files={'LICENSE':b'owned notice','README.md':b'owned metadata','hardware/ArcDice.kicad_pcb':b'owned pcb','hardware/ArcDice.kicad_pro':b'owned project','hardware/ArcDice.kicad_sch':b'owned schematic'}
   for name,raw in files.items():
    target=base/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
   before=p.tree_hash(base)
   with mock.patch.object(q.c,'ROOT',root),mock.patch.object(source,'capture',return_value=files):
    board,family=q.selected_source('arcdice')
    self.assertEqual(board,base/'hardware/ArcDice.kicad_pcb');self.assertIn('exposed',family);self.assertEqual(p.tree_hash(base),before)
    (base/'LICENSE').write_bytes(b'changed notice')
    with self.assertRaisesRegex(p.Rejected,'notice-bearing'):q.selected_source('arcdice')
    self.assertEqual((base/'LICENSE').read_bytes(),b'changed notice')
if __name__=='__main__':unittest.main()
