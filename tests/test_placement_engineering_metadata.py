"""Owned pure metadata fixtures; formatter doubles do not qualify Native."""
import copy
import json
import unittest
import uuid

from experiments.placement_native_proposal_v1 import engineering_metadata as m


def identity(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'owned-engineering-metadata:' + name))


def uid(name):
    return ['uuid', json.dumps(identity(name))]


def fixture(*, point=True, duplicate_numbers=False):
    """Owned AST with the observed unit/no/point field shapes, not copied CAD."""
    pads = ['1', '1', '2', '2'] if duplicate_numbers else ['1', '2']
    fp = ['footprint', '"Owned:metadata-control"', ['layer', '"F.Cu"'], uid('fp'),
          ['at', '20', '10', '90'], ['attr', 'through_hole'],
          ['units', ['unit', ['name', '"A"'], ['pins', '"1"', '"2"']]],
          ['duplicate_pad_numbers_are_jumpers', 'no']]
    for index, number in enumerate(pads):
        fp.append(['pad', json.dumps(number), 'thru_hole', 'circle',
                   ['at', str(index), '0', '90'], ['size', '2', '2'], ['drill', '1'],
                   ['layers', '"*.Cu"', '"*.Mask"'], uid('pad' + str(index))])
    if point:
        fp.append(['point', ['at', '21.25', '10'], ['size', '2'],
                   ['layer', '"F.Fab"'], uid('point')])
    return fp


class EngineeringMetadataTests(unittest.TestCase):
    def capture(self, fp):
        return m.capture(fp)

    def formatted(self, fp):
        return m.c.sx.dump(fp)

    def test_exact_owned_unit_no_and_fixed_point_census(self):
        fp = fixture(); before = copy.deepcopy(fp)
        captured = self.capture(fp)
        self.assertEqual(fp, before)
        self.assertEqual(captured['units'], [{'name': 'A', 'pins': ['1', '2']}])
        self.assertEqual(captured['points'], [dict(uuid=identity('point'),
            position_nm=[21250000, 10000000], size_nm=2000000, layer='F.Fab')])
        proof = m.compare(captured, self.formatted(fp), False)
        self.assertTrue(proof['immutable_metadata_equal'])
        self.assertFalse(proof['native_execution_proven'])

    def test_unit_omission_and_zero_pad_artwork_are_explicit(self):
        fp = fixture(point=False); fp.remove(m.c.sx.one(fp, 'units'))
        fp[:] = [row for row in fp if not (type(row) is list and row[0] == 'pad')]
        record = self.capture(fp)
        self.assertFalse(record['units_present']); self.assertEqual(record['units'], [])
        self.assertEqual(record['pads'], [])

    def test_duplicate_pad_numbers_remain_separate_physical_instances(self):
        captured = self.capture(fixture(duplicate_numbers=True))
        self.assertEqual(len(captured['pads']), 4)
        self.assertEqual(sorted(row['number'] for row in captured['pads']), ['1', '1', '2', '2'])
        self.assertEqual(len({row['uuid'] for row in captured['pads']}), 4)
        self.assertEqual(captured['units'][0]['pins'], ['1', '2'])

    def test_detached_capture_validate_and_compare_do_not_mutate_inputs(self):
        fp = fixture(); captured = self.capture(fp); original = copy.deepcopy(captured)
        detached = m.validate(captured); detached['points'][0]['position_nm'][0] += 1
        self.assertEqual(captured, original)
        fp[-1][1][1] = '22'
        self.assertEqual(captured, original)
        with self.assertRaisesRegex(ValueError, 'differs'):
            m.compare(captured, self.formatted(fp), False)
        self.assertEqual(captured, original)

    def test_points_never_receive_movement_authority(self):
        fp = fixture(); captured = self.capture(fp)
        with self.assertRaisesRegex(ValueError, 'remain fixed'):
            m.compare(captured, self.formatted(fp), False, owner_moved=True)
        plain = fixture(point=False)
        self.assertTrue(m.compare(self.capture(plain), self.formatted(plain), False,
                                  owner_moved=True)['immutable_metadata_equal'])

    def test_fixed_point_owner_pose_is_independently_bound(self):
        captured = self.capture(fixture())
        for field, value in (('x', '21'), ('y', '11'), ('angle', '180'), ('side', '"B.Cu"')):
            fp = fixture(); at = m.c.sx.one(fp, 'at')
            if field == 'x': at[1] = value
            if field == 'y': at[2] = value
            if field == 'angle': at[3] = value
            if field == 'side': m.c.sx.one(fp, 'layer')[1] = value
            # No caller movement hint is needed to detect the changed owner.
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'differs'):
                m.compare(captured, self.formatted(fp), False)
        plain = fixture(point=False); original = self.capture(plain)
        m.c.sx.one(plain, 'at')[1:3] = ['21', '11']
        self.assertTrue(m.compare(original, self.formatted(plain), False)['immutable_metadata_equal'])

    def test_single_explicit_no_is_mandatory_and_no_jumper_group_is_admitted(self):
        for fault in ('missing', 'yes', 'bool', 'empty', 'extra', 'duplicate', 'groups'):
            fp = fixture(); flag = m.c.sx.one(fp, 'duplicate_pad_numbers_are_jumpers')
            if fault == 'missing': fp.remove(flag)
            if fault == 'yes': flag[1] = 'yes'
            if fault == 'bool': flag[1] = False
            if fault == 'empty': flag[:] = flag[:1]
            if fault == 'extra': flag.append('no')
            if fault == 'duplicate': fp.append(copy.deepcopy(flag))
            if fault == 'groups': fp.append(['jumper_pad_groups', ['"1"', '"2"']])
            with self.subTest(fault=fault), self.assertRaises(ValueError): self.capture(fp)

    def test_unit_mapping_is_closed_unique_and_bound_to_actual_pads(self):
        for fault in ('empty', 'unknown', 'duplicate-name', 'duplicate-pin', 'other-unit-pin',
                      'unknown-pin', 'missing-name', 'missing-pins', 'nested-pin', 'name-extra'):
            fp = fixture(); units = m.c.sx.one(fp, 'units'); unit = units[1]
            if fault == 'empty': units[:] = units[:1]
            if fault == 'unknown': unit.append(['swap', 'yes'])
            if fault == 'duplicate-name': units.append(copy.deepcopy(unit))
            if fault == 'duplicate-pin': unit[-1].append('"1"')
            if fault == 'other-unit-pin': units.append(['unit', ['name', '"B"'], ['pins', '"1"']])
            if fault == 'unknown-pin': unit[-1][-1] = '"3"'
            if fault == 'missing-name': unit.remove(unit[1])
            if fault == 'missing-pins': unit.pop()
            if fault == 'nested-pin': unit[-1].append(['pin', '"2"'])
            if fault == 'name-extra': unit[1].append('"B"')
            with self.subTest(fault=fault), self.assertRaises(ValueError): self.capture(fp)

    def test_uuid_census_includes_physical_pads_points_and_other_children(self):
        for fault in ('owner', 'pad-pad', 'point-owner', 'point-pad', 'point-graphic',
                      'missing-point', 'bad-point', 'duplicate-singleton'):
            fp = fixture(); point = m.c.sx.one(fp, 'point'); pads = m.c.sx.children(fp, 'pad')
            if fault == 'owner': m.c.sx.one(fp, 'uuid')[1] = '"NOT-UUID"'
            if fault == 'pad-pad': pads[1][-1][1] = pads[0][-1][1]
            if fault == 'point-owner': point[-1][1] = m.c.sx.one(fp, 'uuid')[1]
            if fault == 'point-pad': point[-1][1] = pads[0][-1][1]
            if fault == 'point-graphic': fp.append(['fp_line', uid('point')])
            if fault == 'missing-point': point.pop()
            if fault == 'bad-point': point[-1][1] = '"not-uuid"'
            if fault == 'duplicate-singleton': point.append(copy.deepcopy(point[-1]))
            with self.subTest(fault=fault), self.assertRaises(ValueError): self.capture(fp)

    def test_fixed_points_require_exact_supported_geometry_and_passive_layers(self):
        for fault in ('rotation', 'nan', 'fractional-nm', 'oversize-coordinate', 'zero-size',
                      'oversize-size', 'copper', 'mask', 'unknown', 'duplicate-layer'):
            fp = fixture(); point = m.c.sx.one(fp, 'point')
            if fault == 'rotation': point[1].append('90')
            if fault == 'nan': point[1][1] = 'NaN'
            if fault == 'fractional-nm': point[1][1] = '0.0000001'
            if fault == 'oversize-coordinate': point[1][1] = '2001'
            if fault == 'zero-size': point[2][1] = '0'
            if fault == 'oversize-size': point[2][1] = '101'
            if fault == 'copper': point[3][1] = '"F.Cu"'
            if fault == 'mask': point[3][1] = '"F.Mask"'
            if fault == 'unknown': point.append(['locked', 'yes'])
            if fault == 'duplicate-layer': point.append(copy.deepcopy(point[3]))
            with self.subTest(fault=fault), self.assertRaises(ValueError): self.capture(fp)

    def test_unknown_root_and_hazardous_attributes_are_refused(self):
        for addition in (['clearance', '0'], ['jumper_pad_groups'], ['attr', 'power'],
                         ['attr', 'through_hole', 'through_hole']):
            fp = fixture()
            if addition[0] == 'attr': fp.remove(m.c.sx.one(fp, 'attr'))
            fp.append(addition)
            with self.subTest(addition=addition), self.assertRaises(ValueError): self.capture(fp)

    def test_native_text_evidence_is_owner_pad_and_metadata_bound(self):
        expected = self.capture(fixture())
        for fault in ('owner', 'pad-number', 'pad-id', 'units-missing', 'unit-name', 'pin-order',
                      'flag-missing', 'point-missing', 'point-size', 'point-identity', 'extra-point'):
            fp = fixture()
            if fault == 'owner': m.c.sx.one(fp, 'uuid')[1] = json.dumps(identity('other-owner'))
            if fault == 'pad-number': m.c.sx.children(fp, 'pad')[0][1] = '"3"'
            if fault == 'pad-id': m.c.sx.children(fp, 'pad')[0][-1][1] = json.dumps(identity('other-pad'))
            if fault == 'units-missing': fp.remove(m.c.sx.one(fp, 'units'))
            if fault == 'unit-name': m.c.sx.one(fp, 'units')[1][1][1] = '"B"'
            if fault == 'pin-order': m.c.sx.one(fp, 'units')[1][-1][1:] = ['"2"', '"1"']
            if fault == 'flag-missing': fp.remove(m.c.sx.one(fp, 'duplicate_pad_numbers_are_jumpers'))
            if fault == 'point-missing': fp.remove(m.c.sx.one(fp, 'point'))
            if fault == 'point-size': m.c.sx.one(fp, 'point')[2][1] = '2.001'
            if fault == 'point-identity': m.c.sx.one(fp, 'point')[-1][1] = json.dumps(identity('other-point'))
            if fault == 'extra-point':
                point = copy.deepcopy(m.c.sx.one(fp, 'point')); point[-1][1] = json.dumps(identity('other-point')); fp.append(point)
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                m.compare(expected, self.formatted(fp), False)

    def test_actual_bool_getter_and_movement_flag_cannot_be_coerced(self):
        fp = fixture(); captured = self.capture(fp)
        for flag in (True, 0, 1, 'no', None):
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                m.compare(captured, self.formatted(fp), flag)
        for moved in (0, 1, None, 'false'):
            with self.subTest(moved=moved), self.assertRaises(ValueError):
                m.compare(captured, self.formatted(fp), False, owner_moved=moved)

    def test_record_tampering_and_noncanonical_wire_data_refuse(self):
        record = self.capture(fixture())
        for fault in ('policy', 'schema-bool', 'points-fixed', 'flag', 'extra', 'point-bool',
                      'unit-unknown', 'pad-order', 'point-size-infinite', 'point-pose'):
            changed = copy.deepcopy(record)
            if fault == 'policy': changed['policy'] += '-other'
            if fault == 'schema-bool': changed['schema'] = True
            if fault == 'points-fixed': changed['points_fixed'] = False
            if fault == 'flag': changed['duplicate_pad_numbers_are_jumpers'] = True
            if fault == 'extra': changed['accept'] = True
            if fault == 'point-bool': changed['points'][0]['position_nm'][0] = True
            if fault == 'unit-unknown': changed['units'][0]['pins'].append('3')
            if fault == 'pad-order': changed['pads'].reverse()
            if fault == 'point-size-infinite': changed['points'][0]['size_nm'] = float('inf')
            if fault == 'point-pose': changed['point_owner_pose']['angle'] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError): m.validate(changed)

    def test_bounded_inputs_and_aliases_refuse(self):
        for fp in (['footprint', '"x"', *[uid(str(i)) for i in range(m.MAX_NODES)]],
                   ['footprint', '"' + 'x' * m.MAX_BYTES + '"']):
            with self.assertRaises(ValueError): self.capture(fp)
        fp = fixture(); fp.append(fp)
        with self.assertRaises(ValueError): self.capture(fp)
        captured = self.capture(fixture())
        for text in ('', '(' + 'x' * m.MAX_BYTES + ')', 'not sexpr', self.formatted(fixture()) + '()'):
            with self.subTest(size=len(text)), self.assertRaises(ValueError):
                m.compare(captured, text, False)


if __name__ == '__main__':
    unittest.main()
