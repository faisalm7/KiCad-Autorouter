"""Demonstrated KiCad10 metadata compatibility, without machining admission."""
import copy,json,tempfile,unittest
from pathlib import Path
from autorouter import pipeline as p,sexpr as sx

class PassiveRuleMetadata(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=p.c.ROOT/'tests');self.addCleanup(self.temp.cleanup)
  self.board=Path(self.temp.name)/'owned.kicad_pcb'
  self.tree=['kicad_pcb',['version','20260206'],['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal']]]
  self.project={'board':{'design_settings':{'rule_severities':{'missing_tuning_profile':'warning','track_on_post_machined_layer':'error'}}},'net_settings':{'classes':[{'name':'Default','tuning_profile':''}]},'tuning_profiles':{'meta':{'version':0},'tuning_profiles_impedance_geometric':[]}}
 def preflight(self,tree=None):
  sx.write(self.board,self.tree if tree is None else tree)
  file=self.board.with_suffix('.kicad_pro');file.write_text(json.dumps(self.project));before=file.read_bytes()
  try:return p.preflight(self.board)
  finally:self.assertEqual(file.read_bytes(),before)
 def test_passive_tuning_severities_preserved_but_machining_check_must_block(self):
  for value in ('error','warning','ignore'):
   self.project['board']['design_settings']['rule_severities']['missing_tuning_profile']=value
   self.preflight()
  for value in ('warning','ignore'):
   self.project['board']['design_settings']['rule_severities']['track_on_post_machined_layer']=value
   with self.assertRaisesRegex(p.Rejected,'core native check not blocking'):self.preflight()
 def test_active_missing_profile_and_definitions_never_become_supported(self):
  for key,value in [('tuning_profile','undefined'),('tuning_profile',None)]:
   self.project['net_settings']['classes'][0][key]=value
   with self.assertRaisesRegex(p.Rejected,'tuning profile'):self.preflight()
  self.project['net_settings']['classes'][0]['tuning_profile']=''
  self.project['tuning_profiles']['tuning_profiles_impedance_geometric']=[{'name':'Defined'}]
  with self.assertRaisesRegex(p.Rejected,'profile definitions'):self.preflight()
 def test_pad_via_machining_fields_block_even_zero_and_nested(self):
  for field in ('backdrill','tertiary_drill','front_post_machining','back_post_machining'):
   for row in ([field],[field,['size','0']]):
    for item in (['footprint','"Owned"',['pad','"1"','thru_hole','circle',row]],['via',row],['via',['padstack',row]]):
     with self.subTest(field=field,item=item):
      tree=copy.deepcopy(self.tree);tree.append(item)
      with self.assertRaisesRegex(p.Rejected,'backdrilled/post-machined'):self.preflight(tree)
  tree=copy.deepcopy(self.tree);tree.append(['footprint','"Owned"',['property','"Description"','"backdrill"']]);self.preflight(tree)
 def test_actual_findings_are_critical_even_if_native_warning_or_ignored(self):
  base={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':[]}
  for key in ('track_on_post_machined_layer','missing_tuning_profile'):
   for severity in ('warning','error','exclusion'):
    native=copy.deepcopy(base);native['findings']=[{'type':key,'severity':severity,'items':[]}]
    native['warnings']=int(severity=='warning');before=copy.deepcopy(native)
    self.assertFalse(p.native_accepted(native));self.assertEqual(native,before)
   native=copy.deepcopy(base);native['ignored_checks']=[{'key':key}];self.assertFalse(p.native_accepted(native))
 def test_unknown_and_malformed_severity_stay_rejected(self):
  for key,value in [('future_check','error'),('missing_tuning_profile',None),('track_on_post_machined_layer',True)]:
   self.project['board']['design_settings']['rule_severities'][key]=value
   with self.assertRaisesRegex(p.Rejected,'unknown rule severity'):self.preflight()
   self.project['board']['design_settings']['rule_severities'].pop(key)
 def test_generated_machining_via_rejects_before_native_or_dimension_audit(self):
  source=self.preflight();candidate=self.board.parent/'candidate'/'owned.kicad_pcb';candidate.parent.mkdir()
  tree=copy.deepcopy(source);tree.append(['via',['at','10','10'],['size','1'],['drill','0.5'],['layers','"F.Cu"','"B.Cu"'],['net','"N"'],['backdrill',['size','1.2'],['layers','"F.Cu"','"B.Cu"']]])
  self.assertEqual(p.immutable(tree),p.immutable(source));sx.write(candidate,tree)
  class NeverNative:
   calls=0
   def drc(self,*args,**kwargs):self.calls+=1;raise AssertionError('unsupported via reached native')
  job=NeverNative()
  with self.assertRaisesRegex(p.Rejected,'backdrilled/post-machined'):p.validate_candidate(job,source,candidate,p.tree_hash(self.board.parent),[])
  self.assertEqual(job.calls,0)
  with self.assertRaisesRegex(p.Rejected,'backdrilled/post-machined'):p.audit_route_dimensions(tree,[],{'nets':[]})
 def test_rehashed_receipt_cannot_admit_generated_machining_via(self):
  from test_result import ResultFreshnessTests
  case=ResultFreshnessTests(methodName='runTest');case.setUp();self.addCleanup(case.doCleanups)
  tree=sx.read(case.candidate);tree.append(['via',['at','10','10'],['size','1'],['drill','0.5'],['layers','"F.Cu"','"B.Cu"'],['net','"GND"'],['back_post_machining','counterbore',['size','1.2'],['depth','0.2']]])
  sx.write(case.candidate,tree);case.data['candidate_sha256']=p.sha(case.candidate);case.save_receipt()
  with self.assertRaisesRegex(p.Rejected,'backdrilled/post-machined'):p.check_result(case.receipt)

if __name__=='__main__':unittest.main()
