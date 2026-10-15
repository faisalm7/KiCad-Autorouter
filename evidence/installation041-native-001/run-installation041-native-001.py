"""Prepare, then run ONE fresh installed explicit1007 API fixture.
SPDX-License-Identifier: GPL-3.0-or-later
Uses the existing bounded runner/shared publisher/check_result; no old record repair.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,hashlib,json,os,shutil,stat,sys
ROOT=Path(__file__).resolve().parents[1]
CLONE=ROOT/'.runs/installation-041/checkout'
PREPARING='--prepare' in sys.argv
sys.path.insert(0,str(ROOT if PREPARING else CLONE));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,config as c
from autorouter.runner import run
from scripts import install_smoke as install
from experiments.native_schematic_transport_v1 import fixture
BASE=ROOT/'.runs/installation-041';CLONE=BASE/'checkout'
PREP=ROOT/'.runs/installation041-native-preparation-001';OUT=ROOT/'.runs/installation041-native-001'
WORK=CLONE/'.runs/installation041-explicit1007';PROTOCOL=PREP/'protocol.json'
PROOF=ROOT/'.runs/kicad-1007-bundle-qualification-001/result.json'
PROOF_PIN='26564ecd90268e463760270902d302445d9b0e6859105d3ed06e5976a8989c73'
# Caller-declared context; signed receipt is an immutable comparison proof only.
NATIVE_TOOLCHAIN={'schema': 1, 'mode': 'experimental-native-qualification', 'expected_version': '10.0.7', 'tools': {'cli': {'path': '/Users/faisal/Projects/KiCad-Autorouter-local/.tools/kicad-10.0.7-local-001/KiCad.app/Contents/MacOS/kicad-cli', 'sha256': '0b9d96dbdac9517e7d85833f926fee07a563549ffe2c55670147bff3f562d01f'}, 'python': {'path': '/Users/faisal/Projects/KiCad-Autorouter-local/.tools/kicad-10.0.7-local-001/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9', 'sha256': 'fd8c2fa5393bebb9be6789dab8583acee6c5cff90d42696e8c1dbcabe02ec39f'}, 'pcbnew': {'path': '/Users/faisal/Projects/KiCad-Autorouter-local/.tools/kicad-10.0.7-local-001/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/_pcbnew.so', 'sha256': '610ae51927809192be637d0de03c32d006332638e2272cbf11a553fe65c75f6e'}}}


def clean(root,head):
    receipt=f.read_json(BASE/'result.json')
    branch=receipt['source_branch'] if root==ROOT else None
    if install.git_identity(root,head,branch)!=receipt['git_identity_witnesses'][str(root)]:
        raise p.Rejected('source/installed Git identity changed')


def stable(plan):
    if p.sha(PROOF)!=PROOF_PIN:raise p.Rejected('qualified signed bundle receipt changed')
    if plan['native_toolchain']!=NATIVE_TOOLCHAIN:raise p.Rejected('explicit caller Native context differs')
    nt=p.ExperimentalNativeToolchain.from_record(NATIVE_TOOLCHAIN)
    expected=plan['source_native_tools'] if PREPARING else plan['native_tools']
    if not PREPARING and (Path(sys.executable)!=CLONE/'.venv/bin/python' or Path(sys.prefix).resolve()!=CLONE/'.venv' or sys.prefix==sys.base_prefix):
        raise p.Rejected('outer requires independent installed interpreter')
    if c.ROOT!=(ROOT if PREPARING else CLONE) or any(not Path(m.__file__).resolve().is_relative_to(c.ROOT) for m in (p,f,h,c,install,fixture)):
        raise p.Rejected('prepare/source or execute/installed import context differs')
    if p.tool_manifest(native_toolchain=nt)!=expected:raise p.Rejected('current tools/implementation/HEAD changed')
    for tool,digest in plan['source_native_tools']['files'].items():
        if p.sha(Path(tool))!=digest:raise p.Rejected('frozen original tool changed')
    if p.sha(BASE/'result.json')!=plan['installation_receipt_sha256'] or p.sha(BASE/'source-tracked.json')!=plan['source_inventory_sha256']:
        raise p.Rejected('installation baseline material changed')
    source=f.read_json(BASE/'source-tracked.json');listing=(BASE/'03-source-files.log').read_text();selected=install.distribution_listing(listing)
    for root,rows in ((ROOT,listing),(CLONE,selected)):
        expected=source if root==ROOT else {n:source[n] for n in selected.split('\0') if n}
        if install.tracked_inventory(root,rows)!=expected:raise p.Rejected('complete source/installed subset changed')
        clean(root,plan['git_head'])
    if p.sha(WORK/'installed1007.py')!=plan['installed_companion_sha256'] or p.sha(Path(__file__))!=plan['controller_sha256']:
        raise p.Rejected('installed companion/controller changed')
    for tool,digest in plan['native_tools']['files'].items():
        if p.sha(Path(tool))!=digest:raise p.Rejected('installed native/engine tool changed')
    if Path(plan['original_jar']).stat().st_ino==(CLONE/'.tools'/Path(plan['original_jar']).name).stat().st_ino:raise p.Rejected('copied JAR is not independent')
    return nt


def prepare(head):
    receipt=f.read_json(BASE/'result.json')
    if (receipt.get('passed') is not True or receipt.get('status')!='passed'
            or receipt.get('source_installation_mode')!='distribution' or receipt.get('git_head')!=head
            or receipt.get('source_checkout')!=str(ROOT) or receipt.get('output')!=str(BASE)):
        raise p.Rejected('completed current ordinary distribution baseline required')
    clean(ROOT,head);clean(CLONE,head)
    if p.sha(PROOF)!=PROOF_PIN:raise p.Rejected('qualified bundle proof changed')
    proof=f.read_json(PROOF)
    if proof.get('signature_verified') is not True or proof.get('notarization_verified') is not True:
        raise p.Rejected('existing signed/notarized bundle proof missing')
    if proof['experimental_native_toolchain']!=NATIVE_TOOLCHAIN:raise p.Rejected('signed proof differs from explicit caller context')
    nt=p.ExperimentalNativeToolchain.from_record(NATIVE_TOOLCHAIN)
    tools=p.tool_manifest(native_toolchain=nt)
    if tools['git_head']!=head:raise p.Rejected('prospective source checkpoint differs')
    PREP.mkdir();WORK.mkdir()
    companion=Path(__file__).with_name('installation041-installed1007.py')
    shutil.copyfile(companion,WORK/'installed1007.py')
    installed_tools=json.loads(json.dumps(tools));installed_tools['files'].pop(str(c.JAR))
    installed_tools['files'][str(CLONE/'.tools'/c.JAR.name)]=c.JAR_SHA256
    plan=dict(schema=1,kind='installation041-installed1007-v1',status='frozen_for_lead_execution',
        git_head=head,installation=str(BASE),checkout=str(CLONE),native_output=str(WORK/'native'),
        installation_receipt_sha256=p.sha(BASE/'result.json'),source_inventory_sha256=receipt['source_inventory_sha256'],
        installed_git_identity=install.git_identity(CLONE,head),bundle_proof_sha256=PROOF_PIN,
        native_toolchain=nt.record(),source_native_tools=tools,native_tools=installed_tools,
        original_jar=str(c.JAR),jar_sha256=c.JAR_SHA256,
        installed_companion_sha256=p.sha(WORK/'installed1007.py'),controller_sha256=p.sha(Path(__file__)),
        fixture_code_sha256={str(x.relative_to(ROOT)):p.sha(x) for x in (ROOT/'experiments/native_schematic_transport_v1').iterdir() if x.is_file()},
        fixture_files_sha256={n:hashlib.sha256(raw).hexdigest() for n,raw in fixture.files().items()},
        limits=dict(route_wall_full_cpu_seconds=120,whole_wall_full_cpu_seconds=180,worker_seconds=176,
            publication_allowance_seconds=2,scratch_bytes=128*1024**2,group_rss_bytes=4*1024**3,log_bytes=256*1024),
        scope='Fresh required installed041 API diagnostic after shared bounded-file IO helper change; baseline smoke unchanged. No prior001/002 worker rerun to repair records; this is fresh required installed qualification. No historical rewriting, normal1007 promotion, customDRU, freshOS, GUI, physical or comparative claim.')
    stable(plan)
    plan['preparation_costs']={'wall_seconds':time.monotonic()-START,'full_cpu_seconds':cpu()-CPU0,'publication_allowance_seconds':2}
    p.save_json(PROTOCOL,plan)
    print(json.dumps(dict(prepared=True,protocol=str(PROTOCOL),protocol_sha256=p.sha(PROTOCOL),tests_or_native_executed=False)))


def execute(head):
    plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
    if plan.get('kind')!='installation041-installed1007-v1' or plan.get('status')!='frozen_for_lead_execution' or plan['git_head']!=head:
        raise p.Rejected('frozen intended installed protocol required')
    nt=stable(plan);OUT.mkdir();owner={};h.capture_destination(owner,OUT)
    preparation=plan['preparation_costs'];prepwall=preparation['wall_seconds']+2;prepcpu=preparation['full_cpu_seconds']+2
    if preparation['publication_allowance_seconds']!=2 or min(prepwall,prepcpu)<2:raise p.Rejected('invalid prospective preparation costs')
    env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}}
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PIP_NO_INDEX='1')
    for key,name in (('KICAD_CONFIG_HOME','kicad-config'),('KICAD_CACHE_HOME','kicad-cache'),('KICAD_DOCUMENTS_HOME','kicad-documents')):
        directory=OUT/name;(directory/('10.0' if key=='KICAD_CONFIG_HOME' else 'kicad/10.0')).mkdir(parents=True)
        env[key]=str(directory)
    # Parent owns the project's existing shared lane; p.route itself has no flock.
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared lane required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        argv=[*f.SANDBOX,str(CLONE/'.venv/bin/python'),'-B',str(WORK/'installed1007.py'),
            '--protocol',str(PROTOCOL),'--protocol-sha256',pin]
        process=run(argv,cwd=WORK,env=env,log=OUT/'command.log',timeout=max(.001,176-prepwall-(time.monotonic()-START)),
            max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
        childpath=WORK/'native/result.json';child=f.read_json(childpath) if childpath.is_file() else None
        child_literal=f.canonical(child) if child is not None else None
        child_bound=bool(child and child.get('completed_evidence')==f.evidence_inventory(WORK/'native'))
        if child_bound and f.canonical(f.read_json(childpath))!=child_literal:raise p.Rejected('child changed before outer witness')
        material=p.tree_hash(WORK);logpin=p.sha(OUT/'command.log')
        passed=bool(child_bound and child.get('passed') is True and child.get('status')=='completed'
            and child.get('accepted') is False and child.get('production_admitted') is False
            and child.get('tools')==plan['native_tools'] and process['status']=='success' and process['exit_code']==0
            and process['cleanup_complete'] is True and process['log_truncated'] is False)
        record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'failed',
            production_admitted=False,git_head=head,process=process,protocol_sha256=pin,
            controller_sha256=p.sha(Path(__file__)),child_receipt_sha256=p.sha(childpath) if child else None,
            child_material=material,child_completed_evidence_bound=child_bound,log_sha256=logpin,limits=plan['limits'],preparation_costs=preparation,scope=plan['scope'])
        def remaining():return min(178-prepwall-(time.monotonic()-START),178-prepcpu-(cpu()-CPU0))
        def fresh():
            h.owned_destination(owner);stable(plan)
            if p.sha(PROTOCOL)!=pin or p.tree_hash(WORK)!=material or p.sha(OUT/'command.log')!=logpin:raise p.Rejected('installed completed material/protocol changed')
            if child_bound and (f.canonical(f.read_json(childpath))!=child_literal or f.evidence_inventory(WORK/'native')!=child['completed_evidence']):
                raise p.Rejected('published child witness/literal changed')
            if record['passed']:p.check_experimental_local_settings(WORK/'native/route',f.read_json(WORK/'native/route/result.json'),nt)
        def account():
            record.update(invocation_wall_seconds=time.monotonic()-START,invocation_full_cpu_seconds=cpu()-CPU0,
                wall_seconds=prepwall+time.monotonic()-START,full_cpu_seconds=prepcpu+cpu()-CPU0,publication_allowance_seconds=2)
            if remaining()<=0 and record['status']=='completed':record.update(passed=False,status='budget_exceeded')
            if record['status']!='completed':record['passed']=False
        def final_check():
            fresh()
            if record['passed']:
                checked=p.check_result(WORK/'native/route/result.json',native_toolchain=nt,experimental_schematic_parity=True)
                if checked.get('current') is not True:raise p.Rejected('installed outer final shared result check refused')
            fresh()
        f.publish(OUT,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final_check)
        stored=f.read_json(OUT/'result.json');ok=stored.get('passed') is True and stored.get('status')=='completed'
        print(json.dumps({k:stored.get(k) for k in ('passed','status','wall_seconds','full_cpu_seconds')}))
        return 0 if ok else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-head',required=True)
    parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    if args.prepare:prepare(args.source_head)
    else:raise SystemExit(execute(args.source_head))
