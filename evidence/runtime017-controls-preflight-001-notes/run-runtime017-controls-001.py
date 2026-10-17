"""Finite017 failure-control enclosure using reviewed017/pair helper functions."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,hashlib,importlib.util,json,os,re,stat,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,gui,provenance as pv
BASE=ROOT/'.runs/runtime-directory-017'
PRODUCTION_OUTER=ROOT/'.runs/run-runtime017-production-001.py'
PRODUCTION_OUTER_PIN='c8474903c6cbfd66b09965474383be8193b4b1156574cd7facdbb3664719a72f'
CHILD_KIND='installed-runtime017-failure-controls-v1'

def require(value,reason):
    if not value:raise p.Rejected(reason)

def production_helper():
    require(p.sha(PRODUCTION_OUTER)==PRODUCTION_OUTER_PIN,'reviewed017 production enclosure helper changed')
    spec=importlib.util.spec_from_file_location('reviewed017_enclosure',PRODUCTION_OUTER);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    require(p.sha(PRODUCTION_OUTER)==PRODUCTION_OUTER_PIN,'production helper changed during import')
    return module

def frozen(protocol,pin,prod,shared):
    plan=f.read_json(protocol)
    require(p.sha(protocol)==pin and plan.get('status')=='frozen'and plan.get('kind')=='runtime017-failure-controls-protocol-v1'
        and plan['outer_controller_sha256']==p.sha(Path(__file__)),'exact frozen017 controls protocol/controller required')
    require(plan['controls']==['class_mismatch_before_engine','same_original_native_short','real_engine_cancel']and
        plan['limits']==dict(child_wall_full_cpu_seconds=238,child_watchdog_seconds=245,outer_wall_full_cpu_seconds=258,external_wall_full_cpu_seconds=260),'exact finite three-control scope/envelope required')
    require(plan['production_outer_sha256']==p.sha(PRODUCTION_OUTER)==PRODUCTION_OUTER_PIN,'reviewed production helper changed')
    require(type(plan['positive_receipt_sha256'])is str and re.fullmatch('[0-9a-f]{64}',plan['positive_receipt_sha256'])
        and type(plan['production_protocol_sha256'])is str and re.fullmatch('[0-9a-f]{64}',plan['production_protocol_sha256']),'actual positive/protocol pins must replace prospective placeholders')
    production=prod.frozen(Path(plan['production_protocol']),plan['production_protocol_sha256'],shared)
    for key in ('runtime','source_head','runtime_manifest_sha256','runtime_tools','runtime_python','coordinator_tools','coordinator_python',
            'shared_pair_helper','shared_pair_helper_sha256','signal_bridge_controller','signal_bridge_sha256'):
        require(plan[key]==production[key],'controls must use exact production context: '+key)
    runtime=Path(plan['runtime']);child=runtime/'.runs'/plan['installed_child_name']
    require(p.sha(child)==plan['child_sha256'],'exact installed failure-control child required')
    raw,positive,error=prod.read_child(Path(plan['positive_receipt']),plan['production_protocol_sha256'])
    require(error is None and raw is not None and hashlib.sha256(raw).hexdigest()==plan['positive_receipt_sha256']
        and positive.get('passed')is True and positive.get('status')=='completed'and positive.get('accepted')is False
        and positive.get('tools')==plan['runtime_tools']and positive.get('python_context')==plan['runtime_python'],'actual completed0174Cu positive prerequisite differs')
    enclosure=f.read_json(Path(plan['positive_enclosure']))
    require(p.sha(Path(plan['positive_enclosure']))==plan['positive_enclosure_sha256']and enclosure.get('kind')=='runtime017-four-cu-production-enclosure-v1'
        and enclosure.get('passed')is True and enclosure.get('status')=='completed'and enclosure.get('accepted')is False
        and enclosure.get('protocol_sha256')==plan['production_protocol_sha256']and enclosure.get('child_receipt_sha256')==plan['positive_receipt_sha256']
        and enclosure['process']['exit_code']==0 and not enclosure['process']['cancel_requested']and not enclosure['process']['log_truncated'],'actual reaped0174Cu positive enclosure differs')
    require(p.tree_hash(Path(plan['mismatch_source']).parent)==plan['mismatch_source_hashes'],'retained exact mismatch packet changed')
    for path,digest in plan['prerequisite_sha256'].items():require(p.sha(Path(path))==digest,'controls prerequisite changed: '+path)
    return plan

def read_child(receipt,pin):
    if not os.path.lexists(receipt):return None,None,None
    raw=pv.read_bytes(receipt,8*1024**2)
    try:
        row=json.loads(raw,object_pairs_hook=pv._strict_object,parse_constant=lambda value:(_ for _ in()).throw(ValueError('invalid JSON constant')))
        require(type(row)is dict and row.get('schema')==1 and row.get('kind')==CHILD_KIND and row.get('protocol_sha256')==pin,'controls child kind/protocol identity differs')
    except Exception as exc:return raw,None,type(exc).__name__+': '+str(exc)
    return raw,row,None

def execute(protocol,pin):
    prod=production_helper();shared=prod.shared_helpers();plan=frozen(protocol,pin,prod,shared);runtime=Path(plan['runtime']);child=runtime/'.runs'/plan['installed_child_name']
    out=BASE/'failure-controls-execution-001';out.mkdir();owner={};h.capture_destination(owner,out);job=gui.CliJob()
    helper=Path(plan['signal_bridge_controller']);spec=importlib.util.spec_from_file_location('retained017_controls_bridge',helper);bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with bridge.cancellation_bridge(job)as(queued,live),os.fdopen(fd,'r+')as lane:
        info=os.fstat(lane.fileno());require(stat.S_ISREG(info.st_mode)and info.st_nlink==1,'ordinary shared Native lane required')
        fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
        process=job.run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B',str(child),'--protocol',str(protocol),'--protocol-sha256',pin],out/'command.log',timeout=245)
        receipt=runtime/'.runs/failure-controls-001/result.json';raw=None;row=None;error=None
        try:raw,row,error=read_child(receipt,pin)
        except Exception as exc:error=type(exc).__name__+': '+str(exc)
        material=f.evidence_inventory(receipt.parent)if receipt.parent.is_dir()else None;logpin=p.sha(out/'command.log')
        passed=bool(row and row.get('passed')is True and row.get('controls_passed')is True and row.get('status')=='completed'and row.get('accepted')is False
            and row.get('source_head')==plan['source_head']and row.get('tools')==plan['runtime_tools']and row.get('python_context')==plan['runtime_python']
            and [item.get('name')for item in row.get('checks',[])]==plan['controls']and all(item.get('passed')is True for item in row['checks'])
            and process['exit_code']==0 and not process['cancel_requested']and not process['log_truncated'])
        record=dict(schema=1,kind='runtime017-failure-controls-enclosure-v1',accepted=False,passed=passed,controls_passed=passed,status='completed'if passed else'failed',
            source_head=plan['source_head'],protocol_sha256=pin,process=process,child=row,scope=plan['scope'],coordinator_tools=p.tool_manifest(),
            coordinator_python=shared.coordinator_python_context(),child_receipt=str(receipt),child_receipt_error=error,
            child_receipt_sha256=None if raw is None else hashlib.sha256(raw).hexdigest(),child_receipt_bytes=None if raw is None else len(raw),
            accounting_point='Inner sample includes reaped child. External complete command wall and user+systemCPU<=260s remain mandatory; preparation/review costs are separate.')
        def remaining():return min(258-(time.monotonic()-START),258-(cpu()-CPU0))
        def fresh():
            if record['passed']:live()
            h.owned_destination(owner);frozen(protocol,pin,prod,shared)
            require((f.evidence_inventory(receipt.parent)if receipt.parent.is_dir()else None)==material and p.sha(out/'command.log')==logpin,'completed controls material changed')
            shared.child_bytes_fresh(receipt,raw)
            if record['passed']:live()
        def account():
            record.update(inner_sample_wall_seconds=time.monotonic()-START,inner_sample_full_cpu_seconds=cpu()-CPU0)
            if remaining()<=0:record.update(passed=False,controls_passed=False,status='budget_exceeded')
            if queued[0]or job.cancel_requested:record.update(passed=False,controls_passed=False,status='cancelled')
            if record['status']!='completed':record.update(passed=False,controls_passed=False)
        def final():fresh();require(remaining()>0,'whole controls enclosure deadline exhausted')
        try:
            f.publish(out,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final)
            if record['passed']:fresh();live();shared.child_bytes_fresh(receipt,raw);require(remaining()>0,'whole controls deadline exhausted after publication')
        except BaseException as exc:
            def failed():raise exc
            f.publish(out,record,failed,account,remaining,owned=lambda:h.owned_destination(owner))
        print(json.dumps({key:record.get(key)for key in('passed','controls_passed','status','inner_sample_wall_seconds','inner_sample_full_cpu_seconds')}))
        return 0 if record['passed']and record['controls_passed']and record['status']=='completed'else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True);args=parser.parse_args()
    raise SystemExit(execute(args.protocol.resolve(),args.protocol_sha256))
