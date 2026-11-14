"""Pure authored adapter controls; not Native export or routing evidence."""
import copy
import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from autorouter import adapter as a, sexpr as sx
from autorouter.pipeline import Rejected
from experiments.selected_unselected_plane_v1 import controls as fixture, policy


OBSTACLES = [{'layer': 'F.Cu', 'bbox_mm': [.01, .02, .03, .04]}]
GOLDEN = {  # Captured from pre-change adapter504f544f; complete bytes/receipt.
    'graphics': ('2f47237035974fecd98f13c5be02bb468902b22bdc28b7891eb55e43b70b50cf',
                 'cda2b0c29b114569d3e9063c7586c65ed6580efa79989e63ca2e4ccce3279686'),
    'planes': ('8396555cd26b3807ca5d113b8b9f87316c065141ce7c7b9ec49e836b1dab4827',
               '97965f18fb77c5a91270fa4e01cf5da39574f30fbc68bfb186953fc2dc2af9aa'),
    'both': ('8d64810c008ad8302b89ed87d253fb9cfbb73e8ff33692da4bd6868cdafd1576',
             'b63fc8bd52d420be618f40350cfdd3d4f0c187f647dedb084e0d987b04b795d2')}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def transport(names=None, *, source=None, dsn=None):
    source = fixture.source() if source is None else source
    dsn = fixture.dsn() if dsn is None else dsn
    names = ['ACTIVE'] if names is None else names
    return dict(source_bytes=source, selected_names=names, context=policy.capture(source, dsn, names))


class SelectedPlaneAdapterTests(unittest.TestCase):
    def test_none_preserves_prechange_bytes_and_entire_receipt_in_every_mode(self):
        for mode, (output_hash, receipt_hash) in GOLDEN.items():
            with self.subTest(mode=mode), patch.object(policy, 'apply', side_effect=AssertionError('No policy call')):
                omitted = a.adapt_bytes(fixture.dsn(), mode, OBSTACLES)
                explicit = a.adapt_bytes(fixture.dsn(), mode, OBSTACLES, plane_transport=None)
                self.assertEqual(omitted, explicit)
                output, record = explicit
                self.assertEqual(sha(output), output_hash)
                self.assertEqual(sha(json.dumps(record, sort_keys=True, separators=(',', ':'),
                                               ensure_ascii=False).encode()), receipt_hash)

    def test_mixed_planes_preserve_order_graphics_and_every_nonplane_semantic(self):
        raw = fixture.dsn(); request = transport(); before = copy.deepcopy(request)
        for mode in ('planes', 'both'):
            with self.subTest(mode=mode):
                output, record = a.adapt_bytes(raw, mode, OBSTACLES, plane_transport=request)
                old = a._parse_dsn(raw.decode()); expected = copy.deepcopy(old)
                structure = sx.one(expected, 'structure')
                structure[:] = [row for row in structure if not (
                    type(row) is list and row and row[0] == 'plane' and sx.unquote(row[1]) == 'ACTIVE')]
                if mode == 'both':
                    graphics, unused = a.adapt_bytes(raw, 'graphics', OBSTACLES)
                    structure.extend([row for row in sx.children(sx.one(a._parse_dsn(graphics.decode()), 'structure'), 'keepout')
                                      if sx.unquote(row[1]).startswith(a._KEEP_OUT_PREFIX)])
                self.assertEqual(a._parse_dsn(output.decode()), expected)
                self.assertEqual(sx.children(sx.one(expected, 'structure'), 'plane'),
                    [row for row in sx.children(sx.one(old, 'structure'), 'plane') if sx.unquote(row[1]) != 'ACTIVE'])
                self.assertEqual((record['planes_removed'], record['planes_retained']), (2, 3))
                self.assertEqual(record['graphics_keepouts_added'], int(mode == 'both'))
                self.assertEqual(record['plane_transport'], policy.apply(request['source_bytes'], raw,
                    request['selected_names'], request['context'])[1])
                self.assertEqual(record['input_sha256'], sha(raw)); self.assertEqual(record['output_sha256'], sha(output))
                self.assertEqual(record['classification'], 'experimental_selected_unselected_plane_adapter')
                self.assertIs(record['experimental'], True)
                for flags in (record, record['plane_transport']):
                    for key in ('native_export_verified', 'original_design_validated', 'routing_accepted'):
                        self.assertIs(flags[key], False)
        self.assertEqual(request, before)

    def test_selection_is_explicit_not_purpose_and_legacy_modern_identity_stay_coherent(self):
        for modern in (False, True):
            request = transport(['GND'], source=fixture.source(modern))
            output, record = a.adapt_bytes(fixture.dsn(), 'planes', [], plane_transport=request)
            planes = sx.children(sx.one(a._parse_dsn(output.decode()), 'structure'), 'plane')
            self.assertEqual([sx.unquote(row[1]) for row in planes], ['ACTIVE', 'quiet reference', 'ACTIVE', 'quiet reference'])
            self.assertEqual(record['planes_removed'], 1)
            self.assertEqual(record['plane_transport']['selection_binding']['source_net_mapping'],
                             'modern_names' if modern else 'legacy_table')

    def test_strict_input_shape_and_incompatible_modes_refuse(self):
        for fault in ('not-dict', 'missing', 'extra', 'source-type', 'names-tuple', 'name-type', 'context-type'):
            value = transport()
            if fault == 'not-dict': value = []
            elif fault == 'missing': value.pop('context')
            elif fault == 'extra': value['native_export_verified'] = True
            elif fault == 'source-type': value['source_bytes'] = bytearray(value['source_bytes'])
            elif fault == 'names-tuple': value['selected_names'] = ('ACTIVE',)
            elif fault == 'name-type': value['selected_names'] = [True]
            else: value['context'] = []
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                a.adapt_bytes(fixture.dsn(), 'both', [], plane_transport=value)
        for mode in ('graphics', 'unknown'):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                a.adapt_bytes(fixture.dsn(), mode, [], plane_transport=transport())

    def test_changed_source_DSN_selection_or_context_never_falls_back(self):
        for fault in ('source', 'dsn', 'order', 'action', 'authority', 'missing', 'extra'):
            request = transport(['ACTIVE', 'GND']); raw = fixture.dsn()
            if fault == 'source': request['source_bytes'] += b'\n'
            elif fault == 'dsn': raw += b'\n'
            elif fault == 'order': request['selected_names'].reverse()
            elif fault == 'action': request['context']['planes'][0]['action'] = 'retain'
            elif fault == 'authority': request['context']['native_export_verified'] = True
            elif fault == 'missing': request['context'].pop('source_zone_census')
            else: request['context']['approval'] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                a.adapt_bytes(raw, 'both', OBSTACLES, plane_transport=request)

    def test_malformed_planes_and_incoherent_source_nets_refuse(self):
        request = transport()
        for before, after in [(b'(plane ACTIVE (polygon', b'(plane ACTIVE extra (polygon'),
                              (b'(plane GND', b'(plane UNKNOWN'),
                              (b'(polygon F.Cu 0 0 0 1000', b'(circle F.Cu 0 0 0 1000'),
                              (b'(polygon F.Cu 0 0 0 1000', b'(polygon In1.Cu 0 0 0 1000'),
                              (b'(polygon F.Cu 0 0 0 1000', b'(polygon F.Cu 1 0 0 1000')]:
            with self.subTest(after=after), self.assertRaises(ValueError):
                a.adapt_bytes(fixture.dsn().replace(before, after, 1), 'planes', [], plane_transport=request)
        request['source_bytes'] = request['source_bytes'].replace(b'(net 1 "ACTIVE")', b'(net 1 "wrong")', 1)
        with self.assertRaisesRegex(Rejected, 'terminal differs from legacy net table'):
            a.adapt_bytes(fixture.dsn(), 'both', [], plane_transport=request)

    def test_bounds_and_cyclic_context_refuse_without_new_authority(self):
        for fault in ('source-size', 'context-size', 'context-cycle', 'names-size'):
            request = transport()
            if fault == 'source-size': request['source_bytes'] = b'x' * (policy.MAX_BYTES + 1)
            elif fault == 'context-size': request['context']['extra'] = 'x' * policy.MAX_CONTEXT_BYTES
            elif fault == 'context-cycle': request['context']['self'] = request['context']
            else: request['selected_names'] = ['ACTIVE'] * 65
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                a.adapt_bytes(fixture.dsn(), 'both', [], plane_transport=request)

    def test_no_planes_or_all_selected_are_explicit_experimental_zero_retention(self):
        tree = a._parse_dsn(fixture.dsn().decode()); structure = sx.one(tree, 'structure')
        structure[:] = [row for row in structure if not (type(row) is list and row and row[0] == 'plane')]
        for raw, names in [(fixture.dsn(), ['ACTIVE', 'quiet reference', 'GND']),
                           (a._dump_dsn(tree).encode(), ['ACTIVE'])]:
            request = transport(names, dsn=raw)
            output, record = a.adapt_bytes(raw, 'planes', [], plane_transport=request)
            self.assertEqual(output, a.adapt_bytes(raw, 'planes', [])[0])
            self.assertEqual(record['planes_retained'], 0); self.assertTrue(record['experimental'])

    def test_independent_expected_AST_refuses_nonplane_or_retained_plane_changes(self):
        request = transport(); raw = fixture.dsn(); plane_output, plane_record = policy.apply(
            request['source_bytes'], raw, request['selected_names'], request['context'])
        for fault in ('dimension', 'wiring', 'retained-plane', 'nested-unknown'):
            tree = a._parse_dsn(plane_output.decode())
            if fault == 'dimension': sx.one(sx.one(tree, 'structure'), 'rule')[1][1] = '199'
            elif fault == 'wiring': sx.one(tree, 'wiring').clear()
            elif fault == 'retained-plane': sx.children(sx.one(tree, 'structure'), 'plane')[0][2][3] = '999'
            else: sx.one(sx.one(tree, 'structure'), 'unknown').clear()
            with self.subTest(fault=fault), patch.object(policy, 'apply', return_value=(a._dump_dsn(tree).encode(), plane_record)), \
                    self.assertRaisesRegex(ValueError, 'protected semantics'):
                a.adapt_bytes(raw, 'both', [], plane_transport=request)

    def test_atomic_file_API_forwards_variant_and_refuses_stale_context_before_write(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            path = Path(folder) / 'task.dsn'; path.write_bytes(fixture.dsn()); path.chmod(0o640)
            request = transport(); expected, record = a.adapt_bytes(fixture.dsn(), 'both', OBSTACLES, plane_transport=request)
            self.assertEqual(a.adapt_dsn(path, 'both', OBSTACLES, plane_transport=request), record)
            self.assertEqual(path.read_bytes(), expected); self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
            path.write_bytes(fixture.dsn()); request['context']['native_export_verified'] = True
            with self.assertRaises(ValueError): a.adapt_dsn(path, 'both', [], plane_transport=request)
            self.assertEqual(path.read_bytes(), fixture.dsn()); self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)


if __name__ == '__main__':
    unittest.main()
