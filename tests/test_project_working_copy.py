"""Actual small filesystem controls; these do not establish Native routing."""
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from autorouter import pipeline as p, placement_clearance as pc

ROOT=Path(__file__).resolve().parents[1]

class ProjectWorkingCopyTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'.cache').mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'.cache')
        self.root=Path(self.tmp.name).resolve();self.source=self.root/'source'
        self.source.mkdir();(self.source/'nested').mkdir();(self.source/'empty').mkdir()
        (self.source/'board.kicad_pcb').write_bytes(b'(kicad_pcb (version 20260206))\n')
        (self.source/'board.kicad_pro').write_bytes(b'{"board": {}}\n')
        (self.source/'nested'/'owned-tool').write_bytes(b'fixture only; never execute\n')
        (self.source/'nested'/'owned-tool').chmod(0o500)
        self.destination=self.root/'working copy'
        self.addCleanup(self.dispose_owned_fixture)

    def dispose_owned_fixture(self):
        # All objects here were synthesized by this test. Restore their planned
        # fixture permissions for cleanup; never operate on project evidence.
        for folder,dirs,files in os.walk(self.root,topdown=True,followlinks=False):
            Path(folder).chmod(0o700)
            for name in dirs:
                q=Path(folder)/name
                if not q.is_symlink():q.chmod(0o700)
            for name in files:
                q=Path(folder)/name
                if not q.is_symlink():q.chmod(0o600)
        self.tmp.cleanup()

    def signature(self):
        files,dirs=pc.inventory(self.source,with_directories=True)
        modes={str(q.relative_to(self.source)):stat.S_IMODE(q.lstat().st_mode)
               for q in (self.source,*self.source.rglob('*'))}
        return files,dirs,modes

    def test_readonly_source_becomes_detached_mutable_copy_without_source_changes(self):
        for q in self.source.rglob('*'):
            q.chmod(0o500 if q.is_dir() or q.name=='owned-tool' else 0o400)
        self.source.chmod(0o500);before=self.signature()
        self.assertEqual(pc.copy_project(self.source,self.destination),before[0])
        self.assertEqual(pc.inventory(self.destination,with_directories=True)[:2],before[:2])
        self.assertEqual(self.signature(),before)
        for name in before[0]:
            a=self.source/name;b=self.destination/name
            self.assertNotEqual(a.stat().st_ino,b.stat().st_ino)
            self.assertEqual(b.stat().st_nlink,1)
            self.assertTrue(stat.S_IMODE(b.stat().st_mode)&stat.S_IWUSR)
        self.assertEqual(stat.S_IMODE((self.destination/'nested'/'owned-tool').stat().st_mode)&0o111,0o100)
        (self.destination/'board.kicad_pcb').write_bytes(b'only the generated copy changes\n')
        self.assertEqual(self.signature(),before)

    def test_restrictive_umask_does_not_break_new_working_copy_or_change_parent_process(self):
        before=self.signature()
        code='''import os,sys,json,stat
from pathlib import Path
from autorouter import placement_clearance as pc
os.umask(0o777)
source,dest=map(Path,sys.argv[1:]);pc.copy_project(source,dest)
print(json.dumps({"root_mode":stat.S_IMODE(dest.stat().st_mode),"file_mode":stat.S_IMODE((dest/"board.kicad_pcb").stat().st_mode),"exec_mode":stat.S_IMODE((dest/"nested"/"owned-tool").stat().st_mode)}))
'''
        env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1')
        result=subprocess.run([sys.executable,'-B','-c',code,str(self.source),str(self.destination)],
                              cwd=self.root,env=env,capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout),dict(root_mode=0o700,file_mode=0o600,exec_mode=0o700))
        self.assertEqual(self.signature(),before)

    def test_existing_destination_is_refused_without_overwrite(self):
        self.destination.mkdir();sentinel=self.destination/'keep';sentinel.write_bytes(b'unique retained bytes')
        before=self.signature()
        with self.assertRaises(p.Rejected):pc.copy_project(self.source,self.destination)
        self.assertEqual(sentinel.read_bytes(),b'unique retained bytes');self.assertEqual(self.signature(),before)

    def test_parent_alias_into_source_refused_before_creating_anything(self):
        other=self.root/'other';other.mkdir();before=self.signature()
        with self.assertRaises((p.Rejected,ValueError)):
            pc.copy_project(self.source,other/'..'/'source'/'new')
        self.assertFalse((self.source/'new').exists());self.assertEqual(self.signature(),before)

    def test_case_alias_into_source_refused_on_case_insensitive_filesystem(self):
        alias=self.root/'SOURCE'
        if not alias.exists() or not alias.samefile(self.source):self.skipTest('case-sensitive filesystem')
        before=self.signature()
        with self.assertRaises((p.Rejected,ValueError)):
            pc.copy_project(self.source,alias/'new')
        self.assertFalse((self.source/'new').exists());self.assertEqual(self.signature(),before)

    def test_links_refused_before_output_and_never_followed(self):
        outside=self.root/'outside';outside.mkdir();(outside/'keep').write_bytes(b'outside fixture')
        link=self.source/'link';link.symlink_to(outside,target_is_directory=True)
        with self.assertRaises(p.Rejected):pc.copy_project(self.source,self.destination)
        self.assertFalse(self.destination.exists());self.assertEqual((outside/'keep').read_bytes(),b'outside fixture')
        link.unlink();dest_link=self.root/'dest-link';dest_link.symlink_to(outside,target_is_directory=True)
        with self.assertRaises((p.Rejected,ValueError)):pc.copy_project(self.source,dest_link/'new')
        self.assertFalse((outside/'new').exists())

    def test_caps_refuse_before_creating_output(self):
        before=self.signature()
        for limits in (dict(max_bytes=1),dict(max_files=1),dict(max_entries=1)):
            with self.subTest(limits=limits),self.assertRaises(p.Rejected):
                pc.copy_project(self.source,self.destination,**limits)
            self.assertFalse(self.destination.exists());self.assertEqual(self.signature(),before)

    def test_changed_source_refuses_and_retains_both_versions(self):
        original=pc.inventory
        def observe(directory,**kwargs):
            if Path(directory)==self.source and not kwargs.get('contents',False):
                (self.source/'board.kicad_pro').write_bytes(b'changed by fixture actor\n')
            return original(directory,**kwargs)
        with patch.object(pc,'inventory',side_effect=observe),self.assertRaises(p.Rejected):
            pc.copy_project(self.source,self.destination)
        self.assertEqual((self.source/'board.kicad_pro').read_bytes(),b'changed by fixture actor\n')
        self.assertEqual((self.destination/'board.kicad_pro').read_bytes(),b'{"board": {}}\n')

    def test_new_empty_source_directory_refuses_and_retains_partial_copy(self):
        original=pc.inventory
        def observe(directory,**kwargs):
            if Path(directory)==self.source and not kwargs.get('contents',False):
                (self.source/'new-empty').mkdir()
            return original(directory,**kwargs)
        with patch.object(pc,'inventory',side_effect=observe),self.assertRaises(p.Rejected):
            pc.copy_project(self.source,self.destination)
        self.assertTrue((self.source/'new-empty').is_dir())
        self.assertFalse((self.destination/'new-empty').exists())
        self.assertEqual(pc.inventory(self.destination),pc.inventory(self.source))

    def test_source_hardlinks_are_read_without_mutating_their_shared_inode(self):
        a=self.source/'board.kicad_pro';linked=self.source/'linked-project';os.link(a,linked)
        before=self.signature();pc.copy_project(self.source,self.destination)
        (self.destination/'board.kicad_pro').write_bytes(b'new owned candidate\n')
        self.assertEqual(self.signature(),before)
        self.assertNotEqual(a.stat().st_ino,(self.destination/'board.kicad_pro').stat().st_ino)
        self.assertEqual(a.stat().st_ino,linked.stat().st_ino)

    def test_unreadable_source_is_not_repermissioned(self):
        if os.geteuid()==0:self.skipTest('root does not exercise ordinary read denial')
        target=self.source/'board.kicad_pro';target.chmod(0)
        with self.assertRaises(PermissionError):pc.copy_project(self.source,self.destination)
        self.assertFalse(self.destination.exists());self.assertEqual(stat.S_IMODE(target.stat().st_mode),0)

if __name__=='__main__':unittest.main()
