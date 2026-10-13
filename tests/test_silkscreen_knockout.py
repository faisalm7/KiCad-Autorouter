"""Static scope controls; actual native serialization/rendering is separate."""
import copy,unittest
from autorouter import pipeline as p,sexpr as sx
class SilkscreenKnockout(unittest.TestCase):
 def tree(self,layer='B.SilkS',extras=('knockout',)):
  return ['kicad_pcb',['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal'],['7','"F.SilkS"','user'],['9','"B.SilkS"','user'],['25','"Edge.Cuts"','user']],['gr_text','"owned"',['layer','"'+layer+'"',*extras],['effects',['font',['size','1','1']],['justify','mirror']]]]
 def test_only_two_declared_root_silk_sides_preserve_all_atoms(self):
  for side in ('F.SilkS','B.SilkS'):
   tree=self.tree(side);before=copy.deepcopy(tree);p.check_edge_text_support(tree);self.assertEqual(tree,before)
 def test_knockout_copper_edge_unknown_duplicate_extra_and_nested_reject(self):
  for side in ('F.Cu','Edge.Cuts','MadeUp.Layer'):
   with self.subTest(side=side),self.assertRaises(p.Rejected):p.check_edge_text_support(self.tree(side))
  for extras in (('knockout','knockout'),('future',),('"knockout"',),('knockout','future')):
   with self.subTest(extras=extras),self.assertRaises(p.Rejected):p.check_edge_text_support(self.tree(extras=extras))
  for parent in ('footprint','dimension'):
   tree=self.tree();tree[-1]=[parent,'"owned"',tree[-1]]
   if parent=='dimension':tree[-1].append(['layer','"F.SilkS"'])
   with self.subTest(parent=parent),self.assertRaises(p.Rejected):p.check_edge_text_support(tree)
 def test_undeclared_silk_and_duplicate_layer_remain_rejected(self):
  tree=self.tree();sx.one(tree,'layers').pop(4)
  with self.assertRaises(p.Rejected):p.check_edge_text_support(tree)
  tree=self.tree();tree[-1].append(['layer','"F.SilkS"'])
  with self.assertRaises(p.Rejected):p.check_edge_text_support(tree)
if __name__=='__main__':unittest.main()
