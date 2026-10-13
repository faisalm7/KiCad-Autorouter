"""Qualification opt-in and shared publisher output-ownership guards."""
from pathlib import Path
import tempfile,unittest
from autorouter import floor_route as f,handoff as h,pipeline as p
from scripts import qualify_review_export as q

class WorkflowQualifierGuards(unittest.TestCase):
    def test_no_native_opt_in_creates_nothing(self):
        with tempfile.TemporaryDirectory(dir=h.c.ROOT/'tests') as name:
            out=Path(name)/'unused'
            with self.assertRaisesRegex(p.Rejected,'run-native'):q.qualify(out)
            self.assertFalse(out.exists())
    def test_unowned_output_rejects_before_any_retained_receipt_access(self):
        with tempfile.TemporaryDirectory(dir=h.c.ROOT/'tests') as name:
            out=Path(name)/'unused'
            with self.assertRaisesRegex(p.Rejected,'project-local'):q.qualify(out,run_native=True)
            self.assertFalse(out.exists())
    def test_shared_publisher_never_archives_a_replaced_preexisting_directory(self):
        with tempfile.TemporaryDirectory(dir=h.c.ROOT/'tests') as name:
            root=Path(name);out=root/'owned';out.mkdir();replacement=root/'existing';replacement.mkdir()
            (replacement/'result.json').write_text('existing');owner={};h.capture_destination(owner,out)
            out.rename(root/'retained');replacement.rename(out)
            with self.assertRaises(p.Rejected):
                f.publish(out,{'accepted':False},lambda:None,lambda:None,lambda:10,owned=lambda:h.owned_destination(owner))
            self.assertEqual((out/'result.json').read_text(),'existing');self.assertEqual(sorted(x.name for x in out.iterdir()),['result.json'])
    def test_nested_cancellation_cause_stops_the_whole_batch(self):
        error=p.Rejected('cancelled');error.__cause__=KeyboardInterrupt()
        self.assertTrue(q.cancelled(error));self.assertFalse(q.cancelled(p.Rejected('ordinary failure')))

if __name__=='__main__':unittest.main()
