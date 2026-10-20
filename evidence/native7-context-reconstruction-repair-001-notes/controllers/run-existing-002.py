from pathlib import Path
import sys,time,resource,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
O=R/'.runs/native7-context-existing-targeted-002';O.mkdir();start=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
cpu0=cpu();modules=['tests.test_native7_parent_import_order','tests.test_native7_guard_reconstruction','tests.test_normal_selected_import','tests.test_named_edge_parent','tests.test_thermal_parent','tests.test_sexpr_memo', 'tests.test_validation_readback', 'tests.test_native7_improve_parent', 'tests.test_native7_improve_child_context', 'tests.test_native7_review_boundary', 'tests.test_native7_choice_boundary', 'tests.test_handoff', 'tests.test_inherited_trial_readback'];pins={str(f.relative_to(R)):p.sha(f) for f in [R/'autorouter/sexpr.py',R/'autorouter/pipeline.py',R/'autorouter/strategy.py',*[R/(m.replace('.','/')+'.py') for m in modules]]}
bootstrap='import sys,os,unittest;sys.path.insert(0,'+repr(str(R))+');sys.path.insert(0,'+repr(str(R/'tests'))+');os.chdir('+repr(str(R))+');unittest.main(module=None)'
process=run([str(R/'.venv/bin/python'),'-B','-c',bootstrap,*modules],cwd=O,log=O/'command.log',timeout=90,max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
record=dict(schema=1,process=process,wall_seconds=time.monotonic()-start,full_cpu_seconds=cpu()-cpu0,source_sha256=pins,controller_sha256=p.sha(Path(__file__)),source_current=all(p.sha(R/n)==v for n,v in pins.items()),scope='Existing targeted regressions after operation-local reconstruction-only Context reuse; every private-child/parent semantic read and authority/freshness fence remains, no result memo. No actual Native or routing quality claim.')
p.save_json(O/'execution.json',record);print(json.dumps({k:record[k] for k in ('wall_seconds','full_cpu_seconds','source_current')}));print(json.dumps({k:process[k] for k in ('status','exit_code','cleanup_complete')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 else 2)
