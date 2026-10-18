"""One frozen functional recovery/delivery using existing product helpers."""
from pathlib import Path
import argparse,sys,time,resource,json
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--runtime',required=True);ap.add_argument('--protocol',required=True);ap.add_argument('--protocol-sha256',required=True);ap.add_argument('--case',choices=('native7','legacy0'),required=True);a=ap.parse_args();runtime=Path(a.runtime);sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,gui,handoff as h,floor_route as f,review_export as ex,preferences as pref
assert c.ROOT==runtime and Path(sys.prefix).resolve()==runtime/'.venv'
protocol=Path(a.protocol);assert p.sha(protocol)==a.protocol_sha256;plan=f.read_json(protocol);case=plan['cases'][a.case];assert case['runtime']==str(runtime) and c.NATIVE_VERSION==case['native_version'];assert p.sha(Path(__file__))==plan['controller_sha256']
source=Path(plan['source']);out=Path(case['output']);tools=p.tool_manifest();assert tools['implementation_sha256']==plan['implementation_sha256'] and tools['git_head']==plan['source_head'];assert p.tree_hash(source.parent)==plan['source_hashes'];p.check_storage(active_root=out);out.mkdir();owner={};h.capture_destination(owner,out)
if runtime!=ROOT:assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']
settings=dict(pref.DEFAULTS,seconds=plan['routing_seconds'],adapter='both',profile='standard');flow=gui.Request(str(source),str(out),json.dumps(settings),True).prepare();processes=[]
report=dict(schema=1,kind='actual-fixed-thermal-parent-functional-delivery',case=a.case,accepted=False,project_complete=False,workflow_delivered=False,status='failed',actual_GUI=False,human_review=False,protocol_sha256=a.protocol_sha256,tools=tools,source=str(source),source_hashes=plan['source_hashes'],workspace=str(flow.workspace),processes=processes,routing_seconds=plan['routing_seconds'],export_seconds=plan['export_seconds'],whole_budget_seconds=plan['whole_budget_seconds'],scope='One exposed licensed functional method.0completion-only/7standard fixed incumbent; no comparative, GUI, broad/electrical or release claim. All actualconversion/attempt/selection/validation/delivery charged.')
def left():return min(plan['whole_budget_seconds']-(time.monotonic()-START),plan['whole_budget_seconds']-(cpu()-CPU0))-15
def fresh():
 flow.fresh();assert h.owned_destination(owner)==out and p.tool_manifest()==tools and p.sha(protocol)==a.protocol_sha256 and p.sha(Path(__file__))==plan['controller_sha256'] and p.tree_hash(source.parent)==plan['source_hashes'];assert left()>0
python=[str(runtime/'.venv/bin/python'),'-B','-m','autorouter']
def cli(stage,arguments,bound,adopt=False):
 fresh();job=gui.CliJob();log=out/(stage+'.log');process=job.run(arguments,log,timeout=min(bound,left()));processes.append(dict(stage=stage,process=process,log_sha256=p.sha(log)))
 if adopt:job.adopt(flow,stage,process,log)
 elif process['exit_code']!=0 or process['cancel_requested'] or process['log_truncated']:raise p.Rejected('actualCLI failed/cancelled: '+stage)
 fresh();return process
route=out/'thermal-route/result.json';export=out/'export/export.json'
try:
 cli('preview',flow.command('preview'),60,True)
 begin=time.monotonic();begin_cpu=cpu()
 cli('thermal_route',python+['recover',str(source),'--seconds',str(plan['routing_seconds']),'--output',str(route.parent)],plan['routing_seconds']+15)
 p.check_result(route)
 report.update(method_wall_seconds=time.monotonic()-begin,method_full_CPU_seconds=cpu()-begin_cpu)
 for stage,args,bound in [('review',['review-copy',str(route),'--render','--output',str(out/'review')],60),('choice',['review-choice',str(out/'review/review.json'),'--choice','accept','--output',str(out/'choice')],60),('export',['review-export',str(out/'choice/choice.json'),'--seconds',str(plan['export_seconds']),'--output',str(export.parent)],plan['export_seconds']+15),('verify_export',['review-export-check',str(export)],60)]:cli(stage,python+args,bound)
 with p.validation_readback_session():
  report['route_readback']=p.check_result(route);report['export_readback']=ex.check_export(export)
 assert report['route_readback']['current'] and report['export_readback']['current'];fresh();report.update(workflow_delivered=True,status='completed',export_receipt=str(export),export_sha256=p.sha(export))
except (Exception,KeyboardInterrupt) as exc:report.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',reason=type(exc).__name__+': '+str(exc),workflow_delivered=False)
if route.is_file():
 r=f.read_json(route);report.update(route_receipt=str(route),route_sha256=p.sha(route),route_status=r.get('status'),route_accepted=r.get('accepted'),native=r.get('native'),metrics=r.get('metrics'),incumbent=r.get('incumbent'),repair=r.get('repair'),recovery_needed=r.get('recovery_needed'),candidate_sha256=r.get('candidate_sha256'),route_reason=r.get('reason'))
try:fresh()
except BaseException as exc:report.update(status='freshness_or_budget_failed',workflow_delivered=False,reason=type(exc).__name__+': '+str(exc))
report.update(sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True,source_originals_unchanged=p.tree_hash(source.parent)==plan['source_hashes'])
p.save_json(out/'result.json',report);print(json.dumps({k:report.get(k) for k in ('case','status','workflow_delivered','reason','route_reason','sampled_wall_seconds','sampled_full_CPU_seconds')}),flush=True)
raise SystemExit(0 if report['workflow_delivered'] and report['status']=='completed' else 2)
