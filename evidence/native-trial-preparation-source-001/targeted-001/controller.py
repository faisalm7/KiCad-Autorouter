from pathlib import Path
import sys,time,resource,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
O=R/'.runs/native-trial-preparation-targeted-001';O.mkdir();start=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
cpu0=cpu();modules=['tests.test_strategy','tests.test_placement_allocation','tests.test_pruning_scoring','tests.test_pruning_preferences','tests.test_improve_preferences_cli','tests.test_pruning_preferences_freshness','tests.test_universal_missing_baselines','tests.test_core_local_settings','tests.test_normal_local_settings_policy','tests.test_alias_budget_publication'];pins={str(f.relative_to(R)):p.sha(f) for f in [R/'autorouter/strategy.py',R/'autorouter/placement_strategy.py',R/'autorouter/pipeline.py',R/'autorouter/local_settings.py',*[R/(m.replace('.','/')+'.py') for m in modules]]}
bootstrap='import sys,os,unittest;sys.path.insert(0,'+repr(str(R))+');os.chdir('+repr(str(R))+');unittest.main(module=None)'
process=run([str(R/'.venv/bin/python'),'-B','-c',bootstrap,*modules],cwd=O,log=O/'command.log',timeout=90,max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
record=dict(schema=1,process=process,wall_seconds=time.monotonic()-start,full_cpu_seconds=cpu()-cpu0,source_sha256=pins,controller_sha256=p.sha(Path(__file__)),source_current=all(p.sha(R/n)==v for n,v in pins.items()),scope='Software scheduling/legacycontract/selectedbaseline-label tests. No Native routing-quality claim.')
p.save_json(O/'execution.json',record);print(json.dumps({k:record[k] for k in ('wall_seconds','full_cpu_seconds','source_current')}));print(json.dumps({k:process[k] for k in ('status','exit_code','cleanup_complete')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 else 2)
