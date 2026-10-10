"""Pure wrapper controls; no native or engine qualification is implied."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import experiment_paired as m


class PairedControls(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve();(self.root/'.runs').mkdir();(self.root/'source').mkdir()
        self.board=self.root/'source/board.kicad_pcb';self.board.write_text('synthetic')
        self.script=self.root/'wrapper.py';self.script.write_text('frozen synthetic wrapper')
        self.out=self.root/'.runs/paired';self.wall=0.;self.cpu=0.;self.shared=(10.,8.);self.c_cost=(20.,20.)
        self.calls=[];self.portfolio_cost=(20.,20.)
        patches=[patch.object(m.c,'ROOT',self.root),patch.object(m,'SCRIPT',self.script),
            patch.object(m.time,'monotonic',side_effect=lambda:self.wall),
            patch.object(m.q,'total_process_cpu',side_effect=lambda:self.cpu),
            patch.object(m.q,'selected_source',return_value=(self.board,'synthetic')),
            patch.object(m.portfolio,'freeze',side_effect=self.freeze),patch.object(m.q,'verify_freeze'),
            patch.object(m.subprocess,'run',return_value=SimpleNamespace(stdout=self.script.read_bytes())),
            patch.object(m.portfolio,'experiment',side_effect=self.portfolio),
            patch.object(m,'verify_portfolio',side_effect=lambda directory,result,board,frozen:result),
            patch.object(m,'prune',side_effect=self.prune),patch.object(m.q,'observations',return_value=[{'final_delivery_accepted': True}]),
            patch.object(m.q,'summarize',side_effect=self.summarize)]
        for item in patches:item.start();self.addCleanup(item.stop)

    def freeze(self,board):
        self.wall+=self.shared[0];self.cpu+=self.shared[1]
        return {'tools':{'git_head':'synthetic'},'source_hashes':{},'files_sha256':{}}

    def portfolio(self,directory,project):
        self.calls.append('portfolio');self.wall+=self.portfolio_cost[0];self.cpu+=self.portfolio_cost[1]
        return {'id':'B2_portfolio','status':'completed','accepted':True,'selected':{'id':'via_default'},
            'pareto_frontier':['via_default','via_low'],
            'trials':[{'id':'via_default','vias':2,'length_mm':800.},{'id':'via_low','vias':3,'length_mm':650.}]}

    def prune(self,board,directory,seconds,*,proposal_policy):
        self.assertEqual(seconds,120);self.assertEqual(proposal_policy,'feedback')
        self.calls.append('C');self.wall+=self.c_cost[0];self.cpu+=self.c_cost[1]
        return {'tools':{'git_head':'synthetic'},'source_hashes':{},'status':'routing_accepted','accepted':True,'steps':[]}

    def summarize(self,arm,directory,result,wall,cpu):
        return {'id':'C_feedback','status':'routing_accepted','accepted':True,'vias':2,'length_mm':700.}

    def test_shared_cost_charged_to_each_arm_and_frontier_preserved(self):
        result=m.experiment(self.out)
        self.assertEqual(self.calls,['portfolio','C'])
        self.assertEqual([row['charged_wall_seconds'] for row in result['results']],[30.,30.])
        self.assertEqual([row['charged_cpu_seconds'] for row in result['results']],[28.,28.])
        self.assertEqual([row['invocation_wall_seconds'] for row in result['results']],[20.,20.])
        self.assertEqual(len(result['comparisons']),2)
        self.assertTrue(result['comparisons'][0]['C_dominates_with_1e_6mm_tolerance'])
        self.assertFalse(result['comparisons'][1]['C_dominates_with_1e_6mm_tolerance'])

    def test_thermal_arm_starts_its_own_fresh_operation_with_full_charged_budget(self):
        def recovery(board,directory,seconds):
            self.assertEqual((board,seconds),(self.board,120))
            self.assertEqual(directory,self.out/'C_thermal')
            self.calls.append('thermal');self.wall+=20.;self.cpu+=20.
            return {'tools':{'git_head':'synthetic'},'source_hashes':{},'status':'routing_accepted',
                    'accepted':True,'steps':[],'strategy':'native_validated_thermal_bridge'}
        def summary(arm,*args):
            self.assertEqual(arm,m.THERMAL_ARM)
            return {'id':'C_thermal','status':'routing_accepted','accepted':True,'vias':2,'length_mm':700.}
        with patch.object(m,'recover',side_effect=recovery),patch.object(m.q,'summarize',side_effect=summary),patch.object(m,'verify_thermal_incumbent') as verify:
            result=m.experiment(self.out,system='thermal')
            verify.assert_called_once()
        self.assertEqual(self.calls,['portfolio','thermal'])
        self.assertEqual([row['charged_cpu_seconds'] for row in result['results']],[28.,28.])
        self.assertEqual(result['comparisons'][0]['system'],'C_thermal')

    def test_shared_overhead_can_disqualify_otherwise_in_budget_C(self):
        self.c_cost=(115.,115.)
        result=m.experiment(self.out)
        row=result['results'][1]
        self.assertTrue(row['accepted_before_shared_charge'])
        self.assertTrue(row['within_enclosing_budgets'])
        self.assertFalse(row['accepted']);self.assertFalse(row['within_charged_budgets'])
        self.assertEqual(result['comparisons'],[])

    def test_final_publication_crossing_cap_corrects_main_receipt(self):
        self.shared=(95.,95.);saved=m.p.save_json;injected=False
        def save(path,data):
            nonlocal injected
            saved(path,data)
            if path.name=='paired-summary.json' and not injected:
                self.wall+=6.;self.cpu+=6.;injected=True
        with patch.object(m.p,'save_json',side_effect=save):result=m.experiment(self.out)
        retained=json.loads((self.out/'paired-summary.json').read_text())
        self.assertFalse(any(row['accepted'] for row in retained['results']))
        self.assertEqual(retained['comparisons'],[])
        self.assertEqual(result['results'][0]['charged_cpu_seconds'],121.)

    def test_final_publication_interrupt_rewrites_main_receipt(self):
        saved=m.p.save_json;injected=False
        def save(path,data):
            nonlocal injected
            saved(path,data)
            if path.name=='paired-summary.json' and not injected:
                injected=True;raise KeyboardInterrupt
        with patch.object(m.p,'save_json',side_effect=save):result=m.experiment(self.out)
        retained=json.loads((self.out/'paired-summary.json').read_text())
        self.assertEqual(result['status'],'cancelled');self.assertEqual(retained['status'],'cancelled')
        self.assertFalse(any(row['accepted'] for row in retained['results']))
        self.assertEqual(retained['comparisons'],[])
        self.assertFalse(retained['results'][1]['observations'][0]['final_delivery_accepted'])

    def test_interrupted_final_partial_is_preserved_and_main_rejected(self):
        saved=m.p.save_json;injected=False
        def save(path,data):
            nonlocal injected
            if path.name=='paired-summary.json' and not injected:
                path.with_suffix('.json.partial').write_text('partial evidence');injected=True;raise KeyboardInterrupt
            saved(path,data)
        with patch.object(m.p,'save_json',side_effect=save):m.experiment(self.out)
        self.assertEqual((self.out/'paired-summary.json.partial.cancelled').read_text(),'partial evidence')
        retained=json.loads((self.out/'paired-summary.json').read_text())
        self.assertEqual(retained['status'],'cancelled');self.assertEqual(retained['comparisons'],[])

    def test_peer_cap_rejection_clears_other_arm_observation(self):
        self.shared=(5.,5.);self.portfolio_cost=(110.,110.)
        saved=m.p.save_json;injected=False
        def save(path,data):
            nonlocal injected
            saved(path,data)
            if path.name=='paired-summary.json' and not injected:
                self.wall+=6.;self.cpu+=6.;injected=True
        with patch.object(m.p,'save_json',side_effect=save):m.experiment(self.out)
        retained=json.loads((self.out/'paired-summary.json').read_text())
        self.assertFalse(any(row['accepted'] for row in retained['results']))
        self.assertTrue(retained['results'][1]['within_charged_budgets'])
        self.assertFalse(retained['results'][1]['observations'][0]['final_delivery_accepted'])

    def test_failed_invocation_time_and_outcome_remain_charged(self):
        def failed(*args,**kwargs):
            self.calls.append('C');self.wall+=30.;self.cpu+=35.
            raise RuntimeError('deliberate synthetic failure')
        with patch.object(m,'prune',side_effect=failed):result=m.experiment(self.out)
        self.assertEqual(len(result['results']),2)
        row=result['results'][1]
        self.assertEqual(row['status'],'invocation_error');self.assertFalse(row['accepted'])
        self.assertEqual(row['invocation_cpu_seconds'],35.)
        self.assertEqual(row['charged_cpu_seconds'],43.)
        self.assertEqual(result['comparisons'],[])


if __name__=='__main__':unittest.main()
