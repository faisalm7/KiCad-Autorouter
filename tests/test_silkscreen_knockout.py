"""Static scope controls; actual native serialization/rendering is separate."""
import copy,json,unittest
from autorouter import pipeline as p,sexpr as sx
class SilkscreenKnockout(unittest.TestCase):
 def tree(self,layer='B.SilkS',extras=('knockout',)):
  return ['kicad_pcb',['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal'],['7','"F.SilkS"','user'],['9','"B.SilkS"','user'],['25','"Edge.Cuts"','user']],['gr_text','"owned"',['layer','"'+layer+'"',*extras],['effects',['font',['size','1','1']],['justify','mirror']]]]
 def test_declared_root_silk_and_copper_knockout_preserve_all_atoms(self):
  for side in ('F.SilkS','B.SilkS','F.Cu','B.Cu'):
   tree=self.tree(side);before=copy.deepcopy(tree);p.check_edge_text_support(tree);self.assertEqual(tree,before)
 def test_edge_unknown_duplicate_extra_and_nested_knockout_reject(self):
  for side in ('Edge.Cuts','MadeUp.Layer'):
   with self.subTest(side=side),self.assertRaises(p.Rejected):p.check_edge_text_support(self.tree(side))
  for extras in (('knockout','knockout'),('future',),('"knockout"',),('knockout','future')):
   with self.subTest(extras=extras),self.assertRaises(p.Rejected):p.check_edge_text_support(self.tree(extras=extras))
  for side in ('F.SilkS','B.SilkS','F.Cu','B.Cu'):
   for parent in ('footprint','dimension'):
    tree=self.tree(side);tree[-1]=[parent,'"owned"',tree[-1]]
    if parent=='dimension':tree[-1].append(['layer','"F.SilkS"'])
    with self.subTest(parent=parent,side=side),self.assertRaises(p.Rejected):p.check_edge_text_support(tree)
 def test_undeclared_silk_and_copper_and_duplicate_layer_remain_rejected(self):
  for side in ('F.Cu','B.Cu'):
   tree=self.tree(side);table=sx.one(tree,'layers');table[:]=[row for row in table if not isinstance(row,list) or row[1]!=json.dumps(side)]
   with self.subTest(side=side),self.assertRaises(p.Rejected):p.check_edge_text_support(tree)
  tree=self.tree();sx.one(tree,'layers').pop(4)
  with self.assertRaises(p.Rejected):p.check_edge_text_support(tree)
  tree=self.tree();tree[-1].append(['layer','"F.SilkS"'])
  with self.assertRaises(p.Rejected):p.check_edge_text_support(tree)
if __name__=='__main__':unittest.main()
