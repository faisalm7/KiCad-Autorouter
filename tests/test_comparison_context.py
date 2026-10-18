"""Caller-bound comparison controls; authored files, never Native routing proof.

The tools/source identity provider is stubbed. Captured source policy, bounded
file readers, context sealing, exact engine settings and dispatch are real.
No test executes KiCad, Java, Git, a sandbox or an installed workflow.
"""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from autorouter import comparison as cmp, config as c, pipeline as p
from autorouter import placement_clearance as pc, provenance as pv

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
        for negative in (False, True):
            row = copy.deepcopy(self.data)
            row.update(accepted=not negative, status='drc_rejected' if negative else 'routing_accepted')
            p.save_json(self.receipt, row)
            with self.subTest(negative=negative), patch.object(p, 'check_normal_engine_provenance', side_effect=RuntimeError('required-normal-engine-proof')) as engine:
                with self.assertRaisesRegex(RuntimeError, 'required-normal-engine-proof'):
                    p._check_result_uncached(self.receipt, comparison_context=self.context, _rejected_attempt=negative)
                engine.assert_called_once_with(self.output, row)
        row['status'] = 'cancelled'; p.save_json(self.receipt, row)
        with self.assertRaisesRegex(p.Rejected, 'completed-negative routing contract'):
            p.check_rejected_routing_attempt(self.receipt, comparison_context=self.context)

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
