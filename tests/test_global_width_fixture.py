"""Owned fixture and mutation controls; no Native/JVM acceptance evidence."""
import copy,json,signal,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,sexpr as sx
from experiments.stronger_incumbent_v1 import global_width_fixture as fixture,global_width_control as control
from experiments.placement_handoff_native_v1.driver import copy_bytes


class GlobalWidthFixture(unittest.TestCase):
    def test_exited_command_argv_cwd_cleanup_log_and_literal_are_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();folder=root/'.runs/global-min-width-command-001/run';folder.mkdir(parents=True)
            wrapper=root/'wrapper.py';wrapper.write_text('owned synthetic enclosure; never executed\n')
            log=folder/'command.log';log.write_text('actual command A\n')
            argv=[str(root/'.venv/bin/python'),'-B',str(Path(control.__file__)),'--mode','run','--source-head','owned','--protocol-sha256','pin']
            process=dict(argv=argv,cwd=str(folder),status='success',exit_code=0,cleanup_complete=True,log_truncated=False,log=str(log),log_bytes=log.stat().st_size)
            data=dict(mode='run',source_head='owned',passed=True,module_sha256=p.sha(Path(control.__file__)),controller_sha256=p.sha(wrapper),log_sha256=p.sha(log),process=process)
            receipt=folder/'execution.json';p.save_json(receipt,data)
            with patch.object(control,'ROOT',root),patch.object(control,'COMMAND',wrapper):
                original=control.check_command_enclosure('owned','pin')
                for mode in ('argv','cwd','cleanup','mode','log','log_path','log_size','log_size_bool','late_literal'):
                    changed=copy.deepcopy(data);log.write_text('actual command A\n')
                    if mode=='argv':changed['process']['argv'][-1]='wrong'
                    elif mode=='cwd':changed['process']['cwd']=str(root)
                    elif mode=='cleanup':changed['process']['cleanup_complete']=False
                    elif mode=='mode':changed['mode']='prepare'
                    elif mode=='log':log.write_text('actual command B\n')
                    elif mode=='log_path':changed['process']['log']=str(root/'wrong.log')
                    elif mode=='log_size':changed['process']['log_bytes']=1
                    elif mode=='log_size_bool':changed['process']['log_bytes']=True
                    else:changed['late_field']=True
                    p.save_json(receipt,changed)
                    with self.subTest(mode=mode):
                        if mode=='late_literal':self.assertNotEqual(control.check_command_enclosure('owned','pin'),original)
                        else:
                            with self.assertRaises(p.Rejected):control.check_command_enclosure('owned','pin')

    def test_controller_cancellation_exit_and_signal_handlers_are_preserved(self):
        handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
        for status,passed,code in [('cancelled',False,130),('completed',True,0),('failed',False,2)]:
            with self.subTest(status=status),patch.object(sys,'argv',['control','--mode','run','--source-head','owned','--protocol-sha256','pin']),patch.object(control.f,'read_json',return_value={'git_head':'owned'}),patch.object(control.p,'sha',return_value='pin'),patch.object(control,'context'),patch.object(control,'execute',return_value={'status':status,'passed':passed}),self.assertRaises(SystemExit) as result:
                control.main()
            self.assertEqual(result.exception.code,code)
            self.assertEqual({sig:signal.getsignal(sig) for sig in handlers},handlers)

    def test_fresh_source_has_original_positive_minimum_and_unchanged_Default_target(self):
        first=fixture.files();self.assertEqual(first,fixture.files())
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();copy_bytes(first,root/'source');board=root/'source'/(fixture.STEM+'.kicad_pcb')
            original=p.preflight(board);guard=p.global_width_source_guard(board)
            self.assertEqual(guard['min_track_width_mm'],.2)
            self.assertEqual(guard['original_project_sha256'],p.sha(board.with_suffix('.kicad_pro')))
            project=json.loads(first[fixture.STEM+'.kicad_pro'])
            self.assertEqual(project['net_settings']['classes'][0]['track_width'],.3)
            self.assertEqual(project['net_settings']['classes'][0]['priority'],2147483647)
            self.assertEqual(len(sx.children(original,'footprint')),6)
            self.assertEqual(len([r for r in p.routes(original) if p.locked(r)]),1)
            self.assertEqual(p.tree_hash(board.parent),{n:p.hashlib.sha256(raw).hexdigest() for n,raw in first.items()})

    def test_undersized_countercontrol_changes_one_tool_signal_width_and_preserves_KEEP(self):
        tree=sx.parse(fixture.files()[fixture.STEM+'.kicad_pcb'].decode())
        tree.append(['segment',['start','12','10'],['end','26','13'],['width','0.3'],['layer','"F.Cu"'],['net','"ROUTE"'],['uuid','"00000000-0000-4000-8000-000000000001"']])
        before=copy.deepcopy(tree);changed,rows=control.narrowed(tree)
        self.assertEqual(tree,before);self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['after_width'],'0.1');self.assertEqual(p.immutable(before),p.immutable(changed))
        self.assertEqual([r for r in p.routes(before) if p.locked(r)],[r for r in p.routes(changed) if p.locked(r)])
        restored=copy.deepcopy(changed);sx.one(p.routes(restored)[-1],'width')[1]='0.3';self.assertEqual(restored,before)


if __name__=='__main__':unittest.main()
