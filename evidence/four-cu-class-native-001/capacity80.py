from pathlib import Path
import time,resource,sys,json
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
out=ROOT/'.runs/four-cu-capacity-targeted-001';out.mkdir()
code={str(q):p.sha(q) for q in [ROOT/'scripts/backup.py',*ROOT.glob('tests/test_backup*.py'),ROOT/'scripts/install_smoke.py',ROOT/'tests/test_install_smoke.py']}
mods=['tests.test_backup_compact_delta','tests.test_backup_incremental','tests.test_backup','tests.test_backup_capacity','tests.test_backup_file_capacity','tests.test_backup_draft_source','tests.test_backup_floor_fixture','tests.test_install_smoke']
bootstrap='import sys,unittest;sys.dont_write_bytecode=True;sys.path[:0]='+repr([str(ROOT),str(ROOT/'tests')])+';unittest.main(module=None,argv='+repr(['unittest','-v',*mods])+')'
proc=run([str(ROOT/'.venv/bin/python'),'-B','-c',bootstrap],cwd=out,log=out/'command.log',timeout=120,max_log_bytes=256*1024,max_workdir_bytes=8*1024**2,max_group_rss_bytes=1024**3)
record=dict(process=proc,wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,code_sha256=code,log_sha256=p.sha(out/'command.log'),source_unchanged=code=={n:p.sha(Path(n)) for n in code},scope='Only finite raw-file/directory305k-to310k and complete-installedsource22k-to22.5k counts change after actual sourcefile guard refusal and measured nextinstall rawforecast. Bytes/time/receipt/scopes/archive/security/design acceptance unchanged. Actual installed/fullchainrestore stillrequired; full107predates these two small operational constants.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ['wall_seconds','full_cpu_seconds','source_unchanged']}));print(json.dumps({k:proc[k] for k in ['status','exit_code','cleanup_complete']}));raise SystemExit(0 if proc['status']=='success' and proc['exit_code']==0 and record['source_unchanged'] else 2)
