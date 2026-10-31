"""Disjoint completed CLI cost/reporting controls, no subprocess or Native."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock
import unittest
from scripts import qualify_current_method as method, report_current_comparison as report
from scripts import freeze_current_comparison as frozen


def fields():return dict(handoff_stage_policy='bounded-review60-choice30-v2',delivery_stage_seconds=dict(review=60,choice=30))
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return hashlib.sha256(path.read_bytes()).hexdigest()


class ActualMethodCliTimingSeam(unittest.TestCase):
    def test_actual_cli_body_separates_joined_call_from_adoption_and_freshness(self):
        for kind in (method.REVIEW60_KIND,method.CURRENT40_KIND):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as folder:
                out=Path(folder).resolve();events=[];record=dict(processes=[])
                process=dict(argv=['owned','inert-command'],exit_code=0,cancel_requested=False,log_truncated=False,
                    log_bytes=2,wall_seconds=24.)
                class Job:
                    def run(self,argv,log,timeout):
                        events.append('run');log.write_text('{}');write(log.with_suffix('.process.json'),process);return process
                    def adopt(self,*args,**kwargs):events.append('adopt')
                root=ast.parse(Path(method.__file__).read_text());main=next(n for n in root.body if isinstance(n,ast.FunctionDef) and n.name=='main')
                node=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='cli')
                wall=Mock(side_effect=[10.,35.,40.]);cpu=Mock(side_effect=[20.,40.,45.])
                def require(value,message):
                    if not value:raise ValueError(message)
                def fresh():events.append('fresh')
                scope=dict(plan=dict(kind=kind),REVIEW60_KIND=method.REVIEW60_KIND,record=record,
                    fresh=fresh,left=lambda:600.,method_left=lambda:450.,gui=SimpleNamespace(CliJob=Job),out=out,
                    pv=frozen.pv,f=frozen.f,p=SimpleNamespace(Rejected=ValueError,sha=report.digest),require=require,
                    time=SimpleNamespace(monotonic=wall),cpu=cpu,cli_cost_sample=method.cli_cost_sample)
                exec(compile(ast.Module(body=[node],type_ignores=[]),str(method.__file__)+'::cli-only','exec'),scope)
                workflow=SimpleNamespace(timeout=lambda stage:90.)
                self.assertIs(scope['cli']('review',process['argv'],workflow=workflow),process)
                self.assertEqual(events,['fresh','run','adopt','fresh'])
                item=record['processes'][0]
                if kind==method.REVIEW60_KIND:
                    self.assertEqual(item['completed_cli_exit']['wall_seconds'],25.)
                    self.assertEqual(item['completed_cli_exit']['full_CPU_seconds'],20.)
                    self.assertEqual(item['post_cli_adoption_and_freshness']['wall_seconds'],5.)
                    self.assertEqual(item['post_cli_adoption_and_freshness']['full_CPU_seconds'],5.)
                else:
                    self.assertNotIn('completed_cli_exit',item);self.assertNotIn('post_cli_adoption_and_freshness',item)
                    wall.assert_not_called();cpu.assert_not_called()

    def test_cost_sample_refuses_boolean_nonfinite_or_decreasing_clocks(self):
        for values in ((True,0.,1.,1.),(0.,0.,float('nan'),1.),(0.,0.,1.,float('inf')),(2.,0.,1.,1.),(0.,2.,1.,1.)):
            with self.subTest(values=values),self.assertRaises(ValueError):
                method.cli_cost_sample(*values,scope='completed_cli_exit',joined=True)
        sample=method.cli_cost_sample(0.,0.,1.,1.,scope='completed_cli_exit',joined=False)
        self.assertIs(sample['joined'],False)  # Failure diagnostic only; reader cannot qualify it.


class CompletedCliReportingControls(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name).resolve()
        self.out=self.root/'native7-method-owned';self.out.mkdir();self.workspace=self.out/('autorouter-gui-'+'a'*32);self.workspace.mkdir()
        self.plan=dict(fields(),kind=method.REVIEW60_KIND,arm='Cimprove',output=str(self.out),runtime=str(self.root/'runtime'),source=str(self.root/'source/owned.kicad_pcb'))
        self.data=dict(fields(),kind=method.REVIEW60_KIND,workspace=str(self.workspace),processes=[],
            status='completed',controls_passed=True,attempt_qualified=True,workflow_delivered=True,outcome='validated_delivery')
        prefix=[str(self.root/'runtime/.venv/bin/python'),'-B','-m','autorouter'];settings=str(self.workspace/'settings.json')
        route=self.workspace/'route/result.json';review=self.workspace/'review/review.json';choice=self.workspace/'choice/choice.json';export=self.workspace/'export/export.json'
        self.paths=dict(route=route,review=review,choice=choice,export=export)
        self.bound_records=dict(
            route=dict(status='routing_accepted',accepted=True,candidate=str(route.parent/'candidate/owned.kicad_pcb'),
                candidate_sha256='a'*64,metrics={},wall_seconds=1.,total_cpu_seconds=1.),
            review=dict(handoff_stage_policy='bounded-review60-choice30-v2',status='ready_for_manual_review',
                budget_seconds=60,cpu_budget_seconds=60,within_budget=True,wall_seconds=35.,total_cpu_seconds=34.),
            choice=dict(handoff_stage_policy='bounded-review60-choice30-v2',status='disposition_recorded',choice='accept',choice_recorded=True,
                budget_seconds=30,cpu_budget_seconds=30,within_budget=True,wall_seconds=1.,total_cpu_seconds=1.),
            export=dict(status='export_validated',export_accepted=True,project_file=str(export.parent/'candidate/owned.kicad_pro'),
                candidate_sha256='a'*64,native_report_sha256='b'*64,wall_seconds=1.,total_cpu_seconds=1.))
        commands={
            'preview':['preview',self.plan['source'],'--settings',settings,'--purpose','improve'],
            'route':['improve',self.plan['source'],'--settings',settings,'--output',str(route.parent)],
            'review':['review-copy',str(route),'--render','--output',str(review.parent)],
            'choice':['review-choice',str(review),'--choice','accept','--output',str(choice.parent)],
            'export':['review-export',str(choice),'--seconds','120','--output',str(export.parent)],
            'verify_export':['review-export-check',str(export)]}
        for stage,arguments in commands.items():
            log=self.out/(stage+'.log');journal=self.out/(stage+'.process.json')
            process=dict(argv=prefix+arguments,exit_code=0,cancel_requested=False,log_truncated=False,log_bytes=0,wall_seconds=1.)
            row=dict(stage=stage,argv=process['argv'],journal=str(journal),log=str(log),process=process)
            for scope in ('completed_cli_exit','post_cli_adoption_and_freshness'):
                row[scope]=method.cli_cost_sample(0.,0.,2.,2.,scope=scope,joined=True)
            self.data['processes'].append(row)
        self.refresh_bound_records()
        self.review=self.data['processes'][2]['completed_cli_exit'];self.review.update(wall_seconds=40.,full_CPU_seconds=39.)
        self.timing=dict(wall_seconds=200.,CPU_seconds=190.)

    def refresh_bound_records(self):
        # These inert owned files exercise real current hashes/custody. They
        # carry no Native or design-validation authority.
        route,review,choice,export=(self.paths[name] for name in ('route','review','choice','export'))
        route_pin=write(route,self.bound_records['route'])
        self.bound_records['review'].update(receipt=str(route),receipt_sha256=route_pin)
        review_pin=write(review,self.bound_records['review'])
        self.bound_records['choice'].update(receipt=str(route),receipt_sha256=route_pin,review=str(review),review_sha256=review_pin)
        choice_pin=write(choice,self.bound_records['choice'])
        self.bound_records['export']['inputs']=dict(receipt=str(route),receipt_sha256=route_pin,
            review=str(review),review_sha256=review_pin,choice=str(choice),choice_sha256=choice_pin)
        write(export,self.bound_records['export'])
        self.data.update(selected_route_receipt=str(route),export_receipt=str(export))
        for row in self.data['processes']:
            stage=row['stage'];record=self.bound_records.get(stage,{})
            if stage=='route':
                logged={key:value for key,value in record.items() if key in {'status','accepted','reason','candidate','wall_seconds','total_cpu_seconds','metrics'}}
            elif stage=='export':
                logged={key:value for key,value in record.items() if key in {'status','export_accepted','project_file','candidate_sha256','native_report_sha256','wall_seconds','total_cpu_seconds'}}
            else:logged=record
            log=Path(row['log']);row['log_sha256']=write(log,logged);row['process']['log_bytes']=log.stat().st_size
            row['journal_sha256']=write(Path(row['journal']),row['process'])

    def facts(self):return report.completed_cli_facts(self.plan,self.data,self.timing)

    def test_complete_cli_headroom_needs_actual_both_clocks_and_separate_adoption(self):
        result=self.facts();self.assertTrue(result['complete_review_cli_headroom_qualified'])
        self.assertEqual(result['complete_review_cli']['wall_seconds'],40.)
        self.assertEqual(result['stages']['review']['post_cli_adoption_and_freshness']['wall_seconds'],2.)
        self.assertEqual(result['review_stage_headroom_seconds'],dict(wall=20.,CPU=21.))
        for field in ('wall_seconds','full_CPU_seconds'):
            previous=self.review[field];self.review[field]=45.001
            self.assertFalse(self.facts()['complete_review_cli_headroom_qualified']);self.review[field]=previous

    def test_completed_cli_cannot_underreport_bound_review55_samples(self):
        # RED was observed before the reader fix: exact bound55/55 coexisted
        # with measured2/2 and incorrectly qualified positive headroom.
        self.review.update(wall_seconds=2.,full_CPU_seconds=2.)
        self.bound_records['review'].update(wall_seconds=55.,total_cpu_seconds=55.)
        self.refresh_bound_records()  # Rebind every current receipt/log hash.
        with self.assertRaisesRegex(ValueError,'omits bound review'):
            self.facts()

    def test_each_known_receipt_sample_is_a_lower_bound_for_its_complete_cli(self):
        for stage in ('route','review','choice','export'):
            for receipt_key,cost_key in (('wall_seconds','wall_seconds'),('total_cpu_seconds','full_CPU_seconds')):
                with self.subTest(stage=stage,field=receipt_key):
                    sample=next(row for row in self.data['processes'] if row['stage']==stage)['completed_cli_exit']
                    previous=sample[cost_key];sample[cost_key]=.5
                    with self.assertRaisesRegex(ValueError,'omits (?:joined|bound '+stage+')'):self.facts()
                    sample[cost_key]=previous

    def test_rebound_current_receipt_must_still_match_actual_cli_stdout(self):
        self.bound_records['review']['wall_seconds']+=1.
        # Refresh review->choice->export custody while retaining the original
        # independently pinned CLI stdout, process and byte counts.
        review_pin=write(self.paths['review'],self.bound_records['review'])
        self.bound_records['choice']['review_sha256']=review_pin
        choice_pin=write(self.paths['choice'],self.bound_records['choice'])
        self.bound_records['export']['inputs'].update(review_sha256=review_pin,choice_sha256=choice_pin)
        write(self.paths['export'],self.bound_records['export'])
        with self.assertRaisesRegex(ValueError,'log differs from bound review'):self.facts()

    def test_changed_current_receipt_cannot_hide_behind_old_bound_hashes(self):
        write(self.paths['review'],dict(self.bound_records['review'],wall_seconds=55.,total_cpu_seconds=55.))
        with self.assertRaisesRegex(ValueError,'stage receipt binding differs'):self.facts()

    def test_missing_nonfinite_boolean_or_unjoined_measurement_cannot_qualify(self):
        for change in (dict(joined=False),dict(joined=1),dict(wall_seconds=True),dict(full_CPU_seconds=float('nan')),
                dict(wall_seconds=-1.),dict(scope='prepublication_receipt'),dict(schema=True)):
            before=copy.deepcopy(self.review);self.review.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):self.facts()
            self.review.clear();self.review.update(before)
        last=self.data['processes'].pop()
        with self.assertRaisesRegex(ValueError,'six ordered'):self.facts()
        self.data['processes'].append(last)

    def test_cost_cannot_omit_process_time_or_exceed_actual_complete_external_exit(self):
        self.review['wall_seconds']=.5
        with self.assertRaisesRegex(ValueError,'omits joined'):self.facts()
        self.review['wall_seconds']=40.;self.timing['CPU_seconds']=1.
        with self.assertRaisesRegex(ValueError,'exceed complete external'):self.facts()

    def test_forged_journal_or_relabelled_command_cannot_supply_review_headroom(self):
        row=self.data['processes'][2];row['process']['argv'][4]='preview'
        row['journal_sha256']=write(Path(row['journal']),row['process'])
        with self.assertRaisesRegex(ValueError,'actual joined successful command'):self.facts()

    def test_late_workflow_failure_cannot_keep_a_positive_headroom_claim(self):
        for change in (dict(status='failed'),dict(controls_passed=False),dict(attempt_qualified=False),dict(workflow_delivered=False),dict(outcome='unqualified_failure')):
            before=copy.deepcopy(self.data);self.data.update(change)
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'complete delivered method'):self.facts()
            self.data=before

    def test_api_baselines_are_explicitly_unmeasured_not_receipt_cpu(self):
        self.plan['arm']='B1';self.data['processes']=[]
        result=self.facts();self.assertFalse(result['complete_review_cli_headroom_qualified'])
        self.assertIn('not a substitute',result['scope'])
