"""Constructed parent-class Improve controls; no Native/engine/GUI qualification.

The real owned Context, source/class parser, class/dimension auditors and export
stage dispatch execute. Worker readbacks are explicit seams, never Native proof.
"""
import copy
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
from autorouter import _improve_context as child, config as c, floor_route as f
from autorouter import gui, local_settings as local, netclass as n, pipeline as p
from autorouter import preferences as pref, review_export as export, sexpr as sx, strategy as s
from experiments.netclass_parent_transport_v1 import fixture
from tests import test_native7_improve_child_context as child_fixture
from tests import test_native7_improve_parent as parent_fixture
from tests import test_netclass_parent_pipeline as class_fixture
from tests.test_strategy import metrics

REAL_NETCLASS_POLICY = p.netclass_policy


class ParentClassImproveControls(unittest.TestCase):
    make = child_fixture.ImproveChildContextControls.make
    parent_data = parent_fixture.Native7ParentControls.parent_data

    def setUp(self):
        child_fixture.ImproveChildContextControls.setUp(self)
        files, _ = fixture.prepare(protected=True)
        self.source.write_bytes(files['fixture.kicad_pcb'])
        self.source.with_suffix('.kicad_pro').write_bytes(files['fixture.kicad_pro'])
        # The inherited flat SCH and Native/preflight stubs are constructed;
        # this fixture is not an electrically matched Native project.
        self.hashes = p.tree_hash(self.source.parent)
        shutil.rmtree(self.parent/'snapshot')
        shutil.copytree(self.source.parent,self.parent/'snapshot')
        policy_patch = patch.object(p,'netclass_policy',side_effect=REAL_NETCLASS_POLICY)
        policy_patch.start(); self.addCleanup(policy_patch.stop)
        self.policy = REAL_NETCLASS_POLICY(self.source)
        self.assertEqual(self.policy['mode'],n.PARENT_POLICY)
        self.context = self.make(netclass_policy=copy.deepcopy(self.policy))
        self.board = self.source
        self.project = json.loads(self.source.with_suffix('.kicad_pro').read_text())

    def record(self):
        data = child_fixture.ImproveChildContextControls.record(self)
        data['netclass_policy'] = copy.deepcopy(self.policy)
        return data

    def incumbent(self,data):
        inc = self.record()
        candidate = self.context.output/'candidate'/self.source.name
        shutil.copytree(self.source.parent,candidate.parent)
        inc.update(accepted=True,status='routing_accepted',steps=[],task_sha256='a'*64,
                   candidate=str(candidate),candidate_sha256=p.sha(candidate))
        # These files bind the fixture only. Full DSN/Native readback remains a
        # sentinel seam below; their contents are never accepted as real proof.
        for name in ('native.dsn','task.dsn','export-netclasses.json'):
            (self.context.output/name).write_text('constructed material; not Native evidence\n')
        p.save_json(self.context.output/'result.json',inc)
        data.update(task_sha256=inc['task_sha256'],incumbent={'receipt':str(self.context.output/'result.json')})
        data['netclass_parent_dsn_basis'] = p.parent_dsn_basis(self.parent)
        return inc

    def mapping(self):
        result = class_fixture.ParentPipelineControls.mapping(self)
        result['native_version'] = c.NATIVE_VERSION
        return result

    def test_versioned_scope_preserves_source_and_requires_explicit_live_context(self):
        before = p.tree_hash(self.source.parent)
        effective = dict(pref.DEFAULTS,profile='tuned',seconds=90)
        self.assertEqual(s.native7_single_scope(self.source,effective),effective)
        self.assertEqual(self.context.record()['policy'],child.PARENT_CLASS_POLICY)
        self.assertEqual(self.context.record()['netclass_policy'],self.policy)
        self.assertEqual(p.tree_hash(self.source.parent),before)
        with self.assertRaises(p.Rejected):self.make()  # old Default contract
        data = self.record()
        self.assertTrue(child.check_record(self.context.output,data,self.context))
        with self.assertRaises(p.Rejected):child.check_record(self.context.output,data,None)
        with self.assertRaises(p.Rejected):child.require(self.context.record())

    def test_other_modes_flags_hierarchy_and_four_copper_remain_unsupported(self):
        effective = dict(pref.DEFAULTS,profile='tuned',seconds=90)
        with patch.object(p,'netclass_policy',return_value={'mode':'literal-two-class-v1'}):
            with self.assertRaises(p.Rejected):s.native7_single_scope(self.source,effective)
            with self.assertRaises(p.Rejected):self.make(netclass_policy={'mode':'literal-two-class-v1'})
        for requirement in ({'flags':['POWER']},{'hierarchy':True}):
            with self.subTest(requirement=requirement),patch.object(p,'check_schematic_class_support',return_value=requirement):
                with self.assertRaises(p.Rejected):s.native7_single_scope(self.source,effective)
                with self.assertRaises(p.Rejected):self.make(netclass_policy=self.policy)
        tree = sx.read(self.source)
        layers = sx.one(tree,'layers')
        layers[2:2] = [['4','"In1.Cu"','signal'],['6','"In2.Cu"','signal']]
        sx.write(self.source,tree)
        with self.assertRaises((ValueError,p.Rejected)):s.native7_single_scope(self.source,effective)

    def test_unknown_priorities_patterns_and_native_parameter_parents_refuse(self):
        project_path = self.source.with_suffix('.kicad_pro');original = project_path.read_bytes()
        for change in ('priority','unknown_pattern'):
            changed = copy.deepcopy(self.project)
            if change=='priority':changed['net_settings']['classes'][1]['priority']=True
            else:changed['net_settings']['netclass_patterns'][0]['netclass']='UNKNOWN'
            project_path.write_text(json.dumps(changed))
            with self.subTest(change=change),self.assertRaises((ValueError,p.Rejected)):
                s.native7_single_scope(self.source,dict(pref.DEFAULTS,profile='tuned',seconds=90))
            project_path.write_bytes(original)
        mapping = self.mapping()
        self.assertTrue(p.audit_candidate_netclasses(self.source,[],mapping)['native']['passed'])
        mapping['nets'][1]['parameter_parents']['width_nm']['name']='Default'
        with self.assertRaises(ValueError):p.audit_candidate_netclasses(self.source,[],mapping)

    def test_original_class_targets_are_not_clamped_and_wrong_new_width_refuses(self):
        tree = sx.read(self.source);protected = [r for r in p.routes(tree) if p.locked(r)]
        self.assertTrue(p.audit_candidate_netclasses(self.source,protected,self.mapping())['native']['passed'])
        tree.append(['segment',['start','15','10'],['end','20','10'],['width','0.4'],
                     ['layer','"F.Cu"'],['net','"/PWR_PAIR"'],['uuid','"10000000-0000-0000-0000-000000000001"']])
        sx.write(self.source,tree)
        with self.assertRaisesRegex(p.Rejected,'native netclass target'):
            p.audit_candidate_netclasses(self.source,protected,self.mapping())

    def test_mutable_class_policy_field_remains_sealed(self):
        self.context.netclass_policy['source_class_names'].append('FORGED')
        with self.assertRaises(p.Rejected):child.require(self.context)

    def test_parent_class_context_retains_original_owned_inode_and_exact_types(self):
        for owner in (self.context.parent_owner,self.context._owner):
            identity=owner['directory_identity']
            owner['directory_identity']=(float(identity[0]),identity[1])
            with self.assertRaises(p.Rejected):child.require(self.context)
            owner['directory_identity']=identity
        retained=self.workspace/'retained-parent-class-route'
        self.parent.rename(retained);self.parent.mkdir()
        try:
            with self.assertRaises(p.Rejected):child.require(self.context)
        finally:self.parent.rmdir();retained.rename(self.parent)

    def test_same_policy_summary_cannot_hide_changed_original_pro_bytes(self):
        project_path = self.source.with_suffix('.kicad_pro')
        project_path.write_bytes(project_path.read_bytes()+b'\n')
        with self.assertRaises(p.Rejected):child.require(self.context)

    def test_parent_policy_downgrade_and_default_target_material_cannot_mix(self):
        data = self.parent_data();inc = self.incumbent(data)
        self.assertEqual(data['native7_improve_parent']['policy'],s.NATIVE7_PARENT_CLASS_POLICY)
        self.assertIsNone(s.native7_default_target_basis(self.parent,data))
        wrong = copy.deepcopy(data);wrong['native7_improve_parent']['policy']=s.NATIVE7_PARENT_POLICY
        with self.assertRaises(p.Rejected):s.native7_incumbent_context(self.parent,wrong)
        inc['default_target_transport']={'policy':'forged'};p.save_json(self.context.output/'result.json',inc)
        data['netclass_parent_dsn_basis']=p.parent_dsn_basis(self.parent)
        with self.assertRaises(p.Rejected):s.native7_default_target_basis(self.parent,data)

    def test_dsn_readback_keeps_private_child_context_and_original_basis(self):
        data = self.parent_data();self.incumbent(data)
        with patch.object(p,'check_result',return_value={'constructed':True}) as checker:
            p.check_parent_dsn_basis(self.parent,data,_improve_context=self.context)
        checker.assert_called_once_with(self.context.output/'result.json',_improve_context=self.context)
        def rewrite(*args,**kwargs):
            (self.context.output/'task.dsn').write_text('coherently rewritten during checker')
            data['netclass_parent_dsn_basis']=p.parent_dsn_basis(self.parent)
        with patch.object(p,'check_result',side_effect=rewrite),self.assertRaisesRegex(p.Rejected,'captured DSN basis'):
            p.check_parent_dsn_basis(self.parent,data,_improve_context=self.context)

    def test_pure_dsn_lineage_keeps_every_basis_without_child_acceptance(self):
        data=self.parent_data();inc=self.incumbent(data)
        with patch.object(p,'check_result',side_effect=AssertionError('pure lineage grants no child acceptance')):
            self.assertEqual(p._parent_dsn_lineage(self.parent,data),inc)
            for name in ('result.json','native.dsn','task.dsn','export-netclasses.json'):
                path=self.context.output/name;raw=path.read_bytes()
                try:
                    path.write_bytes(raw+b'\n')
                    with self.subTest(name=name),self.assertRaises(p.Rejected):p._parent_dsn_lineage(self.parent,data)
                finally:path.write_bytes(raw)

    def test_late_parent_class_audit_precedes_material_and_all_root_prl_last(self):
        data = self.parent_data();self.incumbent(data);(self.parent/'trials').mkdir()
        events=[]
        def audit(*args,**kwargs):
            self.assertFalse(kwargs['default_target_policy'])
            self.assertIsNone(kwargs['default_target_basis']);events.append('own class audit')
        with patch.object(p,'check_final_netclass_evidence',side_effect=audit), \
                patch.object(p,'check_experimental_local_settings'), \
                patch.object(local,'check_final_events',side_effect=lambda *a,**k:events.append('all root PRL last')):
            s.check_native7_final(self.parent,data,material=lambda:events.append('material'))
        self.assertEqual(events,['own class audit','material','all root PRL last'])

    def test_actual_trial_replay_uses_fresh_native_class_dimensions(self):
        data = self.parent_data();self.incumbent(data)
        folder = self.parent/'trials/trial-0000';candidate=folder/'candidate'/self.source.name
        shutil.copytree(self.source.parent,candidate.parent)
        shutil.copytree(self.source.parent,folder/'refill')
        native={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'findings':[], 'ignored_checks':[]}
        (folder/'final-drc.json').write_text('{}')
        for wrong in (False,True):
            tree=sx.read(self.source)
            if wrong:tree.append(['segment',['start','15','10'],['end','20','10'],['width','0.4'],
                ['layer','"F.Cu"'],['net','"/PWR_PAIR"'],['uuid','"10000000-0000-0000-0000-000000000002"']])
            for file in (candidate,folder/'pre-refill.kicad_pcb',folder/'refill'/self.source.name):sx.write(file,tree)
            mapping=self.mapping();mapping.update(source=str(candidate),board_sha256=p.sha(candidate))
            p.save_json(folder/'final-netclasses.json',mapping)
            if not wrong:
                protected=[r for r in p.routes(sx.read(self.source)) if p.locked(r)]
                audit=p.audit_candidate_netclasses(candidate,protected,mapping)
                audit['native_map_file_sha256']=p.sha(folder/'final-netclasses.json')
                p.save_json(folder/'final-netclass-audit.json',audit)
            result=dict(id=folder.name,status='improvement_validated',accepted=True,steps=[],
                finished_elapsed_seconds=10.,finished_observed_cpu_seconds=10.,
                single_trial_guard=dict(wall_deadline_elapsed_seconds=50.,work_cpu_limit_seconds=50.),
                candidate_sha256=p.sha(candidate),native=native,native_report_sha256=p.sha(folder/'final-drc.json'),
                metrics=metrics(tree))
            p.save_json(folder/'metrics.json',result['metrics'])
            with self.subTest(wrong_new_width=wrong),patch.object(f,'check_drc_stage',return_value=native), \
                    patch.object(f,'process_check'):
                if wrong:
                    with self.assertRaisesRegex(p.Rejected,'native netclass target'):
                        s._adaptive_trial_native(self.parent,data,result,guard_key='single_trial_guard')
                else:self.assertTrue(s._adaptive_trial_native(self.parent,data,result,guard_key='single_trial_guard'))

    def test_unmarked_direct_single_guard_keeps_true_default_audit_when_basis_is_none(self):
        # No product legacy caller reaches this private single-guard branch.
        # Preserve its old True fallback explicitly even for direct invocations.
        legacy=self.workspace/'unmarked-direct-helper'
        candidate=legacy/'trials/trial-0000/candidate'/self.source.name
        shutil.copytree(self.source.parent,candidate.parent)
        folder=candidate.parent.parent
        shutil.copytree(self.source.parent,folder/'refill')
        shutil.copytree(self.source.parent,legacy/'snapshot')
        (folder/'pre-refill.kicad_pcb').write_bytes(self.source.read_bytes())
        (folder/'final-drc.json').write_text('{}')
        native={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'findings':[], 'ignored_checks':[]}
        data=dict(budget_seconds=90.,cpu_budget_seconds=90.,source=str(self.source),source_hashes=self.hashes)
        record=dict(id=folder.name,status='improvement_validated',accepted=True,steps=[],
            finished_elapsed_seconds=10.,finished_observed_cpu_seconds=10.,
            single_trial_guard=dict(wall_deadline_elapsed_seconds=50.,work_cpu_limit_seconds=50.),
            candidate_sha256=p.sha(candidate),native=native,native_report_sha256=p.sha(folder/'final-drc.json'))
        for version in ('10.0.0','10.0.7'):
            with self.subTest(version=version),patch.object(c,'NATIVE_VERSION',version), \
                    patch.object(f,'check_drc_stage',return_value=native), \
                    patch.object(p,'check_final_netclass_evidence',side_effect=p.Rejected('old Default audit sentinel')) as audit:
                with self.assertRaisesRegex(p.Rejected,'old Default audit sentinel'):
                    s._adaptive_trial_native(legacy,data,record,guard_key='single_trial_guard')
            self.assertIsNone(audit.call_args.kwargs['default_target_basis'])
            self.assertIs(audit.call_args.kwargs['default_target_policy'],True)

    def test_actual_export_stage_demands_fresh_class_audit_with_no_default_basis(self):
        data = self.parent_data();inc = self.incumbent(data)
        folder = self.workspace/'export-validation';candidate = folder/'candidate'/self.source.name
        shutil.copytree(self.source.parent,candidate.parent)
        shutil.copytree(self.source.parent,folder/'refill')
        native={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'findings':[], 'ignored_checks':[]}
        binding=dict(receipt=str(self.parent/'result.json'),source=str(self.source),source_hashes=self.hashes,
                     input_policy='native',validated_candidate=inc['candidate'],validated_candidate_sha256=inc['candidate_sha256'])
        stage=dict(candidate=str(candidate),candidate_sha256=p.sha(candidate),native=native,
                   schematic_parity=p.parity_declaration(self.source,self.hashes))
        with patch.object(f,'check_drc_stage',return_value=native), \
                patch.object(p,'check_final_netclass_evidence',side_effect=p.Rejected('fresh export class audit sentinel')) as audit:
            with self.assertRaisesRegex(p.Rejected,'fresh export class audit sentinel'):
                export.check_stage(folder,stage,binding,data,None,None,None)
        self.assertFalse(audit.call_args.kwargs['default_target_policy'])
        self.assertIsNone(audit.call_args.kwargs['default_target_basis'])
        self.assertTrue(audit.call_args.kwargs['sandboxed'])


class DefaultContractRegression(unittest.TestCase):
    setUp = child_fixture.ImproveChildContextControls.setUp
    make = child_fixture.ImproveChildContextControls.make

    def test_default_record_and_parent_marker_stay_on_original_versions(self):
        record = self.context.record()
        self.assertEqual(record['policy'],child.POLICY)
        self.assertNotIn('netclass_policy',record)
        self.assertNotIn('netclass_policy',record['inputs'])
        data={};s._bind_native7_parent(self.parent,data,self.context)
        self.assertEqual(data['native7_improve_parent']['policy'],s.NATIVE7_PARENT_POLICY)
        self.assertNotIn('netclass_policy',data)
        self.assertEqual(s.NATIVE_FINAL_RESERVE_SECONDS,40)
        self.assertEqual(s.MAX_TRIALS,32)


if __name__=='__main__':unittest.main()
