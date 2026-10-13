"""Focused pure continuation controls; no native/solver/Git calls."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).absolute().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from tests import test_portfolio as legacy
from autorouter import pipeline as p
from scripts import experiment_portfolio as m

class ResumeControls(legacy.PortfolioControls):
    def setUp(self):
        override=patch.object(legacy,'m',m);override.start();self.addCleanup(override.stop)
        super().setUp();self.base=self.root/'.runs/prior';self.old=self.base/'B2_portfolio';self.old.mkdir(parents=True)
        (self.old/'frozen-code').mkdir();(self.old/'frozen-code/unchanged').write_bytes(b'old code')
        (self.root/'core').write_bytes(b'unchanged core');(self.root/'scripts').mkdir();(self.root/m.RESUME_SCRIPT).write_bytes(b'new checker')
        self.oldf={'tools':{'git_head':'0'*40,'implementation_sha256':{'core':'same'}},'source_hashes':{},'files_sha256':{m.RESUME_SCRIPT:'old','core':p.sha(self.root/'core')}}
        oldscript=self.old/'frozen-code'/m.RESUME_SCRIPT;oldscript.parent.mkdir();oldscript.write_bytes(b'old checker')
        self.oldf['files_sha256'][m.RESUME_SCRIPT]=p.sha(oldscript)
        (self.old/'frozen-code/core').write_bytes((self.root/'core').read_bytes())
        (self.root/'unchanged').write_bytes(b'old code')
        self.oldf['files_sha256']['unchanged']=p.sha(self.old/'frozen-code/unchanged')
        self.frozen.clear();self.frozen.update(copy.deepcopy(self.oldf));self.frozen['tools']['git_head']='1'*40;self.frozen['files_sha256'][m.RESUME_SCRIPT]=p.sha(self.root/m.RESUME_SCRIPT)
        data=super().route(self.board,self.old/'01-via_default',105.,False,'both','tuned',scoring_variant='via_default');data['tools']=self.oldf['tools'];p.save_json(self.old/'01-via_default/result.json',data)
        row={'index':0,'id':'via_default','assigned_seconds':105.,'guidance_policy':None,'status':'routing_accepted','reason':None,'accepted_in_trial_receipt':True,'eligible':False,
             'invocation_wall_seconds':18.,'invocation_cpu_seconds':25.,'result':str(self.old/'01-via_default/result.json'),'result_sha256':p.sha(self.old/'01-via_default/result.json'),
             'candidate':data['candidate'],'candidate_sha256':data['candidate_sha256'],'native_report_sha256':data['native_report_sha256'],'vias':2,'length_mm':100.}
        protocol={'source':str(self.board),'freeze':self.oldf,'variants':list(m.VARIANTS),'fixed_order':True,'guidance_policy':None,'scoring':{name:p.engine_scoring_settings(name) for name in m.VARIANTS},'root_finalization_reserve_seconds':15.,'wall_budget_seconds':120.,'cpu_budget_seconds':120.}
        p.save_json(self.old/'protocol.json',protocol)
        oldsummary={'source':str(self.board),'status':'invalidated','comparison_eligible':False,'selected':None,'reason':'Rejected: trial engine profile differs from declared variant','guidance_policy':None,'protocol_sha256':p.sha(self.old/'protocol.json'),'wall_budget_seconds':120.,'cpu_budget_seconds':120.,'wall_seconds':29.,'total_cpu_seconds':31.,'trials':[row]}
        p.save_json(self.old/'portfolio-summary.json',oldsummary)
        invoice={'id':'B2_portfolio','result':str(self.old/'portfolio-summary.json'),'result_sha256':p.sha(self.old/'portfolio-summary.json'),'assigned_seconds':120.,'invocation_wall_seconds':30.,'invocation_cpu_seconds':32.}
        p.save_json(self.base/'paired-summary.json',{'results':[invoice]});p.save_json(self.base/'B2_portfolio-invocation.json',invoice);p.save_json(self.base/'protocol.json',{'inner_allowance_seconds':120.,'freeze':self.oldf})
        self.plan={'schema':1,'policy':m.RESUME_POLICY,'project':'nus-usb-led','guidance_policy':None,'source':str(self.board),'old_directory':str(self.old),
                   'artifacts':{str(self.base/n):p.sha(self.base/n) for n in ['paired-summary.json','protocol.json','B2_portfolio-invocation.json','B2_portfolio/portfolio-summary.json','B2_portfolio/protocol.json']},
                   'budget_seconds':120.,'prior_invocation_wall_seconds':30.,'prior_invocation_cpu_seconds':32.,'retained_variants':['via_default'],'continue_variants':['via_low','via_high'],'allowed_compatibility_changes':['tools.git_head','files_sha256/'+m.RESUME_SCRIPT]}
        self.planpath=self.root/'.runs/resume-plan.json';self.planpin=self.save_plan();self.wall=self.cpu=0.;self.calls=[];self.costs=[(10.,12.)]*3;self.sizes=[(2,90.),(2,80.),(2,70.)]
    def save_plan(self):
        p.save_json(self.planpath,self.plan);return p.sha(self.planpath)
    def route(self,*args,**kwargs):
        result=super().route(*args,**kwargs);result['tools']=self.frozen['tools'];p.save_json(args[1]/'result.json',result);return result
    def resumed(self,**kwargs):return m.experiment(self.out,'nus-usb-led',resume_plan=self.planpath,resume_plan_sha256=self.planpin,**kwargs)
    def test_resume_only_unattempted_variants_and_preserve_prior_contract(self):
        before=m.pc.inventory(self.old,with_directories=True);seen=[];verify=m.verify_row
        def check(row,board,frozen):seen.append((row['id'],frozen['tools']['git_head']));return verify(row,board,frozen)
        with patch.object(m,'verify_row',side_effect=check):r=self.resumed()
        self.assertEqual(self.calls,[('via_low',73.),('via_high',61.)]);self.assertTrue(r['comparison_eligible']);self.assertEqual(len(r['trials']),3)
        self.assertEqual((r['wall_seconds'],r['total_cpu_seconds']),(50.,56.));self.assertEqual(r['selected']['id'],'via_high')
        self.assertEqual(m.pc.inventory(self.old,with_directories=True),before)
        self.assertTrue(all(head==('0'*40 if name=='via_default' else '1'*40) for name,head in seen))
        protocol=json.loads((self.out/'protocol.json').read_text());self.assertEqual(m.trial_freeze(protocol,r['trials'][0]),self.oldf)
    def test_setup_is_charged_on_top_of_full_prior_invoice_not_nested_sample(self):
        def frozen(board):self.wall+=5.;self.cpu+=6.;return self.frozen
        with patch.object(m,'freeze',side_effect=frozen):r=self.resumed()
        self.assertEqual(self.calls[0][1],67.);self.assertEqual((r['wall_seconds'],r['total_cpu_seconds']),(55.,62.))
        self.assertEqual(r['prior_invocation_cpu_seconds'],32.)
    def test_core_or_source_change_invalidates_before_any_new_trial(self):
        self.frozen['tools']['implementation_sha256']['core']='changed';r=self.resumed();self.assertFalse(r['comparison_eligible']);self.assertEqual(self.calls,[]);self.assertIn('core',r['reason']);self.assertEqual((r['wall_seconds'],r['total_cpu_seconds']),(30.,32.))
    def test_undercharged_plan_cannot_override_actual_paired_cost(self):
        self.plan['prior_invocation_cpu_seconds']=31.;self.planpin=self.save_plan();r=self.resumed();self.assertEqual(self.calls,[]);self.assertFalse(r['comparison_eligible']);self.assertIn('complete measured',r['reason'])
    def test_any_started_extra_variant_blocks_narrow_resume(self):
        (self.old/'02-via_low').mkdir();r=self.resumed();self.assertEqual(self.calls,[]);self.assertFalse(r['comparison_eligible']);self.assertIn('prefix',r['reason'])
    def test_late_retained_mutation_invalidates_fresh_positive_index(self):
        save=p.save_json
        def write(path,value):
            save(path,value)
            if path.name=='portfolio-summary.json' and value.get('comparison_eligible') is True:(self.old/'frozen-code/unchanged').write_bytes(b'changed')
        with patch.object(p,'save_json',side_effect=write):r=self.resumed()
        self.assertFalse(r['comparison_eligible']);self.assertIsNone(r['selected']);self.assertFalse(json.loads((self.out/'portfolio-summary.json').read_text())['comparison_eligible'])
        self.assertIn('retained completed',r['reason'])
    def test_corrupt_initial_frozen_code_rejects_before_new_trials(self):
        (self.old/'frozen-code/core').write_bytes(b'corrupt before inventory capture')
        r=self.resumed();self.assertFalse(r['comparison_eligible']);self.assertEqual(self.calls,[])
        self.assertIn('frozen portfolio code',r['reason'])
    def test_failed_corrective_write_cannot_leave_positive_index(self):
        save=p.save_json
        def write(path,value):
            if path.name=='portfolio-summary.json' and value.get('status')=='invalidated':
                raise OSError('deliberate corrective write failure')
            save(path,value)
            if path.name=='portfolio-summary.json' and value.get('comparison_eligible') is True:
                (self.old/'frozen-code/unchanged').write_bytes(b'late retained mutation')
        with patch.object(p,'save_json',side_effect=write),self.assertRaises(OSError):self.resumed()
        self.assertFalse((self.out/'portfolio-summary.json').exists())
        self.assertEqual(len(list(self.out.glob('invalidated-portfolio-summary-*.json'))),1)
    def test_new_cpu_overshoot_disqualifies_paid_retained_winner(self):
        self.costs=[(10.,100.)];r=self.resumed();self.assertEqual(r['status'],'budget_exceeded');self.assertFalse(r['comparison_eligible']);self.assertEqual(len(self.calls),1);self.assertIsNone(r['selected']);self.assertEqual(r['total_cpu_seconds'],132.)
    def test_cancel_keeps_retained_row_but_delivers_no_candidate(self):
        with patch.object(p,'route',side_effect=KeyboardInterrupt):r=self.resumed()
        self.assertEqual(r['status'],'cancelled');self.assertFalse(r['comparison_eligible']);self.assertEqual(len(r['trials']),2);self.assertTrue(r['trials'][0]['eligible'])
    def test_fresh_output_cannot_be_inside_original_comparison(self):
        target=self.base/'new-summary'
        with self.assertRaises(p.Rejected):m.experiment(target,'nus-usb-led',resume_plan=self.planpath,resume_plan_sha256=self.planpin)
        self.assertFalse(target.exists())

class DefaultControls(legacy.PortfolioControls):
    def setUp(self):
        override=patch.object(legacy,'m',m);override.start();self.addCleanup(override.stop)
        super().setUp()

def load_tests(loader, tests, pattern):
    names=[name for name in ResumeControls.__dict__ if name.startswith('test_')]
    suite=unittest.TestSuite(ResumeControls(name) for name in names)
    suite.addTests(DefaultControls(name) for name in ['test_shared_cpu_budget_drives_rolling_allocation','test_summary_write_budget_crossing_corrects_acceptance'])
    return suite

if __name__=='__main__':unittest.main(verbosity=2)
