"""Bounded comparison metadata, never a DSN/SES geometry exemption."""
import unittest
from experiments.roller_export_alias_v1 import padless_alias as a
from autorouter.adapter import _parse_dsn,_dump_dsn
# Authored fixture only; never rely on ignored raw experimental data in suite.
from tests.test_padless_alias_scope import source

def dsn(binding,path):
 names=[r['alias'] for r in binding['aliases']]
 return (f'(pcb "{path}" (parser (string_quote ")) (unit um) (resolution um 10) (structure (layer F.Cu (type signal))) (library (image OwnedDecoration)) (placement (component OwnedDecoration (place {names[0]} 1 0 front 0) (place {names[1]} 2 0 front 0))) (network))').encode()

class BoundDesignPath(unittest.TestCase):
 def test_only_exact_bound_absolute_metadata_normalizes(self):
  raw=source();pa=a.plan(raw,'A');pb=a.plan(raw,'B');x='/owned/A/native.dsn';y='/owned/B/native.dsn'
  da,db=dsn(pa,x),dsn(pb,y)
  self.assertNotEqual(a.normalize_dsn(da,raw,pa),a.normalize_dsn(db,raw,pb))
  self.assertEqual(a.normalize_dsn(da,raw,pa,export_path=x),a.normalize_dsn(db,raw,pb,export_path=y))
  self.assertEqual(da,dsn(pa,x))
 def test_wrong_relative_traversal_or_other_role_rejects(self):
  raw=source();plan=a.plan(raw);path='/owned/A/native.dsn';data=dsn(plan,path)
  for bad in ('/wrong/native.dsn','native.dsn','/owned/../A/native.dsn','/owned/A/other.dsn'):
   with self.subTest(bad=bad),self.assertRaises(ValueError):a.normalize_dsn(data,raw,plan,export_path=bad)
  tree=_parse_dsn(data.decode());tree.append(['unknown','"'+path+'"'])
  with self.assertRaisesRegex(ValueError,'outside root'):a.normalize_dsn(_dump_dsn(tree).encode(),raw,plan,export_path=path)
 def test_geometry_difference_not_normalized(self):
  raw=source();plan=a.plan(raw);path='/owned/A/native.dsn';data=dsn(plan,path)
  changed=data.replace(b' 1 0 front',b' 9 0 front')
  self.assertNotEqual(a.normalize_dsn(data,raw,plan,export_path=path),a.normalize_dsn(changed,raw,plan,export_path=path))

if __name__=='__main__':unittest.main()
