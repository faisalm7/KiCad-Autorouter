"""Caller-bound comparison controls; authored files, never Native routing proof.

The tools/source identity provider is stubbed. Captured source policy, bounded
file readers, context sealing, exact engine settings and dispatch are real.
No test executes KiCad, Java, Git, a sandbox or an installed workflow.
"""
import ast
import copy
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from autorouter import comparison as cmp, config as c, floor_route as f, handoff as h, pipeline as p
from autorouter import local_settings as ls, placement_clearance as pc, provenance as pv
from tests import normal_prl_fixture, test_engine_fanout as engine_fixture

PROJECT = Path(__file__).resolve().parents[1]


class ComparisonContextControls(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir=PROJECT / '.cache')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.runtime = self.root / 'runtime'
        self.output = self.runtime / '.runs' / (cmp.PREFIX + 'owned-control')
        (self.output / 'code').mkdir(parents=True)
        self.project = self.root / 'source'; self.project.mkdir()
        self.source = self.project / 'owned.kicad_pcb'
        for suffix, text in (('.kicad_pcb', '(kicad_pcb (version 20260206))\n'),
                             ('.kicad_pro', '{}\n'), ('.kicad_sch', '(kicad_sch)\n')):
            self.source.with_suffix(suffix).write_text(text)
        implementation = {}
        for name in ('pipeline.py', 'comparison.py'):
            path = self.output / 'code' / name
            shutil.copy2(PROJECT / 'autorouter' / name, path)
            implementation['autorouter/' + name] = p.sha(path)
        self.tools = dict(kicad='10.0.7', comparison_route_policy=cmp.POLICY,
            source_provenance=dict(kind=pv.KIND, native_version='10.0.7'),
            implementation_sha256=implementation, files={'owned-not-executed': '1' * 64})
        self.hashes = pc.inventory(self.project)
        for target in (patch.object(c, 'ROOT', self.runtime), patch.object(c, 'NATIVE_VERSION', '10.0.7'),
                       patch.object(c, 'current_native_selection', return_value={'version': '10.0.7'}),
                       patch.object(p, 'tool_manifest', side_effect=lambda: copy.deepcopy(self.tools))):
            target.start(); self.addCleanup(target.stop)
        self.context = self.make_context()
        self.data = self.make_record()
        cmp.bind(self.output, self.data, self.context)
        self.receipt = self.output / 'result.json'
        p.save_json(self.receipt, self.data)

    def make_context(self, **changes):
        args = dict(source=self.source, output=self.output, profile='tuned', seconds=120,
                    tools=copy.deepcopy(self.tools), source_hashes=copy.deepcopy(self.hashes))
        args.update(changes)
        return cmp.Context(**args)

    def make_record(self):
        return dict(schema=1, source=str(self.source), source_hashes=copy.deepcopy(self.hashes),
            tools=copy.deepcopy(self.tools), engine_profile='tuned', baseline=p.engine_baseline('tuned', 'both'),
            adapter='both', scope='whole_board_unlocked_routing', scoring_variant=None,
            budget_seconds=120, cpu_budget_seconds=120, schematic_parity='checked by final native DRC')

    def authorize(self, **changes):
        args = dict(context=self.context, source=self.source, output=self.output, seconds=120,
            keep=False, adapter='both', profile='tuned', scoring=None, guidance='native', extras=())
        args.update(changes); return cmp.authorize(**args)

    def context_record(self, context):
        """Only author a contract fixture; no routing/Native result is implied."""
        row = self.make_record()
        row.update(source=str(context.source), source_hashes=copy.deepcopy(context.source_hashes),
                   tools=copy.deepcopy(context.tools), engine_profile=context.profile,
                   baseline=p.engine_baseline(context.profile, context.adapter),
                   adapter=context.adapter, scoring_variant=context.scoring_variant,
                   budget_seconds=context.seconds, cpu_budget_seconds=context.seconds)
        (self.output / cmp.SIDECAR).unlink()
        cmp.bind(self.output, row, context)
        return row

    def test_stock_and_three_score_contexts_bind_exact_existing_engine_choices(self):
        cases = [('none', 'standard', None), ('both', 'standard', None),
                 ('both', 'tuned', None), *[('both', 'tuned', score)
                 for score in ('via_default', 'via_low', 'via_high')]]
        scores = {'via_default': (50, 5), 'via_low': (25, 3), 'via_high': (100, 10)}
        for adapter, profile, score in cases:
            with self.subTest(adapter=adapter, profile=profile, score=score):
                context = self.make_context(adapter=adapter, profile=profile, scoring_variant=score)
                cmp.authorize(context, self.source, self.output, 120, False,
                              adapter, profile, score, 'native', ())
                row = self.context_record(context)
                self.assertTrue(cmp.check_record(self.output, row, context))
                self.assertEqual(context.record()['adapter'], adapter)
                self.assertEqual(context.record()['scoring_variant'], score)
                self.assertIs(row['production_admitted'], False)
                settings = p.engine_profile_settings(profile, 90, scoring_variant=score)
                flags = [arg for arg in settings['argv'] if arg.startswith('--router.scoring.')]
                expected = [] if score is None else [
                    '--router.scoring.via_costs=' + str(scores[score][0]),
                    '--router.scoring.plane_via_costs=' + str(scores[score][1])]
                self.assertEqual(flags, expected)
                p.save_json(self.receipt, row)
                with self.assertRaisesRegex(p.Rejected, 'explicit caller context'):
                    p.check_result(self.receipt)

    def test_adapter_scoring_types_and_outside_fixed_tuples_refuse(self):
        class StringSubclass(str):pass
        changes = [dict(adapter=value) for value in (None, False, 0, [], {}, 'graphics', 'planes', StringSubclass('both'))]
        changes += [dict(scoring_variant=value) for value in (False, 0, [], {}, '', 'unknown', StringSubclass('via_low'))]
        changes += [dict(adapter='none', profile='tuned'),
                    dict(adapter='none', profile='standard', scoring_variant='via_default'),
                    dict(adapter='both', profile='standard', scoring_variant='via_low')]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(p.Rejected):self.make_context(**change)
        for field, value in (('adapter', 'none'), ('scoring_variant', 'via_low')):
            context = self.make_context()
            object.__setattr__(context, field, value)  # Test a bypass of the frozen dataclass only.
            with self.subTest(sealed_field=field), self.assertRaisesRegex(p.Rejected, 'expectations changed'):
                context.check()

    def test_stock_and_scored_calls_reach_only_the_existing_normal_transport_gate(self):
        for adapter, profile, score in (('none', 'standard', None), ('both', 'tuned', 'via_high')):
            context = self.make_context(adapter=adapter, profile=profile, scoring_variant=score)
            with self.subTest(adapter=adapter, score=score), patch.object(p, 'sha', return_value=c.JAR_SHA256), \
                    patch.object(p, 'check_storage', side_effect=RuntimeError('normal-storage-gate')) as storage, \
                    patch.object(p, 'Job') as job:
                with self.assertRaisesRegex(RuntimeError, 'normal-storage-gate'):
                    p.route(self.source, self.output, 120, False, adapter, profile,
                            scoring_variant=score, comparison_context=context)
                storage.assert_called_once_with(active_root=self.output); job.assert_not_called()
            for changed_adapter, changed_score in (('both' if adapter == 'none' else 'none', score),
                                                    (adapter, 'via_low' if score != 'via_low' else 'via_high')):
                with self.subTest(wrong_request=(changed_adapter, changed_score)), \
                        patch.object(p, 'check_storage', side_effect=AssertionError('dispatch')), self.assertRaises(p.Rejected):
                    p.route(self.source, self.output, 120, False, changed_adapter, profile,
                            scoring_variant=changed_score, comparison_context=context)

    def test_stock_scored_receipts_and_sidecars_cannot_change_caller_or_policy(self):
        for adapter, profile, score in (('none', 'standard', None), ('both', 'tuned', 'via_low')):
            context = self.make_context(adapter=adapter, profile=profile, scoring_variant=score)
            good = self.context_record(context)
            for field, value in (('adapter', 'both' if adapter == 'none' else 'none'),
                                 ('scoring_variant', 'via_high'), ('baseline', 'B1')):
                changed = copy.deepcopy(good); changed[field] = value
                with self.subTest(adapter=adapter, changed=field), self.assertRaises(p.Rejected):
                    cmp.check_record(self.output, changed, context)
            wrong = self.make_context(adapter='both', profile='tuned', scoring_variant='via_high')
            with self.assertRaises(p.Rejected):cmp.check_record(self.output, good, wrong)
            sidecar = self.output / cmp.SIDECAR; original = sidecar.read_bytes()
            for field, value in (('adapter', 'both' if adapter == 'none' else 'none'),
                                 ('scoring_variant', 'via_high'), ('policy', 'selected-native7-fixed-comparison-v1')):
                row = json.loads(original); row[field] = value; sidecar.write_text(json.dumps(row))
                changed = copy.deepcopy(good); changed['comparison_route']['sha256'] = p.sha(sidecar)
                with self.subTest(sidecar_field=field), self.assertRaises(p.Rejected):
                    cmp.check_record(self.output, changed, context)
                sidecar.write_bytes(original)
            changed = copy.deepcopy(good)
            changed['comparison_route']['policy'] = 'selected-native7-fixed-comparison-v1'
            with self.assertRaises(p.Rejected):cmp.check_record(self.output, changed, context)
            if score is not None:
                changed = copy.deepcopy(good); changed.pop('scoring_variant')
                with self.assertRaises(p.Rejected):cmp.check_record(self.output, changed, context)

    def test_three_score_provenance_rejects_reauthored_missing_duplicate_and_changed_flags(self):
        for score in ('via_default', 'via_low', 'via_high'):
            with self.subTest(score=score):
                # Setup-only reuse of the complete existing authored engine/PRL
                # fixture. Its Native1000 data is not current-version routing
                # evidence; the shared engine settings/journal checker is real.
                setup = engine_fixture.EngineFanoutControls('runTest')
                self.addCleanup(setup.doCleanups)
                with patch.object(c, 'ROOT', PROJECT), patch.object(c, 'NATIVE_VERSION', '10.0.0'):
                    case = setup.publication_fixture('tuned', None)
                    case.data['scoring_variant'] = score
                    normal_prl_fixture._authored_normal_engine(case.run, case.data)
                p.check_engine_profile_record(case.data, case.run)
                good = copy.deepcopy(case.data)
                process = f.read_json(case.run / 'engine-process.json')
                scoreflag = p.engine_scoring_settings(score)['argv'][0]
                for fault in ('marker_missing', 'wrong_marker', 'missing_flag', 'duplicate_flag', 'changed_flag', 'journal_only', 'missing_worker'):
                    row = copy.deepcopy(good); worker = next(s for s in row['steps'] if s['name'] == 'engine')
                    if fault == 'marker_missing':row.pop('scoring_variant')
                    elif fault == 'wrong_marker':row['scoring_variant'] = 'via_high' if score != 'via_high' else 'via_low'
                    elif fault == 'missing_worker':row['steps'].remove(worker)
                    elif fault == 'journal_only':pass  # Alter only the durable process below.
                    else:
                        for argv in (row['engine_budget']['argv'], worker['argv']):
                            if fault == 'missing_flag':argv.remove(scoreflag)
                            elif fault == 'duplicate_flag':argv.append(scoreflag)
                            else:argv[argv.index(scoreflag)] = '--router.scoring.via_costs=1'
                    # Reauthor both declarations and journal for changed flags;
                    # exact profile derivation must still detect the fault.
                    journal = copy.deepcopy(worker)
                    if fault == 'journal_only':journal['argv'].append('--router.scoring.via_costs=1')
                    p.save_json(case.run / 'engine-process.json', journal)
                    with self.subTest(fault=fault), self.assertRaises(p.Rejected):
                        p.check_engine_profile_record(row, case.run)
                    p.save_json(case.run / 'engine-process.json', process)

    def test_typed_caller_fixed_source_and_existing_profiles(self):
        self.context.check(); self.authorize()
        for profile in ('standard', 'tuned'):
            context = self.make_context(profile=profile)
            cmp.authorize(context, self.source, self.output, 120, False, 'both', profile, None, 'native', ())
            settings = p.engine_profile_settings(profile, 90)
            self.assertIn('--router.optimizer.max_threads=1', settings['argv'])
            self.assertGreater(settings['assigned_job_timeout_seconds'], 0)
            self.assertIn('--router.autorouter.max_passes=' + ('100' if profile == 'tuned' else '30'), settings['argv'])
        for values in ({'profile': 'completion-only'}, {'profile': 'tuned-free-angle'},
                       {'seconds': True}, {'seconds': float('nan')}, {'seconds': 901},
                       {'source': str(self.source)}, {'tools': []}, {'source_hashes': {}}):
            with self.subTest(values=values), self.assertRaises((p.Rejected, ValueError)):
                self.make_context(**values)
        for wrong in ({}, object(), type('DerivedContext', (cmp.Context,), {})(
                self.source, self.output, 'tuned', 120, copy.deepcopy(self.tools), copy.deepcopy(self.hashes))):
            with self.subTest(type=type(wrong)), self.assertRaises(p.Rejected):cmp.require_context(wrong)

    def test_reserved_output_and_complete_schematic_are_not_optional(self):
        for changes in ({'output': self.runtime / '.runs' / 'ordinary'},
                        {'output': self.root / (cmp.PREFIX + 'outside-runtime')},
                        {'output': self.project / (cmp.PREFIX + 'source-child')},
                        {'source_hashes': {k:v for k,v in self.hashes.items() if not k.endswith('.kicad_sch')}},
                        {'source_hashes': {**self.hashes, '../escape': '0' * 64}}):
            with self.subTest(changes=changes), self.assertRaises((p.Rejected, ValueError)):
                self.make_context(**changes)
        alias = self.root / 'alias'; alias.symlink_to(self.project, target_is_directory=True)
        with self.assertRaises(ValueError):self.make_context(source=alias / self.source.name)
        ordinary = self.runtime / '.runs' / 'ordinary'; ordinary.mkdir()
        (ordinary / cmp.SIDECAR).write_text('{}\n')
        self.assertTrue(cmp.marked(ordinary))  # Detection is intentionally broader than eligibility.
        with self.assertRaises(p.Rejected):self.make_context(output=ordinary)

    def test_caller_seal_rejects_mutation_or_selected_runtime_drift(self):
        for field in ('tools', 'source_hashes'):
            context = self.make_context()
            getattr(context, field)['unexpected'] = '0' * 64
            with self.subTest(field=field), self.assertRaisesRegex(p.Rejected, 'expectations changed'):
                context.check()
        for name, value in (('NATIVE_VERSION', '10.0.0'), ('ROOT', self.root)):
            with self.subTest(name=name), patch.object(c, name, value), self.assertRaises(p.Rejected):
                self.context.check()
        for change in ({'kicad': '10.0.0'}, {'comparison_route_policy': 'unknown'},
                       {'source_provenance': {}}, {'source_provenance': []}):
            tools = {**self.tools, **change}
            with self.subTest(change=change), self.assertRaises(p.Rejected):self.make_context(tools=tools).check()

    def test_source_addition_or_changed_live_tool_manifest_is_stale(self):
        self.source.with_suffix('.kicad_pro').write_text('{"changed": true}\n')
        with self.assertRaisesRegex(p.Rejected, 'source changed'):self.context.check()
        self.source.with_suffix('.kicad_pro').write_text('{}\n')
        self.source.with_suffix('.kicad_dru').write_text('(version 1)\n')
        with self.assertRaises(p.Rejected):self.context.check()
        self.source.with_suffix('.kicad_dru').unlink()
        self.tools['files']['owned-not-executed'] = '2' * 64
        with self.assertRaises(p.Rejected):self.context.check()

    def test_request_changes_and_optional_overrides_refuse_before_dispatch(self):
        for change in ({'source': self.source.with_name('other.kicad_pcb')}, {'output': self.output / 'child'},
                       {'seconds': 121}, {'keep': True}, {'adapter': 'none'}, {'profile': 'standard'},
                       {'scoring': 'via_low'}, {'guidance': 'board-floors-v1'}, {'extras': ({},)},
                       {'extras': (False,)}, {'extras': (20000,)}):
            with self.subTest(change=change), self.assertRaises(p.Rejected):self.authorize(**change)
        for change in ({'settings_path': self.root / 'settings.json'}, {'preference_overrides': {}},
                       {'_fanout_enabled': False}, {'_optimizer_enabled': False},
                       {'_engine_clearance_margin_nm': 20000}, {'_engine_global_width_policy': 'x'},
                       {'native_toolchain': object()}, {'experimental_schematic_parity': True}):
            with self.subTest(change=change), patch.object(p, 'check_storage', side_effect=AssertionError('dispatch')), self.assertRaises(p.Rejected):
                p.route(self.source, self.output, 120, False, 'both', 'tuned', comparison_context=self.context, **change)

    def test_live_context_cannot_bypass_normal_transport_or_accounting(self):
        # Stop before Job/native dispatch: authorize only removes capability
        # dispatch; JAR integrity and normal storage gates remain operative.
        with patch.object(p, 'sha', return_value=c.JAR_SHA256), patch.object(p, 'check_storage', side_effect=RuntimeError('normal-storage-gate')) as storage, patch.object(p, 'Job') as job:
            with self.assertRaisesRegex(RuntimeError, 'normal-storage-gate'):
                p.route(self.source, self.output, 120, False, 'both', 'tuned', comparison_context=self.context)
            storage.assert_called_once_with(active_root=self.output); job.assert_not_called()
        with patch.object(p, 'check_storage', side_effect=AssertionError('dispatch')), self.assertRaisesRegex(p.Rejected, 'selected Native'):
            p.route(self.source, self.root / 'ordinary', 120, False, 'both', 'tuned')
        with self.assertRaisesRegex(p.Rejected, 'reserved comparison output'):
            p.route(self.source, self.output, 120, False, 'both', 'standard')

    def test_record_is_bound_to_exact_context_and_captured_policy(self):
        self.assertTrue(cmp.check_record(self.output, self.data, self.context))
        for change in ({'profile': 'standard'}, {'seconds': 121}, {'output': self.output.parent / (cmp.PREFIX + 'other')}):
            with self.subTest(change=change), self.assertRaises(p.Rejected):
                cmp.check_record(self.output, self.data, self.make_context(**change))
        sidecar = self.output / cmp.SIDECAR
        sidecar.write_bytes(sidecar.read_bytes() + b'\n')
        with self.assertRaises(p.Rejected):cmp.check_record(self.output, self.data, self.context)

    def test_retained_settings_markers_cannot_expand_fixed_scope(self):
        forbidden = ('strategy', 'input_policy', 'routing_preferences', 'diagnostic_schema', 'production_qualified',
            'experimental_route_policy', 'experimental_native_toolchain', 'experimental_schematic_parity_policy',
            'guidance_policy', 'engine_fanout_override', 'engine_optimizer_override', 'engine_angle_binding',
            'engine_planning_clearance_margin_nm', 'engine_global_width_policy', 'incumbent_scoring_contract',
            'incumbent_scoring_variant', 'incumbent_receipt_sha256', 'pruning_preferences', 'pruning_preferences_policy')
        for field in forbidden:
            row = copy.deepcopy(self.data); row[field] = None
            with self.subTest(field=field), self.assertRaises(p.Rejected):cmp.check_record(self.output, row, self.context)
        for field, value in (('schema', True), ('production_admitted', 0), ('adapter', 'none'), ('engine_profile', 'standard'),
                             ('baseline', 'B0'), ('scope', 'selected_nets'), ('scoring_variant', 'via_low'),
                             ('budget_seconds', 121), ('cpu_budget_seconds', 121), ('schematic_parity', 'not checked')):
            row = copy.deepcopy(self.data); row[field] = value
            with self.subTest(field=field), self.assertRaises(p.Rejected):cmp.check_record(self.output, row, self.context)

    def test_policy_deletion_cannot_be_reauthored_as_a_new_valid_source_pin(self):
        for name, declaration in (('pipeline.py', 'COMPARISON_ROUTE_POLICY'), ('comparison.py', 'POLICY')):
            with self.subTest(name=name):
                path = self.output / 'code' / name; original = path.read_bytes()
                path.write_bytes(b'\n'.join(b'# removed comparison declaration' if line.split(b'=')[0].strip() == declaration.encode() else line for line in original.split(b'\n')))
                self.assertTrue(path.read_bytes() != original)
                self.tools['implementation_sha256']['autorouter/' + name] = p.sha(path)
                context = self.make_context(); data = self.make_record()
                (self.output / cmp.SIDECAR).unlink(); cmp.bind(self.output, data, context)
                with self.assertRaisesRegex(p.Rejected, 'source policy'):cmp.check_record(self.output, data, context)
                path.write_bytes(original); self.tools['implementation_sha256']['autorouter/' + name] = p.sha(path)

    def test_default_reader_refuses_even_combined_receipt_and_sidecar_deletion(self):
        row = copy.deepcopy(self.data)
        row.pop('comparison_route'); row.pop('production_admitted')
        (self.output / cmp.SIDECAR).unlink(); p.save_json(self.receipt, row)
        with self.assertRaisesRegex(p.Rejected, 'explicit caller context'):p.check_result(self.receipt)
        with self.assertRaisesRegex(p.Rejected, 'explicit caller context'):p.check_rejected_routing_attempt(self.receipt)
        with self.assertRaises((p.Rejected, OSError)):cmp.check_record(self.output, row, self.context)

    def test_explicit_reader_bypasses_cache_and_preserves_caller_identity(self):
        with p.validation_readback_session(), patch.object(p, '_check_result_uncached', return_value={'controlled': True}) as check:
            for _ in range(2):self.assertEqual(p.check_result(self.receipt, comparison_context=self.context), {'controlled': True})
            self.assertEqual(check.call_count, 2)
            check.assert_called_with(self.receipt, native_toolchain=None, experimental_schematic_parity=False, comparison_context=self.context)
            p.check_rejected_routing_attempt(self.receipt, comparison_context=self.context)
            check.assert_called_with(self.receipt, _rejected_attempt=True, comparison_context=self.context)
        with self.assertRaises(p.Rejected):p.check_result(self.receipt, comparison_context={})

    def test_positive_and_completed_negative_keep_normal_engine_validation(self):
        contexts = [self.make_context(adapter='none', profile='standard'),
                    self.make_context(scoring_variant='via_low'), self.context]
        for context in contexts:
            fixture = self.context_record(context)
            for negative in (False, True):
                row = copy.deepcopy(fixture)
                row.update(accepted=not negative, status='drc_rejected' if negative else 'routing_accepted')
                p.save_json(self.receipt, row)
                with self.subTest(adapter=context.adapter, score=context.scoring_variant, negative=negative), \
                        patch.object(p, 'check_normal_engine_provenance', side_effect=RuntimeError('required-normal-engine-proof')) as engine:
                    with self.assertRaisesRegex(RuntimeError, 'required-normal-engine-proof'):
                        p._check_result_uncached(self.receipt, comparison_context=context, _rejected_attempt=negative)
                    engine.assert_called_once_with(self.output, row)
        row['status'] = 'cancelled'; p.save_json(self.receipt, row)
        with self.assertRaisesRegex(p.Rejected, 'completed-negative routing contract'):
            p.check_rejected_routing_attempt(self.receipt, comparison_context=self.context)

    def test_direct_comparison_interrupt_publishes_durable_cancelled_receipt(self):
        # Reuse the existing AST publication-control pattern: the interrupt
        # handler and entire following publication tail are exact production
        # nodes. Only the expensive route body is an authored worker interrupt.
        # The durable process row is synthetic, never Native cleanup evidence.
        source = Path(p.__file__)
        producer = next(node for node in ast.parse(source.read_bytes()).body
                        if isinstance(node, ast.FunctionDef) and node.name == '_route')
        guarded = [node for node in producer.body if isinstance(node, ast.Try)
                   and any(isinstance(handler.type, ast.Name)
                           and handler.type.id == 'KeyboardInterrupt'
                           for handler in node.handlers)]
        self.assertEqual(len(guarded), 1)
        index = producer.body.index(guarded[0])
        interrupt = ast.parse('try:\n    interrupt_worker()\nexcept KeyboardInterrupt:\n    pass\n').body[0]
        interrupt.handlers = copy.deepcopy(guarded[0].handlers)
        wrapper = ast.FunctionDef(name='publication_control',
            args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
            body=[interrupt, *copy.deepcopy(producer.body[index + 1:])], decorator_list=[])
        module = ast.fix_missing_locations(ast.Module(body=[wrapper], type_ignores=[]))
        process = dict(name='engine', cwd=str(self.output), status='cancelled',
                       exit_code=-15, cleanup_complete=True, wall_seconds=0.,
                       cpu_seconds=0., monitor_cpu_seconds=0., max_rss_bytes=0)
        p.save_json(self.output / 'engine-process.json', process)

        def interrupt_worker():
            raise KeyboardInterrupt('authored completed-worker cancellation')

        for context in (self.context, None):
            with self.subTest(explicit_comparison=context is not None):
                self.receipt.unlink(missing_ok=True)
                report = copy.deepcopy(self.data)
                report.update(accepted=False, status='validator_error')
                started = time.monotonic()
                job = SimpleNamespace(steps=[copy.deepcopy(process)], started=started,
                                      cpu_started=time.process_time(), deadline=started + 120, _inherited_budget=None)
                job.remaining=lambda:p.Job.remaining(job)
                namespace = dict(vars(p))
                namespace.update(report=report, job=job, output=self.output,
                    source=self.source, seconds=120, comparison=cmp,
                    comparison_context=context, _improve_context=None, _improve_budget=None,
                    _preferences=None, class_requirement=None,
                    native_toolchain=None, experimental_schematic_parity=False,
                    _fanout_enabled=None, engine_profile='tuned',
                    operation_children=f.child_cpu(), interrupt_worker=interrupt_worker)
                exec(compile(module, str(source), 'exec'), namespace)
                if context is None:
                    # Preserve the pre-existing legacy no-preferences behavior.
                    with self.assertRaises(KeyboardInterrupt):namespace['publication_control']()
                    self.assertFalse(self.receipt.exists())
                    continue
                result = namespace['publication_control']()
                durable = f.read_json(self.receipt)
                self.assertEqual(result, durable)
                self.assertEqual(durable['status'], 'cancelled')
                self.assertEqual(durable['reason'], 'interrupted route')
                self.assertIs(durable['accepted'], False)
                self.assertIs(durable['production_admitted'], False)
                self.assertIs(durable['whole_project_drc_clean'], False)
                self.assertEqual(durable['steps'], [process])
                self.assertEqual(f.read_json(self.output / 'engine-process.json'), process)
                self.assertIn('control_child_cpu_seconds', durable)
                self.assertTrue(cmp.check_record(self.output, durable, self.context))
                with self.assertRaisesRegex(p.Rejected, 'explicit caller context'):
                    p.check_result(self.receipt)
                self.assertEqual(p.tree_hash(self.project), self.hashes)
                self.assertNotIn('candidate', durable)
                self.assertFalse((self.output / 'export').exists())

    @unittest.skipUnless(hasattr(os, 'chflags') and hasattr(stat, 'UF_IMMUTABLE'),
                         'actual owned Mac PRL metadata control required')
    def test_final_comparison_tool_read_cannot_escape_prl_metadata_replay(self):
        # Compile the exact final reader tail, as existing publication controls
        # do. This isolates its ordering, not complete Native acceptance. The
        # shared PRL guard/replay and actual owned file flags remain real.
        producer = next(node for node in ast.parse(Path(p.__file__).read_bytes()).body
                        if isinstance(node, ast.FunctionDef) and node.name == '_check_result_uncached')
        start = next(index for index, node in reversed(list(enumerate(producer.body)))
                     if isinstance(node, ast.If) and isinstance(node.test, ast.Name)
                     and node.test.id == 'preferences_guarded')
        wrapper = ast.FunctionDef(name='reader_final_control',
            args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
            body=copy.deepcopy(producer.body[start:]), decorator_list=[])
        module = ast.fix_missing_locations(ast.Module(body=[wrapper], type_ignores=[]))
        inputs = self.output / 'final-drc-input'; inputs.mkdir()
        board = inputs / self.source.name; shutil.copy2(self.source, board)
        prl = board.with_suffix('.kicad_prl'); prl.write_text('{"owned":"unchanged"}\n')
        owner = {}; h.capture_destination(owner, self.output)
        before = p.tree_hash(inputs)
        with ls.preserve(prl, self.output, owner) as event:pass
        binding = dict(input=str(board), saved=False, before=before,
                       local_settings_policy=ls.JOB_POLICY)
        process = dict(argv=[str(c.CLI), 'pcb', 'drc', str(board)], cleanup_complete=True,
                       local_settings_policy=ls.JOB_POLICY, local_settings_protection=event)
        raw, flags = prl.read_bytes(), prl.stat().st_flags
        self.assertEqual(flags, 0)
        for fault in (False, True):
            state = {'tool_reads': 0, 'mutated': False}
            def manifest():
                state['tool_reads'] += 1
                if fault and not state['mutated']:
                    os.chflags(prl, stat.UF_IMMUTABLE, follow_symlinks=False)
                    state['mutated'] = True
                return copy.deepcopy(self.tools)
            namespace = dict(vars(p))
            namespace.update(path=self.receipt, data=self.data, source=self.source,
                result={'current': True, 'applied': False}, is_comparison=True,
                is_improve_child=False, is_improve_parent=False,
                _improve_context=None, _improve_budget=None,
                comparison=cmp, comparison_context=self.context, _rejected_attempt=False,
                preferences_guarded=True, bounded_inventory=pc.inventory, bounded_bytes=pc.read_bytes,
                bounded_evidence=pc.evidence_inventory,
                readback_material=pc.evidence_inventory(self.output),
                comparison_material=p.tree_hash(self.output), receipt_digest=p.sha(self.receipt),
                binding=binding, process=process, check_event=ls.check_event,
                # Restrict the eventual shared all-worker replay seam to this
                # one actual captured event; no synthetic DRC is called real.
                check_experimental_local_settings=lambda *args: ls.check_event(self.output, binding, process))
            exec(compile(module, str(p.__file__), 'exec'), namespace)
            try:
                with self.subTest(late_tool_metadata_fault=fault), patch.object(p, 'tool_manifest', side_effect=manifest):
                    if fault:
                        try:
                            current = namespace['reader_final_control']()
                        except p.Rejected as exc:
                            self.assertRegex(str(exc), 'flags')
                        else:
                            self.assertTrue(state['mutated'])
                            self.assertEqual(prl.stat().st_flags, stat.UF_IMMUTABLE)
                            self.assertEqual(p.tree_hash(self.output), namespace['comparison_material'])
                            self.fail('Late tool changed owned PRL flags with unchanged bytes; '
                                      'production final reader tail returned ' + repr(current))
                    else:
                        self.assertTrue(namespace['reader_final_control']()['current'])
                self.assertGreater(state['tool_reads'], 0)
                self.assertEqual(state['mutated'], fault)
                self.assertEqual(prl.read_bytes(), raw)
            finally:
                os.chflags(prl, flags, follow_symlinks=False)

    def test_production_consumers_and_sidecar_alias_refuse(self):
        with self.assertRaises(p.Rejected):p.check_experimental_route(self.data)
        self.assertFalse(self.data['production_admitted'])
        alias = self.output / 'outside.json'; alias.write_text(json.dumps(self.context.record()))
        (self.output / cmp.SIDECAR).unlink(); (self.output / cmp.SIDECAR).symlink_to(alias)
        with self.assertRaises(ValueError):cmp.check_record(self.output, self.data, self.context)

    def test_sidecar_is_bounded_and_strict_even_with_a_reauthored_digest(self):
        sidecar = self.output / cmp.SIDECAR
        sidecar.write_bytes(b' ' * (512 * 1024 + 1))
        with self.assertRaises(ValueError):cmp.check_record(self.output, self.data, self.context)
        sidecar.write_text('{"policy":"first","policy":"second"}')
        self.data['comparison_route']['sha256'] = p.sha(sidecar)
        with self.assertRaises(p.Rejected):cmp.check_record(self.output, self.data, self.context)

    def test_bind_and_retained_readback_recheck_source_after_authorization(self):
        self.authorize()
        (self.output / cmp.SIDECAR).unlink()
        self.source.with_suffix('.kicad_pro').write_text('{"changed_after_intake": true}\n')
        with self.assertRaises(p.Rejected):cmp.bind(self.output, self.data, self.context)
        with self.assertRaises(p.Rejected):p.check_result(self.receipt, comparison_context=self.context)
        with self.assertRaises(p.Rejected):p.check_rejected_routing_attempt(self.receipt, comparison_context=self.context)


if __name__ == '__main__':unittest.main()
