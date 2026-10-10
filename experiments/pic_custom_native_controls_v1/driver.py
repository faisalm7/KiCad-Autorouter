"""ROOT-only six owned custom-pad controls; no routing or production support."""
from __future__ import annotations
import argparse,copy,fcntl,hashlib,json,resource,shutil,signal,subprocess,sys,time,uuid
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import config as c,pipeline as p,sexpr as sx,floor_route as f,placement_clearance as io
from autorouter.runner import run
import fixture,checks,recipes
SOURCE=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb'
RECEIPT=ROOT/'data/sources.json'
RECEIPT_SHA='a2a8e9e22ff3e109de94733aa8f5e99ca5fd476ef9ec20be837c54100036eac1'
BOARD_SHA='1ca70b620506818eb0227e2863bbd573d1fec1672072dc43d0dbe8475e69c8fb'
PROJECT_SHA='3b0ac39da5af86d0baa2a64da55a89c39ba00148dc82b54f3062f5c3650a5cc5'
WRAPPER=c.PYTHON.parent.parent/'lib/python3.9/site-packages/pcbnew.py'
WRAPPER_SHA='cd1c06c4709c653256ebd0c98c66d80cd72033767fac27c34ea01b5ec586116a'
SECONDS=180;LIMIT=32*1024*1024;RESERVE=2*1024*1024
HELPERS=('driver.py','worker.py','fixture.py','checks.py','recipes.py','test_controls.py','test_recipes.py','PROTOCOL.json','README.md')
DEPENDENCIES=('experiments/pic_custom_observer_v1/mapping.py',)
BASELINE_REPORT_REL='evidence/pic-custom-observation-002/original-drc.json'
BASELINE_REPORT_SHA='a3ae0798c019ee60d3fb37171a18bc940043c6329dbf1f24dc9c9463f1df01d7'
OBSERVED_IGNORED=('footprint_filters_mismatch','silk_edge_clearance','track_not_centered_on_via','tuning_profile_track_geometries')
EXPECTED_GATE='unsupported: custom pads not qualified; unknown rule severity semantics: footprint_symbol_field_mismatch; unknown rule severity semantics: missing_tuning_profile; unknown rule severity semantics: text_on_edge_cuts; unknown rule severity semantics: track_on_post_machined_layer'
FALSE_CLAIMS={'routing_accepted':False,'geometry_qualified':False,'format_support_qualified':False,'dependency_complete':False,'custom_routing_support_qualified':False,'nondefault_resolution_qualified':False,'new_severity_enforcement_qualified':False,'arbitrary_reflection_qualified':False,'new_engine_execution':False,'board_saved':False}
def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return f.read_json(path)
def inventory(path):return io.inventory(path,max_bytes=LIMIT,max_files=2048,max_entries=4096)
def digest(path):return sha_bytes(io.read_bytes(path,LIMIT))
def size(path):return sum(map(len,io.inventory(path,contents=True,max_bytes=LIMIT,max_files=2048,max_entries=4096).values()))

def owned(path,*,output=False):
    path=Path(path).absolute()
    if '..' in path.parts or any(x.is_symlink() for x in (path,*path.parents)):raise p.Rejected('real canonical paths required')
    if not path.is_relative_to(ROOT):raise p.Rejected('path outside checkout')
    if output and (path.parent!=ROOT/'.runs' or path.exists()):raise p.Rejected('fresh direct .runs output required')
    return path

def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime

def source_binding():
    owned(SOURCE);owned(RECEIPT)
    if sha_bytes(io.read_bytes(RECEIPT))!=RECEIPT_SHA:raise p.Rejected('acquisition manifest changed')
    receipt=read(RECEIPT);expected={};total=0
    if receipt.get('commit')!='69cafb907ebc09e7722a2a464b1d466fc2e3608d':raise p.Rejected('source commit differs')
    for row in receipt['files']:
        if row.get('project_id')!='kicad-pic-programmer':continue
        path=owned(ROOT/'.data'/row['destination'])
        if not path.is_relative_to(SOURCE.parent):raise p.Rejected('acquisition path outside source')
        name=str(path.relative_to(SOURCE.parent))
        if name in expected:raise p.Rejected('duplicate acquired path')
        raw=io.read_bytes(path,LIMIT-total);total+=len(raw)
        if len(raw)!=row['bytes'] or sha_bytes(raw)!=row['sha256'] or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=row['git_blob_sha1']:raise p.Rejected('acquired source blob differs')
        expected[name]=row['sha256']
    if len(expected)!=15 or total!=1366598 or inventory(SOURCE.parent)!=expected or expected.get(SOURCE.name)!=BOARD_SHA or expected.get(SOURCE.with_suffix('.kicad_pro').name)!=PROJECT_SHA:raise p.Rejected('complete acquired source inventory differs')
    return expected,total

def snapshot(out,tools,remaining=lambda:SECONDS):
    sources={ROOT/name:digest for name,digest in tools['implementation_sha256'].items()}
    sources[ROOT/'toolchain.lock.json']=p.sha(ROOT/'toolchain.lock.json')
    for name in HELPERS:sources[owned(HERE/name)]=digest(HERE/name)
    for name in DEPENDENCIES:sources[owned(ROOT/name)]=digest(ROOT/name)
    sources[owned(ROOT/BASELINE_REPORT_REL)]=BASELINE_REPORT_SHA
    for path,expected_digest in sources.items():
        rel=str(owned(path).relative_to(ROOT));available=remaining()
        if available<=0:raise p.Rejected('budget exhausted before committed snapshot')
        blob=subprocess.run(['git','show',tools['git_head']+':'+rel],cwd=ROOT,capture_output=True,check=True,timeout=min(3,available)).stdout
        if sha_bytes(blob)!=expected_digest or p.sha(path)!=expected_digest:raise p.Rejected('commit exact core/toolchain/helpers before native: '+rel)
    (out/'code').mkdir()
    bindings={}
    for path,expected_digest in sources.items():
        rel=str(path.relative_to(ROOT));target=out/'code'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        if p.sha(target)!=expected_digest:raise p.Rejected('helper changed during snapshot')
        bindings[rel]=expected_digest
    return bindings

def observe_argv(out):
    return [*f.SANDBOX,str(c.PYTHON),str(HERE/'worker.py'),str(out/'observe-input'/SOURCE.name),str(out/'observation.json'),str(out/'native.dsn'),str(out/'custom-pads.json')]
def drc_argv(out):
    return [*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(out/'original-drc.json'),str(out/'original-drc-input'/SOURCE.name)]

class ControlJob(f.FloorJob):
    def __init__(self,out,remaining,batch):
        super().__init__(out,SECONDS,remaining);self.batch=batch;self.stage_evidence={};self.binding_evidence={}
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        actual=[str(x) for x in (argv if already_sandboxed else [*f.SANDBOX,*argv])]
        expected=observe_argv(self.out) if name=='observe' else drc_argv(self.out)
        if name not in ('observe','original-drc') or actual!=expected:raise p.Rejected('only exact nonsaving diagnostic stages allowed')
        available=self.remaining()
        if available<=0 or size(self.batch)>LIMIT:raise p.Rejected('shared resource cap exhausted')
        result=run(actual,cwd=self.out,log=self.out/(name+'.log'),timeout=min(30,available),env=self.env,
            max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
        result['name']=name;self.steps.append(result);p.save_json(self.out/(name+'-process.json'),result)
        if result['status']=='cancelled':raise KeyboardInterrupt
        if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed or result.get('cleanup_complete') is not True:raise p.Rejected(name+': '+result['status'])
        outputs=['observation.json','native.dsn','custom-pads.json'] if name=='observe' else ['original-drc.json']
        self.stage_evidence[name]={key:digest(self.out/key) for key in outputs+[name+'-process.json',name+'.log']}
        if self.remaining()<=0 or size(self.batch)>LIMIT:raise p.Rejected('shared resource cap exceeded after stage')
        return result
    def drc(self,name,board,save=False):
        # Narrow original Job.drc protocol, with bounded tree inventories and a
        # binding-file capture before the unchanged central report parser runs.
        if name!='original-drc' or save is not False or board!=self.out/'observe-input'/SOURCE.name:raise p.Rejected('only nonsaving owned-fixture DRC allowed')
        before=inventory(board.parent);work=self.out/'original-drc-input'
        shutil.copytree(board.parent,work);target=work/board.name
        result=self.step(name,drc_argv(self.out),allowed=(0,5),already_sandboxed=True)
        after=inventory(work)
        if any(after.get(k)!=v for k,v in before.items()) or set(after)-set(before)-{target.with_suffix('.kicad_prl').name}:raise p.Rejected('native DRC modified fixture or rules')
        result.update(validated_input_sha256=before[board.name],emitted_candidate=str(board))
        binding=self.out/'original-drc-binding.json';p.save_json(binding,{'source':str(board),'input':str(target),'before':before,'after':after,'saved':False})
        self.binding_evidence[binding.name]=digest(binding)
        native=p.parse_report(self.out/'original-drc.json',board.name)
        if (result['exit_code']==0)==bool(native['findings']):raise p.Rejected('DRC exit/report mismatch')
        return native

def observation_binding(out,hashes,scene,project):
    native=read(out/'observation.json');custom=read(out/'custom-pads.json');raw=io.read_bytes(out/'native.dsn',20*1024**2)
    if not raw:raise p.Rejected('empty native DSN')
    f.context_binding(native,out/'observe-input'/SOURCE.name,hashes,'export',sha_bytes(raw))
    for key in ('context_schema','native_version','units','mode','source','board_sha256','project_sha256','dsn_sha256','input_hashes_before','input_hashes_after'):
        if custom.get(key)!=native.get(key):raise p.Rejected('custom/floor binding differs')
    if custom.get('floor_context_sha256')!=digest(out/'observation.json'):raise p.Rejected('custom floor digest differs')
    return checks.observe(native,custom,raw,scene,project)

def drc_binding(out,steps,hashes,native):
    source=out/'observe-input'/SOURCE.name;target=out/'original-drc-input'/SOURCE.name
    binding=read(out/'original-drc-binding.json')
    if binding.get('source')!=str(source) or binding.get('input')!=str(target) or binding.get('saved') is not False or binding.get('before')!=hashes:raise p.Rejected('DRC input identity differs')
    after=binding['after']
    if any(after.get(k)!=v for k,v in hashes.items()) or set(after)-set(hashes)-{target.with_suffix('.kicad_prl').name} or inventory(target.parent)!=after:raise p.Rejected('DRC changed fixture/project')
    f.process_check(out,{'steps':steps},'original-drc',drc_argv(out),allowed=(5 if native['findings'] else 0,))
    if p.parse_report(out/'original-drc.json',SOURCE.name)!=native:raise p.Rejected('native summary/raw differ')
    return {'board_sha256':digest(target),'project_sha256':digest(target.with_suffix('.kicad_pro')),'report_sha256':digest(out/'original-drc.json'),'binding_sha256':digest(out/'original-drc-binding.json')}

def publish(out,record,stable,account,remaining):
    path=out/'summary.json'
    def invalidate():
        for candidate in (path,out/'summary.json.partial'):
            if candidate.exists():candidate.rename(out/('invalidated-'+uuid.uuid4().hex+'-'+candidate.name))
    try:
        stable();account();expected=f.canonical(record);p.save_json(path,record)
        if f.canonical(read(path))!=expected:raise p.Rejected('summary changed after write')
        stable();final_size=size(out)
        if f.canonical(record)!=expected or f.canonical(read(path))!=expected or final_size>LIMIT or remaining()<=0:raise p.Rejected('summary stale or final cap exceeded')
    except (Exception,KeyboardInterrupt) as exc:
        first=record.get('error');error=type(exc).__name__+': '+str(exc)
        invalidate();record.update(**FALSE_CLAIMS,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',
            controls_passed=False,original_inputs_unchanged=None,error=first if first is not None else error,final_validation_error=error);account()
        try:p.save_json(path,record)
        except (Exception,KeyboardInterrupt):invalidate()
    return record

def experiment(out,*,run_native=False):
    if run_native is not True:raise p.Rejected('--run-native required; ROOT-only execution')
    start=time.monotonic();cpu0=cpu();out=owned(out,output=True);out.mkdir()
    remaining=lambda:max(0,min(SECONDS-(time.monotonic()-start),SECONDS-(cpu()-cpu0)))
    record={'schema':1,'status':'incomplete','controls_passed':False,**FALSE_CLAIMS,'source':str(SOURCE),
        'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_ceiling_bytes':LIMIT,
        'scope':'Six fixed owned development controls; original complete project and all rules preserved. No routing engine, production eligibility, arbitrary geometry/reflection, nondefault or new-severity enforcement qualification.',
        'accounting_point':'Stored totals precede final publication freshness/size checks; acceptance caps include them. Wall/full self+waited-child CPU are measured caps, not hard OS quotas. Finite samples are not atomic authentication.',
        'cases':[{'variant':v,'case':c,'status':'not_attempted','native_executed':False,'control_passed':False,'stages':{}} for v,c in fixture.ORDER]}
    authorized=False;frozen=None;completed={};jobs={};hashes={};project=None;original=None;whole=None
    def account():
        steps=[step for job in jobs.values() for step in job.steps]
        record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=cpu()-cpu0,child_step_cpu_seconds=sum(step.get('cpu_seconds') or 0 for step in steps),
            monitor_cpu_seconds=sum(step.get('monitor_cpu_seconds') or 0 for step in steps),native_executed=bool(steps))
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS
        if not record['within_budget']:record.update(controls_passed=False,status='budget_exceeded')
    def material():
        if not authorized:return
        if inventory(SOURCE.parent)!=hashes or digest(RECEIPT)!=RECEIPT_SHA:raise p.Rejected('original source/acquisition changed')
        if sha_bytes(io.read_bytes(WRAPPER,4*1024**2))!=WRAPPER_SHA:raise p.Rejected('native wrapper changed')
        if frozen is not None:
            if inventory(out/'code')!=frozen or any(digest(ROOT/rel)!=sha for rel,sha in record['runtime_sources'].items()):raise p.Rejected('core/helper/protocol changed')
            if any(p.sha(Path(path))!=sha for path,sha in record['tools']['files'].items()):raise p.Rejected('runtime tool material changed')
        for key,expected in completed.items():
            if inventory(out/key)!=expected:raise p.Rejected('completed case evidence changed')
        if whole is not None and {k:v for k,v in inventory(out).items() if k!='summary.json' and not k.startswith('invalidated-')}!=whole:raise p.Rejected('completed batch material changed')
    def stable():
        if not authorized:return
        if any(record.get(key) is not value for key,value in FALSE_CLAIMS.items()):raise p.Rejected('diagnostic scope changed')
        if ([(row.get('variant'),row.get('case')) for row in record['cases']]!=list(fixture.ORDER)
                or record.get('source_hashes')!=hashes):raise p.Rejected('fixed case/source identity changed')
        if frozen is not None and p.tool_manifest()!=record['tools']:raise p.Rejected('code/tool/HEAD changed')
        material()
        for row in record['cases']:
            key=row['variant']+'-'+row['case'];job=jobs.get(key)
            if job is None:continue
            caseout=job.out
            captured=job.stage_evidence.get('observe')
            if row.get('dsn_export_succeeded',False) is not bool(captured) or row.get('native_dsn_sha256')!=(captured.get('native.dsn') if captured else None):raise p.Rejected('captured export facts differ')
            for stage,entries in job.stage_evidence.items():
                if any(digest(caseout/name)!=sha for name,sha in entries.items()):raise p.Rejected('native stage evidence changed')
                if row['stages'].get(stage)!=entries:raise p.Rejected('recorded stage evidence differs')
            if any(digest(caseout/name)!=sha for name,sha in job.binding_evidence.items()) or row.get('binding_evidence',{})!=job.binding_evidence:raise p.Rejected('native binding evidence changed')
            if row.get('input_hashes') is not None and inventory(caseout/'observe-input')!=row['input_hashes']:raise p.Rejected('authored fixture copy changed')
            if row.get('geometry_verified'):
                observed=observation_binding(caseout,row['input_hashes'],row['scene'],project)
                if observed!=row['observation']:raise p.Rejected('recorded geometry observation changed')
                f.process_check(caseout,{'steps':job.steps},'observe',observe_argv(caseout))
            if row.get('native_binding') is not None:
                if drc_binding(caseout,job.steps,row['input_hashes'],row['native'])!=row['native_binding']:raise p.Rejected('native report/binding changed')
                passed,hits=checks.predicate(row['case'],row['native'],read(caseout/'original-drc.json'),row['scene'],ignored)
                if passed is not row['expected_predicate_met'] or hits!=row['target_findings']:raise p.Rejected('recorded expected findings changed')
                positive=row['case']=='positive' or any(r['variant']==row['variant'] and r['case']=='positive' and r.get('expected_predicate_met') is True and r.get('geometry_verified') is True for r in record['cases'])
                if row.get('paired_positive_passed') is not positive or row['control_passed'] is not (passed and positive):raise p.Rejected('paired control qualification differs')
            elif row.get('control_passed') is not False:raise p.Rejected('unvalidated case cannot pass')
        if record['controls_passed'] is True and (len(completed)!=6 or not all(row['control_passed'] is True for row in record['cases'])):raise p.Rejected('batch pass lacks all six qualified cases')
        material()
    try:
        p.check_storage();hashes,total=source_binding();authorized=True;project=read(SOURCE.with_suffix('.kicad_pro'));original=sx.read(SOURCE)
        try:p.preflight(SOURCE)
        except p.Rejected as exc:record['production_gate_rejection']=str(exc)
        else:raise p.Rejected('original unexpectedly eligible; re-review scope')
        if record['production_gate_rejection']!=EXPECTED_GATE:raise p.Rejected('production scope changed')
        source_ignored=sorted(k for k,v in project['board']['design_settings']['rule_severities'].items() if v=='ignore')
        if digest(ROOT/BASELINE_REPORT_REL)!=BASELINE_REPORT_SHA:raise p.Rejected('original native ignored-check baseline changed')
        ignored=sorted(row['key'] for row in read(ROOT/BASELINE_REPORT_REL)['ignored_checks'])
        if ignored!=list(OBSERVED_IGNORED) or set(ignored)-set(source_ignored)!={'track_not_centered_on_via'}:raise p.Rejected('original observed effective ignored set differs')
        record.update(source_hashes=hashes,source_bytes=total,source_file_count=len(hashes),acquisition_receipt_sha256=RECEIPT_SHA,
            source_explicit_ignored_checks=source_ignored,original_observed_effective_ignored_checks=ignored,
            original_native_report={'path':BASELINE_REPORT_REL,'sha256':BASELINE_REPORT_SHA})
        record['protocol']=read(HERE/'PROTOCOL.json');record['protocol_sha256']=digest(HERE/'PROTOCOL.json')
        if record['protocol']!=protocol():raise p.Rejected('committed protocol differs from fixed implementation')
        record['tools']=p.tool_manifest();record['runtime_sources']=snapshot(out,record['tools'],remaining);frozen=inventory(out/'code')
        if size(out)+12*total+RESERVE>LIMIT:raise p.Rejected('twelve project copies exceed reserved32MiB ceiling')
        record['planned_project_copy_bytes_upper_bound']=12*total
        for row in record['cases']:
            key=row['variant']+'-'+row['case']
            if remaining()<=0:raise p.Rejected('shared budget exhausted before next case')
            job=ControlJob(out/key,remaining,out);jobs[key]=job
            try:
                stable();board,scene=fixture.prepare(original,row['case'],row['variant']);row['scene']=json.loads(f.canonical(scene))
                expected=dict(hashes);expected[SOURCE.name]=sha_bytes(board);row['input_hashes']=expected
                shutil.copytree(SOURCE.parent,job.out/'observe-input');(job.out/'observe-input'/SOURCE.name).write_bytes(board)
                if inventory(job.out/'observe-input')!=expected:raise p.Rejected('fixture derivation/project copy differs')
                p.save_json(job.out/'recipe.json',row['scene'])
                job.step('observe',observe_argv(job.out),already_sandboxed=True);row['stages']=copy.deepcopy(job.stage_evidence)
                row.update(native_executed=True,dsn_export_succeeded=True,native_dsn_sha256=row['stages']['observe']['native.dsn'])
                row['observation']=observation_binding(job.out,expected,row['scene'],project);row['geometry_verified']=True
                f.process_check(job.out,{'steps':job.steps},'observe',observe_argv(job.out));stable()
                native=job.drc('original-drc',job.out/'observe-input'/SOURCE.name,save=False);row['stages']=copy.deepcopy(job.stage_evidence);row['binding_evidence']=dict(job.binding_evidence)
                row['native']=native;row['native_binding']=drc_binding(job.out,job.steps,expected,native)
                passed,hits=checks.predicate(row['case'],native,read(job.out/'original-drc.json'),row['scene'],ignored)
                positive=row['case']=='positive' or any(r['variant']==row['variant'] and r['case']=='positive' and r['control_passed'] is True for r in record['cases'])
                row.update(expected_predicate_met=passed,target_findings=hits,paired_positive_passed=positive,control_passed=passed and positive,status='passed' if passed and positive else 'failed_expected_predicate')
            except (Exception,KeyboardInterrupt) as exc:
                row.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',control_passed=False,error=type(exc).__name__+': '+str(exc))
                if isinstance(exc,KeyboardInterrupt):raise
            finally:
                captured=job.stage_evidence.get('observe')
                row.update(stages=copy.deepcopy(job.stage_evidence),binding_evidence=dict(job.binding_evidence),steps=copy.deepcopy(job.steps),native_executed=bool(job.steps),
                    dsn_export_succeeded=bool(captured),native_dsn_sha256=captured.get('native.dsn') if captured else None)
                # Capture each finished case once; later checks never rebase it.
                completed[key]=inventory(job.out)
            stable()
        record.update(controls_passed=all(row['control_passed'] is True for row in record['cases']),original_inputs_unchanged=True)
        record['status']='controls_passed' if record['controls_passed'] else 'failed_controls'
        whole=inventory(out);record['completed_evidence']=whole
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
    return publish(out,record,stable,account,remaining)

def protocol():
    return {'schema':1,'name':'owned-custom-native-controls-v1.1','order':[{'variant':v,'case':c} for v,c in fixture.ORDER],
        'wall_seconds':SECONDS,'full_cpu_seconds':SECONDS,'output_bytes':LIMIT,'source_board_sha256':BOARD_SHA,'source_project_sha256':PROJECT_SHA,
        'original_native_report_sha256':BASELINE_REPORT_SHA,'expected_effective_ignored_checks':list(OBSERVED_IGNORED),
        'width_nm':500000,'clearance_nm':250000,'board_saved':False,'routing_engine':False,'production_custom_support':False,
        'intrusion_predicate':'Require nonexcluded same CONCAVE/FOREIGN_TRACK copper shorting_items or clearance error; allow at most one additional same-pair solder_mask_bridge error. Mask-only and unrelated errors fail. All raw findings retained.',
        'prior_exposed_run':{'path':'.runs/pic-custom-native-controls-001/summary.json','sha256':'dadb2512fef6bc4147ae522868acdc983d1d36bc8363bf14cd140e422f2f07db','status_preserved':'failed_controls'},
        'transform':'front0 identity; back90 T(x,y)=(40-y,40-x)mm; exact native world rings required. Y-symmetric shapes do not qualify arbitrary chiral reflection.'}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--run-native',action='store_true');args=ap.parse_args(argv)
    if not args.run_native:ap.error('--run-native required; ROOT-only execution')
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in previous:signal.signal(sig,interrupted)
        with owned(ROOT/'.runs/quality-experiment.lock').open('a') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);record=experiment(args.output,run_native=True)
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
    print(json.dumps({'status':record['status'],'controls_passed':record['controls_passed'],'routing_accepted':False}))
    return 0 if record['controls_passed'] else 2
if __name__=='__main__':raise SystemExit(main())
