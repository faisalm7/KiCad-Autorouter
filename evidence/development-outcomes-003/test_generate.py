"""Pure stored-receipt falsifiers. Synthetic files are never native evidence."""
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('outcomes003',Path(__file__).with_name('generate.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)

class Scalars(unittest.TestCase):
 def test_duplicate_and_nonfinite_json(self):
  for raw in ('{"x":1,"x":2}','NaN','Infinity','-Infinity'):
   with self.assertRaises(ValueError):json.loads(raw,object_pairs_hook=g.pairs,parse_constant=g.nonfinite)
 def test_strict_measurements(self):
  for value in (True,-1,float('nan'),float('inf')):
   with self.assertRaises(ValueError):g.amount(value)
  for value in (True,1.0,-1):
   with self.assertRaises(ValueError):g.count(value)
 def test_gain_loss_ties_quality_guard(self):
  for a,b,category in ((False,True,'gained'),(True,False,'lost'),(False,False,'tied_invalid'),(True,True,'tied_valid')):
   first={'policy':'a','accepted':a,'opens':0,'blocking':0,'warnings':1,'exclusions':0,'length_mm':10.,'vias':1};last={**first,'policy':'b','accepted':b,'length_mm':12.,'vias':2}
   key,result=g.compare(first,last);self.assertEqual(key,category);self.assertEqual(result['completion_difference'],int(b)-int(a));self.assertEqual('length_delta_mm'in result,a and b)
 def test_truthy_acceptance_rejected(self):
  with self.assertRaises(ValueError):g.boolean(1)
 def test_missing_explicit_file(self):
  with self.assertRaises(ValueError):g.Reader().read(Path(__file__).with_name('not-a-real-run.json'))

class StoredFiles(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
  self.override=patch.object(g,'ROOT',self.root);self.override.start();self.addCleanup(self.override.stop)
  boards=[]
  for i,name in enumerate([g.BOARD]+[f'boards/b{i}.kicad_pcb'for i in range(13)]):
   self.raw(name,f'synthetic-{i}'.encode());boards.append({'board':name,'source_sha256':g.sha(f'synthetic-{i}'.encode()),'static_eligible_at_recorded_gate':i<3,'unsupported_reason':None if i<3 else'unsupported','static_evidence':'recorded-gate'})
  self.raw(Path(g.BOARD).parent/'multichannel_mixer.kicad_pro',b'{}')
  self.old={'schema':2,'boards':boards,'counts':{'acquired_boards':14,'complete_inputs':7,'incomplete_inputs':7,'recorded_static_eligible':3,'recorded_static_unsupported':11,'inputs_with_at_least_one_recorded_accepted_production_policy':2,'inputs_with_recorded_accepted_placement_diagnostic':0},'input_files':{},'diagnostic_accepted_inputs':[],'limits':[],'owned_qualification_controls':[{'historical':'preserved'}]}
  self.write(g.OLD,self.old)
  self.fixture_source=self.raw('owned/fixture.kicad_pcb',b'owned-synthetic');self.raw('owned/fixture.kicad_pro',b'{}')
  self.declared={'schema':2,'fixed_order':g.POLICIES,'wall_seconds_per_arm':120,'cpu_seconds_per_arm':120,'profile':'completion-only','adapter':'both','strict_generated_dimensions':True,'search_parameters':g.PARAMETERS,'qualification_fixture':{'source_hashes':self.tree(self.fixture_source.parent),'required_policy':g.POLICIES[2]}}
  self.protocol_bytes=json.dumps(self.declared).encode();self.files={'experiments/native_combined.py':g.sha(b'helper'),'experiments/protocol.json':g.sha(self.protocol_bytes)}
  self.tools={'git_head':'a'*40,'files':{'/Applications/KiCad/kicad-cli':'b'*64},'implementation_sha256':{}}
  self.freeze={'tools':self.tools,'files_sha256':self.files,'protocol_sha256':g.sha(self.protocol_bytes),'helper_files':{'native_combined.py':'experiments/native_combined.py','protocol.json':'experiments/protocol.json'}}
  self.fixture=self.receipt('fixture',self.fixture_source,2,True);self.fixture_path=self.write('fixture/result.json',self.fixture)
  self.make_batch()
 def raw(self,path,value):
  path=Path(path);path=path if path.is_absolute()else self.root/path;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value);return path
 def write(self,path,value):return self.raw(path,json.dumps(value,allow_nan=False).encode())
 def tree(self,path):return {str(x.relative_to(path)):g.sha(x.read_bytes())for x in sorted(path.rglob('*'))if x.is_file()}
 def receipt(self,relative,source,index,accepted):
  out=self.root/relative;name=source.name;source_hashes=self.tree(source.parent)
  for filename in source_hashes:
   self.raw(out/'snapshot'/filename,(source.parent/filename).read_bytes());self.raw(out/'candidate'/filename,(source.parent/filename).read_bytes());self.raw(out/'final-drc-input'/filename,(source.parent/filename).read_bytes())
  for filename in self.files:self.raw(out/'code/source'/filename,self.protocol_bytes if filename.endswith('protocol.json')else b'helper')
  self.raw(out/'code/native_combined.py',b'helper')
  findings=[]if accepted else[{'type':'clearance','severity':'error','items':[]}]
  raw={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':name,'included_severities':['error','warning','exclusion'],'ignored_checks':[],'unconnected_items':[],'schematic_parity':[],'violations':findings}
  self.write(out/'final-drc.json',raw);native=g.ns.parse_data(json.loads((out/'final-drc.json').read_text()),name);metrics={'version':'10.0.0','vias':1,'track_length_mm':10.}
  self.write(out/'metrics.json',metrics)
  candidate=out/'candidate'/name;binding={'source':str(candidate),'input':str(out/'final-drc-input'/name),'saved':False,'before':source_hashes,'after':source_hashes};self.write(out/'final-drc-binding.json',binding)
  steps=[]
  for stage in sorted(g.STEPS):
   code=5 if stage=='final-drc'and findings else 0
   record={'name':stage,'cpu_seconds':.1,'monitor_cpu_seconds':0.,'exit_code':code,'status':'success'if code==0 else'nonzero_exit','cleanup_complete':True,'argv':['synthetic-stage']}
   if stage=='final-drc':record['argv']=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)','/Applications/KiCad/kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(out/'final-drc.json'),str(out/'final-drc-input'/name)]
   self.write(out/(stage+'-process.json'),record);step=copy.deepcopy(record)
   if stage=='final-drc':step.update(validated_input_sha256=source_hashes[name],emitted_candidate=str(candidate))
   steps.append(step)
  chain={'search_parameters':g.PARAMETERS[index],'placement_removed_count':2}
  for key,file in [('native_dsn_sha256','native.dsn'),('floor_guided_sha256','floor-guided.dsn'),('placement_guided_sha256','placement-guided.dsn'),('pre_adapter_sha256','pre-adapter.dsn'),('task_dsn_sha256','task.dsn'),('search_guidance_sha256','search-guidance.json'),('floor_context_sha256','floor-export-context.json'),('area_context_sha256','area-context.json')]:self.raw(out/file,b'synthetic-chain');chain[key]=g.sha(b'synthetic-chain')
  return {'diagnostic_schema':2,'production_qualified':False,'comparison_eligible':False,'physical_electrical_validation':False,'policy':g.POLICIES[index],'search_parameters':g.PARAMETERS[index],'routing_accepted':accepted,'status':'diagnostic_accepted'if accepted else'drc_rejected','source':str(source),'source_hashes':source_hashes,'freeze':copy.deepcopy(self.freeze),'tools':copy.deepcopy(self.tools),'observer_sha256':g.sha(b'helper'),'engine_profile':'completion-only','adapter':'both','budget_seconds':100.,'cpu_budget_seconds':100.,'wall_seconds':10.,'total_cpu_seconds':6.,'parent_cpu_seconds':2.,'waited_child_cpu_seconds':4.,'within_budget':True,'candidate':str(candidate),'candidate_sha256':source_hashes[name],'steps':steps,'native':native,'native_report_sha256':g.sha((out/'final-drc.json').read_bytes()),'metrics':metrics,'chain':chain,'evidence_hashes':self.tree(out)}
 def make_batch(self,accepted=(False,True,False)):
  self.arms=[self.receipt(f'batch/arm-{i}',self.root/g.BOARD,i,a)for i,a in enumerate(accepted)]
  self.protocol={'source':str(self.root/g.BOARD),'source_hashes':self.tree((self.root/g.BOARD).parent),'fixture_receipt':str(self.fixture_path),'fixture_sha256':g.sha(self.fixture_path.read_bytes()),'frozen':copy.deepcopy(self.freeze),'protocol':copy.deepcopy(self.declared),'identical_assigned_seconds':100.}
  for file in self.files:self.raw('batch/code/'+file,self.protocol_bytes if file.endswith('protocol.json')else b'helper')
  for name in self.protocol['source_hashes']:self.raw('batch/source-project/'+name,((self.root/g.BOARD).parent/name).read_bytes())
  self.summary={'schema':2,'kind':'diagnostic_placement_search_three_arm','status':'completed','production_qualified':False,'comparison_eligible':True,'raw_tasks_equivalent':True,'shared_wall_seconds':2.,'shared_cpu_seconds':1.,'batch_wall_seconds':38.,'batch_cpu_seconds':22.,'results':[]}
  for arm in self.arms:self.summary['results'].append({'policy':arm['policy'],'accepted':arm['routing_accepted'],'verified_native_accepted':arm['routing_accepted'],'status':arm['status'],'diagnostic_verified':True,'within_charged_caps':True,'charged_wall_seconds':14.,'charged_cpu_seconds':8.,'invocation_wall_seconds':12.,'invocation_cpu_seconds':7.,'chain':copy.deepcopy(arm['chain']),**{key:arm['native'][key]for key in ('opens','blocking','warnings','exclusions')},'length_mm':arm['metrics']['track_length_mm'],'vias':arm['metrics']['vias']})
  self.summary['comparison']={key:g.compare(self.summary['results'][a],self.summary['results'][b])[1]for key,(a,b)in g.PAIRS.items()};self.save()
 def save(self):
  self.write('batch/protocol.json',self.protocol);self.summary['protocol_sha256']=g.sha((self.root/'batch/protocol.json').read_bytes())
  for i,arm in enumerate(self.arms):
   path=self.write(f'batch/arm-{i}/result.json',arm);self.summary['results'][i]['receipt_sha256']=g.sha(path.read_bytes())
  paths=[self.root/'fixture',self.fixture_source.parent,self.root/'batch/code',self.root/'batch/source-project']+[self.root/f'batch/arm-{i}'for i in range(3)]
  self.summary['completed_trees']={str(p):self.tree(p)for p in paths};return self.write('batch/summary.json',self.summary)
 def result(self):return g.build([self.fixture_path],self.save())
 def test_realistic_gain_loss_tie_full_denominator(self):
  r=self.result();self.assertEqual(len(r['boards']),14);self.assertEqual(sum(x['static_eligible_at_recorded_gate']for x in r['boards']),3);self.assertEqual(r['counts']['inputs_with_at_least_one_recorded_accepted_production_policy'],2);self.assertEqual(r['diagnostic_accepted_inputs'],[g.BOARD]);self.assertEqual(r['owned_qualification_controls'],self.old['owned_qualification_controls'])
  for key,category in [('margin_effect','gained'),('via_cost_effect','lost'),('combined_effect','tied_invalid')]:
   row=r['placement_search_three_arm_outcomes'][key];self.assertEqual(row[category],[g.BOARD]);self.assertEqual(len(row['unevaluated']),13);self.assertNotIn('length_delta_mm',row['comparison'])
 def test_early_fixture_failure_has_no_native_but_retains_cost(self):
  d=copy.deepcopy(self.fixture);d.pop('native');d.update(status='rejected',routing_accepted=False,error='pre-engine failure',wall_seconds=1.2,total_cpu_seconds=.8)
  path=self.write('early/result.json',d);r=g.build([path]);self.assertEqual(r['search_v2_owned_qualification_controls'][0]['recorded_receipt'],d);self.assertEqual(r['diagnostic_accepted_inputs'],[])
 def test_invalidated_experiment_cannot_inherit_raw_arm_acceptance(self):
  self.summary.update(status='invalidated',comparison_eligible=False,comparison=None,reason='late mutation')
  for row in self.summary['results']:row.update(accepted=False,verified_native_accepted=False)
  r=self.result();self.assertEqual(r['diagnostic_accepted_inputs'],[])
  for key in g.PAIRS:self.assertEqual(len(r['placement_search_three_arm_outcomes'][key]['unevaluated']),14)
 def test_consistently_rehashed_summary_cannot_change_counters_metrics_or_acceptance(self):
  for field,value in [('opens',1),('blocking',1),('warnings',9),('exclusions',1),('vias',2),('length_mm',11.),('accepted',False),('status','drc_rejected')]:
   with self.subTest(field=field):
    before=copy.deepcopy(self.summary['results'][1]);self.summary['results'][1][field]=value
    with self.assertRaises(ValueError):self.result()
    self.summary['results'][1]=before
 def test_raw_native_counter_and_critical_warning_mismatch_reject(self):
  out=self.root/'batch/arm-1';raw=json.loads((out/'final-drc.json').read_text());raw['violations']=[{'type':'padstack_invalid','severity':'warning','items':[]}];self.write(out/'final-drc.json',raw)
  arm=self.arms[1];arm['native_report_sha256']=g.sha((out/'final-drc.json').read_bytes());arm['evidence_hashes']['final-drc.json']=arm['native_report_sha256']
  with self.assertRaises(ValueError):self.result()
  arm['native']=g.ns.parse_data(json.loads((out/'final-drc.json').read_text()),Path(g.BOARD).name);self.summary['results'][1]['warnings']=1
  with self.assertRaises(ValueError):self.result()
 def test_full_source_code_protocol_and_parameters_guard(self):
  mutations=[lambda:self.arms[1]['source_hashes'].update({'bogus':'a'*64}),lambda:self.arms[1]['freeze']['files_sha256'].update({'bogus':'a'*64}),lambda:self.protocol['frozen']['tools'].update(git_head='b'*40),lambda:self.protocol['protocol'].update(search_parameters=[]),lambda:self.arms[1].update(search_parameters=g.PARAMETERS[0])]
  for action in mutations:
   before=copy.deepcopy((self.arms,self.protocol));action()
   with self.assertRaises(ValueError):self.result()
   self.arms,self.protocol=before
 def test_costs_caps_full_shared_and_cpu_sum_guard(self):
  mutations=[lambda:self.summary['results'][1].update(charged_cpu_seconds=7.),lambda:self.summary.update(batch_cpu_seconds=21.),lambda:self.summary['results'][1].update(invocation_cpu_seconds=1.,charged_cpu_seconds=2.),lambda:self.arms[1].update(total_cpu_seconds=99.),lambda:self.arms[1].update(budget_seconds=90.,cpu_budget_seconds=90.),lambda:self.summary.update(shared_wall_seconds=True)]
  for action in mutations:
   before=copy.deepcopy((self.arms,self.summary));action()
   with self.assertRaises(ValueError):self.result()
   self.arms,self.summary=before
 def test_missing_stale_candidate_or_metrics_fails(self):
  path=self.root/'batch/arm-1/candidate'/Path(g.BOARD).name;original=path.read_bytes();path.write_bytes(b'tampered')
  with self.assertRaises(ValueError):self.result()
  path.write_bytes(original);self.write('batch/arm-1/metrics.json',{'version':'10.0.0','vias':2,'track_length_mm':10.})
  with self.assertRaises(ValueError):self.result()
 def test_recorded_comparison_cannot_publish_invalid_quality_delta(self):
  self.summary['comparison']['margin_effect']['length_delta_mm']=1.
  with self.assertRaises(ValueError):self.result()
 def test_actual_file_change_during_publication_rejects(self):
  reader=g.Reader();path=self.root/g.BOARD;reader.bytes(path);path.write_bytes(b'changed')
  with self.assertRaises(ValueError):reader.stable()
 def test_new_inventory_file_before_publication_rejects(self):
  reader=g.Reader();directory=self.root/'owned';g.inventory(reader,directory,self.tree(directory));self.raw(directory/'unexpected',b'new')
  with self.assertRaises(ValueError):reader.stable()
 def test_process_exit_and_candidate_binding_guard(self):
  step=next(x for x in self.arms[1]['steps']if x['name']=='final-drc');record=json.loads((self.root/'batch/arm-1/final-drc-process.json').read_text());step['status']=record['status']='nonzero_exit';self.write('batch/arm-1/final-drc-process.json',record);self.arms[1]['evidence_hashes']['final-drc-process.json']=g.sha((self.root/'batch/arm-1/final-drc-process.json').read_bytes())
  with self.assertRaises(ValueError):self.result()

class BoundedIO(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
  self.override=patch.object(g,'ROOT',self.root);self.override.start();self.addCleanup(self.override.stop)
  self.a=self.root/'a';self.a.write_bytes(b'x')
 def test_final_oversized_stat_rejects_before_read(self):
  import os
  reader=g.Reader();reader.bytes(self.a);real_stat=Path.stat;opened=[];real_open=Path.open
  def virtual(path,*args,**kwargs):
   info=real_stat(path,*args,**kwargs)
   if path==self.a:
    values=list(info);values[6]=33*1024*1024;return os.stat_result(values)
   return info
  def track(path,*args,**kwargs):opened.append(path);return real_open(path,*args,**kwargs)
  with patch.object(Path,'stat',virtual),patch.object(Path,'open',track):
   with self.assertRaisesRegex(ValueError,'bounded'):reader.stable()
  self.assertEqual(opened,[])
 def test_read_caps_growth_even_if_initial_stat_small(self):
  reader=g.Reader();calls=[];real_open=Path.open
  class Growing:
   def __init__(self):self.stream=real_open(self_outer.a,'rb')
   def __enter__(self):return self
   def __exit__(self,*args):self.stream.close()
   def fileno(self):return self.stream.fileno()
   def read(self,size):calls.append(size);return b'x'*size
  self_outer=self
  with patch.object(g,'MAX_FILE_BYTES',4),patch.object(Path,'open',lambda *_a,**_k:Growing()):
   with self.assertRaisesRegex(ValueError,'grew'):reader.bytes(self.a)
  self.assertEqual(calls,[5]);self.assertEqual(reader.hashes,{})
 def test_unexpected_final_entry_rejects_before_next_iterator_item(self):
  reader=g.Reader();g.inventory(reader,self.root,{'a':g.sha(b'x')});b=self.root/'b';b.write_bytes(b'y');events=[]
  real_scandir=g.os.scandir
  with real_scandir(self.root)as stream:entries={e.name:e for e in stream}
  class Sentinel:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def __iter__(self):
    yield entries['a'];yield entries['b'];events.append('continued');raise AssertionError('continued beyond unexpected entry')
  with patch.object(g.os,'scandir',lambda _path:Sentinel()):
   with self.assertRaisesRegex(ValueError,'unexpected'):reader.stable()
  self.assertEqual(events,[])
 def test_initial_unknown_file_rejects_before_body_or_next_entry(self):
  b=self.root/'b';b.write_bytes(b'y');events=[]
  with g.os.scandir(self.root)as stream:entries={e.name:e for e in stream}
  class Sentinel:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def __iter__(self):
    yield entries['b'];events.append('continued');raise AssertionError('eager collection')
  with patch.object(g.os,'scandir',lambda _path:Sentinel()),patch.object(Path,'open',side_effect=AssertionError('unknown body read')):
   with self.assertRaisesRegex(ValueError,'unexpected'):g.inventory(g.Reader(),self.root,{'a':g.sha(b'x')})
  self.assertEqual(events,[])
 def test_empty_directories_consume_entry_budget(self):
  for i in range(3):(self.root/str(i)).mkdir()
  with patch.object(g,'MAX_TREE_ENTRIES',2):
   with self.assertRaisesRegex(ValueError,'entry count'):g.inventory(g.Reader(),self.root,{'a':g.sha(b'x')})
 def test_aggregate_and_recorded_file_caps(self):
  b=self.root/'b';b.write_bytes(b'yyy');expected={'a':g.sha(b'x'),'b':g.sha(b'yyy')}
  with patch.object(g,'MAX_TREE_BYTES',3):
   with self.assertRaisesRegex(ValueError,'byte bound'):g.inventory(g.Reader(),self.root,expected)
  with patch.object(g,'MAX_TREE_FILES',1):
   with self.assertRaisesRegex(ValueError,'bounded recorded'):g.inventory(g.Reader(),self.root,expected)
 def test_parser_consumes_data_without_file_access(self):
  data={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':'a.kicad_pcb','included_severities':['error','warning','exclusion'],'ignored_checks':[],'unconnected_items':[],'schematic_parity':[],'violations':[]}
  with patch.object(Path,'open',side_effect=AssertionError('parser reopened a file')),patch.object(Path,'read_text',side_effect=AssertionError('parser reopened a file')):
   result=g.ns.parse_data(data,'a.kicad_pcb')
  self.assertTrue(g.ns.native_accepted(result))
 def test_saved_hash_cannot_be_rebased_by_final_read(self):
  reader=g.Reader();reader.bytes(self.a);before=copy.deepcopy(reader.hashes);self.a.write_bytes(b'y')
  with self.assertRaisesRegex(ValueError,'changed'):reader.stable()
  self.assertEqual(reader.hashes,before)

if __name__=='__main__':unittest.main()
