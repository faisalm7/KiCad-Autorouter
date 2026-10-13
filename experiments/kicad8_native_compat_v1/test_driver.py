"""Pure threats to compatibility interpretation; no native/JVM invocation."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('kicad8_compat_driver',HERE/'driver.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
class Controls(unittest.TestCase):
    def test_monitored_output_is_fresh_owned_and_narrow(self):
        import tempfile
        with tempfile.TemporaryDirectory(dir=d.ROOT/'.runs',prefix='kicad8-native-compat-test-') as folder:
            parent=Path(folder);target=parent/'run'
            self.assertEqual(d.control_output(target),target)
            target.mkdir()
            with self.assertRaises(d.p.Rejected):d.control_output(target)
            with self.assertRaises(d.p.Rejected):d.control_output(parent/'arbitrary')
            alias=parent/'alias';alias.symlink_to(target,target_is_directory=True)
            with self.assertRaises(d.p.Rejected):d.control_output(alias)
    def test_owned_old_grammar_has_numeric_nets_layers_and_stable_ids(self):
        tree=d.sx.parse(d.fixture.board('positive').decode());self.assertEqual(d.sx.one(tree,'version'),['version','20240108'])
        self.assertEqual(d.sx.one(tree,'layers')[1:3],[['0','"F.Cu"','signal'],['31','"B.Cu"','signal']]);self.assertEqual(d.sx.children(tree,'net'),[['net','0','""'],['net','1','"SIGNAL"'],['net','2','"GND"']])
        self.assertEqual(len(d.sx.children(tree,'footprint')),4);self.assertEqual(len(d.sx.children(tree,'zone')),1)
        self.assertEqual(d.fixture.board('positive'),d.fixture.board('positive'))
    def test_invalid_controls_change_only_one_exact_route_atom_or_object(self):
        positive=d.sx.parse(d.fixture.board('positive').decode());missing=d.sx.parse(d.fixture.board('missing_track').decode());narrow=d.sx.parse(d.fixture.board('narrow_track').decode())
        self.assertEqual(d.p.immutable(positive),d.p.immutable(missing));self.assertEqual(d.p.immutable(positive),d.p.immutable(narrow));self.assertEqual(d.p.routes(missing),[])
        route=d.p.routes(narrow)[0];self.assertEqual(d.sx.one(route,'width'),['width','0.2']);d.sx.one(route,'width')[1]='0.3';self.assertEqual(narrow,positive)
    def test_actual_emission_comparison_does_not_strip_version_or_other_fields(self):
        first=d.sx.parse(d.fixture.board('positive').decode());second=copy.deepcopy(first);d.emission_equal(first,second)
        d.sx.one(second,'version')[1]='20260206'
        with self.assertRaisesRegex(d.p.Rejected,'geometry'):d.emission_equal(first,second)
        second=copy.deepcopy(first);d.sx.one(d.p.routes(second)[0],'width')[1]='0.2'
        with self.assertRaisesRegex(d.p.Rejected,'routes'):d.emission_equal(first,second)
    def test_only_derived_fill_can_enter_original_shell(self):
        original=d.sx.parse(d.fixture.board('positive').decode());saved=copy.deepcopy(original)
        zone=d.sx.children(saved,'zone')[0];zone.append(['filled_polygon',['layer','"B.Cu"'],['pts',['xy','7','14'],['xy','23','14'],['xy','23','19']]])
        result=d.old_shell(original,saved);self.assertEqual(d.sx.one(result,'version'),['version','20240108']);self.assertEqual(d.p.immutable(result),d.p.immutable(original));self.assertEqual(d.p.routes(result),d.p.routes(original));self.assertTrue(d.sx.children(d.sx.children(result,'zone')[0],'filled_polygon'))
        self.assertFalse(d.sx.children(d.sx.children(original,'zone')[0],'filled_polygon'))
    def test_missing_zone_and_changed_original_header_fail_closed(self):
        original=d.sx.parse(d.fixture.board('positive').decode());saved=copy.deepcopy(original);saved.remove(d.sx.children(saved,'zone')[0])
        with self.assertRaisesRegex(d.p.Rejected,'lost zone'):d.old_shell(original,saved)
        d.sx.one(original,'version')[1]='20260206'
        with self.assertRaisesRegex(d.p.Rejected,'source format'):d.old_shell(original,original)
    def native(self,findings=None,opens=0,blocking=0):return {'opens':opens,'blocking':blocking,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':findings or []}
    def test_negative_requires_exact_unexcluded_critical_finding(self):
        self.assertTrue(d.fixture.expected('positive',self.native())[0])
        row={'type':'unconnected_items','severity':'error','excluded':False,'items':[{'uuid':u} for u in d.fixture.PADS[:2]]};native=self.native([row],opens=1)
        self.assertTrue(d.fixture.expected('missing_track',native)[0]);bad=copy.deepcopy(native);bad['findings'][0]['items'][0]['uuid']='other';self.assertFalse(d.fixture.expected('missing_track',bad)[0]);bad=copy.deepcopy(native);bad['findings'][0]['excluded']=True;self.assertFalse(d.fixture.expected('missing_track',bad)[0])
        width={'type':'track_width','severity':'error','excluded':False,'items':[{'uuid':d.fixture.TRACK}]};self.assertTrue(d.fixture.expected('narrow_track',self.native([width],blocking=1))[0])
    def test_context_projection_only_normalizes_local_net_codes(self):
        original={'native_version':'10.0.0','units':'integer nanometres','floors_nm':{'min_clearance':300000},'pads':[{'uuid':'p','netcode':1,'net':'SIGNAL','position_nm':[0,0]}],'nets':[{'name':'SIGNAL','netcode':1,'width_nm':300000}],'routes':[],'obstacles':[]}
        after=copy.deepcopy(original);after['pads'][0]['netcode']=2;after['nets'][0]['netcode']=2;self.assertEqual(d.geometry(original),d.geometry(after))
        after['pads'][0]['position_nm']=[1,0];self.assertNotEqual(d.geometry(original),d.geometry(after));self.assertIn('netcode',original['pads'][0])
    def test_unpromoted_or_implicit_native_cannot_create_output(self):
        with patch.object(d,'HERE',d.ROOT/'.runs/kicad8-native-compat-draft-001'),patch.object(d,'shared') as shared:
            with self.assertRaisesRegex(d.p.Rejected,'promote'):d.experiment(d.ROOT/'.runs/not-created',run_native=True)
            with self.assertRaisesRegex(d.p.Rejected,'promote'):d.experiment(d.ROOT/'.runs/not-created',run_native=False)
            shared.owned.assert_not_called()
if __name__=='__main__':unittest.main()
