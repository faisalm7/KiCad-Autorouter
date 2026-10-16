"""Regression for actual GUI058 export rounding; these are accounting tests."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from autorouter import pipeline as p


class SequentialCpuAccounting(unittest.TestCase):
    def test_actual058_step_samples_conservatively_reconcile(self):
        samples=[.429328,.39550599999999997,.336955,.50948,.464964,.334905,.334458]
        self.assertLess(2.805596-sum(samples),0)
        walls=[1.0553566659800708,.4112466670339927,.34279270900879055,1.1225677079637535,
               .4729428749997169,.34075312496861443,.3405203750007786]
        steps=[dict(cpu_seconds=x,monitor_cpu_seconds=0.,wall_seconds=wall) for x,wall in zip(samples,walls)]
        result=p.sequential_cpu_components(1.9870119999999998,2.805596,steps)
        self.assertEqual(result['control_child_cpu_seconds'],0.)
        self.assertGreaterEqual(result['total_cpu_seconds'],1.9870119999999998+2.805596)
        record=dict(result,steps=steps,wall_seconds=6.064186042000074,budget_seconds=60.,cpu_budget_seconds=60.)
        p.check_resource_accounting(record)
        with self.assertRaises(p.Rejected):
            p.check_resource_accounting({**record,'cpu_budget_seconds':5.,'total_cpu_seconds':5.01})

    def test_control_children_and_monitor_cpu_are_counted(self):
        steps=[dict(cpu_seconds=2.,monitor_cpu_seconds=.5)]
        result=p.sequential_cpu_components(1.,3.,steps)
        self.assertEqual(result,dict(parent_cpu_seconds=1.,child_cpu_seconds=2.,
            control_child_cpu_seconds=1.,monitor_cpu_seconds=.5,total_cpu_seconds=4.5))

    def test_only_bounded_negative_roundoff_can_be_reconciled(self):
        steps=[dict(cpu_seconds=1e-6,monitor_cpu_seconds=0.)]
        self.assertEqual(p.sequential_cpu_components(0.,0.,steps)['total_cpu_seconds'],1e-6)
        steps[0]['cpu_seconds']=math.nextafter(1e-6,math.inf)
        with self.assertRaisesRegex(p.Rejected,'below recorded'):
            p.sequential_cpu_components(0.,0.,steps)

    def test_invalid_components_remain_invalid(self):
        for value in (-1.,True,float('nan'),float('inf'),None):
            for field in ('parent','waited','child','monitor'):
                with self.subTest(field=field,value=value),self.assertRaises(p.Rejected):
                    p.sequential_cpu_components(value if field=='parent' else 0.,value if field=='waited' else 0.,
                        [dict(cpu_seconds=value if field=='child' else 0.,monitor_cpu_seconds=value if field=='monitor' else 0.)])

    def test_shared_reader_still_rejects_negative_residual(self):
        record=dict(steps=[],wall_seconds=1.,budget_seconds=60.,cpu_budget_seconds=60.,
            parent_cpu_seconds=0.,child_cpu_seconds=0.,monitor_cpu_seconds=0.,
            control_child_cpu_seconds=-4.440892098500626e-16,total_cpu_seconds=0.)
        with self.assertRaisesRegex(p.Rejected,'invalid resource accounting'):
            p.check_resource_accounting(record)

    def test_overflow_cannot_produce_a_finite_receipt(self):
        with self.assertRaises(p.Rejected):
            p.sequential_cpu_components(1e308,1e308,[dict(cpu_seconds=1e308,monitor_cpu_seconds=0.)])


if __name__=='__main__':unittest.main()
