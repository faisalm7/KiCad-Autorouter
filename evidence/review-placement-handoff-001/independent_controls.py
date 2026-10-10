"""Independent real-file proposed-handoff lifecycle suite; no native, engine or GUI."""
from pathlib import Path
import importlib.util,json,os,signal,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
module=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('autorouter.independent_review_handoff',module);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def case(name):
 base=out/name;base.mkdir();source=base/'source';candidate=base/'run/candidate';source.mkdir();candidate.mkdir(parents=True);target=base/'review'
 for folder in (source,candidate):
  (folder/'board.kicad_pcb').write_text('(kicad_pcb)\n');(folder/'board.kicad_pro').write_text('{"original":true}\n');(folder/'board.kicad_dru').write_text('(version 1)\n')
 receipt=candidate.parent/'result.json';digest=p.sha(candidate/'board.kicad_pcb');data={'schema':1,'source':str(source/'board.kicad_pcb'),'candidate':str(candidate/'board.kicad_pcb'),'candidate_sha256':digest};receipt.write_text(json.dumps(data))
 verified={'current':True,'applied':False,'candidate':str(candidate/'board.kicad_pcb'),'candidate_sha256':digest};calls=0;runtime_calls=0;fired=False;cpu_now=[0.0];wall_now=[0.0];original_save=h.save_json;original_runtime=h.runtime_inventory
 before_handlers={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
 def check(_):
  nonlocal calls,fired
  calls+=1;v=dict(verified)
  if calls==2 and name in ('copied_project_second','copied_rules_second'):
   file='board.kicad_pro' if name=='copied_project_second' else 'board.kicad_dru';(target/'project'/file).write_text('modified copied rule');fired=True
  if calls==3 and name=='source_third':(source/'board.kicad_pro').write_text('modified original');fired=True
  if calls==3 and name=='evidence_third':(candidate.parent/'unexpected.json').write_text('{}');fired=True
  if calls==3 and name=='wrong_policy_third':v['input_policy']='placement-clearance-v1';fired=True
  return v
 def runtime():
  nonlocal runtime_calls,fired
  runtime_calls+=1;v=original_runtime()
  if runtime_calls==9 and name=='canonical_final_material':
   file=target/'review.json';value=json.loads(file.read_text());value['candidate_sha256']='0'*64;file.write_text(json.dumps(value));fired=True
  return v
 def save(path,record):
  nonlocal fired
  if name=='corrective_failure' and fired:
   original_save(path.with_name(path.name+'.partial'),record);raise OSError('injected corrective write failure')
  original_save(path,record)
  if record.get('status')!='ready_for_manual_review' or fired:return
  if name=='source_after_write':(source/'board.kicad_pro').write_text('modified original');fired=True
  elif name=='copy_after_write':(target/'project/board.kicad_pcb').write_text('modified copy');fired=True
  elif name=='canonical_after_write':
   bad=dict(record);bad['candidate_sha256']='0'*64;Path(path).write_text(json.dumps(bad));fired=True
  elif name=='returned_record_after_write':record['candidate_sha256']='0'*64;fired=True
  elif name in ('interrupt_after_write','corrective_failure'):fired=True;raise KeyboardInterrupt
  elif name in ('SIGINT_after_write','SIGTERM_after_write'):fired=True;os.kill(os.getpid(),getattr(signal,name.split('_')[0]))
  elif name=='cpu_after_write':fired=True;cpu_now[0]=31
  elif name=='wall_after_write':fired=True;wall_now[0]=31
 contexts=[patch.object(h,'check_result',check),patch.object(h,'save_json',save),patch.object(h,'runtime_inventory',runtime)]
 if name=='cpu_after_write':contexts.append(patch.object(h,'cpu_seconds',side_effect=lambda:cpu_now[0]))
 if name=='wall_after_write':contexts.append(patch.object(h.time,'monotonic',side_effect=lambda:wall_now[0]))
 from contextlib import ExitStack
 with ExitStack() as stack:
  for ctx in contexts:stack.enter_context(ctx)
  try:returned=h.review_copy(receipt,target);error=None
  except BaseException as exc:returned=None;error=type(exc).__name__+': '+str(exc)
 path=target/'review.json';canonical=json.loads(path.read_text()) if path.exists() else None
 good=(canonical is not None and canonical.get('status')=='ready_for_manual_review')
 result={'case':name,'triggered':fired,'check_calls':calls,'runtime_calls':runtime_calls,'raised':error,'canonical_ready':good,'canonical_status':canonical.get('status') if canonical else None,'return_matches_canonical':returned==canonical,'handlers_restored':{s:signal.getsignal(s) for s in before_handlers}==before_handlers,'archived_ready_or_partial':len(list(target.glob('invalidated-review-*'))) if target.exists() else 0,'source_and_run_are_synthetic':True,'central_validation_mocked':True,'native_jobs':0,'engine_jobs':0}
 if name=='unchanged':result['passed']=good and returned==canonical and p.tree_hash(target/'project')==p.tree_hash(candidate) and error is None
 else:result['passed']=fired and not good and error is not None
 result['passed'] = result['passed'] and result['handlers_restored']
 (base/'outcome.json').write_text(json.dumps(result,indent=2)+'\n');return result
names=['unchanged','copied_project_second','copied_rules_second','source_third','evidence_third','wrong_policy_third','source_after_write','copy_after_write','canonical_after_write','returned_record_after_write','interrupt_after_write','SIGINT_after_write','SIGTERM_after_write','corrective_failure','cpu_after_write','wall_after_write','canonical_final_material']
rows=[case(name) for name in names];result={'schema':1,'module':str(module),'module_sha256':p.sha(module),'case_count':len(rows),'passed':all(r['passed'] for r in rows),'cases':rows,'scope':'Tiny real filesystem mutation and real self-signal controls, mocked central validator; no native evidence claim.'}
(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'module_sha256':result['module_sha256'],'cases':len(rows),'failed':[r['case'] for r in rows if not r['passed']]},indent=2));raise SystemExit(0 if result['passed'] else 1)
