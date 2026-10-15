"""Check owned falsifiers do not inject UUID faults or change their source."""
import copy,unittest
from pathlib import Path
from autorouter import sexpr as sx
from experiments.native_components_v1 import fixtures
class NativeComponentFixtureControls(unittest.TestCase):
 def source(self):return sx.read(Path(__file__).resolve().parents[1]/'fixtures/smoke/smoke.kicad_pcb')
 def test_complete_census_has_no_duplicate_native_object_uuid(self):
  def ids(node):
   if isinstance(node,list):
    if node and node[0]=='uuid':yield sx.unquote(node[1])
    for child in node:yield from ids(child)
  for case in fixtures.CASES:
   with self.subTest(case=case):
    tree,_=fixtures.recipe(case,self.source());values=list(ids(tree));self.assertEqual(len(values),len(set(values)))
 def test_recipes_preserve_source_and_are_deterministic(self):
  base=self.source();before=copy.deepcopy(base)
  for case in fixtures.CASES:
   tree,groups=fixtures.recipe(case,base);self.assertEqual(base,before);self.assertEqual((tree,groups),fixtures.recipe(case,base))
