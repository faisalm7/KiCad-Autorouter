"""Actual owned-file OS controls; no mocked native pass or rule waiver."""
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from autorouter import pipeline as p, handoff as h
from autorouter.runner import run
from experiments.original_project_native_v1.local_settings import preserve


@unittest.skipUnless(sys.platform=='darwin' and hasattr(os,'chflags'), 'Mac file flags required')
class LocalSettingsPreservation(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='prl-control-',dir=p.c.ROOT/'.runs')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.owner={};h.capture_destination(self.owner,self.root)
        self.path=self.root/'owned.kicad_prl';self.path.write_bytes(b'{"authored":"unchanged"}\n')

    def test_actual_overwrite_truncate_atomic_replace_and_unlink_denied(self):
        before=self.path.read_bytes();replacement=self.root/'replacement';replacement.write_bytes(b'changed')
        with preserve(self.path,self.root,self.owner) as event:
            operations=[lambda:self.path.write_bytes(b'changed'),
                        lambda:os.truncate(self.path,0),
                        lambda:os.replace(replacement,self.path),lambda:self.path.unlink()]
            for operation in operations:
                with self.assertRaises(PermissionError):operation()
                self.assertEqual(self.path.read_bytes(),before)
            self.assertEqual(self.path.stat().st_flags,stat.UF_IMMUTABLE)
        self.assertTrue(event['flags_restored']);self.assertTrue(event['bytes_unchanged'])
        self.path.write_bytes(b'ordinary owned file again')

    def test_cancellation_and_exception_restore_flags_without_byte_changes(self):
        before=p.sha(self.path)
        for exception in (ValueError,KeyboardInterrupt):
            with self.subTest(exception=exception),self.assertRaises(exception):
                with preserve(self.path,self.root,self.owner):raise exception('deliberate control')
            self.assertEqual(self.path.stat().st_flags,0);self.assertEqual(p.sha(self.path),before)

    def test_unconfirmed_child_cleanup_keeps_protection_until_explicit_owned_cleanup(self):
        try:
            with self.assertRaisesRegex(p.Rejected,'cleanup not confirmed'):
                with preserve(self.path,self.root,self.owner,cleanup_complete=lambda:False):pass
            self.assertEqual(self.path.stat().st_flags,stat.UF_IMMUTABLE)
        finally:
            os.chflags(self.path,0,follow_symlinks=False)

    def test_actual_timed_out_worker_reaped_before_flag_restore(self):
        state={'complete':False};before=p.sha(self.path)
        with preserve(self.path,self.root,self.owner,cleanup_complete=lambda:state['complete']) as event:
            result=run([sys.executable,'-c','import time; time.sleep(10)'],cwd=self.root,
                       log=self.root/'worker.log',timeout=.2,max_log_bytes=1024,
                       max_workdir_bytes=4096,max_group_rss_bytes=128*1024**2)
            state['complete']=result['cleanup_complete']
            self.assertEqual(result['status'],'timeout')
        self.assertTrue(event['flags_restored']);self.assertEqual(p.sha(self.path),before)

    def test_noncanonical_symlink_hardlink_and_preexisting_flags_refuse(self):
        for path,root in ((self.path,p.c.ROOT/'.runs'),
                          (self.root/'child'/'..'/self.path.name,self.root)):
            with self.subTest(path=path,root=root),self.assertRaises(p.Rejected):
                with preserve(path,root,self.owner):pass
        link=self.root/'link.kicad_prl';link.symlink_to(self.path)
        with self.assertRaises(p.Rejected):
            with preserve(link,self.root,self.owner):pass
        link.unlink();os.link(self.path,link)
        with self.assertRaises(p.Rejected):
            with preserve(self.path,self.root,self.owner):pass
        link.unlink()
        try:
            os.chflags(self.path,stat.UF_NODUMP,follow_symlinks=False)
            with self.assertRaises(p.Rejected):
                with preserve(self.path,self.root,self.owner):pass
            self.assertEqual(self.path.stat().st_flags,stat.UF_NODUMP)
        finally:os.chflags(self.path,0,follow_symlinks=False)

    def test_replaced_captured_root_is_not_adopted(self):
        moved=self.root.with_name(self.root.name+'-moved')
        self.root.rename(moved)
        try:
            self.root.mkdir();self.path.write_bytes(b'unrelated replacement')
            with self.assertRaisesRegex(p.Rejected,'replaced'):
                with preserve(self.path,self.root,self.owner):pass
            self.assertEqual(self.path.stat().st_flags,0)
            self.assertEqual((moved/self.path.name).stat().st_flags,0)
        finally:
            self.path.unlink();self.root.rmdir();moved.rename(self.root)

    def test_failed_cleanup_worker_metadata_survives_guard_refusal(self):
        # Deliberately invalid runner metadata, no native process or pass.
        from experiments.original_project_native_v1 import driver as d
        from scripts import fetch_led_demo as demo
        project='audio-player-my1690x';cfg=demo.fixed_profile(project)
        name=Path(cfg['board_path']).name;fixture=p.c.ROOT/'fixtures/smoke/smoke.kicad_pcb'
        files={'Hardware/'+name:fixture.read_bytes(),
               'Hardware/'+Path(name).with_suffix('.kicad_pro').name:fixture.with_suffix('.kicad_pro').read_bytes(),
               'Hardware/'+Path(name).with_suffix('.kicad_prl').name:self.path.read_bytes()}
        original_run=d.subprocess.run
        def committed(args,**kwargs):
            if args[:2]==['git','show']:
                return SimpleNamespace(stdout=(p.c.ROOT/args[2].split(':',1)[1]).read_bytes())
            return original_run(args,**kwargs)
        def failed_worker(args,**kwargs):
            Path(kwargs['log']).write_text('Controlled metadata only; no Native launched.\n')
            return {'status':'timeout','exit_code':-15,'cleanup_complete':False,
                    'argv':args,'cwd':str(kwargs['cwd']),'log':str(kwargs['log']),
                    'wall_seconds':.01,'cpu_seconds':0.,'monitor_cpu_seconds':0.}
        out=self.root/'diagnostic'
        try:
            with patch.object(d.subprocess,'run',side_effect=committed),\
                 patch.object(d,'run',side_effect=failed_worker),\
                 patch.object(demo,'capture_native_source',return_value=(self.root,files)):
                result=d.experiment(project,str(out),run_native=True,protect_local_settings=True)
            self.assertEqual(result['status'],'failed');self.assertFalse(result['accepted'])
            receipt=d.f.read_json(out/'job/original-refill-process.json')
            self.assertFalse(receipt['cleanup_complete'])
            self.assertIn('cleanup not confirmed',receipt['local_settings_protection']['guard_error'])
            self.assertEqual(result['steps'][0],receipt)
            self.assertEqual((out/'saved'/Path(name).with_suffix('.kicad_prl').name).stat().st_flags,stat.UF_IMMUTABLE)
        finally:
            for path in out.rglob('*.kicad_prl'):
                if path.stat().st_flags==stat.UF_IMMUTABLE:os.chflags(path,0,follow_symlinks=False)


if __name__=='__main__':unittest.main()
