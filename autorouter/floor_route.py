"""Explicit direct-route board-floor correction and bound evidence verification.

No strategy, portfolio, recovery or handoff support is implied by this policy.
"""
from __future__ import annotations
import copy
import datetime
import json
import math
import os
from pathlib import Path
import resource
import shutil
import signal
import time
import uuid
from . import pipeline as p, config as c, sexpr as sx, board_floor as g
from .floor_context import LIMITS

POLICY='board-floors-v1'
PLACEMENT_POLICY='placement-clearance-v1'
SEARCH_POLICY='placement-search-v1'
PLACEMENT_POLICIES={PLACEMENT_POLICY,SEARCH_POLICY}
GUIDANCE_POLICIES={POLICY,*PLACEMENT_POLICIES}
SANDBOX=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)']


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def read_json(path):
    path=Path(path)
    if path.is_symlink() or path.stat().st_size>sx.MAX_BYTES:raise p.Rejected('invalid bounded floor evidence')
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise p.Rejected('duplicate JSON field')
            result[key]=value
        return result
    def constant(value):raise p.Rejected('invalid resource accounting: nonfinite JSON value')
    from .placement_clearance import read_bytes
    return json.loads(read_bytes(path),object_pairs_hook=pairs,parse_constant=constant)


def child_cpu():
    value=resource.getrusage(resource.RUSAGE_CHILDREN)
    return value.ru_utime+value.ru_stime


def evidence_markers(directory):
    markers=set()
    with os.scandir(directory) as entries:
        for count,entry in enumerate(entries,1):
            if count>4000:raise p.Rejected('bounded evidence entry ceiling')
            if entry.name.startswith(('placement-','planning-')):markers.add('placement')
            if entry.name.startswith('placement-search'):markers.add('search')
            if entry.name.startswith('floor-'):markers.add('floor')
    return markers


def receipt_policy(data,directory):
    """Refuse single-field downgrade while preserving old native/C receipts."""
    markers=evidence_markers(directory)
    if data.get('schema')==4 or data.get('input_policy')==SEARCH_POLICY or 'placement_search' in data or 'search' in markers:
        from .placement_clearance import parameters
        if (type(data.get('schema')) is not int or data['schema']!=4 or data.get('input_policy')!=SEARCH_POLICY
                or data.get('adapter')!='both' or data.get('scope')!='whole_board_unlocked_routing'
                or canonical(data.get('planning_parameters'))!=canonical(parameters())
                or any(key in data for key in ('strategy','netclass_policy','guidance_policy','diagnostic_schema','production_qualified','routing_preferences'))
                or (directory/'routing-preferences.json').exists() or (directory/'routing-preferences.json').is_symlink()):
            raise p.Rejected('missing, mixed or downgraded placement search policy')
        expected=search_contract(data.get('engine_profile'),data.get('scoring_variant'))
        path=directory/'placement-search.json'
        if (data.get('baseline')!=p.engine_baseline(data['engine_profile'],'both')
                or canonical(read_json(path))!=canonical(expected)
                or data.get('placement_search')!={'file':path.name,'sha256':p.sha(path)}):
            raise p.Rejected('placement search contract differs')
        return SEARCH_POLICY
    new_artifacts='placement' in markers
    new_claims=any(key.startswith(('placement_','planning_')) for key in data) or data.get('input_policy')==PLACEMENT_POLICY
    if data.get('schema')==3 or new_artifacts or new_claims:
        from .placement_clearance import parameters
        if (type(data.get('schema')) is not int or data['schema']!=3 or data.get('input_policy')!=PLACEMENT_POLICY
                or data.get('adapter')!='both' or data.get('scope')!='whole_board_unlocked_routing'
                or data.get('baseline')!='completion_only_probe' or data.get('engine_profile')!='completion-only'
                or data.get('scoring_variant')!='via_default' or canonical(data.get('planning_parameters'))!=canonical(parameters())
                or any(key in data for key in ('strategy','netclass_policy','guidance_policy','diagnostic_schema','production_qualified'))):
            raise p.Rejected('missing, mixed or downgraded placement policy')
        return PLACEMENT_POLICY
    artifacts='floor' in markers
    claims='input_policy' in data or 'guidance_policy' in data or any(key.startswith('floor_') for key in data)
    if data.get('schema')==2 or artifacts or claims:
        if (type(data.get('schema')) is not int or data['schema']!=2 or data.get('input_policy')!=POLICY
                or data.get('adapter')!='both' or data.get('scope')!='whole_board_unlocked_routing'
                or data.get('baseline') not in {'B1','B2_tuned','completion_only_probe'}
                or 'strategy' in data or 'netclass_policy' in data or data.get('scoring_variant') is not None):
            raise p.Rejected('missing, mixed or downgraded floor policy')
        return POLICY
    return 'native'


def search_contract(profile,scoring_variant):
    """Finite experimental search choices; the base placement DSN is unchanged."""
    if type(profile) is not str or profile not in {'standard','tuned','completion-only'}:
        raise p.Rejected('unknown placement search profile')
    if type(scoring_variant) is not str or scoring_variant not in {'via_default','via_low','via_high'}:
        raise p.Rejected('unknown placement search scoring variant')
    return {'schema':1,'policy':SEARCH_POLICY,'base_policy':PLACEMENT_POLICY,
            'engine_profile':profile,'scoring_variant':scoring_variant,
            'scoring':p.engine_scoring_settings(scoring_variant),'strict_class_targets':True}


def evidence_inventory(directory):
    if 'placement' in evidence_markers(directory):
        from .placement_clearance import evidence_inventory as bounded_inventory
        hashes=bounded_inventory(directory)
    else:hashes=p.tree_hash(directory)
    return {name:digest for name,digest in hashes.items()
            if name not in {'result.json','result.json.partial'}
            and not name.startswith(('invalidated-result-','interrupted-result-'))}


def context_argv(mode,board,path,dsn=None,area_output=None):
    result=[*SANDBOX,str(c.PYTHON),str(c.ROOT/'autorouter/floor_context.py'),mode,str(board),str(path)]
    if dsn is not None:result.append(str(dsn))
    if area_output is not None:
        if mode!='export' or dsn is None:raise p.Rejected('area observation requires export')
        result.append(str(area_output))
    return result


def context_binding(native,board,hashes,mode,dsn_hash=None):
    if (native.get('source')!=str(board) or native.get('board_sha256')!=hashes.get(board.name)
            or native.get('project_sha256')!=hashes.get(board.with_suffix('.kicad_pro').name)
            or native.get('input_hashes_before')!=hashes or native.get('input_hashes_after')!=hashes
            or native.get('mode')!=mode or native.get('dsn_sha256')!=dsn_hash
            or native.get('limits')!=LIMITS or native.get('board_saved') is not False):
        raise p.Rejected('native floor context input/project/mode binding differs')


def acquire_context(job,mode,board,*,areas=False):
    name='floor-'+mode;path=job.out/(name+'-context.json');dsn=job.out/'native.dsn' if mode=='export' else None
    before=p.tree_hash(board.parent)
    area_output=job.out/'placement-area-context.json' if areas else None
    job.step(name,context_argv(mode,board,path,dsn,area_output),already_sandboxed=True)
    native=read_json(path)
    context_binding(native,board,before,mode,p.sha(dsn) if dsn else None)
    if p.tree_hash(board.parent)!=before:raise p.Rejected('native floor context modified project')
    return native


def policy_contract(raw,native,project,task,source_hashes):
    task_bytes=(sx.dump(task)+'\n').encode();guided,audit=g.transform(raw,native,project,task_bytes)
    return guided,{'schema':1,'policy':POLICY,'source_hashes':source_hashes,'task_sha256':g.sha(task_bytes),
                  'project_sha256':g.sha(project),'transformation':audit}


def validate_contract(original,candidate,source_hashes,protected,contract,out,*,guidance_basis=None):
    if protected or p.netclass_policy(candidate) is not None:raise p.Rejected('floor policy excludes retained routes and literal netclasses')
    task=g.task_from_source(original)
    basis=Path(out if guidance_basis is None else guidance_basis)
    if guidance_basis is not None and any(path.is_symlink() for path in (basis,*basis.parents)):
        raise p.Rejected('floor guidance basis must not use symlinks')
    from .placement_clearance import read_bytes
    native=read_json(basis/'floor-export-context.json');raw=read_bytes(basis/'native.dsn')
    guided,expected=policy_contract(raw,native,candidate.with_suffix('.kicad_pro').read_bytes(),task,source_hashes)
    if canonical(contract)!=canonical(expected):raise p.Rejected('floor validation contract differs from original task')
    if read_bytes(basis/'floor-guided.dsn')!=guided:raise p.Rejected('floor guided bytes changed')
    context=g.qualify(json.loads(candidate.with_suffix('.kicad_pro').read_text()),native,task)
    g.audit_generated_routes(sx.read(candidate),context)
    return task,context


def final_context(job,original,candidate,source_hashes,protected,contract,*,guidance_basis=None):
    task,_=validate_contract(original,candidate,source_hashes,protected,contract,job.out,guidance_basis=guidance_basis)
    native=acquire_context(job,'final',candidate)
    context=g.qualify(json.loads(candidate.with_suffix('.kicad_pro').read_text()),native,task)
    audit={'candidate_sha256':p.sha(candidate),'native_context_sha256':p.sha(job.out/'floor-final-context.json'),
           'generated':g.audit_generated_routes(sx.read(candidate),context),
           'native_routes':g.audit_native_routes(sx.read(candidate),native)}
    p.save_json(job.out/'floor-final-audit.json',audit)


def process_check(directory,data,name,argv,*,allowed=(0,)):
    process=read_json(directory/(name+'-process.json'))
    if (process.get('argv')!=argv or process.get('cwd')!=str(directory) or process.get('name')!=name
            or type(process.get('exit_code')) is not int or process['exit_code'] not in allowed
            or process.get('status')!=('success' if process['exit_code']==0 else 'nonzero_exit')
            or process.get('cleanup_complete') is not True):raise p.Rejected('floor process provenance differs: '+name)
    matches=[step for step in data.get('steps',[]) if step.get('name')==name and step.get('cwd')==str(directory)]
    if len(matches)!=1 or any(matches[0].get(key)!=value for key,value in process.items()):raise p.Rejected('floor step differs from retained process: '+name)
    return process


def engine_argv(directory,settings):
    return p.engine_argv(directory,settings)


def check_final_context(directory,data,original,candidate,protected,contract,guidance_basis=None):
    """Check this candidate's fresh final observation against its export basis.

    The caller additionally binds/validates any external incumbent receipt and
    complete evidence tree. This helper does not authenticate a loose basis.
    """
    task,_=validate_contract(original,candidate,data['source_hashes'],protected,contract,directory,guidance_basis=guidance_basis)
    final_native=read_json(directory/'floor-final-context.json');expected=dict(data['source_hashes']);expected[candidate.name]=data['candidate_sha256']
    context_binding(final_native,candidate,expected,'final')
    final_policy=g.qualify(json.loads(candidate.with_suffix('.kicad_pro').read_text()),final_native,task)
    audited={'candidate_sha256':p.sha(candidate),'native_context_sha256':p.sha(directory/'floor-final-context.json'),
             'generated':g.audit_generated_routes(sx.read(candidate),final_policy),'native_routes':g.audit_native_routes(sx.read(candidate),final_native)}
    if read_json(directory/'floor-final-audit.json')!=audited:raise p.Rejected('final floor route audit differs')
    process_check(directory,data,'floor-final',context_argv('final',candidate,directory/'floor-final-context.json'))
    return audited


def check_floor_result(directory,data,original,candidate,protected):
    policy=receipt_policy(data,directory)
    if policy not in GUIDANCE_POLICIES:raise p.Rejected('floor-backed policy required')
    new_policy=policy in PLACEMENT_POLICIES
    required_code={'autorouter/board_floor.py','autorouter/floor_context.py','autorouter/floor_route.py','autorouter/adapter.py'}
    if new_policy:required_code.update({'autorouter/placement_transform.py','autorouter/placement_clearance.py'})
    if not required_code<=set(data.get('tools',{}).get('implementation_sha256',{})):raise p.Rejected('floor implementation provenance incomplete')
    if data.get('floor_evidence_hashes')!=evidence_inventory(directory):raise p.Rejected('completed floor evidence changed')
    contract=read_json(directory/'floor-policy.json')
    if data.get('floor_policy')!={'file':'floor-policy.json','sha256':p.sha(directory/'floor-policy.json')}:
        raise p.Rejected('floor policy receipt binding missing or changed')
    task,context=validate_contract(original,candidate,data['source_hashes'],protected,contract,directory)
    task_hash=g.sha((sx.dump(task)+'\n').encode())
    expected=dict(data['source_hashes']);expected[candidate.name]=task_hash
    exported=directory/'floor-export-input'/candidate.name
    if p.tree_hash(exported.parent)!=expected or data.get('task_sha256')!=task_hash:raise p.Rejected('retained floor export input differs from original task')
    native=read_json(directory/'floor-export-context.json')
    context_binding(native,exported,expected,'export',p.sha(directory/'native.dsn'))
    if native.get('routes')!=[]:raise p.Rejected('floor export unexpectedly retained routes')
    process_check(directory,data,'floor-export',context_argv('export',exported,directory/'floor-export-context.json',directory/'native.dsn',directory/'placement-area-context.json' if new_policy else None))
    if new_policy:
        from .placement_clearance import read_bytes
        raw=read_bytes(directory/'native.dsn',20*1024*1024);guided=read_bytes(directory/'floor-guided.dsn');adapted=read_bytes(directory/'task.dsn')
    else:
        raw=(directory/'native.dsn').read_bytes();guided=(directory/'floor-guided.dsn').read_bytes();adapted=(directory/'task.dsn').read_bytes()
    if new_policy:
        from . import placement_clearance as pc
        pc.check_chain(directory,data);pc.check_freeze(directory,data)
    elif g.verify_chain(raw,guided,adapted,native,candidate.with_suffix('.kicad_pro').read_bytes(),(sx.dump(task)+'\n').encode())!=contract['transformation']:
        raise p.Rejected('floor derivation receipt differs')
    if data.get('floor_guided_dsn_sha256')!=g.sha(guided):raise p.Rejected('guided DSN hash differs')
    check_final_context(directory,data,original,candidate,protected,contract)
    settings=data.get('engine_budget',{})
    expected_settings=p.engine_profile_settings(data['engine_profile'],settings.get('remaining_outer_wall_seconds_at_assignment'),strict_class_targets=True,scoring_variant=data['scoring_variant'] if new_policy else None)
    expected_settings.update(outer_task_wall_budget_seconds=data['budget_seconds'],outer_task_cpu_budget_seconds=data['cpu_budget_seconds'])
    if settings!=expected_settings:raise p.Rejected('floor engine configuration differs')
    process_check(directory,data,'engine',engine_argv(directory,settings['argv']))
    if data['engine_profile']=='tuned' and data.get('optimizer_threshold_audit')!=p.optimizer_threshold_audit(directory/'engine.log',0.1):raise p.Rejected('floor optimizer threshold evidence differs')
    if data['baseline']!=p.engine_baseline(data['engine_profile'],'both'):raise p.Rejected('floor baseline/profile mismatch')
    for name,action,output,extra in [('import','import',directory/'imported.kicad_pcb',[directory/'routes.ses']),('metrics','metrics',directory/'metrics.json',[])]:
        process_check(directory,data,name,[*SANDBOX,str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),action,str(candidate),str(output),*[str(x) for x in extra]])
    audit_transport(directory,data,task,candidate)
    required={'source-drc','floor-export','engine','import','refill-drc','floor-final','final-drc','metrics'}
    from . import schematic_field_evidence as fields
    if fields.has_fields(data.get('native',{}).get('findings',[])):required.update(fields.names('final-drc'))
    if {step.get('name') for step in data.get('steps',[])}!=required or len(data['steps'])!=len(required):raise p.Rejected('unexpected/missing floor execution stages')


def check_drc_stage(directory,data,name,source,input_path,saved,before,*,schematic_parity=False,sandboxed=True,native_toolchain=None):
    """Verify a retained original-rule DRC stage, including exact saved input."""
    p.experimental_native_version(native_toolchain)
    if native_toolchain is not None and schematic_parity:raise p.Rejected('experimental schematic parity is unqualified')
    binding=read_json(directory/(name+'-binding.json'));after=binding.get('after')
    expected_toolchain=None if native_toolchain is None else native_toolchain.record()
    if binding.get('experimental_native_toolchain')!=expected_toolchain:raise p.Rejected('DRC experimental toolchain binding differs')
    if (binding.get('source')!=str(source) or binding.get('input')!=str(input_path)
            or binding.get('saved') is not saved or binding.get('before')!=before or not isinstance(after,dict)):
        raise p.Rejected('floor '+name+' binding differs')
    p.check_drc_project(before,after,source.name,saved=saved)
    if p.tree_hash(input_path.parent)!=after:
        raise p.Rejected('retained floor native stage input changed')
    native=p.parse_report(directory/(name+'.json'),source.name,native_toolchain=native_toolchain)
    argv=[*(SANDBOX if sandboxed else []),str(c.CLI if native_toolchain is None else native_toolchain.cli),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones',
          '--exit-code-violations','--output',str(directory/(name+'.json'))]
    if schematic_parity:argv.insert((len(SANDBOX) if sandboxed else 0)+8,'--schematic-parity')
    if saved:argv.append('--save-board')
    argv.append(str(input_path))
    process_check(directory,data,name,argv,allowed=(5 if native['findings'] else 0,))
    matching=next(step for step in data['steps'] if step['name']==name and step['cwd']==str(directory))
    if matching.get('validated_input_sha256')!=before[source.name] or matching.get('emitted_candidate')!=str(source):
        raise p.Rejected('floor native stage step/input mismatch')
    from . import schematic_field_evidence as fields
    fields.check_processes(directory,data,name,input_path,sandboxed=sandboxed)
    p.experimental_native_version(native_toolchain)
    return native


def audit_transport(directory,data,task,candidate):
    """Reconstruct final bytes from retained import and saved native refill."""
    ses=directory/'routes.ses';imported=directory/'imported.kicad_pcb'
    if ses.is_symlink() or not ses.is_file() or not 0<ses.stat().st_size<=sx.MAX_BYTES:
        raise p.Rejected('missing or invalid retained SES transport')
    if imported.is_symlink() or not imported.is_file():raise p.Rejected('missing retained native import')
    before_refill=p.transplant_routes(task,sx.read(imported))
    before_hash=g.sha((sx.dump(before_refill)+'\n').encode())
    source_native=check_drc_stage(directory,data,'source-drc',directory/'snapshot'/candidate.name,directory/'source-drc-input'/candidate.name,False,data['source_hashes'])
    if data.get('source_drc')!=source_native:raise p.Rejected('floor source DRC summary differs')
    before=dict(data['source_hashes']);before[candidate.name]=before_hash
    refill=directory/'refill'/candidate.name
    check_drc_stage(directory,data,'refill-drc',refill,refill,True,before)
    expected=p.transplant_fill(before_refill,sx.read(refill))
    if (sx.dump(expected)+'\n').encode()!=candidate.read_bytes():raise p.Rejected('final candidate differs from task/import/refill reconstruction')


class FloorJob(p.Job):
    def __init__(self,out,seconds,remaining,*,native_toolchain=None):
        super().__init__(out,seconds,native_toolchain=native_toolchain);self.remaining=remaining
        self.env={key:value for key,value in self.env.items() if key not in {'PYTHONPATH','PYTHONHOME'} and (not key.startswith('KICAD_') or key in {'KICAD_CONFIG_HOME','KICAD_CACHE_HOME','KICAD_DOCUMENTS_HOME'})}
        (self.out/'tmp').mkdir();self.env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(self.out/'tmp'))
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        available=self.remaining()
        cap=available-15 if name=='engine' else min(30,available)
        if cap<=0:raise p.Rejected('floor operation budget exhausted')
        self.deadline=time.monotonic()+cap
        return super().step(name,argv if already_sandboxed else [*SANDBOX,*argv],allowed)


def publish(output,report,stable,account,remaining,*,owned=None,final_check=None):
    """No canonical positive survives cancellation, staleness or write failure."""
    def archive():
        if owned is not None:owned()
        for name,prefix in [('result.json','invalidated-result-'),('result.json.partial','interrupted-result-')]:
            path=output/name
            if path.exists():
                if owned is not None:owned()
                path.rename(output/(prefix+uuid.uuid4().hex+path.suffix))
    try:
        stable();account();expected=canonical(report)
        if owned is not None:owned()
        p.save_json(output/'result.json',report)
        if canonical(read_json(output/'result.json'))!=expected:raise p.Rejected('floor receipt changed after publication')
        stable()
        if report['accepted']:p.check_result(output/'result.json')
        stable()
        if canonical(read_json(output/'result.json'))!=expected:raise p.Rejected('floor receipt changed during final readback')
        if report['accepted'] and remaining()<=0:raise p.Rejected('floor budget exceeded during final publication')
        if final_check is not None:
            final_check()
            if remaining()<=0:raise p.Rejected('floor budget exceeded during final check')
            if canonical(report)!=expected or canonical(read_json(output/'result.json'))!=expected:
                raise p.Rejected('floor receipt changed during final check')
    except (Exception,KeyboardInterrupt) as exc:
        archive();report.update(accepted=False,whole_project_drc_clean=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',reason=type(exc).__name__+': '+str(exc))
        account()
        try:
            if owned is not None:owned()
            p.save_json(output/'result.json',report)
        except (Exception,KeyboardInterrupt):archive()
    return report


def route(source,output,seconds,keep_existing,adapter,profile,scoring_variant,*,guidance_policy=POLICY,preferences=None):
    if guidance_policy not in GUIDANCE_POLICIES:raise p.Rejected('unknown floor-backed guidance policy')
    if guidance_policy==SEARCH_POLICY:
        if keep_existing or adapter!='both' or preferences is not None:raise p.Rejected('unsupported: placement search requires whole-board adapter=both without preferences')
        scoring_variant='via_default' if scoring_variant is None else scoring_variant
        search_contract(profile,scoring_variant)
    elif keep_existing or adapter!='both' or scoring_variant is not None:raise p.Rejected('unsupported: guidance requires whole-board adapter=both without scoring overrides')
    if guidance_policy==PLACEMENT_POLICY and profile!='completion-only':raise p.Rejected('unsupported: placement policy requires completion-only profile')
    p.engine_scoring_settings(scoring_variant)
    if profile not in {'standard','tuned','completion-only'}:raise p.Rejected('unknown engine profile')
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 5<=seconds<=900:raise p.Rejected('budget must be 5–900 seconds')
    # Keep cancellation active through export, import, final readback and publication.
    def interrupted(signum,frame):raise KeyboardInterrupt
    handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        for sig in handlers:signal.signal(sig,interrupted)
        if guidance_policy==SEARCH_POLICY:
            return _route(source,output,seconds,profile,guidance_policy,preferences,scoring_variant=scoring_variant)
        return _route(source,output,seconds,profile,guidance_policy,preferences)
    finally:
        for sig,handler in handlers.items():signal.signal(sig,handler)


def _route(source,output,seconds,profile,guidance_policy=POLICY,preferences=None,*,scoring_variant=None):
    search=guidance_policy==SEARCH_POLICY
    search_parameters=search_contract(profile,scoring_variant) if search else None
    if search and preferences is not None:raise p.Rejected('unsupported: placement search excludes preferences')
    new_policy=guidance_policy in PLACEMENT_POLICIES
    if new_policy:from . import placement_clearance as pc
    started,parent_start,child_start=time.monotonic(),time.process_time(),child_cpu()
    if preferences is not None:
        started,parent_start,child_start=preferences['started'],preferences['parent_cpu'],preferences['child_cpu']
    source,output=Path(source).absolute(),Path(output).absolute()
    if any(path.is_symlink() for path in (source,*source.parents,output,*output.parents)):raise p.Rejected('floor paths must not use symlinks')
    source,output=source.resolve(strict=True),output.resolve()
    if source.parent==output or source.parent in output.parents:raise p.Rejected('output must be outside source project')
    def remaining():return max(0,min(started+seconds-time.monotonic(),seconds-(time.process_time()-parent_start+child_cpu()-child_start)))
    job=FloorJob(output,seconds,remaining);job.started=started;job.cpu_started=parent_start
    report={'schema':4 if search else 3 if new_policy else 2,'input_policy':guidance_policy,'status':'rejected','accepted':False,'physical_electrical_validation':False,'schematic_parity':'not checked',
        'source':str(source),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'budget_seconds':seconds,'cpu_budget_seconds':seconds,
        'cpu_budget_enforcement':'remaining wall/CPU assignment and final acceptance cap; no hard total-CPU quota','baseline':p.engine_baseline(profile,'both'),
        'adapter':'both','engine_profile':profile,'scoring_variant':scoring_variant if search else 'via_default' if new_policy else None,'scope':'whole_board_unlocked_routing'}
    if new_policy:report['planning_parameters']=pc.parameters()
    frozen=False;completed=None
    def stable():
        p.preferences_fresh(output,preferences)
        if not frozen:return
        inventory=pc.inventory if new_policy else p.tree_hash
        if p.tool_manifest()!=report['tools']:raise p.Rejected('floor source/tool/code/HEAD changed')
        if new_policy:pc.check_freeze(output,report)
        if completed is not None and evidence_inventory(output)!=completed:raise p.Rejected('completed floor evidence changed')
        if inventory(source.parent)!=hashes or inventory(output/'snapshot')!=hashes:raise p.Rejected('floor source/snapshot changed')
        p.preferences_fresh(output,preferences)
    def account():
        steps=job.steps
        report.update(steps=steps,wall_seconds=time.monotonic()-started,parent_cpu_seconds=time.process_time()-parent_start,
            child_cpu_seconds=sum(s.get('cpu_seconds') or 0 for s in steps),monitor_cpu_seconds=sum(s.get('monitor_cpu_seconds') or 0 for s in steps),
            peak_child_rss_bytes=max([s.get('max_rss_bytes') or 0 for s in steps]+[0]))
        report['control_child_cpu_seconds']=max(0,child_cpu()-child_start-report['child_cpu_seconds']-report['monitor_cpu_seconds'])
        report['total_cpu_seconds']=sum(report[key] for key in ('parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','control_child_cpu_seconds'))
        report['resource_accounting_point']='Stored totals precede final receipt write and readback; final acceptance wall/CPU cap includes both and all freshness checks.'
        report['resource_limitations']='Sequential bounded worker; parent and waited-child CPU include metadata and failed stages. Group RSS/disk polling may overshoot; detached descendants are unsupported.'
        if any(s.get('status')=='cancelled' or s.get('cleanup_complete') is not True for s in steps):report.update(accepted=False,status='cancelled')
        if report['wall_seconds']>seconds or report['total_cpu_seconds']>seconds:report.update(accepted=False,status='budget_exceeded')
        if not report['accepted']:report['whole_project_drc_clean']=False
    try:
        p.capture_preferences(report,output,preferences)
        if search:
            p.save_json(output/'placement-search.json',search_parameters)
            report['placement_search']={'file':'placement-search.json','sha256':p.sha(output/'placement-search.json')}
        p.check_storage()
        hashes=pc.placement.inventory(pc.files(source.parent)) if new_policy else p.tree_hash(source.parent)
        original=p.preflight(source)
        if p.netclass_policy(source) is not None:raise p.Rejected('unsupported: floor policy requires one Default class')
        task=g.task_from_source(original)
        g.qualify_scope(json.loads(source.with_suffix('.kicad_pro').read_text()),task)
        if new_policy:pc.narrow_source(original)
        report.update(source_hashes=hashes,tools=p.tool_manifest())
        report['schematic_parity']=p.parity_declaration(source,hashes)
        if new_policy:
            freeze=pc.capture_freeze(report['tools']);shutil.copy2(c.ROOT/'toolchain.lock.json',output/'placement-toolchain.lock.json')
            p.save_json(output/'placement-source-freeze.json',freeze)
            report['placement_source_freeze']={'file':'placement-source-freeze.json','sha256':p.sha(output/'placement-source-freeze.json')}
        shutil.copytree(source.parent,output/'snapshot');shutil.copytree(source.parent,output/'candidate');(output/'code').mkdir()
        for relative,digest in report['tools']['implementation_sha256'].items():
            dest=output/'code'/Path(relative).name;shutil.copy2(c.ROOT/relative,dest)
            if p.sha(dest)!=digest:raise p.Rejected('floor code changed during snapshot')
        frozen=True;stable();candidate=output/'candidate'/source.name;sx.write(candidate,task)
        report['task_sha256']=p.sha(candidate)
        shutil.copytree(candidate.parent,output/'floor-export-input');exported=output/'floor-export-input'/source.name
        report['source_drc']=job.drc('source-drc',output/'snapshot'/source.name)
        native=acquire_context(job,'export',exported,areas=new_policy)
        raw=pc.read_bytes(output/'native.dsn',20*1024*1024) if new_policy else (output/'native.dsn').read_bytes()
        guided,contract=policy_contract(raw,native,candidate.with_suffix('.kicad_pro').read_bytes(),task,hashes)
        (output/'floor-guided.dsn').write_bytes(guided);(output/'task.dsn').write_bytes(guided);p.save_json(output/'floor-policy.json',contract)
        if new_policy:
            outputs,composition=pc.derive_chain(output,source.name,hashes)
            for name,raw in outputs.items():(output/name).write_bytes(raw)
            p.save_json(output/'placement-policy.json',composition)
            report['placement_policy']={'file':'placement-policy.json','sha256':p.sha(output/'placement-policy.json')}
            pc.check_chain(output,report)
        else:
            from .adapter import adapt_dsn
            report['adapter_transformations']=adapt_dsn(output/'task.dsn','both',native['obstacles'])
            g.verify_chain((output/'native.dsn').read_bytes(),guided,(output/'task.dsn').read_bytes(),native,candidate.with_suffix('.kicad_pro').read_bytes(),(sx.dump(task)+'\n').encode())
        report.update(native_dsn_sha256=p.sha(output/'native.dsn'),floor_guided_dsn_sha256=g.sha(guided),task_dsn_sha256=p.sha(output/'task.dsn'),floor_policy={'file':'floor-policy.json','sha256':p.sha(output/'floor-policy.json')})
        (output/'engine-config').mkdir()
        settings=p.engine_profile_settings(profile,remaining(),strict_class_targets=True,scoring_variant=report['scoring_variant'])
        settings.update(outer_task_wall_budget_seconds=seconds,outer_task_cpu_budget_seconds=seconds);report['engine_budget']=settings
        job.step('engine',engine_argv(output,settings['argv']),already_sandboxed=True)
        if profile=='tuned':report['optimizer_threshold_audit']=p.optimizer_threshold_audit(output/'engine.log',0.1)
        if not (output/'routes.ses').is_file():raise p.Rejected('engine emitted no SES')
        imported=output/'imported.kicad_pcb';job.native('import','import',candidate,imported,output/'routes.ses')
        sx.write(candidate,p.transplant_routes(task,sx.read(imported)))
        final_hash,native=p.validate_candidate(job,original,candidate,hashes,[],guidance_contract=contract)
        job.native('metrics','metrics',candidate,output/'metrics.json');p.verify_candidate_files(candidate,hashes,final_hash)
        report.update(candidate=str(candidate),candidate_sha256=final_hash,native_report_sha256=p.sha(output/'final-drc.json'),native=native,
            metrics=read_json(output/'metrics.json'),invariants_unchanged=True,native_rejection_reasons=p.native_rejection_reasons(native),
            accepted=p.native_accepted(native),status='routing_accepted' if p.native_accepted(native) else 'drc_rejected',
            whole_project_drc_clean=p.native_accepted(native) and native['warnings']==0)
        completed=evidence_inventory(output);report['floor_evidence_hashes']=completed
    except KeyboardInterrupt:report.update(accepted=False,status='cancelled',reason='interrupted floor route')
    except Exception as exc:report.update(accepted=False,status='unsupported' if 'unsupported:' in str(exc) else 'rejected',reason=type(exc).__name__+': '+str(exc))
    return publish(output,report,stable,account,remaining)
