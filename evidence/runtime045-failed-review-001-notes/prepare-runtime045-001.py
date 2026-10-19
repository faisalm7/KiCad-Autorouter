"""Finite local preparation via existing installer/process helpers; no qualification claim."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,shutil,os
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
from scripts.prepare_runtime import prepare
HEAD='c074c6624e776b136b8a48b6601518e41f2f506e';tools=p.tool_manifest();assert tools['git_head']==HEAD
full=f.read_json(R/'.runs/full-integration-194/execution.json');assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete'] and not full['process']['log_truncated']
assert shutil.disk_usage(R).free>4*1024**3
out=R/'.runs/runtime-directory-045';assert not out.exists();out.mkdir(mode=0o700);runtime=out/'runtime'
recipe=prepare(R,runtime,copy_local_engine=True,native_version='10.0.7');manifest_pin=p.sha(runtime/'runtime-distribution.json')
env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME') and not k.startswith('KICAD_')};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
base=Path(sys._base_executable);assert str(base)=='/Users/faisal/.pyenv/versions/3.11.9/bin/python3.11'
process=run([*f.SANDBOX,str(base),'-B','-m','venv','--copies',str(runtime/'.venv')],cwd=out,env=env,log=out/'venv.log',timeout=90,max_log_bytes=128*1024,max_workdir_bytes=256*1024**2,max_group_rss_bytes=1024**3)
p.save_json(out/'venv-process.json',process);assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated']
assert p.sha(runtime/'runtime-distribution.json')==manifest_pin and p.tool_manifest()==tools
(runtime/'.runs').mkdir(mode=0o700)  # Documented mutable job root before CLI qualification.
record={'schema':1,'kind':'runtime045-existing-local-preparation-v1','prepared':True,'qualified':False,'actual_GUI':False,'source_head':HEAD,'runtime':str(runtime),'manifest_sha256':manifest_pin,'recipe':recipe,'base_python':{'path':str(base),'sha256':p.sha(base)},'venv_process_sha256':p.sha(out/'venv-process.json'),'full194_execution_sha256':p.sha(R/'.runs/full-integration-194/execution.json'),'controller_sha256':p.sha(Path(__file__)),'sampled_wall_seconds':time.monotonic()-START,'sampled_full_CPU_seconds':cpu()-CPU0,'scope':'New immutable exact7 root using existing committed_snapshot/prepare writer, local64.6MBengine cache and copiedPython3.11.9venv. SameMac/account/externalpinnedtools; no download/cleanOS/standalone/Native/GUI/release claim.'}
p.save_json(out/'preparation.json',record);print(json.dumps({'runtime':str(runtime),'manifest_sha256':manifest_pin,'prepared':True}))
