"""Independent mocked-stage wrapper controls; no native or routing claims."""
import copy,json,os,signal,sys,tempfile,unittest,types
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import recovery as r,pipeline as p,sexpr as sx
NATIVE={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':[]}

class Harness:
 def __init__(self,base,mode='normal'):
  self.base=Path(base).resolve();self.mode=mode;self.clock=1000.;self.parent=10.;self.child=20.;self.save_count=0;self.validation_calls=0;self.changed=False;self.budgets=[]
  self.source=self.base/'source'/'board.kicad_pcb';self.source.parent.mkdir(parents=True)
  self.source.write_text('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (31 "B.Cu" signal)))\n');self.source.with_suffix('.kicad_pro').write_text('{}\n');self.out=self.base/'run'
  self.manifest={'implementation_sha256':{'autorouter/__init__.py':p.sha(ROOT/'autorouter/__init__.py')},'git_head':'frozen'}
 def step(self,name,cpu,wall):return {'name':name,'cpu_seconds':cpu,'wall_seconds':wall,'monitor_cpu_seconds':0.,'status':'success','cleanup_complete':True}
 def advance(self,parent=0,child=0,wall=0):self.parent+=parent;self.child+=child;self.clock+=wall
 def baseline(self,source,out,seconds,*args):
  self.budgets.append(seconds);out=Path(out);out.mkdir();candidate=out/'candidate'/Path(source).name;candidate.parent.mkdir();candidate.write_bytes(self.source.read_bytes());candidate.with_suffix('.kicad_pro').write_bytes(self.source.with_suffix('.kicad_pro').read_bytes())
  self.advance(parent=3,child=10,wall=15)
  result={'status':'routing_accepted','accepted':True,'candidate':str(candidate),'candidate_sha256':p.sha(candidate),'steps':[self.step('engine',10,10)],'native':copy.deepcopy(NATIVE),'parent_cpu_seconds':999,'child_cpu_seconds':999,'total_cpu_seconds':1998}
  if self.mode=='metadata_cpu':self.advance(child=2)
  if self.mode.startswith('repair_'):result.update(status='drc_rejected',accepted=False)
  if self.mode=='missing_candidate':result.update(status='drc_rejected',accepted=False);result.pop('candidate')
  if self.mode=='missing_receipt':return result
  if self.mode=='source_stale':self.source.with_suffix('.kicad_pro').write_text('{"changed":true}\n')
  if self.mode=='code_stale':self.changed=True
  if self.mode=='cancelled_incumbent':result['steps'][0]['status']='cancelled'
  if self.mode=='incomplete_cleanup':result['steps'][0]['cleanup_complete']=False
  (out/'result.json').write_text(json.dumps(result));return result
 def validate(self,job,original,candidate,hashes,protected):
  self.validation_calls+=1;self.advance(parent=1,child=5,wall=2);job.steps.append(self.step('final-drc',5,2));(job.out/'final-drc.json').write_text('{}\n')
  if self.mode=='hash_change':candidate.write_text(candidate.read_text()+'\n')
  return p.sha(candidate),copy.deepcopy(NATIVE)
 def native(self,job,name,action,board,output,*args):
  self.advance(parent=.2,child=1,wall=1);job.steps.append(self.step('metrics',1,1));Path(output).write_text('{"version":"10.0.0","vias":0,"track_length_mm":0}\n')
 def check(self,path):
  if self.mode=='invalid_incumbent' and Path(path).parent.name=='incumbent':raise p.Rejected('synthetic invalid incumbent')
  return {'current':True}
 def run(self):
  owner=self;real_job=p.Job;real_save=p.save_json
  thermal=types.ModuleType('autorouter.thermal')
  def repair(job,original,candidate,hashes,protected,native,**kwargs):
   if owner.mode=='repair_false':return {'validation_passed':False,'status':'unsupported'}
   target=Path(kwargs['out'])/'candidate'/candidate.name;target.parent.mkdir(parents=True)
   target.write_bytes(candidate.read_bytes());target.with_suffix('.kicad_pro').write_bytes(candidate.with_suffix('.kicad_pro').read_bytes())
   owner.advance(parent=2,child=4,wall=3);job.steps.append(owner.step('repair-native',4,3))
   return {'validation_passed':True,'candidate':str(target),'candidate_sha256':'0'*64 if owner.mode=='repair_wrong_hash' else p.sha(target)}
  thermal.attempt_repair=repair
  class FakeJob(real_job):
   def native(self,*args):return owner.native(self,*args)
  def manifest():return {**owner.manifest,'git_head':'changed' if owner.changed else 'frozen'}
  def save(path,value):
   if Path(path)==owner.out/'result.json' and owner.mode=='publish_correction_failure' and owner.save_count==2:
    raise OSError('synthetic disk failure during cancelled receipt rewrite')
   real_save(path,value)
   if Path(path)==owner.out/'result.json':
    owner.save_count+=1
    if owner.save_count==2 and value.get('accepted'):
     if owner.mode in ('publish_interrupt','publish_correction_failure'):raise KeyboardInterrupt
     if owner.mode=='publish_sigterm':os.kill(os.getpid(),signal.SIGTERM)
     if owner.mode=='publish_source_stale':owner.source.with_suffix('.kicad_pro').write_text('{"changed":true}\n')
     if owner.mode=='publish_code_stale':owner.changed=True
     if owner.mode=='publish_cpu_cap':owner.advance(parent=121)
     if owner.mode=='publish_wall_cap':owner.advance(wall=121)
  with patch.dict(sys.modules,{'autorouter.thermal':thermal}),patch.object(r.time,'monotonic',lambda:owner.clock),patch.object(r.time,'process_time',lambda:owner.parent),patch.object(r,'child_cpu',lambda:owner.child),patch.object(p,'Job',FakeJob),patch.object(p,'tool_manifest',manifest),patch.object(p,'check_storage',lambda:None),patch.object(p,'preflight',lambda path:sx.read(path)),patch.object(p,'route',owner.baseline),patch.object(p,'validate_candidate',owner.validate),patch.object(p,'check_result',owner.check),patch.object(p,'save_json',save):
   return r.recover(owner.source,owner.out,120)

class Controls(unittest.TestCase):
 def exercise(self,mode):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
   h=Harness(folder,mode);result=h.run();stored=json.loads((h.out/'result.json').read_text());return result,stored,h.validation_calls,h.budgets
 def test_cpu_not_double_counted(self):
  a,b,c,budgets=self.exercise('normal');self.assertTrue(a['accepted']);self.assertAlmostEqual(a['total_cpu_seconds'],20.2);self.assertAlmostEqual(a['parent_cpu_seconds'],4.2);self.assertEqual(a['child_cpu_seconds'],16);self.assertEqual(a['control_child_cpu_seconds'],0);self.assertEqual(budgets,[80.]);self.assertEqual(c,1)
 def test_metadata_child_cpu_included(self):
  a,b,c,_=self.exercise('metadata_cpu');self.assertTrue(a['accepted']);self.assertEqual(a['control_child_cpu_seconds'],2);self.assertAlmostEqual(a['total_cpu_seconds'],22.2)
 def test_shared_repair_steps_counted_once(self):
  a,b,c,_=self.exercise('repair_positive');self.assertTrue(a['accepted']);self.assertAlmostEqual(a['total_cpu_seconds'],26.2);self.assertEqual(a['child_cpu_seconds'],20);self.assertEqual(len([x for x in a['steps'] if x['name']=='repair-native']),1)
 def test_invalid_repair_or_wrong_hash_rejected(self):
  for mode in ('repair_false','repair_wrong_hash'):
   a,b,c,_=self.exercise(mode);self.assertFalse(b['accepted']);self.assertEqual(c,0)
 def test_missing_or_invalid_incumbent(self):
  for mode in ('missing_candidate','missing_receipt','invalid_incumbent'):
   with self.subTest(mode=mode):
    a,b,c,_=self.exercise(mode);self.assertFalse(b['accepted']);self.assertEqual(c,0)
 def test_cancel_or_incomplete_incumbent(self):
  for mode in ('cancelled_incumbent','incomplete_cleanup'):
   a,b,c,_=self.exercise(mode);self.assertFalse(b['accepted']);self.assertEqual(c,0)
 def test_candidate_hash_must_remain_exact(self):
  a,b,c,_=self.exercise('hash_change');self.assertFalse(b['accepted']);self.assertIn('differs from validated selection',b['reason'])
 def test_source_and_code_freeze(self):
  for mode in ('source_stale','code_stale'):
   a,b,c,_=self.exercise(mode);self.assertFalse(b['accepted']);self.assertEqual(c,0)
 def test_keyboard_interrupt_after_final_publish(self):
  a,b,c,_=self.exercise('publish_interrupt');self.assertFalse(b['accepted']);self.assertEqual(b['status'],'cancelled')
 def test_source_and_code_changes_during_publication(self):
  for mode in ('publish_source_stale','publish_code_stale'):
   a,b,c,_=self.exercise(mode);self.assertFalse(b['accepted']);self.assertEqual(b['status'],'invalidated')
 def test_signal_handlers_restored(self):
  before={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
  self.exercise('normal')
  self.assertEqual(before,{s:signal.getsignal(s) for s in before})
 def test_failed_cancelled_rewrite_cannot_leave_canonical_accepted(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
   h=Harness(folder,'publish_correction_failure')
   with self.assertRaises(OSError):h.run()
   self.assertFalse((h.out/'result.json').exists())
   self.assertTrue(list(h.out.glob('invalidated-result-*.json')))
 def test_cpu_and_wall_overrun_after_publish(self):
  for mode in ('publish_cpu_cap','publish_wall_cap'):
   a,b,c,_=self.exercise(mode);self.assertFalse(b['accepted']);self.assertEqual(b['status'],'budget_exceeded')

if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1]=='--sigterm-repro':
  base=Path(sys.argv[2]);base.mkdir(exist_ok=False);Harness(base,'publish_sigterm').run()
 else:unittest.main()
