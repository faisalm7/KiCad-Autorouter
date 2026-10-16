"""Existing production controller qualification in one curated runtime; no wx."""
import argparse,json,resource,sys,time,threading
from pathlib import Path
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
ap=argparse.ArgumentParser();ap.add_argument('--runtime',required=True);ap.add_argument('--source',required=True);ap.add_argument('--output',required=True);ap.add_argument('--method',choices=['route','improve'],required=True);a=ap.parse_args()
runtime=Path(a.runtime);sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,gui,handoff as h,floor_route as f,preferences as pref,review_export as ex,provenance as pv
assert c.ROOT==runtime and Path(sys.prefix).resolve()==runtime/'.venv'
source=Path(a.source);original=p.tree_hash(source.parent);tools=p.tool_manifest();assert tools['source_provenance']['kind']==pv.KIND
out=Path(a.output);out.mkdir();owner={};h.capture_destination(owner,out);selfpin=p.sha(Path(__file__))
settings=dict(pref.DEFAULTS,seconds=90)
if a.method=='improve':settings=gui.improve_preset(settings)
def fresh():
 assert p.sha(Path(__file__))==selfpin and p.tree_hash(source.parent)==original and p.tool_manifest()==tools
 assert h.owned_destination(owner)==out
 for name,module in tuple(sys.modules.items()):
  if name.split('.')[0]=='autorouter' and getattr(module,'__file__',None):assert Path(module.__file__).resolve().is_relative_to(runtime),name
fresh();flow=gui.Request(str(source),str(out),json.dumps(settings),True,a.method).prepare();processes=[]
report=dict(schema=1,accepted=False,workflow_delivered=False,status='failed',actual_GUI=False,human_review=False,method=a.method,source=str(source),source_hashes=original,tools=tools,settings=settings,workspace=str(flow.workspace),driver_sha256=selfpin,processes=processes,whole_budget_seconds=240,scope='New curated runtime using actual production Request/Workflow/CliJob/CLI and native proof readers, owned complete schematic and protected copper. SOFTWARE TEST accept intent; no actual window/human/comparative/standalone claim.')
try:
 for stage in ('preview','route','review','choice','export','verify_export'):
  fresh();left=min(225-(time.monotonic()-START),225-(cpu()-CPU0));assert left>1,'delivery reserve exhausted'
  choice='accept' if stage=='choice' else None;job=gui.CliJob();log=out/(stage+'.log')
  process=job.run(flow.command(stage,choice=choice),log,timeout=min(flow.timeout(stage),left));processes.append(dict(stage=stage,process=process,log_sha256=p.sha(log)))
  job.adopt(flow,stage,process,log,choice=choice)
 inspected={}
 def inspect():
  try:inspected['target']=str(flow.inspect_path('export',job=gui.CliJob()))
  except BaseException as exc:inspected['error']=type(exc).__name__+': '+str(exc)
 thread=threading.Thread(target=inspect);thread.start();thread.join(90);assert not thread.is_alive()
 assert 'error' not in inspected and inspected['target']==str(flow.records['export']['project_file'])
 with p.validation_readback_session():
  report['route_readback']=p.check_result(flow.workspace/'route/result.json')
  report['export_readback']=ex.check_export(flow.workspace/'export/export.json')
 assert report['route_readback']['current'] is True and report['export_readback']['current'] is True
 report.update(workflow_delivered=True,status='completed',background_inspection=inspected)
except (Exception,KeyboardInterrupt) as exc:
 report.update(workflow_delivered=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc))
route=flow.workspace/'route/result.json'
if route.is_file():
 data=f.read_json(route);report.update(route_receipt_sha256=p.sha(route),route_status=data.get('status'),native=data.get('native'),metrics=data.get('metrics'),candidate_sha256=data.get('candidate_sha256'))
try:fresh()
except BaseException as exc:report.update(workflow_delivered=False,status='freshness_failed',error=str(exc))
report.update(sampled_wall_seconds=time.monotonic()-START,sampled_full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2,external_exit_required=True)
if max(report['sampled_wall_seconds'],report['sampled_full_cpu_seconds'])+2>240:report.update(workflow_delivered=False,status='budget_exceeded')
p.save_json(out/'result.json',report)
raise SystemExit(0 if report['workflow_delivered'] and report['status']=='completed' else 2)
