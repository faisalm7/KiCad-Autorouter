"""One prospectively frozen Roller generated-route diagnostic; never admission."""
from pathlib import Path
import argparse,copy,hashlib,json,math,shutil,signal,sys,time
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io,handoff as h,sexpr as sx,adapter,local_settings,native_edge,netclass as nc,pour_rule_area as pour
from autorouter.runner import run
from experiments.pic_mixed_transport_probe_v1 import ses_native as sn
from experiments.roller_export_alias_v1 import padless_alias as alias
from experiments.roller_support_v1 import checks
from experiments.roller_generated_route_v1 import transport
SECONDS=120;BOOT=2;LIMIT=64*1024**2;RSS=4*1024**3
SOURCE=ROOT/'.data/corpus-expansion-audit-001/sparkfun__SparkFun_Roller_Encoder_Breakout'
NAME='SparkFun_Roller_Encoder_Breakout.kicad_pcb'
WORKER=ROOT/'experiments/roller_export_alias_v1/worker.py'
OLD=ROOT/'.runs/roller-export-alias-native-003'
CODE_REQUIRED={str((HERE/n).relative_to(ROOT)) for n in ('driver.py','transport.py')}|{
    'experiments/roller_export_alias_v1/worker.py','experiments/roller_export_alias_v1/padless_alias.py',
    'experiments/roller_support_v1/worker.py','experiments/roller_support_v1/checks.py',
    'experiments/pic_mixed_transport_probe_v1/ses_native.py','experiments/pic_mixed_transport_probe_v1/ses_checks.py'}
REQUIRED={'.runs/roller-semantics-native-001','.runs/roller-no-export-continuation-001','.runs/roller-export-alias-native-002','.runs/roller-export-alias-native-003'}

def need(ok,message):
    if not ok:raise p.Rejected(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def encoded(tree):return (sx.dump(tree)+'\n').encode()
def inventory(path):return io.inventory(path,max_bytes=LIMIT,max_files=10000,max_entries=20000)
def witness(path):
    files,dirs=io.inventory(path,max_bytes=LIMIT,max_files=10000,max_entries=20000,with_directories=True)
    return {'files':{k:v for k,v in files.items() if k not in {'result.json','result.json.partial'} and not k.startswith(('invalidated-result-','interrupted-result-'))},'directories':list(dirs)}
def packet(destination,boardraw=None):
    destination.mkdir()
    for path in (SOURCE/'Hardware').iterdir():
        need(path.is_file() and not path.is_symlink(),'fixed flat Hardware population required');shutil.copy2(path,destination/path.name)
    notices=destination/'_licenses/creator';notices.mkdir(parents=True)
    for name in ('LICENSE.md','README.md'):shutil.copy2(SOURCE/name,notices/name)
    board=destination/NAME
    if boardraw is not None:board.write_bytes(boardraw)
    return board

def check_stage(root,data,name):
    binding=f.read_json(root/(name+'-binding.json'))
    return f.check_drc_stage(root,data,name,Path(binding['source']),Path(binding['input']),binding['saved'],binding['before'],schematic_parity=name.endswith('final') and Path(binding['source']).with_suffix('.kicad_sch').name in binding['before'])

def baseline(original,hashes,tools):
    """Actual retained saved/final reports and exact original-shell reconstruction."""
    old=f.read_json(OLD/'result.json');candidate=Path(old['final_candidate'])
    need(old.get('controls_passed') is True and old.get('accepted') is False and old.get('engine_execution') is False,'retained protected transport did not qualify')
    need(old['tools']['files']==tools['files'],'retained Native tool binaries differ')
    saved=check_stage(OLD,old,'candidate-refill');final=check_stage(OLD,old,'candidate-final')
    need(final==old['native'] and p.sha(OLD/'candidate-final.json')==old['final_report_sha256'],'retained original report pin differs')
    p.verify_candidate_files(candidate,hashes,old['final_candidate_sha256'])
    need(io.read_bytes(candidate)==encoded(p.transplant_fill(original,sx.read(OLD/'saved'/NAME)))
        and p.routes(sx.read(candidate))==p.routes(original),'retained original shell/routes differ')
    need(p.native_accepted(final) and (final['opens'],final['blocking'],final['warnings'],final['exclusions'])==(0,0,1,0)
        and sn.same_findings(saved,final),'retained whole-original Native baseline differs')
    controls=f.read_json(ROOT/'.runs/roller-semantics-native-001/result.json')
    for name,negative in (('jumper_positive',False),('jumper_crossing',True),('signal_crossing',True)):
        row=next(x for x in controls['cases'] if x['case']==name)
        observed=check_stage(ROOT/'.runs/roller-semantics-native-001',controls,name+'-final')
        need(row.get('control_passed') is True and observed==row['native'] and (observed['blocking']>0)==negative,'retained copper-text/jumper control differs')
    continuation=f.read_json(ROOT/'.runs/roller-no-export-continuation-001/result.json')
    need(continuation['original_native']==final and continuation['original_candidate_sha256']==p.sha(candidate),'retained original baseline lineage differs')
    return final


def check_export(out,data,board):
    """Replay one fresh task export and its during-alias full Native observations."""
    source=io.read_bytes(board);hashes=inventory(board.parent);ctx=f.read_json(out/'context.json');diag=f.read_json(out/'diagnostic.json');events=f.read_json(out/'alias-evidence.json')
    argv=[str(p.c.PYTHON),str(WORKER),str(board),str(out/'context.json'),str(out/'native.dsn'),str(out/'diagnostic.json'),'A',str(out/'before.kicad_pcb'),str(out/'after.kicad_pcb')]
    f.process_check(out,data,'task-alias-export',[*f.SANDBOX,*argv]);f.context_binding(ctx,board,hashes,'final',None)
    need(ctx.get('routes')==[] and len(ctx['nets'])==4 and all(x['class']=='Default' for x in ctx['nets']),'authoritative four-Default unrouted context required')
    need(len(ctx['pads'])<=10000 and all(len(ctx[k])<=10000 for k in ('nets','routes','obstacles')),'Native item ceiling')
    binding=alias.plan(source,'A');raw=io.read_bytes(out/'native.dsn');alias.dsn_aliases(raw,source,binding)
    need(events.get('source_sha256')==p.sha(board) and events.get('context_sha256')==p.sha(out/'context.json')
        and events.get('diagnostic_sha256')==p.sha(out/'diagnostic.json') and events.get('dsn_sha256')==p.sha(out/'native.dsn')
        and events.get('before_board_sha256')==p.sha(out/'before.kicad_pcb') and events.get('after_board_sha256')==p.sha(out/'after.kicad_pcb'),'alias geometry sidecar binding differs')
    rows=events['events'];need([x['phase'] for x in rows]==['during_alias','restored'],'full alias observations missing')
    from experiments.roller_export_alias_v1.worker import without_authorized_reference_display
    restored=rows[1]['observation'];during=rows[0]['observation']
    need(without_authorized_reference_display(during,binding,True)==without_authorized_reference_display(restored,binding)
        and sx.read(out/'before.kicad_pcb')==sx.read(out/'after.kicad_pcb'),'alias changed Native geometry or emission')
    need(diag['observation_before_export']==diag['observation_after_export'] and diag['same_loaded_board'] is True
        and diag['observation_before_export']['native_observation_sha256']==digest(f.canonical(restored).encode()),'same-load geometry diagnostic differs')
    proof=alias.unused_class_proof(source,io.read_bytes(board.with_suffix('.kicad_pro')),ctx,raw)
    text={'observation_before_export':restored['layers_text'],'observation_after_export':restored['layers_text'],'same_loaded_board':True}
    layer=checks.layer_text(sx.read(board),text,raw.decode())
    return ctx,binding,proof,layer


def engine_input(out,budget):
    argv=p.engine_argv(out,budget['argv'])
    need(argv.count('-de')==1,'one engine input required')
    path=Path(argv[argv.index('-de')+1])
    need(path==out/'task.dsn','fixed engine input path differs')
    return path.name


def verify_phase_preimages(out,original,ctx,phases,negative_control):
    if 'positive' in phases:
        expected=p.transplant_routes(transport.task(original),sx.read(out/'imported.kicad_pcb'),protected=[],policy='exact_non_uuid_lock_position_v2')
        need(io.read_bytes(Path(phases['positive']['directory'])/'pre-refill.kicad_pcb')==encoded(expected),'positive pre-refill is not exact generated routing on original task')
    if 'negative' in phases:
        expected,control=transport.bridge(sx.read(Path(phases['positive']['candidate'])),ctx)
        need(control==negative_control and io.read_bytes(Path(phases['negative']['directory'])/'pre-refill.kicad_pcb')==encoded(expected),'negative is not the exact deterministic physical bridge')


def experiment(output,*,run_native=False):
    need(run_native is True,'explicit ROOT sequential Native opt-in required')
    start=time.monotonic();cpu0=h.cpu_seconds();spec_raw=io.read_bytes(HERE/'protocol.json');spec=f.read_json(HERE/'protocol.json')
    need(spec.get('status')=='prospectively_frozen' and spec.get('driver_sha256')==p.sha(__file__) and spec.get('budget_seconds')==SECONDS
        and spec.get('bootstrap_allowance_seconds')==BOOT and REQUIRED<=set(spec.get('retained_inventories',{}))
        and CODE_REQUIRED<=set(spec.get('code_sha256',{})),'prospective protocol/source/evidence pins required')
    remaining=lambda:max(0,min(SECONDS-BOOT-(time.monotonic()-start),SECONDS-BOOT-(h.cpu_seconds()-cpu0)))
    out=local_settings.canonical(Path(output).absolute());need(out==ROOT/spec['output'] and out.parent==ROOT/'.runs' and not out.exists(),'fresh exact direct .runs output required')
    tools=None;runtime={};complete=None;phases={};jobs=[];hashes=None;original=None
    class Job(f.FloorJob):
        def __init__(self,path):
            super().__init__(path,SECONDS,remaining,protect_local_settings=True);jobs.append(self)
        def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
            a=list(map(str,argv));actual=a if already_sandboxed else [*f.SANDBOX,*a]
            need(not already_sandboxed or name=='engine','only exact engine owns explicit sandbox argv')
            need((name=='task-alias-export' and a[:2]==[str(p.c.PYTHON),str(WORKER)] and len(a)==9)
                or a[:2]==[str(p.c.PYTHON),str(ROOT/'autorouter/native.py')]
                or a[:3]==[str(p.c.CLI),'pcb','drc'] or a[:4]==[str(p.c.CLI),'sch','export','netlist']
                or name=='engine' and actual==p.engine_argv(self.out,record['engine_budget']['argv']),'fixed dispatch differs')
            cap=remaining()-(20 if name=='engine' else 0);need(cap>0,'whole wall/full CPU exhausted before worker')
            result=run(actual,cwd=self.out,log=self.out/(name+'.log'),timeout=cap if name=='engine' else min(30,cap),env=self.env,
                max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=RSS)
            result['name']=name;self.steps.append(result);p.save_json(self.out/(name+'-process.json'),result)
            if result['status']=='cancelled':raise KeyboardInterrupt
            need(result['status'] in ('success','nonzero_exit') and type(result['exit_code'])is int and result['exit_code'] in allowed
                and result.get('cleanup_complete')is True and result.get('log_truncated')is False,'worker failed or cleanup/log incomplete: '+name)
            need(remaining()>0,'whole wall/full CPU exhausted after worker');return result
    job=Job(out);owner={};h.capture_destination(owner,out)
    record=dict(schema=1,kind='roller_generated_route_diagnostic',accepted=False,qualified=False,production_support_qualified=False,
        physical_electrical_validation=False,status='running',budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,bootstrap_allowance_seconds=BOOT,
        output_cap_bytes=LIMIT,item_ceiling=10000,one_engine_only=True,adapter='both',engine_profile='standard',input_policy='native',
        scope='whole_board_unlocked_routing',schematic_parity='complete original schematic required',protocol_sha256=digest(spec_raw),phases=phases,
        previous_controls_rerun=False,previous_routed_exports_rerun=False,ancestry_independent=False,asset_closure_qualified=False,
        resource_accounting_point='Actor sample precedes guarded final callback; whole outer wall/full CPU and bootstrap remain mandatory.',
        prior_development_costs='Retained prior diagnostic costs are separate disclosed development work; older unmeasured startup remains unknown.')
    def stable():
        h.owned_destination(owner);need(io.read_bytes(HERE/'protocol.json')==spec_raw,'prospective protocol changed')
        need(inventory(SOURCE)==spec['source_inventory'],'source five-file project changed')
        for name,pin in spec['code_sha256'].items():need(p.sha(ROOT/name)==pin,'pinned helper changed: '+name)
        for name,pins in spec['retained_inventories'].items():need(inventory(ROOT/name)==pins,'retained prior evidence changed: '+name)
        if tools is not None:need(p.tool_manifest()==tools,'tool/code/HEAD changed')
        for name,pin in runtime.items():need(p.sha(ROOT/name)==pin,'committed source changed')
        if complete is not None:need(witness(out)==complete,'completed or failed partial evidence changed')
    def account():
        record.update(wall_seconds=time.monotonic()-start,full_cpu_seconds=h.cpu_seconds()-cpu0,
            charged_wall_seconds=BOOT+time.monotonic()-start,charged_full_cpu_seconds=BOOT+h.cpu_seconds()-cpu0,
            steps=[step for value in jobs for step in value.steps])
        inventory(out)
        if remaining()<=0:record.update(status='budget_exceeded',qualified=False)
        if record['status']!='completed':record['qualified']=False
    def capture_code(value):
        (value.out/'code').mkdir()
        for name in tools['implementation_sha256']:shutil.copy2(ROOT/name,value.out/'code'/Path(name).name)
    def read_phase(name):
        row=phases[name];value=next(j for j in jobs if str(j.out)==row['directory']);candidate=Path(row['candidate']);data={'steps':value.steps,'tools':tools}
        prefill=sx.read(value.out/'pre-refill.kicad_pcb');before={**hashes,NAME:p.sha(value.out/'pre-refill.kicad_pcb')}
        saved=f.check_drc_stage(value.out,data,'refill-drc',value.out/'refill'/NAME,value.out/'refill'/NAME,True,before)
        native=f.check_drc_stage(value.out,data,'final-drc',candidate,value.out/'final-drc-input'/NAME,False,{**hashes,NAME:row['candidate_sha256']},schematic_parity=True)
        need(saved==row['saved_native'] and native==row['native'] and p.sha(value.out/'final-drc.json')==row['report_sha256'],'phase raw Native summaries/report differ')
        need(io.read_bytes(candidate)==encoded(p.transplant_fill(prefill,sx.read(value.out/'refill'/NAME)))
            and p.immutable(sx.read(candidate))==p.immutable(original),'phase original-shell/refill mismatch')
        p.verify_candidate_files(candidate,hashes,row['candidate_sha256']);p.check_hole_machining_support(sx.read(candidate))
        p.check_pour_evidence(value.out,data,original,candidate,source_hashes=hashes,correction=False,sandboxed=True)
        local_settings.check_normal_policy(value.out,data,max_bytes=LIMIT,max_files=10000)
        return native
    def validate(name,tree):
        value=Job(out/name);capture_code(value);candidate=packet(value.out/'candidate',encoded(tree))
        phases[name]={'directory':str(value.out),'candidate':str(candidate),'status':'incomplete'};row=phases[name]
        need(p.immutable(tree)==p.immutable(original) and len(p.routes(tree))<=10000,'candidate changed fixed geometry or exceeded route ceiling')
        p.check_hole_machining_support(tree);p.verify_candidate_files(candidate,hashes);p.legacy_zone_evidence(original,candidate)
        (value.out/'pre-refill.kicad_pcb').write_bytes(encoded(tree));shutil.copytree(candidate.parent,value.out/'refill')
        row['saved_native']=value.drc('refill-drc',value.out/'refill'/NAME,save=True)
        sx.write(candidate,p.transplant_fill(tree,sx.read(value.out/'refill'/NAME)))
        need(p.immutable(sx.read(candidate))==p.immutable(original),'refill changed original nonrouting intent')
        row.update(candidate_sha256=p.sha(candidate),native=value.drc('final-drc',candidate,schematic_parity=True),
            report_sha256=p.sha(value.out/'final-drc.json'),status='observed')
        read_phase(name);return value,candidate,row['native']
    def replay():
        stable()
        if original is None:return
        reference=baseline(original,hashes,tools)
        if 'task_sha256' in record:
            need(p.sha(out/'task'/NAME)==record['task_sha256'] and sx.read(out/'task'/NAME)==transport.task(original),'fresh task differs from whole-unrouted source')
            ctx,binding,proof,layer=check_export(out,{'steps':job.steps},out/'task'/NAME)
            need(proof==record['native_export_class_proof'] and layer==record['layer_text_proof'],'export proof differs')
            f.process_check(out,{'steps':job.steps},'obstacles',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'obstacles',str(out/'task'/NAME),str(out/'obstacles.json')])
            adapted,change=adapter.adapt_bytes(io.read_bytes(out/'native.dsn'),'both',f.read_json(out/'obstacles.json'))
            corrected,edge=native_edge.correct(adapted,native_edge.derive_context(io.read_bytes(out/'snapshot'/NAME),io.read_bytes((out/'snapshot'/NAME).with_suffix('.kicad_pro'))))
            need(io.read_bytes(out/'task.dsn')==corrected and change==record['adapter_transformations'] and edge==record['native_edge_correction'],'raw-to-adapter/edge bytes differ')
            checks.inactive_default(f.read_json((out/'task'/NAME).with_suffix('.kicad_pro')),ctx,corrected.decode())
        if 'engine_budget' in record and (out/'engine-process.json').exists():
            expected=p.engine_profile_settings('standard',record['engine_budget']['remaining_outer_wall_seconds_at_assignment'],strict_class_targets=True)
            need(expected==record['engine_budget'],'engine strict-target/budget settings differ')
            f.process_check(out,{'steps':job.steps},'engine',p.engine_argv(out,expected['argv']))
        if (out/'imported.kicad_pcb').exists():
            _,receipt=transport.session(io.read_bytes(out/'routes.ses'),io.read_bytes(out/'task.dsn'),io.read_bytes(out/'task'/NAME),alias.plan(io.read_bytes(out/'task'/NAME)),engine_input_name=engine_input(out,record['engine_budget']))
            need(receipt==record['session_transport'],'fixed-placement/alias routing proof differs')
            local_settings.check_normal_policy(out,{'steps':[step for value in jobs for step in value.steps],'tools':tools},max_bytes=LIMIT,max_files=10000)
            need(sn.semantic_diff(sx.read(out/'before.kicad_pcb'),sx.read(out/'imported.kicad_pcb'))['equal'],'Native imported fixed geometry differs')
        verify_phase_preimages(out,original,ctx,phases,record.get('negative_control'))
        for name,row in phases.items():
            if row.get('status')!='observed':continue
            native=read_phase(name)
            if name=='positive':need(p.native_accepted(native) and sn.same_findings(reference,native),'positive original-rule/warning acceptance differs')
            elif name=='negative':
                control=record['negative_control']
                need(not p.native_accepted(native) and native['exclusions']==0 and (native['opens']>0 or native['blocking']>0)
                    and any(x['severity']=='error' and any(i.get('uuid')==control['uuid'] for i in x['items']) for x in native['findings']),'negative physical fault did not bind a Native rejection')
            else:raise p.Rejected('unknown validation phase')
        if record['status']=='completed':
            need(set(phases)=={'positive','negative'} and all(row.get('status')=='observed' for row in phases.values())
                and record.get('candidate_native_validated')is True and 'metrics' in record and record.get('qualified')is True,'completed diagnostic phases/proofs missing')
        if 'metrics' in record:
            value=next(j for j in jobs if j.out==out/'positive');candidate=Path(phases['positive']['candidate'])
            f.process_check(value.out,{'steps':value.steps},'metrics',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',str(candidate),str(value.out/'metrics.json')])
            need(f.read_json(value.out/'metrics.json')==record['metrics'] and p.sha(value.out/'metrics.json')==record['metrics_sha256'],'actual final metrics differ')
            f.process_check(value.out,{'steps':value.steps},'final-netclasses',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'netclasses',str(candidate),str(value.out/'final-netclasses.json')])
            finalmap=f.read_json(value.out/'final-netclasses.json');need(finalmap['source']==str(candidate) and finalmap['board_sha256']==p.sha(candidate)
                and finalmap['project_sha256']==p.sha(candidate.with_suffix('.kicad_pro')) and finalmap['board_saved']is False,'candidate effective class map stale')
            need(checks.inactive_default(f.read_json(candidate.with_suffix('.kicad_pro')),finalmap,io.read_bytes(out/'task.dsn').decode())==record['final_class_proof']
                and p.audit_route_dimensions(sx.read(candidate),[],finalmap)==record['route_dimension_audit'],'final Native class/target proof differs')
        stable();need(remaining()>0,'final callback exhausted whole budget')
    try:
        stable();p.check_storage();tools=p.tool_manifest();capture_code(job)
        extras={**tools['implementation_sha256'],**spec['code_sha256'],str((HERE/'protocol.json').relative_to(ROOT)):digest(spec_raw)}
        runtime=io.capture_freeze({**tools,'implementation_sha256':extras})['files_sha256'];record.update(tools=tools,runtime_source_sha256=runtime)
        original=sx.read(SOURCE/'Hardware'/NAME);need(len(p.routes(original))==11 and all(x[0]=='segment' and not p.locked(x) for x in p.routes(original)),'fixed eleven-unlocked-source-segment task required')
        p.check_rule_area_support(original);p.check_hole_machining_support(original);need(not pour.qualify(original),'fixed source has unexpected pour restriction')
        sourceboard=packet(out/'snapshot');hashes=inventory(sourceboard.parent);record['source_hashes']=hashes
        pinned_source=f.read_json(ROOT/'experiments/roller_export_alias_v1/native-pins.json')['source_inventory']
        need(spec['source_inventory']==pinned_source,'original creator source/notice pins differ')
        reference=baseline(original,hashes,tools);record['original_native']=reference
        task=transport.task(original);board=packet(out/'task',encoded(task));record['task_sha256']=p.sha(board)
        argv=[p.c.PYTHON,WORKER,board,out/'context.json',out/'native.dsn',out/'diagnostic.json','A',out/'before.kicad_pcb',out/'after.kicad_pcb']
        job.step('task-alias-export',argv);ctx,binding,proof,layer=check_export(out,{'steps':job.steps},board)
        record.update(native_export_class_proof=proof,layer_text_proof=layer)
        job.native('obstacles','obstacles',board,out/'obstacles.json');need(inventory(board.parent)=={**hashes,NAME:record['task_sha256']},'obstacle worker changed task companions')
        adapted,change=adapter.adapt_bytes(io.read_bytes(out/'native.dsn'),'both',f.read_json(out/'obstacles.json'))
        corrected,edge=native_edge.correct(adapted,native_edge.derive_context(io.read_bytes(sourceboard),io.read_bytes(sourceboard.with_suffix('.kicad_pro'))))
        (out/'task.dsn').write_bytes(corrected);checks.inactive_default(f.read_json(board.with_suffix('.kicad_pro')),ctx,corrected.decode())
        record.update(adapter_transformations=change,native_edge_correction=edge,engine_budget=p.engine_profile_settings('standard',remaining()-10,strict_class_targets=True))
        p.save_json(out/'pre-engine.json',record);(out/'engine-config').mkdir();stable()
        job.step('engine',p.engine_argv(out,record['engine_budget']['argv']),already_sandboxed=True)
        _,record['session_transport']=transport.session(io.read_bytes(out/'routes.ses'),corrected,io.read_bytes(board),binding,engine_input_name=engine_input(out,record['engine_budget']))
        job.native('import','import',board,out/'imported.kicad_pcb',out/'routes.ses')
        need(sn.semantic_diff(sx.read(out/'before.kicad_pcb'),sx.read(out/'imported.kicad_pcb'))['equal'],'import changed Native nonrouting fixed geometry')
        tree=p.transplant_routes(task,sx.read(out/'imported.kicad_pcb'),protected=[],policy='exact_non_uuid_lock_position_v2')
        value,candidate,native=validate('positive',tree)
        need(p.native_accepted(native) and sn.same_findings(reference,native),'generated candidate failed original fullSCH/rules/warnings')
        value.native('final-netclasses','netclasses',candidate,value.out/'final-netclasses.json');finalmap=f.read_json(value.out/'final-netclasses.json')
        record.update(final_class_proof=checks.inactive_default(f.read_json(candidate.with_suffix('.kicad_pro')),finalmap,corrected.decode()),
            route_dimension_audit=p.audit_route_dimensions(sx.read(candidate),[],finalmap))
        value.native('metrics','metrics',candidate,value.out/'metrics.json');metrics=f.read_json(value.out/'metrics.json')
        need(metrics.get('version')=='10.0.0' and metrics.get('copper_layers')==2 and type(metrics.get('vias'))is int and metrics['vias']>=0
            and type(metrics.get('track_length_mm'))in (int,float) and math.isfinite(metrics['track_length_mm']) and metrics['track_length_mm']>=0,'invalid actual Native metrics')
        record.update(metrics=metrics,metrics_sha256=p.sha(value.out/'metrics.json'),candidate_native_validated=True)
        fault,control=transport.bridge(sx.read(candidate),ctx);record['negative_control']=control
        _,_,invalid=validate('negative',fault)
        need(not p.native_accepted(invalid) and invalid['exclusions']==0 and (invalid['opens']>0 or invalid['blocking']>0)
            and any(x['severity']=='error' and any(i.get('uuid')==control['uuid'] for i in x['items']) for x in invalid['findings']),'physical fault escaped UUID-bound Native rejection')
        record.update(status='completed',qualified=True);replay()
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',qualified=False,initial_failure=type(exc).__name__+': '+str(exc))
    complete=witness(out);record['completed_material']=complete;account()
    return f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=replay)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    if not args.run_native:parser.error('--run-native required after prospective freeze/checkpoint')
    old={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
    def stop(*_):raise KeyboardInterrupt
    try:
        for s in old:signal.signal(s,stop)
        result=experiment(args.output,run_native=True)
    finally:
        for s,handler in old.items():signal.signal(s,handler)
    print({k:result.get(k) for k in ('status','qualified','initial_failure','reason','charged_wall_seconds','charged_full_cpu_seconds')})
    raise SystemExit(0 if result.get('qualified') is True else 2)
