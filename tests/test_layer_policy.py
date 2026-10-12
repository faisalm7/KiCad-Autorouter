"""Pure layer-scope controls; no routing/native qualification."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
from autorouter import sexpr as sx
from autorouter.adapter import _parse_dsn, _dump_dsn

from autorouter import layer_policy as lp
DSN = (ROOT / 'evidence/placement-production-native-001/native.dsn').read_bytes()
SOURCE = (ROOT / 'tests/fixtures/board-floor/fixture.kicad_pcb').read_bytes()


def raw(tree): return (sx.dump(tree) + '\n').encode()
def segment(uid='new', layer='F.Cu', kind='segment'):
    middle = '(mid 1 1)' if kind == 'arc' else ''
    return sx.parse(f'({kind} (start 0 0) {middle} (end 2 0) (width .2) (layer "{layer}") (net "SIGNAL_A") (uuid "{uid}"))')
def via(uid='via'):
    return sx.parse(f'(via (at 2 0) (size .8) (drill .4) (layers "F.Cu" "B.Cu") (net "SIGNAL_A") (uuid "{uid}"))')


class Layers(unittest.TestCase):
    def setUp(self):
        self.original = SOURCE
        self.names = ['F.Cu']
        self.kw = dict(scope='whole_board_unlocked_routing', engine_profile='completion-only', guidance_policy='native')

    def bind(self, source=None, exported=DSN, engine=DSN):
        return lp.bind(source or self.original, exported, engine, self.names, **self.kw)

    def audit(self, candidate, binding=None, exported=DSN, engine=DSN):
        return lp.audit_candidate(self.original, raw(candidate), exported, engine,
                                  binding or self.bind(exported=exported, engine=engine),
                                  allowed_names=self.names, **self.kw)

    def test_real_export_masks_are_name_mapped_not_request_order(self):
        for names, mask in [(['F.Cu'], [True, False]), (['B.Cu'], [False, True]),
                            (['B.Cu', 'F.Cu'], [True, True])]:
            with self.subTest(names=names):
                self.names = names; b = self.bind()
                self.assertEqual(b['routable'], mask)
                self.assertEqual(b['engine_signal_layers'], ['F.Cu', 'B.Cu'])
                self.assertEqual(b['engine_argument'], '--router.layers.routable=' + ','.join(str(v).lower() for v in mask))

    def test_explicit_bad_requests_modes_and_unqualified_version(self):
        for bad in ['source_all', [], ['F.Cu', 'F.Cu'], ['F.Cu', 'B.Cu', 'F.Cu'], ['f.cu'], [0], [True], ('F.Cu',)]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                lp.bind(SOURCE, DSN, DSN, bad, **self.kw)
        for key, value in [('engine_profile', 'standard'), ('engine_profile', 'tuned'), ('guidance_policy', 'board-floors-v1'), ('guidance_policy', 'placement-clearance-v1'), ('scope', 'selected_nets')]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.bind_with(**{key: value})
        tree = sx.parse(SOURCE.decode()); sx.one(tree, 'version')[1] = '20241229'
        with self.assertRaises(ValueError): self.bind(source=raw(tree))

    def bind_with(self, **kw):
        return lp.bind(SOURCE, DSN, DSN, self.names, **(self.kw | kw))

    def test_source_physical_order_alias_duplicate_and_stackup(self):
        for mode in ['reverse', 'four', 'duplicate', 'alias', 'stackup', 'hidden_copper']:
            tree = sx.parse(SOURCE.decode()); layers = sx.one(tree, 'layers')
            if mode == 'reverse': layers[1:3] = list(reversed(layers[1:3]))
            elif mode == 'four': layers.insert(2, ['4', '"In1.Cu"', 'signal'])
            elif mode == 'duplicate': layers.append(copy.deepcopy(layers[1]))
            elif mode == 'alias': layers[1].append('"Top"')
            elif mode == 'hidden_copper': layers.insert(2, ['4', '"Renamed"', 'user'])
            else: sx.one(tree, 'setup').append(['stackup', ['layer', '"B.Cu"', ['type', '"copper"']], ['layer', '"F.Cu"', ['type', '"copper"']]])
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.bind(source=raw(tree))

    def test_both_native_and_engine_dsn_order_and_indices_checked(self):
        for mode in ['reverse', 'index', 'duplicate', 'type', 'extra', 'missing_quote']:
            tree = _parse_dsn(DSN.decode()); structure = sx.one(tree, 'structure')
            rows = sx.children(structure, 'layer')
            if mode == 'reverse': structure[1:3] = rows[::-1]
            elif mode == 'index': sx.one(sx.one(rows[0], 'property'), 'index')[1] = '1'
            elif mode == 'duplicate': rows[1][1] = rows[0][1]
            elif mode == 'type': sx.one(rows[0], 'type')[1] = 'power'
            elif mode == 'extra': rows[0].append(['cost', '0'])
            changed = _dump_dsn(tree).encode()
            if mode == 'missing_quote': changed = changed.replace(b'(string_quote ")', b'')
            for side in ['exported', 'engine']:
                with self.subTest(mode=mode, side=side), self.assertRaises(ValueError): self.bind(**{side: changed})

    def test_segments_arcs_and_through_via_span(self):
        for kind in ['segment', 'arc']:
            tree = sx.parse(SOURCE.decode()); tree.append(segment(kind=kind))
            self.assertTrue(self.audit(tree)['layer_scope_passed'])
            sx.one(tree[-1], 'layer')[1] = '"B.Cu"'
            with self.assertRaisesRegex(ValueError, 'disallowed'): self.audit(tree)
        tree = sx.parse(SOURCE.decode()); tree.append(via())
        with self.assertRaisesRegex(ValueError, 'disallowed'): self.audit(tree)
        self.names = ['F.Cu', 'B.Cu']
        self.assertEqual(self.audit(tree)['new_routes'][0]['layers'], ['F.Cu', 'B.Cu'])
        for bad in ['micro', 'blind', 'through']:
            changed = copy.deepcopy(tree); changed[-1].insert(1, bad)
            with self.subTest(bad=bad), self.assertRaises(ValueError): self.audit(changed)

    def test_exact_protected_routes_are_exempt_not_spoofable(self):
        for kind in ['segment', 'arc', 'via']:
            tree = sx.parse(SOURCE.decode()); route = via() if kind == 'via' else segment(layer='B.Cu', kind=kind)
            route.append(['locked', 'yes']); tree.append(route); self.original = raw(tree)
            result = self.audit(tree)
            self.assertEqual(len(result['protected_exemptions']), 1)
            self.assertEqual(result['protected_exemptions'][0]['outside_allowed_names'], ['B.Cu'])
            changed = copy.deepcopy(tree); changed[-1].append(['unknown', 'value'])
            with self.subTest(kind=kind), self.assertRaises(ValueError): self.audit(changed)
            changed = copy.deepcopy(tree); changed.pop()
            with self.assertRaisesRegex(ValueError, 'protected'): self.audit(changed)
        # Partial completion protects an unlocked original on B.Cu, whole-board does not.
        tree = sx.parse(SOURCE.decode()); tree.append(segment(layer='B.Cu')); self.original = raw(tree)
        with self.assertRaisesRegex(ValueError, 'disallowed'): self.audit(tree)
        self.kw['scope'] = 'partial_completion'
        self.assertEqual(len(self.audit(tree)['protected_exemptions']), 1)

    def test_duplicate_uuid_and_malformed_layer_fail(self):
        for mode in ['uuid', 'duplicate_uuid', 'layer', 'plural', 'extra_atom', 'via_span']:
            tree = sx.parse(SOURCE.decode()); tree.append(segment())
            if mode == 'uuid': tree[-1].remove(sx.one(tree[-1], 'uuid'))
            elif mode == 'duplicate_uuid': tree.append(segment(layer='B.Cu'))
            elif mode == 'layer': tree[-1].append(['layer', '"B.Cu"'])
            elif mode == 'plural': tree[-1].append(['layers', '"F.Cu"', '"B.Cu"'])
            elif mode == 'extra_atom': sx.one(tree[-1], 'layer').append('"B.Cu"')
            else: tree[-1] = via(); sx.one(tree[-1], 'layers')[2] = '"F.Cu"'
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.audit(tree)

    def test_binding_cannot_supply_choices_or_alias_boolean_integer(self):
        tree = sx.parse(SOURCE.decode()); tree.append(segment())
        for key, value in [('routable', [1, 0]), ('requested_names', ['B.Cu']), ('schema', True), ('engine_argument', '--router.layers.routable=true,true'), ('source_sha256', '0' * 64)]:
            binding = self.bind(); binding[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'binding'): self.audit(tree, binding=binding)
        stale = self.bind(); self.original += b'\n'
        with self.assertRaisesRegex(ValueError, 'binding'): self.audit(tree, binding=stale)

    def test_copper_must_precede_every_noncopper_declaration(self):
        tree = sx.parse(SOURCE.decode()); layers = sx.one(tree, 'layers')
        layers[2:4] = [layers[3], layers[2]]
        with self.assertRaisesRegex(ValueError, 'physical'):
            self.bind(source=raw(tree))

    def test_known_route_grammar_rejects_unknown_missing_and_malformed_fields(self):
        self.names = ['F.Cu', 'B.Cu']
        for kind in ['segment', 'arc', 'via']:
            good = via() if kind == 'via' else segment(kind=kind)
            candidate = sx.parse(SOURCE.decode()); candidate.append(good)
            self.assertTrue(self.audit(candidate)['layer_scope_passed'])
            variants = []
            # Every essential singleton is required and no extra/duplicate fields
            # can hide layer-specific or custom-padstack semantics.
            for node in good[1:]:
                missing = copy.deepcopy(good); missing.remove(node); variants.append(missing)
                duplicate = copy.deepcopy(good); duplicate.append(copy.deepcopy(node)); variants.append(duplicate)
            for field in [['future_route_layer', '"B.Cu"'], ['padstack', ['mode', 'custom']], 'blind', 'mystery']:
                bad = copy.deepcopy(good); bad.append(field); variants.append(bad)
            point = 'at' if kind == 'via' else 'start'
            for value in ['nan', 'inf', '1e999', '"1"', 'false']:
                bad = copy.deepcopy(good); sx.one(bad, point)[1] = value; variants.append(bad)
            dimension = 'size' if kind == 'via' else 'width'
            for value in ['0', '-.1']:
                bad = copy.deepcopy(good); sx.one(bad, dimension)[1] = value; variants.append(bad)
            bad = copy.deepcopy(good); sx.one(bad, point).append('2'); variants.append(bad)
            bad = copy.deepcopy(good); sx.one(bad, 'net')[1] = '""'; variants.append(bad)
            for i, bad in enumerate(variants):
                candidate[-1] = bad
                with self.subTest(kind=kind, variant=i), self.assertRaises(ValueError):
                    self.audit(candidate)

    def test_candidate_cannot_change_source_geometry_and_inputs_untouched(self):
        original = sx.parse(SOURCE.decode()); tree = copy.deepcopy(original)
        sx.one(tree, 'layers')[1][1] = '"B.Cu"'
        with self.assertRaisesRegex(ValueError, 'immutable'): self.audit(tree)
        self.audit(original)
        self.assertEqual(raw(original), raw(sx.parse(SOURCE.decode())))
        self.assertEqual(self.original, SOURCE)
        for invalid in [bytearray(SOURCE), b'', b'\xff']:
            with self.subTest(invalid=type(invalid)), self.assertRaises(ValueError):
                lp.bind(invalid, DSN, DSN, self.names, **self.kw)


if __name__ == '__main__': unittest.main()
