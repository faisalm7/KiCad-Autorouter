"""Prototype qualification through shared production Native audit/export.
Reuses retained saved fill; no repeated refill, routing or support admission.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import copy,fcntl,importlib.util,json,os,runpy,signal,stat,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
DRAFT=ROOT/'.runs/inner-pour-four-layer-draft-002';BASE=ROOT/'.runs/inner-pour-fill-native-001'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
def instrument(native=False):
 import autorouter
 for name in('placement_transform','floor_context','pour_rule_area',*(['pour_rule_area_native']if native else[])):
  module=load('autorouter.'+name,DRAFT/'patch-tree/autorouter'/(name+'.py'));setattr(autorouter,name,module)
if len(sys.argv)>1 and sys.argv[1]=='--native':
 instrument(True);sys.argv=[str(ROOT/'autorouter/native.py'),*sys.argv[2:]];runpy.run_path(sys.argv[0],run_name='__main__');raise SystemExit(0)
from autorouter import pipeline as p,floor_route as f,config as c,handoff as h,placement_clearance as io,sexpr as sx
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as existing
from experiments.placement_handoff_native_v1.driver import copy_bytes
SOURCE=ROOT/'.runs/inner-pour-metadata-native-001/sources/omitted_net_island0'
SAVED=ROOT/'.runs/inner-pour-saved-native-001/execution/worker/omitted_net_island0/saved'
READBACK=ROOT/'.runs/inner-pour-saved-readback-002/result.json'
LIMITS=dict(wall_seconds=60,full_CPU_seconds=60,worker_timeout_seconds=55,aggregate_bytes=32*1024**2,group_RSS_bytes=2*1024**3,log_bytes=256*1024,finalization_reserve_seconds=2)
def draft_files():
 manifest=f.read_json(DRAFT/'manifest.json')
 for name,row in manifest['files'].items():
  if p.sha(DRAFT/name)!=row['sha256']or(DRAFT/name).stat().st_size!=row['bytes']:raise p.Rejected('frozen prototype changed')
 return manifest
def context(plan,pin):
 draft_files()
 if p.sha(DRAFT/'manifest.json')!=plan['draft_manifest_sha256']or p.sha(__file__)!=plan['driver_sha256']or p.tool_manifest()!=plan['tools']or p.sha(BASE/'protocol.json')!=pin:raise p.Rejected('prototype/source/tool context changed')
 if p.tree_hash(SOURCE)!=plan['source_hashes']or p.tree_hash(SAVED)!=plan['saved_hashes']or p.sha(READBACK)!=plan['readback_sha256']:raise p.Rejected('retained native donor/source changed')
def prepare():
 draft_files();prior=f.read_json(READBACK)
 if prior['status']!='diagnostic_readback_complete'or prior['qualified']is not False:raise p.Rejected('diagnostic prerequisite differs')
 BASE.mkdir();plan=dict(schema=1,driver_sha256=p.sha(__file__),draft_manifest_sha256=p.sha(DRAFT/'manifest.json'),tools=p.tool_manifest(),source_hashes=p.tree_hash(SOURCE),saved_hashes=p.tree_hash(SAVED),readback_sha256=p.sha(READBACK),limits=LIMITS,accepted=False,qualified=False,scope='Prototype 002 audit via unchanged production native.py with explicit frozen module instrumentation. Retained actual saved fill transplanted onto original omitted-net source; actual direct matrix audit and injected derived-fill rejection without refill; actual raw Native DSN export and pure exact attribution. No engine/support/final candidate acceptance.',preparation_wall_seconds=time.monotonic()-START,preparation_CPU_seconds=cpu()-CPU0)
 p.save_json(BASE/'protocol.json',plan);print(json.dumps({'prepared':True,'native_executed':False,'protocol_sha256':p.sha(BASE/'protocol.json')}))
def worker(plan,pin):
 context(plan,pin);instrument();from autorouter import pour_rule_area as policy
 out=BASE/'execution/worker';out.mkdir();owner={};h.capture_destination(owner,out);remaining=lambda:min(53-(time.monotonic()-START),53-(cpu()-CPU0));record=dict(schema=1,status='failed',controls_passed=False,qualified=False,accepted=False,protocol_sha256=pin)
 for sig in(signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:(_ for _ in()).throw(KeyboardInterrupt()))
 job=existing.BoundJob(out/'job',remaining(),remaining,protect_local_settings=True)
 try:
  copy_bytes(io.inventory(SOURCE,contents=True),job.out/'original');source=next((job.out/'original').glob('*.kicad_pcb'));original=sx.read(source)
  recipe=load('frozen_inner_pour_fill_recipe',DRAFT/'native_recipe.py').prepare(io.read_bytes(source),io.read_bytes(SAVED/source.name))
  positive=job.out/'positive';copy_bytes(io.inventory(SOURCE,contents=True),positive);board=positive/source.name
  board.write_bytes(recipe['positive']);filled=sx.read(board)
  if p.immutable(filled)!=p.immutable(original)or p.routes(filled)!=p.routes(original):raise p.Rejected('source-preserving fill reconstruction failed')
  positive_before=p.tree_hash(positive);audit=job.out/'positive-audit.json';argv=[c.PYTHON,'-B',Path(__file__),'--native','pour-audit',board,audit]
  job.step('positive-audit',argv);f.process_check(job.out,{'steps':job.steps},'positive-audit',[*f.SANDBOX,*map(str,argv)])
  observed=f.read_json(audit);policy.verify_native_record(observed,board)
  checks=observed['fill_checks']
  if len(checks)!=2 or not any(row['layer']=='In1.Cu'and row['applicable']is False and row['intersection']and row['native_fill_outline_count']>0 for row in checks)or not any(row['layer']=='In2.Cu'and row['applicable']is True and not row['intersection']and row['native_fill_outline_count']>0 for row in checks):raise p.Rejected('nonvacuous complete In1/In2 matrix missing')
  negative=job.out/'negative';copy_bytes(io.inventory(positive,contents=True),negative);bad=negative/source.name;bad.write_bytes(recipe['negative']);bad_tree=sx.read(bad)
  if p.immutable(bad_tree)!=p.immutable(filled)or p.routes(bad_tree)!=p.routes(filled):raise p.Rejected('negative changed nonfill design')
  negative_before=p.tree_hash(negative);bad_audit=job.out/'negative-audit.json';bad_argv=[c.PYTHON,'-B',Path(__file__),'--native','pour-audit',bad,bad_audit]
  job.step('negative-audit',bad_argv,allowed=(1,));f.process_check(job.out,{'steps':job.steps},'negative-audit',[*f.SANDBOX,*map(str,bad_argv)],allowed=(1,))
  rejected=f.read_json(bad_audit)
  if rejected['passed']is not False or not any(row['layer']=='In2.Cu'and row['applicable']is True and row['intersection']and row['passed']is False for row in rejected['fill_checks']):raise p.Rejected('actual In2 intrusion was not rejected')
  try:policy.verify_native_record(rejected,bad)
  except ValueError:pass
  else:raise p.Rejected('negative shared readback accepted')
  dsn=job.out/'native.dsn';mapping=job.out/'native-classes.json';job.native('source-export','export',source,dsn,mapping)
  corrected,attribution=policy.correct(io.read_bytes(source),io.read_bytes(dsn));(job.out/'corrected.dsn').write_bytes(corrected);p.save_json(job.out/'attribution.json',attribution)
  if attribution['removed_count']!=1 or attribution['untargeted_ast_identical']is not True or attribution['removed'][0]['layer']!='In2.Cu':raise p.Rejected('exact source Native DSN attribution failed')
  if p.tree_hash(positive)!=positive_before or p.tree_hash(negative)!=negative_before or p.tree_hash(source.parent)!=plan['source_hashes']:raise p.Rejected('read-only Native operation modified inputs')
  record.update(status='controls_passed',controls_passed=True,source_preserving_transplant=True,recipe=recipe['recipe'],positive=observed,negative=rejected,exact_dsn_attribution=attribution,positive_hashes=positive_before,negative_hashes=negative_before,steps=job.steps)
 except(Exception,KeyboardInterrupt)as exc:record.update(status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',error=type(exc).__name__+': '+str(exc),steps=job.steps)
 witness=existing.material(out);record['completed_evidence']=witness
 def stable():
  h.owned_destination(owner);context(plan,pin)
  if existing.material(out)!=witness:raise p.Rejected('completed prototype controls changed')
 def account():
  record.update(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
  if remaining()<=0:record.update(status='budget_exceeded',controls_passed=False)
 f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
 print(json.dumps({k:record.get(k)for k in('status','controls_passed','error','reason','wall_seconds','full_CPU_seconds')}))
 return 0 if record['status']=='controls_passed'and record['controls_passed']else 2
def execute(plan,pin):
 context(plan,pin);out=BASE/'execution';out.mkdir();fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
 with os.fdopen(fd,'r+')as lock:
  info=os.fstat(lock.fileno())
  if not stat.S_ISREG(info.st_mode)or info.st_nlink!=1:raise p.Rejected('ordinary shared quality lane required')
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',__file__,'--worker',pin],cwd=out,log=out/'command.log',timeout=55,max_log_bytes=LIMITS['log_bytes'],max_workdir_bytes=LIMITS['aggregate_bytes'],max_group_rss_bytes=LIMITS['group_RSS_bytes'])
  child=out/'worker/result.json';data=f.read_json(child)if child.exists()else None;context(plan,pin)
  passed=bool(data and data.get('controls_passed')is True and data.get('status')=='controls_passed'and process['status']=='success'and process['exit_code']==0 and process['cleanup_complete']and not process['log_truncated'])
  record=dict(schema=1,qualified=False,accepted=False,controls_passed=passed,process=process,child_sha256=p.sha(child)if child.exists()else None,protocol_sha256=pin,wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
  if max(record['wall_seconds'],record['full_CPU_seconds'])>60:record['controls_passed']=False
  p.save_json(out/'execution.json',record);print(json.dumps({'controls_passed':record['controls_passed'],'status':process['status'],'exit_code':process['exit_code']}))
  return 0 if record['controls_passed']else 2
if __name__=='__main__':
 if sys.argv[1]=='--prepare':prepare()
 else:
  plan=f.read_json(BASE/'protocol.json');pin=p.sha(BASE/'protocol.json')
  if sys.argv[1]=='--worker':
   if sys.argv[2]!=pin:raise p.Rejected('explicit prototype protocol pin required')
   raise SystemExit(worker(plan,pin))
  if sys.argv[1]!='--run':raise p.Rejected('fixed prepare/run/worker mode required')
  raise SystemExit(execute(plan,pin))
