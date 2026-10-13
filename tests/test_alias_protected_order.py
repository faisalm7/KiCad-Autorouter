"""Exact protected-record reconciliation, without a native support claim."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,sexpr as sx
from experiments.roller_export_alias_v1 import padless_alias

path=Path(__file__).resolve().parents[1]/'experiments/roller_export_alias_v1/retained_ses.py'
spec=importlib.util.spec_from_file_location('alias_order',path);m=importlib.util.module_from_spec(spec)
with patch.dict(sys.modules,{'padless_alias':padless_alias}):spec.loader.exec_module(m)

def board():
 tree=['kicad_pcb',['version','20241229'],['net','1','"GND"'],['net','2','"SIG"']]
 for i,net in enumerate(('1','1','2'),1):
  tree.append(['segment',['uuid',f'"{i}"'],['start',str(i),'0'],['end',str(i),'1'],['width','0.2'],['layer','"F.Cu"'],['net',net]])
 return tree

class ProtectedOrder(unittest.TestCase):
 def test_only_order_changes_all_full_nodes_remain_exact(self):
  source=board();rebuilt=copy.deepcopy(source);rebuilt[-3:]=[rebuilt[-1],rebuilt[-3],rebuilt[-2]]
  self.assertNotEqual(p.routes(rebuilt),p.routes(source));result=m.restore_protected_order(source,rebuilt)
  self.assertEqual(p.routes(result),p.routes(source));self.assertEqual(result,source)
  self.assertNotEqual(p.routes(rebuilt),p.routes(source))
 def test_missing_extra_or_duplicate_identity_refused(self):
  for edit in (lambda t:t.pop(),lambda t:t.append(copy.deepcopy(t[-1])),lambda t:sx.one(t[-1],'uuid').__setitem__(1,'"1"')):
   changed=board();edit(changed)
   with self.subTest(edit=edit),self.assertRaises(ValueError):m.restore_protected_order(board(),changed)
 def test_changed_geometry_net_metadata_or_nonnrouting_refused(self):
  for edit in (lambda t:sx.one(t[-1],'width').__setitem__(1,'0.1'),lambda t:sx.one(t[-1],'net').__setitem__(1,'1'),lambda t:t[-1].append(['locked','yes']),lambda t:t.append(['property','"changed"','"yes"'])):
   changed=board();edit(changed)
   with self.subTest(edit=edit),self.assertRaises(ValueError):m.restore_protected_order(board(),changed)

if __name__=='__main__':unittest.main()
