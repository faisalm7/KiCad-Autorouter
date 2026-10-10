"""Explicit diagnostic placement/clearance/search routing; never a production receipt.

Reuses production floor guidance and final validation. Genuine rule-area
prohibitions are unsupported because current native keepout controls failed.
No runtime monkeypatch, engine work on import, or relaxation of source rules.
"""
from __future__ import annotations
import argparse,copy,datetime,fcntl,hashlib,json,math,resource,shutil,signal,subprocess,sys,time,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=next(x for x in HERE.parents if (x/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT),str(HERE)]
from autorouter import config as c,pipeline as p,sexpr as sx,board_floor as g,floor_route as f
import placement_transform as placement
import native_combined as observer
import search_guidance as search

POLICIES=tuple(search.PRESETS)
HELPERS=('diagnostic_route.py','native_combined.py','placement_transform.py','search_guidance.py','experiment_search.py','protocol.json')
OBSERVER_SHA='3fb123a8a1fdbe119a7de60e97677940e26a15b5562a822599d854ba04553a70'
TRANSFORM_SHA='bfd4ff85a92ad57a9908e46904e67b1d5fce65647689e489a566d6434260fdb5'


def owned(value):
    path=Path(value).absolute()
    if '..' in path.parts or not path.is_relative_to(ROOT) or any(x.is_symlink() for x in (path,*path.parents)):
        raise p.Rejected('real project-local path required')
    return path


def cpu():
    child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time()+child.ru_utime+child.ru_stime


def files(directory):
    inventory=p.tree_hash(directory)
    result={name:(directory/name).read_bytes() for name in inventory}
    if placement.inventory(result)!=inventory:raise p.Rejected('complete project byte snapshot changed')
    return result


def narrow_source(original):
    """Reject genuine/unqualified restrictions, independently of native DRC."""
    if sx.children(original,'module'):raise p.Rejected('legacy module alias outside diagnostic scope')
    placement.rectangle(original);rows=placement.source_zones(original)
    rule=[row for row in rows if row['is_rule_area']]
    if not rule:raise p.Rejected('diagnostic requires an enabled all-allowed placement area')
    if any(not row['placement_enabled'] or row['placement_source_type']!='SHEETNAME' or any(row['disallow'].values()) for row in rule):
        raise p.Rejected('genuine or disabled rule area outside native-qualified diagnostic scope')
    return rows


def protocol_contract():
    protocol=f.read_json(HERE/'protocol.json')
    expected={'schema':2,'fixed_order':list(POLICIES),'wall_seconds_per_arm':120,'cpu_seconds_per_arm':120,
        'final_shared_reserve_seconds':5,'profile':'completion-only','adapter':'both','strict_generated_dimensions':True,
        'search_parameters':[search.parameters(policy) for policy in POLICIES],
        'native_observer_sha256':OBSERVER_SHA,'placement_transform_sha256':TRANSFORM_SHA}
    if any(f.canonical(protocol.get(key))!=f.canonical(value) for key,value in expected.items()):raise p.Rejected('prospective search protocol differs from fixed runtime contract')
    if protocol.get('qualification_fixture',{}).get('required_policy')!=POLICIES[2]:raise p.Rejected('strongest same-code fixture policy required')
    return protocol


def freeze():
    protocol_contract()
    tools=p.tool_manifest();paths=[owned(HERE/name) for name in HELPERS]
    paths.extend(owned(ROOT/name) for name in tools['implementation_sha256']);paths.append(ROOT/'toolchain.lock.json')
    pinned={str(path.relative_to(ROOT)):p.sha(path) for path in paths}
    if p.sha(HERE/'placement_transform.py')!=TRANSFORM_SHA:raise p.Rejected('reviewed placement transform changed')
    if p.sha(HERE/'native_combined.py')!=OBSERVER_SHA:raise p.Rejected('reviewed combined observer changed')
    for relative,digest in pinned.items():
        raw=subprocess.run(['git','show',tools['git_head']+':'+relative],cwd=ROOT,capture_output=True,check=True,timeout=5).stdout
        if hashlib.sha256(raw).hexdigest()!=digest:raise p.Rejected('commit exact diagnostic/protocol/core sources before native routing')
    return {'tools':tools,'files_sha256':pinned,'protocol_sha256':p.sha(HERE/'protocol.json'),'helper_files':{name:str((HERE/name).relative_to(ROOT)) for name in HELPERS}}


def verify_freeze(frozen):
    if p.tool_manifest()!=frozen['tools'] or any(p.sha(owned(ROOT/name))!=digest for name,digest in frozen['files_sha256'].items()):
        raise p.Rejected('diagnostic code/tool/HEAD/protocol changed')


def combined_argv(directory,board):
    return [*f.SANDBOX,str(c.PYTHON),'-B',str(directory/'code/native_combined.py'),str(board),
            str(directory/'floor-export-context.json'),str(directory/'area-context.json'),str(directory/'native.dsn')]


def derive(directory,source_hashes,policy):
    """Rederive every source->native->floor->placement->planning-margin->both adapter byte step."""
    if policy not in POLICIES:raise p.Rejected('unknown diagnostic policy')
    original_files=files(directory/'snapshot');meta=f.read_json(directory/'route-meta.json');name=meta.get('board_name')
    if name not in original_files or meta.get('policy')!=policy:raise p.Rejected('diagnostic board/policy metadata differs')
    source=sx.parse(original_files[name].decode());narrow_source(source);task=g.task_from_source(source)
    task_bytes=(sx.dump(task)+'\n').encode();native_input=files(directory/'floor-export-input')
    expected=dict(source_hashes);expected[name]=g.sha(task_bytes)
    if placement.inventory(original_files)!=source_hashes or placement.inventory(native_input)!=expected:
        raise p.Rejected('original/export-task inventory differs')
    board=directory/'floor-export-input'/name;raw=(directory/'native.dsn').read_bytes()
    native=f.read_json(directory/'floor-export-context.json');areas=f.read_json(directory/'area-context.json')
    f.context_binding(native,board,expected,'export',g.sha(raw))
    if native.get('routes')!=[]:raise p.Rejected('export task retained routes')
    if (areas.get('source')!=str(board) or areas.get('limits')!=observer.AREA_LIMITS
            or areas.get('adapter_transformation_performed') is not False or areas.get('routing_accepted') is not False):
        raise p.Rejected('area observation path/cap/scope differs')
    # All arms share the identical bound native and placement transforms.
    placement.native_binding(original_files,native_input,name,areas,raw)
    project=original_files[name[:-10]+'.kicad_pro']
    guided,contract=f.policy_contract(raw,native,project,task,source_hashes)
    if (directory/'floor-guided.dsn').read_bytes()!=guided or f.canonical(f.read_json(directory/'floor-policy.json'))!=f.canonical(contract):
        raise p.Rejected('raw-to-floor guidance provenance differs')
    placed,removal=placement.transform(original_files,native_input,name,areas,raw,guided)
    if (directory/'placement-guided.dsn').read_bytes()!=placed or f.canonical(f.read_json(directory/'placement-transform.json'))!=f.canonical(removal):
        raise p.Rejected('placement transform bytes/receipt differ')
    context=g.qualify(json.loads(project),native,task)
    preadapter,planning=search.transform(placed,context,policy)
    if f.canonical(f.read_json(directory/'search-guidance.json'))!=f.canonical(planning):raise p.Rejected('search planning provenance differs')
    if (directory/'pre-adapter.dsn').read_bytes()!=preadapter:raise p.Rejected('pre-adapter DSN differs from declared policy')
    adapted=g.adapter_bytes(preadapter,native['obstacles'])
    if (directory/'task.dsn').read_bytes()!=adapted:raise p.Rejected('both adapter/engine input differs')
    return task,contract,{'native_dsn_sha256':g.sha(raw),'floor_guided_sha256':g.sha(guided),'pre_adapter_sha256':g.sha(preadapter),
        'task_dsn_sha256':g.sha(adapted),'placement_guided_sha256':g.sha(placed),'search_guidance_sha256':p.sha(directory/'search-guidance.json'),
        'placement_removed_count':removal['removed_count'],'search_parameters':search.parameters(policy),
        'floor_context_sha256':p.sha(directory/'floor-export-context.json'),'area_context_sha256':p.sha(directory/'area-context.json')}


def check_result(path):
    """Diagnostic consistency only; deliberately not production check-result."""
    path=owned(path);digest=p.sha(path);directory=path.parent;data=f.read_json(path)
    if (type(data.get('diagnostic_schema')) is not int or data.get('diagnostic_schema')!=2 or data.get('production_qualified') is not False or data.get('comparison_eligible') is not False
            or data.get('policy') not in POLICIES or data.get('engine_profile')!='completion-only' or data.get('adapter')!='both'):
        raise p.Rejected('not a scoped diagnostic receipt')
    if f.canonical(data.get('search_parameters'))!=f.canonical(search.parameters(data['policy'])):raise p.Rejected('declared search parameters differ')
    source=owned(data['source']);hashes=data['source_hashes'];candidate=directory/'candidate'/source.name
    if data.get('candidate')!=str(candidate) or p.tree_hash(source.parent)!=hashes or p.tree_hash(directory/'snapshot')!=hashes:
        raise p.Rejected('diagnostic source/snapshot/candidate identity changed')
    p.verify_candidate_files(candidate,hashes,data['candidate_sha256']);original=p.preflight(source);narrow_source(original)
    if p.immutable(sx.read(candidate))!=p.immutable(original):raise p.Rejected('diagnostic immutable source geometry changed')
    task,contract,chain=derive(directory,hashes,data['policy'])
    if chain!=data.get('chain'):raise p.Rejected('diagnostic chain summary changed')
    if data.get('evidence_hashes')!=f.evidence_inventory(directory):raise p.Rejected('completed diagnostic evidence changed')
    if data.get('freeze',{}).get('tools')!=data.get('tools'):raise p.Rejected('diagnostic tool freeze differs')
    # Source/code bytes are bound to their retained run, not a later HEAD.
    for name,digest_code in data['freeze']['files_sha256'].items():
        snapshot=directory/'code/source'/name
        if not snapshot.is_file() or p.sha(snapshot)!=digest_code:raise p.Rejected('frozen diagnostic code source changed')
    if data['observer_sha256']!=data['freeze']['files_sha256'][data['freeze']['helper_files']['native_combined.py']] or p.sha(directory/'code/native_combined.py')!=data['observer_sha256']:raise p.Rejected('executed observer snapshot changed')
    expected_names={'source-drc','floor-area-export','engine','import','refill-drc','floor-final','final-drc','metrics'}
    if len(data.get('steps',[]))!=len(expected_names) or {x.get('name') for x in data['steps']}!=expected_names:raise p.Rejected('diagnostic stage inventory differs')
    f.process_check(directory,data,'floor-area-export',combined_argv(directory,directory/'floor-export-input'/source.name))
    settings=p.engine_profile_settings('completion-only',data['engine_budget']['remaining_outer_wall_seconds_at_assignment'],strict_class_targets=True,scoring_variant=search.parameters(data['policy'])['scoring_variant'])
    settings.update(outer_task_wall_budget_seconds=data['budget_seconds'],outer_task_cpu_budget_seconds=data['cpu_budget_seconds'])
    if settings!=data['engine_budget']:raise p.Rejected('diagnostic engine settings differ')
    f.process_check(directory,data,'engine',f.engine_argv(directory,settings['argv']))
    for name,action,target,extra in [('import','import',directory/'imported.kicad_pcb',[directory/'routes.ses']),('metrics','metrics',directory/'metrics.json',[])]:
        f.process_check(directory,data,name,[*f.SANDBOX,str(c.PYTHON),str(ROOT/'autorouter/native.py'),action,str(candidate),str(target),*[str(x)for x in extra]])
    f.audit_transport(directory,data,task,candidate)
    f.validate_contract(original,candidate,hashes,[],contract,directory)
    final_map=f.read_json(directory/'floor-final-context.json');expected=dict(hashes);expected[source.name]=data['candidate_sha256']
    f.context_binding(final_map,candidate,expected,'final');qualified=g.qualify(json.loads(candidate.with_suffix('.kicad_pro').read_text()),final_map,task)
    audit={'candidate_sha256':p.sha(candidate),'native_context_sha256':p.sha(directory/'floor-final-context.json'),
           'generated':g.audit_generated_routes(sx.read(candidate),qualified),'native_routes':g.audit_native_routes(sx.read(candidate),final_map)}
    if f.read_json(directory/'floor-final-audit.json')!=audit:raise p.Rejected('final original floor/route audit differs')
    f.process_check(directory,data,'floor-final',f.context_argv('final',candidate,directory/'floor-final-context.json'))
    raw=directory/'final-drc.json';native=p.parse_report(raw,source.name)
    if p.sha(raw)!=data['native_report_sha256'] or native!=data['native']:raise p.Rejected('final raw native report changed')
    binding=f.read_json(directory/'final-drc-binding.json');native_input=directory/'final-drc-input'/source.name;after=binding.get('after')
    if (binding.get('source')!=str(candidate) or binding.get('input')!=str(native_input) or binding.get('saved') is not False or binding.get('before')!=expected
            or not isinstance(after,dict) or any(after.get(k)!=v for k,v in expected.items()) or set(after)-set(expected)-{source.with_suffix('.kicad_prl').name}
            or p.tree_hash(native_input.parent)!=after):raise p.Rejected('final native input/source rules differ')
    argv=[*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(raw),str(native_input)]
    f.process_check(directory,data,'final-drc',argv,allowed=(5 if native['findings'] else 0,))
    final_step=next(x for x in data['steps'] if x['name']=='final-drc')
    if final_step.get('validated_input_sha256')!=data['candidate_sha256'] or final_step.get('emitted_candidate')!=str(candidate):raise p.Rejected('final native step/candidate binding differs')
    metrics=f.read_json(directory/'metrics.json')
    if metrics!=data['metrics'] or metrics.get('version')!='10.0.0':raise p.Rejected('diagnostic metrics differ')
    valid=audit_accounting(data)
    if p.sha(path)!=digest:raise p.Rejected('diagnostic receipt changed while checking')
    return {'diagnostic_verified':True,'routing_accepted':valid,'production_qualified':False}


def audit_accounting(data):
    for key in ('budget_seconds','cpu_budget_seconds','wall_seconds','total_cpu_seconds','parent_cpu_seconds','waited_child_cpu_seconds'):
        if isinstance(data.get(key),bool) or not isinstance(data.get(key),(int,float)) or not math.isfinite(data[key]) or data[key]<0:raise p.Rejected('invalid diagnostic accounting')
    if not 50<=data['budget_seconds']<=120 or data['cpu_budget_seconds']!=data['budget_seconds']:raise p.Rejected('diagnostic budget contract differs')
    if abs(data['total_cpu_seconds']-data['parent_cpu_seconds']-data['waited_child_cpu_seconds'])>1e-7:raise p.Rejected('diagnostic CPU accounting sum differs')
    for step in data['steps']:
        for key in ('cpu_seconds','monitor_cpu_seconds'):
            value=step.get(key)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:raise p.Rejected('invalid process CPU accounting')
    if data['waited_child_cpu_seconds']+1e-6<sum((step.get('cpu_seconds')or 0)+(step.get('monitor_cpu_seconds')or 0) for step in data['steps']):raise p.Rejected('diagnostic child CPU undercount')
    valid=p.native_accepted(data['native']) and data['wall_seconds']<=data['budget_seconds'] and data['total_cpu_seconds']<=data['cpu_budget_seconds']
    if data.get('routing_accepted') is not valid or (valid and data.get('status')!='diagnostic_accepted') or (not valid and data.get('status') not in {'drc_rejected','budget_exceeded','cancelled','invalidated'}):raise p.Rejected('diagnostic acceptance/status contradicts native/budget outcome')
    return valid


def route(source,out,seconds,policy):
    if policy not in POLICIES or isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 50<=seconds<=120:
        raise p.Rejected('diagnostic policy and 50..120 second budget required')
    started=time.monotonic();parent0=time.process_time();r0=resource.getrusage(resource.RUSAGE_CHILDREN);child0=r0.ru_utime+r0.ru_stime;cpu0=parent0+child0;source=owned(source);out=owned(out)
    if out.exists() or not (ROOT/'.runs') in out.parents or source.parent in out.parents:raise p.Rejected('fresh separate .runs output required')
    def remaining():return max(0,min(started+seconds-time.monotonic(),seconds-(cpu()-cpu0)))
    job=f.FloorJob(out,seconds,remaining)
    record={'diagnostic_schema':2,'status':'rejected','routing_accepted':False,'production_qualified':False,'comparison_eligible':False,
            'source':str(source),'policy':policy,'search_parameters':search.parameters(policy),'budget_seconds':seconds,'cpu_budget_seconds':seconds,'engine_profile':'completion-only','adapter':'both',
            'scope':'whole original project; diagnostic all-allowed placement only; no genuine rule-area restrictions',
            'physical_electrical_validation':False,'steps':job.steps,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    frozen=None;hashes=None;completed=None
    def stable():
        if frozen is None:return
        verify_freeze(frozen)
        if p.tree_hash(source.parent)!=hashes or p.tree_hash(out/'snapshot')!=hashes:raise p.Rejected('diagnostic source changed')
        if completed is not None and f.evidence_inventory(out)!=completed:raise p.Rejected('completed diagnostic evidence changed')
    def account():
        child=resource.getrusage(resource.RUSAGE_CHILDREN);parent_delta=time.process_time()-parent0;child_delta=child.ru_utime+child.ru_stime-child0
        record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=parent_delta+child_delta,parent_cpu_seconds=parent_delta,waited_child_cpu_seconds=child_delta,child_step_cpu_seconds=sum(x.get('cpu_seconds')or 0 for x in job.steps),
                      monitor_cpu_seconds=sum(x.get('monitor_cpu_seconds')or 0 for x in job.steps),peak_child_rss_bytes=max([x.get('max_rss_bytes')or 0 for x in job.steps]+[0]))
        record['within_budget']=record['wall_seconds']<=seconds and record['total_cpu_seconds']<=seconds
        if not record['within_budget']:record.update(routing_accepted=False,status='budget_exceeded')
        if any(x.get('status')=='cancelled' for x in job.steps):record.update(routing_accepted=False,status='cancelled')
    try:
        p.check_storage();original=p.preflight(source);narrow_source(original);task=g.task_from_source(original)
        hashes=p.tree_hash(source.parent);shutil.copytree(source.parent,out/'snapshot');shutil.copytree(source.parent,out/'candidate')
        frozen=freeze();record.update(freeze=frozen,tools=frozen['tools'],source_hashes=hashes)
        (out/'code').mkdir()
        for name,digest_code in frozen['files_sha256'].items():
            dest=out/'code/source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
            if p.sha(dest)!=digest_code:raise p.Rejected('diagnostic source changed during snapshot')
        shutil.copy2(HERE/'native_combined.py',out/'code/native_combined.py');record['observer_sha256']=p.sha(out/'code/native_combined.py')
        p.save_json(out/'route-meta.json',{'board_name':source.name,'policy':policy});stable()
        candidate=out/'candidate'/source.name;sx.write(candidate,task);shutil.copytree(candidate.parent,out/'floor-export-input')
        record['source_drc']=job.drc('source-drc',out/'snapshot'/source.name)
        job.step('floor-area-export',combined_argv(out,out/'floor-export-input'/source.name),already_sandboxed=True)
        native=f.read_json(out/'floor-export-context.json');raw=(out/'native.dsn').read_bytes()
        guided,contract=f.policy_contract(raw,native,source.with_suffix('.kicad_pro').read_bytes(),task,hashes)
        (out/'floor-guided.dsn').write_bytes(guided);p.save_json(out/'floor-policy.json',contract)
        placed,removal=placement.transform(files(out/'snapshot'),files(out/'floor-export-input'),source.name,f.read_json(out/'area-context.json'),raw,guided)
        (out/'placement-guided.dsn').write_bytes(placed);p.save_json(out/'placement-transform.json',removal)
        context=g.qualify(json.loads(source.with_suffix('.kicad_pro').read_text()),native,task)
        preadapter,planning=search.transform(placed,context,policy);p.save_json(out/'search-guidance.json',planning)
        (out/'pre-adapter.dsn').write_bytes(preadapter);(out/'task.dsn').write_bytes(g.adapter_bytes(preadapter,native['obstacles']))
        _,_,record['chain']=derive(out,hashes,policy);stable();(out/'engine-config').mkdir()
        settings=p.engine_profile_settings('completion-only',remaining(),strict_class_targets=True,scoring_variant=search.parameters(policy)['scoring_variant'])
        settings.update(outer_task_wall_budget_seconds=seconds,outer_task_cpu_budget_seconds=seconds);record['engine_budget']=settings
        job.step('engine',f.engine_argv(out,settings['argv']),already_sandboxed=True)
        imported=out/'imported.kicad_pcb';job.native('import','import',candidate,imported,out/'routes.ses')
        sx.write(candidate,p.transplant_routes(task,sx.read(imported)))
        final,native=p.validate_candidate(job,original,candidate,hashes,[],guidance_contract=contract)
        job.native('metrics','metrics',candidate,out/'metrics.json');p.verify_candidate_files(candidate,hashes,final)
        record.update(candidate=str(candidate),candidate_sha256=final,native=native,native_report_sha256=p.sha(out/'final-drc.json'),
                      metrics=f.read_json(out/'metrics.json'),routing_accepted=p.native_accepted(native),status='diagnostic_accepted' if p.native_accepted(native) else 'drc_rejected')
        completed=f.evidence_inventory(out);record['evidence_hashes']=completed
    except KeyboardInterrupt:record.update(status='cancelled',routing_accepted=False)
    except Exception as exc:record.update(status='rejected',routing_accepted=False,error=type(exc).__name__+': '+str(exc))
    record['accounting_point']='Stored totals precede final publication/readback/freshness; final acceptance wall/CPU caps include all checks; correction may finish outside cap.'
    return publish_result(out,record,stable,account,remaining)



def publish_result(out,record,stable,account,remaining,checker=check_result):
    """Canonical publication; never leave a positive receipt after correction failure."""
    def archive():
        for name in ('result.json','result.json.partial'):
            path=out/name
            if path.exists():path.rename(out/('invalidated-result-'+uuid.uuid4().hex+'-'+name))
    try:
        stable();account();expected=f.canonical(record);p.save_json(out/'result.json',record)
        if f.canonical(f.read_json(out/'result.json'))!=expected:raise p.Rejected('diagnostic receipt changed on write')
        if 'native' in record:checker(out/'result.json')
        stable()
        if f.canonical(f.read_json(out/'result.json'))!=expected:raise p.Rejected('diagnostic receipt changed during readback')
        if remaining()<=0:raise p.Rejected('diagnostic final publication exceeded budget')
    except (Exception,KeyboardInterrupt) as exc:
        archive();record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',routing_accepted=False,error=type(exc).__name__+': '+str(exc));account()
        try:p.save_json(out/'result.json',record)
        except (Exception,KeyboardInterrupt):archive()
    return record

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path);parser.add_argument('--output',type=Path);parser.add_argument('--check-result',type=Path)
    parser.add_argument('--seconds',type=float,default=60);parser.add_argument('--policy',choices=POLICIES,default=POLICIES[2]);parser.add_argument('--run-diagnostic',action='store_true');args=parser.parse_args(argv)
    if args.check_result is not None:
        if args.run_diagnostic or args.source or args.output:parser.error('--check-result cannot be combined with routing arguments')
        print(json.dumps(check_result(args.check_result)));return 0
    if not args.run_diagnostic or args.source is None or args.output is None:parser.error('--run-diagnostic, --source and --output required; no native work executed')
    handlers={sig:signal.getsignal(sig)for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in handlers:signal.signal(sig,interrupted)
        with owned(ROOT/'.runs/quality-experiment.lock').open('a') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            result=route(args.source,args.output,args.seconds,args.policy)
    finally:
        for sig,handler in handlers.items():signal.signal(sig,handler)
    print(json.dumps({'status':result['status'],'routing_accepted':result['routing_accepted'],'production_qualified':False}))
    return 0 if result['routing_accepted'] else 1
if __name__=='__main__':raise SystemExit(main())
