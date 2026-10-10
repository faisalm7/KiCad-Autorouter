import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).absolute().parent))
ROOT=next(p for p in Path(__file__).absolute().parents if (p/'autorouter/runner.py').is_file())
sys.path.insert(0,str(ROOT))
import derive as d

class Derivation(unittest.TestCase):
    def rows(self,ident='front0-positive'):
        p=ROOT/d.BASIS/ident
        return [(p/'native.dsn').read_bytes(),*[json.loads((p/n).read_bytes()) for n in ('custom-pads.json','observation.json','recipe.json')]]
    def test_actual_six_derivations_and_only_allowed_changes(self):
        inputs,expected=d.prepare(ROOT,lambda p:p.read_bytes())
        self.assertEqual(tuple(x[:-4] for x in inputs),d.IDS)
        for row in expected:
            self.assertEqual({a['area_um2'] for a in row['areas']},{1350000,1875000})
            self.assertEqual(len(row['pins']),4)
            self.assertFalse(row['plane_nets_expected'])
            self.assertEqual(row['connectivity_expected'],'false_hull' not in row['case'])
    def test_original_pin_mapping_tamper_rejected(self):
        r=self.rows();raw=r[0].replace(b'CONVEX-1 CONCAVE-1',b'CONCAVE-1 CONVEX-1')
        r[0]=raw;r[1]['dsn_sha256']=r[2]['dsn_sha256']=d.sha(raw)
        with self.assertRaisesRegex(ValueError,'terminal mapping'):d.derive(*r)
    def test_no_hidden_anchor_resize(self):
        for key,value in [('size_nm',[400000,300000]),('offset_nm',[1000,0]),('drill_nm',[1000,1000]),('net','FOREIGN')]:
            with self.subTest(key=key):
                r=self.rows();r[1]['observation_before_export']['pads'][0][key]=value;r[1]['observation_after_export']=copy.deepcopy(r[1]['observation_before_export'])
                with self.assertRaisesRegex(ValueError,'anchor'):d.derive(*r)
    def test_world_transform_independently_rechecked(self):
        r=self.rows('back90-positive');r[1]['observation_before_export']['pads'][0]['effective_world']['outlines'][0]['outline']['points_nm'][0][0]+=1000
        r[1]['observation_after_export']=copy.deepcopy(r[1]['observation_before_export'])
        with self.assertRaisesRegex(ValueError,'polygon disagreement'):d.derive(*r)
    def test_submicrometre_geometry_not_silently_rounded(self):
        r=self.rows();r[1]['observation_before_export']['pads'][0]['effective_world']['outlines'][0]['outline']['points_nm'][0][0]+=1
        r[1]['observation_after_export']=copy.deepcopy(r[1]['observation_before_export'])
        with self.assertRaisesRegex(ValueError,'micrometre'):d.derive(*r)
    def test_complex_polygon_rejected(self):
        r=self.rows();r[1]['observation_before_export']['pads'][0]['effective_world']['arc_count']=1
        r[1]['observation_after_export']=copy.deepcopy(r[1]['observation_before_export'])
        with self.assertRaisesRegex(ValueError,'simple'):d.derive(*r)
    def test_recorded_native_context_digest_not_rebased(self):
        def read(p):
            raw=p.read_bytes()
            if p.name=='observation.json':raw+=b' '
            return raw
        with self.assertRaisesRegex(ValueError,'recorded stage'):d.prepare(ROOT,read)

if __name__=='__main__':unittest.main()
