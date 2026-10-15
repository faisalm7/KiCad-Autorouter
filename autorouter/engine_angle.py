"""Explicit Freerouting search-angle baseline; original Native rules stay final.

SPDX-License-Identifier: GPL-3.0-or-later
The pinned v2.5.0 parser defaults an omitted snap_angle to 45 degrees. This
initial experimental profile inserts canonical `(snap_angle none)` into a
separate engine input. It does not change the corrected task or an explicit
source angle. Actual JAR loading and Native outcomes require qualification.
"""
import copy
import hashlib
import re
from decimal import Decimal,InvalidOperation
from pathlib import Path
from . import pipeline as p, sexpr as sx, adapter as dsn

PROFILE='tuned-free-angle'
POLICY='explicit-omitted-snap-angle-none-v1'
INPUT='engine-free-angle.dsn'
RECORD='engine-angle.json'
MAX_BYTES=20*1024**2
CLEARANCE_MARGIN_NM=20000
CLEARANCE_POLICY='engine-only-default-clearance20-v1'


def _margin(value):
    if value is not None and (type(value)is not int or value!=CLEARANCE_MARGIN_NM):
        raise p.Rejected('planning clearance margin accepts only None or literal integer20000nm')
    return value


def _clearance_targets(tree):
    """Bounded ordinary Default scopes only; return the TWO mutable atoms."""
    dsn._check_units(tree)
    def walk(node):
        if isinstance(node,list):
            yield node
            for child in node:yield from walk(child)
    nodes=list(walk(tree))
    if any(len([n for n in nodes if n and n[0]==key])!=1 for key in ('unit','resolution')):
        raise ValueError('planning clearance requires unique unnested um unit/resolution')
    structure=sx.one(tree,'structure');network=sx.one(tree,'network')
    if structure is None or network is None:raise ValueError('planning structure/network required')
    classes=sx.children(network,'class')
    if len([n for n in nodes if n and n[0]=='class'])!=1:raise ValueError('planning nested or duplicate class scope')
    if len(classes)!=1 or len(classes[0])<2 or classes[0][1]!='kicad_default':raise ValueError('planning singleton literal kicad_default required')
    if any(isinstance(n,list) and (not n or n[0] not in {'rule','circuit'}) for n in classes[0][2:]):raise ValueError('planning unknown Default class child')
    circuits=sx.children(classes[0],'circuit')
    if len(circuits)!=1 or len(circuits[0])!=2 or not isinstance(circuits[0][1],list) or len(circuits[0][1])!=2 or circuits[0][1][0]!='use_via' or type(circuits[0][1][1])is not str:raise ValueError('planning Default through-via circuit scope required')
    rules=sx.children(structure,'rule');crules=sx.children(classes[0],'rule')
    if not 1<=len(rules)<=2 or len(crules)!=1:raise ValueError('planning global/class rule groups differ')
    def numeric(atom):
        if type(atom)is not str or len(atom)>24 or re.fullmatch(r'(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)',atom)is None:raise ValueError('planning finite decimal numeric atom required')
        value=Decimal(atom)
        if not value.is_finite() or not 0<=value<=1000000 or value*1000!=(value*1000).to_integral_value():raise ValueError('planning bounded nanometre decimal required')
        return value
    ordinary=[];edge=[]
    pairs={'default_kicadedge','smd_kicadedge','kicadedge_kicadedge'}
    for index,rule in enumerate(rules):
        if len(rule)==4 and all(isinstance(x,list) for x in rule[1:]) and [x[0] for x in rule[1:]]==['width','clearance','clearance'] and len(rule[1])==2 and len(rule[2])==2 and rule[3][2:]==[['type','smd_smd']]:
            if len(rule[3])!=3 or numeric(rule[1][1])<=0 or numeric(rule[2][1])<=0:raise ValueError('planning ordinary positive width/clearance required')
            numeric(rule[3][1]);ordinary.append((index,rule))
        elif len(rule)==4 and all(isinstance(x,list) and len(x)==3 and x[0]=='clearance' and isinstance(x[2],list) and len(x[2])==2 and x[2][0]=='type' for x in rule[1:]) and {x[2][1] for x in rule[1:]}==pairs:
            if any(numeric(x[1])<=0 for x in rule[1:]):raise ValueError('planning positive edge values required')
            edge.append(rule)
        else:raise ValueError('planning unknown global/typed clearance rule group')
    if len(ordinary)!=1 or len(edge)>1:raise ValueError('planning duplicate or missing ordinary/edge rule')
    gi,rule=ordinary[0];classrule=crules[0]
    if (len(classrule)!=3 or any(not isinstance(x,list) or len(x)!=2 for x in classrule[1:])
            or [x[0] for x in classrule[1:]]!=['width','clearance']
            or numeric(classrule[1][1])!=numeric(rule[1][1]) or numeric(classrule[2][1])!=numeric(rule[2][1])):
        raise ValueError('planning Default width/clearance target mismatch')
    allowed_rules=[*rules,classrule];allowed_clearances=[*sx.children(rule,'clearance'),classrule[2],*(x for e in edge for x in e[1:])]
    if any(n and (n[0]=='rule' and all(n is not a for a in allowed_rules) or n[0]=='clearance' and all(n is not a for a in allowed_clearances) or n[0] in {'layer_rule','class_class'}) for n in nodes):
        raise ValueError('planning nested or unknown rule/clearance scope')
    boundary=sx.one(structure,'boundary');edgeclasses=[n for n in nodes if n and n[0]=='clearance_class']
    if edge:
        if boundary is None or len(edgeclasses)!=1 or edgeclasses[0]!=['clearance_class','kicadedge'] or all(edgeclasses[0] is not n for n in boundary):raise ValueError('planning edge matrix/boundary binding differs')
    elif edgeclasses:raise ValueError('planning unknown clearance class')
    return [(f'structure/rule[{gi}]/clearance',rule[2]),('network/class[kicad_default]/rule/clearance',classrule[2])]


def transform(raw,*,clearance_margin_nm=None):
    _margin(clearance_margin_nm)
    if type(raw) is not bytes or not 0<len(raw)<=MAX_BYTES:
        raise p.Rejected('bounded exact DSN bytes required for search angle')
    try:
        tree=dsn._parse_dsn(raw.decode('utf-8'))
        if not tree or tree[0]!='pcb':raise ValueError('Specctra pcb root required')
        structure=sx.one(tree,'structure')
        if structure is None:raise ValueError('single structure required')
        def visit(node):
            if not isinstance(node,list):return
            if node and isinstance(node[0],str) and node[0].replace('_','').lower()=='snapangle':
                raise ValueError('explicit or ambiguous source angle is outside this baseline scope')
            for child in node:visit(child)
        visit(tree)
        result=copy.deepcopy(tree);sx.one(result,'structure').append(['snap_angle','none'])
        changes=[]
        if clearance_margin_nm is not None:
            for address,node in _clearance_targets(result):
                before=node[1];node[1]=dsn._atom_number(Decimal(before)+Decimal(clearance_margin_nm)/1000)
                changes.append(dict(address=address,before=before,after=node[1]))
        check=copy.deepcopy(result);sx.one(check,'structure').remove(['snap_angle','none'])
        if clearance_margin_nm is not None:
            for (address,node),change in zip(_clearance_targets(check),changes):
                if address!=change['address'] or node[1]!=change['after']:raise ValueError('planning clearance reverse witness differs')
                node[1]=change['before']
        if check!=tree:raise ValueError('search angle changed another DSN element')
        emitted=dsn._dump_dsn(result).encode()
        if dsn._parse_dsn(emitted.decode())!=result:raise ValueError('search-angle semantic roundtrip differs')
        if len(emitted)>MAX_BYTES:raise ValueError('search-angle output exceeds DSN ceiling')
        record=dict(schema=1,policy=POLICY,profile=PROFILE,
            input=dict(file='task.dsn',sha256=hashlib.sha256(raw).hexdigest()),
            output=dict(file=INPUT,sha256=hashlib.sha256(emitted).hexdigest()),
            source_angle='omitted: pinned Freerouting default fortyfive_degree',
            requested_angle='none',exact_only_structure_snap_angle_insert=clearance_margin_nm is None)
        if clearance_margin_nm is not None:
            record.update(clearance_margin_nm=clearance_margin_nm,planning_clearance=dict(policy=CLEARANCE_POLICY,classification='B1_adapter_only',changes=changes,
                exact_reversible_ast_edit=True,native_rules_changed=False,task_source_changed=False,routing_accepted=False,universal_geometry_bound=False))
        return emitted,record
    except (ValueError,UnicodeError,TypeError,IndexError,InvalidOperation) as exc:
        raise p.Rejected('unsupported search-angle transport: '+str(exc)) from exc


def prepare(directory,*,clearance_margin_nm=None):
    from .placement_clearance import read_bytes
    directory=Path(directory);raw=read_bytes(directory/'task.dsn',MAX_BYTES)
    emitted,record=transform(raw,clearance_margin_nm=clearance_margin_nm)
    with (directory/INPUT).open('xb') as stream:stream.write(emitted)
    with (directory/RECORD).open('x') as stream:
        import json
        stream.write(json.dumps(record,sort_keys=True,indent=2)+'\n')
    return dict(file=RECORD,sha256=p.sha(directory/RECORD))


def marked(directory,data):
    directory=Path(directory)
    rows=data.get('steps',[])
    from .floor_route import read_json
    journal=directory/'engine-process.json'
    actual=read_json(journal) if journal.exists() or journal.is_symlink() else None
    rows=[*(rows if type(rows)is list else []),actual]
    visible_worker=any(type(row)is dict and type(row.get('argv'))is list
        and any(type(value)is str and Path(value).name==INPUT for value in row['argv']) for row in rows)
    return (data.get('engine_profile')==PROFILE or 'engine_angle_binding' in data or 'engine_planning_clearance_margin_nm' in data
        or any((directory/name).exists() or (directory/name).is_symlink() for name in [RECORD,INPUT])
        or visible_worker)


def check(directory,data):
    from .floor_route import canonical,read_json
    from .placement_clearance import read_bytes
    directory=Path(directory);marker=directory/RECORD;engine_input=directory/INPUT
    active=data.get('engine_profile')==PROFILE
    if not active:
        if marked(directory,data):
            raise p.Rejected('search-angle evidence on another engine profile')
        return None
    if type(data.get('engine_budget'))is not dict:
        raise p.Rejected('search-angle profile requires retained engine budget')
    marker_raw=read_bytes(marker,64*1024)
    expected_binding=dict(file=RECORD,sha256=hashlib.sha256(marker_raw).hexdigest())
    if data.get('engine_angle_binding')!=expected_binding:
        raise p.Rejected('search-angle binding missing or changed')
    proof=read_json(marker);declared='engine_planning_clearance_margin_nm' in data
    proof_marked=type(proof)is dict and 'clearance_margin_nm' in proof
    margin=data.get('engine_planning_clearance_margin_nm');_margin(margin)
    if declared!=proof_marked or declared and (margin is None or proof['clearance_margin_nm']!=margin or type(proof['clearance_margin_nm'])is not int):
        raise p.Rejected('planning clearance reciprocal report/proof margin missing or invalid')
    if declared and p.check_engine_optimizer_override(data) is not False:raise p.Rejected('planning clearance requires optimizerFalse/fanoutFalse')
    raw=read_bytes(directory/'task.dsn',MAX_BYTES)
    emitted,expected=transform(raw,clearance_margin_nm=margin)
    if (canonical(read_json(marker))!=canonical(expected)
            or read_bytes(engine_input,MAX_BYTES)!=emitted
            or read_bytes(marker,64*1024)!=marker_raw):
        raise p.Rejected('engine search-angle task/proof differs')
    return expected


def check_scope(data,input_policy,native_toolchain=None):
    if (input_policy!='native' or data.get('adapter')!='both'
            or data.get('scope')!='whole_board_unlocked_routing' or data.get('strategy') is not None
            or data.get('baseline')!='B2_tuned_free_angle' or native_toolchain is not None
            or 'routing_preferences' in data or 'layer_binding' in data):
        raise p.Rejected('unsupported: search-angle receipt requires ordinary native corrected whole-board scope')

    if 'engine_planning_clearance_margin_nm' in data:
        if _margin(data['engine_planning_clearance_margin_nm']) is None or p.check_engine_optimizer_override(data,input_policy=input_policy,native_toolchain=native_toolchain) is not False:
            raise p.Rejected('planning clearance requires ordinary optimizerFalse/fanoutFalse scope')
