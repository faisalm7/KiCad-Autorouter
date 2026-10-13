"""Pure control-flow tests. Mocked native stages do not qualify route correctness."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import pipeline as p
from scripts import experiment_portfolio as m


class ScoringControls(unittest.TestCase):
    def test_three_verified_presets_do_not_change_rules_or_deadlines(self):
        for variant, expected in [('via_default',(50,5)),('via_low',(25,3)),('via_high',(100,10))]:
            for strict in (False,True):
                old=p.engine_profile_settings('tuned',105,strict_class_targets=strict)
                new=p.engine_profile_settings('tuned',105,strict_class_targets=strict,scoring_variant=variant)
                self.assertEqual(new['argv'][:-2],old['argv'])
                self.assertEqual(new['assigned_job_timeout_seconds'],old['assigned_job_timeout_seconds'])
                self.assertEqual(new['argv'][-2:],[f'--router.scoring.via_costs={expected[0]}',f'--router.scoring.plane_via_costs={expected[1]}'])

    def test_unknown_costs_cannot_inject_engine_arguments(self):
        for value in ('--router.ignore_net_classes=true',{},[],0,True,'invalid'):
            with self.subTest(value=value),self.assertRaises(p.Rejected):p.engine_scoring_settings(value)

    def test_default_call_preserves_existing_flags(self):
        self.assertEqual(p.engine_scoring_settings(None),{'variant':None,'argv':[]})
        self.assertFalse(any('via_costs' in arg for arg in p.engine_profile_settings('standard',120)['argv']))


class PortfolioControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();(self.root/'.runs').mkdir();(self.root/'source').mkdir()
        self.board=self.root/'source/board.kicad_pcb';self.board.write_text('fixture')
        self.board.with_suffix('.kicad_pro').write_text('{}')
        self.wall=0.;self.cpu=0.;self.calls=[];self.out=self.root/'.runs/portfolio'
        self.frozen={'tools':{},'source_hashes':{},'files_sha256':{}}
        self.sizes=[(2,100.),(3,80.),(2,90.)];self.costs=[(18.,25.)]*3
        self.patches=[patch.object(m.c,'ROOT',self.root),patch.object(m.time,'monotonic',side_effect=lambda:self.wall),
            patch.object(m.q,'total_process_cpu',side_effect=lambda:self.cpu),patch.object(p,'check_storage'),
            patch.object(m.q,'selected_source',return_value=(self.board,'synthetic-controls')),
            patch.object(m,'freeze',return_value=self.frozen),patch.object(m.q,'verify_freeze'),
            patch.object(p,'route',side_effect=self.route),patch.object(p,'check_result',side_effect=self.checked)]
        for item in self.patches:item.start();self.addCleanup(item.stop)

    def route(self,board,directory,seconds,keep,adapter,profile,*,scoring_variant):
        index=len(self.calls);self.calls.append((scoring_variant,seconds))
        wall,cpu=self.costs[index];self.wall+=wall;self.cpu+=cpu
        vias,length=self.sizes[index];directory.mkdir()
        engine=p.engine_profile_settings(profile,seconds,scoring_variant=scoring_variant)
        engine.update(outer_task_wall_budget_seconds=seconds,outer_task_cpu_budget_seconds=seconds)
        step={'name':'engine','argv':['java',*engine['argv']],'status':'success','exit_code':0,'cleanup_complete':True}
        p.save_json(directory/'engine-process.json',step)
        result={'source':str(board),'source_hashes':{},'tools':{},'adapter':adapter,'engine_profile':profile,
            'scoring_variant':scoring_variant,'scope':'whole_board_unlocked_routing',
            'budget_seconds':seconds,'cpu_budget_seconds':seconds,'status':'routing_accepted','accepted':True,
            'candidate':str(directory/'candidate/board.kicad_pcb'),'candidate_sha256':'candidate-'+scoring_variant,
            'native_report_sha256':'native-'+scoring_variant,'metrics':{'vias':vias,'track_length_mm':length},
            'native':{'opens':0,'blocking':0,'exclusions':0},'steps':[step],'engine_budget':engine}
        p.save_json(directory/'result.json',result)
        return result

    def checked(self,receipt):
        data=json.loads(receipt.read_text())
        return {'candidate':data['candidate'],'candidate_sha256':data['candidate_sha256'],'current':True,'applied':False}

    def test_shared_cpu_budget_drives_rolling_allocation(self):
        result=m.experiment(self.out)
        self.assertEqual(self.calls,[('via_default',105.),('via_low',80.),('via_high',55.)])
        self.assertTrue(result['comparison_eligible'])
        self.assertEqual(result['total_cpu_seconds'],75.)
        self.assertEqual(result['wall_seconds'],54.)
        self.assertEqual(result['selected']['id'],'via_high')
        self.assertEqual(result['pareto_frontier'],['via_low','via_high'])
        self.assertNotIn('accepted',result)

    def test_original_width_guard_is_required_in_tuned_profile_readback(self):
        project=self.board.with_suffix('.kicad_pro')
        project.write_text(json.dumps({'board':{'design_settings':{'rules':{'min_track_width':0.2}}}}))
        directory=self.root/'.runs/guarded';data=self.route(self.board,directory,100,False,'both','tuned',scoring_variant='via_default')
        engine=p.engine_profile_settings('tuned',100,strict_class_targets=True,scoring_variant='via_default')
        engine.update(outer_task_wall_budget_seconds=100,outer_task_cpu_budget_seconds=100)
        data['engine_budget']=engine;data['minimum_width_guard']=p.minimum_width_guard(self.board,'both')
        data['steps'][0]['argv']=['java',*engine['argv']]
        p.save_json(directory/'engine-process.json',data['steps'][0]);receipt=directory/'result.json';p.save_json(receipt,data)
        row={'result':str(receipt),'result_sha256':p.sha(receipt),'id':'via_default','assigned_seconds':100,
            'vias':data['metrics']['vias'],'length_mm':data['metrics']['track_length_mm'],
            'candidate':data['candidate'],'candidate_sha256':data['candidate_sha256'],
            'native_report_sha256':data['native_report_sha256']}
        self.assertTrue(m.verify_row(row,self.board,self.frozen)['current'])
        data['minimum_width_guard']['original_project_sha256']='0'*64;p.save_json(receipt,data);row['result_sha256']=p.sha(receipt)
        with self.assertRaisesRegex(p.Rejected,'original width guard'):
            m.verify_row(row,self.board,self.frozen)

    def test_prep_and_selection_costs_are_in_global_budget(self):
        def frozen(board):self.wall+=5.;self.cpu+=6.;return self.frozen
        with patch.object(m,'freeze',side_effect=frozen):result=m.experiment(self.out)
        self.assertEqual(self.calls[0][1],99.)
        self.assertEqual(result['wall_seconds'],59.)
        self.assertEqual(result['total_cpu_seconds'],81.)

    def test_reserves_stop_before_third_attempt_without_erasing_trials(self):
        self.costs=[(20.,40.)]*3
        result=m.experiment(self.out)
        self.assertEqual(len(self.calls),2)
        self.assertEqual(len(result['trials']),2)
        self.assertTrue(result['comparison_eligible'])
        self.assertIn('reserves',result['stop_reason'])

    def test_cpu_overshoot_disqualifies_previous_valid_candidate(self):
        self.costs=[(18.,25.),(18.,100.)]
        result=m.experiment(self.out)
        self.assertEqual(result['status'],'budget_exceeded')
        self.assertFalse(result['comparison_eligible']);self.assertIsNone(result['selected'])
        self.assertEqual(len(result['trials']),2)

    def test_cancel_preserves_failed_trial_but_no_delivery(self):
        real=self.route
        def route(*a,**kw):
            if self.calls:raise KeyboardInterrupt
            return real(*a,**kw)
        with patch.object(p,'route',side_effect=route):result=m.experiment(self.out)
        self.assertEqual(result['status'],'cancelled');self.assertIsNone(result['selected'])
        self.assertEqual(len(result['trials']),2)
        self.assertEqual(result['trials'][1]['status'],'cancelled')

    def test_source_change_invalidates_result(self):
        with patch.object(m.q,'verify_freeze',side_effect=[None,p.Rejected('source changed')]):result=m.experiment(self.out)
        self.assertEqual(result['status'],'invalidated');self.assertFalse(result['comparison_eligible'])
        self.assertEqual(len(result['trials']),1)

    def test_invalid_native_metric_cannot_rank(self):
        self.sizes[0]=(True,100.)
        result=m.experiment(self.out)
        self.assertEqual(result['status'],'invalidated');self.assertIsNone(result['selected'])

    def test_receipt_switch_during_check_fails_closed(self):
        original=self.checked
        def switched(receipt):
            result=original(receipt);data=json.loads(receipt.read_text());data['metrics']['vias']+=1
            p.save_json(receipt,data);return result
        with patch.object(p,'check_result',side_effect=switched):result=m.experiment(self.out)
        self.assertEqual(result['status'],'invalidated');self.assertIn('changed while checking',result['reason'])

    def test_profile_label_cannot_hide_wrong_engine_cost(self):
        route=self.route
        def wrong(*a,**kw):
            result=route(*a,**kw)
            result['steps'][0]['argv'][-1]='--router.scoring.plane_via_costs=99'
            p.save_json(a[1]/'result.json',result)
            p.save_json(a[1]/'engine-process.json',result['steps'][0])
            return result
        with patch.object(p,'route',side_effect=wrong):result=m.experiment(self.out)
        self.assertEqual(result['status'],'invalidated')
        self.assertIn('execution arguments',result['reason'])

    def test_output_collision_does_not_replace_original(self):
        self.out.mkdir();marker=self.out/'precious';marker.write_text('preserved')
        with self.assertRaises(FileExistsError):m.experiment(self.out)
        self.assertEqual(marker.read_text(),'preserved')

    def test_stable_tie_and_pareto_keep_all_valid_metrics(self):
        self.sizes=[(2,100.),(2,100.),(3,120.)]
        result=m.experiment(self.out)
        self.assertEqual(result['selected']['id'],'via_default')
        self.assertEqual(result['pareto_frontier'],['via_default','via_low'])
        self.assertEqual(len(result['trials']),3)

    def test_summary_write_budget_crossing_corrects_acceptance(self):
        saved=p.save_json
        def write(path,value):
            saved(path,value)
            if path.name=='portfolio-summary.json' and value.get('comparison_eligible'):
                self.cpu=120.1
        with patch.object(p,'save_json',side_effect=write):result=m.experiment(self.out)
        self.assertFalse(result['comparison_eligible']);self.assertEqual(result['status'],'budget_exceeded')
        self.assertFalse(json.loads((self.out/'portfolio-summary.json').read_text())['comparison_eligible'])

    def test_cancel_after_final_positive_write_clears_eligibility(self):
        saved=p.save_json
        def write(path,value):
            saved(path,value)
            if path.name=='portfolio-summary.json' and value.get('comparison_eligible'):
                raise KeyboardInterrupt
        with patch.object(p,'save_json',side_effect=write):result=m.experiment(self.out)
        self.assertEqual(result['status'],'cancelled');self.assertIsNone(result['selected'])
        retained=json.loads((self.out/'portfolio-summary.json').read_text())
        self.assertFalse(retained['comparison_eligible']);self.assertEqual(len(retained['trials']),3)

    def test_cancel_inside_final_write_preserves_partial_and_rejects(self):
        saved=p.save_json
        def write(path,value):
            if path.name=='portfolio-summary.json' and value.get('comparison_eligible'):
                path.with_suffix('.json.partial').write_text('interrupted bytes')
                raise KeyboardInterrupt
            saved(path,value)
        with patch.object(p,'save_json',side_effect=write):result=m.experiment(self.out)
        self.assertEqual(result['status'],'cancelled');self.assertFalse(result['comparison_eligible'])
        self.assertEqual((self.out/'cancelled-summary.partial').read_text(),'interrupted bytes')
        self.assertFalse((self.out/'portfolio-summary.json.partial').exists())

    def test_cancel_inside_interim_write_preserves_partial_and_rejects(self):
        saved=p.save_json
        def write(path,value):
            if path.name=='portfolio-summary.json' and value.get('status')=='incomplete':
                path.with_suffix('.json.partial').write_text('interrupted interim')
                raise KeyboardInterrupt
            saved(path,value)
        with patch.object(p,'save_json',side_effect=write):result=m.experiment(self.out)
        self.assertEqual(result['status'],'cancelled');self.assertFalse(result['comparison_eligible'])
        self.assertEqual((self.out/'cancelled-summary.partial').read_text(),'interrupted interim')
        self.assertEqual(len(result['trials']),1)


if __name__=='__main__':unittest.main()
