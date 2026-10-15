"""Installed040 pure reader; lead-only, no Native/JVM/tests/network/Git."""
import time,resource
START=time.monotonic()
def cpu():
 a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
 return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import os,sys,json
ROOT=Path(__file__).resolve().parents[2];installed=ROOT/'.runs/installation-040/checkout'
sys.path.insert(0,str(installed));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,config as c
from autorouter.runner import run
from scripts import install_smoke as install
assert Path(install.__file__).resolve().is_relative_to(installed)
assert c.ROOT==installed and all(Path(m.__file__).resolve().is_relative_to(installed) for m in (p,f,h,c))
out=ROOT/'.runs/current-installation040-review-005'
inputs=out/'input-pins.json';inputs_pin=p.sha(inputs);pins=f.read_json(inputs)
assert pins['kind']=='installation040-reader-inputs-v1'
assert all(p.sha(ROOT/name)==digest for name,digest in pins['files_sha256'].items())
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}}
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run([*f.SANDBOX,str(installed/'.venv/bin/python'),'-B',str(out/'audit.py')],cwd=out,env=env,log=out/'command.log',timeout=max(.001,58-(time.monotonic()-START)),max_log_bytes=64*1024,max_workdir_bytes=16*1024**2,max_group_rss_bytes=1024**3)
checks_path=out/'checks.json'
checks=f.read_json(checks_path) if checks_path.is_file() else None
checks_pin=p.sha(checks_path) if checks is not None else None
checks_literal=f.canonical(checks) if checks is not None else None
log_pin=p.sha(out/'command.log');reader_pin=p.sha(out/'audit.py');controller_pin=p.sha(Path(__file__))
old_reader_pin=p.sha(ROOT/'.runs/current-installation039-review-001/audit.py')
groups={'real_installed_context','actual_commands_and_selected_tests','installed_targeted_current_changes',
 'complete_source_and_installed_inventory','installed_actual_native_smoke_and_current_readback',
 'outer_costs_and_publication','late_complete_material_and_source'}
passed=(process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
 and process['log_truncated'] is False and type(checks) is dict and checks.get('passed') is True
 and set(checks.get('checks',{}))==groups and not checks.get('failures')
 and all(row.get('passed') is True for row in checks['checks'].values()))
record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'failed',
 source_current=True,process=process,publication_allowance_seconds=2,
 input_pins_sha256=inputs_pin,reader_sha256=reader_pin,
 adapted_reader_source_sha256=old_reader_pin,controller_sha256=controller_pin,
 log_sha256=log_pin,checks_sha256=checks_pin,
 scope='Missing-only current installed040 retained qualification under guarded publication. Original targeted pre-write receipt and actual Native outer invalidation remain unchanged. Installed current child producer/shared transport can qualify; no retroactive outer-publication completion, historical timing rewrite, new Native/JVM/test, production/default/GUI/quality claim.')
owner={};h.capture_destination(owner,out)
def remaining():return min(58-(time.monotonic()-START),58-(cpu()-CPU0))
def fresh():
 h.owned_destination(owner)
 if p.sha(inputs)!=inputs_pin or not all(p.sha(ROOT/name)==digest for name,digest in pins['files_sha256'].items()):
  raise p.Rejected('installed reader input/source material changed during publication')
 if (p.sha(Path(__file__))!=controller_pin or p.sha(out/'audit.py')!=reader_pin
     or p.sha(ROOT/'.runs/current-installation039-review-001/audit.py')!=old_reader_pin
     or p.sha(out/'command.log')!=log_pin or checks_pin is None
     or p.sha(checks_path)!=checks_pin or f.canonical(f.read_json(checks_path))!=checks_literal):
  raise p.Rejected('installed reader/child checks or log changed during publication')
 baseline=ROOT/'.runs/installation-040';retained=f.read_json(baseline/'result.json')
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
  plan=f.read_json(ROOT/'.runs/installation040-native-preparation-001/protocol.json')
  nt=p.ExperimentalNativeToolchain.from_record(plan['native_toolchain'])
  route=Path(plan['native_output'])/'route'
  p.check_experimental_local_settings(route,f.read_json(route/'result.json'),nt)
 if remaining()<=0:raise p.Rejected('installed reader budget exhausted during final PRL check')
def account():
 record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,
               whole_delivery_within_budget=remaining()>0)
 record['passed']=bool(passed and record['status']=='completed' and remaining()>0)
 if record['status']!='completed':record['source_current']=False
 record['cost_scope']='From first outer line before imports through guarded checks; stored sample precedes shared publication, final wall/fullCPU guards stay under58 plus2 tail within60. No historical writer timing reclassification.'
f.publish(out,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=fresh)
stored=f.read_json(out/'result.json')
print(json.dumps({k:stored[k] for k in ('passed','source_current','status','wall_seconds','full_cpu_seconds','whole_delivery_within_budget','checks_sha256')}))
raise SystemExit(0 if stored.get('passed') is True and stored.get('status')=='completed' else 2)
