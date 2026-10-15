from pathlib import Path
import sys,time,json,resource
START=time.monotonic();CPU=sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f
from autorouter.runner import run
label=sys.argv[1];out=ROOT/'.runs'/label;out.mkdir()
names=sys.argv[2:] or ['tests.test_strategy.StrategyControlFlowTests.test_adaptive_branch_rebinds_after_last_inventory_callback','tests.test_strategy.StrategyControlFlowTests.test_adaptive_final_source_or_code_callback_invalidates_publication','tests.test_strategy.StrategyControlFlowTests.test_adaptive_stop_decision_rejects_an_appended_trial','tests.test_strategy.StrategyControlFlowTests.test_adaptive_duplicate_chain_does_not_skip_later_distinct_group']
pins={n:p.sha(ROOT/n) for n in ['autorouter/strategy.py','tests/test_strategy.py','tests/test_pruning_preferences_freshness.py','autorouter/pipeline.py','tests/test_storage_scan.py']}
code='import sys,os,unittest;sys.path.insert(0,'+repr(str(ROOT))+');os.chdir('+repr(str(ROOT))+');suite=unittest.defaultTestLoader.loadTestsFromNames('+repr(names)+');r=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(0 if r.wasSuccessful() else 1)'
result=run([str(ROOT/'.venv/bin/python'),'-B','-c',code],cwd=out,log=out/'tests.log',timeout=max(.001,40-(time.monotonic()-START)),max_log_bytes=256*1024,max_workdir_bytes=1024*1024,max_group_rss_bytes=2*1024**3)
record=dict(schema=1,names=names,source_sha256=pins,process=result,wall_seconds=time.monotonic()-START,full_cpu_seconds=time.process_time()+f.child_cpu()-CPU,controller_sha256=p.sha(Path(__file__)),log_sha256=p.sha(out/'tests.log'),scope='Authored software mutation/control-flow regressions only; no Native routing evidence.')
assert pins=={n:p.sha(ROOT/n) for n in pins};p.save_json(out/'execution.json',record)
print(json.dumps({k:record[k] for k in ('wall_seconds','full_cpu_seconds')}));print((out/'tests.log').read_text());raise SystemExit(0 if result['status']=='success' and result['exit_code']==0 else 2)
