"""Authored syntax/receipt dispatch controls; no native routing proof."""
import copy,json,shutil,tempfile,time,unittest
from pathlib import Path
from unittest import mock
from autorouter import pipeline as p,preferences as pref,sexpr as sx
import tests.test_result as result_fixture
ROOT=Path(__file__).resolve().parents[1]
CONTEXT=('whole_board_unlocked_routing','native','source_all')
BOARD='(kicad_pcb (version 20240108) (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (49 "F.Fab" user)) (net 0 "") (net 1 "GND") (footprint "authored" (at 10 10) (uuid "745aa611-f567-4c65-9521-a39ed0952a59") (property "Reference" "J1" (layer "F.Fab"))) (segment (start 1 1) (end 2 1) (width 0.25) (layer "F.Cu") (net 1) (uuid "934a58bd-3229-4ecb-b5ca-3c26a44cfb8d")))\n'
PROJECT={'net_settings':{'classes':[{'name':'Default','track_width':0.25,'clearance':0.2,'via_diameter':0.8,'via_drill':0.4}],'netclass_patterns':[],'netclass_assignments':None},'board':{'design_settings':{'rules':{},'rule_severities':{},'drc_exclusions':[]}}}

class ScopeControls(unittest.TestCase):
 def setUp(self):
  scratch=ROOT/'.cache/legacy-scope-tests';scratch.mkdir(parents=True,exist_ok=True);tmp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(tmp.cleanup);self.root=Path(tmp.name);self.source=self.root/'a.kicad_pcb';self.source.write_text(BOARD);self.project=self.source.with_suffix('.kicad_pro');self.project.write_text(json.dumps(PROJECT));self.run=self.root/'run';self.run.mkdir()
 def reject(self,scope):
  with self.assertRaises(p.Rejected):p.preflight(self.source,task_scope=scope)
 def test_default_closed_and_exact_context_preserves_source(self):
  before=p.tree_hash(self.root)
  with self.assertRaisesRegex(p.Rejected,'unqualified board format'):p.preflight(self.source)
  self.assertEqual(p.preflight(self.source,task_scope=CONTEXT),sx.parse(BOARD));self.assertEqual(p.tree_hash(self.root),before)
  for value in (True,list(CONTEXT),{'accepted':True},CONTEXT[:2],CONTEXT+(None,),('whole_board_unlocked_routing','native',['F.Cu','B.Cu'])):
   with self.subTest(value=value):self.reject(value)
 def test_partial_selected_layer_guidance_and_other_versions_refuse(self):
  for value in [('partial_completion','native','source_all'),('selected_nets','native','source_all'),('whole_board_unlocked_routing','board-floors-v1','source_all'),('whole_board_unlocked_routing','placement-clearance-v1','source_all'),('whole_board_unlocked_routing','placement-search-v1','source_all'),('whole_board_unlocked_routing','native','F.Cu')]:
   with self.subTest(value=value):self.reject(value)
  for version in ('20221018','20240107','20240109'):
   self.source.write_text(BOARD.replace('20240108',version));self.reject(CONTEXT)
  for version in ('20241229','20260206'):
   self.source.write_text(BOARD.replace('20240108',version));self.assertEqual(sx.one(p.preflight(self.source),'version')[1],version)
 def test_actual_four_layers_classes_and_locked_source_refuse(self):
  self.source.write_text(BOARD.replace('(31 "B.Cu" signal)','(1 "In1.Cu" signal) (2 "In2.Cu" signal) (31 "B.Cu" signal)'));self.reject(CONTEXT);self.source.write_text(BOARD)
  for change in ('renamed','second','pattern','assignment'):
   value=copy.deepcopy(PROJECT)
   if change=='renamed':value['net_settings']['classes'][0]['name']='Power'
   elif change=='second':value['net_settings']['classes'].append({**value['net_settings']['classes'][0],'name':'Power'})
   elif change=='pattern':value['net_settings']['netclass_patterns']=[{'pattern':'*','netclass':'Default'}]
   else:value['net_settings']['netclass_assignments']={'GND':'Default'}
   self.project.write_text(json.dumps(value))
   with self.subTest(change=change):self.reject(CONTEXT)
  self.project.write_text(json.dumps(PROJECT));self.source.write_text(BOARD.replace('(width 0.25)','(width 0.25) (locked yes)'));self.reject(CONTEXT)
 def test_forged_whole_source_all_does_not_hide_markers_or_preset(self):
  base={'scope':CONTEXT[0]};self.assertEqual(p.task_scope_for_record(base,self.run),CONTEXT)
  for change in ('selected_file','layer_process','layer_budget','selected_preset','layer_preset','protected'):
   data=copy.deepcopy(base)
   if change=='selected_file':(self.run/'routing-scope-input.dsn').write_text('authored selected witness')
   elif change=='layer_process':(self.run/'engine-process.json').write_text(json.dumps({'argv':['--router.layers.active=F.Cu']}))
   elif change=='layer_budget':data['engine_budget']={'argv':['--router.layers.active=F.Cu']}
   elif change=='protected':data['protected_route_import']={}
   else:
    effective=dict(pref.DEFAULTS,profile='completion-only')
    if change=='selected_preset':effective.update(scope='selected_nets',nets=['GND'])
    else:effective['layers']=['F.Cu']
    data['routing_preferences']={'effective':effective}
   with self.subTest(change=change):self.reject(p.task_scope_for_record(data,self.run))
   for name in ('routing-scope-input.dsn','engine-process.json'):
    path=self.run/name
    if path.exists():path.unlink()
 def test_exact_zero_protection_strict_proof_does_not_hide_source_locks_or_bad_proofs(self):
  binding={'policy':'exact_non_uuid_lock_position_v2','matches':[],
           'transplanted_routes_sha256':'1'*64,'imported_sha256':'2'*64}
  data={'scope':CONTEXT[0],'protected_route_import':binding}
  context=p.task_scope_for_record(data,self.run)
  self.assertEqual(context,CONTEXT);self.assertEqual(p.preflight(self.source,task_scope=context),sx.parse(BOARD))
  for change in ('matches','policy','extra','missing','hash','hash_type'):
   bad=copy.deepcopy(data);proof=bad['protected_route_import']
   if change=='matches':proof['matches']=[{'original_uuid':'authored'}]
   elif change=='policy':proof['policy']=p.SELECTED_PROPOSAL_IMPORT_POLICY
   elif change=='extra':proof['selected_names']=[]
   elif change=='missing':del proof['imported_sha256']
   elif change=='hash':proof['imported_sha256']='not-a-digest'
   else:proof['imported_sha256']=True
   with self.subTest(change=change):self.reject(p.task_scope_for_record(bad,self.run))
  self.source.write_text(BOARD.replace('(width 0.25)','(width 0.25) (locked yes)'))
  self.reject(context)
 def test_preview_uses_resolved_choices_and_never_claims_native(self):
  from autorouter.__main__ import preview
  result=preview(self.source);self.assertTrue(result['static_preflight_passed']);self.assertFalse(result['native_validation_performed'])
  for overrides in ({'scope':'partial_completion'},{'scope':'selected_nets','nets':['GND'],'profile':'completion-only'},{'layers':['F.Cu'],'profile':'completion-only'},{'guidance':'board-floors-v1','adapter':'both'}):
   with self.subTest(overrides=overrides),self.assertRaises(p.Rejected):preview(self.source,overrides=overrides)
 def test_native_producer_resolves_selected_before_premature_whole_label(self):
  preset=self.root/'selected.json';preset.write_text(json.dumps(dict(pref.DEFAULTS,scope='selected_nets',nets=['GND'],profile='completion-only')))
  source_dir=self.root/'producer-source';source_dir.mkdir();source=source_dir/'a.kicad_pcb';source.write_text(BOARD);source.with_suffix('.kicad_pro').write_text(json.dumps(PROJECT))
  real_sha=p.sha
  def digest(path):return p.c.JAR_SHA256 if Path(path)==p.c.JAR else real_sha(path)
  with mock.patch.object(p,'check_storage'),mock.patch.object(p,'sha',side_effect=digest),mock.patch.object(p,'tool_manifest',return_value={'implementation_sha256':{}}),mock.patch.object(p.Job,'drc',side_effect=AssertionError('no Native before scope rejection')) as drc:
   result=p.route(source,self.root/'selected-run',settings_path=preset)
  self.assertFalse(result['accepted']);self.assertIn('unqualified board format',result['reason']);drc.assert_not_called()

class ReadbackControls(unittest.TestCase):
 def setUp(self):
  self.fixture=result_fixture.ResultFreshnessTests('test_matching_files_remain_current_without_applying_anything');self.fixture.setUp();self.addCleanup(self.fixture.doCleanups);x=self.fixture
  for folder in (x.source_dir,x.run/'snapshot',x.run/'candidate',x.run/'final-drc-input'):
   (folder/x.source.name).write_text(BOARD);(folder/x.source.with_suffix('.kicad_pro').name).write_text(json.dumps(PROJECT))
  x.binding.update(before=p.tree_hash(x.candidate.parent),after=p.tree_hash(x.candidate.parent));(x.run/'final-drc-binding.json').write_text(json.dumps(x.binding))
  x.data.update(source_hashes=p.tree_hash(x.source_dir),candidate_sha256=p.sha(x.candidate));x.data['steps'][0]['validated_input_sha256']=p.sha(x.candidate)
  from tests.normal_prl_fixture import refresh_authored_normal_import
  refresh_authored_normal_import(x.run,x.data,test_root=x.root);x.save_receipt()
 def test_existing_central_reader_admits_only_the_authored_legacy_scope(self):
  self.assertTrue(p.check_result(self.fixture.receipt)['current'])
  self.fixture.data['scope']='partial_completion';self.fixture.save_receipt()
  with self.assertRaisesRegex(p.Rejected,'unqualified board format'):p.check_result(self.fixture.receipt)
 def test_forged_source_all_label_with_actual_layer_process_refuses(self):
  x=self.fixture;(x.run/'engine-process.json').write_text(json.dumps({'argv':['--router.layers.active=F.Cu']}));x.save_receipt()
  with self.assertRaisesRegex(p.Rejected,'unqualified board format'):p.check_result(x.receipt)
 def test_forged_whole_label_with_selected_artifact_refuses(self):
  x=self.fixture;(x.run/'routing-scope-input.dsn').write_text('authored selected witness');x.save_receipt()
  with self.assertRaisesRegex(p.Rejected,'selected-net evidence cannot downgrade'):p.check_result(x.receipt)
if __name__=='__main__':unittest.main(verbosity=2)
