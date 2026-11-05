"""Unshipped one-family research worker; never a normal routing receipt.

Run twice only after a reviewed prospective protocol: EEPROM, then STM32.
The retained both cell is replayed, not rerouted. External600s enclosure and
complete exit accounting remain mandatory; this worker is not its supervisor.
"""
from pathlib import Path
import argparse,hashlib,json,os,signal,sys,time
import resource

ENTRY_WALL=time.monotonic()
ENTRY_CPU=time.process_time()+resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime

ROOT=Path(__file__).resolve().parents[2]
RUNTIME=ROOT/'.runs/runtime074 fresh install 001'
MANIFEST='584ee929eaf3d277dc535556e42c71ac5196a74f1c5e3fd53a2cce5a67853d61'
BUILD='6fbbbf22dfb8250f1578fb4d7a45ff0e161b3194'
STUDY=ROOT/'.runs/protected-gap-runtime074-comparison-001'
POPULATION='a04314302bd8b3963750fddb852dea1d6286d252c94a163cdb1f8689f38a9f3e'
CHILDREN='09a49117e6cbac0c5a32c94cdc42cad681ba797aa4427ffc56bbcf61ac62a421'
KIND='protected-default-plane-factor-research-v1'
FAMILIES=('eeprom','stm32')
LIMITS=dict(routing_seconds=420,method_wall_cpu_cap_seconds=450,complete_wall_cpu_cap_seconds=600)


def installed_api():
    # No source-package monkeypatch, mixed ROOT/T modules or Native-version
    # reassignment. Import only the exact qualified installed074 authority.
    if any(name=='autorouter' or name.startswith('autorouter.') for name in sys.modules):
        raise RuntimeError('fresh process without preloaded autorouter required')
    if any(x.is_symlink() for x in (RUNTIME,*RUNTIME.parents)) or not RUNTIME.is_dir():
        raise RuntimeError('exact canonical installed074 runtime required')
    if Path(sys.prefix).absolute()!=RUNTIME/'.venv':
        raise RuntimeError('execute with the exact installed074 .venv interpreter')
    sys.path.insert(0,str(RUNTIME));sys.path.insert(1,str(ROOT));sys.dont_write_bytecode=True
    from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as pc,provenance as pv
    from autorouter import sexpr as sx,config as c,adapter,local_settings
    for name,module in tuple(sys.modules.items()):
        if name=='autorouter' or name.startswith('autorouter.'):
            if RUNTIME/'autorouter' not in Path(module.__file__).absolute().parents:
                raise RuntimeError('mixed installed/module authority')
    if c.ROOT!=RUNTIME or c.NATIVE_VERSION!='10.0.7' or p.sha(RUNTIME/pv.MANIFEST)!=MANIFEST:
        raise RuntimeError('actual installed074 identity differs')
    manifest=f.read_json(RUNTIME/pv.MANIFEST);pins=pv._file_map(manifest['immutable_files_sha256'])
    if len(pins)!=54 or any(p.sha(RUNTIME/name)!=pin for name,pin in pins.items()):
        raise RuntimeError('installed074 curated54 changed')
    return p,f,h,pc,pv,sx,adapter,local_settings,pins


def experiment(protocol_name,protocol_pin,family):
    p,f,h,pc,pv,sx,adapter,local_settings,runtime_pins=installed_api()
    from experiments.protected_plane_factor_v1 import factor
    if Path(factor.__file__).resolve()!=Path(__file__).resolve().with_name('factor.py'):
        raise RuntimeError('research factor module path differs')
    transform=factor.transform
    from scripts.backup import require_headroom
    start=ENTRY_WALL;cpu0=ENTRY_CPU
    remaining=lambda:max(0,min(420-(time.monotonic()-start),420-(h.cpu_seconds()-cpu0)))
    need=lambda ok,message:None if ok else (_ for _ in ()).throw(p.Rejected(message))
    protocol=h.real_path(protocol_name);need(protocol.parent==ROOT/'.runs','protocol must be an exact .runs-root file')
    raw=pc.read_bytes(protocol,1024**2);need(hashlib.sha256(raw).hexdigest()==protocol_pin,'prospective protocol pin differs')
    spec=json.loads(raw)
    need(set(spec)=={'schema','kind','administration_head','driver_sha256','factor_sha256','limits','family_order','families'}
        and type(spec['schema']) is int and spec['schema']==1 and spec['kind']==KIND
        and spec['family_order']==list(FAMILIES) and spec['limits']==LIMITS
        and all(type(v) is int for v in spec['limits'].values()) and family in FAMILIES
        and type(spec['families']) is dict and set(spec['families'])==set(FAMILIES),'exact frozen two-family protocol required')
    for row in spec['families'].values():
        need(set(row)=={'output','prior_child_sha256','prior_route_sha256'},'exact family authority row required')
    def code_current():
        need(pv._git(ROOT,'rev-parse','HEAD').decode().strip()==spec['administration_head'],'research HEAD changed')
        for name,key in [('driver.py','driver_sha256'),('factor.py','factor_sha256')]:
            path=Path(__file__).with_name(name);rel=path.relative_to(ROOT).as_posix();data=pc.read_bytes(path)
            need(hashlib.sha256(data).hexdigest()==spec[key] and pv._git(ROOT,'show',spec['administration_head']+':'+rel)==data,'commit exact reviewed research source before Native')
        need(p.sha(protocol)==protocol_pin and all(p.sha(RUNTIME/n)==v for n,v in runtime_pins.items()),'protocol/runtime changed')
    code_current();need(p.sha(STUDY/'population.json')==POPULATION and p.sha(STUDY/'frozen-children.json')==CHILDREN,'frozen comparison authority changed')
    population=f.read_json(STUDY/'population.json');item=f.read_json(STUDY/'frozen-children.json')['protocols'][family]['Cdefault']
    old_protocol=h.real_path(item['path']);need(p.sha(old_protocol)==item['sha256'],'captured Default protocol changed');plan=f.read_json(old_protocol)
    old_child=Path(plan['output'])/'result.json';need(p.sha(old_child)==spec['families'][family]['prior_child_sha256'],'captured Default child changed')
    child=f.read_json(old_child);prior=h.real_path(child['selected_route_receipt'])
    need(prior.name=='result.json' and p.sha(prior)==child['selected_route_sha256']==spec['families'][family]['prior_route_sha256'],'captured Default route changed')
    old=f.read_json(prior);source=h.real_path(plan['source']);hashes=plan['source_hashes']
    need(plan['source_head']==BUILD and plan['runtime']==str(RUNTIME) and plan['runtime_manifest_sha256']==MANIFEST
        and plan['default_settings']==dict(schema=1,seconds=420,adapter='both',guidance='native',layers='source_all',profile='standard',scope='whole_board_unlocked_routing',scoring_preference=None)
        and old['source']==str(source) and old['source_hashes']==hashes and old['scope']=='whole_board_unlocked_routing'
        and old['engine_profile']=='standard' and old['adapter']=='both','captured Default scope differs')
    replay=lambda:p.check_result(prior) if old['accepted'] is True else p.check_rejected_routing_attempt(prior,ordinary_profile='standard')
    replay();original=p.preflight(source,task_scope=('whole_board_unlocked_routing','native','source_all'))
    need(p.netclass_policy(source) is None and old['source_drc']['blocking']==old['source_drc']['exclusions']==0,'sole Default and valid original source required')
    task=p.routing_task(original,'whole_board_unlocked_routing');task_raw=(sx.dump(task)+'\n').encode();protected=p.routes(task)
    need(hashlib.sha256(task_raw).hexdigest()==old['task_sha256'],'captured exact task hash differs')
    olddir=prior.parent;prior_inventory=pc.evidence_inventory(olddir)
    edge_context=p.native_edge_context(source,known_named=p.named_edge_scope(olddir,old))
    graphics,derivation=transform(pc.read_bytes(olddir/'native.dsn'),f.read_json(olddir/'export-netclasses.json'),pc.read_bytes(source.with_suffix('.kicad_pro')),task_raw,
        export_source=str(olddir/'candidate'/source.name),captured_default=pc.read_bytes(olddir/'default-targets.dsn'),captured_derivation=f.read_json(olddir/'default-targets.json'),
        obstacles=f.read_json(olddir/'obstacles.json'),edge_context=edge_context,captured_both_before_edge=pc.read_bytes(olddir/'edge-adapter-input.dsn'),
        captured_both=pc.read_bytes(olddir/'task.dsn'),captured_both_edge=f.read_json(olddir/'native-edge-correction.json'))
    output=h.real_path(spec['families'][family]['output'],existing=False)
    need(output.parent==ROOT/'.runs' and output.name.startswith('protected-plane-factor074-') and not os.path.lexists(output)
        and source.parent not in output.parents and output not in source.parents,'fresh exact research namespace required')
    ordered=None
    if family=='stm32':
        ordered=h.real_path(spec['families']['eeprom']['output'])/'result.json';first=f.read_json(ordered)
        need(first.get('kind')==KIND and first.get('family')=='eeprom' and first.get('protocol_sha256')==protocol_pin
            and first.get('status') in ('completed','failed','cancelled','invalidated') and first.get('cleanup_complete') is True,'EEPROM must finish and clean up first')
    ordered_pin=None if ordered is None else p.sha(ordered)
    require_headroom(output.parent,8*sum(len(v) for v in pc.inventory(source.parent,contents=True).values())+16*1024**2,'one protected-plane factor family')
    p.check_storage(active_root=output);output.mkdir();owner={};h.capture_destination(owner,output);tools=p.tool_manifest();job=None;prefill=None;final_hash=None
    rec=dict(schema=1,kind=KIND,family=family,status='running',protocol_sha256=protocol_pin,accepted=False,production_admitted=False,product_scope_admitted=False,
        factor_completed=False,candidate_native_valid=False,cleanup_complete=True,limits=LIMITS,prior_route=str(prior),prior_route_sha256=p.sha(prior),
        prior_child_sha256=p.sha(old_child),prior_complete_time_log=str(old_protocol.parent/'outer-time.log'),
        prior_complete_time_log_sha256=p.sha(old_protocol.parent/'outer-time.log'),source=str(source),source_hashes=hashes,tools=tools,factor=derivation,
        accounting_caveat='Diagnostic reuses captured both exports and its old routing result. New complete external cost includes current replay/conversion/engine/import/Native/publication; historical acquisition/routing costs remain separate. This is not a fresh equal-budget product comparison or delivery.')
    def stable():
        h.owned_destination(owner);code_current();need(remaining()>0,'420wall/fullCPU factor budget exhausted')
        need(p.tool_manifest()==tools and p.tree_hash(source.parent)==hashes and pc.evidence_inventory(olddir)==prior_inventory,'original/runtime/captured prior evidence changed')
        need(p.sha(old_child)==spec['families'][family]['prior_child_sha256'] and (ordered is None or p.sha(ordered)==ordered_pin),'retained child/order witness changed')
        pc.evidence_inventory(output)
        if job is not None:
            task_hashes=dict(hashes);task_hashes[source.name]=hashlib.sha256(task_raw).hexdigest()
            need(p.tree_hash(job.out/'snapshot')==hashes and p.tree_hash(job.out/'task-input')==task_hashes,'research source/task snapshot changed')
            need(pc.read_bytes(job.out/'task.dsn')==graphics,'new exact engine task changed')
    def readback():
        stable()
        if final_hash is None:return
        candidate=job.out/'candidate'/source.name;saved=job.out/'refill'/source.name;data=dict(steps=job.steps)
        before=dict(hashes);before[source.name]=hashlib.sha256((sx.dump(prefill)+'\n').encode()).hexdigest()
        f.check_drc_stage(job.out,data,'refill-drc',saved,saved,True,before)
        after=dict(hashes);after[source.name]=final_hash
        native=f.check_drc_stage(job.out,data,'final-drc',candidate,job.out/'final-drc-input'/source.name,False,after,schematic_parity=True)
        need(native==rec['native'] and p.sha(job.out/'final-drc.json')==rec['native_report_sha256'],'own final Native/hash changed')
        need(pc.read_bytes(candidate)==(sx.dump(p.transplant_fill(prefill,sx.read(saved)))+'\n').encode(),'actual import/refill reconstruction differs')
        p.verify_candidate_files(candidate,hashes,final_hash);need(p.immutable(sx.read(candidate))==p.immutable(original),'original fixed placement/rules changed')
        p.check_legacy_zone_evidence(job.out,original,candidate,implementation=tools['implementation_sha256'])
        policy=p.normal_strict_import_policy(original,protected)
        p.check_protected_import(job.out,rec,task,candidate,protected,**({'strict_expected_policy':policy} if policy==p.PROTECTED_VIA_IMPORT_POLICY else {}))
        p.check_final_netclass_evidence(job.out,data,candidate,protected,default_target_policy=True,sandboxed=True,default_target_basis=derivation['default_target_derivation'])
        f.process_check(job.out,data,'import',[*f.SANDBOX,*p.native_prefix(),'import',str(job.out/'task-input'/source.name),str(job.out/'imported.kicad_pcb'),str(job.out/'routes.ses'),'--task-copper-fixed'])
        f.process_check(job.out,data,'engine',p.engine_argv(job.out,rec['engine_budget']['argv'],profile='standard'))
        need(p.immutable(sx.read(job.out/'imported.kicad_pcb'))==p.immutable(sx.read(olddir/'imported.kicad_pcb')),'Native fixed task shell changed')
        p.check_engine_profile_record(dict(rec,steps=job.steps),job.out)
        imports=local_settings.check_normal_policy(job.out,dict(rec,steps=job.steps),max_bytes=100*1024**2,max_files=4000)
        need(imports==[dict(cwd=str(job.out),name='import',source=str(job.out/'task-input'/source.name),
            output=str(job.out/'imported.kicad_pcb'),session=str(job.out/'routes.ses'))],'own exact fixed-placement import census differs')
        # The generic same-job normal import reader cannot consume a reused
        # export. Never fabricate a new export row: replay the actual old whole
        # body and exact old fixed-copper export, then bind its task to our
        # unchanged new task-input and the exact new fixed-copper import above.
        f.process_check(olddir,old,'export',[*p.native_prefix(),'export',str(olddir/'candidate'/source.name),
            str(olddir/'task.dsn'),str(olddir/'export-netclasses.json'),'--task-copper-fixed'])
        need(p.sha(job.out/'task-input'/source.name)==old['task_sha256'],'reused fixed export/new import task differs')
        replay();stable()
    def account():
        rec.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=h.cpu_seconds()-cpu0,within_budget=remaining()>0,steps=[] if job is None else job.steps,
            cleanup_complete=job is None or all(s.get('cleanup_complete') is True for s in job.steps),accepted=False,production_admitted=False,product_scope_admitted=False)
        if rec['status']!='completed' or not rec['within_budget']:rec.update(factor_completed=False,candidate_native_valid=False)
    try:
        job=f.FloorJob(output/'route',420,remaining,protect_local_settings=True)
        for name in ('snapshot','candidate','task-input'):pc.copy_project(source.parent,job.out/name)
        candidate=job.out/'candidate'/source.name;task_input=job.out/'task-input'/source.name
        sx.write(candidate,task);sx.write(task_input,task)
        (job.out/'code').mkdir()
        for name,pin in tools['implementation_sha256'].items():
            data=pc.read_bytes(RUNTIME/name);need(hashlib.sha256(data).hexdigest()==pin,'captured installed code changed');(job.out/'code'/Path(name).name).write_bytes(data)
        (job.out/'task.dsn').write_bytes(graphics);(job.out/'default-targets.json').write_text(json.dumps(derivation['default_target_derivation'],sort_keys=True)+'\n');(job.out/'engine-config').mkdir()
        budget=p.engine_profile_settings('standard',remaining(),strict_class_targets=True)
        need(budget['argv']==old['engine_budget']['argv'],'exact captured strict engine flags cannot fit remaining budget')
        budget.update(outer_task_wall_budget_seconds=420,outer_task_cpu_budget_seconds=420)
        rec.update(engine_budget=budget,engine_profile='standard',adapter='graphics',scope='whole_board_unlocked_routing',budget_seconds=420,cpu_budget_seconds=420,
            default_target_transport=dict(policy=p.DEFAULT_TARGET_ADMISSION_POLICY,file='default-targets.json',sha256=p.sha(job.out/'default-targets.json')))
        width=p.minimum_width_guard(source,'graphics')
        if width is not None:rec['minimum_width_guard']=width
        stable();job.step('engine',p.engine_argv(job.out,budget['argv'],profile='standard'),already_sandboxed=True)
        job.native('import','import',task_input,job.out/'imported.kicad_pcb',job.out/'routes.ses','--task-copper-fixed')
        audit={};prefill=p.transplant_routes(task,sx.read(job.out/'imported.kicad_pcb'),protected=protected,audit=audit,policy=p.normal_strict_import_policy(original,protected))
        sx.write(candidate,prefill);rec['protected_route_import']=dict(imported_sha256=p.sha(job.out/'imported.kicad_pcb'),**audit)
        final_hash,native=p.validate_candidate(job,original,candidate,hashes,protected,schematic_parity=True,default_target_policy=True)
        rec.update(candidate=str(candidate),candidate_sha256=final_hash,native=native,native_report_sha256=p.sha(job.out/'final-drc.json'),
            status='completed',factor_completed=True,candidate_native_valid=p.native_accepted(native),native_rejection_reasons=p.native_rejection_reasons(native))
        readback()
    except (Exception,KeyboardInterrupt) as exc:
        rec.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc),factor_completed=False,candidate_native_valid=False)
    return f.publish(output,rec,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=readback)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True)
    parser.add_argument('--family',choices=FAMILIES,required=True);parser.add_argument('--run-native',action='store_true');args=parser.parse_args()
    if not args.run_native:parser.error('explicit reviewed --run-native required; draft is not qualified by its existence')
    def stop(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
    result=experiment(args.protocol,args.protocol_sha256,args.family)
    print(json.dumps({key:result.get(key) for key in ('status','family','factor_completed','candidate_native_valid','error','wall_seconds','total_cpu_seconds')},sort_keys=True))
    raise SystemExit(0 if result['factor_completed'] else 2)
