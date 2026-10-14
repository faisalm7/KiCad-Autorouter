"""Actual descriptor copy boundaries; only tiny authored fixtures, no native."""
import copy,os,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments.placement_handoff_native_v1 import driver as d
HERE=Path(__file__).absolute().parent

class CopyBoundaries(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=HERE,prefix='copy-test-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.target=self.root/'packet';self.files={'LICENSE':b'authored notice','README.md':b'authored readme','hardware/board.kicad_pcb':b'authored pcb','hardware/board.kicad_pro':b'{}','hardware/board.kicad_sch':b'authored sch'}
 def after_write(self,callback,files=None):
  real_open=d.os.open;real_write=d.os.write;opened={};state=[]
  def track(path,flags,*args,**kwargs):
   fd=real_open(path,flags,*args,**kwargs)
   if flags&os.O_WRONLY:opened[fd]=str(path)
   return fd
  def mutate(fd,raw):
   count=real_write(fd,raw)
   if opened.get(fd)=='LICENSE' and not state:state.append(True);callback()
   return count
  with mock.patch.object(d.os,'open',side_effect=track),mock.patch.object(d.os,'write',side_effect=mutate):d.copy_bytes(files or self.files,self.target)
 def test_complete_bytes_nested_paths_empty_file_and_readonly_inputs(self):
  files={**self.files,'hardware/empty':b''};before=copy.deepcopy(files);d.copy_bytes(files,self.target)
  self.assertEqual(d.inventory(self.target),d.hashes(files));self.assertEqual(files,before)
  for name,raw in files.items():self.assertEqual((self.target/name).read_bytes(),raw)
 def test_canonical_key_types_aliases_and_prefix_collision_reject_before_mkdir(self):
  invalid=[{'../outside':b'x'},{'/absolute':b'x'},{'a//b':b'x'},{'./a':b'x'},{'a/':b'x'},{'a/./b':b'x'},{'a\\b':b'x'},{'a\n':b'x'},{'e\u0301':b'x'},{'A':b'x','a':b'y'},{'A/x':b'x','a/y':b'y'},{'a':b'x','a/b':b'y'},{'a':bytearray(b'x')},{True:b'x'}]
  for files in invalid:
   with self.subTest(files=files),self.assertRaises(d.p.Rejected):d.copy_bytes(files,self.target)
   self.assertFalse(self.target.exists())
 def test_existing_target_is_never_adopted_or_modified(self):
  self.target.mkdir();owner=self.target/'owner';owner.write_bytes(b'other owner')
  with self.assertRaises(FileExistsError):d.copy_bytes(self.files,self.target)
  self.assertEqual(list(self.target.iterdir()),[owner]);self.assertEqual(owner.read_bytes(),b'other owner')
 def test_root_replacement_after_license_cannot_overwrite_new_owner_pcb(self):
  moved=self.root/'retained-original';owner=b'other owner pcb'
  def replace():
   self.target.rename(moved);self.target.mkdir();(self.target/'hardware').mkdir();(self.target/'hardware/board.kicad_pcb').write_bytes(owner)
  with self.assertRaises(d.p.Rejected):self.after_write(replace)
  self.assertEqual((self.target/'hardware/board.kicad_pcb').read_bytes(),owner);self.assertFalse((self.target/'README.md').exists());self.assertEqual((moved/'LICENSE').read_bytes(),self.files['LICENSE'])
 def test_foreign_nested_directory_after_root_license_is_not_adopted(self):
  owner=b'foreign nested pcb'
  def replace():
   (self.target/'hardware').mkdir();(self.target/'hardware/board.kicad_pcb').write_bytes(owner)
  with self.assertRaises(FileExistsError):self.after_write(replace)
  self.assertEqual((self.target/'hardware/board.kicad_pcb').read_bytes(),owner);self.assertEqual((self.target/'LICENSE').read_bytes(),self.files['LICENSE'])
 def test_created_nested_directory_replacement_rejected_before_other_owner_write(self):
  moved=self.root/'retained-hardware';owner=b'foreign nested pcb'
  files={'hardware/LICENSE':b'notice','hardware/board.kicad_pcb':b'our pcb'}
  def replace():
   (self.target/'hardware').rename(moved);(self.target/'hardware').mkdir();(self.target/'hardware/board.kicad_pcb').write_bytes(owner)
  with self.assertRaises(d.p.Rejected):self.after_write(replace,files)
  self.assertEqual((self.target/'hardware/board.kicad_pcb').read_bytes(),owner);self.assertEqual((moved/'LICENSE').read_bytes(),b'notice')
 def test_replacement_between_guard_and_open_cannot_redirect_descriptor(self):
  moved=self.root/'retained-hardware';owner=b'foreign nested pcb';real=d.os.open;state=[]
  def replace(path,flags,*args,**kwargs):
   if str(path)=='board.kicad_pcb' and flags&os.O_WRONLY and not state:
    state.append(True);(self.target/'hardware').rename(moved);(self.target/'hardware').mkdir();(self.target/'hardware/board.kicad_pcb').write_bytes(owner)
   return real(path,flags,*args,**kwargs)
  with mock.patch.object(d.os,'open',side_effect=replace),self.assertRaises(d.p.Rejected):d.copy_bytes(self.files,self.target)
  self.assertEqual((self.target/'hardware/board.kicad_pcb').read_bytes(),owner);self.assertTrue((moved/'board.kicad_pcb').exists());self.assertEqual((moved/'board.kicad_pcb').read_bytes(),b'')
 def test_existing_final_file_or_symlink_after_notice_never_overwritten(self):
  owner=self.root/'owner-pcb';owner.write_bytes(b'owner')
  for link in (False,True):
   target=self.root/('packet-link' if link else 'packet-file');real=d.os.open;state=[]
   def collide(path,flags,*args,**kwargs):
    if str(path)=='board.kicad_pcb' and flags&os.O_WRONLY and not state:
     state.append(True)
     if link:(target/'hardware/board.kicad_pcb').symlink_to(owner)
     else:(target/'hardware/board.kicad_pcb').write_bytes(b'other owner')
    return real(path,flags,*args,**kwargs)
   with self.subTest(link=link),mock.patch.object(d.os,'open',side_effect=collide),self.assertRaises(FileExistsError):d.copy_bytes(self.files,target)
   self.assertEqual(owner.read_bytes(),b'owner')
   if not link:self.assertEqual((target/'hardware/board.kicad_pcb').read_bytes(),b'other owner')
 def test_symlink_ancestor_or_new_nested_symlink_rejected_without_target_read(self):
  other=self.root/'other';other.mkdir();link=self.root/'link';link.symlink_to(other,target_is_directory=True)
  with self.assertRaises(d.p.Rejected):d.copy_bytes(self.files,link/'packet')
  self.assertFalse((other/'packet').exists())
  def replace():(self.target/'hardware').symlink_to(other,target_is_directory=True)
  with self.assertRaises(FileExistsError):self.after_write(replace)
  self.assertEqual(list(other.iterdir()),[])
 def test_extra_empty_directory_cannot_pass_exact_inventory(self):
  real=d.io.inventory
  def extra(directory,*args,**kwargs):
   (self.target/'unexpected').mkdir();return real(directory,*args,**kwargs)
  with mock.patch.object(d.io,'inventory',side_effect=extra),self.assertRaises(d.p.Rejected):d.copy_bytes(self.files,self.target)
  self.assertTrue((self.target/'unexpected').is_dir());self.assertEqual((self.target/'LICENSE').read_bytes(),self.files['LICENSE'])
 def test_all_opened_descriptors_closed_on_nested_replacement(self):
  real=d.os.open;opened=[];moved=self.root/'retained-original'
  def track(*args,**kwargs):
   fd=real(*args,**kwargs);opened.append(fd);return fd
  def replace():self.target.rename(moved);self.target.mkdir()
  with mock.patch.object(d.os,'open',side_effect=track),self.assertRaises(d.p.Rejected):self.after_write(replace)
  for fd in set(opened):
   with self.subTest(fd=fd),self.assertRaises(OSError):os.fstat(fd)
 def test_late_file_tamper_extra_directory_and_write_failure_preserve_partials(self):
  real=d.io.inventory
  def tamper(directory,*args,**kwargs):
   (self.target/'LICENSE').write_bytes(b'changed');return real(directory,*args,**kwargs)
  with mock.patch.object(d.io,'inventory',side_effect=tamper),self.assertRaises(d.p.Rejected):d.copy_bytes(self.files,self.target)
  self.assertTrue((self.target/'hardware/board.kicad_pcb').exists())
  target=self.root/'failed';real_write=d.os.write;count=[0]
  def fail(fd,raw):
   count[0]+=1
   if count[0]==2:raise OSError('deliberate write failure')
   return real_write(fd,raw)
  with mock.patch.object(d.os,'write',side_effect=fail),self.assertRaisesRegex(OSError,'deliberate'):d.copy_bytes(self.files,target)
  self.assertEqual((target/'LICENSE').read_bytes(),self.files['LICENSE']);self.assertTrue((target/'README.md').exists());self.assertFalse((target/'hardware').exists())
if __name__=='__main__':unittest.main()
