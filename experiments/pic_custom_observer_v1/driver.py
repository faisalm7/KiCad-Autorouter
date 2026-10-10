"""Bounded unsupported-original pic custom-pad observations; never routes or saves a board.

Only the lead may execute with --run-native after tracked promotion/checkpoint.
Successful observations do not qualify custom-pad routing, geometry, format or dependency closure.
"""
from __future__ import annotations
import argparse,fcntl,hashlib,json,resource,shutil,signal,subprocess,sys,time,uuid
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import config as c,pipeline as p,sexpr as sx,floor_route as f,placement_clearance as io
from autorouter.runner import run
import mapping
SOURCE=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb'
RECEIPT=ROOT/'data/sources.json'
RECEIPT_SHA='a2a8e9e22ff3e109de94733aa8f5e99ca5fd476ef9ec20be837c54100036eac1'
BOARD_SHA='1ca70b620506818eb0227e2863bbd573d1fec1672072dc43d0dbe8475e69c8fb'
PROJECT_SHA='3b0ac39da5af86d0baa2a64da55a89c39ba00148dc82b54f3062f5c3650a5cc5'
WRAPPER=c.PYTHON.parent.parent/'lib/python3.9/site-packages/pcbnew.py'
WRAPPER_SHA='cd1c06c4709c653256ebd0c98c66d80cd72033767fac27c34ea01b5ec586116a'
SECONDS=60;LIMIT=20*1024*1024;RESERVE=1024*1024
HELPERS=('driver.py','worker.py','mapping.py','test_driver.py','README.md')
OBSERVATIONS=('custom-pad-export',)
EXPECTED_GATE='unsupported: custom pads not qualified; unknown rule severity semantics: footprint_symbol_field_mismatch; unknown rule severity semantics: missing_tuning_profile; unknown rule severity semantics: text_on_edge_cuts; unknown rule severity semantics: track_on_post_machined_layer'

def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return f.read_json(path)
def inventory(path):return io.inventory(path,max_bytes=LIMIT,max_files=512,max_entries=1024)
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

source_notes=mapping.source_notes

def observation_mode(observation):
    if observation!='custom-pad-export':raise p.Rejected('unknown observation mode')
    return 'export'

def observe_argv(out,observation='custom-pad-export'):
    observation_mode(observation);board=out/'observe-input'/SOURCE.name
    return [*f.SANDBOX,str(c.PYTHON),str(HERE/'worker.py'),str(board),str(out/'observation.json'),str(out/'native.dsn'),str(out/'custom-pads.json')]

def observation_outputs(out,observation):
    observation_mode(observation)
    return ['observation.json','native.dsn','custom-pads.json']

def observe_binding(out,hashes,notes,observation='custom-pad-export'):
    observation_mode(observation);board=out/'observe-input'/SOURCE.name
    observed=read(out/'observation.json');custom=read(out/'custom-pads.json');raw=io.read_bytes(out/'native.dsn',LIMIT)
    if not raw:raise p.Rejected('empty native DSN')
    f.context_binding(observed,board,hashes,'export',sha_bytes(raw))
    if observed.get('context_schema')!=1 or observed.get('native_version')!='10.0.0' or observed.get('units')!='integer nanometres' or observed.get('routing_accepted') is not False:raise p.Rejected('unexpected observation schema')
    for key in ('context_schema','native_version','units','mode','source','board_sha256','project_sha256','dsn_sha256','input_hashes_before','input_hashes_after'):
        if custom.get(key)!=observed.get(key):raise p.Rejected('custom/floor evidence binding differs')
    if custom.get('floor_context_sha256')!=sha_bytes(io.read_bytes(out/'observation.json',LIMIT)):raise p.Rejected('custom floor digest differs')
    mapping.floor_identity(observed,notes,read(SOURCE.with_suffix('.kicad_pro')))
    rows=mapping.custom_identity(custom,observed,notes)
    correspondence=mapping.dsn_correspondence(raw,observed,rows)
    return {**observed,'custom_pad_observation':custom,'dsn_correspondence':correspondence}

def snapshot(out,tools,remaining=lambda:SECONDS):
    sources={ROOT/name:digest for name,digest in tools['implementation_sha256'].items()}
    sources[ROOT/'toolchain.lock.json']=p.sha(ROOT/'toolchain.lock.json')
    for name in HELPERS:sources[owned(HERE/name)]=p.sha(HERE/name)
    for path,digest in sources.items():
        rel=str(owned(path).relative_to(ROOT));available=remaining()
        if available<=0:raise p.Rejected('budget exhausted before committed snapshot')
        blob=subprocess.run(['git','show',tools['git_head']+':'+rel],cwd=ROOT,capture_output=True,check=True,timeout=min(3,available)).stdout
        if sha_bytes(blob)!=digest or p.sha(path)!=digest:raise p.Rejected('commit exact core/toolchain/helpers before native: '+rel)
    (out/'code').mkdir()
    bindings={}
    for path,digest in sources.items():
        rel=str(path.relative_to(ROOT));target=out/'code'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        if p.sha(target)!=digest:raise p.Rejected('helper changed during snapshot')
        bindings[rel]=digest
    return bindings

def size(path):
    hashes=inventory(path)
    return sum((path/name).stat().st_size for name in hashes)

def reserve_copy(out,source_bytes,copies):
    if type(copies) is not int or copies<0 or size(out)+source_bytes*copies+RESERVE>LIMIT:raise p.Rejected('project copies/output exceed20MiB planned ceiling')

class ObservationJob(f.FloorJob):
    """Use proven isolation and runner, narrowed to two nonsaving native actions."""
    def __init__(self,out,seconds,remaining,observation='custom-pad-export'):
        observation_mode(observation);self.observation=observation
        super().__init__(out,seconds,remaining);self.stage_evidence={}
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        actual=[str(x) for x in (argv if already_sandboxed else [*f.SANDBOX,*argv])]
        expected=observe_argv(self.out,self.observation) if name=='observe' else drc_argv(self.out)
        if name not in ('observe','original-drc') or actual!=expected:raise p.Rejected('only exact nonsaving observation/DRC allowed')
        observation_outputs(self.out,self.observation)
        available=self.remaining()
        if available<=0:raise p.Rejected('shared wall/CPU budget exhausted')
        result=run(actual,cwd=self.out,log=self.out/(name+'.log'),
            timeout=available,env=self.env,max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
        result['name']=name;self.steps.append(result);p.save_json(self.out/(name+'-process.json'),result)
        if result['status']=='cancelled':raise KeyboardInterrupt
        if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed or result.get('cleanup_complete') is not True:raise p.Rejected(name+': '+result['status'])
        names=(observation_outputs(self.out,self.observation) if name=='observe' else ['original-drc.json'])+[name+'-process.json',name+'.log']
        self.stage_evidence[name]={key:sha_bytes(io.read_bytes(self.out/key,LIMIT)) for key in names}
        if self.remaining()<=0 or size(self.out)>LIMIT:raise p.Rejected('observation resource cap exceeded')
        return result

def drc_argv(out):
    return [*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(out/'original-drc.json'),str(out/'original-drc-input'/SOURCE.name)]

def drc_binding(out,steps,hashes,native):
    board=out/'observe-input'/SOURCE.name;target=out/'original-drc-input'/SOURCE.name;binding=read(out/'original-drc-binding.json')
    if binding.get('source')!=str(board) or binding.get('input')!=str(target) or binding.get('saved') is not False or binding.get('before')!=hashes:raise p.Rejected('DRC input binding differs')
    after=binding['after']
    if any(after.get(k)!=v for k,v in hashes.items()) or set(after)-set(hashes)-{target.with_suffix('.kicad_prl').name} or inventory(target.parent)!=after:raise p.Rejected('DRC changed copied original/rules')
    expected=drc_argv(out)
    f.process_check(out,{'steps':steps},'original-drc',expected,allowed=(5 if native['findings'] else 0,))
    if p.parse_report(out/'original-drc.json',SOURCE.name)!=native:raise p.Rejected('raw DRC summary differs')
    return {'board_sha256':p.sha(target),'project_sha256':p.sha(target.with_suffix('.kicad_pro')),'report_sha256':p.sha(out/'original-drc.json'),'binding_sha256':p.sha(out/'original-drc-binding.json')}

def publish(out,record,stable,account,remaining):
    path=out/'summary.json'
    def invalidate():
        for candidate in (path,out/'summary.json.partial'):
            if candidate.exists():candidate.rename(out/('invalidated-'+uuid.uuid4().hex+'-'+candidate.name))
    try:
        stable();account();expected=f.canonical(record);p.save_json(path,record)
        if f.canonical(read(path))!=expected:raise p.Rejected('summary changed afterwrite')
        stable()
        final_size=size(out)
        if (f.canonical(record)!=expected or f.canonical(read(path))!=expected
                or final_size>LIMIT or remaining()<=0):raise p.Rejected('summary stale or final resourcecap exceeded')
    except (Exception,KeyboardInterrupt) as exc:
        first_error=record.get('error');final_error=type(exc).__name__+': '+str(exc)
        invalidate();record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',observations_complete=False,
            routing_accepted=False,geometry_qualified=False,format_support_qualified=False,dependency_complete=False,
            original_inputs_unchanged=None,error=first_error if first_error is not None else final_error,
            final_validation_error=final_error);account()
        try:p.save_json(path,record)
        except (Exception,KeyboardInterrupt):invalidate()
    return record

def experiment(out,*,run_native=False,observation='custom-pad-export'):
    if run_native is not True:raise p.Rejected('--run-native required')
    mode=observation_mode(observation)
    start=time.monotonic();cpu0=cpu();out=owned(out,output=True)
    remaining=lambda:max(0,min(SECONDS-(time.monotonic()-start),SECONDS-(cpu()-cpu0)))
    job=ObservationJob(out,SECONDS,remaining,observation)
    record={'schema':1,'status':'incomplete','observations_complete':False,'routing_accepted':False,'dependency_complete':False,'format_support_qualified':False,
        'correspondence_verified':False,'native_original_pad_route_identities_match':None,
        'observation':observation,'native_observation_mode':mode,'dsn_export_requested':mode=='export','dsn_export_succeeded':False,'native_dsn_sha256':None,
        'geometry_qualified':False,'semantic_migration_performed':False,'board_saved':False,'new_engine_execution':False,'source':str(SOURCE),'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_ceiling_bytes':LIMIT,
        'scope':'Unsupported original custom-pad development input; two complete unchanged copies, same-load ' + observation + ' observation plus separate original-rule DRC. No routing/acceptance auditor, aliases, substitutions or source save.',
        'accounting_point':'Stored totals precede final publication; completed observations require final whole-run wall/parent+waited-child CPU and output caps. Polling can overshoot; no hard aggregate CPU quota.'}
    authorized=False;frozen=None;completed=None;stage_one=None;stage_two=None
    def account():
        record.update(steps=job.steps,wall_seconds=time.monotonic()-start,total_cpu_seconds=cpu()-cpu0,child_step_cpu_seconds=sum(x.get('cpu_seconds') or 0 for x in job.steps),monitor_cpu_seconds=sum(x.get('monitor_cpu_seconds') or 0 for x in job.steps),native_executed=bool(job.steps))
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS
        if not record['within_budget']:record.update(observations_complete=False,status='budget_exceeded')
    def stable():
        if not authorized:return
        observation_outputs(out,observation)
        if record.get('observation')!=observation or record.get('native_observation_mode')!=mode or record.get('dsn_export_requested') is not (mode=='export') or record.get('dsn_export_succeeded') is not (mode=='export' and stage_one is not None):raise p.Rejected('recorded observation selection differs')
        # Metadata executes Git. Rehash all trusted material after that call,
        # not merely before it, so mutations during metadata cannot be adopted.
        if frozen is not None and p.tool_manifest()!=record['tools']:raise p.Rejected('frozen core/tool/HEAD changed')
        if stage_one is not None:
            if any(sha_bytes(io.read_bytes(out/name,LIMIT))!=digest for name,digest in stage_one.items()):raise p.Rejected('stage-one observation evidence changed')
            if record.get('observation_sha256')!=stage_one['observation.json'] or record.get('native_dsn_sha256')!=stage_one.get('native.dsn'):raise p.Rejected('recorded raw observation digest differs')
            f.process_check(out,{'steps':job.steps},'observe',observe_argv(out,observation))
            if type(record.get('correspondence_verified')) is not bool:raise p.Rejected('malformed correspondence status')
            if record['correspondence_verified']:
                observed=observe_binding(out,hashes,notes,observation)
                if (record.get('custom_pad_observation')!=observed['custom_pad_observation'] or record.get('dsn_correspondence')!=observed['dsn_correspondence'] or record.get('native_effective_floors_nm')!=observed['floors_nm'] or record.get('native_effective_nets')!=observed['nets']):
                    raise p.Rejected('recorded observation differs from frozen raw evidence')
            if inventory(out/'observe-input')!=hashes:raise p.Rejected('observation source copy changed')
        if stage_two is not None:
            if any(sha_bytes(io.read_bytes(out/name,LIMIT))!=digest for name,digest in stage_two.items()):raise p.Rejected('stage-two native report evidence changed')
            if drc_binding(out,job.steps,hashes,record['native'])!=record['native_binding']:raise p.Rejected('recorded native binding differs from frozen raw evidence')
        if completed is not None:
            if record.get('correspondence_verified') is not True:raise p.Rejected('completed observation lacks verified correspondence')
            now={k:v for k,v in inventory(out).items() if k!='summary.json' and not k.startswith('invalidated-')}
            if now!=completed:raise p.Rejected('completed observation evidence changed')
            f.process_check(out,{'steps':job.steps},'observe',observe_argv(out,observation))
            if [step['name'] for step in job.steps]!=['observe','original-drc']:raise p.Rejected('unexpected completed native stage census')
        if sha_bytes(io.read_bytes(WRAPPER,4*1024*1024))!=WRAPPER_SHA:raise p.Rejected('native wrapper changed')
        if frozen is not None:
            if any(p.sha(Path(path))!=digest for path,digest in record['tools']['files'].items()):raise p.Rejected('runtime tool material changed')
            if inventory(out/'code')!=frozen or any(p.sha(ROOT/rel)!=digest for rel,digest in record['runtime_sources'].items()):raise p.Rejected('runtime core/helper changed')
        if inventory(SOURCE.parent)!=hashes or sha_bytes(io.read_bytes(RECEIPT,LIMIT))!=RECEIPT_SHA:raise p.Rejected('original source/acquisition changed')
    try:
        p.check_storage();hashes,total=source_binding();authorized=True
        try:p.preflight(SOURCE)
        except p.Rejected as exc:record['production_gate_rejection']=str(exc)
        else:raise p.Rejected('original unexpectedly productioneligible; re-review scope')
        if record['production_gate_rejection']!=EXPECTED_GATE:raise p.Rejected('original gate scope changed')
        notes=source_notes(sx.read(SOURCE),read(SOURCE.with_suffix('.kicad_pro')));record.update(source_hashes=hashes,source_bytes=total,source_file_count=len(hashes),source_notes=notes,acquisition_receipt_sha256=RECEIPT_SHA)
        record['native_wrapper_sha256']=WRAPPER_SHA
        if sha_bytes(io.read_bytes(WRAPPER,4*1024*1024))!=WRAPPER_SHA:raise p.Rejected('native wrapper changed')
        record['tools']=p.tool_manifest();record['runtime_sources']=snapshot(out,record['tools'],remaining);frozen=inventory(out/'code');record['code_inventory']=frozen
        reserve_copy(out,total,2);record['planned_project_copy_bytes']=2*total
        shutil.copytree(SOURCE.parent,out/'observe-input');stable()
        if inventory(out/'observe-input')!=hashes:raise p.Rejected('observation copy differs')
        board=out/'observe-input'/SOURCE.name;argv=observe_argv(out,observation)
        job.step('observe',argv,already_sandboxed=True)
        stage_one=dict(job.stage_evidence['observe'])
        # Export/process facts precede correspondence parsing. A mapping failure
        # must not erase a successfully emitted, frozen native artifact.
        record.update(dsn_export_succeeded=True,stage_one_evidence=stage_one,
            observation_sha256=stage_one['observation.json'],native_dsn_sha256=stage_one['native.dsn'])
        observed=observe_binding(out,hashes,notes,observation)
        f.process_check(out,{'steps':job.steps},'observe',argv)
        record.update(correspondence_verified=True,native_effective_floors_nm=observed['floors_nm'],native_effective_nets=observed['nets'],native_original_pad_route_identities_match=True,custom_pad_observation=observed['custom_pad_observation'],dsn_correspondence=observed['dsn_correspondence'])
        stable();reserve_copy(out,total,1)
        native=job.drc('original-drc',board,save=False);stage_two=dict(job.stage_evidence['original-drc']);record['stage_two_evidence']=stage_two
        record['native']=native;record['native_binding']=drc_binding(out,job.steps,hashes,native)
        record['central_native_rejection_reasons']=p.native_rejection_reasons(native);record['central_native_policy_accepted']=p.native_accepted(native)
        record['settings_observation']={'project_bytes_unchanged':True,'source_ignored_keys':sorted(k for k,v in notes['source_design_settings']['rule_severities'].items() if v=='ignore'),'native_ignored_keys':sorted(x['key'] for x in native['ignored_checks']),'source_exclusions':notes['source_design_settings']['drc_exclusions'],'native_exclusions':native['exclusions'],'native_severities_included':['error','warning','exclusion'],'drc_memory_refill_requested':True,'saved_fill_or_full_semantic_equivalence_observed':False}
        if inventory(out/'observe-input')!=hashes:raise p.Rejected('observation input changed')
        record.update(status='observations_complete',observations_complete=True,original_inputs_unchanged=True,output_bytes_before_summary=size(out))
        completed=inventory(out);record['completed_evidence']=completed
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',observations_complete=False,error=type(exc).__name__+': '+str(exc))
    return publish(out,record,stable,account,remaining)

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--run-native',action='store_true');ap.add_argument('--observation',choices=OBSERVATIONS,default='custom-pad-export');args=ap.parse_args(argv)
    if not args.run_native:ap.error('--run-native required; no native execution')
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in previous:signal.signal(sig,interrupted)
        with owned(ROOT/'.runs/quality-experiment.lock').open('a') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);record=experiment(args.output,run_native=True,observation=args.observation)
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
    print(json.dumps({'status':record['status'],'observations_complete':record['observations_complete'],'routing_accepted':False,'format_support_qualified':False}))
    return 0 if record['observations_complete'] else 2
if __name__=='__main__':raise SystemExit(main())
