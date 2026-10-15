"""Targeted actual-reader closure/real Mac PRL metadata regressions; no Native execution."""
from pathlib import Path
import ast,hashlib,json,os,stat,sys,tempfile,types,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,local_settings as ls,config as c
READER=Path(__file__).parent/'.runs/read-universal-shift-interface-native-paired300-002.py'
class LateWitnesses(unittest.TestCase):
 def test_fixed_hashes_and_actual_prl_metadata(self):
  tree=ast.parse(READER.read_text());audit=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='audit')
  stable=next(n for n in audit.body if isinstance(n,ast.FunctionDef) and n.name=='stable')
  module=ast.fix_missing_locations(ast.Module(body=[stable],type_ignores=[]))
  with tempfile.TemporaryDirectory(prefix='late-witness-',dir=Path(__file__).parent) as tmp:
   root=Path(tmp);base=root/'base';base.mkdir();out=root/'out';out.mkdir();cwd=base/'arm';cwd.mkdir();inp=cwd/'input';inp.mkdir();board=inp/'x.kicad_pcb';board.write_text('fixture')
   prl=board.with_suffix('.kicad_prl');prl.write_text('{"unchanged":true}\n');reader=base/'reader.py';reader.write_text('fixture')
   binding=dict(input=str(board),saved=False,before={prl.name:p.sha(prl)},local_settings_policy=ls.JOB_POLICY)
   process=dict(argv=[str(c.CLI),'pcb','drc',str(board)],status='success',exit_code=0,cleanup_complete=True,local_settings_policy=ls.JOB_POLICY,
    local_settings_protection=dict(policy=ls.POLICY,present=True,path=str(prl),sha256=p.sha(prl),flags_before=0,flags_during=stat.UF_IMMUTABLE,flags_restored=True,bytes_unchanged=True))
   p.save_json(cwd/'final-drc-binding.json',binding);p.save_json(cwd/'final-drc-process.json',process)
   p.save_json(out/'result.json',dict(status='completed'));p.save_json(out/'execution.json',dict(result_sha256=p.sha(out/'result.json')))
   changes=[lambda:None]
   def manifest():changes[0]();return {'fixture':True}
   def require(value,reason):
    if not value:raise p.Rejected(reason)
   ns=dict(p=types.SimpleNamespace(tool_manifest=manifest,sha=p.sha),q=types.SimpleNamespace(verify_freeze=lambda *a:None),
    f=f,c=c,ls=ls,Path=Path,require=require,spec=dict(tools={'fixture':True},complete_source_files_sha256={},reader_sha256=p.sha(reader)),
    protocol={'freeze':{}},board=board,prerequisites=lambda:None,dependencies={},base=base,ROOT=ROOT,h=types.SimpleNamespace(owned_destination=lambda *a:None),owner={},
    result={'workers':[dict(cwd=str(cwd),name='final-drc')]},inventory=lambda *a:{},material={},source_witness={},pins={},remaining=lambda:45,
    output=out,result_pin=p.sha(out/'result.json'),execution_pin=p.sha(out/'execution.json'))
   exec(compile(module,str(READER),'exec'),ns);check=ns['stable'];check()
   originals={n:(out/n).read_bytes() for n in ('result.json','execution.json')}
   for name in originals:
    changes[0]=lambda name=name:(out/name).write_text('{}')
    with self.subTest(mutation=name),self.assertRaises(p.Rejected):check()
    (out/name).write_bytes(originals[name])
   changes[0]=lambda:os.chflags(prl,stat.UF_IMMUTABLE,follow_symlinks=False)
   try:
    with self.assertRaises(p.Rejected):check()
   finally:os.chflags(prl,0,follow_symlinks=False)
   link=inp/'same-byte-hardlink'
   changes[0]=lambda:os.link(prl,link)
   try:
    with self.assertRaises(p.Rejected):check()
   finally:link.unlink()
   changes[0]=lambda:None;check()
 def test_cumulative_account_charges_prior_plus_only_new_work(self):
  tree=ast.parse(READER.read_text());audit=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='audit');account=next(n for n in audit.body if isinstance(n,ast.FunctionDef) and n.name=='account')
  module=ast.fix_missing_locations(ast.Module(body=[account],type_ignores=[]))
  prior=dict(charged_wall_seconds=54.,charged_cpu_seconds=43.)
  row=dict(prior_row=prior,invocation_wall_seconds=10.,invocation_cpu_seconds=10.,raw_paired_accepted=True)
  result=dict(status='completed',results=[row])
  outer=dict(wall_seconds=100.,full_cpu_seconds=90.,source_current=True,clean_checkpoint_before=True,clean_checkpoint_after=True,whole_delivery_within_budget=True)
  summary=dict(status='completed',results=[dict(invocation_wall_seconds=10.,invocation_cpu_seconds=10.) for _ in range(4)])
  ns=dict(result=result,outer=outer,summary=summary,elapsed=lambda:(5.,4.),number=lambda x:x,remaining=lambda:40.,require=lambda value,reason:None if value else (_ for _ in ()).throw(AssertionError(reason)),common_wall=24.7,common_cpu=18.1,PUBLICATION=2.,STARTUP=1.,process=dict(status='success',exit_code=0),paired=types.SimpleNamespace(comparisons=lambda rows:[]))
  exec(compile(module,str(READER),'exec'),ns);ns['account']()
  self.assertAlmostEqual(row['charged_wall_seconds'],158.7);self.assertAlmostEqual(row['charged_cpu_seconds'],130.1)
  self.assertTrue(row['accepted']);self.assertEqual(prior,dict(charged_wall_seconds=54.,charged_cpu_seconds=43.))
 def test_final_failure_clears_delivered_rows(self):
  path=Path(__file__).parent/'.runs/run-universal-shift-interface-native-paired300-readback-001.py';tree=ast.parse(path.read_text())
  tail=[n for n in tree.body if isinstance(n,ast.Try)][-1]
  handler=tail.handlers[0]
  module=ast.fix_missing_locations(ast.Module(body=handler.body,type_ignores=[]))
  record={'passed':True,'final_charged_results':[{'accepted':True,'raw_paired_accepted':True}]}
  ns=dict(record=record,exc=p.Rejected('late callback changed witness'),time=types.SimpleNamespace(monotonic=lambda:46.),START=0.,cpu=lambda:46.,CPU0=0.,p=types.SimpleNamespace(save_json=lambda *a:None),OUT=Path('.'))
  exec(compile(module,str(path),'exec'),ns)
  self.assertFalse(record['passed']);self.assertFalse(record['source_current']);self.assertFalse(record['final_charged_results'][0]['accepted']);self.assertTrue(record['final_charged_results'][0]['raw_paired_accepted'])
 def test_enclosure_final_callback_order(self):
  path=Path(__file__).parent/'.runs/run-universal-shift-interface-native-paired300-readback-001.py';tree=ast.parse(path.read_text())
  stable=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='stable')
  text=ast.unparse(stable)
  self.assertLess(text.index('p.tool_manifest'),text.index('ls.check_event'))
  self.assertLess(text.index('ls.check_event'),text.index('pc.inventory'))
  self.assertIn('execution_pin',text)
if __name__=='__main__':unittest.main(verbosity=2)
