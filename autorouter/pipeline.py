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
SELECTED_PROPOSAL_IMPORT_POLICY='selected-proposals-exact-source-v1'
NORMAL_SELECTED_PROPOSAL_IMPORT_POLICY='selected-proposals-exact-source-v1'
PROTECTED_VIA_IMPORT_POLICY='legacy-via-off-source-v3'
NORMAL_PROTECTED_VIA_IMPORT_POLICY='legacy-via-off-source-v3'
NORMAL_TASK_COPPER_FIXED_POLICY='native-task-copper-fixed-v1'
NORMAL_NATIVE_EXPORT_ALIAS_POLICY='source-bound-padless-export-v1'
NORMAL_ENGINE_PROVENANCE_POLICY='mandatory-normal-engine-journal-v1'
NAMED_EDGE_ADMISSION_POLICY='known-named-whole-native-edge-v1'
ENGINE_GLOBAL_WIDTH_POLICY='original-global-minimum-width-v1'
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
    if toolchain is None:return c.NATIVE_VERSION
    if type(toolchain)is not ExperimentalNativeToolchain:raise Rejected('explicit experimental native toolchain required')
    toolchain.check();return toolchain.expected_version


def require_native_scope(*, purpose='route', scope='whole_board_unlocked_routing',
                         guidance='native', layers='source_all', profile='standard',
                         adapter='both', scoring=None):
    """Keep a selected tool version from silently admitting unqualified modes.

    The 1007 ordinary Route/Preview remains corrected standard whole/partial.
    The separate fixed thermal method reuses standard whole-board Route.
    Existing 1000 advanced contracts stay intact.
    This is a capability guard, never a fallback or a validation pass.
    """
    if c.NATIVE_VERSION == '10.0.0':return
    scopes={'whole_board_unlocked_routing','partial_completion'} if purpose=='route' else {'whole_board_unlocked_routing'} if purpose=='thermal-recovery' else set()
    if (c.NATIVE_VERSION != '10.0.7' or scope not in scopes
            or guidance != 'native' or layers != 'source_all' or profile != 'standard'
            or adapter != 'both' or scoring is not None):
        raise Rejected('unsupported: selected Native version permits corrected-standard whole/partial Route or fixed whole-board thermal recovery on all source layers; other combinations require separate qualification')



EXPERIMENTAL_PARITY_POLICY='explicit-pinned-flat-fields-v1'
FIELD_LOCAL_SETTINGS_POLICY='job-owned-field-prl-immutable-v1'

def experimental_parity_policy(native_toolchain, enabled):
    """Explicit diagnostic opt-in; production version and route support stay fixed."""
    if type(enabled) is not bool:raise Rejected('explicit experimental parity boolean required')
    experimental_native_version(native_toolchain)
    if not enabled:return None
    if native_toolchain is None:raise Rejected('experimental parity needs an explicit pinned toolchain')
    return EXPERIMENTAL_PARITY_POLICY

EXPERIMENTAL_ROUTE_POLICY='explicit-pinned-native-route-v1'

def native_prefix(native_toolchain=None):
    """Exact worker prefix, selected by the caller rather than its receipt."""
    experimental_native_version(native_toolchain)
    if native_toolchain is None:return [str(c.PYTHON),str(c.ROOT/'autorouter/native.py')]
    return [str(native_toolchain.python),str(c.ROOT/'autorouter/native.py'),
            '--experimental-native',json.dumps(native_toolchain.record(),sort_keys=True)]


def experimental_route_record(native_toolchain, enabled):
    policy=experimental_parity_policy(native_toolchain,enabled)
    if native_toolchain is None:return {}
    if policy is None:raise Rejected('experimental routing requires explicit full schematic parity')
    return {'experimental_route_policy':EXPERIMENTAL_ROUTE_POLICY,
            'experimental_native_toolchain':native_toolchain.record(),
            'experimental_schematic_parity_policy':policy,'production_admitted':False}


def check_experimental_route(data,native_toolchain=None,experimental_schematic_parity=False):
    """A marker cannot authorize another runtime or broaden the qualified scope."""
    expected=experimental_route_record(native_toolchain,experimental_schematic_parity)
    names=('experimental_route_policy','experimental_native_toolchain',
           'experimental_schematic_parity_policy','production_admitted')
    if native_toolchain is None:
        if any(name in data for name in names) or 'experimental_native_toolchain' in data.get('tools',{}):
            raise Rejected('experimental routing requires explicit caller toolchain context')
        return
    from .floor_route import canonical
    if any(canonical(data.get(name))!=canonical(value) for name,value in expected.items()):
        raise Rejected('experimental routing marker or explicit toolchain differs')
    if (type(data.get('schema')) is not int or data.get('schema')!=1 or data.get('strategy') is not None or data.get('input_policy','native')!='native'
            or data.get('scope')!='whole_board_unlocked_routing' or data.get('adapter')!='none'
            or data.get('engine_profile')!='standard' or data.get('scoring_variant') is not None
            or data.get('baseline')!='B0' or 'routing_preferences' in data):
        raise Rejected('unsupported experimental routing scope')
    if (Path(data.get('source','')).with_suffix('.kicad_sch').name not in data.get('source_hashes',{})
            or data.get('schematic_parity')!='checked by final native DRC'):
        raise Rejected('experimental routing requires a complete checked native schematic')


def check_experimental_local_settings(directory,data,native_toolchain):
    """Reuse field and whole-worker guards after the late material reads."""
    from . import schematic_field_evidence as fields,local_settings as local
    from .floor_route import read_json
    if fields.has_fields(data.get('native',{}).get('findings',[])):
        fields.check_local_settings(directory,'final-drc',read_json(Path(directory)/'final-drc-binding.json'))
    local.check_normal_policy(directory,data,native_toolchain=native_toolchain)


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

def check_storage(*, active_root=None):
    """Fresh logical-size/headroom guard for active work, or explicit archive audit.

    Runtime callers pass their exact job root. Retained research is not part of
    a running job and is neither required nor traversed. The no-argument form
    preserves the separate finite 18 GiB archive audit for setup/research tools.
    This is a sampled guard, not a filesystem quota or hostile-writer sandbox.
    """
    limit=18*1024**3; total=0; deadline=time.monotonic()+15.0
    volume=c.ROOT
    if active_root is None:
        scopes=[c.ROOT/name for name in ('.data','.tools','.runs')]
    else:
        from .local_settings import canonical
        root=canonical(Path(active_root).absolute())
        if root in (c.ROOT,*[c.ROOT/name for name in ('.data','.tools','.runs')]) or root==Path(root.anchor):
            raise Rejected('active storage guard requires an individual job root')
        scopes=[root];volume=root
        while not volume.exists():volume=volume.parent
    for root in scopes:
        remaining=deadline-time.monotonic()
        if remaining<=0:raise Rejected('project cache/data size scan exceeded time bound')
        try:
            try:os.lstat(root)
            except FileNotFoundError:continue  # Only an initially absent top-level scope.
            total+=_workdir_bytes(root,limit-total,max_entries=500_000,
                                 max_seconds=remaining,count_file_symlinks=True)
        except (OSError,RuntimeError) as exc:
            raise Rejected('project cache/data size scan failed: '+str(exc)) from exc
        if total>limit:raise Rejected('18 GiB '+('project cache/data' if active_root is None else 'active job')+' ceiling exceeded')
    if time.monotonic()>deadline:raise Rejected('project cache/data size scan exceeded time bound')
    if shutil.disk_usage(c.ROOT).free<2*1024**3 or (volume!=c.ROOT and shutil.disk_usage(volume).free<2*1024**3):
        raise Rejected('less than 2 GiB disk headroom')
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
        copper_count=sum(isinstance(x,list) and len(x)>2 and re.fullmatch(r'(?:F|B|In[0-9]+)\.Cu',sx.unquote(x[1])) is not None for x in layers)
        if copper_count==4:
            from .netclass import four_copper_source_layers
            four_copper_source_layers(sx.read(board))
        elif copper_count!=2:raise ValueError('native netclasses require canonical two or four copper layers')
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
            root_knockout=(len(layers)==1 and len(layers[0])==3
                and id(node) in root_texts and key=='gr_text'
                and isinstance(layers[0][1],str)
                and sx.unquote(layers[0][1]) in {'F.SilkS','B.SilkS','F.Cu','B.Cu'}
                and layers[0][2]=='knockout')
            if len(layers)!=1 or (len(layers[0])!=2 and not root_knockout) or not isinstance(layers[0][1],str):
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

def task_choices_for_record(data,*,input_policy=None):
    """Read consistent recorded choices; all evidence readers still apply."""
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
    return (scope,policy,layers)


def task_scope_for_record(data,directory,*,input_policy=None):
    """Derive task choices for narrow legacy syntax; never an acceptance flag.

    Existing captured-choice/process readers still verify their full proofs.
    Missing/mixed choices return no admission context. Modern preflight ignores
    this context; 20240108 requires the exact whole/native/source_all tuple.
    """
    choices=task_choices_for_record(data,input_policy=input_policy)
    if choices is None:return None
    if (selected_scope_markers(directory,data) or layer_markers(directory,data)
            or data.get('protected_routes',0)!=0):return None
    if 'protected_route_import' in data:
        # Current normal whole-board producers retain strict reconciliation even
        # with zero protection. Its presence alone is not protected copper.
        binding=data['protected_route_import']
        if (type(binding) is not dict or set(binding)!={'policy','matches','transplanted_routes_sha256','imported_sha256'}
                or binding['policy']!='exact_non_uuid_lock_position_v2' or binding['matches']!=[]
                or any(type(binding[key]) is not str or re.fullmatch('[0-9a-f]{64}',binding[key]) is None
                       for key in ('transplanted_routes_sha256','imported_sha256'))):return None
    return choices


def check_schematic_class_support(board, *, class_context=None):
    """Refuse by default; explicit Route context permits pending Native proof.

    Examine every captured modern schematic, including child directories.
    Native format/parity checks retain responsibility for other SCH semantics.
    """
    from .placement_clearance import inventory, read_bytes
    try:
        if class_context is not None and (type(class_context) is not str or class_context != 'native-route-flat-classes-v1'):
            raise ValueError('unknown schematic class context')
        root = Path(board).parent
        pending_class_check = False
        captured = inventory(root, max_bytes=100*1024**2,
                             max_files=2000, max_entries=4000)
        for name, expected in captured.items():
            if Path(name).suffix.casefold() != '.kicad_sch':
                continue
            raw = read_bytes(root/name)
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError('schematic changed during class-intent check: '+name)
            tree = sx.parse(raw.decode('utf-8'))
            if not tree or tree[0] != 'kicad_sch':
                raise ValueError('unknown schematic root: '+name)
            version = sx.one(tree, 'version')
            if (version is None or len(version) != 2
                    or type(version[1]) is not str or len(version[1]) != 8
                    or not version[1].isascii() or not version[1].isdecimal()
                    or int(version[1]) <= 0):
                raise ValueError('malformed schematic version: '+name)
            pending = [tree]
            while pending:
                node = pending.pop()
                if node and node[0] == 'netclass_flag':
                    if class_context is None:
                        raise ValueError('schematic netclass_flag unsupported: PCB class '
                                         'membership and inheritance are not independently '
                                         'verified: '+name)
                    pending_class_check = True
                if node and node[0] == 'sheet':
                    raise ValueError('schematic hierarchy dependency closure and class '
                                     'intent are not independently verified: '+name)
                pending.extend(child for child in node[1:] if isinstance(child, list))
        if pending_class_check:
            from .schematic_class_evidence import requirement
            required = requirement(board)
            if required is None:
                raise ValueError('source class directive requires Native proof')
            return required
    except (OSError, ValueError, Rejected) as exc:
        raise Rejected('schematic class intent not qualified: '+str(exc)) from exc


def class_context_for_record(data,directory,*,input_policy,native_toolchain=None):
    """Only ordinary native Route and its checked export may request this proof.

    The context permits static eligibility. Actual task/final Native evidence is
    separately mandatory and is detected from the source, never a receipt flag.
    """
    if (type(data) is not dict or input_policy!='native' or native_toolchain is not None or 'strategy' in data
            or type(data.get('schema')) is not int or data['schema']!=1
            or data.get('engine_profile') not in {'standard','tuned','completion-only'}
            or any(key in data for key in ('engine_fanout_override','engine_optimizer_override','engine_angle_binding',
                'engine_planning_clearance_margin_nm','engine_global_width_policy','experimental_route_policy',
                'experimental_native_toolchain','experimental_schematic_parity_policy','production_admitted',
                'diagnostic_schema','production_qualified'))):
        return None
    choices=task_choices_for_record(data,input_policy=input_policy)
    if choices is None or selected_scope_markers(directory,data) or layer_markers(directory,data):return None
    scope,guidance,layers=choices
    if scope not in {'whole_board_unlocked_routing','partial_completion'} or guidance!='native' or layers!='source_all':
        return None
    return 'native-route-flat-classes-v1'


def check_route_class_evidence(directory,data,original,candidate,*,class_context):
    """Replay both actual observations, including a reconstructed preengine task."""
    from . import schematic_class_evidence as classes
    required=check_schematic_class_support(Path(data['source']),class_context=class_context)
    if required is None:
        if any(classes.present(directory,data,stage) for stage in ('task','final')):
            raise Rejected('unexpected schematic class evidence on an unflagged source')
        return False
    if class_context is None or not all(key in data for key in ('schematic_class_task','schematic_class_final')):
        raise Rejected('missing source and final schematic class proof')
    from .placement_clearance import read_bytes, evidence_inventory, inventory, verify_candidate
    material=evidence_inventory(Path(directory))
    if required['source_hashes']!=data['source_hashes']:
        raise Rejected('class proof source project differs')
    raw_project=read_bytes(candidate.with_suffix('.kicad_pro'));raw_schematic=read_bytes(candidate.with_suffix('.kicad_sch'))
    task=routing_task(original,data['scope'],selected_scope_names(data))
    task_raw=(sx.dump(task)+'\n').encode()
    if hashlib.sha256(task_raw).hexdigest()!=data.get('task_sha256'):
        raise Rejected('class proof routing task differs')
    classes.check(directory,data,'task',board_raw=task_raw,source=str(candidate),project_raw=raw_project,
        schematic_raw=raw_schematic,native_map=Path(directory)/'export-netclasses.json')
    classes.check(directory,data,'final',board_raw=read_bytes(candidate),source=str(candidate),project_raw=raw_project,
        schematic_raw=raw_schematic,native_map=Path(directory)/'final-netclasses.json')
    verify_candidate(candidate,data['source_hashes'],data['candidate_sha256'])
    if inventory(Path(data['source']).parent,max_bytes=100*1024*1024)!=data['source_hashes'] or evidence_inventory(Path(directory))!=material:
        raise Rejected('class routing evidence/source changed during replay')
    for stage in ('task','final'):classes.check_local_settings(directory,stage)
    return True


def preflight(board,*,task_scope=None,class_context=None):
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
    try: check_schematic_class_support(board,class_context=class_context)
    except Rejected as exc: reasons.append(str(exc))
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

def selected_proposal_protection(original,names):
    """Require exact source protection and conservatively refuse selected locks."""
    from . import routing_scope as rs, board_floor as g
    names=rs.validate_names(names);protected=rs.protected_routes(original,names)
    _,resolve=g.source_net_identity(original)
    if any(resolve(sx.one(route,'net')) in names for route in protected):
        raise Rejected('selected proposals with locked selected copper are unqualified')
    return protected


def normal_selected_import_policy(original,names):
    """Source-derived strict fallback preserves previously supported selected locks."""
    from . import routing_scope as rs,board_floor as g
    names=rs.validate_names(names);protected=rs.protected_routes(original,names)
    _,resolve=g.source_net_identity(original)
    return (normal_strict_import_policy(original,protected) if any(resolve(sx.one(route,'net')) in names for route in protected)
            else SELECTED_PROPOSAL_IMPORT_POLICY)


def legacy_via_omitted(route):
    return (route[0]=='via' and not any(sx.children(route,key)
            for key in ('capping','covering','plugging','filling')))


def normal_strict_import_policy(original,protected):
    """Only the qualified legacy source population has implicit OFF modes.

    Pinned KiCad10 parser <20250228: omission is OFF; modern omission inherits.
    Restrict admission to our already supported20241229 source format. Final
    reconstruction always restores the entire literal original via record.
    """
    return (PROTECTED_VIA_IMPORT_POLICY if sx.children(original,'version')==[['version','20241229']]
            and any(legacy_via_omitted(route) for route in protected)
            else 'exact_non_uuid_lock_position_v2')


def routing_task(original,scope,names=None):
    """The exact fixed-placement export preimage, shared with proof readers."""
    if scope=='selected_nets':
        from . import routing_scope as rs
        task=rs.task(original,names)
    elif scope in {'whole_board_unlocked_routing','partial_completion'}:
        task=copy.deepcopy(original)
        if scope=='whole_board_unlocked_routing':
            task[:]=[node for node in task if not isinstance(node,list) or not node or node[0] not in ROUTES or locked(node)]
    else:raise Rejected('unknown original routing task scope')
    for zone in sx.children(task,'zone'):
        zone[:]=[node for node in zone if not isinstance(node,list) or not node or node[0] not in DERIVED_ZONE]
    return task


def normal_import_contract(directory,data,imports,*,input_policy,original,native_toolchain=None):
    """Force current direct normal import proofs from captured producer code.

    Import rows come only from the existing checked Native process census.
    Genuine older producers retain their original strict readback contract.
    """
    experimental_native_version(native_toolchain)
    from .local_settings import canonical,policy_declarations
    from .placement_clearance import read_bytes
    root=canonical(Path(directory));producer=root/'code/pipeline.py'
    raw=read_bytes(producer,1024**2)
    if hashlib.sha256(raw).hexdigest()!=data.get('tools',{}).get('implementation_sha256',{}).get('autorouter/pipeline.py'):
        raise Rejected('normal selected import producer differs')
    requested={'NORMAL_SELECTED_PROPOSAL_IMPORT_POLICY':SELECTED_PROPOSAL_IMPORT_POLICY}
    if input_policy=='native':
        requested['NORMAL_PROTECTED_VIA_IMPORT_POLICY']=PROTECTED_VIA_IMPORT_POLICY
        requested['NORMAL_TASK_COPPER_FIXED_POLICY']='native-task-copper-fixed-v1'
    declarations=policy_declarations(raw,requested)
    policy=declarations['NORMAL_SELECTED_PROPOSAL_IMPORT_POLICY']
    marker=data.get('tools',{}).get('normal_selected_proposal_import_policy')
    strict_declaration=None
    if input_policy=='native':
        if declarations['NORMAL_TASK_COPPER_FIXED_POLICY'] is None and b'from .task_copper import check_contract' in raw:
            raise Rejected('task copper pipeline source declaration missing')
        from .task_copper import check_contract
        check_contract(root,data,imports,declaration=declarations['NORMAL_TASK_COPPER_FIXED_POLICY'],native_toolchain=native_toolchain)
        strict_declaration=declarations['NORMAL_PROTECTED_VIA_IMPORT_POLICY']
        strict_marker=data.get('tools',{}).get('normal_protected_via_import_policy')
        if strict_declaration is None:
            if strict_marker is not None or b'\ndef normal_strict_import_policy(' in raw:
                raise Rejected('normal protected via source declaration missing')
        elif strict_marker!=strict_declaration or policy is None:
            raise Rejected('normal protected via tool/selected source declaration missing')
    if policy is None:
        if marker is not None:raise Rejected('normal selected import source declaration missing')
        return None
    if marker!=policy:raise Rejected('normal selected import tool declaration missing')
    if imports is None:raise Rejected('normal selected import requires qualified Native import census')
    direct=[row for row in imports if row['cwd']==str(root)]
    if direct and data.get('strategy')=='native_validated_thermal_bridge':
        raise Rejected('thermal parent requires its checked incumbent, not a direct import')
    # input_policy is derived by the existing receipt_policy/recognize readers,
    # never directly from a JSON label. Nested incumbents have their own receipt.
    if input_policy!='native':return None
    strict_policy=(normal_strict_import_policy(original,protected_for_record(data,original))
        if strict_declaration is not None and native_toolchain is None else 'exact_non_uuid_lock_position_v2')
    if type(data.get('schema')) is not int or data['schema']!=1:raise Rejected('normal import requires native schema1')
    if not direct:
        # Only recognized native parent methods can lack an own import. A
        # relocated process or phase annotation is not an incumbent receipt.
        from .floor_route import read_json,canonical as encode
        strategy=data.get('strategy');helper={'native_validated_zone_net_pruning':'strategy.py',
            'native_validated_thermal_bridge':'recovery.py'}.get(strategy)
        if (helper is None or data.get('baseline')!='C-prototype'
                or data.get('scope')!='whole_board_unlocked_routing' or selected_scope_markers(root,data)):
            raise Rejected('current normal routing requires its exact direct import population')
        if hashlib.sha256(read_bytes(root/'code'/helper,1024**2)).hexdigest()!=data['tools']['implementation_sha256'].get('autorouter/'+helper):
            raise Rejected('normal parent implementation provenance missing')
        child=root/'incumbent';inc=read_json(child/'result.json')
        if (any(inc.get(key)!=data.get(key) for key in ('source','source_hashes','tools'))
                or type(inc.get('schema')) is not int or inc['schema']!=1 or inc.get('scope')!='whole_board_unlocked_routing'
                or inc.get('adapter')!='both' or inc.get('input_policy') not in (None,'native')
                or len(imports)!=1 or imports[0]['cwd']!=str(child)
                or [dict(step,phase='incumbent') for step in inc.get('steps',[])]!=[step for step in data['steps'] if step.get('phase')=='incumbent']):
            raise Rejected('normal parent import differs from actual incumbent receipt')
        child_candidate=child/'candidate'/Path(data['source']).name
        if inc.get('candidate')!=str(child_candidate):raise Rejected('normal parent incumbent candidate escaped')
        child_contract=normal_import_contract(child,inc,imports,input_policy='native',original=original)
        if child_contract is None:raise Rejected('normal parent incumbent lacks its direct import proof')
        verify_candidate_files(child_candidate,data['source_hashes'],inc['candidate_sha256'])
        if immutable(sx.read(child_candidate))!=immutable(original):raise Rejected('normal parent incumbent source geometry changed')
        child_protected=protected_for_record(inc,original)
        check_protected_import(child,inc,original,child_candidate,child_protected,**child_contract)
        if strategy=='native_validated_zone_net_pruning':
            # The calling check_result already checks scoring and this exact
            # accepted child; repeat its shared reader, never trust a JSON flag.
            from .strategy import check_incumbent_scoring
            check_incumbent_scoring(root,data)
        else:
            from . import thermal
            strict_parent=thermal.check_parent_scope(root,data)
            expected_profile=thermal.parent_profile() if strict_parent else 'completion-only'
            if strict_parent:
                # A rejected incumbent does not pass the positive result reader.
                # Replay its actual configuration and complete budget here too;
                # a profile label cannot conceal a differently tuned child.
                check_normal_engine_provenance(child,inc)
                check_engine_profile_record(inc,child)
                check_resource_accounting(inc)
                if (inc.get('baseline')!=engine_baseline(expected_profile,'both')
                        or inc.get('budget_seconds')!=data.get('incumbent_assigned_seconds')
                        or inc.get('cpu_budget_seconds')!=data.get('incumbent_assigned_seconds')
                        or not 5<=inc['budget_seconds']<=data['budget_seconds']-40.0
                        or any(k in inc for k in ('engine_fanout_override','engine_optimizer_override',
                            'engine_angle_binding','engine_planning_clearance_margin_nm','engine_global_width_policy'))):
                    raise Rejected('thermal incumbent configuration or assigned budget differs')
            expected={'receipt':str(child/'result.json'),'receipt_sha256':sha(child/'result.json'),
                'status':inc.get('status'),'accepted':inc.get('accepted')}
            if (encode(data.get('incumbent'))!=encode(expected) or inc.get('engine_profile')!=expected_profile
                    or type(inc.get('accepted')) is not bool):raise Rejected('thermal parent incumbent binding differs')
            if inc['accepted']:check_result(child/'result.json')
            elif inc.get('status')=='drc_rejected' and thermal.sole_thermal(inc.get('native')) is not None:
                thermal._report_binding(child_candidate,child/'final-drc.json',child/'final-drc-binding.json',data['source_hashes'],inc['native'])
                known_named=check_named_edge_policy(child,inc,input_policy='native',direct_import=True)
                check_pour_evidence(child,inc,original,child_candidate,_known_named_edge=known_named)
                check_native_edge_transport(child,inc,_known_named_edge=known_named)
            else:raise Rejected('thermal parent incumbent is not a qualified original Native outcome')
            thermal.check_parent_selection(root,data,inc)
        return None
    pins=data['tools']['implementation_sha256']
    for name in ('adapter.py','routing_scope.py','board_floor.py','preferences.py','sexpr.py'):
        if hashlib.sha256(read_bytes(root/'code'/name,1024**2)).hexdigest()!=pins.get('autorouter/'+name):
            raise Rejected('normal selected import helper provenance missing')
    candidate=root/'candidate'/Path(data['source']).name
    expected={'cwd':str(root),'name':'import','source':str(candidate),
              'output':str(root/'imported.kicad_pcb'),'session':str(root/'routes.ses')}
    if direct!=[expected]:raise Rejected('normal selected import direct worker identity differs')
    # Retain the exact preimage and independently check the actual saved worker,
    # including zone-free boards. A plausible saved board alone is not evidence.
    from . import floor_route as f
    before_path=root/'pre-refill.kicad_pcb';before=sx.parse(read_bytes(before_path).decode('utf-8'))
    if immutable(before)!=immutable(original) or routes(before)!=routes(sx.read(candidate)):
        raise Rejected('normal saved refill changed original geometry or routes')
    refill=root/'refill'/candidate.name
    f.check_drc_stage(root,data,'refill-drc',refill,refill,True,
        {**data['source_hashes'],candidate.name:sha(before_path)},sandboxed=False,native_toolchain=native_toolchain)
    if (sx.dump(transplant_fill(before,sx.read(refill)))+'\n').encode()!=read_bytes(candidate):
        raise Rejected('normal saved refill reconstruction differs')
    binding=data.get('protected_route_import')
    if not isinstance(binding,dict):raise Rejected('current normal import requires complete proof, including zero protection')
    names=selected_scope_names(data)
    if names is None:
        if binding.get('policy')!=strict_policy:
            raise Rejected('nonselected normal import requires strict policy')
        return {'strict_expected_policy':strict_policy} if strict_policy==PROTECTED_VIA_IMPORT_POLICY else {}
    required=normal_selected_import_policy(original,names)
    if required!=policy:required=strict_policy
    if binding.get('policy')!=required:raise Rejected('normal selected import policy differs from original locks')
    if required==policy:return {'expected_policy':policy,'selected_names':names}
    return {'strict_expected_policy':strict_policy} if strict_policy==PROTECTED_VIA_IMPORT_POLICY else {}


def transplant_routes(original, imported, *, protected=(), audit=None, policy='exact_non_uuid_v1', selected_names=None):
    if policy==SELECTED_PROPOSAL_IMPORT_POLICY:
        # Explicit proposal selection with caller-forced scope/proof. Imported nonselected
        # routes are not preservation evidence; restore the exact source records.
        from . import routing_scope as rs, board_floor as g
        names=rs.validate_names(selected_names);protected=list(protected)
        expected=selected_proposal_protection(original,names)
        source_names,resolve=g.source_net_identity(original)
        _,import_resolve=g.source_net_identity(imported)
        if protected!=expected:raise Rejected('selected proposals require the complete exact source protection')
        rs._route_map(imported)  # Refuse malformed/ambiguous imported route IDs and locks.
        generated=[];selected=[];ignored=[]
        for raw in routes(imported):
            name=import_resolve(sx.one(raw,'net'))
            if not name or name not in source_names:raise Rejected('imported proposal has no exact source net identity')
            converted=convert_route_nets(raw,imported,original)
            if resolve(sx.one(converted,'net'))!=name:raise Rejected('proposal net conversion changed native identity')
            record={'kind':raw[0],'uuid':sx.unquote(sx.one(raw,'uuid')[1]),'net_name':name,
                    'imported_record_sha256':hashlib.sha256(sx.dump(raw).encode()).hexdigest()}
            if name in names:
                generated.append(converted);selected.append({**record,'converted_record_sha256':hashlib.sha256(sx.dump(converted).encode()).hexdigest()})
            else:ignored.append(record)
        out=copy.deepcopy(original)
        out[:]=[node for node in out if not isinstance(node,list) or not node or node[0] not in ROUTES]
        out.extend(copy.deepcopy(protected));out.extend(generated)
        rs.audit(original,out,names)  # Exact source records, generated IDs/locks/nets; never Native acceptance.
        if audit is not None:
            audit.update(policy=policy,requested_names=names,
                source_immutable_sha256=hashlib.sha256(sx.dump(immutable(original)).encode()).hexdigest(),
                protected_source_records=[{'kind':node[0],'uuid':sx.unquote(sx.one(node,'uuid')[1]),
                    'record_sha256':hashlib.sha256(sx.dump(node).encode()).hexdigest()} for node in protected],
                selected_proposals=selected,ignored_nonselected_proposals=ignored,
                transplanted_routes_sha256=hashlib.sha256(sx.dump(routes(out)).encode()).hexdigest())
        return out
    if selected_names is not None:raise Rejected('explicit selected names require the selected proposal policy')
    if policy not in {'exact_non_uuid_v1','exact_non_uuid_lock_position_v2',PROTECTED_VIA_IMPORT_POLICY}:
        raise Rejected('unknown protected import policy')
    legacy_vias=policy==PROTECTED_VIA_IMPORT_POLICY
    if legacy_vias and (sx.children(original,'version')!=[['version','20241229']]
            or sx.children(imported,'version')!=[['version','20260206']]):
        raise Rejected('protected legacy via policy requires exact source/import formats')
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
            if policy in {'exact_non_uuid_lock_position_v2',PROTECTED_VIA_IMPORT_POLICY}:
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
        matches={};legacy_matches={}
        off_fields={'capping':['capping','no'],
            'covering':['covering',['front','no'],['back','no']],
            'plugging':['plugging',['front','no'],['back','no']],
            'filling':['filling','no']}
        for index,route in enumerate(imported_routes):
            matches.setdefault(signature(route),[]).append(index)
            # A separate map prevents explicit source values or modern inherited
            # omission from using this rule. Require all six explicit OFF values,
            # once each, with no extra subfields; no general flag stripping.
            if legacy_vias and route[0]=='via' and all(sx.children(route,key)==[value] for key,value in off_fields.items()):
                stripped=[node for node in route if not isinstance(node,list) or not node or node[0] not in off_fields]
                legacy_matches.setdefault(signature(stripped),[]).append(index)
        def matching(route):
            return (legacy_matches if legacy_vias and legacy_via_omitted(route) else matches).get(signature(route),[])
        used=set()
        for route in protected:
            if original_counts.get(sx.dump(route))!=1:
                raise Rejected('protected import route is not a unique original')
            identity(route)
            indices=matching(route)
            if len(indices)!=1 or indices[0] in used:
                raise Rejected('protected route missing, changed or ambiguous after import')
            used.add(indices[0])
        ids=[identity(route) for route in imported_routes]
        if len(set(ids))!=len(ids):raise Rejected('duplicate imported route UUID')
        for route in protected:
            index=matching(route)[0]
            reconciled.append({'original_uuid':identity(route),'imported_uuid':identity(imported_routes[index]),
                'non_uuid_sha256':hashlib.sha256(signature(route).encode()).hexdigest(),
                **({'legacy_explicit_off_restored':True} if legacy_vias and legacy_via_omitted(route) else {})})
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


def check_protected_import(directory, data, original, candidate, protected, *, expected_policy=None, selected_names=None, strict_expected_policy=None):
    binding=data.get('protected_route_import')
    if strict_expected_policy is not None or isinstance(binding,dict) and binding.get('policy')==PROTECTED_VIA_IMPORT_POLICY:
        if (strict_expected_policy!=PROTECTED_VIA_IMPORT_POLICY or expected_policy is not None or selected_names is not None
                or not isinstance(binding,dict) or binding.get('policy')!=strict_expected_policy
                or normal_strict_import_policy(original,protected)!=strict_expected_policy):
            raise Rejected('source-derived strict protected via readback proof required')
    proposal_readback=(expected_policy is not None or selected_names is not None
        or isinstance(binding,dict) and binding.get('policy')==SELECTED_PROPOSAL_IMPORT_POLICY)
    if proposal_readback:
        # Qualified normal callers and diagnostic actors must force this policy
        # independently of the optional record, including zero protection.
        if (expected_policy!=SELECTED_PROPOSAL_IMPORT_POLICY or selected_names is None
                or data.get('scope')!='selected_nets' or not isinstance(binding,dict)
                or binding.get('policy')!=expected_policy):
            raise Rejected('explicit selected proposal policy/readback proof required')
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
    rebuilt=transplant_routes(original,sx.parse(raw.decode('utf-8')),protected=protected,audit=audit,policy=binding.get('policy'),
        **({'selected_names':selected_names} if proposal_readback else {}))
    if canonical(audit)!=canonical(data['protected_route_import']):raise Rejected('protected import reconciliation differs')
    if routes(sx.read(candidate))!=routes(rebuilt):raise Rejected('protected import routes differ from final candidate')

def check_refill_route_nets(original, filled):
    """A saved Native refill must validate the same route net identities.

    Numbered-to-named serialization is legitimate; silently assigning a route
    to a different net is not. Reuse strict native net/UUID decoders.
    """
    from . import board_floor as g, routing_scope as rs
    def identities(tree):
        _,resolve=g.source_net_identity(tree)
        return {identity:(route[0],resolve(sx.one(route,'net')))
                for identity,route in rs._route_map(tree).items()}
    try:before,after=identities(original),identities(filled)
    except (ValueError,KeyError,TypeError) as exc:
        raise Rejected('ambiguous Native refill route identity: '+str(exc)) from exc
    if before!=after:
        raise Rejected('Native refill changed route identities or net assignments')


def transplant_fill(original, filled):
    check_refill_route_nets(original,filled)
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
        proof=fields.readback(path,data,native_toolchain=native_toolchain)
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
    def __init__(self, out, seconds, *, native_toolchain=None, protect_local_settings=False, experimental_schematic_parity=False):
        experimental_native_version(native_toolchain)
        self.native_toolchain=native_toolchain
        self.experimental_schematic_parity=experimental_schematic_parity
        if experimental_parity_policy(native_toolchain,experimental_schematic_parity) is not None and protect_local_settings is not True:
            raise Rejected('experimental parity requires protected local settings')
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
        # Parent -B is not inherited by KiCad's separate Python workers. Keep
        # derived bytecode out of the manifest-bound product directory.
        self.env.update(LANG='C',LC_ALL='C',PYTHONDONTWRITEBYTECODE='1')
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
        if result['status']=='cancelled':raise KeyboardInterrupt
        if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed:
            raise Rejected(name+': '+result['status']+' exit='+str(result['exit_code']))
        experimental_native_version(self.native_toolchain)
        return result
    def native(self,name,action,board,output,*args):
        prefix=[] if self.native_toolchain is None else ['--experimental-native',json.dumps(self.native_toolchain.record(),sort_keys=True)]
        return self.step(name,[self.native_python,c.ROOT/'autorouter/native.py',*prefix,action,board,output,*args])
    def drc(self,name,board,save=False,*,schematic_parity=False):
        # No input copy, immutable flag or worker journal for an expired job.
        # The step still rechecks its budget; uncertain later failures stay closed.
        if self.deadline-time.monotonic()<=0:
            raise Rejected('timeout: whole task budget exhausted before DRC preparation')
        policy=experimental_parity_policy(self.native_toolchain,self.experimental_schematic_parity)
        if self.native_toolchain is not None and schematic_parity and policy is None:
            raise Rejected('experimental schematic parity needs explicit diagnostic opt-in')
        if policy is not None and self.protect_local_settings is not True:
            raise Rejected('experimental parity requires protected local settings')
        stage_policy=policy if schematic_parity else None
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
        if stage_policy is not None:local_settings_binding['experimental_schematic_parity_policy']=stage_policy
        if self.protect_local_settings and schematic_parity:local_settings_binding['field_local_settings_policy']=FIELD_LOCAL_SETTINGS_POLICY
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

def audit_candidate_netclasses(candidate, protected, native, *, native_toolchain=None):
    from .netclass import audit_native
    project=candidate.with_suffix('.kicad_pro')
    if (native.get('source')!=str(candidate) or native.get('board_sha256')!=sha(candidate)
            or native.get('project_sha256')!=sha(project) or native.get('board_saved') is not False):
        raise Rejected('native netclass map is not bound to candidate and original project')
    from .netclass import PARENT_POLICY
    policy=netclass_policy(candidate)
    source_tree=sx.read(candidate)
    if 'copper_layers' in native or sum(isinstance(x,list) and len(x)>2 and re.fullmatch(r'(?:F|B|In[0-9]+)\.Cu',sx.unquote(x[1])) is not None for x in sx.one(source_tree,'layers',[]))==4:
        from .netclass import four_copper_source_layers,four_copper_native_layers
        if four_copper_source_layers(source_tree)!=four_copper_native_layers(native):raise Rejected('source/native copper layers differ')
    mapping=audit_native(native,json.loads(project.read_text()),parent_policy=policy is not None and policy['mode']==PARENT_POLICY,native_toolchain=native_toolchain)
    dimensions=audit_route_dimensions(source_tree,protected,native)
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

def check_pour_evidence(directory,data,original,candidate,*,source_hashes=None,correction=True,sandboxed=None,_known_named_edge=False):
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
        adapted,_=native_edge.correct(adapted,native_edge_context(directory/'snapshot'/candidate.name,known_named=_known_named_edge))
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


def validate_candidate(job, original, candidate, source_hashes, protected, *, guidance_contract=None, guidance_basis=None, layer_contract=None, selected_names=None, schematic_parity=False, class_context=None):
    # A complete captured native schematic must participate in final acceptance
    # for every routing scope, including optimizer trials and fresh exports.
    schematic_parity=schematic_parity or Path(candidate).with_suffix('.kicad_sch').name in source_hashes
    class_requirement=check_schematic_class_support(candidate,class_context=class_context)
    if class_requirement is not None and (guidance_contract is not None or layer_contract is not None or selected_names is not None or getattr(job,'native_toolchain',None) is not None):
        raise Rejected('unsupported: flat class proof requires ordinary native whole/partial Route')
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
    # Preserve the Native save preimage for exact later worker/fill replay.
    from .placement_clearance import read_bytes
    preimage=job.out/'pre-refill.kicad_pcb';raw=read_bytes(candidate)
    if preimage.exists() or preimage.is_symlink():
        if read_bytes(preimage)!=raw:raise Rejected('retained pre-refill input differs')
    else:
        with preimage.open('xb') as stream:stream.write(raw)
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
    elif netclass_policy(candidate) is not None or getattr(job,"native_toolchain",None) is not None:
        mapping=job.out/'final-netclasses.json'
        job.native('final-netclasses','netclasses',candidate,mapping)
        audited=audit_candidate_netclasses(candidate,protected,json.loads(mapping.read_text()),native_toolchain=getattr(job,"native_toolchain",None))
        audited['native_map_file_sha256']=sha(mapping)
        save_json(job.out/'final-netclass-audit.json',audited)
    if selected_names is not None:rs.audit(original,sx.read(candidate),selected_names)
    native=job.drc('final-drc',candidate,schematic_parity=True) if schematic_parity else job.drc('final-drc',candidate)
    if class_requirement is not None:
        from . import schematic_class_evidence as classes
        job.schematic_class_final=classes.collect(job,'final',candidate,job.out/'final-netclasses.json')
    verify_candidate_files(candidate,source_hashes,final_hash)
    legacy=legacy_zone_evidence(original,candidate)
    if legacy is not None:save_json(job.out/'legacy-zone-witness.json',legacy)
    return final_hash,native


def selected_tool_pins():
    """One fresh selected-role map for execution and retained receipt checks."""
    try:
        selection=c.current_native_selection()
        return {**json.loads((c.ROOT/'toolchain.lock.json').read_text())['tools'],**selection['tools']}
    except (ValueError,OSError,KeyError,TypeError) as exc:
        raise Rejected('selected native toolchain changed or invalid: '+str(exc)) from exc


def check_recorded_tool_pins(tools, *, native_toolchain=None):
    pins=selected_tool_pins()
    expected={str(c.resolve_tool_path(pin['path'])):pin['sha256'] for name,pin in pins.items()
              if native_toolchain is None or name in {'java','freerouting'}}
    recorded=tools.get('files',{})
    if (not isinstance(recorded,dict) or any(recorded.get(path)!=digest for path,digest in expected.items())
            or native_toolchain is None and c.NATIVE_VERSION!='10.0.0' and set(recorded)!=set(expected)):
        raise Rejected('recorded tool pins differ from qualified toolchain')


def tool_manifest(*,native_toolchain=None):
    version=experimental_native_version(native_toolchain)
    expected=selected_tool_pins()
    resolved={name:c.resolve_tool_path(pin['path']) for name,pin in expected.items()}
    if resolved.get('freerouting')!=c.JAR: raise Rejected('engine pin does not identify project-local JAR')
    native=(c.CLI,c.PYTHON,c.PCBNEW) if native_toolchain is None else (native_toolchain.cli,native_toolchain.python,native_toolchain.pcbnew)
    files={str(p):sha(p) for p in (*native,c.JAVA,c.JAR) if p.is_file()}
    for name, pin in expected.items():
        if native_toolchain is not None and name not in {'java','freerouting'}:continue
        path=resolved[name]
        if (files.get(str(path))!=pin['sha256'] or path.stat().st_size!=pin['bytes']): raise Rejected('pinned tool changed or missing: '+name)
    implementation={str(p.relative_to(c.ROOT)):sha(p) for p in sorted((c.ROOT/'autorouter').glob('*.py'))}
    from .provenance import source_identity
    try:identity=source_identity(c.ROOT,implementation)
    except (ValueError,OSError,subprocess.SubprocessError) as exc:
        raise Rejected('runtime source provenance unavailable: '+str(exc)) from exc
    return {'implementation_sha256':implementation,'git_head':identity['git_head'],'source_provenance':identity,'kicad':version,'freerouting':'2.5.0','files':files,'network':'engine sandbox-exec deny network*',
            'normal_drc_local_settings_policy':NORMAL_DRC_LOCAL_SETTINGS_POLICY,
            'normal_selected_proposal_import_policy':NORMAL_SELECTED_PROPOSAL_IMPORT_POLICY,
            'normal_protected_via_import_policy':NORMAL_PROTECTED_VIA_IMPORT_POLICY,
            'normal_task_copper_fixed_policy':NORMAL_TASK_COPPER_FIXED_POLICY,
            'normal_native_export_alias_policy':NORMAL_NATIVE_EXPORT_ALIAS_POLICY,
            **({'experimental_native_toolchain':native_toolchain.record()} if native_toolchain is not None else {})}

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


def engine_profile_settings(profile, remaining_seconds, *, strict_class_targets=False, scoring_variant=None, experimental_free_angle=False, fanout_enabled=None, experimental_fanout=False, optimizer_enabled=None, experimental_optimizer=False, global_width_policy=None):
    """Assign cooperative internal deadlines inside the outer wall budget.

    Freerouting accepts numeric seconds or HH:mm:ss, not values such as 90s.
    Its job monitor permits 30 seconds of graceful stopping. Both that grace
    and a native-finalization planning reserve are withheld uniformly. The
    supervisor and measured CPU acceptance cap remain authoritative.
    """
    if profile not in {'standard','tuned','completion-only','tuned-free-angle'}: raise Rejected('unknown engine profile')
    if type(experimental_free_angle)is not bool:raise Rejected('typed experimental free-angle profile opt-in required')
    if profile=='tuned-free-angle' and not experimental_free_angle:
        raise Rejected('unsupported: free-angle profile requires explicit native baseline opt-in')
    if global_width_policy is not None and (type(global_width_policy)is not str or global_width_policy!=ENGINE_GLOBAL_WIDTH_POLICY
            or strict_class_targets is not True or profile!='tuned-free-angle' or experimental_free_angle is not True
            or fanout_enabled is not False or experimental_fanout is not True
            or optimizer_enabled is not False or experimental_optimizer is not True):
        raise Rejected('global width policy requires literal strict free-angle optimizerFalse/fanoutFalse settings')
    if fanout_enabled is not None and fanout_enabled is not False:raise Rejected('fanout override accepts only None or typed False')
    if type(experimental_fanout)is not bool:raise Rejected('typed fanout override opt-in required')
    if fanout_enabled is False and (experimental_fanout is not True or (strict_class_targets is not False and global_width_policy is None) or profile not in {'tuned','tuned-free-angle'}):
        raise Rejected('unsupported: fanout override requires explicit non-strict tuned native baseline')
    if optimizer_enabled is not None and optimizer_enabled is not False:raise Rejected('optimizer override accepts only None or typed False')
    if type(experimental_optimizer)is not bool:raise Rejected('typed optimizer override opt-in required')
    if optimizer_enabled is False and (experimental_optimizer is not True or profile!='tuned-free-angle' or fanout_enabled is not False
            or experimental_fanout is not True or (strict_class_targets is not False and global_width_policy is None)):
        raise Rejected('unsupported: optimizer override requires explicit non-strict free-angle fanout-disabled baseline')
    tuned=profile in {'tuned','tuned-free-angle'}
    if type(strict_class_targets) is not bool: raise Rejected('invalid static netclass target policy')
    if isinstance(remaining_seconds,bool) or not isinstance(remaining_seconds,(int,float)) or not math.isfinite(remaining_seconds):
        raise Rejected('invalid remaining engine budget')
    available=math.floor(remaining_seconds-ENGINE_NATIVE_RESERVE_SECONDS-ENGINE_GRACE_RESERVE_SECONDS)
    if available<1: raise Rejected('insufficient remaining budget for engine grace and native finalization reserves')
    job_cap=min(100 if tuned else 60,available)
    optimizer_cap=None if profile=='completion-only' else min(90 if tuned else 30,job_cap)
    def span(seconds): return f'{seconds//3600:02}:{seconds//60%60:02}:{seconds%60:02}'
    scoring=engine_scoring_settings(scoring_variant)
    args=['--router.autorouter.max_passes='+('100' if tuned else '30'),
          '--router.job_timeout='+span(job_cap)]
    if strict_class_targets:
        # Pinned micro-neckdown can run during fanout even when automatic
        # neckdown is false. Exact class targets therefore exclude both paths.
        args+=['--router.automatic_neckdown=false','--router.fanout.enabled=false','--router.neck_width_um=0']
    if fanout_enabled is False and not strict_class_targets:args+=['--router.fanout.enabled=false']
    if profile=='completion-only':
        args+=['--router.optimizer.enabled=false']
    else:
        args+=['--router.optimizer.max_threads=1','--router.optimizer.max_passes='+('50' if tuned else '10'),
               '--router.optimizer.timeout='+span(optimizer_cap)]
        if tuned:
            # Actual pinned JAR probe verifies CLI fraction .001 -> internal .1%.
            args+=['--router.optimizer.improvement_threshold=0.001','--router.optimizer.enable_preflight_guards=false',
                   '--router.optimizer.max_consecutive_failures=100','--router.optimizer.max_consecutive_failures_pass1=100']
    if optimizer_enabled is False:args+=['--router.optimizer.enabled=false']
    args+=scoring['argv']
    result={'profile':profile,'argv':args,'scoring':scoring,'strict_class_targets':strict_class_targets,'remaining_outer_wall_seconds_at_assignment':remaining_seconds,
            'assigned_job_timeout_seconds':job_cap,'assigned_optimizer_timeout_seconds':optimizer_cap,
            'native_finalization_reserve_seconds':ENGINE_NATIVE_RESERVE_SECONDS,
            'engine_grace_reserve_seconds':ENGINE_GRACE_RESERVE_SECONDS,
            'internal_deadlines':'cooperative planning caps; external supervision and measured CPU acceptance cap remain authoritative'}
    if fanout_enabled is False:result['fanout_enabled']=False
    if optimizer_enabled is False:result['optimizer_enabled']=False
    if global_width_policy is not None:result['global_width_policy']=global_width_policy
    return result


def global_width_source_guard(source):
    """Narrow original positive global minimum with one literal Default target."""
    guard=minimum_width_guard(source,'both')
    project=json.loads(Path(source).with_suffix('.kicad_pro').read_text())
    settings=project.get('net_settings',{})
    classes=settings.get('classes') if type(settings)is dict else None
    if (guard is None or type(classes)is not list or len(classes)!=1 or type(classes[0])is not dict
            or classes[0].get('name')!='Default' or netclass_policy(source) is not None):
        raise Rejected('global width policy requires positive original minimum and one literal Default class')
    for name,kind in (('netclass_assignments',dict),('netclass_patterns',list)):
        value=settings.get(name)
        if value is not None and (type(value)is not kind or value):
            raise Rejected('global width policy does not support class assignments or patterns')
    target=classes[0].get('track_width')
    if type(target) not in (int,float) or not math.isfinite(target) or target<guard['min_track_width_mm']:
        raise Rejected('global width policy requires Default width at least the original minimum')
    return guard


def check_engine_global_width_policy(data):
    """Reciprocal versioned scope; never replace the original width guard."""
    from .floor_route import canonical
    marker='engine_global_width_policy' in data
    budget=data.get('engine_budget');budget_marker=type(budget)is dict and 'global_width_policy' in budget
    if not marker and not budget_marker:return None
    if (not marker or not budget_marker or type(data['engine_global_width_policy'])is not str
            or data['engine_global_width_policy']!=ENGINE_GLOBAL_WIDTH_POLICY
            or type(budget['global_width_policy'])is not str or budget['global_width_policy']!=ENGINE_GLOBAL_WIDTH_POLICY
            or budget.get('strict_class_targets') is not True or data.get('engine_profile')!='tuned-free-angle'
            or data.get('adapter')!='both' or data.get('scope')!='whole_board_unlocked_routing'
            or data.get('strategy') is not None or data.get('netclass_policy') is not None
            or data.get('engine_fanout_override') is not False or data.get('engine_optimizer_override') is not False
            or type(data.get('engine_planning_clearance_margin_nm'))is not int or data['engine_planning_clearance_margin_nm']!=20000):
        raise Rejected('global width policy marker/budget or scope missing or invalid')
    guard=global_width_source_guard(data['source'])
    if canonical(data.get('minimum_width_guard'))!=canonical(guard):
        raise Rejected('global width policy original minimum guard differs')
    argv=budget.get('argv')
    for prefix,expected in (('--router.automatic_neckdown','--router.automatic_neckdown=false'),
            ('--router.fanout.enabled','--router.fanout.enabled=false'),('--router.neck_width_um','--router.neck_width_um=0')):
        if type(argv)is not list or [a for a in argv if type(a)is str and a.startswith(prefix)]!=[expected]:
            raise Rejected('global width policy requires exact strict neckdown/fanout settings')
    return ENGINE_GLOBAL_WIDTH_POLICY


def check_engine_fanout_override(data,*,input_policy=None,native_toolchain=None):
    """Reciprocal opt-in; mandatory engine provenance prevents deletion fallback."""
    marker='engine_fanout_override' in data
    budget=data.get('engine_budget');budget_marker=type(budget)is dict and 'fanout_enabled' in budget
    if (marker and data['engine_fanout_override'] is not False or budget_marker and budget['fanout_enabled'] is not False
            or marker!=budget_marker):raise Rejected('fanout override marker/budget missing or invalid')
    if not marker:return None
    width_policy=check_engine_global_width_policy(data)
    if (budget.get('strict_class_targets') is not False and width_policy is None or type(budget.get('argv'))is not list
            or budget['argv'].count('--router.fanout.enabled=false')!=1):raise Rejected('fanout override requires exact non-strict disabled settings')
    if input_policy is not None and (input_policy!='native' or data.get('adapter')!='both'
            or data.get('scope')!='whole_board_unlocked_routing' or data.get('strategy') is not None
            or data.get('engine_profile') not in {'tuned','tuned-free-angle'} or native_toolchain is not None
            or data.get('baseline')!=engine_baseline(data['engine_profile'],'both')
            or 'routing_preferences' in data or 'layer_binding' in data):
        raise Rejected('unsupported: fanout override requires ordinary non-strict tuned native whole-board scope')
    return False


def check_engine_optimizer_override(data,*,input_policy=None,native_toolchain=None):
    """Explicit stock optimizer-disable baseline; retain all inactive optimizer caps."""
    marker='engine_optimizer_override' in data
    budget=data.get('engine_budget');budget_marker=type(budget)is dict and 'optimizer_enabled' in budget
    if (marker and data['engine_optimizer_override'] is not False or budget_marker and budget['optimizer_enabled'] is not False
            or marker!=budget_marker):raise Rejected('optimizer override marker/budget missing or invalid')
    if not marker:return None
    fanout=check_engine_fanout_override(data,input_policy=input_policy,native_toolchain=native_toolchain)
    if (fanout is not False or data.get('engine_profile')!='tuned-free-angle' or (budget.get('strict_class_targets') is not False and check_engine_global_width_policy(data) is None)
            or type(budget.get('argv'))is not list
            or [arg for arg in budget['argv'] if type(arg)is str and arg.startswith('--router.optimizer.enabled')]!=['--router.optimizer.enabled=false']):
        raise Rejected('optimizer override requires exact non-strict free-angle fanout-disabled settings')
    return False


def check_normal_engine_provenance(directory,data):
    """A current direct Native producer cannot omit its actual engine journal."""
    from .local_settings import policy_declaration
    from .placement_clearance import read_bytes
    directory=Path(directory);code=directory/'code/pipeline.py'
    if not code.exists() and not code.is_symlink():return  # Existing full code census rejects absent evidence later.
    raw=read_bytes(code,1024**2)
    if hashlib.sha256(raw).hexdigest()!=data.get('tools',{}).get('implementation_sha256',{}).get('autorouter/pipeline.py'):
        raise Rejected('normal engine producer code differs')
    required=policy_declaration(raw,name='NORMAL_ENGINE_PROVENANCE_POLICY',expected=NORMAL_ENGINE_PROVENANCE_POLICY)
    if required is not None and type(data.get('engine_budget'))is not dict:
        raise Rejected('normal engine producer requires retained engine budget/journal')


def check_engine_profile_record(data,directory):
    """Replay declared native settings against the retained actual engine argv."""
    from .floor_route import read_json
    directory=Path(directory)
    from .engine_angle import check as check_engine_angle
    check_engine_angle(directory,data)
    fanout=check_engine_fanout_override(data,input_policy='native')
    optimizer=check_engine_optimizer_override(data,input_policy='native')
    captured=directory/'routing-preferences.json'
    if 'routing_preferences' in data or captured.exists() or captured.is_symlink():
        return check_preferences_record(directory,data)
    width=check_minimum_width_record(data,directory)
    engine=data['engine_budget']
    expected=engine_profile_settings(data['engine_profile'],engine['remaining_outer_wall_seconds_at_assignment'],
        strict_class_targets=data.get('netclass_policy') is not None or data.get('scope')=='selected_nets' or width is not None,
        scoring_variant=data.get('scoring_variant'),experimental_free_angle=data['engine_profile']=='tuned-free-angle',fanout_enabled=fanout,experimental_fanout=fanout is False,optimizer_enabled=optimizer,experimental_optimizer=optimizer is False,global_width_policy=check_engine_global_width_policy(data))
    workers=[step for step in data['steps'] if step.get('name')=='engine']
    if (any(engine.get(key)!=value for key,value in expected.items())
            or engine.get('outer_task_wall_budget_seconds')!=data['budget_seconds']
            or engine.get('outer_task_cpu_budget_seconds')!=data['cpu_budget_seconds']
            or len(workers)!=1
            or workers[0].get('argv')!=engine_argv(directory,expected['argv'],profile=data['engine_profile'])
            or workers[0].get('cwd')!=str(directory)
            or workers[0].get('status')!='success' or workers[0].get('exit_code')!=0
            or workers[0].get('cleanup_complete') is not True
            or read_json(Path(directory)/'engine-process.json')!=workers[0]):
        raise Rejected('declared native engine profile differs from its execution journal')


def engine_baseline(profile,adapter):
    if profile=='completion-only': return 'completion_only_probe'
    if profile=='tuned': return 'B2_tuned'
    if profile=='tuned-free-angle': return 'B2_tuned_free_angle'
    if profile=='standard': return 'B0' if adapter=='none' else 'B1'
    raise Rejected('unknown engine profile')


def native_edge_context(board,*,known_named=False):
    """Use exact original files and the existing custom-rule support boundary."""
    from . import native_edge
    from .placement_clearance import read_bytes
    board=Path(board)
    context=native_edge.derive_context(read_bytes(board),read_bytes(board.with_suffix('.kicad_pro')),
        experimental_named_classes=known_named)
    rules=board.with_suffix('.kicad_dru')
    if rules.exists() or rules.is_symlink():
        context.update(applicable=False,reason='edge transport with custom-rule companion is unqualified')
    return context


def named_edge_scope(directory,data):
    """Initial admission covers ordinary whole-board/source-all routing only.

    Captured preferences and retained scope/layer process markers must agree.
    This is shared by the producer and the centrally qualified receipt reader.
    """
    if (data.get('scope')!='whole_board_unlocked_routing'
            or data.get('engine_profile') not in {'standard','tuned','completion-only'}
            or any(key in data for key in ('engine_fanout_override','engine_optimizer_override',
                'engine_angle_binding','experimental_route_policy'))
            or selected_scope_markers(directory,data) or layer_markers(directory,data)
            or native_minimum_markers(directory,data)):
        return False
    from . import preferences as pref
    for key in ('routing_preferences','pruning_preferences'):
        if key in data:
            effective=pref.validate(data[key]['effective'])
            if (effective['scope'],effective['guidance'],effective['layers'])!=('whole_board_unlocked_routing','native','source_all'):
                return False
    return True


def check_named_edge_policy(directory,data,*,input_policy,direct_import,native_toolchain=None):
    """Derive authority from pinned captured code and the checked import census.

    A marker alone, a stock run, or a parent strategy cannot enable named scope.
    Legacy captured producers keep the byte-exact Default-only interpretation.
    The public check_result has no caller-supplied admission override.
    """
    from .local_settings import policy_declaration
    from .placement_clearance import read_bytes
    producer=Path(directory)/'code/pipeline.py';raw=read_bytes(producer,1024**2)
    if type(direct_import) is not bool:raise Rejected('checked direct import decision required')
    if hashlib.sha256(raw).hexdigest()!=data.get('tools',{}).get('implementation_sha256',{}).get('autorouter/pipeline.py'):
        raise Rejected('named edge producer source pin differs')
    policy=policy_declaration(raw,name='NAMED_EDGE_ADMISSION_POLICY',expected=NAMED_EDGE_ADMISSION_POLICY)
    direct=(input_policy=='native' and direct_import and data.get('adapter') in {'graphics','planes','both'}
            and data.get('strategy') is None and native_toolchain is None)
    marker='native_edge_admission_policy'
    if policy is None or not direct:
        if marker in data:raise Rejected('named edge policy without qualified direct producer')
        return False
    if data.get(marker)!=policy:raise Rejected('missing or changed named edge admission policy')
    return named_edge_scope(directory,data)


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


def check_native_edge_transport(directory,data,*,_known_named_edge=False):
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
                and ('native_edge_admission_policy' in data
                    or 'autorouter/native_edge.py' in data.get('tools',{}).get('implementation_sha256',{}))):
            raise Rejected('new native adapter receipt lost its edge transport record')
        return
    if data.get('input_policy','native')!='native' or data.get('adapter')=='none':
        raise Rejected('edge correction requires corrected native adapter lineage')
    board=directory/'snapshot'/Path(data['source']).name
    if tree_hash(board.parent)!=data['source_hashes']:
        raise Rejected('edge correction original snapshot differs')
    context=native_edge_context(board,known_named=_known_named_edge)
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


def engine_argv(directory, settings, *, profile=None):
    """One exact invocation for native and floor guidance, also used by readback."""
    directory=Path(directory)
    input_name='engine-free-angle.dsn' if profile=='tuned-free-angle' else 'task.dsn'
    return ['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(c.JAVA),
        '-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',str(c.JAR),
        '--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da',
        '--user_data_path='+str(directory/'engine-config'),'--logging.file.enabled=false',*settings,
        '-de',str(directory/input_name),'-do',str(directory/'routes.ses')]


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


def route(source, output, seconds=120, keep_existing=False, adapter='none', engine_profile='standard', *, scoring_variant=None, guidance_policy='native', settings_path=None, preference_overrides=None, _preferences=None, native_toolchain=None, experimental_schematic_parity=False, _fanout_enabled=None, _optimizer_enabled=None, _engine_clearance_margin_nm=None, _engine_global_width_policy=None):
    """Keep cancellation active between workers and through final publication."""
    def interrupted(*_):raise KeyboardInterrupt
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        for sig in previous:signal.signal(sig,interrupted)
        return _route(source,output,seconds,keep_existing,adapter,engine_profile,
            scoring_variant=scoring_variant,guidance_policy=guidance_policy,settings_path=settings_path,
            preference_overrides=preference_overrides,_preferences=_preferences,native_toolchain=native_toolchain,
            experimental_schematic_parity=experimental_schematic_parity,_fanout_enabled=_fanout_enabled,
            _optimizer_enabled=_optimizer_enabled,_engine_clearance_margin_nm=_engine_clearance_margin_nm,
            _engine_global_width_policy=_engine_global_width_policy)
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)


def _route(source, output, seconds=120, keep_existing=False, adapter='none', engine_profile='standard', *, scoring_variant=None, guidance_policy='native', settings_path=None, preference_overrides=None, _preferences=None, native_toolchain=None, experimental_schematic_parity=False, _fanout_enabled=None, _optimizer_enabled=None, _engine_clearance_margin_nm=None, _engine_global_width_policy=None):
    entry_started,entry_parent=time.monotonic(),time.process_time()
    from .floor_route import child_cpu
    operation_children=child_cpu()
    if _engine_global_width_policy is not None and (type(_engine_global_width_policy)is not str
            or _engine_global_width_policy!=ENGINE_GLOBAL_WIDTH_POLICY or type(_engine_clearance_margin_nm)is not int
            or _engine_clearance_margin_nm!=20000 or engine_profile!='tuned-free-angle'
            or _optimizer_enabled is not False or _fanout_enabled is not False):
        raise Rejected('unsupported: global width policy requires explicit free-angle clearance20 optimizerFalse/fanoutFalse')
    if _engine_clearance_margin_nm is not None:
        if type(_engine_clearance_margin_nm)is not int or _engine_clearance_margin_nm!=20000:raise Rejected('planning clearance margin accepts only None or literal integer20000nm')
        if engine_profile!='tuned-free-angle' or _optimizer_enabled is not False or _fanout_enabled is not False:
            raise Rejected('unsupported: planning clearance requires explicit free-angle optimizerFalse/fanoutFalse route')
    if _optimizer_enabled is not None and _optimizer_enabled is not False:raise Rejected('optimizer override accepts only None or typed False')
    if _optimizer_enabled is False and (engine_profile!='tuned-free-angle' or _fanout_enabled is not False):
        raise Rejected('unsupported: optimizer override requires explicit free-angle fanout-disabled route')
    if _fanout_enabled is not None and _fanout_enabled is not False:raise Rejected('fanout override accepts only None or typed False')
    if _fanout_enabled is False and (keep_existing is not False or adapter!='both' or guidance_policy!='native'
            or settings_path is not None or preference_overrides is not None or _preferences is not None
            or native_toolchain is not None or experimental_schematic_parity is not False or engine_profile not in {'tuned','tuned-free-angle'}):
        raise Rejected('unsupported: fanout override requires ordinary non-strict tuned native whole-board route')
    experimental_record=experimental_route_record(native_toolchain,experimental_schematic_parity)
    if native_toolchain is not None and (settings_path is not None or preference_overrides is not None
            or _preferences is not None or keep_existing is not False or adapter!='none'
            or engine_profile!='standard' or scoring_variant is not None or guidance_policy!='native'):
        raise Rejected('unsupported: explicit experimental route supports only ordinary standard whole-board transport')
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
    if engine_profile=='tuned-free-angle' and (keep_existing is not False or adapter!='both'
            or guidance_policy!='native' or _preferences is not None or native_toolchain is not None):
        raise Rejected('unsupported: free-angle baseline requires ordinary native corrected whole-board route')
    if native_toolchain is None:
        effective=_preferences['effective'] if _preferences else {}
        require_native_scope(scope=effective.get('scope','partial_completion' if keep_existing else 'whole_board_unlocked_routing'),
            guidance=guidance_policy,layers=effective.get('layers','source_all'),
            profile=engine_profile,adapter=adapter,scoring=scoring_variant)
    if guidance_policy not in {'native','board-floors-v1','placement-clearance-v1'}: raise Rejected('unknown guidance policy')
    if guidance_policy in {'board-floors-v1','placement-clearance-v1'}:
        from .floor_route import route as floor_route
        return floor_route(source,output,seconds,keep_existing,adapter,engine_profile,scoring_variant,guidance_policy=guidance_policy,preferences=_preferences)
    if engine_profile not in {'standard','tuned','completion-only','tuned-free-angle'}: raise Rejected('unknown engine profile')
    engine_scoring_settings(scoring_variant)
    operation_started=_preferences['started'] if _preferences else entry_started if native_toolchain is not None or engine_profile=='tuned-free-angle' or _fanout_enabled is False else time.monotonic()
    operation_started_utc=_preferences['started_utc'] if _preferences else datetime.datetime.now(datetime.timezone.utc).isoformat()
    operation_cpu=_preferences['parent_cpu'] if _preferences else entry_parent if native_toolchain is not None or engine_profile=='tuned-free-angle' or _fanout_enabled is False else time.process_time()
    from .local_settings import canonical
    canonical(Path(source).absolute());canonical(Path(output).absolute())
    source=Path(source).resolve(strict=True); output=Path(output).resolve()
    if source.parent==output or source.parent in output.parents: raise Rejected('output must be outside source project')
    if _fanout_enabled is False:
        preflight(source,task_scope=('whole_board_unlocked_routing','native','source_all'))
        if _engine_global_width_policy is not None:global_width_source_guard(source)
        elif netclass_policy(source) is not None or minimum_width_guard(source,adapter) is not None:
            raise Rejected('unsupported: fanout override requires derived non-strict class/width targets')
    if not math.isfinite(seconds) or seconds<5 or seconds>900: raise Rejected('budget must be 5–900 seconds')
    if sha(c.JAR)!=c.JAR_SHA256: raise Rejected('engine hash mismatch')
    check_storage(active_root=output)
    job=Job(output,seconds,protect_local_settings=True,**({'native_toolchain':native_toolchain,
        'experimental_schematic_parity':experimental_schematic_parity} if native_toolchain is not None else {}))
    job.started=operation_started; job.deadline=operation_started+seconds; job.cpu_started=operation_cpu
    code=output/'code'; code.mkdir()
    for path in (c.ROOT/'autorouter').glob('*.py'): shutil.copy2(path,code/path.name)
    report={'schema':1,'status':'validator_error','accepted':False,'physical_electrical_validation':False,'schematic_parity':'not checked','source':str(source),
            'started_utc':operation_started_utc,'budget_seconds':seconds,'cpu_budget_seconds':seconds,'cpu_budget_enforcement':'postcompletion acceptance cap; no total-CPU preemption','baseline':engine_baseline(engine_profile,adapter),'adapter':adapter,'engine_profile':engine_profile,'scoring_variant':scoring_variant,'scope':'partial_completion' if keep_existing else 'whole_board_unlocked_routing',
            'tools':tool_manifest(**({'native_toolchain':native_toolchain} if native_toolchain is not None else {})),**experimental_record}
    if native_toolchain is None and adapter!='none':
        report['native_edge_admission_policy']=NAMED_EDGE_ADMISSION_POLICY
    if _fanout_enabled is False:report['engine_fanout_override']=False
    if _optimizer_enabled is False:report['engine_optimizer_override']=False
    if _engine_clearance_margin_nm is not None:report['engine_planning_clearance_margin_nm']=_engine_clearance_margin_nm
    if _engine_global_width_policy is not None:report['engine_global_width_policy']=_engine_global_width_policy
    class_requirement=None
    try:
        capture_preferences(report,output,_preferences)
        before=tree_hash(source.parent); report['source_hashes']=before
        selected=_preferences['effective'].get('nets') if _preferences and _preferences['effective']['scope']=='selected_nets' else None
        scope=_preferences['effective']['scope'] if _preferences else report['scope']
        layers=_preferences['effective']['layers'] if _preferences else 'source_all'
        class_context=('native-route-flat-classes-v1' if native_toolchain is None
            and engine_profile in {'standard','tuned','completion-only'} and _fanout_enabled is None
            and _optimizer_enabled is None and scope in {'whole_board_unlocked_routing','partial_completion'}
            and guidance_policy=='native' and layers=='source_all' else None)
        original=preflight(source,task_scope=(scope,guidance_policy,layers),class_context=class_context)
        class_requirement=check_schematic_class_support(source,class_context=class_context)
        if class_requirement is not None and _preferences is None:
            job.started=entry_started;job.deadline=entry_started+seconds;job.cpu_started=entry_parent
        from .netclass import PARENT_POLICY
        source_policy=netclass_policy(source)
        if selected is not None and source_policy is not None and source_policy['mode']==PARENT_POLICY:
            raise Rejected('unsupported: selected-net composite class transport not qualified')
        parity=source.with_suffix('.kicad_sch').name in before
        if native_toolchain is not None and not parity:raise Rejected('unsupported: explicit experimental route requires complete native schematic')
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
        task=routing_task(original,report['scope'],selected)
        protected=copy.deepcopy(routes(task))
        sx.write(candidate,task)
        report['task_sha256']=sha(candidate)
        report['source_drc']=job.drc('source-drc',snapshot)
        policy=netclass_policy(candidate)
        from .netclass import PARENT_POLICY
        parent_classes=policy is not None and policy['mode']==PARENT_POLICY
        if selected is not None and parent_classes:
            raise Rejected('unsupported: selected-net composite class transport not qualified')
        if policy is None and native_toolchain is None:
            job.native('export','export',candidate,output/'task.dsn','--task-copper-fixed')
            shutil.copy2(output/'task.dsn',output/'native.dsn')
        else:
            from .netclass import audit_dsn
            mapping=output/'export-netclasses.json'
            job.native('export','export',candidate,output/'task.dsn',mapping,
                *(['--task-copper-fixed'] if native_toolchain is None else []))
            native_classes=json.loads(mapping.read_text())
            # The task contains only protected routes, and its original rules.
            audit_candidate_netclasses(candidate,protected,native_classes,native_toolchain=native_toolchain)
            shutil.copy2(output/'task.dsn',output/'native.dsn')
            report['netclass_policy']=policy
            report['netclass_export_audit']=audit_dsn(output/'native.dsn',native_classes,json.loads(candidate.with_suffix('.kicad_pro').read_text()),parent_policy=parent_classes,native_toolchain=native_toolchain)
        if class_requirement is not None:
            from . import schematic_class_evidence as classes
            report['schematic_class_task']=classes.collect(job,'task',candidate,output/'export-netclasses.json')
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
            corrected,edge_record=native_edge.correct((output/'task.dsn').read_bytes(),native_edge_context(snapshot,
                known_named=native_toolchain is None and named_edge_scope(output,report)))
            (output/'task.dsn').write_bytes(corrected)
            save_json(output/'native-edge-correction.json',edge_record)
            report['native_edge_correction']=edge_record
        if policy is not None or native_toolchain is not None:
            report['netclass_task_audit']=audit_dsn(output/'task.dsn',native_classes,json.loads(candidate.with_suffix('.kicad_pro').read_text()),parent_policy=parent_classes,native_toolchain=native_toolchain)
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
        report['engine_budget']=engine_profile_settings(engine_profile,job.deadline-time.monotonic(),strict_class_targets=policy is not None or selected is not None or width_guard is not None,scoring_variant=scoring_variant,experimental_free_angle=engine_profile=='tuned-free-angle',fanout_enabled=_fanout_enabled,experimental_fanout=_fanout_enabled is False,optimizer_enabled=_optimizer_enabled,experimental_optimizer=_optimizer_enabled is False,global_width_policy=_engine_global_width_policy)
        report['engine_budget']['outer_task_wall_budget_seconds']=seconds
        report['engine_budget']['outer_task_cpu_budget_seconds']=seconds
        engine_settings=report['engine_budget']['argv']
        if layers is not None:engine_settings.append(layers['binding']['engine_argument'])
        if selection_argument is not None:engine_settings.append(selection_argument)
        if engine_profile=='tuned-free-angle':
            from .engine_angle import prepare as prepare_engine_angle
            if _engine_global_width_policy is not None:
                from .engine_angle import check_global_width_targets
                check_global_width_targets(output,source)
            report['engine_angle_binding']=prepare_engine_angle(output,**({'clearance_margin_nm':_engine_clearance_margin_nm} if _engine_clearance_margin_nm is not None else {}))
        preferences_fresh(output,_preferences)
        job.step('engine',engine_argv(output,engine_settings,profile=engine_profile))
        if engine_profile in {'tuned','tuned-free-angle'}:
            report['optimizer_threshold_audit']=optimizer_threshold_audit(output/'engine.log',0.1)
        if not (output/'routes.ses').is_file(): raise Rejected('engine emitted no SES')
        imported=output/'imported.kicad_pcb'
        job.native('import','import',candidate,imported,output/'routes.ses',
            *(['--task-copper-fixed'] if native_toolchain is None else []))
        reconciliation={}
        import_policy=(normal_selected_import_policy(original,selected) if selected is not None else
            normal_strict_import_policy(original,protected) if native_toolchain is None else 'exact_non_uuid_lock_position_v2')
        sx.write(candidate,transplant_routes(task,sx.read(imported),protected=protected,audit=reconciliation,
            policy=import_policy,
            **({'selected_names':selected} if import_policy==SELECTED_PROPOSAL_IMPORT_POLICY else {})))
        report['protected_route_import']={'imported_sha256':sha(imported),**reconciliation}
        extra={'selected_names':selected,'schematic_parity':parity} if selected is not None else {}
        final_hash, native = validate_candidate(job, original, candidate, before, protected,layer_contract=layers,class_context=class_context,**extra)
        if class_requirement is not None:
            report['schematic_class_final']=job.schematic_class_final
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
        if _preferences is None and class_requirement is None:raise
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
    report['resource_limitations']='One sequential worker; Java 2GiB heap; group RSS4GiB and workdir512MiB polling guards may overshoot;18GiB total cache checked before task. Peak direct-child RSS and polled group RSS are different metrics. CPU descendants only if accounted for by child wait; monitoring CPU included.'
    if report['wall_seconds']>seconds:
        report['accepted']=False; report['status']='timeout'
    elif report['total_cpu_seconds']>seconds:
        report['accepted']=False; report['status']='cpu_budget_exceeded'
    report['resource_accounting_point']='Summary sampled before final receipt write; wall and measured CPU acceptance caps rechecked after that write. No hard total-CPU preemption.'
    from .floor_route import publish,child_cpu,evidence_inventory
    completed=evidence_inventory(output)
    def remaining():
        return min(job.deadline-time.monotonic(),seconds-(time.process_time()-job.cpu_started+child_cpu()-(_preferences['child_cpu'] if _preferences else operation_children)))
    def account():
        report.update(wall_seconds=time.monotonic()-job.started,parent_cpu_seconds=time.process_time()-job.cpu_started)
        report['control_child_cpu_seconds']=max(0,child_cpu()-(_preferences['child_cpu'] if _preferences else operation_children)-report['child_cpu_seconds']-report['monitor_cpu_seconds'])
        report['total_cpu_seconds']=sum(report[key] for key in ('parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','control_child_cpu_seconds'))
        report['resource_accounting_point']='Stored totals precede guarded publication; final wall/full CPU acceptance caps include all preference intake, readback and freshness checks.'
        if report['wall_seconds']>seconds or report['total_cpu_seconds']>seconds:
            report.update(accepted=False,status='budget_exceeded')
        if not report['accepted']:report['whole_project_drc_clean']=False
    def stable():
        if report['accepted']:
            if tool_manifest(**({'native_toolchain':native_toolchain} if native_toolchain is not None else {}))!=report['tools']:raise Rejected('runtime changed during preference publication')
            if evidence_inventory(output)!=completed:raise Rejected('completed preference routing evidence changed')
            if tree_hash(source.parent)!=before or tree_hash(output/'snapshot')!=before:
                raise Rejected('source changed during preference publication')
            if native_toolchain is not None:check_experimental_local_settings(output,report,native_toolchain)
        preferences_fresh(output,_preferences)
        if report['accepted'] and (_fanout_enabled is False or engine_profile=='tuned-free-angle'):
            # Last: byte/tool/source/preferences reads cannot witness PRL flags.
            from .local_settings import check_normal_policy
            check_normal_policy(output,report)
        if report['accepted'] and class_requirement is not None:
            check_route_class_evidence(output,report,original,candidate,class_context=class_context)
    return publish(output,report,stable,account,remaining,
        result_checker=(lambda file:check_result(file,native_toolchain=native_toolchain,experimental_schematic_parity=experimental_schematic_parity)) if native_toolchain is not None else None)


_readback_session=ContextVar('autorouter_validated_readback_session',default=None)


@contextmanager
def validation_readback_session():
    """Reuse bounded routing consistency checks only within this invocation.

    Every reuse hashes the complete evidence/source trees and actual tool/code
    identity twice. Native execution and candidate acceptance are never cached.
    Hot replacement of checker functions invalidates reuse. No disk cache exists.
    """
    from . import (adapter,board_floor,engine_angle,floor_context,floor_route,handoff,layer_policy,legacy_zone,local_settings,padless_alias,padless_alias_native,
                   native_edge,netclass,placement_clearance,placement_strategy,routing_scope,thermal,thermal_geometry,
                   placement_transform,pour_rule_area,preferences,runner,strategy,task_copper,
                   schematic_fields,schematic_field_evidence,schematic_classes,schematic_class_evidence)
    import sys
    modules=(sys.modules[__name__],c,sx,adapter,board_floor,engine_angle,floor_context,
             floor_route,handoff,layer_policy,legacy_zone,local_settings,padless_alias,padless_alias_native,native_edge,netclass,placement_clearance,
             placement_strategy,placement_transform,pour_rule_area,preferences,runner,strategy,
             routing_scope,thermal,thermal_geometry,schematic_fields,schematic_field_evidence,schematic_classes,schematic_class_evidence,task_copper)
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
        raise Rejected('noncanonical routing source in readback session')
    limit,files=(ps.LIMIT,ps.MAX_FILES) if data['schema']==5 else (100*1024*1024,2000)
    # Tool discovery can yield to another writer. Sample all retained/source
    # bytes and PRL metadata only after this callback and current live identity.
    tools=tool_manifest()
    runtime=(hashlib.sha256(pc.read_bytes(c.ROOT/'toolchain.lock.json')).hexdigest(),
             tools,str(c.ROOT),str(c.CLI),str(c.PYTHON),str(c.PCBNEW),str(c.JAVA),str(c.JAR))
    live=_readback_live_identity(state['modules'])
    evidence=pc.inventory(path.parent,max_bytes=limit,max_files=files,
                          max_entries=files*2,with_directories=True)
    original=pc.inventory(source.parent,with_directories=True)
    # File flags/link counts affect the PRL contract but are outside byte hashes.
    import stat
    local_metadata=[]
    for name in evidence[0]:
        if Path(name).suffix=='.kicad_prl':
            info=(path.parent/name).lstat()
            local_metadata.append((name,getattr(info,'st_flags',0),info.st_nlink,stat.S_IFMT(info.st_mode)))
    return (evidence,original,tuple(sorted(local_metadata)),runtime,live)


def check_result(path, *, native_toolchain=None, experimental_schematic_parity=False):
    """Check evidence; optional scoped reuse never substitutes fresh native DRC."""
    try:c.current_native_selection()
    except (ValueError,OSError) as exc:raise Rejected('selected native toolchain changed: '+str(exc)) from exc
    experimental_route_record(native_toolchain,experimental_schematic_parity)
    if native_toolchain is not None:
        return _check_result_uncached(path,native_toolchain=native_toolchain,experimental_schematic_parity=experimental_schematic_parity)
    state=_readback_session.get()
    if state is None:return _check_result_uncached(path)
    try:
        from .floor_route import read_json,receipt_policy
        from .placement_clearance import read_bytes
        target=Path(path).absolute()
        raw=read_bytes(target)  # Reject symlink aliases before resolving them.
        data=read_json(target)
        if (target.name!='result.json' or target!=target.resolve(strict=True)
                or type(data.get('schema')) is not int or data['schema'] not in (1,3,4,5)
                or data.get('accepted') is not True or data.get('status')!='routing_accepted'
                or 'diagnostic_schema' in data or 'production_qualified' in data
                or any(key in data for key in ('experimental_route_policy','experimental_native_toolchain','production_admitted'))):
            return _check_result_uncached(path)
        if data['schema']==1:
            try:native=receipt_policy(data,target.parent)=='native'
            except Rejected:native=False  # The full checker retains its policy refusal.
            if (not native or data.get('strategy') not in (None,'native_validated_zone_net_pruning','native_validated_thermal_bridge')):
                return _check_result_uncached(path)
        elif data.get('input_policy') not in {'placement-clearance-v1','placement-search-v1','placement-pruning-v1'}:
            return _check_result_uncached(path)
        before=_readback_witness(target,data,state)
        if before[0][0].get(target.name)!=hashlib.sha256(raw).hexdigest():
            raise Rejected('routing receipt changed before cached readback')
        entry=state['entries'].get(target)
        if entry is not None and entry[0]==before:
            if _readback_witness(target,data,state)!=before:
                raise Rejected('routing evidence changed during cached readback')
            return copy.deepcopy(entry[1])
        state['entries'].pop(target,None)
        result=_check_result_uncached(target)
        if _readback_witness(target,data,state)!=before:
            raise Rejected('routing evidence changed during full readback')
        if len(state['entries'])>=8:state['entries'].pop(next(iter(state['entries'])))
        state['entries'][target]=(before,copy.deepcopy(result))
        return result
    except BaseException:
        state['entries'].clear()
        raise


def sequential_cpu_components(parent_cpu, waited_cpu, steps):
    """Conservatively reconcile sequential wait4 totals with per-step samples.

    Separate floating-point additions can differ by a few ulps. Only a deficit
    within the existing receipt algebra tolerance may round up to zero; missing
    CPU, negative measurements and nonfinite values still refuse publication.
    """
    def number(value):
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:
            raise Rejected('invalid resource accounting')
        return value
    def total(values):
        try:return number(math.fsum(values))
        except OverflowError as exc:raise Rejected('invalid resource accounting') from exc
    parent,waited=number(parent_cpu),number(waited_cpu)
    child=total(number(step['cpu_seconds']) for step in steps)
    monitor=total(number(step['monitor_cpu_seconds']) for step in steps)
    residual=waited-child
    if residual < -1e-6:
        raise Rejected('waited child CPU is below recorded step CPU')
    control=max(0.0,residual)
    return dict(parent_cpu_seconds=parent,child_cpu_seconds=child,
        control_child_cpu_seconds=control,monitor_cpu_seconds=monitor,
        total_cpu_seconds=total((parent,child,monitor,control)))


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


def check_rejected_routing_attempt(path):
    """Diagnose one completed ordinary tuned failure; never authorize a candidate.

    This bypasses the positive readback cache. All retained Native, process,
    source, rule and budget checks still run; no fresh Native execution occurs.
    Cancellation, stale inputs and invalid/incomplete evidence raise.
    """
    from .placement_clearance import read_bytes
    target=Path(path).absolute()
    read_bytes(target)  # Refuse symlink aliases before the common body resolves.
    if target.name!='result.json' or target!=target.resolve(strict=True):
        raise Rejected('completed-negative reader requires canonical result.json')
    return _check_result_uncached(target,_rejected_attempt=True)


def _check_result_uncached(path, *, native_toolchain=None, experimental_schematic_parity=False,
                           _rejected_attempt=False):
    """Check local evidence consistency; this is not authentication or fresh DRC.

    All receipts are mutable local JSON. A party rewriting the complete evidence
    set can fabricate a consistent history; safe application needs fresh native
    validation too. This function never applies a live-editor change.
    """
    try:c.current_native_selection()
    except (ValueError,OSError) as exc:raise Rejected('selected native toolchain changed: '+str(exc)) from exc
    if type(_rejected_attempt) is not bool or (_rejected_attempt and native_toolchain is not None):
        raise Rejected('completed-negative mode requires the ordinary production toolchain')
    path=Path(path).resolve(strict=True)
    from .floor_route import receipt_policy, read_json
    from .placement_clearance import read_bytes as bounded_bytes
    receipt_digest=hashlib.sha256(bounded_bytes(path)).hexdigest()
    # Parse once strictly before policy dispatch; duplicate selectors cannot hide schema3.
    data=read_json(path)
    check_experimental_route(data,native_toolchain,experimental_schematic_parity)
    if native_toolchain is None and c.NATIVE_VERSION!='10.0.0':
        if data.get('schema')!=1 or data.get('strategy') not in (None,'native_validated_thermal_bridge') or data.get('input_policy','native')!='native':
            raise Rejected('unsupported: selected Native version has no qualified advanced receipt lineage')
        purpose='route'
        if data.get('strategy')=='native_validated_thermal_bridge':
            from .thermal import check_parent_scope
            if not check_parent_scope(path.parent,data):raise Rejected('selected Native thermal parent requires its exact source policy')
            purpose='thermal-recovery'
        effective=data.get('routing_preferences',{}).get('effective',{})
        require_native_scope(purpose=purpose,scope=data.get('scope'),guidance=effective.get('guidance','native'),
            layers=effective.get('layers','source_all'),profile=data.get('engine_profile'),
            adapter=data.get('adapter'),scoring=data.get('scoring_variant'))
    from .engine_angle import check as check_engine_angle
    angle_contract=check_engine_angle(path.parent,data)  # Independent of optional legacy engine_budget dispatch.
    check_engine_global_width_policy(data)
    fanout_contract=check_engine_fanout_override(data)
    optimizer_contract=check_engine_optimizer_override(data)
    explicit_material=tree_hash(path.parent) if native_toolchain is not None else None
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
    if angle_contract is not None:
        from .engine_angle import check_scope as check_engine_angle_scope
        check_engine_angle_scope(data,input_policy,native_toolchain)
    if fanout_contract is False:check_engine_fanout_override(data,input_policy=input_policy,native_toolchain=native_toolchain)
    if optimizer_contract is False:check_engine_optimizer_override(data,input_policy=input_policy,native_toolchain=native_toolchain)
    if _rejected_attempt:
        # Closed diagnostic scope, independent of the positive acceptance API.
        # Derive native policy above; ordinary receipts omit input_policy.
        if (type(data.get('schema')) is not int or data['schema']!=1
                or data.get('accepted') is not False or data.get('status')!='drc_rejected'
                or data.get('baseline')!='B2_tuned' or data.get('adapter')!='both'
                or data.get('engine_profile')!='tuned' or input_policy!='native'
                or data.get('scope')!='whole_board_unlocked_routing'
                or any(key in data for key in ('strategy','input_policy','guidance_policy',
                    'diagnostic_schema','production_qualified','engine_angle_binding',
                    'engine_planning_clearance_margin_nm','engine_global_width_policy',
                    'engine_fanout_override','engine_optimizer_override',
                    'incumbent_scoring_contract','incumbent_scoring_variant','incumbent_receipt_sha256',
                    'pruning_preferences','pruning_preferences_policy'))
                or angle_contract is not None or fanout_contract is not None or optimizer_contract is not None
                or selected_scope_markers(path.parent,data) or layer_markers(path.parent,data)
                or any(marker.exists() or marker.is_symlink() for marker in (scoring_marker,pruning_marker))):
            raise Rejected('unsupported completed-negative routing contract')
    if input_policy=='native' and data.get('strategy') is None:
        check_normal_engine_provenance(path.parent,data)
    # Captured-choice runs use the shared bounded reader for a complete witness,
    # including original rule copies and native evidence, before interpreting it.
    # Recheck after every late settings/process read; board-only layer checks
    # cannot detect a concurrently changed project file or native report.
    preferences_guarded=(_rejected_attempt or 'native_edge_admission_policy' in data
        or 'schematic_class_task' in data or 'schematic_class_final' in data
        or 'engine_optimizer_override' in data or 'engine_fanout_override' in data or data.get('engine_profile')=='tuned-free-angle' or 'engine_angle_binding' in data
        or (path.parent/'engine-angle.json').exists() or (path.parent/'engine-free-angle.dsn').exists()
        or 'routing_preferences' in data or (path.parent/'routing-preferences.json').exists()
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
    if not _rejected_attempt and (data.get('schema') not in (1,2,3,4,5) or data.get('accepted') is not True or data.get('status')!='routing_accepted'):
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
    class_context=class_context_for_record(data,path.parent,input_policy=input_policy,native_toolchain=native_toolchain)
    original=preflight(source,task_scope=task_scope_for_record(data,path.parent,input_policy=input_policy),class_context=class_context)
    current=sx.read(candidate)
    check_hole_machining_support(current)
    if immutable(current)!=immutable(original): raise Rejected('immutable geometry changed')
    check_legacy_zone_evidence(path.parent,original,candidate,
        implementation=data.get('tools',{}).get('implementation_sha256',{}))
    protected=protected_for_record(data,original)
    if any(route not in routes(current) for route in protected): raise Rejected('protected route changed')
    steps=data.get('steps')
    if not isinstance(steps,list) or not steps or any(not isinstance(step,dict) for step in steps):
        raise Rejected('missing process history')
    if any(step.get('status')=='cancelled' or step.get('cleanup_complete') is not True for step in steps):
        raise Rejected('cancelled or incomplete process cleanup in receipt')
    from .local_settings import check_normal_policy
    imports=check_normal_policy(path.parent,data,native_toolchain=native_toolchain)
    import_contract=normal_import_contract(path.parent,data,imports,input_policy=input_policy,original=original,native_toolchain=native_toolchain)
    check_protected_import(path.parent,data,original,candidate,protected,**(import_contract or {}))
    known_named_edge=check_named_edge_policy(path.parent,data,input_policy=input_policy,
        direct_import=import_contract is not None,native_toolchain=native_toolchain)

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
    if netclass_policy(candidate) is not None or native_toolchain is not None:
        from .netclass import audit_dsn, audit_native, PARENT_POLICY
        parent_classes=netclass_policy(candidate) is not None and netclass_policy(candidate)['mode']==PARENT_POLICY
        if data['scope']=='selected_nets' and parent_classes:
            raise Rejected('selected-net composite class transport not qualified')
        native_classes=evidence('final-netclasses.json')
        audited=audit_candidate_netclasses(candidate,protected,native_classes,native_toolchain=native_toolchain)
        audited['native_map_file_sha256']=sha(path.parent/'final-netclasses.json')
        if evidence('final-netclass-audit.json')!=audited: raise Rejected('retained native netclass audit differs from candidate')
        process=evidence('final-netclasses-process.json')
        expected=[*native_prefix(native_toolchain),'netclasses',str(candidate),str(path.parent/'final-netclasses.json')]
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
            task=routing_task(original,data['scope'],selected_scope_names(data))
            task_hash=hashlib.sha256((sx.dump(task)+'\n').encode()).hexdigest()
            exported=evidence('export-netclasses.json')
            project=json.loads(candidate.with_suffix('.kicad_pro').read_text())
            if (data.get('task_sha256')!=task_hash or exported.get('board_sha256')!=task_hash
                    or exported.get('project_sha256')!=sha(candidate.with_suffix('.kicad_pro'))
                    or exported.get('source')!=str(candidate) or exported.get('board_saved') is not False):
                raise Rejected('export netclass map differs from original routing task')
            if 'copper_layers' in exported or sum(isinstance(x,list) and len(x)>2 and re.fullmatch(r'(?:F|B|In[0-9]+)\.Cu',sx.unquote(x[1])) is not None for x in sx.one(task,'layers',[]))==4:
                from .netclass import four_copper_source_layers,four_copper_native_layers
                if four_copper_source_layers(task)!=four_copper_native_layers(exported):raise Rejected('export source/native copper layers differ')
            audit_native(exported,project,parent_policy=parent_classes,native_toolchain=native_toolchain)
            if (data.get('netclass_policy')!=netclass_policy(candidate)
                    or data.get('netclass_export_audit')!=audit_dsn(path.parent/'native.dsn',exported,project,parent_policy=parent_classes,native_toolchain=native_toolchain)
                    or data.get('netclass_task_audit')!=audit_dsn(path.parent/('routing-scope-input.dsn' if data['scope']=='selected_nets' else 'task.dsn'),exported,project,parent_policy=parent_classes,native_toolchain=native_toolchain)):
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
    native=parse_report(path.parent/'final-drc.json',candidate.name,native_toolchain=native_toolchain)
    reasons=native_rejection_reasons(native)
    if _rejected_attempt:
        if (native['exclusions'] or any(reason.startswith(('malformed ','missing ','unknown ','disabled '))
                for reason in reasons)):
            raise Rejected('unsupported or malformed Native evidence is not an ordinary completed rejection')
        if not reasons or data.get('native_rejection_reasons')!=reasons:
            raise Rejected('completed-negative reasons differ from raw Native findings')
    elif reasons: raise Rejected('native findings reject candidate: '+'; '.join(reasons))
    if ((any(step.get('phase')=='incumbent' and step.get('name')=='engine' for step in data.get('steps',[]))
            or (path.parent/'incumbent/result.json').exists())
            and data.get('strategy') not in {'native_validated_zone_net_pruning','native_validated_thermal_bridge','placement-native-pruning-v1'}):
        raise Rejected('incumbent workers require their recognized strategy')
    if data.get('native')!=native or data.get('invariants_unchanged') is not True: raise Rejected('receipt native summary differs from raw evidence')
    if data.get('whole_project_drc_clean') is not (not reasons and native['warnings']==0): raise Rejected('receipt cleanliness claim differs from native evidence')
    metrics=evidence('metrics.json')
    if data.get('metrics')!=metrics or metrics.get('version')!=experimental_native_version(native_toolchain): raise Rejected('receipt metrics differ from retained native metrics')

    process=evidence('final-drc-process.json')
    expected_argv=[str(c.CLI if native_toolchain is None else native_toolchain.cli),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(path.parent/'final-drc.json'),str(native_input)]
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
        sandboxed=input_policy in {'board-floors-v1','placement-clearance-v1','placement-search-v1',ps.POLICY},native_toolchain=native_toolchain)
    check_route_class_evidence(path.parent,data,original,candidate,class_context=class_context)
    if any(step.get('status')=='cancelled' or step.get('cleanup_complete') is not True for step in steps): raise Rejected('cancelled or incomplete process cleanup in receipt')
    check_pour_evidence(path.parent,data,original,candidate,_known_named_edge=known_named_edge)
    check_native_edge_transport(path.parent,data,_known_named_edge=known_named_edge)
    check_preferences_record(path.parent,data)

    if 'engine_budget' in data:
        check_minimum_width_record(data,path.parent)
        if input_policy=='native':check_engine_profile_record(data,path.parent)

    check_resource_accounting(data)

    tools=data.get('tools',{})
    implementation=tools.get('implementation_sha256')
    if tools.get('kicad')!=experimental_native_version(native_toolchain) or not isinstance(implementation,dict) or not implementation: raise Rejected('missing pinned implementation provenance')
    if not {'autorouter/pipeline.py','autorouter/native.py','autorouter/runner.py','autorouter/sexpr.py'}<=set(implementation): raise Rejected('incomplete implementation provenance')
    actual_code=tree_hash(path.parent/'code')
    expected_code={}
    for relative,digest in implementation.items():
        parts=Path(relative).parts
        if len(parts)!=2 or parts[0]!='autorouter' or not parts[1].endswith('.py') or actual_code.get(parts[1])!=digest:
            raise Rejected('retained implementation differs from provenance')
        expected_code[parts[1]]=digest
    if actual_code!=expected_code: raise Rejected('retained implementation file set differs from provenance')
    check_recorded_tool_pins(tools,native_toolchain=native_toolchain)
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
    if 'protected_route_import' in data or import_contract is not None:
        check_protected_import(path.parent,data,original,candidate,protected,**(import_contract or {}))
        verify_candidate_files(candidate,data['source_hashes'],data['candidate_sha256'])
        if hashlib.sha256(bounded_bytes(path)).hexdigest()!=receipt_digest:
            raise Rejected('protected import receipt changed during readback')
    imports=check_normal_policy(path.parent,data,native_toolchain=native_toolchain)
    import_contract=normal_import_contract(path.parent,data,imports,input_policy=input_policy,original=original,native_toolchain=native_toolchain)
    check_protected_import(path.parent,data,original,candidate,protected,**(import_contract or {}))
    if known_named_edge!=check_named_edge_policy(path.parent,data,input_policy=input_policy,
            direct_import=import_contract is not None,native_toolchain=native_toolchain):
        raise Rejected('named edge admission changed during readback')
    check_event(path.parent,binding,process)  # Flags/link counts are outside byte witnesses.
    check_route_class_evidence(path.parent,data,original,candidate,class_context=class_context)
    if native_toolchain is not None:
        # Reuse the same Native stage reader and exact original/import/refill
        # reconstruction; the experimental receipt never authorizes its tools.
        from .floor_route import check_drc_stage,process_check
        options={'native_toolchain':native_toolchain,'experimental_schematic_parity':True,'sandboxed':False}
        task=routing_task(original,data['scope'])
        pre_refill=transplant_routes(task,sx.read(path.parent/'imported.kicad_pcb'),protected=protected,policy='exact_non_uuid_lock_position_v2')
        pre_bytes=(sx.dump(pre_refill)+'\n').encode()
        if bounded_bytes(path.parent/'pre-refill.kicad_pcb')!=pre_bytes:raise Rejected('experimental pre-refill input differs from exact task/import')
        refill=path.parent/'refill'/source.name
        refill_before=dict(data['source_hashes']);refill_before[source.name]=hashlib.sha256(pre_bytes).hexdigest()
        observed=check_drc_stage(path.parent,data,'source-drc',path.parent/'snapshot'/source.name,path.parent/'source-drc-input'/source.name,False,data['source_hashes'],**options)
        if data.get('source_drc')!=observed:raise Rejected('experimental source DRC summary differs')
        check_drc_stage(path.parent,data,'refill-drc',refill,refill,True,refill_before,**options)
        if (sx.dump(transplant_fill(pre_refill,sx.read(refill)))+'\n').encode()!=bounded_bytes(candidate):
            raise Rejected('experimental final candidate differs from task/import/refill')
        check_drc_stage(path.parent,data,'final-drc',candidate,native_input,False,expected,schematic_parity=True,**options)
        for name,action,output,args in [('export','export',path.parent/'task.dsn',[path.parent/'export-netclasses.json']),
                ('import','import',path.parent/'imported.kicad_pcb',[path.parent/'routes.ses']),
                ('metrics','metrics',path.parent/'metrics.json',[])]:
            process_check(path.parent,data,name,[*native_prefix(native_toolchain),action,str(candidate),str(output),*[str(x) for x in args]])
        # Alias/import and PRL readers have already checked the full process census.
        from . import schematic_field_evidence as fields
        names={'source-drc','export','engine','import','refill-drc','final-netclasses','final-drc','metrics'}
        if fields.has_fields(native['findings']):names.update(fields.names('final-drc'))
        if len(steps)!=len(names) or {step.get('name') for step in steps}!=names:raise Rejected('experimental routing worker population differs')
        actual_tools=tool_manifest(native_toolchain=native_toolchain)
        if (tools.get('files')!=actual_tools['files'] or tools.get('experimental_native_toolchain')!=native_toolchain.record()
                or tools.get('freerouting')!=actual_tools['freerouting']):raise Rejected('explicit runtime tool pins differ')
        if (tree_hash(source.parent)!=data['source_hashes'] or tree_hash(path.parent/'snapshot')!=data['source_hashes']
                or tree_hash(path.parent)!=explicit_material):raise Rejected('experimental evidence/source changed during readback')
        check_experimental_local_settings(path.parent,data,native_toolchain)
        result.update(experimental_route_policy=EXPERIMENTAL_ROUTE_POLICY,production_admitted=False)
    if preferences_guarded:
        # Final callbacks above may inspect the complete captured import/native
        # lineage. Keep the existing bounded witness after every such reader,
        # including plain API jobs with no captured preferences or class flags.
        if bounded_inventory(source.parent,max_bytes=100*1024*1024)!=data['source_hashes']:
            raise Rejected('source project changed during preference readback')
        if bounded_evidence(path.parent)!=readback_material:
            raise Rejected('complete preference routing evidence changed during readback')
        check_event(path.parent,binding,process)
    if _rejected_attempt:
        # Return only after the late evidence/source/process freshness guards.
        return {'current':False,'validated_rejection':True,'routing_accepted':False,
            'candidate':str(candidate),'candidate_sha256':data['candidate_sha256'],
            'native_report_sha256':data['native_report_sha256'],
            'native_rejection_reasons':reasons,'receipt_sha256':receipt_digest,'applied':False,
            'authentication':'none; mutable local evidence consistency only',
            'warning':'Completed Native rejection only; no route acceptance, infeasibility proof or fresh validation.'}
    return result
