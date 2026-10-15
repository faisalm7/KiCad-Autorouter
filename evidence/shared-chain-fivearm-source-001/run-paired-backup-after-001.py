from pathlib import Path
import sys,time,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
O=R/'.runs/paired-backup-after-001';O.mkdir();pins={n:p.sha(R/n) for n in ['scripts/experiment_paired.py','scripts/backup.py','tests/test_paired.py','tests/test_backup_capacity.py']};start=time.monotonic();cpu=time.process_time()+f.child_cpu()
process=run([str(R/'.venv/bin/python'),'-B',str(R/'.runs/test-paired-backup-after-001.py')],cwd=O,log=O/'command.log',timeout=120,max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
assert pins=={n:p.sha(R/n) for n in pins}
p.save_json(O/'execution.json',dict(schema=1,process=process,source_sha256=pins,wall_seconds=time.monotonic()-start,full_cpu_seconds=time.process_time()+f.child_cpu()-cpu,scope='Shared fivearm driver/returnpublication/cancellation/freshness/budget and unchanged backup guards with10GiB bytecap; pure software only, no Native routing claim.'));print(json.dumps({k:process.get(k) for k in ['status','exit_code','cleanup_complete']}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 else 2)
