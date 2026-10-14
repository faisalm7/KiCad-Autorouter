"""Snapshot, bounded engine, structural preservation and native validation.

Experimental whole-board completion only. Original projects are never written.
"""
from __future__ import annotations
import copy
from contextlib import contextmanager
from contextvars import ContextVar
import datetime
from dataclasses import dataclass
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
from .runner import run, _workdir_bytes

ROUTES={'segment','via','arc'}
NORMAL_DRC_LOCAL_SETTINGS_POLICY='job-owned-prl-immutable-v1'
DERIVED_ZONE={'filled_polygon','fill_segments'}
CRITICAL_CHECKS={'hole_clearance','hole_to_hole','hole_near_hole','starved_thermal','zones_intersect','padstack','items_not_allowed','through_hole_pad_without_hole','unconnected_items','shorting_items','clearance','track_width','via_diameter','annular_width','drill_out_of_range','copper_edge_clearance','invalid_outline','tracks_crossing'}
CRITICAL_CHECKS |= {'track_on_post_machined_layer'}

# KiCad 10 keys observed in pinned project settings / native default report.
KNOWN_CHECKS = CRITICAL_CHECKS | set('annular_width clearance connection_width copper_edge_clearance copper_sliver courtyards_overlap creepage diff_pair_gap_out_of_range diff_pair_uncoupled_length_too_long drill_out_of_range duplicate_footprints extra_footprint footprint footprint_filters_mismatch footprint_symbol_mismatch footprint_type_mismatch hole_clearance hole_near_hole hole_to_hole holes_co_located invalid_outline isolated_copper item_on_disabled_layer items_not_allowed length_out_of_range lib_footprint_issues lib_footprint_mismatch malformed_courtyard microvia_drill_out_of_range mirrored_text_on_front_layer missing_courtyard missing_footprint net_conflict nonmirrored_text_on_back_layer npth_inside_courtyard overlapping_pads padstack pth_inside_courtyard shorting_items silk_edge_clearance silk_over_copper silk_overlap skew_out_of_range solder_mask_bridge starved_thermal text_height text_thickness through_hole_pad_without_hole too_many_vias track_angle track_dangling track_segment_length track_width tracks_crossing unconnected_items unresolved_variable via_dangling zones_intersect track_not_centered_on_via tuning_profile_track_geometries'.split())

class Rejected(Exception):
    pass

@dataclass(frozen=True)
class ExperimentalNativeToolchain:
    """Explicit 10.0.7 diagnostic tools; not production admission or signing proof."""
    cli: Path
    python: Path
    pcbnew: Path
    expected_version: str
    cli_sha256: str
    python_sha256: str
    pcbnew_sha256: str

    def __post_init__(self):
        if self.expected_version!='10.0.7':raise Rejected('unsupported experimental native version')
        self.check()

    def check(self):
        from .placement_clearance import read_bytes
        for name in ('cli','python','pcbnew'):
            path=getattr(self,name);pin=getattr(self,name+'_sha256')
            if (not isinstance(path,Path) or not path.is_absolute() or '..' in path.parts
                    or not isinstance(pin,str) or not re.fullmatch(r'[0-9a-f]{64}',pin)):
                raise Rejected('canonical explicitly pinned experimental tool required')
            raw=read_bytes(path,128*1024*1024)
            if hashlib.sha256(raw).hexdigest()!=pin:raise Rejected('experimental native tool changed: '+name)

    def record(self):
        return {'schema':1,'mode':'experimental-native-qualification','expected_version':self.expected_version,
                'tools':{name:{'path':str(getattr(self,name)),'sha256':getattr(self,name+'_sha256')}
                         for name in ('cli','python','pcbnew')}}

    @classmethod
    def from_record(cls,record):
        if (type(record)is not dict or set(record)!={'schema','mode','expected_version','tools'}
                or type(record['schema'])is not int or record['schema']!=1
                or record['mode']!='experimental-native-qualification'
                or type(record['tools'])is not dict or set(record['tools'])!={'cli','python','pcbnew'}):
            raise Rejected('invalid experimental native tool record')
        args={'expected_version':record['expected_version']}
        for name,row in record['tools'].items():
            if type(row)is not dict or set(row)!={'path','sha256'} or type(row['path'])is not str:
                raise Rejected('invalid experimental tool path/pin record')
            args[name]=Path(row['path']);args[name+'_sha256']=row['sha256']
        return cls(**args)


def experimental_native_version(toolchain):
    if toolchain is None:return '10.0.0'
    if type(toolchain)is not ExperimentalNativeToolchain:raise Rejected('explicit experimental native toolchain required')
    toolchain.check();return toolchain.expected_version


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
    # Fresh full accepted-state scan: no cache or omitted retained evidence.
    # Retained native evidence plus the separately signed official KiCad copy
    # exceeded the initial 10 GiB operational default. Keep all three scopes
    # under a finite 16 GiB aggregate; routing and per-worker limits are unchanged.
    limit=16*1024**3; total=0; deadline=time.monotonic()+15.0
    for directory in ['.data','.tools','.runs']:
        remaining=deadline-time.monotonic()
        if remaining<=0:raise Rejected('project cache/data size scan exceeded time bound')
        root=c.ROOT/directory
        try:
            try:os.lstat(root)
            except FileNotFoundError:continue  # Only an initially absent top-level scope.
            total+=_workdir_bytes(root,limit-total,max_entries=500_000,
                                 max_seconds=remaining,count_file_symlinks=True)
        except (OSError,RuntimeError) as exc:
            raise Rejected('project cache/data size scan failed: '+str(exc)) from exc
        if total>limit:raise Rejected('16 GiB project cache/data ceiling exceeded')
    if time.monotonic()>deadline:raise Rejected('project cache/data size scan exceeded time bound')
    if shutil.disk_usage(c.ROOT).free<2*1024**3:raise Rejected('less than 2 GiB disk headroom')
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
    from .netclass import qualify_project, qualify_parent_project, PARENT_POLICY
    try:
        try:policy=qualify_project(project)
        except ValueError as literal_error:
            try:policy=qualify_parent_project(project)
            except ValueError as parent_error:
                raise ValueError(str(literal_error)+'; '+str(parent_error)) from parent_error
        layers=sx.one(sx.read(board),'layers',[])
        if sum(isinstance(x,list) and len(x)>2 and re.fullmatch(r'(?:F|B|In[0-9]+)\.Cu',sx.unquote(x[1])) is not None for x in layers)!=2:
            raise ValueError('native netclasses currently require two copper layers')
        if policy['mode'] not in {'literal_two_class',PARENT_POLICY}: raise ValueError('unqualified netclass binding mode')
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
    root_texts={id(node) for node in sx.children(tree,'gr_text')}
    def visit(node):
        if not isinstance(node,list) or not node:return
        key=node[0]
        if not isinstance(key,str):raise Rejected('malformed board item in text-layer check')
        surface_field=key=='property' and any(sx.children(node,k) for k in ('at','effects','layer'))
        if key in text_items or surface_field:
            layers=sx.children(node,'layer')
            silk_knockout=(len(layers)==1 and len(layers[0])==3
                and id(node) in root_texts and key=='gr_text'
                and isinstance(layers[0][1],str)
                and sx.unquote(layers[0][1]) in {'F.SilkS','B.SilkS'}
                and layers[0][2]=='knockout')
            if len(layers)!=1 or (len(layers[0])!=2 and not silk_knockout) or not isinstance(layers[0][1],str):
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
    validation. Explicitly unrestricted areas retain their previous scope;
    narrow root pour-only areas require an independent saved-fill audit.
    """
    if sx.children(tree,'module'):
        raise Rejected('legacy module footprints not qualified')
    from .pour_rule_area import qualify
    try:qualified={row['uuid'] for row in qualify(tree)}
    except ValueError as exc:raise Rejected('rule-area restrictions not qualified: '+str(exc)) from exc
    flags={'tracks','vias','pads','copperpour','footprints'}
    zones=list(sx.children(tree,'zone'))
    for footprint in sx.children(tree,'footprint'):
        zones.extend(sx.children(footprint,'zone'))
    for zone in zones:
        keepout=sx.one(zone,'keepout')
        placement=sx.one(zone,'placement')
        if keepout is None and placement is None:
            continue
        uid=sx.one(zone,'uuid')
        if uid is not None and len(uid)==2 and isinstance(uid[1],str) and sx.unquote(uid[1]) in qualified:continue
        if (keepout is None or len(keepout)!=6
                or any(not isinstance(n,list) or len(n)!=2
                       or n[0] not in flags or n[1]!='allowed' for n in keepout[1:])
                or {n[0] for n in keepout[1:]}!=flags):
            raise Rejected('rule-area restrictions not qualified by pinned native validator')


# Registered KiCad10 metadata; global outline-text refusal remains mandatory.
KNOWN_CHECKS |= {'text_on_edge_cuts'}
KNOWN_CHECKS |= {'footprint_symbol_field_mismatch'}
KNOWN_CHECKS |= {'missing_tuning_profile'}

def check_hole_machining_support(tree):
    """Recognizing KiCad10 severity names does not admit removed copper.

    The pinned pad/via parser supports these four fields. Their geometry has
    not been qualified through DSN/SES, so refuse even inactive/malformed
    declarations rather than relying on an editable DRC severity.
    """
    fields={'backdrill','tertiary_drill','front_post_machining','back_post_machining'}
    def visit(node):
        if not isinstance(node,list) or not node:return
        if node[0] in fields:raise Rejected('backdrilled/post-machined pads or vias not qualified')
        for child in node[1:]:visit(child)
    for fp in sx.children(tree,'footprint'):
        for pad in sx.children(fp,'pad'):visit(pad)
    for via in sx.children(tree,'via'):visit(via)

def task_scope_for_record(data,directory,*,input_policy=None):
    """Derive task choices for narrow legacy syntax; never an acceptance flag.

    Existing captured-choice/process readers still verify their full proofs.
    Missing/mixed choices return no admission context. Modern preflight ignores
    this context; 20240108 requires the exact whole/native/source_all tuple.
    """
    from . import preferences as pref
    if type(data) is not dict:return None
    scope=data.get('scope');policy=data.get('input_policy','native') if input_policy is None else input_policy
    layers='source_all'
    if data.get('guidance_policy',policy)!=policy:return None
    for key in ('routing_preferences','pruning_preferences'):
        if key not in data:continue
        try:effective=pref.validate(data[key]['effective'])
        except (ValueError,TypeError,KeyError):return None
        if effective['scope']!=scope or effective['guidance']!=policy:return None
        if layers!='source_all' and effective['layers']!=layers:return None
        layers=effective['layers']
    if (selected_scope_markers(directory,data) or layer_markers(directory,data)
            or 'protected_route_import' in data or data.get('protected_routes',0)!=0):return None
    return (scope,policy,layers)


def preflight(board,*,task_scope=None):
    t=sx.read(board)
    reasons=[]
    if t[0]!='kicad_pcb': reasons.append('not a KiCad board')
    version=sx.one(t,'version')[1]
    legacy=(version=='20240108' and type(task_scope) is tuple
        and len(task_scope)==3 and all(type(v) is str for v in task_scope)
        and task_scope==('whole_board_unlocked_routing','native','source_all'))
    if version not in {'20241229','20260206'} and not legacy: reasons.append('unqualified board format version')
    layers=sx.one(t,'layers',[])
    if sum(isinstance(x,list) and len(x)>2 and re.fullmatch(r'(?:F|B|In[0-9]+)\.Cu',sx.unquote(x[1])) is not None for x in layers) not in (2,4): reasons.append('requires 2 or 4 copper layers')
    project=board.with_suffix('.kicad_pro')
    if not project.is_file(): reasons.append('complete .kicad_pro required')
    else:
        p=json.loads(project.read_text()); settings=p.get('board',{}).get('design_settings',{})
        if legacy:
            from . import board_floor as g
            try:g.qualify_scope(p,g.task_from_source(t))
            except (ValueError,TypeError,KeyError) as exc:reasons.append('legacy 20240108 task scope: '+str(exc))
        try: netclass_policy(board)
        except Rejected as exc: reasons.append(str(exc).removeprefix('unsupported: '))
        if settings.get('drc_exclusions'): reasons.append('DRC exclusions not qualified')
        for key,val in settings.get('rule_severities',{}).items():
            if key=='zone_has_empty_net' and val=='error':
                from .legacy_zone import qualify
                try: qualify(t,p)
                except ValueError as exc: reasons.append(str(exc))
                continue
            if key not in KNOWN_CHECKS or val not in {'error','warning','ignore'}: reasons.append('unknown rule severity semantics: '+key)
            if key in CRITICAL_CHECKS and val!='error' and (key,val) not in {('padstack','warning'),('hole_to_hole','warning')}: reasons.append('core native check not blocking: '+key)
    rules=board.with_suffix('.kicad_dru')
    if rules.exists() and rules.read_text().strip(): reasons.append('custom rules not qualified')
    try: check_hole_machining_support(t)
    except Rejected as exc: reasons.append(str(exc))
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

def parse_report(path, board_name, *, native_toolchain=None):
    expected_version=experimental_native_version(native_toolchain)
    data=json.loads(Path(path).read_text())
    if data.get('$schema')!='https://schemas.kicad.org/drc.v1.json' or data.get('kicad_version')!=expected_version or data.get('source')!=board_name:
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
    result={'opens':len(data['unconnected_items']), 'blocking':sum(v['severity']=='error' for v in data['violations']+data['schematic_parity']),
            'warnings':sum(v['severity']=='warning' for v in findings), 'exclusions':sum(v['severity']=='exclusion' or v.get('excluded',False) for v in findings),
            'ignored_checks':data['ignored_checks'],'findings':findings}
    from . import schematic_field_evidence as fields
    if fields.has_fields(findings):
        proof=fields.readback(path,data)
        if proof is not None:result['field_parity']=proof
    return result


# Finding types are not project-setting keys: KiCad's padstack_invalid has no
# editable severity. Keep parse_report's native summary schema unchanged so old
# evidence can be rechecked under this stricter application acceptance policy.
CRITICAL_FINDINGS = CRITICAL_CHECKS | {'padstack_invalid','text_on_edge_cuts','net_conflict','footprint_symbol_field_mismatch','missing_tuning_profile'}


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
        from . import schematic_field_evidence as fields
        if finding['type'] in CRITICAL_FINDINGS and not (finding['type']==fields.TYPE and fields.qualified(native)):
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
    def __init__(self, out, seconds, *, native_toolchain=None, protect_local_settings=False):
        experimental_native_version(native_toolchain)
        self.native_toolchain=native_toolchain
        self.native_cli=c.CLI if native_toolchain is None else native_toolchain.cli
        self.native_python=c.PYTHON if native_toolchain is None else native_toolchain.python
        if type(protect_local_settings) is not bool:raise Rejected('explicit local-settings guard option required')
        self.protect_local_settings=protect_local_settings;self._local_settings_owner=None
        if protect_local_settings:
            from .local_settings import canonical
            canonical(Path(out).absolute())
        self.out=Path(out).absolute() if protect_local_settings else Path(out).resolve(); self.out.mkdir(parents=True,exist_ok=False)
        if protect_local_settings:
            canonical(self.out)
            from . import handoff as h
            self._local_settings_owner={};h.capture_destination(self._local_settings_owner,self.out)
        self.started=time.monotonic(); self.cpu_started=time.process_time()
        self.deadline=self.started+seconds; self.steps=[]; self.seconds=seconds
        self.env=os.environ.copy()
        self.env.update(LANG='C',LC_ALL='C')  # Stable pinned native diagnostics.
        if native_toolchain is not None:
            for key in ('PYTHONPATH','PYTHONHOME'):self.env.pop(key,None)
            self.env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
        # Avoid writing personal KiCad settings. No model/API/network used in route time.
        for key, relative in [('KICAD_CONFIG_HOME','kicad-config'),('KICAD_CACHE_HOME','kicad-cache'),('KICAD_DOCUMENTS_HOME','kicad-documents')]:
            base=self.out/relative
            (base/('10.0' if key=='KICAD_CONFIG_HOME' else 'kicad/10.0')).mkdir(parents=True)
            self.env[key]=str(base)
    def step(self, name, argv, allowed=(0,)):
        experimental_native_version(self.native_toolchain)
        remaining=self.deadline-time.monotonic()
        if remaining<=0: raise Rejected('timeout: whole task budget exhausted')
        result=run([str(a) for a in argv],cwd=self.out,log=self.out/(name+'.log'),timeout=remaining,env=self.env)
        result['name']=name; self.steps.append(result)
        save_json(self.out/(name+'-process.json'),result)
        if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed:
            raise Rejected(name+': '+result['status']+' exit='+str(result['exit_code']))
        experimental_native_version(self.native_toolchain)
        return result
    def native(self,name,action,board,output,*args):
        prefix=[] if self.native_toolchain is None else ['--experimental-native',json.dumps(self.native_toolchain.record(),sort_keys=True)]
        return self.step(name,[self.native_python,c.ROOT/'autorouter/native.py',*prefix,action,board,output,*args])
    def drc(self,name,board,save=False,*,schematic_parity=False):
        if self.native_toolchain is not None and schematic_parity:
            raise Rejected('experimental area qualification does not admit schematic parity yet')
        if self.protect_local_settings:
            from .local_settings import canonical
            from . import handoff as h
            if type(name) is not str or name in ('','.','..') or '/' in name or chr(92) in name or any(ord(x)<32 for x in name):raise Rejected('canonical PRL DRC stage name required')
            board=canonical(Path(board))
            if h.owned_destination(self._local_settings_owner)!=self.out:raise Rejected('PRL Job root changed')
            if save and self.out not in board.parents:raise Rejected('saved PRL Native input must belong to Job root')
        original_input=board
        before=tree_hash(board.parent)
        local_settings_binding={'local_settings_policy':'job-owned-prl-immutable-v1'} if self.protect_local_settings else {}
        validation_before=None; phase='copy'
        try:
            if not save:
                work=self.out/(name+'-input')
                if self.protect_local_settings:
                    canonical(work)
                    if self.out not in work.parents:raise Rejected('PRL validation copy outside Job root')
                board=work/board.name
                shutil.copytree(original_input.parent,work)
            phase='input_snapshot'; validation_before=tree_hash(board.parent)
            if validation_before!=before: raise Rejected('native DRC validation copy differs before native')
            report=self.out/(name+'.json')
            argv=[self.native_cli,'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',report]
            if schematic_parity:argv.insert(8,'--schematic-parity')
            if save: argv+=['--save-board']
            phase='native'
            if self.protect_local_settings:
                from .local_settings import drc_step
                result=drc_step(self,name,argv+[board])
            else:result=self.step(name,argv+[board],allowed=(0,5))
            phase='output_snapshot'; after=tree_hash(board.parent)
            phase='project_preservation'; check_drc_project(before,after,board.name,saved=save)
            result['validated_input_sha256']=before[board.name]
            result['emitted_candidate']=str(original_input)
            phase='binding_publication'
            save_json(self.out/(name+'-binding.json'),{'source':str(original_input),'input':str(board),'before':before,'after':after,'saved':save,**local_settings_binding,
                **({'experimental_native_toolchain':self.native_toolchain.record()} if self.native_toolchain is not None else {})})
            phase='report_parse'; parsed=parse_report(report,board.name,native_toolchain=self.native_toolchain)
            any_findings=bool(parsed['findings'])
            phase='exit_report'
            if (result['exit_code']==0)==any_findings: raise Rejected('DRC exit/report mismatch')
            from . import schematic_field_evidence as fields
            if schematic_parity:
                phase='schematic_parity_availability'
                fields.check_availability(self.out,name,result,json.loads(report.read_text()),required=True)
            if fields.has_fields(parsed['findings']) and schematic_parity:
                phase='complete_field_observation'
                fields.collect(self,name,board,json.loads(report.read_text()))
                parsed=parse_report(report,board.name,native_toolchain=self.native_toolchain)
            return parsed
        except (Exception,KeyboardInterrupt) as exc:
            if self.protect_local_settings:
                try:h.owned_destination(self._local_settings_owner)
                except (Exception,KeyboardInterrupt) as ownership:
                    exc.add_note('PRL owned root unavailable; no failure journal written: '+str(ownership));raise exc
            # Evidence only: retain the first failure and never normalize a
            # modified project or turn an unavailable report into a pass.
            errors=[]; after=None
            try: after=tree_hash(board.parent)
            except (Exception,KeyboardInterrupt) as capture:
                errors.append('after snapshot: '+type(capture).__name__+': '+str(capture))
            binding={'source':str(original_input),'input':str(board),'before':before,'after':after,'saved':save,**local_settings_binding,
                **({'experimental_native_toolchain':self.native_toolchain.record()} if self.native_toolchain is not None else {})}
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
    check_hole_machining_support(tree)
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
    from .netclass import PARENT_POLICY
    policy=netclass_policy(candidate)
    mapping=audit_native(native,json.loads(project.read_text()),parent_policy=policy is not None and policy['mode']==PARENT_POLICY)
    dimensions=audit_route_dimensions(sx.read(candidate),protected,native)
    return {'native':mapping,'route_dimensions':dimensions,'candidate_sha256':sha(candidate),
            'project_sha256':sha(project)}

def parent_dsn_basis(directory):
    """Bind a pruning run to its own retained, independently checked engine input."""
    directory=Path(directory);base=directory/'incumbent'
    return {'policy':'native-parent-dsn-basis-v1','receipt':'incumbent/result.json',
            'files_sha256':{name:sha(base/name) for name in
                ('result.json','native.dsn','task.dsn','export-netclasses.json')}}

def check_parent_dsn_basis(directory,data):
    """A C label never removes the native/DSN contract in the new class scope."""
    from .floor_route import read_json
    from .netclass import PARENT_POLICY
    directory=Path(directory);base=directory/'incumbent/result.json'
    if (data.get('strategy')!='native_validated_zone_net_pruning'
            or data.get('netclass_parent_dsn_basis')!=parent_dsn_basis(directory)):
        raise Rejected('parent-class strategy requires its exact native/DSN incumbent basis')
    incumbent=read_json(base)
    if (incumbent.get('baseline')!='B2_tuned' or incumbent.get('engine_profile')!='tuned'
            or incumbent.get('netclass_policy',{}).get('mode')!=PARENT_POLICY
            or any(incumbent.get(key)!=data.get(key) for key in ('source','source_hashes','task_sha256','scope'))
            or data.get('incumbent',{}).get('receipt')!=str(base)):
        raise Rejected('parent-class incumbent task/source lineage differs')
    inherited=[{key:value for key,value in step.items() if key!='phase'} for step in data['steps'] if step.get('phase')=='incumbent']
    if inherited!=incumbent.get('steps'):raise Rejected('parent-class incumbent process/cost lineage differs')
    check_result(base)
    if data['netclass_parent_dsn_basis']!=parent_dsn_basis(directory):raise Rejected('parent-class incumbent basis changed during readback')

def check_pour_evidence(directory,data,original,candidate,*,source_hashes=None,correction=True,sandboxed=None):
    """Require saved-refill/native-fill proof from source intent, never a flag."""
    from . import pour_rule_area as pour, floor_route as f
    from .placement_clearance import read_bytes
    directory=Path(directory);candidate=Path(candidate);areas=pour.qualify(original)
    names=('pour-before-refill.kicad_pcb','pour-keepout-audit.json','pour-dsn-correction.json','pour-corrected.dsn')
    if not areas:
        if any((directory/n).exists() or (directory/n).is_symlink() for n in names):raise Rejected('pour evidence without qualified source intent')
        return
    if sandboxed is None:sandboxed=data.get('input_policy') in {'board-floors-v1','placement-clearance-v1','placement-search-v1','placement-pruning-v1'}
    prefix=f.SANDBOX if sandboxed else []
    audit=f.read_json(directory/'pour-keepout-audit.json')
    try:pour.verify_native_record(audit,candidate)
    except ValueError as exc:raise Rejected(str(exc)) from exc
    f.process_check(directory,data,'pour-keepout-audit',[*prefix,str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'pour-audit',str(candidate),str(directory/'pour-keepout-audit.json')])
    before_path=directory/'pour-before-refill.kicad_pcb';before=sx.parse(read_bytes(before_path).decode())
    if immutable(before)!=immutable(original) or routes(before)!=routes(sx.read(candidate)):raise Rejected('pour refill changed original geometry/routing')
    hashes=dict(source_hashes if source_hashes is not None else data['source_hashes']);hashes[candidate.name]=sha(before_path)
    refill=directory/'refill'/candidate.name
    f.check_drc_stage(directory,data,'refill-drc',refill,refill,True,hashes,sandboxed=sandboxed)
    if (sx.dump(transplant_fill(before,sx.read(refill)))+'\n').encode()!=read_bytes(candidate):raise Rejected('pour saved-refill reconstruction differs')
    if not correction:return
    engine=[s for s in data.get('steps',[]) if s.get('name')=='engine' and s.get('cwd')==str(directory)]
    if not engine:
        if data.get('baseline')!='C-prototype':raise Rejected('pour correction requires original native engine lineage')
        check_result(directory/'incumbent/result.json')
        return
    if len(engine)!=1:raise Rejected('ambiguous pour correction engine lineage')
    if data.get('adapter')=='none':
        if ('pour_dsn_correction' in data or 'adapter_transformations' in data
                or any((directory/n).exists() or (directory/n).is_symlink() for n in names[2:])):
            raise Rejected('stock workflow cannot claim pour adapter correction')
        input_path=directory/('routing-scope-input.dsn' if data.get('scope')=='selected_nets' else 'task.dsn')
        if read_bytes(input_path)!=read_bytes(directory/'native.dsn'):raise Rejected('stock pour workflow raw engine input differs')
        return
    source_bytes=read_bytes(directory/'snapshot'/candidate.name)
    corrected,record=pour.correct(source_bytes,read_bytes(directory/'native.dsn'))
    if (f.canonical(data.get('pour_dsn_correction'))!=f.canonical(record)
            or f.canonical(f.read_json(directory/'pour-dsn-correction.json'))!=f.canonical(record)
            or read_bytes(directory/'pour-corrected.dsn')!=corrected
            or data.get('adapter_transformations',{}).get('input_sha256')!=pour.sha(corrected)):
        raise Rejected('missing/downgraded pour DSN correction lineage')
    from .adapter import adapt_bytes
    adapted,adapter_record=adapt_bytes(corrected,data['adapter'],f.read_json(directory/'obstacles.json'))
    if 'native_edge_correction' in data:
        from . import native_edge
        adapted,_=native_edge.correct(adapted,native_edge_context(directory/'snapshot'/candidate.name))
    engine_input=directory/('routing-scope-input.dsn' if data.get('scope')=='selected_nets' else 'task.dsn')
    if read_bytes(engine_input)!=adapted or f.canonical(data.get('adapter_transformations'))!=f.canonical(adapter_record):
        raise Rejected('pour corrected-to-adapter engine input differs')

def legacy_zone_evidence(original,candidate):
    """Independent legacy-rule witness, never a native severity alias.

    Exact net/pad/zone intent is already an immutable candidate requirement.
    Requiring the same sufficient copper-pad witness closes the old native
    validator gap without claiming complete native pad-count equivalence.
    """
    from . import legacy_zone as legacy
    from .floor_route import canonical
    project_path=Path(candidate).with_suffix('.kicad_pro')
    project=json.loads(project_path.read_text())
    if legacy.KEY not in project.get('board',{}).get('design_settings',{}).get('rule_severities',{}):return None
    try:
        source=legacy.qualify(original,project)
        final=legacy.qualify(sx.read(candidate),project)
    except ValueError as exc:raise Rejected(str(exc)) from exc
    if canonical(source)!=canonical(final):raise Rejected('legacy zone source/candidate witness changed')
    return {'schema':1,'policy':legacy.POLICY,'native_enforcement_claimed':False,
            'project_sha256':sha(project_path),'candidate_sha256':sha(candidate),'witness':final,
            'implementation_sha256':{name:sha(c.ROOT/name) for name in
                ('autorouter/legacy_zone.py','autorouter/board_floor.py','autorouter/floor_route.py',
                 'autorouter/placement_clearance.py','autorouter/sexpr.py','autorouter/pipeline.py')}}


def check_legacy_zone_evidence(directory,original,candidate,*,implementation=None):
    from .floor_route import canonical,read_json
    path=Path(directory)/'legacy-zone-witness.json'
    expected=legacy_zone_evidence(original,candidate)
    if expected is None:
        if path.exists() or path.is_symlink():raise Rejected('unexpected legacy zone witness')
    else:
        try:actual=read_json(path)
        except (OSError,ValueError) as exc:raise Rejected('missing or changed legacy zone witness') from exc
        if implementation is not None:
            current=expected['implementation_sha256']
            recorded=actual.get('implementation_sha256') if type(actual) is dict else None
            if (type(implementation) is not dict or type(recorded) is not dict
                    or set(recorded)!=set(current)
                    or any(type(pin) is not str or not re.fullmatch(r'[0-9a-f]{64}',pin)
                           or implementation.get(name)!=pin for name,pin in recorded.items())):
                raise Rejected('legacy zone compatibility implementation provenance missing or changed')
            if recorded!=current:
                from .placement_clearance import read_bytes
                import stat
                directory=Path(directory);runs=c.ROOT/'.runs'
                try:
                    relative=directory.relative_to(runs)
                    if (not relative.parts or '..' in directory.parts or not directory.is_absolute()
                            or directory.resolve(strict=True)!=directory
                            or any(node.is_symlink() for node in (directory,*directory.parents))):
                        raise Rejected('legacy zone captured producer requires canonical project .runs directory')
                    locations=[directory/'code']
                    if len(relative.parts)>1:locations.append(directory.parent/'code')
                    locations=[node for node in locations if node.exists() or node.is_symlink()]
                    if len(locations)!=1:raise Rejected('legacy zone captured producer code missing or ambiguous')
                    code=locations[0]
                    if not code.is_dir() or code.resolve(strict=True)!=code:
                        raise Rejected('legacy zone captured producer code alias')
                    owner=code.stat()
                    for name,pin in recorded.items():
                        source=code/Path(name).name
                        before=source.lstat();raw=read_bytes(source,1024*1024);after=source.lstat()
                        identity=lambda info:(info.st_dev,info.st_ino,info.st_mode,info.st_nlink,info.st_size,info.st_mtime_ns)
                        if (not stat.S_ISREG(before.st_mode) or before.st_nlink!=1
                                or identity(before)!=identity(after) or hashlib.sha256(raw).hexdigest()!=pin):
                            raise Rejected('legacy zone captured producer file missing, aliased or changed')
                    if (owner.st_dev,owner.st_ino)!=(code.stat().st_dev,code.stat().st_ino):
                        raise Rejected('legacy zone captured producer directory changed')
                except (OSError,ValueError) as exc:
                    raise Rejected('legacy zone captured producer provenance missing or changed') from exc
            # Only producer metadata may differ. All semantics were rederived
            # above by current code; captured source is checked, never executed.
            expected['implementation_sha256']=recorded
        if canonical(actual)!=canonical(expected):raise Rejected('missing or changed legacy zone witness')


def validate_candidate(job, original, candidate, source_hashes, protected, *, guidance_contract=None, guidance_basis=None, layer_contract=None, selected_names=None, schematic_parity=False):
    # A complete captured native schematic must participate in final acceptance
    # for every routing scope, including optimizer trials and fresh exports.
    schematic_parity=schematic_parity or Path(candidate).with_suffix('.kicad_sch').name in source_hashes
    check_rule_area_support(original)
    check_hole_machining_support(original)
    check_hole_machining_support(sx.read(candidate))
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
    legacy_zone_evidence(original,candidate)  # Reject before any native normalization.
    from . import pour_rule_area as pour
    pour_areas=pour.qualify(original)
    if pour_areas:
        before_refill=job.out/'pour-before-refill.kicad_pcb'
        with before_refill.open('xb') as stream:stream.write(candidate.read_bytes())
    shutil.copytree(candidate.parent,job.out/'refill')
    refill=job.out/'refill'/candidate.name
    job.drc('refill-drc',refill,save=True)
    sx.write(candidate,transplant_fill(sx.read(candidate),sx.read(refill)))
    check_hole_machining_support(sx.read(candidate))
    if immutable(sx.read(candidate))!=immutable(original): raise Rejected('immutable geometry changed after refill')
    if layer_contract is not None:layer_contract['audit']=audit_layer_contract(candidate,layer_contract)
    final_hash=sha(candidate)
    if pour_areas:
        job.native('pour-keepout-audit','pour-audit',candidate,job.out/'pour-keepout-audit.json')
        pour.verify_native_record(json.loads((job.out/'pour-keepout-audit.json').read_text()),candidate)
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
    legacy=legacy_zone_evidence(original,candidate)
    if legacy is not None:save_json(job.out/'legacy-zone-witness.json',legacy)
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
    return {'implementation_sha256':implementation,'git_head':git_head,'kicad':'10.0.0','freerouting':'2.5.0','files':files,'network':'engine sandbox-exec deny network*',
            'normal_drc_local_settings_policy':NORMAL_DRC_LOCAL_SETTINGS_POLICY}

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

def check_engine_profile_record(data,directory):
    """Replay declared native settings against the retained actual engine argv."""
    from .floor_route import read_json
    directory=Path(directory)
    captured=directory/'routing-preferences.json'
    if 'routing_preferences' in data or captured.exists() or captured.is_symlink():
        return check_preferences_record(directory,data)
    width=check_minimum_width_record(data,directory)
    engine=data['engine_budget']
    expected=engine_profile_settings(data['engine_profile'],engine['remaining_outer_wall_seconds_at_assignment'],
        strict_class_targets=data.get('netclass_policy') is not None or data.get('scope')=='selected_nets' or width is not None,
        scoring_variant=data.get('scoring_variant'))
    workers=[step for step in data['steps'] if step.get('name')=='engine']
    if (any(engine.get(key)!=value for key,value in expected.items())
            or engine.get('outer_task_wall_budget_seconds')!=data['budget_seconds']
            or engine.get('outer_task_cpu_budget_seconds')!=data['cpu_budget_seconds']
            or len(workers)!=1
            or workers[0].get('argv')!=engine_argv(directory,expected['argv'])
            or workers[0].get('cwd')!=str(directory)
            or workers[0].get('status')!='success' or workers[0].get('exit_code')!=0
            or workers[0].get('cleanup_complete') is not True
            or read_json(Path(directory)/'engine-process.json')!=workers[0]):
        raise Rejected('declared native engine profile differs from its execution journal')


def engine_baseline(profile,adapter):
    if profile=='completion-only': return 'completion_only_probe'
    if profile=='tuned': return 'B2_tuned'
    if profile=='standard': return 'B0' if adapter=='none' else 'B1'
    raise Rejected('unknown engine profile')


def native_edge_context(board):
    """Use exact original files and the existing custom-rule support boundary."""
    from . import native_edge
    from .placement_clearance import read_bytes
    board=Path(board)
    context=native_edge.derive_context(read_bytes(board),read_bytes(board.with_suffix('.kicad_pro')))
    rules=board.with_suffix('.kicad_dru')
    if rules.exists() or rules.is_symlink():
        context.update(applicable=False,reason='edge transport with custom-rule companion is unqualified')
    return context


def native_minimum_markers(directory,data):
    """Recognize partial experimental evidence; never enable a normal receipt."""
    names=('minimum-preferences.dsn','minimum-preferences.json','minimum-export-context.json')
    return (any(key in data for key in ('native_minimum_preferences','native_minimum_export_context_sha256'))
        or any((Path(directory)/name).exists() or (Path(directory)/name).is_symlink() for name in names))


def native_minimum_contract(directory,data):
    """Recompute a diagnostic-only fixed basis, without accepting a candidate.

    The frozen actor must additionally check the retained real export process
    and its prospective prefix pins, and always call check_native_minimum_transport.
    Context/source/process paths are never rewritten to a new producer.
    """
    from . import board_floor as g,adapter,native_edge,floor_route as f,netclass,sexpr,floor_context
    from .placement_clearance import read_bytes
    from .local_settings import canonical as canonical_path
    directory=Path(directory)
    if (data.get('accepted') is not False or data.get('production_support_qualified') is not False
            or data.get('input_policy','native')!='native' or data.get('guidance_policy','native')!='native'
            or data.get('scope')!='whole_board_unlocked_routing' or data.get('adapter') not in ('graphics','both')
            or data.get('protected_routes',0)!=0 or 'protected_route_import' in data
            or selected_scope_markers(directory,data) or layer_markers(directory,data)):
        raise Rejected('minimum experiment requires diagnostic whole native/source-all lineage')
    from . import preferences as pref
    for key in ('routing_preferences','pruning_preferences'):
        if key in data:
            effective=pref.validate(data[key]['effective'])
            if (effective['scope'],effective['guidance'],effective['layers'])!=('whole_board_unlocked_routing','native','source_all'):
                raise Rejected('minimum experiment preference scope differs')
    if ('pour_dsn_correction' in data or 'floor_policy' in data
            or any((directory/name).exists() or (directory/name).is_symlink()
                for name in ('pour-corrected.dsn','pour-dsn-correction.json','floor-guided.dsn','floor-policy.json'))):
        raise Rejected('minimum experiment cannot relabel pour/floor guidance')
    board=directory/'snapshot'/Path(data['source']).name
    if tree_hash(board.parent)!=data['source_hashes'] or board.with_suffix('.kicad_dru').exists() or board.with_suffix('.kicad_dru').is_symlink():
        raise Rejected('minimum experiment original snapshot/rules differ')
    task_bytes=(sx.dump(g.task_from_source(sx.read(board)))+'\n').encode()
    raw=read_bytes(directory/'native.dsn');context_path=directory/'minimum-export-context.json'
    context=f.read_json(context_path)
    if (data.get('native_dsn_sha256')!=g.sha(raw)
            or data.get('native_minimum_export_context_sha256')!=sha(context_path)):
        raise Rejected('minimum experiment retained native export/context pin differs')
    native_input=Path(context['source']);canonical_path(native_input)
    if not native_input.is_relative_to(c.ROOT/'.runs'):
        raise Rejected('minimum experiment native input must be a retained run copy')
    expected=dict(data['source_hashes']);expected[board.name]=g.sha(task_bytes)
    f.context_binding(context,native_input,expected,'export',g.sha(raw))
    if tree_hash(native_input.parent)!=expected or read_bytes(native_input)!=task_bytes:
        raise Rejected('minimum experiment actual export input differs from reconstructed task')
    modules=(g,adapter,native_edge,f,netclass,sexpr,floor_context)
    required={'autorouter/'+Path(module.__file__).name:sha(Path(module.__file__)) for module in modules}
    required['autorouter/pipeline.py']=sha(Path(__file__))
    required['autorouter/native.py']=sha(Path(__file__).with_name('native.py'))
    implementation=data.get('tools',{}).get('implementation_sha256',{})
    if any(implementation.get(name)!=digest or sha(directory/'code'/Path(name).name)!=digest for name,digest in required.items()):
        raise Rejected('minimum experiment captured/live implementation differs')
    derived,transformation=g.transform(raw,context,read_bytes(board.with_suffix('.kicad_pro')),task_bytes,target_policy=g.MINIMUM_POLICY)
    contract={'schema':1,'policy':g.MINIMUM_POLICY,'source_hashes':data['source_hashes'],
        'native_context_sha256':sha(context_path),'implementation_sha256':required,'transformation':transformation}
    return derived,contract


def check_native_minimum_transport(directory,data):
    """Mandatory experimental actor reader: total proof deletion cannot downgrade."""
    if not native_minimum_markers(directory,data):raise Rejected('minimum experiment lost its mandatory transport proof')
    return check_native_edge_transport(directory,data)


def check_native_edge_transport(directory,data):
    """Replay the narrow edge-only correction from unchanged snapshot bytes."""
    from . import native_edge,adapter
    from .placement_clearance import read_bytes
    from .floor_route import read_json,canonical
    directory=Path(directory); marker=directory/'native-edge-correction.json';prior=directory/'edge-adapter-input.dsn'
    minimum=native_minimum_markers(directory,data)
    if ('native_edge_correction' not in data and not marker.exists() and not marker.is_symlink()
            and not prior.exists() and not prior.is_symlink()):
        if minimum:raise Rejected('minimum experiment requires its edge transport chain')
        direct_native=('engine_budget' in data
            or any((directory/name).exists() or (directory/name).is_symlink() for name in ('native.dsn','engine-process.json'))
            or any(step.get('name')=='engine' and step.get('cwd')==str(directory) for step in data.get('steps',[])))
        if (data.get('input_policy','native')=='native' and data.get('adapter')!='none'
                and direct_native
                and 'autorouter/native_edge.py' in data.get('tools',{}).get('implementation_sha256',{})):
            raise Rejected('new native adapter receipt lost its edge transport record')
        return
    if data.get('input_policy','native')!='native' or data.get('adapter')=='none':
        raise Rejected('edge correction requires corrected native adapter lineage')
    board=directory/'snapshot'/Path(data['source']).name
    if tree_hash(board.parent)!=data['source_hashes']:
        raise Rejected('edge correction original snapshot differs')
    context=native_edge_context(board)
    if minimum:
        from . import board_floor as g
        base,contract=native_minimum_contract(directory,data)
        proof=directory/'minimum-preferences.json'
        expected={'file':proof.name,'sha256':sha(proof),'policy':g.MINIMUM_POLICY}
        if (canonical(data.get('native_minimum_preferences'))!=canonical(expected)
                or canonical(read_json(proof))!=canonical(contract)
                or read_bytes(directory/'minimum-preferences.dsn')!=base):
            raise Rejected('minimum experiment proof, targets or native basis differ')
    else:
        base=read_bytes(directory/('pour-corrected.dsn' if 'pour_dsn_correction' in data else 'native.dsn'))
    adapted,adapter_record=adapter.adapt_bytes(base,data['adapter'],read_json(directory/'obstacles.json'))
    corrected,record=native_edge.correct(adapted,context)
    engine_input=directory/('routing-scope-input.dsn' if data.get('scope')=='selected_nets' else 'task.dsn')
    if (read_bytes(prior)!=adapted or read_bytes(engine_input)!=corrected
            or canonical(data.get('native_edge_correction'))!=canonical(record)
            or canonical(read_json(marker))!=canonical(record)
            or canonical(data.get('adapter_transformations'))!=canonical(adapter_record)):
        raise Rejected('native edge correction input, source rule or metadata differs')
    return record


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


def minimum_width_guard(source, adapter):
    """Prevent engine neckdown below a positive original board width minimum.

    Stock B0 keeps its ordinary settings. Corrected workflows retain all class
    targets and disable automatic width reduction; native DRC remains authority.
    """
    if adapter=='none':return None
    project=Path(source).with_suffix('.kicad_pro')
    value=json.loads(project.read_text()).get('board',{}).get('design_settings',{}).get('rules',{}).get('min_track_width',0)
    if type(value) not in (int,float) or not math.isfinite(value) or value<0:raise Rejected('unsupported: malformed original track-width minimum')
    if value==0:return None
    return {'policy':'original-positive-minimum-no-automatic-neckdown-v1',
            'min_track_width_mm':value,'original_project_sha256':sha(project)}


def check_minimum_width_record(data, directory=None):
    if data.get('adapter')=='none' and 'minimum_width_guard' not in data:return None
    guard=minimum_width_guard(data['source'],data['adapter'])
    if 'minimum_width_guard' not in data:
        # Historical native receipts predate this policy. Bind compatibility to
        # their retained implementation, rather than an editable JSON opt-out.
        if guard is not None and directory is not None and data.get('input_policy','native')=='native':
            from .placement_clearance import read_bytes
            if b'\ndef minimum_width_guard(' in read_bytes(Path(directory)/'code/pipeline.py'):
                raise Rejected('current native width policy requires original width guard')
        return None
    from .floor_route import canonical
    if guard is None or canonical(data['minimum_width_guard'])!=canonical(guard) or data.get('engine_budget',{}).get('strict_class_targets') is not True:
        raise Rejected('original width guard or engine reduction policy differs')
    return guard


def selected_parity_required(data,directory=None):
    # Historical whole-board receipts explicitly did not check parity. Keep
    # their evidence readable; new receipts declare the actual complete-input
    # check, and their retained native argv must agree with that declaration.
    if (data.get('scope')!='selected_nets' and data.get('schematic_parity') not in
            {'checked by final native DRC','unavailable: no native schematic in source project'}):
        if (directory is not None and Path(data.get('source','')).with_suffix('.kicad_sch').name
                in data.get('source_hashes',{})):
            from .placement_clearance import read_bytes
            # A new availability-aware worker cannot use an editable declaration
            # to opt out. Old retained code remains an explicitly historical read.
            if b'fields.check_availability(self.out,name,result' in read_bytes(Path(directory)/'code/pipeline.py'):
                raise Rejected('current retained implementation requires schematic parity declaration')
        return False
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
    width_guard=check_minimum_width_record(data,directory)
    settings=engine_profile_settings(effective['profile'],assigned.get('remaining_outer_wall_seconds_at_assignment'),
        strict_class_targets=effective['guidance']!='native' or data.get('netclass_policy') is not None or effective['scope']=='selected_nets' or width_guard is not None,scoring_variant=scoring)
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
        elif (data.get('native_edge_correction') or data.get('adapter_transformations',{})).get('output_sha256')!=dsn_binding['input_sha256']:
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
    from .local_settings import canonical
    canonical(Path(source).absolute());canonical(Path(output).absolute())
    source=Path(source).resolve(strict=True); output=Path(output).resolve()
    if source.parent==output or source.parent in output.parents: raise Rejected('output must be outside source project')
    if not math.isfinite(seconds) or seconds<5 or seconds>900: raise Rejected('budget must be 5–900 seconds')
    if sha(c.JAR)!=c.JAR_SHA256: raise Rejected('engine hash mismatch')
    check_storage()
    job=Job(output,seconds,protect_local_settings=True)
    job.started=operation_started; job.deadline=operation_started+seconds; job.cpu_started=operation_cpu
    code=output/'code'; code.mkdir()
    for path in (c.ROOT/'autorouter').glob('*.py'): shutil.copy2(path,code/path.name)
    report={'schema':1,'status':'validator_error','accepted':False,'physical_electrical_validation':False,'schematic_parity':'not checked','source':str(source),
            'started_utc':operation_started_utc,'budget_seconds':seconds,'cpu_budget_seconds':seconds,'cpu_budget_enforcement':'postcompletion acceptance cap; no total-CPU preemption','baseline':engine_baseline(engine_profile,adapter),'adapter':adapter,'engine_profile':engine_profile,'scoring_variant':scoring_variant,'scope':'partial_completion' if keep_existing else 'whole_board_unlocked_routing',
            'tools':tool_manifest()}
    try:
        capture_preferences(report,output,_preferences)
        before=tree_hash(source.parent); report['source_hashes']=before
        selected=_preferences['effective'].get('nets') if _preferences and _preferences['effective']['scope']=='selected_nets' else None
        scope=_preferences['effective']['scope'] if _preferences else report['scope']
        layers=_preferences['effective']['layers'] if _preferences else 'source_all'
        original=preflight(source,task_scope=(scope,guidance_policy,layers))
        from .netclass import PARENT_POLICY
        source_policy=netclass_policy(source)
        if selected is not None and source_policy is not None and source_policy['mode']==PARENT_POLICY:
            raise Rejected('unsupported: selected-net composite class transport not qualified')
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
        from .netclass import PARENT_POLICY
        parent_classes=policy is not None and policy['mode']==PARENT_POLICY
        if selected is not None and parent_classes:
            raise Rejected('unsupported: selected-net composite class transport not qualified')
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
            report['netclass_export_audit']=audit_dsn(output/'native.dsn',native_classes,json.loads(candidate.with_suffix('.kicad_pro').read_text()),parent_policy=parent_classes)
        report['native_dsn_sha256']=sha(output/'native.dsn')
        if adapter!='none':
            from . import pour_rule_area as pour
            if pour.qualify(original):
                corrected,correction=pour.correct(snapshot.read_bytes(),(output/'native.dsn').read_bytes())
                (output/'pour-corrected.dsn').write_bytes(corrected)
                (output/'task.dsn').write_bytes(corrected)
                save_json(output/'pour-dsn-correction.json',correction)
                report['pour_dsn_correction']=correction
        if adapter!='none':
            from .adapter import adapt_dsn
            job.native('obstacles','obstacles',candidate,output/'obstacles.json')
            report['adapter_transformations']=adapt_dsn(output/'task.dsn',adapter,json.loads((output/'obstacles.json').read_text()))
            from . import native_edge
            shutil.copy2(output/'task.dsn',output/'edge-adapter-input.dsn')
            corrected,edge_record=native_edge.correct((output/'task.dsn').read_bytes(),native_edge_context(snapshot))
            (output/'task.dsn').write_bytes(corrected)
            save_json(output/'native-edge-correction.json',edge_record)
            report['native_edge_correction']=edge_record
        if policy is not None:
            report['netclass_task_audit']=audit_dsn(output/'task.dsn',native_classes,json.loads(candidate.with_suffix('.kicad_pro').read_text()),parent_policy=parent_classes)
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
        width_guard=minimum_width_guard(source,adapter)
        if width_guard is not None:report['minimum_width_guard']=width_guard
        report['engine_budget']=engine_profile_settings(engine_profile,job.deadline-time.monotonic(),strict_class_targets=policy is not None or selected is not None or width_guard is not None,scoring_variant=scoring_variant)
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
    report['resource_limitations']='One sequential worker; Java 2GiB heap; group RSS4GiB and workdir512MiB polling guards may overshoot;16GiB total cache checked before task. Peak direct-child RSS and polled group RSS are different metrics. CPU descendants only if accounted for by child wait; monitoring CPU included.'
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
    from . import (adapter,board_floor,floor_context,floor_route,layer_policy,legacy_zone,local_settings,
                   netclass,placement_clearance,placement_strategy,
                   placement_transform,pour_rule_area,preferences,runner,strategy,
                   schematic_fields,schematic_field_evidence)
    import sys
    modules=(sys.modules[__name__],c,sx,adapter,board_floor,floor_context,
             floor_route,layer_policy,legacy_zone,local_settings,netclass,placement_clearance,
             placement_strategy,placement_transform,pour_rule_area,preferences,runner,strategy,
             schematic_fields,schematic_field_evidence)
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
    runtime=(hashlib.sha256(pc.read_bytes(c.ROOT/'toolchain.lock.json')).hexdigest(),
             tool_manifest(),str(c.ROOT),str(c.CLI),str(c.PYTHON),str(c.PCBNEW),str(c.JAVA),str(c.JAR))
    live=_readback_live_identity(state['modules'])
    # File flags/link counts affect the PRL contract but are outside byte hashes.
    import stat
    local_metadata=[]
    for name in evidence[0]:
        if Path(name).suffix=='.kicad_prl':
            info=(path.parent/name).lstat()
            local_metadata.append((name,getattr(info,'st_flags',0),info.st_nlink,stat.S_IFMT(info.st_mode)))
    return (evidence,original,tuple(sorted(local_metadata)),runtime,live)


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
    if native_minimum_markers(path.parent,data):
        raise Rejected('experimental native-minimum transport is not a normal routing receipt')
    scoring_marker=path.parent/'pruning-scoring.json'
    pruning_marker=path.parent/'pruning-preferences.json'
    if (data.get('strategy')=='native_validated_zone_net_pruning' or scoring_marker.exists()
            or scoring_marker.is_symlink() or 'incumbent_scoring_contract' in data
            or 'pruning_preferences' in data or 'pruning_preferences_policy' in data
            or pruning_marker.exists() or pruning_marker.is_symlink()):
        from .strategy import check_incumbent_scoring
        check_incumbent_scoring(path.parent,data)
    elif 'incumbent_scoring_variant' in data or 'incumbent_receipt_sha256' in data:
        # Placement-backed pruning has its separate explicit incumbent contract.
        if data.get('input_policy')!='placement-pruning-v1':
            raise Rejected('pruning scoring marker on another routing policy')
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
        or (path.parent/'routing-preferences.json').is_symlink() or layer_markers(path.parent,data)
        or 'pruning_preferences' in data or 'pruning_preferences_policy' in data
        or pruning_marker.exists() or pruning_marker.is_symlink())
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
    original=preflight(source,task_scope=task_scope_for_record(data,path.parent,input_policy=input_policy))
    current=sx.read(candidate)
    check_hole_machining_support(current)
    if immutable(current)!=immutable(original): raise Rejected('immutable geometry changed')
    check_legacy_zone_evidence(path.parent,original,candidate,
        implementation=data.get('tools',{}).get('implementation_sha256',{}))
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
        from .netclass import audit_dsn, audit_native, PARENT_POLICY
        parent_classes=netclass_policy(candidate)['mode']==PARENT_POLICY
        if data['scope']=='selected_nets' and parent_classes:
            raise Rejected('selected-net composite class transport not qualified')
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
        if data.get('baseline')=='C-prototype' and parent_classes:
            check_parent_dsn_basis(path.parent,data)
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
            audit_native(exported,project,parent_policy=parent_classes)
            if (data.get('netclass_policy')!=netclass_policy(candidate)
                    or data.get('netclass_export_audit')!=audit_dsn(path.parent/'native.dsn',exported,project,parent_policy=parent_classes)
                    or data.get('netclass_task_audit')!=audit_dsn(path.parent/('routing-scope-input.dsn' if data['scope']=='selected_nets' else 'task.dsn'),exported,project,parent_policy=parent_classes)):
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
    if ((any(step.get('phase')=='incumbent' and step.get('name')=='engine' for step in data.get('steps',[]))
            or (path.parent/'incumbent/result.json').exists())
            and data.get('strategy') not in {'native_validated_zone_net_pruning','native_validated_thermal_bridge','placement-native-pruning-v1'}):
        raise Rejected('incumbent workers require their recognized strategy')
    if data.get('native')!=native or data.get('invariants_unchanged') is not True: raise Rejected('receipt native summary differs from raw evidence')
    if data.get('whole_project_drc_clean') is not (native['warnings']==0): raise Rejected('receipt cleanliness claim differs from native evidence')
    metrics=evidence('metrics.json')
    if data.get('metrics')!=metrics or metrics.get('version')!='10.0.0': raise Rejected('receipt metrics differ from retained native metrics')

    process=evidence('final-drc-process.json')
    expected_argv=[str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(path.parent/'final-drc.json'),str(native_input)]
    if selected_parity_required(data,path.parent):expected_argv.insert(8,'--schematic-parity')
    if input_policy in {'board-floors-v1','placement-clearance-v1','placement-search-v1',ps.POLICY}:
        from .floor_route import SANDBOX
        expected_argv=SANDBOX+expected_argv
    findings=bool(native['findings'])
    if process.get('argv')!=expected_argv or process.get('cwd')!=str(path.parent) or process.get('name')!='final-drc' or process.get('exit_code')!=(5 if findings else 0) or process.get('status')!=('nonzero_exit' if findings else 'success') or process.get('cleanup_complete') is not True:
        raise Rejected('native process provenance is inconsistent')
    steps=data.get('steps')
    if not isinstance(steps,list) or not steps or any(not isinstance(step,dict) for step in steps): raise Rejected('missing process history')
    from .local_settings import check_event
    check_event(path.parent,binding,process)
    matching=[step for step in steps if step.get('name')=='final-drc' and step.get('cwd')==str(path.parent)]
    if len(matching)!=1 or any(matching[0].get(key)!=value for key,value in process.items()) or matching[0].get('validated_input_sha256')!=data['candidate_sha256'] or matching[0].get('emitted_candidate')!=str(candidate):
        raise Rejected('final native step differs from process or input binding')
    from . import schematic_field_evidence as fields
    fields.check_processes(path.parent,data,'final-drc',native_input,
        sandboxed=input_policy in {'board-floors-v1','placement-clearance-v1','placement-search-v1',ps.POLICY})
    if any(step.get('status')=='cancelled' or step.get('cleanup_complete') is not True for step in steps): raise Rejected('cancelled or incomplete process cleanup in receipt')
    check_pour_evidence(path.parent,data,original,candidate)
    check_native_edge_transport(path.parent,data)
    check_preferences_record(path.parent,data)

    if 'engine_budget' in data:
        check_minimum_width_record(data,path.parent)
        if input_policy=='native':check_engine_profile_record(data,path.parent)

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
    if preferences_guarded:
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
    from .local_settings import check_normal_policy
    check_normal_policy(path.parent,data)
    check_event(path.parent,binding,process)  # Flags/link counts are outside byte witnesses.
    return result
