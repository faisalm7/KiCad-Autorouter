"""ROOT-only continuation of the failed original KiCad8 diagnostic; no admission."""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,json,math,shutil,signal,subprocess,sys,time
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'experiments/kicad8_native_compat_v1'))
from autorouter import pipeline as p,sexpr as sx,floor_route as f,placement_clearance as io
from experiments.kicad8_native_compat_v1 import driver as prior
from experiments.lipo_native_diagnostic_v1 import driver as shared
SECONDS=90;LIMIT=20*1024**2;HELPERS=('driver.py','test_driver.py','PROTOCOL.json','README.md')
FALSE_FLAGS=('dsn_export_supported',*prior.FALSE_FLAGS)
STAGES=('original-context','original-native','refill-drc','final-drc','saved-context','saved-native','shell-context','shell-native')

def digest(raw):return hashlib.sha256(raw).hexdigest()
def inventory(path):return shared.inventory(path)
def qualifications(record):
    if any(record.get(key) is not False for key in FALSE_FLAGS):raise p.Rejected('unsupported qualification claim')
def footprint_census(board):
    """Identity/reference census, retaining duplicate references and every footprint."""
    result=[];seen=set()
    for fp in sx.children(board,'footprint'):
        identifier=sx.one(fp,'uuid')
        references=[x for x in sx.children(fp,'property') if len(x)>2 and sx.unquote(x[1])=='Reference']
        references += [x for x in sx.children(fp,'fp_text') if len(x)>2 and sx.unquote(x[1])=='reference']
        if identifier is None or len(identifier)!=2 or len(references)!=1:raise p.Rejected('ambiguous footprint identity/reference')
        key=sx.unquote(identifier[1])
        if not key or key in seen:raise p.Rejected('duplicate/empty footprint UUID')
        attributes=sx.one(fp,'attr') or []
        seen.add(key);result.append({'uuid':key,'reference':sx.unquote(references[0][2]),'pad_count':len(sx.children(fp,'pad')),
                                    'board_only':'board_only' in attributes,'exclude_from_bom':'exclude_from_bom' in attributes,'exclude_from_pos_files':'exclude_from_pos_files' in attributes})
    return sorted(result,key=lambda x:x['uuid'])
def duplicate_references(census):
    groups={}
    for row in census:groups.setdefault(row['reference'],[]).append(row)
    return {name:rows for name,rows in sorted(groups.items()) if len(rows)>1}
def emission_equal_by_uuid(first,second):
    """Exact non-fill AST and every route record; list order is not geometry."""
    if p.immutable(first)!=p.immutable(second):raise p.Rejected('native non-fill geometry differs')
    def records(board):
        result={}
        for route in p.routes(board):
            identifiers=sx.children(route,'uuid')
            if len(identifiers)!=1 or len(identifiers[0])!=2:raise p.Rejected('ambiguous native route UUID')
            key=sx.unquote(identifiers[0][1])
            if not key or key in result:raise p.Rejected('duplicate/empty native route UUID')
            result[key]=route
        return result
    a,b=records(first),records(second)
    if a!=b:raise p.Rejected('native route geometry, identity or population differs')
    return {'comparison':'exact-native-emission-by-uuid-v1','non_fill_native_ast_equal':True,
            'native_routes_equal_by_uuid':True,'route_count':len(a),'route_list_order_equal':p.routes(first)==p.routes(second),
            'non_fill_native_ast_sha256':digest((sx.dump(p.immutable(first))+'\n').encode()),
            'route_records_sha256':digest(f.canonical(a).encode()),
            'first_route_list_sha256':digest(sx.dump(p.routes(first)).encode()),
            'second_route_list_sha256':digest(sx.dump(p.routes(second)).encode())}
def prefix_readback(protocol):
    """Read retained native controls; never execute them again."""
    pin=protocol['prefix'];folder=shared.owned(ROOT/pin['directory'])
    if inventory(folder)!=pin['inventory'] or p.sha(folder/'run/summary.json')!=pin['summary_sha256'] or p.sha(folder/'execution.json')!=pin['execution_sha256']:
        raise p.Rejected('complete prior failure evidence differs')
    record=f.read_json(folder/'run/summary.json');execution=f.read_json(folder/'execution.json')
    if (record.get('status')!='failed' or record.get('observations_complete') is not False or record.get('error')!='Rejected: original-export: nonzero_exit exit=1'
            or execution['process'].get('exit_code')!=2 or execution['process'].get('status')!='nonzero_exit' or execution['process'].get('cleanup_complete') is not True):
        raise p.Rejected('prior failure disposition differs')
    for key,pinned in [('wall_seconds','prior_outer_wall_seconds'),('full_cpu_seconds','prior_outer_full_cpu_seconds')]:
        actual=execution.get(key);expected=pin[pinned]
        if isinstance(actual,bool) or not isinstance(actual,(int,float)) or not math.isfinite(actual) or actual<0 or actual!=expected or not 0<actual<SECONDS:
            raise p.Rejected('prior full-prefix resource charge differs')
    if len(record['cases'])!=4 or [x['case'] for x in record['cases']]!=[*pin['completed_owned_cases'],pin['failed_case']]:raise p.Rejected('prior case population differs')
    rows=[];flat=[]
    for row in record['cases']:
        case=row['case'];out=folder/'run'/case
        if f.read_json(out/'case.json')!=row or any(row.get(key) is not False for key in prior.FALSE_FLAGS):raise p.Rejected('prior raw case/claim differs')
        flat.extend(row['steps'])
        if case==pin['failed_case']:
            if row.get('status')!='failed' or row.get('observations_complete') is not False or len(row['steps'])!=1:raise p.Rejected('prior failed export case differs')
            board=out/'observe-input'/prior.SOURCE.name
            f.process_check(out,row,'original-export',f.context_argv('export',board,out/'original-export-context.json',out/'original-export.dsn'),allowed=(1,))
            if (out/'original-export.dsn').exists() or (out/'original-export-context.json').exists():raise p.Rejected('failed export unexpectedly published outputs')
            continue
        if row.get('status')!='observed' or row.get('observations_complete') is not True or row.get('expected_native_outcome') is not True:raise p.Rejected('prior owned control did not complete')
        original=folder/'run/owned-sources'/case/'fixture.kicad_pcb';candidate=out/'candidate/fixture.kicad_pcb';saved=out/'refill/fixture.kicad_pcb'
        hashes=inventory(original.parent)
        if hashes!=row['source_hashes'] or p.sha(original)!=row['source_sha256']:raise p.Rejected('prior owned source differs')
        native=f.check_drc_stage(out,row,'refill-drc',saved,saved,True,hashes)
        expected=dict(hashes);expected[candidate.name]=row['candidate_sha256']
        final=f.check_drc_stage(out,row,'final-drc',candidate,out/'final-drc-input'/candidate.name,False,expected)
        if native!=row['saved_drc']['native'] or final!=row['final_drc']['native'] or native!=final:raise p.Rejected('prior native DRC findings differ')
        for name in ('refill-drc','final-drc'):
            entry=row['saved_drc' if name=='refill-drc' else 'final_drc']
            if p.sha(out/(name+'.json'))!=entry['report_sha256'] or p.sha(out/(name+'-binding.json'))!=entry['binding_sha256']:raise p.Rejected('prior raw DRC binding differs')
        if prior.fixture.expected(case,final)!=(True,row['targeted_findings']):raise p.Rejected('prior native critical predicate differs')
        p.verify_candidate_files(candidate,hashes,row['candidate_sha256'])
        if (sx.dump(prior.old_shell(sx.read(original),sx.read(saved)))+'\n').encode()!=io.read_bytes(candidate):raise p.Rejected('prior original-shell candidate differs')
        if case=='positive':
            a=sx.read(out/'original-native.kicad_pcb')
            if prior.emission_equal(a,sx.read(out/'saved-native.kicad_pcb'))!=row['native_serialization_equivalence'] or prior.emission_equal(a,sx.read(out/'shell-native.kicad_pcb'))!=row['shell_serialization_equivalence']:raise p.Rejected('prior native emissions differ')
            contexts=[]
            for name,board in [('original-export',out/'observe-input/fixture.kicad_pcb'),('saved-export',saved),('shell-export',candidate)]:
                context=f.read_json(out/(name+'-context.json'));f.context_binding(context,board,inventory(board.parent),'export',p.sha(out/(name+'.dsn')))
                f.process_check(out,row,name,f.context_argv('export',board,out/(name+'-context.json'),out/(name+'.dsn')));contexts.append(prior.geometry(context))
            if not contexts[0]==contexts[1]==contexts[2] or digest(f.canonical(contexts[0]).encode())!=row['native_geometry_sha256']:raise p.Rejected('prior actual same-load context differs')
            for name,board in [('original-native',out/'observe-input/fixture.kicad_pcb'),('saved-native',saved),('shell-native',candidate)]:
                f.process_check(out,row,name,[*f.SANDBOX,str(prior.c.PYTHON),str(ROOT/'autorouter/native.py'),'roundtrip',str(board),str(out/(name+'.kicad_pcb'))])
        if len(row['steps'])!=(8 if case=='positive' else 2):raise p.Rejected('prior completed process census differs')
        rows.append({'case':case,'native':final,'native_reexecuted':False,'steps':len(row['steps'])})
    if flat!=record['steps'] or len(flat)!=13 or inventory(folder)!=pin['inventory']:raise p.Rejected('prior complete process history/evidence changed')
    return {'directory':pin['directory'],'status':'failed','summary_sha256':pin['summary_sha256'],'execution_sha256':pin['execution_sha256'],
            'original_export_failure_preserved':True,'owned_controls':rows,'actual_unique_native_processes':13,
            'prior_outer_wall_seconds':pin['prior_outer_wall_seconds'],'prior_outer_full_cpu_seconds':pin['prior_outer_full_cpu_seconds']}

def observe_final(job,name,board):
    before=inventory(board.parent);path=job.out/(name+'-context.json');argv=f.context_argv('final',board,path)
    job.step(name,argv,already_sandboxed=True);context=f.read_json(path)
    f.context_binding(context,board,before,'final',None);f.process_check(job.out,{'steps':job.steps},name,argv)
    if inventory(board.parent)!=before or context.get('routing_accepted') is not False or context.get('native_version')!='10.0.0':raise p.Rejected('final observation changed input or scope')
    return context
def ideal_probe(job,source):
    hashes=inventory(source.parent);original=sx.read(source)
    if source.with_suffix('.kicad_prl').exists() or source.with_suffix('.kicad_prl').is_symlink():raise p.Rejected('existing original PRL needs separately qualified protection')
    if sx.one(original,'version')!=['version','20240108'] or p.netclass_policy(source) is not None:raise p.Rejected('original format or planned native stage scope differs')
    row={'case':'ideal_diode','status':'running','observations_complete':False,'source_sha256':p.sha(source),'source_hashes':hashes,'steps':job.steps,**{k:False for k in FALSE_FLAGS}}
    try:
        prior.copy_project(source.parent,job.out/'observe-input');board=job.out/'observe-input'/source.name
        original_context=observe_final(job,'original-context',board);native_original=prior.roundtrip(job,'original-native',board)
        static_census=footprint_census(original);native_census=footprint_census(native_original)
        if static_census!=native_census:raise p.Rejected('actual native footprint reference census differs from source')
        row.update(original_native_footprint_census=native_census,original_duplicate_references=duplicate_references(native_census),
                   original_native_footprint_census_sha256=digest(f.canonical(native_census).encode()),duplicate_reference_cause_scope='Actual native retention plus pinned exporter source; no original caught C++ exception was captured.')
        prior.copy_project(source.parent,job.out/'candidate');candidate=job.out/'candidate'/source.name
        candidate_sha,final=p.validate_candidate(job,original,candidate,hashes,[route for route in p.routes(original) if p.locked(route)])
        saved=job.out/'refill'/source.name;saved_native=p.parse_report(job.out/'refill-drc.json',source.name)
        row['saved_drc']=prior.drc_readback(job,'refill-drc',saved,saved_native,hashes,True)
        expected=dict(hashes);expected[candidate.name]=candidate_sha
        row['final_drc']=prior.drc_readback(job,'final-drc',candidate,final,expected,False)
        if (sx.dump(prior.old_shell(original,sx.read(saved)))+'\n').encode()!=io.read_bytes(candidate):raise p.Rejected('shared original-shell reconstruction differs')
        reloaded=observe_final(job,'saved-context',saved);native_saved=prior.roundtrip(job,'saved-native',saved)
        candidate_context=observe_final(job,'shell-context',candidate);native_candidate=prior.roundtrip(job,'shell-native',candidate)
        row['native_serialization_equivalence']=emission_equal_by_uuid(native_original,native_saved)
        row['shell_serialization_equivalence']=emission_equal_by_uuid(native_original,native_candidate)
        if not prior.geometry(original_context)==prior.geometry(reloaded)==prior.geometry(candidate_context):raise p.Rejected('saved/original-shell same-load geometry or rules changed')
        if footprint_census(native_saved)!=native_census or footprint_census(native_candidate)!=native_census:raise p.Rejected('saved/original-shell native footprint census differs')
        if final!=saved_native:raise p.Rejected('saved and original-shell native findings/ignored checks differ')
        if [s['name'] for s in job.steps]!=list(STAGES):raise p.Rejected('unplanned native stage census')
        p.verify_candidate_files(candidate,hashes,candidate_sha)
        row.update(status='observed',observations_complete=True,candidate=str(candidate),candidate_sha256=candidate_sha,original_inputs_unchanged=True,
                   shared_validation_invoked=True,native_geometry_sha256=digest(f.canonical(prior.geometry(original_context)).encode()),
                   context_limit='Final-mode context excludes export-only obstacle capture; complete native-emitted non-fill AST includes all geometry/graphics. All contexts use the same mode.',
                   original_rule_drc_findings_retained=True,dsn_retry_performed=False)
        qualifications(row);return row
    except (Exception,KeyboardInterrupt) as exc:
        row.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',observations_complete=False,error=type(exc).__name__+': '+str(exc));raise
    finally:p.save_json(job.out/'case.json',row)

def experiment(output,*,run_native=False):
    if run_native is not True or HERE!=ROOT/'experiments/kicad8_native_compat_continuation_v1':raise p.Rejected('ROOT promote/checkpoint required before --run-native')
    start=time.monotonic();cpu0=shared.cpu();protocol=f.read_json(HERE/'PROTOCOL.json');pin=protocol['prefix']
    remaining=lambda:max(0,min(SECONDS-pin['prior_outer_wall_seconds']-(time.monotonic()-start),SECONDS-pin['prior_outer_full_cpu_seconds']-(shared.cpu()-cpu0)))
    out=prior.control_output(output);out.mkdir();tools=None;runtime={};frozen=None;completed=None;job=None;prefix=None;prefix_material=None;runtime_binding=None;code_binding=None
    record={'schema':1,'status':'incomplete','observations_complete':False,'original_inputs_unchanged':None,'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_ceiling_bytes':LIMIT,
        'protocol_sha256':p.sha(HERE/'PROTOCOL.json'),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**{k:False for k in FALSE_FLAGS},
        'scope':'Ideal-diode-only final-mode load/save/refill continuation; complete failed prior controls and costs retained. No DSN retry, aliases, source normalization, routing, SES or format admission.'}
    def account():
        wall=time.monotonic()-start;cpu=shared.cpu()-cpu0;steps=[] if job is None else job.steps
        record.update(steps=steps,new_wall_seconds=wall,new_full_cpu_seconds=cpu,wall_seconds=pin['prior_outer_wall_seconds']+wall,total_cpu_seconds=pin['prior_outer_full_cpu_seconds']+cpu,
                      prior_outer_wall_seconds=pin['prior_outer_wall_seconds'],prior_outer_full_cpu_seconds=pin['prior_outer_full_cpu_seconds'],within_budget=remaining()>0,native_executed=bool(steps))
        record['accounting_point']='Stored cumulative totals precede publication; ROOT outer wrapper must add full continuation launch/publication/readback costs. Prior failed run includes completed controls and failed export. Polling caps can overshoot, not an OS aggregate quota.'
        if remaining()<=0:record.update(status='budget_exceeded',observations_complete=False)
    def stable():
        qualifications(record)
        if remaining()<=0 or shared.size(out)>LIMIT:raise p.Rejected('cumulative native compatibility resource cap')
        if inventory(ROOT/pin['directory'])!=pin['inventory']:raise p.Rejected('prior failed evidence changed')
        for rel,expected in protocol['original_trees'].items():
            if inventory(ROOT/rel)!=expected:raise p.Rejected('original input/notices changed')
        if p.sha(HERE/'PROTOCOL.json')!=record['protocol_sha256'] or p.sha(ROOT/protocol['acquisition_receipt'])!=protocol['acquisition_receipt_sha256']:raise p.Rejected('protocol/acquisition changed')
        if prefix_material is not None and (f.canonical(prefix)!=prefix_material or f.canonical(record.get('prefix'))!=prefix_material):raise p.Rejected('recorded retained prefix differs')
        if tools is not None and (p.tool_manifest()!=tools or inventory(out/'code')!=code_binding or any(p.sha(ROOT/name)!=sha for name,sha in (runtime_binding or {}).items())
                                  or record.get('runtime_sources')!=runtime_binding or record.get('code_inventory')!=code_binding):raise p.Rejected('tool/code/HEAD changed')
        if completed is not None:
            if inventory(job.out)!=completed or f.read_json(job.out/'case.json')!=record.get('case'):raise p.Rejected('completed new native evidence/record changed')
            if any(name.endswith('.dsn') for name in completed):raise p.Rejected('unexpected new DSN in final-mode continuation')
    try:
        p.check_storage();prefix=prefix_readback(protocol);prefix_material=f.canonical(prefix);record['prefix']=prefix;stable()
        if protocol['new_stages']!=list(STAGES) or protocol['qualification']!={k:False for k in FALSE_FLAGS} or protocol.get('raw_real_board_publication') is not False:raise p.Rejected('continuation scope differs')
        source=shared.owned(ROOT/protocol['source'])
        if source!=prior.SOURCE or protocol['source_revision']!='c950f439b55c08009e14fecc60f0fecd5832a42e':raise p.Rejected('source scope differs')
        receipt=f.read_json(ROOT/protocol['acquisition_receipt']);rows=[r for r in receipt['files'] if r['repository']=='sparkfun/SparkFun_Ideal_Diode_Breakout']
        if len(rows)!=6:raise p.Rejected('acquisition population differs')
        for row in rows:
            raw=io.read_bytes(shared.owned(ROOT/row['local_path']));blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if row['commit']!=protocol['source_revision'] or len(raw)!=row['bytes'] or digest(raw)!=row['sha256'] or blob!=row['git_blob_sha1']:raise p.Rejected('source acquisition blob differs')
        try:p.preflight(source)
        except p.Rejected as exc:
            if str(exc)!='unsupported: unqualified board format version':raise
            record['original_preflight_rejection']=str(exc)
        else:raise p.Rejected('production format guard unexpectedly opened')
        tools=p.tool_manifest();record['tools']=tools;runtime=shared.snapshot(out,tools,remaining)
        helper_paths=[*(HERE/name for name in HELPERS),*(ROOT/'experiments/kicad8_native_compat_v1'/name for name in ('driver.py','fixture.py'))]
        for path in helper_paths:
            rel=str(path.relative_to(ROOT));raw=io.read_bytes(path);available=remaining()
            if available<=0:raise p.Rejected('cumulative budget exhausted before helper snapshot')
            blob=subprocess.run(['git','show',tools['git_head']+':'+rel],cwd=ROOT,capture_output=True,check=True,timeout=min(3,available)).stdout
            if blob!=raw:raise p.Rejected('commit exact continuation helper first: '+rel)
            target=out/'code'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);runtime[rel]=digest(raw)
        record['runtime_sources']=runtime;frozen=inventory(out/'code');record['code_inventory']=frozen;runtime_binding=dict(runtime);code_binding=dict(frozen)
        original_bytes=sum((source.parent/name).stat().st_size for name in inventory(source.parent))
        if shared.size(out)+4*original_bytes+4*1024**2>LIMIT:raise p.Rejected('complete project copies/reserve exceed20MiB')
        stable();job=f.FloorJob(out/'ideal_diode',SECONDS,remaining)
        try:record['case']=ideal_probe(job,source)
        except (Exception,KeyboardInterrupt):
            if (job.out/'case.json').is_file():record['case']=f.read_json(job.out/'case.json')
            raise
        completed=inventory(job.out);record['completed_evidence']=completed;stable()
        record.update(status='observations_complete',observations_complete=True,original_inputs_unchanged=True)
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',observations_complete=False,error=type(exc).__name__+': '+str(exc))
    return shared.publish(out,record,stable,account,remaining)

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--run-native',action='store_true');args=ap.parse_args(argv)
    if not args.run_native:ap.error('--run-native required after reviewed committed promotion')
    prior_signals={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in prior_signals:signal.signal(sig,interrupted)
        with shared.owned(ROOT/'.runs/quality-experiment.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=experiment(args.output,run_native=True)
    finally:
        for sig,handler in prior_signals.items():signal.signal(sig,handler)
    print(json.dumps({key:result[key] for key in ('status','observations_complete','format_support_qualified')}));return 0 if result['observations_complete'] else 2
if __name__=='__main__':raise SystemExit(main())
