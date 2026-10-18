"""Temporary Native protection of the exact fixed-placement routing task.

Only the explicit normal worker flag enables this. No source/board is saved
here. Literal source geometry, lock and manufacturing checks remain in the
existing importer and final Native validation. DSN rounding is not waived.
"""
from . import config as c, sexpr as sx

POLICY='native-task-copper-fixed-v1'
FLAG='--task-copper-fixed'
MAX_ROUTES=100000


def native_census(board,pcbnew):
    from .floor_context import route_width
    import uuid
    rows={}
    for item in board.GetTracks():
        uid=str(item.m_Uuid.AsString())
        identity=uuid.UUID(uid)
        if identity.int==0 or identity.hex in rows or len(rows)>=MAX_ROUTES:
            raise ValueError('unique bounded Native task copper required')
        def xy(value):return [int(value.x),int(value.y)]
        row=dict(uuid=uid,kind=str(item.GetClass()),locked=item.IsLocked(),
                 net=str(item.GetNetname()),width_nm=route_width(item,pcbnew))
        if type(row['locked']) is not bool:raise ValueError('typed Native task lock required')
        if isinstance(item,pcbnew.PCB_VIA):
            row.update(at_nm=xy(item.GetPosition()),drill_nm=int(item.GetDrillValue()),
                top=int(item.TopLayer()),bottom=int(item.BottomLayer()),via_type=int(item.GetViaType()))
        else:
            row.update(start_nm=xy(item.GetStart()),end_nm=xy(item.GetEnd()),layer=int(item.GetLayer()))
            if isinstance(item,pcbnew.PCB_ARC):row['mid_nm']=xy(item.GetMid())
            elif row['kind']!='PCB_TRACK':raise ValueError('unknown Native task routing kind')
        rows[identity.hex]=row
    return rows


def invoke(board,source,pcbnew,operation,*,importing=False):
    """Fix task routes only while the supplied Native operation runs.

    Restore only original false→true locks, by unique surviving UUID. Never
    repair a missing/changed original or unlock a generated route. Restore on
    exceptions too; any uncertainty prevents the caller's later board save.
    """
    from pathlib import Path
    from .placement_clearance import read_bytes
    from .routing_scope import _route_map,_locked
    if pcbnew.GetBuildVersion()!=c.NATIVE_VERSION or type(importing) is not bool:
        raise ValueError('task copper requires qualified Native'+c.NATIVE_VERSION+' operation')
    source=Path(source);project=source.with_suffix('.kicad_pro')
    raw,pro=read_bytes(source),read_bytes(project)
    source_routes=_route_map(sx.parse(raw.decode('utf-8')))
    before=native_census(board,pcbnew)
    if set(before)!=set(source_routes):raise ValueError('Native/source task copper UUID population differs')
    for key,route in source_routes.items():
        if before[key]['locked']!=_locked(route):raise ValueError('Native/source task lock differs')
    fixed={key:dict(row,locked=True) for key,row in before.items()}
    cause=None;result=None
    try:
        for item in board.GetTracks():item.SetLocked(True)
        if native_census(board,pcbnew)!=fixed:raise ValueError('fixing task copper changed Native geometry')
        result=operation()
        after=native_census(board,pcbnew)
        if (not importing and after!=fixed) or any(after.get(key)!=row for key,row in fixed.items()):
            raise ValueError('Native operation changed or missed fixed task copper')
    except BaseException as exc:cause=exc
    finally:
        errors=[]
        try:
            # Refuse unexpected original lock loss before restoration. This
            # includes already-locked originals: the helper never repairs them.
            observed=native_census(board,pcbnew)
            if any(observed.get(key)!=row for key,row in fixed.items()):
                raise ValueError('fixed task copper changed before restoration')
            import uuid
            items=list(board.GetTracks());by={uuid.UUID(str(item.m_Uuid.AsString())).hex:item for item in items}
            if len(by)!=len(items):raise ValueError('ambiguous task copper restoration')
            for key,row in before.items():
                if row['locked'] is False:by[key].SetLocked(False)
            restored=native_census(board,pcbnew)
            if any(restored.get(key)!=row for key,row in before.items()):
                raise ValueError('task copper lock restoration differs')
        except BaseException as exc:errors.append(type(exc).__name__+': '+str(exc))
        try:
            if read_bytes(source)!=raw or read_bytes(project)!=pro:
                raise ValueError('Native task source or project changed')
        except BaseException as exc:errors.append(type(exc).__name__+': '+str(exc))
        if errors:raise ValueError('task copper restoration failed: '+'; '.join(errors)) from cause
    if cause is not None:raise cause
    return result


def check_contract(root,data,imports,*,declaration,native_toolchain=None):
    """Force paired worker flags from captured source, never a receipt option.

    Existing export/import readers establish the exact process census and all
    sidecars. This adds no optional proof/cache and no geometry normalization.
    """
    from pathlib import Path
    from . import pipeline as p
    from .adapter import native_command_parser
    from .local_settings import policy_declaration
    from .placement_clearance import read_bytes
    pins=data.get('tools',{}).get('implementation_sha256',{})
    raw=read_bytes(Path(root)/'code/native.py',1024**2)
    if p.sha(Path(root)/'code/native.py')!=pins.get('autorouter/native.py'):
        raise p.Rejected('task copper Native source provenance differs')
    native_policy=policy_declaration(raw,name='TASK_COPPER_FIXED_POLICY',expected=POLICY)
    if native_policy is None and b'task_copper.invoke(' in raw:
        raise p.Rejected('task copper Native source declaration missing')
    marker=data.get('tools',{}).get('normal_task_copper_fixed_policy')
    parse=native_command_parser(native_toolchain,data=data,with_task_copper=True)
    operations=[]
    for step in data.get('steps',[]):
        for action in ('export','import'):
            parsed=parse(step.get('argv'),action)
            if parsed is not None:operations.append((step,action,*parsed))
    if declaration is None and native_policy is None:
        if marker is not None or any(flag for _,_,_,flag in operations):
            raise p.Rejected('task copper source declaration missing')
        return  # Historical workers retain their original strict contract.
    if declaration!=POLICY or native_policy!=POLICY or marker!=POLICY:
        raise p.Rejected('task copper pipeline/Native/tool declaration differs')
    helper=Path(root)/'code/task_copper.py'
    if p.sha(helper)!=pins.get('autorouter/task_copper.py'):
        raise p.Rejected('task copper helper source provenance differs')
    if imports is None:raise p.Rejected('task copper requires actual qualified Native import census')
    wanted=native_toolchain is None
    pairs=set()
    for row in imports:
        cwd=row['cwd'];candidate=row['source']
        matching=[(s,a,flag) for s,kind,a,flag in operations if kind=='import' and s.get('cwd')==cwd
                  and a[3:]==[candidate,row['output'],row['session']]]
        exports=[(s,a,flag) for s,kind,a,flag in operations if kind=='export' and s.get('cwd')==cwd
                 and a[3:5]==[candidate,str(Path(cwd)/'task.dsn')]]
        if len(matching)!=1 or len(exports)!=1 or matching[0][2] is not wanted or exports[0][2] is not wanted:
            raise p.Rejected('normal task copper requires paired exact export/import flags')
        pairs.update((cwd,s['name']) for s,_,_ in matching+exports)
    if any(flag and (s.get('cwd'),s.get('name')) not in pairs for s,_,_,flag in operations):
        raise p.Rejected('unpaired task copper worker')
