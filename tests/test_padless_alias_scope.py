"""Source-backed alias-scope regression; no native correctness claim."""
import json,unittest
from experiments.roller_export_alias_v1 import padless_alias as alias
from autorouter import sexpr as sx

def source(text=None,kind='fp_text'):
 tree=['kicad_pcb',['version','20241229']]
 for i in (1,2):
  fp=['footprint','"OwnedDecoration"',['uuid',json.dumps(f'00000000-0000-4000-8000-{i:012d}')],['property','"Reference"','"DUP"',['layer','"F.Fab"']],['layer','"F.Cu"'],['at',str(i),'0'],['attr','board_only']]
  if text is not None and i==1:
   fp.append([kind,'user',json.dumps(text),['layer','"F.Cu"']] if kind=='fp_text' else [kind,json.dumps(text),['layer','"F.Cu"']])
  tree.append(fp)
 return (sx.dump(tree)+'\n').encode()

class AliasMacroScope(unittest.TestCase):
 def test_legacy_reference_value_and_current_variable_macros_reject(self):
  for text in ('%R','x%R-y','%V','${REFERENCE}'):
   for kind in ('fp_text','fp_text_box'):
    with self.subTest(text=text,kind=kind),self.assertRaisesRegex(ValueError,'variable-dependent'):
     alias.plan(source(text,kind))
 def test_macro_on_root_copper_text_rejects(self):
  tree=sx.parse(source().decode());tree.append(['gr_text','"%R"',['layer','"F.Cu"']])
  with self.assertRaisesRegex(ValueError,'variable-dependent'):alias.plan((sx.dump(tree)+'\n').encode())
 def test_literal_surface_and_original_bytes_preserved(self):
  raw=source('owned literal copper');before=bytes(raw);plan=alias.plan(raw)
  self.assertEqual(len(plan['aliases']),2);self.assertEqual(raw,before)
  self.assertFalse(plan['routing_accepted'])

if __name__=='__main__':unittest.main()
