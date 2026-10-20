"""Pure source/boundary regressions. Native evidence is a separate finite run."""
import copy
import unittest

from autorouter import pipeline as p, sexpr as sx
from experiments.qfn_escape_seed_v1 import controls as c


class EscapeControlBoundary(unittest.TestCase):
    def test_reference_is_removed_and_only_original_keep_is_protected(self):
        original=sx.parse(c.fixture.board().decode())
        before=copy.deepcopy(original)
        complete,seeds,protected,metadata=c.completed_control(original)
        self.assertEqual(original,before)
        self.assertEqual(len(seeds),16)
        self.assertEqual(len(protected),1)
        self.assertEqual(protected,[route for route in p.routes(original) if p.locked(route)])
        self.assertTrue(all(not p.locked(route) for route in seeds))
        self.assertEqual(p.immutable(complete),p.immutable(original))
        self.assertFalse(metadata['contact_or_clearance_proven'])
        self.assertEqual(len(sx.children(sx.children(original,'footprint')[0],'pad')),17)
        self.assertEqual(sx.one(sx.children(sx.children(original,'footprint')[0],'pad')[-1],'zone_connect'),['zone_connect','2'])
        self.assertTrue(any(len(row)==4 for row in sx.one(original,'layers')[1:]))
        # Altering removable reference geometry cannot change seed selection.
        changed=copy.deepcopy(original)
        sx.one(p.routes(changed)[0],'end')[1:]=['37','37']
        self.assertEqual(c.completed_control(changed),(complete,seeds,protected,metadata))

    def test_destinations_bind_fresh_work_to_direct_runs_children(self):
        preparation=c.ROOT/'.runs/qfn-escape-test-preparation'
        output=c.ROOT/'.runs/qfn-escape-test-output'
        outer=output.with_name(output.name+'-enclosure')
        plan=dict(preparation=str(preparation),output=str(output),enclosure=str(outer),
                  source=str(preparation/'original'/(c.fixture.STEM+'.kicad_pcb')))
        self.assertEqual(c.destinations(plan,preparation/'protocol.json',output),outer)
        for bad in (preparation/'original/new-child',c.RUNTIME/'qfn-escape-new-child',
                    c.ROOT/'qfn-escape-new-child',output/'nested',output.parent/'other-name'):
            with self.subTest(path=bad),self.assertRaises(p.Rejected):
                c.destinations(plan,preparation/'protocol.json',bad)
        for key,value in (('output',str(preparation)),('source',str(output/'original.kicad_pcb')),
                          ('enclosure',str(preparation))):
            with self.subTest(key=key),self.assertRaises(p.Rejected):
                c.destinations(dict(plan,**{key:value}),preparation/'protocol.json',output)


if __name__=='__main__':
    unittest.main()
