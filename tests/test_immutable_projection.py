"""Owned AST equivalence/isolation controls; no Native or speed qualification.

The private projection may share retained nodes temporarily. Its callers must
deepcopy before returning or editing them; only parsed plain lists/string atoms
are in scope. Nested fill-looking metadata remains original source intent.
"""
import copy
import unittest
from unittest.mock import patch

from autorouter import pipeline as p, sexpr as sx
from tests import test_refill_route_nets as refill_fixture


def legacy_immutable(tree):
    """The pre-projection implementation, retained as a semantic oracle."""
    out = copy.deepcopy(tree)
    out[:] = [node for node in out if not isinstance(node, list) or not node
              or node[0] not in {'segment', 'via', 'arc'}]
    for zone in sx.children(out, 'zone'):
        zone[:] = [node for node in zone if not isinstance(node, list) or not node
                   or node[0] not in {'filled_polygon', 'fill_segments'}]
    return out


def legacy_fill_after_identity_check(original, filled):
    """Old transplant body; actual identity dispatch is exercised separately."""
    out = copy.deepcopy(original)
    by_id = {sx.one(zone, 'uuid')[1]: zone for zone in sx.children(filled, 'zone')}
    for zone in sx.children(out, 'zone'):
        identity = sx.one(zone, 'uuid')[1]
        if identity not in by_id:
            raise p.Rejected('native refill lost zone')
        zone[:] = [node for node in zone if not isinstance(node, list) or not node
                   or node[0] not in {'filled_polygon', 'fill_segments'}]
        zone.extend(copy.deepcopy(node) for node in by_id[identity]
                    if isinstance(node, list) and node and node[0] in {'filled_polygon', 'fill_segments'})
    return out


def list_ids(node):
    if not isinstance(node, list):
        return set()
    return {id(node)}.union(*(list_ids(child) for child in node))


def board():
    # Nested names deliberately resemble editable root routing/derived fill.
    # The projection must preserve them without interpreting unknown intent.
    return sx.parse('''(kicad_pcb
      (version 20241229) (general (thickness 1.6))
      (layers (0 "F.Cu" signal) (2 "B.Cu" signal))
      (setup (stackup (layer "F.Cu" (thickness 0.035))) (rules (clearance 0.3)))
      (net 0 "") (net 1 "SIGNAL")
      (footprint "Owned" (uuid "footprint")
        (property "Reference" "U1")
        (pad "1" smd rect (at 1 2) (size 1 2) (layers "F.Cu") (net 1 "SIGNAL"))
        (segment (future nested-route))
        (zone (uuid "nested-zone") (filled_polygon (future keep-this))
          (fill_segments (future keep-this-too))))
      (zone (uuid "zone-a") (net 1) (net_name "SIGNAL") (layer "F.Cu")
        (connect_pads (clearance 0.3)) (fill (thermal_gap 0.4) (thermal_bridge_width 0.3))
        (keepout (tracks not_allowed))
        (polygon (pts (xy 0 0) (xy 4 0) (xy 4 4)))
        (future (filled_polygon nested) (fill_segments nested))
        (filled_polygon (layer "F.Cu") (pts (xy 1 1) (xy 2 1)))
        (fill_segments (layer "F.Cu") (pts (xy 1 1) (xy 1 2))) ())
      (zone (uuid "zone-b") (net 1) (layer "B.Cu") (hatch edge 0.5)
        (filled_polygon (pts (xy 3 3))))
      (unknown_root (zone (uuid "unknown-zone") (filled_polygon nested))
        (segment (unknown kept)) (via (unknown kept)) (arc (unknown kept)))
      (filled_polygon root-kept) (fill_segments root-kept) () root-atom
      (segment (uuid "segment") (net 1) (width 0.3) (locked yes))
      (via (uuid "via") (net 1) (size 0.9) (drill 0.4))
      (arc (uuid "arc") (net 1) (width 0.3)))''')


class ImmutableProjectionControls(unittest.TestCase):
    def test_exact_old_projection_for_all_route_kinds_and_unknown_intent(self):
        source = board()
        for tree in (source, ['kicad_pcb'], ['kicad_pcb', [], 'unknown'],
                     ['kicad_pcb', *reversed(source[1:])]):
            with self.subTest(children=len(tree)):
                before = copy.deepcopy(tree)
                actual = p.immutable(tree)
                self.assertEqual(actual, legacy_immutable(tree))
                self.assertEqual(tree, before)
                self.assertFalse(p.routes(actual))
                for zone in sx.children(actual, 'zone'):
                    self.assertFalse(sx.children(zone, 'filled_polygon'))
                    self.assertFalse(sx.children(zone, 'fill_segments'))

    def test_only_direct_root_zone_fill_and_root_routes_are_discarded(self):
        original = board()
        expected = p.immutable(original)
        changed = copy.deepcopy(original)
        for route in p.routes(changed):
            route.append(['future_route_field', 'discarded-with-route'])
        for zone in sx.children(changed, 'zone'):
            zone.append(['filled_polygon', ['future_native_fill', 'discarded']])
            zone.append(['fill_segments', ['future_native_fill', 'discarded']])
        self.assertEqual(p.immutable(changed), expected)
        for kind in ('setup', 'net', 'footprint', 'unknown_root', 'root_fill', 'zone_intent', 'nested_fill'):
            changed = copy.deepcopy(original)
            if kind == 'root_fill':
                target = sx.children(changed, 'filled_polygon')[0]
            elif kind == 'zone_intent':
                target = sx.one(sx.children(changed, 'zone')[0], 'fill')
            elif kind == 'nested_fill':
                target = sx.one(sx.children(changed, 'zone')[0], 'future')
            else:
                target = sx.children(changed, kind)[0]
            target.append(['retained_change', kind])
            with self.subTest(retained=kind):
                self.assertNotEqual(p.immutable(changed), expected)

    def test_immutable_result_has_no_mutable_alias_to_input(self):
        original = board()
        before = copy.deepcopy(original)
        projected = p.immutable(original)
        self.assertFalse(list_ids(original) & list_ids(projected))
        sx.children(projected, 'footprint')[0].append(['output_only', []])
        self.assertEqual(original, before)
        retained = copy.deepcopy(projected)
        sx.children(original, 'zone')[0].append(['input_only', []])
        self.assertEqual(projected, retained)

    def test_transplant_exact_old_fill_semantics_and_original_route_order(self):
        original = board()
        filled = copy.deepcopy(original)
        zones = sx.children(filled, 'zone')
        for index, zone in enumerate(zones):
            zone[:] = [node for node in zone if not isinstance(node, list) or not node
                       or node[0] not in {'filled_polygon', 'fill_segments'}]
            # Only derived children are imported, not this changed zone intent.
            zone.append(['native_only_intent', str(index)])
            zone.extend([['fill_segments', ['new', str(index)]],
                         ['filled_polygon', ['new', str(index)]],
                         ['filled_polygon', ['second_new', str(index)]]])
        filled[:] = [node for node in filled if node not in zones] + list(reversed(zones))
        filled.append(['zone', ['uuid', '"native-extra-zone"'], ['filled_polygon', 'ignored']])
        before = copy.deepcopy((original, filled))
        with patch.object(p, 'check_refill_route_nets') as identity:
            actual = p.transplant_fill(original, filled)
        identity.assert_called_once_with(original, filled)
        self.assertIs(identity.call_args.args[0], original)
        self.assertIs(identity.call_args.args[1], filled)
        self.assertEqual(actual, legacy_fill_after_identity_check(original, filled))
        self.assertEqual(p.routes(actual), p.routes(original))
        self.assertEqual(p.immutable(actual), p.immutable(original))
        self.assertEqual((original, filled), before)
        self.assertFalse(list_ids(actual) & (list_ids(original) | list_ids(filled)))
        sx.children(actual, 'zone')[0].append(['output_only', []])
        self.assertEqual((original, filled), before)

    def test_missing_source_zone_still_refuses_without_mutating_either_input(self):
        original = board()
        filled = copy.deepcopy(original)
        filled.remove(sx.children(filled, 'zone')[0])
        before = copy.deepcopy((original, filled))
        with patch.object(p, 'check_refill_route_nets') as identity, self.assertRaises(p.Rejected):
            p.transplant_fill(original, filled)
        identity.assert_called_once_with(original, filled)
        self.assertEqual((original, filled), before)

    def test_identity_refusal_propagates_before_fill_can_be_adopted(self):
        original = board()
        filled = copy.deepcopy(original)
        before = copy.deepcopy((original, filled))
        failure = p.Rejected('constructed route/net refusal')
        with patch.object(p, 'check_refill_route_nets', side_effect=failure) as identity:
            with self.assertRaises(p.Rejected) as raised:
                p.transplant_fill(original, filled)
        self.assertIs(raised.exception, failure)
        identity.assert_called_once_with(original, filled)
        self.assertEqual((original, filled), before)

    def test_real_route_and_net_identity_check_survives_projection(self):
        original = refill_fixture.board()
        original.append(['zone', ['uuid', '"' + refill_fixture.uid('fill-zone') + '"'],
                         ['net', '1'], ['net_name', '"GND"'],
                         ['filled_polygon', ['pts', ['xy', '1', '1']]]])
        filled = refill_fixture.RefillRouteNetControls.named(self, original)
        sx.one(sx.children(filled, 'zone')[0], 'filled_polygon').append(['new_fill', 'retained'])
        self.assertEqual(p.transplant_fill(original, filled),
                         legacy_fill_after_identity_check(original, filled))
        for kind in ('net', 'uuid', 'kind', 'missing_route'):
            changed = copy.deepcopy(filled)
            route = p.routes(changed)[0]
            if kind == 'net':
                sx.one(route, 'net')[1] = '"LED"'
            elif kind == 'uuid':
                sx.one(route, 'uuid')[1] = '"' + refill_fixture.uid('different-route') + '"'
            elif kind == 'kind':
                route[0] = 'arc'
            else:
                changed.remove(route)
            with self.subTest(kind=kind), self.assertRaises(p.Rejected):
                p.transplant_fill(original, changed)


if __name__ == '__main__':
    unittest.main()
