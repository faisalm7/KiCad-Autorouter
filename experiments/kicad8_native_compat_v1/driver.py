"""ROOT-only original KiCad8 native compatibility observations; no admission."""
from pathlib import Path
import argparse,copy,datetime,fcntl,hashlib,json,shutil,signal,subprocess,sys,time
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'experiments/lipo_native_diagnostic_v1'))
from autorouter import config as c,pipeline as p,sexpr as sx,floor_route as f,placement_clearance as io
from experiments.lipo_native_diagnostic_v1 import driver as shared
import fixture
SECONDS=90;LIMIT=20*1024**2;HELPERS=('driver.py','fixture.py','test_driver.py','PROTOCOL.json','README.md')
CASES=(*fixture.CASES,'ideal_diode');SOURCE=ROOT/'.data/expansion004/ideal-diode/Hardware/SparkFun_Ideal_Diode_Breakout.kicad_pcb'
TEMPLATE=ROOT/'evidence/placement-area-native-001/allowed_placement/candidate'
FALSE_FLAGS=('routing_accepted','production_supported','format_support_qualified','ses_import_qualified','dependency_complete','physical_electrical_validation')

def digest(raw):return hashlib.sha256(raw).hexdigest()
def inventory(path):return shared.inventory(path)
def control_output(path):
    path=shared.owned(path)
    direct=path.parent==ROOT/'.runs'
    monitored=(path.name=='run' and path.parent.parent==ROOT/'.runs' and path.parent.name.startswith('kicad8-native-compat-') and path.parent.is_dir())
    if path.exists() or not (direct or monitored):raise p.Rejected('fresh direct or monitored compatibility output required')
    return path
def geometry(context):
    """Compare actual same-load geometry/rules, allowing only local netcode renumbering."""
    value={key:copy.deepcopy(context[key]) for key in ('native_version','units','floors_nm','pads','nets','routes','obstacles')}
    for key in ('pads','nets','routes'):
        for row in value[key]:row.pop('netcode',None)
        value[key].sort(key=f.canonical)
    value['obstacles'].sort(key=f.canonical);return value

def emission_equal(first,second):
    """Full actual KiCad10 emissions, except derived fill; no header stripping."""
    if p.immutable(first)!=p.immutable(second) or p.routes(first)!=p.routes(second):raise p.Rejected('native saved/reloaded non-fill geometry or routes differ')
    return {'non_fill_native_ast_equal':True,'native_routes_equal':True,
        'non_fill_native_ast_sha256':digest((sx.dump(p.immutable(first))+'\n').encode()),'native_routes_sha256':digest(sx.dump(p.routes(first)).encode())}

def old_shell(original,saved):
    if sx.one(original,'version')!=['version','20240108']:raise p.Rejected('original source format differs')
    result=p.transplant_fill(original,saved)
    if p.immutable(result)!=p.immutable(original) or p.routes(result)!=p.routes(original) or sx.one(result,'version')!=['version','20240108']:
        raise p.Rejected('original shell/route preservation failed')
    return result

def copy_project(source,target):
    shutil.copytree(source,target)
    if inventory(source)!=inventory(target):raise p.Rejected('complete copied project differs')

def observe(job,name,board):
    expected=inventory(board.parent);path=job.out/(name+'-context.json');dsn=job.out/(name+'.dsn');argv=f.context_argv('export',board,path,dsn)
    job.step(name,argv,already_sandboxed=True);context=f.read_json(path)
    f.context_binding(context,board,expected,'export',p.sha(dsn));f.process_check(job.out,{'steps':job.steps},name,argv)
    if context.get('routing_accepted') is not False or context.get('native_version')!='10.0.0':raise p.Rejected('unexpected observational native context')
    return context

def roundtrip(job,name,board):
    before=inventory(board.parent);output=job.out/(name+'.kicad_pcb');job.native(name,'roundtrip',board,output)
    f.process_check(job.out,{'steps':job.steps},name,[*f.SANDBOX,str(c.PYTHON),str(ROOT/'autorouter/native.py'),'roundtrip',str(board),str(output)])
    if inventory(board.parent)!=before or not output.is_file():raise p.Rejected('native roundtrip changed input or emitted nothing')
    return sx.read(output)

def drc_readback(job,name,board,native,before,saved):
    target=board if saved else job.out/(name+'-input')/board.name
    actual=f.check_drc_stage(job.out,{'steps':job.steps},name,board,target,saved,before)
    if actual!=native:raise p.Rejected('native DRC interpretation differs')
    return {'native':native,'report_sha256':p.sha(job.out/(name+'.json')),'binding_sha256':p.sha(job.out/(name+'-binding.json'))}


def probe(job,source,case):
    source_hashes=inventory(source.parent);original=sx.read(source)
    if source.with_suffix('.kicad_prl').exists():raise p.Rejected('existing PRL needs separately qualified write protection; no exemption')
    if sx.one(original,'version')!=['version','20240108']:raise p.Rejected('not the pinned original KiCad8 format')
    full_observation=case in ('positive','ideal_diode')
    row={'case':case,'status':'running','source_sha256':p.sha(source),'source_hashes':source_hashes,'steps':job.steps,'original_format':'20240108',**{key:False for key in FALSE_FLAGS}}
    try:
        if full_observation:
            input_path=job.out/'observe-input';copy_project(source.parent,input_path);board=input_path/source.name
            before=observe(job,'original-export',board);native_original=roundtrip(job,'original-native',board)
        candidate_dir=job.out/'candidate';copy_project(source.parent,candidate_dir);candidate=candidate_dir/source.name
        # The shared finalizer performs saved refill, exact old-shell derived
        # fill transplant, protected/invariant checks and the actual final DRC.
        # Calling this diagnostic does not enable the blocked preflight format.
        protected=[route for route in p.routes(original) if p.locked(route)]
        digest_candidate,final=p.validate_candidate(job,original,candidate,source_hashes,protected)
        row['shared_validation_invoked']=True;saved=job.out/'refill'/source.name
        native=p.parse_report(job.out/'refill-drc.json',source.name)
        row['saved_drc']=drc_readback(job,'refill-drc',saved,native,source_hashes,True)
        expected=dict(source_hashes);expected[candidate.name]=digest_candidate
        row['final_drc']=drc_readback(job,'final-drc',candidate,final,expected,False)
        shell=old_shell(original,sx.read(saved))
        if (sx.dump(shell)+'\n').encode()!=io.read_bytes(candidate):raise p.Rejected('shared original-shell reconstruction differs')
        if full_observation:
            reloaded=observe(job,'saved-export',saved);native_saved=roundtrip(job,'saved-native',saved)
            row['native_serialization_equivalence']=emission_equal(native_original,native_saved)
            if geometry(before)!=geometry(reloaded):raise p.Rejected('saved/reloaded same-load geometry or rules differ')
            candidate_context=observe(job,'shell-export',candidate);native_candidate=roundtrip(job,'shell-native',candidate)
            row['shell_serialization_equivalence']=emission_equal(native_original,native_candidate)
            if geometry(candidate_context)!=geometry(before):raise p.Rejected('original-shell native geometry/rules changed')
            row['native_geometry_sha256']=digest(f.canonical(geometry(before)).encode())
        else:row['full_geometry_observation']='Not repeated for exact one-route invalid controls; native saved/final DRC and original-shell invariants are checked.'
        p.verify_candidate_files(candidate,source_hashes,digest_candidate)
        if final!=native:raise p.Rejected('saved and original-shell native findings/ignored checks differ')
        if case!='ideal_diode':
            passed,hits=fixture.expected(case,final);row.update(expected_native_outcome=passed,targeted_findings=hits)
            if not passed:raise p.Rejected('actual '+case+' critical native control differs')
        row.update(status='observed',observations_complete=True,candidate=str(candidate),candidate_sha256=digest_candidate,
            original_inputs_unchanged=True)
        return row
    except (Exception,KeyboardInterrupt) as exc:
        row.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',observations_complete=False,error=type(exc).__name__+': '+str(exc));raise
    finally:p.save_json(job.out/'case.json',row)


def experiment(output,*,run_native=False):
    if run_native is not True or HERE!=ROOT/'experiments/kicad8_native_compat_v1':raise p.Rejected('ROOT promote/checkpoint required before --run-native')
    start=time.monotonic();cpu0=shared.cpu();remaining=lambda:max(0,min(SECONDS-(time.monotonic()-start),SECONDS-(shared.cpu()-cpu0)))
    out=control_output(output);out.mkdir();protocol=f.read_json(HERE/'PROTOCOL.json');jobs=[];completed={};source_inputs={};tools=None;frozen=None;runtime={}
    record={'schema':1,'status':'incomplete','observations_complete':False,'original_inputs_unchanged':None,'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_ceiling_bytes':LIMIT,
        'protocol_sha256':p.sha(HERE/'PROTOCOL.json'),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':[],**{key:False for key in FALSE_FLAGS},
        'scope':'Three authored20240108 critical native controls then one unchanged acquired ideal-diode save/refill compatibility observation. No routing, SES import or admission.'}
    def account():
        record.update({key:False for key in FALSE_FLAGS});record.update(steps=[s for job in jobs for s in job.steps],wall_seconds=time.monotonic()-start,total_cpu_seconds=shared.cpu()-cpu0,within_budget=remaining()>0)
        record['native_executed']=bool(record['steps']);record['accounting_point']='Stored totals precede final publication. Whole wall/parent-plus-waited-child CPU includes all native calls, failed attempts and final checks; observed caps, not OS aggregate quotas.'
        if remaining()<=0:record.update(status='budget_exceeded',observations_complete=False)
    def stable():
        if shared.size(out)>LIMIT or remaining()<=0:raise p.Rejected('whole compatibility resource cap')
        if tools is None:return
        if p.tool_manifest()!=tools or inventory(out/'code')!=frozen or any(p.sha(ROOT/name)!=sha for name,sha in runtime.items()):raise p.Rejected('tool/code/HEAD changed')
        if p.sha(HERE/'PROTOCOL.json')!=record['protocol_sha256']:raise p.Rejected('protocol changed')
        for rel,expected in protocol['original_trees'].items():
            if inventory(ROOT/rel)!=expected:raise p.Rejected('original input/notices changed')
        for folder,expected in source_inputs.items():
            if inventory(Path(folder))!=expected:raise p.Rejected('authored source changed')
        for folder,expected in completed.items():
            if inventory(Path(folder))!=expected:raise p.Rejected('completed native evidence changed')
        if any(record[key] is not False for key in FALSE_FLAGS):raise p.Rejected('unsupported qualification claim')
    try:
        p.check_storage()
        for rel,expected in protocol['original_trees'].items():
            if inventory(ROOT/rel)!=expected:raise p.Rejected('original source pin differs')
        if SOURCE.with_suffix('.kicad_prl').exists():raise p.Rejected('unexpected original PRL; preservation policy must be reviewed first')
        receipt=f.read_json(ROOT/protocol['acquisition_receipt']);rows=[row for row in receipt['files'] if row['repository']=='sparkfun/SparkFun_Ideal_Diode_Breakout']
        if p.sha(ROOT/protocol['acquisition_receipt'])!=protocol['acquisition_receipt_sha256'] or len(rows)!=6:raise p.Rejected('original acquisition receipt differs')
        for row in rows:
            raw=io.read_bytes(ROOT/row['local_path']);blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if row['commit']!='c950f439b55c08009e14fecc60f0fecd5832a42e' or len(raw)!=row['bytes'] or digest(raw)!=row['sha256'] or blob!=row['git_blob_sha1']:raise p.Rejected('original source acquisition blob differs')
        try:p.preflight(SOURCE)
        except p.Rejected as exc:
            if str(exc)!='unsupported: unqualified board format version':raise
            record['original_preflight_rejection']=str(exc)
        else:raise p.Rejected('existing production format guard unexpectedly opened')
        tools=p.tool_manifest();record['tools']=tools;runtime=shared.snapshot(out,tools,remaining)
        for path in [*(HERE/name for name in HELPERS),TEMPLATE/'fixture.kicad_pro',TEMPLATE/'PROVENANCE.md',*sorted((TEMPLATE/'_licenses').iterdir())]:
            rel=str(path.relative_to(ROOT));raw=io.read_bytes(path);blob=subprocess.run(['git','show',tools['git_head']+':'+rel],cwd=ROOT,capture_output=True,check=True,timeout=max(.001,min(3,remaining()))).stdout
            if blob!=raw:raise p.Rejected('commit exact compatibility helper/template first: '+rel)
            target=out/'code'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);runtime[rel]=digest(raw)
        record['runtime_sources']=runtime;frozen=inventory(out/'code');record['code_inventory']=frozen
        for case in fixture.CASES:
            folder=out/'owned-sources'/case;folder.mkdir(parents=True);(folder/'fixture.kicad_pcb').write_bytes(fixture.board(case));shutil.copy2(TEMPLATE/'fixture.kicad_pro',folder/'fixture.kicad_pro');shutil.copytree(TEMPLATE/'_licenses',folder/'_licenses')
            (folder/'PROVENANCE.md').write_text('Original authored KiCad8 numeric-net/layer grammar control under GPL-3.0. Unchanged attributed KiCad multichannel project settings retain CC-BY-SA4.0 and original notices. Case: '+case+'. No real source board adapted or relabelled.\n')
            source_inputs[str(folder)]=inventory(folder)
        original_bytes=sum((SOURCE.parent/name).stat().st_size for name in inventory(SOURCE.parent))
        if shared.size(out)+4*original_bytes+4*1024**2>LIMIT:raise p.Rejected('complete native copies/reserve exceed20MiB')
        for case in CASES:
            stable();source=SOURCE if case=='ideal_diode' else out/'owned-sources'/case/'fixture.kicad_pcb';job=f.FloorJob(out/case,SECONDS,remaining);jobs.append(job)
            try:row=probe(job,source,case)
            except (Exception,KeyboardInterrupt):
                if (job.out/'case.json').is_file():record['cases'].append(f.read_json(job.out/'case.json'))
                raise
            record['cases'].append(row);completed[str(job.out)]=inventory(job.out);stable()
        record.update(status='observations_complete',observations_complete=True,original_inputs_unchanged=True,completed_evidence=completed)
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',observations_complete=False,error=type(exc).__name__+': '+str(exc))
    return shared.publish(out,record,stable,account,remaining)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--run-native',action='store_true');args=ap.parse_args(argv)
    if not args.run_native:ap.error('--run-native required after reviewed committed promotion')
    prior={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in prior:signal.signal(sig,interrupted)
        with shared.owned(ROOT/'.runs/quality-experiment.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=experiment(args.output,run_native=True)
    finally:
        for sig,handler in prior.items():signal.signal(sig,handler)
    print(json.dumps({key:result[key] for key in ('status','observations_complete','format_support_qualified')}));return 0 if result['observations_complete'] else 2
if __name__=='__main__':raise SystemExit(main())
