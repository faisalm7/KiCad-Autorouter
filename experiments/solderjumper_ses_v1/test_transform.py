"""Pure allowed-edit controls, explicitly not Native or routing evidence."""
import copy,json,unittest
from pathlib import Path
from autorouter import sexpr as sx
from autorouter.adapter import _parse_dsn,_dump_dsn
from experiments.solderjumper_ses_v1 import transform as t

ROOT=Path(__file__).resolve().parents[2]
class Edits(unittest.TestCase):
    def inputs(self,generated=False):
        b=ROOT/'evidence/pic-custom-native-controls-002/back90-positive'
        raw=(b/'native.dsn').read_bytes().replace(b'"10.0.0"',b'"10.0.7"')
        custom=json.loads((b/'custom-pads.json').read_bytes());context=json.loads((b/'observation.json').read_bytes())
        project_raw=(b/'observe-input/pic_programmer.kicad_pro').read_bytes();project=json.loads(project_raw)
        rows=copy.deepcopy(context['nets']);cls=project['net_settings']['classes'][0]
        for n in rows:
            n['parameter_parents']={k:dict(name='Default',specified=True,priority=cls['priority'],value_nm=n[k]) for k in ('width_nm','clearance_nm','via_diameter_nm','via_drill_nm')}
        context['mapping']=dict(schema=1,native_version='10.0.7',units='integer nanometres',source=context['source'],board_sha256=context['board_sha256'],project_sha256=context['project_sha256'],board_saved=False,nets=rows,effective_floors_nm=context['floors_nm'])
        if generated:
            tree=_parse_dsn(raw.decode());sx.one(tree,'wiring')[1:]=[];raw=_dump_dsn(tree).encode()
        # Constructed scalar controls only; these are never written as fresh Native observations.
        for value in (custom,context):value.update(native_version='10.0.7',dsn_sha256=t.area.sha(raw))
        return [raw,custom,context,json.loads((b/'recipe.json').read_bytes()),project_raw]
    def ses(self,derived,generated=False):
        tree=_parse_dsn(derived.decode());scale=lambda value:str(t.ses.number(value)*10)
        place=copy.deepcopy(sx.one(tree,'placement'));place.insert(1,['resolution','um','10'])
        for component in sx.children(place,'component'):
            for pin in sx.children(component,'place'):
                pin[2]=scale(pin[2]);pin[3]=scale(pin[3]);pin[:]=[v for v in pin if type(v) is not list]
        nets={name:['net',name] for name in ('CONTACT','FOREIGN')}
        for wire in sx.children(sx.one(tree,'wiring'),'wire'):
            w=copy.deepcopy(wire);net=sx.one(w,'net');w.remove(net)
            # Actual pinned writer omits type for conduction areas and unfixed tracks.
            if sx.one(w,'type') is not None:w.remove(sx.one(w,'type'))
            shape=sx.one(w,'path') or sx.one(w,'polygon');shape[2:]=[scale(v) for v in shape[2:]];nets[net[1]].append(w)
        name='task' if generated else 'original-mixed.dsn'
        return ['session',json.dumps(name.replace('.dsn','.ses')),['base_design',json.dumps(name)],place,['was_is'],['routes',['resolution','um','10'],['parser',['host_cad','"KiCad\'s Pcbnew"'],['host_version','"10.0.7"']],['library_out'],['network_out',*nets.values()]]]
    def test_both_seed_modes_allowed_edits(self):
        for generated in (False,True):
            with self.subTest(generated=generated):
                derived,exp=t.derive(*self.inputs(generated),generated=generated)
                self.assertEqual(exp['target']['typed_clearance_um'],dict(before='62.5',after='250'))
                self.assertFalse(exp['production_admitted']);self.assertEqual(exp['seed_routes'],0 if generated else 2)
                raw=(sx.dump(self.ses(derived,generated))+'\n').encode();filtered,proof=t.import_session(raw,derived,exp)
                self.assertEqual(proof['synthetic_areas_removed'],2);self.assertTrue(proof['other_AST_exact'])
                self.assertNotIn(b'(polygon',filtered)
    def test_project_or_parent_not_normalized(self):
        args=self.inputs();args[-1]+=b' '
        with self.assertRaisesRegex(ValueError,'unchanged original'):t.derive(*args)
        args=self.inputs();args[2]['mapping']['nets'][0]['parameter_parents']['clearance_nm']['name']='POWER'
        with self.assertRaisesRegex(ValueError,'parent'):t.derive(*args)
    def test_net_members_and_geometry_do_not_rebase(self):
        args=self.inputs();args[0]=args[0].replace(b'CONVEX-1 CONCAVE-1',b'CONVEX-1 FOREIGN_A-1')
        for d in args[1:3]:d['dsn_sha256']=t.area.sha(args[0])
        with self.assertRaisesRegex(ValueError,'terminal'):t.derive(*args)
        args=self.inputs();args[1]['observation_before_export']['pads'][0]['effective_world']['outlines'][0]['outline']['points_nm'][0][0]+=1000;args[1]['observation_after_export']=copy.deepcopy(args[1]['observation_before_export'])
        with self.assertRaisesRegex(ValueError,'contour'):t.derive(*args)
    def test_extra_wrong_area_and_route_changes_refuse(self):
        derived,exp=t.derive(*self.inputs());base=self.ses(derived)
        for role in ('area','extra','wire','host','design','spurious-fixed-marker'):
            tree=copy.deepcopy(base);net=sx.one(sx.one(tree,'routes'),'network_out')[1]
            if role=='area':sx.one(net[-1],'polygon')[3]=str(int(sx.one(net[-1],'polygon')[3])+1)
            elif role=='extra':net.append(copy.deepcopy(net[-1]))
            elif role=='wire':sx.one(net[2],'path')[2]='4999'
            elif role=='host':sx.one(sx.one(sx.one(tree,'routes'),'parser'),'host_version')[1]='"10.0.0"'
            elif role=='design':sx.one(tree,'base_design')[1]='"other.dsn"'
            else:net[-1].append(['type','protect'])
            with self.subTest(role=role),self.assertRaises(ValueError):t.import_session((sx.dump(tree)+'\n').encode(),derived,exp)
    def test_empty_task_cannot_hide_reference_routes(self):
        with self.assertRaisesRegex(ValueError,'seed-route'):t.derive(*self.inputs(),generated=True)
    def test_derived_dsn_custody_and_actual_map_binding(self):
        derived,expected=t.derive(*self.inputs());raw=(sx.dump(self.ses(derived))+'\n').encode()
        with self.assertRaisesRegex(ValueError,'DSN binding'):t.import_session(raw,derived+b' ',expected)
        args=self.inputs();args[2]['mapping']['board_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'map binding'):t.derive(*args)

if __name__=='__main__':unittest.main()
