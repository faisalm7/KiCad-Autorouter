from pathlib import Path
import sys,time,resource,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
O=R/'.runs/universal-preparation950-guard-targeted-001';O.mkdir();start=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
cpu0=cpu();modules=['tests.test_universal_missing_baselines'];pins={str(f.relative_to(R)):p.sha(f) for f in [R/'autorouter/strategy.py',R/'autorouter/placement_strategy.py',R/'autorouter/pipeline.py',R/'autorouter/local_settings.py',R/'experiments/universal_shift_recovery_v1/pruning_readback.py',*[R/(m.replace('.','/')+'.py') for m in modules]]}
bootstrap='import sys,os,unittest;sys.path.insert(0,'+repr(str(R))+');os.chdir('+repr(str(R))+');unittest.main(module=None)'
process=run([str(R/'.venv/bin/python'),'-B','-c',bootstrap,*modules],cwd=O,log=O/'command.log',timeout=90,max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
record=dict(schema=1,process=process,wall_seconds=time.monotonic()-start,full_cpu_seconds=cpu()-cpu0,source_sha256=pins,controller_sha256=p.sha(Path(__file__)),source_current=all(p.sha(R/n)==v for n,v in pins.items()),scope='Software scheduling/legacycontract/selectedbaseline-label tests. No Native routing-quality claim.')
p.save_json(O/'execution.json',record);print(json.dumps({k:record[k] for k in ('wall_seconds','full_cpu_seconds','source_current')}));print(json.dumps({k:process[k] for k in ('status','exit_code','cleanup_complete')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 else 2)
