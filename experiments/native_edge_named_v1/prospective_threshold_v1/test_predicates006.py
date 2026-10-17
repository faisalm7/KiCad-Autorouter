"""Retained005/pure policy regressions, not new Native qualification."""
import copy
import unittest
from experiments.native_edge_named_v1.prospective_threshold_v1 import controller006 as t


class ExpectedNativeFindings(unittest.TestCase):
    def setUp(self):
        self.source = t.importer.frozen(t.previous.OUT/'result.json',t.PREVIOUS_RESULT_PIN)['source_native']

    def test_actual005_source_is_expected_unrouted_input_never_accepted_candidate(self):
        self.assertEqual(t.p.native_rejection_reasons(self.source),[
            'native error finding: unconnected_items','native opens=2',
            'policy-critical native finding: unconnected_items (error)'])
        t.source_predicate(self.source)
        self.assertFalse(t.p.native_accepted(self.source))
        for mutation in ('extra_error','missing_connection','wrong_error'):
            bad=copy.deepcopy(self.source)
            if mutation=='extra_error':
                bad['blocking']=1
                bad['findings'].append(dict(type='clearance',severity='error',items=[]))
            elif mutation=='missing_connection':
                bad['findings'].pop(0)
            else:
                bad['findings'][0]['type']='clearance'
            with self.subTest(mutation=mutation),self.assertRaises(t.p.Rejected):
                t.source_predicate(bad)

    def test_edge_negative_keeps_critical_reason_and_refuses_unrelated_error(self):
        # Synthetic policy shape built from actual retained warning evidence;
        # actual candidate Native/byte/process proof remains mandatory elsewhere.
        negative=copy.deepcopy(self.source)
        negative.update(opens=0,blocking=1)
        negative['findings']=[row for row in negative['findings'] if row['severity']!='error']
        negative['findings'].append(dict(type='copper_edge_clearance',severity='error',items=[]))
        self.assertEqual(t.p.native_rejection_reasons(negative),[
            'native blocking=1','native error finding: copper_edge_clearance',
            'policy-critical native finding: copper_edge_clearance (error)'])
        t.result_predicate(negative,self.source,False)
        self.assertFalse(t.p.native_accepted(negative))
        for check in ('clearance','track_width','unconnected_items'):
            bad=copy.deepcopy(negative);bad['blocking']=2
            bad['findings'].append(dict(type=check,severity='error',items=[]))
            with self.subTest(unrelated_error=check),self.assertRaises(t.p.Rejected):
                t.result_predicate(bad,self.source,False)
        with self.assertRaises(t.p.Rejected):
            t.result_predicate(negative,self.source,True)


if __name__=='__main__':unittest.main()
