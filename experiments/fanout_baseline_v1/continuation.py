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
PREP=ROOT/'.runs/fanout-native-control-preparation-002';PROTOCOL=PREP/'protocol.json'
OUT=ROOT/'.runs/fanout-native-control-002';CHILD=OUT/'native'
POSITIVE=ROOT/'.runs/fanout-native-control-001/native'
OLD_PROTOCOL=ROOT/'.runs/fanout-native-control-preparation-001/protocol.json'
OLD_OUTER=ROOT/'.runs/fanout-native-control-001/result.json'
OLD_HEAD='da255bfb15cc5881af7d591dc59c4fd5f6b27afe'
OLD_PROTOCOL_SHA='d5e21e92e3d82af8dc7f94a12395e7a52ac727a0cf869c059bbbdc19a1e26f98'
OLD_OUTER_SHA='0143f7a6e24639451e469358c834ef8560e839c77c8fbcfc92470ca568a2e066'
OLD_POSITIVE_SHA='5d1f610da8220d2e8658cd385cde7fbae1afac7f0e6c141409886e5871c84c55'
LIMITS=dict(route_wall_full_cpu_seconds=120,whole_wall_full_cpu_seconds=180,publication_allowance_seconds=2,scratch_bytes=128*1024**2,group_rss_bytes=4*1024**3,log_bytes=256*1024)
SCOPE='Missing-only continuation from exact historical001 positive: no route/source/refill/final-positive Native repeat; old failed attempt costs retained; current original-rule short only. Fresh owned exposed NONSTRICT synthetic branch control: free-angle fanoutFalse positive plus same-original physical-short negative. Only source creation minimum.25→0 differs; Default.30 targets/priority/fullSCH/KEEP unchanged. No source repair, quality/comparative/family/default/GUI/installed/physical approval claim.'


def hashes(files):return {n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}


def check_prior_witness():
    """Check the original published witnesses before adopting retained bytes."""
    if (p.sha(OLD_OUTER)!=OLD_OUTER_SHA or p.sha(OLD_PROTOCOL)!=OLD_PROTOCOL_SHA
            or p.sha(POSITIVE/'route/result.json')!=OLD_POSITIVE_SHA):
        raise p.Rejected('fixed historical receipts changed')
    failed=f.read_json(OLD_OUTER);path=POSITIVE/'result.json';child=f.read_json(path)
    if (failed.get('child_completed_evidence_bound') is not True
            or p.sha(path)!=failed.get('child_receipt_sha256') or f.canonical(child)!=failed.get('child_literal')
            or shared.material(POSITIVE)!=child.get('completed_evidence')
            or shared.material(OLD_OUTER.parent)!=failed.get('completed_evidence')):
        raise p.Rejected('historical published child/outer witness or literal differs')
    return failed,child


def context(plan,pin=None):
    shared.clean(plan['git_head'])
    if (plan.get('kind')!='owned-nonstrict-fanout-false-missing-only-v1' or plan.get('limits')!=LIMITS
            or plan.get('status')!='frozen_for_lead_execution' or plan.get('source_id')!=fixture.SOURCE_ID
            or plan.get('profile')!=angle.PROFILE or plan.get('fanout_enabled') is not False or plan['tools'].get('kicad')!='10.0.0'
            or p.tool_manifest()!=plan['tools'] or hashes(fixture.files())!=plan['source_sha256']
            or p.tree_hash(PREP/'source')!=plan['source_sha256']
            or any(p.sha(ROOT/n)!=value for n,value in plan['code_sha256'].items())):
        raise p.Rejected('frozen fresh non-strict control context differs')
    if (plan.get('historical_head')!=OLD_HEAD or plan['historical_tools'].get('git_head')!=OLD_HEAD
            or {k:v for k,v in plan['tools'].items() if k!='git_head'}!={k:v for k,v in plan['historical_tools'].items() if k!='git_head'}
            or p.sha(OLD_PROTOCOL)!=OLD_PROTOCOL_SHA or p.sha(OLD_OUTER)!=OLD_OUTER_SHA
            or p.sha(POSITIVE/'route/result.json')!=OLD_POSITIVE_SHA
            or f.canonical(f.read_json(POSITIVE/'route/result.json'))!=plan['retained_positive']['literal']
            or any(p.sha(ROOT/n)!=value for n,value in plan['prior_attempts']['files_sha256'].items())):
        raise p.Rejected('specifically retained historical positive/failed attempts changed')
    check_prior_witness()
    old=f.read_json(OLD_PROTOCOL)
    if any(p.sha(ROOT/n)!=value for n,value in old['code_sha256'].items()):raise p.Rejected('original001 producer/helper source bytes changed')
    if pin is not None and (p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan)):
        raise p.Rejected('prospective protocol changed')


def prepare(head):
    shared.clean(head);tools=p.tool_manifest()
    if tools['git_head']!=head or head==OLD_HEAD:raise p.Rejected('exact NEW clean checkpoint required')
    if p.sha(OLD_PROTOCOL)!=OLD_PROTOCOL_SHA or p.sha(OLD_OUTER)!=OLD_OUTER_SHA or p.sha(POSITIVE/'route/result.json')!=OLD_POSITIVE_SHA:raise p.Rejected('fixed immutable001 evidence differs')
    failed,child=check_prior_witness()
    old=f.read_json(OLD_PROTOCOL);routed=f.read_json(POSITIVE/'route/result.json')
    if (old['git_head']!=OLD_HEAD or failed.get('passed') is not False or failed.get('status')!='failed'
            or child.get('error')!='ValueError: duplicate singleton rule' or child.get('physical_short') is not None
            or (POSITIVE/'invalid').exists() or (POSITIVE/'invalid-job').exists() or routed.get('accepted') is not True or routed['tools']!=old['tools']):
        raise p.Rejected('exact failed001 reader-only failure/accepted positive/no-short boundary differs')
    if {k:v for k,v in tools.items() if k!='git_head'}!={k:v for k,v in old['tools'].items() if k!='git_head'}:
        raise p.Rejected('historical positive allows ONLY this named HEAD difference; core/tools must be byte exact')
    PREP.mkdir();copy_bytes(fixture.files(),PREP/'source')
    if p.tree_hash(PREP/'source')!=old['source_sha256'] or p.tree_hash(POSITIVE/'source')!=old['source_sha256']:raise p.Rejected('identical full authored original source required')
    names=set(tools['implementation_sha256'])|set(old['code_sha256'])|{str(Path(__file__).relative_to(ROOT))}
    priorfiles={str((OLD_OUTER.parent/n).relative_to(ROOT)):v for n,v in p.tree_hash(OLD_OUTER.parent).items()}
    priorfiles.update({str((OLD_PROTOCOL.parent/n).relative_to(ROOT)):v for n,v in p.tree_hash(OLD_PROTOCOL.parent).items()})
    timing={};wall=full=0.
    for stage,expected in (('native-prepare',(1.19,.87)),('native-prepare002',(.86,.92)),('native-run',(26.85,17.18))):
        path=ROOT/('.runs/fanout-command-timing-001/'+stage+'-time.log');text=io.read_bytes(path,64*1024).decode()
        import re
        values={key:float(value) for key,value in re.findall(r'(?m)^(real|user|sys) ([0-9.]+)$',text)}
        if set(values)!={'real','user','sys'} or abs(values['real']-expected[0])>1e-8 or abs(values['user']+values['sys']-expected[1])>1e-8:raise p.Rejected('fixed externally observed prior costs differ')
        w,fcpu=values['real'],values['user']+values['sys'];wall+=w+2;full+=fcpu+2+.02
        timing[stage]=dict(whole_command_wall_seconds=w,whole_command_full_cpu_seconds=fcpu,publication_allowance_seconds=2,rounding_cpu_allowance_seconds=.02)
        for suffix in ('time.log','command.log'):
            artifact=path.with_name(stage+'-'+suffix);priorfiles[str(artifact.relative_to(ROOT))]=p.sha(artifact)
    plan=dict(schema=1,kind='owned-nonstrict-fanout-false-missing-only-v1',status='frozen_for_lead_execution',git_head=head,
        source_id=fixture.SOURCE_ID,profile=angle.PROFILE,fanout_enabled=False,source_sha256=old['source_sha256'],protected_ast=old['protected_ast'],
        historical_tools=old['tools'],historical_head=OLD_HEAD,tools=tools,code_sha256={n:p.sha(ROOT/n) for n in sorted(names)},
        retained_positive=dict(receipt=str(POSITIVE/'route/result.json'),receipt_sha256=OLD_POSITIVE_SHA,literal=f.canonical(routed)),
        prior_attempts=dict(files_sha256=priorfiles,wall_seconds=wall,full_cpu_seconds=full,operations=timing,scope='Three actual external command-exit costs once, explicit2s allowance each and.02CPU rounding per two-decimal user+sys. Old stored outer samples NOT added again.'),limits=LIMITS,scope=SCOPE)
    read_positive(plan,None);context(plan)
    plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
    p.save_json(PROTOCOL,plan);print(f.canonical(dict(prepared=True,protocol=str(PROTOCOL),sha256=p.sha(PROTOCOL),native_executed=False)))


def require_width300(tree):
    """One literal width300 across rule groups; clearance-only groups stay intact."""
    classes=sx.children(sx.one(tree,'network'),'class')
    def widths(parent):
        return [value for rule in sx.children(parent,'rule') for value in rule[1:]
            if isinstance(value,list) and value and value[0]=='width']
    if (sx.one(tree,'unit')!=['unit','um'] or widths(sx.one(tree,'structure'))!=[['width','300']]
            or len(classes)!=1 or widths(classes[0])!=[['width','300']]):
        raise p.Rejected('exact single structure/class width300 required')


def read_positive(plan,pin):
    context(plan,pin);receipt=POSITIVE/'route/result.json';receipt_pin=p.sha(receipt);data=f.read_json(receipt);material=shared.material(POSITIVE/'route')
    source=POSITIVE/'source'/(fixture.STEM+'.kicad_pcb');candidate=Path(data['candidate']);original=sx.read(source);current=sx.read(candidate)
    if (data.get('source')!=str(source) or data.get('tools')!=plan['historical_tools'] or data.get('source_hashes')!=plan['source_sha256']
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
    for name in ('native.dsn','task.dsn'):
        require_width300(dsn._parse_dsn(io.read_bytes(receipt.parent/name).decode()))
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
        ls.check_normal_policy(POSITIVE/'route',f.read_json(POSITIVE/'route/result.json'),max_bytes=128*1024**2,max_files=2048)
    if child.get('physical_short'):
        bad=child['physical_short']
        ls.check_normal_policy(CHILD/'invalid-job',dict(steps=bad['steps'],source_hashes=bad['before'],tools=plan['tools']),max_bytes=128*1024**2,max_files=2048)


def worker(plan,pin):
    context(plan,pin);CHILD.mkdir();owner={};h.capture_destination(owner,CHILD);copy_bytes(io.inventory(PREP/'source',contents=True),CHILD/'source')
    record=dict(schema=1,accepted=False,passed=False,status='failed',git_head=plan['git_head'],protocol_sha256=pin,tools=plan['tools'],scope=SCOPE);routed=None;bad=None
    def remaining():return min(174-(time.monotonic()-START),174-(cpu()-CPU0))
    try:
        routed=f.read_json(POSITIVE/'route/result.json')
        if routed.get('accepted') is not True:raise p.Rejected('fresh fanoutFalse route refused: '+str(routed.get('reason',routed.get('status'))))
        if p.sha(POSITIVE/'route/result.json')!=OLD_POSITIVE_SHA:raise p.Rejected('retained positive receipt differs')
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
        if routed and routed.get('accepted') is True and not record.get('positive'):ls.check_normal_policy(POSITIVE/'route',f.read_json(POSITIVE/'route/result.json'),max_bytes=128*1024**2,max_files=2048)
        if bad is not None and not record.get('physical_short'):ls.check_normal_policy(CHILD/'invalid-job',dict(steps=bad['steps'],source_hashes=bad['before'],tools=plan['tools']),max_bytes=128*1024**2,max_files=2048)
        check_prl(plan,record)
    def account():controls.account_delivery(record,time.monotonic()-START,cpu()-CPU0,remaining())
    f.publish(CHILD,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    stored=f.read_json(CHILD/'result.json')
    if f.canonical(stored)!=f.canonical(record):raise p.Rejected('child stored literal differs')
    return 0 if stored.get('passed') and stored.get('status')=='completed' else 130 if stored.get('status')=='cancelled' else 2


def execute(plan,pin):
    context(plan,pin);OUT.mkdir();owner={};h.capture_destination(owner,OUT);prior=plan['preparation_costs'];pw=prior['wall_seconds']+2+plan['prior_attempts']['wall_seconds'];pcpu=prior['full_cpu_seconds']+2+plan['prior_attempts']['full_cpu_seconds']
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
            process=process,child_receipt_sha256=cpin,child_literal=literal,child_completed_evidence_bound=bound,completed_evidence=material,log_sha256=logpin,preparation_costs=prior,prior_attempts=plan['prior_attempts'],limits=LIMITS,scope=SCOPE,
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
