"""Fixed through-via controls for the Native source-baseline placement scope."""
from pathlib import Path
import unittest

from autorouter import placement_copper, placement_view, sexpr as sx
from experiments.constrained_placement_v1 import constraints
from experiments.placement_native_proposal_v1 import contract
from experiments.live_editor_v1.probe import FIXTURE, NAME


SOURCE = FIXTURE / (NAME + '.kicad_pcb')
SCOPE = contract.THT_BASELINE_SCOPE
VIA = '41dde572-0b23-4b39-811f-cdf4676a2bc0'


def with_via(*, net='KEEP', fields=''):
    tree = sx.read(SOURCE)
    tree.append(sx.parse(f'(via (at 18 10) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") '
                         f'(net "{net}") (uuid "{VIA}") {fields})'))
    return (sx.dump(tree) + '\n').encode()


class ViaPlacementTests(unittest.TestCase):
    def test_via_is_witnessed_as_a_protected_obstacle_and_drawn(self):
        observed = contract.inspect_board(with_via(), scope=SCOPE)
        row = next(route for route in observed['routes'] if route['uuid'] == VIA)
        self.assertEqual((row['kind'], row['at_nm'], row['layers'], row['width_nm'], row['drill_nm']),
                         ('via', [18_000_000, 10_000_000], ['F.Cu', 'B.Cu'], 600_000, 300_000))
        selected = next(row['uuid'] for row in observed['footprints'] if row['reference'] == 'J1')
        options = dict(scope=SCOPE, selected=[selected], region_nm=[7_000_000, 7_000_000, 31_000_000, 14_000_000])
        facts = contract.facts_from_observation(observed, **options)
        self.assertEqual(next(area['bounds_mm'] for area in facts['keepouts'] if area['id'] == VIA), [17.7, 9.7, 18.3, 10.3])
        with self.assertRaises(constraints.Refused) as caught:
            contract.validate_moves(observed, {selected: [18_000_000, 10_000_000]}, **options)
        self.assertEqual(caught.exception.constraint, 'protected_tracks')
        self.assertIn('data-role="preserved-via"', placement_view.scene(observed, {}, [], options['region_nm'])['svg'])

    def test_incident_via_and_unhandled_via_attributes_refuse(self):
        raw = with_via(net='ROUTE_A')
        observed = contract.inspect_board(raw, scope=SCOPE)
        selected = [row['uuid'] for row in observed['footprints'] if row['reference'] in ('J1', 'J2')]
        with self.assertRaisesRegex(ValueError, 'via on ROUTE_A at 18, 10 mm'):
            placement_copper.propose(raw, selected, scope=SCOPE)
        with self.assertRaisesRegex(ValueError, 'via at 18, 10 mm.*capping'):
            contract.inspect_board(with_via(fields='(capping yes)'), scope=SCOPE)

    def test_unsupported_board_arc_names_the_actual_edge(self):
        tree = sx.read(SOURCE)
        tree.append(sx.parse('(gr_arc (layer "Edge.Cuts"))'))
        with self.assertRaisesRegex(ValueError, r'curved board edge .*Edge.Cuts'):
            contract.inspect_board(sx.dump(tree).encode(), scope=SCOPE)
