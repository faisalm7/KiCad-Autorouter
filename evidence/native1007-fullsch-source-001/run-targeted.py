"""Targeted software controls using the existing bounded runner; no Native proof."""
import time,resource
START=time.monotonic()
def cpu():
 a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
 return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import os,sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
out=ROOT/'.runs/native-schematic-targeted-001';out.mkdir()
modules=['tests.test_native_toolchain','tests.test_native_schematic_transport','tests.test_schematic_fields','tests.test_schematic_fields_native_version','tests.test_schematic_field_evidence','tests.test_parity_availability','tests.test_drc_failure_binding','tests.test_normal_local_settings_policy','tests.test_core_local_settings']
names=['autorouter/pipeline.py','autorouter/floor_route.py','autorouter/schematic_fields.py','autorouter/schematic_field_evidence.py','autorouter/local_settings.py']+[m.replace('.','/')+'.py' for m in modules]
frozen={n:p.sha(ROOT/n) for n in names}
env={k:v for k,v in os.environ.items() if k!='PYTHONHOME'};env.update(PYTHONPATH=str(ROOT)+os.pathsep+str(ROOT/'tests'),PYTHONDONTWRITEBYTECODE='1')
process=run([str(ROOT/'.venv/bin/python'),'-B','-m','unittest',*modules,'-v'],cwd=out,env=env,log=out/'command.log',timeout=max(.001,88-(time.monotonic()-START)),max_log_bytes=128*1024,max_workdir_bytes=4*1024**2,max_group_rss_bytes=1024**3)
current=frozen=={n:p.sha(ROOT/n) for n in frozen};wall=time.monotonic()-START;full=cpu()-CPU0
passed=current and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'] and max(wall,full)+2<=90
record=dict(schema=1,passed=passed,source_current=current,process=process,source_sha256=frozen,modules=modules,wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2,whole_wall_full_cpu_cap_seconds=90,controller_sha256=p.sha(Path(__file__)),log_sha256=p.sha(out/'command.log'),scope='Explicit experimental schematic opt-in and protected mode, exact typed field transport/version identities, hidden later fields, default1000/parityavailability/PRL/failure journals. Software controls only; actual fullSCH/Native qualification remains prospective.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('passed','source_current','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if passed else 2)
