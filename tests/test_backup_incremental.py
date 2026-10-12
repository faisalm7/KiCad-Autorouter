"""Small actual Git/archive chains; no project-wide backups or native execution."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import unittest
from unittest.mock import patch
from scripts import backup

spec=importlib.util.spec_from_file_location('backup_existing_fixture',Path(__file__).with_name('test_backup.py'))
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)


class IncrementalTests(unittest.TestCase):
    setUp=fixture.BackupTests.setUp

    def base(self):
        receipt=backup.create(self.root);backup.verify(receipt,self.root);return receipt

    def write(self,path,value):
        path.write_text(json.dumps(value,sort_keys=True)+'\n')

    def test_two_deltas_restore_latest_files_empty_directories_absence_and_git(self):
        full=self.base(); full_bytes={p.name:p.read_bytes()for p in full.parent.iterdir()if p.is_file()}
        (self.root/'.data/board.bin').write_bytes(b'changed')
        (self.root/'.runs/new').mkdir();(self.root/'.runs/new/raw').write_bytes(b'new raw')
        (self.root/'.runs/literal ; $(ignored).json').unlink()
        first=backup.create(self.root,parent=full);one=json.loads(first.read_text())
        self.assertEqual([r['path']for r in one['delta']['inventory']['files']],['.data/board.bin','.runs/new/raw'])
        self.assertEqual(one['delta']['deleted_files'],['.runs/literal ; $(ignored).json'])
        integrity=json.loads(backup.checkpoint(first,self.root).read_text())
        self.assertTrue(integrity['integrity_checked']);self.assertFalse(integrity['full_restoration_tested'])
        (self.root/'.data/board.bin').unlink();(self.root/'.data/board.bin').mkdir();(self.root/'.data/board.bin/inside').write_text('file became directory')
        (self.root/'.runs/new/raw').unlink();(self.root/'.runs/new').rmdir();(self.root/'.runs/new').write_text('directory became file')
        (self.root/'.local-reference/history.md').unlink();(self.root/'.local-reference').rmdir()
        (self.root/'.runs/empty').mkdir()
        (self.root/'new-source').write_text('source checkpoint')
        backup.git(self.root,'add','new-source');backup.git(self.root,'commit','--quiet','-m','next source');backup.git(self.root,'tag','next-tag')
        second=backup.create(self.root,parent=first);two=json.loads(second.read_text())
        self.assertIn('.local-reference',two['delta']['deleted_directories'])
        result=json.loads(backup.verify(second,self.root).read_text());restored=Path(result['restore_directory'])
        self.assertTrue(result['full_restoration_tested']);self.assertEqual(result['chain_length'],3)
        self.assertEqual(backup.inventory(restored/'non-git'),backup.inventory(self.root))
        self.assertEqual(backup.git(restored/'checkout','show-ref'),backup.git(self.root,'show-ref'))
        self.assertEqual((restored/'checkout/new-source').read_text(),'source checkpoint')
        self.assertFalse((restored/'non-git/.local-reference').exists());self.assertTrue((restored/'non-git/.runs/empty').is_dir())
        for name,raw in full_bytes.items():self.assertEqual((full.parent/name).read_bytes(),raw)

    def test_unchanged_delta_has_no_file_payload_and_old_full_still_restores(self):
        full=self.base();delta=backup.create(self.root,parent=full);value=json.loads(delta.read_text())
        self.assertEqual(value['delta']['inventory']['files'],[]);self.assertEqual(value['delta']['deleted_files'],[])
        self.assertTrue(json.loads(backup.verify(delta,self.root).read_text())['verified'])
        self.assertTrue(json.loads(backup.verify(full,self.root).read_text())['verified'])

    def test_unverified_full_and_different_source_parent_refused(self):
        full=backup.create(self.root)
        with self.assertRaisesRegex(backup.BackupError,'restore-verified'):backup.create(self.root,parent=full)
        backup.verify(full,self.root)
        value=json.loads(full.read_text());value['source_root']='/different/original';self.write(full,value)
        # A matching restoration record cannot grant access to a different source checkout.
        backup.verify(full,self.root)
        with self.assertRaisesRegex(backup.BackupError,'different original'):backup.create(self.root,parent=full)

    def test_missing_parent_changed_parent_and_cycle_refused(self):
        full=self.base();delta=backup.create(self.root,parent=full);raw=full.read_bytes()
        full.rename(full.with_suffix('.held'))
        with self.assertRaises(OSError):backup.load_chain(delta,self.root)
        full.with_suffix('.held').rename(full)
        full.write_bytes(raw+b' ')
        with self.assertRaisesRegex(backup.BackupError,'Parent receipt hash'):backup.load_chain(delta,self.root)
        full.write_bytes(raw)
        value=json.loads(delta.read_text());value['parent']={'name':delta.relative_to(self.root/'.local-backups').as_posix(),'sha256':'0'*64};self.write(delta,value)
        with self.assertRaisesRegex(backup.BackupError,'cycle'):backup.load_chain(delta,self.root)

    def test_deleted_or_changed_file_cannot_disappear_from_delta_accounting(self):
        full=self.base();(self.root/'.data/board.bin').unlink();(self.root/'.runs/new').write_text('new')
        delta=backup.create(self.root,parent=full);original=json.loads(delta.read_text())
        for key in ('deletion','payload','directory'):
            v=copy.deepcopy(original)
            if key=='deletion':v['delta']['deleted_files']=[]
            elif key=='payload':v['delta']['inventory']['files']=[];v['delta']['inventory']['total_file_bytes']=0
            else:v['delta']['deleted_directories']=['.runs']
            self.write(delta,v)
            with self.subTest(key=key),self.assertRaisesRegex(backup.BackupError,'accounting'):backup.load_chain(delta,self.root)

    def test_parent_artifact_verification_and_new_archive_tampering_refused(self):
        full=self.base();delta=backup.create(self.root,parent=full);v=json.loads(delta.read_text())
        proof=self.root/'.local-backups'/v['base_verification']['name'];saved=proof.read_bytes();proof.write_bytes(saved+b' ')
        with self.assertRaisesRegex(backup.BackupError,'restoration evidence'):backup.load_chain(delta,self.root)
        proof.write_bytes(saved)
        archive=delta.parent/'non-git.tar.gz';saved=archive.read_bytes();archive.write_bytes(saved+b'bad')
        with self.assertRaisesRegex(backup.BackupError,'artifact size/hash'):backup.verify(delta,self.root)
        archive.write_bytes(saved)
        parent_archive=full.parent/'non-git.tar.gz';parent_archive.write_bytes(parent_archive.read_bytes()+b'bad')
        with self.assertRaisesRegex(backup.BackupError,'artifact size/hash'):backup.checkpoint(delta,self.root)

    def test_reference_escape_symlink_duplicate_json_and_chain_ceiling(self):
        full=self.base();delta=backup.create(self.root,parent=full);original=json.loads(delta.read_text())
        for name in ('../receipt.json','/receipt.json','checkpoint/../receipt.json'):
            v=copy.deepcopy(original);v['parent']['name']=name;self.write(delta,v)
            with self.subTest(name=name),self.assertRaises(backup.BackupError):backup.load_chain(delta,self.root)
        self.write(delta,original)
        saved=full.read_bytes();full.unlink();full.symlink_to(delta)
        with self.assertRaisesRegex(backup.BackupError,'regular receipt'):backup.load_chain(delta,self.root)
        full.unlink();full.write_bytes(saved)
        delta.write_text('{"schema":2,"schema":1}')
        with self.assertRaisesRegex(backup.BackupError,'Duplicate'):backup.load_chain(delta,self.root)
        self.write(delta,original)
        with patch.object(backup,'MAX_CHAIN',2),self.assertRaisesRegex(backup.BackupError,'ceiling'):backup.create(self.root,parent=delta)

    def test_late_parent_receipt_or_proof_mutation_never_writes_integrity_success(self):
        for target_kind in ('receipt','proof'):
            with self.subTest(target_kind=target_kind):
                full=self.base();delta=backup.create(self.root,parent=full);data=json.loads(delta.read_text())
                target=full if target_kind=='receipt' else self.root/'.local-backups'/data['base_verification']['name']
                saved=target.read_bytes();real=backup.restore_archive
                def restore(*args,**kwargs):
                    real(*args,**kwargs);target.write_bytes(saved+b' ')
                with patch.object(backup,'restore_archive',side_effect=restore),self.assertRaises(backup.BackupError):backup.checkpoint(delta,self.root)
                self.assertEqual(list(delta.parent.glob('integrity-*.json')),[]);target.write_bytes(saved)

    def test_rehashed_bad_delta_payload_still_fails_its_complete_inventory(self):
        full=self.base();path=self.root/'.runs/new';path.write_text('good')
        delta=backup.create(self.root,parent=full);value=json.loads(delta.read_text());archive=delta.parent/'non-git.tar.gz'
        archive.rename(archive.with_suffix('.original'));path.write_text('evil')
        backup.make_archive(self.root,archive,value['delta']['inventory'])
        value['archive'].update(size=archive.stat().st_size,sha256=backup.digest(archive));self.write(delta,value)
        with self.assertRaisesRegex(backup.BackupError,'file hash mismatch'):backup.load_chain(delta,self.root)

    def test_publication_cancellation_or_late_material_staleness_preserves_no_positive_proof(self):
        for kind in ('cancel','stale','canonical'):
            with self.subTest(kind=kind):
                out=self.root/(kind+'.json');calls=0;real=backup.exclusive_json
                def write(path,value):
                    real(path,value)
                    if kind=='cancel':raise KeyboardInterrupt('after write')
                    if kind=='canonical':path.write_text('{"verified": true}')
                def stable():
                    nonlocal calls
                    calls+=1
                    if calls==2 and kind=='stale':raise backup.BackupError('material changed')
                with patch.object(backup,'exclusive_json',side_effect=write),self.assertRaises((backup.BackupError,KeyboardInterrupt)):
                    backup.publish_check(out,{'verified':True,'receipt_sha256':'0'*64},stable)
                self.assertFalse(out.exists());self.assertEqual(len(list(self.root.glob('invalidated-*-'+out.name))),1)


    def test_second_archive_pass_rechecks_whitelist_before_opening_targets(self):
        for kind in ('escape', 'unknown', 'directory', 'symlink', 'size', 'duplicate', 'missing'):
            with self.subTest(kind=kind):
                root=self.root/kind;root.mkdir();(root/'.data').mkdir()
                (root/'.data/payload').write_bytes(b'original')
                manifest=backup.inventory(root);archive=root/'data.tgz'
                backup.make_archive(root,archive,manifest);real=backup.audit_archive
                def audit(*args,**kwargs):
                    result=real(*args,**kwargs)
                    with tarfile.open(archive,'w:gz') as writer:
                        directory=tarfile.TarInfo('.data');directory.type=tarfile.DIRTYPE
                        writer.addfile(directory)
                        if kind=='directory':
                            extra=tarfile.TarInfo('.data/unknown');extra.type=tarfile.DIRTYPE;writer.addfile(extra)
                        if kind!='missing':
                            name={'escape':'../outside','unknown':'.data/unlisted'}.get(kind,'.data/payload')
                            item=tarfile.TarInfo(name)
                            if kind=='symlink':
                                item.type=tarfile.SYMTYPE;item.linkname='../outside';writer.addfile(item)
                            else:
                                raw=b'originalx' if kind=='size' else b'original'
                                item.size=len(raw);writer.addfile(item,io.BytesIO(raw))
                                if kind=='duplicate':writer.addfile(item,io.BytesIO(raw))
                    return result
                with patch.object(backup,'audit_archive',side_effect=audit),self.assertRaises(backup.BackupError):
                    backup.restore_archive(archive,root/'restore',manifest)
                self.assertFalse((root/'outside').exists())
                self.assertFalse((root/'restore/.data/unlisted').exists())
                self.assertFalse((root/'restore/.data/unknown').exists())
                if kind!='duplicate':self.assertFalse((root/'restore/.data/payload').exists())
                self.assertEqual((root/'.data/payload').read_bytes(),b'original')

    def test_archive_payload_read_is_bounded_and_rejects_truncation_or_overflow(self):
        class Source:
            def __init__(self,raw):self.raw=raw;self.read_sizes=[]
            def extractfile(self,item):
                outer=self
                class Payload(io.BytesIO):
                    def read(self,size=-1):
                        outer.read_sizes.append(size);return super().read(size)
                return Payload(self.raw)
        row={'size':8,'sha256':backup.hashlib.sha256(b'original').hexdigest()}
        for raw in (b'original',b'orig',b'original-excess'):
            source=Source(raw);out=io.BytesIO()
            if raw==b'original':backup.archive_payload(source,None,row,out)
            else:
                with self.assertRaises(backup.BackupError):backup.archive_payload(source,None,row,out)
            self.assertLessEqual(len(out.getvalue()),8)
            self.assertTrue(all(0<size<=8 for size in source.read_sizes))
            if len(raw)>=8:self.assertEqual(source.read_sizes,[8,1])

    def test_actual_child_signals_after_proof_write_invalidate_and_restore_handler(self):
        script = r'''from pathlib import Path
import json,os,signal,sys
sys.path.insert(0,sys.argv[1])
from scripts import backup
proof=Path(sys.argv[2]);which=sys.argv[3];original=backup.exclusive_json
def prior_term(signum,frame):pass
signal.signal(signal.SIGTERM,prior_term)
previous_int=signal.getsignal(signal.SIGINT)
def write(path,value):
    original(path,value)
    if which!='none':os.kill(os.getpid(),getattr(signal,which))
backup.exclusive_json=write
cancelled=False
try:backup.publish_check(proof,{'verified':True},lambda:None)
except KeyboardInterrupt:cancelled=True
print(json.dumps({'cancelled':cancelled,'term_restored':signal.getsignal(signal.SIGTERM) is prior_term,
                  'int_restored':signal.getsignal(signal.SIGINT) is previous_int}))
sys.exit(3 if cancelled else 0)
'''
        for which in ('none','SIGINT','SIGTERM'):
            with self.subTest(which=which):
                out=self.root/('signal-'+which+'.json')
                result=subprocess.run([sys.executable,'-B','-c',script,str(backup.ROOT),str(out),which],
                                      capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,0 if which=='none' else 3,result.stderr)
                state=json.loads(result.stdout)
                self.assertTrue(state['term_restored']);self.assertTrue(state['int_restored'])
                self.assertEqual(state['cancelled'],which!='none')
                invalidated=list(self.root.glob('invalidated-*-'+out.name))
                self.assertEqual(out.exists(),which=='none')
                self.assertEqual(len(invalidated),0 if which=='none' else 1)
                if invalidated:self.assertEqual(json.loads(invalidated[0].read_text()),{'verified':True})


if __name__=='__main__':unittest.main()
