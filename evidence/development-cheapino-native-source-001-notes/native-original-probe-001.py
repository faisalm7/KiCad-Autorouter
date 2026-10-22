"""One unchanged original-project diagnostic; preparation and Native are explicit.

Run --prepare separately under /usr/bin/time, then --execute with its receipt
SHA. No Route/preflight override, source save, engine, Java, or publication.
"""
import time,resource
START=time.monotonic()
CPU=sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
import argparse,fcntl,json,os,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent
RUNTIME=ROOT/'.runs/runtime-directory-058/runtime';RAW=ROOT/'.data/development-cheapino-001'
MANIFEST='4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74'

def main():
 ap=argparse.ArgumentParser(description=__doc__);mode=ap.add_mutually_exclusive_group(required=True)
 mode.add_argument('--prepare',action='store_true');mode.add_argument('--execute',action='store_true')
 ap.add_argument('--protocol-sha256',required=True);ap.add_argument('--preparation-sha256');a=ap.parse_args()
 if a.execute and not a.preparation_sha256:ap.error('--execute requires the completed preparation receipt SHA')
 if BASE!=ROOT/'.runs/development-cheapino-native-source-001':raise ValueError('fixed fresh diagnostic namespace required')
 sys.dont_write_bytecode=True;sys.path[:0]=[str(RUNTIME),str(ROOT)]
 from autorouter import pipeline as p,config as c,provenance as pv,placement_clearance as io,floor_route as f,runner,handoff as h,local_settings as ls
 from experiments.licensed_acquisition_v1.fetch import cancellation
 if c.ROOT!=RUNTIME or Path(p.__file__).resolve()!=RUNTIME/'autorouter/pipeline.py' or c.NATIVE_VERSION!='10.0.7':raise ValueError('original058 runtime required')
 protocol=BASE/'protocol.json';digest=lambda path:pv.file_digest(pv.canonical(Path(path)),128*1024**2)[0]
 if digest(protocol)!=a.protocol_sha256:raise ValueError('explicit protocol pin differs')
 plan=f.read_json(protocol);manifest=f.read_json(RUNTIME/pv.MANIFEST)
 if (plan['kind']!='cheapino-original-native-diagnostic-v1' or plan['runtime']!=str(RUNTIME) or plan['manifest_sha256']!=MANIFEST
     or manifest['build_source']['git_head']!='8f5e96b88dd22cd25919bb71ce47711612994efa'
     or plan['raw_root']!=str(RAW) or plan['source_prl_present'] is not False
     or Path(sys.executable).resolve()!=Path(plan['supervisor_python']['path']).resolve()):raise ValueError('fixed source/runtime/Python identity required')
 expected={k:v['sha256'] for k,v in plan['raw_files'].items()};project={k.removeprefix('pcb/'):v for k,v in expected.items() if k.startswith('pcb/')}
 if (set(expected)!={'LICENSE.txt','readme.md','pcb/cheapino.kicad_pcb','pcb/cheapino.kicad_pro','pcb/cheapino.kicad_sch','pcb/cheapino.round-tracks-config'}
     or plan['limits']!=dict(overall_wall=120,overall_CPU=120,native_seconds=60,log_bytes=262144,output_bytes=50*1024**2,RSS_bytes=1024**3,files=1024,entries=2048,workers=1)):raise ValueError('exact original six-file/cap contract required')
 native_selection=c.current_native_selection()
 if native_selection!=plan['native_selection']:raise ValueError('Native selection differs from protocol')
 pins={protocol:a.protocol_sha256,RUNTIME/pv.MANIFEST:MANIFEST,Path(__file__).resolve():plan['controller_sha256']}
 pins.update({ROOT/name:pin for name,pin in plan['prerequisite_sha256'].items()})
 pins.update({RUNTIME/name:pin for name,pin in manifest['immutable_files_sha256'].items()})
 pins.update({Path(pin['path']):pin['sha256'] for pin in (*native_selection['tools'].values(),plan['supervisor_python'],plan['sandbox'])})
 prep_out=BASE/'preparation001';receipt=prep_out/'result.json';copy_root=prep_out/'source';source=copy_root/'pcb/cheapino.kicad_pcb'
 owners={}
 def owned(path):
  pv.canonical(path)
  if path not in owners:
   if not path.is_dir() or path.stat().st_uid!=os.getuid():raise ValueError('owned real directory required')
   owners[path]={};h.capture_destination(owners[path],path)
  h.owned_destination(owners[path])
  if path.stat().st_uid!=os.getuid():raise ValueError('directory ownership changed')
 for path in (ROOT,BASE,RUNTIME,RAW,RAW/'pcb'):owned(path)
 inventory=lambda path:io.inventory(path,max_bytes=2*1024**2,max_files=6,max_entries=8,with_directories=True)
 def stable(*,prl=True):
  for path,pin in pins.items():
   if digest(path)!=pin:raise ValueError('captured source/tool/helper changed: '+str(path))
  if c.current_native_selection()!=native_selection or inventory(RAW)!=(expected,('.','pcb')):raise ValueError('raw six-file source changed')
  for path in tuple(owners):owned(path)
  if copy_root.exists():
   if inventory(copy_root)!=(expected,('.','pcb')) or p.tree_hash(source.parent)!=project:raise ValueError('preserved complete source copy changed')
  io.inventory(BASE,max_bytes=50*1024**2,max_files=1024,max_entries=2048)
  if prl:
   for path in BASE.rglob('*.kicad_prl'):ls.check_current_metadata(path)
 def elapsed_cpu():return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))-CPU
 def remaining():
  value=min(120-(time.monotonic()-START),120-elapsed_cpu())
  if value<=0:raise ValueError('original overall wall/full-CPU budget exhausted')
  return value
 def account():record.update(wall_seconds=time.monotonic()-START,total_cpu_seconds=elapsed_cpu())
 stable();remaining()
 with cancellation(),pv.canonical(ROOT/'.runs/quality-experiment.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);stable();remaining()
  if a.prepare:
   if a.preparation_sha256 is not None:raise ValueError('preparation cannot consume an old receipt')
   prep_out.mkdir(mode=0o700);owned(prep_out)
   record=dict(schema=1,kind=plan['kind'],status='preparing',accepted=False,production_admitted=False,Native=False,routing_attempted=False,protocol_sha256=a.protocol_sha256)
   try:
    shutil.copytree(RAW,copy_root);os.chmod(copy_root,0o700)
    for path in copy_root.rglob('*'):os.chmod(path,0o700 if path.is_dir() else 0o600)
    owned(copy_root);owned(copy_root/'pcb');stable()
    record.update(status='prepared',source=str(source),source_hashes=project,raw_files=plan['raw_files'],source_prl_present=False,source_unchanged=True)
   except (Exception,KeyboardInterrupt) as exc:record.update(status='preparation_refused',error=type(exc).__name__+': '+str(exc))
   result=f.publish(prep_out,record,stable,account,remaining,owned=lambda:owned(prep_out),final_check=lambda:(stable(),remaining()))
  else:
   if digest(receipt)!=a.preparation_sha256:raise ValueError('explicit completed preparation pin differs')
   prepared=f.read_json(receipt)
   if prepared['status']!='prepared' or prepared['Native'] is not False or prepared['protocol_sha256']!=a.protocol_sha256 or prepared['source']!=str(source) or prepared['source_hashes']!=project:raise ValueError('exact successful preparation required')
   pins[receipt]=a.preparation_sha256
   for path in (prep_out,copy_root,copy_root/'pcb'):owned(path)
   class Job(p.Job):
    def step(self,name,argv,allowed=(0,)):
     stable(prl=False);limit=min(60,remaining(),native_deadline-time.monotonic())
     if limit<=0:raise ValueError('single Native operation allowance exhausted')
     result=runner.run([str(x) for x in [*f.SANDBOX,*argv]],cwd=self.out,log=self.out/(name+'.log'),timeout=limit,env=self.env,
      max_log_bytes=262144,max_group_rss_bytes=1024**3,max_workdir_bytes=50*1024**2-sum(p.stat().st_size for p in copy_root.rglob('*') if p.is_file()))
     result['name']=name;self.steps.append(result);p.save_json(self.out/(name+'-process.json'),result)
     if result['status']=='cancelled':raise KeyboardInterrupt('Native cancellation')
     if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed or result['cleanup_complete'] is not True or result['log_truncated'] is not False:raise ValueError('bounded Native worker failed')
     stable(prl=False);remaining();return result
   stable();job=Job(BASE/'native-original-001',120,protect_local_settings=True);owned(job.out);job.remaining=remaining
   for key in tuple(job.env):
    if key in ('PYTHONPATH','PYTHONHOME') or key.startswith('KICAD_') and key not in ('KICAD_CONFIG_HOME','KICAD_CACHE_HOME','KICAD_DOCUMENTS_HOME'):job.env.pop(key)
   for key,name in (('HOME','home'),('TMPDIR','tmp')):(job.out/name).mkdir();job.env[key]=str(job.out/name)
   job.env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1');native_deadline=time.monotonic()+min(60,remaining())
   record=dict(schema=1,kind=plan['kind'],status='running',accepted=False,production_admitted=False,Native=True,routing_attempted=False,
    source=str(source),source_hashes=project,source_prl_present=False,source_unchanged=False,protocol_sha256=a.protocol_sha256,preparation_sha256=a.preparation_sha256,
    controller_sha256=plan['controller_sha256'],runtime=str(RUNTIME),runtime_manifest_sha256=MANIFEST,steps=job.steps,
    accounting='Parent plus waited-child CPU; preparation is separately metered. Stored totals precede final external exit; authoring/review additional unknown. Polled bounds may overshoot.',
    scope='Original source only, full SCH/refill/original PRO. Opens alone are routing demand; counts do not establish eligibility, candidate acceptance, electrical/physical or human qualification. No CAD publication.')
   completed=None
   def final_readback():
    stable()
    if completed is not None:
     native=f.check_drc_stage(job.out,record,'original-drc',source,job.out/'original-drc-input'/source.name,False,project,schematic_parity=True)
     if native!=completed:raise ValueError('final original-source Native readback differs')
    remaining();stable()
   try:
    completed=job.drc('original-drc',source,save=False,schematic_parity=True);final_readback()
    record.update(status='completed_diagnostic',native=completed,source_native_policy=p.native_accepted(completed),source_native_reasons=p.native_rejection_reasons(completed),source_unchanged=True,
     final_report_sha256=p.sha(job.out/'original-drc.json'),final_binding_sha256=p.sha(job.out/'original-drc-binding.json'),opens_are_routing_demand_not_source_invalidity=True)
   except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'diagnostic_refused',error=type(exc).__name__+': '+str(exc))
   result=f.publish(job.out,record,stable,account,remaining,owned=lambda:owned(job.out),final_check=final_readback)
 print(json.dumps({key:result.get(key) for key in ('status','accepted','routing_attempted','source_unchanged','wall_seconds','total_cpu_seconds','error')}))
 return 0 if result['status'] in ('prepared','completed_diagnostic') else 1

if __name__=='__main__':raise SystemExit(main())
