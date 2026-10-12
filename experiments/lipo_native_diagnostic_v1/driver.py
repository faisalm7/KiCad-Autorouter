"""Bounded finite original-source A/B observations; never routes or saves a board.

Only the lead may execute with --run-native after tracked promotion/checkpoint.
Successful observations do not qualify old-format routing or dependency closure.
"""
from __future__ import annotations
import argparse,fcntl,hashlib,json,resource,shutil,signal,subprocess,sys,time,uuid
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import config as c,pipeline as p,sexpr as sx,floor_route as f,placement_clearance as io
from autorouter.runner import run
from dataclasses import replace
import source_profiles as profiles
SOURCE=ROOT/'.data/expansion003/lipo-disconnector/lipo_disconnector.kicad_pcb'
RECEIPT=ROOT/'.runs/licensed-acquisition-003/lipo-disconnector-001/receipt.json'
RECEIPT_SHA='b57bc2ce29d7c5e45939fbf917896d02536b357e8b5a08c04828dd8305107c27'
BOARD_SHA='3ef2141230ce971115381107486892bdf06a724c5d31d9ef2103622e113cf4e0'
PROJECT_SHA='8bc2dc577fb98404f317730b10ba2945f213a14e212b7a0b3e7fba7943a8d95e'
SECONDS=30;LIMIT=20*1024*1024;RESERVE=1024*1024
HELPERS=('driver.py','test_driver.py','source_profiles.py','README.md')
OBSERVATIONS=('export','context-only')

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

def source_spec(source_profile='lipo'):
    try:spec=profiles.select(source_profile,ROOT)
    except ValueError as exc:raise p.Rejected(str(exc)) from exc
    # Preserve legacy public constants/test seams; they remain committed code,
    # never user-supplied paths. The new profile has no path override surface.
    if source_profile=='lipo':
        spec=replace(spec,source=SOURCE,receipt=RECEIPT,receipt_sha256=RECEIPT_SHA,
                     board_sha256=BOARD_SHA,project_sha256=PROJECT_SHA)
    return spec

def source_binding(source_profile='lipo'):
    spec=source_spec(source_profile);source,receipt_path=spec.source,spec.receipt
    owned(source);owned(receipt_path)
    if sha_bytes(io.read_bytes(receipt_path))!=spec.receipt_sha256:raise p.Rejected('acquisition receipt changed')
    receipt=read(receipt_path)
    if receipt.get('status')!='acquired_unqualified' or receipt.get('split')!='development':raise p.Rejected('acquisition scope changed')
    if spec.acquisition_project is not None and receipt.get('project')!=spec.acquisition_project:raise p.Rejected('acquisition project differs')
    if spec.acquisition_protocol is not None and receipt.get('protocol_sha256')!=spec.acquisition_protocol:raise p.Rejected('acquisition protocol differs')
    expected={};total=0
    for row in receipt['files']:
        path=owned(ROOT/row['local_path'])
        if not path.is_relative_to(source.parent):raise p.Rejected('acquisition path outside source')
        name=str(path.relative_to(source.parent))
        if name in expected:raise p.Rejected('duplicate acquired path')
        raw=io.read_bytes(path,LIMIT-total);total+=len(raw)
        if len(raw)!=row['bytes'] or sha_bytes(raw)!=row['sha256'] or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=row['git_blob_sha1']:raise p.Rejected('acquired source blob differs')
        expected[name]=row['sha256']
    if len(expected)!=spec.files or total!=spec.bytes or inventory(source.parent)!=expected or expected.get(source.name)!=spec.board_sha256 or expected.get(source.with_suffix('.kicad_pro').name)!=spec.project_sha256:raise p.Rejected('complete acquired source inventory differs')
    return expected,total

def source_notes(board,project,source_profile='lipo'):
    spec=source_spec(source_profile)
    if sx.one(board,'version')!=['version',spec.board_format]:raise p.Rejected('not pinned original format')
    pads=[];netnames={int(n[1]):sx.unquote(n[2]) for n in sx.children(board,'net')}
    for fp in sx.children(board,'footprint'):
        refs=[x for x in sx.children(fp,spec.reference_kind) if len(x)>2 and sx.unquote(x[1])==('reference' if spec.reference_kind=='fp_text' else 'Reference')]
        if len(refs)!=1:raise p.Rejected('ambiguous original reference')
        for pad in sx.children(fp,'pad'):
            identifier=sx.one(pad,spec.pad_id);net=sx.one(pad,'net');code=int(net[1]) if net else 0
            if identifier is None or len(identifier)!=2:raise p.Rejected('missing original pad '+spec.pad_id)
            pads.append({'uuid':sx.unquote(identifier[1]),'reference':sx.unquote(refs[0][2]),'number':sx.unquote(pad[1]),'net':netnames.get(code,'')})
    zones=[[x for x in z if not isinstance(x,list) or not x or x[0] not in p.DERIVED_ZONE] for z in sx.children(board,'zone')]
    route_ids=[sx.unquote(sx.one(x,spec.pad_id)[1]) for x in p.routes(board)]
    if (len(pads),len(zones),len(route_ids),len(sx.children(board,'footprint')),sum(bool(x) for x in netnames.values()))!=(spec.pads,spec.zones,spec.routes,spec.footprints,spec.nets):raise p.Rejected('original census changed')
    if len({x['uuid'] for x in pads})!=len(pads) or len(set(route_ids))!=len(route_ids):raise p.Rejected('ambiguous original pad/route identity')
    return {'format':spec.board_format,'source_pads_identity':pads,'source_nonempty_nets':sorted(x for x in netnames.values() if x),
        'source_route_ids':sorted(route_ids),
        'source_zone_intent_ast':zones,'zone_intent_observation':'Static original AST only; native zone/teardrop reinterpretation and migration are unobserved.',
        'source_design_settings':project['board']['design_settings'],'source_net_settings':project['net_settings'],'source_meta':project['meta'],
        'unobserved_native_semantics':['full footprint/pad/drill geometry','edge arcs and stackup','all original zone/layer/legacy teardrop intent','save/refill serialization','import/route transplantation','library and model resolution'],
        'dependency_complete':False,'format_support_qualified':False}

def observation_mode(observation):
    if observation not in OBSERVATIONS:raise p.Rejected('unknown observation mode')
    return 'export' if observation=='export' else 'final'

def observe_argv(out,observation='export',source_profile='lipo'):
    mode=observation_mode(observation);board=out/'observe-input'/source_spec(source_profile).source.name
    return f.context_argv(mode,board,out/'observation.json',out/'native.dsn' if mode=='export' else None)

def observation_outputs(out,observation):
    mode=observation_mode(observation);dsn=out/'native.dsn'
    if mode=='final' and (dsn.exists() or dsn.is_symlink()):raise p.Rejected('unexpected DSN in context-only observation')
    return ['observation.json','native.dsn'] if mode=='export' else ['observation.json']

def observe_binding(out,hashes,notes,observation='export',source_profile='lipo'):
    board=out/'observe-input'/source_spec(source_profile).source.name;observed=read(out/'observation.json');dsn=out/'native.dsn'
    mode=observation_mode(observation);observation_outputs(out,observation)
    if mode=='export' and not 0<len(io.read_bytes(dsn,LIMIT))<=LIMIT:raise p.Rejected('empty native DSN')
    f.context_binding(observed,board,hashes,mode,p.sha(dsn) if mode=='export' else None)
    if observed.get('context_schema')!=1 or observed.get('native_version')!='10.0.0' or observed.get('units')!='integer nanometres' or observed.get('routing_accepted') is not False:raise p.Rejected('unexpected observation schema')
    native_pads=[{k:r[k] for k in ('uuid','reference','number','net')} for r in observed['pads']]
    key=lambda row:row['uuid']
    if len({x['uuid'] for x in native_pads})!=len(native_pads) or sorted(native_pads,key=key)!=sorted(notes['source_pads_identity'],key=key):raise p.Rejected('native original terminal identities differ')
    if sorted(x['uuid'] for x in observed['routes'])!=notes['source_route_ids'] or sorted(x['name'] for x in observed['nets'])!=notes['source_nonempty_nets']:raise p.Rejected('native original route/net identities differ')
    return observed

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
    def __init__(self,out,seconds,remaining,observation='export',source_profile='lipo'):
        observation_mode(observation);source_spec(source_profile);self.observation=observation;self.source_profile=source_profile
        super().__init__(out,seconds,remaining);self.stage_evidence={}
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        actual=[str(x) for x in (argv if already_sandboxed else [*f.SANDBOX,*argv])]
        profile=getattr(self,'source_profile','lipo')
        expected=observe_argv(self.out,self.observation,profile) if name=='observe' else drc_argv(self.out,profile)
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

def drc_argv(out,source_profile='lipo'):
    return [*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(out/'original-drc.json'),str(out/'original-drc-input'/source_spec(source_profile).source.name)]

def drc_binding(out,steps,hashes,native,source_profile='lipo'):
    source=source_spec(source_profile).source
    board=out/'observe-input'/source.name;target=out/'original-drc-input'/source.name;binding=read(out/'original-drc-binding.json')
    if binding.get('source')!=str(board) or binding.get('input')!=str(target) or binding.get('saved') is not False or binding.get('before')!=hashes:raise p.Rejected('DRC input binding differs')
    after=binding['after']
    if any(after.get(k)!=v for k,v in hashes.items()) or set(after)-set(hashes)-{target.with_suffix('.kicad_prl').name} or inventory(target.parent)!=after:raise p.Rejected('DRC changed copied original/rules')
    expected=drc_argv(out,source_profile)
    f.process_check(out,{'steps':steps},'original-drc',expected,allowed=(5 if native['findings'] else 0,))
    if p.parse_report(out/'original-drc.json',source.name)!=native:raise p.Rejected('raw DRC summary differs')
    return {'board_sha256':p.sha(target),'project_sha256':p.sha(target.with_suffix('.kicad_pro')),'report_sha256':p.sha(out/'original-drc.json'),'binding_sha256':p.sha(out/'original-drc-binding.json')}

def publish(out,record,stable,account,remaining):
    path=out/'summary.json'
    def invalidate():
        for candidate in (path,out/'summary.json.partial'):
            if candidate.exists():candidate.rename(out/('invalidated-'+uuid.uuid4().hex+'-'+candidate.name))
    try:
        stable();account();expected=f.canonical(record);p.save_json(path,record)
        if f.canonical(read(path))!=expected:raise p.Rejected('summary changed afterwrite')
        final_size=size(out)
        stable()
        if f.canonical(read(path))!=expected or f.canonical(record)!=expected or final_size>LIMIT or remaining()<=0:raise p.Rejected('summary stale or final resourcecap exceeded')
    except (Exception,KeyboardInterrupt) as exc:
        invalidate();record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',observations_complete=False,original_inputs_unchanged=None,error=record.get('error',type(exc).__name__+': '+str(exc)),finalization_error=type(exc).__name__+': '+str(exc),routing_accepted=False,format_support_qualified=False,dependency_complete=False);account()
        try:p.save_json(path,record)
        except (Exception,KeyboardInterrupt):invalidate()
    return record

def experiment(out,*,run_native=False,observation='export',source_profile='lipo'):
    if run_native is not True:raise p.Rejected('--run-native required')
    mode=observation_mode(observation);spec=source_spec(source_profile);source=spec.source
    start=time.monotonic();cpu0=cpu();out=owned(out,output=True)
    remaining=lambda:max(0,min(SECONDS-(time.monotonic()-start),SECONDS-(cpu()-cpu0)))
    job=ObservationJob(out,SECONDS,remaining,observation,source_profile)
    record={'schema':1,'status':'incomplete','observations_complete':False,'routing_accepted':False,'dependency_complete':False,'format_support_qualified':False,
        'observation':observation,'native_observation_mode':mode,'dsn_export_requested':mode=='export','dsn_export_succeeded':False,'native_dsn_sha256':None,
        'semantic_migration_performed':False,'board_saved':False,'new_engine_execution':False,'source':str(source),'source_profile':source_profile,'source_spec':spec.record(),'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_ceiling_bytes':LIMIT,
        'scope':'Unsupported original-format development input; two complete unchanged copies, same-load ' + observation + ' observation plus separate original-rule DRC. No routing/acceptance auditor, aliases, substitutions or source save.',
        'accounting_point':'Stored totals precede final publication; completed observations require final whole-run wall/parent+waited-child CPU and output caps. Polling can overshoot; no hard aggregate CPU quota.'}
    authorized=False;frozen=None;completed=None;stage_one=None;stage_two=None;observation_validated=False
    def account():
        record.update(steps=job.steps,wall_seconds=time.monotonic()-start,total_cpu_seconds=cpu()-cpu0,child_step_cpu_seconds=sum(x.get('cpu_seconds') or 0 for x in job.steps),monitor_cpu_seconds=sum(x.get('monitor_cpu_seconds') or 0 for x in job.steps),native_executed=bool(job.steps))
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS
        if not record['within_budget']:record.update(observations_complete=False,status='budget_exceeded')
    def stable():
        if not authorized:return
        observation_outputs(out,observation)
        if record.get('source')!=str(source) or record.get('source_profile')!=source_profile or record.get('source_spec')!=spec.record() or source_spec(source_profile)!=spec:raise p.Rejected('recorded source profile differs')
        if 'production_gate_rejection' in record and record['production_gate_rejection']!=spec.gate_rejection:raise p.Rejected('recorded original gate scope differs')
        if record.get('observation')!=observation or record.get('native_observation_mode')!=mode or record.get('dsn_export_requested') is not (mode=='export') or record.get('dsn_export_succeeded') is not (mode=='export' and stage_one is not None):raise p.Rejected('recorded observation selection differs')
        # Metadata executes Git. Rehash all trusted material after that call,
        # not merely before it, so mutations during metadata cannot be adopted.
        if frozen is not None and p.tool_manifest()!=record['tools']:raise p.Rejected('frozen core/tool/HEAD changed')
        if stage_one is not None:
            if any(sha_bytes(io.read_bytes(out/name,LIMIT))!=digest for name,digest in stage_one.items()):raise p.Rejected('stage-one observation evidence changed')
            if (record.get('stage_one_evidence')!=stage_one or record.get('observation_sha256')!=stage_one['observation.json']
                    or record.get('native_dsn_sha256')!=stage_one.get('native.dsn') or record.get('native_original_pad_route_identities_match') is not observation_validated):raise p.Rejected('recorded export/capture facts differ')
            if observation_validated:
                observed=observe_binding(out,hashes,notes,observation,source_profile)
            if observation_validated and (record.get('native_effective_floors_nm')!=observed['floors_nm'] or record.get('native_effective_nets')!=observed['nets']):
                raise p.Rejected('recorded observation differs from frozen raw evidence')
            if inventory(out/'observe-input')!=hashes:raise p.Rejected('observation source copy changed')
        if stage_two is not None:
            if any(sha_bytes(io.read_bytes(out/name,LIMIT))!=digest for name,digest in stage_two.items()):raise p.Rejected('stage-two native report evidence changed')
            if drc_binding(out,job.steps,hashes,record['native'],source_profile)!=record['native_binding']:raise p.Rejected('recorded native binding differs from frozen raw evidence')
        if completed is not None:
            now={k:v for k,v in inventory(out).items() if k!='summary.json' and not k.startswith('invalidated-')}
            if now!=completed:raise p.Rejected('completed observation evidence changed')
            f.process_check(out,{'steps':job.steps},'observe',observe_argv(out,observation,source_profile))
            if [step['name'] for step in job.steps]!=['observe','original-drc']:raise p.Rejected('unexpected completed native stage census')
        if frozen is not None:
            if any(p.sha(Path(path))!=digest for path,digest in record['tools']['files'].items()):raise p.Rejected('runtime tool material changed')
            if inventory(out/'code')!=frozen or any(p.sha(ROOT/rel)!=digest for rel,digest in record['runtime_sources'].items()):raise p.Rejected('runtime core/helper changed')
        if inventory(source.parent)!=hashes or sha_bytes(io.read_bytes(spec.receipt,LIMIT))!=spec.receipt_sha256:raise p.Rejected('original source/acquisition changed')
    try:
        p.check_storage();hashes,total=source_binding(source_profile);authorized=True
        try:p.preflight(source)
        except p.Rejected as exc:record['production_gate_rejection']=str(exc)
        else:raise p.Rejected('original unexpectedly productioneligible; re-review scope')
        if record['production_gate_rejection']!=spec.gate_rejection:raise p.Rejected('original gate scope changed')
        notes=source_notes(sx.read(source),read(source.with_suffix('.kicad_pro')),source_profile);record.update(source_hashes=hashes,source_bytes=total,source_file_count=len(hashes),source_notes=notes,acquisition_receipt_sha256=spec.receipt_sha256)
        record['tools']=p.tool_manifest();record['runtime_sources']=snapshot(out,record['tools'],remaining);frozen=inventory(out/'code');record['code_inventory']=frozen
        reserve_copy(out,total,2);record['planned_project_copy_bytes']=2*total
        shutil.copytree(source.parent,out/'observe-input');stable()
        if inventory(out/'observe-input')!=hashes:raise p.Rejected('observation copy differs')
        board=out/'observe-input'/source.name;argv=observe_argv(out,observation,source_profile)
        job.step('observe',argv,already_sandboxed=True)
        stage_one=dict(job.stage_evidence['observe'])
        record.update(dsn_export_succeeded=mode=='export',stage_one_evidence=stage_one,observation_sha256=stage_one['observation.json'],native_dsn_sha256=stage_one.get('native.dsn'),native_original_pad_route_identities_match=False)
        observed=observe_binding(out,hashes,notes,observation,source_profile)
        f.process_check(out,{'steps':job.steps},'observe',argv)
        record.update(dsn_export_succeeded=mode=='export',stage_one_evidence=stage_one,observation_sha256=stage_one['observation.json'],native_dsn_sha256=stage_one.get('native.dsn'),native_effective_floors_nm=observed['floors_nm'],native_effective_nets=observed['nets'],native_original_pad_route_identities_match=True)
        observation_validated=True
        stable();reserve_copy(out,total,1)
        native=job.drc('original-drc',board,save=False);stage_two=dict(job.stage_evidence['original-drc']);record['stage_two_evidence']=stage_two
        record['native']=native;record['native_binding']=drc_binding(out,job.steps,hashes,native,source_profile)
        record['central_native_rejection_reasons']=p.native_rejection_reasons(native);record['central_native_policy_accepted']=p.native_accepted(native)
        record['settings_observation']={'project_bytes_unchanged':True,'source_ignored_keys':sorted(k for k,v in notes['source_design_settings']['rule_severities'].items() if v=='ignore'),'native_ignored_keys':sorted(x['key'] for x in native['ignored_checks']),'source_exclusions':notes['source_design_settings']['drc_exclusions'],'native_exclusions':native['exclusions'],'native_severities_included':['error','warning','exclusion'],'drc_memory_refill_requested':True,'saved_fill_or_full_semantic_equivalence_observed':False,'all_original_severity_enforcement_qualified':False}
        if inventory(out/'observe-input')!=hashes:raise p.Rejected('observation input changed')
        record.update(status='observations_complete',observations_complete=True,original_inputs_unchanged=True,output_bytes_before_summary=size(out))
        completed=inventory(out);record['completed_evidence']=completed
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',observations_complete=False,error=type(exc).__name__+': '+str(exc))
    return publish(out,record,stable,account,remaining)

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--run-native',action='store_true');ap.add_argument('--observation',choices=OBSERVATIONS,default='export');ap.add_argument('--source-profile',choices=profiles.NAMES,default='lipo');args=ap.parse_args(argv)
    if not args.run_native:ap.error('--run-native required; no native execution')
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in previous:signal.signal(sig,interrupted)
        with owned(ROOT/'.runs/quality-experiment.lock').open('a') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);record=experiment(args.output,run_native=True,observation=args.observation,**({'source_profile':args.source_profile} if args.source_profile!='lipo' else {}))
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
    print(json.dumps({'status':record['status'],'observations_complete':record['observations_complete'],'routing_accepted':False,'format_support_qualified':False}))
    return 0 if record['observations_complete'] else 2
if __name__=='__main__':raise SystemExit(main())
