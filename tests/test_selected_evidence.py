"""Regress the reproduced selected-scope downgrade with the existing receipt seam.

All native/process/report data here are synthetic; this is no PCB qualification.
"""
import copy,json,unittest,uuid
from autorouter import pipeline as p,preferences as pref,routing_scope as rs,sexpr as sx
import test_result as fixtures

class SelectedEvidence(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.ResultFreshnessTests('test_matching_files_remain_current_without_applying_anything')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups);x=self.fixture
        # Replace the inherited zero-cost mock engine with this fixture's own
        # explicit selected-scope process below; this is setup before faults.
        x.data['steps']=[row for row in x.data['steps'] if row.get('name')!='engine']
        original=sx.read(x.source);original.extend([['net','0','""'],['net','1','"GND"']])
        for index,route in enumerate(p.routes(original)):
            sx.one(route,'net')[:]=['net','1'];sx.one(route,'uuid')[:]=['uuid',json.dumps(str(uuid.uuid5(uuid.NAMESPACE_URL,'selected-receipt:'+str(index))))]
        raw=(sx.dump(original)+'\n').encode()
        for path in [x.source,x.run/'snapshot'/x.source.name,x.candidate,x.run/'final-drc-input'/x.source.name]:path.write_bytes(raw)
        (x.run/'pre-refill.kicad_pcb').write_bytes(raw)
        x.data.update(scope='selected_nets',source_hashes=p.tree_hash(x.source_dir),candidate_sha256=p.sha(x.candidate),
                      adapter='none',engine_profile='completion-only',scoring_variant=None,
                      schematic_parity='unavailable: no native schematic in source project',
                      selected_net_binding=rs.bind(raw,['GND']),selected_net_audit=rs.audit(original,original,['GND']),
                      task_sha256=rs.bind(raw,['GND'])['task_sha256'])
        x.binding.update(before=p.tree_hash(x.candidate.parent),after=p.tree_hash(x.candidate.parent));p.save_json(x.run/'final-drc-binding.json',x.binding)
        x.data['steps'][0]['validated_input_sha256']=p.sha(x.candidate)
        request={'captured':None,'effective':pref.resolve(overrides={'scope':'selected_nets','nets':['GND'],'profile':'completion-only'}),
                 'snapshot':pref.snapshot(overrides={'scope':'selected_nets','nets':['GND'],'profile':'completion-only'})}
        p.capture_preferences(x.data,x.run,request)
        from tests.normal_prl_fixture import authored_zero_alias_dsn,refresh_authored_normal_export
        network=['network',['net','GND',['pins','J1-1']],['class','kicad_default','GND',['rule',['width','200']]]]
        dsn=authored_zero_alias_dsn(p.routing_task(original,'selected_nets',['GND']),x.run/'task.dsn',network=network)
        emitted,dsn_binding=rs.partition_dsn(dsn,['GND']);x.data['selected_dsn_binding']=dsn_binding
        (x.run/'routing-scope-input.dsn').write_bytes(dsn)
        settings=p.engine_profile_settings('completion-only',100,strict_class_targets=True);settings.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
        process={'name':'engine','argv':p.engine_argv(x.run,settings['argv']),'cwd':str(x.run),
                 'status':'success','exit_code':0,'cleanup_complete':True,'wall_seconds':0.1,'cpu_seconds':0.1,'monitor_cpu_seconds':0.}
        p.save_json(x.run/'engine-process.json',process);x.data['engine_budget']=settings;x.data['steps'].insert(0,process)
        x.data.update(child_cpu_seconds=1.1,total_cpu_seconds=1.4)
        for name,field in [('native.dsn','native_dsn_sha256'),('task.dsn','task_dsn_sha256')]:
            (x.run/name).write_bytes(dsn if name=='native.dsn' else emitted);x.data[field]=p.sha(x.run/name)
        # Replace the inherited authored import metadata with this selected
        # fixture's own exact import; preserve its zero-cost saved-refill row.
        x.data['steps']=[step for step in x.data['steps'] if step['name']!='import']
        (x.run/'refill'/x.source.name).write_bytes(raw)
        refill_binding=json.loads((x.run/'refill-drc-binding.json').read_text())
        refill_binding.update(before=p.tree_hash(x.run/'refill'),after=p.tree_hash(x.run/'refill'))
        p.save_json(x.run/'refill-drc-binding.json',refill_binding)
        for step in x.data['steps']:
            if step['name']=='refill-drc':step['validated_input_sha256']=p.sha(x.run/'refill'/x.source.name)
        imported=x.run/'imported.kicad_pcb';imported.write_bytes(raw);audit={'imported_sha256':p.sha(imported)}
        # Complete the authored import lineage too; this is synthetic receipt
        # syntax/provenance, never evidence that SES produced this board.
        session=x.run/'routes.ses'
        process={'name':'import','argv':[str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py'),
                    'import',str(x.candidate),str(imported),str(session)],'cwd':str(x.run),
                 'status':'success','exit_code':0,'cleanup_complete':True,
                 'wall_seconds':0.1,'cpu_seconds':0.1,'monitor_cpu_seconds':0.}
        p.save_json(x.run/'import-process.json',process);x.data['steps'].insert(1,process)
        x.data.update(child_cpu_seconds=1.2,total_cpu_seconds=1.5)
        p.transplant_routes(original,original,protected=rs.protected_routes(original,['GND']),audit=audit,policy='exact_non_uuid_lock_position_v2')
        x.data['protected_route_import']=audit
        # Scope/source edits above are intentional setup. Rebuild the owned
        # zero-cost export proof now, never after a tested fault.
        refresh_authored_normal_export(x.run,x.data,test_root=x.root,raw_dsn=dsn,task_dsn=emitted)
        from tests.normal_prl_fixture import mark_authored_receipt
        mark_authored_receipt(x.run,x.data,test_root=x.root,fixed_imports=True,authored_engine=False)
        x.save_receipt()

    def test_selected_receipt_requires_both_exports_even_without_literal_classes(self):
        x=self.fixture;self.assertTrue(p.check_result(x.receipt)['current']);good=copy.deepcopy(x.data)
        for missing in [('native_dsn_sha256',),('task_dsn_sha256',),('native_dsn_sha256','task_dsn_sha256')]:
            x.data=copy.deepcopy(good)
            for key in missing:del x.data[key]
            x.save_receipt()
            with self.subTest(missing=missing),self.assertRaisesRegex(p.Rejected,'routing export'):p.check_result(x.receipt)
        x.data=copy.deepcopy(good)
        for name in ('native.dsn','task.dsn'):
            path=x.run/name;original=path.read_bytes();path.write_bytes(b'unrelated task\n');x.save_receipt()
            with self.subTest(name=name),self.assertRaisesRegex(p.Rejected,'routing export|raw Native alias DSN missing'):p.check_result(x.receipt)
            path.write_bytes(original)

    def test_selected_protection_reconciliation_and_task_binding_are_mandatory(self):
        x=self.fixture;self.assertTrue(p.check_result(x.receipt)['current']);good=copy.deepcopy(x.data)
        del x.data['protected_route_import'];x.save_receipt()
        with self.assertRaisesRegex(p.Rejected,'complete protected import|current normal import requires complete proof'):p.check_result(x.receipt)
        x.data=copy.deepcopy(good);x.data['task_sha256']='0'*64;x.save_receipt()
        with self.assertRaisesRegex(p.Rejected,'selected-net source binding|alias input differs from original normal task'):p.check_result(x.receipt)

    def test_complete_selector_removal_cannot_hide_retained_scoped_input(self):
        x=self.fixture;self.assertTrue(p.check_result(x.receipt)['current'])
        for key in ['selected_net_binding','selected_net_audit','selected_dsn_binding','routing_preferences','protected_route_import']:del x.data[key]
        (x.run/'routing-preferences.json').unlink();x.data['scope']='whole_board_unlocked_routing';x.save_receipt()
        with self.assertRaisesRegex(p.Rejected,'cannot downgrade'):p.check_result(x.receipt)

    def test_rehashed_adapter_input_cannot_change_native_exported_class_rules(self):
        x=self.fixture;x.data['adapter']='both';x.data['routing_preferences']['effective']['adapter']='both'
        path=x.run/'routing-preferences.json';request={'captured':None,
            'effective':pref.resolve(overrides={'scope':'selected_nets','nets':['GND'],'profile':'completion-only','adapter':'both'}),
            'snapshot':pref.snapshot(overrides={'scope':'selected_nets','nets':['GND'],'profile':'completion-only','adapter':'both'})}
        path.unlink();p.capture_preferences(x.data,x.run,request)
        # Model the current corrected adapter stages, including the explicit
        # unqualified-edge record for this intentionally minimal board fixture.
        from tests.test_native_edge import DSN
        from autorouter import adapter,native_edge
        tree=adapter._parse_dsn(DSN)
        sx.children(sx.one(tree,'placement'),'component')[0][2][1]='J1'
        sx.one(sx.children(sx.one(tree,'network'),'net')[0],'pins')[1]='J1-1'
        native=adapter._dump_dsn(tree).encode();(x.run/'native.dsn').write_bytes(native)
        adapted,adapter_record=adapter.adapt_bytes(native,'both',[])
        corrected,edge_record=native_edge.correct(adapted,p.native_edge_context(x.run/'snapshot'/x.source.name))
        p.save_json(x.run/'obstacles.json',[]);(x.run/'edge-adapter-input.dsn').write_bytes(adapted)
        p.save_json(x.run/'native-edge-correction.json',edge_record)
        base=x.run/'routing-scope-input.dsn';base.write_bytes(corrected)
        emitted,binding=rs.partition_dsn(corrected,['GND']);(x.run/'task.dsn').write_bytes(emitted)
        x.data.update(adapter_transformations=adapter_record,native_edge_correction=edge_record,
            native_dsn_sha256=p.sha(x.run/'native.dsn'),task_dsn_sha256=p.sha(x.run/'task.dsn'),selected_dsn_binding=binding)
        from tests.normal_prl_fixture import refresh_authored_normal_export
        refresh_authored_normal_export(x.run,x.data,test_root=x.root,raw_dsn=native,task_dsn=emitted)
        x.save_receipt()
        self.assertTrue(p.check_result(x.receipt)['current'])
        base.write_bytes(base.read_bytes().replace(b'width 200',b'width 100'))
        emitted,binding=rs.partition_dsn(base.read_bytes(),['GND']);(x.run/'task.dsn').write_bytes(emitted)
        x.data.update(task_dsn_sha256=p.sha(x.run/'task.dsn'),selected_dsn_binding=binding)
        x.data['adapter_transformations']['output_sha256']=p.sha(base);x.save_receipt()
        with self.assertRaisesRegex(p.Rejected,'original network or class rules|native edge correction'):p.check_result(x.receipt)

if __name__=='__main__':unittest.main()
