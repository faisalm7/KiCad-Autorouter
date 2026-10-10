"""Snapshot, bounded engine, structural preservation and native validation.

Experimental whole-board completion only. Original projects are never written.
"""
from __future__ import annotations
import copy
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import resource
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

def preflight(board):
    t=sx.read(board)
    reasons=[]
    if t[0]!='kicad_pcb': reasons.append('not a KiCad board')
    if sx.one(t,'version')[1] not in {'20241229','20260206'}: reasons.append('unqualified board format version')
    layers=sx.one(t,'layers',[])
    if sum(isinstance(x,list) and len(x)>2 and x[2]=='signal' for x in layers) not in (2,4): reasons.append('requires 2 or 4 copper layers')
    project=board.with_suffix('.kicad_pro')
    if not project.is_file(): reasons.append('complete .kicad_pro required')
    else:
        p=json.loads(project.read_text()); settings=p.get('board',{}).get('design_settings',{})
        nc=p.get('net_settings',{})
        if nc.get('netclass_patterns') or nc.get('netclass_assignments') or len(nc.get('classes',[]))>1: reasons.append('netclass bindings not qualified')
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
    return {'opens':len(data['unconnected_items']), 'blocking':sum(v['severity']=='error' for v in data['violations']+data['schematic_parity']),
            'warnings':sum(v['severity']=='warning' for v in findings), 'exclusions':sum(v['severity']=='exclusion' for v in findings),
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
    native=job.drc('final-drc',candidate)
    verify_candidate_files(candidate,source_hashes,final_hash)
    return final_hash,native


def tool_manifest():
    files={str(p):sha(p) for p in (c.CLI,c.PYTHON,c.JAVA,c.JAR) if p.is_file()}
    if c.PCBNEW.is_file(): files[str(c.PCBNEW)]=sha(c.PCBNEW)
    expected=json.loads((c.ROOT/'toolchain.lock.json').read_text())['tools']
    for name, pin in expected.items():
        path=Path(pin['path'])
        if files.get(str(path))!=pin['sha256']: raise Rejected('pinned tool changed or missing: '+name)
    implementation={str(p.relative_to(c.ROOT)):sha(p) for p in sorted((c.ROOT/'autorouter').glob('*.py'))}
    git_head=subprocess.run(['git','rev-parse','HEAD'],cwd=c.ROOT,capture_output=True,text=True,check=True).stdout.strip()
    return {'implementation_sha256':implementation,'git_head':git_head,'kicad':'10.0.0','freerouting':'2.5.0','files':files,'network':'engine sandbox-exec deny network*'}

def route(source, output, seconds=120, keep_existing=False, adapter='none'):
    operation_started=time.monotonic()
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
            'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'budget_seconds':seconds,'baseline':'B0' if adapter=='none' else 'B1','adapter':adapter,'scope':'partial_completion' if keep_existing else 'whole_board_unlocked_routing',
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
        job.native('export','export',candidate,output/'task.dsn')
        if adapter!='none':
            from .adapter import adapt_dsn
            job.native('obstacles','obstacles',candidate,output/'obstacles.json')
            report['adapter_transformations']=adapt_dsn(output/'task.dsn',adapter,json.loads((output/'obstacles.json').read_text()))
        config_dir=output/'engine-config'; config_dir.mkdir()
        job.step('engine',['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',c.JAVA,'-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',c.JAR,
            '--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da','--user_data_path='+str(config_dir),'--logging.file.enabled=false',
            '--router.autorouter.max_passes=30','--router.optimizer.max_threads=1','--router.optimizer.max_passes=10','--router.job_timeout=60s','--router.optimizer.timeout=30s',
            '-de',output/'task.dsn','-do',output/'routes.ses'])
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
    save_json(output/'result.json',report)
    return report


def check_result(path):
    """Check a local receipt remains applicable; never applies a live-editor change."""
    path=Path(path).resolve(strict=True)
    data=json.loads(path.read_text())
    if data.get('schema')!=1 or data.get('accepted') is not True or data.get('status')!='routing_accepted':
        raise Rejected('receipt is not an accepted routing result')
    source=Path(data['source'])
    if tree_hash(source.parent)!=data['source_hashes']: raise Rejected('stale source project')
    candidate=Path(data['candidate'])
    if candidate.parent.parent!=path.parent: raise Rejected('candidate does not belong to this run')
    verify_candidate_files(candidate,data['source_hashes'],data['candidate_sha256'])
    if sha(path.parent/'final-drc.json')!=data['native_report_sha256']: raise Rejected('native report changed')
    native=parse_report(path.parent/'final-drc.json',candidate.name)
    if native['opens'] or native['blocking'] or native['exclusions']: raise Rejected('native findings reject candidate')
    return {'current':True,'candidate':str(candidate),'candidate_sha256':data['candidate_sha256'],'applied':False,'warning':'Human PCB review and electrical/physical validation remain required.'}
