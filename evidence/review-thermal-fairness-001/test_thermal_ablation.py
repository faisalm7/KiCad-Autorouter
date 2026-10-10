"""Pure wrapper controls; mocked native stages are not routing evidence."""
from pathlib import Path
import copy
import importlib.util
import json
import os
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=next(parent for parent in Path(__file__).resolve().parents if (parent/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT))
try:
    from scripts import experiment_thermal_ablation as m
except ImportError:
    spec=importlib.util.spec_from_file_location('thermal_ablation_draft',Path(__file__).with_name('experiment_thermal_ablation.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class Harness(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory(dir=ROOT);self.addCleanup(td.cleanup);self.root=Path(td.name)
        (self.root/'.runs').mkdir();(self.root/'source').mkdir();self.board=self.root/'source/a.kicad_pcb';self.board.write_text('synthetic')
        self.out=self.root/'.runs/output';self.prior=self.root/'.runs/prior';self.prior.mkdir();self.script=self.root/'scripts/ablation.py';self.script.parent.mkdir();self.script.write_text('frozen')
        self.wall=self.cpu=0.;self.calls=[];self.mode='normal';self.published=False
        self.frozen={'tools':{'git_head':'new','implementation_sha256':{'x':'hash'},'files':{}},'source_hashes':{'a.kicad_pcb':'hash'},'files_sha256':{}}
        self.reference={'results':[{'id':'C_thermal','accepted':True,'length_mm':11.,'vias':2}], 'bound_files_sha256':{},'prior_directory':str(self.prior),'prior_tree_sha256':{}}
        patches=[patch.object(m.c,'ROOT',self.root),patch.object(m,'SCRIPT',self.script),patch.object(m.time,'monotonic',lambda:self.wall),patch.object(m.q,'total_process_cpu',lambda:self.cpu),
                 patch.object(m.q,'selected_source',return_value=(self.board,'synthetic')),patch.object(m,'freeze',side_effect=self.freeze),patch.object(m,'cross_bind',return_value=self.reference),
                 patch.object(m.q,'verify_freeze',side_effect=self.stable),patch.object(m.p,'check_storage'),patch.object(m.p,'route',side_effect=self.route),
                 patch.object(m,'verify_arm',return_value={'engine_contract_verified':True}),patch.object(m.q,'summarize',side_effect=self.summarize)]
        for x in patches:x.start();self.addCleanup(x.stop)
    def freeze(self,board):self.wall+=5.;self.cpu+=4.;return copy.deepcopy(self.frozen)
    def stable(self,*args):
        if self.mode=='stale' and self.published:raise m.p.Rejected('synthetic postpublication stale source/code')
    def route(self,board,directory,seconds,keep,adapter,profile):
        self.calls.append((board,seconds,keep,adapter,profile));self.wall+=10.;self.cpu+=8.
        directory.mkdir();(directory/'candidate').mkdir();(directory/'candidate/board.kicad_pcb').write_text('synthetic board');(directory/'candidate/board.kicad_pro').write_text('synthetic rules');(directory/'final-drc.json').write_text('{}')
        if self.mode=='fail_first' and len(self.calls)==1:raise ValueError('synthetic failure')
        return {'status':'routing_accepted','accepted':True,'tools':self.frozen['tools'],'source_hashes':self.frozen['source_hashes']}
    def summarize(self,arm,directory,data,wall,cpu):
        return {**arm,'status':data['status'],'accepted':data['accepted'],'length_mm':12.,'vias':2}
    def run_case(self):
        real=m.p.save_json
        def save(path,data):
            if self.mode=='rewrite_fail' and Path(path)==self.out/'summary.json' and self.published:raise OSError('synthetic failed correction')
            real(path,data)
            if Path(path)==self.out/'summary.json' and not self.published:
                self.published=True
                if self.mode in {'interrupt','rewrite_fail'}:raise KeyboardInterrupt
                if self.mode=='sigterm':os.kill(os.getpid(),signal.SIGTERM)
                if self.mode=='wall_cap':self.wall+=120
                if self.mode=='cpu_cap':self.cpu+=120
                if self.mode in {'prior_project','prior_native_input'}:
                    path=self.prior/('candidate' if self.mode=='prior_project' else 'final-drc-input')/'board.kicad_pro'
                    path.parent.mkdir();path.write_text('changed synthetic rules')
                if self.mode in {'arm_board','arm_project','arm_report','protocol','frozen_code'}:
                    names={'arm_board':'B0_standard120/candidate/board.kicad_pcb','arm_project':'B0_standard120/candidate/board.kicad_pro','arm_report':'B0_standard120/final-drc.json','protocol':'protocol.json','frozen_code':'frozen-code/tampered'}
                    (self.out/names[self.mode]).write_text('changed synthetic evidence')
        with patch.object(m.p,'save_json',side_effect=save):return m.experiment(self.out,self.prior)
    def test_three_fresh_calls_shared_cost_charged_once_to_each(self):
        result=self.run_case();self.assertEqual(result['status'],'completed')
        self.assertEqual([(x[1],x[2],x[3],x[4]) for x in self.calls],[(120,False,'none','standard'),(120,False,'both','standard'),(120,False,'both','completion-only')])
        self.assertEqual([r['charged_wall_seconds'] for r in result['results']],[15]*3)
        self.assertEqual([r['charged_cpu_seconds'] for r in result['results']],[12]*3)
        self.assertEqual(len(result['comparisons']),3)
        self.assertEqual(result['comparisons'][2]['completion_difference'],0)
    def test_failed_attempt_cost_retained_and_next_arm_runs(self):
        self.mode='fail_first';data=self.run_case();self.assertEqual(len(self.calls),3)
        self.assertFalse(data['results'][0]['accepted']);self.assertEqual(data['results'][0]['charged_wall_seconds'],15)
    def test_final_keyboard_interrupt_invalidates_canonical_summary(self):
        self.mode='interrupt';self.run_case();stored=json.loads((self.out/'summary.json').read_text())
        self.assertEqual(stored['status'],'cancelled');self.assertFalse(any(x['accepted'] for x in stored['results']));self.assertEqual(stored['comparisons'],[])
    def test_actual_sigterm_is_caught_and_handlers_restored(self):
        previous={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
        self.mode='sigterm';data=self.run_case();self.assertEqual(data['status'],'cancelled');self.assertFalse(any(x['accepted'] for x in data['results']))
        self.assertEqual(previous,{s:signal.getsignal(s) for s in previous})
    def test_failed_correction_cannot_leave_accepted_canonical_summary(self):
        self.mode='rewrite_fail'
        with self.assertRaises(OSError):self.run_case()
        self.assertFalse((self.out/'summary.json').exists());self.assertTrue(list(self.out.glob('invalidated-*-summary.json')))
    def test_postpublication_wall_cap_invalidates(self):
        self.mode='wall_cap';data=self.run_case();self.assertEqual(data['status'],'invalidated');self.assertFalse(any(x['accepted'] for x in data['results']))
    def test_postpublication_cpu_cap_invalidates(self):
        self.mode='cpu_cap';data=self.run_case();self.assertEqual(data['status'],'invalidated');self.assertFalse(any(x['accepted'] for x in data['results']))
    def test_postpublication_prior_project_mutation_invalidates(self):
        self.mode='prior_project';data=self.run_case();self.assertEqual(data['status'],'invalidated');self.assertFalse(any(x['accepted'] for x in data['results']))
    def test_postpublication_prior_native_input_mutation_invalidates(self):
        self.mode='prior_native_input';data=self.run_case();self.assertEqual(data['status'],'invalidated');self.assertFalse(any(x['accepted'] for x in data['results']))
    def test_postpublication_new_candidate_mutation_invalidates(self):
        self.mode='arm_board';data=self.run_case();self.assertEqual(data['status'],'invalidated');self.assertFalse(any(x['accepted'] for x in data['results']))
    def test_postpublication_new_project_mutation_invalidates(self):
        self.mode='arm_project';data=self.run_case();self.assertEqual(data['status'],'invalidated');self.assertFalse(any(x['accepted'] for x in data['results']))
    def test_postpublication_new_report_mutation_invalidates(self):
        self.mode='arm_report';data=self.run_case();self.assertEqual(data['status'],'invalidated');self.assertFalse(any(x['accepted'] for x in data['results']))
    def test_postpublication_protocol_mutation_invalidates(self):
        self.mode='protocol';data=self.run_case();self.assertEqual(data['status'],'invalidated');self.assertFalse(any(x['accepted'] for x in data['results']))
    def test_postpublication_frozen_copy_mutation_invalidates(self):
        self.mode='frozen_code';data=self.run_case();self.assertEqual(data['status'],'invalidated');self.assertFalse(any(x['accepted'] for x in data['results']))
    def test_postpublication_staleness_invalidates(self):
        self.mode='stale';data=self.run_case();self.assertEqual(data['status'],'invalidated');self.assertFalse(any(x['accepted'] for x in data['results']))


class CrossBinding(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory(dir=ROOT);self.addCleanup(td.cleanup);self.root=Path(td.name);self.prior=self.root/'prior';self.prior.mkdir()
        self.board=self.root/'board';self.board.write_text('synthetic')
        self.script=self.root/'scripts/ablation.py';self.script.parent.mkdir();self.script.write_text('harness')
        oldfiles={'autorouter/a.py':'code','scripts/experiment_paired.py':'pair'}
        self.frozen={'tools':{'git_head':'new','implementation_sha256':{'autorouter/a.py':'code-hash'},'files':{'java':'java-hash'}},'source_hashes':{'board':'source-hash'},'files_sha256':{}}
        for name,text in oldfiles.items():
            dest=self.prior/'frozen-code'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text);self.frozen['files_sha256'][name]=m.p.sha(dest)
        self.old=copy.deepcopy(self.frozen);self.old['tools']['git_head']='old';self.frozen['files_sha256']['scripts/ablation.py']=m.p.sha(self.script)
        self.protocol={'freeze':self.old,'source':str(self.board),'arm_order':['B2_portfolio','C_thermal'],'system_contract':m.paired.THERMAL_ARM,'wall_budget_per_arm_seconds':120,'cpu_budget_per_arm_seconds':120}
        (self.prior/'protocol.json').write_text(json.dumps(self.protocol))
        bdir=self.prior/'B2_portfolio';bdir.mkdir();(bdir/'portfolio-summary.json').write_text('{}')
        cdir=self.prior/'C_thermal';cdir.mkdir();self.cdata={'accepted':False,'tools':self.old['tools'],'source_hashes':self.old['source_hashes']};(cdir/'result.json').write_text(json.dumps(self.cdata))
        self.rows=[{'id':'B2_portfolio','accepted':False,'result_sha256':'b','selected':None,'pareto_frontier':[],'trials':[]},{'id':'C_thermal','accepted':False,'result_sha256':m.p.sha(cdir/'result.json')}]
        for row in self.rows:row.update(invocation_wall_seconds=10.,invocation_cpu_seconds=8.,charged_wall_seconds=12.,charged_cpu_seconds=10.)
        self.summary={'status':'completed','protocol_sha256':m.p.sha(self.prior/'protocol.json'),'results':self.rows,'shared_overhead_wall_seconds':2.,'shared_overhead_cpu_seconds':2.,'batch_wall_seconds':22.,'batch_cpu_seconds':18.}
        self.write_summary()
        patches=[patch.object(m.c,'ROOT',self.root),patch.object(m,'SCRIPT',self.script),patch.object(m.paired,'verify_portfolio',return_value={**self.rows[0],'accepted':False})]
        for x in patches:x.start();self.addCleanup(x.stop)
    def write_summary(self):(self.prior/'paired-summary.json').write_text(json.dumps(self.summary))
    def check(self):return m.cross_bind(self.prior,self.board,self.frozen)
    def test_recorded_head_only_difference_and_added_harness_allowed(self):
        result=self.check();self.assertEqual((result['prior_git_head'],result['current_git_head']),('old','new'));self.assertTrue(result['production_source_tools_and_existing_protocol_bytes_equal'])
    def test_production_implementation_change_rejected(self):
        self.frozen['tools']['implementation_sha256']['autorouter/a.py']='changed'
        with self.assertRaises(m.p.Rejected):self.check()
    def test_tool_binary_change_rejected(self):
        self.frozen['tools']['files']['java']='changed'
        with self.assertRaises(m.p.Rejected):self.check()
    def test_source_change_rejected(self):
        self.frozen['source_hashes']['board']='changed'
        with self.assertRaises(m.p.Rejected):self.check()
    def test_existing_protocol_change_rejected(self):
        self.frozen['files_sha256']['scripts/experiment_paired.py']='changed'
        with self.assertRaises(m.p.Rejected):self.check()
    def test_inconsistent_prior_charged_budget_rejected(self):
        self.rows[0]['charged_cpu_seconds']=1.;self.write_summary()
        with self.assertRaises(m.p.Rejected):self.check()
    def test_prior_summary_change_detected_after_binding(self):
        result=self.check();(self.prior/'paired-summary.json').write_text('{}')
        with self.assertRaises(m.p.Rejected):m.unchanged(result['bound_files_sha256'])
    def test_full_prior_project_and_native_inputs_bound(self):
        path=self.prior/'C_thermal/candidate/board.kicad_pro';path.parent.mkdir();path.write_text('original rules')
        result=self.check();self.assertEqual(result['prior_tree_sha256'],m.p.tree_hash(self.prior))
        path.write_text('changed rules');self.assertNotEqual(result['prior_tree_sha256'],m.p.tree_hash(self.prior))
    def test_missing_prior_final_summary_rejected(self):
        (self.prior/'paired-summary.json').unlink()
        with self.assertRaises(m.p.Rejected):self.check()

class EngineContract(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory(dir=ROOT);self.addCleanup(td.cleanup);self.root=Path(td.name);self.directory=self.root/'arm';self.directory.mkdir()
        self.board=self.root/'board';self.board.write_text('synthetic');self.arm=dict(m.ARMS[2]);self.frozen={'tools':{'git_head':'new'},'source_hashes':{}}
        self.data={'tools':self.frozen['tools'],'source_hashes':{},'source':str(self.board),'budget_seconds':120,'cpu_budget_seconds':120,'scoring_variant':None,
                   'adapter':'both','engine_profile':'completion-only','scope':'whole_board_unlocked_routing','accepted':False,'status':'drc_rejected'}
        settings=m.p.engine_profile_settings('completion-only',100)
        self.data['engine_budget']={**settings,'outer_task_wall_budget_seconds':120,'outer_task_cpu_budget_seconds':120}
        argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(m.c.JAVA),'-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',str(m.c.JAR),'--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da','--user_data_path='+str(self.directory/'engine-config'),'--logging.file.enabled=false',*settings['argv'],'-de',str(self.directory/'task.dsn'),'-do',str(self.directory/'routes.ses')]
        self.data['steps']=[{'name':'engine','argv':argv,'cwd':str(self.directory),'status':'success','exit_code':0,'cleanup_complete':True}]
        for name,key in [('native.dsn','native_dsn_sha256'),('task.dsn','task_dsn_sha256')]:
            path=self.directory/name;path.write_text('synthetic DSN');self.data[key]=m.p.sha(path)
        self.process()
    def process(self):(self.directory/'engine-process.json').write_text(json.dumps(self.data['steps'][0]))
    def check(self):return m.verify_arm(self.arm,self.directory,self.data,self.board,self.frozen)
    def test_expected_native_rejection_still_checks_engine(self):
        result=self.check();self.assertTrue(result['engine_contract_verified']);self.assertTrue(result['engine_completed_successfully'])
    def test_rejected_engine_wrong_executable_blocked(self):
        self.data['steps'][0]['argv'][0]='/wrong';self.process()
        with self.assertRaises(m.p.Rejected):self.check()
    def test_rejected_engine_wrong_cwd_blocked(self):
        self.data['steps'][0]['cwd']=str(self.root);self.process()
        with self.assertRaises(m.p.Rejected):self.check()
    def test_rejected_engine_wrong_profile_blocked(self):
        self.data['engine_budget']['assigned_job_timeout_seconds']=1
        with self.assertRaises(m.p.Rejected):self.check()
    def test_rejected_task_hash_change_blocked(self):
        (self.directory/'task.dsn').write_text('changed')
        with self.assertRaises(m.p.Rejected):self.check()
    def test_timeout_invocation_contract_retained_without_success_claim(self):
        self.data.update(status='engine_failed');self.data['steps'][0].update(status='timeout',exit_code=-9);self.process()
        result=self.check();self.assertTrue(result['engine_contract_verified']);self.assertFalse(result['engine_completed_successfully'])
    def test_failure_before_engine_explicitly_unverified(self):
        self.data.update(status='unsupported',steps=[]);(self.directory/'engine-process.json').unlink()
        self.assertFalse(self.check()['engine_contract_verified'])
    def test_missing_engine_for_native_outcome_rejected(self):
        self.data['steps']=[];(self.directory/'engine-process.json').unlink()
        with self.assertRaises(m.p.Rejected):self.check()

if __name__=='__main__':unittest.main()
