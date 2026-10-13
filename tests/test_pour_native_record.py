"""Saved-fill readback tamper regressions; these do not establish native proof."""
import copy,json,tempfile,unittest
from pathlib import Path
from autorouter import pour_rule_area as m,sexpr as sx,pipeline as p
from test_pour_rule_area import board,zone
class SavedPourRecord(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=p.c.ROOT/'tests');self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name).resolve()/'owned.kicad_pcb'
  self.tree=board([zone(),['zone',['net','1'],['uuid','"00000000-0000-0000-0000-000000000099"'],['layers','"F.Cu"','"B.Cu"']]])
  sx.write(self.path,self.tree);self.path.with_suffix('.kicad_pro').write_text('{}')
  areas=m.qualify(self.tree);checks=[dict(x,native_fill_outline_count=0,intersection=[],passed=True) for x in m.fill_matrix(self.tree,areas)]
  self.record={'schema':1,'policy':m.AUDIT_POLICY,'native_version':'10.0.0','source':str(self.path),
   'board_sha256':m.sha(self.path.read_bytes()),'project_sha256':m.sha(self.path.with_suffix('.kicad_pro').read_bytes()),'board_saved':False,
   'source_areas':areas,'passed':True,'native_areas':[{k:v for k,v in a.items() if k!='source_zone_ast_sha256'} for a in areas],
   'native_zone_uuids':sorted(m._atom(z,'uuid') for z in sx.children(self.tree,'zone')),'fill_checks':checks}
 def test_complete_source_matrix_and_allowed_back_overlap(self):
  row=self.record['fill_checks'][1];row['intersection']=[{'owned_nonapplicable_probe':True}]
  self.assertFalse(row['applicable']);self.assertTrue(m.verify_native_record(self.record,self.path))
 def test_missing_duplicate_reordered_or_truncated_matrix_rejects(self):
  for variant in ([],self.record['fill_checks'][:1],self.record['fill_checks'][::-1],[self.record['fill_checks'][0]]*2):
   with self.subTest(variant=variant):
    record=copy.deepcopy(self.record);record['fill_checks']=variant
    with self.assertRaises(ValueError):m.verify_native_record(record,self.path)
 def test_source_hash_native_flags_counts_and_intrusion_reject(self):
  for kind in ('hash','flags','census','count','bool_count','intrusion','passed','extra'):
   record=copy.deepcopy(self.record)
   if kind=='hash':record['board_sha256']='0'*64
   elif kind=='flags':record['native_areas'][0]['disallow']['copperpour']=False
   elif kind=='census':record['native_zone_uuids'].pop()
   elif kind=='count':record['fill_checks'][0]['native_fill_outline_count']=1
   elif kind=='bool_count':record['fill_checks'][0]['native_fill_outline_count']=False
   elif kind=='intrusion':record['fill_checks'][0]['intersection']=[{'owned_bad_geometry':True}]
   elif kind=='passed':record['fill_checks'][0]['passed']=1
   else:record['optional_native_proof']=True
   with self.subTest(kind=kind),self.assertRaises(ValueError):m.verify_native_record(record,self.path)
 def test_qualified_source_requires_audit_even_without_optional_receipt_flag(self):
  empty=Path(self.tmp.name)/'run';empty.mkdir()
  with self.assertRaises((OSError,ValueError,p.Rejected)):
   p.check_pour_evidence(empty,{'adapter':'none','steps':[]},self.tree,self.path)
 def test_any_footprint_zone_blocks_new_pour_policy(self):
  for z in (zone(),['zone',['net','1']]):
   tree=copy.deepcopy(self.tree);tree.append(['footprint','"owned"',z])
   with self.assertRaises(ValueError):m.qualify(tree)
 def test_no_pour_preserves_previous_large_zone_scope(self):
  plain=board([['zone',['net','1']] for _ in range(17)])
  self.assertEqual(m.qualify(plain),[]);p.check_rule_area_support(plain)
  plain.append(zone())
  with self.assertRaisesRegex(ValueError,'zone population'):m.qualify(plain)
if __name__=='__main__':unittest.main()
