"""Constructed admission/source-proof controls; no Native qualification."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import config as c, pipeline as p, sexpr as sx
from autorouter.__main__ import preview
from tests.test_default_targets import fixtures


class TunedLowSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root/'snapshot'/'owned.kicad_pcb'
        self.source.parent.mkdir()
        _, _, self.project, self.original = fixtures()
        self.write_source()
        self.code = self.root/'code'/'pipeline.py'
        self.code.parent.mkdir()
        self.code.write_bytes(Path(p.__file__).read_bytes())
        self.version = patch.object(c, 'NATIVE_VERSION', '10.0.7')
        self.version.start(); self.addCleanup(self.version.stop)
        self.data = dict(schema=1, status='routing_accepted', accepted=True,
            baseline='B2_tuned', source=str(self.source),
            scope='whole_board_unlocked_routing', adapter='both',
            engine_profile='tuned', scoring_variant='via_low',
            tools={'implementation_sha256': {'autorouter/pipeline.py': p.sha(self.code)}})
        self.capture()

    def write_source(self):
        sx.write(self.source, self.original)
        self.source.with_suffix('.kicad_pro').write_text(json.dumps(self.project))
        self.source.with_suffix('.kicad_sch').write_text('(kicad_sch (version 20260206))\n')

    def capture(self):
        self.record = p.native7_tuned_low_source_record(self.source, self.data['scope'])
        self.proof = self.root/'native7-tuned-low-source.json'
        self.proof.write_text(json.dumps(self.record))
        self.data.update(source_hashes=self.record['source_hashes'],
            task_sha256=self.record['task_sha256'],
            native7_tuned_low_source=dict(policy=p.NATIVE7_TUNED_LOW_POLICY,
                file=self.proof.name, sha256=p.sha(self.proof)))

    def check(self, **kwargs):
        return p.check_native7_tuned_low_evidence(self.root, self.data, **kwargs)

    def test_only_exact_explicit_native7_configuration_is_added(self):
        for scope in ('whole_board_unlocked_routing', 'partial_completion'):
            p.require_native_scope(scope=scope, profile='tuned', scoring='via_low')
        for wrong in ({'scoring': None}, {'scoring': 'via_default'}, {'scoring': 'via_high'},
                      {'profile': 'standard'}, {'profile': 'completion-only'}, {'adapter': 'none'},
                      {'adapter': 'graphics'}, {'layers': ['F.Cu']}, {'scope': 'selected_nets'},
                      {'guidance': 'board-floors-v1'}, {'purpose': 'improve'},
                      {'purpose': 'thermal-recovery'}):
            with self.subTest(wrong=wrong), self.assertRaises(p.Rejected):
                p.require_native_scope(**{**dict(profile='tuned', scoring='via_low'), **wrong})
        p.require_native_scope()
        p.require_native_scope(scoring='via_high')
        p.require_native_scope(scope='selected_nets', profile='completion-only')
        p.require_native_scope(purpose='improve', profile='tuned')
        with patch.object(c, 'NATIVE_VERSION', '10.0.0'):
            p.require_native_scope(profile='tuned', scoring='via_low')

    def test_both_formats_and_scopes_have_rederived_source_task_proofs(self):
        for version in ('20241229', '20260206'):
            for scope in ('whole_board_unlocked_routing', 'partial_completion'):
                sx.one(self.original, 'version')[1] = version
                self.write_source(); self.data['scope'] = scope; self.capture()
                before = p.tree_hash(self.source.parent)
                self.assertEqual(self.check(), self.record)
                self.assertEqual(self.record['board_format'], version)
                self.assertEqual(p.tree_hash(self.source.parent), before)

    def test_source_contract_refuses_other_formats_classes_layers_and_schematics(self):
        for mutation in ('version', 'four', 'class', 'assignment', 'pattern', 'flag',
                         'hierarchy', 'missing_project', 'missing_schematic', 'child_flag'):
            self.write_source()
            child = self.source.parent/'child.kicad_sch'
            if child.exists(): child.unlink()
            tree = sx.read(self.source); project = copy.deepcopy(self.project)
            sch = self.source.with_suffix('.kicad_sch')
            if mutation == 'version': sx.one(tree, 'version')[1] = '20240108'
            elif mutation == 'four': sx.one(tree, 'layers').insert(2, ['4', '"In1.Cu"', 'signal'])
            elif mutation == 'class': project['net_settings']['classes'][0]['name'] = 'OTHER'
            elif mutation == 'assignment': project['net_settings']['netclass_assignments'] = {'DATA': 'Default'}
            elif mutation == 'pattern': project['net_settings']['netclass_patterns'] = [{'pattern': '*', 'netclass': 'Default'}]
            elif mutation == 'flag': sch.write_text('(kicad_sch (version 20260206) (netclass_flag))')
            elif mutation == 'hierarchy': sch.write_text('(kicad_sch (version 20260206) (sheet))')
            elif mutation == 'child_flag': child.write_text('(kicad_sch (version 20260206) (netclass_flag))')
            sx.write(self.source, tree)
            self.source.with_suffix('.kicad_pro').write_text(json.dumps(project))
            if mutation == 'missing_project': self.source.with_suffix('.kicad_pro').unlink()
            if mutation == 'missing_schematic': sch.unlink()
            with self.subTest(mutation=mutation), self.assertRaises(p.Rejected):
                p.native7_tuned_low_source_record(self.source, 'whole_board_unlocked_routing')

    def test_malformed_project_and_scope_are_not_implicit_default(self):
        for value in (None, [], False, {}, {'net_settings': None}, {'net_settings': []},
                      {'net_settings': {}}, {'net_settings': {'classes': None}},
                      {'net_settings': {'classes': [False]}}):
            self.source.with_suffix('.kicad_pro').write_text(json.dumps(value))
            with self.subTest(value=value), self.assertRaises(p.Rejected):
                p.native7_tuned_low_source_record(self.source, 'whole_board_unlocked_routing')
        self.write_source()
        for scope in ('selected_nets', None, [], True):
            with self.subTest(scope=scope), self.assertRaises(p.Rejected):
                p.native7_tuned_low_source_record(self.source, scope)

    def test_producer_and_preview_refuse_before_any_job_or_native(self):
        self.source.with_suffix('.kicad_sch').unlink()
        out = self.root/'never-created'
        with patch.object(p, 'Job') as worker, patch.object(p, 'check_storage') as storage:
            with self.assertRaises(p.Rejected):
                p.route(self.source, out, 90, adapter='both', engine_profile='tuned', scoring_variant='via_low')
            worker.assert_not_called(); storage.assert_not_called()
        with patch.object(p, 'preflight') as preflight:
            with self.assertRaises(p.Rejected):
                preview(self.source, overrides=dict(profile='tuned', scoring_preference='via_low'))
            preflight.assert_not_called()
        self.assertFalse(out.exists())

    def test_preview_uses_closed_class_context_without_native(self):
        with patch.object(p, 'preflight', return_value=self.original) as preflight:
            result = preview(self.source, overrides=dict(profile='tuned', scoring_preference='via_low'))
        self.assertFalse(result['native_validation_performed'])
        self.assertIsNone(preflight.call_args.kwargs['class_context'])

    def test_fanout_override_refuses_before_storage_or_native(self):
        with patch.object(p, 'Job') as worker, patch.object(p, 'check_storage') as storage:
            with self.assertRaisesRegex(p.Rejected, 'ordinary unmodified Route settings'):
                p.route(self.source, self.root/'never-created', 90, adapter='both',
                        engine_profile='tuned', scoring_variant='via_low', _fanout_enabled=False)
            storage.assert_not_called(); worker.assert_not_called()

    def test_marker_or_sidecar_deletion_cannot_downgrade_mode(self):
        for mutation in ('marker', 'sidecar', 'both'):
            self.capture()
            if mutation in ('marker', 'both'): self.data.pop('native7_tuned_low_source')
            if mutation in ('sidecar', 'both'): self.proof.unlink()
            with self.subTest(mutation=mutation), self.assertRaises((p.Rejected, OSError)):
                self.check()

    def test_source_and_rehashed_record_changes_refuse(self):
        for field, value in [('policy', 'other'), ('scope', 'partial_completion'),
                             ('protected_count', 42), ('task_sha256', '0'*64),
                             ('source_hashes', {})]:
            self.capture(); wrong = copy.deepcopy(self.record); wrong[field] = value
            self.proof.write_text(json.dumps(wrong))
            self.data['native7_tuned_low_source']['sha256'] = p.sha(self.proof)
            with self.subTest(field=field), self.assertRaises(p.Rejected): self.check()
        self.capture()
        with self.source.with_suffix('.kicad_sch').open('a') as stream: stream.write('\n')
        with self.assertRaises(p.Rejected): self.check()

    def test_captured_capability_cannot_be_deleted_rehashed_or_nested(self):
        original = self.code.read_text()
        literal = "NATIVE7_TUNED_LOW_POLICY='native7-tuned-low-sole-default-v1'"
        for mutation in ('missing', 'unknown', 'dynamic', 'nested', 'duplicate', 'old_comparison'):
            code = original
            if mutation == 'missing': code = code.replace(literal, '# missing capability')
            elif mutation == 'unknown': code = code.replace(literal, "NATIVE7_TUNED_LOW_POLICY='unknown'")
            elif mutation == 'dynamic': code = code.replace(literal, "NATIVE7_TUNED_LOW_POLICY=str('native7-tuned-low-sole-default-v1')")
            elif mutation == 'nested': code = code.replace(literal, 'if True:\n    '+literal)
            elif mutation == 'duplicate': code = code.replace(literal, literal+'\n'+literal)
            else: code = "COMPARISON_ROUTE_POLICY='selected-native7-fixed-comparison-v2'\n"
            self.code.write_text(code)
            self.data['tools']['implementation_sha256']['autorouter/pipeline.py'] = p.sha(self.code)
            with self.subTest(mutation=mutation), self.assertRaises(p.Rejected): self.check()

    def test_foreign_modes_cannot_carry_this_proof_and_comparison_is_not_upgraded(self):
        for kwargs in ({'ordinary': False}, {'native_toolchain': object()}, {'input_policy': 'board-floors-v1'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(p.Rejected): self.check(**kwargs)
        for key, value in [('engine_profile', 'standard'), ('scoring_variant', None),
                           ('strategy', 'native_validated_zone_net_pruning'),
                           ('production_admitted', False), ('engine_fanout_override', False)]:
            saved = copy.deepcopy(self.data); self.data[key] = value
            with self.subTest(key=key), self.assertRaises(p.Rejected): self.check()
            self.data = saved
        self.data.pop('native7_tuned_low_source'); self.proof.unlink()
        self.assertIsNone(self.check(ordinary=False))

    def test_central_reader_requires_proof_before_engine_or_native_evidence(self):
        self.data.pop('native7_tuned_low_source'); self.proof.unlink()
        receipt = self.root/'result.json'; receipt.write_text(json.dumps(self.data))
        with patch.object(c, 'current_native_selection', return_value={'version': '10.0.7'}), \
                patch.object(p, 'check_normal_engine_provenance') as engine:
            with self.assertRaises((p.Rejected, OSError)):
                p._check_result_uncached(receipt)
            engine.assert_not_called()


if __name__ == '__main__': unittest.main()
