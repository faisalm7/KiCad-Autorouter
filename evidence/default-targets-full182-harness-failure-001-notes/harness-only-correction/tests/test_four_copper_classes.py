"""Prospective4Cu class transport controls; pure software, never Native proof."""
import ast
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from autorouter import netclass as n,pipeline as p,sexpr as sx
from autorouter.netclass_native import observe_floors
from autorouter.floor_context import FLOORS
from tests.test_netclass import fixtures
from experiments.four_copper_class_transport_v1 import fixture


def four_mapping():
    tree,native,project=fixtures()
    structure=sx.one(tree,'structure');layers=sx.children(structure,'layer')
    structure[1:3]=[['layer',name,['type','signal'],['property',['index',str(i)]]] for i,name in enumerate(n.FOUR_COPPER_NAMES)]
    def convert(node):
        for i,value in enumerate(node):
            if isinstance(value,str):node[i]=value.replace('Via[0-1]','Via[0-3]')
            elif isinstance(value,list):convert(value)
    convert(tree)
    for stack in sx.children(sx.one(tree,'library'),'padstack'):
        diameter=sx.one(sx.children(stack,'shape')[0],'circle')[2]
        attach=sx.one(stack,'attach')
        stack[2:]=[['shape',['circle',name,diameter]] for name in n.FOUR_COPPER_NAMES]+[attach]
    native['copper_layers']=[dict(id=code,name=name,type='signal',index=i) for i,(code,name) in enumerate(zip(n.FOUR_COPPER_IDS,n.FOUR_COPPER_NAMES))]
    return tree,native,project


class FourCopperMapping(unittest.TestCase):
    def test_four_complete_mapping_and_existing_two_receipt_branch(self):
        self.assertTrue(n.audit_mapping(*four_mapping())['passed'])
        tree,native,project=fixtures();self.assertNotIn('copper_layers',native)
        result=n.audit_mapping(tree,native,project)
        self.assertEqual(result['membership'],{'DATA':'kicad_default','GND':'Power'})
        self.assertTrue(all('Via[0-1]' in row['via'] for row in result['classes']))

    def test_wrong_native_order_id_type_alias_or_missing_metadata_refuses(self):
        for change in ('order','id','type','alias','duplicate','missing'):
            tree,native,project=four_mapping();rows=native['copper_layers']
            if change=='order':rows[1],rows[2]=rows[2],rows[1]
            elif change=='id':rows[1]['id']=6
            elif change=='type':rows[1]['type']='power'
            elif change=='alias':rows[1]['name']='Inner power'
            elif change=='duplicate':rows[2]=copy.deepcopy(rows[1])
            else:del native['copper_layers']
            with self.subTest(change=change),self.assertRaises(ValueError):n.audit_mapping(tree,native,project)

    def test_dsn_layer_order_index_duplicate_and_foreign_layer_refuse(self):
        for change in ('order','index','duplicate','foreign'):
            tree,native,project=four_mapping();layers=sx.children(sx.one(tree,'structure'),'layer')
            if change=='order':layers[1][1],layers[2][1]=layers[2][1],layers[1][1]
            elif change=='index':sx.one(layers[2],'property')[1][1]='1'
            elif change=='duplicate':layers[2][1]=layers[1][1]
            else:layers[2][1]='In3.Cu'
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'layer order/index'):n.audit_mapping(tree,native,project)

    def test_inner_via_shape_missing_duplicate_foreign_or_diameter_refuse(self):
        for change in ('missing','duplicate','foreign','diameter'):
            tree,native,project=four_mapping();stack=sx.children(sx.one(tree,'library'),'padstack')[1];shapes=sx.children(stack,'shape')
            if change=='missing':stack.remove(shapes[2])
            elif change=='duplicate':sx.one(shapes[2],'circle')[1]='In1.Cu'
            elif change=='foreign':sx.one(shapes[2],'circle')[1]='In3.Cu'
            else:sx.one(shapes[2],'circle')[2]='1500'
            with self.subTest(change=change),self.assertRaises(ValueError):n.audit_mapping(tree,native,project)

    def test_unused_declared_blind_buried_via_also_refuses(self):
        for span in ('0-1','1-2','1-3'):
            tree,native,project=four_mapping();old=sx.children(sx.one(tree,'library'),'padstack')[0];extra=copy.deepcopy(old)
            extra[1]='"Via['+span+']_1400:600_um"';sx.one(tree,'library').append(extra);sx.one(sx.one(tree,'structure'),'via').append(extra[1])
            with self.subTest(span=span),self.assertRaisesRegex(ValueError,'full through-via'):n.audit_mapping(tree,native,project)

    def test_pipeline_reader_binds_exported_marker_to_reconstructed_source(self):
        # Producer already audits the current task candidate. Retained readback
        # must check the export marker against task reconstructed from SOURCE.
        tree=ast.parse(Path(p.__file__).read_text())
        checker=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='_check_result_uncached')
        calls=[node for node in ast.walk(checker) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)]
        self.assertTrue(any(node.func.id=='four_copper_source_layers' and len(node.args)==1 and isinstance(node.args[0],ast.Name) and node.args[0].id=='task' for node in calls))
        self.assertTrue(any(node.func.id=='four_copper_native_layers' and len(node.args)==1 and isinstance(node.args[0],ast.Name) and node.args[0].id=='exported' for node in calls))

    def test_inner_terminal_count_and_class_parent_tamper_refuse(self):
        tree,native,project=four_mapping();native['nets'][0]['copper_pad_count']=2
        with self.assertRaisesRegex(ValueError,'terminal count'):n.audit_mapping(tree,native,project)
        from tests.test_netclass_parent_policy import example
        tree,native,project=example();native['copper_layers']=four_mapping()[1]['copper_layers']
        native['nets'][1]['parameter_parents']['width_nm']['name']='Default'
        with self.assertRaisesRegex(ValueError,'dimension parent'):n.audit_native(native,project,parent_policy=True)


class FourCopperNativeCensus(unittest.TestCase):
    def observe(self,count=4,**altered):
        # Execute only the actual worker function with a scalar-only API double.
        module=ast.parse(Path(p.c.ROOT/'autorouter/native.py').read_text())
        node=next(row for row in module.body if isinstance(row,ast.FunctionDef) and row.name=='netclasses')
        ids={'F.Cu':0,'In1.Cu':4,'In2.Cu':6,'B.Cu':2};calls=[];floor_calls=[]
        expected_floors=dict(zip(FLOORS,(300000,200000,900000,400000,250000)))
        def settings():
            floor_calls.append('loaded settings')
            return NS(**{attribute:expected_floors[key] for key,attribute in FLOORS.items()})
        def pad(layers,code=1):return NS(GetNetCode=lambda:code,GetNetname=lambda:'INNER',IsOnLayer=lambda layer:layer in layers)
        net=NS(GetNetCode=lambda:1,GetNetClassSlow=lambda:None)
        board=NS(SynchronizeNetsAndNetClasses=lambda flag:calls.append(flag),GetCopperLayerCount=lambda:count,
            GetLayerID=lambda name:ids[name],GetLayerName=lambda layer:next(name for name,code in ids.items() if code==layer),
            IsLayerEnabled=lambda layer:layer in ids.values(),GetLayerType=lambda _:0,
            GetPads=lambda:[pad({4}),pad({0,2,4,6}),pad({0,2}),pad({4},0)],GetNetsByName=lambda:{'INNER':net},
            GetDesignSettings=settings)
        for name,value in altered.items():setattr(board,name,value)
        native=NS(F_Cu=0,B_Cu=2,In1_Cu=4,In2_Cu=6,LT_SIGNAL=0,GetBuildVersion=lambda:'10.0.0')
        namespace=dict(pcbnew=native,Path=Path,file_hash=lambda _: 'fixed',
            observe_class=lambda _:dict(**{'class':'Default'}),observe_floors=observe_floors)
        exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-native-netclasses','exec'),namespace)
        result=namespace['netclasses'](board,'/owned/source.kicad_pcb',('fixed','fixed'))
        self.assertEqual(calls,[False]);self.assertEqual(floor_calls,['loaded settings'])
        self.assertEqual(result['effective_floors_nm'],expected_floors);return result

    def test_inner_only_and_all_layer_pads_count_once_each(self):
        result=self.observe();self.assertEqual(result['nets'][0]['copper_pad_count'],3)
        self.assertEqual(n.four_copper_native_layers(result),list(n.FOUR_COPPER_NAMES))

    def test_two_layer_shape_and_count_remain_legacy(self):
        result=self.observe(count=2);self.assertNotIn('copper_layers',result)
        self.assertEqual(result['nets'][0]['copper_pad_count'],2)

    def test_native_alias_disabled_layer_wrong_id_or_power_type_refuse(self):
        for change in (dict(GetLayerName=lambda _:'alias'),dict(IsLayerEnabled=lambda _:False),
                       dict(GetLayerID=lambda _:-1),dict(GetLayerType=lambda _:1)):
            with self.subTest(api=next(iter(change))),self.assertRaises(ValueError):self.observe(**change)


class FourCopperOwnedSource(unittest.TestCase):
    def test_factory_is_distinct_complete_and_does_not_mutate_seed_generator(self):
        before=fixture.base.files();files=fixture.files();self.assertEqual(before,fixture.base.files())
        self.assertEqual(set(files),{fixture.STEM+suffix for suffix in ('.kicad_pcb','.kicad_pro','.kicad_sch','.kicad_prl')})
        tree=sx.parse(files[fixture.STEM+'.kicad_pcb'].decode())
        self.assertEqual(n.four_copper_source_layers(tree),list(n.FOUR_COPPER_NAMES))
        self.assertEqual(sx.children(tree,'zone'),[]);self.assertEqual(len(sx.children(tree,'via')),0)
        self.assertEqual(len(sx.children(tree,'footprint')),6);self.assertEqual(len(p.routes(tree)),1)
        self.assertTrue(p.locked(p.routes(tree)[0]));self.assertEqual(sx.one(p.routes(tree)[0],'width'),['width','0.3'])
        for name,raw in files.items():self.assertNotIn(fixture.base.SOURCE_ID.encode(),raw)

    def test_prospective_preflight_and_source_bytes_stay_exact(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp).resolve()/'owned';fixture.write_project(folder);board=folder/(fixture.STEM+'.kicad_pcb')
            before=p.tree_hash(folder);p.preflight(board);self.assertEqual(p.tree_hash(folder),before)
            self.assertEqual(p.netclass_policy(board)['mode'],n.PARENT_POLICY)

    def test_noncanonical_source_layers_and_stackup_refuse(self):
        original=sx.parse(fixture.files()[fixture.STEM+'.kicad_pcb'].decode())
        for change in ('order','duplicate','alias','foreign','type','stackup'):
            tree=copy.deepcopy(original);layers=sx.one(tree,'layers')
            if change=='order':layers[2],layers[3]=layers[3],layers[2]
            elif change=='duplicate':layers.append(copy.deepcopy(layers[2]))
            elif change=='alias':layers[2][1]='"inner power"'
            elif change=='foreign':layers.append(['8','"In3.Cu"','signal'])
            elif change=='type':layers[2][2]='power'
            else:sx.one(tree,'setup').append(['stackup',*([['layer','"'+name+'"',['type','"copper"']] for name in reversed(n.FOUR_COPPER_NAMES)])])
            with self.subTest(change=change),self.assertRaises(ValueError):n.four_copper_source_layers(tree)

    def test_candidate_requires_source_bound_four_layer_native_marker_and_exact_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp).resolve()/'owned';fixture.write_project(folder);board=folder/(fixture.STEM+'.kicad_pcb')
            project=json.loads(board.with_suffix('.kicad_pro').read_text());configured={row['name']:row for row in project['net_settings']['classes']};rows=[]
            for code,(name,cls) in enumerate((('KEEP','Default'),('ROUTE','POWER'),('GND','SIGNAL')),1):
                source=configured[cls];values={key:round(source[setting]*1000000) for key,setting,_ in n._DIMENSIONS}
                rows.append(dict(name=name,netcode=code,**{'class':cls if cls=='Default' else cls+',Default'},copper_pad_count=2,**values,
                    parameter_parents={key:dict(name=cls,value_nm=values[key],specified=True,priority=source['priority']) for key,_,_ in n._DIMENSIONS}))
            native=dict(schema=1,native_version='10.0.0',units='integer nanometres',source=str(board),board_sha256=p.sha(board),
                project_sha256=p.sha(board.with_suffix('.kicad_pro')),board_saved=False,nets=rows,copper_layers=four_mapping()[1]['copper_layers'])
            protected=p.routes(sx.read(board));self.assertTrue(p.audit_candidate_netclasses(board,protected,native)['native']['passed'])
            missing=copy.deepcopy(native);del missing['copper_layers']
            with self.assertRaises(ValueError):p.audit_candidate_netclasses(board,protected,missing)
            tampered=copy.deepcopy(native);tampered['nets'][1]['parameter_parents']['width_nm']['name']='Default'
            with self.assertRaisesRegex(ValueError,'dimension parent'):p.audit_candidate_netclasses(board,protected,tampered)

    def test_foreign_source_route_layer_refuses(self):
        tree=sx.parse(fixture.files()[fixture.STEM+'.kicad_pcb'].decode())
        sx.one(p.routes(tree)[0],'layer')[1]='"In3.Cu"'
        with self.assertRaisesRegex(ValueError,'foreign four-copper route'):n.four_copper_source_layers(tree)

    def test_partial_blind_buried_nonuniform_source_vias_refuse(self):
        original=sx.parse(fixture.files()[fixture.STEM+'.kicad_pcb'].decode())
        for change in ('partial','blind','buried','micro','padstack','remove_unused'):
            tree=copy.deepcopy(original);via=['via',['at','20','10'],['size','1.2'],['drill','0.5'],['layers','"F.Cu"','"B.Cu"'],['net','"ROUTE"']]
            if change=='partial':sx.one(via,'layers')[2]='"In1.Cu"'
            elif change=='padstack':via.append(['padstack'])
            elif change=='remove_unused':via.append(['remove_unused_layers','yes'])
            else:via.append(change)
            tree.append(via)
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'uniform full through-vias'):n.four_copper_source_layers(tree)


class FourCopperNoncopperDisplay(unittest.TestCase):
    def source(self):
        return sx.parse(fixture.files()[fixture.STEM+'.kicad_pcb'].decode())

    def row(self,tree,code='5'):
        return next(row for row in sx.one(tree,'layers')[1:] if row[0]==code)

    def aliases(self,tree):
        for code,label in (('5','F.Silkscreen'),('7','B.Silkscreen'),
                           ('31','F.Courtyard'),('29','B.Courtyard')):
            self.row(tree,code).append(json.dumps(label))
        return tree

    def test_display_metadata_preserves_canonical_result_and_complete_ast(self):
        tree=self.aliases(self.source());before=copy.deepcopy(tree)
        encoded=sx.dump(tree)
        self.assertEqual(n.four_copper_source_layers(tree),list(n.FOUR_COPPER_NAMES))
        self.assertEqual(tree,before);self.assertEqual(sx.dump(tree),encoded)
        # No non-layer source field, including the protected route, is changed.
        without=copy.deepcopy(tree)
        for row in sx.one(without,'layers')[1:]:del row[3:]
        self.assertEqual(without,self.source())

    def test_complete_owned_project_preflight_keeps_every_file_exact(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp).resolve()/'owned';fixture.write_project(folder)
            board=folder/(fixture.STEM+'.kicad_pcb')
            expected=self.aliases(sx.read(board));sx.write(board,expected)
            before=p.tree_hash(folder)
            self.assertEqual(p.preflight(board),expected)
            self.assertEqual(p.netclass_policy(board)['mode'],n.PARENT_POLICY)
            self.assertEqual(p.tree_hash(folder),before)

    def test_display_bytes_and_supported_escaping_are_bounded(self):
        for label in ('F.SilkS','a'*256,'μ'*128,'Front "silk" \\ drawing'):
            tree=self.source();self.row(tree).append(json.dumps(label,ensure_ascii=False))
            with self.subTest(label=label):
                self.assertEqual(n.four_copper_source_layers(tree),list(n.FOUR_COPPER_NAMES))
        for atom in ('"'+('a'*257)+'"','"'+('μ'*129)+'"','"'+('a'*515)+'"',
                     'unquoted','"unterminated','"bad"quote"','"bad\\q"','""',
                     '" leading"','"trailing "','"line\nbreak"','"tab\tbreak"',
                     '"nul\x00byte"','"delete\x7fbyte"','"\ud800"'):
            tree=self.source();self.row(tree).append(atom)
            with self.subTest(atom=repr(atom)),self.assertRaisesRegex(ValueError,'display name'):
                n.four_copper_source_layers(tree)

    def test_canonical_and_display_collisions_refuse_including_later_rows(self):
        # Reserve every supported canonical name, even an absent noncopper row.
        for label in ('F.Cu','in1.cu','B.Cu','f.silks','B.CrtYd','User.4'):
            tree=self.source();self.row(tree).append(json.dumps(label))
            with self.subTest(label=label),self.assertRaisesRegex(ValueError,'colliding'):
                n.four_copper_source_layers(tree)
        for first,second in (('Drawing','Drawing'),('Drawing','drawing'),('Straße','STRASSE'),
                             ('Front "silk"','Front "silk"')):
            tree=self.source();self.row(tree).append(json.dumps(first,ensure_ascii=False))
            self.row(tree,'7').append(json.dumps(second,ensure_ascii=False))
            with self.subTest(labels=(first,second)),self.assertRaisesRegex(ValueError,'colliding'):
                n.four_copper_source_layers(tree)

    def test_display_atom_cannot_hide_physical_identity_or_copper_alias(self):
        for change in ('foreign_id','wrong_canonical','wrong_type','duplicate_id',
                       'copper_alias','nested_atom','extra_atom','physical_order','stackup','via_span'):
            tree=self.aliases(self.source());row=self.row(tree);layers=sx.one(tree,'layers')
            if change=='foreign_id':row[0]='999'
            elif change=='wrong_canonical':row[1]='"F.Adhes"'
            elif change=='wrong_type':row[2]='signal'
            elif change=='duplicate_id':row[0]='7'
            elif change=='copper_alias':layers[1].append('"Front copper"')
            elif change=='nested_atom':row[3]=['display','"Front"']
            elif change=='extra_atom':row.append('"extra"')
            elif change=='physical_order':layers[2],layers[3]=layers[3],layers[2]
            elif change=='stackup':sx.one(tree,'setup').append(['stackup',
                *[['layer',json.dumps(name),['type','copper']] for name in reversed(n.FOUR_COPPER_NAMES)]])
            else:tree.append(['via',['at','20','10'],['size','1.2'],['drill','0.5'],
                              ['layers','"F.Cu"','"In1.Cu"'],['net','"ROUTE"']])
            with self.subTest(change=change),self.assertRaises(ValueError):n.four_copper_source_layers(tree)

    def test_preflight_rejects_display_collision_without_rewriting_project(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp).resolve()/'owned';fixture.write_project(folder)
            board=folder/(fixture.STEM+'.kicad_pcb');tree=self.source()
            self.row(tree).append('"In1.Cu"');sx.write(board,tree)
            before=p.tree_hash(folder)
            with self.assertRaisesRegex(p.Rejected,'colliding noncopper display name'):p.preflight(board)
            self.assertEqual(p.tree_hash(folder),before)

if __name__=='__main__':unittest.main()
