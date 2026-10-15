"""One fresh non-strict owned fanout-False Native branch control, not quality.
Reuse existing route/shared Native readers, BoundJob negative and publisher.
Root must first integrate/checkpoint passing fanout software/source changes.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,hashlib,json,math,os,re,signal,stat,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as io,sexpr as sx,board_floor as g,chain_proposals as cp,local_settings as ls,engine_angle as angle,adapter as dsn
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as shared
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.free_angle_baseline_v1 import controls
from experiments.fanout_baseline_v1 import fixture
from experiments.fanout_baseline_v1.continuation import require_width300
PREP=ROOT/'.runs/no-optimizer-native-control-preparation-001';PROTOCOL=PREP/'protocol.json'
OUT=ROOT/'.runs/no-optimizer-native-control-001';CHILD=OUT/'native'
TIMING=ROOT/'.runs/no-optimizer-native-control-timing-001';QUAL=ROOT/'.runs/no-optimizer-native-control-qualification-001'
LIMITS=dict(route_wall_full_cpu_seconds=120,whole_wall_full_cpu_seconds=180,publication_allowance_seconds=2,scratch_bytes=128*1024**2,group_rss_bytes=4*1024**3,log_bytes=256*1024)
SCOPE='Fresh owned existing four-file non-strict fixture; Native fullSCH free-angle fanoutFalse optimizerFalse positive, one effective pinned JAR DSN/settings getter and same-original physical-short negative. Stock B2 qualification only; no non45 geometry requirement, gain/C novelty/default/GUI/installed/family/physical approval claim.'


def hashes(files):return {n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}


def context(plan,pin=None):
    shared.clean(plan['git_head'])
    if (plan.get('kind')!='owned-free-angle-fanout-false-no-optimizer-v1' or plan.get('limits')!=LIMITS
            or plan.get('status')!='frozen_for_lead_execution' or plan.get('source_id')!=fixture.SOURCE_ID
            or plan.get('profile')!=angle.PROFILE or plan.get('fanout_enabled') is not False or plan.get('optimizer_enabled') is not False or plan['tools'].get('kicad')!='10.0.0'
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
    p.engine_profile_settings(angle.PROFILE,120,scoring_variant='via_default',experimental_free_angle=True,fanout_enabled=False,experimental_fanout=True,optimizer_enabled=False,experimental_optimizer=True)
    PREP.mkdir();owned=fixture.files()
    if len(owned)!=4:raise p.Rejected('exact existing four-file source required')
    copy_bytes(owned,PREP/'source');board=PREP/'source'/(fixture.STEM+'.kicad_pcb')
    original=p.preflight(board);protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
    if p.netclass_policy(board) is not None or p.minimum_width_guard(board,'both') is not None or len(protected)!=1 or len(p.routes(original))!=1:
        raise p.Rejected('fresh source must derive strictFalse and exactly one protected KEEP route')
    names=set(tools['implementation_sha256'])|{str(Path(__file__).relative_to(ROOT)),str(Path(fixture.__file__).relative_to(ROOT)),
        str(Path(fixture.base.__file__).relative_to(ROOT)),str(Path(fixture.base.base.__file__).relative_to(ROOT)),
        str(Path(controls.__file__).relative_to(ROOT)),'experiments/fanout_baseline_v1/continuation.py','experiments/fanout_baseline_v1/OptimizerObservation.java','experiments/hfe_original_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py'}
    plan=dict(schema=1,kind='owned-free-angle-fanout-false-no-optimizer-v1',status='frozen_for_lead_execution',git_head=head,
        source_id=fixture.SOURCE_ID,profile=angle.PROFILE,fanout_enabled=False,optimizer_enabled=False,source_sha256=p.tree_hash(board.parent),
        tools=tools,protected_ast=protected,code_sha256={n:p.sha(ROOT/n) for n in sorted(names)},limits=LIMITS,scope=SCOPE)
    context(plan);plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
    p.save_json(PROTOCOL,plan);print(f.canonical(dict(prepared=True,protocol=str(PROTOCOL),sha256=p.sha(PROTOCOL),native_executed=False)))


def read_positive(plan,pin):
    context(plan,pin);receipt=CHILD/'route/result.json';receipt_pin=p.sha(receipt);data=f.read_json(receipt);material=shared.material(CHILD/'route')
    source=CHILD/'source'/(fixture.STEM+'.kicad_pcb');candidate=Path(data['candidate']);original=sx.read(source);current=sx.read(candidate)
    if (data.get('source')!=str(source) or data.get('tools')!=plan['tools'] or data.get('source_hashes')!=plan['source_sha256']
            or p.tree_hash(source.parent)!=plan['source_sha256'] or data.get('engine_profile')!=angle.PROFILE or data.get('adapter')!='both'
            or data.get('scope')!='whole_board_unlocked_routing' or data.get('scoring_variant')!='via_default'
            or data.get('engine_fanout_override') is not False or data.get('engine_optimizer_override') is not False or data.get('budget_seconds')!=120 or data.get('cpu_budget_seconds')!=120
            or p.immutable(original)!=p.immutable(current) or any(row not in p.routes(current) for row in plan['protected_ast'])):
        raise p.Rejected('positive source/config/rules/protection scope differs')
    p.check_engine_fanout_override(data,input_policy='native');p.check_engine_optimizer_override(data,input_policy='native');p.check_engine_profile_record(data,receipt.parent)
    budget=data['engine_budget'];expected=p.engine_profile_settings(angle.PROFILE,budget['remaining_outer_wall_seconds_at_assignment'],scoring_variant='via_default',experimental_free_angle=True,fanout_enabled=False,experimental_fanout=True)
    actual={k:v for k,v in budget.items() if k not in ('optimizer_enabled','outer_task_wall_budget_seconds','outer_task_cpu_budget_seconds')};actual['argv']=list(actual['argv']);actual['argv'].remove('--router.optimizer.enabled=false')
    if actual!=expected or budget['strict_class_targets'] is not False or any(x in budget['argv'] for x in ('--router.automatic_neckdown=false','--router.neck_width_um=0')):
        raise p.Rejected('optimizer override changed settings beyond exactly one optimizer-disable flag')
    # Native export must still carry the authored Default.30 target, in um.
    for name in ('native.dsn','task.dsn'):
        require_width300(dsn._parse_dsn(io.read_bytes(receipt.parent/name).decode()))
    _,resolve=g.source_net_identity(current);oblique=[]
    for row in p.routes(current):
        if row[0]!='segment' or row in plan['protected_ast'] or resolve(sx.one(row,'net'))!='ROUTE':continue
        a,b=cp.xy(sx.one(row,'start')),cp.xy(sx.one(row,'end'));dx,dy=abs(b[0]-a[0]),abs(b[1]-a[1])
        if min(dx,dy)>100000 and abs(dx-dy)>100000:oblique.append(row)
    checked=p.check_result(receipt);native=data['native'];fields=native.get('field_parity',{}).get('qualification',{})
    if (checked.get('current') is not True or data.get('accepted') is not True
            or data.get('schematic_parity')!='checked by final native DRC' or data['source_drc']['opens']!=1 or data['source_drc']['blocking']
            or not p.native_accepted(native) or native['warnings']!=6 or native['exclusions']!=0
            or fields.get('component_count')!=6 or fields.get('compared_field_count')!=18):raise p.Rejected('fullSCH optimizer-disabled positive outcome incomplete')
    if p.sha(candidate)!=data['candidate_sha256'] or p.sha(receipt.parent/'final-drc.json')!=data['native_report_sha256']:raise p.Rejected('final candidate/report pin differs')
    p.check_resource_accounting(data);context(plan,pin)
    if p.sha(receipt)!=receipt_pin or f.canonical(f.read_json(receipt))!=f.canonical(data) or shared.material(receipt.parent)!=material:raise p.Rejected('positive changed during readback')
    ls.check_normal_policy(receipt.parent,data,max_bytes=128*1024**2,max_files=2048)
    return dict(receipt=str(receipt),receipt_sha256=receipt_pin,candidate_sha256=data['candidate_sha256'],native_report_sha256=data['native_report_sha256'],native=native,metrics=data['metrics'],non45_route_segments=oblique,shared_readback=checked)


def getter_argv(route):
    data=f.read_json(route/'result.json');p.check_engine_profile_record(data,route)
    flags=data['engine_budget']['argv']
    if any(type(value)is not str or not value.startswith('--router.') for value in flags):raise p.Rejected('exact relevant router argv required')
    return [str(p.c.JAVA),'-Xms64m','-Xmx512m','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','--class-path',str(p.c.JAR),
        str(ROOT/'experiments/fanout_baseline_v1/OptimizerObservation.java'),str(route/angle.INPUT),*flags]


def observe_optimizer(plan,routed,remaining):
    route=Path(routed['candidate']).parent.parent;folder=CHILD/'optimizer-getter'
    job=shared.BoundJob(folder,180,remaining,protect_local_settings=True)
    argv=getter_argv(route);step=job.step('effective-settings',argv)
    row=dict(step=step,input_sha256=p.sha(route/angle.INPUT),jar_sha256=p.sha(p.c.JAR),java_sha256=p.sha(p.c.JAVA),
        source_sha256=p.sha(ROOT/'experiments/fanout_baseline_v1/OptimizerObservation.java'),stdout_sha256=p.sha(folder/'effective-settings.log'),
        actual_engine_argv=f.read_json(route/'engine-process.json')['argv'],query_argv=argv)
    check_optimizer_observation(plan,row)
    return row


def check_optimizer_observation(plan,row):
    route=CHILD/'route';folder=CHILD/'optimizer-getter';argv=getter_argv(route)
    process=f.process_check(folder,dict(steps=[row['step']]),'effective-settings',[*f.SANDBOX,*argv])
    raw=io.read_bytes(folder/'effective-settings.log',256*1024);observed=json.loads(raw.decode().splitlines()[-1])
    if (process.get('log_truncated') is not False or row.get('query_argv')!=argv or row.get('stdout_sha256')!=hashlib.sha256(raw).hexdigest()
            or row.get('input_sha256')!=p.sha(route/angle.INPUT) or row.get('jar_sha256')!=p.sha(p.c.JAR)
            or row.get('java_sha256')!=p.sha(p.c.JAVA) or row.get('source_sha256')!=p.sha(ROOT/'experiments/fanout_baseline_v1/OptimizerObservation.java')
            or row.get('actual_engine_argv')!=f.read_json(route/'engine-process.json')['argv']
            or observed.get('input_sha256')!=row['input_sha256'] or observed.get('jar_sha256')!=row['jar_sha256']
            or observed.get('optimizer_enabled') is not False or observed.get('fanout_enabled') is not False or observed.get('loaded_angle')!='NONE'
            or observed.get('parse_warnings')!=[] or observed.get('diagnostic_only') is not True
            or observed.get('actual_settings_argv')!=f.read_json(route/'result.json')['engine_budget']['argv']
            or observed.get('settings_sources')!=['pinned defaults','actual DSN','actual CLI']
            or observed.get('parsed_cli_arguments',{}).get('router.optimizer.enabled')!='false'
            or observed.get('parsed_cli_arguments',{}).get('router.fanout.enabled')!='false'):
        raise p.Rejected('one actual pinned-JAR optimizer/fanout/angle observation differs')


def replay_negative(plan,bad):
    folder=CHILD/'invalid-job';data=dict(steps=bad['steps'],source_hashes=bad['before'],tools=plan['tools'])
    observed=f.check_drc_stage(folder,data,'invalid-final',Path(bad['candidate']),folder/'invalid-final-input'/Path(bad['candidate']).name,False,bad['before'],schematic_parity=True)
    if p.sha(Path(bad['candidate']))!=bad['candidate_sha256'] or p.sha(folder/'invalid-final.json')!=bad['report_sha256'] or f.canonical(observed)!=f.canonical(bad['native']):raise p.Rejected('same-original short proof changed')
    if p.native_accepted(observed) or observed['blocking']<1 or not any(row['severity']=='error' and row['type']=='shorting_items' for row in observed['findings']):raise p.Rejected('same-original short negative is no longer a Native rejection')
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
        routed=p.route(CHILD/'source'/(fixture.STEM+'.kicad_pcb'),CHILD/'route',120,False,'both',angle.PROFILE,scoring_variant='via_default',_fanout_enabled=False,_optimizer_enabled=False)
        if routed.get('accepted') is not True:raise p.Rejected('fresh fanoutFalse route refused: '+str(routed.get('reason',routed.get('status'))))
        if f.canonical(f.read_json(CHILD/'route/result.json'))!=f.canonical(routed):raise p.Rejected('returned/stored route differs')
        record['positive']=read_positive(plan,pin);record['optimizer_observation']=observe_optimizer(plan,routed,remaining);bad=controls.negative(plan,routed,remaining,output=CHILD);record['physical_short']=bad
        record.update(passed=True,status='completed')
    except (Exception,KeyboardInterrupt) as exc:
        record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) or controls.cancelled_execution(routed,CHILD) else 'failed',error=type(exc).__name__+': '+str(exc))
    witness=shared.material(CHILD);record['completed_evidence']=witness
    def stable():
        h.owned_destination(owner);context(plan,pin)
        if shared.material(CHILD)!=witness or p.tree_hash(CHILD/'source')!=plan['source_sha256']:raise p.Rejected('published Native child/source changed')
        if record['passed'] and read_positive(plan,pin)!=record['positive']:raise p.Rejected('late positive proof differs')
        if record.get('optimizer_observation'):check_optimizer_observation(plan,record['optimizer_observation'])
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
        passed=bool(bound and child.get('passed') is True and child.get('status')=='completed' and child.get('accepted') is False and child.get('tools')==plan['tools'] and child.get('git_head')==plan['git_head'] and child.get('protocol_sha256')==pin and child.get('optimizer_observation') is not None and child.get('physical_short') is not None and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
        record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'cancelled' if process['status']=='cancelled' or child and child.get('status')=='cancelled' else 'failed',git_head=plan['git_head'],tools=plan['tools'],protocol_sha256=pin,
            process=process,child_receipt_sha256=cpin,child_literal=literal,child_completed_evidence_bound=bound,completed_evidence=material,log_sha256=logpin,preparation_costs=prior,limits=LIMITS,scope=SCOPE,
            external_cost_qualification_required=True,cost_scope='Sampled outer self+reaped child plus declared preparation/publication allowances; NOT complete external process-exit totals. Final qualify mode requires actual prepare/run external time logs and all current proofs within180s.')
        def stable():
            h.owned_destination(owner);context(plan,pin)
            if shared.material(OUT)!=material or p.sha(OUT/'command.log')!=logpin:raise p.Rejected('outer material changed')
            if child is not None and (not bound or p.sha(path)!=cpin or f.canonical(f.read_json(path))!=literal or shared.material(CHILD)!=child['completed_evidence']):raise p.Rejected('published child changed after exit')
            if record['passed'] and read_positive(plan,pin)!=child['positive']:raise p.Rejected('outer positive shared proof differs')
            if child and child.get('optimizer_observation'):check_optimizer_observation(plan,child['optimizer_observation'])
            if child and child.get('physical_short'):replay_negative(plan,child['physical_short'])
            if shared.material(OUT)!=material:raise p.Rejected('outer material changed late')
            if child is not None:check_prl(plan,child)
        def account():controls.account_delivery(record,pw+time.monotonic()-START,pcpu+cpu()-CPU0,remaining())
        f.publish(OUT,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
        result=f.read_json(OUT/'result.json')
        if f.canonical(result)!=f.canonical(record):raise p.Rejected('outer canonical snapshot differs')
        print(f.canonical({k:result.get(k) for k in ('passed','status','wall_seconds','full_cpu_seconds','child_completed_evidence_bound')}))
        return 0 if result.get('passed') and result.get('status')=='completed' else 130 if result.get('status')=='cancelled' else 2


def qualify(plan,pin):
    """Missing-only pure readback; actual exited prepare/run costs are mandatory."""
    context(plan,pin);QUAL.mkdir();owner={};h.capture_destination(owner,QUAL)
    outer=f.read_json(OUT/'result.json');outerpin=p.sha(OUT/'result.json');child=f.read_json(CHILD/'result.json');childpin=p.sha(CHILD/'result.json')
    literal=f.canonical(outer);cliteral=f.canonical(child);material=shared.material(OUT)
    expected_worker=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--mode','worker','--source-head',plan['git_head'],'--protocol-sha256',pin]
    process=outer.get('process',{})
    if (outer.get('passed') is not True or outer.get('status')!='completed' or outer.get('accepted') is not False or outer.get('limits')!=LIMITS or outer.get('child_completed_evidence_bound') is not True or outer.get('external_cost_qualification_required') is not True
            or outer.get('child_literal')!=cliteral or outer.get('child_receipt_sha256')!=childpin
            or child.get('status')!='completed' or child.get('passed') is not True or child.get('accepted') is not False or child.get('protocol_sha256')!=pin
            or outer.get('protocol_sha256')!=pin or outer.get('git_head')!=plan['git_head'] or child.get('git_head')!=plan['git_head']
            or outer.get('tools')!=plan['tools'] or child.get('tools')!=plan['tools'] or child.get('completed_evidence')!=shared.material(CHILD)
            or outer.get('completed_evidence')!=material or outer.get('process',{}).get('cleanup_complete') is not True
            or process.get('argv')!=expected_worker or process.get('cwd')!=str(OUT) or process.get('log')!=str(OUT/'command.log')
            or process.get('status')!='success' or type(process.get('exit_code'))is not int or process['exit_code']!=0 or process.get('log_truncated') is not False
            or p.sha(OUT/'command.log')!=outer.get('log_sha256')):
        raise p.Rejected('exact completed fresh child/outer proof required')
    timing={};costs=[];pins={}
    for stage in ('prepare','run'):
        path=TIMING/(stage+'-time.log');raw=io.read_bytes(path,64*1024);text=raw.decode()
        matches=re.findall(r'(?m)^(real|user|sys) ([0-9]+(?:\.[0-9]+)?)$',text)
        values={key:float(value) for key,value in matches}
        if len(matches)!=3 or set(values)!={'real','user','sys'} or any(not math.isfinite(v) or v<0 for v in values.values()):raise p.Rejected('complete actual external timing required')
        command=io.read_bytes(TIMING/(stage+'-command.log'),256*1024).decode()
        lines=command.splitlines()
        invocation=json.loads(lines[0]);result=json.loads(lines[-1])
        expected_args=[str(Path(__file__).resolve()),'--mode',stage,'--source-head',plan['git_head']]+(['--protocol-sha256',pin] if stage=='run' else [])
        if invocation!=dict(invocation=dict(argv=expected_args,python=str(ROOT/'.venv/bin/python'),cwd=str(ROOT),controller_sha256=p.sha(Path(__file__)))):raise p.Rejected('external timing command attribution differs')
        if stage=='prepare':
            expected_result=dict(prepared=True,protocol=str(PROTOCOL),sha256=pin,native_executed=False)
            minimum_wall=plan['preparation_costs']['wall_seconds'];minimum_cpu=plan['preparation_costs']['full_cpu_seconds']
        else:
            expected_result={k:outer.get(k) for k in ('passed','status','wall_seconds','full_cpu_seconds','child_completed_evidence_bound')}
            minimum_wall=outer['wall_seconds']-plan['preparation_costs']['wall_seconds']-2
            minimum_cpu=outer['full_cpu_seconds']-plan['preparation_costs']['full_cpu_seconds']-2
        if result!=expected_result or values['real']+.02<minimum_wall or values['user']+values['sys']+.02<minimum_cpu:raise p.Rejected('external timing/result attribution or sampled lower bound differs')
        timing[stage]=dict(whole_command_wall_seconds=values['real'],whole_command_full_cpu_seconds=values['user']+values['sys'],publication_allowance_seconds=2,rounding_cpu_allowance_seconds=.02)
        costs.append((values['real']+2,values['user']+values['sys']+2+.02))
        for suffix in ('time.log','command.log'):
            file=TIMING/(stage+'-'+suffix);pins[str(file.relative_to(ROOT))]=p.sha(file)
    priorwall=sum(x[0] for x in costs);priorcpu=sum(x[1] for x in costs)
    def remaining():return min(178-priorwall-(time.monotonic()-START),178-priorcpu-(cpu()-CPU0))
    record=dict(schema=1,accepted=False,passed=True,status='completed',git_head=plan['git_head'],protocol_sha256=pin,tools=plan['tools'],
        outer_receipt_sha256=outerpin,child_receipt_sha256=childpin,completed_evidence=material,external_operations=timing,external_files_sha256=pins,
        cost_scope='REPLACES sampled preparation/run charges with both actual whole external exited commands once plus2s each/.02CPU rounding each; current pure qualification sampled live+2 and late180s guard. Current reader process-exit CPU is not claimed measured.',scope=SCOPE)
    def stable():
        h.owned_destination(owner);context(plan,pin)
        if p.sha(OUT/'result.json')!=outerpin or f.canonical(f.read_json(OUT/'result.json'))!=literal or p.sha(CHILD/'result.json')!=childpin or f.canonical(f.read_json(CHILD/'result.json'))!=cliteral or shared.material(OUT)!=material:raise p.Rejected('final exited output changed')
        if read_positive(plan,pin)!=child['positive']:raise p.Rejected('final positive proof changed')
        check_optimizer_observation(plan,child['optimizer_observation']);replay_negative(plan,child['physical_short'])
        if any(p.sha(ROOT/n)!=value for n,value in pins.items()) or shared.material(OUT)!=material:raise p.Rejected('final timing/material changed late')
        check_prl(plan,child)
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared lane lock required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        def account():controls.account_delivery(record,priorwall+time.monotonic()-START,priorcpu+cpu()-CPU0,remaining())
        f.publish(QUAL,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
        stored=f.read_json(QUAL/'result.json')
        if f.canonical(stored)!=f.canonical(record):raise p.Rejected('qualification literal differs')
        return 0 if stored.get('passed') and stored.get('status')=='completed' else 130 if stored.get('status')=='cancelled' else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=('prepare','worker','run','qualify'),required=True);parser.add_argument('--source-head',required=True);parser.add_argument('--protocol-sha256');args=parser.parse_args()
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def cancel(*_):raise KeyboardInterrupt
    try:
        for sig in previous:signal.signal(sig,cancel)
        if args.mode in ('prepare','run'):
            print(f.canonical(dict(invocation=dict(argv=sys.argv,python=sys.executable,cwd=str(Path.cwd()),controller_sha256=p.sha(Path(__file__))))),flush=True)
        if args.mode=='prepare':prepare(args.source_head)
        else:
            plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
            if args.protocol_sha256!=pin or plan.get('git_head')!=args.source_head:raise p.Rejected('exact future checkpoint/protocol required')
            raise SystemExit(worker(plan,pin) if args.mode=='worker' else qualify(plan,pin) if args.mode=='qualify' else execute(plan,pin))
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
