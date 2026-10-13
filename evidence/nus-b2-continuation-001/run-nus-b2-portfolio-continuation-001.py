"""Foreground envelope; resumes only predeclared unattempted B2 variants."""
from pathlib import Path
import datetime,json,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
start=time.monotonic();cpu=time.process_time()+f.child_cpu()
out=ROOT/'.runs/nus-b2-portfolio-continuation-001';out.mkdir()
protocol=f.read_json(ROOT/'.runs/nus-b2-portfolio-continuation-001-protocol.json')
assert p.tool_manifest()==protocol['tools']
plan=Path(protocol['resume_plan']);assert p.sha(plan)==protocol['resume_plan_sha256']
budget=protocol['same_arm_allowance_seconds'];prior=protocol['prior_entire_invocation']
argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/experiment_portfolio.py'),
 '--project','nus-usb-led','--budget',repr(budget),'--resume-plan',str(plan),
 '--resume-plan-sha256',protocol['resume_plan_sha256'],'--output',str(out/'portfolio')]
timeout=budget-prior['wall_seconds']-(time.monotonic()-start)
assert timeout>0
process=run(argv,cwd=out,log=out/'command.log',timeout=timeout,max_log_bytes=256*1024,
 max_workdir_bytes=64*1024**2,max_group_rss_bytes=2*1024**3)
wall=time.monotonic()-start;cost=time.process_time()+f.child_cpu()-cpu
record={'schema':1,'status':'executed','process':process,'protocol_sha256':p.sha(ROOT/'.runs/nus-b2-portfolio-continuation-001-protocol.json'),
 'whole_new_wall_seconds':wall,'whole_new_full_cpu_seconds':cost,
 'prior_entire_invocation':prior,'combined_active_wall_seconds':prior['wall_seconds']+wall,
 'combined_full_cpu_seconds':prior['full_cpu_seconds']+cost,'same_arm_allowance_seconds':budget,
 'within_enclosing_budget':prior['wall_seconds']+wall<=budget and prior['full_cpu_seconds']+cost<=budget,
 'calendar_gap':'Prior invocation completed before C; active-work wall reported separately from uninterrupted elapsed calendar time.',
 'new_native_variants':['via_low','via_high'],'retained_default_rerun':False,
 'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'accounting_point':'Whole foreground process including new startup/publication; later additive all-arm readback/publication needs its own charge.'}
p.save_json(out/'execution.json',record)
print(json.dumps({k:record[k] for k in ('combined_active_wall_seconds','combined_full_cpu_seconds','within_enclosing_budget')}))
raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and record['within_enclosing_budget'] else 2)
