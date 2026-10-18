"""Scope/reader controls; no actual Native or platform qualification."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import config as c,pipeline as p,strategy,recovery,placement_strategy
from autorouter import __main__ as cli

class SelectedScopeTests(unittest.TestCase):
 def test_selected7_default_and_partial_allowed_advanced_refused(self):
  with patch.object(c,'NATIVE_VERSION','10.0.7'):
   p.require_native_scope();p.require_native_scope(scope='partial_completion')
   for kwargs in ({'purpose':'improve'},{'scope':'selected_nets'},{'guidance':'placement-clearance-v1'},
      {'layers':['F.Cu']},{'profile':'tuned'},{'adapter':'none'},{'scoring':'via_low'}):
    with self.subTest(kwargs=kwargs),self.assertRaisesRegex(p.Rejected,'unsupported: selected Native'):
     p.require_native_scope(**kwargs)
 def test_refusal_precedes_source_and_output_access_in_public_entries(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'absent.kicad_pcb';out=Path(tmp)/'untouched'
   with patch.object(c,'NATIVE_VERSION','10.0.7'):
    for call in (lambda:strategy.prune(source,out),lambda:placement_strategy.prune(source,out),
      lambda:recovery.recover(source,out),lambda:cli.preview(source,purpose='improve'),
      lambda:p.route(source,out,adapter='both',guidance_policy='board-floors-v1')):
     with self.assertRaisesRegex(p.Rejected,'unsupported: selected Native'):call()
     self.assertFalse(out.exists())
 def test_default_reader_uses_selected_version_but_not_diagnostic_markers(self):
  with tempfile.TemporaryDirectory() as tmp:
   f=Path(tmp)/'report.json'
   d={'$schema':'https://schemas.kicad.org/drc.v1.json','source':'board.kicad_pcb',
      'kicad_version':'10.0.7','included_severities':['error','warning','exclusion'],
      'ignored_checks':[],'violations':[],'unconnected_items':[],'schematic_parity':[]}
   f.write_text(json.dumps(d))
   with patch.object(c,'NATIVE_VERSION','10.0.7'):
    self.assertEqual(p.parse_report(f,'board.kicad_pcb')['blocking'],0)
    for version in ('10.0.0','10.0.8',True):
     d['kicad_version']=version;f.write_text(json.dumps(d))
     with self.assertRaises(p.Rejected):p.parse_report(f,'board.kicad_pcb')
    with self.assertRaisesRegex(p.Rejected,'explicit caller toolchain'):
     p.check_experimental_route({'experimental_route_policy':'invented'})
 def test_selection_drift_is_a_tool_manifest_failure(self):
  with patch.object(c,'current_native_selection',side_effect=ValueError('changed selection')):
   with self.assertRaisesRegex(p.Rejected,'selected native toolchain changed'):
    p.tool_manifest()
 def test_recorded_normal_pins_follow_selected_profile_and_reject_mixed_roles(self):
  lock=json.loads((c.ROOT/'toolchain.lock.json').read_text())
  selection=c.native_selection(lock,'10.0.7')
  expected={**lock['tools'],**selection['tools']}
  files={str(c.resolve_tool_path(pin['path'])):pin['sha256'] for pin in expected.values()}
  with patch.object(c,'current_native_selection',return_value=selection),patch.object(c,'NATIVE_VERSION','10.0.7'):
   self.assertEqual(p.selected_tool_pins(),expected)
   p.check_recorded_tool_pins({'files':files})
   for role in ('kicad_cli','kicad_python','pcbnew'):
    mixed=dict(files);mixed.pop(selection['tools'][role]['path']);old=lock['tools'][role];mixed[old['path']]=old['sha256']
    with self.subTest(role=role),self.assertRaisesRegex(p.Rejected,'recorded tool pins'):
     p.check_recorded_tool_pins({'files':mixed})
   extra={**files,lock['tools']['kicad_cli']['path']:lock['tools']['kicad_cli']['sha256']}
   with self.assertRaises(p.Rejected):p.check_recorded_tool_pins({'files':extra})
 def test_uncached_negative_reader_refuses_selection_drift_before_evidence(self):
  with patch.object(c,'current_native_selection',side_effect=ValueError('changed profile')):
   with self.assertRaisesRegex(p.Rejected,'selected native toolchain changed'):
    p._check_result_uncached('/not-read/result.json',_rejected_attempt=True)
if __name__=='__main__':unittest.main()
