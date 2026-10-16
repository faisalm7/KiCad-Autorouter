"""Focused bookkeeping/late-publication controls; no Native routing claim."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from scripts import qualify_installed_workflow as driver, experiment_paired as paired
from autorouter import pipeline as p, review_export as ex


class InstalledDeliveryControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.route = self.root/'result.json'; self.route.write_bytes(b'{}')
        self.export = self.root/'export.json'; self.export.write_bytes(b'{}')
        self.report = dict(arm='B1', selected_route_receipt=str(self.route), selected_route_sha256=p.sha(self.route),
                           export_receipt=str(self.export), export_sha256=p.sha(self.export))
        self.board = self.root/'board.kicad_pcb'
        self.context = SimpleNamespace(freeze=lambda: {'installed_context': {}, 'tools': {}, 'source_hashes': {}})
        for item in (patch.object(p,'check_result',return_value={'current':True}),
                     patch.object(ex,'check_export',return_value={'current':True})):
            item.start(); self.addCleanup(item.stop)

    def test_export_or_selected_receipt_reformatting_cannot_leave_stale_recorded_hash(self):
        driver.verify_delivery(self.report,self.board,self.context)
        for path in (self.route,self.export):
            with self.subTest(path=path):
                path.write_bytes(b'{}\n')
                with self.assertRaisesRegex(p.Rejected,'receipt hash changed'):
                    driver.verify_delivery(self.report,self.board,self.context)
                path.write_bytes(b'{}')

    def test_receipt_change_inside_final_native_reader_is_also_refused(self):
        def changed(_):self.export.write_bytes(b'{}\n');return {'current':True}
        with patch.object(ex,'check_export',side_effect=changed):
            with self.assertRaisesRegex(p.Rejected,'receipt hash changed'):
                driver.verify_delivery(self.report,self.board,self.context)

    def test_entire_portfolio_not_only_selected_receipt_is_checked_at_final_delivery(self):
        directory=self.root/'portfolio';directory.mkdir()
        summary=directory/'portfolio-summary.json';summary.write_bytes(b'{}')
        self.report.update(arm='B2_portfolio',portfolio_directory=str(directory),portfolio={},portfolio_summary_sha256=p.sha(summary))
        with patch.object(paired,'verify_portfolio',side_effect=p.Rejected('losing negative changed'))as checked:
            with self.assertRaisesRegex(p.Rejected,'losing negative changed'):
                driver.verify_delivery(self.report,self.board,self.context)
        checked.assert_called_once_with(directory,{},self.board,self.context.freeze())
        summary.write_bytes(b'{}\n')
        with self.assertRaisesRegex(p.Rejected,'summary hash changed'):
            driver.verify_delivery(self.report,self.board,self.context)

    def test_corrupt_partial_json_retains_hash_and_error_without_throwing(self):
        self.route.write_bytes(b'{broken')
        result=driver.read_attempt(self.route)
        self.assertEqual(result['sha256'],hashlib.sha256(b'{broken').hexdigest())
        self.assertIn('read_error',result);self.assertNotIn('accepted',result)
        self.route.write_text(json.dumps({'accepted':False,'status':'drc_rejected','source_drc':{'opens':2}}))
        result=driver.read_attempt(self.route)
        self.assertIs(result['accepted'],False);self.assertEqual(result['source_drc'],{'opens':2})


class InstalledPairedNegativeReader(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.board=self.root/'board.kicad_pcb'
        self.directory=self.root/'portfolio';self.directory.mkdir()
        self.frozen={'installed_context':{'runtime':str(self.root)},'tools':{},'source_hashes':{}}
        positive=dict(index=0,id='via_default',eligible=True,accepted_in_trial_receipt=True,vias=1,length_mm=20,
            result=str(self.directory/'01-via_default/result.json'),result_sha256='a'*64,candidate='positive',
            candidate_sha256='b'*64,native_report_sha256='c'*64)
        negative=dict(index=1,id='via_low',eligible=False,accepted_in_trial_receipt=False,validated_rejection=True,
            result=str(self.directory/'02-via_low/result.json'),vias=1,length_mm=10)
        for row in (positive,negative):
            path=Path(row['result']);path.parent.mkdir();path.write_text(json.dumps({'status':'routing_accepted'if row['eligible']else'drc_rejected'}))
        protocol=dict(freeze=self.frozen,variants=list(paired.portfolio.VARIANTS))
        paired.p.save_json(self.directory/'protocol.json',protocol)
        self.summary=dict(status='completed',comparison_eligible=True,protocol_sha256=p.sha(self.directory/'protocol.json'),
            trials=[positive,negative],pareto_frontier=['via_default'],selected={key:positive[key]for key in
            ('id','result','result_sha256','candidate','candidate_sha256','native_report_sha256','vias','length_mm')},
            wall_seconds=50,total_cpu_seconds=50)
        self.save()
        for item in (patch.object(paired.portfolio,'verify_row'),patch.object(paired.portfolio,'verify_negative_row')):
            item.start();self.addCleanup(item.stop)

    def save(self):paired.p.save_json(self.directory/'portfolio-summary.json',self.summary)
    def check(self):return paired.verify_portfolio(self.directory,self.summary,self.board,self.frozen)

    def test_completed_installed_portfolio_rechecks_loser_and_propagates_refusal(self):
        self.assertTrue(self.check()['accepted'])
        paired.portfolio.verify_negative_row.assert_called_once_with(self.summary['trials'][1],self.board,self.frozen)
        with patch.object(paired.portfolio,'verify_negative_row',side_effect=p.Rejected('raw failed candidate changed')):
            with self.assertRaisesRegex(p.Rejected,'raw failed candidate changed'):self.check()

    def test_missing_negative_flag_or_eligibility_relabel_cannot_skip_loser_checks(self):
        original=copy.deepcopy(self.summary)
        for change in ({'validated_rejection':False},{'eligible':True}):
            with self.subTest(change=change):
                self.summary=copy.deepcopy(original);self.summary['trials'][1].update(change);self.save()
                with self.assertRaises(p.Rejected):self.check()

    def test_complete_installed_freeze_mismatch_cannot_be_hidden_by_same_tools(self):
        path=self.directory/'protocol.json';value=json.loads(path.read_text());value['freeze']['installed_context']['runtime']='changed'
        paired.p.save_json(path,value);self.summary['protocol_sha256']=p.sha(path);self.save()
        with self.assertRaisesRegex(p.Rejected,'complete frozen context'):self.check()


if __name__=='__main__':unittest.main()
