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
    def test_actual_intrusion_subdivision_only_at_original_pin(self):
        from autorouter.adapter import _parse_dsn
        from autorouter import sexpr as sx
        for ident in d.IDS:
            raw,*rest=self.rows(ident); derived,expected=d.derive(raw,*rest)
            tree=_parse_dsn(derived.decode()); wires=sx.children(d.exact_one(tree,'wiring'),'wire')
            paths=[d.exact_one(w,'path') for w in wires if sx.children(w,'path')]
            self.assertEqual(len(paths),3 if 'intrusion' in ident else 2)
            splits=expected['trace_splits'][1]
            if 'intrusion' in ident:
                point=splits['centers'][0]['position_um']; self.assertEqual(splits['centers'][0]['reference'],'FOREIGN_B')
                foreign=paths[1:]; self.assertEqual(foreign[0][-2:],[str(x) for x in point]); self.assertEqual(foreign[1][3:5],[str(x) for x in point])
            else:self.assertEqual(splits['centers'],[])
    def test_split_rejects_recipe_drift_and_ambiguous_terminal(self):
        from autorouter.adapter import _parse_dsn
        r=self.rows('front0-foreign_intrusion');tree=_parse_dsn(r[0].decode());wire=d.exact_one(tree,'wiring')[2]
        args=[wire,r[3]['tracks'][1],r[2]['pads'],'F.Cu','top_layer']
        for kind in ('width','path','duplicate','fractional'):
            a=copy.deepcopy(args)
            if kind=='width':a[1]['width_nm']+=1000
            elif kind=='path':d.exact_one(a[0],'path')[-1]='-14401'
            elif kind=='duplicate':a[2].append(copy.deepcopy(a[2][3]))
            else:a[2][3]['position_nm'][0]+=1
            with self.subTest(kind=kind),self.assertRaises(ValueError):d.split_wire(*a)
        for kind in ('wrong_net','wrong_layer','off_segment'):
            a=copy.deepcopy(args)
            if kind=='wrong_net':a[2][3]['net']='CONTACT'
            elif kind=='wrong_layer':a[2][3]['copper_layers']=['B.Cu']
            else:a[2][3]['position_nm'][0]+=1000
            pieces,centers=d.split_wire(*a);self.assertEqual(pieces,[wire]);self.assertEqual(centers,[])
    def test_importer_name_normalization_collision_rejected(self):
        from autorouter.adapter import _parse_dsn,_dump_dsn
        self.assertEqual(d.imported_name('pad12.750.0'), 'pad12')
        self.assertEqual(d.imported_name('pad.١'), 'pad.١')  # Java default regex digit class is ASCII.
        r=self.rows();tree=_parse_dsn(r[0].decode());stacks=d.sx.children(d.exact_one(tree,'library'),'padstack')
        stacks[0][1]='collision.1';stacks[1][1]='collision.2'
        r[0]=_dump_dsn(tree).encode();r[1]['dsn_sha256']=r[2]['dsn_sha256']=d.sha(r[0])
        with self.assertRaisesRegex(ValueError,'name collision'):d.derive(*r)

if __name__=='__main__':unittest.main()
