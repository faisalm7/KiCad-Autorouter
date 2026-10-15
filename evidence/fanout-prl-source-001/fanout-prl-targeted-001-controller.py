from pathlib import Path
import time,resource,sys,json
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
out=ROOT/'.runs/fanout-prl-targeted-001';out.mkdir()
mods=['tests.test_engine_fanout','tests.test_engine_angle','tests.test_engine_angle_native_control','tests.test_engine_profiles','tests.test_preference_publication','tests.test_pruning_preferences_freshness','tests.test_padstack_policy','tests.test_selected_evidence','tests.test_result.ResultFreshnessTests.test_current_normal_engine_budget_cannot_be_removed_with_its_worker']
code={str(q):p.sha(q) for q in [*ROOT.glob('autorouter/*.py'),*ROOT.glob('tests/*.py'),*ROOT.glob('experiments/free_angle_baseline_v1/*'),*ROOT.glob('experiments/fanout_baseline_v1/*')] if q.is_file()}
bootstrap='import sys,unittest;sys.dont_write_bytecode=True;sys.path[:0]='+repr([str(ROOT),str(ROOT/'tests')])+';from experiments.free_angle_baseline_v1 import enclosure;unittest.main(module=None,argv='+repr(['unittest','-v',*mods])+')'
proc=run([str(ROOT/'.venv/bin/python'),'-B','-c',bootstrap],cwd=out,log=out/'command.log',timeout=120,max_log_bytes=256*1024,max_workdir_bytes=8*1024**2,max_group_rss_bytes=1024**3)
record=dict(process=proc,wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,code_sha256=code,log_sha256=p.sha(out/'command.log'),source_unchanged=code=={n:p.sha(Path(n)) for n in code},expected_unique_methods=78,scope='Reviewed private non-strict fanout override; real exact stable callback/owned flag-only PRL freshness regressions after actual before-fix defect, default None invariance/reciprocaljournal/scope and safe explicit short-output path. Portable scratch setup fixes. Software only; Native/source/originalrules/protected/fullSCH remains actual later gate, no quality/family/default claim.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ['wall_seconds','full_cpu_seconds','source_unchanged']}));print(json.dumps({k:proc[k] for k in ['status','exit_code','cleanup_complete']}));raise SystemExit(0 if proc['status']=='success' and proc['exit_code']==0 and record['source_unchanged'] else 2)
