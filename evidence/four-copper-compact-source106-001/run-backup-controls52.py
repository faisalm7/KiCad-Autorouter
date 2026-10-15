from pathlib import Path
import time,resource,sys,json
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
out=ROOT/'.runs/backup-compact-delta-controls-002';out.mkdir()
code={str(q):p.sha(q) for q in [ROOT/'scripts/backup.py',*ROOT.glob('tests/test_backup*.py')]}
mods=['tests.test_backup_compact_delta','tests.test_backup_incremental','tests.test_backup','tests.test_backup_capacity','tests.test_backup_file_capacity','tests.test_backup_draft_source','tests.test_backup_floor_fixture']
bootstrap='import sys,unittest;sys.dont_write_bytecode=True;sys.path[:0]='+repr([str(ROOT),str(ROOT/'tests')])+';unittest.main(module=None,argv='+repr(['unittest','-v',*mods])+')'
proc=run([str(ROOT/'.venv/bin/python'),'-B','-c',bootstrap],cwd=out,log=out/'command.log',timeout=120,max_log_bytes=256*1024,max_workdir_bytes=8*1024**2,max_group_rss_bytes=1024**3)
record=dict(process=proc,wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,code_sha256=code,log_sha256=p.sha(out/'command.log'),source_unchanged=code=={n:p.sha(Path(n)) for n in code},scope='Targeted backup modules; actual small scratch archive/Git/CLI tests, no Native/JVM/project-wide backup. Initial001invalid caller scan arguments failed before runner/tests; cost unavailable, preserved separately.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ['wall_seconds','full_cpu_seconds','source_unchanged']}));print(json.dumps({k:proc[k] for k in ['status','exit_code','cleanup_complete']}));raise SystemExit(0 if proc['status']=='success' and proc['exit_code']==0 and record['source_unchanged'] else 2)
