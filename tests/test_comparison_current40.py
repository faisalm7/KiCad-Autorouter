"""Constructed current40 admission/reporting controls, no Native or tool query."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import freeze_current_comparison as frozen, qualify_current_method as method
from scripts import report_current_comparison as report
from tests import test_comparison_improve as controls
from tests.test_current_comparison_report import write


class Current40Contracts(unittest.TestCase):
    def test_reporter_dependency_is_not_parsed_as_json_or_admitted_in_legacy(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name).resolve();path=root/'scripts/report_current_comparison.py';path.parent.mkdir()
            path.write_bytes(b'"""owned Python reporter fixture"""\npass\n');pin=report.digest(path)
            with patch.object(frozen,'ROOT',root),patch.object(frozen,'CURRENT40_REPORTER_SHA',pin):
                frozen.qualification_dependency(path,pin,frozen.CURRENT40_VERSION)
                with self.assertRaises(ValueError):frozen.qualification_dependency(path,pin,'improve-v2')
                with self.assertRaises(ValueError):frozen.qualification_dependency(path,'0'*64,frozen.CURRENT40_VERSION)
                other=root/'other.py';other.write_bytes(path.read_bytes())
                with self.assertRaises(ValueError):frozen.qualification_dependency(other,pin,frozen.CURRENT40_VERSION)
                valid=root/'evidence.json';json_pin=write(valid,dict(owned=True))
                frozen.qualification_dependency(valid,json_pin,frozen.CURRENT40_VERSION)
                valid.write_bytes(valid.read_bytes()+b' ')
                with self.assertRaises(ValueError):frozen.qualification_dependency(valid,json_pin,frozen.CURRENT40_VERSION)

    def test_exact_versions_and_reserve_do_not_alias(self):
        self.assertEqual(frozen.contract('improve-v2')[3:],(method.IMPROVE_KIND,'qualify-current-method-002.py'))
        self.assertEqual(frozen.contract(frozen.CURRENT40_VERSION)[3:],(method.CURRENT40_KIND,'qualify-current-method-003.py'))
        self.assertEqual(method.method_reserve(dict(kind=method.IMPROVE_KIND)),25)
        self.assertEqual(method.method_reserve(dict(kind=method.CURRENT40_KIND,improve_finalization_reserve_seconds=40)),40)
        for plan in (dict(kind=method.IMPROVE_KIND,improve_finalization_reserve_seconds=40),
                     dict(kind=method.CURRENT40_KIND),
                     dict(kind=method.CURRENT40_KIND,improve_finalization_reserve_seconds=25),
                     dict(kind=method.CURRENT40_KIND,improve_finalization_reserve_seconds=40.0)):
            with self.subTest(plan=plan),self.assertRaises(ValueError):method.method_reserve(plan)
        path=Path(frozen.__file__).with_name('enclose_current_comparison.py')
        node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='ordinary_method_contract')
        scope={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(path)+'::constructed','exec'),scope)
        allows=scope['ordinary_method_contract']
        self.assertTrue(allows(dict(kind=method.CURRENT40_KIND,arm='Cimprove'),Path('qualify-current-method-003.py'),False))
        for child,external in [('qualify-current-method-002.py',False),('qualify-current-method-003.py',True)]:
            self.assertFalse(allows(dict(kind=method.CURRENT40_KIND,arm='Cimprove'),Path(child),external))

    def test_current40_declared_value_is_pinned_and_typed(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name).resolve();path=root/'autorouter/_improve_context.py';path.parent.mkdir()
            for value in ('40','25','40.0','True'):
                path.write_text('RESERVE_SECONDS = '+value+'\n')
                pins={'autorouter/_improve_context.py':hashlib.sha256(path.read_bytes()).hexdigest()}
                if value=='40':self.assertEqual(frozen.current40_reserve(root,pins),40)
                else:
                    with self.subTest(value=value),self.assertRaises(ValueError):frozen.current40_reserve(root,pins)
            path.write_text('RESERVE_SECONDS = 40\n')
            with self.assertRaises(ValueError):frozen.current40_reserve(root,{'autorouter/_improve_context.py':'0'*64})

    def test_root_only_installation_record_never_becomes_authority(self):
        original,runtime=Path('/owned/original'),Path('/owned/installed')
        old=dict(root=str(original),immutable_files_sha256={str(i):'a'*64 for i in range(54)},
            native_version='10.0.7',local_engine=dict(sha256='b'*64))
        new=dict(old,root=str(runtime))
        receipt=dict(schema=1,kind='existing-runtime-installation-record-v1',source_root=str(original),
            destination_root=str(runtime),source_manifest_sha256='c'*64,destination_manifest_sha256='d'*64,
            immutable_files=54,local_engine=new['local_engine'],record_is_authoritative=False,
            receipt_may_remain_on_refusal=True,same_mac_dependency_locations_required=True,
            **dict.fromkeys(('mutable_state_copied','venv_created','launcher_created',
                             'native_qualification_performed','standalone','published'),False))
        def check(o=old,n=new,r=receipt):
            frozen.installed_root_binding(o,n,r,original,runtime,'c'*64,'d'*64)
        check()
        for key,value in [('source_manifest_sha256','e'*64),('destination_manifest_sha256','e'*64),
                          ('record_is_authoritative',True),('native_qualification_performed',True),
                          ('destination_root',str(original))]:
            bad=dict(receipt,**{key:value})
            with self.subTest(key=key),self.assertRaises(ValueError):check(r=bad)
        bad=copy.deepcopy(new);bad['immutable_files_sha256']['0']='f'*64
        with self.assertRaises(ValueError):check(n=bad)

    def test_wrong_cohort_bytes_or_qualification_payload_refuse_before_query(self):
        with tempfile.TemporaryDirectory() as name,patch.object(frozen,'ROOT',Path(name).resolve()):
            root=Path(name).resolve();runtime=root/'.runs/runtime060 fresh install 001'
            pin='8f385b397ddb6379ce35bab92d62ceff55029c6a796f7d3269c5c5b34ed1ba30'
            identity=dict(git_head=frozen.CURRENT40_HEAD,native_version='10.0.7')
            bindings={}
            for index,key in enumerate(frozen.CURRENT40_060_PINS):
                path=root/key;path.parent.mkdir(parents=True,exist_ok=True)
                bindings[key]=write(path,dict(owned_fixture=index))
            with patch.object(frozen,'CURRENT40_060_PINS',bindings):
                first=root/next(iter(bindings))
                first.write_bytes(first.read_bytes()+b' ')
                with self.assertRaisesRegex(ValueError,'pinned JSON changed'):
                    frozen.current40_installed_scope({},runtime,pin,identity,{})
                write(first,dict(owned_fixture=0))
                with self.assertRaisesRegex(ValueError,'exact completed installed13 cohort'):
                    frozen.current40_installed_scope({'changed':True},runtime,pin,identity,{})
            with self.assertRaisesRegex(ValueError,'exact installed060'):
                frozen.current40_installed_scope({},runtime,'0'*64,identity,{})

    def test_all_four_clusters_and_unsupported_arm_stay_in_denominator(self):
        names=frozen.IMPROVE_POPULATION;families=['ds18','ir','eeprom','arcdice']
        q=dict(kind=frozen.CURRENT40_QUALIFICATION_KIND,Native_cohort_only=True,
            source_head=frozen.CURRENT40_HEAD,runtime='/owned/runtime',runtime_manifest_sha256='a'*64,
            cohort_cases=13,finalization_reserve_seconds=40,actual_GUI_qualified=False,full_GUI_claim=False)
        pop=dict(schema=1,kind=frozen.CURRENT40_POPULATION_KIND,population=list(names),
            planned_arm_order=list(frozen.IMPROVE_ARM_ORDER),limits=frozen.LIMITS,planned_family_order=families,
            families=dict.fromkeys(families,{}),outputs={key:dict.fromkeys(names,'path') for key in families},
            administration_head='b'*40,source_head=frozen.CURRENT40_HEAD,runtime='/owned/runtime',
            runtime_manifest_sha256='a'*64,improve_finalization_reserve_seconds=40,qualification=q)
        children=dict(schema=1,administration_head='b'*40,policy_or_board_changes_after_first_arm=False,
            protocols={key:dict.fromkeys(names,{}) for key in families})
        self.assertEqual(report.population_shape(pop,children),families)
        self.assertEqual(sum(len(rows) for rows in children['protocols'].values()),24)
        for field in ('improve_finalization_reserve_seconds',):
            bad=copy.deepcopy(pop);bad[field]=25
            with self.assertRaises(ValueError):report.population_shape(bad,children)
        bad=copy.deepcopy(children);del bad['protocols']['arcdice']['Cimprove']
        with self.assertRaises(ValueError):report.population_shape(pop,bad)


class Current40ImproveFacts(unittest.TestCase):
    def setUp(self):
        self.control=controls.ImproveFactsTests()
        self.control.setUp();self.addCleanup(self.control.doCleanups)

    def current(self):
        c=self.control;c.plan.update(kind=method.CURRENT40_KIND,improve_finalization_reserve_seconds=40)
        c.context['finalization_reserve_seconds']=40
        child=c.folder/'incumbent/improve-child-context.json';write(child,c.context)
        c.inc['native_improve_child']['sha256']=report.digest(child);write(c.folder/'incumbent/result.json',c.inc)
        c.parent['native7_default_target_basis']['receipt_sha256']=report.digest(c.folder/'incumbent/result.json')
        marker=c.folder/'native7-improve-parent.json'
        c.parent['native7_improve_parent']['sha256']=write(marker,dict(schema=1,
            policy='selected-native7-single-improve-parent-v1',context=c.context))
        c.parent.update(finalization_reserve_seconds=40,finalization_cpu_reserve_seconds=40)
        c.trial['single_trial_guard']['work_cpu_limit_seconds']=380
        c.parent['steps'] = [*[dict(step,phase='incumbent') for step in c.inc['steps']],
            *[dict(step,phase='trial-0000') for step in c.trial['steps']],
            *[step for step in c.parent['steps'] if step.get('phase') not in ('incumbent','trial-0000')]]
        c.save()

    def test_historical25_is_still_admitted_and40_requires_new_version(self):
        c=self.control;c.plan['kind']=method.IMPROVE_KIND
        self.assertTrue(c.facts()['qualified_parent'])
        self.current();self.assertTrue(c.facts()['qualified_parent'])
        c.plan=dict(c.plan,kind=method.IMPROVE_KIND);c.plan.pop('improve_finalization_reserve_seconds')
        with self.assertRaises(ValueError):c.facts()

    def test_current40_rejects_parent_context_and_trial_reserve_mismatches(self):
        self.current();c=self.control
        for key in ('finalization_reserve_seconds','finalization_cpu_reserve_seconds'):
            old=c.parent[key];c.parent[key]=25;c.save()
            with self.subTest(key=key),self.assertRaises(ValueError):c.facts()
            c.parent[key]=old;c.save()
        marker=c.folder/'native7-improve-parent.json'
        c.context['finalization_reserve_seconds']=25
        c.parent['native7_improve_parent']['sha256']=write(marker,dict(schema=1,
            policy='selected-native7-single-improve-parent-v1',context=c.context));c.save()
        with self.assertRaises(ValueError):c.facts()
        c.context['finalization_reserve_seconds']=40
        c.parent['native7_improve_parent']['sha256']=write(marker,dict(schema=1,
            policy='selected-native7-single-improve-parent-v1',context=c.context));c.save()
        c.trial['single_trial_guard']['work_cpu_limit_seconds']=395;c.save()
        with self.assertRaises(ValueError):c.facts()

    def test_incumbent_header_change_cannot_receive_a_new_first_read_seal(self):
        self.current();c=self.control
        # Own Native data stay byte-identical. The already bound parent's
        # incumbent hash must still refuse this otherwise plausible edit.
        c.inc['budget_seconds']=1
        write(c.folder/'incumbent/result.json',c.inc)
        with self.assertRaisesRegex(ValueError,'Default basis differs'):c.facts()

    def test_parent_worker_lineage_cannot_omit_incumbent_or_trial(self):
        self.current();c=self.control;original=copy.deepcopy(c.parent['steps'])
        for phase in ('incumbent','trial-0000'):
            c.parent['steps']=[step for step in original if step.get('phase')!=phase];c.save()
            with self.subTest(phase=phase),self.assertRaisesRegex(ValueError,'worker lineage'):c.facts()
        c.parent['steps']=original;c.save();self.assertTrue(c.facts()['qualified_parent'])

    def test_completed90_prerequisite_budget_is_explicit_and_not_receipt_selected(self):
        self.current();c=self.control
        def replay(seconds):
            return report.improve_facts(c.folder/'result.json',c.plan,[c.root],qualified_parent=True,
                public_sanitize=True,prerequisite_seconds=seconds)
        with self.assertRaises(ValueError):replay(90)
        c.context['method_seconds']=90
        child=c.folder/'incumbent/improve-child-context.json';write(child,c.context)
        c.inc['native_improve_child']['sha256']=report.digest(child);write(c.folder/'incumbent/result.json',c.inc)
        c.parent['native7_default_target_basis']['receipt_sha256']=report.digest(c.folder/'incumbent/result.json')
        c.parent['native7_improve_parent']['sha256']=write(c.folder/'native7-improve-parent.json',
            dict(schema=1,policy='selected-native7-single-improve-parent-v1',context=c.context))
        c.parent.update(budget_seconds=90,cpu_budget_seconds=90)
        c.trial['single_trial_guard'].update(work_cpu_limit_seconds=50,wall_deadline_elapsed_seconds=50);c.save()
        self.assertTrue(replay(90)['qualified_parent'])
        with self.assertRaises(ValueError):c.facts()  # Normal comparison still420.
        for seconds in (True,25,90.0,420):
            with self.subTest(seconds=seconds),self.assertRaises(ValueError):replay(seconds)


class UnsupportedPreviewFacts(unittest.TestCase):
    def test_mutable_export_witness_cannot_reseal_changed_recorded_preview(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name).resolve();plot=root/'plots/F.Cu.svg';plot.parent.mkdir()
            plot.write_bytes(b'<svg>original owned fixture</svg>')
            source=root/'plot-input';source.mkdir();board=source/'owned.kicad_pcb';board.write_bytes(b'owned inert input')
            preview=dict(files={'plots/F.Cu.svg':report.digest(plot)},
                input_trees={'plot-input':report.io.inventory(source)})
            report.preview_material(root,preview)
            plot.write_bytes(b'<svg>changed fixture</svg>')
            refreshed_export_witness={'plots/F.Cu.svg':report.digest(plot)}
            self.assertNotEqual(refreshed_export_witness,preview['files'])
            with self.assertRaisesRegex(ValueError,'preview bytes changed'):report.preview_material(root,preview)
            plot.write_bytes(b'<svg>original owned fixture</svg>');board.write_bytes(b'changed input')
            with self.assertRaisesRegex(ValueError,'preview input changed'):report.preview_material(root,preview)

    def test_exact_refusal_stays_unqualified_without_native_or_downstream_work(self):
        with tempfile.TemporaryDirectory() as name:
            out=Path(name).resolve();workspace=out/('autorouter-gui-'+'a'*32);workspace.mkdir()
            settings=dict(schema=1,profile='tuned',seconds=420)
            write(workspace/'settings.json',settings)
            plan=dict(kind=method.CURRENT40_KIND,arm='Cimprove',runtime='/owned/runtime',
                source='/owned/source/board.kicad_pcb',improve_settings=settings)
            argv=['/owned/runtime/.venv/bin/python','-B','-m','autorouter','preview',plan['source'],
                '--settings',str(workspace/'settings.json'),'--purpose','improve']
            log=out/'preview.log';journal=out/'preview.process.json'
            write(log,dict(accepted=False,error='unsupported: selected7 Improve requires sole explicit/implicit Default'))
            process=dict(argv=argv,exit_code=2,cancel_requested=False,log_truncated=False,log_bytes=log.stat().st_size)
            item=dict(stage='preview',argv=argv,log=str(log),log_sha256=report.digest(log),
                journal=str(journal),journal_sha256=write(journal,process),process=process)
            data=dict(status='failed',outcome='unqualified_failure',attempt_qualified=False,controls_passed=False,
                workflow_delivered=False,workspace=str(workspace),processes=[item])
            observation=report.unsupported_improve_preview(plan,data,out)
            self.assertTrue(observation['observed_unsupported'])
            self.assertFalse(observation['Native_completion_qualified'])
            self.assertFalse(data['attempt_qualified']);self.assertFalse(data['workflow_delivered'])
            for mutation in ('cancel','route','wrong-source','different-error'):
                original=copy.deepcopy(item)
                if mutation=='cancel':
                    item['process']['cancel_requested']=True
                elif mutation=='route':(workspace/'route').mkdir()
                elif mutation=='wrong-source':
                    item['process']['argv'][5]='/owned/different.kicad_pcb';item['argv']=item['process']['argv']
                else:
                    write(log,dict(accepted=False,error='other failure'))
                    item['log_sha256']=report.digest(log);item['process']['log_bytes']=log.stat().st_size
                item['journal_sha256']=write(journal,item['process'])
                if mutation=='different-error':self.assertIsNone(report.unsupported_improve_preview(plan,data,out))
                else:
                    with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                        report.unsupported_improve_preview(plan,data,out)
                if mutation=='route':(workspace/'route').rmdir()
                item.clear();item.update(original)
                item['journal_sha256']=write(journal,item['process'])


if __name__=='__main__':unittest.main()
