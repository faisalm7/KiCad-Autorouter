"""Real-file stage boundary falsifiers; native methods mocked, no process launch."""
import ast,copy,importlib.util,json,shutil,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
from experiments.pic_mixed_transport_probe_v1 import driver,routing_native,routing_checks
from experiments.pic_mixed_transport_probe_v1.test_routing import RoutingChecks
spec=importlib.util.spec_from_file_location('lifecycle',Path(__file__).with_name('reproduce_lifecycle_v2.py'));life=importlib.util.module_from_spec(spec);spec.loader.exec_module(life)
CLEAN={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'findings':[],'ignored_checks':[]}

def run(out,mutate):
 out.mkdir();source_dir=out/'source';source_dir.mkdir();source=source_dir/driver.original.SOURCE.name
 shutil.copyfile(driver.original.SOURCE,source);shutil.copyfile(driver.original.SOURCE.with_suffix('.kicad_pro'),source.with_suffix('.kicad_pro'))
 hashes=p.tree_hash(source_dir);(out/'raw.ses').write_text('MOCK ONLY; never imported')
 cb=life.callbacks(Path(driver.__file__),out);cb['capture']();record={};armed=False;mutated=False;stages=[];validation_hash=None
 def alter(board):
  nonlocal mutated
  tree=sx.read(board);tree.append(['segment',['start','100','100'],['end','101','100'],['width','0.8'],['layer','"F.Cu"'],['net','"VCC"']]);sx.write(board,tree);mutated=True
 def capture():
  nonlocal armed
  candidate=out/'routing-native/candidate'/source.name
  if armed and mutate=='seal' and not cb['mutable_files']:
   alter(candidate);armed=False
  cb['capture']()
 class Job:
  def __init__(self,path,*args):self.out=path;path.mkdir();self.steps=[]
  def native(self,name,action,*args):
   cb['stable']();stages.append(name)
   if action=='import':shutil.copyfile(args[0],args[1])
   elif action=='metrics':
    if mutate=='metrics':alter(args[0])
    args[1].write_text('{}')
   else:raise AssertionError(action)
  def drc(self,*args,**kwargs):cb['stable']();return copy.deepcopy(CLEAN)
 def validate(job,original,candidate,source_hashes,protected):
  nonlocal armed,validation_hash
  # Return a true exact candidate digest and reports from a mocked stage.
  p.verify_candidate_files(candidate,source_hashes);validation_hash=p.sha(candidate)
  (job.out/'final-drc.json').write_text('{}');(job.out/'final-drc-binding.json').write_text('{}');armed=True
  return validation_hash,copy.deepcopy(CLEAN)
 error=None;result=None
 with patch.object(routing_native.ses_native,'SesJob',Job),patch.object(p,'validate_candidate',validate):
  try:result=routing_native.execute(out,source,{}, {'generated_engine_to_ses_exact':True},lambda:180,None,{},capture,record,lambda path:driver.pending_candidate(out,path,cb['frozen'],cb['mutable_files'],capture))
  except Exception as exc:error=type(exc).__name__+': '+str(exc)
 candidate=out/'routing-native/candidate'/source.name
 return {'mutation':mutate,'mutated':mutated,'stages':stages,'error':error,'returned':result is not None,
  'candidate_sealed':str(candidate.relative_to(out)) in cb['frozen'],'digest_matches_validation':p.sha(candidate)==validation_hash,
  'source_unchanged':p.tree_hash(source_dir)==hashes}

def cancellation():
 tree=ast.parse(Path(driver.__file__).read_text());gate=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and any(isinstance(v,ast.Constant) and v.value=='observed cancellation mode differs from requested action' for v in ast.walk(n)))
 code=compile(ast.fix_missing_locations(ast.Module(body=[gate],type_ignores=[])),str(driver.__file__),'exec')
 RoutingChecks.setUpClass();case=RoutingChecks();results=[]
 for requested in (False,True):
  for reported in (False,True):
   observed,expected=case.synthetic();observed['cancel_before_routing']=reported;observed['routing']['stop_requested']=reported
   valid=routing_checks.compare(observed,expected,case.retained)['lifecycle_verified'];error=None
   try:exec(code,{'observed':observed,'cancel_routing':requested})
   except ValueError as exc:error=str(exc)
   results.append({'requested':requested,'observed':reported,'independent_observation_valid':valid,'error':error})
 return results

def main():
 out=Path(sys.argv[1]).resolve();out.mkdir();pins={str(Path(m.__file__).relative_to(ROOT)):p.sha(Path(m.__file__)) for m in (driver,routing_native,routing_checks)}
 result={'schema':1,'native_executed':False,'jvm_executed':False,'scope':'Mock-native stages with real complete candidate bytes; no routing/DRC qualification','source_pins':pins,
 'candidate_boundaries':[run(out/mode,mode) for mode in ('none','seal','metrics')],'cancel_mode':cancellation()}
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 assert result['candidate_boundaries'][0]['returned'] is True
 assert all(r['mutated'] and not r['returned'] and 'candidate project/rules/file set changed' in r['error'] for r in result['candidate_boundaries'][1:])
 assert all(r['source_unchanged'] and r['candidate_sealed'] for r in result['candidate_boundaries'])
 assert all((r['requested']==r['observed'])==(r['error'] is None) for r in result['cancel_mode'])
 result['source_unchanged']=all(p.sha(ROOT/name)==digest for name,digest in pins.items());assert result['source_unchanged']
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
