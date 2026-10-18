"""Focused bookkeeping/late-publication controls; no Native routing claim."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from scripts import qualify_installed_workflow as driver, experiment_paired as paired
from autorouter import pipeline as p, review_export as ex


class InstalledDeliveryControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.route = self.root/'result.json'; self.route.write_bytes(b'{}')
        self.export = self.root/'export.json'; self.export.write_bytes(b'{}')
        self.report = dict(arm='B1', selected_route_receipt=str(self.route), selected_route_sha256=p.sha(self.route),
                           export_receipt=str(self.export), export_sha256=p.sha(self.export))
        self.board = self.root/'board.kicad_pcb'
        self.context = SimpleNamespace(freeze=lambda: {'installed_context': {}, 'tools': {}, 'source_hashes': {}})
        for item in (patch.object(p,'check_result',return_value={'current':True}),
                     patch.object(ex,'check_export',return_value={'current':True})):
            item.start(); self.addCleanup(item.stop)

    def test_export_or_selected_receipt_reformatting_cannot_leave_stale_recorded_hash(self):
        driver.verify_delivery(self.report,self.board,self.context)
        for path in (self.route,self.export):
            with self.subTest(path=path):
                path.write_bytes(b'{}\n')
                with self.assertRaisesRegex(p.Rejected,'receipt hash changed'):
                    driver.verify_delivery(self.report,self.board,self.context)
                path.write_bytes(b'{}')

    def test_receipt_change_inside_final_native_reader_is_also_refused(self):
        def changed(_):self.export.write_bytes(b'{}\n');return {'current':True}
        with patch.object(ex,'check_export',side_effect=changed):
            with self.assertRaisesRegex(p.Rejected,'receipt hash changed'):
                driver.verify_delivery(self.report,self.board,self.context)

    def test_entire_portfolio_not_only_selected_receipt_is_checked_at_final_delivery(self):
        directory=self.root/'portfolio';directory.mkdir()
        summary=directory/'portfolio-summary.json';summary.write_bytes(b'{}')
        self.report.update(arm='B2_portfolio',portfolio_directory=str(directory),portfolio={},portfolio_summary_sha256=p.sha(summary))
        with patch.object(paired,'verify_portfolio',side_effect=p.Rejected('losing negative changed'))as checked:
            with self.assertRaisesRegex(p.Rejected,'losing negative changed'):
                driver.verify_delivery(self.report,self.board,self.context)
        checked.assert_called_once_with(directory,{},self.board,self.context.freeze())
        summary.write_bytes(b'{}\n')
        with self.assertRaisesRegex(p.Rejected,'summary hash changed'):
            driver.verify_delivery(self.report,self.board,self.context)

    def test_corrupt_partial_json_retains_hash_and_error_without_throwing(self):
        self.route.write_bytes(b'{broken')
        result=driver.read_attempt(self.route)
        self.assertEqual(result['sha256'],hashlib.sha256(b'{broken').hexdigest())
        self.assertIn('read_error',result);self.assertNotIn('accepted',result)
        self.route.write_text(json.dumps({'accepted':False,'status':'drc_rejected','source_drc':{'opens':2}}))
        result=driver.read_attempt(self.route)
        self.assertIs(result['accepted'],False);self.assertEqual(result['source_drc'],{'opens':2})

    def test_protocol_keeps_complete_old_and_thermal_populations_separate(self):
        for kind, arms in (('installed-workflow-exposed-comparison-v1', driver.ORIGINAL_ARMS),
                           ('installed-workflow-thermal-comparison-v2', driver.THERMAL_ARMS),
                           (driver.RESERVED_KIND, driver.THERMAL_ARMS)):
            plan = dict(kind=kind, arms=list(arms))
            self.assertEqual(driver.protocol_arms(plan), arms)
            for bad in (list(arms[:-1]), list(reversed(arms)), [*arms, arms[-1]], None):
                with self.subTest(kind=kind, bad=bad), self.assertRaises(p.Rejected):
                    driver.protocol_arms(dict(plan, arms=bad))
        for bad in ({}, [], {'kind': True}, {'kind': 'unqualified', 'arms': list(driver.THERMAL_ARMS)}):
            with self.subTest(bad=bad), self.assertRaises(p.Rejected): driver.protocol_arms(bad)


class InstalledFixedPresetControls(unittest.TestCase):
    def plan(self, kind=driver.DELIVERY_KIND):
        old = kind not in (driver.RESERVED_KIND, driver.DELIVERY_KIND)
        arms = driver.ORIGINAL_ARMS if kind.endswith('-v1') else driver.THERMAL_ARMS
        result = dict(schema=1, kind=kind, arms=list(arms),
            routing_seconds=105 if old else 420,
            method_wall_cpu_cap_seconds=120 if old else 450,
            delivery_wall_cpu_cap_seconds=240 if old else 600,
            allocation='remaining' if old else 'balanced')
        if not old:
            result['installed_trial_accounting_policy'] = driver.RESERVED_POLICY
        if kind == driver.DELIVERY_KIND:
            result['export_validation_seconds'] = 120
        return result

    def test_current_commands_keep_routing_and_native_export_allocations_distinct(self):
        from scripts import experiment_portfolio as portfolio
        preset = driver.protocol_preset(self.plan())
        for command in ('recover', 'review-export'):
            with self.subTest(command=command):
                arguments = preset.timed_cli_arguments(command, '/owned/input', '/owned/output')
                expected = 420 if command == 'recover' else 120
                self.assertEqual(arguments, [command, '/owned/input', '--seconds', str(expected), '--output', '/owned/output'])
                if command == 'review-export':
                    self.assertEqual(ex.validate_seconds(float(arguments[arguments.index('--seconds') + 1])), preset.export_validation_seconds)
        self.assertEqual(preset.portfolio_options(), dict(budget=420, outer_ceiling=450,
            allocation='balanced', installed_trial_policy=portfolio.INSTALLED_TRIAL_RESERVE_POLICY))
        for arm in driver.THERMAL_ARMS:
            with self.subTest(arm=arm):
                settings = driver.routing_settings(arm, preset)
                self.assertEqual(settings['seconds'], 420)
                self.assertEqual(settings['scope'], 'whole_board_unlocked_routing')
                self.assertEqual(settings['layers'], 'source_all')
        self.assertEqual(driver.routing_settings('B1', preset)['profile'], 'standard')
        self.assertEqual(driver.routing_settings('B2_completion', preset)['profile'], 'completion-only')
        self.assertEqual(driver.routing_settings('C_thermal', preset)['profile'], 'completion-only')
        self.assertEqual(driver.routing_settings('C_single', preset)['profile'], 'tuned')

    def test_historical_v3_keeps_failed_manual_export_spelling_visible(self):
        # Real v3 reached accepted Native routing but tried unsupported420s export.
        # Preserve its frozen caller; v4 and the product helper fix new jobs only.
        preset = driver.protocol_preset(self.plan(driver.RESERVED_KIND))
        arguments = preset.timed_cli_arguments('review-export', 'choice', 'output')
        self.assertEqual(arguments[arguments.index('--seconds') + 1], '420')
        with self.assertRaises(p.Rejected): ex.validate_seconds(420)
        current = self.plan(); current.pop('export_validation_seconds')
        with self.assertRaises(p.Rejected): driver.protocol_preset(current)

    def test_delivery_reserve_counts_wall_and_cpu_and_allows_long_routing_cli(self):
        preset = driver.protocol_preset(self.plan())
        self.assertGreaterEqual(preset.cli_timeout_seconds, preset.routing_seconds)
        self.assertLessEqual(preset.cli_timeout_seconds, preset.method_wall_cpu_cap_seconds)
        self.assertEqual(preset.remaining(0, 0), 585)
        self.assertEqual(preset.remaining(560, 580), 5)
        self.assertEqual(preset.remaining(586, 0), -1)
        self.assertEqual(preset.remaining(0, 586), -1)
        self.assertEqual(min(preset.cli_timeout_seconds, preset.remaining(550, 540)), 35)

    def test_old_presets_keep_commands_deadlines_profiles_and_remaining_allocation(self):
        presets = [driver.protocol_preset(self.plan(kind)) for kind in (
            'installed-workflow-exposed-comparison-v1', 'installed-workflow-thermal-comparison-v2')]
        self.assertEqual(presets[0], presets[1])
        for preset in presets:
            self.assertEqual(preset.portfolio_options(), dict(budget=105, outer_ceiling=120, allocation='remaining'))
            self.assertEqual(preset.timed_cli_arguments('recover', 'board', 'output'),
                ['recover', 'board', '--seconds', '105', '--output', 'output'])
            self.assertEqual(preset.timed_cli_arguments('review-export', 'choice', 'output'),
                ['review-export', 'choice', '--seconds', '105', '--output', 'output'])
            self.assertEqual(preset.remaining(0, 0), 225)
            self.assertEqual(preset.cli_timeout_seconds, 165)
            self.assertEqual(driver.routing_settings('B1', preset)['seconds'], 105)

    def test_real_workflow_carries_each_fixed_settings_budget_into_export(self):
        from autorouter import gui
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / 'source'; source.mkdir()
            output = root / 'output'; output.mkdir()
            board = source / 'owned.kicad_pcb'
            original = b'owned synthetic source\n'
            for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch'):
                board.with_suffix(suffix).write_bytes(original)
            for kind in ('installed-workflow-exposed-comparison-v1',
                         'installed-workflow-thermal-comparison-v2', driver.RESERVED_KIND, driver.DELIVERY_KIND):
                preset = driver.protocol_preset(self.plan(kind))
                expected_seconds = preset.routing_seconds
                for arm, method in (('B1', 'route'), ('C_single', 'improve')):
                    with self.subTest(kind=kind, arm=arm):
                        settings = driver.routing_settings(arm, preset)
                        flow = gui.Request(str(board), str(output), json.dumps(settings),
                                           saved_closed=True, method=method).prepare()
                        captured = json.loads((flow.workspace / 'settings.json').read_bytes())
                        self.assertEqual(captured, settings)
                        self.assertEqual(json.loads(flow.settings_bytes), captured)
                        self.assertEqual(captured['seconds'], expected_seconds)
                        # Synthetic state exercises emitted commands, not successful routing/review.
                        flow.ready.add('preview')
                        route = flow.command('route')
                        self.assertEqual(route[4:6], [method, str(board)])
                        self.assertEqual(route[route.index('--settings') + 1],
                                         str(flow.workspace / 'settings.json'))
                        flow.ready.update(('route', 'review', 'choice'))
                        flow.choice = 'accept'
                        export = flow.command('export')
                        self.assertEqual(export[4:6], ['review-export',
                                         str(flow.workspace / 'choice/choice.json')])
                        self.assertEqual(export[export.index('--seconds') + 1],
                                         str(gui.export_validation_seconds(captured['seconds'])))
                        self.assertEqual(ex.validate_seconds(float(export[export.index('--seconds') + 1])), gui.export_validation_seconds(captured['seconds']))
                        self.assertEqual(export[export.index('--output') + 1],
                                         str(flow.workspace / 'export'))
            for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch'):
                self.assertEqual(board.with_suffix(suffix).read_bytes(), original)

    def test_budget_policy_or_arm_hybrids_are_refused_before_execution(self):
        for kind in ('installed-workflow-exposed-comparison-v1',
                     'installed-workflow-thermal-comparison-v2', driver.RESERVED_KIND, driver.DELIVERY_KIND):
            plan = self.plan(kind)
            changes = ({'routing_seconds': plan['routing_seconds'] + 1},
                {'method_wall_cpu_cap_seconds': plan['method_wall_cpu_cap_seconds'] + 1},
                {'delivery_wall_cpu_cap_seconds': plan['delivery_wall_cpu_cap_seconds'] + 1},
                {'routing_seconds': str(plan['routing_seconds'])}, {'schema': True},
                {'allocation': 'remaining' if kind in (driver.RESERVED_KIND, driver.DELIVERY_KIND) else 'balanced'},
                {'installed_trial_accounting_policy': None if kind in (driver.RESERVED_KIND, driver.DELIVERY_KIND) else driver.RESERVED_POLICY},
                {'installed_trial_accounting_policy': 'unknown'}, {'arms': plan['arms'][:-1]},
                {'export_validation_seconds': None if kind == driver.DELIVERY_KIND else 120},
                {'export_validation_seconds': 121})
            for change in changes:
                with self.subTest(kind=kind, change=change), self.assertRaises(p.Rejected):
                    driver.protocol_preset(dict(plan, **change))
        plan = self.plan(); plan.pop('installed_trial_accounting_policy')
        with self.assertRaises(p.Rejected): driver.protocol_preset(plan)
        plan = self.plan(); plan['kind'] = 'unqualified-custom'
        with self.assertRaises(p.Rejected): driver.protocol_preset(plan)
        preset = driver.protocol_preset(self.plan())
        with self.assertRaises(ValueError): driver.routing_settings('unknown', preset)
        with self.assertRaises(ValueError): preset.timed_cli_arguments('unqualified', 'board', 'output')


class InstalledPairedNegativeReader(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.board=self.root/'board.kicad_pcb'
        self.directory=self.root/'portfolio';self.directory.mkdir()
        self.frozen={'installed_context':{'runtime':str(self.root)},'tools':{},'source_hashes':{}}
        positive=dict(index=0,id='via_default',eligible=True,accepted_in_trial_receipt=True,vias=1,length_mm=20,
            result=str(self.directory/'01-via_default/result.json'),result_sha256='a'*64,candidate='positive',
            candidate_sha256='b'*64,native_report_sha256='c'*64)
        negative=dict(index=1,id='via_low',eligible=False,accepted_in_trial_receipt=False,validated_rejection=True,
            result=str(self.directory/'02-via_low/result.json'),vias=1,length_mm=10)
        for row in (positive,negative):
            path=Path(row['result']);path.parent.mkdir();path.write_text(json.dumps({'status':'routing_accepted'if row['eligible']else'drc_rejected'}))
        protocol=dict(freeze=self.frozen,variants=list(paired.portfolio.VARIANTS))
        paired.p.save_json(self.directory/'protocol.json',protocol)
        self.summary=dict(status='completed',comparison_eligible=True,protocol_sha256=p.sha(self.directory/'protocol.json'),
            trials=[positive,negative],pareto_frontier=['via_default'],selected={key:positive[key]for key in
            ('id','result','result_sha256','candidate','candidate_sha256','native_report_sha256','vias','length_mm')},
            wall_seconds=50,total_cpu_seconds=50)
        self.save()
        for item in (patch.object(paired.portfolio,'verify_row'),patch.object(paired.portfolio,'verify_negative_row')):
            item.start();self.addCleanup(item.stop)

    def save(self):paired.p.save_json(self.directory/'portfolio-summary.json',self.summary)
    def check(self):return paired.verify_portfolio(self.directory,self.summary,self.board,self.frozen)

    def test_completed_installed_portfolio_rechecks_loser_and_propagates_refusal(self):
        self.assertTrue(self.check()['accepted'])
        paired.portfolio.verify_negative_row.assert_called_once_with(self.summary['trials'][1],self.board,self.frozen)
        with patch.object(paired.portfolio,'verify_negative_row',side_effect=p.Rejected('raw failed candidate changed')):
            with self.assertRaisesRegex(p.Rejected,'raw failed candidate changed'):self.check()

    def test_missing_negative_flag_or_eligibility_relabel_cannot_skip_loser_checks(self):
        original=copy.deepcopy(self.summary)
        for change in ({'validated_rejection':False},{'eligible':True}):
            with self.subTest(change=change):
                self.summary=copy.deepcopy(original);self.summary['trials'][1].update(change);self.save()
                with self.assertRaises(p.Rejected):self.check()

    def test_complete_installed_freeze_mismatch_cannot_be_hidden_by_same_tools(self):
        path=self.directory/'protocol.json';value=json.loads(path.read_text());value['freeze']['installed_context']['runtime']='changed'
        paired.p.save_json(path,value);self.summary['protocol_sha256']=p.sha(path);self.save()
        with self.assertRaisesRegex(p.Rejected,'complete frozen context'):self.check()


if __name__=='__main__':unittest.main()
