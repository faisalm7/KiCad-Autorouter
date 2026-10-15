"""Thin sequential IR/ArcDice angle pair; no default or comparative gain claim.
SPDX-License-Identifier: GPL-3.0-or-later
Prepare only after the owned control PASSES; each run encloses one fresh arm.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,hashlib,json,os,signal,stat,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as io,sexpr as sx,local_settings as ls
from autorouter.runner import run
from scripts import experiment_quality as q
from scripts.fetch_led_demo import capture_native_source
from experiments.native_paired_v1 import observations as obs
from experiments.hfe_original_native_v1 import driver as shared
PREP=ROOT/'.runs/free-angle-pair-preparation-001';PROTOCOL=PREP/'protocol.json'
OUT=ROOT/'.runs/free-angle-pair-001'
CONTROL=ROOT/'.runs/free-angle-native-enclosure-003/result.json'
ORDER=[('ir-obstacle','stock45'),('ir-obstacle','NONE'),('arcdice','stock45'),('arcdice','NONE')]
PROFILES={'stock45':'tuned','NONE':'tuned-free-angle'}
LIMITS=dict(route=120,worker=180,delivered=240,output=128*1024**2,rss=4*1024**3,log=256*1024,publication=2)
GATES={
 'ir-obstacle':['.runs/ir-obstacle-original-native-001/result.json','.runs/ir-obstacle-original-native-readback-001/result.json','.runs/ir-obstacle-original-field-gate-003/result.json'],
 'arcdice':['.runs/arcdice-original-native-001/result.json','.runs/arcdice-original-native-002-readback/result.json']}


def control(pin,path=CONTROL):
    path=ls.canonical(Path(path))
    if ROOT/'.runs' not in path.parents or path.name!='result.json':raise p.Rejected('local canonical owned control receipt required')
    if p.sha(path)!=pin:raise p.Rejected('fixed owned control receipt changed')
    data=f.read_json(path);folder=path.parent/'native';child=f.read_json(folder/'result.json')
    if (data.get('kind')!='actual-complete-owned-stock-free-angle-native-v1' or data.get('passed') is not True
            or data.get('status')!='completed' or data.get('child_completed_evidence_bound') is not True
            or child.get('passed') is not True or child.get('status')!='completed'
            or not child.get('positive') or not child.get('physical_short') or len(child.get('loader_observations',[]))!=4
            or p.sha(folder/'result.json')!=data.get('child_receipt_sha256')
            or p.tree_hash(folder)!=data.get('child_material_sha256')
            or shared.material(folder)!=child.get('completed_evidence')):
        raise p.Rejected('actual owned loader/fullSCH/short control has not passed intact')
    receipt=Path(child['positive'].get('receipt',str(folder/'route/result.json')))
    p.check_result(receipt)
    positive=f.read_json(receipt)
    if p.sha(receipt)!=child['positive']['receipt_sha256'] or p.tree_hash(receipt.parent)!=child['positive']['retained_material_sha256']:raise p.Rejected('retained actual positive changed')
    ls.check_normal_policy(receipt.parent,positive,max_bytes=LIMITS['output'],max_files=2048)
    bad=child['physical_short']
    ls.check_normal_policy(folder/'invalid-job',dict(steps=bad['steps'],source_hashes=bad['before'],tools=child['tools']),max_bytes=LIMITS['output'],max_files=2048)
    return data


def source(project):
    board,family=q.selected_source(project);packet,files=capture_native_source(project,root=ROOT)
    return board,family,dict(packet=str(packet),files={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()})


def prepare(head,control_pin,control_path):
    shared.clean(head);owned=control(control_pin,control_path)
    if owned['git_head']!=head:raise p.Rejected('owned control must bind this exact current checkpoint')
    PREP.mkdir();projects={}
    for project in ('ir-obstacle','arcdice'):
        board,family,packet=source(project);freeze=q.freeze(board);p.preflight(board)
        gates={n:p.sha(ROOT/n) for n in GATES[project]}
        original=f.read_json(ROOT/GATES[project][-1])
        baseline=original['qualified_native'] if project=='ir-obstacle' else original['native']
        if not p.native_accepted(baseline):raise p.Rejected('qualified original fullSCH baseline unavailable')
        projects[project]=dict(source=str(board),family=family,packet=packet,freeze=freeze,gates=gates,baseline=baseline)
    plan=dict(schema=1,kind='fresh-ir-arcdice-corrected-tuned-angle-pair-v1',status='frozen',git_head=head,
        helper_sha256={n:p.sha(ROOT/n) for n in ['experiments/native_paired_v1/observations.py','experiments/native_paired_v1/readback.py','scripts/experiment_paired.py','experiments/hfe_original_native_v1/driver.py']},controller_sha256=p.sha(Path(__file__)),control_receipt=str(ls.canonical(control_path)),control_sha256=control_pin,control_material=p.tree_hash(control_path.parent),
        projects=projects,arm_order=[list(x) for x in ORDER],profiles=PROFILES,scoring_variant='via_default',limits=LIMITS,
        source_acquisition='Existing immutable local originals; no GET or historical solver reuse. Source-preflight work is fresh inside each arm.',
        scope='Two exposed existing circuits, ordinary native1000 whole-board corrected adapter, tuned stock45 versus NONE only. No C/portfolio, generalization, independent pedigree, raw CAD publication or default promotion.')
    context(plan)
    plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
    if max(plan['preparation_costs']['wall_seconds'],plan['preparation_costs']['full_cpu_seconds'])+2>=58:raise p.Rejected('preparation exhausted fixed complete-delivery margin')
    p.save_json(PROTOCOL,plan);print(f.canonical(dict(prepared=True,protocol=str(PROTOCOL),sha256=p.sha(PROTOCOL),native_executed=False)))


def context(plan,pin=None):
    shared.clean(plan['git_head'])
    if (plan.get('kind')!='fresh-ir-arcdice-corrected-tuned-angle-pair-v1' or plan.get('status')!='frozen'
            or plan.get('limits')!=LIMITS or plan.get('profiles')!=PROFILES or plan.get('arm_order')!=[list(x) for x in ORDER]
            or set(plan.get('projects',{}))!={'ir-obstacle','arcdice'}
            or plan.get('scoring_variant')!='via_default' or p.sha(Path(__file__))!=plan['controller_sha256']):raise p.Rejected('fixed pair protocol/controller differs')
    if any(p.sha(ROOT/n)!=value for n,value in plan['helper_sha256'].items()):raise p.Rejected('frozen pair helper changed')
    owned=control(plan['control_sha256'],Path(plan['control_receipt']))
    if owned.get('git_head')!=plan['git_head']:raise p.Rejected('owned qualification checkpoint differs')
    if p.tree_hash(Path(plan['control_receipt']).parent)!=plan['control_material']:raise p.Rejected('owned qualification material changed')
    for project,spec in plan['projects'].items():
        board,family,packet=source(project)
        if str(board)!=spec['source'] or family!=spec['family'] or packet!=spec['packet']:raise p.Rejected('original source packet changed')
        q.verify_freeze(spec['freeze'],board)
        for name,digest in spec['gates'].items():
            if p.sha(ROOT/name)!=digest:raise p.Rejected('historical original proof changed')
    if pin is not None and (p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan)):raise p.Rejected('frozen protocol changed')


def worker(plan,pin,project,angle):
    context(plan,pin);spec=plan['projects'][project];board=Path(spec['source']);folder=OUT/project/angle/'child'
    folder.mkdir();owner={};h.capture_destination(owner,folder)
    record=dict(schema=1,accepted=False,passed=False,status='failed',project=project,angle=angle,profile=PROFILES[angle],
        scoring_variant='via_default',protocol_sha256=pin,git_head=plan['git_head'],tools=spec['freeze']['tools'],scope=plan['scope'])
    routed=None
    try:
        route_start,route_cpu=time.monotonic(),cpu()
        routed=p.route(board,folder/'route',120,False,'both',PROFILES[angle],scoring_variant='via_default')
        route_wall,route_full=time.monotonic()-route_start,cpu()-route_cpu
        stored=f.read_json(folder/'route/result.json')
        if f.canonical(stored)!=f.canonical(routed):raise p.Rejected('returned routing receipt differs from stored snapshot')
        if stored.get('tools')!=record['tools'] or stored.get('source_hashes')!=spec['freeze']['source_hashes']:raise p.Rejected('fresh result source/tool binding differs')
        with p.validation_readback_session():
            record['workers']=obs.workers(folder/'route',stored,board,spec['freeze']['source_hashes'],sx.read(board))
            error=obs.resource_failure(folder/'route',stored)
            if (folder/'route/final-drc.json').is_file():
                record['candidate']=obs.candidate(folder/'route',stored,board,sx.read(board),spec['freeze']['source_hashes'],spec['baseline'],resource_error=error)
            arm=dict(id=angle,adapter='both',engine_profile=PROFILES[angle],operation='route')
            row=q.summarize(arm,folder/'route',stored,route_wall,route_full)
            row['observations']=q.observations(folder/'route',stored,row)
        record.update(row=row,route_receipt_sha256=p.sha(folder/'route/result.json'),resource_failure=error,
            passed=row['accepted'],status='completed')
        if not record['passed']:record['status']='failed'
    except (Exception,KeyboardInterrupt) as exc:
        record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) or routed and q.cancelled(routed) else 'failed',error=type(exc).__name__+': '+str(exc))
    witness=shared.material(folder);record['completed_evidence']=witness
    def remaining():return min(178-(time.monotonic()-START),178-(cpu()-CPU0))
    def stable():
        h.owned_destination(owner);context(plan,pin)
        if shared.material(folder)!=witness:raise p.Rejected('completed arm evidence changed')
        if routed is not None and routed.get('accepted') is True:p.check_result(folder/'route/result.json')
        if shared.material(folder)!=witness:raise p.Rejected('completed arm evidence changed late')
        if routed is not None:ls.check_normal_policy(folder/'route',routed,max_bytes=LIMITS['output'],max_files=2048)
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
        if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
        if record['status']!='completed':record['passed']=False
    f.publish(folder,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    result=f.read_json(folder/'result.json');return 0 if result.get('passed') is True and result.get('status')=='completed' else 130 if result.get('status')=='cancelled' else 2


def execute(plan,pin,project,angle):
    context(plan,pin);index=ORDER.index((project,angle))
    # Four fresh explicit commands, frozen order; failures retained, cancellation stops.
    for prior_project,prior_angle in ORDER[:index]:
        prior=f.read_json(OUT/prior_project/prior_angle/'result.json')
        if prior.get('protocol_sha256')!=pin or prior.get('status')=='cancelled':raise p.Rejected('prior arm absent/different/cancelled')
    folder=OUT/project/angle
    if folder.exists() or folder.is_symlink():raise p.Rejected('fresh exclusive arm output required')
    folder.parent.mkdir(parents=True,exist_ok=True);folder.mkdir();owner={};h.capture_destination(owner,folder)
    prep=plan['preparation_costs'];prewall=prep['wall_seconds']+2;precpu=prep['full_cpu_seconds']+2
    def remaining():return min(238-prewall-(time.monotonic()-START),238-precpu-(cpu()-CPU0))
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared lane required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__)), '--mode','worker','--source-head',plan['git_head'],'--protocol-sha256',pin,'--project',project,'--arm',angle]
        process=run(argv,cwd=folder,log=folder/'command.log',timeout=max(.001,min(180,remaining())),max_log_bytes=LIMITS['log'],max_workdir_bytes=LIMITS['output'],max_group_rss_bytes=LIMITS['rss'])
        path=folder/'child/result.json';childpin=p.sha(path) if path.is_file() else None
        child=f.read_json(path) if childpin else None;literal=f.canonical(child)
        bound=bool(child and child.get('completed_evidence')==shared.material(folder/'child') and p.sha(path)==childpin and f.canonical(f.read_json(path))==literal)
        witness=shared.material(folder);passed=bool(bound and child.get('passed') is True and child.get('status')=='completed' and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
        record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'cancelled' if process['status']=='cancelled' or child and child.get('status')=='cancelled' else 'failed',
            project=project,angle=angle,protocol_sha256=pin,git_head=plan['git_head'],controller_sha256=plan['controller_sha256'],process=process,
            child_receipt_sha256=childpin,child_completed_evidence_bound=bound,child=child,completed_evidence=witness,
            preparation_costs=prep,complete_delivered_cap_seconds=240,scope=plan['scope'],
            accounting_scope='Actual enclosing self+reaped-descendant CPU/wall includes full child routing, semantic readback and child publication tail; final enclosing publication bounded separately by2s allowance, with actual late cap enforcement.')
        def stable():
            h.owned_destination(owner);context(plan,pin)
            if shared.material(folder)!=witness:raise p.Rejected('complete enclosing material changed')
            if child is not None and (not bound or p.sha(path)!=childpin or f.canonical(f.read_json(path))!=literal or shared.material(folder/'child')!=child['completed_evidence']):raise p.Rejected('published child changed after exit')
            if child is not None and child.get('route_receipt_sha256'):
                route_data=f.read_json(folder/'child/route/result.json')
                ls.check_normal_policy(folder/'child/route',route_data,max_bytes=LIMITS['output'],max_files=2048)
        def account():
            record.update(wall_seconds=prewall+time.monotonic()-START,full_cpu_seconds=prepcpu+cpu()-CPU0,publication_allowance_seconds=2)
            if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
            if record['status']!='completed':record['passed']=False
        f.publish(folder,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
        result=f.read_json(folder/'result.json');print(f.canonical({k:result.get(k) for k in ['project','angle','passed','status','wall_seconds','full_cpu_seconds']}))
        return 0 if result.get('passed') is True and result.get('status')=='completed' else 130 if result.get('status')=='cancelled' else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=['prepare','run','worker'],required=True)
    parser.add_argument('--source-head',required=True);parser.add_argument('--protocol-sha256');parser.add_argument('--control-sha256')
    parser.add_argument('--control-receipt',type=Path,default=CONTROL)
    parser.add_argument('--project',choices=['ir-obstacle','arcdice']);parser.add_argument('--arm',choices=list(PROFILES));args=parser.parse_args()
    def cancel(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,cancel)
    if args.mode=='prepare':prepare(args.source_head,args.control_sha256,args.control_receipt)
    else:
        plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
        if plan['git_head']!=args.source_head or args.protocol_sha256!=pin or (args.project,args.arm) not in ORDER:raise p.Rejected('exact frozen intended arm required')
        raise SystemExit(worker(plan,pin,args.project,args.arm) if args.mode=='worker' else execute(plan,pin,args.project,args.arm))
