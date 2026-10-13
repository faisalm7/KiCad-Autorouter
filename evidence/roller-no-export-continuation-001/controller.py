"""Only unfinished native observations; previous owned controls stay exact."""
from pathlib import Path
import json,sys,time,shutil,fcntl
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx,config as c
start=time.monotonic();cpu=time.process_time()+f.child_cpu();out=ROOT/'.runs/roller-no-export-continuation-001';out.mkdir()
old=ROOT/'.runs/roller-semantics-native-001';oldbefore=pc.inventory(old,with_directories=True);previous=f.read_json(ROOT/'.runs/roller-semantics-native-001-execution/execution.json')
protocol=ROOT/'.runs/roller-no-export-continuation-draft-001/PROTOCOL.json';tools=p.tool_manifest();worker=ROOT/'experiments/roller_support_v1/observe_only.py';budget=30.;remaining=lambda:max(0,min(budget-(time.monotonic()-start),budget-(time.process_time()+f.child_cpu()-cpu)))
p.save_json(out/'protocol.json',{'tools':tools,'controller_sha256':p.sha(Path(__file__)),'draft_protocol_sha256':p.sha(protocol),'worker_sha256':p.sha(worker),'previous_inventory':oldbefore,'previous_whole_execution':previous,'cases':['original','active_5mil'],'optional_original_only_new_stages':['refill','no-export-reload','final-parity'],'no_original_reference_or_class_rewriting':True,'previous_three_owned_native_cases_repeated':False,'native_executed_before_pin':False})
job=f.FloorJob(out/'job',budget,remaining);record={'schema':1,'status':'failed','controls_passed':False,'accepted':False,'production_support_qualified':False,'new_engine_execution':False,'cases':[],'previous_owned_cases_repeated':False,'tools':tools}
try:
 with (ROOT/'.runs/quality-experiment.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for name in ('original','active_5mil'):
   base=out/name;base.mkdir();shutil.copytree(old/name/'observe-input',base/'input');board=base/'input/SparkFun_Roller_Encoder_Breakout.kicad_pcb';before=p.tree_hash(board.parent)
   context=base/'context.json';diag=base/'diagnostic.json';job.step(name,[c.PYTHON,worker,board,context,diag]);ctx=f.read_json(context);d=f.read_json(diag)
   f.context_binding(ctx,board,before,'final');assert d['dsn_sha256'] is None and d['input_hashes_before']==before and d['input_hashes_after']==before and d['floor_context_sha256']==p.sha(context)
   native=d['observation_before_export'];assert native==d['observation_after_export'] and all(r['pad_count']==0 for g in native['duplicate_reference_groups'] for r in g['footprints'])
   nets={r['name']:r for r in ctx['nets']};assert set(nets)=={'A','B','GND','SWITCH'}
   assert all(r['class']==('5mil' if name=='active_5mil' and n=='A' else 'Default') for n,r in nets.items())
   assert nets['A']['width_nm']==(127000 if name=='active_5mil' else 152400)
   record['cases'].append({'case':name,'control_passed':True,'source_hashes':before,'context_sha256':p.sha(context),'diagnostic_sha256':p.sha(diag),'native_netclasses':ctx['nets'],'duplicate_reference_groups':native['duplicate_reference_groups'],'native_layers':native['layers'],'copper_text_uuids':[r['uuid'] for r in native['copper_text']],'routing_accepted':False,'dsn_exported':False})
  # New original stages were never reached in001. Savingrefill then native reload;
  # only derived fill is transplanted to the untouched original shell.
  original=out/'original/input/SparkFun_Roller_Encoder_Breakout.kicad_pcb';saved=out/'original/saved';shutil.copytree(original.parent,saved);savedboard=saved/original.name;before=p.tree_hash(saved)
  native=job.drc('original-refill',savedboard,save=True);f.check_drc_stage(job.out,{'steps':job.steps},'original-refill',savedboard,savedboard,True,before)
  job.step('original-reload',[c.PYTHON,worker,savedboard,out/'original/reload-context.json',out/'original/reload-diagnostic.json'])
  candidate=out/'original/candidate';shutil.copytree(original.parent,candidate);candidate=candidate/original.name;sx.write(candidate,p.transplant_fill(sx.read(original),sx.read(savedboard)))
  assert p.immutable(sx.read(candidate))==p.immutable(sx.read(original)) and p.routes(sx.read(candidate))==p.routes(sx.read(original));p.verify_candidate_files(candidate,p.tree_hash(original.parent))
  try:
   final=job.drc('original-final',candidate,schematic_parity=True)
   record.update(original_native=final,original_candidate_sha256=p.sha(candidate),original_native_report_sha256=p.sha(job.out/'original-final.json'),original_native_rejection_reasons=p.native_rejection_reasons(final))
  except p.Rejected as exc:
   record.update(original_final_rejection=str(exc),original_native=p.parse_report(job.out/'original-final.json',original.name),original_candidate_sha256=p.sha(candidate),original_native_report_sha256=p.sha(job.out/'original-final.json'))
  assert pc.inventory(old,with_directories=True)==oldbefore and tools==p.tool_manifest()
  record.update(status='observations_complete_original_export_still_failed',controls_passed=True)
except (Exception,KeyboardInterrupt) as exc:record.update(status='failed',reason=type(exc).__name__+': '+str(exc),controls_passed=False)
record.update(wall_seconds=time.monotonic()-start,full_cpu_seconds=time.process_time()+f.child_cpu()-cpu,steps=job.steps)
record['combined_active_wall_seconds']=previous['wall_seconds']+record['wall_seconds'];record['combined_full_cpu_seconds']=previous['full_cpu_seconds']+record['full_cpu_seconds'];record['calendar_gap_disclosed']=True
record['within_new30_wall_full_cpu']=max(record['wall_seconds'],record['full_cpu_seconds'])<30
if not record['within_new30_wall_full_cpu']:record.update(controls_passed=False,status='budget_exceeded')
p.save_json(out/'result.json',record);print(json.dumps({k:record.get(k) for k in ('status','controls_passed','reason','original_final_rejection','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['controls_passed'] else 2)
