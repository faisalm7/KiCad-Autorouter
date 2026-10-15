"""Fixed placement/clearance input policy; native rules remain authoritative.

This composes pure transforms, not another routing lifecycle. The 20µm planning
margin is a measured conservative parameter, not a universal geometry bound.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from . import board_floor as g, config as c, pipeline as p, sexpr as sx
from . import placement_transform as placement
from .floor_context import AREA_LIMITS

POLICY='placement-clearance-v1'
MARGIN_NM=20000
SCORING='via_default'


def parameters():
    return {'clearance_margin_nm':MARGIN_NM,'scoring_variant':SCORING,'via_costs':50,'plane_via_costs':5}


def read_bytes(path,limit=sx.MAX_BYTES):
    """Reject special files/symlinks and bound a size-racing file on its descriptor."""
    path=Path(path)
    if any(x.is_symlink() for x in (path,*path.parents)):raise p.Rejected('placement symlink unsupported')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as handle:
        before=os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size>limit:raise p.Rejected('placement bounded regular file required')
        raw=handle.read(before.st_size+1);after=os.fstat(handle.fileno())
    if len(raw)>limit or len(raw)!=before.st_size or (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
        raise p.Rejected('placement file changed or exceeded read ceiling')
    return raw


def inventory(directory,*,contents=False,max_bytes=32*1024*1024,max_files=2000,max_entries=4000,with_directories=False):
    """Streaming entry bounds apply before any project payload read or sort."""
    directory=Path(directory);result={};directories=[];total=0;entries=0;pending=[directory]
    while pending:
        folder=pending.pop()
        if not folder.is_dir() or any(x.is_symlink() for x in (folder,*folder.parents)):raise p.Rejected('real placement directory required')
        if with_directories:directories.append(str(folder.relative_to(directory)))
        with os.scandir(folder) as iterator:
            for item in iterator:
                entries+=1
                if entries>max_entries:raise p.Rejected('placement project entry ceiling')
                if item.is_symlink():raise p.Rejected('placement project symlink unsupported')
                if item.is_dir(follow_symlinks=False):pending.append(Path(item.path));continue
                if not item.is_file(follow_symlinks=False):raise p.Rejected('placement special project file unsupported')
                if len(result)>=max_files:raise p.Rejected('placement project file ceiling')
                raw=read_bytes(item.path,max_bytes-total);total+=len(raw)
                result[str(Path(item.path).relative_to(directory))]=raw if contents else g.sha(raw)
    files=dict(sorted(result.items()))
    return (files,tuple(sorted(directories))) if with_directories else files


def files(directory):
    result=inventory(directory,contents=True)
    placement.inventory(result)
    return result


def evidence_inventory(directory):
    # Retained execution copies/logs have the original floor100MiB/2000-file cap;
    # a separate finite entry cap prevents unbounded empty-directory traversal.
    return inventory(directory,max_bytes=100*1024*1024)


def narrow_source(original):
    if sx.children(original,'module'):raise p.Rejected('unsupported: legacy module outside placement policy')
    placement.rectangle(original);rows=placement.source_zones(original)
    rule=[row for row in rows if row['is_rule_area']]
    if not rule:raise p.Rejected('unsupported: enabled all-allowed placement area required')
    if any(not row['placement_enabled'] or row['placement_source_type']!='SHEETNAME' or any(row['disallow'].values()) for row in rule):
        raise p.Rejected('unsupported: genuine or disabled rule area outside placement policy')
    return rows


def clearance_nodes(tree):
    rule=sx.one(sx.one(tree,'structure'),'rule');classes=sx.children(sx.one(tree,'network'),'class')
    if len(classes)!=1:raise ValueError('one original class required')
    return [rule[2],rule[3],sx.one(classes[0],'rule')[2]]


def expected_tree(original,context):
    g.audit_export(original,context,guided=True)
    result=copy.deepcopy(original);value=context['derived_nm']['clearance_nm']+MARGIN_NM
    for node in clearance_nodes(result):node[1]=g.atom_um(value)
    return result


def verify_edit(original,planned,context):
    if planned!=expected_tree(original,context):raise ValueError('nondeclared planning DSN atom or geometry change')
    restored=copy.deepcopy(planned)
    for actual,before in zip(clearance_nodes(restored),clearance_nodes(original)):actual[1]=before[1]
    if restored!=original:raise ValueError('nonclearance AST differs')
    g.audit_export(restored,context,guided=True)
    return {'exact_declared_ast_change':True,'clearance_atom_count':3,'routing_accepted':False}


def planning_transform(placed,context):
    if not isinstance(placed,bytes) or not 0<len(placed)<=sx.MAX_BYTES:raise ValueError('bounded placement DSN bytes required')
    original=g._parse_dsn(placed.decode('utf-8'));planned=expected_tree(original,context)
    audit=verify_edit(original,planned,context);encoded=g._dump_dsn(planned).encode('utf-8')
    if len(encoded)>sx.MAX_BYTES or g._parse_dsn(encoded.decode('utf-8'))!=planned:raise ValueError('planning DSN roundtrip/size failed')
    return encoded,{'schema':1,'policy':POLICY,'parameters':parameters(),'input_sha256':g.sha(placed),'output_sha256':g.sha(encoded),
        'original_floor_context_sha256':g.sha(placement.canonical(context)),'original_derived_nm':copy.deepcopy(context['derived_nm']),
        'planning_clearance_nm':context['derived_nm']['clearance_nm']+MARGIN_NM,
        'clearance_atom_addresses':['structure/rule/clearance','structure/rule/clearance/type=smd_smd','network/class/rule/clearance'],
        'audit':audit,'native_rules_changed':False,'routing_accepted':False}


def derive_chain(directory,name,source_hashes):
    """Reconstruct raw→floor→placement→planning→adapter from original bytes."""
    from . import floor_route as f
    original_files=files(directory/'snapshot');native_input=files(directory/'floor-export-input')
    if not isinstance(name,str) or Path(name).name!=name or not name.endswith('.kicad_pcb'):raise p.Rejected('placement board identity differs')
    original=sx.parse(original_files[name].decode());narrow_source(original);task=g.task_from_source(original)
    task_bytes=(sx.dump(task)+'\n').encode();expected=dict(source_hashes);expected[name]=g.sha(task_bytes)
    if placement.inventory(original_files)!=source_hashes or placement.inventory(native_input)!=expected:raise p.Rejected('original/export-task inventory differs')
    board=directory/'floor-export-input'/name;raw=read_bytes(directory/'native.dsn',20*1024*1024)
    native=f.read_json(directory/'floor-export-context.json');areas=f.read_json(directory/'placement-area-context.json')
    f.context_binding(native,board,expected,'export',g.sha(raw))
    if native.get('routes')!=[]:raise p.Rejected('placement export retained routes')
    if (areas.get('source')!=str(board) or f.canonical(areas.get('limits'))!=f.canonical(AREA_LIMITS)
            or areas.get('adapter_transformation_performed') is not False or areas.get('routing_accepted') is not False):
        raise p.Rejected('area observation path/cap/scope differs')
    placement.native_binding(original_files,native_input,name,areas,raw)
    project=original_files[str(Path(name).with_suffix('.kicad_pro'))]
    guided,contract=f.policy_contract(raw,native,project,task,source_hashes)
    if read_bytes(directory/'floor-guided.dsn')!=guided or f.canonical(f.read_json(directory/'floor-policy.json'))!=f.canonical(contract):
        raise p.Rejected('raw-to-floor guidance provenance differs')
    placed,removal=placement.transform(original_files,native_input,name,areas,raw,guided)
    context=g.qualify(json.loads(project),native,task);planned,planning=planning_transform(placed,context)
    adapted=g.adapter_bytes(planned,native['obstacles'])
    outputs={'placement-guided.dsn':placed,'planning-guided.dsn':planned,'task.dsn':adapted}
    receipt={'schema':1,'policy':POLICY,'parameters':parameters(),'source_hashes':source_hashes,'task_sha256':g.sha(task_bytes),
        'project_sha256':g.sha(project),'floor_context_sha256':p.sha(directory/'floor-export-context.json'),
        'area_context_sha256':p.sha(directory/'placement-area-context.json'),'floor_policy_sha256':p.sha(directory/'floor-policy.json'),
        'native_dsn_sha256':g.sha(raw),'floor_guided_dsn_sha256':g.sha(guided),
        'outputs_sha256':{key:g.sha(value) for key,value in outputs.items()},'removal':removal,'planning':planning,
        'routing_accepted':False,'native_rules_changed':False}
    return outputs,receipt


def check_chain(directory,data):
    from . import floor_route as f
    outputs,receipt=derive_chain(directory,Path(data['source']).name,data['source_hashes'])
    if any(read_bytes(directory/name)!=raw for name,raw in outputs.items()):raise p.Rejected('placement planning/adapter bytes differ')
    path=directory/'placement-policy.json'
    if f.canonical(f.read_json(path))!=f.canonical(receipt) or data.get('placement_policy')!={'file':path.name,'sha256':p.sha(path)}:
        raise p.Rejected('placement policy receipt differs')
    if f.canonical(data.get('planning_parameters'))!=f.canonical(parameters()):raise p.Rejected('fixed placement parameters differ')


def capture_freeze(tools):
    """New runs require committed core/lock; later readback uses saved evidence."""
    pinned={**tools['implementation_sha256'],'toolchain.lock.json':p.sha(c.ROOT/'toolchain.lock.json')}
    for relative,digest in pinned.items():
        raw=subprocess.run(['git','show',tools['git_head']+':'+relative],cwd=c.ROOT,capture_output=True,check=True,timeout=5).stdout
        if g.sha(raw)!=digest:raise p.Rejected('commit exact placement core/toolchain before routing')
    return {'schema':1,'policy':POLICY,'git_head':tools['git_head'],'files_sha256':pinned}


def check_freeze(directory,data):
    from . import floor_route as f
    path=directory/'placement-source-freeze.json';frozen=f.read_json(path);tools=data['tools']
    lock=directory/'placement-toolchain.lock.json'
    expected={'schema':1,'policy':POLICY,'git_head':tools.get('git_head'),
        'files_sha256':{**tools['implementation_sha256'],'toolchain.lock.json':p.sha(lock)}}
    if (not isinstance(tools.get('git_head'),str) or re.fullmatch(r'[0-9a-f]{40}',tools['git_head']) is None
            or f.canonical(frozen)!=f.canonical(expected) or data.get('placement_source_freeze')!={'file':path.name,'sha256':p.sha(path)}
            or read_bytes(lock)!=read_bytes(c.ROOT/'toolchain.lock.json')):raise p.Rejected('placement committed-source freeze differs')


def verify_candidate(candidate,source_hashes,digest):
    expected={**source_hashes,candidate.name:digest}
    if inventory(candidate.parent)!=expected:raise p.Rejected('placement candidate tree changed')


def final_freshness(directory,data):
    from . import floor_route as f
    source=Path(data['source'])
    if inventory(source.parent)!=data['source_hashes'] or inventory(directory/'snapshot')!=data['source_hashes']:
        raise p.Rejected('placement source/snapshot changed during readback')
    verify_candidate(Path(data['candidate']),data['source_hashes'],data['candidate_sha256'])
    if f.evidence_inventory(directory)!=data.get('floor_evidence_hashes'):raise p.Rejected('placement evidence changed during readback')
    check_freeze(directory,data)
