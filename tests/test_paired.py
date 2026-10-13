"""Pure wrapper controls; no native or engine qualification is implied."""
import json
from contextlib import contextmanager
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

    def test_placement_cache_entry_and_cleanup_are_charged_before_delivery(self):
        @contextmanager
        def session():
            self.wall+=1.;self.cpu+=1.
            try:yield
            finally:self.wall+=2.;self.cpu+=2.
        def route(*args,**kwargs):
            self.wall+=20.;self.cpu+=20.
            return {'tools':{'git_head':'synthetic'},'source_hashes':{},'status':'routing_accepted','accepted':True,'steps':[]}
        def prune(*args):
            value=route();self.wall+=88.;self.cpu+=88.;return value
        def portfolio(directory,project,**kwargs):
            value=self.portfolio(directory,project)
            value.update(guidance_policy='placement-search-v1',wall_budget_seconds=kwargs['budget'],cpu_budget_seconds=kwargs['budget'])
            for row in value['trials']:row['guidance_policy']='placement-search-v1'
            return value
        def summarize(arm,*args):return {'id':arm['id'],'status':'routing_accepted','accepted':True,'vias':2,'length_mm':700.}
        with patch.object(m.p,'validation_readback_session',session),patch.object(m.p,'route',route),patch.object(m.f,'route',route),patch.object(m.ps,'prune',prune),patch.object(m.ps.pc,'inventory',return_value={}),patch.object(m.portfolio,'experiment',portfolio),patch.object(m.q,'summarize',summarize):
            result=m.experiment(self.out,project_name='multichannel',system='placement')
        self.assertEqual(result['shared_overhead_cpu_seconds'],11.)
        # Freeze10 + entry1 + exit2 are shared13, while the10wall/8CPU
        # fixture's CPU freeze is8. C108+11=119 here, still under120.
        self.assertEqual(result['results'][-1]['charged_cpu_seconds'],119.)
        self.assertEqual(result['results'][-1]['charged_wall_seconds'],121.)
        self.assertFalse(result['results'][-1]['accepted'])
        self.assertTrue(result['results'][-1]['accepted_before_shared_charge'])

    @contextmanager
    def native_four(self, *, overrides=None, failed_c=False, mutate_prior=False):
        """Actual wrapper flow, fake workers, and real completed-arm inventories."""
        overrides=overrides or {}
        self.native_assignments=[]
        @contextmanager
        def session():
            self.wall+=1.;self.cpu+=1.
            try:yield
            finally:self.wall+=2.;self.cpu+=2.
        def outcome(directory,seconds,adapter,profile):
            directory.mkdir();(directory/'evidence.txt').write_text(directory.name)
            return {'tools':{'git_head':'synthetic'},'source_hashes':{},
                'status':'routing_accepted','accepted':True,'steps':[],
                'adapter':adapter,'engine_profile':profile,'scope':'whole_board_unlocked_routing',
                'budget_seconds':seconds,'cpu_budget_seconds':seconds}
        def route(board,directory,seconds,keep_existing,adapter,profile):
            self.assertEqual(board,self.board);self.assertFalse(keep_existing)
            self.assertEqual((directory.name,adapter,profile),
                ('B0','none','standard') if directory.name=='B0' else ('B1','both','standard'))
            self.calls.append(directory.name);self.native_assignments.append(seconds)
            self.wall+=20.;self.cpu+=20.
            result=outcome(directory,seconds,adapter,profile)
            result.update(overrides.get(directory.name,{}))
            if mutate_prior and directory.name=='B1':
                (directory.parent/'B0/evidence.txt').write_text('changed prior arm')
            return result
        def portfolio(directory,project,**kwargs):
            self.assertEqual(set(kwargs),{'budget'})
            self.native_assignments.append(kwargs['budget'])
            result=self.portfolio(directory,project);self.calls[-1]='B2_portfolio'
            directory.mkdir();(directory/'evidence.txt').write_text('portfolio')
            result.update(guidance_policy=None,wall_budget_seconds=kwargs['budget'],cpu_budget_seconds=kwargs['budget'])
            for trial in result['trials']:trial['guidance_policy']=None
            result.update(overrides.get('B2_portfolio',{}))
            return result
        def prune(board,directory,seconds,*,proposal_policy):
            self.assertEqual((board,directory.name,proposal_policy),(self.board,'C_feedback','feedback'))
            self.calls.append('C_feedback');self.native_assignments.append(seconds)
            result=outcome(directory,seconds,'both','tuned')
            if failed_c:
                self.wall+=30.;self.cpu+=35.;raise RuntimeError('deliberate native C failure')
            self.wall+=self.c_cost[0];self.cpu+=self.c_cost[1]
            result.update(zone_net_ids=[],trials=[],improvements=0)
            result.update(overrides.get('C_feedback',{}))
            return result
        def summarize(arm,directory,result,wall,cpu):
            return {'id':arm['id'],'status':result['status'],'accepted':result['accepted'],
                    'vias':2,'length_mm':800.,'warnings':40}
        with patch.object(m.p,'validation_readback_session',session),patch.object(m.p,'route',route),\
             patch.object(m,'prune',prune),patch.object(m.portfolio,'experiment',portfolio),\
             patch.object(m.q,'summarize',summarize),\
             patch.object(m.f,'route',side_effect=AssertionError('placement guidance used')),\
             patch.object(m.ps,'prune',side_effect=AssertionError('placement pruning used')):
            yield

    def test_native_all_four_arms_own_incumbent_and_equal_frozen_allowance(self):
        with self.native_four():result=m.experiment(self.out,project_name='unrestricted-native-project',system='native-all')
        self.assertEqual(self.calls,['B0','B1','B2_portfolio','C_feedback'])
        self.assertEqual(self.native_assignments,[104.]*4)
        protocol=json.loads((self.out/'protocol.json').read_text())
        self.assertEqual(protocol['arm_order'],self.calls)
        self.assertEqual(protocol['inner_allowance_seconds'],104.)
        self.assertEqual(protocol['system_contract'],m.C_ARM)
        self.assertIsNone(protocol['guidance_policy'])
        self.assertNotIn('pruning_allocation',protocol)
        self.assertEqual(tuple(m.portfolio.VARIANTS),('via_default','via_low','via_high'))
        self.assertEqual([r['charged_wall_seconds'] for r in result['results']],[33.]*4)
        self.assertEqual([r['charged_cpu_seconds'] for r in result['results']],[31.]*4)
        self.assertEqual(result['shared_overhead_wall_seconds'],13.)
        self.assertEqual(result['shared_overhead_cpu_seconds'],11.)
        self.assertTrue(all(row['accepted'] for row in result['results']))

    def test_native_all_zero_zone_no_proposals_and_ties_remain_explicit(self):
        with self.native_four():result=m.experiment(self.out,system='native-all')
        row=result['results'][-1]
        self.assertEqual(row['zone_net_ids'],[])
        self.assertEqual(row['pruning_trial_count'],0)
        self.assertEqual(row['pruning_improvements'],0)
        self.assertEqual(row['zone_pruning_opportunity'],'no_declared_zone_nets')
        self.assertEqual(row['warnings'],40)
        self.assertEqual(len(result['comparisons']),4)
        self.assertFalse(any(c.get('C_dominates_with_1e_6mm_tolerance') or c.get('pareto_improvement') for c in result['comparisons']))

    def test_native_all_failures_and_session_cleanup_stay_charged(self):
        with self.native_four(failed_c=True):result=m.experiment(self.out,system='native-all')
        row=result['results'][-1]
        self.assertEqual(row['status'],'invocation_error');self.assertFalse(row['accepted'])
        self.assertIn('deliberate native C failure',row['reason'])
        self.assertEqual(row['invocation_cpu_seconds'],35.)
        self.assertEqual(row['charged_cpu_seconds'],46.)
        self.assertEqual(result['comparisons'],[])

    def test_native_all_overhead_can_reject_accepted_inner_native_C(self):
        self.c_cost=(108.,108.)
        with self.native_four():result=m.experiment(self.out,system='native-all')
        row=result['results'][-1]
        self.assertTrue(row['accepted_before_shared_charge'])
        self.assertTrue(row['within_enclosing_budgets'])
        self.assertEqual(row['charged_wall_seconds'],121.)
        self.assertFalse(row['accepted']);self.assertEqual(result['comparisons'],[])

    def test_native_all_rejects_guidance_and_mismatched_inner_contracts(self):
        for index,(arm,changed) in enumerate((('B0',{'budget_seconds':120.}),
            ('B1',{'input_policy':'placement-search-v1'}),
            ('C_feedback',{'cpu_budget_seconds':120.}),
            ('B2_portfolio',{'wall_budget_seconds':120.}),
            ('B2_portfolio',{'guidance_policy':'placement-search-v1'}))):
            with self.subTest(arm=arm,changed=changed):
                self.out=self.root/'.runs'/('native-contract-'+str(index));self.calls=[]
                with self.native_four(overrides={arm:changed}):result=m.experiment(self.out,system='native-all')
                row=next(r for r in result['results'] if r['id']==arm)
                self.assertFalse(row['accepted']);self.assertEqual(row['status'],'invocation_error')

    def test_native_all_completed_arm_changed_before_next_worker_invalidates_pair(self):
        with self.native_four(mutate_prior=True):result=m.experiment(self.out,system='native-all')
        self.assertEqual(self.calls,['B0','B1'])
        self.assertEqual(result['status'],'invalidated')
        self.assertFalse(any(row['accepted'] for row in result['results']))
        self.assertIn('completed comparison arm changed',result['reason'])

    def test_native_all_final_publication_cost_cannot_leave_positive_comparison(self):
        self.c_cost=(106.,106.);saved=m.p.save_json;injected=False
        def save(path,data):
            nonlocal injected
            saved(path,data)
            if path.name=='paired-summary.json' and not injected:
                self.wall+=2.;self.cpu+=2.;injected=True
        with self.native_four(),patch.object(m.p,'save_json',side_effect=save):
            result=m.experiment(self.out,system='native-all')
        retained=json.loads((self.out/'paired-summary.json').read_text())
        self.assertFalse(any(row['accepted'] for row in retained['results']))
        self.assertEqual(retained['comparisons'],[])
        self.assertFalse(retained['results'][-1]['observations'][0]['final_delivery_accepted'])
        self.assertTrue(result['results'][-1]['paired_publication_budget_rejected'])

    def test_native_all_stale_final_arm_clears_nested_delivery_claim(self):
        saved=m.p.save_json;injected=False
        def save(path,data):
            nonlocal injected
            saved(path,data)
            if path.name=='paired-summary.json' and not injected:
                (self.out/'C_feedback/evidence.txt').write_text('changed after publication')
                injected=True
        with self.native_four(),patch.object(m.p,'save_json',side_effect=save):
            result=m.experiment(self.out,system='native-all')
        retained=json.loads((self.out/'paired-summary.json').read_text())
        self.assertEqual(result['status'],'invalidated')
        self.assertFalse(any(row['accepted'] for row in retained['results']))
        self.assertEqual(retained['comparisons'],[])
        self.assertFalse(retained['results'][-1]['observations'][0]['final_delivery_accepted'])


if __name__=='__main__':unittest.main()
