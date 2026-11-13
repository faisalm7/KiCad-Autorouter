"""Small authored pure controls; outside normal tests discovery, no Native proof."""
import copy
import unittest
from unittest.mock import patch

from autorouter import adapter, pipeline as p, sexpr as sx
from experiments.selected_unselected_plane_v1 import policy as m


def source(modern=False):
    board = ['kicad_pcb', ['version', '20260206' if modern else '20241229'],
             ['layers', ['0', '"F.Cu"', 'signal'], ['2', '"B.Cu"', 'signal']]]
    if not modern:
        board.extend([['net', '0', '""'], *[['net', str(i), '"'+name+'"']
                      for i, name in enumerate(('ACTIVE', 'quiet reference', 'GND'), 1)]])
    for i, name in enumerate(('ACTIVE', 'quiet reference', 'GND'), 1):
        net = ['net', '"'+name+'"'] if modern else ['net', str(i), '"'+name+'"']
        board.append(['footprint', '"Owned"', ['pad', '"1"', 'smd', 'rect', net]])
        zone_net = ['net', '"'+name+'"'] if modern else ['net', str(i)]
        zone = ['zone', zone_net, ['layer', '"F.Cu"'], ['polygon', ['pts', ['xy', '0', '0'], ['xy', '5', '0'], ['xy', '5', '5']]]]
        if not modern: zone.append(['net_name', '"'+name+'"'])
        board.append(zone)
    return (sx.dump(board)+'\n').encode()


def dsn():
    return b'''(pcb owned (parser (string_quote ")) (unit um) (resolution um 10)
    (structure (layer F.Cu (type signal) (property (index 0)))
      (layer B.Cu (type signal) (property (index 1)))
      (boundary (rect pcb 0 0 10000 10000))
      (plane ACTIVE (polygon F.Cu 0 0 0 1000 0 1000 1000))
      (keepout exact (rect F.Cu 1 2 3 4))
      (plane "quiet reference" (polygon F.Cu 0 1000 0 2000 0 2000 1000))
      (unknown (plane nested_unknown must_survive))
      (plane ACTIVE (polygon F.Cu 0 0 2000 1000 2000 1000 3000))
      (plane GND (polygon F.Cu 0 2000 2000 3000 2000 3000 3000))
      (plane "quiet reference" (polygon F.Cu 0 3000 0 4000 0 4000 1000))
      (rule (width 200) (clearance 200)))
    (placement (component Owned (place J1 0 0 front 0)))
    (library (image Owned (pin PAD 1 0 0)))
    (network (net ACTIVE (pins J1-1)) (net "quiet reference" (pins J2-1))
      (net GND (pins J3-1)) (class kicad_default ACTIVE "quiet reference" GND
      (circuit (use_via V)) (rule (width 200) (clearance 200))))
    (wiring (wire (path B.Cu 200 1 2 3 4) (net GND) (type fix))))'''


class PlanePolicyControls(unittest.TestCase):
    def setUp(self):
        self.source = source(); self.dsn = dsn(); self.names = ['ACTIVE']

    def apply(self, **changed):
        source_raw = changed.get('source', self.source); dsn_raw = changed.get('dsn', self.dsn)
        names = changed.get('names', self.names)
        context = changed['context'] if 'context' in changed else m.capture(source_raw, dsn_raw, names)
        return m.apply(source_raw, dsn_raw, names, context)

    def test_mixed_multiple_planes_preserve_exact_order_and_every_nonplane_node(self):
        before = copy.deepcopy((self.source, self.dsn, self.names))
        emitted, record = self.apply(); old = adapter._parse_dsn(self.dsn.decode()); new = adapter._parse_dsn(emitted.decode())
        old_structure = sx.one(old, 'structure'); new_structure = sx.one(new, 'structure')
        expected = [row for row in sx.children(old_structure, 'plane') if row[1] != 'ACTIVE']
        self.assertEqual(sx.children(new_structure, 'plane'), expected)
        for structure in (old_structure, new_structure):
            structure[:] = [row for row in structure if not (type(row) is list and row and row[0] == 'plane')]
        self.assertEqual(old, new)
        self.assertEqual([row['action'] for row in record['planes']], ['omit','retain','omit','retain','retain'])
        self.assertEqual((self.source, self.dsn, self.names), before)
        for field in ('native_export_verified','original_design_validated','routing_accepted'):
            self.assertIs(record[field], False)

    def test_purpose_names_never_control_selection(self):
        emitted, record = self.apply(names=['GND'])
        self.assertEqual([row['net_name'] for row in record['planes'] if row['action'] == 'omit'], ['GND'])
        self.assertEqual(len(sx.children(sx.one(adapter._parse_dsn(emitted.decode()), 'structure'), 'plane')), 4)

    def test_all_selected_omits_all_direct_planes_but_not_nested_unknowns(self):
        emitted, _ = self.apply(names=['GND','ACTIVE','quiet reference'])
        structure = sx.one(adapter._parse_dsn(emitted.decode()), 'structure')
        self.assertFalse(sx.children(structure, 'plane'))
        self.assertEqual(sx.one(structure, 'unknown'), ['unknown', ['plane','nested_unknown','must_survive']])

    def test_modern_and_legacy_source_identities_are_supported_separately(self):
        for modern in (False, True):
            raw = source(modern); context = m.capture(raw, self.dsn, self.names)
            self.assertEqual(context['selection_binding']['source_net_mapping'], 'modern_names' if modern else 'legacy_table')
            m.apply(raw, self.dsn, self.names, context)

    def test_source_DSN_and_ordered_selection_changes_refuse_existing_context(self):
        context = m.capture(self.source, self.dsn, ['ACTIVE','GND'])
        for source_raw, dsn_raw, names in ((self.source+b'\n',self.dsn,['ACTIVE','GND']),
                (self.source,self.dsn+b'\n',['ACTIVE','GND']),
                (self.source,self.dsn,['GND','ACTIVE']), (self.source,self.dsn,['ACTIVE'])):
            with self.subTest(names=names), self.assertRaises(ValueError): m.apply(source_raw, dsn_raw, names, context)

    def test_caller_context_mutation_is_not_authority(self):
        before = m.capture(self.source, self.dsn, self.names)
        for mode in ('action','hash','selection','authority','extra'):
            context = copy.deepcopy(before)
            if mode == 'action': context['planes'][0]['action'] = 'retain'
            elif mode == 'hash': context['source_sha256'] = '0'*64
            elif mode == 'selection': context['selection_binding']['requested_names'] = ['GND']
            elif mode == 'authority': context['native_export_verified'] = True
            else: context['extra'] = True
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.apply(context=context)

    def test_unknown_net_incoherent_census_and_missing_source_zone_refuse(self):
        variants = [self.dsn.replace(b'(plane GND', b'(plane UNKNOWN'),
                    self.dsn.replace(b'(net GND (pins', b'(net OTHER (pins'),
                    self.dsn.replace(b'ACTIVE "quiet reference" GND', b'ACTIVE "quiet reference" GND GND')]
        for raw in variants:
            with self.subTest(raw=raw), self.assertRaises((ValueError, p.Rejected)): m.capture(self.source, raw, self.names)
        board = sx.parse(self.source.decode()); board.remove(sx.children(board,'zone')[-1])
        with self.assertRaises(ValueError): m.capture((sx.dump(board)+'\n').encode(), self.dsn, self.names)

    def test_malformed_unknown_shape_layer_and_numeric_semantics_refuse(self):
        for before, after in ((b'(plane ACTIVE (polygon',b'(plane ACTIVE malformed (polygon'),
                (b'(polygon F.Cu 0 0 0 1000',b'(circle F.Cu 0 0 0 1000'),
                (b'(polygon F.Cu 0 0 0 1000',b'(polygon In1.Cu 0 0 0 1000'),
                (b'(polygon F.Cu 0 0 0 1000',b'(polygon F.Cu 1 0 0 1000'),
                (b'(polygon F.Cu 0 0 0 1000',b'(polygon F.Cu 0 NaN 0 1000'),
                (b'(polygon F.Cu 0 0 0 1000',b'(polygon F.Cu 0 2000001 0 1000'),
                (b'1000 0 1000 1000)',b'1000 0 1000)')):
            raw = self.dsn.replace(before, after, 1)
            with self.subTest(after=after), self.assertRaises(ValueError): m.capture(self.source, raw, self.names)

    def test_coordinate_bound_is_exact_and_independent_of_decimal_precision(self):
        from decimal import localcontext
        for precision in (6, 28):
            for coordinate in (b'2000000.000000000000000000000001',
                               b'2000000.1', b'-2000000.1', b'1e1000000'):
                raw = self.dsn.replace(b'(polygon F.Cu 0 0 0 1000',
                    b'(polygon F.Cu 0 ' + coordinate + b' 0 1000', 1)
                with self.subTest(precision=precision, coordinate=coordinate), localcontext() as context:
                    context.prec = precision
                    with self.assertRaises(ValueError):
                        m.capture(self.source, raw, self.names)

    def test_legacy_zone_and_terminal_aliases_refuse(self):
        for mode in ('zone_name','pad_name','duplicate_code','wrong_layer'):
            board = sx.parse(self.source.decode())
            if mode == 'zone_name': sx.one(sx.children(board,'zone')[0],'net_name')[1] = '"GND"'
            elif mode == 'pad_name': sx.one(sx.one(sx.children(board,'footprint')[0],'pad'),'net')[2] = '"GND"'
            elif mode == 'duplicate_code': board.append(['net','1','"OTHER"'])
            else: sx.one(board,'layers')[2][0] = '31'
            with self.subTest(mode=mode), self.assertRaises((ValueError, p.Rejected)): m.capture((sx.dump(board)+'\n').encode(), self.dsn, self.names)

    def test_absent_planes_is_explicit_zero_delta(self):
        tree = adapter._parse_dsn(self.dsn.decode()); structure = sx.one(tree,'structure')
        structure[:] = [row for row in structure if not (type(row)is list and row and row[0]=='plane')]
        raw = adapter._dump_dsn(tree).encode(); context = m.capture(self.source,raw,self.names)
        emitted, record = m.apply(self.source,raw,self.names,context)
        self.assertEqual(adapter._parse_dsn(emitted.decode()),tree); self.assertEqual(record['planes'],[])

    def test_size_and_context_bounds_fail_before_unbounded_work(self):
        with patch.object(m.sx,'parse',side_effect=AssertionError('parser must not be reached')):
            with self.assertRaises(ValueError): m.capture(b'x'*(m.MAX_BYTES+1),self.dsn,self.names)
        context = m.capture(self.source,self.dsn,self.names); context['extra'] = 'x'*m.MAX_CONTEXT_BYTES
        with self.assertRaisesRegex(ValueError,'context exceeds'): self.apply(context=context)
        cycle = {}; cycle['self'] = cycle
        with self.assertRaisesRegex(ValueError,'context exceeds'): self.apply(context=cycle)


if __name__ == '__main__': unittest.main(verbosity=2)
