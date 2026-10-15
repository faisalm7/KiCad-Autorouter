"""Prospective untouched HFE original1007 diagnostic; no routing admission.
SPDX-License-Identifier: GPL-3.0-or-later
Lead copies this to ROOT/.runs after the required checkpoint; never auto-fetch.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,collections,fcntl,hashlib,json,os,re,signal,stat,subprocess,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io,handoff as h,sexpr as sx,local_settings as ls
from autorouter.runner import run
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.original_project_native_v1.driver import route_records
SOURCE=ROOT/'.runs/hfe-original-acquisition-001/source'
ACQUISITION=SOURCE.parent/'result.json'
COMMIT='7be61154def1890aa66368b3385ad8661447d52f'
STEM='transistor-hfe-measurement-circuit'
SOURCE_PINS={
 'LICENSE':'eeecc593866fa1c3b80189c7e3dc0ceb77740557fa92f81771f891cc54c579cb',
 'README.md':'f94f23f2ffc9771a22955aecd9ce24f529cb7aa8fd4ddae9f8dd5196ce21ffb8',
 'cc-component.kicad_sch':'412415a834bfa9f727182532f334b0cbfdd247d2d796b5b5772ab413e2d8a875',
 STEM+'.kicad_pcb':'d3d6d28a1f65d3950aa04552194c5e182adcad407c96d11a1673de19d39c0651',
 STEM+'.kicad_pro':'684f83f599188810229a3e1bcc3378daef39625db1e75f1042e367627f6671a5',
 STEM+'.kicad_sch':'8431a00b25b339919a0432a22eade01756dd6bbf45238bcab3c4a9a79b22cee8'}
PROOF=ROOT/'.runs/kicad-1007-bundle-qualification-001/result.json'
PROOF_PIN='26564ecd90268e463760270902d302445d9b0e6859105d3ed06e5976a8989c73'
PREP=ROOT/'.runs/hfe-original-native-preparation-001';PROTOCOL=PREP/'protocol.json'
OUTER=ROOT/'.runs/hfe-original-native-execution-001';CHILD=OUTER/'native'
LIMIT=128*1024**2
STATIC_REFUSAL='unsupported: netclass bindings not qualified: native netclasses currently require two copper layers; rule-area restrictions not qualified: pour-only area requires explicit net 0'


def source():
    receipt=f.read_json(ACQUISITION)
    if (receipt.get('passed') is not True or receipt.get('status')!='completed' or receipt.get('commit')!=COMMIT
            or receipt.get('source_files_sha256')!=SOURCE_PINS):raise p.Rejected('fixed acquisition receipt differs')
    files=io.inventory(SOURCE,contents=True,max_bytes=4*1024**2,max_files=6,max_entries=6)
    if {n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}!=SOURCE_PINS:raise p.Rejected('six immutable acquired source files differ')
    return files


def clean(head):
    if re.fullmatch(r'[0-9a-f]{40}',head) is None:raise p.Rejected('exact intended source HEAD required')
    env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_TERMINAL_PROMPT='0')
    args=['git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null']
    def observed(tail):return subprocess.run([*args,*tail],cwd=ROOT,env=env,capture_output=True,text=True,check=True,timeout=10).stdout.strip()
    if observed(['rev-parse','HEAD'])!=head or observed(['status','--porcelain=v1','--untracked-files=normal']):raise p.Rejected('clean frozen source required')


def material(root):
    files,dirs=io.inventory(root,max_bytes=LIMIT,max_files=2048,max_entries=4096,with_directories=True)
    files={n:v for n,v in files.items() if n not in {'result.json','result.json.partial'} and not n.startswith(('invalidated-result-','interrupted-result-'))}
    return dict(files=files,directories=list(dirs))


def current(plan):
    clean(plan['git_head']);source()
    if p.sha(ACQUISITION)!=plan['acquisition_receipt_sha256'] or p.sha(PROOF)!=PROOF_PIN:raise p.Rejected('source or signed bundle proof changed')
    nt=p.ExperimentalNativeToolchain.from_record(plan['native_toolchain'])
    if p.tool_manifest(native_toolchain=nt)!=plan['tools']:raise p.Rejected('current pinned tools/code/HEAD differ')
    if any(p.sha(ROOT/name)!=pin for name,pin in plan['code_sha256'].items()):raise p.Rejected('frozen diagnostic implementation changed')
    return nt


def prepare(head):
    clean(head);source()
    if p.sha(PROOF)!=PROOF_PIN:raise p.Rejected('fixed signed/notarized proof changed')
    proof=f.read_json(PROOF)
    if proof.get('signature_verified') is not True or proof.get('notarization_verified') is not True:raise p.Rejected('qualified bundle proof unavailable')
    nt=p.ExperimentalNativeToolchain.from_record(proof['experimental_native_toolchain']);tools=p.tool_manifest(native_toolchain=nt)
    if tools['git_head']!=head:raise p.Rejected('intended checkpoint differs')
    # Preserve the refusal as evidence; this diagnostic never changes admission.
    try:p.preflight(SOURCE/(STEM+'.kicad_pcb'))
    except p.Rejected as exc:refusal=str(exc)
    else:raise p.Rejected('expected unchanged static refusal absent')
    if refusal!=STATIC_REFUSAL:raise p.Rejected('current static refusal changed; inspect before Native')
    names=set(tools['implementation_sha256'])|{str(Path(__file__).relative_to(ROOT)),
        'experiments/original_project_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py'}
    plan=dict(schema=1,kind='hfe-original-native1007-v1',status='frozen_for_lead_execution',git_head=head,
        source_commit=COMMIT,source_files_sha256=SOURCE_PINS,source_path=str(SOURCE),static_refusal=refusal,
        acquisition_receipt_sha256=p.sha(ACQUISITION),bundle_proof_sha256=PROOF_PIN,native_toolchain=nt.record(),tools=tools,
        code_sha256={n:p.sha(ROOT/n) for n in sorted(names)},
        limits=dict(whole_wall_full_cpu_seconds=120,worker_wall_seconds=90,worker_wall_full_cpu_seconds=90,
            scratch_bytes=LIMIT,group_rss_bytes=2*1024**3,log_bytes=256*1024,publication_allowance_seconds=2),
        source_route_count=785,accepted=False,production_support_qualified=False,
        scope='Untouched original HFE diagnostic only: saved refill and all-original-route original-shell fullSCH on caller-pinned1007. No engine/export/routing, source repair, schema waiver, support admission, physical/GUI/default/tool promotion or comparative claim.')
    PREP.mkdir();current(plan)
    plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
    p.save_json(PROTOCOL,plan)
    print(f.canonical(dict(prepared=True,protocol=str(PROTOCOL),sha256=p.sha(PROTOCOL),native_executed=False)))


def raw_stage(job,name):
    """Preserve raw array counts when normal parsing fails; never call them pass."""
    path=job.out/(name+'.json');value=dict(qualified=False,report_sha256=None,raw_population=None)
    if not path.exists() and not path.is_symlink():return value
    try:
        captured=io.read_bytes(path,64*1024**2);value['report_sha256']=hashlib.sha256(captured).hexdigest()
        raw=f.read_json(path)
        if p.sha(path)!=value['report_sha256']:raise p.Rejected('raw report changed during capture')
        arrays={k:raw[k] for k in ('violations','unconnected_items','schematic_parity')}
        if any(type(x)is not list for x in arrays.values()):raise p.Rejected('raw arrays unavailable')
        severity=collections.Counter(str(x.get('severity','MISSING')) for rows in arrays.values() for x in rows if type(x)is dict)
        value.update(raw_version=raw.get('kicad_version'),raw_source=raw.get('source'),
            raw_population={k:len(v) for k,v in arrays.items()},raw_severity_histogram=dict(severity),
            raw_ignored_checks=raw.get('ignored_checks'),raw_included_severities=raw.get('included_severities'))
    except Exception as exc:value['raw_capture_error']=type(exc).__name__+': '+str(exc)
    return value


class BoundJob(f.FloorJob):
    # Same FloorJob/Job dispatch and PRL lifecycle, explicit narrower runner caps.
    # Inner workers own separate process groups; each needs its own RSS/log cap.
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        p.experimental_native_version(self.native_toolchain)
        cap=min(30,self.remaining())
        if cap<=0:raise p.Rejected('whole original diagnostic budget exhausted')
        self.deadline=time.monotonic()+cap
        actual=[str(x) for x in (argv if already_sandboxed else [*f.SANDBOX,*argv])]
        step=run(actual,cwd=self.out,log=self.out/(name+'.log'),timeout=cap,env=self.env,
            max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
        step['name']=name;self.steps.append(step);p.save_json(self.out/(name+'-process.json'),step)
        if (step['status'] not in ('success','nonzero_exit') or type(step['exit_code'])is not int
                or step['exit_code'] not in allowed or step.get('cleanup_complete') is not True or step.get('log_truncated') is not False):
            raise p.Rejected(name+': '+step['status']+' exit='+str(step['exit_code']))
        p.experimental_native_version(self.native_toolchain)
        return step


def worker(plan,pin):
    nt=current(plan)
    if CHILD.exists() or CHILD.is_symlink():raise p.Rejected('fresh original diagnostic child required')
    CHILD.mkdir();owner={};h.capture_destination(owner,CHILD)
    def remaining():return min(88-(time.monotonic()-START),88-(cpu()-CPU0))
    job=BoundJob(CHILD/'job',90,remaining,native_toolchain=nt,protect_local_settings=True,experimental_schematic_parity=True)
    code={Path(name).name:io.read_bytes(ROOT/name,1024**2) for name in plan['tools']['implementation_sha256']}
    copy_bytes(code,job.out/'code')
    captured={name:io.read_bytes(ROOT/name,1024**2) for name in plan['code_sha256']}
    captured['prospective-protocol.json']=io.read_bytes(PROTOCOL)
    copy_bytes(captured,CHILD/'control-code');copy_bytes(source(),CHILD/'original')
    board=CHILD/'original'/(STEM+'.kicad_pcb');original=sx.read(board)
    if len(route_records(original))!=785:raise p.Rejected('complete original route identity census differs')
    record=dict(schema=1,accepted=False,passed=False,status='failed',observation_complete=False,
        production_support_qualified=False,tools=plan['tools'],source_commit=COMMIT,source_files_sha256=SOURCE_PINS,
        static_refusal=plan['static_refusal'],source_route_count=785,protocol_sha256=pin,steps=job.steps,scope=plan['scope'])
    stages=[];candidate=None;completed=None
    try:
        saved=job.out/'saved';copy_bytes(source(),saved);savedboard=saved/board.name;before=p.tree_hash(saved)
        stages.append(('original-refill',savedboard,savedboard,True,before,False))
        refill=job.drc('original-refill',savedboard,save=True)
        observed=f.check_drc_stage(job.out,record,'original-refill',savedboard,savedboard,True,before,
            native_toolchain=nt,experimental_schematic_parity=True)
        if f.canonical(observed)!=f.canonical(refill):raise p.Rejected('refill shared readback differs')
        emitted=sx.read(savedboard)
        record.update(native_saved_nonfill_ast_equal=p.immutable(original)==p.immutable(emitted),
            native_saved_route_records_equal=route_records(original)==route_records(emitted))
        candidate=CHILD/'candidate'/board.name;copy_bytes(source(),candidate.parent)
        sx.write(candidate,p.transplant_fill(original,emitted))
        if p.immutable(sx.read(candidate))!=p.immutable(original) or route_records(sx.read(candidate))!=route_records(original):raise p.Rejected('source shell/all785route records changed')
        p.verify_candidate_files(candidate,SOURCE_PINS,p.sha(candidate));before_final=p.tree_hash(candidate.parent)
        stages.append(('original-final',candidate,job.out/'original-final-input'/board.name,False,before_final,True))
        final=job.drc('original-final',candidate,schematic_parity=True)
        observed=f.check_drc_stage(job.out,record,'original-final',candidate,job.out/'original-final-input'/board.name,False,before_final,
            schematic_parity=True,native_toolchain=nt,experimental_schematic_parity=True)
        if f.canonical(observed)!=f.canonical(final):raise p.Rejected('fullSCH shared readback differs')
        record.update(observation_complete=True,original_native=refill,parity_native=final,
            native_routing_scope_accepted=p.native_accepted(final),final_candidate=str(candidate),final_candidate_sha256=p.sha(candidate),
            final_native_report_sha256=p.sha(job.out/'original-final.json'),original_shell_nonfill_ast_equal=True,all_original_route_records_exact=True)
        record['passed']=p.native_accepted(final)
        record['status']='completed' if record['passed'] else 'observed_unqualified'
    except (Exception,KeyboardInterrupt) as exc:
        record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) or any(step.get('status')=='cancelled' for step in job.steps) else 'failed',error=type(exc).__name__+': '+str(exc))
    record['raw_reports']={}
    try:
        for name,*_ in stages:record['raw_reports'][name]=raw_stage(job,name)
    except KeyboardInterrupt as exc:
        record.update(passed=False,status='cancelled',error=type(exc).__name__+': '+str(exc))
    for captured in record['raw_reports'].values():
        captured['shared_stage_replay_complete']=record['observation_complete']
    completed=material(CHILD);record['completed_evidence']=completed
    def stable():
        h.owned_destination(owner);current(plan)
        if p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan):raise p.Rejected('frozen prospective protocol changed')
        if p.tree_hash(board.parent)!=SOURCE_PINS or material(CHILD)!=completed:raise p.Rejected('original/completed Native material changed')
        if candidate is not None:
            p.verify_candidate_files(candidate,SOURCE_PINS,p.sha(candidate))
            if p.immutable(sx.read(candidate))!=p.immutable(original) or route_records(sx.read(candidate))!=route_records(original):raise p.Rejected('all original shell/route records changed late')
        if record['observation_complete']:
            if p.sha(candidate)!=record['final_candidate_sha256'] or p.sha(job.out/'original-final.json')!=record['final_native_report_sha256']:raise p.Rejected('final candidate/report changed')
            for name,src,inp,savedflag,before,parity in stages:
                native=f.check_drc_stage(job.out,record,name,src,inp,savedflag,before,schematic_parity=parity,native_toolchain=nt,experimental_schematic_parity=True)
                if f.canonical(native)!=f.canonical(record['parity_native' if parity else 'original_native']):raise p.Rejected('late Native stage changed')
            ls.check_normal_policy(job.out,record,max_bytes=LIMIT,max_files=2048,native_toolchain=nt)
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
        if remaining()<=0:
            record['passed']=False
            if record['status']!='cancelled':record['status']='budget_exceeded'
        if record['status']!='completed':record['passed']=False
    f.publish(CHILD,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    stored=f.read_json(CHILD/'result.json');print(f.canonical({k:stored.get(k) for k in ('passed','status','observation_complete','wall_seconds','full_cpu_seconds')}))
    return 0 if stored.get('passed') is True and stored.get('status')=='completed' else 2


def execute(plan,pin):
    nt=current(plan);OUTER.mkdir();owner={};h.capture_destination(owner,OUTER)
    costs=plan['preparation_costs'];prepwall=costs['wall_seconds']+2;prepcpu=costs['full_cpu_seconds']+2
    if costs['publication_allowance_seconds']!=2 or min(prepwall,prepcpu)<2:raise p.Rejected('preparation costs differ')
    def remaining():return min(118-prepwall-(time.monotonic()-START),118-prepcpu-(cpu()-CPU0))
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared quality lane required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__)),
            '--mode','worker','--source-head',plan['git_head'],'--protocol-sha256',pin]
        process=run(argv,cwd=OUTER,log=OUTER/'command.log',timeout=max(.001,min(90,remaining())),
            max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
        path=CHILD/'result.json';childpin=p.sha(path) if path.is_file() else None
        child=f.read_json(path) if childpin is not None else None
        child_bound=bool(child and material(CHILD)==child.get('completed_evidence')
            and p.sha(path)==childpin and f.canonical(f.read_json(path))==f.canonical(child))
        # Only bind the enclosing witness after checking the child's own
        # pre-publication witness and exact literal receipt; do not adopt edits.
        witness=material(OUTER);logpin=p.sha(OUTER/'command.log')
        passed=bool(child_bound and child.get('passed') is True and child.get('status')=='completed'
            and child.get('observation_complete') is True and child.get('accepted') is False and child.get('production_support_qualified') is False
            and child.get('tools')==plan['tools'] and process['status']=='success' and process['exit_code']==0
            and process['cleanup_complete'] is True and process['log_truncated'] is False)
        record=dict(schema=1,accepted=False,passed=passed,status='cancelled' if process['status']=='cancelled' or child and child.get('status')=='cancelled' else 'completed' if passed else 'failed',production_support_qualified=False,
            source_commit=COMMIT,source_files_sha256=SOURCE_PINS,git_head=plan['git_head'],tools=plan['tools'],protocol_sha256=pin,
            controller_sha256=p.sha(Path(__file__)),preparation_costs=costs,process=process,child_receipt_sha256=childpin,child_material_bound=child_bound,
            child=child,completed_evidence=witness,log_sha256=logpin,limits=plan['limits'],scope=plan['scope'])
        def stable():
            h.owned_destination(owner);current(plan)
            if p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan):raise p.Rejected('enclosing protocol changed')
            if material(OUTER)!=witness or p.sha(OUTER/'command.log')!=logpin:raise p.Rejected('whole completed evidence changed')
            if child is not None and (not child_bound or material(CHILD)!=child.get('completed_evidence')
                    or p.sha(path)!=record['child_receipt_sha256'] or f.canonical(f.read_json(path))!=f.canonical(child)):
                raise p.Rejected('child pre-publication material or literal receipt changed')
            if child and child.get('observation_complete'):
                job=CHILD/'job';ls.check_normal_policy(job,child,max_bytes=LIMIT,max_files=2048,native_toolchain=nt)
        def account():
            record.update(invocation_wall_seconds=time.monotonic()-START,invocation_full_cpu_seconds=cpu()-CPU0,
                wall_seconds=prepwall+time.monotonic()-START,full_cpu_seconds=prepcpu+cpu()-CPU0,publication_allowance_seconds=2)
            if remaining()<=0:
                record['passed']=False
                if record['status']!='cancelled':record['status']='budget_exceeded'
            if record['status']!='completed':record['passed']=False
        f.publish(OUTER,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
        stored=f.read_json(OUTER/'result.json');print(f.canonical({k:stored.get(k) for k in ('passed','status','wall_seconds','full_cpu_seconds')}))
        return 0 if stored.get('passed') is True and stored.get('status')=='completed' else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-head',required=True)
    parser.add_argument('--mode',choices=('prepare','run','worker'),default='run');parser.add_argument('--protocol-sha256')
    args=parser.parse_args()
    def interrupted(signum,frame):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    if args.mode=='prepare':prepare(args.source_head)
    else:
        plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
        if (plan.get('kind')!='hfe-original-native1007-v1' or plan.get('status')!='frozen_for_lead_execution'
                or plan.get('git_head')!=args.source_head):raise p.Rejected('frozen intended prospective source required')
        if args.mode=='worker':
            if args.protocol_sha256!=pin:raise p.Rejected('worker prospective pin differs')
            raise SystemExit(worker(plan,pin))
        raise SystemExit(execute(plan,pin))
