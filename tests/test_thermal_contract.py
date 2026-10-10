"""Adversarial filesystem receipt controls only; no native or engine execution."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=next(parent for parent in Path(__file__).resolve().parents
          if (parent/'autorouter'/'pipeline.py').is_file())
sys.path.insert(0,str(ROOT))
from scripts import experiment_paired as m


class ThermalContract(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(dir=ROOT/'.runs')
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);self.directory=self.root/'C_thermal';self.inc=self.directory/'incumbent'
        self.inc.mkdir(parents=True);self.board=self.root/'source.kicad_pcb'
        self.board.write_text('synthetic original')
        self.frozen={'source_hashes':{'source.kicad_pcb':m.p.sha(self.board)},'tools':{'git_head':'synthetic'}}
        for name in ('native.dsn','task.dsn'):(self.inc/name).write_text('synthetic '+name)
        settings=m.p.engine_profile_settings('completion-only',70.,strict_class_targets=True)
        settings.update(outer_task_wall_budget_seconds=80.,outer_task_cpu_budget_seconds=80.)
        argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(m.c.JAVA),
              '-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',str(m.c.JAR),
              '--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da',
              '--user_data_path='+str(self.inc/'engine-config'),'--logging.file.enabled=false',
              *settings['argv'],'-de',str(self.inc/'task.dsn'),'-do',str(self.inc/'routes.ses')]
        self.data={**copy.deepcopy(self.frozen),'source':str(self.board),'adapter':'both',
                   'engine_profile':'completion-only','scoring_variant':None,'scope':'whole_board_unlocked_routing',
                   'budget_seconds':80.,'cpu_budget_seconds':80.,'accepted':False,'status':'drc_rejected',
                   'netclass_policy':{'mode':'literal_two_class'},'engine_budget':settings,
                   'steps':[{'name':'engine','argv':argv,'cwd':str(self.inc),'status':'success','exit_code':0,
                             'cleanup_complete':True,'log_truncated':False}],
                   'native_dsn_sha256':m.p.sha(self.inc/'native.dsn'),'task_dsn_sha256':m.p.sha(self.inc/'task.dsn')}
        self.result={'accepted':True,'budget_seconds':120.,'recovery_reserve_seconds':40.,
                     'incumbent_assigned_seconds':80.,'incumbent':{'receipt':str(self.inc/'result.json'),
                       'status':'drc_rejected','accepted':False}}
        self.publish()

    def publish(self):
        (self.inc/'result.json').write_text(json.dumps(self.data))
        (self.inc/'engine-process.json').write_text(json.dumps(self.data['steps'][0]))
        self.result['incumbent']['receipt_sha256']=m.p.sha(self.inc/'result.json')

    def verify(self):return m.verify_thermal_incumbent(self.directory,self.result,self.board,self.frozen)

    def test_positive_bound_rejected_incumbent(self):self.verify()

    def test_receipt_bytes_changed(self):
        (self.inc/'result.json').write_text('{}')
        with self.assertRaises(m.p.Rejected):self.verify()

    def test_wrong_declared_contract(self):
        changes={'source':str(self.root/'other.kicad_pcb'),'source_hashes':{},'tools':{},'adapter':'none',
                 'engine_profile':'tuned','scoring_variant':'via_low','scope':'partial_completion',
                 'budget_seconds':81.,'cpu_budget_seconds':81.,'accepted':True,'status':'timeout'}
        original=copy.deepcopy(self.data)
        for key,value in changes.items():
            with self.subTest(key=key):
                self.data=copy.deepcopy(original);self.data[key]=value;self.publish()
                with self.assertRaises(m.p.Rejected):self.verify()

    def test_router_setting_tampered_in_both_receipts(self):
        step=self.data['steps'][0];step['argv']=[x.replace('--router.optimizer.enabled=false','--router.optimizer.enabled=true') for x in step['argv']]
        self.publish()
        with self.assertRaises(m.p.Rejected):self.verify()

    def test_process_receipt_differs(self):
        (self.inc/'engine-process.json').write_text('{}')
        with self.assertRaises(m.p.Rejected):self.verify()

    def test_raw_or_task_export_changed(self):
        for name in ('native.dsn','task.dsn'):
            with self.subTest(name=name):
                old=(self.inc/name).read_bytes();(self.inc/name).write_text('changed')
                with self.assertRaises(m.p.Rejected):self.verify()
                (self.inc/name).write_bytes(old)

    def test_wrong_engine_executable_even_with_correct_router_flags(self):
        self.data['steps'][0]['argv'][3]='/usr/bin/true';self.publish()
        with self.assertRaises(m.p.Rejected):self.verify()

    def test_wrong_engine_input_even_with_correct_router_flags(self):
        self.data['steps'][0]['argv'][-3]=str(self.root/'different.dsn');self.publish()
        with self.assertRaises(m.p.Rejected):self.verify()

    def test_wrong_engine_working_directory(self):
        self.data['steps'][0]['cwd']=str(self.root);self.publish()
        with self.assertRaises(m.p.Rejected):self.verify()

    def test_symlink_incumbent_directory(self):
        moved=self.root/'different-incumbent';self.inc.rename(moved);self.inc.symlink_to(moved,target_is_directory=True)
        with self.assertRaises(m.p.Rejected):self.verify()

    def test_internal_remaining_cannot_exceed_assigned_budget(self):
        settings=m.p.engine_profile_settings('completion-only',200.,strict_class_targets=True)
        settings.update(outer_task_wall_budget_seconds=80.,outer_task_cpu_budget_seconds=80.)
        self.data['engine_budget']=settings
        old=self.data['steps'][0]['argv'];i=next(i for i,a in enumerate(old) if a.startswith('--router.'))
        self.data['steps'][0]['argv']=old[:i]+settings['argv']+old[-4:];self.publish()
        with self.assertRaises(m.p.Rejected):self.verify()


if __name__=='__main__':unittest.main(verbosity=2)
