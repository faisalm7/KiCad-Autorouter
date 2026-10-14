"""One unattempted high-cost trial, bounded by all inherited comparison costs."""
from pathlib import Path
import datetime,json,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
from scripts import experiment_quality as q
specpath=ROOT/'.runs/arcdice-b2-high-only-001-protocol.json'
spec=f.read_json(specpath)
if sys.argv[1:]==['--inner']:
    board=Path(spec['source']);q.verify_freeze(spec['freeze'],board)
    for name,pin in spec['artifacts'].items():assert p.sha(Path(name))==pin
    result=p.route(board,ROOT/'.runs/arcdice-b2-high-only-001/trial',spec['assigned_inner_seconds'],False,'both','tuned',scoring_variant='via_high')
    print(json.dumps({k:result.get(k) for k in ('status','accepted','reason')}))
    raise SystemExit(0 if result.get('accepted') else 2)
start=time.monotonic();cpu=time.process_time()+f.child_cpu()
out=ROOT/'.runs/arcdice-b2-high-only-001';out.mkdir()
q.verify_freeze(spec['freeze'],Path(spec['source']))
for name,pin in spec['artifacts'].items():assert p.sha(Path(name))==pin
argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--inner']
timeout=spec['inherited_remaining_wall_seconds']-(time.monotonic()-start)
assert timeout>0
process=run(argv,cwd=out,log=out/'command.log',timeout=timeout,max_log_bytes=256*1024,
    max_workdir_bytes=64*1024**2,max_group_rss_bytes=2*1024**3)
wall=time.monotonic()-start;cost=time.process_time()+f.child_cpu()-cpu
record={'schema':1,'process':process,'protocol_sha256':p.sha(specpath),'wrapper_sha256':p.sha(Path(__file__)),
    'whole_new_wall_seconds':wall,'whole_new_full_cpu_seconds':cost,'already_committed_charge':spec['already_committed_charge'],
    'combined_charged_wall_seconds':spec['already_committed_charge']['wall_seconds']+wall,
    'combined_charged_full_cpu_seconds':spec['already_committed_charge']['full_cpu_seconds']+cost,
    'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'original_completed_native_repeated':False,'nominal_planning_never_exempts_full120_caps':True,
    'small_receipt_publication_covered_by_separate_startup_charge':True}
record['within_full120_caps']=max(record['combined_charged_wall_seconds'],record['combined_charged_full_cpu_seconds'])<=120.
p.save_json(out/'execution.json',record)
print(json.dumps({k:record[k] for k in ('combined_charged_wall_seconds','combined_charged_full_cpu_seconds','within_full120_caps')}))
raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and record['within_full120_caps'] else 2)
