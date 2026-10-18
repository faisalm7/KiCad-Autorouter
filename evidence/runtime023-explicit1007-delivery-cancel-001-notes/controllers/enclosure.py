"""Unexecuted straight reuse of the retained explicit1007 delivery enclosure.

Fresh runtime023 caller API controls only; no product/GUI/version promotion.
Prepare and execute only after the lead releases the sequential Native lane.
The cancel case needs an actual SIGINT/SIGTERM request; its name proves nothing.
"""
import time, resource
START=time.monotonic()
def cpu():
    return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse, fcntl, hashlib, json, os, signal, stat, sys, threading
from contextlib import contextmanager
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, handoff as h
from autorouter.runner import run
from autorouter.gui import CliJob, child_environment
BASE=ROOT/'.runs/runtime-directory-023';RUNTIME=BASE/'runtime'
OLD_PLAN=ROOT/'.runs/runtime-directory-015/native1007-delivery-protocol-004.json'
OLD_PLAN_PIN='61d2c6d03efce6d126aaed3386ee233177804546ceb6c3637ce12697ce788e31'
OLD_CHILD=ROOT/'.runs/native1007-delivery-child-003.py'
OLD_CHILD_PIN='53db973ec50c73395718e24820197ce260326cd28a14f89cbe04dc63c955c62c'
MANIFEST_PIN='3df808e340dbe8c01ddebafe5c5c12583dc8d4d0cfea407c9252b0a89c41de81'
SOURCE_HEAD='8c0c8468823751d9b5dc4c9a9c51b1d622269a27'
PROOF=ROOT/'.runs/kicad-1007-bundle-qualification-001/result.json'
PROOF_PIN='26564ecd90268e463760270902d302445d9b0e6859105d3ed06e5976a8989c73'
BUNDLE=ROOT/'.tools/kicad-10.0.7-local-001/KiCad.app/Contents'
NATIVE={'schema':1,'mode':'experimental-native-qualification','expected_version':'10.0.7','tools':{
    'cli':{'path':str(BUNDLE/'MacOS/kicad-cli'),'sha256':'0b9d96dbdac9517e7d85833f926fee07a563549ffe2c55670147bff3f562d01f'},
    'python':{'path':str(BUNDLE/'Frameworks/Python.framework/Versions/3.9/bin/python3.9'),'sha256':'fd8c2fa5393bebb9be6789dab8583acee6c5cff90d42696e8c1dbcabe02ec39f'},
    'pcbnew':{'path':str(BUNDLE/'Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/_pcbnew.so'),'sha256':'610ae51927809192be637d0de03c32d006332638e2272cbf11a553fe65c75f6e'}}}

@contextmanager
def cancellation_bridge(job):
    # Unchanged retained bridge: the signal handler never takes CliJob's lock.
    queued=[False];stop=threading.Event()
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def dispatch():
        while not stop.wait(.01):
            if queued[0]:
                job.cancel();return
    def request(*_):queued[0]=True
    def live():
        if queued[0]:raise p.Rejected('enclosure cancellation requested')
        job.check_live()
        if queued[0]:raise p.Rejected('enclosure cancellation requested')
    broker=threading.Thread(target=dispatch,name='finite-cancel-forwarder',daemon=False)
    broker.start()
    try:
        for sig in previous:signal.signal(sig,request)
        yield queued,live
    finally:
        if queued[0]:job.cancel()
        stop.set();broker.join()
        for sig,handler in previous.items():signal.signal(sig,handler)

def native():
    if p.sha(PROOF)!=PROOF_PIN:raise p.Rejected('retained signed bundle prerequisite changed')
    proof=f.read_json(PROOF)
    if (proof.get('signature_verified') is not True or proof.get('notarization_verified') is not True
            or proof.get('experimental_native_toolchain')!=NATIVE):
        raise p.Rejected('existing signed/notarized prerequisite differs from caller context')
    return p.ExperimentalNativeToolchain.from_record(NATIVE)

def locations(case):
    stem='runtime023-explicit1007-'+case+'-001'
    return (BASE/(stem+'-protocol.json'),RUNTIME/'.runs'/(stem+'-child.py'),
            BASE/(stem+'-enclosure'),RUNTIME/'.runs'/stem,BASE/(stem+'-preparation'))

def prepare(case):
    plan_path,child,output,delivery,prep=locations(case)
    if any(path.exists() or path.is_symlink() for path in (plan_path,child,output,delivery,prep)):
        raise p.Rejected('fresh case storage required; retained evidence is never overwritten')
    if p.sha(OLD_PLAN)!=OLD_PLAN_PIN or p.sha(OLD_CHILD)!=OLD_CHILD_PIN:
        raise p.Rejected('retained fixture/helper prerequisite changed')
    native();old=f.read_json(OLD_PLAN)
    if p.sha(RUNTIME/'runtime-distribution.json')!=MANIFEST_PIN:raise p.Rejected('runtime023 manifest changed')
    manifest=f.read_json(RUNTIME/'runtime-distribution.json')
    if manifest['build_source']['git_head']!=SOURCE_HEAD:raise p.Rejected('runtime023 source head differs')
    for name,pin in manifest['build_source']['files_sha256'].items():
        if p.sha(RUNTIME/name)!=pin:raise p.Rejected('frozen runtime file changed: '+name)
    prep.mkdir()
    # Existing tool_manifest reads pins/provenance only; it runs no Native tool.
    code='import json,sys;sys.path.insert(0,sys.argv[1]);from autorouter.pipeline import ExperimentalNativeToolchain as T,tool_manifest;print(json.dumps(tool_manifest(native_toolchain=T.from_record(json.loads(sys.argv[2])))))'
    proc=run([str(RUNTIME/'.venv/bin/python'),'-B','-c',code,str(RUNTIME),json.dumps(NATIVE,sort_keys=True)],
        cwd=prep,env=child_environment(),log=prep/'runtime-tools.json',timeout=20,
        max_log_bytes=64*1024,max_group_rss_bytes=1024**3,max_workdir_bytes=256*1024**2)
    p.save_json(prep/'process.json',proc)
    if (proc.get('status')!='success' or proc.get('exit_code')!=0 or proc.get('cleanup_complete') is not True
            or proc.get('log_truncated') is not False):raise p.Rejected('runtime pin capture refused')
    tools=f.read_json(prep/'runtime-tools.json')
    if (tools.get('git_head')!=SOURCE_HEAD or tools.get('source_provenance',{}).get('manifest_sha256')!=MANIFEST_PIN
            or tools.get('experimental_native_toolchain')!=NATIVE):raise p.Rejected('runtime023 explicit context differs')
    raw=OLD_CHILD.read_bytes();before=b"out = ROOT / '.runs/native1007-delivery-002'"
    if hashlib.sha256(raw).hexdigest()!=OLD_CHILD_PIN or p.sha(OLD_PLAN)!=OLD_PLAN_PIN:
        raise p.Rejected('retained fixture/helper changed during preparation')
    after=("out = ROOT / '.runs/"+delivery.name+"'").encode()
    if raw.count(before)!=1:raise p.Rejected('exact sole helper destination relocation required')
    with child.open('xb') as stream:stream.write(raw.replace(before,after))
    plan={name:old[name] for name in ('board_name','fixture_files','fixture_sha256','fixture_code_sha256','limits')}
    plan.update(schema=1,kind='runtime023-owned-explicit1007-delivery-api-v1',case=case,
        runtime=str(RUNTIME),source_head=SOURCE_HEAD,runtime_tools=tools,native_toolchain=NATIVE,
        signature_prerequisite_sha256=PROOF_PIN,runtime_manifest_sha256=MANIFEST_PIN,
        controller_sha256=p.sha(Path(__file__)),child_sha256=p.sha(child),
        reused_fixture_protocol_sha256=OLD_PLAN_PIN,reused_child_sha256=OLD_CHILD_PIN,
        child_change='Exactly one owned output destination relocation; all helper checks unchanged.',
        processes=[proc],preparation_wall_seconds=time.monotonic()-START,
        preparation_full_cpu_seconds=cpu()-CPU0,preparation_publication_budget_charge_seconds=4,
        accepted=False,production_admitted=False,actual_GUI=False,human_review=False,
        external_complete_exit_required=True,
        scope='Fresh runtime023 explicit caller-pinned1007 B0 Route/rendered review/software intent/fresh Native export/current readback and default-consumer refusals, using the unchanged owned fixture. Existing180wall/fullCPU whole slice,172child/176worker/178finalization fences,120route,30-60export and inner resource/network/original/fullSCH/protected-copper guards retained. Existing SIGINT/SIGTERM bridge only; no automatic cancellation or claimed cancellation pass. Preparation is charged with4s conservative publication allowance; prior runtime build, authoring/review and any earlier failures are separate nonzero costs. Complete enclosing exit timing must confirm180s eligibility. No product source, global app/configuration, production admission, GUI, Windows, independent-family, speed/quality superiority, human or physical/electrical qualification.')
    p.save_json(plan_path,plan)
    print(json.dumps(dict(prepared=True,case=case,protocol=str(plan_path),protocol_sha256=p.sha(plan_path),
        Native_executed=False,runtime_rebuilt=False,production_admitted=False,actual_GUI=False)))

def execute(case,pin):
    plan_path,child,output,delivery,prep=locations(case)
    plan=f.read_json(plan_path);native()
    if (p.sha(plan_path)!=pin or plan['native_toolchain']!=NATIVE or plan.get('case')!=case
            or p.sha(Path(__file__))!=plan['controller_sha256']):raise p.Rejected('explicit frozen protocol/controller required')
    if p.sha(RUNTIME/'runtime-distribution.json')!=plan['runtime_manifest_sha256']:raise p.Rejected('runtime manifest changed')
    if p.sha(child)!=plan['child_sha256']:raise p.Rejected('frozen child changed')
    if delivery.exists() or output.exists():raise p.Rejected('fresh execution storage required')
    output.mkdir();owner={};h.capture_destination(owner,output)
    lockpath=ROOT/'.runs/quality-experiment.lock';fd=os.open(lockpath,os.O_RDWR|os.O_NOFOLLOW)
    job=CliJob()
    prep_wall=plan['preparation_wall_seconds']+plan['preparation_publication_budget_charge_seconds']
    prep_cpu=plan['preparation_full_cpu_seconds']+plan['preparation_publication_budget_charge_seconds']
    with cancellation_bridge(job) as (queued,live):
        with os.fdopen(fd,'r+') as lane:
            info=os.fstat(lane.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared Native lane required')
            fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:
                proc=job.run([*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B',str(child),
                    '--protocol',str(plan_path),'--protocol-sha256',pin],output/'command.log',
                    timeout=max(.001,min(176-prep_wall-(time.monotonic()-START),176-prep_cpu-(cpu()-CPU0))))
            except BaseException as exc:
                proc=dict(exit_code=None,cancel_requested=job.cancel_requested,log_truncated=False,
                    error=type(exc).__name__+': '+str(exc),cleanup_scope='Existing inner worker ownership; no outer descendant certification.')
            result=delivery/'result.json';row=f.read_json(result) if result.exists() else None
            # Only this fresh case; never scan runtime023's historical .runs.
            material=f.evidence_inventory(delivery) if delivery.exists() else None
            logpin=p.sha(output/'command.log')
            passed=bool(case=='delivery' and row and row.get('passed') is True and row.get('status')=='completed'
                and row.get('accepted') is False and row.get('production_admitted') is False
                and row.get('tools')==plan['runtime_tools'] and proc['exit_code']==0
                and proc['cancel_requested'] is False and proc['log_truncated'] is False)
            record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'failed',
                production_admitted=False,actual_GUI=False,human_review=False,case=case,
                source_head=plan['source_head'],protocol_sha256=pin,process=proc,child=row,
                completed_evidence=material,log_sha256=logpin,scope=plan['scope'],
                cancellation_qualified=False,cancellation_scope='Record actual request/worker evidence only; case name or old synthetic bridge controls are not fresh Native cancellation proof.')
            def remaining():return min(178-prep_wall-(time.monotonic()-START),178-prep_cpu-(cpu()-CPU0))
            def fresh():
                if record['passed']:live()
                h.owned_destination(owner);native()
                actual=f.evidence_inventory(delivery) if delivery.exists() else None
                if p.sha(plan_path)!=pin or actual!=material or p.sha(output/'command.log')!=logpin:
                    raise p.Rejected('completed bounded execution changed')
                if record['passed']:live()
            def account():
                record.update(execution_wall_seconds=time.monotonic()-START,execution_full_cpu_seconds=cpu()-CPU0,
                    charged_preparation_wall_seconds=prep_wall,charged_preparation_full_cpu_seconds=prep_cpu,
                    wall_seconds=prep_wall+time.monotonic()-START,full_cpu_seconds=prep_cpu+cpu()-CPU0,
                    cancellation_request_observed=queued[0] or job.cancel_requested)
                if remaining()<=0:record.update(passed=False,status='budget_exceeded')
                if queued[0] or job.cancel_requested:record.update(passed=False,status='cancelled')
                if record['status']!='completed':record['passed']=False
            try:
                f.publish(output,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=fresh)
                if record['passed']:live()
            except BaseException as exc:
                def failed():raise exc
                f.publish(output,record,failed,account,remaining,owned=lambda:h.owned_destination(owner))
            print(json.dumps({key:record.get(key) for key in ('passed','status','wall_seconds','full_cpu_seconds','cancellation_request_observed')}))
            return 0 if record['passed'] and record['status']=='completed' else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=('delivery','cancel'),default='delivery')
    parser.add_argument('--prepare',action='store_true');parser.add_argument('--protocol-sha256')
    args=parser.parse_args()
    if args.prepare and args.protocol_sha256:parser.error('prepare and execute are separate frozen steps')
    if args.prepare:prepare(args.case)
    elif args.protocol_sha256:raise SystemExit(execute(args.case,args.protocol_sha256))
    else:parser.error('execute requires frozen protocol SHA256')
