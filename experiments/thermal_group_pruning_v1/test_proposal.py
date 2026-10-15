"""Authored pure geometry/provenance controls; no Native process or board data."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
import uuid

from autorouter import pipeline as p, sexpr as sx, strategy as s
from experiments.thermal_group_pruning_v1 import proposal as q

FP = '5035a454-156c-4012-b606-11aebd706ac1'
PAD = '995c065f-82cb-4488-8cc9-a1f91b74d228'
ZONE = '47944329-067e-401b-a2aa-33b29bfe4df1'


def digest(tree):
    return hashlib.sha256((sx.dump(tree) + '\n').encode()).hexdigest()


def segment(start, end, index, net='1', layer='F.Cu'):
    return sx.parse('(segment (start %s %s) (end %s %s) (width 0.25) (layer "%s") (net %s) (uuid "%s"))' % (
        *start, *end, layer, net, uuid.UUID(int=100 + index)))


def fixture(name='BIAS_RETURN'):
    original = sx.parse('''(kicad_pcb (version 20260206)
        (layers (0 "F.Cu" signal) (2 "B.Cu" signal))
        (net 0 "") (net 1 %s) (net 2 "SENSE")
        (footprint "authored" (uuid "%s") (at 1 2)
          (pad "7" smd rect (at 0 0) (size 1 1) (layers "F.Cu")
             (net 1 %s) (uuid "%s")))
        (zone (net 1) (net_name %s) (layers "F.Cu" "B.Cu") (uuid "%s")
          (connect_pads (clearance 0.2)) (fill (thermal_gap 0.2))
          (polygon (pts (xy 0 0) (xy 20 0) (xy 20 20) (xy 0 20)))))''' % (
            json.dumps(name), FP, json.dumps(name), PAD, json.dumps(name), ZONE))
    warm = copy.deepcopy(original)
    warm.append(segment((10, 10), (10, 11), 1, net='2'))
    base = copy.deepcopy(warm)
    base.extend([segment((1, 2), (3, 2), 2), segment((3, 2), (3, 3), 3),
                 segment((5, 5), (5, 6), 4), segment((5, 6), (6, 6), 5)])
    finding = {'description': 'Thermal relief connection to zone incomplete (layer F.Cu; zone min spoke count 2; actual 1)',
        'type': 'starved_thermal', 'severity': 'error', 'items': [
            {'uuid': ZONE, 'pos': {'x': 0, 'y': 0}}, {'uuid': PAD, 'pos': {'x': 1, 'y': 2}}]}
    scene = {'schema': 1, 'kind': 'native thermal geometry observations only', 'native_version': '10.0.0',
        'units': 'integer nanometres unless explicitly named otherwise', 'mode': 'native-thermal-contact-v1',
        'status': 'observations_complete', 'api_error_count': 0, 'board_saved': False,
        'refill_executed': False, 'drc_executed': False, 'solver_executed': False, 'source_unchanged': True,
        'board_sha256': digest(warm), 'project_sha256': '1' * 64, 'finding': copy.deepcopy(finding),
        'target_pad_uuid': PAD, 'zone_uuid': ZONE, 'net_code': 1, 'net_name': name, 'reported_layer': 'F.Cu',
        'zone_copper_layers': ['F.Cu', 'B.Cu'], 'target_position_nm': [1000000, 2000000],
        'pads': [{'uuid': PAD, 'footprint_uuid': FP, 'pad_number': '7', 'logical_terminal': [FP, '7'],
            'net_code': 1, 'net_name': name, 'position_nm': [1000000, 2000000],
            'layers': [{'canonical': 'F.Cu', 'on_layer': True, 'flash_layer': True}],
            'native_layer_geometry_qualified': False, 'unsupported_reasons': ['authored scene is not a polygon certificate']}]}
    return original, warm, base, scene, finding


class ProposalControls(unittest.TestCase):
    def rejected(self, values):
        with self.assertRaises(p.Rejected):
            q.derive(*values)

    def test_exact_component_deletion_preserves_other_nets_rules_and_inputs(self):
        values = fixture(); before = copy.deepcopy(values)
        result, record = q.derive(*values)
        self.assertEqual(values, before)
        self.assertEqual(p.immutable(result), p.immutable(values[0]))
        self.assertEqual(p.routes(result), p.routes(values[2])[:3])
        self.assertEqual(record['kept_route_ids'], sorted(map(s.route_id, p.routes(values[2])[1:3])))
        self.assertEqual(record['deleted_route_ids'], sorted(map(s.route_id, p.routes(values[2])[3:])))
        self.assertEqual(record['result_ast_sha256'], digest(result))
        self.assertEqual(record['protected_audit_after']['protected_routes'], record['protected_audit_before']['protected_routes'])
        self.assertFalse(record['native_validation_performed'])
        self.assertFalse(record['routing_accepted'])
        self.assertFalse(record['electrical_certificate'])
        reordered = copy.deepcopy(values)
        tree = reordered[2]; tree[:] = [n for n in tree if n not in p.routes(tree)] + list(reversed(p.routes(values[2])))
        _, replay = q.derive(*reordered)
        self.assertEqual(record['kept_route_ids'], replay['kept_route_ids'])
        self.assertEqual(record['deleted_route_ids'], replay['deleted_route_ids'])
        self.assertEqual(record['components'], replay['components'])

    def test_board_finding_and_native_identity_drift_refuse(self):
        for mutation in ('board', 'finding', 'pad', 'zone', 'duplicate-pad', 'footprint', 'terminal', 'report-position', 'typed-schema'):
            with self.subTest(mutation=mutation):
                values = fixture(); original, warm, base, scene, finding = values
                if mutation == 'board': scene['board_sha256'] = '0' * 64
                elif mutation == 'finding': finding['items'][0]['uuid'] = PAD
                elif mutation == 'pad': scene['target_pad_uuid'] = FP
                elif mutation == 'zone': scene['zone_uuid'] = PAD
                elif mutation == 'duplicate-pad': scene['pads'].append(copy.deepcopy(scene['pads'][0]))
                elif mutation == 'footprint': scene['pads'][0]['footprint_uuid'] = ZONE
                elif mutation == 'terminal': scene['pads'][0]['logical_terminal'][1] = '8'
                elif mutation == 'report-position':
                    finding['items'][1]['pos']['x'] = 1.000001; scene['finding'] = copy.deepcopy(finding)
                else: scene['schema'] = True
                self.rejected(values)

    def test_net_layer_and_observer_errors_are_not_ignored(self):
        for mutation in ('net-name', 'net-code', 'pad-net', 'reported-layer', 'zone-layers', 'pad-layer', 'duplicate-layer', 'version', 'saved', 'api-error', 'refilled'):
            with self.subTest(mutation=mutation):
                values = fixture(); scene = values[3]
                if mutation == 'net-name': scene['net_name'] = 'OTHER'
                elif mutation == 'net-code': scene['net_code'] = 2
                elif mutation == 'pad-net': scene['pads'][0]['net_code'] = True
                elif mutation == 'reported-layer': scene['reported_layer'] = 'B.Cu'
                elif mutation == 'zone-layers': scene['zone_copper_layers'] = ['B.Cu']
                elif mutation == 'pad-layer': scene['pads'][0]['layers'][0]['on_layer'] = False
                elif mutation == 'duplicate-layer': scene['pads'][0]['layers'].append(copy.deepcopy(scene['pads'][0]['layers'][0]))
                elif mutation == 'version': scene['native_version'] = '10.0.7'
                elif mutation == 'saved': scene['board_saved'] = True
                elif mutation == 'api-error': scene['api_error_count'] = False
                else: scene['refill_executed'] = True
                self.rejected(values)

    def test_coordinates_width_and_mixed_route_shapes_fail_closed(self):
        for value in ('0.0000001', '0.000999999999999999999999999999999999', '-0.000999999999999999999999999999999999', 'NaN', 'inf', '1/2', '1e999999999999', '1000001'):
            with self.subTest(coordinate=value):
                values = fixture(); sx.one(p.routes(values[2])[1], 'start')[1] = value
                self.rejected(values)
        for mutation in ('zero-width', 'negative-width', 'zero-length', 'via', 'bad-layer', 'duplicate-start', 'extra-coordinate', 'extra-field'):
            with self.subTest(mutation=mutation):
                values = fixture(); route = p.routes(values[2])[1]
                if mutation == 'zero-width': sx.one(route, 'width')[1] = '0'
                elif mutation == 'negative-width': sx.one(route, 'width')[1] = '-0.25'
                elif mutation == 'zero-length': sx.one(route, 'end')[1:] = sx.one(route, 'start')[1:]
                elif mutation == 'via': route[0] = 'via'
                elif mutation == 'bad-layer': sx.one(route, 'layer')[1] = '"In1.Cu"'
                elif mutation == 'duplicate-start': route.append(copy.deepcopy(sx.one(route, 'start')))
                elif mutation == 'extra-coordinate': sx.one(route, 'start').append('3')
                else: route.append(['unknown', 'yes'])
                self.rejected(values)

    def test_missing_or_near_anchor_and_unchanged_single_component_refuse(self):
        for mutation in ('one-nanometre-away', 'no-deletion', 'native-noninteger'):
            with self.subTest(mutation=mutation):
                values = fixture(); scene = values[3]
                if mutation == 'one-nanometre-away': sx.one(p.routes(values[2])[1], 'start')[1] = '1.000001'
                elif mutation == 'no-deletion': values[2][:] = values[2][:-2]
                else: scene['pads'][0]['position_nm'][0] = 1000000.0
                self.rejected(values)

    def test_eligible_bound_and_protected_or_original_geometry_mutation_refuse(self):
        values = fixture(); base = values[2]
        base[:] = [row for row in base if row not in p.routes(base)[1:]]
        base.extend(segment((1, 2 + i), (1, 3 + i), 20 + i) for i in range(q.MAX_ELIGIBLE + 1))
        self.rejected(values)
        values = fixture(); sx.one(p.routes(values[2])[0], 'end')[2] = '12'; self.rejected(values)
        values = fixture(); sx.one(sx.children(values[2], 'zone')[0], 'connect_pads')[1][1] = '0.001'; self.rejected(values)
        values = fixture(); p.routes(values[2])[2][-1] = copy.deepcopy(p.routes(values[2])[1][-1]); self.rejected(values)


if __name__ == '__main__':
    unittest.main()
