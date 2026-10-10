"""Pure controls on retained actual native export; no new native validation."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE))
import diagnostic_route as d
import search_guidance as search
FIXTURE=d.ROOT/'evidence/placement-routing-fixture-002'

class ActualExportTests(unittest.TestCase):
    def setUp(self):
        self.raw=(FIXTURE/'pre-adapter.dsn').read_bytes()
        task=d.sx.read(FIXTURE/'floor-export-input/fixture.kicad_pcb')
        native=d.f.read_json(FIXTURE/'floor-export-context.json')
        project=d.f.read_json(FIXTURE/'snapshot/fixture.kicad_pro')
        self.context=d.g.qualify(project,native,task)
        self.tree=d.g._parse_dsn(self.raw.decode())
        self.policy=d.POLICIES[1]
    def test_actual_export_only_three_exact_clearance_atoms_change(self):
        output,receipt=search.transform(self.raw,self.context,self.policy)
        changed=[];planned=d.g._parse_dsn(output.decode())
        def compare(a,b,path=()):
            if isinstance(a,list) and isinstance(b,list):
                self.assertEqual(len(a),len(b))
                for index,(first,last) in enumerate(zip(a,b)):compare(first,last,path+(index,))
            elif a!=b:changed.append((path,a,b))
        compare(self.tree,planned)
        self.assertEqual(len(changed),3);self.assertTrue(all(first=='300' and last=='320' for _,first,last in changed))
        self.assertEqual(receipt['original_derived_nm'],self.context['derived_nm'])
        self.assertEqual(receipt['planning_clearance_nm'],320000)
        self.assertFalse(receipt['native_rules_changed']);self.assertFalse(receipt['routing_accepted'])
        search.verify_edit(self.tree,planned,self.context,self.policy)
    def test_margin_zero_preserves_all_ast_and_canonical_bytes(self):
        output,receipt=search.transform(self.raw,self.context,d.POLICIES[0])
        self.assertEqual(d.g._parse_dsn(output.decode()),self.tree)
        self.assertEqual(output,d.g._dump_dsn(self.tree).encode())
        self.assertEqual(receipt['planning_clearance_nm'],300000)
    def test_cost_arm_has_identical_margin_dsn_and_explicit_distinct_engine_flags(self):
        first,_=search.transform(self.raw,self.context,d.POLICIES[1]);last,_=search.transform(self.raw,self.context,d.POLICIES[2]);self.assertEqual(first,last)
        for policy,via,plane in [(d.POLICIES[0],50,5),(d.POLICIES[1],50,5),(d.POLICIES[2],25,3)]:
            params=search.parameters(policy);engine=d.p.engine_profile_settings('completion-only',70,strict_class_targets=True,scoring_variant=params['scoring_variant'])
            self.assertEqual(engine['scoring']['via_costs'],via);self.assertEqual(engine['scoring']['plane_via_costs'],plane)
            self.assertIn('--router.scoring.via_costs='+str(via),engine['argv']);self.assertIn('--router.scoring.plane_via_costs='+str(plane),engine['argv'])
            self.assertIn('--router.automatic_neckdown=false',engine['argv']);self.assertIn('--router.fanout.enabled=false',engine['argv'])
    def test_context_and_original_ast_not_modified(self):
        context=copy.deepcopy(self.context);original=copy.deepcopy(self.tree)
        search.transform(self.raw,self.context,self.policy)
        self.assertEqual(context,self.context);self.assertEqual(original,self.tree)
    def test_wrong_missing_duplicate_clearance_or_extra_rule_rejected(self):
        for kind in ('wrong','missing','duplicate','extra'):
            tree=copy.deepcopy(self.tree);rule=d.sx.one(d.sx.one(tree,'structure'),'rule')
            if kind=='wrong':rule[2][1]='299'
            elif kind=='missing':rule.pop()
            elif kind=='duplicate':rule.append(copy.deepcopy(rule[2]))
            else:rule.append(['clearance','300',['type','pad_pad']])
            with self.subTest(kind=kind),self.assertRaises(ValueError):search.transform(d.g._dump_dsn(tree).encode(),self.context,self.policy)
    def test_pad_geometry_width_via_net_and_undeclared_clearance_changes_rejected(self):
        expected=search.expected_tree(self.tree,self.context,self.policy)
        for kind in ('width','via','pin','net','smd','class'):
            changed=copy.deepcopy(expected);structure=d.sx.one(changed,'structure');network=d.sx.one(changed,'network')
            if kind=='width':d.sx.one(structure,'rule')[1][1]='301'
            elif kind=='via':d.sx.one(structure,'via')[1]='"different-via"'
            elif kind=='net':d.sx.children(network,'net')[0][1]='"WRONG_NET"'
            elif kind=='pin':d.sx.children(d.sx.one(changed,'library'),'image')[0][2][1]='"different-pin"'
            elif kind=='smd':search.clearance_nodes(changed)[1][1]='321'
            else:search.clearance_nodes(changed)[2][1]='321'
            with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'nondeclared'):search.verify_edit(self.tree,changed,self.context,self.policy)
    def test_native_preferences_or_floors_are_not_reinterpreted_as_padding(self):
        changed=copy.deepcopy(self.context);changed['derived_nm']['clearance_nm']=320000
        with self.assertRaisesRegex(ValueError,'global'):search.transform(self.raw,changed,self.policy)
    def test_wrong_named_policy_and_arbitrary_values_rejected(self):
        for bad in (None,True,0,20000,'placement-search-v2-margin-20um','floor-plus-placement-diagnostic-v1'):
            with self.subTest(policy=bad),self.assertRaises(ValueError):search.transform(self.raw,self.context,bad)
    def test_noncanonical_whitespace_is_reencoded_but_ast_preserved(self):
        raw=b'\n'+self.raw+b'\n';output,_=search.transform(raw,self.context,d.POLICIES[0]);self.assertEqual(d.g._parse_dsn(output.decode()),self.tree)
    def test_bound_input_output_context_receipt(self):
        output,receipt=search.transform(self.raw,self.context,self.policy)
        self.assertEqual(receipt['input_sha256'],d.g.sha(self.raw));self.assertEqual(receipt['output_sha256'],d.g.sha(output))
        digest=hashlib.sha256(json.dumps(self.context,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        self.assertEqual(receipt['original_floor_context_sha256'],digest)
    def test_required_helpers_exact_v1_copies(self):
        for name in ('native_combined.py','placement_transform.py'):
            self.assertEqual((HERE/name).read_bytes(),(d.ROOT/'experiments/placement_diagnostic_v1'/name).read_bytes())
    def test_protocol_fixed_order_and_strongest_fixture_gate(self):
        protocol=d.f.read_json(HERE/'protocol.json');self.assertEqual(protocol['fixed_order'],list(d.POLICIES))
        self.assertEqual(protocol['qualification_fixture']['required_policy'],d.POLICIES[2])
        self.assertEqual(protocol['wall_seconds_per_arm'],120);self.assertEqual(protocol['cpu_seconds_per_arm'],120)


class ActualDeriveTests(unittest.TestCase):
    def setUp(self):
        import tempfile,shutil
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.out=Path(self.tmp.name);self.policy=d.POLICIES[2]
        for name in ('snapshot','floor-export-input'):shutil.copytree(FIXTURE/name,self.out/name)
        for name in ('native.dsn','floor-export-context.json','area-context.json'):shutil.copy2(FIXTURE/name,self.out/name)
        self.hashes=d.p.tree_hash(self.out/'snapshot');board=self.out/'floor-export-input/fixture.kicad_pcb'
        for name in ('floor-export-context.json','area-context.json'):
            value=d.f.read_json(self.out/name);value['source']=str(board);d.p.save_json(self.out/name,value)
        d.p.save_json(self.out/'route-meta.json',{'board_name':board.name,'policy':self.policy})
        task=d.sx.read(board);native=d.f.read_json(self.out/'floor-export-context.json');raw=(self.out/'native.dsn').read_bytes();project=(self.out/'snapshot/fixture.kicad_pro').read_bytes()
        guided,contract=d.f.policy_contract(raw,native,project,task,self.hashes)
        (self.out/'floor-guided.dsn').write_bytes(guided);d.p.save_json(self.out/'floor-policy.json',contract)
        placed,removal=d.placement.transform(d.files(self.out/'snapshot'),d.files(self.out/'floor-export-input'),board.name,d.f.read_json(self.out/'area-context.json'),raw,guided)
        (self.out/'placement-guided.dsn').write_bytes(placed);d.p.save_json(self.out/'placement-transform.json',removal)
        context=d.g.qualify(json.loads(project),native,task);planned,receipt=search.transform(placed,context,self.policy)
        (self.out/'pre-adapter.dsn').write_bytes(planned);d.p.save_json(self.out/'search-guidance.json',receipt)
        (self.out/'task.dsn').write_bytes(d.g.adapter_bytes(planned,native['obstacles']))
    def tearDown(self):self.tmp.cleanup()
    def derive(self):return d.derive(self.out,self.hashes,self.policy)
    def test_all_actual_export_bindings_rederive_without_native_or_forged_context(self):
        task,contract,chain=self.derive();self.assertEqual(chain['placement_removed_count'],2)
        self.assertEqual(chain['search_parameters']['clearance_margin_nm'],20000)
        self.assertEqual(contract['transformation']['derived_nm']['clearance_nm'],300000)
    def test_changed_planning_receipt_rejected_even_with_updated_output_hash(self):
        path=self.out/'search-guidance.json';receipt=d.f.read_json(path);receipt['planning_clearance_nm']=330000
        receipt['output_sha256']=d.p.sha(self.out/'pre-adapter.dsn');d.p.save_json(path,receipt)
        with self.assertRaisesRegex(d.p.Rejected,'planning provenance'):self.derive()
    def test_changed_input_and_rehashed_planning_receipt_cannot_hide_width_change(self):
        path=self.out/'pre-adapter.dsn';tree=d.g._parse_dsn(path.read_text());d.sx.one(d.sx.one(tree,'structure'),'rule')[1][1]='301';path.write_text(d.g._dump_dsn(tree))
        receipt=d.f.read_json(self.out/'search-guidance.json');receipt['output_sha256']=d.p.sha(path);d.p.save_json(self.out/'search-guidance.json',receipt)
        (self.out/'task.dsn').write_bytes(d.g.adapter_bytes(path.read_bytes(),[]))
        with self.assertRaisesRegex(d.p.Rejected,'planning provenance'):self.derive()
    def test_original_native_floor_context_cannot_be_relabelled_for_padding(self):
        path=self.out/'floor-export-context.json';native=d.f.read_json(path);native['floors_nm']['min_clearance']=320000;d.p.save_json(path,native)
        with self.assertRaisesRegex(ValueError,'native loaded floor'):self.derive()
    def test_margin_policy_label_cannot_disagree_with_dsn(self):
        d.p.save_json(self.out/'route-meta.json',{'board_name':'fixture.kicad_pcb','policy':d.POLICIES[0]})
        with self.assertRaisesRegex(d.p.Rejected,'planning provenance'):d.derive(self.out,self.hashes,d.POLICIES[0])

class ProtocolTests(unittest.TestCase):
    def test_fixed_contract_matches(self):self.assertEqual(d.protocol_contract()['fixed_order'],list(d.POLICIES))
    def test_reordered_arms_weak_fixture_or_type_changed_cap_rejected(self):
        from unittest.mock import patch
        for key,value in [('fixed_order',list(reversed(d.POLICIES))),('cpu_seconds_per_arm',True),('search_parameters',[])]:
            protocol=d.f.read_json(HERE/'protocol.json');protocol[key]=value
            with patch.object(d.f,'read_json',return_value=protocol),self.assertRaises(d.p.Rejected):d.protocol_contract()
        protocol=d.f.read_json(HERE/'protocol.json');protocol['qualification_fixture']['required_policy']=d.POLICIES[0]
        with patch.object(d.f,'read_json',return_value=protocol),self.assertRaises(d.p.Rejected):d.protocol_contract()

if __name__=='__main__':unittest.main()
