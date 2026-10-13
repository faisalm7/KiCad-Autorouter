"""Scope hint preserves pins, physical obstacles and full copied class rules."""
import unittest
from autorouter import routing_scope as rs,pipeline as p,sexpr as sx
from autorouter.adapter import _parse_dsn

class SelectedDsn(unittest.TestCase):
    RAW=b'''(pcb fixture (parser (string_quote ")) (structure (rule (width 200)))
    (placement (component image (place J1 1 2 front 0)))
    (library (image image (pin PAD 1 0 0)))
    (network (net A (pins J1-1 J2-1)) (net B (pins J3-1 J4-1))
    (class kicad_default A B (circuit (use_via V))
    (rule (width 200) (clearance 150) (unknown_preserved yes))))
    (wiring (wire (path F.Cu 200 1 2 3 4) (net B) (type route))))'''

    def test_exclusion_clones_all_rules_without_removing_any_pin_or_obstacle(self):
        raw,binding=rs.partition_dsn(self.RAW,['A']);before=_parse_dsn(self.RAW.decode());after=_parse_dsn(raw.decode())
        network=sx.one(after,'network');classes=sx.children(network,'class')
        self.assertEqual(sx.children(network,'net'),sx.children(sx.one(before,'network'),'net'))
        for key in ('structure','placement','library','wiring'):self.assertEqual(sx.one(before,key),sx.one(after,key))
        rules=sx.children(sx.one(before,'network'),'class')[0][4:]
        self.assertEqual(classes[0][3:],rules);self.assertEqual(classes[1][3:],rules)
        self.assertEqual(classes[0][2],'A');self.assertEqual(classes[1][2],'B')
        self.assertIn(sx.unquote(classes[1][1]),binding['engine_argument'])
        self.assertTrue(binding['all_nets_and_pins_retained']);self.assertFalse(binding['native_classes_changed'])

    def test_all_selected_has_no_ignored_class_but_still_retains_network(self):
        _,binding=rs.partition_dsn(self.RAW,['A','B']);self.assertIsNone(binding['engine_argument']);self.assertEqual(binding['ignored_engine_classes'],[])

    def test_missing_or_ambiguous_membership_is_unsupported(self):
        for bad in [self.RAW.replace(b'default A B',b'default A A'),self.RAW.replace(b'default A B',b'default A'),
                    self.RAW.replace(b'default A B',b'default A B UNKNOWN')]:
            with self.subTest(raw=bad),self.assertRaises(p.Rejected):rs.partition_dsn(bad,['A'])
        with self.assertRaises(p.Rejected):rs.partition_dsn(self.RAW,['UNKNOWN'])

    def test_named_class_collision_rejects_instead_of_excluding_selected_class(self):
        _,binding=rs.partition_dsn(self.RAW,['A']);reserved=binding['ignored_engine_classes'][0].encode()
        with self.assertRaises(p.Rejected):rs.partition_dsn(self.RAW.replace(b'kicad_default',reserved),['A'])

    def test_interclass_or_per_net_references_fail_closed(self):
        for bad in [self.RAW.replace(b'(net A',b'(class_class (classes kicad_default Power) (rule (clearance 700))) (net A'),
                    self.RAW.replace(b'(pins J1-1 J2-1)',b'(pins J1-1 J2-1) (class kicad_default)')]:
            with self.subTest(raw=bad),self.assertRaisesRegex(p.Rejected,'reference semantics'):rs.partition_dsn(bad,['A'])

    def test_engine_default_aliases_cannot_overwrite_distinct_copied_rules(self):
        bad=self.RAW.replace(b'kicad_default A B',b'kicad_default A').replace(b'(class kicad_default',b'(class default B (rule (width 800))) (class kicad_default')
        with self.assertRaisesRegex(p.Rejected,'class names ambiguous'):rs.partition_dsn(bad,['A','B'])

if __name__=='__main__':unittest.main()
