"""New longer-budget baseline probe; original 120-second failure is retained."""
from pathlib import Path
import datetime,json,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
from scripts import experiment_quality as q
specpath=ROOT/'.runs/cellscan-b1-budget240-001-protocol.json'
spec=f.read_json(specpath)
def stable():
    q.verify_freeze(spec['freeze'],Path(spec['source']))
    for name,pin in spec['artifacts'].items():
        if p.sha(Path(name))!=pin:raise p.Rejected('completed prefix or controller changed')
if sys.argv[1:]==['--inner']:
    stable()
    result=p.route(Path(spec['source']),ROOT/'.runs/cellscan-b1-budget240-001/trial',spec['assigned_inner_seconds'],False,'both','standard')
    stable()
    print(json.dumps({k:result.get(k) for k in ('status','accepted','reason','metrics')}))
    raise SystemExit(0 if result.get('accepted') else 2)
start=time.monotonic();cpu=time.process_time()+f.child_cpu()
out=ROOT/'.runs/cellscan-b1-budget240-001';out.mkdir()
stable()
process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--inner'],cwd=out,log=out/'command.log',
    timeout=spec['remaining_wall_seconds']-(time.monotonic()-start),max_log_bytes=256*1024,max_workdir_bytes=64*1024**2,max_group_rss_bytes=2*1024**3)
wall=time.monotonic()-start;cost=time.process_time()+f.child_cpu()-cpu
record=dict(schema=1,process=process,protocol_sha256=p.sha(specpath),wrapper_sha256=p.sha(Path(__file__)),
    whole_new_wall_seconds=wall,whole_new_full_cpu_seconds=cost,already_committed_charge=spec['already_committed_charge'],
    combined_charged_wall_seconds=spec['already_committed_charge']['wall_seconds']+wall,
    combined_charged_full_cpu_seconds=spec['already_committed_charge']['full_cpu_seconds']+cost,
    finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),old120_result_unchanged=True,
    comparison_eligible=False,claims_limit=spec['claims_limit'])
record['within_cumulative240_caps']=max(record['combined_charged_wall_seconds'],record['combined_charged_full_cpu_seconds'])<=240
stable();p.save_json(out/'execution.json',record)
print(json.dumps({k:record[k] for k in ('combined_charged_wall_seconds','combined_charged_full_cpu_seconds','within_cumulative240_caps')}))
raise SystemExit(0 if process['status']=='success' and process['exit_code'] in (0,2) and process['cleanup_complete'] and record['within_cumulative240_caps'] else 2)
