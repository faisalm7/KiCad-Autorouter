"""One bounded actual task-connectivity falsification; no engine or acceptance."""
from pathlib import Path
import argparse, json, shutil, sys, time, signal
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, board_floor as g, native_connected as nc
from autorouter import handoff as h, placement_clearance as pc, sexpr as sx
from scripts.experiment_quality import selected_source
SECONDS=60

def account_probe(record,job,started,cpu,remaining):
    record.update(steps=job.steps,wall_seconds=time.monotonic()-started,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu,within_budget=remaining()>0)
    if not record['within_budget']:record.update(status='budget_exceeded')
    if record['status']!='completed':record['eligibility_qualified']=False

def experiment(output):
    started=time.monotonic();cpu=time.process_time()+f.child_cpu()
    if output.parent!=ROOT/'.runs' or output.exists() or output.is_symlink():raise p.Rejected('fresh direct .runs output required')
    source,family=selected_source('nus-usb-led');original=p.preflight(source);hashes=p.tree_hash(source.parent)
    tools=p.tool_manifest();code={str(x.relative_to(ROOT)):p.sha(x) for x in Path(__file__).parent.glob('*.py')}
    p.check_storage();job=p.Job(output,SECONDS);job.started=started;job.deadline=started+SECONDS
    owner={};h.capture_destination(owner,output);completed=None
    record=dict(schema=1,kind='native-task-connectivity-probe',status='incomplete',accepted=False,routing_executed=False,
                eligibility_qualified=False,production_admitted=False,source=str(source),source_hashes=hashes,family=family,tools=tools,
                code_sha256=code,budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,
                scope='Fresh whole-board stripped task and saved native refill only; no engine, original-route feature or routing/quality/generalization claim.')
    def remaining():return max(0,min(SECONDS-(time.monotonic()-started),SECONDS-(time.process_time()+f.child_cpu()-cpu)))
    def stable():
        h.owned_destination(owner)
        if remaining()<=0:raise p.Rejected('task-probe wall/fullCPU cap exhausted')
        if p.tool_manifest()!=tools or p.tree_hash(source.parent)!=hashes:raise p.Rejected('task-probe source/runtime changed')
        if any(p.sha(ROOT/name)!=pin for name,pin in code.items()):raise p.Rejected('task-probe driver changed')
        if p.tree_hash(output/'snapshot')!=hashes:raise p.Rejected('task-probe snapshot changed')
        if completed is not None and f.evidence_inventory(output)!=completed:raise p.Rejected('task-probe completed evidence changed')
    def account():
        account_probe(record,job,started,cpu,remaining)
    def readback():
        if record['eligibility_qualified']:
            nc.readback(output,record,source,task,refill,candidate,output/'native.dsn')
        stable()
    try:
        shutil.copytree(source.parent,output/'snapshot');shutil.copytree(source.parent,output/'task')
        task=output/'task'/source.name
        sx.write(task,g.task_from_source(original))
        before=p.tree_hash(task.parent);stable()
        shutil.copytree(task.parent,output/'candidate');candidate=output/'candidate'/source.name
        digest,native=p.validate_candidate(job,sx.read(task),candidate,before,[])
        refill=output/'refill'/source.name
        record['task_native']=native
        record['task_native_report_sha256']=p.sha(output/'final-drc.json')
        record['original_shell_sha256']=digest
        record['native_witness']='saved-refill-and-final-original-shell-v1'
        record['saved_nonfill_ast_equal']=p.immutable(sx.read(task))==p.immutable(sx.read(refill))
        record['saved_route_records_equal']=p.routes(sx.read(task))==p.routes(sx.read(refill))
        job.native('task-export','export',task,output/'native.dsn')
        f.process_check(output,{'steps':job.steps},'task-export',[str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'export',str(task),str(output/'native.dsn')])
        if p.tree_hash(task.parent)!=before:raise p.Rejected('task export modified original task project')
        classification=nc.derive(pc.read_bytes(source),pc.read_bytes(task),pc.read_bytes(candidate),native,pc.read_bytes(output/'native.dsn',20*1024**2),hashes,source_name=source.name,report_sha256=record['task_native_report_sha256'])
        p.save_json(output/nc.RECORD_FILE,classification);record['native_connected_classification']=classification
        record.update(status='completed',eligibility_qualified=True,steps=job.steps)
        readback()
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',eligibility_qualified=False,reason=type(exc).__name__+': '+str(exc),initial_failure=type(exc).__name__+': '+str(exc))
    completed=f.evidence_inventory(output);record['completed_evidence']=completed
    f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=readback)
    print(json.dumps({k:record.get(k)for k in ('status','eligibility_qualified','reason','wall_seconds','total_cpu_seconds')}))
    return record['status']=='completed' and record['eligibility_qualified']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if not args.run_native:parser.error('explicit --run-native required')
    def interrupted(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    raise SystemExit(0 if experiment(args.output) else 2)
