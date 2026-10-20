"""Owned pure NPTH-circle transport controls; not Native or routing proof."""
import copy
import hashlib
import unittest

from autorouter import default_targets as targets, sexpr as sx
from autorouter.adapter import _parse_dsn, _dump_dsn
from tests.test_default_targets import fixtures, inputs, SOURCE


class ImageKeepoutTests(unittest.TestCase):
    def make(self, *, four=False, fixed=False):
        raw, native, project, task = fixtures(four=four, fixed=fixed)
        tree = _parse_dsn(raw.decode())
        image = sx.children(sx.one(tree, 'library'), 'image')[0]
        layers = [row[1] for row in sx.children(sx.one(tree, 'structure'), 'layer')]
        # Project-owned schematic-free mechanical holes, no extra net terminals.
        # Their exported keepouts include the hole clearance and stay untouched.
        footprint = sx.children(task, 'footprint')[0]
        for x in ('-2000', '2000'):
            footprint.append(['pad', '""', 'np_thru_hole', 'circle',
                              ['at', str(int(x) / 1000), '-1.5'], ['size', '.75', '.75'],
                              ['drill', '.75'], ['layers', '"*.Cu"', '"*.Mask"']])
            for layer in layers:
                image.append(['keepout', '""', ['circle', layer, '1250', x, '1500']])
        return tree, native, project, task

    def args(self, parts):
        tree, native, project, task = parts
        return inputs(_dump_dsn(tree).encode(), native, project, task)

    def transform(self, parts):
        return targets.transform(*self.args(parts), source=SOURCE)

    def keepout(self, tree):
        return sx.children(sx.children(sx.one(tree, 'library'), 'image')[0], 'keepout')[0]

    def test_two_and_four_layer_keepouts_survive_exact_transform_and_protected_wiring(self):
        for four in (False, True):
            for fixed in (False, True):
                with self.subTest(four=four, fixed=fixed):
                    parts = self.make(four=four, fixed=fixed); original = copy.deepcopy(parts)
                    guided, receipt = self.transform(parts); tree = _parse_dsn(guided.decode())
                    self.assertEqual(sx.children(sx.one(tree, 'library'), 'image'),
                                     sx.children(sx.one(parts[0], 'library'), 'image'))
                    self.assertEqual(sx.one(tree, 'wiring'), sx.one(parts[0], 'wiring'))
                    self.assertEqual(parts, original)
                    self.assertEqual(targets.check(self.args(parts)[0], guided, receipt,
                                                  *self.args(parts)[1:], source=SOURCE), receipt)
                    self.assertFalse(receipt['native_execution_proven'])
                    self.assertFalse(receipt['production_support_qualified'])

    def test_image_keepout_shape_name_population_and_layer_faults_refuse(self):
        changes = [lambda k: k.__setitem__(1, 'named'),
                   lambda k: k.__delitem__(2),
                   lambda k: k.append(copy.deepcopy(k[2])),
                   lambda k: k.append(['rule', ['clearance', '1']]),
                   lambda k: k[2].__setitem__(0, 'polygon'),
                   lambda k: k[2].pop(),
                   lambda k: k[2].append('0'),
                   lambda k: k[2].__setitem__(3, ['rule', ['width', '1']])]
        changes += [lambda k, layer=layer: k[2].__setitem__(1, layer)
                    for layer in ('F.Mask', 'signal', 'In1.Cu', 'foreign', '"F.Cu"')]
        for index, change in enumerate(changes):
            with self.subTest(fault=index):
                parts = self.make(); change(self.keepout(parts[0]))
                with self.assertRaises(ValueError): self.transform(parts)

    def test_circle_dimensions_and_coordinates_require_exact_bounded_nanometres(self):
        faults = [(2, v) for v in ('0', '-1', 'NaN', 'Infinity', '-Infinity', '2147483.648',
                                   '.0001', '1e100000', '1' * 65)]
        faults += [(index, value) for index in (3, 4)
                   for value in ('NaN', 'Infinity', '2147483.648', '-2147483.648', '.0001', '"0"')]
        for index, value in faults:
            with self.subTest(index=index, value=value):
                parts = self.make(); self.keepout(parts[0])[2][index] = value
                with self.assertRaises(ValueError): self.transform(parts)
        parts = self.make(); self.keepout(parts[0])[2][3:] = ['0', '-0']
        self.transform(parts)  # Zero/signed coordinates are valid, unlike diameter.

    def test_circle_support_is_local_to_image_and_does_not_change_floor_grammar(self):
        for parent in ('structure', 'library', 'network', 'outline'):
            with self.subTest(parent=parent):
                parts = self.make(); tree = parts[0]; keepout = self.keepout(tree)
                image = sx.children(sx.one(tree, 'library'), 'image')[0]; image.remove(keepout)
                if parent == 'outline': image.append(['outline', keepout])
                else: sx.one(tree, parent).append(keepout)
                with self.assertRaises(ValueError): self.transform(parts)
        # Existing floor-only grammar remains independently closed to this form.
        with self.assertRaises(ValueError): targets.floors.grammar(self.make()[0])
        parts = self.make()
        sx.children(sx.one(parts[0], 'structure'), 'layer')[0][1] = 'foreign'
        with self.assertRaises(ValueError): self.transform(parts)

    def test_rehashed_output_and_receipt_cannot_drop_or_change_keepout_constraints(self):
        parts = self.make(fixed=True); raw, native, project, task = self.args(parts)
        guided, receipt = self.transform(parts)
        for fault in ('omit_one', 'omit_all', 'position', 'diameter', 'layer', 'add', 'receipt'):
            with self.subTest(fault=fault):
                tree = _parse_dsn(guided.decode()); rec = copy.deepcopy(receipt)
                image = sx.children(sx.one(tree, 'library'), 'image')[0]; keepout = self.keepout(tree)
                if fault == 'omit_one': image.remove(keepout)
                elif fault == 'omit_all': image[:] = [n for n in image if not isinstance(n, list) or n[0] != 'keepout']
                elif fault == 'position': keepout[2][3] = '0'
                elif fault == 'diameter': keepout[2][2] = '1'
                elif fault == 'layer': keepout[2][1] = 'B.Cu'
                elif fault == 'add': image.append(copy.deepcopy(keepout))
                else: rec['input_sha256'] = '0' * 64
                encoded = _dump_dsn(tree).encode(); rec['output_sha256'] = hashlib.sha256(encoded).hexdigest()
                with self.assertRaises(ValueError):
                    targets.check(raw, encoded, rec, native, project, task, source=SOURCE)


if __name__ == '__main__':
    unittest.main()
