"""Pure reporting controls, including stored synthetic JSON receipts. Not native evidence."""
import importlib.util,json,unittest
from pathlib import Path
p=Path(__file__).with_name('generate.py');spec=importlib.util.spec_from_file_location('index_draft',p);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
class ReportingControls(unittest.TestCase):
 def test_gain_loss_and_both_ties(self):
  for first,last,key,delta in [(False,True,'gained',1),(True,False,'lost',-1),(True,True,'tied_valid',0),(False,False,'tied_invalid',0)]:
   outcome,row=g.classify(first,last,'board');self.assertEqual(outcome,key);self.assertEqual(row['completion_difference'],delta)
 def test_truthy_nonboolean_does_not_invent_gain(self):
  for bad in (1,0,None,'true'):
   with self.assertRaises(ValueError):g.classify(False,bad,'board')
 def test_duplicate_receipt_key_rejected(self):
  with self.assertRaises(ValueError):json.loads('{"accepted":false,"accepted":true}',object_pairs_hook=g.pairs)
 def test_nonfinite_receipt_rejected(self):
  for token in ('NaN','Infinity','-Infinity'):
   with self.assertRaises(ValueError):json.loads(token,parse_constant=g.nonfinite)
 def test_boolean_or_negative_or_nonfinite_cost_rejected(self):
  for bad in (True,-1,float('nan'),float('inf')):
   with self.assertRaises(ValueError):g.amount(bad)
 def test_missing_explicit_pair_input_fails_before_optional_use(self):
  with self.assertRaisesRegex(ValueError,'missing'):g.Reader().read(Path(__file__).with_name('NOT_A_REAL_PAIR.json'))

# Real JSON files in isolated synthetic populations, never native or corpus boards.
import copy,tempfile
from unittest.mock import patch
class StoredReceiptControls(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name).resolve();self.patch=patch.object(g,'ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)
  boards=[];support=[]
  for i,name in enumerate([g.BOARD]+[f'boards/board-{i}.kicad_pcb'for i in range(13)]):
   raw=f'synthetic board {i}'.encode();path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
   boards.append({'board':name,'source_sha256':g.sha(raw),'static_eligible_at_recorded_gate':i<3,'unsupported_reason':None if i<3 else 'unsupported','static_evidence':'historical'})
   support.append({'board':name,'sha256':g.sha(raw),'full_preflight_eligible':i<3,'full_preflight_reason':'unsupported'})
  self.write(g.OLD,{'input_files':{},'boards':boards,'counts':{'inputs_with_at_least_one_recorded_accepted_routing_policy':2,'total_inputs':14},'pair_outcomes':{'retained':'unchanged'},'limits':[]})
  self.write(g.GATE,{'boards':support,'total':14,'full_preflight_eligible':3,'all_inputs_unchanged':True,'pipeline_sha256':'a'*64})
  self.tools={'git_head':'a'*40,'files':{'tool':'b'*64},'implementation_sha256':{'core.py':'c'*64}}
  self.freeze={'tools':self.tools,'files_sha256':{'core.py':'c'*64},'protocol_sha256':'d'*64,'helper_files':{'helper':'helper.py'}}
  self.source_hashes={Path(g.BOARD).name:boards[0]['source_sha256'],'project.kicad_pro':'e'*64}
  self.fixture=self.receipt(g.POLICIES[1],True);self.fixture['source_hashes']={'fixture.kicad_pcb':'f'*64};self.fixture['source']='owned/fixture.kicad_pcb'
  self.fixture_path=self.write('fixture/result.json',self.fixture)
 def write(self,path,value):
  target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(value,allow_nan=False));return target
 def receipt(self,policy,accepted):
  return {'diagnostic_schema':1,'production_qualified':False,'comparison_eligible':False,'policy':policy,'routing_accepted':accepted,'status':'diagnostic_accepted'if accepted else 'drc_rejected','source':g.BOARD,'source_hashes':copy.deepcopy(self.source_hashes),'freeze':copy.deepcopy(self.freeze),'tools':copy.deepcopy(self.tools),'engine_profile':'completion-only','adapter':'both','budget_seconds':100,'cpu_budget_seconds':100,'wall_seconds':10.,'total_cpu_seconds':6.,'parent_cpu_seconds':2.,'waited_child_cpu_seconds':4.,'within_budget':True,'candidate':'candidate/board.kicad_pcb','candidate_sha256':'b'*64,'steps':[{'cpu_seconds':3.,'monitor_cpu_seconds':1.}],'native':{'opens':0 if accepted else 2,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':[]if accepted else [{'type':'unconnected_items'}]},'metrics':{'track_length_mm':23.,'vias':1}}
 def pair(self,first=False,last=True):
  self.arm=[self.receipt(policy,accepted)for policy,accepted in zip(g.POLICIES,(first,last))]
  fixture_sha=g.sha(self.fixture_path.read_bytes())
  self.protocol={'source':g.BOARD,'source_hashes':copy.deepcopy(self.source_hashes),'frozen':copy.deepcopy(self.freeze),'fixture_sha256':fixture_sha,'identical_assigned_seconds':100,'protocol':{'fixed_order':g.POLICIES,'wall_seconds_per_arm':120,'cpu_seconds_per_arm':120,'qualification_fixture':{'source_hashes':self.fixture['source_hashes']}}}
  self.summary={'kind':'diagnostic_floor_placement_pair','production_qualified':False,'comparison_eligible':True,'status':'completed','raw_tasks_equivalent':True,'shared_wall_seconds':2.,'shared_cpu_seconds':1.,'results':[]}
  for arm in self.arm:
   self.summary['results'].append({'policy':arm['policy'],'accepted':arm['routing_accepted'],'verified_native_accepted':arm['routing_accepted'],'status':arm['status'],'diagnostic_verified':True,'within_charged_caps':True,'charged_wall_seconds':14.,'charged_cpu_seconds':8.,'invocation_wall_seconds':12.,'invocation_cpu_seconds':7.,**{k:arm['native'][k]for k in ('opens','blocking','warnings','exclusions')},'length_mm':arm['metrics']['track_length_mm'],'vias':arm['metrics']['vias']})
  self.summary['comparison']={'floor_accepted':first,'placement_accepted':last,'completion_difference':int(last)-int(first),**{key+'_delta':self.arm[1]['native'][key]-self.arm[0]['native'][key]for key in ('opens','blocking','warnings','exclusions')}}
  if first and last:self.summary['comparison'].update(length_delta_mm=0.,via_delta=0)
  return self.save_pair()
 def save_pair(self):
  self.write('pair/protocol.json',self.protocol);self.summary['protocol_sha256']=g.sha((self.root/'pair/protocol.json').read_bytes())
  for i,arm in enumerate(self.arm):
   path=self.write(f'pair/arm-{i}/result.json',arm);self.summary['results'][i]['receipt_sha256']=g.sha(path.read_bytes())
  return self.write('pair/summary.json',self.summary)
 def result(self):return g.build([self.fixture_path],self.save_pair())
 def test_early_failed_fixture_without_native_stays_pending_and_preserves_cost(self):
  d={'diagnostic_schema':1,'production_qualified':False,'comparison_eligible':False,'policy':g.POLICIES[1],'routing_accepted':False,'status':'rejected','error':'pre-engine parser failure','wall_seconds':3.1,'total_cpu_seconds':1.9}
  path=self.write('early/result.json',d);r=g.build([path]);self.assertEqual(len(r['boards']),14);self.assertEqual(r['placement_diagnostic_pair_outcomes']['status'],'pending_no_pair_supplied');self.assertEqual(r['owned_qualification_controls'][0]['recorded_receipt'],d);self.assertEqual(r['counts']['inputs_with_at_least_one_recorded_accepted_production_policy'],2)
 def test_completed_gain_loss_and_ties_from_bound_arm_receipts(self):
  for first,last,key in [(False,True,'gained'),(True,False,'lost'),(True,True,'tied_valid'),(False,False,'tied_invalid')]:
   with self.subTest(first=first,last=last):
    self.pair(first,last);r=self.result();o=r['placement_diagnostic_pair_outcomes'];self.assertEqual(o[key],[g.BOARD]);self.assertEqual(len(o['unevaluated']),13);self.assertEqual('length_delta_mm'in o['comparison'],first and last);self.assertEqual(r['counts']['inputs_with_at_least_one_recorded_accepted_production_policy'],2)
 def test_invalidated_pair_cannot_report_gain_but_retains_raw_accepted_diagnostic(self):
  self.pair();self.summary.update(status='invalidated',comparison_eligible=False,comparison=None,reason='late stale evidence')
  for row in self.summary['results']:row.update(accepted=False,verified_native_accepted=False)
  r=self.result();o=r['placement_diagnostic_pair_outcomes'];self.assertEqual(o['gained'],[]);self.assertIsNone(o['comparison']);self.assertEqual(len(o['unevaluated']),14);self.assertEqual(r['diagnostic_accepted_inputs'],[])
 def test_summary_cannot_upgrade_or_change_bound_native_arm(self):
  mutations=[('verdict',lambda:self.arm[1].update(routing_accepted=False)),('status',lambda:self.arm[1].update(status='drc_rejected')),('counter',lambda:self.arm[1]['native'].update(opens=9)),('length',lambda:self.arm[1]['metrics'].update(track_length_mm=24.)),('via',lambda:self.arm[1]['metrics'].update(vias=2)),('counter_boolean',lambda:self.arm[1]['native'].update(opens=False))]
  for name,mutation in mutations:
   with self.subTest(name=name):
    self.pair();mutation()
    with self.assertRaises(ValueError):self.result()
 def test_accepted_fixture_must_have_clean_native_status_and_consistent_budget(self):
  mutations=[lambda d:d.update(status='rejected'),lambda d:d['native'].update(findings=[{'type':'bad'}]),lambda d:d['native'].update(opens=1),lambda d:d.update(wall_seconds=101),lambda d:d.update(total_cpu_seconds=99),lambda d:d.update(within_budget=False)]
  for mutation in mutations:
   d=copy.deepcopy(self.fixture);mutation(d);path=self.write('bad-fixture/result.json',d)
   with self.assertRaises(ValueError):g.build([path])
 def test_pair_cannot_change_full_source_tools_freeze_or_charged_cost(self):
  mutations=[('project',lambda:self.arm[1]['source_hashes'].update({'project.kicad_pro':'f'*64})),('tools',lambda:self.arm[1]['tools'].update(git_head='f'*40)),('code',lambda:self.arm[1]['freeze']['files_sha256'].update({'core.py':'f'*64})),('fixture_code',lambda:self.protocol['frozen']['files_sha256'].update({'core.py':'f'*64})),('charged',lambda:self.summary['results'][1].update(charged_wall_seconds=13.)),('assigned',lambda:self.arm[1].update(budget_seconds=90,cpu_budget_seconds=90)),('invocation',lambda:self.summary['results'][1].update(invocation_cpu_seconds=1,charged_cpu_seconds=2))]
  for name,mutation in mutations:
   with self.subTest(name=name):
    self.pair();mutation()
    with self.assertRaises(ValueError):self.result()

if __name__=='__main__':unittest.main()
