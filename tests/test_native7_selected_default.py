"""Prospective narrow selected/Default composition controls; no Native proof."""
import copy,json,uuid,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import config as c,pipeline as p,preferences as pref,routing_scope as rs,sexpr as sx
from tests import test_default_target_integration as integration

class Native7SelectedDefaultTests(unittest.TestCase):
    setUp=integration.DefaultTargetIntegrationTests.setUp
    write=integration.DefaultTargetIntegrationTests.write
    check=integration.DefaultTargetIntegrationTests.check

    def selected(self):
        names=['DATA']
        for board in (self.snapshot,self.candidate):
            board.with_suffix('.kicad_sch').write_text('(kicad_sch (version 20260206))\n')
        self.data.update(schema=1,scope='selected_nets',engine_profile='completion-only',scoring_variant=None,
            source_hashes=p.tree_hash(self.snapshot.parent),
            routing_preferences={'effective':pref.resolve(overrides=dict(scope='selected_nets',profile='completion-only',adapter='both',nets=names))},
            selected_net_binding=rs.bind(self.snapshot.read_bytes(),names),
            selected_net_audit=rs.audit(self.original,sx.read(self.candidate),names))
        raw=(self.root/'default-targets.dsn').read_bytes()
        emitted,self.data['selected_dsn_binding']=rs.partition_dsn(raw,names)
        (self.root/'routing-scope-input.dsn').write_bytes(raw)
        (self.root/'task.dsn').write_bytes(emitted)
        return names

    def test_only_exact_native7_selected_configuration_opens(self):
        p.require_native_scope(scope='selected_nets',profile='completion-only')
        for wrong in ({'profile':'standard'},{'adapter':'none'},{'scoring':'via_high'},
                      {'layers':['F.Cu']},{'guidance':'placement-clearance-v1'},{'purpose':'improve'}):
            with self.subTest(wrong=wrong),self.assertRaises(p.Rejected):
                p.require_native_scope(**{**dict(scope='selected_nets',profile='completion-only'),**wrong})

    def test_named_selected_task_and_full_partition_are_rederived(self):
        names=self.selected()
        self.assertEqual(self.check(),self.record)
        raw=(self.root/'routing-scope-input.dsn').read_bytes()
        emitted,binding=rs.partition_dsn(raw,names)
        self.assertEqual(emitted,(self.root/'task.dsn').read_bytes())
        self.assertEqual(binding,self.data['selected_dsn_binding'])
        self.assertTrue(binding['all_nets_and_pins_retained'])
        self.assertTrue(binding['class_rules_copied_exactly'])
        self.assertFalse(binding['native_classes_changed'])

    def test_selected_default_markers_cannot_be_deleted_into_legacy(self):
        self.selected();self.data.pop('default_target_transport')
        (self.root/'default-targets.json').unlink();(self.root/'default-targets.dsn').unlink()
        with self.assertRaises((p.Rejected,OSError)):self.check()

    def test_selected_source_and_choice_refusals_stay_closed(self):
        self.selected()
        for mutation in ('missing_selection','unknown_name','score','profile','subset'):
            saved=copy.deepcopy(self.data)
            if mutation=='missing_selection':self.data.pop('selected_net_binding')
            elif mutation=='unknown_name':self.data['routing_preferences']['effective']['nets']=['UNKNOWN']
            elif mutation=='score':self.data['scoring_variant']='via_high'
            elif mutation=='profile':self.data['engine_profile']='standard'
            else:self.data['routing_preferences']['effective']['layers']=['F.Cu']
            with self.subTest(mutation=mutation),self.assertRaises((p.Rejected,ValueError)):self.check()
            self.data=saved

    def test_source_guard_refuses_nondefault_four_copper_selected_lock_and_missing_SCH(self):
        names=self.selected();original=self.snapshot.read_bytes();pro=self.snapshot.with_suffix('.kicad_pro').read_bytes()
        for mutation in ('nondefault','patterns','four_copper','selected_lock','missing_SCH'):
            self.snapshot.write_bytes(original);self.snapshot.with_suffix('.kicad_pro').write_bytes(pro)
            sch=self.snapshot.with_suffix('.kicad_sch');sch.write_text('(kicad_sch (version 20260206))\n')
            tree=sx.read(self.snapshot);project=json.loads(pro)
            if mutation=='nondefault':
                other=copy.deepcopy(project['net_settings']['classes'][0]);other['name']='SECOND';project['net_settings']['classes'].append(other)
            elif mutation=='patterns':project['net_settings']['netclass_patterns']=[{'netclass':'Default','pattern':'*'}]
            elif mutation=='four_copper':sx.one(tree,'layers').insert(2,['4','"In1.Cu"','signal'])
            elif mutation=='selected_lock':
                tree.append(['segment',['start','0','0'],['end','1','0'],['width','.3'],['layer','"F.Cu"'],['net','"DATA"'],['locked','yes'],['uuid',json.dumps(str(uuid.uuid4()))]])
            else:sch.unlink()
            sx.write(self.snapshot,tree);self.snapshot.with_suffix('.kicad_pro').write_text(json.dumps(project))
            with self.subTest(mutation=mutation),self.assertRaises(p.Rejected):p.check_native7_selected_source(self.snapshot,names)

    def test_selected_source_limit_refuses_before_output_or_worker(self):
        self.selected();self.snapshot.with_suffix('.kicad_sch').unlink();out=self.root/'never-created'
        effective=self.data['routing_preferences']['effective']
        request=dict(effective=effective,started=0,parent_cpu=0,child_cpu=0,started_utc='authored')
        with patch.object(p,'Job') as worker,patch.object(p,'check_storage') as storage:
            with self.assertRaises(p.Rejected):
                p.route(self.snapshot,out,**pref.route_arguments(effective),_preferences=request)
        worker.assert_not_called();storage.assert_not_called();self.assertFalse(out.exists())

    def test_malformed_project_and_settings_refuse_before_job_or_output(self):
        names=self.selected();effective=self.data['routing_preferences']['effective']
        request=dict(effective=effective,started=0,parent_cpu=0,child_cpu=0,started_utc='authored')
        for project in (None,[],False,'invalid',{'net_settings':None},
                        {'net_settings':[]},{'net_settings':False},{'net_settings':'invalid'}):
            self.snapshot.with_suffix('.kicad_pro').write_text(json.dumps(project))
            out=self.root/'never-created-malformed'
            with self.subTest(project=project):
                with self.assertRaises(p.Rejected):p.check_native7_selected_source(self.snapshot,names)
                with patch.object(p,'Job') as worker,patch.object(p,'check_storage') as storage:
                    with self.assertRaises(p.Rejected):
                        p.route(self.snapshot,out,**pref.route_arguments(effective),_preferences=request)
                worker.assert_not_called();storage.assert_not_called();self.assertFalse(out.exists())

    def test_selected_capability_is_required_even_after_producer_rehash(self):
        self.selected();self.assertEqual(self.check(),self.record)
        before=self.code.read_text()
        literal="NATIVE7_SELECTED_DEFAULT_POLICY='native7-selected-sole-default-v1'"
        self.assertIn(literal,before)
        for mutation in ('missing','unknown','nested','dynamic','duplicate','old_Default_only',
                         'missing_with_transport_deleted'):
            code=before
            if mutation in ('missing','missing_with_transport_deleted'):code=code.replace(literal,'# capability removed')
            elif mutation=='unknown':code=code.replace(literal,"NATIVE7_SELECTED_DEFAULT_POLICY='unknown'")
            elif mutation=='nested':code=code.replace(literal,'if True:\n    '+literal)
            elif mutation=='dynamic':code=code.replace(literal,"NATIVE7_SELECTED_DEFAULT_POLICY=str('native7-selected-sole-default-v1')")
            elif mutation=='duplicate':code=code.replace(literal,literal+'\n'+literal)
            else:code="DEFAULT_TARGET_ADMISSION_POLICY='single-default-global-floor-targets-v2'\n"
            self.code.write_text(code)
            self.data['tools']['implementation_sha256']['autorouter/pipeline.py']=p.sha(self.code)
            if mutation=='missing_with_transport_deleted':
                self.data.pop('default_target_transport')
                (self.root/'default-targets.json').unlink();(self.root/'default-targets.dsn').unlink()
            with self.subTest(mutation=mutation),self.assertRaises(p.Rejected):self.check()

    def test_marker_deletion_and_invalid_selected_metadata_never_return_legacy_None(self):
        self.selected();self.assertEqual(self.check(),self.record);before=copy.deepcopy(self.data)
        self.data.pop('default_target_transport')
        (self.root/'default-targets.json').unlink();(self.root/'default-targets.dsn').unlink()
        for mutation in ('adapter','strategy','input_policy','profile','scoring'):
            self.data=copy.deepcopy(before);self.data.pop('default_target_transport');input_policy='native'
            if mutation=='adapter':self.data['adapter']='none'
            elif mutation=='strategy':self.data['strategy']='native_validated_thermal_bridge'
            elif mutation=='input_policy':input_policy='board-floors-v1'
            elif mutation=='profile':self.data['engine_profile']='standard'
            else:self.data['scoring_variant']='via_high'
            with self.subTest(mutation=mutation),self.assertRaises(p.Rejected):
                p.check_default_target_transport(self.root,self.data,self.original,self.candidate,
                                                 input_policy=input_policy)

    def test_ordinary_Native7_does_not_require_selected_capability(self):
        literal="NATIVE7_SELECTED_DEFAULT_POLICY='native7-selected-sole-default-v1'"
        self.code.write_text(self.code.read_text().replace(literal,'# earlier ordinary producer'))
        self.data['tools']['implementation_sha256']['autorouter/pipeline.py']=p.sha(self.code)
        self.assertEqual(self.check(),self.record)

    def test_legacy_Native1000_unmarked_selected_Default_path_stays_historical(self):
        self.selected();self.data.pop('default_target_transport')
        (self.root/'default-targets.json').unlink();(self.root/'default-targets.dsn').unlink()
        with patch.object(c,'NATIVE_VERSION','10.0.0'):self.assertIsNone(self.check())

    def test_existing_exact_default_and_scope_tamper_refusals_are_retained(self):
        self.selected();wrong=copy.deepcopy(self.record);wrong['derived_nm']['width_nm']=200000
        self.write('default-targets.json',wrong)
        self.data['default_target_transport']['sha256']=p.sha(self.root/'default-targets.json')
        with self.assertRaises(p.Rejected):self.check()

if __name__=='__main__':unittest.main()
