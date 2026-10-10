"""Pure final-publication failure controls. No native or routing subprocesses."""
from pathlib import Path
import json,tempfile,unittest
import negative_control as n

class Publication(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup);self.out=Path(self.temp.name)
        self.summary={'status':'expected_native_rejection','control_passed':True,'routing_accepted':False}
    def stored(self):return json.loads((self.out/'negative-summary.json').read_text())
    def test_cancel_after_positive_publication(self):
        calls=[]
        def save(path,value):
            n.p.save_json(path,value);calls.append(1)
            if len(calls)==1:raise KeyboardInterrupt
        n.publish(self.summary,self.out,lambda:(1.,1.),lambda:None,save)
        self.assertFalse(self.stored()['control_passed']);self.assertEqual(self.stored()['status'],'cancelled')
    def test_interrupted_partial_preserved(self):
        calls=[]
        def save(path,value):
            calls.append(1)
            if len(calls)==1:(self.out/'negative-summary.json.partial').write_text('partial');raise KeyboardInterrupt
            n.p.save_json(path,value)
        n.publish(self.summary,self.out,lambda:(1.,1.),lambda:None,save)
        self.assertFalse(self.stored()['control_passed'])
        self.assertEqual([p.read_text() for p in self.out.glob('interrupted-*.partial')],['partial'])
    def test_postpublication_tamper_invalidates(self):
        calls=[]
        def verify():
            calls.append(1)
            if len(calls)>1:raise ValueError('selected native report changed')
        n.publish(self.summary,self.out,lambda:(1.,1.),verify,n.p.save_json)
        self.assertFalse(self.stored()['control_passed']);self.assertEqual(self.stored()['status'],'invalidated')
    def test_publication_cpu_cap_crossing_invalidates(self):
        calls=[]
        def save(path,value):n.p.save_json(path,value);calls.append(1)
        n.publish(self.summary,self.out,lambda:(1.,31. if calls else 1.),lambda:None,save)
        self.assertFalse(self.stored()['control_passed']);self.assertEqual(self.stored()['status'],'budget_exceeded')
    def test_paths_cannot_escape_checkout(self):
        with self.assertRaises(n.p.Rejected):n.local('/unrelated/not-read')
        with self.assertRaises(n.p.Rejected):n.local('.runs/../elsewhere')

if __name__=='__main__':unittest.main(verbosity=2)
