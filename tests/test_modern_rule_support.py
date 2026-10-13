"""Global static admission and unchanged critical-warning acceptance controls.

Actual KiCad severity/geometry behavior needs the separate native protocol.
"""
from pathlib import Path
import copy,json,tempfile,unittest
from unittest.mock import patch
from autorouter import pipeline as p,sexpr as sx

class ModernRuleAdmission(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=p.c.ROOT/'tests');self.addCleanup(self.temp.cleanup);self.board=Path(self.temp.name)/'owned.kicad_pcb'
  self.tree=['kicad_pcb',['version','20260206'],['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal'],['17','"Dwgs.User"','user'],['25','"Edge.Cuts"','user'],['35','"F.Fab"','user'],['39','"User.1"','user']]]
  self.project={'board':{'design_settings':{'rule_severities':{'hole_to_hole':'warning','clearance':'error','text_on_edge_cuts':'error'}}},'net_settings':{'classes':[]}}
 def preflight(self,tree=None):
  sx.write(self.board,self.tree if tree is None else tree);self.board.with_suffix('.kicad_pro').write_text(json.dumps(self.project));return p.preflight(self.board)
 def test_registered_key_and_hole_warning_preserve_original_rules(self):
  before=copy.deepcopy(self.project);self.preflight();self.assertEqual(json.loads(self.board.with_suffix('.kicad_pro').read_text()),before)
 def test_hole_ignored_and_other_critical_warning_remain_blocked(self):
  for key,severity in [('hole_to_hole','ignore'),('hole_near_hole','warning'),('clearance','warning')]:
   with self.subTest(key=key):
    saved=copy.deepcopy(self.project);self.project['board']['design_settings']['rule_severities'][key]=severity
    with self.assertRaisesRegex(p.Rejected,'core native check not blocking'):self.preflight()
    self.project=saved
 def test_all_outline_text_forms_and_severities_block_globally(self):
  for key in ('gr_text','fp_text','gr_text_box','fp_text_box','property','dimension'):
   for severity in ('error','warning','ignore',None):
    for layer in ('"Edge.Cuts"','Edge.Cuts'):
     with self.subTest(item=key,severity=severity,layer=layer):
      self.project['board']['design_settings']['rule_severities'].pop('text_on_edge_cuts',None)
      if severity:self.project['board']['design_settings']['rule_severities']['text_on_edge_cuts']=severity
      item=[key,'"Owned hidden label"',['layer',layer],['at','1','1'],['hide','yes']]
      tree=copy.deepcopy(self.tree);tree.append(['footprint','"Owned"',item] if key in {'fp_text','fp_text_box','property'} else item)
      with self.assertRaisesRegex(p.Rejected,'on Edge.Cuts'):self.preflight(tree)
 def test_nested_dimension_text_and_fields_block(self):
  tree=copy.deepcopy(self.tree);tree.append(['dimension',['layer','"Dwgs.User"'],['gr_text','"nested"',['layer','"Edge.Cuts"']]])
  with self.assertRaisesRegex(p.Rejected,'on Edge.Cuts'):self.preflight(tree)
 def test_off_edge_text_label_is_not_a_layer_instruction(self):
  tree=copy.deepcopy(self.tree);tree.extend([['gr_text','"Edge.Cuts"',['layer','"Dwgs.User"']],['footprint','"Owned"',['property','"Value"','"Edge.Cuts"',['at','1','1'],['layer','"F.Fab"']],['property','"Sheetname"','"Edge.Cuts"']]])
  self.preflight(tree)
 def test_missing_duplicate_and_malformed_surface_layer_fail_closed(self):
  for fields in ([],[['layer']], [['layer','"F.Fab"','extra']], [['layer','"F.Fab"'],['layer','"Edge.Cuts"']]):
   with self.subTest(fields=fields):
    tree=copy.deepcopy(self.tree);tree.append(['gr_text','"owned"',*fields])
    with self.assertRaisesRegex(p.Rejected,'layer semantics'):self.preflight(tree)
 def test_critical_warning_and_disabled_native_finding_policy_unchanged(self):
  base={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':[]}
  self.assertTrue(p.native_accepted(base));native=copy.deepcopy(base);native.update(warnings=1,findings=[{'type':'hole_to_hole','severity':'warning','items':[]}])
  self.assertIn('policy-critical native finding: hole_to_hole (warning)',p.native_rejection_reasons(native));self.assertFalse(p.native_accepted(native))
  ignored=copy.deepcopy(base);ignored['ignored_checks']=[{'key':'hole_to_hole'}];self.assertFalse(p.native_accepted(ignored))
  self.assertIn('hole_to_hole',p.CRITICAL_CHECKS);self.assertIn('hole_to_hole',p.CRITICAL_FINDINGS)
 def test_unknown_empty_numeric_surface_layers_reject(self):
  for layer in ('""','"MadeUp.Layer"','25'):
   with self.subTest(layer=layer):
    tree=copy.deepcopy(self.tree);tree.append(['gr_text','"owned"',['layer',layer]])
    with self.assertRaisesRegex(p.Rejected,'declared source layer'):self.preflight(tree)
  tree=copy.deepcopy(self.tree);tree.append(['gr_text','"owned"',['layer','"User.1"']]);self.preflight(tree)
 def test_actual_edge_warning_and_disabled_edge_check_never_become_acceptance(self):
  base={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':[]}
  warning=copy.deepcopy(base);warning.update(warnings=1,findings=[{'type':'text_on_edge_cuts','severity':'warning','items':[]}]);self.assertFalse(p.native_accepted(warning))
  ignored=copy.deepcopy(base);ignored['ignored_checks']=[{'key':'text_on_edge_cuts'}];self.assertFalse(p.native_accepted(ignored))

if __name__=='__main__':unittest.main()
