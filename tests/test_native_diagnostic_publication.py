"""Actual shared publication controls using authored local bytes; no native."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from autorouter import config as c,floor_route as f,handoff as h,pipeline as p


class NativeDiagnosticPublicationControls(unittest.TestCase):
    def setUp(self):
        scratch=c.ROOT/'.cache';scratch.mkdir(exist_ok=True)
        temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve()

    def inputs(self,name):
        output=self.root/name;output.mkdir();owner={};h.capture_destination(owner,output)
        source=self.root/(name+'-source');source.write_bytes(b'owned diagnostic input')
        pin=hashlib.sha256(source.read_bytes()).hexdigest();remaining=[10.0]
        report=dict(schema=1,status='completed',accepted=False,controls_passed=True,
            native_toolchain_qualified=True,production_admitted=False,within_budget=True)
        def owned():return h.owned_destination(owner)
        def stable():
            owned()
            if hashlib.sha256(source.read_bytes()).hexdigest()!=pin:raise p.Rejected('owned input changed')
        def account():
            report['within_budget']=remaining[0]>0
            if report['status']!='completed' or not report['within_budget']:
                report.update(controls_passed=False,native_toolchain_qualified=False)
        return output,source,report,stable,account,lambda:remaining[0],owned,remaining

    def test_default_and_explicit_positive_use_real_shared_publisher(self):
        for explicit in (False,True):
            with self.subTest(explicit=explicit):
                output,source,report,stable,account,remaining,owned,clock=self.inputs('positive-'+str(explicit))
                called=[]
                def final():called.append(True);stable()
                kwargs={'final_check':final} if explicit else {}
                actual=f.publish(output,report,stable,account,remaining,owned=owned,**kwargs)
                self.assertEqual(actual['status'],'completed');self.assertTrue(actual['controls_passed'])
                self.assertFalse(actual['accepted']);self.assertFalse(actual['production_admitted'])
                self.assertEqual(f.canonical(f.read_json(output/'result.json')),f.canonical(actual))
                self.assertEqual(called,[True] if explicit else [])
                self.assertFalse(list(output.glob('invalidated-result-*')))

    def test_final_callback_input_receipt_or_record_mutation_is_invalidated(self):
        for kind in ('input','receipt','record','cancel'):
            with self.subTest(kind=kind):
                output,source,report,stable,account,remaining,owned,clock=self.inputs('mutation-'+kind)
                def final():
                    if kind=='input':source.write_bytes(b'stale input');stable()
                    elif kind=='receipt':
                        changed=f.read_json(output/'result.json');changed['controls_passed']=False
                        p.save_json(output/'result.json',changed)
                    elif kind=='record':report['callback_mutation']=True
                    else:raise KeyboardInterrupt('authored final cancellation')
                actual=f.publish(output,report,stable,account,remaining,owned=owned,final_check=final)
                self.assertEqual(actual['status'],'cancelled' if kind=='cancel' else 'invalidated')
                self.assertFalse(actual['controls_passed']);self.assertFalse(actual['native_toolchain_qualified'])
                self.assertFalse(actual['accepted']);self.assertFalse(actual['production_admitted'])
                self.assertTrue(list(output.glob('invalidated-result-*')))
                self.assertEqual(f.canonical(f.read_json(output/'result.json')),f.canonical(actual))

    def test_final_callback_expiry_rejects_even_when_routing_accepted_false(self):
        output,source,report,stable,account,remaining,owned,clock=self.inputs('expired')
        def final():stable();clock[0]=0.0
        actual=f.publish(output,report,stable,account,remaining,owned=owned,final_check=final)
        self.assertEqual(actual['status'],'invalidated');self.assertFalse(actual['within_budget'])
        self.assertFalse(actual['controls_passed']);self.assertFalse(actual['native_toolchain_qualified'])
        self.assertFalse(actual['accepted']);self.assertIn('budget',actual['reason'])
        self.assertTrue(list(output.glob('invalidated-result-*')))
        self.assertEqual(f.canonical(f.read_json(output/'result.json')),f.canonical(actual))


if __name__=='__main__':unittest.main()
