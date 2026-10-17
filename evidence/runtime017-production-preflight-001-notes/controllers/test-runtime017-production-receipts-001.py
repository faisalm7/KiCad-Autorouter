"""Pure raw-receipt controls; no Native, JVM, routing or GUI qualification."""
from pathlib import Path
import importlib.util,json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('production017enclosure',ROOT/'.runs/run-runtime017-production-001.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ReceiptControls(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=ROOT/'.runs');self.path=Path(self.temp.name)/'result.json';self.pin='a'*64
  self.row=dict(schema=1,kind=m.CHILD_KIND,protocol_sha256=self.pin,passed=True,status='completed')
 def tearDown(self):self.temp.cleanup()
 def write(self,row):self.path.write_text(json.dumps(row))
 def test_exact_captured_bytes(self):
  self.write(self.row);raw,row,error=m.read_child(self.path,self.pin)
  self.assertEqual(raw,self.path.read_bytes());self.assertEqual(row,self.row);self.assertIsNone(error)
  m.shared_helpers().child_bytes_fresh(self.path,raw)
 def test_absent_receipt(self):self.assertEqual(m.read_child(self.path,self.pin),(None,None,None))
 def test_wrong_identity_rejects(self):
  for key,value in [('kind','another-qualifier'),('protocol_sha256','b'*64),('schema',2)]:
   with self.subTest(key=key):
    self.write(dict(self.row,**{key:value}));raw,row,error=m.read_child(self.path,self.pin)
    self.assertEqual(raw,self.path.read_bytes());self.assertIsNone(row);self.assertIn('identity',error)
 def test_duplicate_and_nonfinite_reject(self):
  for content in ('{"schema":1,"schema":1}', '{"value":NaN}'):
   with self.subTest(content=content):
    self.path.write_text(content);raw,row,error=m.read_child(self.path,self.pin)
    self.assertEqual(raw,content.encode());self.assertIsNone(row);self.assertIsNotNone(error)
 def test_removed_and_changed_bytes_reject(self):
  self.write(self.row);raw,_,_=m.read_child(self.path,self.pin);self.write(dict(self.row,passed=False))
  with self.assertRaises(m.p.Rejected):m.shared_helpers().child_bytes_fresh(self.path,raw)
  self.path.unlink()
  with self.assertRaises(m.p.Rejected):m.shared_helpers().child_bytes_fresh(self.path,raw)
if __name__=='__main__':unittest.main(verbosity=2)
