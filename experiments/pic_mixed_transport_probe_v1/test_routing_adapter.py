"""Pure retained-evidence B1 controls; no native, JVM, or routing execution."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from autorouter import adapter as a, sexpr as sx
from experiments.pic_mixed_transport_probe_v1 import routing_adapter as r

ROOT = Path(__file__).resolve().parents[2]


class RoutingAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / 'evidence/pic-selective-routing-001/unrouted.dsn').read_bytes()
        context_raw = (ROOT / 'evidence/pic-mixed-transport-probe-005/context.json').read_bytes()
        if a._digest(cls.raw) != '29fac563a4675c1c3dacacc7cdaabe4e761e48221547f96fbdddd46b4ce817e9':
            raise ValueError('actual retained unrouted DSN changed')
        if a._digest(context_raw) != 'b4da59c31f10616c46b538a9fe00a722215f3d3444a6402853c7c1efc0bc8ac9':
            raise ValueError('actual retained native context changed')
        cls.context = json.loads(context_raw)

    def apply(self, raw=None, context=None):
        with tempfile.TemporaryDirectory(dir=ROOT / '.runs', prefix='adapter-unit-') as temp:
            path = Path(temp) / 'task.dsn'
            path.write_bytes(self.raw if raw is None else raw)
            receipt = r.apply(path, self.context if context is None else context)
            return path.read_bytes(), receipt

    def test_actual_adapter_and_complete_reverse_preserve_inputs(self):
        before = copy.deepcopy(self.context)
        with mock.patch.object(a, 'adapt_dsn', wraps=a.adapt_dsn) as actual_adapter:
            adapted, receipt = self.apply()
        actual_adapter.assert_called_once()
        self.assertEqual(actual_adapter.call_args.args[1], 'both')
        self.assertEqual(actual_adapter.call_args.args[2], [x['snapped'] for x in receipt['obstacles']])
        self.assertEqual(self.context, before)
        self.assertTrue(r.verify(self.raw, adapted, self.context, receipt))
        self.assertEqual(receipt['classification'], 'B1_adapter_only')
        self.assertEqual(receipt['adapter']['planes_removed'], 1)
        self.assertEqual(receipt['adapter']['graphics_keepouts_added'], 19)
        self.assertEqual(receipt['adapter']['net_pin_mapping']['nets'], 111)
        self.assertEqual(receipt['adapter']['net_pin_mapping']['pins'], 236)
        self.assertFalse(receipt['routing_executed']); self.assertFalse(receipt['routing_accepted'])
        original = a._parse_dsn(self.raw.decode()); final = a._parse_dsn(adapted.decode())
        self.assertEqual(sx.one(original, 'wiring'), sx.one(final, 'wiring'))
        self.assertEqual([n for n in original if not isinstance(n, list) or n[0] != 'structure'],
                         [n for n in final if not isinstance(n, list) or n[0] != 'structure'])

    def test_every_native_box_is_outward_bounded_and_grid_exact(self):
        adapted, receipt = self.apply()
        self.assertEqual(len(receipt['obstacles']), 19)
        self.assertEqual([x['original']['layer'] for x in receipt['obstacles']], ['top_layer'] * 17 + ['bottom_layer'] * 2)
        for row in receipt['obstacles']:
            self.assertEqual(row['original'], self.context['obstacles'][row['index']])
            for i, (old, new) in enumerate(zip(row['original']['bbox_mm'], row['snapped']['bbox_mm'])):
                old, new = Decimal(str(old)), Decimal(str(new))
                expansion = old - new if i < 2 else new - old
                self.assertGreaterEqual(expansion, 0)
                self.assertLess(expansion, Decimal('.0001'))
                self.assertEqual(new / Decimal('.0001'), (new / Decimal('.0001')).to_integral_value())
        self.assertEqual(receipt['obstacles'][0]['snapped']['bbox_mm'], [76.6232, 53.7763, 86.3769, 57.2237])
        rects = receipt['adapter']['transformations'][1:]
        self.assertEqual(rects[0]['rect_um'], ['76623.2', '-57223.7', '86376.9', '-53776.3'])
        self.assertTrue(r.verify(self.raw, adapted, self.context, receipt))

    def test_negative_coordinates_use_floor_not_truncation(self):
        context = copy.deepcopy(self.context)
        context['obstacles'][0]['bbox_mm'] = [-1.000001, -2.000001, -.000099, -.000001]
        _, receipt = self.apply(context=context)
        self.assertEqual(receipt['obstacles'][0]['snapped']['bbox_mm'], [-1.0001, -2.0001, 0.0, 0.0])

    def test_rehashed_bbox_shrink_layer_and_extra_ast_mutations_reject(self):
        adapted, receipt = self.apply()
        def keepout(tree): return sx.children(sx.one(tree, 'structure'), 'keepout')[-19]
        changes = [lambda t: keepout(t)[2].__setitem__(2, '76623.3'),
                   lambda t: keepout(t)[2].__setitem__(1, 'bottom_layer'),
                   lambda t: sx.one(t, 'wiring').append(['wire', ['path', 'top_layer', '500', '0', '0', '1', '1'], ['net', 'VCC'], ['type', 'route']]),
                   lambda t: sx.one(t, 'network').append(['unknown', 'change']),
                   lambda t: sx.one(t, 'structure').append(copy.deepcopy(receipt['removed_plane']['node'])),
                   lambda t: sx.one(t, 'wiring')[1][1].__setitem__(3, '148358')]
        for index, change in enumerate(changes):
            with self.subTest(case=index):
                tree = a._parse_dsn(adapted.decode()); change(tree)
                raw = a._dump_dsn(tree).encode(); bad = copy.deepcopy(receipt)
                bad['output_sha256'] = bad['adapter']['output_sha256'] = a._digest(raw)
                bad['adapter']['output_bytes'] = len(raw)
                with self.assertRaises(ValueError): r.verify(self.raw, raw, self.context, bad)

    def test_ledger_flags_and_adapter_receipt_tampering_reject(self):
        adapted, receipt = self.apply()
        changes = [lambda x: x['obstacles'][0]['snapped']['bbox_mm'].__setitem__(0, 76.6233),
                   lambda x: x['obstacles'][0]['original']['bbox_mm'].__setitem__(0, 76.6231),
                   lambda x: x['obstacles'][0].update(index=True),
                   lambda x: x['obstacles'].reverse(),
                   lambda x: x['removed_plane'].update(structure_index=1),
                   lambda x: x['removed_plane']['node'].__setitem__(1, 'VCC'),
                   lambda x: x['adapter']['transformations'][1].update(dsn_layer='bottom_layer'),
                   lambda x: x['adapter']['transformations'].pop(),
                   lambda x: x['adapter'].update(native_project_modified=True),
                   lambda x: x.update(schema=True),
                   lambda x: x.update(remaining_ordinary_routes=False),
                   lambda x: x.update(routing_accepted=True),
                   lambda x: x.update(extra='unbound')]
        for index, change in enumerate(changes):
            with self.subTest(case=index):
                bad = copy.deepcopy(receipt); change(bad)
                with self.assertRaises(ValueError): r.verify(self.raw, adapted, self.context, bad)

    def test_wrong_original_scope_never_calls_existing_adapter(self):
        def wiring(t): return sx.one(t, 'wiring')
        def plane(t): return sx.children(sx.one(t, 'structure'), 'plane')[0]
        changes = [lambda t: wiring(t).append(['via', 'seed', '1', '2', ['net', 'VCC'], ['type', 'route']]),
                   lambda t: wiring(t).append(copy.deepcopy(wiring(t)[1])),
                   lambda t: sx.one(wiring(t)[1], 'type').__setitem__(1, 'route'),
                   lambda t: sx.one(wiring(t)[1], 'polygon').__setitem__(3, '148358'),
                   lambda t: plane(t).__setitem__(1, 'VCC'),
                   lambda t: plane(t)[2].__setitem__(3, '223521'),
                   lambda t: sx.one(t, 'structure').append(copy.deepcopy(plane(t))),
                   lambda t: sx.one(t, 'structure').append(['keepout', a._KEEP_OUT_PREFIX + 'seed', ['rect', 'top_layer', '0', '0', '1', '1']]),
                   lambda t: sx.one(t, 'resolution').__setitem__(2, '1')]
        for index, change in enumerate(changes):
            with self.subTest(case=index):
                tree = a._parse_dsn(self.raw.decode()); change(tree)
                with mock.patch.object(a, 'adapt_dsn') as adapter:
                    with self.assertRaises(ValueError): self.apply(a._dump_dsn(tree).encode())
                    adapter.assert_not_called()

    def test_context_counts_kinds_layers_numeric_and_full_binding(self):
        changes = [lambda c: c['obstacles'].pop(),
                   lambda c: c['obstacles'][0].update(kind='PCB_SHAPE'),
                   lambda c: c['obstacles'][0].update(layer='F.Cu'),
                   lambda c: c['obstacles'][0].update(dsn_layer='bottom_layer'),
                   lambda c: c['obstacles'][0]['bbox_mm'].__setitem__(0, True),
                   lambda c: c['obstacles'][0]['bbox_mm'].__setitem__(0, float('nan')),
                   lambda c: c['obstacles'][0]['bbox_mm'].__setitem__(2, 1),
                   lambda c: c['obstacles'][0]['bbox_mm'].__setitem__(0, 1.0000001),
                   lambda c: c.update(board_saved=True),
                   lambda c: c.update(context_schema=True)]
        for index, change in enumerate(changes):
            with self.subTest(case=index):
                context = copy.deepcopy(self.context); change(context)
                with self.assertRaises(ValueError): self.apply(context=context)
        adapted, receipt = self.apply(); context = copy.deepcopy(self.context)
        context['source'] += '-changed'
        with self.assertRaises(ValueError): r.verify(self.raw, adapted, context, receipt)

    def test_existing_adapter_output_and_receipt_are_verified(self):
        real = a.adapt_dsn
        def wrong_receipt(*args):
            result = real(*args); result['limitations'].pop(); return result
        with mock.patch.object(a, 'adapt_dsn', side_effect=wrong_receipt):
            with self.assertRaises(ValueError): self.apply()
        def wrong_output(*args):
            result = real(*args); path = args[0]
            tree = a._parse_dsn(path.read_text()); sx.one(tree, 'wiring').pop()
            path.write_text(a._dump_dsn(tree)); return result
        with mock.patch.object(a, 'adapt_dsn', side_effect=wrong_output):
            with self.assertRaises(ValueError): self.apply()

    def test_bounded_bytes_and_real_file_symlink_rejected(self):
        adapted, receipt = self.apply()
        for raw in (b'', b'x' * (r.MAX_INPUT + 1), self.raw.decode()):
            with self.subTest(kind=type(raw).__name__, size=len(raw)):
                with self.assertRaises(ValueError): r.verify(raw, adapted, self.context, receipt)
        with tempfile.TemporaryDirectory(dir=ROOT / '.runs', prefix='adapter-unit-') as temp:
            path = Path(temp) / 'task.dsn'; path.write_bytes(self.raw)
            alias = Path(temp) / 'alias.dsn'; alias.symlink_to(path)
            with self.assertRaises(Exception): r.apply(alias, self.context)
            self.assertEqual(path.read_bytes(), self.raw)


if __name__ == '__main__':
    unittest.main()
