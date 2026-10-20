"""Owned geometry controls only; no Native contact or routing proof."""
import copy
import unittest
import uuid

from autorouter import chain_proposals as cp, pipeline as p, sexpr as sx
from experiments.qfn_escape_seed_v1 import seed as q


TEST_NAMESPACE = uuid.UUID('5d7e7758-4b99-4ec8-9735-069384767273')
TARGETS = dict(width_nm=200000, clearance_nm=200000,
               via_diameter_nm=600000, via_drill_nm=300000)


def uid(key):
    return '"' + str(uuid.uuid5(TEST_NAMESPACE, key)) + '"'


def pad(key, number, x, y, *, net='N', size=('0.6', '0.2'), angle=None):
    at = ['at', str(x), str(y)] + ([] if angle is None else [str(angle)])
    return ['pad', '"' + str(number) + '"', 'smd', 'rect', at,
            ['size', *size], ['layers', '"F.Cu"', '"F.Paste"', '"F.Mask"'],
            ['net', '"' + net + '"'], ['uuid', uid(key)]]


def package(key='package', count=8):
    pads = []
    for i in range(count):
        # Two perimeter rows, with every centre's dominant axis along X.
        side = -2 if i % 2 == 0 else 2
        y = q._mm((i // 2) * 50000 - (count // 2 - 1) * 25000)
        pads.append(pad(key + '/pad/' + str(i), i + 1, side, y))
    return ['footprint', '"Owned:Perimeter"', ['layer', '"F.Cu"'],
            ['at', '10', '20'], ['uuid', uid(key)],
            ['property', '"Reference"', '"OWNED"'], *pads]


def board(*footprints):
    return ['kicad_pcb', ['version', '20260206'],
            ['layers', ['0', '"F.Cu"', 'signal'], ['2', '"B.Cu"', 'signal'],
             ['9', '"F.Paste"', 'user'], ['11', '"F.Mask"', 'user']],
            *footprints]


def segment(key, *, locked=False):
    return ['segment', ['start', '1', '1'], ['end', '2', '1'],
            ['width', '0.3'], ['layer', '"F.Cu"'], ['net', '"N"'],
            ['uuid', uid(key)], *([['locked', 'yes']] if locked else [])]


def geometries(metadata):
    return sorted((tuple(row['start_nm']), tuple(row['end_nm']), row['width_nm'])
                  for row in metadata['seeds'])


class EscapeSeedControls(unittest.TestCase):
    def generate(self, task=None, protected=None, targets=None):
        return q.generate(board(package()) if task is None else task,
                          [] if protected is None else protected,
                          TARGETS if targets is None else targets)

    def test_exact_outward_length_width_and_nonadmitting_receipt(self):
        task = board(package()); before = copy.deepcopy(task)
        out, info = self.generate(task)
        self.assertEqual(task, before)
        self.assertEqual(info['generated_count'], 8)
        self.assertEqual(p.immutable(out), p.immutable(task))
        self.assertFalse(info['accepted']); self.assertFalse(info['routing_accepted'])
        self.assertFalse(info['contact_or_clearance_proven'])
        self.assertTrue(info['original_source_and_targets_binding_required'])
        for row, route in zip(info['seeds'], p.routes(out)):
            start, end = row['start_nm'], row['end_nm']
            self.assertEqual(abs(end[0] - start[0]), 800000)  # .3 + .2 + .3 mm.
            self.assertEqual(start[1], end[1])
            self.assertEqual(end[0] > start[0], start[0] > 10000000)
            self.assertEqual(cp.nm(sx.one(route, 'width')[1]), 200000)
            self.assertEqual(sx.one(route, 'layer'), ['layer', '"F.Cu"'])
            self.assertEqual(route[0], 'segment'); self.assertFalse(p.locked(route))
        self.assertEqual(self.generate(task), (out, info))

    def test_whole_task_strips_reference_and_keeps_exact_protected_ast(self):
        protected = segment('protected', locked=True)
        source = board(package()); source.extend([segment('reference'), protected])
        untouched = copy.deepcopy(source)
        with self.assertRaises(ValueError): self.generate(source, [protected])
        task = p.routing_task(source, 'whole_board_unlocked_routing')
        out, info = self.generate(task, [protected])
        self.assertEqual(source, untouched)
        self.assertEqual(p.routes(out)[0], protected)
        self.assertEqual(info['protected_count'], 1)
        self.assertEqual(p.immutable(out), p.immutable(source))
        changed = copy.deepcopy(source)
        sx.one(p.routes(changed)[0], 'end')[1:] = ['97', '-43']
        self.assertEqual(self.generate(p.routing_task(changed, 'whole_board_unlocked_routing'), [protected]), (out, info))
        for wrong in ([], [segment('other', locked=True)], [segment('reference')]):
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                self.generate(task, wrong)
        unlocked = segment('unlocked')
        with self.assertRaises(ValueError): self.generate(board(package(), unlocked), [unlocked])

    def test_no_name_reference_or_input_order_selection(self):
        task = board(package('one'), package('two'))
        _, before = self.generate(task)
        changed = copy.deepcopy(task)
        for fp in sx.children(changed, 'footprint'):
            fp[1] = '"Other:StillGeometry"'
            sx.one(fp, 'property')[2] = '"J995"'
            for node in sx.children(fp, 'pad'):
                sx.one(node, 'net')[1] = '"uninterpreted renamed net"'
        _, after = self.generate(changed)
        self.assertEqual(before['generated_count'], 16)
        self.assertEqual(geometries(before), geometries(after))
        changed[3:] = list(reversed(changed[3:]))
        self.assertEqual(geometries(self.generate(changed)[1]), geometries(after))

    def test_roundrect_and_ninety_degree_long_axis_are_equivalent(self):
        task = board(package()); expected = geometries(self.generate(task)[1])
        for node in sx.children(sx.children(task, 'footprint')[0], 'pad'):
            node[3] = 'roundrect'; node.append(['roundrect_rratio', '0.25'])
            sx.one(node, 'at').append('90'); sx.one(node, 'size')[1:] = ['0.2', '0.6']
        self.assertEqual(geometries(self.generate(task)[1]), expected)
        for angle in ('-90', '270', '450'):
            for node in sx.children(sx.children(task, 'footprint')[0], 'pad'):
                sx.one(node, 'at')[3] = angle
            self.assertEqual(geometries(self.generate(task)[1]), expected)

    def test_y_axis_perimeter_is_outward_and_square_center_diagonal_skip(self):
        fp = package(); pads = sx.children(fp, 'pad')
        for i, node in enumerate(pads):
            sx.one(node, 'at')[1:3] = [str((i // 2) / 10), '-2' if i % 2 == 0 else '2']
            sx.one(node, 'size')[1:] = ['0.2', '0.6']
        _, info = self.generate(board(fp))
        self.assertEqual(info['generated_count'], 8)
        self.assertTrue(all(abs(r['end_nm'][1] - r['start_nm'][1]) == 800000
                            and r['end_nm'][0] == r['start_nm'][0] for r in info['seeds']))
        # Additional connected copper is preserved, but never seeded by guessing an axis.
        fp.extend([pad('centre', 9, 0, 0, size=('1', '1')),
                   pad('diagonal', 10, 2, 2), pad('interior', 11, 1, '0.1'),
                   pad('square', 12, 2, 0, size=('0.2', '0.2'))])
        _, info = self.generate(board(fp))
        skipped = {r['pad_uuid'] for r in info['skips']}
        self.assertTrue({sx.unquote(uid(k)) for k in ('centre', 'diagonal', 'interior', 'square')} <= skipped)

    def test_net_requires_two_real_logical_terminals_not_two_pad_shapes(self):
        fp = package()
        for node in sx.children(fp, 'pad'):
            node[1] = '"1"'
        _, info = self.generate(board(fp))
        self.assertEqual(info['generated_count'], 0)
        self.assertEqual(len(info['skips']), 8)
        # A second real PTH terminal counts, but is never selected as a seed.
        remote = ['footprint', '"Owned:PTH"', ['layer', '"B.Cu"'], ['at', '20', '30'],
                  ['uuid', uid('remote')],
                  ['pad', '"1"', 'thru_hole', 'circle', ['at', '0', '0'],
                   ['size', '1', '1'], ['drill', '0.4'], ['layers', '"*.Cu"'],
                   ['net', '"N"'], ['uuid', uid('remote/pad')]]]
        self.assertEqual(self.generate(board(fp, remote))[1]['generated_count'], 8)
        sx.one(sx.children(fp, 'pad')[0], 'net')[1] = '"different"'
        with self.assertRaises(ValueError): self.generate(board(fp, remote))

    def test_nonconnected_mechanical_pad_is_not_a_real_terminal_or_geometry_candidate(self):
        fp = package(); mechanical = pad('mechanical', '', 0, 0, size=('2', '2'))
        mechanical[3] = 'circle'; mechanical.remove(sx.one(mechanical, 'net')); fp.append(mechanical)
        out, info = self.generate(board(fp))
        self.assertEqual(info['generated_count'], 8)
        self.assertEqual(p.immutable(out), p.immutable(board(fp)))

    def test_canonical_numbered_net_table_is_retained_without_aliasing(self):
        task = board(package()); task[1] = ['version', '20241229']
        task[3:3] = [['net', '0', '""'], ['net', '1', '"N"']]
        for node in sx.children(sx.children(task, 'footprint')[0], 'pad'):
            sx.one(node, 'net')[1:] = ['1', '"N"']
        out, info = self.generate(task)
        self.assertEqual(info['generated_count'], 8)
        self.assertTrue(all(sx.one(r, 'net') == ['net', '1', '"N"'] for r in p.routes(out)))
        sx.one(sx.children(sx.children(task, 'footprint')[0], 'pad')[0], 'net')[2] = '"wrong"'
        with self.assertRaises(ValueError): self.generate(task)

    def test_package_population_and_global_seed_limit_never_accept_prefix(self):
        for count, expected in ((7, 0), (8, 8), (64, 64), (65, 0)):
            with self.subTest(count=count):
                self.assertEqual(self.generate(board(package(count=count)))[1]['generated_count'], expected)
        task = board(*(package(str(i)) for i in range(32)))
        self.assertEqual(self.generate(task)[1]['generated_count'], 256)
        task.append(package('overflow')); before = copy.deepcopy(task)
        with self.assertRaises(ValueError): self.generate(task)
        self.assertEqual(task, before)

    def test_unsupported_package_placement_and_footprint_overrides_are_visible(self):
        mutations = [lambda fp: sx.one(fp, 'layer').__setitem__(1, '"B.Cu"'),
                     lambda fp: sx.one(fp, 'at').append('90')]
        for name in ('clearance', 'zone_connect', 'net_tie_pad_groups', 'padstack'):
            mutations.append(lambda fp, name=name: fp.append([name, '0']))
        for mutate in mutations:
            task = board(package()); mutate(sx.children(task, 'footprint')[0])
            _, info = self.generate(task)
            self.assertEqual(info['generated_count'], 0); self.assertTrue(info['skips'])

    def test_pad_overrides_shape_orientation_and_nonexact_dimensions_skip_package(self):
        mutations = [lambda n: n.__setitem__(3, 'trapezoid'),
                     lambda n: sx.one(n, 'at').append('45'),
                     lambda n: sx.one(n, 'size').__setitem__(1, 'NaN'),
                     lambda n: sx.one(n, 'size').__setitem__(1, '0.0000001'),
                     lambda n: sx.one(n, 'layers').append('"B.Cu"'),
                     lambda n: n.append(['size', '0.6', '0.2'])]
        for key in ('clearance', 'rect_delta', 'drill', 'padstack', 'solder_mask_margin'):
            mutations.append(lambda n, key=key: n.append([key, '0']))
        for mutate in mutations:
            task = board(package()); mutate(sx.children(sx.children(task, 'footprint')[0], 'pad')[0])
            _, info = self.generate(task)
            self.assertEqual(info['generated_count'], 0); self.assertTrue(info['skips'])

    def test_pad_extent_width_and_roundrect_ratio_are_not_rounded_or_weakened(self):
        for value in ('0.600001', '0.2'):
            task = board(package())
            for node in sx.children(sx.children(task, 'footprint')[0], 'pad'):
                sx.one(node, 'size')[1] = value
            self.assertEqual(self.generate(task)[1]['generated_count'], 0)
        for ratio in (None, '-0.1', '0.500001', 'NaN'):
            task = board(package()); node = sx.children(sx.children(task, 'footprint')[0], 'pad')[0]
            node[3] = 'roundrect'
            if ratio is not None: node.append(['roundrect_rratio', ratio])
            self.assertEqual(self.generate(task)[1]['generated_count'], 0)
        wider = dict(TARGETS, width_nm=200001)
        self.assertEqual(self.generate(targets=wider)[1]['generated_count'], 0)

    def test_exact_target_map_type_bounds_and_via_half_extent(self):
        bad = [None, [], dict(TARGETS, extra=1), {k: v for k, v in TARGETS.items() if k != 'clearance_nm'}]
        for key in TARGETS:
            for value in (True, 0, -1, 1.0, '200000', 2147483648):
                bad.append(dict(TARGETS, **{key: value}))
        bad.extend([dict(TARGETS, via_diameter_nm=600001), dict(TARGETS, via_drill_nm=600000)])
        for targets in bad:
            with self.subTest(targets=targets), self.assertRaises(ValueError):
                q.generate(board(package()), [], targets)

    def test_copper_identity_is_not_guessed_from_alias_type_or_layer_count(self):
        mutations = [lambda rows: rows[1].__setitem__(2, 'mixed'),
                     lambda rows: rows[2].__setitem__(2, 'power'),
                     lambda rows: rows[1].append('"upper_trace"'),
                     lambda rows: rows.insert(2, ['4', '"In1.Cu"', 'signal']),
                     lambda rows: rows.append(copy.deepcopy(rows[1])),
                     lambda rows: rows.__setitem__(slice(1, 3), list(reversed(rows[1:3])))]
        for mutate in mutations:
            task = board(package()); mutate(sx.one(task, 'layers'))
            with self.assertRaises(ValueError): self.generate(task)

    def test_noncopper_display_names_are_preserved_without_copper_alias_authority(self):
        task=board(package());sx.one(task,'layers')[3].append('"Owned paste display"')
        out,info=self.generate(task)
        self.assertEqual(info['generated_count'],8)
        self.assertEqual(p.immutable(out),p.immutable(task))
        self.assertEqual(sx.one(out,'layers'),sx.one(task,'layers'))
        sx.one(task,'layers')[3][-1]='""'
        with self.assertRaises(ValueError):self.generate(task)

    def test_square_solid_zone_center_is_untouched_unseeded_and_visible(self):
        fp=package();center=pad('solid-center',9,0,0,size=('1','1'))
        center.append(['zone_connect','2']);fp.append(center);task=board(fp)
        out,info=self.generate(task)
        self.assertEqual(info['generated_count'],8)
        self.assertEqual(p.immutable(out),p.immutable(task))
        self.assertIn(dict(footprint_uuid=sx.unquote(uid('package')),pad_uuid=sx.unquote(uid('solid-center')),reason='unchanged_square_center_solid_zone_pad'),info['skips'])
        for mutate in (lambda n:sx.one(n,'zone_connect').__setitem__(1,'1'),
                       lambda n:sx.one(n,'at').__setitem__(1,'0.1'),
                       lambda n:sx.one(n,'size').__setitem__(1,'1.1'),
                       lambda n:n.append(['clearance','0']),
                       lambda n:sx.one(n,'at').append('45')):
            bad=copy.deepcopy(task);mutate(sx.children(sx.children(bad,'footprint')[0],'pad')[-1])
            self.assertEqual(self.generate(bad)[1]['generated_count'],0)

    def test_uuid_identity_collision_missing_and_duplicate_refuse(self):
        task = board(package()); out, info = self.generate(task)
        collision = copy.deepcopy(task)
        collision.append(['property', '"owned marker"', ['uuid', '"' + info['seeds'][0]['segment_uuid'] + '"']])
        with self.assertRaises(ValueError): self.generate(collision)
        for replacement in (None, uid('package'), '"not-a-uuid"', '"00000000-0000-0000-0000-000000000000"'):
            bad = copy.deepcopy(task); first = sx.children(sx.children(bad, 'footprint')[0], 'pad')[0]
            if replacement is None: first.remove(sx.one(first, 'uuid'))
            else: sx.one(first, 'uuid')[1] = replacement
            with self.assertRaises(ValueError): self.generate(bad)
        self.assertEqual(len({sx.one(r, 'uuid')[1] for r in p.routes(out)}), 8)

    def test_detached_outputs_targets_and_derived_fill_refusal(self):
        task = board(package()); targets = dict(TARGETS)
        out, info = self.generate(task, targets=targets)
        saved = copy.deepcopy((out, info))
        sx.one(sx.children(task, 'footprint')[0], 'at')[1] = '99'; targets['width_nm'] = 99
        self.assertEqual((out, info), saved)
        out.append(['property', '"result only"', '"changed"']); info['targets']['width_nm'] = 7
        self.assertEqual(targets['width_nm'], 99)
        dirty = board(package()); dirty.append(['zone', ['filled_polygon', ['pts', ['xy', '0', '0']]]])
        with self.assertRaises(ValueError): self.generate(dirty)


if __name__ == '__main__':
    unittest.main()
