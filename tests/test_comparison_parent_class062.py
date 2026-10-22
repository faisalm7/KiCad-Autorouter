"""Constructed062 administration/reporting controls; no Native/query/GUI proof."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from autorouter import config, netclass, pipeline, sexpr
from scripts import freeze_current_comparison as frozen, report_current_comparison as report
from tests import test_comparison_current40 as current40
from tests import test_netclass_parent_pipeline as class_fixture
from tests.test_current_comparison_report import write


class ParentClass062Contracts(unittest.TestCase):
    def population(self):
        names=frozen.IMPROVE_POPULATION
        q=dict(kind=frozen.PARENT_CLASS_QUALIFICATION_KIND,Native_cohort_only=True,
            source_head=frozen.PARENT_CLASS_HEAD,runtime=str(report.ROOT/'.runs/runtime062 fresh install 001'),
            runtime_manifest_sha256=frozen.PARENT_CLASS_MANIFEST,cohort_cases=13,
            parent_class_completed_trials=1,parent_class_invalid_controls=2,finalization_reserve_seconds=40,
            actual_GUI_qualified=False,full_GUI_claim=False)
        pop=dict(schema=1,kind=frozen.PARENT_CLASS_POPULATION_KIND,population=list(names),
            planned_arm_order=list(frozen.IMPROVE_ARM_ORDER),limits=frozen.LIMITS,planned_family_order=['arcdice'],
            families={'arcdice':{}},outputs={'arcdice':dict.fromkeys(names,'path')},administration_head='a'*40,
            source_head=q['source_head'],runtime=q['runtime'],runtime_manifest_sha256=q['runtime_manifest_sha256'],
            improve_finalization_reserve_seconds=40,improve_parent_class_policy='native-parent-dimensions-v1',qualification=q)
        children=dict(schema=1,administration_head='a'*40,policy_or_board_changes_after_first_arm=False,
            protocols={'arcdice':dict.fromkeys(names,{})})
        return pop,children

    def test_shared_validator_has_exact_separate060_and062_configurations(self):
        old=frozen.installed_scope_contract(frozen.CURRENT40_VERSION)
        current=frozen.installed_scope_contract(frozen.PARENT_CLASS_VERSION)
        self.assertEqual(old[:4],('060','212',frozen.CURRENT40_HEAD,
            '8f385b397ddb6379ce35bab92d62ceff55029c6a796f7d3269c5c5b34ed1ba30'))
        self.assertIs(old[4],frozen.CURRENT40_060_PINS)
        self.assertEqual(current[:4],('062','218',frozen.PARENT_CLASS_HEAD,frozen.PARENT_CLASS_MANIFEST))
        self.assertIs(current[4],frozen.PARENT_CLASS_062_PINS)
        self.assertNotEqual(old[4],current[4])
        with self.assertRaises(ValueError):frozen.installed_scope_contract('improve-v4-parent-class061')
        # In particular the new identity must not keep the old original root.
        self.assertEqual(frozen.ROOT/('.runs/runtime-directory-'+current[0]+'/runtime'),
            frozen.ROOT/'.runs/runtime-directory-062/runtime')

    def test_separate_version_keeps_existing_driver_budget_and_legacy_contracts(self):
        self.assertEqual(frozen.contract(frozen.PARENT_CLASS_VERSION),
            (*frozen.contract(frozen.CURRENT40_VERSION)[:2],frozen.PARENT_CLASS_POPULATION_KIND,
             frozen.CURRENT40_METHOD_KIND,'qualify-current-method-003.py'))
        self.assertNotEqual(frozen.PARENT_CLASS_QUALIFICATION_KIND,frozen.CURRENT40_QUALIFICATION_KIND)
        self.assertEqual(frozen.contract('improve-v2')[3],'installed-native7-current-method-v2')
        self.assertEqual(report.improve_reserve(dict(kind=frozen.IMPROVE_METHOD_KIND)),25)
        self.assertEqual(report.improve_reserve(dict(kind=frozen.CURRENT40_METHOD_KIND,improve_finalization_reserve_seconds=40)),40)

    def test_all_six_and_typed062_qualification_are_required_without_GUI_transfer(self):
        pop,children=self.population();self.assertEqual(report.population_shape(pop,children),['arcdice'])
        mutations=[('actual_GUI_qualified',True),('full_GUI_claim',True),('cohort_cases',12),
            ('parent_class_completed_trials',True),('parent_class_invalid_controls',1),
            ('finalization_reserve_seconds',40.0),('source_head',frozen.CURRENT40_HEAD),
            ('runtime_manifest_sha256','0'*64),('kind',frozen.CURRENT40_QUALIFICATION_KIND)]
        for field,value in mutations:
            bad=copy.deepcopy(pop);bad['qualification'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):report.population_shape(bad,children)
        bad=copy.deepcopy(children);del bad['protocols']['arcdice']['Cimprove']
        with self.assertRaises(ValueError):report.population_shape(pop,bad)
        bad=copy.deepcopy(pop);bad['improve_parent_class_policy']='single-default-global-floor-targets-v2'
        with self.assertRaises(ValueError):report.population_shape(bad,children)
        bad=copy.deepcopy(pop);bad['kind']=frozen.CURRENT40_POPULATION_KIND
        with self.assertRaises(ValueError):report.population_shape(bad,children)

    def test_literal062_and060_identity_gates_do_not_alias(self):
        root=frozen.ROOT;identity=dict(git_head=frozen.PARENT_CLASS_HEAD,native_version='10.0.7')
        runtime=root/'.runs/runtime062 fresh install 001'
        with self.assertRaisesRegex(ValueError,'exact installed062'):
            frozen.parent_class_installed_scope({},runtime,'0'*64,identity,{})
        with self.assertRaisesRegex(ValueError,'exact installed060'):
            frozen.current40_installed_scope({},runtime,frozen.PARENT_CLASS_MANIFEST,identity,{})
        with self.assertRaisesRegex(ValueError,'exact installed062'):
            frozen.parent_class_installed_scope({},root/'.runs/runtime060 fresh install 001',
                frozen.PARENT_CLASS_MANIFEST,identity,{})

    def test_every_fixed_raw_pin_is_read_before_summary_can_qualify(self):
        with tempfile.TemporaryDirectory() as name,patch.object(frozen,'ROOT',Path(name).resolve()):
            root=Path(name).resolve();pins={}
            for key in frozen.PARENT_CLASS_062_PINS:
                pins[key]=write(root/key,dict(owned_inert_fixture=True))
            identity=dict(git_head=frozen.PARENT_CLASS_HEAD,native_version='10.0.7')
            with patch.object(frozen,'PARENT_CLASS_062_PINS',pins),patch.object(frozen,'query_runtime') as query:
                for key in pins:
                    file=root/key;raw=file.read_bytes();file.write_bytes(raw+b' ')
                    with self.subTest(key=key),self.assertRaisesRegex(ValueError,'pinned JSON changed'):
                        frozen.parent_class_installed_scope({},root/'.runs/runtime062 fresh install 001',
                            frozen.PARENT_CLASS_MANIFEST,identity,{})
                    file.write_bytes(raw)
                query.assert_not_called()

    def test062_reporter_dependency_does_not_broaden060_or_legacy(self):
        with tempfile.TemporaryDirectory() as name,patch.object(frozen,'ROOT',Path(name).resolve()):
            root=Path(name).resolve();file=root/'scripts/report_current_comparison.py';file.parent.mkdir()
            file.write_bytes(b'# owned inert reporter fixture\n');pin=report.digest(file)
            with patch.object(frozen,'PARENT_CLASS_REPORTER_SHA',pin):
                frozen.qualification_dependency(file,pin,frozen.PARENT_CLASS_VERSION)
                for version in (frozen.CURRENT40_VERSION,'improve-v2'):
                    with self.subTest(version=version),self.assertRaises(ValueError):
                        frozen.qualification_dependency(file,pin,version)


class ParentClassReportLineage(unittest.TestCase):
    def setUp(self):
        self.fixture=current40.Current40ImproveFacts();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.fixture.current();self.control=self.fixture.control;c=self.control
        c.plan['improve_parent_class_policy']='native-parent-dimensions-v1'
        c.context.update(policy='selected-native7-single-parent-class-child-v1',netclass_policy={'mode':'native-parent-dimensions-v1'})
        child=c.folder/'incumbent/improve-child-context.json';write(child,c.context)
        c.inc['native_improve_child']=dict(policy='selected-native7-single-parent-class-child-v1',file=child.name,sha256=report.digest(child))
        c.inc.pop('default_target_transport');c.parent.pop('native7_default_target_basis')
        (c.folder/'incumbent/default-targets.json').unlink()
        write(c.folder/'incumbent/result.json',c.inc)
        c.parent['native7_improve_parent']=dict(policy='selected-native7-single-parent-class-parent-v1',
            file='native7-improve-parent.json',sha256=write(c.folder/'native7-improve-parent.json',
                dict(schema=1,policy='selected-native7-single-parent-class-parent-v1',context=c.context)))
        c.save()
        # These seams isolate marker/own-final/trial dispatch. Real class and
        # dimension auditors are exercised separately below; no worker is run.
        for patcher in (patch.object(report,'parent_class_audit',return_value=({},{})),
                        patch.object(report,'parent_class_basis',return_value={'policy':'constructed-basis-seam'})):
            patcher.start();self.addCleanup(patcher.stop)

    def test_class_markers_keep_own_trial_native_and_historical_Default_separation(self):
        c=self.control;facts=c.facts();self.assertTrue(facts['qualified_parent'])
        self.assertTrue(facts['trials'][0]['Native_completion_qualified'])
        c.plan.pop('improve_parent_class_policy')
        with self.assertRaisesRegex(ValueError,'marker/context'):c.facts()
        c.plan['improve_parent_class_policy']='native-parent-dimensions-v1'
        c.trial['steps'][0]['cleanup_complete']=False;c.save()
        with self.assertRaises(ValueError):c.facts()

    def test_rebound_child_marker_cannot_replace_its_parent_context(self):
        c=self.control;child=c.folder/'incumbent/improve-child-context.json'
        changed=dict(c.context,source_hashes={'forged':'0'*64})
        c.inc['native_improve_child']['sha256']=write(child,changed)
        write(c.folder/'incumbent/result.json',c.inc)
        with self.assertRaisesRegex(ValueError,'exact parent'):c.facts()

    def test062_does_not_relabel_the_old060_Default_only_preview_error(self):
        self.assertIsNone(report.unsupported_improve_preview(self.control.plan,{},self.control.root))


class ParentClassPureAudit(unittest.TestCase):
    def setUp(self):
        self.fixture=class_fixture.ParentPipelineControls();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.folder=Path(temporary.name).resolve()/'route'
        self.source=self.fixture.board;candidate=self.folder/'candidate'/self.source.name
        shutil.copytree(self.source.parent,candidate.parent)
        self.candidate=candidate;self.policy=pipeline.netclass_policy(self.source)
        self.protected=[row for row in pipeline.routes(sexpr.read(self.source)) if pipeline.locked(row)]
        tool_dir=self.folder.parent/'tools';tool_dir.mkdir()
        tool_files={}
        for name in ('kicad-cli','python3.9','_pcbnew.so'):
            file=tool_dir/name;file.write_bytes(b'owned inert tool identity; never executed')
            tool_files[str(file)]=report.digest(file)
        self.plan=dict(kind=frozen.CURRENT40_METHOD_KIND,improve_parent_class_policy='native-parent-dimensions-v1',
            source=str(self.source),source_hashes=report.io.inventory(self.source.parent),runtime='/owned/runtime',
            tools={'kicad':'10.0.7','files':tool_files,'implementation_sha256':
                {'autorouter/'+file.name:report.digest(file) for file in (report.ROOT/'autorouter').glob('*.py')}})
        mapping=self.fixture.mapping();mapping.update(source=str(candidate),board_sha256=report.digest(candidate),native_version='10.0.7')
        write(self.folder/'final-netclasses.json',mapping)
        audit=pipeline.audit_candidate_netclasses(candidate,self.protected,mapping,
            native_toolchain=report.parent_class_toolchain(self.plan),default_target_policy=False)
        audit['native_map_file_sha256']=report.digest(self.folder/'final-netclasses.json')
        write(self.folder/'final-netclass-audit.json',audit)

    def test_checkout1000_audits_pinned1007_without_mutating_config_or_starting_tools(self):
        self.assertEqual(config.NATIVE_VERSION,'10.0.0')
        native=report.read(self.folder/'final-netclasses.json')
        with self.assertRaisesRegex(ValueError,'Unexpected native version'):
            pipeline.audit_candidate_netclasses(self.candidate,self.protected,native)
        toolchain=report.parent_class_toolchain(self.plan)
        self.assertEqual(pipeline.experimental_native_version(toolchain),'10.0.7')
        source_result=(pipeline,netclass,sexpr,self.policy,self.protected)
        with patch.object(report,'parent_class_source',return_value=source_result),patch.object(report.f,'process_check'):
            self.assertEqual(report.parent_class_audit(self.folder,{},self.plan)[0],self.policy)
        self.assertEqual(config.NATIVE_VERSION,'10.0.0')
        bad=copy.deepcopy(self.plan);bad['tools']['files'][str(toolchain.pcbnew)]='0'*64
        with self.assertRaises(pipeline.Rejected):report.parent_class_toolchain(bad)
        bad=copy.deepcopy(self.plan);bad['tools']['kicad']='10.0.0'
        with self.assertRaises(ValueError):report.parent_class_toolchain(bad)

    def test_alias_marker_maps_are_outside_this_canonical_parent_scope(self):
        native=report.read(self.folder/'final-netclasses.json');native['source_all_copper_layers']={}
        write(self.folder/'final-netclasses.json',native)
        with patch.object(report,'parent_class_source',return_value=(pipeline,netclass,sexpr,self.policy,self.protected)),\
             patch.object(report.f,'process_check'),self.assertRaisesRegex(ValueError,'alias-marker'):
            report.parent_class_audit(self.folder,{},self.plan)

    def test_export_requires_exact_sandboxed_process_and_own_export_role(self):
        export=self.folder.parent/'export'/'validation'
        shutil.copytree(self.folder,export)
        candidate=export/'candidate'/self.source.name
        native=report.read(export/'final-netclasses.json')
        native.update(source=str(candidate),board_sha256=report.digest(candidate))
        write(export/'final-netclasses.json',native)
        audit=pipeline.audit_candidate_netclasses(candidate,self.protected,native,
            native_toolchain=report.parent_class_toolchain(self.plan))
        audit['native_map_file_sha256']=report.digest(export/'final-netclasses.json')
        write(export/'final-netclass-audit.json',audit)
        python=next(p for p in self.plan['tools']['files'] if Path(p).name=='python3.9')
        bare=[python,str(Path(self.plan['runtime'])/'autorouter/native.py'),'netclasses',str(candidate),str(export/'final-netclasses.json')]
        step=dict(name='final-netclasses',argv=[*report.f.SANDBOX,*bare],cwd=str(export),
            exit_code=0,status='success',cleanup_complete=True,log_truncated=False)
        data=dict(kind='review-export-v1',export_accepted=True,steps=[step])
        write(export/'final-netclasses-process.json',step)
        source_result=(pipeline,netclass,sexpr,self.policy,self.protected)
        with patch.object(report,'parent_class_source',return_value=source_result):
            report.parent_class_audit(export,data,self.plan,export=True)
            with self.assertRaisesRegex(pipeline.Rejected,'process provenance'):
                report.parent_class_audit(export,data,self.plan)
            step['argv']=bare;write(export/'final-netclasses-process.json',step)
            with self.assertRaisesRegex(pipeline.Rejected,'process provenance'):
                report.parent_class_audit(export,data,self.plan,export=True)
            with self.assertRaisesRegex(ValueError,'export role'):
                report.parent_class_audit(export,dict(data,kind='wrong'),self.plan,export=True)

    def test_new_followup_refuses_sole_Default_even_if_marked_as_parent_policy(self):
        with patch.object(pipeline,'netclass_policy',return_value=dict(mode=netclass.PARENT_POLICY,source_class_names=['Default'])):
            with self.assertRaisesRegex(ValueError,'multiple original classes'):report.parent_class_source(self.plan)

    def test_real_class_dimensions_and_original_PRO_refuse_coherent_wrong_width_or_source(self):
        source_result=(pipeline,netclass,sexpr,self.policy,self.protected)
        with patch.object(report,'parent_class_source',return_value=source_result),patch.object(report.f,'process_check'):
            self.assertEqual(report.parent_class_audit(self.folder,{},self.plan)[0],self.policy)
            tree=sexpr.read(self.candidate)
            tree.append(['segment',['start','10','10'],['end','15','10'],['width','0.4'],
                ['layer','"F.Cu"'],['net','"/PWR_PAIR"'],['uuid','"00000000-0000-0000-0000-000000000001"']])
            sexpr.write(self.candidate,tree)
            mapping=report.read(self.folder/'final-netclasses.json');mapping['board_sha256']=report.digest(self.candidate)
            write(self.folder/'final-netclasses.json',mapping)
            with self.assertRaisesRegex(pipeline.Rejected,'native netclass target'):
                report.parent_class_audit(self.folder,{},self.plan)
            self.candidate.write_bytes(self.source.read_bytes())
            self.candidate.with_suffix('.kicad_pro').write_bytes(self.source.with_suffix('.kicad_pro').read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'original/protected'):
                report.parent_class_audit(self.folder,{},self.plan)

    def test_incumbent_four_file_basis_and_rebound_DSN_cannot_hide_stale_audit(self):
        folder=self.folder;base=folder/'incumbent';base.mkdir(parents=True)
        for name in ('native.dsn','task.dsn'):(base/name).write_bytes(b'owned inert DSN boundary')
        mapping=self.fixture.mapping();mapping.update(source=str(base/'candidate'/self.source.name),
            board_sha256=report.digest(self.source),native_version='10.0.7')
        write(base/'export-netclasses.json',mapping)
        prefs=write(folder/'pruning-preferences.json',dict(owned=True));code={'owned.py':b'owned inert code'}
        for directory in (folder/'code',base/'code'):
            directory.mkdir()
            for name,raw in code.items():(directory/name).write_bytes(raw)
        code_pins={name:report.digest(folder/'code'/name) for name in code}
        plan=copy.deepcopy(self.plan);plan['tools']['implementation_sha256']={'autorouter/'+k:v for k,v in code_pins.items()}
        shutil.copytree(self.source.parent,folder/'snapshot')
        inc=dict(baseline='B2_tuned',engine_profile='tuned',scope='whole_board_unlocked_routing',
            source=plan['source'],source_hashes=plan['source_hashes'],netclass_policy=self.policy,
            task_sha256=report.digest(self.source),budget_seconds=50,cpu_budget_seconds=50)
        def dsn_audit(file,*args,**kwargs):
            if kwargs:
                self.assertIs(kwargs.get('parent_policy'),True)
                self.assertEqual(pipeline.experimental_native_version(kwargs.get('native_toolchain')),'10.0.7')
                self.assertEqual(config.NATIVE_VERSION,'10.0.0')
            return dict(dsn_sha256=report.digest(file),constructed_parser_seam=True)
        for name,key in (('native.dsn','netclass_export_audit'),('task.dsn','netclass_task_audit')):inc[key]=dsn_audit(base/name)
        write(base/'result.json',inc)
        parent=dict(netclass_policy=self.policy,task_sha256=inc['task_sha256'],netclass_parent_dsn_basis=pipeline.parent_dsn_basis(folder))
        stat=folder.stat();context=dict(policy='selected-native7-single-parent-class-child-v1',netclass_policy=self.policy,
            method_seconds=90,assigned_seconds=50,allocation=dict(elapsed_wall_seconds=0,elapsed_cpu_seconds=0),
            directory_identity=[stat.st_dev,stat.st_ino],inputs=dict(snapshot=plan['source_hashes'],code=code_pins,
                netclass_policy=self.policy,preferences_sha256=prefs,effective=dict(frozen.pref.DEFAULTS,seconds=90,profile='tuned')))
        with patch.object(report,'parent_class_source',return_value=(pipeline,netclass,sexpr,self.policy,self.protected)),\
             patch.object(netclass,'audit_dsn',side_effect=dsn_audit),patch.object(report.f,'process_check'):
            self.assertEqual(report.parent_class_basis(folder,parent,inc,context,plan),parent['netclass_parent_dsn_basis'])
            (base/'task.dsn').write_bytes(b'changed owned DSN')
            with self.assertRaisesRegex(ValueError,'incumbent/source/basis'):
                report.parent_class_basis(folder,parent,inc,context,plan)
            parent['netclass_parent_dsn_basis']=pipeline.parent_dsn_basis(folder)
            with self.assertRaisesRegex(ValueError,'Native/DSN dimensions'):
                report.parent_class_basis(folder,parent,inc,context,plan)

    def test_unknown_or_changed_parser_implementation_cannot_audit_class_proofs(self):
        self.plan['tools']['implementation_sha256']['autorouter/netclass.py']='0'*64
        with self.assertRaisesRegex(ValueError,'implementation changed'):report.parent_class_source(self.plan)


if __name__=='__main__':unittest.main()
