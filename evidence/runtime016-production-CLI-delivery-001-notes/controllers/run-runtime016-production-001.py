"""Finite existing-CliJob enclosure for the frozen installed production workflow."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,importlib.util,json,os,stat,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,gui
spec=importlib.util.spec_from_file_location('existing_bridge',ROOT/'.runs/run-native1007-delivery-004.py');bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
def execute(pin):
    base=ROOT/'.runs/runtime-directory-016';runtime=base/'runtime';protocol=base/'production-delivery-protocol-001.json';plan=f.read_json(protocol)
    if p.sha(protocol)!=pin or p.sha(runtime/'runtime-distribution.json')!=plan['runtime_manifest_sha256']:raise p.Rejected('frozen production protocol/runtime required')
    child=runtime/'.runs/qualify-runtime016-production-001.py'
    if p.sha(child)!=plan['child_sha256']:raise p.Rejected('production driver changed')
    out=base/'production-delivery-execution-001';out.mkdir();owner={};h.capture_destination(owner,out);job=gui.CliJob()
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with bridge.cancellation_bridge(job)as(queued,live),os.fdopen(fd,'r+')as lane:
        info=os.fstat(lane.fileno())
        if not stat.S_ISREG(info.st_mode)or info.st_nlink!=1:raise p.Rejected('ordinary shared Native lane required')
        fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
        process=job.run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B',str(child),'--protocol',str(protocol),'--protocol-sha256',pin],out/'command.log',timeout=245)
        receipt=runtime/'.runs/production-delivery-001/result.json';row=f.read_json(receipt)if receipt.exists()else None
        material=f.evidence_inventory(runtime/'.runs/production-delivery-001');logpin=p.sha(out/'command.log')
        passed=bool(row and row.get('passed')is True and row.get('status')=='completed' and row.get('tools')==plan['runtime_tools'] and process['exit_code']==0 and not process['cancel_requested'] and not process['log_truncated'])
        record=dict(schema=1,accepted=False,passed=passed,status='completed'if passed else'failed',source_head=plan['source_head'],protocol_sha256=pin,process=process,child=row,scope=plan['scope'])
        def remaining():return min(258-(time.monotonic()-START),258-(cpu()-CPU0))
        def fresh():
            if record['passed']:live()
            h.owned_destination(owner)
            if p.sha(protocol)!=pin or p.sha(child)!=plan['child_sha256']or f.evidence_inventory(runtime/'.runs/production-delivery-001')!=material or p.sha(out/'command.log')!=logpin:raise p.Rejected('completed production workflow changed')
            if record['passed']:live()
        def account():
            record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
            if remaining()<=0:record.update(passed=False,status='budget_exceeded')
            if queued[0]or job.cancel_requested:record.update(passed=False,status='cancelled')
            if record['status']!='completed':record['passed']=False
        try:
            f.publish(out,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=fresh)
            if record['passed']:live()
        except BaseException as exc:
            def failed():raise exc
            f.publish(out,record,failed,account,remaining,owned=lambda:h.owned_destination(owner))
        print(json.dumps({k:record.get(k)for k in('passed','status','wall_seconds','full_cpu_seconds')}))
        return 0 if record['passed']and record['status']=='completed'else 2
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--protocol-sha256',required=True);args=parser.parse_args();raise SystemExit(execute(args.protocol_sha256))
