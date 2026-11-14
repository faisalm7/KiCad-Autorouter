"""Operation-cache dispatch/freshness controls, never actual Native acceptance.

The full-validator seam is explicit. Separate witness tests exercise real small
filesystem graphs; installation and Native workflow remain required evidence.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import pipeline as p, placement, placement_intent, gui


class PlacementScopedReadback(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.out = self.root/'route'; self.out.mkdir()
        self.source = self.root/'source'/'board.kicad_pcb'
        self.source.parent.mkdir(); self.source.write_bytes(b'owned source')
        (self.root/'toolchain.lock.json').write_text('{}')
        self.external = self.root/'retained-proof'; self.external.write_bytes(b'owned proof')
        self.qualification = self.root/'.runs'/'qualification'; self.qualification.mkdir(parents=True)
        self.descriptor = dict(schema=1, kind=placement.ORIGIN_KIND,
            qualification=str(self.qualification), result_sha256='a'*64,
            binding_sha256='b'*64, evidence_sha256='c'*64)
        self.data = dict(schema=1, status='routing_accepted', accepted=True,
                         source=str(self.source), placement_origin=self.descriptor)
        self.receipt = self.out/'result.json'; self.save()
        (self.out/'placement-origin.json').write_text(json.dumps(self.descriptor))
        for context in (patch.object(p.c, 'ROOT', self.root),
                        patch.object(p.c, 'current_native_selection', return_value=None),
                        patch.object(p, 'tool_manifest', return_value={'files': {}, 'implementation_sha256': {}}),
                        patch.object(placement, 'readback_origin_witness', side_effect=self.witness)):
            context.start(); self.addCleanup(context.stop)

    def save(self):
        self.receipt.write_text(json.dumps(self.data))

    def witness(self, *_args):
        return ('placement-origin-readback-v1', self.external.read_bytes())

    def validated(self, _path):
        if self.external.read_bytes() != b'owned proof':
            raise p.Rejected('test full checker rejects changed external proof')
        return dict(current=True, nested={'value': 1})

    def test_complete_first_read_then_detached_reuse_and_context_exit(self):
        with patch.object(p, '_check_result_uncached', side_effect=self.validated) as full:
            with p.validation_readback_session():
                first = p.check_result(self.receipt); first['nested']['value'] = 2
                self.assertEqual(p.check_result(self.receipt)['nested']['value'], 1)
                self.assertEqual(full.call_count, 1)
            p.check_result(self.receipt)
            self.assertEqual(full.call_count, 2)

    def test_external_origin_proof_change_reaches_full_checker_and_clears(self):
        with patch.object(p, '_check_result_uncached', side_effect=self.validated) as full, p.validation_readback_session():
            p.check_result(self.receipt)
            self.external.write_bytes(b'changed one')
            with self.assertRaisesRegex(p.Rejected, 'changed external proof'): p.check_result(self.receipt)
            self.assertEqual(full.call_count, 2)
            self.assertFalse(p._readback_session.get()['entries'])

    def test_unknown_or_mutable_witness_never_gains_cache_eligibility(self):
        for value in (None, (), ('other',), ['placement-origin-readback-v1'],
                      ('placement-origin-readback-v1', [])):
            with self.subTest(value=value), patch.object(placement, 'readback_origin_witness', return_value=value), \
                    patch.object(p, '_check_result_uncached', side_effect=self.validated) as full, p.validation_readback_session():
                p.check_result(self.receipt); p.check_result(self.receipt)
                self.assertEqual(full.call_count, 2)
                self.assertFalse(p._readback_session.get()['entries'])

    def test_unfamiliar_graph_refusal_falls_back_without_weakening_full_check(self):
        with patch.object(placement, 'readback_origin_witness', side_effect=ValueError('unfamiliar graph')), \
                patch.object(p, '_check_result_uncached', side_effect=p.Rejected('actual full refusal')) as full, \
                p.validation_readback_session():
            with self.assertRaisesRegex(p.Rejected, 'actual full refusal'): p.check_result(self.receipt)
            self.assertEqual(full.call_count, 1)
            self.assertFalse(p._readback_session.get()['entries'])

    def test_changed_source_policy_and_same_class_method_force_new_full_read(self):
        replacements = [(placement_intent, 'current'), (gui.SourceGuard, '__init__'),
                        (gui.SourceGuard, '__post_init__'), (gui.SourceGuard, 'check')]
        for owner, name in replacements:
            with self.subTest(name=name), patch.object(p, '_check_result_uncached', side_effect=self.validated) as full, \
                    p.validation_readback_session():
                p.check_result(self.receipt)
                with patch.object(owner, name, wraps=getattr(owner, name)):
                    p.check_result(self.receipt)
                self.assertEqual(full.call_count, 2)

    def test_source_and_routing_files_are_still_in_the_shared_witness(self):
        for target in (self.source, self.out/'new-file'):
            with self.subTest(target=target), patch.object(p, '_check_result_uncached', side_effect=self.validated) as full, \
                    p.validation_readback_session():
                p.check_result(self.receipt)
                target.write_bytes(b'new unchanged-semantics test bytes')
                p.check_result(self.receipt)
                self.assertEqual(full.call_count, 2)

    def test_late_uncached_mutation_never_populates(self):
        def mutate(path):
            value = self.validated(path); self.external.write_bytes(b'changed one'); return value
        with patch.object(p, '_check_result_uncached', side_effect=mutate), p.validation_readback_session():
            with self.assertRaisesRegex(p.Rejected, 'during full readback'): p.check_result(self.receipt)
            self.assertFalse(p._readback_session.get()['entries'])

    def test_late_cached_witness_change_refuses_and_clears(self):
        calls = [0]
        def change(*args):
            calls[0] += 1
            if calls[0] == 4: self.external.write_bytes(b'changed one')
            return self.witness(*args)
        with patch.object(placement, 'readback_origin_witness', side_effect=change), \
                patch.object(p, '_check_result_uncached', side_effect=self.validated), p.validation_readback_session():
            p.check_result(self.receipt)
            with self.assertRaisesRegex(p.Rejected, 'during cached readback'): p.check_result(self.receipt)
            self.assertFalse(p._readback_session.get()['entries'])

    def test_after_only_origin_callback_cannot_hide_shared_source_change(self):
        calls = [0]
        def change(*args):
            calls[0] += 1
            value = self.witness(*args)
            if calls[0] == 4: self.source.write_bytes(b'changed after old shared inventory')
            return value
        with patch.object(placement, 'readback_origin_witness', side_effect=change), \
                patch.object(p, '_check_result_uncached', side_effect=self.validated), p.validation_readback_session():
            p.check_result(self.receipt)
            with self.assertRaisesRegex(p.Rejected, 'during cached readback'): p.check_result(self.receipt)
            self.assertFalse(p._readback_session.get()['entries'])

    def test_after_only_origin_callback_cannot_hide_shared_policy_change(self):
        calls = [0]; original = p.CRITICAL_FINDINGS
        def change(*args):
            calls[0] += 1
            value = self.witness(*args)
            if calls[0] == 4: p.CRITICAL_FINDINGS = original | {'new-test-critical-finding'}
            return value
        try:
            with patch.object(placement, 'readback_origin_witness', side_effect=change), \
                    patch.object(p, '_check_result_uncached', side_effect=self.validated), p.validation_readback_session():
                p.check_result(self.receipt)
                with self.assertRaisesRegex(p.Rejected, 'during cached readback'): p.check_result(self.receipt)
                self.assertFalse(p._readback_session.get()['entries'])
        finally: p.CRITICAL_FINDINGS = original

    def test_comparison_improve_and_transformed_flags_keep_uncached_dispatch(self):
        for key in ('comparison_route', 'native_improve_child', 'experimental_route_policy',
                    'native7_default_target_basis', 'production_admitted'):
            self.data[key] = True; self.save()
            with self.subTest(key=key), patch.object(p, '_check_result_uncached', side_effect=self.validated) as full, \
                    p.validation_readback_session():
                p.check_result(self.receipt); p.check_result(self.receipt)
                self.assertEqual(full.call_count, 2)
                self.assertFalse(p._readback_session.get()['entries'])
            self.data.pop(key); self.save()


if __name__ == '__main__': unittest.main()
