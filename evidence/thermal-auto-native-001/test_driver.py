import copy,importlib,json,sys,tempfile,unittest
from pathlib import Path
import driver
from autorouter import sexpr as sx
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'preparation-002/helpers'))
MODULES={name:importlib.import_module(name) for name in ('copper_path','diagnose','attempt_paths_v2','attempt_graph_v3')}
PROBE=driver.ROOT/'.runs/thermal-generalization-draft-001/native-export-001'
QUAL=PROBE.parent/'qualification-001'
class DriverControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geometry=json.loads((PROBE/'geometry.json').read_text());cls.proposals=json.loads((QUAL/'path-attempt-003.json').read_text());cls.board=sx.read(PROBE/'native-input/interf_u.kicad_pcb')
    def test_actual_four_proofs_reverified(self):self.assertEqual(len(driver.verify_proposals(copy.deepcopy(self.geometry),self.proposals,MODULES)),4)
    def test_negative_pad_hole_rejected(self):
        g=copy.deepcopy(self.geometry);g['pads'][0]['effective_hole']['width_nm']=-1
        with self.assertRaises(driver.Invalid):driver.strict_dimensions(g)
    def test_negative_native_drill_axis_rejected(self):
        g=copy.deepcopy(self.geometry);g['pads'][0]['drill_size_nm'][1]=-1
        with self.assertRaises(driver.Invalid):driver.strict_dimensions(g)
    def test_zero_pth_hole_rejected(self):
        g=copy.deepcopy(self.geometry);p=next(p for p in g['pads'] if p['is_pth']);p['effective_hole']['width_nm']=0;p['drill_size_nm']=[0,0]
        with self.assertRaises(driver.Invalid):driver.strict_dimensions(g)
    def test_negative_via_hole_rejected(self):
        g=copy.deepcopy(self.geometry);g['vias'][0]['drill_nm']=-1
        with self.assertRaises(driver.Invalid):driver.strict_dimensions(g)
    def test_nonpositive_maxerror_rejected(self):
        for value in (0,-1,True):
            g=copy.deepcopy(self.geometry);g['native_max_error_nm']=value
            with self.assertRaises(driver.Invalid):driver.strict_dimensions(g)
    def test_width_tamper_rejected(self):
        r=copy.deepcopy(self.proposals);r['path_certificate_candidates'][0]['width_nm']=400000
        with self.assertRaises(driver.Invalid):driver.verify_proposals(self.geometry,r,MODULES)
    def test_same_logical_terminal_rejected(self):
        r=copy.deepcopy(self.proposals);p=r['path_certificate_candidates'][0];p['other_logical_terminal']=p['target_logical_terminal']
        with self.assertRaises(driver.Invalid):driver.verify_proposals(self.geometry,r,MODULES)
    def test_path_endpoint_in_drill_rejected(self):
        r=copy.deepcopy(self.proposals);r['path_certificate_candidates'][0]['source_copper_path_nm'][-1]=self.geometry['target_position_nm']
        with self.assertRaises(driver.Invalid):driver.verify_proposals(self.geometry,r,MODULES)
    def test_actual_saved_fill_and_dimension_uuid_aliases(self):self.assertEqual(len(driver.fill_binding(self.board,self.geometry,sx)),27)
    def test_changed_saved_fill_rejected(self):
        board=copy.deepcopy(self.board);zone=driver.uuid_index(board,sx)[self.geometry['zone_uuid']][0];pts=sx.one(sx.children(zone,'filled_polygon')[0],'pts');pts[1][1]='123.0'
        with self.assertRaises(driver.Invalid):driver.fill_binding(board,self.geometry,sx)
    def test_duplicate_target_uuid_rejected(self):
        board=copy.deepcopy(self.board);board.append(copy.deepcopy(driver.uuid_index(board,sx)[self.geometry['target_pad_uuid']][0]))
        with self.assertRaises(driver.Invalid):driver.fill_binding(board,self.geometry,sx)
    def test_symlink_path_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            p=Path(td);(p/'actual').write_text('x');(p/'link').symlink_to(p/'actual')
            with self.assertRaises(driver.Invalid):driver.require(p/'link',ROOT)
    def test_outside_path_rejected_without_reads(self):
        with self.assertRaises(driver.Invalid):driver.require('/unrelated/not/read',ROOT)
    def test_exact_nm_serialization(self):
        for value in (-1000001,0,149995000):self.assertEqual(driver.nm(driver.mm(value)),value)

    def test_cancel_after_positive_summary_write_invalidates(self):
        from autorouter import pipeline as pipeline
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            out=Path(td);summary={'status':'diagnostic_native_pass','validation_passed':True,'selected':'candidate-01'};calls=[]
            def save(path,value):
                pipeline.save_json(path,value);calls.append(value['validation_passed'])
                if len(calls)==1:raise KeyboardInterrupt
            driver.publish_summary(summary,out,lambda:(1.,1.),lambda:None,save)
            self.assertEqual(json.loads((out/'summary.json').read_text())['status'],'cancelled');self.assertEqual(calls,[True,False])
    def test_cancel_partial_preserved_and_rejected(self):
        from autorouter import pipeline as pipeline
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            out=Path(td);summary={'status':'diagnostic_native_pass','validation_passed':True};calls=[]
            def save(path,value):
                calls.append(1)
                if len(calls)==1:(out/'summary.json.partial').write_text('interrupted');raise KeyboardInterrupt
                pipeline.save_json(path,value)
            driver.publish_summary(summary,out,lambda:(1.,1.),lambda:None,save)
            self.assertEqual((out/'cancelled-summary.partial').read_text(),'interrupted');self.assertFalse(json.loads((out/'summary.json').read_text())['validation_passed'])
    def test_final_selected_recheck_failure_invalidates(self):
        from autorouter import pipeline as pipeline
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            out=Path(td);summary={'status':'diagnostic_native_pass','validation_passed':True};calls=[]
            def verify():
                calls.append(1)
                if len(calls)>1:raise driver.Invalid('selected report changed')
            driver.publish_summary(summary,out,lambda:(1.,1.),verify,pipeline.save_json)
            result=json.loads((out/'summary.json').read_text());self.assertFalse(result['validation_passed']);self.assertEqual(result['status'],'invalidated')
    def test_final_write_budget_crossing_invalidates(self):
        from autorouter import pipeline as pipeline
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            out=Path(td);summary={'status':'diagnostic_native_pass','validation_passed':True};calls=[]
            def totals():calls.append(1);return (1.,1.) if len(calls)==1 else (61.,1.)
            driver.publish_summary(summary,out,totals,lambda:None,pipeline.save_json)
            result=json.loads((out/'summary.json').read_text());self.assertFalse(result['validation_passed']);self.assertEqual(result['status'],'budget_exceeded')

if __name__=='__main__':unittest.main(verbosity=2)
