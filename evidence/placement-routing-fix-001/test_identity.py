"""Actual retained native export + pure mutations; no native or engine execution."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import board_floor as old,pipeline as p,sexpr as sx,floor_route as f
spec=importlib.util.spec_from_file_location('fixed_board_floor',HERE/'board_floor.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
spec=importlib.util.spec_from_file_location('retained_placement_transform',ROOT/'experiments/placement_diagnostic_v1/placement_transform.py');placement=importlib.util.module_from_spec(spec);spec.loader.exec_module(placement)
RUN=ROOT/'.runs/placement-routing-fixture-001'

def inputs():
    task=sx.read(RUN/'floor-export-input/fixture.kicad_pcb');project=(RUN/'floor-export-input/fixture.kicad_pro').read_bytes()
    return task,project,f.read_json(RUN/'floor-export-context.json'),(RUN/'native.dsn').read_bytes()

def inventory(path):return {str(x.relative_to(path)):x.read_bytes()for x in path.rglob('*')if x.is_file()}

class SavedEvidenceTests(unittest.TestCase):
    def setUp(self):self.task,self.project,self.native,self.raw=inputs()
    def test_actual_failure_reproduced_without_native(self):
        with self.assertRaisesRegex(ValueError,'unqualified named task net reference'):old.transform(self.raw,self.native,self.project,(sx.dump(self.task)+'\n').encode())
    def test_actual_all_bindings_and_strict_floor_transform_pass(self):
        receipt=f.read_json(RUN/'result.json');expected=p.tree_hash(RUN/'floor-export-input')
        self.assertEqual(receipt['source_hashes'],p.tree_hash(RUN/'snapshot'))
        self.assertEqual(receipt['source_hashes'],p.tree_hash(Path(receipt['source']).parent))
        f.context_binding(self.native,RUN/'floor-export-input/fixture.kicad_pcb',expected,'export',g.sha(self.raw))
        original=inventory(RUN/'snapshot');native_input=inventory(RUN/'floor-export-input');placement.native_binding(original,native_input,'fixture.kicad_pcb',f.read_json(RUN/'area-context.json'),self.raw)
        unchanged=sx.dump(self.task);guided,audit=g.transform(self.raw,self.native,self.project,(sx.dump(self.task)+'\n').encode())
        self.assertEqual(unchanged,sx.dump(self.task));self.assertEqual(audit['targets_nm'],{'width_nm':300000,'clearance_nm':300000,'via_diameter_nm':1500000,'via_drill_nm':300000})
        corrected,removal=placement.transform(original,native_input,'fixture.kicad_pcb',f.read_json(RUN/'area-context.json'),self.raw,guided)
        self.assertEqual(removal['removed_count'],2);self.assertEqual(g.adapter_bytes(corrected,self.native['obstacles']),corrected)
        self.assertEqual(g.task_pads(self.task),old.task_pads([x for x in self.task if not isinstance(x,list)or not x or x[0]!='zone']))
    def test_named_pads_and_legacy_numbered_tables_have_same_terminal_identity(self):
        named=g.task_pads(self.task);numbered=copy.deepcopy(self.task);numbered.extend([['net','0','""'],['net','1','"SIGNAL_A"'],['net','2','"SIGNAL_B"']])
        for fp in sx.children(numbered,'footprint'):
            pad=sx.children(fp,'pad')[0];name=sx.one(pad,'net')[1];sx.one(pad,'net')[:]=['net','1'if name=='"SIGNAL_A"'else'2',name]
        self.assertEqual(g.task_pads(numbered),named);self.assertEqual(old.task_pads(numbered),named)
        self.assertEqual(g.qualify(json.loads(self.project),self.native,numbered),g.qualify(json.loads(self.project),self.native,self.task))
    def test_terminal_net_swap_rejected_even_when_net_counts_unchanged(self):
        pads=[sx.children(fp,'pad')[0]for fp in sx.children(self.task,'footprint')]
        sx.one(pads[0],'net')[1],sx.one(pads[2],'net')[1]=sx.one(pads[2],'net')[1],sx.one(pads[0],'net')[1]
        with self.assertRaisesRegex(ValueError,'pad mapping'):g.qualify(json.loads(self.project),self.native,self.task)
    def test_native_net_code_disagrees_with_terminal_name_rejected(self):
        self.native['pads'][0]['netcode']=2
        with self.assertRaises(ValueError):g.qualify(json.loads(self.project),self.native,self.task)
    def test_dsn_dropped_named_net_rejected(self):
        tree=g._parse_dsn(self.raw.decode());network=sx.one(tree,'network');row=sx.children(network,'net')[0];network.remove(row)
        with self.assertRaises(ValueError):g.transform(g._dump_dsn(tree).encode(),self.native,self.project,(sx.dump(self.task)+'\n').encode())

class IdentityNegativeTests(unittest.TestCase):
    def setUp(self):self.task=inputs()[0]
    def zone(self):return sx.children(self.task,'zone')[0]
    def assert_reject(self):
        with self.assertRaises(ValueError):g.source_net_identity(self.task)
    def test_empty_zero_rule_area_omitted_from_connected_net_names(self):self.assertEqual(g.source_net_identity(self.task)[0],{'SIGNAL_A','SIGNAL_B'})
    def test_nonzero_unknown_or_extra_numeric_atom_rejected(self):
        for value in (['net','1'],['net','999'],['net','00'],['net','0','""']):
            with self.subTest(value=value):
                self.task=inputs()[0];sx.one(self.zone(),'net')[:]=value;self.assert_reject()
    def test_conflicting_missing_or_duplicate_net_name_rejected(self):
        for action in ('conflict','missing','duplicate'):
            with self.subTest(action=action):
                self.task=inputs()[0];z=self.zone();name=sx.one(z,'net_name')
                if action=='conflict':name[1]='"SIGNAL_A"'
                elif action=='missing':z.remove(name)
                else:z.append(copy.deepcopy(name))
                self.assert_reject()
    def test_zero_is_never_inferred_for_pad_or_route(self):
        for kind in ('pad','segment'):
            with self.subTest(kind=kind):
                self.task=inputs()[0]
                if kind=='pad':sx.one(sx.children(sx.children(self.task,'footprint')[0],'pad')[0],'net')[:]=['net','0']
                else:self.task.append(['segment',['net','0']])
                self.assert_reject()
        _,resolve=g.source_net_identity(inputs()[0])
        with self.assertRaises(ValueError):resolve(['net','0'])
    def test_quoted_numeric_net_name_remains_distinct(self):
        tree=['kicad_pcb',['footprint',['pad',['net','"0"']]]]
        names,resolve=g.source_net_identity(tree);self.assertEqual(names,{'0'});self.assertEqual(resolve(['net','"0"']),'0')
        with self.assertRaises(ValueError):resolve(['net','0'])
    def test_genuine_restriction_and_malformed_flag_do_not_gain_support(self):
        for flag in ('tracks','vias','pads','copperpour','footprints'):
            self.task=inputs()[0];sx.one(sx.one(self.zone(),'keepout'),flag)[1]='not_allowed';self.assert_reject()
        self.task=inputs()[0];sx.one(self.zone(),'keepout').append(['tracks','allowed']);self.assert_reject()
    def test_copper_zone_and_footprint_zone_zero_do_not_gain_support(self):
        z=self.zone();z.remove(sx.one(z,'keepout'));self.assert_reject()
        self.task=inputs()[0];z=self.zone();self.task.remove(z);sx.children(self.task,'footprint')[0].append(z);self.assert_reject()
    def test_duplicate_zero_field_rejected(self):self.zone().append(['net','0']);self.assert_reject()
    def test_declared_numeric_conflict_stays_strict(self):
        self.task.extend([['net','0','""'],['net','1','"SIGNAL_A"'],['net','2','"SIGNAL_B"']])
        self.assert_reject() # Named pad references are not silently relabeled by new table.
        self.task=['kicad_pcb',['net','0','""'],['net','1','"SIGNAL_A"'],['footprint',['pad',['net','1','"SIGNAL_B"']]]]
        self.assert_reject()

if __name__=='__main__':unittest.main()
