"""ROOT-only prospective Roller semantics probe; no solver or admission."""
import copy,json,shutil,signal,sys,time
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
from autorouter import config as c,pipeline as p,floor_route as f,placement_clearance as io,sexpr as sx,handoff as h
from autorouter.runner import run
if __package__:
    from . import checks,fixture
else:
    import checks,fixture
SECONDS=120.;LIMIT=32*1024**2
CASES=('original','active_5mil','jumper_positive','jumper_crossing','signal_crossing')
def inventory(path):return io.inventory(path,max_bytes=LIMIT,max_files=4000,max_entries=8000)
def size(path):return sum((path/n).stat().st_size for n in inventory(path))
class Job(f.FloorJob):
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        inner=[str(a) for a in argv]
        permitted=(inner[:2]==[str(c.PYTHON),str(HERE/'worker.py')] and len(inner)==6) or inner[:3]==[str(c.CLI),'pcb','drc'] or inner[:4]==[str(c.CLI),'sch','export','netlist'] or inner[:3]==[str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'fields']
        if not permitted or already_sandboxed:raise p.Rejected('only fixed native observer/DRC permitted')
        if self.remaining()<=0:raise p.Rejected('shared budget exhausted')
        result=run([*f.SANDBOX,*inner],cwd=self.out,log=self.out/(name+'.log'),timeout=min(30,self.remaining()),env=self.env,
            max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
        result['name']=name;self.steps.append(result);p.save_json(self.out/(name+'-process.json'),result)
        if result['status']=='cancelled':raise KeyboardInterrupt
        if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed or result.get('cleanup_complete') is not True:raise p.Rejected(name+': '+result['status'])
        return result

def experiment(output,*,run_native=False):
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in previous:signal.signal(sig,interrupted)
        return _experiment(output,run_native=run_native)
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)

def _experiment(output,*,run_native=False):
    if run_native is not True:raise p.Rejected('ROOT native lane only; explicit run_native=True required')
    start=time.monotonic();cpu0=h.cpu_seconds();remaining=lambda:max(0,min(SECONDS+start-time.monotonic(),SECONDS+cpu0-h.cpu_seconds()))
    out=h.real_path(output,existing=False)
    if out.parent!=ROOT/'.runs' or out.exists():raise p.Rejected('fresh direct .runs output required')
    lifecycle={};job=Job(out,SECONDS,remaining);h.capture_destination(lifecycle,out)
    pins=f.read_json(HERE/'pins.json');source=ROOT/pins['source_directory'];boardname=Path(pins['source_board']).name
    runtime={};tools=None;completed={};material={};record={'schema':1,'kind':'roller-semantics-prospective-v1','accepted':False,'status':'incomplete','controls_passed':False,
        'production_support_qualified':False,'dependency_complete':False,'independent_family_established':False,'new_engine_execution':False,
        'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_ceiling_bytes':LIMIT,'cases':[],
        'scope':'Embedded-2D original diagnostics and authored invalid controls; no original rules/metadata relaxation or routing admission.'}
    def owned():h.owned_destination(lifecycle)
    def stable():
        owned()
        for name,digest in pins['files_sha256'].items():
            if p.sha(ROOT/name)!=digest:raise p.Rejected('pinned source/cache changed: '+name)
        if inventory(source)!=pins['source_files']:raise p.Rejected('original source population changed')
        if any(p.sha(ROOT/n)!=v for n,v in runtime.items()) or (runtime and inventory(out/'code')!=runtime):raise p.Rejected('runtime helper freeze changed')
        if tools is not None and p.tool_manifest()!=tools:raise p.Rejected('tool/code/HEAD freeze changed')
        for case,census in completed.items():
            if inventory(out/case)!=census:raise p.Rejected('completed case artifact changed')
        for name,digest in material.items():
            if p.sha(out/name)!=digest:raise p.Rejected('native report/process material changed: '+name)
        if record['accepted'] is not False or record['production_support_qualified'] is not False:raise p.Rejected('diagnostic scope changed')
    def account():
        record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=h.cpu_seconds()-cpu0,steps=job.steps,
            child_step_cpu_seconds=sum(x.get('cpu_seconds') or 0 for x in job.steps),monitor_cpu_seconds=sum(x.get('monitor_cpu_seconds') or 0 for x in job.steps))
        if remaining()<=0 or size(out)>LIMIT:record.update(status='budget_exceeded',controls_passed=False)
        if record['status']!='controls_passed':record['controls_passed']=False
    def observe(caseout,board,tag):
        context=caseout/(tag+'-context.json');dsn=caseout/(tag+'.dsn');diag=caseout/(tag+'-observation.json')
        argv=[c.PYTHON,HERE/'worker.py',board,context,dsn,diag];stage=caseout.name+'-'+tag
        before=inventory(board.parent);job.step(stage,argv)
        actual=f.read_json(context);extra=f.read_json(diag)
        f.context_binding(actual,board,before,'export',p.sha(dsn))
        if extra.get('input_hashes_before')!=before or extra.get('input_hashes_after')!=before or extra.get('floor_context_sha256')!=p.sha(context) or extra.get('dsn_sha256')!=p.sha(dsn):raise p.Rejected('same-load diagnostic binding differs')
        f.process_check(out,{'steps':job.steps},stage,[*f.SANDBOX,*map(str,argv)])
        return actual,extra,dsn
    try:
        stable();tools=p.tool_manifest()
        extras=[HERE/n for n in ('driver.py','worker.py','checks.py','fixture.py','pins.json','PROTOCOL.json')]
        merged={**tools['implementation_sha256'],**{str(x.relative_to(ROOT)):p.sha(x) for x in extras}}
        # Requires promoted, committed helpers; ignored draft deliberately cannot pass this gate.
        runtime=io.capture_freeze({**tools,'implementation_sha256':merged})['files_sha256']
        for name,digest in runtime.items():
            target=out/'code'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
        record.update(tools=tools,runtime_source_sha256=runtime,controller_sha256=p.sha(HERE/'driver.py'),protocol_sha256=p.sha(HERE/'PROTOCOL.json'),pinned_inputs=pins)
        for case in CASES:
            try:
                stable();caseout=out/case;caseout.mkdir();inp=caseout/'observe-input';inp.mkdir()
                if case in ('original','active_5mil'):
                    for item in (source/'Hardware').iterdir():shutil.copy2(item,inp/item.name)
                    notices=inp/'_licenses/creator';notices.mkdir(parents=True)
                    for name in ('LICENSE.md','README.md'):shutil.copy2(source/name,notices/name)
                    board=inp/boardname
                    if case=='active_5mil':
                        pro=f.read_json(board.with_suffix('.kicad_pro'));pro['net_settings']['netclass_patterns']=[{'netclass':'5mil','pattern':'A'}];p.save_json(board.with_suffix('.kicad_pro'),pro)
                    parity=True
                else:
                    tree,pro=fixture.fixture(sx.read(ROOT/'tests/fixtures/board-floor/fixture.kicad_pcb'),f.read_json(ROOT/'tests/fixtures/board-floor/fixture.kicad_pro'),negative=case.endswith('crossing'),layer_type='signal' if case=='signal_crossing' else 'jumper')
                    board=inp/'fixture.kicad_pcb';sx.write(board,tree);p.save_json(board.with_suffix('.kicad_pro'),pro);parity=False
                original=sx.read(board);hashes=inventory(inp);pro=f.read_json(board.with_suffix('.kicad_pro'))
                row={'case':case,'accepted':False,'control_passed':False,'source_hashes':hashes,'board_sha256':p.sha(board),'project_sha256':p.sha(board.with_suffix('.kicad_pro'))};record['cases'].append(row)
                ctx,extra,dsn=observe(caseout,board,'original');row['layer_text_audit']=checks.layer_text(original,extra,dsn.read_text())
                if case=='active_5mil':
                    net=next(x for x in ctx['nets'] if x['name']=='A')
                    if net['class']!='5mil' or (net['width_nm'],net['clearance_nm'])!=(127000,127000):raise p.Rejected('active class negative not exercised')
                    try:checks.inactive_default(pro,ctx,dsn.read_text())
                    except ValueError as exc:row.update(control_passed=True,negative_reason=str(exc),effective_A=net)
                    else:raise p.Rejected('active5mil unexpectedly passed inactive proof')
                else:
                    if case=='original':row['inactive_class_audit']=checks.inactive_default(pro,ctx,dsn.read_text())
                    saved=caseout/'saved';shutil.copytree(inp,saved);savedboard=saved/board.name;before=inventory(saved)
                    stage=case+'-refill';native=job.drc(stage,savedboard,save=True)
                    if f.check_drc_stage(out,{'steps':job.steps},stage,savedboard,savedboard,True,before)!=native:raise p.Rejected('saved native binding differs')
                    _,emission,_=observe(caseout,savedboard,'saved');row['saved_layer_text_audit']=checks.layer_text(sx.read(savedboard),emission,(caseout/'saved.dsn').read_text())
                    if emission['observation_before_export']!=extra['observation_before_export']:raise p.Rejected('native save changed observed layer/copper text intent')
                    cand=caseout/'candidate';shutil.copytree(inp,cand);candidate=cand/board.name;sx.write(candidate,p.transplant_fill(original,sx.read(savedboard)))
                    if p.immutable(sx.read(candidate))!=p.immutable(original) or p.routes(sx.read(candidate))!=p.routes(original):raise p.Rejected('original shell/protected routing changed')
                    p.verify_candidate_files(candidate,hashes,p.sha(candidate));stage=case+'-final';final=job.drc(stage,candidate,schematic_parity=parity)
                    if f.check_drc_stage(out,{'steps':job.steps},stage,candidate,out/(stage+'-input')/candidate.name,False,inventory(cand),schematic_parity=parity)!=final:raise p.Rejected('actual final native binding differs')
                    row.update(native=final,native_rejection_reasons=p.native_rejection_reasons(final),source_native_accepted=p.native_accepted(final),final_candidate_sha256=p.sha(candidate),final_native_report_sha256=p.sha(out/(stage+'.json')))
                    row['control_passed']=True if case=='original' else checks.crossing(final,case.endswith('crossing'),fixture.uid('text'),fixture.uid('cross'))
                row['status']='observed' if row['control_passed'] else 'control_failed';completed[case]=inventory(caseout)
                if not row['control_passed']:record.setdefault('unproven_cases',[]).append(case)
            except Exception as exc:
                if remaining()<=0:raise
                record['cases'][-1].update(status='failed',control_passed=False,reason=type(exc).__name__+': '+str(exc)) if record['cases'] and record['cases'][-1]['case']==case else record['cases'].append({'case':case,'status':'failed','control_passed':False,'reason':type(exc).__name__+': '+str(exc)})
                completed[case]=inventory(out/case)
                record.setdefault('unproven_cases',[]).append(case)
        material.update({x.name:p.sha(x) for x in out.iterdir() if x.is_file()})
        record['native_artifacts_sha256']=material
        record.update(status='controls_passed' if all(x['control_passed'] for x in record['cases']) else 'controls_failed',controls_passed=all(x['control_passed'] for x in record['cases']))
        stable();account()
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,reason=type(exc).__name__+': '+str(exc))
    f.publish(out,record,stable,account,remaining,owned=owned)
    try:
        owned()
        if remaining()<=0 or size(out)>LIMIT:raise p.Rejected('final diagnostic budget/storage exhausted')
        stable();owned()
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',controls_passed=False,reason=type(exc).__name__+': '+str(exc))
        def failed_final_check():raise p.Rejected(record['reason'])
        f.publish(out,record,failed_final_check,account,remaining,owned=owned)
    return record
