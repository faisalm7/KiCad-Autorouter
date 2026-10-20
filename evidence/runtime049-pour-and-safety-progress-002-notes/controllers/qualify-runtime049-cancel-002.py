"""Finite actual Improve CLI cancellation via the production GUI job controller.
Reuse existing owned process-metadata and size helpers; no old PID or OS change.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,argparse,json,threading,hashlib
ap=argparse.ArgumentParser();ap.add_argument('--protocol',required=True);ap.add_argument('--protocol-sha256',required=True);parsed=ap.parse_args()
protocol=Path(parsed.protocol);raw=protocol.read_bytes();assert hashlib.sha256(raw).hexdigest()==parsed.protocol_sha256
plan=json.loads(raw);a=argparse.Namespace(**{key:plan[key] for key in ('runtime','source','output','administration')})
runtime=Path(a.runtime);sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,gui,config as c,floor_route as f,preferences as pref,handoff as h
assert c.ROOT==runtime and Path(sys.prefix).resolve()==runtime/'.venv'
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256'] and p.sha(Path(__file__))==plan['controller_sha256']
admin=Path(a.administration);sys.path.insert(1,str(admin));from scripts.native_cancellation import process_metadata,output_bytes
helper=admin/'scripts/native_cancellation.py';helperpin=p.sha(helper);selfpin=p.sha(Path(__file__));tools=p.tool_manifest()
source=h.real_path(a.source);hashes=p.tree_hash(source.parent);out=h.real_path(a.output,existing=False)
assert out.parent==runtime/'.runs' and out.name.startswith('native7-control-') and not out.exists()
assert source.parent!=out and source.parent not in out.parents and out not in source.parent.parents
out.mkdir(mode=0o700);owner={};h.capture_destination(owner,out)
settings=dict(pref.DEFAULTS,profile='tuned',seconds=90);flow=gui.Request(str(source),str(out),json.dumps(settings),True,'improve').prepare()
report=dict(schema=1,status='failed',accepted=False,production_admitted=False,control_passed=False,project_complete=False,actual_GUI=False,human_review=False,source=str(source),source_hashes=hashes,tools=tools,workspace=str(flow.workspace),settings=settings,whole_wall_full_CPU_seconds=120,helper_sha256=helperpin,controller_sha256=selfpin,scope='Actual single Improve engine-stage SIGINT via production CliJob.cancel. No actual GUI, all-phase/natural-late cancellation, persistent descendant monitor or final-route acceptance claim.')
job=None;thread=None;observed=None;result={}
def remaining():return min(115-(time.monotonic()-START),115-(cpu()-CPU0))
try:
 preview=gui.CliJob();log=out/'preview.log';process=preview.run(flow.command('preview'),log,timeout=min(30,remaining()));preview.adopt(flow,'preview',process,log)
 job=gui.CliJob();log=out/'cancel.log';command=flow.command('route')
 def execute():
  try:result['process']=job.run(command,log,timeout=max(.001,remaining()))
  except BaseException as exc:result['error']=type(exc).__name__+': '+str(exc)
 thread=threading.Thread(target=execute);thread.start()
 engine_log=flow.workspace/'route/incumbent/engine.log';engine_process=engine_log.with_name('engine-process.json')
 deadline=time.monotonic()+min(60,remaining()-15)
 while thread.is_alive() and time.monotonic()<deadline:
  output_bytes(out)
  if engine_log.is_file() and engine_log.stat().st_size and not engine_process.exists() and job.process is not None and job.process.poll() is None:
   rows=[row for row in process_metadata(parent_pid=job.process.pid) if row['pid']==row['pgid']]
   if len(rows)==1:
    observed=rows[0];report['observed_owned_engine']=observed;report['engine_log_bytes_at_signal']=engine_log.stat().st_size;report['signal_elapsed_seconds']=time.monotonic()-START;job.cancel();break
  time.sleep(.01)
 if observed is None:raise AssertionError('No still-running owned engine observed; no cancellation pass inferred')
 thread.join(max(1,remaining()));assert not thread.is_alive(),'CLI cleanup did not finish inside control reserve'
 assert 'error' not in result;process=result['process'];report['process']=process
 assert process['cancel_requested'] is True and process['exit_code']==2 and not process['log_truncated']
 parent_path=flow.workspace/'route/result.json';parent=f.read_json(parent_path);engine=f.read_json(engine_process)
 report.update(parent_receipt_sha256=p.sha(parent_path),parent_status=parent.get('status'),parent_accepted=parent.get('accepted'),engine_process=engine)
 assert parent['status']=='cancelled' and parent['accepted'] is False
 assert engine['pid']==observed['pid'] and engine['status']=='cancelled' and engine['cancel_signal']=='SIGINT' and engine['cleanup_complete'] is True
 report['remaining_owned_group']=process_metadata(pgid=observed['pgid']);assert not report['remaining_owned_group']
 try:job.adopt(flow,'route',process,log)
 except ValueError as exc:assert 'cancelled' in str(exc);report['adoption_refusal']=str(exc)
 else:raise AssertionError('Cancelled invocation adopted')
 assert 'route' not in flow.ready and 'route' not in flow.records and flow.choice is None
 try:p.check_result(parent_path)
 except (p.Rejected,ValueError,OSError) as exc:report['central_reader_refusal']=type(exc).__name__+': '+str(exc)
 else:raise AssertionError('Cancelled parent accepted')
 assert not any((flow.workspace/name).exists() for name in ('review','choice','export'))
 assert p.tree_hash(source.parent)==hashes and p.tool_manifest()==tools and p.sha(helper)==helperpin and p.sha(Path(__file__))==selfpin
 assert protocol.read_bytes()==raw and p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']
 assert h.owned_destination(owner)==out
 report.update(control_passed=True,status='completed')
except (Exception,KeyboardInterrupt) as exc:report['error']=type(exc).__name__+': '+str(exc)
finally:
 if thread is not None and thread.is_alive():
  job.cancel();thread.join(max(1,120-(time.monotonic()-START)))
  if thread.is_alive():report.update(control_passed=False,status='cleanup_unproved')
 report.update(wall_seconds=time.monotonic()-START,total_cpu_seconds=cpu()-CPU0,external_exit_required=True)
 if max(report['wall_seconds'],report['total_cpu_seconds'])+2>120:report.update(control_passed=False,status='budget_exceeded')
 p.save_json(out/'result.json',report)
print(json.dumps(dict(control_passed=report['control_passed'],status=report['status'],error=report.get('error'))));raise SystemExit(0 if report['control_passed'] else 2)
