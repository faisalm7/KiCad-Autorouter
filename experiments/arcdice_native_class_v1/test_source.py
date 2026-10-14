"""Self-contained source capture regressions; no ignored-cache/native/network."""
import copy,hashlib,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments.arcdice_native_class_v1 import source as s
HERE=Path(__file__).absolute().parent

class SourceControls(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=HERE,prefix='source-test-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.source=self.root/s.SOURCE_RELATIVE;self.source.mkdir(parents=True);self.original_rows=copy.deepcopy(s.ROWS);rows=copy.deepcopy(s.ROWS);self.files={}
  for row in rows:
   prefix=('pure capture fixture '+row['source_path']+'\n').encode();raw=prefix+b'x'*(row['bytes']-len(prefix));self.files[row['source_path']]=raw
   row['sha256']=hashlib.sha256(raw).hexdigest();row['git_blob_sha1']=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
   path=self.source/row['source_path'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
  patch=mock.patch.object(s,'ROWS',tuple(rows));patch.start();self.addCleanup(patch.stop)
 def test_capture_complete_original_paths_bytes_and_readonly_source(self):
  before=s.shared.inventory(self.source);captured=s.capture(self.root)
  self.assertEqual(captured,self.files);self.assertEqual((len(captured),sum(map(len,captured.values()))),(5,595341));self.assertEqual(s.shared.inventory(self.source),before)
  captured['LICENSE']=b'changed caller map';self.assertEqual((self.source/'LICENSE').read_bytes(),self.files['LICENSE']);self.assertNotIn('_licenses',captured)
 def test_source_identity_and_names_are_frozen_independently_of_cache(self):
  self.assertEqual((s.REPOSITORY,s.COMMIT),('VorosEgyes/ArcDice','5908d99db1ef98b5996b380c75e5aee8bb8caaa6'))
  self.assertEqual({r['source_path']:r['bytes'] for r in self.original_rows},{'LICENSE':1067,'README.md':2930,'hardware/ArcDice.kicad_pcb':488060,'hardware/ArcDice.kicad_pro':17925,'hardware/ArcDice.kicad_sch':85359})
  self.assertEqual(next(r['sha256'] for r in self.original_rows if r['source_path'].endswith('.kicad_pcb')),'098e90725279e698f61d7f4a5f0281202ba32f655b9c430047c019783a60bf96')
 def test_same_size_tampering_and_truncation_reject(self):
  path=self.source/'hardware/ArcDice.kicad_pro';raw=path.read_bytes()
  for bad in [b'z'+raw[1:],raw[:-1]]:
   with self.subTest(size=len(bad)):
    path.write_bytes(bad)
    with self.assertRaises(ValueError):s.capture(self.root)
 def test_extra_script_rule_or_empty_directory_rejects_without_execution(self):
  for name in ['script.py','hardware/ArcDice.kicad_dru']:
   path=self.source/name;path.write_bytes(b'raise AssertionError("never execute")')
   actual=s.shared.bounded
   def no_extra_read(target,*args,**kwargs):
    if Path(target)==path:raise AssertionError('unexpected member read')
    return actual(target,*args,**kwargs)
   with mock.patch.object(s.shared,'bounded',side_effect=no_extra_read),self.assertRaises(ValueError):s.capture(self.root)
   path.unlink()
  (self.source/'unexpected').mkdir()
  with self.assertRaises(ValueError):s.capture(self.root)
 def test_symlink_member_rejected_without_reading_target(self):
  target=self.root/'unrelated-owned-fixture';target.write_bytes(b'no traversal');link=self.source/'link';link.symlink_to(target)
  actual=s.shared.bounded
  def guarded(path,*args,**kwargs):
   if Path(path)==target:raise AssertionError('symlink target read')
   return actual(path,*args,**kwargs)
  with mock.patch.object(s.shared,'bounded',side_effect=guarded),self.assertRaisesRegex(ValueError,'symlink'):s.capture(self.root)
 def test_symlink_source_ancestor_rejects_before_inventory(self):
  parent=self.source.parent;renamed=parent.with_name('owned-original');parent.rename(renamed);parent.symlink_to(renamed,target_is_directory=True)
  with mock.patch.object(s.shared,'inventory',side_effect=AssertionError('must reject before inventory')),self.assertRaisesRegex(ValueError,'symlink'):s.capture(self.root)
 def test_stale_source_after_returned_payload_detected_by_final_inventory(self):
  actual=s.shared.bounded;calls=[]
  def changed(path,*args,**kwargs):
   raw=actual(path,*args,**kwargs);calls.append(Path(path))
   if len(calls)==6:
    target=self.source/'LICENSE';old=target.read_bytes();target.write_bytes(b'z'+old[1:])
   return raw
  with mock.patch.object(s.shared,'bounded',side_effect=changed),self.assertRaisesRegex(ValueError,'inventory changed'):s.capture(self.root)
 def test_missing_source_has_no_managed_data_or_model_fallback(self):
  other=self.root/'other';other.mkdir();(other/'.data').mkdir()
  with self.assertRaises(FileNotFoundError):s.capture(other)
  self.assertEqual(list((other/'.data').iterdir()),[])
if __name__=='__main__':unittest.main()
