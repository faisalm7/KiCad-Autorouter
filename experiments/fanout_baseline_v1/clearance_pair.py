"""Thin fresh IR engine-only clearance20 diagnostic; old no-margin failure is context only.
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
from experiments.fanout_baseline_v1 import clearance_control as owned
PREP=ROOT/'.runs/clearance-ir-pair-preparation-001';PROTOCOL=PREP/'protocol.json'
OUT=ROOT/'.runs/clearance-ir-pair-command-001'
TIMING=ROOT/'.runs/clearance-ir-pair-timing-001'
CONTROL=ROOT/'.runs/clearance-native-control-qualification-001/result.json'
ORDER=[('ir-obstacle','NONE'),('arcdice','NONE')]
PROFILES={'NONE':'tuned-free-angle'}
LIMITS=dict(route=120,worker=180,delivered=240,output=128*1024**2,rss=4*1024**3,log=256*1024,publication=2,reader_reserve=90)
GATES={
 'ir-obstacle':['.runs/ir-obstacle-original-native-001/result.json','.runs/ir-obstacle-original-native-readback-001/result.json','.runs/ir-obstacle-original-field-gate-003/result.json'],
 'arcdice':['.runs/arcdice-original-native-001/result.json','.runs/arcdice-original-native-002-readback/result.json']}


def control(pin,path=CONTROL):
    path=ls.canonical(Path(path));protocol=owned.PROTOCOL
    if path!=owned.QUAL/'result.json' or path!=CONTROL or p.sha(path)!=pin:
        raise p.Rejected('fixed fresh clearance20 cost-qualified control receipt required')
    protocol_pin=p.sha(protocol);spec=f.read_json(protocol);owned.context(spec,protocol_pin)
    if (spec.get('kind')!='owned-roundrect-engine-margin20-v1' or type(spec.get('engine_clearance_margin_nm'))is not int or spec['engine_clearance_margin_nm']!=20000):raise p.Rejected('fresh exact corner/margin20 control required')
    qualification=f.read_json(path);qliteral=f.canonical(qualification)
    outer=owned.OUT/'result.json';outerpin=p.sha(outer);data=f.read_json(outer);oliteral=f.canonical(data)
    folder=owned.CHILD;childpath=folder/'result.json';childpin=p.sha(childpath);child=f.read_json(childpath);literal=f.canonical(child)
    process=data.get('process',{});argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(owned.__file__).resolve()),'--mode','worker','--source-head',spec['git_head'],'--protocol-sha256',protocol_pin]
    if (qualification.get('passed') is not True or qualification.get('status')!='completed' or qualification.get('accepted') is not False
            or qualification.get('git_head')!=spec['git_head'] or qualification.get('tools')!=spec['tools'] or qualification.get('protocol_sha256')!=protocol_pin
            or qualification.get('outer_receipt_sha256')!=outerpin or qualification.get('child_receipt_sha256')!=childpin
            or qualification.get('completed_evidence')!=shared.material(owned.OUT)
            or set(qualification.get('external_operations',{}))!={'prepare','run'} or set(qualification.get('external_files_sha256',{}))!={str((owned.TIMING/(stage+'-'+suffix)).relative_to(ROOT)) for stage in ('prepare','run') for suffix in ('time.log','command.log')}
            or any(p.sha(ROOT/name)!=digest for name,digest in qualification['external_files_sha256'].items())
            or any(not q.finite_nonnegative(qualification.get(k)) or qualification[k]+2>180 for k in ('wall_seconds','full_cpu_seconds'))
            or data.get('passed') is not True or data.get('status')!='completed' or data.get('accepted') is not False
            or data.get('git_head')!=spec['git_head'] or data.get('tools')!=spec['tools'] or data.get('protocol_sha256')!=protocol_pin
            or data.get('limits')!=owned.LIMITS or data.get('child_completed_evidence_bound') is not True
            or child.get('passed') is not True or child.get('status')!='completed' or child.get('accepted') is not False
            or child.get('git_head')!=spec['git_head'] or child.get('protocol_sha256')!=protocol_pin or child.get('tools')!=spec['tools']
            or not child.get('corner_clearance') or not child.get('positive') or not child.get('physical_short') or not child.get('optimizer_observation')
            or data.get('child_receipt_sha256')!=childpin or data.get('child_literal')!=literal
            or data.get('completed_evidence')!=shared.material(owned.OUT) or child.get('completed_evidence')!=shared.material(folder)
            or process.get('argv')!=argv or process.get('cwd')!=str(owned.OUT) or process.get('log')!=str(owned.OUT/'command.log')
            or process.get('status')!='success' or type(process.get('exit_code')) is not int or process['exit_code']!=0
            or process.get('cleanup_complete') is not True or process.get('log_truncated') is not False
            or p.sha(owned.OUT/'command.log')!=data.get('log_sha256')):
        raise p.Rejected('actual current positive/getter/short/whole-cost qualification unavailable')
    if owned.read_positive(spec,protocol_pin)!=child['positive']:raise p.Rejected('fresh clearance20 positive binding differs')
    owned.replay_corner(spec,child['corner_clearance']);owned.check_optimizer_observation(spec,child['optimizer_observation']);owned.replay_negative(spec,child['physical_short'])
    if (p.sha(path)!=pin or f.canonical(f.read_json(path))!=qliteral or p.sha(protocol)!=protocol_pin
            or p.sha(outer)!=outerpin or f.canonical(f.read_json(outer))!=oliteral
            or p.sha(childpath)!=childpin or f.canonical(f.read_json(childpath))!=literal):
        raise p.Rejected('fresh control qualification/protocol/outer/child changed during replay')
    material=shared.material(owned.OUT)
    if material!=data['completed_evidence'] or shared.material(folder)!=child['completed_evidence']:raise p.Rejected('owned material changed during prerequisite replay')
    owned.check_prl(spec,child)
    return qualification,dict(receipt=str(path),receipt_sha256=pin,qualification_literal=qliteral,protocol=str(protocol),protocol_sha256=protocol_pin,
        outer_receipt_sha256=outerpin,child_receipt_sha256=childpin,child_literal=literal,material=material,
        external_files_sha256=qualification['external_files_sha256'])


def check_control_prl(plan):
    binding=plan['control_binding'];protocol=Path(binding['protocol']);path=owned.CHILD/'result.json'
    if p.sha(protocol)!=binding['protocol_sha256']:raise p.Rejected('owned prerequisite protocol changed before PRL guard')
    spec=f.read_json(protocol);child=f.read_json(path)
    if (p.sha(Path(binding['receipt']))!=binding['receipt_sha256']
            or f.canonical(f.read_json(Path(binding['receipt'])))!=binding['qualification_literal']
            or p.sha(owned.OUT/'result.json')!=binding['outer_receipt_sha256']
            or shared.material(owned.OUT)!=binding['material']
            or any(p.sha(ROOT/name)!=digest for name,digest in binding['external_files_sha256'].items())):
        raise p.Rejected('owned qualification/outer/material/timing changed before PRL guard')
    if p.sha(path)!=binding['child_receipt_sha256'] or f.canonical(child)!=binding['child_literal']:
        raise p.Rejected('owned prerequisite child changed before PRL guard')
    owned.check_prl(spec,child)


def clearance_record(folder,data):
    # Replay exact argv for successful AND failed workers; failure never gains
    # routing acceptance from this settings-only check.
    p.check_engine_fanout_override(data,input_policy='native');p.check_engine_optimizer_override(data,input_policy='native')
    if (data.get('engine_fanout_override') is not False or data.get('engine_optimizer_override') is not False
            or data.get('engine_profile')!='tuned-free-angle' or data.get('scoring_variant')!='via_default'):
        raise p.Rejected('reciprocal optimizerFalse/fanoutFalse/free-angle/via_default marker missing')
    from autorouter import engine_angle
    if type(data.get('engine_planning_clearance_margin_nm'))is not int or data['engine_planning_clearance_margin_nm']!=20000:raise p.Rejected('literal clearance20 report marker required')
    proof=engine_angle.check(folder,data);engine_angle.check_scope(data,'native')
    changes=proof.get('planning_clearance',{}).get('changes',[])
    if (proof.get('clearance_margin_nm')!=20000 or len(changes)!=2 or any(row.get('before')!='200' or row.get('after')!='220' for row in changes)
            or proof.get('planning_clearance',{}).get('classification')!='B1_adapter_only'):raise p.Rejected('IR exact two original200 to engine220 planning atoms required')
    budget=data['engine_budget'];profile=data['engine_profile']
    expected=p.engine_profile_settings(profile,budget['remaining_outer_wall_seconds_at_assignment'],scoring_variant='via_default',
        experimental_free_angle=True,fanout_enabled=False,experimental_fanout=True)
    actual={k:v for k,v in budget.items() if k not in ('optimizer_enabled','outer_task_wall_budget_seconds','outer_task_cpu_budget_seconds')}
    actual['argv']=list(actual['argv']);actual['argv'].remove('--router.optimizer.enabled=false')
    if (actual!=expected or budget.get('strict_class_targets') is not False or budget['argv'].count('--router.optimizer.enabled=false')!=1
            or budget['argv'].count('--router.fanout.enabled=false')!=1
            or any(x in budget['argv'] for x in ('--router.automatic_neckdown=false','--router.neck_width_um=0'))
            or p.netclass_policy(Path(data['source'])) is not None or p.minimum_width_guard(Path(data['source']),'both') is not None
            or budget.get('outer_task_wall_budget_seconds')!=120 or budget.get('outer_task_cpu_budget_seconds')!=120):
        raise p.Rejected('optimizer override changed more than one flag/inactive caps/default neckdown')

    rows=[s for s in data['steps'] if s.get('name')=='engine'];process=f.read_json(folder/'engine-process.json')
    if (len(rows)!=1 or process!=rows[0] or process.get('argv')!=p.engine_argv(folder,budget['argv'],profile=profile)
            or process.get('cwd')!=str(folder) or process.get('cleanup_complete') is not True):raise p.Rejected('actual engine optimizer/fanout journal/lineage differs')
    if data.get('accepted') is True:p.check_engine_profile_record(data,folder)
    return dict(engine_process_sha256=p.sha(folder/'engine-process.json'),strict_class_targets=False,fanout_enabled=False,optimizer_enabled=False,engine_planning_clearance_margin_nm=20000,engine_planning_proof_sha256=p.sha(folder/'engine-angle.json'),only_optimizer_override_flag=True,only_clearance_edit_two_atoms=True,
        worker_status=process['status'],settings_replay_only=True)


def source(project):
    board,family=q.selected_source(project);packet,files=capture_native_source(project,root=ROOT)
    return board,family,dict(packet=str(packet),files={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()})


def eligibility(board):
    policy=p.netclass_policy(board);width=p.minimum_width_guard(board,'both')
    strict=policy is not None or width is not None
    return dict(execution_eligible=not strict,derived_strict_class_targets=strict,netclass_policy=policy,minimum_width_guard=width,
        refusal='unsupported: clearance20 requires free-angle optimizerFalse/fanoutFalse and derived non-strict class/width targets before Job' if strict else None)


def historical_no_margin():
    """Read-only raw historical failure identity; never checker/solver admission."""
    folder=ROOT/'.runs/no-optimizer-pair-001/ir-obstacle/NONE/child/route';receipt=folder/'result.json';data=f.read_json(receipt)
    candidate=folder/'candidate/IR_Sensor.kicad_pcb';report=folder/'final-drc.json'
    errors=[row for row in data.get('native',{}).get('findings',[]) if row.get('severity')=='error']
    if (data.get('tools',{}).get('git_head')!='93e3687c6edd60dd36e34ea93302c3484ae6ff52' or data.get('accepted') is not False or data.get('status')!='drc_rejected'
            or data.get('candidate')!=str(candidate) or data.get('candidate_sha256')!='38424bd6fcb64ef944cfed6b8ffe389f98d88f2c9d7f3e63cc0a49de674d8838'
            or data.get('native_report_sha256')!='a23b290808ad1394a78ad78da3d9a837a28512f82f0f69f65aa4b6e63db6b5ac'
            or p.sha(candidate)!=data['candidate_sha256'] or p.sha(report)!=data['native_report_sha256']
            or len(errors)!=1 or errors[0].get('type')!='clearance' or data['native'].get('opens')!=0 or data['native'].get('blocking')!=1 or data['native'].get('warnings')!=42):
        raise p.Rejected('specific completed no-margin failure context differs')
    return dict(receipt=str(receipt),receipt_sha256=p.sha(receipt),candidate=str(candidate),candidate_sha256=data['candidate_sha256'],native_report=str(report),native_report_sha256=data['native_report_sha256'],
        git_head=data['tools']['git_head'],status=data['status'],accepted=False,errors=errors,metrics=data['metrics'],source_hashes=data['source_hashes'],scope='Raw historical context only; no current reader admission, source metadata rewrite, candidate/incumbent reuse or rerun.')


def prepare(head,control_pin,control_path):
    shared.clean(head);qualified,binding=control(control_pin,control_path)
    if qualified['git_head']!=head:raise p.Rejected('owned control must bind this exact current checkpoint')
    PREP.mkdir();projects={}
    for project in ('ir-obstacle','arcdice'):
        board,family,packet=source(project);freeze=q.freeze(board);p.preflight(board)
        gates={n:p.sha(ROOT/n) for n in GATES[project]}
        original=f.read_json(ROOT/GATES[project][-1])
        baseline=original['qualified_native'] if project=='ir-obstacle' else original['native']
        if not p.native_accepted(baseline) or baseline['warnings']!=({'ir-obstacle':42,'arcdice':26}[project]):raise p.Rejected('qualified untouched original fullSCH baseline unavailable')
        state=eligibility(board)
        if state['execution_eligible'] is not (project=='ir-obstacle'):raise p.Rejected('frozen IR eligible/Arc strict unsupported scope changed; inspect separately')
        projects[project]=dict(source=str(board),family=family,packet=packet,freeze=freeze,gates=gates,gate_material={n:shared.material((ROOT/n).parent) for n in gates},baseline=baseline,eligibility=state)
    historical=historical_no_margin()
    if historical['source_hashes']!=projects['ir-obstacle']['freeze']['source_hashes']:raise p.Rejected('historical context source differs from frozen current original')
    plan=dict(schema=1,kind='fresh-ir-clearance20-with-arcdice-unsupported-v1',status='frozen',git_head=head,
        helper_sha256={n:p.sha(ROOT/n) for n in ['experiments/native_paired_v1/observations.py','experiments/native_paired_v1/readback.py','scripts/experiment_quality.py','scripts/experiment_paired.py','scripts/fetch_led_demo.py','experiments/hfe_original_native_v1/driver.py','experiments/free_angle_baseline_v1/controls.py','experiments/fanout_baseline_v1/native_control.py','experiments/fanout_baseline_v1/continuation.py','experiments/fanout_baseline_v1/clearance_control.py','experiments/fanout_baseline_v1/clearance_fixture.py','experiments/fanout_baseline_v1/OptimizerObservation.java','experiments/fanout_baseline_v1/fixture.py','experiments/fanout_baseline_v1/__init__.py']},controller_sha256=p.sha(Path(__file__)),control_receipt=str(ls.canonical(control_path)),control_sha256=control_pin,control_binding=binding,
        historical_no_margin_context=historical,historical_reference_scope='Immutable exposed outcome references only, no fresh solver reuse or matched-current-batch claim.',projects=projects,tools=projects['ir-obstacle']['freeze']['tools'],arm_order=[list(x) for x in ORDER],profiles=PROFILES,scoring_variant='via_default',engine_fanout_override=False,engine_optimizer_override=False,engine_planning_clearance_margin_nm=20000,limits=LIMITS,planned_external_timing_directory=str(TIMING),
        source_acquisition='Existing immutable local originals; no GET or historical solver reuse. Source-preflight work is fresh inside each arm.',
        scope='Two-row complete exposed IR/Arc population, ONE NEW IR NONE engine-only20um margin with fanoutFalse/optimizerFalse/native1000/whole/both/non-strict; Arc strict unsupported before Job/Native/engine. Original task/default200 rules/geometry/SCH/PRL remain exact; engine only generic/class200to220, SMD/edge unchanged. B1 adapter correctness hypothesis, not C novelty/gain/default/general support. Completed old93e no-margin clearance failure is immutable context only, no rerun/reuse/fresh sameHEAD paired comparison. All new preparation/replays/preflight/ownsolver/reader/cleanup/publication charged; prior original/control engineering separate.')
    context(plan)
    plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
    if max(plan['preparation_costs']['wall_seconds'],plan['preparation_costs']['full_cpu_seconds'])+2>=58:raise p.Rejected('preparation exhausted fixed complete-delivery margin')
    p.save_json(PROTOCOL,plan);print(f.canonical(dict(prepared=True,protocol=str(PROTOCOL),sha256=p.sha(PROTOCOL),native_executed=False)))


def context(plan,pin=None):
    shared.clean(plan['git_head'])
    if (plan.get('kind')!='fresh-ir-clearance20-with-arcdice-unsupported-v1' or plan.get('status')!='frozen'
            or plan.get('limits')!=LIMITS or plan.get('profiles')!=PROFILES or plan.get('arm_order')!=[list(x) for x in ORDER]
            or set(plan.get('projects',{}))!={'ir-obstacle','arcdice'} or plan.get('engine_fanout_override') is not False or plan.get('engine_optimizer_override') is not False or type(plan.get('engine_planning_clearance_margin_nm'))is not int or plan['engine_planning_clearance_margin_nm']!=20000 or plan.get('planned_external_timing_directory')!=str(TIMING)
            or plan.get('scoring_variant')!='via_default' or plan['tools'].get('kicad')!='10.0.0' or p.tool_manifest()!=plan['tools'] or p.sha(Path(__file__))!=plan['controller_sha256']):raise p.Rejected('fixed pair protocol/controller differs')
    if any(p.sha(ROOT/n)!=value for n,value in plan['helper_sha256'].items()):raise p.Rejected('frozen pair helper changed')
    qualified,binding=control(plan['control_sha256'],Path(plan['control_receipt']))
    if qualified.get('git_head')!=plan['git_head'] or qualified.get('tools')!=plan['tools']:raise p.Rejected('owned qualification checkpoint/tools differ')
    if binding!=plan['control_binding']:raise p.Rejected('owned qualification material changed')
    for project,spec in plan['projects'].items():
        board,family,packet=source(project)
        if str(board)!=spec['source'] or family!=spec['family'] or packet!=spec['packet']:raise p.Rejected('original source packet changed')
        q.verify_freeze(spec['freeze'],board)
        if eligibility(board)!=spec['eligibility'] or spec['eligibility']['execution_eligible'] is not (project=='ir-obstacle'):raise p.Rejected('source-derived eligible/unsupported disposition changed')
        for name,digest in spec['gates'].items():
            if p.sha(ROOT/name)!=digest or shared.material((ROOT/name).parent)!=spec['gate_material'][name]:raise p.Rejected('historical original proof/material changed')
    if pin is not None and (p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan)):raise p.Rejected('frozen protocol changed')
    if historical_no_margin()!=plan['historical_no_margin_context']:raise p.Rejected('historical completed no-margin failure context changed')
    check_control_prl(plan)  # Last after all source/gate/protocol byte reads.


def worker(plan,pin,project,angle):
    context(plan,pin);spec=plan['projects'][project];board=Path(spec['source']);folder=OUT/project/angle/'child'
    if spec['eligibility']['execution_eligible'] is not True:raise p.Rejected(spec['eligibility']['refusal'])
    folder.mkdir();owner={};h.capture_destination(owner,folder)
    record=dict(schema=1,accepted=False,passed=False,status='failed',project=project,angle=angle,profile=PROFILES[angle],
        scoring_variant='via_default',protocol_sha256=pin,git_head=plan['git_head'],tools=spec['freeze']['tools'],scope=plan['scope'])
    routed=None
    try:
        route_start,route_cpu=time.monotonic(),cpu()
        routed=p.route(board,folder/'route',120,False,'both',PROFILES[angle],scoring_variant='via_default',_fanout_enabled=False,_optimizer_enabled=False,_engine_clearance_margin_nm=20000)
        route_wall,route_full=time.monotonic()-route_start,cpu()-route_cpu
        stored=f.read_json(folder/'route/result.json')
        if f.canonical(stored)!=f.canonical(routed):raise p.Rejected('returned routing receipt differs from stored snapshot')
        if stored.get('tools')!=record['tools'] or stored.get('source_hashes')!=spec['freeze']['source_hashes']:raise p.Rejected('fresh result source/tool binding differs')
        # Retain raw summary even if a later settings/Native observation fails.
        arm=dict(id=angle,adapter='both',engine_profile=PROFILES[angle],operation='route')
        record['row']=q.summarize(arm,folder/'route',stored,route_wall,route_full)
        record['route_receipt_sha256']=p.sha(folder/'route/result.json')
        record['clearance_replay']=clearance_record(folder/'route',stored)
        with p.validation_readback_session():
            record['workers']=obs.workers(folder/'route',stored,board,spec['freeze']['source_hashes'],sx.read(board))
            error=obs.resource_failure(folder/'route',stored)
            if (folder/'route/final-drc.json').is_file():
                record['candidate']=obs.candidate(folder/'route',stored,board,sx.read(board),spec['freeze']['source_hashes'],spec['baseline'],resource_error=error)
            row=record['row']
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
        check_control_prl(plan)
        if routed is not None:ls.check_normal_policy(folder/'route',routed,max_bytes=LIMITS['output'],max_files=2048)
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
        if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
        if record['status']!='completed':record['passed']=False
    f.publish(folder,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    result=f.read_json(folder/'result.json')
    if f.canonical(result)!=f.canonical(record):raise p.Rejected('child canonical snapshot differs')
    return 0 if result.get('passed') is True and result.get('status')=='completed' else 130 if result.get('status')=='cancelled' else 2


def execute(plan,pin,project,angle):
    context(plan,pin);index=ORDER.index((project,angle))
    if plan['projects'][project]['eligibility']['execution_eligible'] is not True:
        print(f.canonical(next(row for row in dispositions(plan,pin)['rows'] if row['project']==project and row['angle']==angle)))
        return 2  # No Job, arm directory, Native worker or engine is created.
    # Frozen population order; only eligible IR runs; failures/cancellation remain visible.
    for prior_project,prior_angle in ORDER[:index]:
        prior=f.read_json(OUT/prior_project/prior_angle/'result.json')
        if (prior.get('protocol_sha256')!=pin or prior.get('status')=='cancelled'
                or prior.get('process',{}).get('cleanup_complete') is not True
                or not prior.get('child',{}).get('workers')):raise p.Rejected('prior arm absent/different/cancelled or worker cleanup/census unqualified')
    folder=OUT/project/angle
    if folder.exists() or folder.is_symlink():raise p.Rejected('fresh exclusive arm output required')
    folder.parent.mkdir(parents=True,exist_ok=True);folder.mkdir();owner={};h.capture_destination(owner,folder)
    prep=plan['preparation_costs'];prewall=prep['wall_seconds']+2;precpu=prep['full_cpu_seconds']+2
    if prep.get('publication_allowance_seconds')!=2 or any(not q.finite_nonnegative(prep.get(k)) for k in ('wall_seconds','full_cpu_seconds')):raise p.Rejected('finite measured preparation costs required')
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
        witness=shared.material(folder);passed=bool(bound and child.get('passed') is True and child.get('status')=='completed' and child.get('accepted') is False
            and child.get('project')==project and child.get('angle')==angle and child.get('profile')==PROFILES[angle]
            and child.get('protocol_sha256')==pin and child.get('git_head')==plan['git_head'] and child.get('tools')==plan['projects'][project]['freeze']['tools']
            and child.get('row',{}).get('accepted') is True and child.get('clearance_replay',{}).get('engine_planning_clearance_margin_nm')==20000
            and process['status']=='success' and type(process['exit_code'])is int and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
        record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'cancelled' if process['status']=='cancelled' or child and child.get('status')=='cancelled' else 'failed',
            project=project,angle=angle,protocol_sha256=pin,git_head=plan['git_head'],controller_sha256=plan['controller_sha256'],process=process,
            child_receipt_sha256=childpin,child_completed_evidence_bound=bound,child=child,child_literal=literal,completed_evidence=witness,
            preparation_costs=prep,complete_delivered_cap_seconds=240,reader_complete_enclosure_upper_allowance_seconds=90,delivery_qualification_pending_external_complete_costs=True,scope=plan['scope'],
            accounting_scope='Actual enclosing self+reaped-descendant CPU/wall includes full child routing, semantic readback and child publication tail; final enclosing publication bounded separately by2s allowance, with actual late cap enforcement.')
        def stable():
            h.owned_destination(owner);context(plan,pin)
            if shared.material(folder)!=witness:raise p.Rejected('complete enclosing material changed')
            if child is not None and (not bound or p.sha(path)!=childpin or f.canonical(f.read_json(path))!=literal or shared.material(folder/'child')!=child['completed_evidence']):raise p.Rejected('published child changed after exit')
            check_control_prl(plan)
            if child is not None and child.get('route_receipt_sha256'):
                route_data=f.read_json(folder/'child/route/result.json')
                ls.check_normal_policy(folder/'child/route',route_data,max_bytes=LIMITS['output'],max_files=2048)
        def account():
            record.update(wall_seconds=prewall+time.monotonic()-START,full_cpu_seconds=precpu+cpu()-CPU0,publication_allowance_seconds=2)
            if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
            if record['status']!='completed':record['passed']=False
        f.publish(folder,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
        result=f.read_json(folder/'result.json')
        if f.canonical(result)!=f.canonical(record):raise p.Rejected('outer canonical snapshot differs')
        print(f.canonical({k:result.get(k) for k in ['project','angle','passed','status','wall_seconds','full_cpu_seconds']}))
        return 0 if result.get('passed') is True and result.get('status')=='completed' else 130 if result.get('status')=='cancelled' else 2


def dispositions(plan,pin):
    """Enumerate exactly both frozen arms, including absent/unattempted reasons."""
    context(plan,pin);rows=[]
    for project,angle in ORDER:
        path=OUT/project/angle/'result.json';spec=plan['projects'][project]
        if spec['eligibility']['execution_eligible'] is not True:
            if path.parent.exists() or path.parent.is_symlink():raise p.Rejected('unsupported arm unexpectedly has an execution directory')
            rows.append(dict(project=project,angle=angle,status='unsupported',accepted=False,attempted=False,routing_executed=False,native_executed=False,candidate=None,result=None,
                source=spec['source'],source_hashes=spec['freeze']['source_hashes'],reason=spec['eligibility']['refusal'],eligibility=spec['eligibility']))
            continue
        if not path.is_file():
            absent=not path.parent.exists()
            rows.append(dict(project=project,angle=angle,status='not_attempted' if absent else 'missing_receipt',accepted=False,candidate=None,
                reason='No arm output directory: this controller creates it before any Native launch; prior guard/launch refusal or absent command, consult retained outer log.' if absent else 'Arm directory exists without a receipt; attempt outcome unknown, consult retained launch/process log.',result=str(path)))
            continue
        data=f.read_json(path)
        if data.get('protocol_sha256')!=pin:raise p.Rejected('population receipt protocol differs')
        rows.append(dict(project=project,angle=angle,status=data.get('status'),accepted=data.get('passed') is True,
            reason=data.get('error') or data.get('reason'),result=str(path),result_sha256=p.sha(path)))
    check_control_prl(plan)
    return dict(schema=1,arm_order=[list(x) for x in ORDER],rows=rows,scope='complete declared two-arm dispositions; missing rows are never accepted or synthesized candidates')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=['prepare','run','worker','report'],required=True)
    parser.add_argument('--source-head',required=True);parser.add_argument('--protocol-sha256');parser.add_argument('--control-sha256')
    parser.add_argument('--control-receipt',type=Path,default=CONTROL)
    parser.add_argument('--project',choices=['ir-obstacle','arcdice']);parser.add_argument('--arm',choices=list(PROFILES));args=parser.parse_args()
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def cancel(*_):raise KeyboardInterrupt
    try:
        for sig in previous:signal.signal(sig,cancel)
        if args.mode=='prepare':prepare(args.source_head,args.control_sha256,args.control_receipt)
        else:
            plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
            if plan['git_head']!=args.source_head or args.protocol_sha256!=pin:raise p.Rejected('exact frozen intended protocol required')
            if args.mode=='report':print(f.canonical(dispositions(plan,pin)))
            else:
                if (args.project,args.arm) not in ORDER:raise p.Rejected('exact frozen intended arm required')
                raise SystemExit(worker(plan,pin,args.project,args.arm) if args.mode=='worker' else execute(plan,pin,args.project,args.arm))
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
