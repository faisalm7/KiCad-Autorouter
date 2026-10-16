"""Portable cohort caller controls; no Native/JVM or private raw evidence.

These software seams qualify caller behavior, not PCB routing correctness.
"""
import ast
from contextlib import ExitStack, contextmanager
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from experiments.stronger_incumbent_v1.cohort import driver as cohort
from tests import test_field_local_settings_event as field_event_helpers


class StrongerCohortControls(unittest.TestCase):
    def test_actual_command_last_statement_preserves_cancellation(self):
        # Execute the real wrapper's final statement without running its imports,
        # argument parser, process runner or Native-producing command.
        command = Path(cohort.__file__).with_name('command.py')
        statement = ast.parse(command.read_text()).body[-1]
        self.assertIsInstance(statement, ast.Raise)
        code = compile(ast.Module(body=[statement], type_ignores=[]), str(command), 'exec')
        cases = [
            (True, 'success', 0, True, 0),
            (False, 'nonzero_exit', 2, True, 2),
            (False, 'nonzero_exit', 130, True, 130),
            (False, 'cancelled', None, True, 130),
            (False, 'nonzero_exit', 130, False, 2),
        ]
        for passed, status, exit_code, cleanup, expected in cases:
            with self.subTest(status=status, exit_code=exit_code, cleanup=cleanup):
                namespace = dict(passed=passed, process=dict(status=status,
                    exit_code=exit_code, cleanup_complete=cleanup))
                with self.assertRaises(SystemExit) as raised:
                    exec(code, namespace)
                self.assertEqual(raised.exception.code, expected)

    def publication_exit(self, function, record):
        tree = ast.parse(Path(cohort.__file__).read_text())
        body = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == function)
        # Nested callbacks return remaining budgets, not the final record exit.
        exits = [node for node in ast.walk(body) if isinstance(node, ast.Return)
                 and isinstance(node.value, ast.IfExp)
                 and any(isinstance(child, ast.Name) and child.id == 'record'
                         for child in ast.walk(node.value))]
        self.assertEqual(len(exits), 1)
        expression = ast.Expression(body=copy.deepcopy(exits[0].value))
        return eval(compile(expression, str(Path(cohort.__file__)), 'eval'),
                    dict(record=record))

    def assert_publication_exits(self, function):
        for record, expected in [
            (dict(passed=True, status='completed'), 0),
            (dict(passed=False, status='completed'), 2),
            (dict(passed=False, status='cancelled'), 130),
            (dict(passed=False, status='invalidated'), 2),
            (dict(passed=False, status='failed'), 2),
        ]:
            with self.subTest(function=function, record=record):
                self.assertEqual(self.publication_exit(function, record), expected)

    def test_actual_read_publication_exit_preserves_cancellation(self):
        self.assert_publication_exits('read')

    def test_actual_report_publication_exit_preserves_cancellation(self):
        self.assert_publication_exits('report')

    def original_nus_fixture(self, changed=False):
        """Run original_gate itself; replace only fixed external prerequisites.

        No retained/private path is opened. A mismatch must stop before the
        otherwise-valid new-fields reader can mask a stale old DRC reference.
        """
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name).resolve()
        paths = {name: root / name for name in
                 ('public.json', 'gate.py', 'protocol.json', 'producer.json',
                  'reader.json', 'old/result.json')}
        source = root / 'usb_led.kicad_pcb'
        source_hashes = {'usb_led.kicad_pcb': 'original-pcb'}
        native = dict(opens=0, blocking=0, warnings=10, exclusions=0,
                      findings=[], ignored_checks=[])
        old_reference = dict(raw_native=native, material={'old-log': 'original'})
        tools = {'fixed_native_tools': 'software-seam'}
        qualification = dict(qualified=True, component_count=6, compared_field_count=19)
        plan = dict(git_head=cohort.GATE_HEAD, case='nus-usb-led', source=str(source),
                    freeze=dict(source_hashes=source_hashes), tools=tools,
                    code_sha256={}, old_drc_reference=old_reference)
        record = dict(git_head=cohort.GATE_HEAD, protocol_sha256='protocol-pin',
                      passed=True, status='completed', gate_passed=True,
                      accepted=False, completed_evidence={'fixed': 'material'},
                      supplement=dict(qualification=qualification))
        reader = dict(passed=True, status='completed', gate_passed=True,
                      git_head=cohort.GATE_HEAD, protocol_sha256='protocol-pin',
                      producer_receipt_sha256='producer-pin',
                      producer_literal=cohort.f.canonical(record),
                      producer_material={'fixed': 'material'},
                      completed_evidence={'fixed': 'material'})
        entry = dict(producer_git_head=cohort.GATE_HEAD, gate_passed=True,
                     protocol='protocol.json', producer_receipt='producer.json',
                     pure_receipt='reader.json', protocol_sha256='protocol-pin',
                     producer_receipt_sha256='producer-pin',
                     pure_receipt_sha256='reader-pin', source=str(source),
                     source_sha256=source_hashes, code_sha256={},
                     native_counts={key: native[key] for key in
                                    ('opens', 'blocking', 'warnings', 'exclusions')})
        public = dict(kind='qualified-missing-original-source-gates',
                      whole_external_cost_qualified=True,
                      producer_git_head=cohort.GATE_HEAD,
                      files_sha256={}, cases={'nus-usb-led': entry})
        old_aggregate = dict(status='failed', accepted=False)
        documents = {paths['public.json']: public, paths['protocol.json']: plan,
                     paths['producer.json']: record, paths['reader.json']: reader,
                     paths['old/result.json']: old_aggregate}
        digests = dict(zip(paths.values(),
                           ('public-pin', 'gate-pin', 'protocol-pin', 'producer-pin',
                            'reader-pin', 'old-pin')))
        observed_old = copy.deepcopy(old_reference)
        if changed:
            observed_old['material']['old-log'] = 'changed'
        gate = SimpleNamespace(old_nus=Mock(return_value=observed_old),
                               check_worker=Mock(), prl_last=Mock())
        spec = SimpleNamespace(loader=SimpleNamespace(exec_module=Mock()))
        case = dict(source=str(source), source_sha256=source_hashes,
                    original_aggregate=dict(path='old/result.json', sha256='old-pin'))
        stack = self.enterContext(ExitStack())
        for target, name, value in [
            (cohort, 'ROOT', root), (cohort, 'CASES', {'nus-usb-led': case}),
            (cohort, 'GATE_PUBLIC', paths['public.json']),
            (cohort, 'GATE_MODULE', paths['gate.py']),
            (cohort, 'GATE_MODULE_SHA', 'gate-pin'),
        ]:
            stack.enter_context(patch.object(target, name, value))
        stack.enter_context(patch.object(cohort.p, 'sha', side_effect=lambda path: digests[Path(path)]))
        stack.enter_context(patch.object(cohort.f, 'read_json',
            side_effect=lambda path: copy.deepcopy(documents[Path(path)])))
        stack.enter_context(patch.object(cohort.p, 'tool_manifest', return_value=tools))
        stack.enter_context(patch.object(cohort, 'same_transport'))
        stack.enter_context(patch.object(cohort.p, 'native_accepted', return_value=True))
        stack.enter_context(patch.object(cohort.shared, 'material', return_value={'fixed': 'material'}))
        stack.enter_context(patch.object(cohort.importlib.util, 'spec_from_file_location', return_value=spec))
        stack.enter_context(patch.object(cohort.importlib.util, 'module_from_spec', return_value=gate))
        return gate, tools, old_aggregate

    def test_actual_original_gate_refuses_old_nus_reference_mismatch(self):
        gate, tools, _ = self.original_nus_fixture(changed=True)
        with self.assertRaisesRegex(cohort.p.Rejected, 'original NUS raw DRC/process/input/material'):
            cohort.original_gate('nus-usb-led', 'public-pin')
        gate.old_nus.assert_called_once_with(tools)
        gate.check_worker.assert_not_called()
        gate.prl_last.assert_not_called()

    def test_actual_original_gate_keeps_old_nus_aggregate_failed(self):
        gate, tools, old = self.original_nus_fixture()
        native, binding = cohort.original_gate('nus-usb-led', 'public-pin')
        gate.old_nus.assert_called_once_with(tools)
        gate.check_worker.assert_called_once()
        gate.prl_last.assert_called_once()
        self.assertEqual(old, dict(status='failed', accepted=False))
        self.assertEqual(native['warnings'], 10)
        self.assertEqual(native['field_parity']['qualification']['compared_field_count'], 19)
        self.assertIn('old/result.json', binding['files_sha256'])
        self.assertIn('old', binding['materials'])

    @contextmanager
    def original_findings_fixture(self, findings):
        # The actual legacy-original branch, with only external provenance and
        # Native execution seams substituted. No historical artifact is needed.
        expected = [dict(type='lib_footprint_issues', severity='warning',
                         description='owned missing library', items=[
                             dict(uuid='owned-footprint', pos=dict(x=30, y=10))])]
        native = dict(opens=0, blocking=0, warnings=len(findings), exclusions=0,
                      findings=copy.deepcopy(findings), ignored_checks=[])
        with tempfile.TemporaryDirectory() as name, ExitStack() as stack:
            root = Path(name).resolve()
            stage = dict(directory='job', stage='original-final',
                         report='job/original-final.json', report_sha256='report-pin',
                         binding='job/original-final-binding.json', binding_sha256='binding-pin',
                         process='job/original-final-process.json', process_sha256='process-pin',
                         log='job/original-final.log', log_sha256='log-pin',
                         source=str(root/'candidate/owned.kicad_pcb'),
                         input=str(root/'job/input/owned.kicad_pcb'),
                         saved=False, before={}, schematic_parity=True)
            aggregate = dict(status='observed', accepted=False)
            case = dict(source=str(root/'source/owned.kicad_pcb'),
                        original_aggregate=dict(path='old/result.json',
                            sha256='aggregate-pin', status='observed'),
                        original_individual_stages=[stage],
                        baseline_reference=dict(exact_native_findings=expected,
                            ignored_checks_exact_array=[]))
            documents = {root/'old/result.json': aggregate}
            digests = {root/'old/result.json': 'aggregate-pin'}
            for key, pin in [('report', 'report-pin'), ('binding', 'binding-pin'),
                             ('process', 'process-pin'), ('log', 'log-pin')]:
                path = root/stage[key]
                digests[path] = pin
                if path.suffix == '.json':
                    documents[path] = dict(owned_stage=key)
            stack.enter_context(patch.object(cohort, 'ROOT', root))
            stack.enter_context(patch.object(cohort, 'CASES', {'push-button-led': case}))
            stack.enter_context(patch.object(cohort.p, 'sha', side_effect=lambda path: digests[Path(path)]))
            stack.enter_context(patch.object(cohort.f, 'read_json',
                side_effect=lambda path: copy.deepcopy(documents[Path(path)])))
            stage_check = stack.enter_context(patch.object(cohort.f, 'check_drc_stage', return_value=native))
            stack.enter_context(patch.object(cohort.p, 'native_accepted', return_value=True))
            stack.enter_context(patch.object(cohort.shared, 'material', return_value={'owned': 'unchanged'}))
            stack.enter_context(patch.object(cohort.sx, 'read', return_value=['owned-tree']))
            stack.enter_context(patch.object(cohort.p, 'immutable', return_value=['owned-shell']))
            stack.enter_context(patch.object(cohort, 'route_records', return_value=['owned-route']))
            # The separately tested legacy helper owns its non-normal layout.
            stack.enter_context(patch.object(cohort, 'original_legacy_prl'))
            yield native, expected, stage_check

    def test_actual_original_findings_accept_equal_int_and_float_positions(self):
        findings = [dict(type='lib_footprint_issues', severity='warning',
                         description='owned missing library', items=[
                             dict(uuid='owned-footprint', pos=dict(x=30.0, y=10.0))])]
        with self.original_findings_fixture(findings) as (native, expected, stage_check):
            observed, _ = cohort.original_gate('push-button-led', 'unused-public-pin')
            self.assertEqual(observed['findings'], expected)
            self.assertIsInstance(observed['findings'][0]['items'][0]['pos']['x'], float)
            self.assertIs(observed, native)
            stage_check.assert_called_once()

    def test_actual_original_findings_refuse_missing_replaced_and_duplicate_rows(self):
        original = dict(type='lib_footprint_issues', severity='warning',
                        description='owned missing library', items=[
                            dict(uuid='owned-footprint', pos=dict(x=30.0, y=10.0))])
        replacement = copy.deepcopy(original)
        replacement['items'][0]['uuid'] = 'different-footprint'
        for label, findings in [('missing', []), ('replaced', [replacement]),
                                ('duplicate', [original, copy.deepcopy(original)])]:
            with self.subTest(label=label), self.original_findings_fixture(findings):
                with self.assertRaisesRegex(cohort.p.Rejected, 'original full warning/ignored population'):
                    cohort.original_gate('push-button-led', 'unused-public-pin')

    @contextmanager
    def legacy_prl_fixture(self, project):
        """Real owned files and shared guard replay; fake portable flags only.

        Reuse the existing event-control metadata scaffold. No actual chflags,
        historical source, worker, or claimed Native event is involved.
        """
        with tempfile.TemporaryDirectory() as name, ExitStack() as stack:
            root = Path(name).resolve()
            aggregate = root/'legacy/result.json'
            captured = aggregate.parent/'code/autorouter/pipeline.py'
            diagnostic = aggregate.parent/'code/experiments/original_project_native_v1/driver.py'
            captured.parent.mkdir(parents=True)
            captured.write_text('# Owned genuinely pre-policy producer fixture.\n')
            guarded = project == 'ds18b20'
            if guarded:
                diagnostic.parent.mkdir(parents=True)
                diagnostic.write_text('# Owned guarded diagnostic fixture.\n')
            record = dict(tools=dict(implementation_sha256={
                              'autorouter/pipeline.py': cohort.p.sha(captured)}),
                          helper_sha256=cohort.p.sha(diagnostic) if guarded else 'historical-aggregate-bound-helper',
                          protect_local_settings=guarded)
            stages = []
            owned = []
            flag = getattr(cohort.ls.stat, 'UF_IMMUTABLE', 2)
            for stage_name in ('original-refill', 'original-final'):
                board = aggregate.parent/'job'/(stage_name+'-input')/'board.kicad_pcb'
                board.parent.mkdir(parents=True)
                board.write_text('(kicad_pcb)\n')
                prl = board.with_suffix('.kicad_prl')
                prl.write_bytes(b'{"owned_exact_local_state":true}\n')
                before = {board.name: cohort.p.sha(board)}
                if guarded:
                    before[prl.name] = cohort.p.sha(prl)
                after = {board.name: cohort.p.sha(board), prl.name: cohort.p.sha(prl)}
                binding = dict(input=str(board), before=before, after=after)
                process = {}
                if guarded:
                    process['local_settings_protection'] = dict(
                        policy=cohort.ls.POLICY, present=True, path=str(prl),
                        sha256=before[prl.name], flags_before=0, flags_during=flag,
                        flags_restored=True, bytes_unchanged=True)
                binding_path = aggregate.parent/'job'/(stage_name+'-binding.json')
                process_path = aggregate.parent/'job'/(stage_name+'-process.json')
                binding_path.write_text(json.dumps(binding))
                process_path.write_text(json.dumps(process))
                stages.append(dict(binding=str(binding_path.relative_to(root)),
                                   process=str(process_path.relative_to(root)),
                                   binding_sha256=cohort.p.sha(binding_path),
                                   process_sha256=cohort.p.sha(process_path)))
                owned.append(SimpleNamespace(prl=prl, binding=binding,
                    process=process, binding_path=binding_path, process_path=process_path))
            case = dict(original_aggregate=dict(path=str(aggregate.relative_to(root))),
                        original_individual_stages=stages)
            def refresh():
                aggregate.write_text(json.dumps(record))
                case['original_aggregate']['sha256'] = cohort.p.sha(aggregate)
            refresh()
            stack.enter_context(patch.object(cohort, 'ROOT', root))
            stack.enter_context(patch.object(cohort, 'CASES', {project: case}))
            stack.enter_context(patch.object(self, 'root', root, create=True))
            stack.enter_context(patch.object(self, 'flag', flag, create=True))
            stack.enter_context(field_event_helpers.PreservedFieldEventControls.metadata(self))
            yield SimpleNamespace(project=project, captured=captured, diagnostic=diagnostic,
                aggregate=aggregate, record=record, case=case, stages=owned, refresh=refresh)

    def test_guarded_DS18_replays_both_exact_preserve_events(self):
        with self.legacy_prl_fixture('ds18b20') as fixture:
            real_check = cohort.ls.check_preserved
            with patch.object(cohort.ls, 'check_preserved', wraps=real_check) as check:
                self.assertIsNone(cohort.original_legacy_prl('ds18b20'))
                self.assertEqual(check.call_count, 2)
                self.assertEqual([call.args[0] for call in check.call_args_list],
                                 [stage.prl for stage in fixture.stages])
            # A second-stage event cannot borrow a first-stage path or pretend
            # restoration succeeded. The actual shared event checker rejects it.
            second = fixture.stages[1]
            second.process['local_settings_protection']['path'] = str(fixture.stages[0].prl)
            second.process_path.write_text(json.dumps(second.process))
            # Author a coherent synthetic event to isolate event validation;
            # the separate late-rewrite control keeps its frozen hash fixed.
            fixture.case['original_individual_stages'][1]['process_sha256'] = cohort.p.sha(second.process_path)
            with self.assertRaises(cohort.p.Rejected):
                cohort.original_legacy_prl('ds18b20')

    def test_legacy_captured_pipeline_and_guarded_helper_mismatch_refuse(self):
        for name, message in [('captured', 'captured original Native producer'),
                              ('diagnostic', 'captured guarded original diagnostic producer')]:
            with self.subTest(captured=name), self.legacy_prl_fixture('ds18b20') as fixture:
                file = getattr(fixture, name)
                file.write_text(file.read_text()+'# changed after capture\n')
                with self.assertRaisesRegex(cohort.p.Rejected, message):
                    cohort.original_legacy_prl('ds18b20')

    def test_prepolicy_LED_and_Arc_need_no_fabricated_helper_but_keep_prl_bytes(self):
        for project in ('push-button-led', 'arcdice'):
            with self.subTest(project=project), self.legacy_prl_fixture(project) as fixture:
                self.assertFalse(fixture.diagnostic.exists())
                self.assertIsNone(cohort.original_legacy_prl(project))
                fixture.stages[1].prl.write_bytes(b'changed Native-created local state\n')
                with self.assertRaisesRegex(cohort.p.Rejected, 'retained PRL bytes/flags'):
                    cohort.original_legacy_prl(project)

    def test_legacy_expected_created_prl_cannot_disappear_or_become_dangling(self):
        for project in ('push-button-led', 'arcdice'):
            for mutation in ('deleted', 'dangling_symlink'):
                with self.subTest(project=project, mutation=mutation), self.legacy_prl_fixture(project) as fixture:
                    # The retained after-map expects this Native-created PRL;
                    # establish the good final check before the late mutation.
                    self.assertIsNone(cohort.original_legacy_prl(project))
                    stage = fixture.stages[1]
                    self.assertIn(stage.prl.name, stage.binding['after'])
                    stage.prl.unlink()
                    if mutation == 'dangling_symlink':
                        stage.prl.symlink_to(stage.prl.parent/'missing-owned-local-state')
                    self.assertFalse(stage.prl.exists())
                    with self.assertRaisesRegex(cohort.p.Rejected, 'legacy original retained PRL'):
                        cohort.original_legacy_prl(project)

    def test_legacy_final_prl_rejects_late_binding_and_process_rewrites(self):
        for key in ('binding', 'process'):
            with self.subTest(document=key), self.legacy_prl_fixture('push-button-led') as fixture:
                self.assertIsNone(cohort.original_legacy_prl('push-button-led'))
                stage = fixture.stages[1]
                frozen = fixture.case['original_individual_stages'][1]
                expected = frozen[key+'_sha256']
                if key == 'binding':
                    # A late rewritten after-map must not hide a deleted PRL.
                    stage.binding['after'].pop(stage.prl.name)
                    stage.prl.unlink()
                else:
                    # None remains semantically unguarded; only frozen-byte
                    # verification detects this otherwise invisible rewrite.
                    stage.process['local_settings_protection'] = None
                changed_path = getattr(stage, key+'_path')
                changed_path.write_text(json.dumps(getattr(stage, key)))
                self.assertNotEqual(cohort.p.sha(changed_path), expected)
                self.assertEqual(frozen[key+'_sha256'], expected)
                with self.assertRaisesRegex(cohort.p.Rejected,
                        'fixed original '+key+' changed before final PRL check'):
                    cohort.original_legacy_prl('push-button-led')

    def test_unmarked_LED_cannot_adopt_future_policy_even_with_coherent_hashes(self):
        for marker in ('captured_declaration', 'receipt_marker'):
            with self.subTest(marker=marker), self.legacy_prl_fixture('push-button-led') as fixture:
                if marker == 'captured_declaration':
                    fixture.captured.write_text('NORMAL_DRC_LOCAL_SETTINGS_POLICY = '+repr(cohort.ls.JOB_POLICY)+'\n')
                    fixture.record['tools']['implementation_sha256']['autorouter/pipeline.py'] = cohort.p.sha(fixture.captured)
                else:
                    fixture.record['tools']['normal_drc_local_settings_policy'] = cohort.ls.JOB_POLICY
                fixture.refresh()  # Refusal must be semantic, not a stale hash.
                with self.assertRaisesRegex(cohort.p.Rejected, 'specific legacy original protection scope'):
                    cohort.original_legacy_prl('push-button-led')

    def test_each_B2_uses_exact_width_optin_only_for_positive_minimum_cases(self):
        board, output = Path('owned.kicad_pcb'), Path('owned-output')
        for project in ('sonde', 'nus-usb-led', 'push-button-led', 'ds18b20'):
            with self.subTest(project=project), patch.object(cohort.p, 'route', return_value='B2') as route, patch.object(cohort.s, 'prune') as prune:
                self.assertEqual(cohort.invoke(board, output, cohort.CASES[project], 'B2_stronger'), 'B2')
                options = dict(scoring_variant='via_default', _fanout_enabled=False,
                               _optimizer_enabled=False, _engine_clearance_margin_nm=20000)
                if project != 'ds18b20':
                    options['_engine_global_width_policy'] = 'original-global-minimum-width-v1'
                route.assert_called_once_with(board, output, 120, False, 'both', 'tuned-free-angle', **options)
                prune.assert_not_called()

    def test_each_C_owns_fresh_incumbent_with_v2_or_unchanged_DS18_v1(self):
        board, output = Path('owned.kicad_pcb'), Path('owned-output')
        for project in ('sonde', 'nus-usb-led', 'push-button-led', 'ds18b20'):
            with self.subTest(project=project), patch.object(cohort.s, 'prune', return_value='C') as prune, patch.object(cohort.p, 'route') as route:
                self.assertEqual(cohort.invoke(board, output, cohort.CASES[project], 'C_stronger'), 'C')
                policy = 'free-angle-clearance20-v1' if project == 'ds18b20' else 'free-angle-clearance20-global-width-v2'
                prune.assert_called_once_with(board, output, 120, proposal_policy='chains',
                    incumbent_scoring='via_default', _incumbent_policy=policy)
                route.assert_not_called()

    def test_declared_population_retains_arc_and_zero_zone_DS18(self):
        self.assertEqual(len(cohort.POPULATION), 10)
        self.assertEqual(len(set(cohort.POPULATION)), 10)
        self.assertEqual(len(cohort.ORDER), 8)
        self.assertEqual(len(cohort.STAGES), 8)
        self.assertEqual(set(cohort.STAGES.values()), set(cohort.ORDER))
        self.assertEqual(set(cohort.STAGES), {project + '--' + name for project, name in cohort.ORDER})
        # Evaluate ONLY the actual wrapper's two pure stage declarations; never
        # its imports, argparse, output creation or runner.
        tree = ast.parse(Path(cohort.__file__).with_name('command.py').read_text())
        assignments = [node for node in tree.body if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id in
                               {'PROJECTS', 'STAGES'} for target in node.targets)]
        self.assertEqual(len(assignments), 2)
        namespace = {}
        exec(compile(ast.Module(body=assignments, type_ignores=[]),
                     str(Path(cohort.__file__).with_name('command.py')), 'exec'), namespace)
        self.assertEqual(namespace['STAGES'], cohort.STAGES)
        self.assertEqual([row for row in cohort.POPULATION if row[0] == 'arcdice'],
                         [('arcdice', 'B2_stronger'), ('arcdice', 'C_stronger')])
        self.assertFalse(any(project == 'arcdice' for project, _ in cohort.ORDER))
        self.assertEqual(cohort.CASES['ds18b20']['geometry']['ordinary_zones'], 0)
        for name in cohort.ARMS:
            self.assertIn(('ds18b20', name), cohort.ORDER)
            with self.assertRaises(cohort.p.Rejected):
                cohort.stage_id('arcdice', name)
            with self.assertRaises(cohort.p.Rejected):
                cohort.arm_spec(cohort.CASES['arcdice'], name)

    def test_conditional_field_census_requires_actual_original_complete_counts(self):
        baseline = dict(field_parity=dict(qualification=dict(component_count=6, compared_field_count=19)))
        native = dict(findings=[dict(type=cohort.fields.TYPE)],
                      field_parity=dict(qualification=dict(qualified=True, component_count=6, compared_field_count=19)))
        self.assertIsNone(cohort.check_field_census(native, baseline))
        for key, value in [('qualified', False), ('component_count', 7), ('compared_field_count', 18)]:
            changed = copy.deepcopy(native)
            changed['field_parity']['qualification'][key] = value
            with self.subTest(key=key), self.assertRaises(cohort.p.Rejected):
                cohort.check_field_census(changed, baseline)
        with self.assertRaises(cohort.p.Rejected):
            cohort.check_field_census(native, {})
        with self.assertRaises(cohort.p.Rejected):
            cohort.check_field_census(dict(findings=native['findings']), baseline)

    def test_field_census_is_not_inferred_without_field_findings(self):
        self.assertIsNone(cohort.check_field_census(dict(findings=[]), {}))
        with self.assertRaises(cohort.p.Rejected):
            cohort.check_field_census(dict(findings=[], field_parity=dict(qualification={})), {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
