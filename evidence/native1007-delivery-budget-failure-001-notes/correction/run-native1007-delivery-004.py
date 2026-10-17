"""Finite prepare/execute enclosure, reusing the runtime builder and shared runner."""
import time, resource
START=time.monotonic()
def cpu():
    return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse, fcntl, hashlib, json, os, shutil, signal, stat, subprocess, sys, threading
from contextlib import contextmanager
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, handoff as h, provenance as pv
from autorouter.runner import run
from autorouter.gui import CliJob, LOG_LIMIT
from experiments.native_schematic_transport_v1 import fixture
BASE=ROOT/'.runs/runtime-directory-015';RUNTIME=BASE/'runtime'
PLAN=BASE/'native1007-delivery-protocol-004.json'
PROOF=ROOT/'.runs/kicad-1007-bundle-qualification-001/result.json'
PROOF_PIN='26564ecd90268e463760270902d302445d9b0e6859105d3ed06e5976a8989c73'
BUNDLE=ROOT/'.tools/kicad-10.0.7-local-001/KiCad.app/Contents'
NATIVE={'schema':1,'mode':'experimental-native-qualification','expected_version':'10.0.7','tools':{
    'cli':{'path':str(BUNDLE/'MacOS/kicad-cli'),'sha256':'0b9d96dbdac9517e7d85833f926fee07a563549ffe2c55670147bff3f562d01f'},
    'python':{'path':str(BUNDLE/'Frameworks/Python.framework/Versions/3.9/bin/python3.9'),'sha256':'fd8c2fa5393bebb9be6789dab8583acee6c5cff90d42696e8c1dbcabe02ec39f'},
    'pcbnew':{'path':str(BUNDLE/'Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/_pcbnew.so'),'sha256':'610ae51927809192be637d0de03c32d006332638e2272cbf11a553fe65c75f6e'}}}

@contextmanager
def cancellation_bridge(job):
    """Finite signal forwarding for this in-session call; joined before return.

    A Python signal handler may interrupt CliJob while it owns its Lock. Queue
    only a Boolean there; the bounded-lifetime forwarding thread calls cancel.
    """
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

def prepare():
    # Reuse the already-built source73 runtime; do not rerun completed build.
    prior=BASE/'native1007-delivery-protocol-003.json'
    if p.sha(prior)!='e32ede344f2dbf184271f2735c372c934e94d269c4407b84101ba8430d5ebd70':raise p.Rejected('original preparation changed')
    plan=f.read_json(prior);native()
    if p.sha(RUNTIME/'runtime-distribution.json')!=plan['runtime_manifest_sha256']:raise p.Rejected('runtime manifest changed')
    manifest=f.read_json(RUNTIME/'runtime-distribution.json')
    for name,pin in manifest['build_source']['files_sha256'].items():
        if p.sha(RUNTIME/name)!=pin:raise p.Rejected('frozen runtime file changed: '+name)
    child=RUNTIME/'.runs/native1007-delivery-child-003.py'
    if child.exists():raise p.Rejected('fresh corrected child required')
    shutil.copyfile(ROOT/'.runs/native1007-delivery-child-003.py',child)
    plan.update(kind='one-owned-explicit1007-delivery-v2',controller_sha256=p.sha(Path(__file__)),child_sha256=p.sha(child),
        prior_failed_execution=str(BASE/'native1007-delivery-execution-003/result.json'),
        reused_preparation_protocol_sha256=p.sha(prior),
        correction='Only experimental finalization changes: shared publisher stable calls retain exact runtime/protocol/source/evidence witnesses; final_check still performs complete central export readback, including final material/PRL checks. First explicit export readback and all actual Native candidate proofs retained. No product acceptance change.',
        repeated_full_semantic_checks_in_publisher=1,
        preparation_wall_seconds=plan['preparation_wall_seconds']+time.monotonic()-START,
        preparation_full_cpu_seconds=plan['preparation_full_cpu_seconds']+cpu()-CPU0,
        preparation_publication_budget_charge_seconds=4)
    plan['scope']=plan['scope'].replace('conservative2second','conservative4second')
    p.save_json(PLAN,plan)
    print(json.dumps(dict(prepared=True,protocol=str(PLAN),protocol_sha256=p.sha(PLAN),runtime_rebuilt=False)))

def execute(pin):
    plan=f.read_json(PLAN);nt=native()
    if p.sha(PLAN)!=pin or plan['native_toolchain']!=NATIVE or p.sha(Path(__file__))!=plan['controller_sha256']:
        raise p.Rejected('explicit frozen protocol/controller required')
    if p.sha(RUNTIME/'runtime-distribution.json')!=plan['runtime_manifest_sha256']:raise p.Rejected('runtime manifest changed')
    child=RUNTIME/'.runs/native1007-delivery-child-003.py'
    if p.sha(child)!=plan['child_sha256']:raise p.Rejected('frozen child changed')
    output=BASE/'native1007-delivery-execution-004';output.mkdir();owner={};h.capture_destination(owner,output)
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
                proc=job.run([*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B',str(child),'--protocol',str(PLAN),'--protocol-sha256',pin],
                    output/'command.log',timeout=max(.001,min(176-prep_wall-(time.monotonic()-START),176-prep_cpu-(cpu()-CPU0))))
            except BaseException as exc:
                proc=dict(exit_code=None,cancel_requested=job.cancel_requested,log_truncated=False,
                    error=type(exc).__name__+': '+str(exc),cleanup_scope='Existing inner worker ownership; no outer descendant certification.')
            result=RUNTIME/'.runs/native1007-delivery-002/result.json'
            row=f.read_json(result) if result.exists() else None
            material=f.evidence_inventory(RUNTIME/'.runs');logpin=p.sha(output/'command.log')
            passed=bool(row and row.get('passed') is True and row.get('status')=='completed' and row.get('accepted') is False
                and row.get('production_admitted') is False and row.get('tools')==plan['runtime_tools']
                and proc['exit_code']==0 and proc['cancel_requested'] is False and proc['log_truncated'] is False)
            record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'failed',source_head=plan['source_head'],
                protocol_sha256=pin,process=proc,child=row,completed_evidence=material,log_sha256=logpin,scope=plan['scope'])
            def remaining():return min(178-prep_wall-(time.monotonic()-START),178-prep_cpu-(cpu()-CPU0))
            def fresh():
                if record['passed']:live()
                h.owned_destination(owner);native()
                if p.sha(PLAN)!=pin or f.evidence_inventory(RUNTIME/'.runs')!=material or p.sha(output/'command.log')!=logpin:
                    raise p.Rejected('completed bounded execution changed')
                if record['passed']:live()
            def account():
                record.update(execution_wall_seconds=time.monotonic()-START,execution_full_cpu_seconds=cpu()-CPU0,
                    charged_preparation_wall_seconds=prep_wall,charged_preparation_full_cpu_seconds=prep_cpu,
                    wall_seconds=prep_wall+time.monotonic()-START,full_cpu_seconds=prep_cpu+cpu()-CPU0)
                if remaining()<=0:record.update(passed=False,status='budget_exceeded')
                if queued[0] or job.cancel_requested:record.update(passed=False,status='cancelled')
                if record['status']!='completed':record['passed']=False
            try:
                f.publish(output,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=fresh)
                if record['passed']:live()
            except BaseException as exc:
                def failed():raise exc
                f.publish(output,record,failed,account,remaining,owned=lambda:h.owned_destination(owner))
            print(json.dumps({k:record.get(k) for k in ('passed','status','wall_seconds','full_cpu_seconds')}))
            return 0 if record['passed'] and record['status']=='completed' else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('--protocol-sha256')
    args=parser.parse_args()
    if args.prepare:prepare()
    elif args.protocol_sha256:raise SystemExit(execute(args.protocol_sha256))
    else:parser.error('execute requires frozen protocol SHA256')
