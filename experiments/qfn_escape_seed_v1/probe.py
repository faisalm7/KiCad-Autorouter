"""One frozen exposed-development escape diagnostic; never product admission.

SPDX-License-Identifier: GPL-3.0-or-later
Uses the unchanged installed050 partial Route and shared Native/process/readers.
The partial child's seed exemptions NEVER transfer to the whole-original final.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,json,os,signal,stat,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
RUNTIME=ROOT/'.runs/runtime-directory-050/runtime'
sys.path.insert(0,str(RUNTIME));sys.path.append(str(ROOT));sys.dont_write_bytecode=True
from experiments.qfn_escape_seed_v1 import controls as shared
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as io,sexpr as sx,config as c,local_settings as local
from autorouter.runner import run
from autorouter.default_targets import source_dimensions
from scripts.report_current_comparison import complete_cost

SOURCE_MANIFEST=ROOT/'.runs/runtime045-devobordo-development-source-001.json'
SOURCE_PIN='40254aaf8790681522b2b69a5edae3cbbdc6a2a5b24283d42e76d16c1017ab72'
EXTRA=(*shared.EXTRA,'experiments/qfn_escape_seed_v1/probe.py','scripts/report_current_comparison.py','scripts/freeze_current_comparison.py')
CONTROL=ROOT/'.runs/qfn-escape-controls-native-003/result.json'
ENCLOSED_CONTROL=ROOT/'.runs/qfn-escape-controls-native-003-enclosure/result.json'

def paths(plan,protocol,output):
    preparation=shared.run_path(protocol.parent);output=shared.run_path(output)
    outer=shared.run_path(output.with_name(output.name+'-enclosure'))
    if (protocol!=preparation/'protocol.json' or str(preparation)!=plan['preparation']
            or str(output)!=plan['output'] or str(outer)!=plan['enclosure']
            or len({preparation,output,outer})!=3):raise p.Rejected('exact frozen disjoint escape probe paths required')
    return outer

def fresh(plan):
    shared.current(plan)
    if p.sha(SOURCE_MANIFEST)!=SOURCE_PIN:raise p.Rejected('source rights/hash manifest changed')
    specification=f.read_json(SOURCE_MANIFEST)['families']['devobordo']
    if any(plan[key]!=specification[key] for key in ('source','source_hashes','source_rights','publication')):raise p.Rejected('probe source differs from the sole frozen development entry')
    for name,pin in plan['prerequisites'].items():
        if p.sha(Path(name))!=pin:raise p.Rejected('frozen prerequisite changed')
    control=f.read_json(CONTROL)
    if shared.material(CONTROL.parent)!=control['completed_evidence']:raise p.Rejected('owned Native prerequisite material changed')
    local.check_final_events([(CONTROL.parent/name,dict(steps=row['steps'],native=row.get('native') or {})) for name,row in control['cases'].items()],c.CLI)

def preparation_cost(plan,pin):
    path=Path(plan['preparation_time_log'])
    if p.sha(path)!=pin:raise p.Rejected('complete external preparation timing changed')
    return complete_cost(path)

def prepare(folder,output,head):
    folder=shared.run_path(folder);output=shared.run_path(output);outer=shared.run_path(output.with_name(output.name+'-enclosure'))
    if len({folder,output,outer})!=3 or any(os.path.lexists(path) for path in (folder,output,outer)):raise p.Rejected('fresh disjoint preparation/output/enclosure required')
    if subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True,timeout=5).stdout.strip()!=head:raise p.Rejected('exact checkpoint required')
    subprocess.run(['git','ls-files','--error-unmatch','--',*EXTRA],cwd=ROOT,capture_output=True,text=True,check=True,timeout=5)
    if subprocess.run(['git','diff','--name-only','HEAD','--',*EXTRA],cwd=ROOT,capture_output=True,text=True,check=True,timeout=5).stdout.strip():raise p.Rejected('checkpoint probe implementation first')
    if p.sha(SOURCE_MANIFEST)!=SOURCE_PIN:raise p.Rejected('exact exposed development source required')
    specification=f.read_json(SOURCE_MANIFEST)
    if specification['split']!='development-exposed' or set(specification['families'])!={'devobordo'}:raise p.Rejected('one unchanged exposed development source required')
    source=specification['families']['devobordo'];control=f.read_json(CONTROL);enclosed=f.read_json(ENCLOSED_CONTROL)
    if (not control['passed'] or control['status']!='completed' or control['unattempted']
            or not enclosed['passed'] or enclosed['child_sha256']!=p.sha(CONTROL)
            or control['accepted'] or control['production_admitted'] or control['engine_executed']
            or any(not row['control_passed'] for row in control['cases'].values())):raise p.Rejected('all three completed owned Native controls required')
    preparation=f.read_json(ROOT/'.runs/qfn-escape-controls-preparation-003/protocol.json')
    shared.current(preparation)
    if shared.material(CONTROL.parent)!=control['completed_evidence']:raise p.Rejected('completed control evidence changed')
    plan=dict(schema=1,kind='source-geometry-escape-single-development-probe-v1',administration_head=head,
        preparation=str(folder),output=str(output),enclosure=str(outer),runtime=str(RUNTIME),
        runtime_manifest_sha256=shared.MANIFEST,source=source['source'],source_hashes=source['source_hashes'],
        source_rights=source['source_rights'],publication=source['publication'],tools=p.tool_manifest(),
        code_sha256={name:p.sha(ROOT/name) for name in EXTRA},
        prerequisites={str(path):p.sha(path) for path in (CONTROL,ENCLOSED_CONTROL,ROOT/'evidence/runtime050-devobordo-development-001.json',ROOT/'.runs/qfn-escape-controls-preparation-003/protocol.json')},
        targets=shared.TARGETS,policy=shared.seed.POLICY,
        limits=dict(routing_wall_full_CPU_seconds=420,method_wall_full_CPU_seconds=450,complete_wall_full_CPU_seconds=600,export_seconds_reserved=120,per_outer_Native_step_seconds=30,group_RSS_bytes=4*1024**3,aggregate_output_bytes=100*1024**2),
        population=['one fixed escape initialization; no length/via/neckdown/optimizer variants'],
        accepted=False,production_admitted=False,workflow_delivered=False,
        prospective_decision='One attempt only. Measure whole-original Native opens/blocking/warnings/exclusions and retain failures. No product integration if incomplete or invalid. A clean candidate remains experimental pending unrelated-family/installed-workflow qualification; no automatic rerun or policy selection. Reduction in opens alone is diagnostic, not delivery, superior route quality or electrical suitability.',
        scope='Exposed development diagnostic, not a replacement arm in completed frozen050 cohort or an unattended installed product. Same420 Route allocation/450 complete method cap/600 complete cap; generation, queries, partial Route, selection and independent final validation count. No delivery implementation in this probe; reserved export time is unspent, not a validated export. Existing6arm baselines are reused development evidence, no fresh fair performance/speed/holdout claim.',
        sampled_preparation_costs=dict(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0),
        preparation_time_log=str(folder.with_name(folder.name+'-time.log')),
        preparation_accounting='Stored sample excludes later preflight/publication tail. Run requires exact completed external time-log hash; that complete cost is charged instead. Complete external run exit remains authoritative; nested samples overlap.')
    fresh(plan);p.preflight(Path(plan['source']),task_scope=('whole_board_unlocked_routing','native','source_all'),class_context='native-route-flat-classes-v1')
    folder.mkdir();p.save_json(folder/'protocol.json',plan)
    print(json.dumps(dict(protocol=str(folder/'protocol.json'),sha256=p.sha(folder/'protocol.json'),Native_or_engine_executed=False)))

def actor(protocol,pin,output,preparation_pin):
    plan=f.read_json(protocol);paths(plan,protocol,output)
    if p.sha(protocol)!=pin or plan['targets']!=shared.TARGETS or plan['policy']!=shared.seed.POLICY:raise p.Rejected('exact frozen single hypothesis required')
    fresh(plan);prep=preparation_cost(plan,preparation_pin);p.check_storage(active_root=output);output.mkdir();owner={};h.capture_destination(owner,output)
    source=Path(plan['source']);before=plan['source_hashes'];original=sx.read(source)
    protected=[row for row in p.routes(original) if p.locked(row)]
    def method_left():return min(450-prep['wall_seconds']-(time.monotonic()-START),450-prep['CPU_seconds']-(cpu()-CPU0))
    def remaining():return min(method_left(),598-prep['wall_seconds']-(time.monotonic()-START),598-prep['CPU_seconds']-(cpu()-CPU0))
    def bounded():io.inventory(output,max_bytes=100*1024**2,max_files=2000,max_entries=4000)
    def stage_left():bounded();return remaining()
    record=dict(schema=1,status='failed',passed=False,attempt_qualified=False,accepted=False,production_admitted=False,workflow_delivered=False,
        protocol_sha256=pin,preparation_complete_cost=prep,tools=plan['tools'],source=str(source),source_hashes=before,original_protected_count=len(protected),
        actual_GUI=False,human_review=False,physical_electrical_validation=False,steps=[],
        child_partial_validation_is_not_original_acceptance=True,scope=plan['scope'])
    query=None;validation=None;seed_source=None;seed_hashes=None;child=None;final=None;pre_hashes=None;digest=None;native=None
    def interrupted(*_):raise KeyboardInterrupt('escape probe cancelled')
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared Native lane required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            query=shared.BoundJob(output/'original-target-query',450,stage_left,protect_local_settings=True)
            original_copy=query.out/'original'/source.name;shared.copy_bytes(io.inventory(source.parent,contents=True),original_copy.parent)
            query.native('original-netclasses','netclasses',original_copy,query.out/'original-netclasses.json')
            mapping=f.read_json(query.out/'original-netclasses.json')
            audit=p.audit_candidate_netclasses(original_copy,p.routes(original),mapping,default_target_policy=True)
            targets=source_dimensions(original_copy.with_suffix('.kicad_pro').read_bytes(),mapping)['derived_nm']
            if targets!=plan['targets']:raise p.Rejected('source-derived original targets differ from frozen policy')
            p.save_json(query.out/'target-audit.json',audit)
            task=p.routing_task(original,'whole_board_unlocked_routing')
            seeded,metadata=shared.seed.generate(task,protected,targets)
            if not metadata['generated_count'] or p.immutable(seeded)!=p.immutable(original):raise p.Rejected('no supported seeds or immutable mismatch')
            seed_source=output/'seeded-source'/source.name;shared.copy_bytes(io.inventory(source.parent,contents=True),seed_source.parent);sx.write(seed_source,seeded)
            seed_hashes=io.inventory(seed_source.parent);p.save_json(output/'seed-plan.json',metadata)
            record.update(seed_count=metadata['generated_count'],source_target_query_sha256=p.sha(query.out/'original-netclasses.json'),seed_plan_sha256=p.sha(output/'seed-plan.json'),seeded_source_hashes=seed_hashes)
            fresh(plan)
            if method_left()<420:raise p.Rejected('complete420 allocation unavailable after source-only initialization')
            child=p.route(seed_source,output/'partial-route',seconds=420,keep_existing=True,adapter='both',engine_profile='standard')
            if child.get('status')=='cancelled' or any(step.get('status')=='cancelled' for step in child.get('steps',[])):raise KeyboardInterrupt
            record.update(child_receipt_sha256=p.sha(output/'partial-route/result.json'),child_status=child.get('status'),child_accepted=child.get('accepted'))
            if child.get('status') not in ('routing_accepted','drc_rejected') or child.get('invariants_unchanged') is not True:raise p.Rejected('partial child did not complete a Native candidate: '+str(child.get('reason')))
            p.check_engine_profile_record(child,output/'partial-route')
            if child['accepted']:p.check_result(output/'partial-route/result.json')
            child_candidate=Path(child['candidate'])
            p.verify_candidate_files(child_candidate,seed_hashes,child['candidate_sha256'])
            if p.immutable(sx.read(child_candidate))!=p.immutable(original):raise p.Rejected('partial child changed original geometry')
            validation=shared.BoundJob(output/'whole-original-validation',450,stage_left,protect_local_settings=True)
            final=validation.out/'candidate'/source.name;shared.copy_bytes(io.inventory(source.parent,contents=True),final.parent);final.write_bytes(io.read_bytes(child_candidate))
            pre_hashes=io.inventory(final.parent)
            digest,native=p.validate_candidate(validation,original,final,before,protected,default_target_policy=True,class_context='native-route-flat-classes-v1')
            validation.native('metrics','metrics',final,validation.out/'metrics.json')
            record.update(status='completed_native_diagnostic',passed=True,attempt_qualified=True,
                candidate=str(final),candidate_sha256=digest,native=native,native_report_sha256=p.sha(validation.out/'final-drc.json'),
                original_geometry_and_protected_unchanged=True,Native_routing_scope_passed=p.native_accepted(native),
                metrics=f.read_json(validation.out/'metrics.json'),decision='No integration or rerun. Retain this original-validated diagnostic and compare against the fixed development failures. Any incomplete/invalid result is not delivery; any clean candidate still needs product/independent-family qualification.')
        except (Exception,KeyboardInterrupt) as exc:
            record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',passed=False,attempt_qualified=False,reason=type(exc).__name__+': '+str(exc))
        record['steps']=[step for job in (query,validation) if job is not None for step in job.steps]
        witness=shared.material(output);record['completed_evidence']=witness
        def stable():
            bounded();h.owned_destination(owner);fresh(plan);preparation_cost(plan,preparation_pin)
            if p.sha(protocol)!=pin or shared.material(output)!=witness:raise p.Rejected('frozen/completed probe material changed')
            if seed_source is not None and io.inventory(seed_source.parent)!=seed_hashes:raise p.Rejected('seeded source changed')
            if not record['attempt_qualified']:return
            f.process_check(query.out,{'steps':query.steps},'original-netclasses',[*f.SANDBOX,str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'netclasses',str(original_copy),str(query.out/'original-netclasses.json')])
            if io.inventory(original_copy.parent)!=before:raise p.Rejected('target-query original changed')
            if p.audit_candidate_netclasses(original_copy,p.routes(original),f.read_json(query.out/'original-netclasses.json'),default_target_policy=True)!=f.read_json(query.out/'target-audit.json'):raise p.Rejected('original target audit changed')
            regenerated,meta=shared.seed.generate(p.routing_task(original,'whole_board_unlocked_routing'),protected,plan['targets'])
            if io.read_bytes(seed_source)!=(sx.dump(regenerated)+'\n').encode() or f.canonical(meta)!=f.canonical(f.read_json(output/'seed-plan.json')):raise p.Rejected('seed proposal differs from unchanged original-only policy')
            p.check_engine_profile_record(child,output/'partial-route')
            if p.sha(output/'partial-route/result.json')!=record['child_receipt_sha256']:raise p.Rejected('partial receipt changed')
            p.verify_candidate_files(final,before,digest)
            if p.immutable(sx.read(final))!=p.immutable(original) or any(row not in p.routes(sx.read(final)) for row in protected):raise p.Rejected('whole-original geometry/protection changed')
            f.check_drc_stage(validation.out,{'steps':validation.steps},'refill-drc',validation.out/'refill'/source.name,validation.out/'refill'/source.name,True,pre_hashes)
            observed=f.check_drc_stage(validation.out,{'steps':validation.steps},'final-drc',final,validation.out/'final-drc-input'/source.name,False,{**before,source.name:digest},schematic_parity=True)
            if observed!=native or f.read_json(validation.out/'final-drc-binding.json').get('field_local_settings_policy')!=p.FIELD_LOCAL_SETTINGS_POLICY:raise p.Rejected('whole-original Native/field proof changed')
            for name,action,destination in (('final-netclasses','netclasses',validation.out/'final-netclasses.json'),('metrics','metrics',validation.out/'metrics.json')):
                f.process_check(validation.out,{'steps':validation.steps},name,[*f.SANDBOX,str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),action,str(final),str(destination)])
            audit=p.audit_candidate_netclasses(final,protected,f.read_json(validation.out/'final-netclasses.json'),default_target_policy=True);audit['native_map_file_sha256']=p.sha(validation.out/'final-netclasses.json')
            if audit!=f.read_json(validation.out/'final-netclass-audit.json'):raise p.Rejected('whole-original Default audit changed')
            controls=f.read_json(CONTROL)
            packets=[(CONTROL.parent/name,dict(steps=row['steps'],native=row.get('native') or {})) for name,row in controls['cases'].items()]
            local.check_final_events([*packets,(output/'partial-route',child),(validation.out,dict(steps=validation.steps,native=native))],c.CLI)
        def account():
            bounded();record.update(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
            if remaining()<=0:record.update(status='budget_exceeded',passed=False,attempt_qualified=False)
            if record['status']!='completed_native_diagnostic':record.update(passed=False,attempt_qualified=False)
        f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    result=f.read_json(output/'result.json');print(json.dumps({k:result.get(k) for k in ('status','passed','attempt_qualified','reason','seed_count','wall_seconds','full_CPU_seconds')}));return 0 if result['passed'] and result['attempt_qualified'] else 2

def enclose(protocol,pin,output,preparation_pin):
    plan=f.read_json(protocol);outer=paths(plan,protocol,output);fresh(plan);prep=preparation_cost(plan,preparation_pin)
    if p.sha(protocol)!=pin or os.path.lexists(output) or os.path.lexists(outer):raise p.Rejected('fresh frozen probe required')
    p.check_storage(active_root=outer);outer.mkdir()
    process=run([*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B',str(Path(__file__)),'actor','--protocol',str(protocol),'--sha256',pin,'--preparation-time-sha256',preparation_pin,'--output',str(output)],cwd=outer,log=outer/'command.log',timeout=595,max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=2*1024**2)
    p.save_json(outer/'process.json',process);child=f.read_json(output/'result.json') if (output/'result.json').is_file() else None
    passed=bool(child and child['passed'] and child['attempt_qualified'] and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'] and max(time.monotonic()-START+prep['wall_seconds'],cpu()-CPU0+prep['CPU_seconds'])<=450)
    p.save_json(outer/'result.json',dict(schema=1,passed=passed,accepted=False,production_admitted=False,workflow_delivered=False,protocol_sha256=pin,child_sha256=p.sha(output/'result.json') if child else None,process=process,complete_wall_seconds=time.monotonic()-START,complete_full_CPU_seconds=cpu()-CPU0,preparation_complete_cost=prep,external_complete_exit_required=True,scope=plan['scope']))
    print(json.dumps(dict(passed=passed,enclosure=str(outer))));return 0 if passed else 2

def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('prepare','run','actor'));parser.add_argument('--preparation',type=Path);parser.add_argument('--head');parser.add_argument('--protocol',type=Path);parser.add_argument('--sha256');parser.add_argument('--preparation-time-sha256');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.mode=='prepare':
        if not args.preparation or not args.head:parser.error('preparation and exact head required')
        prepare(args.preparation.absolute(),args.output.absolute(),args.head);return 0
    if not args.protocol or not args.sha256 or not args.preparation_time_sha256:parser.error('exact protocol/hash and completed external preparation timing hash required')
    return actor(args.protocol.absolute(),args.sha256,args.output.absolute(),args.preparation_time_sha256) if args.mode=='actor' else enclose(args.protocol.absolute(),args.sha256,args.output.absolute(),args.preparation_time_sha256)
if __name__=='__main__':raise SystemExit(main())
