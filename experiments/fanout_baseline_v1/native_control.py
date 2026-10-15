"""One fresh non-strict owned fanout-False Native branch control, not quality.
Reuse existing route/shared Native readers, BoundJob negative and publisher.
Root must first integrate/checkpoint passing fanout software/source changes.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,hashlib,math,os,signal,stat,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as io,sexpr as sx,board_floor as g,chain_proposals as cp,local_settings as ls,engine_angle as angle,adapter as dsn
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as shared
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.free_angle_baseline_v1 import controls
from experiments.fanout_baseline_v1 import fixture
PREP=ROOT/'.runs/fanout-native-control-preparation-001';PROTOCOL=PREP/'protocol.json'
OUT=ROOT/'.runs/fanout-native-control-001';CHILD=OUT/'native'
LIMITS=dict(route_wall_full_cpu_seconds=120,whole_wall_full_cpu_seconds=180,publication_allowance_seconds=2,scratch_bytes=128*1024**2,group_rss_bytes=4*1024**3,log_bytes=256*1024)
SCOPE='Fresh owned exposed NONSTRICT synthetic branch control: free-angle fanoutFalse positive plus same-original physical-short negative. Only source creation minimum.25→0 differs; Default.30 targets/priority/fullSCH/KEEP unchanged. No source repair, quality/comparative/family/default/GUI/installed/physical approval claim.'


def hashes(files):return {n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}


def context(plan,pin=None):
    shared.clean(plan['git_head'])
    if (plan.get('kind')!='owned-nonstrict-fanout-false-v1' or plan.get('limits')!=LIMITS
            or plan.get('status')!='frozen_for_lead_execution' or plan.get('source_id')!=fixture.SOURCE_ID
            or plan.get('profile')!=angle.PROFILE or plan.get('fanout_enabled') is not False or plan['tools'].get('kicad')!='10.0.0'
            or p.tool_manifest()!=plan['tools'] or hashes(fixture.files())!=plan['source_sha256']
            or p.tree_hash(PREP/'source')!=plan['source_sha256']
            or any(p.sha(ROOT/n)!=value for n,value in plan['code_sha256'].items())):
        raise p.Rejected('frozen fresh non-strict control context differs')
    if pin is not None and (p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan)):
        raise p.Rejected('prospective protocol changed')


def prepare(head):
    shared.clean(head);tools=p.tool_manifest()
    if tools['git_head']!=head:raise p.Rejected('exact clean post-software-checkpoint HEAD required')
    # Existing typed override must already be integrated; no runtime monkeypatch.
    p.engine_profile_settings(angle.PROFILE,120,scoring_variant='via_default',experimental_free_angle=True,fanout_enabled=False,experimental_fanout=True)
    PREP.mkdir();copy_bytes(fixture.files(),PREP/'source');board=PREP/'source'/(fixture.STEM+'.kicad_pcb')
    original=p.preflight(board);protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
    if p.netclass_policy(board) is not None or p.minimum_width_guard(board,'both') is not None or len(protected)!=1 or len(p.routes(original))!=1:
        raise p.Rejected('fresh source must derive strictFalse and exactly one protected KEEP route')
    names=set(tools['implementation_sha256'])|{str(Path(__file__).relative_to(ROOT)),str(Path(fixture.__file__).relative_to(ROOT)),
        str(Path(fixture.base.__file__).relative_to(ROOT)),str(Path(fixture.base.base.__file__).relative_to(ROOT)),
        str(Path(controls.__file__).relative_to(ROOT)),'experiments/hfe_original_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py'}
    plan=dict(schema=1,kind='owned-nonstrict-fanout-false-v1',status='frozen_for_lead_execution',git_head=head,
        source_id=fixture.SOURCE_ID,profile=angle.PROFILE,fanout_enabled=False,source_sha256=p.tree_hash(board.parent),
        tools=tools,protected_ast=protected,code_sha256={n:p.sha(ROOT/n) for n in sorted(names)},limits=LIMITS,scope=SCOPE)
    context(plan);plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
    p.save_json(PROTOCOL,plan);print(f.canonical(dict(prepared=True,protocol=str(PROTOCOL),sha256=p.sha(PROTOCOL),native_executed=False)))


def read_positive(plan,pin):
    context(plan,pin);receipt=CHILD/'route/result.json';receipt_pin=p.sha(receipt);data=f.read_json(receipt);material=shared.material(CHILD/'route')
    source=CHILD/'source'/(fixture.STEM+'.kicad_pcb');candidate=Path(data['candidate']);original=sx.read(source);current=sx.read(candidate)
    if (data.get('source')!=str(source) or data.get('tools')!=plan['tools'] or data.get('source_hashes')!=plan['source_sha256']
            or p.tree_hash(source.parent)!=plan['source_sha256'] or data.get('engine_profile')!=angle.PROFILE or data.get('adapter')!='both'
            or data.get('scope')!='whole_board_unlocked_routing' or data.get('scoring_variant')!='via_default'
            or data.get('engine_fanout_override') is not False or data.get('budget_seconds')!=120 or data.get('cpu_budget_seconds')!=120
            or p.immutable(original)!=p.immutable(current) or any(row not in p.routes(current) for row in plan['protected_ast'])):
        raise p.Rejected('positive source/config/rules/protection scope differs')
    p.check_engine_fanout_override(data,input_policy='native');p.check_engine_profile_record(data,receipt.parent)
    budget=data['engine_budget'];expected=p.engine_profile_settings(angle.PROFILE,budget['remaining_outer_wall_seconds_at_assignment'],scoring_variant='via_default',experimental_free_angle=True)
    actual={k:v for k,v in budget.items() if k not in ('fanout_enabled','outer_task_wall_budget_seconds','outer_task_cpu_budget_seconds')};actual['argv']=list(actual['argv']);actual['argv'].remove('--router.fanout.enabled=false')
    if actual!=expected or budget['strict_class_targets'] is not False or any(x in budget['argv'] for x in ('--router.automatic_neckdown=false','--router.neck_width_um=0')):
        raise p.Rejected('override changed default neckdown/settings beyond one fanout flag')
    # Native export must still carry the authored Default.30 target, in um.
    for name in ('native.dsn','task.dsn'):
        tree=dsn._parse_dsn(io.read_bytes(receipt.parent/name).decode())
        classes=sx.children(sx.one(tree,'network'),'class')
        if sx.one(tree,'unit')!=['unit','um'] or sx.one(sx.one(sx.one(tree,'structure'),'rule'),'width')!=['width','300'] or len(classes)!=1 or sx.one(sx.one(classes[0],'rule'),'width')!=['width','300']:
            raise p.Rejected('Default.30 Native/corrected export target differs')
    _,resolve=g.source_net_identity(current);oblique=[]
    for row in p.routes(current):
        if row[0]!='segment' or row in plan['protected_ast'] or resolve(sx.one(row,'net'))!='ROUTE':continue
        a,b=cp.xy(sx.one(row,'start')),cp.xy(sx.one(row,'end'));dx,dy=abs(b[0]-a[0]),abs(b[1]-a[1])
        if min(dx,dy)>100000 and abs(dx-dy)>100000:oblique.append(row)
    checked=p.check_result(receipt);native=data['native'];fields=native.get('field_parity',{}).get('qualification',{})
    if (checked.get('current') is not True or data.get('accepted') is not True or not oblique
            or data.get('schematic_parity')!='checked by final native DRC' or data['source_drc']['opens']!=1 or data['source_drc']['blocking']
            or not p.native_accepted(native) or native['warnings']!=6 or native['exclusions']!=0
            or fields.get('component_count')!=6 or fields.get('compared_field_count')!=18):raise p.Rejected('fullSCH/non45 positive outcome incomplete')
    if p.sha(candidate)!=data['candidate_sha256'] or p.sha(receipt.parent/'final-drc.json')!=data['native_report_sha256']:raise p.Rejected('final candidate/report pin differs')
    p.check_resource_accounting(data);context(plan,pin)
    if p.sha(receipt)!=receipt_pin or f.canonical(f.read_json(receipt))!=f.canonical(data) or shared.material(receipt.parent)!=material:raise p.Rejected('positive changed during readback')
    ls.check_normal_policy(receipt.parent,data,max_bytes=128*1024**2,max_files=2048)
    return dict(receipt_sha256=receipt_pin,candidate_sha256=data['candidate_sha256'],native_report_sha256=data['native_report_sha256'],native=native,metrics=data['metrics'],non45_route_segments=oblique,shared_readback=checked)


def replay_negative(plan,bad):
    folder=CHILD/'invalid-job';data=dict(steps=bad['steps'],source_hashes=bad['before'],tools=plan['tools'])
    observed=f.check_drc_stage(folder,data,'invalid-final',Path(bad['candidate']),folder/'invalid-final-input'/Path(bad['candidate']).name,False,bad['before'],schematic_parity=True)
    if p.sha(Path(bad['candidate']))!=bad['candidate_sha256'] or p.sha(folder/'invalid-final.json')!=bad['report_sha256'] or f.canonical(observed)!=f.canonical(bad['native']):raise p.Rejected('same-original short proof changed')
    ls.check_normal_policy(folder,data,max_bytes=128*1024**2,max_files=2048)


def check_prl(plan,child):
    """Last metadata-aware prerequisite guard; source/tool authority is caller-pinned."""
    if child.get('positive'):
        ls.check_normal_policy(CHILD/'route',f.read_json(CHILD/'route/result.json'),max_bytes=128*1024**2,max_files=2048)
    if child.get('physical_short'):
        bad=child['physical_short']
        ls.check_normal_policy(CHILD/'invalid-job',dict(steps=bad['steps'],source_hashes=bad['before'],tools=plan['tools']),max_bytes=128*1024**2,max_files=2048)


def worker(plan,pin):
    context(plan,pin);CHILD.mkdir();owner={};h.capture_destination(owner,CHILD);copy_bytes(io.inventory(PREP/'source',contents=True),CHILD/'source')
    record=dict(schema=1,accepted=False,passed=False,status='failed',git_head=plan['git_head'],protocol_sha256=pin,tools=plan['tools'],scope=SCOPE);routed=None;bad=None
    def remaining():return min(174-(time.monotonic()-START),174-(cpu()-CPU0))
    try:
        routed=p.route(CHILD/'source'/(fixture.STEM+'.kicad_pcb'),CHILD/'route',120,False,'both',angle.PROFILE,scoring_variant='via_default',_fanout_enabled=False)
        if routed.get('accepted') is not True:raise p.Rejected('fresh fanoutFalse route refused: '+str(routed.get('reason',routed.get('status'))))
        if f.canonical(f.read_json(CHILD/'route/result.json'))!=f.canonical(routed):raise p.Rejected('returned/stored route differs')
        record['positive']=read_positive(plan,pin);bad=controls.negative(plan,routed,remaining,output=CHILD);record['physical_short']=bad
        record.update(passed=True,status='completed')
    except (Exception,KeyboardInterrupt) as exc:
        record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) or controls.cancelled_execution(routed,CHILD) else 'failed',error=type(exc).__name__+': '+str(exc))
    witness=shared.material(CHILD);record['completed_evidence']=witness
    def stable():
        h.owned_destination(owner);context(plan,pin)
        if shared.material(CHILD)!=witness or p.tree_hash(CHILD/'source')!=plan['source_sha256']:raise p.Rejected('published Native child/source changed')
        if record['passed'] and read_positive(plan,pin)!=record['positive']:raise p.Rejected('late positive proof differs')
        if bad is not None:replay_negative(plan,bad)
        if shared.material(CHILD)!=witness:raise p.Rejected('late child material changed')
        if routed and routed.get('accepted') is True and not record.get('positive'):ls.check_normal_policy(CHILD/'route',f.read_json(CHILD/'route/result.json'),max_bytes=128*1024**2,max_files=2048)
        if bad is not None and not record.get('physical_short'):ls.check_normal_policy(CHILD/'invalid-job',dict(steps=bad['steps'],source_hashes=bad['before'],tools=plan['tools']),max_bytes=128*1024**2,max_files=2048)
        check_prl(plan,record)
    def account():controls.account_delivery(record,time.monotonic()-START,cpu()-CPU0,remaining())
    f.publish(CHILD,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    stored=f.read_json(CHILD/'result.json')
    if f.canonical(stored)!=f.canonical(record):raise p.Rejected('child stored literal differs')
    return 0 if stored.get('passed') and stored.get('status')=='completed' else 130 if stored.get('status')=='cancelled' else 2


def execute(plan,pin):
    context(plan,pin);OUT.mkdir();owner={};h.capture_destination(owner,OUT);prior=plan['preparation_costs'];pw=prior['wall_seconds']+2;pcpu=prior['full_cpu_seconds']+2
    if prior['publication_allowance_seconds']!=2 or any(type(prior[k]) not in (int,float) or not math.isfinite(prior[k]) or prior[k]<0 for k in ('wall_seconds','full_cpu_seconds')):raise p.Rejected('invalid preparation costs')
    def remaining():return min(178-pw-(time.monotonic()-START),178-pcpu-(cpu()-CPU0))
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared lane lock required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--mode','worker','--source-head',plan['git_head'],'--protocol-sha256',pin]
        process=run(argv,cwd=OUT,log=OUT/'command.log',timeout=max(.001,min(176,remaining())),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
        path=CHILD/'result.json';cpin=p.sha(path) if path.is_file() else None;child=f.read_json(path) if cpin else None;literal=f.canonical(child)
        bound=bool(child and child.get('completed_evidence')==shared.material(CHILD) and p.sha(path)==cpin and f.canonical(f.read_json(path))==literal)
        material=shared.material(OUT);logpin=p.sha(OUT/'command.log')
        passed=bool(bound and child.get('passed') is True and child.get('status')=='completed' and child.get('accepted') is False and child.get('tools')==plan['tools'] and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
        record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'cancelled' if process['status']=='cancelled' or child and child.get('status')=='cancelled' else 'failed',git_head=plan['git_head'],tools=plan['tools'],protocol_sha256=pin,
            process=process,child_receipt_sha256=cpin,child_literal=literal,child_completed_evidence_bound=bound,completed_evidence=material,log_sha256=logpin,preparation_costs=prior,limits=LIMITS,scope=SCOPE,
            cost_scope='Whole outer self+reaped child includes preparation and every child routing/readback/publication tail; enclosing stored sample+2allowance and actual late wall/fullCPU guard.')
        def stable():
            h.owned_destination(owner);context(plan,pin)
            if shared.material(OUT)!=material or p.sha(OUT/'command.log')!=logpin:raise p.Rejected('outer material changed')
            if child is not None and (not bound or p.sha(path)!=cpin or f.canonical(f.read_json(path))!=literal or shared.material(CHILD)!=child['completed_evidence']):raise p.Rejected('published child changed after exit')
            if record['passed'] and read_positive(plan,pin)!=child['positive']:raise p.Rejected('outer positive shared proof differs')
            if child and child.get('physical_short'):replay_negative(plan,child['physical_short'])
            if shared.material(OUT)!=material:raise p.Rejected('outer material changed late')
            if child is not None:check_prl(plan,child)
        def account():controls.account_delivery(record,pw+time.monotonic()-START,pcpu+cpu()-CPU0,remaining())
        f.publish(OUT,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
        result=f.read_json(OUT/'result.json')
        if f.canonical(result)!=f.canonical(record):raise p.Rejected('outer canonical snapshot differs')
        print(f.canonical({k:result.get(k) for k in ('passed','status','wall_seconds','full_cpu_seconds','child_completed_evidence_bound')}))
        return 0 if result.get('passed') and result.get('status')=='completed' else 130 if result.get('status')=='cancelled' else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=('prepare','worker','run'),required=True);parser.add_argument('--source-head',required=True);parser.add_argument('--protocol-sha256');args=parser.parse_args()
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def cancel(*_):raise KeyboardInterrupt
    try:
        for sig in previous:signal.signal(sig,cancel)
        if args.mode=='prepare':prepare(args.source_head)
        else:
            plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
            if args.protocol_sha256!=pin or plan.get('git_head')!=args.source_head:raise p.Rejected('exact future checkpoint/protocol required')
            raise SystemExit(worker(plan,pin) if args.mode=='worker' else execute(plan,pin))
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
