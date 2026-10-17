"""One bounded0184Cu delivery enclosure; reused016 runner and frozen pair helpers."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,hashlib,importlib.util,json,os,stat,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,gui,provenance as pv
BASE=ROOT/'.runs/runtime-directory-018'
SHARED=ROOT/'.runs/named-edge-installed-pair-001/run-installed-arm.py'
SHARED_PIN='c412dc76a66bea20b52a071ce6b0de255047d817f5c432a3dbc7d287dc81e12e'
CHILD_KIND='installed-runtime018-production-four-cu-v1'

def require(value,reason):
    if not value:raise p.Rejected(reason)

def shared_helpers():
    require(p.sha(SHARED)==SHARED_PIN,'retained frozen pair helper changed')
    spec=importlib.util.spec_from_file_location('retained_pair_helpers018',SHARED);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    require(p.sha(SHARED)==SHARED_PIN,'retained helper changed during import')
    return module

def frozen(protocol,pin,shared):
    plan=f.read_json(protocol)
    require(p.sha(protocol)==pin and plan.get('status')=='frozen'and plan.get('kind')=='runtime018-four-cu-production-protocol-v1'
        and plan['outer_controller_sha256']==p.sha(Path(__file__)),'exact frozen018 protocol/controller required')
    require(Path(plan['shared_pair_helper'])==SHARED and plan['shared_pair_helper_sha256']==p.sha(SHARED)==SHARED_PIN,'frozen shared helper changed')
    require(plan['limits']==dict(child_wall_full_cpu_seconds=238,child_watchdog_seconds=245,outer_wall_full_cpu_seconds=258,external_wall_full_cpu_seconds=260),'unchanged016 budget envelope required')
    coordinator=p.tool_manifest();actual_python=shared.coordinator_python_context()
    require(len(coordinator['implementation_sha256'])==44 and shared.selected_tools(coordinator)==shared.selected_tools(plan['coordinator_tools'])
        and coordinator['implementation_sha256']==plan['runtime_tools']['implementation_sha256'],'coordinator selected44module/tool/policy context changed')
    require(sys.version_info[:2]==(3,11) and actual_python==plan['coordinator_python'],'actual regular coordinator Python3.11 differs')
    runtime=Path(plan['runtime']);manifest=runtime/'runtime-distribution.json';child=runtime/'.runs'/plan['installed_child_name']
    require(p.sha(manifest)==plan['runtime_manifest_sha256']and p.sha(child)==plan['child_sha256'],'installed018 manifest/child changed')
    runtime_python=plan['runtime_python'];require(shared.python_file_context(runtime/'.venv/bin/python')==
        {key:runtime_python[key]for key in('path','resolved_path','sha256','bytes')}and runtime_python['sha256']==actual_python['sha256']
        and runtime_python['version']==actual_python['version']and runtime_python['implementation']==actual_python['implementation'],'installed actual regular Python3.11 differs')
    manifest_data=f.read_json(manifest)
    require(manifest_data['build_source']['git_head']==plan['source_head']and plan['runtime_tools']['source_provenance']['manifest_sha256']==plan['runtime_manifest_sha256'],'runtime source/manifest metadata differs')
    for name,digest in manifest_data['build_source']['files_sha256'].items():require(p.sha(runtime/name)==digest,'installed product file changed: '+name)
    for path,digest in plan['runtime_tools']['files'].items():require(p.sha(Path(path))==digest,'pinned Native/Java/JAR changed: '+path)
    for path,digest in plan['prerequisite_sha256'].items():require(p.sha(Path(path))==digest,'018 prerequisite changed: '+path)
    require(p.sha(Path(plan['signal_bridge_controller']))==plan['signal_bridge_sha256'],'queued bridge changed')
    return plan

def read_child(receipt,pin):
    if not os.path.lexists(receipt):return None,None,None
    raw=pv.read_bytes(receipt,8*1024**2)
    try:
        row=json.loads(raw,object_pairs_hook=pv._strict_object,parse_constant=lambda value:(_ for _ in()).throw(ValueError('invalid JSON constant')))
        require(type(row)is dict and row.get('schema')==1 and row.get('kind')==CHILD_KIND and row.get('protocol_sha256')==pin,
            '018 child kind/protocol identity differs')
    except Exception as exc:return raw,None,type(exc).__name__+': '+str(exc)
    return raw,row,None

def execute(protocol,pin):
    shared=shared_helpers();plan=frozen(protocol,pin,shared);runtime=Path(plan['runtime']);child=runtime/'.runs'/plan['installed_child_name']
    out=BASE/'production-delivery-execution-001';out.mkdir();owner={};h.capture_destination(owner,out);job=gui.CliJob()
    helper=Path(plan['signal_bridge_controller']);spec=importlib.util.spec_from_file_location('existing_queued_bridge018',helper);bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with bridge.cancellation_bridge(job)as(queued,live),os.fdopen(fd,'r+')as lane:
        info=os.fstat(lane.fileno());require(stat.S_ISREG(info.st_mode)and info.st_nlink==1,'ordinary shared Native lane required')
        fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
        process=job.run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B',str(child),'--protocol',str(protocol),'--protocol-sha256',pin],out/'command.log',timeout=245)
        receipt=runtime/'.runs/production-delivery-001/result.json';raw=None;row=None;error=None
        try:raw,row,error=read_child(receipt,pin)
        except Exception as exc:error=type(exc).__name__+': '+str(exc)
        material=f.evidence_inventory(receipt.parent)if receipt.parent.is_dir()else None;logpin=p.sha(out/'command.log')
        passed=bool(row and row.get('passed')is True and row.get('status')=='completed'and row.get('source_head')==plan['source_head']
            and row.get('tools')==plan['runtime_tools']and row.get('python_context')==plan['runtime_python']
            and process['exit_code']==0 and not process['cancel_requested']and not process['log_truncated'])
        record=dict(schema=1,kind='runtime018-four-cu-production-enclosure-v1',accepted=False,passed=passed,status='completed'if passed else'failed',
            source_head=plan['source_head'],protocol_sha256=pin,process=process,child=row,scope=plan['scope'],
            coordinator_tools=p.tool_manifest(),coordinator_python=shared.coordinator_python_context(),child_receipt=str(receipt),
            child_receipt_sha256=None if raw is None else hashlib.sha256(raw).hexdigest(),child_receipt_bytes=None if raw is None else len(raw),child_receipt_error=error,
            accounting_point='Stored sample includes reaped child; complete external wall/fullCPU<=260s is mandatory. All routing/delivery counts; research/preparation/review separate.')
        def remaining():return min(258-(time.monotonic()-START),258-(cpu()-CPU0))
        def fresh():
            if record['passed']:live()
            h.owned_destination(owner);frozen(protocol,pin,shared)
            require((f.evidence_inventory(receipt.parent)if receipt.parent.is_dir()else None)==material and p.sha(out/'command.log')==logpin,'completed delivery material changed')
            shared.child_bytes_fresh(receipt,raw)
            if record['passed']:live()
        def account():
            record.update(inner_sample_wall_seconds=time.monotonic()-START,inner_sample_full_cpu_seconds=cpu()-CPU0)
            if remaining()<=0:record.update(passed=False,status='budget_exceeded')
            if queued[0]or job.cancel_requested:record.update(passed=False,status='cancelled')
            if record['status']!='completed':record['passed']=False
        def final():fresh();require(remaining()>0,'whole018 enclosure deadline exhausted')
        try:
            f.publish(out,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final)
            if record['passed']:
                fresh();live();shared.child_bytes_fresh(receipt,raw);require(remaining()>0,'whole018 deadline exhausted after publication')
        except BaseException as exc:
            def failed():raise exc
            f.publish(out,record,failed,account,remaining,owned=lambda:h.owned_destination(owner))
        print(json.dumps({key:record.get(key)for key in('passed','status','inner_sample_wall_seconds','inner_sample_full_cpu_seconds')}))
        return 0 if record['passed']and record['status']=='completed'else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True);args=parser.parse_args()
    raise SystemExit(execute(args.protocol.resolve(),args.protocol_sha256))
