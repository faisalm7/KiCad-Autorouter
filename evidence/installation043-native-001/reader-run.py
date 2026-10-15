"""Installed043 pure reader; lead-only, no Native/JVM/tests/network/Git."""
import time,resource
START=time.monotonic()
def cpu():
 a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
 return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import os,sys,json,subprocess
ROOT=Path(__file__).resolve().parents[2];installed=ROOT/'.runs/installation-043/checkout'
sys.path.insert(0,str(installed));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,config as c
from autorouter.runner import run
from scripts import install_smoke as install
assert Path(install.__file__).resolve().is_relative_to(installed)
assert Path(sys.executable)==installed/'.venv/bin/python' and Path(sys.prefix).resolve()==installed/'.venv' and sys.prefix!=sys.base_prefix
assert c.ROOT==installed and all(Path(m.__file__).resolve().is_relative_to(installed) for m in (p,f,h,c))
out=ROOT/'.runs/current-installation043-review-001'
inputs=out/'input-pins.json';inputs_pin=p.sha(inputs);pins=f.read_json(inputs)
assert pins['kind']=='installation043-reader-inputs-v1'
assert all(p.sha(ROOT/name)==digest for name,digest in pins['files_sha256'].items())
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}}
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run([*f.SANDBOX,str(installed/'.venv/bin/python'),'-B',str(out/'audit.py')],cwd=out,env=env,log=out/'command.log',timeout=max(.001,58-(time.monotonic()-START)),max_log_bytes=64*1024,max_workdir_bytes=16*1024**2,max_group_rss_bytes=1024**3)
def forbidden(*a,**kw):raise AssertionError('installed audit forbids workers; only exact read-only installed Git HEAD allowed')
real_run,real_popen=subprocess.run,subprocess.Popen
git_active=False
safe_git=['git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','rev-parse','HEAD']
def readonly_run(argv,*args,**kw):
 global git_active
 # tool_manifest's exact read-only provenance observation, never a worker.
 assert argv==['git','rev-parse','HEAD'] and not args and Path(kw.get('cwd',''))==installed
 assert set(kw)=={'cwd','capture_output','text','check'} and all(kw[k] is True for k in ('capture_output','text','check'))
 assert not git_active
 git_active=True
 try:return real_run(safe_git,**kw)
 finally:git_active=False
def controlled_popen(argv,*args,**kw):
 assert git_active and argv==safe_git and not args and Path(kw.get('cwd',''))==installed
 return real_popen(argv,**kw)
subprocess.run=readonly_run;subprocess.Popen=controlled_popen

checks_path=out/'checks/result.json'
checks=f.read_json(checks_path) if checks_path.is_file() else None
checks_pin=p.sha(checks_path) if checks is not None else None
checks_literal=f.canonical(checks) if checks is not None else None
log_pin=p.sha(out/'command.log');reader_pin=p.sha(out/'audit.py');controller_pin=p.sha(Path(__file__))
old_reader_pin=p.sha(ROOT/'.runs/current-installation042-review-001/audit.py')
groups={'real_installed_context','actual_commands_and_selected_tests','installed_targeted_current_changes',
 'complete_source_and_installed_inventory','installed_actual_native_smoke_and_current_readback',
 'outer_costs_and_publication','late_complete_material_and_source'}
passed=(process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
 and process['log_truncated'] is False and type(checks) is dict and checks.get('passed') is True and checks.get('status')=='completed'
 and f.evidence_inventory(out/'checks')==checks.get('completed_evidence')
 and set(checks.get('checks',{}))==groups and not checks.get('failures')
 and all(row.get('passed') is True for row in checks['checks'].values()))
record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'failed',
 source_current=True,process=process,publication_allowance_seconds=2,
 input_pins_sha256=inputs_pin,reader_sha256=reader_pin,
 adapted_reader_source_sha256=old_reader_pin,controller_sha256=controller_pin,
 log_sha256=log_pin,checks_sha256=checks_pin,
 scope='Fresh installed043 seven-group qualification under guarded publication for current free-angle/provenance core; failed001+missing00269attempts/62unique and one installed owned-v2 fullSCH transport, complete immutable source/distribution/tool/material checks. Prior040 failed records remain. No Native/JVM/tests/network in this reader, historical rewrite, default/production/GUI/quality claim.')
owner={};h.capture_destination(owner,out)
def remaining():return min(58-(time.monotonic()-START),58-(cpu()-CPU0))
def fresh():
 h.owned_destination(owner)
 if p.sha(inputs)!=inputs_pin or not all(p.sha(ROOT/name)==digest for name,digest in pins['files_sha256'].items()):
  raise p.Rejected('installed reader input/source material changed during publication')
 if (p.sha(Path(__file__))!=controller_pin or p.sha(out/'audit.py')!=reader_pin
     or p.sha(ROOT/'.runs/current-installation042-review-001/audit.py')!=old_reader_pin
     or p.sha(out/'command.log')!=log_pin or checks_pin is None
     or p.sha(checks_path)!=checks_pin or f.canonical(f.read_json(checks_path))!=checks_literal
     or f.evidence_inventory(out/'checks')!=checks.get('completed_evidence')):
  raise p.Rejected('installed reader/child checks or log changed during publication')
 baseline=ROOT/'.runs/installation-043';retained=f.read_json(baseline/'result.json')
 listing=(baseline/'03-source-files.log').read_text()
 original=f.read_json(baseline/'source-tracked.json')
 if p.sha(baseline/'source-tracked.json')!=retained['source_inventory_sha256']:
  raise p.Rejected('complete installation source inventory pin differs')
 selected=install.distribution_listing(listing)
 if (install.tracked_inventory(ROOT,listing)!=original
     or install.tracked_inventory(installed,selected)!={name:original[name] for name in selected.split('\0') if name}):
  raise p.Rejected('complete original/installed distribution changed during outer publication')
 for checkout,branch in ((ROOT,retained['source_branch']),(installed,None)):
  if install.git_identity(checkout,retained['git_head'],branch)!=retained['git_identity_witnesses'][str(checkout)]:
   raise p.Rejected('file-only source/installed Git identity changed during outer publication')
 if remaining()<=0:raise p.Rejected('installed reader whole budget exhausted')
 # Same shared final metadata check in the installed package context. The
 # complete current child/material/argv proof was replayed by installed audit.
 if passed:
  plan=f.read_json(ROOT/'.runs/installation043-angle-preparation-001/protocol.json');route=Path(plan['native_output'])/'route'
  from autorouter import local_settings as ls
  smoke=Path(retained['native_receipt']['path']);ls.check_normal_policy(smoke.parent,f.read_json(smoke),max_bytes=128*1024**2,max_files=2048)
  ls.check_normal_policy(route,f.read_json(route/'result.json'),max_bytes=128*1024**2,max_files=2048)
 if remaining()<=0:raise p.Rejected('installed reader budget exhausted during final PRL check')
def account():
 record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,
               whole_delivery_within_budget=remaining()>0)
 record['passed']=bool(passed and record['status']=='completed' and remaining()>0)
 if record['status']!='completed':record['source_current']=False
 record['cost_scope']='From first outer line before imports through guarded checks; stored sample precedes shared publication, final wall/fullCPU guards stay under58 plus2 tail within60. No historical writer timing reclassification.'
def final_check():
 fresh()
 if record['passed']:
  plan=f.read_json(ROOT/'.runs/installation043-angle-preparation-001/protocol.json')
  checked=p.check_result(Path(plan['native_output'])/'route/result.json')
  if checked.get('current') is not True:raise p.Rejected('reader outer installed final shared result check refused')
 fresh()
f.publish(out,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final_check)
stored=f.read_json(out/'result.json')
print(json.dumps({k:stored[k] for k in ('passed','source_current','status','wall_seconds','full_cpu_seconds','whole_delivery_within_budget','checks_sha256')}))
raise SystemExit(0 if stored.get('passed') is True and stored.get('status')=='completed' else 2)
