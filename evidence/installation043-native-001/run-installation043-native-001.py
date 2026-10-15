"""Fresh installed043 owned-v2 fullSCH stock-NONE integration; draft only.
SPDX-License-Identifier: GPL-3.0-or-later
One script: source preparation, installed worker and complete installed enclosure.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,hashlib,json,math,os,shutil,signal,stat,sys
# A copied companion is nested inside the original source's installed checkout.
ROOT=[x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file()][-1]
BASE=ROOT/'.runs/installation-043';CLONE=BASE/'checkout'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=('prepare','run','worker','read'),required=True)
parser.add_argument('--source-head',required=True);parser.add_argument('--protocol-sha256')
args=parser.parse_args() if __name__=='__main__' else None
PREPARING=args is not None and args.mode=='prepare'
sys.path.insert(0,str(ROOT if PREPARING else CLONE));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,config as c,sexpr as sx,board_floor as g,chain_proposals as cp,local_settings as ls
from autorouter.runner import run
from scripts import install_smoke as install
from experiments.free_angle_baseline_v1 import fixture
PREP=ROOT/'.runs/installation043-angle-preparation-001';PROTOCOL=PREP/'protocol.json'
OUT=ROOT/'.runs/installation043-angle-complete-001';WORK=CLONE/'.runs/installation043-angle'
COPY=WORK/'installed_angle.py';NATIVE=WORK/'native'
LIMITS=dict(route_wall_full_cpu_seconds=120,whole_wall_full_cpu_seconds=180,worker_seconds=176,publication_allowance_seconds=2,scratch_bytes=128*1024**2,group_rss_bytes=4*1024**3,log_bytes=256*1024)


def context(plan,pin=None):
    expected_root=ROOT if PREPARING else CLONE
    if c.ROOT!=expected_root or any(not Path(m.__file__).resolve().is_relative_to(expected_root) for m in (p,f,h,c,install,fixture,cp,ls)):
        raise p.Rejected('prepare/source or execute/installed module context differs')
    if not PREPARING:
        if Path(sys.executable)!=CLONE/'.venv/bin/python' or Path(sys.prefix).resolve()!=CLONE/'.venv' or sys.prefix==sys.base_prefix:raise p.Rejected('independent installed interpreter required')
        for name,module in tuple(sys.modules.items()):
            if name.split('.')[0] in {'autorouter','scripts','experiments','tests'} and getattr(module,'__file__',None) and not Path(module.__file__).resolve().is_relative_to(CLONE):raise p.Rejected('project import escaped installed checkout: '+name)
    if (plan.get('kind')!='installation043-owned-v2-free-angle-v1' or plan.get('limits')!=LIMITS
            or plan.get('status')!='frozen_for_lead_execution' or plan.get('checkout')!=str(CLONE)
            or plan.get('native_output')!=str(NATIVE) or plan.get('profile')!='tuned-free-angle'
            or plan.get('scoring_variant')!='via_default' or plan.get('native_version')!='10.0.0'):
        raise p.Rejected('fixed installed owned-v2 scope differs')
    tools=p.tool_manifest()
    if tools!=(plan['source_tools'] if PREPARING else plan['installed_tools']):raise p.Rejected('current pinned tool/implementation/HEAD differs')
    if p.sha(BASE/'result.json')!=plan['installation_receipt_sha256'] or p.sha(BASE/'source-tracked.json')!=plan['source_inventory_sha256']:raise p.Rejected('base installation material changed')
    receipt=f.read_json(BASE/'result.json');listing=(BASE/'03-source-files.log').read_text();source=f.read_json(BASE/'source-tracked.json');selected=install.distribution_listing(listing)
    for root,rows in ((ROOT,listing),(CLONE,selected)):
        expected=source if root==ROOT else {n:source[n] for n in selected.split('\0') if n}
        if install.tracked_inventory(root,rows)!=expected:raise p.Rejected('complete source/distribution changed')
        if install.git_identity(root,plan['git_head'],receipt['source_branch'] if root==ROOT else None)!=receipt['git_identity_witnesses'][str(root)]:raise p.Rejected('source/installed file-only Git identity changed')
    if p.sha(COPY)!=plan['companion_sha256'] or p.sha(Path(plan['controller_source']))!=plan['controller_sha256'] or p.sha(Path(__file__))!=plan['controller_sha256']:raise p.Rejected('controller/installed companion changed')
    if any(p.sha(expected_root/name)!=value for name,value in plan['fixture_code_sha256'].items()):raise p.Rejected('owned generator/base changed')
    if {n:hashlib.sha256(raw).hexdigest() for n,raw in fixture.files().items()}!=plan['fixture_files_sha256']:raise p.Rejected('owned-v2 complete source differs')
    for tools in (plan['source_tools'],plan['installed_tools']):
        for name,value in tools['files'].items():
            if p.sha(Path(name))!=value:raise p.Rejected('pinned original/copied tool changed')
    original=Path(plan['original_jar']);copy=CLONE/'.tools'/original.name
    if copy.is_symlink() or original.is_symlink() or copy.stat().st_ino==original.stat().st_ino or p.sha(copy)!=plan['jar_sha256']:raise p.Rejected('independent copied JAR required')
    if pin is not None and (p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan)):raise p.Rejected('prospective protocol changed')


def prepare(head):
    receipt=f.read_json(BASE/'result.json');tools=p.tool_manifest()
    if (receipt.get('passed') is not True or receipt.get('status')!='passed' or receipt.get('source_installation_mode')!='distribution'
            or receipt.get('git_head')!=head or tools['git_head']!=head or receipt.get('source_checkout')!=str(ROOT) or receipt.get('output')!=str(BASE)):
        raise p.Rejected('completed current ordinary043 distribution baseline required')
    PREP.mkdir();WORK.mkdir();shutil.copyfile(Path(__file__),COPY)
    installed=json.loads(json.dumps(tools));installed['files'].pop(str(c.JAR));installed['files'][str(CLONE/'.tools'/c.JAR.name)]=c.JAR_SHA256
    files=fixture.files();tree=sx.parse(files[fixture.STEM+'.kicad_pcb'].decode());protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},tree)
    if len(files)!=4 or fixture.SOURCE_ID!='owned-free-angle-native-v2' or len(protected)!=1 or len(p.routes(tree))!=1:raise p.Rejected('fixed complete owned-v2/one KEEP source required')
    code=[Path(fixture.__file__),Path(fixture.base.__file__)]
    plan=dict(schema=1,kind='installation043-owned-v2-free-angle-v1',status='frozen_for_lead_execution',git_head=head,
        installation=str(BASE),checkout=str(CLONE),native_output=str(NATIVE),profile='tuned-free-angle',scoring_variant='via_default',native_version='10.0.0',
        installation_receipt_sha256=p.sha(BASE/'result.json'),source_inventory_sha256=receipt['source_inventory_sha256'],
        source_tools=tools,installed_tools=installed,original_jar=str(c.JAR),jar_sha256=c.JAR_SHA256,
        controller_source=str(Path(__file__).resolve()),controller_sha256=p.sha(Path(__file__)),companion_sha256=p.sha(COPY),
        fixture_code_sha256={str(n.relative_to(ROOT)):p.sha(n) for n in code},fixture_files_sha256={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()},protected_ast=protected,limits=LIMITS,
        scope='ONE fresh installed043 default1000 owned-v2 corrected tuned-free-angle via_default whole-board120route/180whole. Requires original1open to0/0/6warnings full6component fields, non45 ROUTE, exact protected KEEP/source/rules/PRL. Existing default60mm PCB-only smoke is a separate base043 outcome. No repeated root loaders/negative,4Cu/1007,external board,GUI/physical/family/comparative/default promotion.')
    context(plan);plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
    if max(plan['preparation_costs']['wall_seconds'],plan['preparation_costs']['full_cpu_seconds'])+2>=30:raise p.Rejected('installed preparation exceeded fixed complete-case margin')
    p.save_json(PROTOCOL,plan);print(f.canonical(dict(prepared=True,protocol=str(PROTOCOL),sha256=p.sha(PROTOCOL),native_executed=False)))


def read_transport(plan,pin=None):
    context(plan,pin);material=f.evidence_inventory(NATIVE);receipt=NATIVE/'route/result.json';receipt_pin=p.sha(receipt);data=f.read_json(receipt)
    source=NATIVE/'source'/(fixture.STEM+'.kicad_pcb');candidate=Path(data['candidate']);original=sx.read(source);current=sx.read(candidate)
    if (data.get('tools')!=plan['installed_tools'] or data.get('source')!=str(source) or data.get('engine_profile')!='tuned-free-angle'
            or data.get('adapter')!='both' or data.get('scoring_variant')!='via_default' or data.get('scope')!='whole_board_unlocked_routing'
            or data.get('budget_seconds')!=120 or data.get('cpu_budget_seconds')!=120):raise p.Rejected('installed original/budget/profile/tool scope differs')
    if p.tree_hash(source.parent)!=plan['fixture_files_sha256'] or data['source_hashes']!=plan['fixture_files_sha256']:raise p.Rejected('complete authored source changed')
    if not source.with_suffix('.kicad_sch').is_file() or source.with_suffix('.kicad_dru').exists() or p.immutable(original)!=p.immutable(current):raise p.Rejected('original source/rules/fullSCH invariants changed')
    protected=p.protected_for_record(data,original)
    if protected!=plan['protected_ast'] or len(p.routes(original))!=1 or any(row not in p.routes(current) for row in protected):raise p.Rejected('original protected KEEP differs')
    _,resolve=g.source_net_identity(current);oblique=[]
    for row in p.routes(current):
        if row[0]!='segment' or row in protected or resolve(sx.one(row,'net'))!='ROUTE':continue
        a,b=cp.xy(sx.one(row,'start')),cp.xy(sx.one(row,'end'));dx,dy=abs(b[0]-a[0]),abs(b[1]-a[1])
        if min(dx,dy)>100000 and abs(dx-dy)>100000:oblique.append(row)
    checked=p.check_result(receipt)
    before,native=data['source_drc'],data['native']
    if (checked.get('current') is not True or data.get('accepted') is not True or not oblique or before['opens']!=1 or before['blocking']
            or not p.native_accepted(native) or native['warnings']!=6 or native['exclusions']!=0
            or data.get('schematic_parity')!='checked by final native DRC'
            or native.get('field_parity',{}).get('qualification',{}).get('component_count')!=6):raise p.Rejected('owned-v2 original/fullSCH/non45 outcome incomplete')
    if data['metrics']!=f.read_json(receipt.parent/'metrics.json') or data['metrics']['version']!='10.0.0' or data['metrics']['copper_layers']!=2:raise p.Rejected('bound actual Native metrics differ')
    if p.sha(candidate)!=data['candidate_sha256'] or p.sha(receipt.parent/'final-drc.json')!=data['native_report_sha256']:raise p.Rejected('candidate/report hash differs')
    p.check_resource_accounting(data);context(plan,pin)
    if p.sha(receipt)!=receipt_pin or f.canonical(f.read_json(receipt))!=f.canonical(data) or f.evidence_inventory(NATIVE)!=material:raise p.Rejected('completed installed material changed during readback')
    ls.check_normal_policy(receipt.parent,data,max_bytes=128*1024**2,max_files=2048)
    return dict(passed=True,route_receipt_sha256=receipt_pin,candidate_sha256=data['candidate_sha256'],native_report_sha256=data['native_report_sha256'],
        metrics=data['metrics'],source_counts={k:before[k] for k in ('opens','blocking','warnings','exclusions')},final_counts={k:native[k] for k in ('opens','blocking','warnings','exclusions')},
        complete_field_components=6,protected_routes=1,non45_route_segments=oblique,worker_count=len(data['steps']),shared_readback=checked,material=material)


def worker(plan,pin):
    context(plan,pin)
    if NATIVE.exists() or NATIVE.is_symlink():raise p.Rejected('fresh installed Native output required')
    NATIVE.mkdir();owner={};h.capture_destination(owner,NATIVE);fixture.write_project(NATIVE/'source')
    record=dict(schema=1,accepted=False,passed=False,status='failed',git_head=plan['git_head'],protocol_sha256=pin,tools=plan['installed_tools'],scope=plan['scope']);routed=None
    config=(c.CLI,c.PYTHON,c.PCBNEW,c.JAR,c.JAVA)
    try:
        routed=p.route(NATIVE/'source'/(fixture.STEM+'.kicad_pcb'),NATIVE/'route',120,False,'both','tuned-free-angle',scoring_variant='via_default')
        if routed.get('accepted') is not True:raise p.Rejected('fresh installed route refused: '+str(routed.get('reason',routed.get('status'))))
        if f.canonical(f.read_json(NATIVE/'route/result.json'))!=f.canonical(routed):raise p.Rejected('producer returned/stored snapshot differs')
        record.update(passed=True,status='completed',transport=read_transport(plan,pin))
    except (Exception,KeyboardInterrupt) as exc:
        record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) or routed and (routed.get('status')=='cancelled' or any(x.get('status')=='cancelled' for x in routed.get('steps',[]))) else 'failed',error=type(exc).__name__+': '+str(exc))
    witness=f.evidence_inventory(NATIVE);record['completed_evidence']=witness
    def remaining():return min(174-(time.monotonic()-START),174-(cpu()-CPU0))
    def fresh():
        h.owned_destination(owner);context(plan,pin)
        if config!=(c.CLI,c.PYTHON,c.PCBNEW,c.JAR,c.JAVA) or f.evidence_inventory(NATIVE)!=witness or p.tree_hash(NATIVE/'source')!=plan['fixture_files_sha256']:raise p.Rejected('installed config/source/completed material changed')
        if record['passed']:ls.check_normal_policy(NATIVE/'route',f.read_json(NATIVE/'route/result.json'),max_bytes=128*1024**2,max_files=2048)
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
        if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
        if record['status']!='completed':record['passed']=False
    def final_check():
        fresh()
        if record['passed'] and read_transport(plan,pin)!=record['transport']:raise p.Rejected('late installed shared proof differs')
        fresh()
    f.publish(NATIVE,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final_check)
    stored=f.read_json(NATIVE/'result.json')
    if f.canonical(stored)!=f.canonical(record):raise p.Rejected('installed child stored literal differs')
    return 0 if stored.get('passed') is True and stored.get('status')=='completed' else 130 if stored.get('status')=='cancelled' else 2


def execute(plan,pin):
    context(plan,pin)
    if NATIVE.exists() or NATIVE.is_symlink():raise p.Rejected('fresh installed case required')
    OUT.mkdir();owner={};h.capture_destination(owner,OUT);prior=plan['preparation_costs'];pw=prior['wall_seconds']+2;pcpu=prior['full_cpu_seconds']+2
    if prior['publication_allowance_seconds']!=2 or any(type(prior[k])not in (int,float) or not math.isfinite(prior[k]) or prior[k]<0 for k in ('wall_seconds','full_cpu_seconds')):raise p.Rejected('invalid preparation costs')
    def remaining():return min(178-pw-(time.monotonic()-START),178-pcpu-(cpu()-CPU0))
    env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PIP_NO_INDEX='1')
    for key,name in (('KICAD_CONFIG_HOME','kicad-config'),('KICAD_CACHE_HOME','kicad-cache'),('KICAD_DOCUMENTS_HOME','kicad-documents')):
        folder=OUT/name;(folder/('10.0' if key=='KICAD_CONFIG_HOME' else 'kicad/10.0')).mkdir(parents=True);env[key]=str(folder)
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared lane required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        argv=[*f.SANDBOX,str(CLONE/'.venv/bin/python'),'-B',str(COPY),'--mode','worker','--source-head',plan['git_head'],'--protocol-sha256',pin]
        process=run(argv,cwd=WORK,env=env,log=OUT/'command.log',timeout=max(.001,min(176,remaining())),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
        childpath=NATIVE/'result.json';childpin=p.sha(childpath) if childpath.is_file() else None;child=f.read_json(childpath) if childpin else None;literal=f.canonical(child)
        bound=bool(child and child.get('completed_evidence')==f.evidence_inventory(NATIVE) and p.sha(childpath)==childpin and f.canonical(f.read_json(childpath))==literal)
        material=p.tree_hash(WORK);logpin=p.sha(OUT/'command.log');witness=f.evidence_inventory(OUT)
        passed=bool(bound and child.get('passed') is True and child.get('status')=='completed' and child.get('accepted') is False and child.get('tools')==plan['installed_tools'] and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
        record=dict(schema=1,kind='actual-complete-installed043-owned-v2',accepted=False,passed=passed,status='completed' if passed else 'cancelled' if process['status']=='cancelled' or child and child.get('status')=='cancelled' else 'failed',
            git_head=plan['git_head'],protocol_sha256=pin,controller_sha256=plan['controller_sha256'],process=process,child_receipt_sha256=childpin,child_literal=literal,child_completed_evidence_bound=bound,
            installed_work_material=material,log_sha256=logpin,completed_evidence=witness,preparation_costs=prior,limits=LIMITS,scope=plan['scope'],
            cost_scope='Actual self+reaped child includes complete worker routing/shared-check/publication tails and preparation; enclosing publication sample+2allowance, with actual late wall/fullCPU guards.')
        def fresh():
            h.owned_destination(owner);context(plan,pin)
            if p.tree_hash(WORK)!=material or p.sha(OUT/'command.log')!=logpin or f.evidence_inventory(OUT)!=witness:raise p.Rejected('complete installed enclosing material changed')
            if child is not None and (not bound or p.sha(childpath)!=childpin or f.canonical(f.read_json(childpath))!=literal or f.evidence_inventory(NATIVE)!=child['completed_evidence']):raise p.Rejected('published child changed after exit')
            if record['passed']:ls.check_normal_policy(NATIVE/'route',f.read_json(NATIVE/'route/result.json'),max_bytes=128*1024**2,max_files=2048)
        def account():
            record.update(wall_seconds=pw+time.monotonic()-START,full_cpu_seconds=pcpu+cpu()-CPU0,publication_allowance_seconds=2)
            if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
            if record['status']!='completed':record['passed']=False
        def final_check():
            fresh()
            if record['passed'] and read_transport(plan,pin)!=child['transport']:raise p.Rejected('outer installed full shared proof differs')
            fresh()
        f.publish(OUT,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final_check)
        result=f.read_json(OUT/'result.json');print(f.canonical({k:result.get(k) for k in ['passed','status','wall_seconds','full_cpu_seconds','child_completed_evidence_bound']}))
        return 0 if result.get('passed') is True and result.get('status')=='completed' else 130 if result.get('status')=='cancelled' else 2


if __name__=='__main__':
    def cancel(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,cancel)
    if args.mode=='prepare':prepare(args.source_head)
    else:
        plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
        if args.protocol_sha256!=pin or plan['git_head']!=args.source_head:raise p.Rejected('exact frozen source/protocol required')
        if args.mode=='read':print(f.canonical(read_transport(plan,pin)))
        else:raise SystemExit(worker(plan,pin) if args.mode=='worker' else execute(plan,pin))
