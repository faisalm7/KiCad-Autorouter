"""Pure edge transport falsifiers; these do not establish native acceptance."""
import copy
import hashlib
import json
import unittest
from autorouter import adapter as a, native_edge as edge, sexpr as sx

BOARD = b'''(kicad_pcb (version 20241229)
 (gr_rect (start 0 0) (end 20 20) (stroke (width 0.05) (type default))
 (fill no) (layer "Edge.Cuts") (uuid "outline"))
 (footprint "part" (layer "F.Cu") (at 1 1)
 (fp_rect (start -1 -1) (end 1 1) (layer "F.SilkS"))))'''
PROJECT = {'board': {'design_settings': {'rules': {'min_copper_edge_clearance': .3}}},
           'net_settings': {'classes': [{'name': 'Default'}], 'netclass_assignments': None, 'netclass_patterns': []}}
DSN = '''(pcb task (parser (string_quote ") (host_cad "KiCad's Pcbnew"))
 (resolution um 10) (unit um)
 (structure (layer top (type signal)) (layer bottom (type signal))
 (boundary (rect pcb 0 -20000 20000 0))
 (keepout original (rect bottom 0 1 2 3))
 (rule (width 200) (clearance 200) (clearance 50 (type smd_smd)))
 (unknown (value "preserve () ; café")))
 (placement (component part (place U1 1000 -1000 front 90)))
 (library (image part (pin pad1 1 0 0)))
 (network (net GND (pins U1-1))
 (class kicad_default GND (circuit (use_via via)) (rule (width 200) (clearance 200))))
 (wiring (wire (path top 200 1 2 3 4) (net GND))))'''


class NativeEdgeTests(unittest.TestCase):
    def context(self, board=BOARD, project=None):
        return edge.derive_context(board,json.dumps(PROJECT if project is None else project).encode())

    def correct(self, dsn=DSN, context=None):
        return edge.correct(dsn.encode(),self.context() if context is None else context)

    def test_only_original_edge_boundary_class_and_three_exact_pairs_change(self):
        board, project = BOARD, json.dumps(PROJECT).encode()
        context=edge.derive_context(board,project);before=copy.deepcopy(context)
        corrected,record=edge.correct(DSN.encode(),context)
        tree=a._parse_dsn(corrected.decode());original=a._parse_dsn(DSN)
        structure=sx.one(tree,'structure');boundary=sx.one(structure,'boundary')
        self.assertEqual(boundary.pop(),['clearance_class','kicadedge'])
        self.assertEqual(structure.pop(),['rule',
            ['clearance','300',['type','default_kicadedge']],
            ['clearance','300',['type','smd_kicadedge']],
            ['clearance','300',['type','kicadedge_kicadedge']]])
        self.assertEqual(tree,original)
        self.assertEqual(context,before)
        self.assertEqual(record['source_sha256'],{'board':hashlib.sha256(board).hexdigest(),'project':hashlib.sha256(project).hexdigest()})
        self.assertEqual(record['input_sha256'],hashlib.sha256(DSN.encode()).hexdigest())
        self.assertEqual(record['output_sha256'],hashlib.sha256(corrected).hexdigest())
        self.assertTrue(record['exact_edge_only_ast_edit'])
        self.assertTrue(record['requires_no_custom_rule_companion'])
        self.assertFalse(record['native_project_modified']);self.assertFalse(record['routing_accepted'])

    def test_zero_width_closed_rectangular_path_in_either_orientation(self):
        for path in ('0 -20000 20000 -20000 20000 0 0 0 0 -20000',
                     '20000 0 20000 -20000 0 -20000 0 0 20000 0'):
            raw=DSN.replace('(rect pcb 0 -20000 20000 0)','(path pcb 0 '+path+')')
            result,record=self.correct(raw);self.assertTrue(record['applied'])
            self.assertEqual(sx.one(sx.one(a._parse_dsn(result.decode()),'structure'),'boundary')[1],
                ['path','pcb','0',*path.split()])

    def test_reversed_native_rectangle_corners_and_project_companion_hashes(self):
        reversed_board=BOARD.replace(b'(start 0 0) (end 20 20)',b'(start 20 20) (end 0 0)')
        context=self.context(reversed_board)
        self.assertEqual(context['rect_um'],self.context()['rect_um'])
        self.assertNotEqual(context['source_sha256']['board'],self.context()['source_sha256']['board'])
        changed=copy.deepcopy(PROJECT);changed['meta']={'author':'project-owned control'}
        self.assertNotEqual(self.context(project=changed)['source_sha256']['project'],self.context()['source_sha256']['project'])

    def test_zero_missing_and_unsupported_native_scope_are_byte_exact_noops(self):
        cases=[]
        zero=copy.deepcopy(PROJECT);zero['board']['design_settings']['rules']['min_copper_edge_clearance']=0;cases.append((BOARD,zero))
        missing=copy.deepcopy(PROJECT);del missing['board']['design_settings']['rules']['min_copper_edge_clearance'];cases.append((BOARD,missing))
        multiple=copy.deepcopy(PROJECT);multiple['net_settings']['classes'].append({'name':'Power'});cases.append((BOARD,multiple))
        pattern=copy.deepcopy(PROJECT);pattern['net_settings']['netclass_patterns']=[{'pattern':'GND','netclass':'Default'}];cases.append((BOARD,pattern))
        custom=copy.deepcopy(PROJECT);custom['board']['design_settings']['custom_rules']=['unqualified'];cases.append((BOARD,custom))
        cases.extend((board,PROJECT) for board in (
            BOARD.replace(b'gr_rect',b'gr_poly'),
            BOARD.replace(b'(fill no)',b'(angle 45) (fill no)'),
            BOARD.replace(b'(layer "F.SilkS")',b'(layer "Edge.Cuts")'),
            BOARD.replace(b'(layer "Edge.Cuts")',b'(layer "F.SilkS")'),
            BOARD.replace(b'(version 20241229)',b'(version 20241229) (gr_line (start 1 1) (end 2 2) (layer "Edge.Cuts"))')))
        cases.append((BOARD.replace(b'(version 20241229)',b'(version 20241229) (rules (edge 0.3))'),PROJECT))
        for board,project in cases:
            with self.subTest(board=board,project=project):
                context=self.context(board,project)
                self.assertFalse(context['applicable']);self.assertTrue(context['reason'])
                corrected,record=self.correct(context=context)
                self.assertEqual(corrected,DSN.encode());self.assertFalse(record['applied'])

    def test_nonfinite_negative_boolean_string_and_duplicate_source_values_reject(self):
        for value in (float('nan'),float('inf'),-.1,True,'0.3'):
            changed=copy.deepcopy(PROJECT);changed['board']['design_settings']['rules']['min_copper_edge_clearance']=value
            with self.subTest(value=value),self.assertRaises(ValueError):self.context(project=changed)
        for board in (BOARD.replace(b'(start 0 0)',b'(start NaN 0)'),
                      BOARD.replace(b'(start 0 0)',b'(start 0 0) (start 0 0)'),
                      BOARD.replace(b'(end 20 20)',b'(end 0 20)'),
                      BOARD.replace(b'(uuid "outline")',b'(uuid "outline") (uuid "other")')):
            with self.subTest(board=board),self.assertRaises(ValueError):self.context(board)
        raw=json.dumps(PROJECT).replace('"min_copper_edge_clearance": 0.3','"min_copper_edge_clearance": 0.3, "min_copper_edge_clearance": 0.2').encode()
        with self.assertRaisesRegex(ValueError,'duplicate project key'):edge.derive_context(BOARD,raw)

    def test_dsn_namespaces_unknown_types_duplicate_scopes_and_units_reject_before_edit(self):
        cases=[DSN.replace('(unit um)','(unit mil)'),DSN.replace('(unit um)','(unit um) (unit um)'),
            DSN.replace('(resolution um 10)','(resolution um NaN)'),
            DSN.replace('(resolution um 10)','(resolution um 10.5)'),
            DSN.replace('(unknown (value','(unknown (unit um) (value'),
            DSN.replace('(rect pcb 0 -20000 20000 0))','(rect pcb 0 -20000 20000 0) (clearance_class existing))'),
            DSN.replace('(net GND','(net kicadedge'),
            DSN.replace('(type smd_smd)','(type default_smd)'),
            DSN.replace('(clearance 200)','(clearance NaN)',1),
            DSN.replace('(clearance 200)','(clearance -1)',1),
            DSN.replace('(rule (width 200)','(rule (width NaN)',1),
            DSN.replace('(unknown (value','(unknown (class custom) (value'),
            DSN.replace('(unknown (value','(unknown (clearance 400) (value'),
            DSN.replace('(unknown (value','(unknown (rule (clearance 300)) (value'),
            DSN.replace('(unknown (value','(unknown (layer_rule top (clearance 300)) (value'),
            DSN.replace('(class kicad_default','(class other'),
            DSN.replace('(network','(network (class other)'),
            DSN.replace('(structure','(structure) (structure',1),
            DSN.replace('(network','(network) (network',1),
            DSN.replace('(rule (width 200)','(rule (width 200) (clearance 200) (clearance 50 (type smd_smd))) (rule (width 200)',1),
            DSN.replace('(boundary','(boundary (rect pcb 0 -20000 20000 0)) (boundary',1)]
        for raw in cases:
            with self.subTest(raw=raw),self.assertRaises(ValueError):self.correct(raw)

    def test_changed_nonrectangular_nonzero_width_boundary_and_export_rounding_reject(self):
        shapes=['(rect pcb 0 -20000 19999 0)','(rect signal 0 -20000 20000 0)',
            '(path pcb 1 0 -20000 20000 -20000 20000 0 0 0 0 -20000)',
            '(path pcb 0 0 -20000 20000 0 20000 -20000 0 0 0 -20000)',
            '(path pcb 0 0 -20000 20000 -20000 20000 0 0 0 0 0)']
        for shape in shapes:
            with self.subTest(shape=shape),self.assertRaises(ValueError):self.correct(DSN.replace('(rect pcb 0 -20000 20000 0)',shape))
        tiny=BOARD.replace(b'(start 0 0)',b'(start 0.00001 0)')
        with self.assertRaisesRegex(ValueError,'export precision'):self.correct(context=self.context(tiny))

    def fractional(self):
        board=BOARD.replace(b'(start 0 0) (end 20 20)',b'(start 0.00025 0) (end 20.00025 20)')
        dsn=DSN.replace('(host_cad "KiCad\'s Pcbnew")','(host_cad "KiCad\'s Pcbnew") (host_version "10.0.0")')
        return board,dsn,self.context(board)

    def test_fractional_rectangle_is_rounded_only_inside_exact_source_and_rule_unchanged(self):
        from decimal import Decimal
        board,dsn,context=self.fractional();before=copy.deepcopy(context)
        raw,record=self.correct(dsn,context);proof=record['inward_boundary']
        self.assertEqual(context,before);self.assertTrue(proof['output_within_original_boundary'])
        self.assertEqual(proof['output_bounds_um'],['0.3','-20000','20000.2','0'])
        self.assertEqual(record['requested_clearance_um'],'300')
        source=list(map(Decimal,proof['source_bounds_um']));target=list(map(Decimal,proof['output_bounds_um']))
        self.assertTrue(target[0]>=source[0] and target[1]>=source[1] and target[2]<=source[2] and target[3]<=source[3])
        self.assertTrue(all(v*10==(v*10).to_integral_value() for v in target))
        tree=a._parse_dsn(raw.decode());original=a._parse_dsn(dsn);bound=sx.one(sx.one(tree,'structure'),'boundary')
        self.assertEqual(bound[1],['rect','pcb','0.3','-20000','20000.2','0'])
        bound.pop();bound[1]=copy.deepcopy(sx.one(sx.one(original,'structure'),'boundary')[1]);sx.one(tree,'structure').pop()
        self.assertEqual(tree,original)

    def test_fractional_path_keeps_closed_side_order_and_every_other_dsn_node(self):
        board,dsn,context=self.fractional()
        for path in ('0 -20000 20000 -20000 20000 0 0 0 0 -20000','20000 0 20000 -20000 0 -20000 0 0 20000 0'):
            text=dsn.replace('(rect pcb 0 -20000 20000 0)','(path pcb 0 '+path+')')
            raw,record=self.correct(text,context);shape=sx.one(sx.one(a._parse_dsn(raw.decode()),'structure'),'boundary')[1]
            values=shape[3:];self.assertEqual(values[:2],values[-2:]);self.assertEqual(shape[:3],['path','pcb','0'])
            self.assertEqual(set(values[::2]),{'0.3','20000.2'})
            self.assertEqual(record['inward_boundary']['input_boundary_ast_sha256'],a._digest(sx.dump(sx.one(sx.one(a._parse_dsn(text),'structure'),'boundary')[1]).encode()))

    def test_fractional_outside_observed_guard_or_wrong_host_grid_refuses(self):
        board,dsn,context=self.fractional()
        for text in (dsn.replace('(host_version "10.0.0")','(host_version "10.0.7")'),
                dsn.replace('(host_version "10.0.0")',''),dsn.replace('(resolution um 10)','(resolution um 100)'),
                dsn.replace('(rect pcb 0 -20000 20000 0)','(rect pcb -0.251 -20000 20000 0)')):
            with self.subTest(text=text),self.assertRaises(ValueError):self.correct(text,context)
        # Guard is inclusive at .5um, but target still comes solely from source.
        raw,_=self.correct(dsn.replace('(rect pcb 0 -20000 20000 0)','(rect pcb -0.25 -20000 20000.75 0)'),context)
        self.assertIn(b'0.3 -20000 20000.2 0',raw)

    def test_degenerate_observed_rectangle_cannot_invent_a_valid_output_bound(self):
        board,dsn,context=self.fractional();context['rect_um']=['0.05','-20000','0.25','0']
        text=dsn.replace('(rect pcb 0 -20000 20000 0)','(rect pcb 0 -20000 0 0)')
        with self.assertRaisesRegex(ValueError,'degenerate rectangle'):self.correct(text,context)

    def test_fractional_subgrid_board_collapses_instead_of_expanding(self):
        board,dsn,context=self.fractional();context['rect_um']=['0.01','-20000','0.09','0']
        text=dsn.replace('(rect pcb 0 -20000 20000 0)','(rect pcb 0 -20000 0.1 0)')
        with self.assertRaisesRegex(ValueError,'no area'):self.correct(text,context)

    def test_near_threshold_grid_rounding_never_reduces_original_edge_margin(self):
        from decimal import Decimal
        board,dsn,context=self.fractional();_,record=self.correct(dsn,context)
        right=Decimal(record['inward_boundary']['output_bounds_um'][2]);original_right=Decimal(record['inward_boundary']['source_bounds_um'][2]);rule=Decimal(record['requested_clearance_um'])
        # A legal item edge at the transformed boundary's exact margin keeps
        # at least the entire original margin. An outward nearest-grid choice
        # would lose .05um and this geometric counterexample would fail.
        self.assertGreaterEqual(original_right-(right-rule),rule)
        self.assertLess(original_right-(Decimal('20000.3')-rule),rule)

    def test_repeat_application_and_tampered_minimum_reject(self):
        corrected,_=self.correct()
        with self.assertRaises(ValueError):edge.correct(corrected,self.context())
        context=self.context();context['requested_clearance_um']='200'
        with self.assertRaisesRegex(ValueError,'original minimum'):self.correct(context=context)

    def test_unknown_incomplete_or_ambiguous_context_rejects(self):
        cases=[None,{},dict(self.context(),unknown='must not silently parse'),
            dict(self.context(),source_sha256={'board':'bad','project':'bad'}),
            dict(self.context(),schema=True),dict(self.context(),requires_no_custom_rule_companion=False),
            dict(self.context(),rect_um=['0','0','0','0'])]
        partial=self.context();del partial['source_edge_sha256'];cases.append(partial)
        for context in cases:
            with self.subTest(context=context),self.assertRaises(ValueError):edge.correct(DSN.encode(),context)

    def test_duplicate_native_root_start_end_layer_and_project_class_names_reject(self):
        for key,original in [('start',b'(start 0 0)'),('end',b'(end 20 20)'),('layer',b'(layer "Edge.Cuts")')]:
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'duplicate singleton'):
                self.context(BOARD.replace(original,original+b' '+original,1))
        project=copy.deepcopy(PROJECT);project['net_settings']['classes'].append({'name':'default'})
        with self.assertRaisesRegex(ValueError,'ambiguous source class'):self.context(project=project)

    def test_root_stackup_repeated_layer_definitions_preserve_exact_edge_rule(self):
        stackup=b'(setup (stackup (layer "F.Cu" (type "copper") (thickness 0.035)) (layer "dielectric 1" (type "core") (thickness 1.51)) (layer "B.Cu" (type "copper") (thickness 0.035))))'
        board=BOARD.replace(b'(version 20241229)',b'(version 20241229) '+stackup)
        context=self.context(board);base=self.context()
        self.assertTrue(context['applicable'])
        for field in ('rect_um','source_edge_sha256','requested_clearance_um','original_min_copper_edge_clearance_mm'):
            self.assertEqual(context[field],base[field])
        self.assertEqual(context['source_sha256']['board'],hashlib.sha256(board).hexdigest())
        self.assertEqual(self.correct(context=context)[0],self.correct()[0])

    def test_stackup_exception_does_not_hide_nested_or_other_duplicate_selectors(self):
        for extra in (b'(footprint "part" (stackup (layer "F.Cu") (layer "B.Cu")))',
                      b'(setup (other (layer "F.Cu") (layer "B.Cu")))',
                      b'(setup (stackup (layer "F.Cu" (layer "Edge.Cuts") (layer "Edge.Cuts"))))',
                      b'(setup (stackup) (stackup))'):
            board=BOARD.replace(b'(version 20241229)',b'(version 20241229) '+extra)
            with self.subTest(extra=extra),self.assertRaisesRegex(ValueError,'duplicate singleton'):
                self.context(board)

    def test_bounded_malformed_inputs_reject(self):
        for raw in ('text',b'',b'\xff',b'(pcb incomplete'):
            with self.subTest(raw=raw),self.assertRaises((ValueError,TypeError)):edge.correct(raw,self.context())
        with self.assertRaises(ValueError):edge.derive_context(b'(wrong_root)',json.dumps(PROJECT).encode())
        with self.assertRaises(ValueError):edge.derive_context(BOARD,b'[]')
        with self.assertRaises(ValueError):self.correct(context={'schema':9,'policy':'unknown'})


if __name__=='__main__':unittest.main()
