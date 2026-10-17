"""Fresh runtime016 default-production CLI workflow using the installed GUI's shared model.

No actual GUI interaction is claimed. Every stage invokes the shipped CLI and
its original Native/acceptance rules. The frozen runtime is never modified.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,gui,handoff as h,review_export as ex
def execute(protocol,pin):
    plan=f.read_json(protocol)
    if p.sha(protocol)!=pin or c.ROOT!=ROOT or Path(sys.prefix).resolve()!=ROOT/'.venv':raise p.Rejected('frozen curated production runtime required')
    tools=p.tool_manifest()
    if tools!=plan['runtime_tools']:raise p.Rejected('production runtime differs from protocol')
    out=ROOT/'.runs/production-delivery-001';out.mkdir();owner={};h.capture_destination(owner,out)
    source=out/'source';source.mkdir()
    for name,text in plan['fixture_files'].items():
        if Path(name).name!=name:raise p.Rejected('flat owned source required')
        (source/name).write_bytes(text.encode())
    name=plan['board_name']
    if type(name)is not str or Path(name).name!=name or Path(name).suffix!='.kicad_pcb' or name not in plan['fixture_files'] or name not in plan['fixture_sha256']:raise p.Rejected('exact flat owned PCB required')
    board=source/name;hashes=p.tree_hash(source)
    if hashes!=plan['fixture_sha256']:raise p.Rejected('owned fixture changed')
    jobs=out/'jobs';jobs.mkdir()
    flow=gui.Request(str(board),str(jobs),json.dumps(plan['settings']),True).prepare()
    record=dict(schema=1,accepted=False,passed=False,status='failed',actual_GUI=False,human_review=False,
                source_head=plan['source_head'],tools=tools,workspace=str(flow.workspace),protocol_sha256=pin,processes=[])
    helper=Path(plan['signal_bridge_controller'])
    if p.sha(helper)!=plan['signal_bridge_sha256']:raise p.Rejected('frozen signal bridge required')
    spec=importlib.util.spec_from_file_location('frozen_signal_bridge',helper);bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
    job=gui.CliJob()
    def remaining():return min(238-(time.monotonic()-START),238-(cpu()-CPU0))
    def stable():
        live();h.owned_destination(owner)
        if p.sha(protocol)!=pin or p.sha(helper)!=plan['signal_bridge_sha256'] or p.tool_manifest()!=tools or p.tree_hash(source)!=hashes:raise p.Rejected('runtime/protocol/source changed')
        flow.fresh();live()
    with bridge.cancellation_bridge(job)as(queued,live):
        try:
            for stage in ('preview','route','review','choice','export','verify_export'):
                if remaining()<30:raise p.Rejected('whole delivery reserve unavailable')
                log=out/(stage+'.command.log');choice='accept' if stage=='choice' else None
                argv=flow.command(stage,choice=choice)
                process=job.run(argv,log,timeout=min(flow.timeout(stage),remaining()-2))
                p.save_json(out/(stage+'.process.json'),process);record['processes'].append(process)
                job.adopt(flow,stage,process,log,choice=choice);stable()
            route=flow.records['route'];export=flow.records['export']
            if route.get('source')!=str(board) or route.get('source_hashes')!=hashes:raise p.Rejected('route differs from exact owned source')
            for data in(route,export):
                if data['native']['opens']!=0 or data['native']['blocking']!=0 or data['metrics']['version']!='10.0.0':raise p.Rejected('unexpected Native result')
            protected=p.protected_for_record(route,p.sx.read(board))
            if len(protected)!=10:raise p.Rejected('protected copper prediction differs')
            record.update(passed=True,status='completed',source_sha256=hashes,protected_routes=10,native=export['native'],metrics=export['metrics'],
                route_sha256=p.sha(flow.workspace/'route/result.json'),export_sha256=p.sha(flow.workspace/'export/export.json'),
                checked_export=flow.records['verify_export'],whole_project_drc_clean=export['whole_project_drc_clean'],
                qualification='Installed production CLI stages through unchanged GUI model, not actual new GUI qualification; same exposed owned4Cu class family, no new completion/quality or independent-family claim.')
        except(Exception,KeyboardInterrupt)as exc:
            record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt)else'failed',error=type(exc).__name__+': '+str(exc))
        material=f.evidence_inventory(out)
        def fresh():
            stable()
            if f.evidence_inventory(out)!=material:raise p.Rejected('completed delivery material changed')
        def final():
            fresh()
            if record['passed']:ex.check_export(flow.workspace/'export/export.json')
        def account():
            record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
            if remaining()<=0:record.update(passed=False,status='budget_exceeded')
            if queued[0]or job.cancel_requested:record.update(passed=False,status='cancelled')
            if record['status']!='completed':record['passed']=False
        try:
            f.publish(out,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final)
            if record['passed']:live()
        except BaseException as exc:
            def failed():raise exc
            f.publish(out,record,failed,account,remaining,owned=lambda:h.owned_destination(owner))
        print(json.dumps({k:record.get(k)for k in('passed','status','wall_seconds','full_cpu_seconds','error')}))
        return 0 if record['passed'] and record['status']=='completed' else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True);args=parser.parse_args()
    raise SystemExit(execute(args.protocol,args.protocol_sha256))
