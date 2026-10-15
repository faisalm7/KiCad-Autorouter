"""Explicit Freerouting search-angle baseline; original Native rules stay final.

SPDX-License-Identifier: GPL-3.0-or-later
The pinned v2.5.0 parser defaults an omitted snap_angle to 45 degrees. This
initial experimental profile inserts canonical `(snap_angle none)` into a
separate engine input. It does not change the corrected task or an explicit
source angle. Actual JAR loading and Native outcomes require qualification.
"""
import copy
import hashlib
from pathlib import Path
from . import pipeline as p, sexpr as sx, adapter as dsn

PROFILE='tuned-free-angle'
POLICY='explicit-omitted-snap-angle-none-v1'
INPUT='engine-free-angle.dsn'
RECORD='engine-angle.json'
MAX_BYTES=20*1024**2


def transform(raw):
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
        check=copy.deepcopy(result);sx.one(check,'structure').remove(['snap_angle','none'])
        if check!=tree:raise ValueError('search angle changed another DSN element')
        emitted=dsn._dump_dsn(result).encode()
        if dsn._parse_dsn(emitted.decode())!=result:raise ValueError('search-angle semantic roundtrip differs')
        if len(emitted)>MAX_BYTES:raise ValueError('search-angle output exceeds DSN ceiling')
        return emitted,dict(schema=1,policy=POLICY,profile=PROFILE,
            input=dict(file='task.dsn',sha256=hashlib.sha256(raw).hexdigest()),
            output=dict(file=INPUT,sha256=hashlib.sha256(emitted).hexdigest()),
            source_angle='omitted: pinned Freerouting default fortyfive_degree',
            requested_angle='none',exact_only_structure_snap_angle_insert=True)
    except (ValueError,UnicodeError,TypeError,IndexError) as exc:
        raise p.Rejected('unsupported search-angle transport: '+str(exc)) from exc


def prepare(directory):
    from .placement_clearance import read_bytes
    directory=Path(directory);raw=read_bytes(directory/'task.dsn',MAX_BYTES)
    emitted,record=transform(raw)
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
    return (data.get('engine_profile')==PROFILE or 'engine_angle_binding' in data
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
    raw=read_bytes(directory/'task.dsn',MAX_BYTES)
    emitted,expected=transform(raw)
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
