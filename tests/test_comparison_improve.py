"""Constructed comparison-v2 guards; no Native, engine or GUI is executed."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import shutil
import unittest

from scripts import freeze_current_comparison as frozen, qualify_current_method as method
from scripts import report_current_comparison as q
from tests import test_current_comparison_report as report_controls
write = report_controls.write


class MethodContractTests(unittest.TestCase):
    def test_report_population_is_versioned_and_cannot_promote_GUI(self):
        names=frozen.IMPROVE_POPULATION
        pop=dict(schema=1,kind=frozen.IMPROVE_POPULATION_KIND,population=list(names),
            planned_arm_order=list(frozen.IMPROVE_ARM_ORDER),limits=frozen.LIMITS,planned_family_order=['owned'],
            families={'owned':{}},outputs={'owned':dict.fromkeys(names,'path')},administration_head='a'*40,
            qualification=dict(kind=frozen.IMPROVE_QUALIFICATION_KIND,actual_GUI_qualified=False,full_GUI_claim=False))
        children=dict(schema=1,administration_head='a'*40,policy_or_board_changes_after_first_arm=False,
            protocols={'owned':dict.fromkeys(names,{})})
        self.assertEqual(q.population_shape(pop,children),['owned'])
        for field in ('actual_GUI_qualified','full_GUI_claim'):
            bad=copy.deepcopy(pop);bad['qualification'][field]=True
            with self.assertRaises(ValueError):q.population_shape(bad,children)
        bad=copy.deepcopy(pop);bad['kind']='frozen-current-six-arm-exposed-development-v1'
        with self.assertRaises(ValueError):q.population_shape(bad,children)
        bad=copy.deepcopy(children);del bad['protocols']['owned']['Cimprove']
        with self.assertRaises(ValueError):q.population_shape(pop,bad)

    def test_versions_do_not_alias_thermal_and_improve(self):
        self.assertIn('Cthermal',method.method_contract(method.KIND)[0])
        self.assertNotIn('Cimprove',method.method_contract(method.KIND)[0])
        self.assertEqual(method.method_contract(method.IMPROVE_KIND),
                         (frozen.IMPROVE_POPULATION,'qualify-current-method-002.py'))
        with self.assertRaises(ValueError):method.method_contract('unknown')
        defaults=dict(frozen.pref.DEFAULTS,seconds=420)
        preset=lambda original:dict(original,profile='tuned')
        plan=dict(kind=method.IMPROVE_KIND,arm='Cimprove',improve_settings=preset(defaults))
        self.assertEqual(method.captured_method_settings(plan,defaults,preset),preset(defaults))
        self.assertEqual(defaults['profile'],'standard')
        plan['arm']='Cdefault'
        self.assertIs(method.captured_method_settings(plan,defaults,preset),defaults)
        plan['improve_settings']=dict(plan['improve_settings'],scoring_preference='via_low')
        with self.assertRaises(ValueError):method.captured_method_settings(plan,defaults,preset)

    def test_enclosure_has_exact_separate_copied_child_allowances(self):
        path=Path(frozen.__file__).with_name('enclose_current_comparison.py')
        node=next(x for x in ast.parse(path.read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='ordinary_method_contract')
        scope={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(path)+'::owned-control','exec'),scope)
        allows=scope['ordinary_method_contract']
        for kind,arm,child in [(method.KIND,'Cthermal','qualify-current-method-001.py'),
                               (method.IMPROVE_KIND,'Cimprove','qualify-current-method-002.py')]:
            self.assertTrue(allows(dict(kind=kind,arm=arm),Path(child),False))
            self.assertFalse(allows(dict(kind=kind,arm=arm),Path(child),True))
        self.assertFalse(allows(dict(kind=method.KIND,arm='Cimprove'),Path('qualify-current-method-001.py'),False))
        self.assertFalse(allows(dict(kind=method.IMPROVE_KIND,arm='Cthermal'),Path('qualify-current-method-002.py'),False))
        self.assertFalse(allows(dict(kind=method.IMPROVE_KIND,arm='Cimprove'),Path('qualify-current-method-001.py'),False))


class ImproveFactsTests(unittest.TestCase):
    def setUp(self):
        self.base=report_controls.ComparisonReportTests('test_own_final_uses_exact_output_not_first_trial_phase')
        self.base.setUp();self.addCleanup(self.base.doCleanups)
        self.root=self.base.root;self.folder=self.root/'improve/route'
        self.plan=dict(self.base.plan,source=str(self.root/'owned.kicad_pcb'),runtime=str(self.root/'runtime'))
        self.metrics=dict(version='10.0.7',vias=0,track_length_mm=10,copper_layers=2)
        self.parent=self.packet(self.folder)
        self.inc=self.packet(self.folder/'incumbent')
        self.context=dict(parent=str(self.folder),output=str(self.folder/'incumbent'),source=self.plan['source'],
            source_hashes=self.plan['source_hashes'],runtime=self.plan['runtime'],method_seconds=420,
            finalization_reserve_seconds=25,scoring_variant=None,profile='tuned',proposal_policy='single',
            tools_sha256=hashlib.sha256(q.f.canonical(self.plan['tools']).encode()).hexdigest())
        child=self.folder/'incumbent/improve-child-context.json';write(child,self.context)
        self.inc['native_improve_child']=dict(policy='selected-native7-single-improve-child-v1',file=child.name,sha256=q.digest(child))
        guide=self.folder/'incumbent/default-targets.json';write(guide,dict(policy='single-default-global-floor-targets-v2'))
        self.inc['default_target_transport']=dict(policy='single-default-global-floor-targets-v2',file=guide.name,sha256=q.digest(guide))
        write(self.folder/'incumbent/result.json',self.inc)
        self.parent.update(strategy='native_validated_zone_net_pruning',proposal_policy='single',engine_profile='tuned',
            budget_seconds=420,cpu_budget_seconds=420,finalization_reserve_seconds=25,finalization_cpu_reserve_seconds=25,
            incumbent=dict(receipt=str(self.folder/'incumbent/result.json'),status='routing_accepted',accepted=True),
            native7_default_target_basis=dict(policy='single-default-global-floor-targets-v2',receipt='incumbent/result.json',
                receipt_sha256=q.digest(self.folder/'incumbent/result.json'),file='incumbent/default-targets.json',sha256=q.digest(guide)),
            best_observed_metrics=self.metrics)
        marker=self.folder/'native7-improve-parent.json';write(marker,dict(schema=1,policy='selected-native7-single-improve-parent-v1',context=self.context))
        self.parent['native7_improve_parent']=dict(policy='selected-native7-single-improve-parent-v1',file=marker.name,sha256=q.digest(marker))
        self.trial_folder=self.folder/'trials/trial-0000';trial=self.packet(self.trial_folder)
        self.trial={key:trial[key] for key in ('accepted','candidate_sha256','native','native_report_sha256','metrics','steps')}
        self.trial.update(id='trial-0000',status='quality_rejected',accepted=False,base_candidate_sha256=self.inc['candidate_sha256'],
            started_elapsed_seconds=10,finished_elapsed_seconds=12,finished_observed_cpu_seconds=11,
            single_trial_guard=dict(wall_deadline_elapsed_seconds=300,work_cpu_limit_seconds=395))
        self.save()

    def packet(self,folder):
        shutil.copytree(self.base.folder,folder)
        data=copy.deepcopy(self.base.data);candidate=folder/'candidate/owned.kicad_pcb';binding=copy.deepcopy(self.base.binding)
        binding.update(source=str(candidate),input=str(folder/'final-drc-input/owned.kicad_pcb'))
        write(folder/'final-drc-binding.json',binding)
        step=copy.deepcopy(self.base.step);step.update(cwd=str(folder));step['argv'][-1]=binding['input'];step['argv'][step['argv'].index('--output')+1]=str(folder/'final-drc.json')
        write(folder/'final-drc-process.json',step)
        data.update(candidate=str(candidate),steps=[step],source=self.plan['source'],metrics=self.metrics,status='routing_accepted')
        self.auxiliary(folder,data);write(folder/'result.json',data)
        return data

    def auxiliary(self,folder,data,qualified=True):
        for name in ('final-netclasses.json','final-netclasses-process.json','refill-drc.json','refill-drc-binding.json','refill-drc-process.json'):
            write(folder/name,dict(inert_synthetic=True))
        write(folder/'final-netclass-audit.json',dict(candidate_sha256=data['candidate_sha256'],
            project_sha256=self.plan['source_hashes']['owned.kicad_pro'],native_map_file_sha256=q.digest(folder/'final-netclasses.json'),
            native=dict(passed=True),route_dimensions=dict(passed=True,checked=dict(protected=1)),
            default_targets=dict(policy='single-default-global-floor-targets-v2')))
        if not any(row.get('type')=='footprint_symbol_field_mismatch' for row in data['native']['findings']):
            data['native'].pop('field_parity',None)
            return
        (folder/'final-drc-fields.net').write_bytes(b'inert synthetic netlist, never Native\n')
        write(folder/'final-drc-fields.json',dict(inert_synthetic=True))
        journals={}
        for name in ('final-drc-fields-netlist','final-drc-fields-audit'):
            journals[name]=write(folder/(name+'-process.json'),dict(cwd=str(folder),status='success',exit_code=0,cleanup_complete=True,log_truncated=False))
        binding=q.read(folder/'final-drc-binding.json')
        write(folder/'final-drc-fields-local-settings.json',dict(input=binding['input'],before=binding['after'],after=binding['after'],
            policy='job-owned-field-prl-immutable-v1',protection=dict(policy='mac-owned-prl-immutable-v1',present=False),processes_sha256=journals))
        proof=dict(schema=1,qualification=dict(qualified=qualified,reason='inert synthetic field detail'))
        for name,key in [('final-drc.json','native_report_sha256'),('final-drc-binding.json','binding_sha256'),
                         ('final-drc-fields.net','netlist_sha256'),('final-drc-fields.json','fields_sha256'),
                         ('final-drc-fields-local-settings.json','local_settings_guard_sha256')]:proof[key]=q.digest(folder/name)
        write(folder/'final-drc-fields-proof.json',proof);data['native']['field_parity']=proof

    def save(self):
        path=self.trial_folder/'result.json';write(path,self.trial)
        self.parent['trials']=[dict(id='trial-0000',receipt=str(path),status=self.trial['status'],accepted=self.trial['accepted'])]
        write(self.folder/'result.json',self.parent)

    def facts(self,qualified=True):
        return q.improve_facts(self.folder/'result.json',self.plan,[self.root],qualified_parent=qualified,public_sanitize=True)

    def test_quality_rejected_is_completed_native_valid_unselected(self):
        fact=self.facts()['trials'][0]
        self.assertFalse(fact['accepted']);self.assertTrue(fact['Native_completion_qualified'])
        self.assertEqual(fact['own_final']['Native_counts'],[0,0,0,0])
        self.assertNotIn('source_hashes',self.trial)
        self.assertNotIn('tools',self.trial)
        self.assertEqual(fact['auxiliary']['field_qualification']['status'],'not_applicable')
        self.assertEqual(self.facts()['parent_auxiliary']['field_qualification']['status'],'not_applicable')
        self.assertEqual(self.facts()['incumbent']['auxiliary']['field_qualification']['status'],'not_applicable')

    def test_no_native_field_findings_need_no_field_observations(self):
        for name in ('final-drc-fields.net','final-drc-fields.json','final-drc-fields-proof.json',
                     'final-drc-fields-local-settings.json','final-drc-fields-netlist-process.json',
                     'final-drc-fields-audit-process.json'):
            (self.trial_folder/name).unlink(missing_ok=True)
        self.trial['native'].pop('field_parity',None)
        fact=q.improve_auxiliary(self.trial_folder,self.trial,self.plan)
        self.assertEqual(fact['field_qualification']['status'],'not_applicable')
        self.assertIsNone(fact['field_qualification']['qualified'])
        self.assertIn('refill-drc.json',fact['files_sha256'])
        self.assertIn('final-netclass-audit.json',fact['files_sha256'])

    def warning_trial(self,kind,status):
        raw=q.read(self.trial_folder/'final-drc.json')
        finding=dict(type=kind,severity='warning',items=[])
        raw['schematic_parity' if kind=='footprint_symbol_field_mismatch' else 'violations']=[finding]
        self.trial['native_report_sha256']=write(self.trial_folder/'final-drc.json',raw)
        self.trial['native'].update(warnings=1,findings=[finding])
        self.trial.update(status=status,accepted=False)
        self.trial['steps'][0].update(status='nonzero_exit',exit_code=5)
        write(self.trial_folder/'final-drc-process.json',self.trial['steps'][0])
        self.auxiliary(self.trial_folder,self.trial,qualified=False);self.save()

    def test_warning_only_policy_rejected_trial_retains_own_negative_proof(self):
        self.warning_trial('footprint_symbol_field_mismatch','drc_rejected')
        fact=self.facts()['trials'][0]
        self.assertTrue(fact['Native_completion_qualified'])
        self.assertIs(fact['own_final']['Native_application_policy']['accepted'],False)
        self.assertEqual(fact['own_final']['Native_counts'],[0,0,1,0])
        self.assertIs(fact['auxiliary']['field_qualification']['qualified'],False)

    def test_quality_rejected_valid_warning_is_not_rejected_for_field_false_alone(self):
        self.warning_trial('lib_footprint_issues','quality_rejected')
        fact=self.facts()['trials'][0]
        self.assertFalse(fact['accepted']);self.assertTrue(fact['Native_completion_qualified'])
        self.assertIs(fact['own_final']['Native_application_policy']['accepted'],True)
        self.assertEqual(fact['own_final']['Native_counts'],[0,0,1,0])
        self.assertEqual(fact['auxiliary']['field_qualification']['status'],'not_applicable')
        native=copy.deepcopy(self.trial['native']);native['field_parity']=dict(qualification=dict(qualified=False))
        self.assertIs(q.native_application_policy(native,self.plan)['accepted'],True)
        self.warning_trial('footprint_symbol_field_mismatch','quality_rejected')
        with self.assertRaises(ValueError):self.facts()

    def test_trial_source_binding_cleanup_and_candidate_tampering_refuse(self):
        original=copy.deepcopy(self.trial)
        self.trial['steps'][0]['cleanup_complete']=False;self.save()
        with self.assertRaises(ValueError):self.facts()
        self.trial=original;self.save()
        candidate=self.trial_folder/'candidate/owned.kicad_pcb';candidate.write_bytes(b'tampered')
        with self.assertRaises(ValueError):self.facts()

    def test_missing_default_map_field_bridge_or_context_refuses(self):
        self.warning_trial('footprint_symbol_field_mismatch','drc_rejected')
        for folder,name in [(self.trial_folder,'final-netclasses.json'),(self.trial_folder,'final-drc-fields-proof.json'),
                            (self.folder/'incumbent','improve-child-context.json')]:
            path=folder/name;raw=path.read_bytes();path.unlink()
            with self.subTest(name=name),self.assertRaises((ValueError,OSError)):self.facts()
            path.write_bytes(raw)

    def test_parent_or_trial_lineage_change_refuses(self):
        self.trial['base_candidate_sha256']='0'*64;self.save()
        with self.assertRaises(ValueError):self.facts()

    def test_trial_summary_requires_actual_bool(self):
        self.parent['trials'][0]['accepted']=0;write(self.folder/'result.json',self.parent)
        with self.assertRaises(ValueError):self.facts()
        self.trial['base_candidate_sha256']=self.inc['candidate_sha256'];self.save()
        self.parent['trials'][0]['receipt']=str(self.root/'outside/result.json');write(self.folder/'result.json',self.parent)
        with self.assertRaises(ValueError):self.facts()

    def test_field_qualification_false_stays_visible(self):
        self.warning_trial('footprint_symbol_field_mismatch','drc_rejected')
        field=self.facts()['trials'][0]['auxiliary']['field_qualification']
        self.assertIs(field['qualified'],False);self.assertNotIn('value',field['detail'])

    def test_no_field_branch_refuses_smuggled_artifacts_journals_record_and_steps(self):
        names=('final-drc-fields.net','final-drc-fields.json','final-drc-fields-proof.json',
               'final-drc-fields-local-settings.json','final-drc-fields-netlist-process.json',
               'final-drc-fields-audit-process.json')
        for name in names:
            path=self.trial_folder/name
            with self.subTest(name=name):
                path.write_bytes(b'inert unexpected field material')
                with self.assertRaisesRegex(ValueError,'without Native field finding'):
                    q.improve_auxiliary(self.trial_folder,self.trial,self.plan)
                path.unlink()
                path.symlink_to(self.trial_folder/'missing-field-material')
                with self.assertRaisesRegex(ValueError,'without Native field finding'):
                    q.improve_auxiliary(self.trial_folder,self.trial,self.plan)
                path.unlink()
        self.trial['native']['field_parity']=None
        with self.assertRaisesRegex(ValueError,'without Native field finding'):
            q.improve_auxiliary(self.trial_folder,self.trial,self.plan)
        del self.trial['native']['field_parity']
        for name in ('final-drc-fields-netlist','final-drc-fields-audit'):
            self.trial['steps'].append(dict(name=name,cwd=str(self.trial_folder)))
            with self.subTest(step=name),self.assertRaisesRegex(ValueError,'without Native field finding'):
                q.improve_auxiliary(self.trial_folder,self.trial,self.plan)
            self.trial['steps'].pop()

    def test_field_applicability_requires_own_report_hash_and_findings(self):
        raw=q.read(self.trial_folder/'final-drc.json');raw['schematic_parity']=[dict(type='footprint_symbol_field_mismatch',severity='warning',items=[])]
        report_pin=write(self.trial_folder/'final-drc.json',raw)
        with self.assertRaisesRegex(ValueError,'applicability report differs'):
            q.improve_auxiliary(self.trial_folder,self.trial,self.plan)
        self.trial['native_report_sha256']=report_pin
        with self.assertRaisesRegex(ValueError,'applicability report differs'):
            q.improve_auxiliary(self.trial_folder,self.trial,self.plan)

    def test_failed_parent_retains_accepted_trial_hashes_without_qualification(self):
        self.trial.update(accepted=True,status='improvement_validated');self.save()
        fact=self.facts(qualified=False)['trials'][0]
        self.assertTrue(fact['accepted']);self.assertFalse(fact['Native_completion_qualified'])
        self.assertEqual(fact['stored_native_evidence']['candidate_sha256'],self.trial['candidate_sha256'])
        self.assertNotIn('own_final',fact)
        self.assertEqual(fact['ignored_checks']['keys'],['lib_footprint_issues'])
        self.assertEqual(fact['finding_types'],{})

    def test_auxiliary_keeps_Default_evidence_hash_not_unknown_payload(self):
        path=self.trial_folder/'final-netclass-audit.json';audit=q.read(path)
        audit['default_targets']['unqualified_foreign_payload']='must not enter generated facts'
        write(path,audit)
        fact=self.facts()['trials'][0]['auxiliary']
        self.assertEqual(fact['Default_targets_policy'],'single-default-global-floor-targets-v2')
        self.assertEqual(fact['files_sha256'][path.name],q.digest(path))
        self.assertNotIn('must not enter',json.dumps(fact))

    def test_strategy_negative_never_becomes_ordinary_completed_negative(self):
        outer=dict(passed=True,status='completed',process=dict(status='success',exit_code=0,cleanup_complete=True,log_truncated=False))
        data=dict(status='completed',controls_passed=True,accepted=False,production_admitted=False,attempt_qualified=True,
            workflow_delivered=False,outcome='validated_completed_negative',method_wall_seconds=10,method_full_cpu_seconds=9)
        self.assertFalse(q.classify(outer,data,dict(wall_seconds=12,CPU_seconds=11),'Cimprove')['attempt_qualified'])

    def test_trial_work_expiry_cannot_be_completed_or_selected(self):
        self.trial['finished_elapsed_seconds']=301;self.save()
        with self.assertRaises(ValueError):self.facts()
        self.trial.update(status='work_reserve_exhausted',accepted=False);self.save()
        self.assertFalse(self.facts()['trials'][0]['Native_completion_qualified'])


if __name__=='__main__':unittest.main()
