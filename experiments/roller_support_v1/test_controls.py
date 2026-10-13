"""Pure source/contract controls; no native processes or solver."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT),str(HERE)]
import checks,fixture
from autorouter import sexpr as sx,pipeline as p,adapter
from tests.test_netclass import fixtures
class Controls(unittest.TestCase):
    def setUp(self):
        self.tree,self.native,self.project=fixtures(True)
        unused=copy.deepcopy(self.project['net_settings']['classes'][0]);unused['name']='5mil';unused['track_width']=0.127
        self.project['net_settings']['classes'].append(unused)
    def test_inactive_definition_proof_keeps_original_project_exact(self):
        before=copy.deepcopy(self.project);result=checks.inactive_default(self.project,self.native,adapter._dump_dsn(self.tree))
        self.assertTrue(result['passed']);self.assertFalse(result['production_support_qualified']);self.assertEqual(self.project,before)
    def test_active_literal_assignment_cannot_use_inactive_proof(self):
        self.project['net_settings']['netclass_patterns']=[{'netclass':'5mil','pattern':'DATA'}]
        with self.assertRaisesRegex(ValueError,'unused'):checks.inactive_default(self.project,self.native,adapter._dump_dsn(self.tree))
    def test_observed_nondefault_even_with_empty_patterns_rejects(self):
        self.native['nets'][0]['class']='5mil'
        with self.assertRaisesRegex(ValueError,'active'):checks.inactive_default(self.project,self.native,adapter._dump_dsn(self.tree))
    def test_effective_default_width_drift_is_not_hidden_by_unused_definition(self):
        self.native['nets'][0]['width_nm']-=1
        with self.assertRaisesRegex(ValueError,'original project value'):checks.inactive_default(self.project,self.native,adapter._dump_dsn(self.tree))
    def test_missing_terminal_still_rejected_by_shared_mapping_audit(self):
        sx.one(sx.children(sx.one(self.tree,'network'),'net')[0],'pins').pop()
        with self.assertRaisesRegex(ValueError,'terminal count'):checks.inactive_default(self.project,self.native,adapter._dump_dsn(self.tree))
    def test_inactive_tuning_intent_remains_blocked(self):
        self.project['net_settings']['classes'][1]['tuning_profile']='secret'
        with self.assertRaisesRegex(ValueError,'tuning'):checks.inactive_default(self.project,self.native,adapter._dump_dsn(self.tree))
    def authored(self,negative=False,layer_type='jumper'):
        return fixture.fixture(sx.read(ROOT/'tests/fixtures/board-floor/fixture.kicad_pcb'),json.loads((ROOT/'tests/fixtures/board-floor/fixture.kicad_pro').read_text()),negative=negative,layer_type=layer_type)
    def observation(self,tree):
        node=sx.children(tree,'gr_text')[0]
        raw={'layers':[{'name':'F.Cu','canonical':'F.Cu','type':'signal'},{'name':'B.Cu','canonical':'B.Cu','type':'jumper'}],
             'copper_text':[{'uuid':fixture.uid('text'),'text':'X','layer':'B.Cu','knockout':True,'position_nm':[30000000,20000000],'shape_outlines':[{'points_nm':[[1,2],[3,4],[5,6]],'holes':0}]}]}
        return {'same_loaded_board':True,'observation_before_export':raw,'observation_after_export':copy.deepcopy(raw)}
    def test_owned_geometry_changes_only_declared_routes_between_knockout_controls(self):
        pos,pro=self.authored();neg,negpro=self.authored(True)
        self.assertEqual(pro,negpro);self.assertEqual(p.immutable(pos),p.immutable(neg));self.assertEqual({sx.unquote(sx.one(n,'uuid')[1]) for n in p.routes(pos)},{sx.unquote(sx.one(n,'uuid')[1]) for n in p.routes(neg)})
        self.assertEqual(len(sx.children(pos,'footprint')),2);self.assertEqual(len(p.routes(pos)),5)
    def test_jumper_type_and_knockout_same_load_binding(self):
        tree,_=self.authored();obs=self.observation(tree);dsn='(pcb owned (parser (string_quote ")) (structure (layer F.Cu (type signal)) (layer B.Cu (type jumper))))'
        self.assertTrue(checks.layer_text(tree,obs,dsn)['passed'])
        with self.assertRaisesRegex(ValueError,'DSN layer'):checks.layer_text(tree,obs,dsn.replace('jumper','signal'))
    def test_knockout_or_export_state_drop_rejects(self):
        tree,_=self.authored();obs=self.observation(tree);obs['observation_after_export']['copper_text'][0]['knockout']=False
        with self.assertRaisesRegex(ValueError,'same-load'):checks.layer_text(tree,obs,'(pcb owned (parser (string_quote ")) (structure))')
    def test_positive_and_uuid_bound_blocking_negative_are_distinct(self):
        raw={'opens':0,'blocking':0,'exclusions':0,'findings':[]};self.assertTrue(checks.crossing(raw,False,'text','track'));self.assertFalse(checks.crossing(raw,True,'text','track'))
        raw.update(blocking=1,findings=[{'type':'clearance','severity':'error','items':[{'uuid':'text'},{'uuid':'track'}]}]);self.assertTrue(checks.crossing(raw,True,'text','track'));self.assertFalse(checks.crossing(raw,False,'text','track'))
        raw['findings'][0]['items'][0]['uuid']='other';self.assertFalse(checks.crossing(raw,True,'text','track'))
    def test_warning_or_unrelated_blocking_cannot_prove_crossing_guard(self):
        raw={'opens':0,'blocking':0,'exclusions':0,'findings':[{'type':'clearance','severity':'warning','items':[{'uuid':'text'},{'uuid':'track'}]}]}
        self.assertFalse(checks.crossing(raw,True,'text','track'));raw.update(blocking=2);raw['findings'][0]['severity']='error';self.assertFalse(checks.crossing(raw,True,'text','track'))
    def test_native_refused_without_explicit_root_lane_flag(self):
        spec=importlib.util.spec_from_file_location('roller_driver',HERE/'driver.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with self.assertRaisesRegex(p.Rejected,'ROOT native lane'):module.experiment(ROOT/'.runs/will-not-be-created')
        self.assertFalse((ROOT/'.runs/will-not-be-created').exists())
if __name__=='__main__':unittest.main(verbosity=2)
