"""Shared coordinate parsing must never round evidence before comparing it."""
import copy
from decimal import localcontext
import unittest

from autorouter.placement_transform import nm
from experiments.placement_native_proposal_v1 import engineering_metadata as metadata
from tests.test_placement_engineering_metadata import fixture


class ExactNativeCoordinates(unittest.TestCase):
    def test_low_precision_cannot_hide_one_nanometre_changes(self):
        for precision in (1, 6, 28):
            with localcontext() as context:
                context.prec = precision
                self.assertEqual(nm('21.250001',1_000_000),21_250_001)
                self.assertEqual(nm('-21.250001',1_000_000),-21_250_001)
                self.assertEqual(nm('125.001',1000),125001)
                source = fixture()
                expected = metadata.capture(source)
                changed = copy.deepcopy(source)
                metadata.c.sx.one(metadata.c.sx.one(changed,'point'),'at')[1] = '21.250001'
                with self.assertRaises(ValueError):
                    metadata.compare(expected,metadata.c.sx.dump(changed),False)
                changed = copy.deepcopy(source)
                metadata.c.sx.one(changed,'at')[3] = '90.0000000000000000000000000000000000001'
                with self.assertRaises(ValueError):
                    metadata.compare(expected,metadata.c.sx.dump(changed),False)
                changed = copy.deepcopy(source)
                metadata.c.sx.one(changed,'at')[1] = '20.000001'
                with self.assertRaises(ValueError):
                    metadata.compare(expected,metadata.c.sx.dump(changed),False)

    def test_fractional_nanometres_and_huge_exponents_refuse_without_Decimal_overflow(self):
        for text in ('21.250000000000000000000000000000000000000000000000000000000001',
                     '1e1000000','1e-1000000','NaN','sNaN','Infinity','-Infinity',
                     '2000.000001','-2000.000001','0.0000001'):
            for precision in (1,6,28):
                with self.subTest(text=text,precision=precision), localcontext() as context:
                    context.prec=precision
                    with self.assertRaises(ValueError): nm(text,1_000_000)

    def test_exact_bounded_values_and_decimal_scales(self):
        for atom,scale,expected in [('2000',1_000_000,2_000_000_000),
                ('-2000',1_000_000,-2_000_000_000),('1.2300000',1_000_000,1_230_000),
                ('1e-6',1_000_000,1),('-0e-1000000',1_000_000,0),('0.5',2,1)]:
            self.assertEqual(nm(atom,scale),expected)
        for scale in (True,False,1.0,0,-1,1_000_001):
            with self.subTest(scale=scale),self.assertRaises(ValueError): nm('1',scale)


if __name__ == '__main__': unittest.main()
