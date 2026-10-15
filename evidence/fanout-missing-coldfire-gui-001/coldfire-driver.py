"""Prospective default1000 ColdFire original-only diagnostic; never routing admission.
SPDX-License-Identifier: GPL-3.0-or-later
Exit0/passed mean completed retained observation, including observed Native rejection.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,hashlib,importlib.util,json,math,os,signal,stat,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,local_settings as ls,placement_clearance as io
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as shared
from experiments.placement_handoff_native_v1.driver import copy_bytes
OBS_PATH=Path(__file__).with_name('observation.py');BINDING=Path(__file__).with_name('SOURCE_BINDING.json')
spec=importlib.util.spec_from_file_location('coldfire_native1000_observation',OBS_PATH)
observation=importlib.util.module_from_spec(spec);spec.loader.exec_module(observation)
KIND='coldfire-original-native1000-v1'
PREP=ROOT/'.runs/coldfire-original-native1000-preparation-001';PROTOCOL=PREP/'protocol.json'
OUTER=ROOT/'.runs/coldfire-original-native1000-execution-001';CHILD=OUTER/'native'
LIMITS=dict(whole_wall_full_cpu_seconds=120,worker_wall_full_cpu_seconds=90,native_worker_seconds=30,
    scratch_bytes=128*1024**2,group_rss_bytes=2*1024**3,log_bytes=256*1024,publication_allowance_seconds=2)
CONFIG=(p.c.CLI,p.c.PYTHON,p.c.PCBNEW,p.c.JAR,p.c.JAVA)


def source():return observation.capture()


def current(plan,pin=None):
    shared.clean(plan['git_head']);binding,files=source()
    if (plan.get('kind')!=KIND or plan.get('status')!='frozen_for_lead_execution' or plan.get('limits')!=LIMITS
            or plan.get('native_version')!='10.0.0' or plan.get('native_toolchain') is not None
            or plan.get('experimental_schematic_parity') is not False or plan.get('accepted') is not False
            or plan.get('production_support_qualified') is not False or plan.get('routing_executed') is not False
            or plan.get('source_binding')!=binding or plan.get('output')!=str(OUTER)
            or plan.get('controller_source')!=str(Path(__file__).resolve())):
        raise p.Rejected('fixed original-only default1000 scope differs')
    if CONFIG!=(p.c.CLI,p.c.PYTHON,p.c.PCBNEW,p.c.JAR,p.c.JAVA) or p.tool_manifest()!=plan['tools']:
        raise p.Rejected('current default tool/code/HEAD differs')
    if any(p.sha(ROOT/name)!=digest for name,digest in plan['code_sha256'].items()):raise p.Rejected('frozen diagnostic/helper bytes differ')
    if pin is not None and (p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan)):
        raise p.Rejected('frozen prospective protocol changed')
    return binding,files


def prepare(head):
    shared.clean(head);binding,files=source();tools=p.tool_manifest()
    if tools['git_head']!=head:raise p.Rejected('exact intended clean future HEAD required')
    refusal=None
    try:p.preflight(ROOT/binding['source_relative']/(binding['stem']+'.kicad_pcb'))
    except p.Rejected as exc:refusal=str(exc)
    if not refusal:raise p.Rejected('original static refusal absent; inspect changed scope before Native')
    names=set(tools['implementation_sha256'])|{str(x.resolve().relative_to(ROOT)) for x in (Path(__file__),OBS_PATH,BINDING)}|{
        'data/fetch.py','data/sources.json','experiments/hfe_original_native_v1/driver.py',
        'experiments/original_project_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py'}
    plan=dict(schema=1,kind=KIND,status='frozen_for_lead_execution',git_head=head,tools=tools,
        native_version='10.0.0',native_toolchain=None,experimental_schematic_parity=False,
        accepted=False,production_support_qualified=False,routing_executed=False,source_binding=binding,
        static_supported=False,static_refusal=refusal,output=str(OUTER),controller_source=str(Path(__file__).resolve()),
        code_sha256={name:p.sha(ROOT/name) for name in sorted(names)},limits=LIMITS,
        scope='ONLY untouched ColdFire original saved refill then exact all3188route original shell fullSCH Native1000. Source52/rules/thermalwarning/PRL/4Cuformat/hierarchy unwaived. No engine/export/metrics/routing, source repair/admission/gain/physical claim. passed+exit0 mean completed diagnostic, NOT Native acceptance.')
    PREP.mkdir();current(plan)
    plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
    if max(plan['preparation_costs']['wall_seconds'],plan['preparation_costs']['full_cpu_seconds'])+2>=28:
        raise p.Rejected('prospective preparation leaves insufficient unchanged whole margin')
    p.save_json(PROTOCOL,plan);print(f.canonical(dict(prepared=True,protocol=str(PROTOCOL),sha256=p.sha(PROTOCOL),native_executed=False)))


def worker(plan,pin):
    current(plan,pin)
    if CHILD.exists() or CHILD.is_symlink():raise p.Rejected('fresh owned child required')
    CHILD.mkdir();owner={};h.capture_destination(owner,CHILD)
    def remaining():return min(88-(time.monotonic()-START),88-(cpu()-CPU0))
    job=shared.BoundJob(CHILD/'job',90,remaining,native_toolchain=None,protect_local_settings=True,experimental_schematic_parity=False)
    names=plan['tools']['implementation_sha256']
    code={Path(name).name:io.read_bytes(ROOT/name,1024**2) for name in names}
    if len(code)!=len(names):raise p.Rejected('ambiguous implementation basenames')
    copy_bytes(code,job.out/'code')
    captured={name:io.read_bytes(ROOT/name,1024**2) for name in plan['code_sha256'] if name!='data/sources.json'}
    captured['data/sources.json']=io.read_bytes(ROOT/'data/sources.json',8*1024**2)
    captured['prospective-protocol.json']=io.read_bytes(PROTOCOL,1024**2);copy_bytes(captured,CHILD/'control-code')
    record,check_stages=observation.observe(job,plan['tools'])
    record.update(kind=KIND,git_head=plan['git_head'],protocol_sha256=pin,static_supported=False,static_refusal=plan['static_refusal'],scope=plan['scope'])
    completed=shared.material(CHILD);record['completed_evidence']=completed
    def stable():
        h.owned_destination(owner);current(plan,pin)
        if shared.material(CHILD)!=completed:raise p.Rejected('completed child material changed')
        check_stages()  # Shared exact two-stage reader; final operation rechecks actual PRL metadata.
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
        if remaining()<=0 and record['status']!='cancelled':record['status']='budget_exceeded'
        record['passed']=bool(record['passed'] and record['observation_complete'] and record['status']=='completed' and remaining()>0)
        record.update(accepted=False,production_support_qualified=False,routing_executed=False)
        if record['status']!='completed':record['native_routing_scope_accepted']=False
    f.publish(CHILD,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    stored=f.read_json(CHILD/'result.json')
    if f.canonical(stored)!=f.canonical(record):raise p.Rejected('published child literal differs')
    print(f.canonical({k:stored.get(k) for k in ('passed','status','observation_complete','native_routing_scope_accepted','wall_seconds','full_cpu_seconds')}))
    return 0 if stored.get('passed') is True and stored.get('status')=='completed' else 130 if stored.get('status')=='cancelled' else 2


def read_child(plan,pin,expected_pin=None,expected_literal=None):
    current(plan,pin);path=CHILD/'result.json';digest=p.sha(path);record=f.read_json(path);literal=f.canonical(record)
    if expected_pin is not None and digest!=expected_pin or expected_literal is not None and literal!=expected_literal:raise p.Rejected('captured child literal/hash changed')
    witness=shared.material(CHILD)
    if (max(record['wall_seconds'],record['full_cpu_seconds'])+2>90
            or record.get('publication_allowance_seconds')!=2):raise p.Rejected('child whole observed costs differ')
    if (record.get('kind')!=KIND or record.get('git_head')!=plan['git_head'] or record.get('protocol_sha256')!=pin
            or record.get('passed') is not True or record.get('status')!='completed' or record.get('observation_complete') is not True
            or record.get('static_refusal')!=plan['static_refusal'] or record.get('completed_evidence')!=witness):
        raise p.Rejected('completed original observation unavailable')
    observation.read_observation(CHILD/'job',record,plan['tools'])
    current(plan,pin)
    if p.sha(path)!=digest or f.canonical(f.read_json(path))!=literal or shared.material(CHILD)!=witness:raise p.Rejected('completed child bytes changed during pure reader')
    ls.check_normal_policy(CHILD/'job',record,max_bytes=LIMITS['scratch_bytes'],max_files=2048)
    return record


def execute(plan,pin):
    current(plan,pin);OUTER.mkdir();owner={};h.capture_destination(owner,OUTER)
    costs=plan['preparation_costs']
    if (costs.get('publication_allowance_seconds')!=2 or any(type(costs.get(k))not in (int,float) or not math.isfinite(costs[k]) or costs[k]<0 for k in ('wall_seconds','full_cpu_seconds'))):raise p.Rejected('finite actual preparation costs required')
    prepwall,prepcpu=costs['wall_seconds']+2,costs['full_cpu_seconds']+2
    def remaining():return min(118-prepwall-(time.monotonic()-START),118-prepcpu-(cpu()-CPU0))
    env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}}
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',LANG='C',LC_ALL='C')
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary existing shared lane required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--mode','worker','--source-head',plan['git_head'],'--protocol-sha256',pin]
        process=run(argv,cwd=OUTER,env=env,log=OUTER/'command.log',timeout=max(.001,min(90,remaining())),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=2*1024**3)
        path=CHILD/'result.json';childpin=p.sha(path) if path.is_file() else None;child=f.read_json(path) if childpin else None;literal=f.canonical(child)
        bound=bool(child and shared.material(CHILD)==child.get('completed_evidence') and p.sha(path)==childpin and f.canonical(f.read_json(path))==literal)
        # Capture the enclosing witness only after verifying the child's own prepublication witness/literal.
        witness=shared.material(OUTER);logpin=p.sha(OUTER/'command.log')
        passed=bool(bound and child.get('passed') is True and child.get('status')=='completed' and child.get('observation_complete') is True
            and child.get('accepted') is False and child.get('production_support_qualified') is False and child.get('routing_executed') is False
            and child.get('tools')==plan['tools'] and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
        record=dict(schema=1,kind=KIND+'-enclosure',accepted=False,passed=passed,status='completed' if passed else 'cancelled' if process['status']=='cancelled' or child and child.get('status')=='cancelled' else 'failed',
            production_support_qualified=False,routing_executed=False,observation_complete=bool(child and child.get('observation_complete')),
            native_routing_scope_accepted=bool(passed and child.get('native_routing_scope_accepted')),git_head=plan['git_head'],tools=plan['tools'],protocol_sha256=pin,
            controller_sha256=p.sha(Path(__file__)),process=process,child_receipt_sha256=childpin,child_literal=literal,child_material_bound=bound,
            completed_evidence=witness,log_sha256=logpin,preparation_costs=costs,limits=LIMITS,scope=plan['scope'])
        def stable():
            h.owned_destination(owner);current(plan,pin)
            if shared.material(OUTER)!=witness or p.sha(OUTER/'command.log')!=logpin:raise p.Rejected('enclosing complete material changed')
            if child is not None and (not bound or p.sha(path)!=childpin or f.canonical(f.read_json(path))!=literal or shared.material(CHILD)!=child['completed_evidence']):raise p.Rejected('child prepublication witness/literal changed')
            if record['passed']:read_child(plan,pin,childpin,literal)
        def account():
            record.update(invocation_wall_seconds=time.monotonic()-START,invocation_full_cpu_seconds=cpu()-CPU0,
                wall_seconds=prepwall+time.monotonic()-START,full_cpu_seconds=prepcpu+cpu()-CPU0,publication_allowance_seconds=2,
                cost_scope='Actual self+reaped child through prepublication sample, includes preparation+2; final guarded wall/fullCPU<118+2within120. External process-exit timing remains separate.')
            if remaining()<=0 and record['status']!='cancelled':record['status']='budget_exceeded'
            record['passed']=bool(passed and record['status']=='completed' and remaining()>0)
            if not record['passed']:record['native_routing_scope_accepted']=False
        f.publish(OUTER,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
        stored=f.read_json(OUTER/'result.json');print(f.canonical({k:stored.get(k) for k in ('passed','status','observation_complete','native_routing_scope_accepted','wall_seconds','full_cpu_seconds')}))
        return 0 if stored.get('passed') is True and stored.get('status')=='completed' else 130 if stored.get('status')=='cancelled' else 2


def read(plan,pin):
    current(plan,pin);outer=f.read_json(OUTER/'result.json');outerpin=p.sha(OUTER/'result.json');literal=f.canonical(outer)
    if (outer.get('kind')!=KIND+'-enclosure' or outer.get('passed') is not True or outer.get('status')!='completed'
            or outer.get('accepted') is not False or outer.get('production_support_qualified') is not False or outer.get('routing_executed') is not False
            or outer.get('controller_sha256')!=p.sha(Path(__file__)) or outer.get('limits')!=LIMITS
            or outer.get('protocol_sha256')!=pin or outer.get('git_head')!=plan['git_head'] or outer.get('tools')!=plan['tools']
            or outer.get('completed_evidence')!=shared.material(OUTER) or outer.get('child_material_bound') is not True):raise p.Rejected('completed enclosing observation unavailable')
    process=outer['process'];expected=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--mode','worker','--source-head',plan['git_head'],'--protocol-sha256',pin]
    if (process['argv']!=expected or process['cwd']!=str(OUTER) or process['status']!='success' or process['exit_code']!=0 or process['cleanup_complete'] is not True or process['log_truncated'] is not False
            or process['log_bytes']!=(OUTER/'command.log').stat().st_size or process['resource_guards']['max_group_rss_bytes']!=2*1024**3 or process['resource_guards']['max_workdir_bytes']!=128*1024**2
            or p.sha(OUTER/'command.log')!=outer['log_sha256'] or max(outer['wall_seconds'],outer['full_cpu_seconds'])+2>120):raise p.Rejected('complete original worker/cost proof differs')
    child=read_child(plan,pin,outer['child_receipt_sha256'],outer['child_literal'])
    if outer.get('observation_complete') is not True:raise p.Rejected('outer observation incomplete')
    if outer['native_routing_scope_accepted'] is not child['native_routing_scope_accepted']:raise p.Rejected('observed Native outcome differs')
    current(plan,pin)
    if p.sha(OUTER/'result.json')!=outerpin or f.canonical(f.read_json(OUTER/'result.json'))!=literal or shared.material(OUTER)!=outer['completed_evidence']:raise p.Rejected('retained enclosing material changed late')
    ls.check_normal_policy(CHILD/'job',child,max_bytes=LIMITS['scratch_bytes'],max_files=2048)
    wall,full=time.monotonic()-START,cpu()-CPU0
    if max(wall,full)+2>120:raise p.Rejected('pure original reader whole wall/fullCPU exceeded120')
    print(f.canonical(dict(current=True,new_native_execution=False,observation_complete=True,native_routing_scope_accepted=child['native_routing_scope_accepted'],accepted=False,production_support_qualified=False,sampled_wall_seconds=wall,sampled_full_cpu_seconds=full,publication_allowance_seconds=2,cost_scope='Separate pure read command, not free Native retry; external process-exit timing required.')))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-head',required=True);parser.add_argument('--mode',choices=('prepare','run','worker','read'),required=True);parser.add_argument('--protocol-sha256');args=parser.parse_args()
    def interrupted(*_):raise KeyboardInterrupt
    handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        for sig in handlers:signal.signal(sig,interrupted)
        if args.mode=='prepare':prepare(args.source_head)
        else:
            plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
            if args.source_head!=plan['git_head'] or args.protocol_sha256!=pin:raise p.Rejected('exact frozen source/protocol pin required')
            if args.mode=='read':read(plan,pin)
            else:raise SystemExit(worker(plan,pin) if args.mode=='worker' else execute(plan,pin))
    finally:
        for sig,handler in handlers.items():signal.signal(sig,handler)
