"""Finite prepare/execute enclosure, reusing the runtime builder and shared runner."""
import time, resource
START=time.monotonic()
def cpu():
    return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse, fcntl, hashlib, json, os, shutil, stat, subprocess, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, handoff as h, provenance as pv
from autorouter.runner import run
from experiments.native_schematic_transport_v1 import fixture
BASE=ROOT/'.runs/runtime-directory-015';RUNTIME=BASE/'runtime'
PLAN=BASE/'native1007-delivery-protocol-001.json'
PROOF=ROOT/'.runs/kicad-1007-bundle-qualification-001/result.json'
PROOF_PIN='26564ecd90268e463760270902d302445d9b0e6859105d3ed06e5976a8989c73'
BUNDLE=ROOT/'.tools/kicad-10.0.7-local-001/KiCad.app/Contents'
NATIVE={'schema':1,'mode':'experimental-native-qualification','expected_version':'10.0.7','tools':{
    'cli':{'path':str(BUNDLE/'MacOS/kicad-cli'),'sha256':'0b9d96dbdac9517e7d85833f926fee07a563549ffe2c55670147bff3f562d01f'},
    'python':{'path':str(BUNDLE/'Frameworks/Python.framework/Versions/3.9/bin/python3.9'),'sha256':'fd8c2fa5393bebb9be6789dab8583acee6c5cff90d42696e8c1dbcabe02ec39f'},
    'pcbnew':{'path':str(BUNDLE/'Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/_pcbnew.so'),'sha256':'610ae51927809192be637d0de03c32d006332638e2272cbf11a553fe65c75f6e'}}}

def native():
    if p.sha(PROOF)!=PROOF_PIN:raise p.Rejected('retained signed bundle prerequisite changed')
    proof=f.read_json(PROOF)
    if (proof.get('signature_verified') is not True or proof.get('notarization_verified') is not True
            or proof.get('experimental_native_toolchain')!=NATIVE):
        raise p.Rejected('existing signed/notarized prerequisite differs from caller context')
    return p.ExperimentalNativeToolchain.from_record(NATIVE)

def prepare():
    dirty=subprocess.run(['git','status','--porcelain'],cwd=ROOT,check=True,capture_output=True,text=True)
    if dirty.stdout:raise p.Rejected('clean audited source checkpoint required before build')
    nt=native();tools=p.tool_manifest(native_toolchain=nt)
    BASE.mkdir();processes=[]
    env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}}
    for name,argv in [('build',[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/prepare_runtime.py'),'--output',str(RUNTIME),'--copy-local-engine']),
                      ('venv',[str(ROOT/'.venv/bin/python'),'-B','-m','venv','--copies','--without-pip',str(RUNTIME/'.venv')])]:
        row=run(argv,cwd=BASE,env=env,log=BASE/(name+'.log'),timeout=90,max_log_bytes=64*1024,
                max_workdir_bytes=256*1024**2,max_group_rss_bytes=1024**3)
        processes.append(row)
        if row['status']!='success' or row['exit_code']!=0 or row['cleanup_complete'] is not True:raise p.Rejected('runtime preparation failed: '+name)
    manifest=f.read_json(RUNTIME/'runtime-distribution.json')
    old=f.read_json(ROOT/'.runs/runtime-directory-014/runtime/runtime-distribution.json')
    a={n:v for n,v in old['build_source']['files_sha256'].items() if n.startswith('autorouter/')}
    b={n:v for n,v in manifest['build_source']['files_sha256'].items() if n.startswith('autorouter/')}
    if set(a)!=set(b) or len(b)!=44 or sorted(n for n in b if a[n]!=b[n])!=['autorouter/handoff.py','autorouter/review_export.py','autorouter/review_view.py']:
        raise p.Rejected('unexpected runtime module change population')
    runtime_tools=json.loads(json.dumps(tools))
    runtime_tools['source_provenance']=pv.source_identity(RUNTIME,b)
    runtime_tools['files'].pop(str(p.c.JAR));runtime_tools['files'][str(RUNTIME/'.tools'/p.c.JAR.name)]=p.c.JAR_SHA256
    work=RUNTIME/'.runs';work.mkdir()
    child=work/'native1007-delivery-child-001.py';shutil.copyfile(ROOT/'.runs/native1007-delivery-child-001.py',child)
    files=fixture.files()
    plan=dict(schema=1,kind='one-owned-explicit1007-delivery-v1',source_head=tools['git_head'],runtime=str(RUNTIME),
        runtime_tools=runtime_tools,native_toolchain=NATIVE,signature_prerequisite_sha256=PROOF_PIN,
        runtime_manifest_sha256=p.sha(RUNTIME/'runtime-distribution.json'),controller_sha256=p.sha(Path(__file__)),
        child_sha256=p.sha(child),fixture_code_sha256=p.sha(ROOT/'experiments/native_schematic_transport_v1/fixture.py'),
        board_name=fixture.STEM+'.kicad_pcb',fixture_files={n:raw.decode() for n,raw in files.items()},
        fixture_sha256={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()},
        limits=dict(whole_wall_full_cpu_seconds=180,worker_seconds=176,child_acceptance_seconds=172,route_seconds=120,
            export_max_seconds=60,export_min_seconds=30,final_reserve_seconds=12,scratch_bytes=128*1024**2,group_rss_bytes=4*1024**3),
        processes=processes,preparation_wall_seconds=time.monotonic()-START,preparation_full_cpu_seconds=cpu()-CPU0,
        scope='One fresh owned explicit caller1007 B0 Route/rendered review/software intent/fresh Native export/readback. Cold build/preparation separate; all ordinary job imports/source copy/conversion/attempts/validation/selection/delivery/readback counted in whole180wall/fullCPU. No current-stable production pin promotion, GUI, Windows, new family, quality superiority, physical or human approval claim.')
    p.save_json(PLAN,plan)
    print(json.dumps(dict(prepared=True,protocol=str(PLAN),protocol_sha256=p.sha(PLAN),source_head=tools['git_head'])))

def execute(pin):
    plan=f.read_json(PLAN);nt=native()
    if p.sha(PLAN)!=pin or plan['native_toolchain']!=NATIVE or p.sha(Path(__file__))!=plan['controller_sha256']:
        raise p.Rejected('explicit frozen protocol/controller required')
    if p.sha(RUNTIME/'runtime-distribution.json')!=plan['runtime_manifest_sha256']:raise p.Rejected('runtime manifest changed')
    child=RUNTIME/'.runs/native1007-delivery-child-001.py'
    if p.sha(child)!=plan['child_sha256']:raise p.Rejected('frozen child changed')
    output=BASE/'native1007-delivery-execution-001';output.mkdir();owner={};h.capture_destination(owner,output)
    lockpath=ROOT/'.runs/quality-experiment.lock';fd=os.open(lockpath,os.O_RDWR|os.O_NOFOLLOW)
    env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}}
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PIP_NO_INDEX='1')
    with os.fdopen(fd,'r+') as lane:
        info=os.fstat(lane.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared Native lane required')
        fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
        proc=run([*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B',str(child),'--protocol',str(PLAN),'--protocol-sha256',pin],
            cwd=RUNTIME/'.runs',env=env,log=output/'command.log',timeout=max(.001,176-(time.monotonic()-START)),
            max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
        result=RUNTIME/'.runs/native1007-delivery-001/result.json'
        row=f.read_json(result) if result.exists() else None
        material=f.evidence_inventory(RUNTIME/'.runs');logpin=p.sha(output/'command.log')
        passed=bool(row and row.get('passed') is True and row.get('status')=='completed' and row.get('accepted') is False
            and row.get('production_admitted') is False and row.get('tools')==plan['runtime_tools']
            and proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] is True and proc['log_truncated'] is False)
        record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'failed',source_head=plan['source_head'],
            protocol_sha256=pin,process=proc,child=row,completed_evidence=material,log_sha256=logpin,scope=plan['scope'])
        def remaining():return min(178-(time.monotonic()-START),178-(cpu()-CPU0))
        def fresh():
            h.owned_destination(owner);native()
            if p.sha(PLAN)!=pin or f.evidence_inventory(RUNTIME/'.runs')!=material or p.sha(output/'command.log')!=logpin:
                raise p.Rejected('completed bounded execution changed')
        def account():
            record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
            if remaining()<=0:record.update(passed=False,status='budget_exceeded')
            if record['status']!='completed':record['passed']=False
        f.publish(output,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=fresh)
        print(json.dumps({k:record.get(k) for k in ('passed','status','wall_seconds','full_cpu_seconds')}))
        return 0 if record['passed'] and record['status']=='completed' else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('--protocol-sha256')
    args=parser.parse_args()
    if args.prepare:prepare()
    elif args.protocol_sha256:raise SystemExit(execute(args.protocol_sha256))
    else:parser.error('execute requires frozen protocol SHA256')
