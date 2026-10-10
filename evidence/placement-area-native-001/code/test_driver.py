"""Pure controls on actual stored fixtures/DSN and publication; no native jobs."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE))
import driver as d
import fixture_recipe as r
import support as s

class FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.positive=d.f.read_json(d.POSITIVE);cls.path=Path(cls.positive['candidate']);cls.base=cls.path.read_bytes();cls.tree=d.sx.parse(cls.base.decode())
    def test_four_complete_projects_only_add_exact_area_nodes(self):
        base_files=d.p.tree_hash(self.path.parent)
        for case in r.CASES:
            with self.subTest(case=case):
                encoded,expected=r.prepare(case,self.base);tree=d.sx.parse(encoded.decode())
                self.assertEqual([x for x in tree if not isinstance(x,list) or not x or x[0]!='zone'],self.tree)
                self.assertEqual(d.p.routes(tree),d.p.routes(self.tree));project=HERE/'fixtures'/case/self.path.name
                self.assertEqual(project.read_bytes(),encoded);files=dict(base_files);files[project.name]=expected['board_sha256']
                self.assertEqual(d.p.tree_hash(project.parent),files)
    def test_mixed_preserves_both_genuine_restrictions_and_allowed_area(self):
        _,mixed=r.prepare('mixed',self.base);rows={z['name']:z for z in mixed['zones']}
        self.assertFalse(any(rows['diagnostic-allowed']['disallow'].values()))
        self.assertEqual(rows['diagnostic-track']['disallow'],dict(tracks=True,vias=False,pads=False,copperpour=False,footprints=False))
        self.assertEqual(rows['diagnostic-via']['disallow'],dict(tracks=False,vias=True,pads=False,copperpour=False,footprints=False))
        self.assertEqual(set(mixed['prohibited_target_uuids']),{r.TARGET_SEGMENT,r.TARGET_VIA})
    def test_moved_reference_route_or_rule_input_is_not_silently_used(self):
        data=self.base.replace(b'(start 40 20)',b'(start 39 20)',1)
        self.assertNotEqual(data,self.base)
        with self.assertRaisesRegex(d.p.Rejected,'pinned'):r.prepare('allowed_placement',data)
    def test_area_copper_lies_inside_qualified_board(self):
        for kind in ('allowed','track','via'):
            _,row=r.area(kind)
            self.assertTrue(all(0<x<50000000 and 0<y<30000000 for x,y in row['outlines_nm'][0]))
        _,track=r.area('track');xs=[p[0] for p in track['outlines_nm'][0]];ys=[p[1]for p in track['outlines_nm'][0]]
        self.assertTrue(min(ys)<20000000<max(ys));self.assertTrue(10000000<min(xs)<max(xs)<40000000)
        _,via=r.area('via');xs=[p[0]for p in via['outlines_nm'][0]];ys=[p[1]for p in via['outlines_nm'][0]]
        self.assertTrue(min(xs)<41645000-750000<41645000+750000<max(xs));self.assertTrue(min(ys)<13960000-750000<13960000+750000<max(ys))

class ObservationTests(unittest.TestCase):
    def setUp(self):
        _,row=r.area('allowed');self.expected={'zones':[row]}
        self.native=dict(context_schema=1,native_version='10.0.0',units='integer nanometres',board_saved=False,routing_accepted=False,
                         adapter_transformation_performed=False,footprint_zone_count=0,footprint_rulearea_count=0,zones=[copy.deepcopy(row)])
    def test_exact_declared_observation(self):self.assertTrue(r.verify_observation(self.native,self.expected)['passed'])
    def test_wrong_flag_or_placement_cannot_be_called_allowed(self):
        for field in ('is_rule_area','placement_enabled'):
            n=copy.deepcopy(self.native);n['zones'][0][field]=False
            with self.assertRaises(d.p.Rejected):r.verify_observation(n,self.expected)
        n=copy.deepcopy(self.native);n['zones'][0]['disallow']['pads']=True
        with self.assertRaises(d.p.Rejected):r.verify_observation(n,self.expected)
    def test_boolean_and_integer_api_types_distinguished(self):
        n=copy.deepcopy(self.native);n['zones'][0]['placement_enabled']=1
        with self.assertRaises(d.p.Rejected):r.verify_observation(n,self.expected)
        n=copy.deepcopy(self.native);n['footprint_rulearea_count']=False
        with self.assertRaises(d.p.Rejected):r.verify_observation(n,self.expected)
        with self.assertRaises(ValueError):d.worker.native_bool(1)
    def test_missing_duplicate_extra_native_area_rejects(self):
        for rows in ([],self.native['zones']*2):
            n=copy.deepcopy(self.native);n['zones']=rows
            with self.assertRaises(d.p.Rejected):r.verify_observation(n,self.expected)
    def test_holes_arcs_footprint_zone_and_shifted_contour_reject(self):
        for key,value in [('holes',[1]),('arc_count',1),('parent','footprint')]:
            n=copy.deepcopy(self.native);n['zones'][0][key]=value
            with self.assertRaises(d.p.Rejected):r.verify_observation(n,self.expected)
        n=copy.deepcopy(self.native);n['zones'][0]['outlines_nm'][0][0][0]+=1
        with self.assertRaises(d.p.Rejected):r.verify_observation(n,self.expected)
        n=copy.deepcopy(self.native);n['footprint_zone_count']=1
        with self.assertRaises(d.p.Rejected):r.verify_observation(n,self.expected)
    def test_wrong_disabled_placement_source_reject(self):
        _,row=r.area('track');n=copy.deepcopy(self.native);n['zones']=[row];expected={'zones':[copy.deepcopy(row)]}
        n['zones'][0]['placement_source']=''
        with self.assertRaises(d.p.Rejected):r.verify_observation(n,expected)

class DsnObservationTests(unittest.TestCase):
    def setUp(self):
        self.expected={'zones':[r.area(k)[1]for k in ('allowed','track','via')]}
        self.text=b'''(pcb fixture (parser (string_quote ")) (structure
          (keepout "" (polygon F.Cu 0 20000 -19000 30000 -19000 30000 -21000 20000 -21000 20000 -19000))
          (keepout "" (polygon B.Cu 0 20000 -19000 30000 -19000 30000 -21000 20000 -21000 20000 -19000))
          (wire_keepout "" (polygon F.Cu 0 24500 -19000 25500 -19000 25500 -21000 24500 -21000 24500 -19000))
          (wire_keepout "" (polygon B.Cu 0 24500 -19000 25500 -19000 25500 -21000 24500 -21000 24500 -19000))
          (via_keepout "" (polygon F.Cu 0 40645 -12960 42645 -12960 42645 -14960 40645 -14960 40645 -12960))
          (via_keepout "" (polygon B.Cu 0 40645 -12960 42645 -12960 42645 -14960 40645 -14960 40645 -12960))))'''
    def test_mixed_actual_kinds_preserved_without_transform(self):
        before=self.text;v=r.verify_dsn(self.text,self.expected)
        self.assertEqual(v['all_allowed_generic_keepouts'],2);self.assertEqual(v['genuine_restriction_keepouts'],4);self.assertFalse(v['dsn_modified']);self.assertEqual(before,self.text)
    def test_restriction_downgrade_or_missing_keepout_reject(self):
        for altered in (self.text.replace(b'wire_keepout',b'keepout',1),self.text.replace(b'via_keepout',b'wire_keepout',1),self.text.replace(b'24500',b'24501',1)):
            with self.assertRaises(d.p.Rejected):r.verify_dsn(altered,self.expected)
    def test_duplicate_native_keepout_not_unambiguous(self):
        tree=r.g._parse_dsn(self.text.decode());structure=d.sx.one(tree,'structure');structure.append(copy.deepcopy(structure[1]))
        with self.assertRaises(d.p.Rejected):r.verify_dsn(r.g._dump_dsn(tree).encode(),self.expected)
    def test_actual_frozen_multichannel_eight_keepouts(self):
        analysis=d.f.read_json(d.ROOT/'.runs/placement-area-diagnosis-001/analysis.json');raw=d.ROOT/'.runs/board-floor-multichannel-001/native.dsn'
        self.assertEqual(d.p.sha(raw),analysis['native_dsn_sha256'])
        zones=[dict(uuid=x['uuid'],layers=x['layers'],disallow=dict.fromkeys(r.FLAGS,False),
                    outlines_nm=[[[u*1000,-v*1000]for u,v in x['polygon_xy_um_export_coordinates']]]) for x in analysis['areas']]
        v=r.verify_dsn(raw.read_bytes(),{'zones':zones});self.assertEqual(v['all_allowed_generic_keepouts'],8);self.assertEqual(v['genuine_restriction_keepouts'],0)

class NativePredicateTests(unittest.TestCase):
    def clean(self):return dict(opens=0,blocking=0,warnings=0,exclusions=0,ignored_checks=[],findings=[])
    def error(self,uid):return dict(type='items_not_allowed',severity='error',items=[{'uuid':uid}])
    def test_allowed_needs_true_native_clean(self):
        n=self.clean();e={'prohibited_target_uuids':[]};self.assertTrue(d.native_expected('allowed_placement',n,e,[])[0])
        n['warnings']=1;self.assertFalse(d.native_expected('allowed_placement',n,e,[])[0])
    def test_mixed_needs_both_targeted_errors(self):
        n=self.clean();n.update(blocking=1,findings=[self.error(r.TARGET_SEGMENT)]);e={'prohibited_target_uuids':[r.TARGET_SEGMENT,r.TARGET_VIA]}
        self.assertFalse(d.native_expected('mixed',n,e,[])[0]);n['findings'].append(self.error(r.TARGET_VIA));n['blocking']=2
        self.assertTrue(d.native_expected('mixed',n,e,[])[0])
    def test_wrong_target_kind_severity_or_ignored_check_fails(self):
        e={'prohibited_target_uuids':[r.TARGET_SEGMENT]}
        for change in ({'type':'clearance'},{'severity':'warning'},{'items':[{'uuid':'wrong'}]},{'excluded':True}):
            row=self.error(r.TARGET_SEGMENT);row.update(change);n=self.clean();n.update(blocking=1,findings=[row]);self.assertFalse(d.native_expected('track_prohibited',n,e,[])[0])
        n=self.clean();n['ignored_checks']=[{'key':'items_not_allowed'}];self.assertFalse(d.native_expected('allowed_placement',n,{'prohibited_target_uuids':[]},[])[0])
    def test_opens_never_control_pass(self):
        n=self.clean();n.update(opens=1,blocking=1,findings=[self.error(r.TARGET_VIA)])
        self.assertFalse(d.native_expected('via_prohibited',n,{'prohibited_target_uuids':[r.TARGET_VIA]},[])[0])

class PublicationTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.out=Path(self.tmp.name);self.record={'status':'completed','controls_passed':True,'within_budget':True}
    def tearDown(self):self.tmp.cleanup()
    def assert_rejected(self):
        file=self.out/'summary.json'
        if file.exists():self.assertFalse(d.f.read_json(file)['controls_passed'])
    def test_cancel_after_positive_and_failed_rewrite_removes_canonical(self):
        stable_calls=[];save_calls=[];real=d.p.save_json
        def stable():
            stable_calls.append(1)
            if len(stable_calls)>1:raise KeyboardInterrupt
        def save(path,value):
            save_calls.append(1)
            if len(save_calls)>1:raise OSError('failed correction')
            real(path,value)
        with patch.object(d.p,'save_json',save):s.publish(self.out,self.record,stable,lambda:None)
        self.assertFalse((self.out/'summary.json').exists());self.assertTrue(list(self.out.glob('invalidated-*-summary.json')))
    def test_summary_mutated_by_final_check_rejects(self):
        calls=[]
        def stable():
            calls.append(1)
            if len(calls)==2:
                value=d.f.read_json(self.out/'summary.json');value['forged']=True;d.p.save_json(self.out/'summary.json',value)
        s.publish(self.out,self.record,stable,lambda:None);self.assert_rejected()
    def test_final_cap_crossing_rejects(self):
        calls=[]
        def account():
            calls.append(1)
            if len(calls)>1:self.record['within_budget']=False
        s.publish(self.out,self.record,lambda:None,account);self.assert_rejected()
    def test_real_partial_receipt_is_retained(self):
        real=d.p.save_json;calls=[]
        def save(path,value):
            calls.append(1)
            if len(calls)==1:Path(str(path)+'.partial').write_text('interrupted');raise KeyboardInterrupt
            real(path,value)
        with patch.object(d.p,'save_json',save):s.publish(self.out,self.record,lambda:None,lambda:None)
        self.assert_rejected();self.assertTrue(list(self.out.glob('invalidated-*-summary.json.partial')))

class InvocationTests(unittest.TestCase):
    def test_no_implicit_native_work(self):
        with patch.object(d.p,'check_result',side_effect=AssertionError('unexpected invocation')):
            with self.assertRaisesRegex(d.p.Rejected,'explicit'):d.experiment(HERE/'unused')
    def test_cancelled_step_cannot_be_treated_as_ordinary_rejection(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            shared=[];job=s.SharedJob(Path(tmp)/'job',lambda:10,shared)
            def cancelled(self,*args,**kwargs):self.steps.append({'status':'cancelled'});raise d.p.Rejected('cancelled child')
            with patch.object(d.p.Job,'step',cancelled):
                with self.assertRaises(KeyboardInterrupt):job.step('fake',['no-executable'])
            self.assertEqual(shared,[{'status':'cancelled'}])

if __name__=='__main__':unittest.main()
