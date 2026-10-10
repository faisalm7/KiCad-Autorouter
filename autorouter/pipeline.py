"""Snapshot, bounded engine, structural preservation and native validation.

Experimental whole-board completion only. Original projects are never written.
"""
from __future__ import annotations
import copy
import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import re
import shutil
import subprocess
import time
from . import config as c, sexpr as sx
from .runner import run

ROUTES={'segment','via','arc'}
DERIVED_ZONE={'filled_polygon','fill_segments'}
CRITICAL_CHECKS={'hole_clearance','hole_to_hole','hole_near_hole','starved_thermal','zones_intersect','padstack','items_not_allowed','through_hole_pad_without_hole','unconnected_items','shorting_items','clearance','track_width','via_diameter','annular_width','drill_out_of_range','copper_edge_clearance','invalid_outline','tracks_crossing'}

# KiCad 10 keys observed in pinned project settings / native default report.
KNOWN_CHECKS = CRITICAL_CHECKS | set('annular_width clearance connection_width copper_edge_clearance copper_sliver courtyards_overlap creepage diff_pair_gap_out_of_range diff_pair_uncoupled_length_too_long drill_out_of_range duplicate_footprints extra_footprint footprint footprint_filters_mismatch footprint_symbol_mismatch footprint_type_mismatch hole_clearance hole_near_hole hole_to_hole holes_co_located invalid_outline isolated_copper item_on_disabled_layer items_not_allowed length_out_of_range lib_footprint_issues lib_footprint_mismatch malformed_courtyard microvia_drill_out_of_range mirrored_text_on_front_layer missing_courtyard missing_footprint net_conflict nonmirrored_text_on_back_layer npth_inside_courtyard overlapping_pads padstack pth_inside_courtyard shorting_items silk_edge_clearance silk_over_copper silk_overlap skew_out_of_range solder_mask_bridge starved_thermal text_height text_thickness through_hole_pad_without_hole too_many_vias track_angle track_dangling track_segment_length track_width tracks_crossing unconnected_items unresolved_variable via_dangling zones_intersect track_not_centered_on_via tuning_profile_track_geometries'.split())

class Rejected(Exception):
    pass

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save_json(path, value):
    p=Path(path); tmp=p.with_suffix(p.suffix+'.partial')
    with tmp.open('x') as f:
        json.dump(value,f,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,p)

def tree_hash(root):
    root=Path(root)
    if root.is_symlink() or not root.is_dir(): raise Rejected('project root must be a real directory')
    result={}
    total=0
    for path in sorted(root.rglob('*')):
        if path.is_symlink(): raise Rejected('symlink in project: '+str(path.relative_to(root)))
        if path.is_file():
            total+=path.stat().st_size
            if total>100*1024*1024 or len(result)>=2000: raise Rejected('project exceeds snapshot limit')
            result[str(path.relative_to(root))]=sha(path)
    return result

def check_storage():
    total=0
    for directory in ['.data','.tools','.runs']:
        root=c.ROOT/directory
        for p in root.rglob('*'):
            if p.is_file(): total+=p.stat().st_size
    if total>10*1024**3: raise Rejected('10 GiB project cache/data ceiling exceeded')
    if shutil.disk_usage(c.ROOT).free<2*1024**3: raise Rejected('less than 2 GiB disk headroom')
    return total

def immutable(tree):
    t=copy.deepcopy(tree)
    t[:]=[n for n in t if not isinstance(n,list) or not n or n[0] not in ROUTES]
    for z in sx.children(t,'zone'):
        z[:]=[n for n in z if not isinstance(n,list) or not n or n[0] not in DERIVED_ZONE]
    return t

def routes(tree): return [n for n in tree if isinstance(n,list) and n and n[0] in ROUTES]

def locked(n):
    return 'locked' in n or sx.one(n,'locked') in (['locked','yes'],['locked'])

def netclass_policy(board):
    """Keep the established Default path; qualify only a narrow new scope."""
    project=json.loads(Path(board).with_suffix('.kicad_pro').read_text())
    settings=project.get('net_settings',{})
    if not (settings.get('netclass_patterns') or settings.get('netclass_assignments') or len(settings.get('classes',[]))>1):
        return None
    from .netclass import qualify_project
    try:
        policy=qualify_project(project)
        layers=sx.one(sx.read(board),'layers',[])
        if sum(isinstance(x,list) and len(x)>2 and re.fullmatch(r'(?:F|B|In[0-9]+)\.Cu',sx.unquote(x[1])) is not None for x in layers)!=2:
            raise ValueError('literal netclasses currently require two copper layers')
        if policy['mode']!='literal_two_class': raise ValueError('unqualified netclass binding mode')
        return policy
    except (ValueError,TypeError,KeyError) as exc:
        raise Rejected('unsupported: netclass bindings not qualified: '+str(exc)) from exc

def preflight(board):
    t=sx.read(board)
    reasons=[]
    if t[0]!='kicad_pcb': reasons.append('not a KiCad board')
    if sx.one(t,'version')[1] not in {'20241229','20260206'}: reasons.append('unqualified board format version')
    layers=sx.one(t,'layers',[])
    if sum(isinstance(x,list) and len(x)>2 and re.fullmatch(r'(?:F|B|In[0-9]+)\.Cu',sx.unquote(x[1])) is not None for x in layers) not in (2,4): reasons.append('requires 2 or 4 copper layers')
    project=board.with_suffix('.kicad_pro')
    if not project.is_file(): reasons.append('complete .kicad_pro required')
    else:
        p=json.loads(project.read_text()); settings=p.get('board',{}).get('design_settings',{})
        try: netclass_policy(board)
        except Rejected as exc: reasons.append(str(exc).removeprefix('unsupported: '))
        if settings.get('drc_exclusions'): reasons.append('DRC exclusions not qualified')
        for key,val in settings.get('rule_severities',{}).items():
            if key not in KNOWN_CHECKS or val not in {'error','warning','ignore'}: reasons.append('unknown rule severity semantics: '+key)
            if key in CRITICAL_CHECKS and val!='error': reasons.append('core native check not blocking: '+key)
    rules=board.with_suffix('.kicad_dru')
    if rules.exists() and rules.read_text().strip(): reasons.append('custom rules not qualified')
    for fp in sx.children(t,'footprint'):
        if sx.children(fp,'net_tie_pad_groups'): reasons.append('net ties not qualified')
        for pad in sx.children(fp,'pad'):
            if len(pad)<4 or pad[3]=='custom': reasons.append('custom pads not qualified')
    for via in sx.children(t,'via'):
        if any(x in via for x in ('blind','micro')): reasons.append('advanced vias not qualified')
    if reasons: raise Rejected('unsupported: '+'; '.join(sorted(set(reasons))))
    return t

def convert_route_nets(route, native_tree, original):
    route=copy.deepcopy(route)
    old={n[1]:n[2] for n in sx.children(native_tree,'net')}
    target={n[2]:n[1] for n in sx.children(original,'net')}
    n=sx.one(route,'net')
    if n:
        name=old.get(n[1],n[1])
        if target:
            if name not in target: raise Rejected('imported route has unknown net '+name)
            n[:]=['net',target[name]]
        else: n[:]=['net',name]
    return route

def transplant_routes(original, imported):
    out=copy.deepcopy(original)
    out[:]=[n for n in out if not isinstance(n,list) or not n or n[0] not in ROUTES]
    out.extend(convert_route_nets(n,imported,original) for n in routes(imported))
    return out

def transplant_fill(original, filled):
    out=copy.deepcopy(original)
    fill_by_id={sx.one(z,'uuid')[1]:z for z in sx.children(filled,'zone')}
    for z in sx.children(out,'zone'):
        zid=sx.one(z,'uuid')[1]
        if zid not in fill_by_id: raise Rejected('native refill lost zone')
        z[:]=[n for n in z if not isinstance(n,list) or not n or n[0] not in DERIVED_ZONE]
        z.extend(copy.deepcopy(n) for n in fill_by_id[zid] if isinstance(n,list) and n and n[0] in DERIVED_ZONE)
    return out

def parse_report(path, board_name):
    data=json.loads(Path(path).read_text())
    if data.get('$schema')!='https://schemas.kicad.org/drc.v1.json' or data.get('kicad_version')!='10.0.0' or data.get('source')!=board_name:
        raise Rejected('validator report identity/schema/version mismatch')
    for key in ('violations','unconnected_items','schematic_parity','ignored_checks','included_severities'):
        if not isinstance(data.get(key),list): raise Rejected('validator report missing '+key)
    if set(data['included_severities'])!={'error','warning','exclusion'}: raise Rejected('validator omitted severities')
    if any(not isinstance(v,dict) or not isinstance(v.get('key'),str) or v['key'] not in KNOWN_CHECKS for v in data['ignored_checks']): raise Rejected('malformed or unknown ignored check')
    if any(v.get('key') in CRITICAL_CHECKS for v in data['ignored_checks']): raise Rejected('validator disabled required check')
    findings=data['violations']+data['unconnected_items']+data['schematic_parity']
    for v in findings:
        if not isinstance(v,dict) or v.get('severity') not in ('error','warning','exclusion') or not isinstance(v.get('type'),str) or not isinstance(v.get('items'),list):
            raise Rejected('invalid finding schema')
        if 'excluded' in v and type(v['excluded']) is not bool:
            raise Rejected('invalid finding exclusion flag')
    return {'opens':len(data['unconnected_items']), 'blocking':sum(v['severity']=='error' for v in data['violations']+data['schematic_parity']),
            'warnings':sum(v['severity']=='warning' for v in findings), 'exclusions':sum(v['severity']=='exclusion' or v.get('excluded',False) for v in findings),
            'ignored_checks':data['ignored_checks'],'findings':findings}

class Job:
    def __init__(self, out, seconds):
        self.out=Path(out).resolve(); self.out.mkdir(parents=True,exist_ok=False)
        self.started=time.monotonic(); self.cpu_started=time.process_time()
        self.deadline=self.started+seconds; self.steps=[]; self.seconds=seconds
        self.env=os.environ.copy()
        # Avoid writing personal KiCad settings. No model/API/network used in route time.
        for key, relative in [('KICAD_CONFIG_HOME','kicad-config'),('KICAD_CACHE_HOME','kicad-cache'),('KICAD_DOCUMENTS_HOME','kicad-documents')]:
            base=self.out/relative
            (base/('10.0' if key=='KICAD_CONFIG_HOME' else 'kicad/10.0')).mkdir(parents=True)
            self.env[key]=str(base)
    def step(self, name, argv, allowed=(0,)):
        remaining=self.deadline-time.monotonic()
        if remaining<=0: raise Rejected('timeout: whole task budget exhausted')
        result=run([str(a) for a in argv],cwd=self.out,log=self.out/(name+'.log'),timeout=remaining,env=self.env)
        result['name']=name; self.steps.append(result)
        save_json(self.out/(name+'-process.json'),result)
        if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed:
            raise Rejected(name+': '+result['status']+' exit='+str(result['exit_code']))
        return result
    def native(self,name,action,board,output,*args):
        return self.step(name,[c.PYTHON,c.ROOT/'autorouter/native.py',action,board,output,*args])
    def drc(self,name,board,save=False):
        original_input=board
        before=tree_hash(board.parent)
        if not save:
            work=self.out/(name+'-input')
            shutil.copytree(board.parent,work)
            board=work/board.name
        report=self.out/(name+'.json')
        argv=[c.CLI,'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',report]
        if save: argv+=['--save-board']
        result=self.step(name,argv+[board],allowed=(0,5))
        after=tree_hash(board.parent)
        for filename,digest in before.items():
            if save and filename==board.name: continue
            if after.get(filename)!=digest: raise Rejected('native DRC modified input or rules: '+filename)
        unexpected=set(after)-set(before)-{board.with_suffix('.kicad_prl').name}
        if unexpected: raise Rejected('native DRC created unexpected project files')
        result['validated_input_sha256']=before[board.name]
        result['emitted_candidate']=str(original_input)
        save_json(self.out/(name+'-binding.json'),{'source':str(original_input),'input':str(board),'before':before,'after':after,'saved':save})
        parsed=parse_report(report,board.name)
        any_findings=bool(parsed['findings'])
        if (result['exit_code']==0)==any_findings: raise Rejected('DRC exit/report mismatch')
        return parsed

def verify_candidate_files(candidate, original_hashes, final_hash=None):
    actual=tree_hash(candidate.parent)
    expected=dict(original_hashes)
    expected[candidate.name]=sha(candidate) if final_hash is None else final_hash
    if actual!=expected: raise Rejected('candidate project/rules/file set changed')

def audit_route_dimensions(tree, protected, native):
    """Check new copper against native class targets, beyond DRC minimums.

    Protected original route objects are exempt from target equality; their
    unchanged geometry remains subject to normal native DRC. This is an exact
    target-preservation scope, not general neckdown/custom-rule support.
    """
    records={row['name']:row for row in native['nets']}
    names={node[1]:sx.unquote(node[2]) for node in sx.children(tree,'net')}
    checked={'segments':0,'arcs':0,'vias':0,'protected':0}
    def dimension(route,key):
        node=sx.one(route,key)
        if node is None or len(node)!=2 or not isinstance(node[1],str): raise Rejected('missing or malformed route '+key)
        try: value=Decimal(node[1])*1000000
        except InvalidOperation: raise Rejected('malformed route '+key) from None
        if not value.is_finite() or value<=0 or value!=value.to_integral_value(): raise Rejected('invalid route '+key)
        return int(value)
    for route in routes(tree):
        if route in protected:
            checked['protected']+=1
            continue
        net=sx.one(route,'net')
        if net is None or len(net)!=2 or not isinstance(net[1],str): raise Rejected('route missing net')
        name=names.get(net[1],sx.unquote(net[1]))
        row=records.get(name)
        if row is None: raise Rejected('generated route has unknown native net '+name)
        if route[0]=='via':
            if any(kind in route for kind in ('blind','micro')) or sx.one(route,'layers')!=['layers','"F.Cu"','"B.Cu"']:
                raise Rejected('unqualified generated via layer span')
            if dimension(route,'size')!=row['via_diameter_nm'] or dimension(route,'drill')!=row['via_drill_nm']:
                raise Rejected('generated via differs from native netclass target: '+name)
            checked['vias']+=1
        else:
            if dimension(route,'width')!=row['width_nm']:
                raise Rejected('generated track differs from native netclass target: '+name)
            checked['arcs' if route[0]=='arc' else 'segments']+=1
    return {'passed':True,'checked':checked,'policy':'exact effective native targets for new routes; protected originals unchanged'}

def audit_candidate_netclasses(candidate, protected, native):
    from .netclass import audit_native
    project=candidate.with_suffix('.kicad_pro')
    if (native.get('source')!=str(candidate) or native.get('board_sha256')!=sha(candidate)
            or native.get('project_sha256')!=sha(project) or native.get('board_saved') is not False):
        raise Rejected('native netclass map is not bound to candidate and original project')
    mapping=audit_native(native,json.loads(project.read_text()))
    dimensions=audit_route_dimensions(sx.read(candidate),protected,native)
    return {'native':mapping,'route_dimensions':dimensions,'candidate_sha256':sha(candidate),
            'project_sha256':sha(project)}

def validate_candidate(job, original, candidate, source_hashes, protected):
    # Reject mutations before native tooling is allowed to normalize anything.
    if immutable(sx.read(candidate))!=immutable(original): raise Rejected('immutable geometry changed')
    if any(n not in routes(sx.read(candidate)) for n in protected): raise Rejected('protected route changed')
    verify_candidate_files(candidate,source_hashes)
    shutil.copytree(candidate.parent,job.out/'refill')
    refill=job.out/'refill'/candidate.name
    job.drc('refill-drc',refill,save=True)
    sx.write(candidate,transplant_fill(sx.read(candidate),sx.read(refill)))
    if immutable(sx.read(candidate))!=immutable(original): raise Rejected('immutable geometry changed after refill')
    final_hash=sha(candidate)
    if netclass_policy(candidate) is not None:
        mapping=job.out/'final-netclasses.json'
        job.native('final-netclasses','netclasses',candidate,mapping)
        audited=audit_candidate_netclasses(candidate,protected,json.loads(mapping.read_text()))
        audited['native_map_file_sha256']=sha(mapping)
        save_json(job.out/'final-netclass-audit.json',audited)
    native=job.drc('final-drc',candidate)
    verify_candidate_files(candidate,source_hashes,final_hash)
    return final_hash,native


def tool_manifest():
    expected=json.loads((c.ROOT/'toolchain.lock.json').read_text())['tools']
    resolved={name:c.resolve_tool_path(pin['path']) for name,pin in expected.items()}
    if resolved.get('freerouting')!=c.JAR: raise Rejected('engine pin does not identify project-local JAR')
    files={str(p):sha(p) for p in (c.CLI,c.PYTHON,c.JAVA,c.JAR) if p.is_file()}
    if c.PCBNEW.is_file(): files[str(c.PCBNEW)]=sha(c.PCBNEW)
    for name, pin in expected.items():
        path=resolved[name]
        if files.get(str(path))!=pin['sha256']: raise Rejected('pinned tool changed or missing: '+name)
    implementation={str(p.relative_to(c.ROOT)):sha(p) for p in sorted((c.ROOT/'autorouter').glob('*.py'))}
    git_head=subprocess.run(['git','rev-parse','HEAD'],cwd=c.ROOT,capture_output=True,text=True,check=True).stdout.strip()
    return {'implementation_sha256':implementation,'git_head':git_head,'kicad':'10.0.0','freerouting':'2.5.0','files':files,'network':'engine sandbox-exec deny network*'}

def optimizer_threshold_audit(log, expected_percent):
    """Reject a logged stop threshold inconsistent with the declared profile.

    Absence of that conditional stop message is recorded as unobserved, never as
    runtime proof of the effective setting. The engine may stop for another cap.
    """
    values=[float(value) for value in re.findall(r'Stopping optimizer because .*?the threshold \(([0-9]+(?:\.[0-9]+)?)%\)',Path(log).read_text())]
    if any(abs(value-expected_percent)>1e-6 for value in values):
        raise Rejected('optimizer runtime threshold differs from declared profile: '+str(values))
    return {'expected_percent':expected_percent,'observed_stop_threshold_percent':values,
            'runtime_observation':'matched' if values else 'stop threshold not logged'}

ENGINE_NATIVE_RESERVE_SECONDS=10
ENGINE_GRACE_RESERVE_SECONDS=30

def engine_scoring_settings(variant=None):
    presets={'via_default':(50,5),'via_low':(25,3),'via_high':(100,10)}
    if variant is None:
        return {'variant':None,'argv':[]}
    if not isinstance(variant,str) or variant not in presets:
        raise Rejected('unknown engine scoring variant')
    via,plane=presets[variant]
    return {'variant':variant,'via_costs':via,'plane_via_costs':plane,
            'argv':[f'--router.scoring.via_costs={via}',f'--router.scoring.plane_via_costs={plane}']}


def engine_profile_settings(profile, remaining_seconds, *, strict_class_targets=False, scoring_variant=None):
    """Assign cooperative internal deadlines inside the outer wall budget.

    Freerouting accepts numeric seconds or HH:mm:ss, not values such as 90s.
    Its job monitor permits 30 seconds of graceful stopping. Both that grace
    and a native-finalization planning reserve are withheld uniformly. The
    supervisor and measured CPU acceptance cap remain authoritative.
    """
    if profile not in {'standard','tuned','completion-only'}: raise Rejected('unknown engine profile')
    if type(strict_class_targets) is not bool: raise Rejected('invalid static netclass target policy')
    if isinstance(remaining_seconds,bool) or not isinstance(remaining_seconds,(int,float)) or not math.isfinite(remaining_seconds):
        raise Rejected('invalid remaining engine budget')
    available=math.floor(remaining_seconds-ENGINE_NATIVE_RESERVE_SECONDS-ENGINE_GRACE_RESERVE_SECONDS)
    if available<1: raise Rejected('insufficient remaining budget for engine grace and native finalization reserves')
    job_cap=min(100 if profile=='tuned' else 60,available)
    optimizer_cap=None if profile=='completion-only' else min(90 if profile=='tuned' else 30,job_cap)
    def span(seconds): return f'{seconds//3600:02}:{seconds//60%60:02}:{seconds%60:02}'
    scoring=engine_scoring_settings(scoring_variant)
    args=['--router.autorouter.max_passes='+('100' if profile=='tuned' else '30'),
          '--router.job_timeout='+span(job_cap)]
    if strict_class_targets:
        # Pinned micro-neckdown can run during fanout even when automatic
        # neckdown is false. Exact class targets therefore exclude both paths.
        args+=['--router.automatic_neckdown=false','--router.fanout.enabled=false','--router.neck_width_um=0']
    if profile=='completion-only':
        args+=['--router.optimizer.enabled=false']
    else:
        args+=['--router.optimizer.max_threads=1','--router.optimizer.max_passes='+('50' if profile=='tuned' else '10'),
               '--router.optimizer.timeout='+span(optimizer_cap)]
        if profile=='tuned':
            # Actual pinned JAR probe verifies CLI fraction .001 -> internal .1%.
            args+=['--router.optimizer.improvement_threshold=0.001','--router.optimizer.enable_preflight_guards=false',
                   '--router.optimizer.max_consecutive_failures=100','--router.optimizer.max_consecutive_failures_pass1=100']
    args+=scoring['argv']
    return {'profile':profile,'argv':args,'scoring':scoring,'strict_class_targets':strict_class_targets,'remaining_outer_wall_seconds_at_assignment':remaining_seconds,
            'assigned_job_timeout_seconds':job_cap,'assigned_optimizer_timeout_seconds':optimizer_cap,
            'native_finalization_reserve_seconds':ENGINE_NATIVE_RESERVE_SECONDS,
            'engine_grace_reserve_seconds':ENGINE_GRACE_RESERVE_SECONDS,
            'internal_deadlines':'cooperative planning caps; external supervision and measured CPU acceptance cap remain authoritative'}

def engine_baseline(profile,adapter):
    if profile=='completion-only': return 'completion_only_probe'
    if profile=='tuned': return 'B2_tuned'
    if profile=='standard': return 'B0' if adapter=='none' else 'B1'
    raise Rejected('unknown engine profile')


def route(source, output, seconds=120, keep_existing=False, adapter='none', engine_profile='standard', *, scoring_variant=None):
    if engine_profile not in {'standard','tuned','completion-only'}: raise Rejected('unknown engine profile')
    engine_scoring_settings(scoring_variant)
    operation_started=time.monotonic()
    operation_started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
    operation_cpu=time.process_time()
    source=Path(source).resolve(strict=True); output=Path(output).resolve()
    if source.parent==output or source.parent in output.parents: raise Rejected('output must be outside source project')
    if not math.isfinite(seconds) or seconds<5 or seconds>900: raise Rejected('budget must be 5–900 seconds')
    if sha(c.JAR)!=c.JAR_SHA256: raise Rejected('engine hash mismatch')
    check_storage()
    job=Job(output,seconds)
    job.started=operation_started; job.deadline=operation_started+seconds; job.cpu_started=operation_cpu
    code=output/'code'; code.mkdir()
    for path in (c.ROOT/'autorouter').glob('*.py'): shutil.copy2(path,code/path.name)
    report={'schema':1,'status':'validator_error','accepted':False,'physical_electrical_validation':False,'schematic_parity':'not checked','source':str(source),
            'started_utc':operation_started_utc,'budget_seconds':seconds,'cpu_budget_seconds':seconds,'cpu_budget_enforcement':'postcompletion acceptance cap; no total-CPU preemption','baseline':engine_baseline(engine_profile,adapter),'adapter':adapter,'engine_profile':engine_profile,'scoring_variant':scoring_variant,'scope':'partial_completion' if keep_existing else 'whole_board_unlocked_routing',
            'tools':tool_manifest()}
    try:
        before=tree_hash(source.parent); report['source_hashes']=before
        original=preflight(source)
        shutil.copytree(source.parent,output/'snapshot'); shutil.copytree(source.parent,output/'candidate')
        snapshot=output/'snapshot'/source.name; candidate=output/'candidate'/source.name
        if tree_hash(output/'snapshot')!=before: raise Rejected('source changed during snapshot')
        task=copy.deepcopy(original)
        if not keep_existing: task[:]=[n for n in task if not isinstance(n,list) or not n or n[0] not in ROUTES or locked(n)]
        for z in sx.children(task,'zone'):
            z[:]=[n for n in z if not isinstance(n,list) or not n or n[0] not in DERIVED_ZONE]
        protected=copy.deepcopy(routes(task))
        sx.write(candidate,task)
        report['task_sha256']=sha(candidate)
        report['source_drc']=job.drc('source-drc',snapshot)
        policy=netclass_policy(candidate)
        if policy is None:
            job.native('export','export',candidate,output/'task.dsn')
        else:
            from .netclass import audit_dsn
            mapping=output/'export-netclasses.json'
            job.native('export','export',candidate,output/'task.dsn',mapping)
            native_classes=json.loads(mapping.read_text())
            # The task contains only protected routes, and its original rules.
            audit_candidate_netclasses(candidate,protected,native_classes)
            shutil.copy2(output/'task.dsn',output/'native.dsn')
            report['netclass_policy']=policy
            report['netclass_export_audit']=audit_dsn(output/'native.dsn',native_classes,json.loads(candidate.with_suffix('.kicad_pro').read_text()))
        if adapter!='none':
            from .adapter import adapt_dsn
            job.native('obstacles','obstacles',candidate,output/'obstacles.json')
            report['adapter_transformations']=adapt_dsn(output/'task.dsn',adapter,json.loads((output/'obstacles.json').read_text()))
        if policy is not None:
            report['netclass_task_audit']=audit_dsn(output/'task.dsn',native_classes,json.loads(candidate.with_suffix('.kicad_pro').read_text()))
        config_dir=output/'engine-config'; config_dir.mkdir()
        report['engine_budget']=engine_profile_settings(engine_profile,job.deadline-time.monotonic(),strict_class_targets=policy is not None,scoring_variant=scoring_variant)
        report['engine_budget']['outer_task_wall_budget_seconds']=seconds
        report['engine_budget']['outer_task_cpu_budget_seconds']=seconds
        engine_settings=report['engine_budget']['argv']
        job.step('engine',['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',c.JAVA,'-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',c.JAR,
            '--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da','--user_data_path='+str(config_dir),'--logging.file.enabled=false',
            *engine_settings,
            '-de',output/'task.dsn','-do',output/'routes.ses'])
        if engine_profile=='tuned':
            report['optimizer_threshold_audit']=optimizer_threshold_audit(output/'engine.log',0.1)
        if not (output/'routes.ses').is_file(): raise Rejected('engine emitted no SES')
        imported=output/'imported.kicad_pcb'
        job.native('import','import',candidate,imported,output/'routes.ses')
        sx.write(candidate,transplant_routes(task,sx.read(imported)))
        final_hash, native = validate_candidate(job, original, candidate, before, protected)
        report['native']=native
        job.native('metrics','metrics',candidate,output/'metrics.json')
        report['metrics']=json.loads((output/'metrics.json').read_text())
        verify_candidate_files(candidate, before, final_hash)
        if tree_hash(source.parent)!=before or tree_hash(output/'snapshot')!=before: raise Rejected('source or snapshot changed')
        report['native_report_sha256']=sha(output/'final-drc.json')
        report['candidate_sha256']=final_hash
        report['candidate']=str(candidate)
        report['invariants_unchanged']=True
        valid=report['native']['opens']==0 and report['native']['blocking']==0 and report['native']['exclusions']==0
        report['status']='routing_accepted' if valid else 'drc_rejected'
        report['accepted']=valid
        report['whole_project_drc_clean']=valid and report['native']['warnings']==0
    except Exception as exc:
        report['reason']=type(exc).__name__+': '+str(exc)
        report['status']='unsupported' if 'unsupported:' in str(exc) else 'rejected'
        report['accepted']=False
    report['steps']=job.steps
    report['wall_seconds']=time.monotonic()-job.started
    report['parent_cpu_seconds']=time.process_time()-job.cpu_started
    report['child_cpu_seconds']=sum(s.get('cpu_seconds') or 0 for s in job.steps)
    report['monitor_cpu_seconds']=sum(s.get('monitor_cpu_seconds') or 0 for s in job.steps)
    report['total_cpu_seconds']=report['parent_cpu_seconds']+report['child_cpu_seconds']+report['monitor_cpu_seconds']
    report['peak_child_rss_bytes']=max([s.get('max_rss_bytes') or 0 for s in job.steps]+[0])
    report['resource_limitations']='One sequential worker; Java 2GiB heap; group RSS4GiB and workdir512MiB polling guards may overshoot;10GiB total cache checked before task. Peak direct-child RSS and polled group RSS are different metrics. CPU descendants only if accounted for by child wait; monitoring CPU included.'
    if report['wall_seconds']>seconds:
        report['accepted']=False; report['status']='timeout'
    elif report['total_cpu_seconds']>seconds:
        report['accepted']=False; report['status']='cpu_budget_exceeded'
    report['resource_accounting_point']='Summary sampled before final receipt write; wall and measured CPU acceptance caps rechecked after that write. No hard total-CPU preemption.'
    save_json(output/'result.json',report)
    # Receipt serialization/fsync must not let an accepted result cross its cap.
    # The corrective rejected receipt need not finish inside the acceptance cap.
    completed_wall=time.monotonic()-job.started
    completed_parent_cpu=time.process_time()-job.cpu_started
    completed_cpu=completed_parent_cpu+report['child_cpu_seconds']+report['monitor_cpu_seconds']
    if completed_wall>seconds or completed_cpu>seconds:
        report.update(accepted=False,status='timeout' if completed_wall>seconds else 'cpu_budget_exceeded',
                      wall_seconds=completed_wall,parent_cpu_seconds=completed_parent_cpu,total_cpu_seconds=completed_cpu)
        save_json(output/'result.json',report)
    return report


def check_result(path):
    """Check local evidence consistency; this is not authentication or fresh DRC.

    All receipts are mutable local JSON. A party rewriting the complete evidence
    set can fabricate a consistent history; safe application needs fresh native
    validation too. This function never applies a live-editor change.
    """
    path=Path(path).resolve(strict=True)
    data=json.loads(path.read_text())
    if data.get('schema')!=1 or data.get('accepted') is not True or data.get('status')!='routing_accepted':
        raise Rejected('receipt is not an accepted routing result')
    source=Path(data['source'])
    if tree_hash(source.parent)!=data['source_hashes']: raise Rejected('stale source project')
    if tree_hash(path.parent/'snapshot')!=data['source_hashes']: raise Rejected('source snapshot changed')
    candidate=Path(data['candidate'])
    if candidate.is_symlink() or candidate.parent.is_symlink() or candidate!=path.parent/'candidate'/source.name: raise Rejected('candidate does not belong to this run')
    verify_candidate_files(candidate,data['source_hashes'],data['candidate_sha256'])
    original=preflight(source)
    current=sx.read(candidate)
    if immutable(current)!=immutable(original): raise Rejected('immutable geometry changed')
    if data.get('scope') not in {'whole_board_unlocked_routing','partial_completion'}: raise Rejected('unknown protected routing scope')
    protected=[route for route in routes(original) if data['scope']=='partial_completion' or locked(route)]
    if any(route not in routes(current) for route in protected): raise Rejected('protected route changed')

    def evidence(name):
        file=path.parent/name
        if file.is_symlink(): raise Rejected('symlink in run evidence: '+name)
        return json.loads(file.read_text())

    if netclass_policy(candidate) is not None:
        from .netclass import audit_dsn, audit_native
        native_classes=evidence('final-netclasses.json')
        audited=audit_candidate_netclasses(candidate,protected,native_classes)
        audited['native_map_file_sha256']=sha(path.parent/'final-netclasses.json')
        if evidence('final-netclass-audit.json')!=audited: raise Rejected('retained native netclass audit differs from candidate')
        process=evidence('final-netclasses-process.json')
        expected=[str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'netclasses',str(candidate),str(path.parent/'final-netclasses.json')]
        if (process.get('argv')!=expected or process.get('cwd')!=str(path.parent) or process.get('name')!='final-netclasses'
                or process.get('exit_code')!=0 or process.get('status')!='success' or process.get('cleanup_complete') is not True):
            raise Rejected('native netclass process provenance is inconsistent')
        matching=[step for step in data.get('steps',[]) if step.get('name')=='final-netclasses' and step.get('cwd')==str(path.parent)]
        if len(matching)!=1 or any(matching[0].get(key)!=value for key,value in process.items()):
            raise Rejected('native netclass step differs from retained process')
        if data.get('baseline')!='C-prototype':
            # Reconstruct the exact native export input from the frozen source,
            # never from the already-routed candidate or receipt assertions.
            task=copy.deepcopy(original)
            if data['scope']=='whole_board_unlocked_routing':
                task[:]=[node for node in task if not isinstance(node,list) or not node or node[0] not in ROUTES or locked(node)]
            for zone in sx.children(task,'zone'):
                zone[:]=[node for node in zone if not isinstance(node,list) or not node or node[0] not in DERIVED_ZONE]
            task_hash=hashlib.sha256((sx.dump(task)+'\n').encode()).hexdigest()
            exported=evidence('export-netclasses.json')
            project=json.loads(candidate.with_suffix('.kicad_pro').read_text())
            if (data.get('task_sha256')!=task_hash or exported.get('board_sha256')!=task_hash
                    or exported.get('project_sha256')!=sha(candidate.with_suffix('.kicad_pro'))
                    or exported.get('source')!=str(candidate) or exported.get('board_saved') is not False):
                raise Rejected('export netclass map differs from original routing task')
            audit_native(exported,project)
            if (data.get('netclass_policy')!=netclass_policy(candidate)
                    or data.get('netclass_export_audit')!=audit_dsn(path.parent/'native.dsn',exported,project)
                    or data.get('netclass_task_audit')!=audit_dsn(path.parent/'task.dsn',exported,project)):
                raise Rejected('retained DSN netclass audits differ from exported evidence')

    binding=evidence('final-drc-binding.json')
    native_input=path.parent/'final-drc-input'/candidate.name
    expected=dict(data['source_hashes']); expected[candidate.name]=data['candidate_sha256']
    if binding.get('source')!=str(candidate) or binding.get('input')!=str(native_input) or binding.get('saved') is not False or binding.get('before')!=expected:
        raise Rejected('final native input binding differs from candidate')
    after=binding.get('after')
    if not isinstance(after,dict) or any(after.get(name)!=digest for name,digest in expected.items()) or set(after)-set(expected)-{candidate.with_suffix('.kicad_prl').name}:
        raise Rejected('native validation changed board or rules')
    if tree_hash(native_input.parent)!=after: raise Rejected('retained native input changed')
    if sha(path.parent/'final-drc.json')!=data['native_report_sha256']: raise Rejected('native report changed')
    native=parse_report(path.parent/'final-drc.json',candidate.name)
    if native['opens'] or native['blocking'] or native['exclusions']: raise Rejected('native findings reject candidate')
    if data.get('native')!=native or data.get('invariants_unchanged') is not True: raise Rejected('receipt native summary differs from raw evidence')
    if data.get('whole_project_drc_clean') is not (native['warnings']==0): raise Rejected('receipt cleanliness claim differs from native evidence')
    metrics=evidence('metrics.json')
    if data.get('metrics')!=metrics or metrics.get('version')!='10.0.0': raise Rejected('receipt metrics differ from retained native metrics')

    process=evidence('final-drc-process.json')
    expected_argv=[str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(path.parent/'final-drc.json'),str(native_input)]
    findings=bool(native['findings'])
    if process.get('argv')!=expected_argv or process.get('cwd')!=str(path.parent) or process.get('name')!='final-drc' or process.get('exit_code')!=(5 if findings else 0) or process.get('status')!=('nonzero_exit' if findings else 'success') or process.get('cleanup_complete') is not True:
        raise Rejected('native process provenance is inconsistent')
    steps=data.get('steps')
    if not isinstance(steps,list) or not steps or any(not isinstance(step,dict) for step in steps): raise Rejected('missing process history')
    matching=[step for step in steps if step.get('name')=='final-drc' and step.get('cwd')==str(path.parent)]
    if len(matching)!=1 or any(matching[0].get(key)!=value for key,value in process.items()) or matching[0].get('validated_input_sha256')!=data['candidate_sha256'] or matching[0].get('emitted_candidate')!=str(candidate):
        raise Rejected('final native step differs from process or input binding')
    if any(step.get('status')=='cancelled' or step.get('cleanup_complete') is not True for step in steps): raise Rejected('cancelled or incomplete process cleanup in receipt')

    def number(value):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0: raise Rejected('invalid resource accounting')
        return value

    wall,budget=number(data.get('wall_seconds')),number(data.get('budget_seconds'))
    cpu_budget=number(data.get('cpu_budget_seconds'))
    if not 5<=cpu_budget<=900 or number(data.get('total_cpu_seconds'))>cpu_budget: raise Rejected('receipt exceeds its recorded CPU budget')
    if not 5<=budget<=900 or wall>budget or sum(number(step.get('wall_seconds')) for step in steps)>wall+1e-6: raise Rejected('receipt exceeds its recorded wall budget')
    child=sum(number(step.get('cpu_seconds')) for step in steps)
    monitor=sum(number(step.get('monitor_cpu_seconds')) for step in steps)
    if abs(number(data.get('child_cpu_seconds'))-child)>1e-6 or abs(number(data.get('monitor_cpu_seconds'))-monitor)>1e-6 or abs(number(data.get('total_cpu_seconds'))-(number(data.get('parent_cpu_seconds'))+child+monitor))>1e-6: raise Rejected('inconsistent CPU accounting')

    tools=data.get('tools',{})
    implementation=tools.get('implementation_sha256')
    if tools.get('kicad')!='10.0.0' or not isinstance(implementation,dict) or not implementation: raise Rejected('missing pinned implementation provenance')
    if not {'autorouter/pipeline.py','autorouter/native.py','autorouter/runner.py','autorouter/sexpr.py'}<=set(implementation): raise Rejected('incomplete implementation provenance')
    actual_code=tree_hash(path.parent/'code')
    expected_code={}
    for relative,digest in implementation.items():
        parts=Path(relative).parts
        if len(parts)!=2 or parts[0]!='autorouter' or not parts[1].endswith('.py') or actual_code.get(parts[1])!=digest:
            raise Rejected('retained implementation differs from provenance')
        expected_code[parts[1]]=digest
    if actual_code!=expected_code: raise Rejected('retained implementation file set differs from provenance')
    pins=json.loads((c.ROOT/'toolchain.lock.json').read_text())['tools']
    if any(tools.get('files',{}).get(str(c.resolve_tool_path(pin['path'])))!=pin['sha256'] for pin in pins.values()): raise Rejected('recorded tool pins differ from qualified toolchain')
    return {'current':True,'candidate':str(candidate),'candidate_sha256':data['candidate_sha256'],'applied':False,'authentication':'none; mutable local evidence consistency only','warning':'Fresh native validation is required before application; human PCB review and electrical/physical validation remain required.'}
