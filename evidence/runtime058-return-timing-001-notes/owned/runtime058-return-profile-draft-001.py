"""DRAFT: two sequential read-only profiles of stored058 publication checks.

Reuse the057 bind profiler/shared runner. This intentionally uses immutable058's
known archive-reader bug as a profiling seam only; no result is promoted, copied,
applied or republished. All output goes to a fresh diagnostic namespace.
"""
from pathlib import Path
import argparse,contextlib,cProfile,fcntl,json,os,pstats,resource,stat,sys,time
ROOT=Path(__file__).resolve().parents[1];RUNTIME=ROOT/'.runs/runtime-directory-058/runtime'
SELF=ROOT/'.runs/runtime058-return-profile-draft-001.py';OUT=ROOT/'.runs/runtime058-return-profile-001'
sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,gui,preferences as pref,provenance as pv,strategy as s
from autorouter.runner import run
ap=argparse.ArgumentParser();ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);ap.add_argument('--execute',action='store_true');ap.add_argument('--worker',choices=('cold','session'));a=ap.parse_args()
assert a.execute,'DRAFT: explicit --execute required'
protocol=a.protocol.absolute();assert p.sha(protocol)==a.protocol_sha256;plan=f.read_json(protocol)
assert p.sha(SELF)==plan['controller_sha256'] and Path(p.__file__).resolve()==RUNTIME/'autorouter/pipeline.py'
assert Path(sys.prefix).resolve()==RUNTIME/'.venv' and plan['runtime']==str(RUNTIME)
assert plan['runtime_manifest_sha256']=='4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74'
ROUTE=Path(plan['route_directory']);ARCHIVE=Path(plan['archive']);SOURCE=Path(plan['source'])
def cpu():return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
def fresh():
 assert p.sha(SELF)==plan['controller_sha256'] and p.sha(protocol)==a.protocol_sha256
 for name,pin in plan['prerequisite_sha256'].items():assert p.sha(Path(name))==pin,name
 assert p.tree_hash(SOURCE.parent)==plan['source_hashes'] and p.tree_hash(ROUTE)==plan['packet_files_sha256']
 info=ROUTE.lstat();assert dict(dev=info.st_dev,ino=info.st_ino,uid=info.st_uid)==plan['parent_identity']
 assert p.tool_manifest()==plan['tools']
 for name,expected in plan['PRL_metadata'].items():
  info=Path(name).lstat();assert dict(mode=stat.S_IFMT(info.st_mode),uid=info.st_uid,nlink=info.st_nlink,flags=getattr(info,'st_flags',0))==expected
fresh()

def worker(variant):
 start=time.monotonic();cpu0=cpu();folder=OUT/variant;assert folder.is_dir() and not (folder/'result.json').exists()
 report=f.read_json(ARCHIVE);seal=f.canonical(report);assert report['accepted'] is True and report['status']=='routing_accepted'
 canonical=f.read_json(ROUTE/'result.json');assert canonical['accepted'] is False and canonical['status']=='timeout'
 assert report['candidate_sha256']==canonical['candidate_sha256'] and p._readback_session.get() is None
 captured=pref.load(Path(plan['settings']));assert pref.resolve(captured)==dict(pref.DEFAULTS,profile='tuned',seconds=90)
 owner={};h.capture_destination(owner,ROUTE);snapshot=ROUTE/'snapshot';completed=f.evidence_inventory(ROUTE)
 record=dict(schema=1,variant=variant,accepted=False,Native=False,routing=False,applied=False,project_complete=False,
  status='started',controller_sha256=plan['controller_sha256'],protocol_sha256=a.protocol_sha256,
  scope=plan['scope'],omissions=plan['omissions'],stages=[])
 def original_fresh():
  pref.check_fresh(captured);s._check_original(SOURCE,snapshot,report['source_hashes'])
 def stable():
  # Same default single/native7 stable branch; incumbent_options is None here.
  h.owned_destination(owner);pref.check_fresh(captured)
  if report.get('source_hashes') and snapshot.is_dir():original_fresh()
  for relative,pin in report['tools']['implementation_sha256'].items():
   if p.sha(RUNTIME/relative)!=pin:raise p.Rejected('profile runtime changed')
  s._chain_context_fresh(ROUTE,report);s._adaptive_branch_fresh(ROUTE,report)
  s.check_incumbent_scoring(ROUTE,report);s.check_single_selection(ROUTE,report)
  def material():
   if p.tool_manifest()!=report['tools'] or f.evidence_inventory(ROUTE)!=completed:raise p.Rejected('profile parent material changed')
   original_fresh()
  s.check_native7_final(ROUTE,report,material=material)
 def stage(name,call):
  wall=time.monotonic();used=cpu();call()
  record['stages'].append(dict(name=name,wall_seconds=time.monotonic()-wall,full_CPU_seconds=cpu()-used))
  if max(time.monotonic()-start,cpu()-cpu0)>90:raise p.Rejected('profile90s wall/fullCPU exhausted')
 profiler=cProfile.Profile();profile_started=time.monotonic();profile_cpu=cpu()
 try:
  profiler.enable()
  with (p.validation_readback_session() if variant=='session' else contextlib.nullcontext()):
   stage('stable_before_account',stable)
   stage('stable_after_omitted_write',stable)
   def reader():
    checked=p.check_result(ARCHIVE)
    if checked.get('current') is not True or checked.get('candidate_sha256')!=report['candidate_sha256']:raise p.Rejected('old058 profiling seam refused')
   stage('one_full_stored_reader',reader)
   stage('stable_after_reader',stable)
  record['status']='completed'
 except BaseException as exc:record.update(status='refused',error=type(exc).__name__+': '+str(exc))
 finally:
  profiler.disable();record.update(instrumented_sequence_wall_seconds=time.monotonic()-profile_started,instrumented_sequence_full_CPU_seconds=cpu()-profile_cpu)
  profiler.dump_stats(str(folder/'profile.pstats'));stats=pstats.Stats(profiler).stats
  rows=[dict(file=file,line=line,function=function,primitive_calls=cc,calls=nc,own_seconds=tt,cumulative_seconds=ct) for (file,line,function),(cc,nc,tt,ct,_) in stats.items()]
  wanted={'_native7_incumbent_context_uncached','native7_incumbent_context','__post_init__','check_incumbent_scoring','check_single_selection','check_native7_final','check_result','_check_result_uncached','parse','_parse_uncached','check'}
  record['selected_functions']=[r for r in rows if r['function'] in wanted and str(RUNTIME/'autorouter') in r['file']]
  record['top_cumulative']=sorted(rows,key=lambda r:r['cumulative_seconds'],reverse=True)[:40]
  record['Context_constructions']=sum(r['calls'] for r in rows if r['function']=='_native7_incumbent_context_uncached' and r['file']==str(RUNTIME/'autorouter/strategy.py'))
  record['Context_count_interpretation']='Entries to existing uncached reconstructed-Context constructor; completed profiles additionally retain Context method call counts. No function was wrapped or replaced.'
  record['simulated_post_account_wall_seconds']=sum(r['wall_seconds'] for r in record['stages'] if r['name']!='stable_before_account')
  record['simulated_post_account_full_CPU_seconds']=sum(r['full_CPU_seconds'] for r in record['stages'] if r['name']!='stable_before_account')
  try:
   fresh();assert p._readback_session.get() is None and f.canonical(report)==seal;h.owned_destination(owner)
   record['inputs_unchanged']=True
  except BaseException as exc:record.update(status='refused',inputs_unchanged=False,freshness_error=type(exc).__name__+': '+str(exc))
  record.update(sampled_wall_seconds=time.monotonic()-start,sampled_full_CPU_seconds=cpu()-cpu0,external_complete_time_required=True)
  if max(record['sampled_wall_seconds'],record['sampled_full_CPU_seconds'])>90:record['status']='over_budget'
  p.save_json(folder/'result.json',record)
  fresh();h.owned_destination(owner)
 print(json.dumps(dict(variant=variant,status=record['status'],Context_constructions=record['Context_constructions'],accepted=False,Native=False,routing=False)),flush=True)
 return record['status']=='completed' and record.get('inputs_unchanged') is True

if a.worker:
 raise SystemExit(0 if worker(a.worker) else 2)
assert not os.path.lexists(OUT)
fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
with os.fdopen(fd,'r+') as lane:
 info=os.fstat(lane.fileno());assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_uid==os.getuid();fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
 OUT.mkdir(mode=0o700);owner={};h.capture_destination(owner,OUT);rows=[]
 for variant in ('cold','session'):
  fresh();folder=OUT/variant;folder.mkdir(mode=0o700)
  process=run(['/usr/bin/time','-lp',*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B',str(SELF),'--protocol',str(protocol),'--protocol-sha256',a.protocol_sha256,'--execute','--worker',variant],
   cwd=folder,env=gui.child_environment(),log=folder/'complete-command-and-time.log',timeout=90,
   max_log_bytes=1024**2,max_group_rss_bytes=2*1024**3,max_workdir_bytes=8*1024**2)
  p.save_json(folder/'process.json',process);fresh();h.owned_destination(owner)
  okay=process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'] and process['cpu_seconds']+process.get('supervisor_cpu_seconds',0)+process.get('monitor_cpu_seconds',0)<=90
  rows.append(dict(variant=variant,profile_completed=okay,process_sha256=p.sha(folder/'process.json'),complete_log_sha256=p.sha(folder/'complete-command-and-time.log'),result_sha256=p.sha(folder/'result.json') if (folder/'result.json').is_file() else None))
  if not okay:break
 fresh();h.owned_destination(owner)
 p.save_json(OUT/'execution.json',dict(schema=1,accepted=False,Native=False,routing=False,project_complete=False,rows=rows,scope=plan['scope'],protocol_sha256=a.protocol_sha256,controller_sha256=plan['controller_sha256']))
 fresh();h.owned_destination(owner)
 print(json.dumps(dict(completed_variants=len(rows),all_profiled=len(rows)==2 and all(r['profile_completed'] for r in rows),accepted=False,Native=False,routing=False)))
 raise SystemExit(0 if len(rows)==2 and all(r['profile_completed'] for r in rows) else 2)
