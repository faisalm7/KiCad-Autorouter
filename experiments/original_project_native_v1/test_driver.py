"""Route-order regression; all full records and identities must remain exact."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
from experiments.original_project_native_v1.driver import route_records
class RouteRecords(unittest.TestCase):
 def test_order_only_permutation_preserves_full_records(self):
  a=['kicad_pcb',['segment',['uuid','a'],['width','0.2']],['via',['uuid','b'],['size','0.6']]]
  self.assertEqual(route_records(a),route_records([a[0],a[2],a[1]]))
  b=copy.deepcopy(a);b[1][2][1]='0.1';self.assertNotEqual(route_records(a),route_records(b))
 def test_missing_or_duplicate_identity_rejects(self):
  for b in [['kicad_pcb',['segment']],['kicad_pcb',['segment',['uuid','a']],['via',['uuid','a']]]]:
   with self.assertRaises(p.Rejected):route_records(b)
if __name__=='__main__':unittest.main()
