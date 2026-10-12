"""Synthetic floor consistency and publication controls; no native execution."""
import copy,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,sexpr as sx,board_floor as g,floor_route as f
from autorouter.floor_context import LIMITS
ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'tests/fixtures/board-floor'

class FloorReceipt(unittest.TestCase):
 def setUp(self):
  (ROOT/'.cache').mkdir(exist_ok=True);self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'.cache');self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);self.src=self.root/'source';self.src.mkdir()
  for name in ('fixture.kicad_pcb','fixture.kicad_pro'):shutil.copy2(FIX/name,self.src/name)
  shutil.copytree(FIX/'_licenses',self.src/'_licenses')
  self.source=self.src/'fixture.kicad_pcb';self.original=p.preflight(self.source);self.hashes=p.tree_hash(self.src)
  self.out=self.root/'run';self.out.mkdir();self.candidate=self.out/'candidate/fixture.kicad_pcb';self.receipt=self.out/'result.json'
  for name in ('snapshot','candidate','floor-export-input'):shutil.copytree(self.src,self.out/name)
  self.task=g.task_from_source(self.original);self.exported=self.out/'floor-export-input/fixture.kicad_pcb';sx.write(self.exported,self.task)
  raw=(FIX/'native.dsn').read_bytes();(self.out/'native.dsn').write_bytes(raw)
  def context(name,board,mode,dsn=None):
   native=json.loads((FIX/name).read_text());inventory=p.tree_hash(board.parent)
   native.update(source=str(board),board_sha256=p.sha(board),project_sha256=p.sha(board.with_suffix('.kicad_pro')),dsn_sha256=dsn,mode=mode,limits=LIMITS,input_hashes_before=inventory,input_hashes_after=inventory,obstacles=[])
   return native
  native=context('export-context.json',self.exported,'export',g.sha(raw));p.save_json(self.out/'floor-export-context.json',native)
  guided,contract=f.policy_contract(raw,native,self.source.with_suffix('.kicad_pro').read_bytes(),self.task,self.hashes)
  p.save_json(self.out/'floor-policy.json',contract);(self.out/'floor-guided.dsn').write_bytes(guided);(self.out/'task.dsn').write_bytes(g.adapter_bytes(guided,[]))
  shutil.copy2(FIX/'candidate.kicad_pcb',self.candidate)
  final=context('final-context.json',self.candidate,'final');p.save_json(self.out/'floor-final-context.json',final)
  ctx=g.qualify(json.loads(self.candidate.with_suffix('.kicad_pro').read_text()),final,self.task)
  p.save_json(self.out/'floor-final-audit.json',{'candidate_sha256':p.sha(self.candidate),'native_context_sha256':p.sha(self.out/'floor-final-context.json'),'generated':g.audit_generated_routes(sx.read(self.candidate),ctx),'native_routes':g.audit_native_routes(sx.read(self.candidate),final)})
  shutil.copytree(self.candidate.parent,self.out/'final-drc-input');shutil.copy2(FIX/'final-drc.json',self.out/'final-drc.json')
  metrics={'version':'10.0.0','vias':1,'track_length_mm':60.};p.save_json(self.out/'metrics.json',metrics)
  before=p.tree_hash(self.candidate.parent);binding={'source':str(self.candidate),'input':str(self.out/'final-drc-input/fixture.kicad_pcb'),'saved':False,'before':before,'after':before};p.save_json(self.out/'final-drc-binding.json',binding)
  settings=p.engine_profile_settings('completion-only',110,strict_class_targets=True);settings.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
  commands={'source-drc':['synthetic source stage'],'floor-export':f.context_argv('export',self.exported,self.out/'floor-export-context.json',self.out/'native.dsn'),
   'engine':f.engine_argv(self.out,settings['argv']),'import':[*f.SANDBOX,str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py'),'import',str(self.candidate),str(self.out/'imported.kicad_pcb'),str(self.out/'routes.ses')],
   'refill-drc':['synthetic refill stage'],'floor-final':f.context_argv('final',self.candidate,self.out/'floor-final-context.json'),
   'final-drc':[*f.SANDBOX,str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(self.out/'final-drc.json'),binding['input']],
   'metrics':[*f.SANDBOX,str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py'),'metrics',str(self.candidate),str(self.out/'metrics.json')]}
  # Synthetic process/transport fixtures, not a new native execution claim.
  shutil.copy2(self.candidate,self.out/'imported.kicad_pcb');(self.out/'routes.ses').write_text('(session synthetic)\n')
  shutil.copytree(self.src,self.out/'source-drc-input');shutil.copytree(self.candidate.parent,self.out/'refill')
  prerefill=p.transplant_routes(self.task,sx.read(self.out/'imported.kicad_pcb'))
  stage_bindings={}
  for name,source,input_path,saved,inputs in [
    ('source-drc',self.out/'snapshot/fixture.kicad_pcb',self.out/'source-drc-input/fixture.kicad_pcb',False,self.hashes),
    ('refill-drc',self.out/'refill/fixture.kicad_pcb',self.out/'refill/fixture.kicad_pcb',True,{**self.hashes,'fixture.kicad_pcb':g.sha((sx.dump(prerefill)+'\n').encode())})]:
   shutil.copy2(FIX/'final-drc.json',self.out/(name+'.json'))
   stage_bindings[name]={'source':str(source),'input':str(input_path),'saved':saved,'before':inputs,'after':p.tree_hash(input_path.parent)}
   p.save_json(self.out/(name+'-binding.json'),stage_bindings[name])
   commands[name]=[*f.SANDBOX,str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(self.out/(name+'.json')),*(['--save-board'] if saved else []),str(input_path)]
  steps=[]
  for name,argv in commands.items():
   step={'name':name,'argv':argv,'cwd':str(self.out),'status':'success','exit_code':0,'cleanup_complete':True,'wall_seconds':.1,'cpu_seconds':.05,'monitor_cpu_seconds':0.}
   p.save_json(self.out/(name+'-process.json'),step)
   if name=='final-drc':step=dict(step,validated_input_sha256=p.sha(self.candidate),emitted_candidate=str(self.candidate))
   if name in stage_bindings:step=dict(step,validated_input_sha256=stage_bindings[name]['before']['fixture.kicad_pcb'],emitted_candidate=stage_bindings[name]['source'])
   steps.append(step)
  (self.out/'code').mkdir();implementation={}
  for path in (ROOT/'autorouter').glob('*.py'):shutil.copy2(path,self.out/'code'/path.name);implementation['autorouter/'+path.name]=p.sha(path)
  pins=json.loads((ROOT/'toolchain.lock.json').read_text())['tools']
  self.data={'schema':2,'input_policy':f.POLICY,'accepted':True,'status':'routing_accepted','baseline':'completion_only_probe','adapter':'both','engine_profile':'completion-only','scoring_variant':None,
   'source':str(self.source),'source_hashes':self.hashes,'scope':'whole_board_unlocked_routing','candidate':str(self.candidate),'candidate_sha256':p.sha(self.candidate),'task_sha256':p.sha(self.exported),
   'native_dsn_sha256':g.sha(raw),'floor_guided_dsn_sha256':g.sha(guided),'task_dsn_sha256':p.sha(self.out/'task.dsn'),'floor_policy':{'file':'floor-policy.json','sha256':p.sha(self.out/'floor-policy.json')},
   'engine_budget':settings,'native_report_sha256':p.sha(self.out/'final-drc.json'),'native':p.parse_report(self.out/'final-drc.json',self.source.name),'invariants_unchanged':True,'whole_project_drc_clean':True,'metrics':metrics,'steps':steps,
   'wall_seconds':2.,'budget_seconds':120.,'cpu_budget_seconds':120.,'parent_cpu_seconds':.1,'child_cpu_seconds':.4,'monitor_cpu_seconds':0.,'total_cpu_seconds':.5,
   'tools':{'kicad':'10.0.0','implementation_sha256':implementation,'files':{str(p.c.resolve_tool_path(pin['path'])):pin['sha256'] for pin in pins.values()}}}
  self.data['source_drc']=p.parse_report(self.out/'source-drc.json',self.source.name)
  self.save()
 def save(self):self.data['floor_evidence_hashes']=f.evidence_inventory(self.out);self.receipt.write_text(json.dumps(self.data))
 def check(self):return p.check_result(self.receipt)
 def mutate(self,name,fn):
  path=self.out/name;data=json.loads(path.read_text());fn(data);path.write_text(json.dumps(data));self.save()
 def test_complete_synthetic_floor_receipt(self):self.assertEqual(self.check()['input_policy'],f.POLICY)
 def test_policy_downgrade(self):
  for key,value in [('input_policy',None),('schema',1),('schema',None),('input_policy','native'),('input_policy','board-floors-v2')]:
   with self.subTest(key=key,value=value):
    old=copy.deepcopy(self.data)
    if value is None:self.data.pop(key)
    else:self.data[key]=value
    self.save()
    with self.assertRaises(p.Rejected):self.check()
    self.data=old
 def test_floor_cannot_be_C(self):
  self.data.update(baseline='C-prototype',strategy='fake');self.save()
  with self.assertRaises(p.Rejected):self.check()
 def test_missing_contract_or_guided(self):
  for name in ('floor-policy.json','floor-guided.dsn'):
   path=self.out/name;raw=path.read_bytes();path.unlink();self.save()
   with self.assertRaises((p.Rejected,FileNotFoundError)):self.check()
   path.write_bytes(raw)
 def test_rehashed_guidance_and_adapter_rule_tamper(self):
  for name,field in [('floor-guided.dsn','floor_guided_dsn_sha256'),('task.dsn','task_dsn_sha256')]:
   path=self.out/name;raw=path.read_bytes();self.assertIn(b'(width 300)',raw);path.write_bytes(raw.replace(b'(width 300)',b'(width 200)'));self.data[field]=p.sha(path);self.save()
   with self.assertRaises((p.Rejected,ValueError)):self.check()
   path.write_bytes(raw);self.data[field]=p.sha(path)
 def test_context_floor_tamper(self):
  self.mutate('floor-export-context.json',lambda d:d['floors_nm'].update(min_track_width=200000))
  with self.assertRaises((p.Rejected,ValueError)):self.check()
 def test_final_native_dimensions(self):
  self.mutate('floor-final-context.json',lambda d:d['routes'][0].update(width_nm=200000))
  with self.assertRaises((p.Rejected,ValueError)):self.check()
 def test_final_project_binding(self):
  self.mutate('floor-final-context.json',lambda d:d.update(project_sha256='0'*64))
  with self.assertRaises(p.Rejected):self.check()
 def test_consistent_context_process_tamper(self):
  self.data['steps'][5]['argv']=['/usr/bin/true'];self.mutate('floor-final-process.json',lambda d:d.update(argv=['/usr/bin/true']))
  with self.assertRaises(p.Rejected):self.check()
 def test_engine_neckdown(self):
  self.data['engine_budget']['argv'].append('--router.automatic_neckdown=true');self.save()
  with self.assertRaises(p.Rejected):self.check()
 def test_unsupported_scope_before_work(self):
  for keep,adapter in [(True,'both'),(False,'none'),(False,'planes')]:
   with self.assertRaises(p.Rejected):p.route(self.source,self.root/'unused',120,keep,adapter,guidance_policy=f.POLICY)
 def test_unknown_guidance(self):
  with self.assertRaises(p.Rejected):p.route('missing','unused',guidance_policy='unknown')
 def test_locked_route(self):
  tree=copy.deepcopy(self.original);tree.append(['segment','locked'])
  with self.assertRaises(ValueError):g.task_from_source(tree)
 def test_literal_classes_not_weakened(self):
  import test_netclass as legacy
  _,_,project=legacy.fixtures()
  with self.assertRaises(ValueError):g.qualify_scope(project,self.task)
 def test_wrong_native_via_enum(self):
  native=json.loads((self.out/'floor-final-context.json').read_text());next(row for row in native['routes'] if row['kind']=='via')['via_type']=3
  with self.assertRaises(ValueError):g.audit_native_routes(sx.read(self.candidate),native)
 def test_handoff_blocked(self):
  from autorouter.handoff import review_copy
  with self.assertRaisesRegex(p.Rejected,'handoff'):review_copy(self.receipt,self.root/'gui')
  self.assertFalse((self.root/'gui').exists())

 def test_missing_transport_files(self):
  for name in ('routes.ses','imported.kicad_pcb'):
   path=self.out/name;raw=path.read_bytes();path.unlink();self.save()
   with self.assertRaises(p.Rejected):self.check()
   path.write_bytes(raw)
 def test_refill_process_cannot_be_arbitrary(self):
  self.data['steps'][4]['argv']=['/usr/bin/true'];self.mutate('refill-drc-process.json',lambda d:d.update(argv=['/usr/bin/true']))
  with self.assertRaises(p.Rejected):self.check()
 def test_refill_before_binding_tamper(self):
  self.mutate('refill-drc-binding.json',lambda d:d['before'].update({'fixture.kicad_pcb':'0'*64}))
  with self.assertRaises(p.Rejected):self.check()
 def test_native_float_dimension_rejected(self):
  native=json.loads((self.out/'floor-final-context.json').read_text());native['routes'][0]['width_nm']=float(native['routes'][0]['width_nm'])
  with self.assertRaises(ValueError):g.audit_native_routes(sx.read(self.candidate),native)
 def test_final_transplant_reconstruction(self):
  tree=sx.read(self.out/'imported.kicad_pcb');sx.one(p.routes(tree)[0],'width')[1]='0.4';sx.write(self.out/'imported.kicad_pcb',tree);self.save()
  with self.assertRaises(p.Rejected):self.check()

 def test_floor_claim_spliced_into_legacy_rejected(self):
  legacy={'schema':1,'accepted':True,'floor_guided_dsn_sha256':'0'*64}
  empty=self.root/'empty';empty.mkdir()
  with self.assertRaises(p.Rejected):f.receipt_policy(legacy,empty)
 def test_empty_SES_rejected(self):
  (self.out/'routes.ses').write_bytes(b'');self.save()
  with self.assertRaises(p.Rejected):self.check()
 def test_export_pad_mapping_reordered_net_rejected(self):
  self.mutate('floor-export-context.json',lambda d:d['pads'][0].update(net='UNKNOWN'))
  with self.assertRaises((ValueError,p.Rejected)):self.check()
 def test_original_context_raw_preference_not_floor_relabelled(self):
  self.mutate('floor-export-context.json',lambda d:d['nets'][0].update(width_nm=300000))
  with self.assertRaises((ValueError,p.Rejected)):self.check()
 def test_new_geometry_policy_requires_actual_derived_target(self):
  native=json.loads((self.out/'floor-final-context.json').read_text());project=json.loads(self.source.with_suffix('.kicad_pro').read_text())
  context=g.qualify(project,native,self.task)
  for key,value,kind in [('width','0.2','segment'),('size','1.4','via'),('drill','0.4','via')]:
   tree=sx.read(self.candidate);sx.one(next(r for r in p.routes(tree) if r[0]==kind),key)[1]=value
   with self.assertRaises(ValueError):g.audit_generated_routes(tree,context)
 def test_cli_dispatches_explicit_policy(self):
  import io
  from contextlib import redirect_stdout
  from autorouter import __main__ as cli
  with patch('sys.argv',['autorouter','route','board','--output','out','--adapter','both','--guidance','board-floors-v1']),patch.object(cli,'route',return_value={'accepted':False}) as route,redirect_stdout(io.StringIO()):
   self.assertEqual(cli.main(),2)
   self.assertEqual(route.call_args.kwargs['preference_overrides']['guidance'],'board-floors-v1')

 def test_matching_process_status_and_zero_exit_contradiction(self):
  self.data['steps'][1]['status']='nonzero_exit'
  self.mutate('floor-export-process.json',lambda d:d.update(status='nonzero_exit'))
  with self.assertRaisesRegex(p.Rejected,'process provenance'):self.check()

class Publication(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'.cache');self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name);self.report={'accepted':True,'status':'routing_accepted','whole_project_drc_clean':True}
 def run_publish(self,stable=lambda:None,remaining=lambda:1):
  with patch.object(p,'check_result',return_value={'current':True}):return f.publish(self.out,self.report,stable,lambda:None,remaining)
 def test_positive(self):self.assertTrue(self.run_publish()['accepted'])
 def test_cancel_after_write(self):
  original=p.save_json;called=[False]
  def save(path,data):
   original(path,data)
   if not called[0]:called[0]=True;raise KeyboardInterrupt
  with patch.object(p,'save_json',save):self.assertFalse(self.run_publish()['accepted'])
  self.assertFalse(json.loads((self.out/'result.json').read_text())['accepted'])
 def test_stale_after_write(self):
  calls=[0]
  def stable():
   calls[0]+=1
   if calls[0]>1:raise p.Rejected('stale')
  self.assertFalse(self.run_publish(stable=stable)['accepted'])
 def test_cap_after_write(self):self.assertFalse(self.run_publish(remaining=lambda:0)['accepted'])
 def test_two_write_failures_vacate_positive(self):
  original=p.save_json
  def save(path,data):original(path,data);path.with_suffix('.json.partial').write_text('{"accepted":true}');raise OSError('injected')
  with patch.object(p,'save_json',save):self.assertFalse(self.run_publish()['accepted'])
  self.assertFalse((self.out/'result.json').exists());self.assertFalse((self.out/'result.json.partial').exists())
 def test_final_checker_mutation(self):
  def checker(path):
   data=json.loads(path.read_text());data['candidate_sha256']='changed';path.write_text(json.dumps(data));return {'current':True}
  with patch.object(p,'check_result',side_effect=checker):self.assertFalse(f.publish(self.out,self.report,lambda:None,lambda:None,lambda:1)['accepted'])
 def test_final_checker_rejects(self):
  with patch.object(p,'check_result',side_effect=p.Rejected('mismatch')):self.assertFalse(f.publish(self.out,self.report,lambda:None,lambda:None,lambda:1)['accepted'])
 def test_boolean_tamper(self):
  self.assertNotEqual(f.canonical({'accepted':True}),f.canonical({'accepted':1}))

if __name__=='__main__':unittest.main()
