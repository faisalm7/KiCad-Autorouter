from pathlib import Path
import time,resource,sys,json
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
out=ROOT/'.runs/free-angle-fixture-missing-005';out.mkdir()
mods=['tests.test_pruning_preferences_freshness']
code={str(q):p.sha(q) for q in [*ROOT.glob('autorouter/*.py'),*ROOT.glob('tests/*.py')]}
bootstrap='import sys,unittest;sys.dont_write_bytecode=True;sys.path[:0]='+repr([str(ROOT),str(ROOT/'tests')])+';unittest.main(module=None,argv='+repr(['unittest','-v',*mods])+')'
proc=run([str(ROOT/'.venv/bin/python'),'-B','-c',bootstrap],cwd=out,log=out/'command.log',timeout=120,max_log_bytes=256*1024,max_workdir_bytes=8*1024**2,max_group_rss_bytes=1024**3)
record=dict(process=proc,wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,code_sha256=code,log_sha256=p.sha(out/'command.log'),source_unchanged=code=={n:p.sha(Path(n)) for n in code},scope='Scoped API-only free-angle baseline transport/provenance, unchanged default/tuned caps, complete Native/original-rule validation remains mandatory. Targeted software controls only; no Native/JVM/quality claim.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ['wall_seconds','full_cpu_seconds','source_unchanged']}));print(json.dumps({k:proc[k] for k in ['status','exit_code','cleanup_complete']}));raise SystemExit(0 if proc['status']=='success' and proc['exit_code']==0 and record['source_unchanged'] else 2)
