"""Snapshot, bounded engine, structural preservation and native validation.

Experimental whole-board completion only. Original projects are never written.
"""
from __future__ import annotations
import copy
from contextlib import contextmanager
from contextvars import ContextVar
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
import signal
import subprocess
import time
from types import FunctionType, MappingProxyType
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
    from .netclass import reject_tuning_intent
    try: reject_tuning_intent(project)
    except ValueError as exc: raise Rejected('unsupported: '+str(exc)) from exc
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

def check_edge_text_support(tree):
    """Refuse outline text intent independently of editable DRC severity.

    KiCad10 registers text_on_edge_cuts, including warning/ignore settings.
    Recognizing that metadata never permits text to become board geometry.
    Only explicit unambiguous layer selectors are qualified for surface text,
    fields, textboxes and dimensions; ordinary non-surface properties remain.
    """
    text_items={'gr_text','fp_text','gr_text_box','fp_text_box','dimension'}
    table=sx.one(tree,'layers',[])
    declared={sx.unquote(row[1]) for row in table[1:] if isinstance(row,list)
        and len(row)>=3 and isinstance(row[1],str) and sx.unquote(row[1])}
    def visit(node):
        if not isinstance(node,list) or not node:return
        key=node[0]
        if not isinstance(key,str):raise Rejected('malformed board item in text-layer check')
        surface_field=key=='property' and any(sx.children(node,k) for k in ('at','effects','layer'))
        if key in text_items or surface_field:
            layers=sx.children(node,'layer')
            if len(layers)!=1 or len(layers[0])!=2 or not isinstance(layers[0][1],str):
                raise Rejected('text/field/dimension layer semantics not qualified')
            if sx.unquote(layers[0][1])=='Edge.Cuts':
                raise Rejected('text/field/textbox/dimension on Edge.Cuts not qualified')
            if sx.unquote(layers[0][1]) not in declared:
                raise Rejected('text/field/dimension layer is not a declared source layer')
        for child in node[1:]:visit(child)
    visit(tree)


def check_rule_area_support(tree):
    """Block restrictions the pinned native validator did not detect.

    Actual placement-area-native-001 controls missed crossing prohibited
    tracks/vias in KiCad 10.0.0. Preserving a DSN obstacle is not independent
    validation. Only explicitly unrestricted areas remain in supported scope.
    """
    if sx.children(tree,'module'):
        raise Rejected('legacy module footprints not qualified')
    flags={'tracks','vias','pads','copperpour','footprints'}
    zones=list(sx.children(tree,'zone'))
    for footprint in sx.children(tree,'footprint'):
        zones.extend(sx.children(footprint,'zone'))
    for zone in zones:
        keepout=sx.one(zone,'keepout')
        placement=sx.one(zone,'placement')
        if keepout is None and placement is None:
            continue
        if (keepout is None or len(keepout)!=6
                or any(not isinstance(n,list) or len(n)!=2
                       or n[0] not in flags or n[1]!='allowed' for n in keepout[1:])
                or {n[0] for n in keepout[1:]}!=flags):
            raise Rejected('rule-area restrictions not qualified by pinned native validator')


# Registered KiCad10 metadata; global outline-text refusal remains mandatory.
KNOWN_CHECKS |= {'text_on_edge_cuts'}

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
            if key in CRITICAL_CHECKS and val!='error' and (key,val) not in {('padstack','warning'),('hole_to_hole','warning')}: reasons.append('core native check not blocking: '+key)
    rules=board.with_suffix('.kicad_dru')
    if rules.exists() and rules.read_text().strip(): reasons.append('custom rules not qualified')
    try: check_rule_area_support(t)
    except Rejected as exc: reasons.append(str(exc))
    try: check_edge_text_support(t)
    except Rejected as exc: reasons.append(str(exc))
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

def transplant_routes(original, imported, *, protected=(), audit=None, policy='exact_non_uuid_v1'):
    if policy not in {'exact_non_uuid_v1','exact_non_uuid_lock_position_v2'}:
        raise Rejected('unknown protected import policy')
    imported_routes=[convert_route_nets(n,imported,original) for n in routes(imported)]
    reconciled=[]
    if protected:
        # KiCad SES import regenerates UUIDs even for unchanged protected tracks.
        # Restore identity only after an unambiguous exact non-UUID match. Never
        # infer copper equivalence, merge/split routes or repair missing geometry.
        def identity(route):
            ids=sx.children(route,'uuid')
            if len(ids)!=1 or len(ids[0])!=2 or not isinstance(ids[0][1],str):
                raise Rejected('protected import requires unique route UUIDs')
            return ids[0][1]
        def signature(route):
            fields=[n for n in route if not isinstance(n,list) or not n or n[0]!='uuid']
            if policy=='exact_non_uuid_lock_position_v2':
                locks=[n for n in fields if n=='locked' or isinstance(n,list) and n and n[0]=='locked']
                if len(locks)>1 or locks and locks[0]!=['locked','yes']:
                    raise Rejected('protected import requires absent or single explicit locked yes')
                if locks:
                    fields.remove(locks[0]);fields.append(locks[0])
            return sx.dump(fields)
        original_counts={}
        for route in routes(original):
            key=sx.dump(route)
            original_counts[key]=original_counts.get(key,0)+1
        matches={}
        for index,route in enumerate(imported_routes):
            matches.setdefault(signature(route),[]).append(index)
        used=set()
        for route in protected:
            if original_counts.get(sx.dump(route))!=1:
                raise Rejected('protected import route is not a unique original')
            identity(route)
            indices=matches.get(signature(route),[])
            if len(indices)!=1 or indices[0] in used:
                raise Rejected('protected route missing, changed or ambiguous after import')
            used.add(indices[0])
        ids=[identity(route) for route in imported_routes]
        if len(set(ids))!=len(ids):raise Rejected('duplicate imported route UUID')
        for route in protected:
            index=matches[signature(route)][0]
            reconciled.append({'original_uuid':identity(route),'imported_uuid':identity(imported_routes[index]),
                'non_uuid_sha256':hashlib.sha256(signature(route).encode()).hexdigest()})
            imported_routes[index]=copy.deepcopy(route)
        ids=[identity(route) for route in imported_routes]
        if len(set(ids))!=len(ids):raise Rejected('restored protected route UUID collision')
    out=copy.deepcopy(original)
    out[:]=[n for n in out if not isinstance(n,list) or not n or n[0] not in ROUTES]
    out.extend(imported_routes)
    if audit is not None:
        audit.update(policy=policy,matches=reconciled,
            transplanted_routes_sha256=hashlib.sha256(sx.dump(imported_routes).encode()).hexdigest())
    return out


def check_protected_import(directory, data, original, candidate, protected):
    if 'protected_route_import' not in data:
        if data.get('scope')=='selected_nets' and protected:
            raise Rejected('selected scope requires complete protected import reconciliation')
        return  # Historical receipts keep their exact original guard.
    from .floor_route import canonical
    from .placement_clearance import read_bytes
    imported=Path(directory)/'imported.kicad_pcb'
    raw=read_bytes(imported,20*1024*1024)
    audit={'imported_sha256':hashlib.sha256(raw).hexdigest()}
    binding=data['protected_route_import']
    if not isinstance(binding,dict):raise Rejected('malformed protected import record')
    rebuilt=transplant_routes(original,sx.parse(raw.decode('utf-8')),protected=protected,audit=audit,policy=binding.get('policy'))
    if canonical(audit)!=canonical(data['protected_route_import']):raise Rejected('protected import reconciliation differs')
    if routes(sx.read(candidate))!=routes(rebuilt):raise Rejected('protected import routes differ from final candidate')

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


# Finding types are not project-setting keys: KiCad's padstack_invalid has no
# editable severity. Keep parse_report's native summary schema unchanged so old
# evidence can be rechecked under this stricter application acceptance policy.
CRITICAL_FINDINGS = CRITICAL_CHECKS | {'padstack_invalid','text_on_edge_cuts','net_conflict'}


def native_rejection_reasons(native):
    """Application policy over unchanged native evidence; never a DRC rewrite."""
    if not isinstance(native,dict) or any(type(native.get(k)) is not int or native[k]<0
                                        for k in ('opens','blocking','warnings','exclusions')):
        return ['malformed native summary counts']
    findings=native.get('findings')
    if not isinstance(findings,list): return ['missing native findings']
    ignored=native.get('ignored_checks')
    if not isinstance(ignored,list): return ['missing native ignored-check metadata']
    reasons=[]
    for check in ignored:
        if not isinstance(check,dict) or not isinstance(check.get('key'),str) or check['key'] not in KNOWN_CHECKS:
            return ['malformed or unknown native ignored check']
        if check['key'] in CRITICAL_FINDINGS:
            reasons.append('disabled policy-critical native check: '+check['key'])
    for key in ('opens','blocking','exclusions'):
        if native[key]: reasons.append('native '+key+'='+str(native[key]))
    for finding in findings:
        if (not isinstance(finding,dict) or not isinstance(finding.get('type'),str)
                or not finding['type'] or finding.get('severity') not in ('error','warning','exclusion')
                or not isinstance(finding.get('items'),list) or any(not isinstance(item,dict) for item in finding['items'])
                or ('excluded' in finding and type(finding['excluded']) is not bool)):
            return ['malformed native finding']
        # Error/exclusion checks also fail closed if a caller supplies dishonest
        # counters. check_result separately re-derives every counter from JSON.
        if finding['type'] not in KNOWN_CHECKS | {'padstack_invalid'}:
            reasons.append('unknown native finding semantics: '+finding['type'])
        if finding['severity']=='error': reasons.append('native error finding: '+finding['type'])
        if finding['severity']=='exclusion' or finding.get('excluded',False):
            reasons.append('excluded native finding: '+finding['type'])
        if finding['type'] in CRITICAL_FINDINGS:
            reasons.append('policy-critical native finding: '+finding['type']+' ('+finding['severity']+')')
    return sorted(set(reasons))


def native_accepted(native):
    return not native_rejection_reasons(native)


def check_drc_project(before, after, board_name, *, saved=False):
    """Preserve original files; native DRC may add only its local UI-state file."""
    if (not isinstance(before,dict) or not isinstance(after,dict)
            or not isinstance(board_name,str) or Path(board_name).name!=board_name
            or not board_name.endswith('.kicad_pcb') or board_name not in before
            or type(saved) is not bool):
        raise Rejected('invalid native project binding')
    for filename,digest in before.items():
        if saved and filename==board_name:
            if filename not in after: raise Rejected('native DRC removed saved board')
            continue
        if after.get(filename)!=digest: raise Rejected('native DRC modified input or rules: '+filename)
    if set(after)-set(before)-{Path(board_name).with_suffix('.kicad_prl').name}:
        raise Rejected('native DRC created unexpected project files')


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
    def drc(self,name,board,save=False,*,schematic_parity=False):
        original_input=board
        before=tree_hash(board.parent)
        validation_before=None; phase='copy'
        try:
            if not save:
                work=self.out/(name+'-input')
                board=work/board.name
                shutil.copytree(original_input.parent,work)
            phase='input_snapshot'; validation_before=tree_hash(board.parent)
            if validation_before!=before: raise Rejected('native DRC validation copy differs before native')
            report=self.out/(name+'.json')
            argv=[c.CLI,'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',report]
            if schematic_parity:argv.insert(8,'--schematic-parity')
            if save: argv+=['--save-board']
            phase='native'; result=self.step(name,argv+[board],allowed=(0,5))
            phase='output_snapshot'; after=tree_hash(board.parent)
            phase='project_preservation'; check_drc_project(before,after,board.name,saved=save)
            result['validated_input_sha256']=before[board.name]
            result['emitted_candidate']=str(original_input)
            phase='binding_publication'
            save_json(self.out/(name+'-binding.json'),{'source':str(original_input),'input':str(board),'before':before,'after':after,'saved':save})
            phase='report_parse'; parsed=parse_report(report,board.name)
            any_findings=bool(parsed['findings'])
            phase='exit_report'
            if (result['exit_code']==0)==any_findings: raise Rejected('DRC exit/report mismatch')
            return parsed
        except (Exception,KeyboardInterrupt) as exc:
            # Evidence only: retain the first failure and never normalize a
            # modified project or turn an unavailable report into a pass.
            errors=[]; after=None
            try: after=tree_hash(board.parent)
            except (Exception,KeyboardInterrupt) as capture:
                errors.append('after snapshot: '+type(capture).__name__+': '+str(capture))
            binding={'source':str(original_input),'input':str(board),'before':before,'after':after,'saved':save}
            try: save_json(self.out/(name+'-binding.json'),binding)
            except (Exception,KeyboardInterrupt) as capture:
                errors.append('binding publication: '+type(capture).__name__+': '+str(capture))
            artifacts={}
            for suffix in ('.json','.log','-process.json'):
                path=self.out/(name+suffix); artifacts[path.name]=None
                try:
                    if path.is_symlink(): raise Rejected('symlink in DRC failure artifact')
                    if path.exists():
                        if not path.is_file() or path.stat().st_size>100*1024*1024:
                            raise Rejected('invalid or oversized DRC failure artifact')
                        artifacts[path.name]={'sha256':sha(path),'bytes':path.stat().st_size}
                except (Exception,KeyboardInterrupt) as capture:
                    errors.append(path.name+': '+type(capture).__name__+': '+str(capture))
            failure={'schema':1,'passed':False,'phase':phase,
                     'error':{'type':type(exc).__name__,'message':str(exc)},'binding':binding,
                     'validation_copy_before':validation_before,'artifacts':artifacts,'capture_errors':errors}
            try: save_json(self.out/(name+'-failure.json'),failure)
            except (Exception,KeyboardInterrupt) as capture:
                errors.append('failure publication: '+type(capture).__name__+': '+str(capture))
            for error in errors: exc.add_note('DRC failure evidence: '+error)
            raise

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

def validate_candidate(job, original, candidate, source_hashes, protected, *, guidance_contract=None, guidance_basis=None, layer_contract=None, selected_names=None, schematic_parity=False):
    # A complete captured native schematic must participate in final acceptance
    # for every routing scope, including optimizer trials and fresh exports.
    schematic_parity=schematic_parity or Path(candidate).with_suffix('.kicad_sch').name in source_hashes
    check_rule_area_support(original)
    if guidance_basis is not None and guidance_contract is None:raise Rejected('guidance basis requires a contract')
    if guidance_contract is not None:
        from .floor_route import validate_contract
        validate_contract(original,candidate,source_hashes,protected,guidance_contract,job.out,guidance_basis=guidance_basis)
    # Reject mutations before native tooling is allowed to normalize anything.
    if immutable(sx.read(candidate))!=immutable(original): raise Rejected('immutable geometry changed')
    if any(n not in routes(sx.read(candidate)) for n in protected): raise Rejected('protected route changed')
    if selected_names is not None:
        from . import routing_scope as rs
        rs.audit(original,sx.read(candidate),selected_names)
    if layer_contract is not None:layer_contract['audit']=audit_layer_contract(candidate,layer_contract)
    verify_candidate_files(candidate,source_hashes)
    shutil.copytree(candidate.parent,job.out/'refill')
    refill=job.out/'refill'/candidate.name
    job.drc('refill-drc',refill,save=True)
    sx.write(candidate,transplant_fill(sx.read(candidate),sx.read(refill)))
    if immutable(sx.read(candidate))!=immutable(original): raise Rejected('immutable geometry changed after refill')
    if layer_contract is not None:layer_contract['audit']=audit_layer_contract(candidate,layer_contract)
    final_hash=sha(candidate)
    if guidance_contract is not None:
        from .floor_route import final_context
        final_context(job,original,candidate,source_hashes,protected,guidance_contract,guidance_basis=guidance_basis)
    elif netclass_policy(candidate) is not None:
        mapping=job.out/'final-netclasses.json'
        job.native('final-netclasses','netclasses',candidate,mapping)
        audited=audit_candidate_netclasses(candidate,protected,json.loads(mapping.read_text()))
        audited['native_map_file_sha256']=sha(mapping)
        save_json(job.out/'final-netclass-audit.json',audited)
    if selected_names is not None:rs.audit(original,sx.read(candidate),selected_names)
    native=job.drc('final-drc',candidate,schematic_parity=True) if schematic_parity else job.drc('final-drc',candidate)
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


def capture_preferences(report, output, request):
    """Keep the exact explicit preset and resolved overrides beside the candidate."""
    if request is None:return
    from . import preferences as pref
    raw=request['snapshot']
    effective=pref.readback(raw,request['effective'])
    path=Path(output)/'routing-preferences.json'
    with path.open('xb') as stream:stream.write(raw)
    report['routing_preferences']={'file':path.name,'sha256':hashlib.sha256(raw).hexdigest(),'effective':effective}
    preferences_fresh(output,request)


def engine_argv(directory, settings):
    """One exact invocation for native and floor guidance, also used by readback."""
    directory=Path(directory)
    return ['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(c.JAVA),
        '-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',str(c.JAR),
        '--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da',
        '--user_data_path='+str(directory/'engine-config'),'--logging.file.enabled=false',*settings,
        '-de',str(directory/'task.dsn'),'-do',str(directory/'routes.ses')]


def preferences_fresh(output, request):
    if request is None:return
    from . import preferences as pref
    from .placement_clearance import read_bytes
    pref.check_fresh(request['captured'])
    if read_bytes(Path(output)/'routing-preferences.json',64*1024)!=request['snapshot']:
        raise Rejected('captured routing preferences changed during execution')


def layer_contract(directory, source, effective, binding=None):
    """Bind source and both retained exports to independently captured choices."""
    from . import layer_policy as lp
    from .placement_clearance import read_bytes
    from .floor_route import canonical
    arguments={'allowed_names':effective['layers'],'scope':effective['scope'],
        'engine_profile':effective['profile'],'guidance_policy':effective['guidance']}
    raw=(read_bytes(Path(source),lp.MAX_BOARD_BYTES),
         read_bytes(Path(directory)/'native.dsn',lp.MAX_DSN_BYTES),
         read_bytes(Path(directory)/'task.dsn',lp.MAX_DSN_BYTES))
    derived=lp.bind(*raw,**arguments)
    if binding is not None and canonical(binding)!=canonical(derived):
        raise Rejected('layer binding differs from captured choices and source exports')
    return {'source':Path(source),'directory':Path(directory),'effective':copy.deepcopy(effective),'binding':derived}


def audit_layer_contract(candidate, contract):
    from . import layer_policy as lp
    from .placement_clearance import read_bytes
    effective=contract['effective'];directory=contract['directory']
    return lp.audit_candidate(read_bytes(contract['source'],lp.MAX_BOARD_BYTES),
        read_bytes(candidate,lp.MAX_BOARD_BYTES),read_bytes(directory/'native.dsn',lp.MAX_DSN_BYTES),
        read_bytes(directory/'task.dsn',lp.MAX_DSN_BYTES),contract['binding'],
        allowed_names=effective['layers'],scope=effective['scope'],
        engine_profile=effective['profile'],guidance_policy=effective['guidance'])


def layer_markers(directory, data):
    """Do not downgrade an incompletely removed layer contract to legacy evidence."""
    if 'layer_binding' in data or 'layer_audit' in data:return True
    def reserved(argv):
        return isinstance(argv,list) and any(isinstance(arg,str) and arg.startswith('--router.layers') for arg in argv)
    if reserved(data.get('engine_budget',{}).get('argv')):return True
    if any(reserved(step.get('argv')) for step in data.get('steps',[]) if isinstance(step,dict)):return True
    path=Path(directory)/'engine-process.json'
    if path.exists() or path.is_symlink():
        from .floor_route import read_json
        return reserved(read_json(path).get('argv'))
    return False


def selected_scope_names(data):
    """Selection is authorized only by the captured, centrally checked preset."""
    if data.get('scope')!='selected_nets':
        if any(key in data for key in ('selected_net_binding','selected_net_audit','selected_dsn_binding')):
            raise Rejected('selected-net evidence without selected scope')
        return None
    from . import preferences as pref, routing_scope as rs
    effective=pref.validate(data.get('routing_preferences',{}).get('effective'))
    if (effective['scope']!='selected_nets' or data.get('schema')!=1
            or data.get('input_policy','native')!='native'
            or type(data.get('selected_net_binding')) is not dict
            or type(data.get('selected_net_audit')) is not dict
            or type(data.get('selected_dsn_binding')) is not dict):
        raise Rejected('missing selected-net choice or preservation evidence')
    return rs.validate_names(effective['nets'])


def selected_scope_markers(directory,data):
    if any(key in data for key in ('selected_net_binding','selected_net_audit','selected_dsn_binding')):return True
    path=Path(directory)/'routing-scope-input.dsn'
    if path.exists() or path.is_symlink():return True
    def reserved(argv):
        return isinstance(argv,list) and any(isinstance(arg,str) and arg.startswith('--router.autorouter.ignore_net_classes') for arg in argv)
    if reserved(data.get('engine_budget',{}).get('argv')):return True
    path=Path(directory)/'engine-process.json'
    if path.exists() or path.is_symlink():
        from .floor_route import read_json
        return reserved(read_json(path).get('argv'))
    return False


def protected_for_record(data,original):
    names=selected_scope_names(data)
    if names is not None:
        from . import routing_scope as rs
        return rs.protected_routes(original,names)
    if data.get('scope') not in {'whole_board_unlocked_routing','partial_completion'}:
        raise Rejected('unknown protected routing scope')
    return [r for r in routes(original) if data['scope']=='partial_completion' or locked(r)]


def parity_declaration(source, source_hashes):
    return ('checked by final native DRC' if Path(source).with_suffix('.kicad_sch').name in source_hashes
            else 'unavailable: no native schematic in source project')


def selected_parity_required(data):
    # Historical whole-board receipts explicitly did not check parity. Keep
    # their evidence readable; new receipts declare the actual complete-input
    # check, and their retained native argv must agree with that declaration.
    if (data.get('scope')!='selected_nets' and data.get('schematic_parity') not in
            {'checked by final native DRC','unavailable: no native schematic in source project'}):return False
    required=Path(data['source']).with_suffix('.kicad_sch').name in data['source_hashes']
    if data.get('schematic_parity')!=parity_declaration(data['source'],data['source_hashes']):raise Rejected('schematic parity declaration differs from complete source')
    return required


def check_preferences_record(directory, data):
    """Recompute the captured choice and bind it to the actual engine invocation."""
    path=Path(directory)/'routing-preferences.json'
    if 'routing_preferences' not in data and not path.exists() and not path.is_symlink():
        if layer_markers(directory,data):raise Rejected('layer evidence requires captured routing preferences')
        if selected_scope_markers(directory,data):raise Rejected('selected-net evidence requires captured routing preferences')
        return
    from . import preferences as pref
    from .placement_clearance import read_bytes
    from .floor_route import read_json, canonical
    binding=data.get('routing_preferences')
    if not isinstance(binding,dict) or set(binding)!={'file','sha256','effective'} or binding['file']!=path.name:
        raise Rejected('missing or malformed routing preferences binding')
    raw=read_bytes(path,64*1024)
    if hashlib.sha256(raw).hexdigest()!=binding['sha256']:raise Rejected('routing preferences snapshot changed')
    effective=pref.readback(raw,binding['effective'])
    scoring='via_default' if effective['guidance']=='placement-clearance-v1' else effective['scoring_preference']
    expected={'scope':effective['scope'],'budget_seconds':effective['seconds'],'cpu_budget_seconds':effective['seconds'],
              'adapter':effective['adapter'],'engine_profile':effective['profile'],'scoring_variant':scoring}
    if any(data.get(key)!=value for key,value in expected.items()) or data.get('input_policy','native')!=effective['guidance']:
        raise Rejected('routing result differs from captured preferences')
    assigned=data.get('engine_budget',{})
    settings=engine_profile_settings(effective['profile'],assigned.get('remaining_outer_wall_seconds_at_assignment'),
        strict_class_targets=effective['guidance']!='native' or data.get('netclass_policy') is not None or effective['scope']=='selected_nets',scoring_variant=scoring)
    settings.update(outer_task_wall_budget_seconds=effective['seconds'],outer_task_cpu_budget_seconds=effective['seconds'])
    if effective['layers']!='source_all':
        if type(data.get('layer_binding')) is not dict or type(data.get('layer_audit')) is not dict:
            raise Rejected('missing final layer binding or audit')
        contract=layer_contract(directory,data['source'],effective,data['layer_binding'])
        audited=audit_layer_contract(Path(data['candidate']),contract)
        if canonical(audited)!=canonical(data['layer_audit']):raise Rejected('final layer audit differs from actual candidate')
        settings['argv'].append(contract['binding']['engine_argument'])
    elif layer_markers(directory,data):raise Rejected('unexpected layer restriction without captured explicit layers')
    names=selected_scope_names(data)
    if names is not None:
        from . import routing_scope as rs
        source=Path(data['source']);candidate=Path(data['candidate'])
        if (canonical(rs.bind(read_bytes(source),names))!=canonical(data['selected_net_binding'])
                or data.get('task_sha256')!=data['selected_net_binding'].get('task_sha256')
                or canonical(rs.audit(preflight(source),sx.read(candidate),names))!=canonical(data['selected_net_audit'])):
            raise Rejected('selected-net source binding or final copper audit differs')
        emitted,dsn_binding=rs.partition_dsn(read_bytes(Path(directory)/'routing-scope-input.dsn',20*1024**2),names)
        if (canonical(dsn_binding)!=canonical(data['selected_dsn_binding'])
                or emitted!=read_bytes(Path(directory)/'task.dsn',20*1024**2)):
            raise Rejected('selected-net engine class partition differs')
        if data['adapter']=='none':
            if read_bytes(Path(directory)/'native.dsn',20*1024**2)!=read_bytes(Path(directory)/'routing-scope-input.dsn',20*1024**2):
                raise Rejected('selected-net unadapted export differs')
        elif data.get('adapter_transformations',{}).get('output_sha256')!=dsn_binding['input_sha256']:
            raise Rejected('selected-net adapter/partition lineage differs')
        from .adapter import _parse_dsn
        if sx.one(_parse_dsn(read_bytes(Path(directory)/'native.dsn',20*1024**2).decode()),'network')!=sx.one(_parse_dsn(read_bytes(Path(directory)/'routing-scope-input.dsn',20*1024**2).decode()),'network'):
            raise Rejected('selected-net adapter changed original network or class rules')
        if dsn_binding['engine_argument'] is not None:settings['argv'].append(dsn_binding['engine_argument'])
        selected_parity_required(data)
    if settings!=assigned:raise Rejected('engine budget differs from captured preferences')
    steps=[step for step in data.get('steps',[]) if step.get('name')=='engine']
    if len(steps)!=1:raise Rejected('missing unique preference-bound engine step')
    process=read_json(Path(directory)/'engine-process.json')
    if process!=steps[0] or process.get('status')!='success' or process.get('exit_code')!=0 or process.get('cleanup_complete') is not True:
        raise Rejected('engine preference process provenance differs')
    if process.get('argv')!=engine_argv(directory,settings['argv']) or process.get('cwd')!=str(directory):
        raise Rejected('engine argv or cwd differs from captured preferences')


def route(source, output, seconds=120, keep_existing=False, adapter='none', engine_profile='standard', *, scoring_variant=None, guidance_policy='native', settings_path=None, preference_overrides=None, _preferences=None):
    if settings_path is not None or preference_overrides is not None:
        if (seconds!=120 or keep_existing is not False or adapter!='none' or engine_profile!='standard'
                or scoring_variant is not None or guidance_policy!='native' or _preferences is not None):
            raise Rejected('pass explicit settings overrides through preference_overrides, not mixed route arguments')
        from . import preferences as pref
        from .floor_route import child_cpu
        request={'started':time.monotonic(),'parent_cpu':time.process_time(),'child_cpu':child_cpu(),
                 'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        captured=pref.load(settings_path) if settings_path is not None else None
        effective=pref.resolve(captured,preference_overrides)
        request.update(captured=captured,effective=effective,snapshot=pref.snapshot(captured,preference_overrides))
        def interrupted(signum,frame):raise KeyboardInterrupt
        handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
        try:
            for sig in handlers:signal.signal(sig,interrupted)
            return route(source,output,**pref.route_arguments(effective),_preferences=request)
        finally:
            for sig,handler in handlers.items():signal.signal(sig,handler)
    if guidance_policy not in {'native','board-floors-v1','placement-clearance-v1'}: raise Rejected('unknown guidance policy')
    if guidance_policy in {'board-floors-v1','placement-clearance-v1'}:
        from .floor_route import route as floor_route
        return floor_route(source,output,seconds,keep_existing,adapter,engine_profile,scoring_variant,guidance_policy=guidance_policy,preferences=_preferences)
    if engine_profile not in {'standard','tuned','completion-only'}: raise Rejected('unknown engine profile')
    engine_scoring_settings(scoring_variant)
    operation_started=_preferences['started'] if _preferences else time.monotonic()
    operation_started_utc=_preferences['started_utc'] if _preferences else datetime.datetime.now(datetime.timezone.utc).isoformat()
    operation_cpu=_preferences['parent_cpu'] if _preferences else time.process_time()
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
        capture_preferences(report,output,_preferences)
        before=tree_hash(source.parent); report['source_hashes']=before
        original=preflight(source)
        selected=_preferences['effective'].get('nets') if _preferences and _preferences['effective']['scope']=='selected_nets' else None
        parity=source.with_suffix('.kicad_sch').name in before
        report['schematic_parity']=parity_declaration(source,before)
        if selected is not None:
            from . import routing_scope as rs
            from .placement_clearance import read_bytes
            report['scope']='selected_nets'
            report['selected_net_binding']=rs.bind(read_bytes(source),selected)
        if _preferences is not None and _preferences['effective']['layers']!='source_all':
            from .layer_policy import _source_layers, _route_map
            _source_layers(original)
            _route_map(original)
        shutil.copytree(source.parent,output/'snapshot'); shutil.copytree(source.parent,output/'candidate')
        snapshot=output/'snapshot'/source.name; candidate=output/'candidate'/source.name
        if tree_hash(output/'snapshot')!=before: raise Rejected('source changed during snapshot')
        task=copy.deepcopy(original)
        if selected is not None:task=rs.task(original,selected)
        elif not keep_existing: task[:]=[n for n in task if not isinstance(n,list) or not n or n[0] not in ROUTES or locked(n)]
        for z in sx.children(task,'zone'):
            z[:]=[n for n in z if not isinstance(n,list) or not n or n[0] not in DERIVED_ZONE]
        protected=copy.deepcopy(routes(task))
        sx.write(candidate,task)
        report['task_sha256']=sha(candidate)
        report['source_drc']=job.drc('source-drc',snapshot)
        policy=netclass_policy(candidate)
        if policy is None:
            job.native('export','export',candidate,output/'task.dsn')
            shutil.copy2(output/'task.dsn',output/'native.dsn')
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
        report['native_dsn_sha256']=sha(output/'native.dsn')
        if adapter!='none':
            from .adapter import adapt_dsn
            job.native('obstacles','obstacles',candidate,output/'obstacles.json')
            report['adapter_transformations']=adapt_dsn(output/'task.dsn',adapter,json.loads((output/'obstacles.json').read_text()))
        if policy is not None:
            report['netclass_task_audit']=audit_dsn(output/'task.dsn',native_classes,json.loads(candidate.with_suffix('.kicad_pro').read_text()))
        selection_argument=None
        if selected is not None:
            shutil.copy2(output/'task.dsn',output/'routing-scope-input.dsn')
            emitted,report['selected_dsn_binding']=rs.partition_dsn((output/'routing-scope-input.dsn').read_bytes(),selected)
            (output/'task.dsn').write_bytes(emitted)
            selection_argument=report['selected_dsn_binding']['engine_argument']
        report['task_dsn_sha256']=sha(output/'task.dsn')
        layers=None
        if _preferences is not None and _preferences['effective']['layers']!='source_all':
            layers=layer_contract(output,source,_preferences['effective'])
            report['layer_binding']=layers['binding']
        config_dir=output/'engine-config'; config_dir.mkdir()
        report['engine_budget']=engine_profile_settings(engine_profile,job.deadline-time.monotonic(),strict_class_targets=policy is not None or selected is not None,scoring_variant=scoring_variant)
        report['engine_budget']['outer_task_wall_budget_seconds']=seconds
        report['engine_budget']['outer_task_cpu_budget_seconds']=seconds
        engine_settings=report['engine_budget']['argv']
        if layers is not None:engine_settings.append(layers['binding']['engine_argument'])
        if selection_argument is not None:engine_settings.append(selection_argument)
        preferences_fresh(output,_preferences)
        job.step('engine',engine_argv(output,engine_settings))
        if engine_profile=='tuned':
            report['optimizer_threshold_audit']=optimizer_threshold_audit(output/'engine.log',0.1)
        if not (output/'routes.ses').is_file(): raise Rejected('engine emitted no SES')
        imported=output/'imported.kicad_pcb'
        job.native('import','import',candidate,imported,output/'routes.ses')
        reconciliation={}
        sx.write(candidate,transplant_routes(task,sx.read(imported),protected=protected,audit=reconciliation,
            policy='exact_non_uuid_lock_position_v2'))
        if protected:report['protected_route_import']={'imported_sha256':sha(imported),**reconciliation}
        extra={'selected_names':selected,'schematic_parity':parity} if selected is not None else {}
        final_hash, native = validate_candidate(job, original, candidate, before, protected,layer_contract=layers,**extra)
        if selected is not None:report['selected_net_audit']=rs.audit(original,sx.read(candidate),selected)
        if layers is not None:report['layer_audit']=layers['audit']
        report['native']=native
        job.native('metrics','metrics',candidate,output/'metrics.json')
        report['metrics']=json.loads((output/'metrics.json').read_text())
        verify_candidate_files(candidate, before, final_hash)
        if tree_hash(source.parent)!=before or tree_hash(output/'snapshot')!=before: raise Rejected('source or snapshot changed')
        report['native_report_sha256']=sha(output/'final-drc.json')
        report['candidate_sha256']=final_hash
        report['candidate']=str(candidate)
        report['invariants_unchanged']=True
        report['native_rejection_reasons']=native_rejection_reasons(native)
        valid=native_accepted(native)
        report['status']='routing_accepted' if valid else 'drc_rejected'
        report['accepted']=valid
        report['whole_project_drc_clean']=valid and report['native']['warnings']==0
        preferences_fresh(output,_preferences)
    except KeyboardInterrupt:
        if _preferences is None:raise
        report.update(accepted=False,status='cancelled',reason='interrupted route')
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
    if _preferences is not None:
        from .floor_route import publish,child_cpu,evidence_inventory
        completed=evidence_inventory(output)
        def remaining():
            return min(job.deadline-time.monotonic(),seconds-(time.process_time()-job.cpu_started+child_cpu()-_preferences['child_cpu']))
        def account():
            report.update(wall_seconds=time.monotonic()-job.started,parent_cpu_seconds=time.process_time()-job.cpu_started)
            report['control_child_cpu_seconds']=max(0,child_cpu()-_preferences['child_cpu']-report['child_cpu_seconds']-report['monitor_cpu_seconds'])
            report['total_cpu_seconds']=sum(report[key] for key in ('parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','control_child_cpu_seconds'))
            report['resource_accounting_point']='Stored totals precede guarded publication; final wall/full CPU acceptance caps include all preference intake, readback and freshness checks.'
            if report['wall_seconds']>seconds or report['total_cpu_seconds']>seconds:
                report.update(accepted=False,status='budget_exceeded')
            if not report['accepted']:report['whole_project_drc_clean']=False
        def stable():
            if report['accepted']:
                if tool_manifest()!=report['tools']:raise Rejected('runtime changed during preference publication')
                if evidence_inventory(output)!=completed:raise Rejected('completed preference routing evidence changed')
                if tree_hash(source.parent)!=before or tree_hash(output/'snapshot')!=before:
                    raise Rejected('source changed during preference publication')
            preferences_fresh(output,_preferences)  # Last: metadata reads above may yield to another writer.
        return publish(output,report,stable,account,remaining)
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


_readback_session=ContextVar('autorouter_validated_readback_session',default=None)


@contextmanager
def validation_readback_session():
    """Reuse bounded placement consistency checks only within this invocation.

    Every reuse hashes the complete evidence/source trees and actual tool/code
    identity twice. Native execution and candidate acceptance are never cached.
    Hot replacement of checker functions invalidates reuse. No disk cache exists.
    """
    from . import (adapter,board_floor,floor_context,floor_route,layer_policy,
                   netclass,placement_clearance,placement_strategy,
                   placement_transform,preferences,runner,strategy)
    import sys
    modules=(sys.modules[__name__],c,sx,adapter,board_floor,floor_context,
             floor_route,layer_policy,netclass,placement_clearance,
             placement_strategy,placement_transform,preferences,runner,strategy)
    existing=_readback_session.get()
    state=existing if existing is not None else {'entries':{},'modules':modules}
    token=_readback_session.set(state)
    try:
        yield
    except BaseException:
        state['entries'].clear()
        raise
    finally:
        if existing is None:state['entries'].clear()
        _readback_session.reset(token)


def _readback_live_identity(modules):
    """Bound current policy constants as well as callable/code identities."""
    count=0
    def value(item,depth=0):
        nonlocal count
        count+=1
        if count>20000 or depth>16:raise Rejected('readback policy identity exceeds bounds')
        kind=type(item).__name__
        if item is None or type(item) in (str,bool,int,float):return (kind,item)
        if isinstance(item,Path):return ('path',str(item))
        if isinstance(item,re.Pattern):return ('regex',item.pattern,item.flags)
        if type(item) is bytes:return ('bytes',item.hex())
        if isinstance(item,(dict,MappingProxyType)):
            return (kind,tuple(sorted((value(k,depth+1),value(v,depth+1)) for k,v in item.items())))
        if type(item) in (tuple,list,set,frozenset):
            rows=tuple(value(x,depth+1) for x in item)
            return (kind,tuple(sorted(rows)) if type(item) in (set,frozenset) else rows)
        raise Rejected('unsupported mutable readback policy identity')
    rows=[]
    for module in modules:
        for name,item in sorted(vars(module).items()):
            if callable(item):
                function=(id(item.__code__),value(item.__defaults__),value(item.__kwdefaults__)) if isinstance(item,FunctionType) else None
                rows.append((module.__name__,name,id(item),function))
            elif name.strip('_').isupper():rows.append((module.__name__,name,value(item)))
    if len(repr(rows).encode())>1024*1024:raise Rejected('readback policy identity byte ceiling')
    return tuple(rows)


def _readback_witness(path,data,state):
    from . import placement_clearance as pc,placement_strategy as ps
    source=Path(data['source'])
    if not source.is_absolute() or source!=source.resolve(strict=True):
        raise Rejected('noncanonical placement source in readback session')
    limit,files=(ps.LIMIT,ps.MAX_FILES) if data['schema']==5 else (100*1024*1024,2000)
    evidence=pc.inventory(path.parent,max_bytes=limit,max_files=files,
                          max_entries=files*2,with_directories=True)
    original=pc.inventory(source.parent,with_directories=True)
    live=_readback_live_identity(state['modules'])
    return (evidence,original,hashlib.sha256(pc.read_bytes(c.ROOT/'toolchain.lock.json')).hexdigest(),
            tool_manifest(),live,str(c.ROOT),str(c.CLI),str(c.PYTHON),str(c.PCBNEW),str(c.JAVA),str(c.JAR))


def check_result(path):
    """Check evidence; optional scoped reuse never substitutes fresh native DRC."""
    state=_readback_session.get()
    if state is None:return _check_result_uncached(path)
    try:
        from .floor_route import read_json
        from .placement_clearance import read_bytes
        target=Path(path).absolute()
        raw=read_bytes(target)  # Reject symlink aliases before resolving them.
        data=read_json(target)
        if (target.name!='result.json' or target!=target.resolve(strict=True)
                or type(data.get('schema')) is not int or data['schema'] not in (3,4,5)
                or data.get('accepted') is not True or data.get('status')!='routing_accepted'
                or data.get('input_policy') not in {'placement-clearance-v1','placement-search-v1','placement-pruning-v1'}):
            return _check_result_uncached(path)
        before=_readback_witness(target,data,state)
        if before[0][0].get(target.name)!=hashlib.sha256(raw).hexdigest():
            raise Rejected('placement receipt changed before cached readback')
        entry=state['entries'].get(target)
        if entry is not None and entry[0]==before:
            if _readback_witness(target,data,state)!=before:
                raise Rejected('placement evidence changed during cached readback')
            return copy.deepcopy(entry[1])
        state['entries'].pop(target,None)
        result=_check_result_uncached(target)
        if _readback_witness(target,data,state)!=before:
            raise Rejected('placement evidence changed during full readback')
        if len(state['entries'])>=8:state['entries'].pop(next(iter(state['entries'])))
        state['entries'][target]=(before,copy.deepcopy(result))
        return result
    except BaseException:
        state['entries'].clear()
        raise


def check_resource_accounting(data, *, child_key='child_cpu_seconds'):
    """Shared sequential receipt budgets and finite parent/child CPU algebra."""
    def number(value):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
            raise Rejected('invalid resource accounting')
        return value
    steps=data['steps']
    wall,budget=number(data.get('wall_seconds')),number(data.get('budget_seconds'))
    cpu_budget=number(data.get('cpu_budget_seconds'))
    if not 5<=cpu_budget<=900 or number(data.get('total_cpu_seconds'))>cpu_budget:
        raise Rejected('receipt exceeds its recorded CPU budget')
    if not 5<=budget<=900 or wall>budget or sum(number(step.get('wall_seconds')) for step in steps)>wall+1e-6:
        raise Rejected('receipt exceeds its recorded wall budget')
    child=sum(number(step.get('cpu_seconds')) for step in steps)
    monitor=sum(number(step.get('monitor_cpu_seconds')) for step in steps)
    control_child=number(data.get('control_child_cpu_seconds',0))
    if (abs(number(data.get(child_key))-child)>1e-6
            or abs(number(data.get('monitor_cpu_seconds'))-monitor)>1e-6
            or abs(number(data.get('total_cpu_seconds'))-(number(data.get('parent_cpu_seconds'))+child+monitor+control_child))>1e-6):
        raise Rejected('inconsistent CPU accounting')


def _check_result_uncached(path):
    """Check local evidence consistency; this is not authentication or fresh DRC.

    All receipts are mutable local JSON. A party rewriting the complete evidence
    set can fabricate a consistent history; safe application needs fresh native
    validation too. This function never applies a live-editor change.
    """
    path=Path(path).resolve(strict=True)
    from .floor_route import receipt_policy, read_json
    from .placement_clearance import read_bytes as bounded_bytes
    receipt_digest=hashlib.sha256(bounded_bytes(path)).hexdigest()
    # Parse once strictly before policy dispatch; duplicate selectors cannot hide schema3.
    data=read_json(path)
    if selected_scope_markers(path.parent,data) and data.get('scope')!='selected_nets':
        raise Rejected('selected-net evidence cannot downgrade routing scope')
    from . import placement_strategy as ps
    input_policy=ps.POLICY if ps.recognize(data,path.parent) else receipt_policy(data,path.parent)
    placement_backed=input_policy in {'placement-clearance-v1','placement-search-v1',ps.POLICY}
    # Captured-choice runs use the shared bounded reader for a complete witness,
    # including original rule copies and native evidence, before interpreting it.
    # Recheck after every late settings/process read; board-only layer checks
    # cannot detect a concurrently changed project file or native report.
    preferences_guarded=('routing_preferences' in data or (path.parent/'routing-preferences.json').exists()
        or (path.parent/'routing-preferences.json').is_symlink() or layer_markers(path.parent,data))
    if preferences_guarded:
        from .placement_clearance import evidence_inventory as bounded_evidence, inventory as bounded_inventory
        readback_material=bounded_evidence(path.parent)
    if placement_backed:
        from .placement_clearance import evidence_inventory as bounded_evidence
        (ps.evidence_inventory if input_policy==ps.POLICY else bounded_evidence)(path.parent)
        if input_policy!=ps.POLICY:bounded_bytes(path.parent/'native.dsn',20*1024*1024)
    if data.get('schema') not in (1,2,3,4,5) or data.get('accepted') is not True or data.get('status')!='routing_accepted':
        raise Rejected('receipt is not an accepted routing result')
    source=Path(data['source'])
    source_inventory=tree_hash
    if placement_backed:
        from .placement_clearance import inventory as source_inventory
    if source_inventory(source.parent)!=data['source_hashes']: raise Rejected('stale source project')
    if source_inventory(path.parent/'snapshot')!=data['source_hashes']: raise Rejected('source snapshot changed')
    candidate=Path(data['candidate'])
    if candidate.is_symlink() or candidate.parent.is_symlink() or candidate!=path.parent/'candidate'/source.name: raise Rejected('candidate does not belong to this run')
    if placement_backed:
        from .placement_clearance import verify_candidate as bounded_candidate
        bounded_candidate(candidate,data['source_hashes'],data['candidate_sha256'])
    else:verify_candidate_files(candidate,data['source_hashes'],data['candidate_sha256'])
    original=preflight(source)
    current=sx.read(candidate)
    if immutable(current)!=immutable(original): raise Rejected('immutable geometry changed')
    protected=protected_for_record(data,original)
    if any(route not in routes(current) for route in protected): raise Rejected('protected route changed')
    check_protected_import(path.parent,data,original,candidate,protected)

    def evidence(name):
        file=path.parent/name
        if file.is_symlink(): raise Rejected('symlink in run evidence: '+name)
        return read_json(file) if placement_backed else json.loads(file.read_text())

    # New runs retain both representations. Older receipts remain explicitly
    # limited to the evidence they originally captured; never synthesize it.
    if data.get('scope')=='selected_nets' or 'native_dsn_sha256' in data or 'task_dsn_sha256' in data:
        for name,field in [('native.dsn','native_dsn_sha256'),('task.dsn','task_dsn_sha256')]:
            file=path.parent/name
            if file.is_symlink() or not file.is_file() or data.get(field)!=sha(file):
                raise Rejected('retained routing export changed or incomplete: '+name)

    if input_policy in {'board-floors-v1','placement-clearance-v1','placement-search-v1'}:
        from .floor_route import check_floor_result
        check_floor_result(path.parent,data,original,candidate,protected)
    elif input_policy==ps.POLICY:
        ps.check_pruning_result(path.parent,data,original,candidate,protected)
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
            if data['scope']=='selected_nets':
                from . import routing_scope as rs
                task=rs.task(original,selected_scope_names(data))
            elif data['scope']=='whole_board_unlocked_routing':
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
                    or data.get('netclass_task_audit')!=audit_dsn(path.parent/('routing-scope-input.dsn' if data['scope']=='selected_nets' else 'task.dsn'),exported,project)):
                raise Rejected('retained DSN netclass audits differ from exported evidence')

    binding=evidence('final-drc-binding.json')
    native_input=path.parent/'final-drc-input'/candidate.name
    expected=dict(data['source_hashes']); expected[candidate.name]=data['candidate_sha256']
    if binding.get('source')!=str(candidate) or binding.get('input')!=str(native_input) or binding.get('saved') is not False or binding.get('before')!=expected:
        raise Rejected('final native input binding differs from candidate')
    after=binding.get('after')
    check_drc_project(expected,after,candidate.name)
    if tree_hash(native_input.parent)!=after: raise Rejected('retained native input changed')
    if sha(path.parent/'final-drc.json')!=data['native_report_sha256']: raise Rejected('native report changed')
    if placement_backed:read_json(path.parent/'final-drc.json')
    native=parse_report(path.parent/'final-drc.json',candidate.name)
    reasons=native_rejection_reasons(native)
    if reasons: raise Rejected('native findings reject candidate: '+'; '.join(reasons))
    if data.get('native')!=native or data.get('invariants_unchanged') is not True: raise Rejected('receipt native summary differs from raw evidence')
    if data.get('whole_project_drc_clean') is not (native['warnings']==0): raise Rejected('receipt cleanliness claim differs from native evidence')
    metrics=evidence('metrics.json')
    if data.get('metrics')!=metrics or metrics.get('version')!='10.0.0': raise Rejected('receipt metrics differ from retained native metrics')

    process=evidence('final-drc-process.json')
    expected_argv=[str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(path.parent/'final-drc.json'),str(native_input)]
    if selected_parity_required(data):expected_argv.insert(8,'--schematic-parity')
    if input_policy in {'board-floors-v1','placement-clearance-v1','placement-search-v1',ps.POLICY}:
        from .floor_route import SANDBOX
        expected_argv=SANDBOX+expected_argv
    findings=bool(native['findings'])
    if process.get('argv')!=expected_argv or process.get('cwd')!=str(path.parent) or process.get('name')!='final-drc' or process.get('exit_code')!=(5 if findings else 0) or process.get('status')!=('nonzero_exit' if findings else 'success') or process.get('cleanup_complete') is not True:
        raise Rejected('native process provenance is inconsistent')
    steps=data.get('steps')
    if not isinstance(steps,list) or not steps or any(not isinstance(step,dict) for step in steps): raise Rejected('missing process history')
    matching=[step for step in steps if step.get('name')=='final-drc' and step.get('cwd')==str(path.parent)]
    if len(matching)!=1 or any(matching[0].get(key)!=value for key,value in process.items()) or matching[0].get('validated_input_sha256')!=data['candidate_sha256'] or matching[0].get('emitted_candidate')!=str(candidate):
        raise Rejected('final native step differs from process or input binding')
    if any(step.get('status')=='cancelled' or step.get('cleanup_complete') is not True for step in steps): raise Rejected('cancelled or incomplete process cleanup in receipt')
    check_preferences_record(path.parent,data)

    check_resource_accounting(data)

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
    result={'current':True,'candidate':str(candidate),'candidate_sha256':data['candidate_sha256'],'applied':False,'authentication':'none; mutable local evidence consistency only','warning':'Fresh native validation is required before application; human PCB review and electrical/physical validation remain required.'}
    if input_policy in {'board-floors-v1','placement-clearance-v1','placement-search-v1',ps.POLICY}: result['input_policy']=input_policy
    if placement_backed:
        from .placement_clearance import final_freshness
        (ps.final_freshness if input_policy==ps.POLICY else final_freshness)(path.parent,data)
        if hashlib.sha256(bounded_bytes(path)).hexdigest()!=receipt_digest:raise Rejected('placement receipt changed during readback')
    check_preferences_record(path.parent,data)
    if 'routing_preferences' in data or (path.parent/'routing-preferences.json').exists() or layer_markers(path.parent,data):
        if hashlib.sha256(bounded_bytes(path)).hexdigest()!=receipt_digest:
            raise Rejected('preference receipt changed during readback')
    if 'protected_route_import' in data:
        check_protected_import(path.parent,data,original,candidate,protected)
        verify_candidate_files(candidate,data['source_hashes'],data['candidate_sha256'])
        if hashlib.sha256(bounded_bytes(path)).hexdigest()!=receipt_digest:
            raise Rejected('protected import receipt changed during readback')
    if preferences_guarded:
        if bounded_inventory(source.parent,max_bytes=100*1024*1024)!=data['source_hashes']:
            raise Rejected('source project changed during preference readback')
        if bounded_evidence(path.parent)!=readback_material:
            raise Rejected('complete preference routing evidence changed during readback')
    return result
