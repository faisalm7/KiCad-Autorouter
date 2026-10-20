"""Bounded owned Native prerequisites, never routing/production admission.

SPDX-License-Identifier: GPL-3.0-or-later
Uses the installed050 validator and existing snapshot/process/publication helpers.
No engine is started. Original source and rules remain immutable.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,copy,fcntl,json,os,signal,stat,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
RUNTIME=ROOT/'.runs/runtime-directory-050/runtime'
sys.path.insert(0,str(RUNTIME));sys.path.append(str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as io,sexpr as sx,config as c
from autorouter.runner import run
from experiments.hfe_original_native_v1.driver import BoundJob,material
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.qfn_escape_seed_v1 import fixture,seed

MANIFEST='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
TARGETS=dict(width_nm=200000,clearance_nm=200000,via_diameter_nm=600000,via_drill_nm=300000)
CASES=('positive','outside_short','seed_width_mutation')
EXTRA=('experiments/qfn_escape_seed_v1/__init__.py','experiments/qfn_escape_seed_v1/fixture.py','experiments/qfn_escape_seed_v1/seed.py','experiments/qfn_escape_seed_v1/controls.py','experiments/hfe_original_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py','experiments/native_schematic_transport_v1/fixture.py','autorouter/chain_proposals.py')

def run_path(value):
    path=h.real_path(value,existing=False)
    if path.parent!=ROOT/'.runs' or not path.name.startswith('qfn-escape-'):
        raise p.Rejected('escape diagnostic requires a direct project .runs/qfn-escape-* destination')
    return path

def destinations(plan,protocol,output):
    preparation=run_path(protocol.parent);destination=run_path(output)
    outer=run_path(destination.with_name(destination.name+'-enclosure'))
    if (protocol!=preparation/'protocol.json' or str(preparation)!=plan['preparation']
            or str(destination)!=plan['output'] or str(outer)!=plan['enclosure']
            or Path(plan['source'])!=preparation/'original'/(fixture.STEM+'.kicad_pcb')
            or len({preparation,destination,outer})!=3):
        raise p.Rejected('exact disjoint frozen preparation/output/enclosure required')
    return outer

def current(plan):
    if c.ROOT!=RUNTIME or c.NATIVE_VERSION!='10.0.7' or p.sha(RUNTIME/'runtime-distribution.json')!=MANIFEST:raise p.Rejected('exact installed050 required')
    if p.tool_manifest()!=plan['tools']:raise p.Rejected('installed tools/runtime changed')
    if any(p.sha(ROOT/name)!=pin for name,pin in plan['code_sha256'].items()):raise p.Rejected('frozen control/generator code changed')
    source=Path(plan['source'])
    if io.inventory(source.parent)!=plan['source_hashes']:raise p.Rejected('owned immutable originals changed')

def completed_control(original):
    protected=[r for r in p.routes(original) if p.locked(r)]
    task=p.routing_task(original,'whole_board_unlocked_routing')
    if len(p.routes(original))!=18 or len(protected)!=1 or p.routes(task)!=protected:raise p.Rejected('all17 reference paths must be removed before generation')
    seeded,metadata=seed.generate(task,protected,TARGETS)
    _,resolve=seed.g.source_net_identity(seeded)
    additions=[r for r in p.routes(seeded) if r not in protected]
    if len(additions)!=16 or p.immutable(seeded)!=p.immutable(original):raise p.Rejected('exact16 control stubs and unchanged design required')
    # Only this known-positive witness uses its authored independent anchors.
    # These tails are never supplied to seed.generate or a research solver.
    pins={pin['net']:pin for pin in fixture.pins()};seen=set();finished=copy.deepcopy(seeded)
    for route in additions:
        net=resolve(sx.one(route,'net'));pin=pins[net]
        if net in seen:raise p.Rejected('one control seed per distinct chip net required')
        seen.add(net);x,y=pin['local']
        if sx.one(route,'start')!=['start',fixture.mm(50+x),fixture.mm(50+y)]:
            # Compare exact nanometres: formatting is not a geometric witness.
            from autorouter.chain_proposals import xy
            if xy(sx.one(route,'start'))!=(int((50+x)*1000000),int((50+y)*1000000)):raise p.Rejected('control seed did not start at its pad centre')
        end=sx.one(route,'end');ax,ay=pin['anchor']
        finished.append(['segment',['start',*end[1:]],['end',fixture.mm(ax),fixture.mm(ay)],['width','0.2'],['layer','"F.Cu"'],['net',sx.one(route,'net')[1]],['uuid',fixture.q(fixture.uid('tail-'+pin['number']))]])
    if seen!=set(pins) or p.immutable(finished)!=p.immutable(original):raise p.Rejected('complete controlled pin population changed')
    # Control-only centre connection is copied after proposal, with its source
    # format. It never enters generator selection or the development solver.
    connectors=[r for r in p.routes(original) if sx.unquote(sx.one(r,'uuid')[1])==fixture.uid('center-contact-control')]
    if len(connectors)!=1:raise p.Rejected('one authored control-only centre connector required')
    finished.append(copy.deepcopy(connectors[0]))
    return finished,additions,protected,metadata

def prepare(folder,head,output):
    folder=run_path(folder);output=run_path(output);outer=run_path(output.with_name(output.name+'-enclosure'))
    if len({folder,output,outer})!=3 or any(os.path.lexists(path) for path in (folder,output,outer)):
        raise p.Rejected('three fresh disjoint preparation/output/enclosure paths required')
    observed=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True,timeout=5).stdout.strip()
    if observed!=head:raise p.Rejected('exact administration checkpoint required')
    subprocess.run(['git','ls-files','--error-unmatch','--',*EXTRA],cwd=ROOT,capture_output=True,text=True,check=True,timeout=5)
    if subprocess.run(['git','diff','--name-only','HEAD','--',*EXTRA],cwd=ROOT,capture_output=True,text=True,check=True,timeout=5).stdout.strip():raise p.Rejected('controlled source changes must be checkpointed first')
    if folder.exists() or folder.is_symlink():raise p.Rejected('fresh preparation required')
    folder.mkdir();copy_bytes(fixture.files(),folder/'original');source=folder/'original'/(fixture.STEM+'.kicad_pcb')
    original=p.preflight(source,task_scope=('whole_board_unlocked_routing','native','source_all'),class_context='native-route-flat-classes-v1')
    p.check_schematic_class_support(source,class_context='native-route-flat-classes-v1')
    completed,additions,protected,metadata=completed_control(original)
    p.save_json(folder/'seed-plan.json',metadata)
    plan=dict(schema=1,kind='owned-native-escape-stub-prerequisites-v1',administration_head=head,preparation=str(folder),output=str(output),enclosure=str(outer),runtime=str(RUNTIME),runtime_manifest_sha256=MANIFEST,source=str(source),source_hashes=io.inventory(source.parent),tools=p.tool_manifest(),code_sha256={name:p.sha(ROOT/name) for name in EXTRA},targets=TARGETS,seed_plan_sha256=p.sha(folder/'seed-plan.json'),cases=list(CASES),expected=dict(seed_count=16,original_protected_count=1,positive='0opens/0blocking/0exclusions, allwarnings retained',outside_short='0opens, at leastone error, allerrors clearance/shorting_items/tracks_crossing and containing authored shortUUID',seed_width_mutation='newstubwidth+1nm must fail exact original Default audit after a real refill; no accepted state'),short_uuid=fixture.uid('outside-short'),limits=dict(whole_wall_full_CPU_seconds=120,actor_wall_full_CPU_seconds=105,per_step_seconds=30,log_bytes=256*1024,group_RSS_bytes=2*1024**3,aggregate_output_bytes=32*1024**2),accepted=False,production_admitted=False,engine_executed=False,scope='One positive fullSCH contact witness and two invalids, sequential once; no engine, old-source repair or source/Default/protected relaxation. Roomy owned control is not routing-quality evidence. No automatic retries. Reference copper is removed before proposal; control-only tails establish a positive witness.',preparation_costs=dict(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0))
    current(plan);p.save_json(folder/'protocol.json',plan)
    print(json.dumps(dict(protocol=str(folder/'protocol.json'),sha256=p.sha(folder/'protocol.json'),Native_executed=False)))

def actor(protocol,pin,output):
    plan=f.read_json(protocol)
    if p.sha(protocol)!=pin or plan['cases']!=list(CASES) or plan['targets']!=TARGETS:raise p.Rejected('exact frozen protocol required')
    destinations(plan,protocol,output)
    current(plan);p.check_storage(active_root=output);output.mkdir()
    # capture_destination mutates the supplied witness; keep that exact object.
    owner={};h.capture_destination(owner,output)
    before=plan['source_hashes'];source=Path(plan['source']);original=sx.read(source)
    complete,additions,protected,metadata=completed_control(original)
    if f.canonical(metadata)!=f.canonical(f.read_json(protocol.parent/'seed-plan.json')):raise p.Rejected('deterministic seed plan changed')
    def bounded_output():
        # Shared finite inventory at stage/publication boundaries. Separate
        # Native process groups retain their own runner caps; this is sampled,
        # cooperative resource protection, not a filesystem quota.
        used=0
        for folder in (output,output.with_name(output.name+'-enclosure')):
            if folder.exists():
                used+=sum(map(len,io.inventory(folder,contents=True,max_bytes=32*1024**2-used,max_files=2048,max_entries=4096).values()))
    def remaining():
        return min(105-(time.monotonic()-START),105-(cpu()-CPU0),118-plan['preparation_costs']['wall_seconds']-(time.monotonic()-START),118-plan['preparation_costs']['full_CPU_seconds']-(cpu()-CPU0))
    def stage_remaining():
        bounded_output()
        return remaining()
    record=dict(schema=1,status='failed',passed=False,accepted=False,production_admitted=False,routing_accepted=False,engine_executed=False,protocol_sha256=pin,cases={},unattempted=list(CASES),steps=[],source_hashes=before,tools=plan['tools'])
    replays=[]
    def interrupted(*_):raise KeyboardInterrupt('owned control interrupted')
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared Native lane required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            for case in CASES:
                current(plan);case_tree=copy.deepcopy(complete)
                if case=='outside_short':
                    _,resolve=seed.g.source_net_identity(complete)
                    a,b=sorted(additions,key=lambda r:resolve(sx.one(r,'net')))[:2]
                    case_tree.append(['segment',['start',*sx.one(a,'end')[1:]],['end',*sx.one(b,'end')[1:]],['width','0.2'],['layer','"F.Cu"'],['net',sx.one(a,'net')[1]],['uuid',fixture.q(plan['short_uuid'])]])
                if case=='seed_width_mutation':
                    identity=sx.one(additions[0],'uuid');matches=[r for r in p.routes(case_tree) if sx.one(r,'uuid')==identity]
                    if len(matches)!=1:raise p.Rejected('unique controlled seed mutation required')
                    sx.one(matches[0],'width')[1]='0.200001'
                job=BoundJob(output/case,110,stage_remaining,protect_local_settings=True)
                candidate=job.out/'candidate'/source.name;copy_bytes(io.inventory(source.parent,contents=True),candidate.parent);sx.write(candidate,case_tree)
                pre_hashes=io.inventory(candidate.parent);row=dict(control_passed=False,candidate=str(candidate),steps=job.steps);record['cases'][case]=row;record['unattempted'].remove(case)
                try:
                    digest,native=p.validate_candidate(job,original,candidate,before,protected,default_target_policy=True,class_context='native-route-flat-classes-v1')
                    row.update(candidate_sha256=digest,native=native,source_geometry_unchanged=True,original_protected_count=1)
                    if case=='seed_width_mutation':raise p.Rejected('CRITICAL: changed seed target was not rejected')
                    if case=='positive':
                        if not p.native_accepted(native):raise p.Rejected('owned positive Native acceptance refused')
                    else:
                        errors=[r for r in native['findings'] if r.get('severity')=='error']
                        if native['opens'] or native['exclusions'] or not errors or any(r['type'] not in {'clearance','shorting_items','tracks_crossing'} or plan['short_uuid'] not in {item['uuid'] for item in r['items']} for r in errors):raise p.Rejected('outside short unexpected/missing Native finding')
                        if [r for r in native['findings'] if r.get('severity')!='error']!=[r for r in record['cases']['positive']['native']['findings'] if r.get('severity')!='error']:raise p.Rejected('outside short independently changed nonerror findings')
                    replays.append((job,candidate,pre_hashes,digest,native));row['control_passed']=True
                except p.Rejected as exc:
                    row['reason']=str(exc)
                    if case=='seed_width_mutation' and str(exc).startswith('generated track differs from native netclass target:') and (job.out/'refill-drc.json').is_file() and (job.out/'final-netclasses.json').is_file() and not (job.out/'final-drc.json').exists():
                        row['control_passed']=True;row['rejected_before_final_DRC']=True;row['candidate_sha256']=p.sha(candidate)
                        replays.append((job,candidate,pre_hashes,p.sha(candidate),None))
                if not row['control_passed']:raise p.Rejected(case+' prerequisite refused; later cases unattempted')
            record['status']='completed';record['passed']=True
        except (Exception,KeyboardInterrupt) as exc:
            cancelled=isinstance(exc,KeyboardInterrupt) or any(step.get('status')=='cancelled' for row in record['cases'].values() for step in row['steps'])
            record.update(status='cancelled' if cancelled else 'failed',passed=False,reason=type(exc).__name__+': '+str(exc))
        witness=material(output);record['completed_evidence']=witness
        def stable():
            bounded_output();h.owned_destination(owner);current(plan)
            if p.sha(protocol)!=pin or p.sha(protocol.parent/'seed-plan.json')!=plan['seed_plan_sha256'] or material(output)!=witness:raise p.Rejected('control/protocol/completed material changed')
            for job,candidate,pre_hashes,digest,native in replays:
                p.verify_candidate_files(candidate,before,digest)
                if p.immutable(sx.read(candidate))!=p.immutable(original) or any(r not in p.routes(sx.read(candidate)) for r in protected):raise p.Rejected('original geometry/protected copper changed')
                refill=job.out/'refill'/candidate.name
                f.check_drc_stage(job.out,{'steps':job.steps},'refill-drc',refill,refill,True,pre_hashes)
                f.process_check(job.out,{'steps':job.steps},'final-netclasses',[*f.SANDBOX,str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'netclasses',str(candidate),str(job.out/'final-netclasses.json')])
                if native is not None:
                    if f.read_json(job.out/'final-drc-binding.json').get('field_local_settings_policy')!=p.FIELD_LOCAL_SETTINGS_POLICY:raise p.Rejected('full schematic field guard required')
                    observed=f.check_drc_stage(job.out,{'steps':job.steps},'final-drc',candidate,job.out/'final-drc-input'/candidate.name,False,{**before,candidate.name:digest},schematic_parity=True)
                    if f.canonical(observed)!=f.canonical(native):raise p.Rejected('own final Native readback changed')
                    audit=p.audit_candidate_netclasses(candidate,protected,f.read_json(job.out/'final-netclasses.json'),default_target_policy=True)
                    audit['native_map_file_sha256']=p.sha(job.out/'final-netclasses.json')
                    if (audit['native']['passed'] is not True or audit['route_dimensions']['passed'] is not True or f.canonical(audit)!=f.canonical(f.read_json(job.out/'final-netclass-audit.json'))):raise p.Rejected('original target re-audit refused')
                else:
                    try:p.audit_candidate_netclasses(candidate,protected,f.read_json(job.out/'final-netclasses.json'),default_target_policy=True)
                    except p.Rejected as exc:
                        if not str(exc).startswith('generated track differs from native netclass target:'):raise
                    else:raise p.Rejected('changed seed target no longer refused')
            # Metadata flags are not represented by the byte inventory. Finish
            # all stage/field/material reads before the shared all-root sweep.
            from autorouter import local_settings as local
            local.check_final_events([(job.out,dict(steps=job.steps,native=native or {})) for job,_,_,_,native in replays],c.CLI)
        def account():
            bounded_output()
            record.update(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
            if remaining()<=0:record.update(status='budget_exceeded',passed=False)
            if record['status']!='completed':
                record['passed']=False
                for row in record['cases'].values():row['control_passed']=False
        f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    result=f.read_json(output/'result.json');print(json.dumps({key:result.get(key) for key in ('status','passed','reason','wall_seconds','full_CPU_seconds')}));return 0 if result['status']=='completed' and result['passed'] is True else 2

def enclosed(protocol,pin,output):
    plan=f.read_json(protocol);current(plan)
    outer=destinations(plan,protocol,output)
    if p.sha(protocol)!=pin or output.exists() or output.is_symlink():raise p.Rejected('fresh exact controls required')
    p.check_storage(active_root=outer);outer.mkdir();argv=[*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B',str(Path(__file__)),'actor','--protocol',str(protocol),'--sha256',pin,'--output',str(output)]
    process=run(argv,cwd=outer,log=outer/'command.log',timeout=115,max_log_bytes=512*1024,max_group_rss_bytes=2*1024**3,max_workdir_bytes=32*1024**2);p.save_json(outer/'process.json',process)
    child=f.read_json(output/'result.json') if (output/'result.json').is_file() else None
    passed=bool(child and child['passed'] is True and child['status']=='completed' and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and max(time.monotonic()-START+plan['preparation_costs']['wall_seconds'],cpu()-CPU0+plan['preparation_costs']['full_CPU_seconds'])<=120)
    p.save_json(outer/'result.json',dict(schema=1,passed=passed,accepted=False,production_admitted=False,child_sha256=p.sha(output/'result.json') if child else None,process=process,protocol_sha256=pin,complete_wall_seconds=time.monotonic()-START,complete_full_CPU_seconds=cpu()-CPU0,preparation_costs=plan['preparation_costs'],scope='Owned Native controls only; complete outer/inner output and individual Native worker limits are distinct polling bounds, not hostile-writer containment. No engine/routing-quality/GUI/electrical qualification.'))
    print(json.dumps(dict(passed=passed,outer=str(outer))));return 0 if passed else 2

def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('prepare','run','actor'));parser.add_argument('--preparation',type=Path);parser.add_argument('--head');parser.add_argument('--protocol',type=Path);parser.add_argument('--sha256');parser.add_argument('--output',type=Path);args=parser.parse_args()
    if args.mode=='prepare':
        if not args.preparation or not args.head or not args.output:parser.error('exact preparation/head/output required')
        prepare(args.preparation.absolute(),args.head,args.output.absolute());return 0
    if not args.protocol or not args.sha256 or not args.output:parser.error('exact protocol/hash/output required')
    return actor(args.protocol.absolute(),args.sha256,args.output.absolute()) if args.mode=='actor' else enclosed(args.protocol.absolute(),args.sha256,args.output.absolute())
if __name__=='__main__':raise SystemExit(main())
