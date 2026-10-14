"""Route-order regression; all full records and identities must remain exact."""
import copy,sys,unittest,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
from experiments.original_project_native_v1.driver import route_records,completed_evidence
class RouteRecords(unittest.TestCase):
 def test_order_only_permutation_preserves_full_records(self):
  a=['kicad_pcb',['segment',['uuid','a'],['width','0.2']],['via',['uuid','b'],['size','0.6']]]
  self.assertEqual(route_records(a),route_records([a[0],a[2],a[1]]))
  b=copy.deepcopy(a);b[1][2][1]='0.1';self.assertNotEqual(route_records(a),route_records(b))
 def test_missing_or_duplicate_identity_rejects(self):
  for b in [['kicad_pcb',['segment']],['kicad_pcb',['segment',['uuid','a']],['via',['uuid','a']]]]:
   with self.assertRaises(p.Rejected):route_records(b)
class CompletedEvidence(unittest.TestCase):
 def test_late_native_context_candidate_report_or_process_change_is_visible(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp).resolve();(out/'job').mkdir();(out/'candidate').mkdir()
   for rel in ['job/class-observation.json','job/original-final.json','job/original-final-process.json','job/original.dsn','candidate/board.kicad_pcb']:
    path=out/rel;path.write_bytes(b'original');before=completed_evidence(out)
    path.write_bytes(b'altered!');self.assertNotEqual(completed_evidence(out),before);path.write_bytes(b'original')
 def test_publication_only_files_exempt_but_added_directory_visible(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp).resolve();(out/'job').mkdir();(out/'job/report.json').write_bytes(b'native')
   before=completed_evidence(out)
   for name in ['result.json','result.json.partial','invalidated-result-owned.json']:(out/name).write_bytes(b'publication')
   self.assertEqual(completed_evidence(out),before)
   (out/'job/empty-extra').mkdir();self.assertNotEqual(completed_evidence(out),before)
if __name__=='__main__':unittest.main()
