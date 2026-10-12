"""Pure actual-evidence stripping/reversal controls; never run KiCad or the JVM."""
import copy
import json
import unittest
from pathlib import Path

from autorouter import sexpr as sx
from autorouter.adapter import _dump_dsn, _parse_dsn
from experiments.pic_mixed_transport_probe_v1 import routing_input as r

ROOT = Path(__file__).resolve().parents[2]


class RoutingInput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        basis = ROOT / 'evidence/pic-local-clearance-transport-001'
        cls.raw = (basis / 'mixed.dsn').read_bytes()
        cls.expected = json.loads((basis / 'expectations.json').read_bytes())
        cls.context = json.loads((ROOT / 'evidence/pic-mixed-transport-probe-005/context.json').read_bytes())
        # Already acquired public original, exact hash bound by committed native
        # evidence. This source is not a newly generated or mock native board.
        cls.native = (ROOT / '.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb').read_bytes()
        if r.transport.sha(cls.native) != cls.context['board_sha256']:
            raise ValueError('original public PIC board differs from captured native basis')

    def derive(self, raw=None, expected=None, native=None, context=None):
        return r.derive(self.raw if raw is None else raw,
                        self.expected if expected is None else expected,
                        self.native if native is None else native,
                        self.context if context is None else context)

    def mutated_dsn(self, change):
        tree = _parse_dsn(self.raw.decode()); change(tree)
        raw = _dump_dsn(tree).encode(); expected = copy.deepcopy(self.expected)
        expected['derived_dsn_sha256'] = r.transport.sha(raw)
        self.assertTrue(tree != _parse_dsn(self.raw.decode()), 'falsifier must actually change AST')
        return raw, expected

    def test_actual_complete_reverse_and_immutable_inputs(self):
        originals = copy.deepcopy((self.expected, self.context))
        derived, receipt = self.derive()
        tree = _parse_dsn(derived.decode()); wiring = sx.one(tree, 'wiring')
        self.assertEqual(len(wiring), 3)
        self.assertTrue(all(sx.one(n, 'polygon') and sx.one(n, 'type') == ['type', 'protect'] for n in wiring[1:]))
        self.assertEqual(receipt['removed'], {'path_wire': 339, 'via': 6})
        self.assertEqual(receipt['native_routes'], {'segments': 370, 'vias': 6, 'locked': 0, 'zones': 1})
        self.assertEqual(r.restore(derived, receipt), _parse_dsn(self.raw.decode()))
        self.assertTrue(r.verify(self.raw, self.expected, self.native, self.context, derived, receipt))
        self.assertEqual((self.expected, self.context), originals)
        self.assertFalse(receipt['routing_executed']); self.assertFalse(receipt['routing_accepted'])
        before = _parse_dsn(self.raw.decode())
        self.assertEqual([n for n in tree if not isinstance(n, list) or n[0] != 'wiring'],
                         [n for n in before if not isinstance(n, list) or n[0] != 'wiring'])

    def test_path_grammar_layer_net_and_numeric_falsifiers(self):
        def wire(t): return sx.children(sx.one(t, 'wiring'), 'wire')[0]
        changes = [lambda t: wire(t).append(['mystery', 'yes']),
                   lambda t: wire(t).append(copy.deepcopy(sx.one(wire(t), 'net'))),
                   lambda t: sx.one(wire(t), 'type').__setitem__(1, 'protect'),
                   lambda t: sx.one(wire(t), 'path').__setitem__(0, 'qarc'),
                   lambda t: sx.one(wire(t), 'path').__setitem__(1, 'unknown_layer'),
                   lambda t: sx.one(wire(t), 'net').__setitem__(1, 'UNKNOWN_NET'),
                   lambda t: sx.one(wire(t), 'path').__setitem__(2, '0'),
                   lambda t: sx.one(wire(t), 'path').__setitem__(3, 'NaN'),
                   lambda t: sx.one(wire(t), 'path').pop(),
                   lambda t: wire(t).append('locked')]
        for i, change in enumerate(changes):
            with self.subTest(case=i):
                raw, expected = self.mutated_dsn(change)
                with self.assertRaises(ValueError): self.derive(raw, expected)

    def test_via_unknown_fixed_and_malformed_falsifiers(self):
        def via(t): return sx.children(sx.one(t, 'wiring'), 'via')[0]
        changes = [lambda t: via(t).__setitem__(1, 'UNKNOWN_PADSTACK'),
                   lambda t: via(t).__setitem__(2, 'Infinity'),
                   lambda t: sx.one(via(t), 'net').__setitem__(1, 'UNKNOWN_NET'),
                   lambda t: sx.one(via(t), 'type').__setitem__(1, 'fix'),
                   lambda t: via(t).append(['type', 'route']),
                   lambda t: via(t).append(['protect', 'on']),
                   lambda t: via(t).pop(2)]
        for i, change in enumerate(changes):
            with self.subTest(case=i):
                raw, expected = self.mutated_dsn(change)
                with self.assertRaises(ValueError): self.derive(raw, expected)

    def test_no_body_or_plane_deletion_extra_wiring_or_changed_population(self):
        def wire(t): return sx.children(sx.one(t, 'wiring'), 'wire')[-1]
        changes = [lambda t: sx.one(t, 'wiring').remove(wire(t)),
                   lambda t: sx.one(t, 'wiring').append(copy.deepcopy(wire(t))),
                   lambda t: sx.one(wire(t), 'net').__setitem__(1, 'GND'),
                   lambda t: sx.one(wire(t), 'polygon').__setitem__(3, '1'),
                   lambda t: sx.one(wire(t), 'type').__setitem__(1, 'route'),
                   lambda t: sx.one(t, 'structure').remove(sx.children(sx.one(t, 'structure'), 'plane')[0]),
                   lambda t: sx.one(t, 'wiring').pop(1),
                   lambda t: sx.one(t, 'wiring').append(['unknown']),
                   lambda t: t.append(copy.deepcopy(sx.one(t, 'wiring')))]
        for i, change in enumerate(changes):
            with self.subTest(case=i):
                raw, expected = self.mutated_dsn(change)
                with self.assertRaises(ValueError): self.derive(raw, expected)

    def test_terminal_and_layer_mapping_preserved(self):
        def pin(t): return sx.children(sx.children(sx.one(t, 'library'), 'image')[0], 'pin')[0]
        changes = [lambda t: pin(t).__setitem__(-2, str(int(pin(t)[-2]) + 1)),
                   lambda t: sx.children(sx.one(t, 'network'), 'net')[0].__setitem__(1, 'UNKNOWN_NET'),
                   lambda t: sx.children(sx.one(t, 'structure'), 'layer')[0].__setitem__(1, 'changed'),
                   lambda t: sx.one(t, 'resolution').__setitem__(2, '1')]
        for i, change in enumerate(changes):
            with self.subTest(case=i):
                raw, expected = self.mutated_dsn(change)
                with self.assertRaises(ValueError): self.derive(raw, expected)

    def test_protected_and_unqualified_native_routes_never_removed(self):
        changes = [lambda b: sx.children(b, 'segment')[0].append('locked'),
                   lambda b: sx.children(b, 'segment')[0].append(['locked', 'yes']),
                   lambda b: sx.children(b, 'via')[0].append(['locked', 'no']),
                   lambda b: sx.children(b, 'segment')[0].append(['unknown', 'x']),
                   lambda b: sx.children(b, 'segment')[0].__setitem__(0, 'arc'),
                   lambda b: sx.children(b, 'via')[0].append(['padstack', 'custom']),
                   lambda b: sx.one(sx.children(b, 'via')[0], 'layers').__setitem__(2, '"In1.Cu"')]
        for i, change in enumerate(changes):
            with self.subTest(case=i):
                board = sx.parse(self.native.decode()); change(board)
                native = (sx.dump(board) + '\n').encode(); context = copy.deepcopy(self.context)
                context['board_sha256'] = r.transport.sha(native)
                with self.assertRaises(ValueError): self.derive(native=native, context=context)

    def test_native_identity_geometry_and_fact_bindings(self):
        changes = [lambda c: c['routes'][0].update(width_nm=799999),
                   lambda c: c['routes'][0].update(net='GND'),
                   lambda c: c['routes'][0]['start_nm'].__setitem__(0, 1),
                   lambda c: c['routes'].pop(),
                   lambda c: c['routes'][0].update(uuid=c['routes'][1]['uuid']),
                   lambda c: c.update(board_sha256='0'*64),
                   lambda c: c.update(context_schema=True),
                   lambda c: c.update(board_saved=True),
                   lambda c: c.update(dsn_sha256='0'*64),
                   lambda c: c.update(input_hashes_after={}),
                   lambda c: c.update(units='millimetres')]
        for i, change in enumerate(changes):
            with self.subTest(case=i):
                context = copy.deepcopy(self.context); change(context)
                with self.assertRaises(ValueError): self.derive(context=context)

    def test_ledger_and_rehashed_output_tamper(self):
        derived, receipt = self.derive()
        for change in (lambda x: x['ledger'].pop(),
                       lambda x: x['ledger'][0].update(index=True),
                       lambda x: x['ledger'][1].update(index=x['ledger'][0]['index']),
                       lambda x: x['ledger'][0]['node'][1].__setitem__(2, '1')):
            bad = copy.deepcopy(receipt); change(bad)
            with self.assertRaises(ValueError): r.restore(derived, bad)
        bad = copy.deepcopy(receipt); bad['remaining_ordinary_routes'] = True
        with self.assertRaises(ValueError): r.verify(self.raw, self.expected, self.native, self.context, derived, bad)
        tree = _parse_dsn(derived.decode()); sx.one(tree, 'wiring').append(copy.deepcopy(receipt['ledger'][0]['node']))
        changed = _dump_dsn(tree).encode(); bad = copy.deepcopy(receipt)
        bad['unrouted_dsn_sha256'] = r.transport.sha(changed)
        with self.assertRaises(ValueError): r.verify(self.raw, self.expected, self.native, self.context, changed, bad)

    def test_input_digest_and_bounds(self):
        with self.assertRaises(ValueError): self.derive(raw=self.raw+b' ')
        for raw in (b'', bytearray(self.raw), b'x'*(r.MAX_INPUT+1)):
            with self.subTest(kind=type(raw).__name__, size=len(raw)), self.assertRaises(ValueError): self.derive(raw=raw)
        changed = copy.deepcopy(self.expected); changed['unused'] = float('nan')
        with self.assertRaises(ValueError): self.derive(expected=changed)
        changed = copy.deepcopy(self.expected); changed['unchanged_original_plane_count'] = True
        with self.assertRaises(ValueError): self.derive(expected=changed)


if __name__ == '__main__': unittest.main()
