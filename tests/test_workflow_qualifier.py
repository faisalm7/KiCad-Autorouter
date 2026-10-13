"""Qualification opt-in and shared publisher output-ownership guards."""
from pathlib import Path
import tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
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
    def test_each_archival_rename_checks_owned_directory(self):
        with tempfile.TemporaryDirectory(dir=h.c.ROOT/'tests') as name:
            root=Path(name);out=root/'owned';out.mkdir();replacement=root/'existing';replacement.mkdir()
            (out/'result.json').write_text('owned');(out/'result.json.partial').write_text('owned-partial')
            (replacement/'result.json.partial').write_text('existing-partial');owner={};h.capture_destination(owner,out)
            rename=Path.rename;swapped=False
            def swap(path,target):
                nonlocal swapped
                result=rename(path,target)
                if path==out/'result.json' and not swapped:
                    swapped=True;rename(out,root/'retained');rename(replacement,out)
                return result
            with patch.object(Path,'rename',swap),self.assertRaises(p.Rejected):
                f.publish(out,{'accepted':False},lambda:(_ for _ in ()).throw(p.Rejected('failed publication')),lambda:None,lambda:10,owned=lambda:h.owned_destination(owner))
            self.assertEqual((out/'result.json.partial').read_text(),'existing-partial')
            self.assertEqual(sorted(x.name for x in out.iterdir()),['result.json.partial'])
    def test_required_rejection_intent_failure_cannot_pass_case(self):
        # A diagnostic controller must not report a passing workflow after its
        # required final rejection record fails. No native validation is mocked
        # into a correctness claim: this tests the controller failure boundary.
        with tempfile.TemporaryDirectory(dir=h.c.ROOT/'tests') as name:
            root=Path(name);(root/'.runs/receipt').mkdir(parents=True);(root/'source').mkdir()
            (root/'source/board.kicad_pcb').write_text('owned-source')
            p.save_json(root/'.runs/receipt/result.json',{'schema':1,'source':str(root/'source/board.kicad_pcb'),'candidate_sha256':'seam'})
            def review(receipt,output,render=False):
                output.mkdir();p.save_json(output/'review.json',{'status':'pure-seam'});return {}
            def choice(review,output,value):
                output.mkdir();p.save_json(output/'choice.json',{'choice':value})
                if value=='reject':raise p.Rejected('rejection persistence failed')
                return {'choice':value,'routing_accepted':False}
            def export(choice,output,seconds):
                output.mkdir();p.save_json(output/'export.json',{'pure_seam':True})
                return {'export_accepted':True,'project_file':str(output/'board.kicad_pro'),'candidate_sha256':'seam','native_report_sha256':'seam','native':dict(opens=0,blocking=0,warnings=0,exclusions=0,ignored_checks=[]),'metrics':{},'steps':[]}
            controller=(h.c.ROOT/'scripts/qualify_review_export.py').read_bytes()
            with patch.object(h.c,'ROOT',root),patch.object(q,'CASES',(('owned_case','.runs/receipt/result.json',1,False),)),patch.object(p,'check_storage'),patch.object(p,'tool_manifest',return_value={'git_head':'a'*40}),patch.object(q.subprocess,'run',return_value=SimpleNamespace(stdout=controller)),patch.object(p,'check_result',return_value={'current':True}),patch.object(h,'review_copy',review),patch.object(h,'review_choice',choice),patch.object(q.e,'export',export),patch.object(q.e,'check_export',return_value={'current':True}):
                result=q.qualify(root/'.runs/control',run_native=True)
            self.assertFalse(result['controls_passed']);self.assertEqual(result['status'],'failed')
            self.assertFalse(result['cases'][0]['passed']);self.assertIn('persistence failed',result['cases'][0]['error'])
    def test_nested_cancellation_cause_stops_the_whole_batch(self):
        error=p.Rejected('cancelled');error.__cause__=KeyboardInterrupt()
        self.assertTrue(q.cancelled(error));self.assertFalse(q.cancelled(p.Rejected('ordinary failure')))

if __name__=='__main__':unittest.main()
