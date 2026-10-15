"""Thin sequential IR/ArcDice angle pair; no default or comparative gain claim.
SPDX-License-Identifier: GPL-3.0-or-later
Prepare only after the owned control PASSES; each run encloses one fresh arm.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,hashlib,json,os,re,signal,stat,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as io,sexpr as sx,local_settings as ls
from autorouter.runner import run
from scripts import experiment_quality as q
from scripts.fetch_led_demo import capture_native_source
from experiments.native_paired_v1 import observations as obs
from experiments.hfe_original_native_v1 import driver as shared
PREP=ROOT/'.runs/free-angle-pair-preparation-002';PROTOCOL=PREP/'protocol.json'
OUT=ROOT/'.runs/free-angle-pair-002'
CONTROL=ROOT/'.runs/free-angle-native-enclosure-003/result.json'
ORDER=[('ir-obstacle','stock45'),('ir-obstacle','NONE'),('arcdice','stock45'),('arcdice','NONE')]
PROFILES={'stock45':'tuned','NONE':'tuned-free-angle'}
LIMITS=dict(route=120,worker=180,delivered=240,output=128*1024**2,rss=4*1024**3,log=256*1024,publication=2)
GATES={
 'ir-obstacle':['.runs/ir-obstacle-original-native-001/result.json','.runs/ir-obstacle-original-native-readback-001/result.json','.runs/ir-obstacle-original-field-gate-003/result.json'],
 'arcdice':['.runs/arcdice-original-native-001/result.json','.runs/arcdice-original-native-002-readback/result.json']}


OLD_PROTOCOL=ROOT/'.runs/free-angle-pair-preparation-001/protocol.json'
OLD_PROTOCOL_PIN='0380b45d6aa3d3af7bf099a5121b51ed3e3591a1d48eb135723dc5cb6b1b0d2e'
OLD_SCRIPT=ROOT/'.runs/run-free-angle-pair-001.py'
OLD_FOLDER=ROOT/'.runs/free-angle-pair-001/ir-obstacle/stock45'
OLD_CHILD=OLD_FOLDER/'child'
OLD_TIME=ROOT/'.runs/free-angle-pair-execution-001/ir-stock45-time.log'
OLD_CHILD_PIN='7e605755b66d238e1ddabe6c4d057b18afe26ad437c4d11510c4c7df78aad91a'
OLD_TIME_PIN='1a255cb9641b68e2d5c536d211ee944df04052279ced652950e2bc096dc17837'


def same_tools(a,b):
    a,b=dict(a),dict(b);a.pop('git_head',None);b.pop('git_head',None)
    if a!=b:raise p.Rejected('metadata continuation changed tool/core/source implementation')


def retained_basis():
    if p.sha(OLD_PROTOCOL)!=OLD_PROTOCOL_PIN or p.sha(OLD_CHILD/'result.json')!=OLD_CHILD_PIN or p.sha(OLD_TIME)!=OLD_TIME_PIN:raise p.Rejected('fixed failed-attempt/retained-child/time evidence changed')
    plan=f.read_json(OLD_PROTOCOL);child=f.read_json(OLD_CHILD/'result.json')
    if p.sha(OLD_SCRIPT)!=plan['controller_sha256']:raise p.Rejected('failed001 controller changed')
    if (child.get('passed') is not True or child.get('status')!='completed' or child.get('project')!='ir-obstacle'
            or child.get('angle')!='stock45' or child.get('profile')!='tuned' or child.get('scoring_variant')!='via_default'
            or child.get('protocol_sha256')!=OLD_PROTOCOL_PIN or shared.material(OLD_CHILD)!=child.get('completed_evidence')
            or p.sha(OLD_CHILD/'route/result.json')!=child.get('route_receipt_sha256')):raise p.Rejected('retained first child does not bind its completed Native material')
    observed={k:float(v) for k,v in re.findall(r'^(real|user|sys) ([0-9.]+)$',io.read_bytes(OLD_TIME,256*1024).decode(),re.M)}
    if observed!={'real':33.35,'user':24.47,'sys':7.41}:raise p.Rejected('exact complete failed-parent time costs differ')
    if p.sha(OLD_CHILD/'result.json')!=OLD_CHILD_PIN:raise p.Rejected('retained first child changed during read')
    return dict(protocol_sha256=OLD_PROTOCOL_PIN,controller_sha256=plan['controller_sha256'],producer_git_head=plan['git_head'],
        child_receipt_sha256=OLD_CHILD_PIN,old_folder_material=p.tree_hash(OLD_FOLDER),time_log_sha256=OLD_TIME_PIN,
        whole_failed_attempt_wall_seconds=33.35,whole_failed_attempt_full_cpu_seconds=31.88,prior_preparation_costs=plan['preparation_costs']),plan,child


def compatibility(old,current):
    for key in ('limits','profiles','arm_order','scoring_variant','helper_sha256','control_receipt','control_sha256','control_material'):
        if old[key]!=current[key]:raise p.Rejected('continuation changed fixed pair contract: '+key)
    for project in ('ir-obstacle','arcdice'):
        a,b=old['projects'][project],current['projects'][project]
        for key in ('source','family','packet','gates','baseline'):
            if a[key]!=b[key]:raise p.Rejected('continuation changed original project/proof: '+key)
        for key in ('files_sha256','source_hashes'):
            if a['freeze'][key]!=b['freeze'][key]:raise p.Rejected('continuation changed frozen implementation/source')
        same_tools(a['freeze']['tools'],b['freeze']['tools'])


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
    basis,oldplan,_=retained_basis()
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
        recovery=basis,owned_control_producer_git_head=owned['git_head'],
        source_acquisition='Existing immutable local originals; retained first IR45 solver is exact001 evidence; next three source preflights/solvers are fresh.',
        scope='Two exposed existing circuits, ordinary native1000 whole-board corrected adapter, tuned stock45 versus NONE only. No C/portfolio, generalization, independent pedigree, raw CAD publication or default promotion.')
    compatibility(oldplan,plan);context(plan)
    plan['current_preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
    prior=basis['prior_preparation_costs'];now=plan['current_preparation_costs']
    if prior['publication_allowance_seconds']!=2:raise p.Rejected('old preparation publication cost differs')
    plan['preparation_costs']=dict(wall_seconds=prior['wall_seconds']+2+now['wall_seconds'],full_cpu_seconds=prior['full_cpu_seconds']+2+now['full_cpu_seconds'],publication_allowance_seconds=2)
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
    if owned.get('git_head')!=plan['owned_control_producer_git_head']:raise p.Rejected('owned producer checkpoint changed')
    basis,oldplan,_=retained_basis()
    if basis!=plan['recovery']:raise p.Rejected('retained first-arm evidence/costs changed')
    compatibility(oldplan,plan)
    positive=Path(f.read_json(Path(plan['control_receipt']).parent/'native/result.json')['positive']['receipt'])
    same_tools(f.read_json(positive)['tools'],p.tool_manifest())
    if p.tree_hash(Path(plan['control_receipt']).parent)!=plan['control_material']:raise p.Rejected('owned qualification material changed')
    for project,spec in plan['projects'].items():
        board,family,packet=source(project)
        if str(board)!=spec['source'] or family!=spec['family'] or packet!=spec['packet']:raise p.Rejected('original source packet changed')
        q.verify_freeze(spec['freeze'],board)
        for name,digest in spec['gates'].items():
            if p.sha(ROOT/name)!=digest:raise p.Rejected('historical original proof changed')
    if pin is not None and (p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan)):raise p.Rejected('frozen protocol changed')


def worker(plan,pin,project,angle):
    if (project,angle)==ORDER[0]:raise p.Rejected('retained first IR45 must never launch another worker')
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
    if (project,angle)==ORDER[0]:raise p.Rejected('use recover-first; never rerun first IR45')
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
            record.update(wall_seconds=prewall+time.monotonic()-START,full_cpu_seconds=precpu+cpu()-CPU0,publication_allowance_seconds=2)
            if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
            if record['status']!='completed':record['passed']=False
        f.publish(folder,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
        result=f.read_json(folder/'result.json');print(f.canonical({k:result.get(k) for k in ['project','angle','passed','status','wall_seconds','full_cpu_seconds']}))
        return 0 if result.get('passed') is True and result.get('status')=='completed' else 130 if result.get('status')=='cancelled' else 2



def recover_first(plan,pin):
    context(plan,pin);basis,oldplan,child=retained_basis();folder=OUT/'ir-obstacle/stock45'
    if folder.exists() or folder.is_symlink():raise p.Rejected('fresh first-arm recovery output required')
    folder.parent.mkdir(parents=True,exist_ok=True);folder.mkdir();owner={};h.capture_destination(owner,folder)
    prep=plan['preparation_costs'];prewall=prep['wall_seconds']+2;precpu=prep['full_cpu_seconds']+2
    oldwall=basis['whole_failed_attempt_wall_seconds'];oldcpu=basis['whole_failed_attempt_full_cpu_seconds']
    def remaining():return min(238-prewall-oldwall-(time.monotonic()-START),238-precpu-oldcpu-(cpu()-CPU0))
    record=dict(schema=1,accepted=False,passed=False,status='failed',project='ir-obstacle',angle='stock45',
        protocol_sha256=pin,git_head=plan['git_head'],original_protocol=str(OLD_PROTOCOL),original_protocol_sha256=OLD_PROTOCOL_PIN,
        original_child=str(OLD_CHILD/'result.json'),original_child_receipt_sha256=OLD_CHILD_PIN,
        original_outer_remains_failed=True,new_native_execution=False,new_engine_execution=False,
        recovery=basis,preparation_costs=prep,complete_delivered_cap_seconds=240,scope=plan['scope'])
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared lane required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            spec=oldplan['projects']['ir-obstacle'];board=Path(spec['source']);route=OLD_CHILD/'route';data=f.read_json(route/'result.json')
            same_tools(data['tools'],plan['projects']['ir-obstacle']['freeze']['tools'])
            if data['source_hashes']!=spec['freeze']['source_hashes'] or data.get('scoring_variant')!='via_default':raise p.Rejected('retained route source/scoring differs')
            with p.validation_readback_session():
                workers=obs.workers(route,data,board,spec['freeze']['source_hashes'],sx.read(board))
                error=obs.resource_failure(route,data)
                candidate=obs.candidate(route,data,board,sx.read(board),spec['freeze']['source_hashes'],spec['baseline'],resource_error=error)
                arm=dict(id='stock45',adapter='both',engine_profile='tuned',operation='route')
                row=q.summarize(arm,route,data,child['row']['invocation_wall_seconds'],child['row']['invocation_cpu_seconds'])
                row['observations']=q.observations(route,data,row)
            if (f.canonical(row)!=f.canonical(child['row']) or f.canonical(workers)!=f.canonical(child['workers'])
                    or f.canonical(candidate)!=f.canonical(child['candidate']) or error!=child['resource_failure'] or row['accepted'] is not True):raise p.Rejected('retained first semantic observation differs')
            record.update(passed=True,status='completed',row=row,retained_worker_count=len(workers),retained_candidate=candidate)
        except (Exception,KeyboardInterrupt) as exc:record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc))
        witness=shared.material(folder);record['completed_evidence']=witness
        def stable():
            h.owned_destination(owner);context(plan,pin)
            if shared.material(folder)!=witness or retained_basis()[0]!=basis:raise p.Rejected('retained recovery/old evidence changed')
            if record['passed']:p.check_result(OLD_CHILD/'route/result.json')
            if shared.material(folder)!=witness or retained_basis()[0]!=basis:raise p.Rejected('recovery evidence changed late')
            ls.check_normal_policy(OLD_CHILD/'route',f.read_json(OLD_CHILD/'route/result.json'),max_bytes=LIMITS['output'],max_files=2048)
        def account():
            record.update(recovery_wall_seconds=time.monotonic()-START,recovery_full_cpu_seconds=cpu()-CPU0,
                wall_seconds=prewall+oldwall+time.monotonic()-START,full_cpu_seconds=precpu+oldcpu+cpu()-CPU0,publication_allowance_seconds=2)
            if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
            if record['status']!='completed':record['passed']=False
        f.publish(folder,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
        result=f.read_json(folder/'result.json');print(f.canonical({k:result.get(k) for k in ['project','angle','passed','status','wall_seconds','full_cpu_seconds']}))
        return 0 if result.get('passed') is True and result.get('status')=='completed' else 130 if result.get('status')=='cancelled' else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=['prepare','run','worker','recover-first'],required=True)
    parser.add_argument('--source-head',required=True);parser.add_argument('--protocol-sha256');parser.add_argument('--control-sha256')
    parser.add_argument('--control-receipt',type=Path,default=CONTROL)
    parser.add_argument('--project',choices=['ir-obstacle','arcdice']);parser.add_argument('--arm',choices=list(PROFILES));args=parser.parse_args()
    def cancel(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,cancel)
    if args.mode=='prepare':prepare(args.source_head,args.control_sha256,args.control_receipt)
    else:
        plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
        if args.mode=='recover-first':args.project,args.arm=ORDER[0]
        if plan['git_head']!=args.source_head or args.protocol_sha256!=pin or (args.project,args.arm) not in ORDER:raise p.Rejected('exact frozen intended arm required')
        raise SystemExit(recover_first(plan,pin) if args.mode=='recover-first' else worker(plan,pin,args.project,args.arm) if args.mode=='worker' else execute(plan,pin,args.project,args.arm))
