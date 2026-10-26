"""Explicit Mac protection of unchanged PRL bytes in fresh owned Job copies.

This guards actual Native input, never restores bytes or waives any PRL field.
It is not isolation from a hostile same-user process that can clear file flags.
"""
from contextlib import contextmanager
from functools import lru_cache
import os
from pathlib import Path
import stat
from . import pipeline as p,handoff as h
POLICY='mac-owned-prl-immutable-v1'
JOB_POLICY='job-owned-prl-immutable-v1'

def canonical(value):
    path=Path(value)
    if (not path.is_absolute() or '..' in path.parts or path.resolve()!=path
            or any(x.is_symlink() for x in (path,*path.parents))):
        raise p.Rejected('PRL requires canonical owned paths')
    return path

@contextmanager
def preserve(path,owned_root,owner,*,cleanup_complete=lambda:True):
    path,owned_root=canonical(path),canonical(owned_root)
    if h.owned_destination(owner)!=owned_root:raise p.Rejected('PRL ownership witness differs')
    if owned_root not in path.parents or path.suffix!='.kicad_prl':raise p.Rejected('PRL must belong to captured owned root')
    if not path.exists():
        yield {'policy':POLICY,'present':False};return
    if not hasattr(os,'chflags') or not hasattr(stat,'UF_IMMUTABLE'):raise p.Rejected('PRL immutable flag unavailable')
    before=path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_flags!=0:raise p.Rejected('PRL guard requires ordinary unflagged exclusive file')
    digest,flag=p.sha(path),stat.UF_IMMUTABLE
    event={'policy':POLICY,'present':True,'path':str(path),'sha256':digest,'flags_before':0,'flags_during':flag,'flags_restored':False,'bytes_unchanged':False}
    if h.owned_destination(owner)!=owned_root:raise p.Rejected('PRL owned output changed')
    os.chflags(path,flag,follow_symlinks=False)
    try:
        frozen=path.stat()
        if (frozen.st_dev,frozen.st_ino)!=(before.st_dev,before.st_ino) or frozen.st_flags!=flag:raise p.Rejected('PRL freeze identity/flag differs')
        yield event
    finally:
        if h.owned_destination(owner)!=owned_root:raise p.Rejected('PRL owned output changed before restoration')
        if cleanup_complete() is not True:raise p.Rejected('PRL remains immutable: child cleanup not confirmed: '+str(path))
        current=path.lstat()
        if not stat.S_ISREG(current.st_mode) or (current.st_dev,current.st_ino)!=(before.st_dev,before.st_ino):raise p.Rejected('PRL identity changed; refusing unrelated flag edit')
        if current.st_flags!=flag:raise p.Rejected('PRL immutable flag changed unexpectedly')
        os.chflags(path,0,follow_symlinks=False)
        event['flags_restored']=path.stat().st_flags==0;event['bytes_unchanged']=p.sha(path)==digest
        if not event['flags_restored'] or not event['bytes_unchanged']:raise p.Rejected('PRL bytes/flags changed during native execution')

def protected_step(job,name,argv,*,allowed=(0,)):
    """Journal one owned Native worker's guard, including plotting failures."""
    start=len(job.steps);state={'complete':False};event=None;native_error=None
    def worker():
        matches=[s for s in job.steps[start:] if s.get('name')==name and s.get('cwd')==str(job.out)]
        return matches[0] if len(matches)==1 else None
    try:
        with preserve(Path(argv[-1]).with_suffix('.kicad_prl'),job.out,job._local_settings_owner,cleanup_complete=lambda:state['complete']) as event:
            try:result=job.step(name,argv,allowed=allowed)
            except (Exception,KeyboardInterrupt) as exc:
                native_error=type(exc).__name__+': '+str(exc);raise
            finally:
                result=worker();state['complete']=result is not None and result.get('cleanup_complete') is True
        if not state['complete']:raise p.Rejected('PRL Native child cleanup not confirmed')
        return result
    except (Exception,KeyboardInterrupt) as exc:
        if event is not None:
            event['guard_error']=type(exc).__name__+': '+str(exc)
            if native_error is not None:event['native_error']=native_error
        raise
    finally:
        result=worker()
        if result is not None:
            if h.owned_destination(job._local_settings_owner)!=job.out:raise p.Rejected('PRL Job root changed before worker journal')
            result['local_settings_policy']=JOB_POLICY;result['local_settings_protection']=event
            p.save_json(job.out/(name+'-process.json'),result)

def drc_step(job,name,argv):
    return protected_step(job,name,argv,allowed=(0,5))

def check_current_metadata(path):
    """Check current PRL file metadata; return False only when absent.

    Byte/provenance checks remain with the caller. This also serves the final
    GUI opening fence after the worker has replayed the full Native evidence.
    """
    path=canonical(Path(path))
    if path.suffix!='.kicad_prl':raise p.Rejected('PRL preservation path must name local settings')
    try:info=path.lstat()
    except FileNotFoundError:return False
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink!=1
            or getattr(info,'st_flags',None)!=0):
        raise p.Rejected('PRL retained current file/flags differ')
    return True

def check_preserved(path,before,event):
    """Recheck exact retained PRL bytes, metadata and one preserve() event."""
    path=canonical(Path(path))
    if path.suffix!='.kicad_prl':raise p.Rejected('PRL preservation path must name local settings')
    if type(before) is not dict:raise p.Rejected('PRL expected input map required')
    present=check_current_metadata(path)
    if path.name not in before:
        expected={'policy':POLICY,'present':False}
    else:
        if (not hasattr(stat,'UF_IMMUTABLE') or not present or not path.exists() or not stat.S_ISREG(path.lstat().st_mode)
                or path.stat().st_nlink!=1 or path.stat().st_flags!=0 or p.sha(path)!=before[path.name]):
            raise p.Rejected('PRL current retained bytes/flags differ')
        expected={'policy':POLICY,'present':True,'path':str(path),'sha256':before[path.name],'flags_before':0,'flags_during':stat.UF_IMMUTABLE,'flags_restored':True,'bytes_unchanged':True}
    if (type(event) is not dict or set(event)!=set(expected)
            or any(type(event[k]) is not type(v) or event[k]!=v for k,v in expected.items())):
        raise p.Rejected('PRL guard event differs from exact Native input')


def check_event(directory,binding,process,*,allow_worker_failure=False):
    """Strict opt-in marker/event replay; legacy unmarked receipts unchanged."""
    marker=binding.get('local_settings_policy');worker_marker=process.get('local_settings_policy')
    if marker is None and worker_marker is None:return
    if marker!=JOB_POLICY or worker_marker!=JOB_POLICY:raise p.Rejected('PRL Job policy marker differs')
    root=canonical(Path(directory));board=canonical(Path(binding['input']));path=board.with_suffix('.kicad_prl')
    if root not in board.parents:raise p.Rejected('PRL validation input outside Job root')
    argv=process.get('argv')
    if (type(argv) is not list or not argv or argv[-1]!=str(board)
            or type(binding.get('saved')) is not bool or binding['saved'] is not ('--save-board' in argv[:-1])):
        raise p.Rejected('PRL saved-input identity differs from worker command')
    if process.get('cleanup_complete') is not True:raise p.Rejected('PRL child cleanup not confirmed')
    event=process.get('local_settings_protection');before=binding['before']
    if allow_worker_failure:
        from .floor_route import read_json,canonical as encode
        from .placement_clearance import inventory,read_bytes
        if (type(event) is not dict or process.get('status') not in
                {'timeout','memory_limit','disk_limit','log_limit','descendants_left_running','spawn_error','runner_error','nonzero_exit'}
                or (process.get('status')=='nonzero_exit' and process.get('exit_code') in (0,5))):
            raise p.Rejected('PRL failure replay requires an actual rejected worker')
        error=event.get('native_error')
        if type(error) is not str or not 0<len(error.encode())<=4096 or event.get('guard_error')!=error:
            raise p.Rejected('PRL failed-worker preservation error differs')
        failure=read_json(Path(directory)/(process['name']+'-failure.json'))
        cause=failure.get('error',{})
        if (type(failure.get('schema')) is not int or failure['schema']!=1
                or failure.get('passed') is not False or failure.get('phase')!='native'
                or error!=str(cause.get('type'))+': '+str(cause.get('message'))
                or encode(failure.get('binding'))!=encode(binding)
                or encode(failure.get('validation_copy_before'))!=encode(before)
                or failure.get('capture_errors')!=[]
                or encode(inventory(board.parent))!=encode(binding.get('after'))):
            raise p.Rejected('PRL failed-worker journal differs')
        p.check_drc_project(before,binding['after'],board.name,saved=binding.get('saved'))
        artifacts=failure.get('artifacts');name=process['name']
        if type(artifacts) is not dict or set(artifacts)!={name+'.json',name+'.log',name+'-process.json'}:
            raise p.Rejected('PRL failed-worker artifact inventory differs')
        for filename,expected in artifacts.items():
            path=canonical(root/filename)
            if expected is None:
                if path.exists():raise p.Rejected('PRL failed-worker absent artifact now exists')
            else:
                raw=read_bytes(path,100*1024**2)
                import hashlib
                if (type(expected) is not dict or set(expected)!={'sha256','bytes'}
                        or type(expected.get('bytes')) is not int or expected['bytes']!=len(raw)
                        or expected.get('sha256')!=hashlib.sha256(raw).hexdigest()):
                    raise p.Rejected('PRL failed-worker artifact pin differs')
        path=board.with_suffix('.kicad_prl')
        event={key:value for key,value in event.items() if key not in {'native_error','guard_error'}}
    check_preserved(path,before,event)


def policy_declaration(raw,*,name='NORMAL_DRC_LOCAL_SETTINGS_POLICY',expected=JOB_POLICY):
    """Inspect bounded captured code as data; never execute a receipt's source."""
    return policy_declarations(raw,{name:expected})[name]


def policy_declarations(raw,policies):
    """Check related declarations in one parse, with the same strict guards."""
    import ast
    if type(raw) is not bytes or len(raw)>1024**2:raise p.Rejected('bounded captured pipeline source required')
    if (type(policies) is not dict or not 1<=len(policies)<=8
            or any(type(name)is not str or type(value)is not str for name,value in policies.items())):
        raise p.Rejected('bounded expected policy namespace required')
    derive,parse,walk=_derive_policy_declarations,ast.parse,ast.walk
    expected=tuple(sorted(policies.items()))
    defaults=tuple(_policy_defaults(function) for function in (derive,parse,walk))
    if sum(len(name)+len(value) for name,value in expected)>8192 or any(value is None for value in defaults):
        result=derive(raw,expected,parse,walk)  # Unsupported memo keys never add a source refusal.
    else:
        result=_cached_policy_declarations(raw,expected,derive,derive.__code__,
            parse,getattr(parse,'__code__',None),walk,getattr(walk,'__code__',None),defaults)
    result=dict(result)
    return {name:result[name] for name in policies}


@lru_cache(maxsize=16)
def _cached_policy_declarations(raw,policies,derive,derive_code,parse,parse_code,walk,walk_code,defaults):
    # At most16 source byte strings (16MiB), each with at most8192 namespace
    # characters; no AST or file evidence is cached. Callable/code keys prevent
    # reuse after checker/parser/walker or bounded default-argument changes.
    return derive(raw,policies,parse,walk)


def _policy_defaults(function):
    """Small immutable memo key only; unfamiliar signatures stay uncached."""
    defaults=getattr(function,'__defaults__',None)
    keywords=getattr(function,'__kwdefaults__',None)
    if (defaults is not None and type(defaults) is not tuple
            or keywords is not None and (type(keywords) is not dict or len(keywords)>16
                or any(type(name) is not str for name in keywords))):return None
    budget=[64,8192]
    def frozen(value,depth=0):
        budget[0]-=1
        if depth>4 or budget[0]<0:raise ValueError
        kind=type(value)
        if kind is tuple:return (tuple,tuple(frozen(item,depth+1) for item in value))
        if kind not in (type(None),bool,int,str,bytes):raise ValueError
        if kind in (str,bytes):budget[1]-=len(value)
        if budget[1]<0 or kind is int and value.bit_length()>256:raise ValueError
        return (kind,value)
    try:return (frozen(defaults),frozen(None if keywords is None else tuple(sorted(keywords.items()))))
    except ValueError:return None


def _derive_policy_declarations(raw,policies,parse,walk):
    """Pure uncached AST derivation; exceptions never enter the memo."""
    import ast
    policies=dict(policies)
    try:tree=parse(raw)
    except (SyntaxError,ValueError,RecursionError) as exc:raise p.Rejected('invalid captured pipeline policy source') from exc
    declarations={name:[] for name in policies}
    for node in walk(tree):
        targets=node.targets if isinstance(node,ast.Assign) else [node.target] if isinstance(node,(ast.AnnAssign,ast.AugAssign,ast.NamedExpr)) else []
        names={item.id for target in targets for item in walk(target) if isinstance(item,ast.Name)}
        for name in names.intersection(policies):declarations[name].append(node)
    result={}
    for name,expected in policies.items():
        declared=declarations[name]
        if not declared:result[name]=None;continue
        node=declared[0]
        if (len(declared)!=1 or node not in tree.body or not isinstance(node,(ast.Assign,ast.AnnAssign))
                or (isinstance(node,ast.Assign) and (len(node.targets)!=1 or not isinstance(node.targets[0],ast.Name)))
                or (isinstance(node,ast.AnnAssign) and not isinstance(node.target,ast.Name))
                or not isinstance(node.value,ast.Constant) or type(node.value.value) is not str or node.value.value!=expected):
            raise p.Rejected('ambiguous or unsupported captured normal DRC policy')
        result[name]=expected
    return tuple(result.items())


def check_normal_policy(directory,data,*,max_bytes=None,max_files=None,native_toolchain=None):
    try:return _check_normal_policy(directory,data,max_bytes=max_bytes,max_files=max_files,native_toolchain=native_toolchain)
    except (OSError,ValueError) as exc:
        raise p.Rejected('invalid normal Native policy evidence: '+str(exc)) from exc


def _check_normal_policy(directory,data,*,max_bytes=None,max_files=None,native_toolchain=None):
    """Close optional-marker deletion using the mandatory captured producer.

    A fully rewritten consistent fabricated history is not authenticated by
    this local reader. Genuine pre-policy source snapshots keep legacy checks.
    """
    from .floor_route import read_json,canonical as encode,SANDBOX
    from .placement_clearance import read_bytes,inventory
    from .adapter import native_command_parser
    native_command_parser(native_toolchain,data=data)  # Typed context before legacy-policy exits.
    expected_cli=str(p.c.CLI if native_toolchain is None else native_toolchain.cli)
    root=canonical(Path(directory));implementation=data.get('tools',{}).get('implementation_sha256',{})
    pipeline=root/'code/pipeline.py';raw=read_bytes(pipeline,1024**2)
    if p.sha(pipeline)!=implementation.get('autorouter/pipeline.py'):raise p.Rejected('normal DRC producer source pin differs')
    declarations=policy_declarations(raw,{'FIELD_LOCAL_SETTINGS_POLICY':'job-owned-field-prl-immutable-v1',
        'NORMAL_DRC_LOCAL_SETTINGS_POLICY':JOB_POLICY})
    field_policy=declarations['FIELD_LOCAL_SETTINGS_POLICY']
    policy=declarations['NORMAL_DRC_LOCAL_SETTINGS_POLICY']
    # Native export policy is independent of PRL presence and its declaration.
    # Check it before the legacy PRL return, using the same bounded census.
    if max_bytes is None or max_files is None:
        from . import placement_strategy as ps
        default_bytes,default_files=(ps.LIMIT,ps.MAX_FILES) if data.get('schema')==5 else (100*1024**2,2000)
        max_bytes=default_bytes if max_bytes is None else max_bytes
        max_files=default_files if max_files is None else max_files
    retained=inventory(root,max_bytes=max_bytes,max_files=max_files,max_entries=max_files*2)
    from .padless_alias import check_exports
    check_exports(root,data,retained,native_toolchain=native_toolchain)
    if policy is None:
        if 'normal_drc_local_settings_policy' in data.get('tools',{}):raise p.Rejected('normal DRC source declaration missing')
        return
    if data.get('tools',{}).get('normal_drc_local_settings_policy')!=policy:raise p.Rejected('normal DRC policy declaration missing from tools')
    for name in ('local_settings.py','handoff.py','floor_route.py','placement_clearance.py'):
        helper=root/'code'/name
        if not helper.is_file() or helper.is_symlink() or p.sha(helper)!=implementation.get('autorouter/'+name):
            raise p.Rejected('normal DRC compatibility implementation provenance missing')
    # Census retained workers as well as declared steps. A removed source,
    # refill or failed-trial row must not hide its still-retained DRC evidence.
    # Reuse the existing whole-evidence bounds, including pruning's larger cap.
    from .adapter import check_fixed_placement_import
    imports=check_fixed_placement_import(root,data,retained,native_toolchain=native_toolchain)
    def is_drc(argv):
        if type(argv) is not list:return False
        command=argv[len(SANDBOX):] if argv[:len(SANDBOX)]==SANDBOX else argv
        visible=any(command[i:i+2]==['pcb','drc'] for i in range(len(command)-1))
        if not visible:return False
        if (any(type(value) is not str for value in command) or len(command)<4
                or command[:3]!=[expected_cli,'pcb','drc']):
            raise p.Rejected('unqualified caller-pinned Native DRC prefix')
        return True
    census=set()
    for name in retained:
        if name.endswith('-process.json'):
            item=read_json(root/name)
            if is_drc(item.get('argv')) or 'local_settings_policy' in item:
                census.add(str(Path(name).with_name(Path(name).name[:-len('-process.json')])))
        elif name.endswith('-binding.json'):
            item=read_json(root/name)
            # Saved is a mandatory Job.drc binding field; plot/input bindings
            # use a different contract and are not Native DRC workers.
            if 'saved' in item or 'local_settings_policy' in item:
                census.add(str(Path(name).with_name(Path(name).name[:-len('-binding.json')])))
    stages=[];declared=set()
    for step in data.get('steps',[]):
        argv=step.get('argv',[])
        if is_drc(argv):
            cwd=canonical(Path(step['cwd']));name=step['name']
            if cwd!=root and root not in cwd.parents:raise p.Rejected('normal DRC worker escaped routing evidence')
            if (type(name) is not str or not 0<len(name.encode())<=128 or name in ('.','..')
                    or any(ch in name for ch in ('/',chr(92))) or any(ord(ch)<32 for ch in name)):
                raise p.Rejected('normal DRC worker stage name invalid')
            identity=str((cwd/name).relative_to(root))
            if identity in declared:raise p.Rejected('duplicate normal DRC worker lineage')
            declared.add(identity)
            process=read_json(cwd/(name+'-process.json'));binding=read_json(cwd/(name+'-binding.json'))
            if (process.get('argv')!=argv or process.get('cwd')!=str(cwd) or process.get('name')!=name
                    or any(encode(step.get(key))!=encode(value) for key,value in process.items())
                    or binding.get('input')!=argv[-1]
                    or process.get('local_settings_policy')!=policy or binding.get('local_settings_policy')!=policy):
                raise p.Rejected('normal DRC worker policy or lineage missing')
            if native_toolchain is None:
                if 'experimental_native_toolchain' in binding:
                    raise p.Rejected('default DRC reader refuses experimental context')
            elif encode(binding.get('experimental_native_toolchain'))!=encode(native_toolchain.record()):
                raise p.Rejected('DRC caller-pinned toolchain binding differs')
            if field_policy is not None and '--schematic-parity' in process['argv'] and binding.get('field_local_settings_policy')!=field_policy:
                raise p.Rejected('normal parity field local-settings policy missing or changed')
            status,exit_code=process.get('status'),process.get('exit_code')
            if ((status=='success' and (type(exit_code) is not int or exit_code!=0))
                    or (status=='nonzero_exit' and (type(exit_code) is not int or exit_code==0))
                    or (exit_code is not None and type(exit_code) is not int)):
                raise p.Rejected('normal DRC worker status/exit pair differs')
            failed=process.get('status')!='success' and not (process.get('status')=='nonzero_exit' and process.get('exit_code')==5)
            if type(data.get('source_hashes')) is dict:
                p.check_drc_project(data['source_hashes'],binding['before'],Path(binding['input']).name,saved=True)
            check_event(cwd,binding,process,allow_worker_failure=failed)
            stages.append((cwd,binding,process,failed))
    if not stages:raise p.Rejected('normal DRC policy has no native workers')
    if census!=declared:raise p.Rejected('normal DRC retained worker population differs from steps')
    p.experimental_native_version(native_toolchain)
    # Repeat current flags after all process/journal/code and tool-pin reads.
    for cwd,binding,process,failed in stages:check_event(cwd,binding,process,allow_worker_failure=failed)
    return imports


def check_final_events(packets, cli, *, pairs=()):
    """Finish all field/journal reads before replaying every owned PRL event.

    Complete per-root lineage/census checks remain each caller's prerequisite.
    This composes their metadata guards without a later root's material read
    escaping an earlier root's last flag check. It authenticates no history.
    """
    from . import floor_route as f, schematic_field_evidence as fields
    pending = list(pairs)
    for folder, data in packets:
        if fields.has_fields(data.get('native', {}).get('findings', [])):
            fields.check_local_settings(folder, 'final-drc', f.read_json(Path(folder) / 'final-drc-binding.json'))
        for step in data.get('steps', []):
            argv = step.get('argv', [])
            if (argv[:3] == [str(cli), 'pcb', 'drc']
                    or argv[:len(f.SANDBOX) + 3] == [*f.SANDBOX, str(cli), 'pcb', 'drc']):
                root = Path(step['cwd']); name = step['name']
                binding = f.read_json(root / (name + '-binding.json'))
                process = f.process_check(root, data, name, argv, allowed=(0, 5))
                pending.append((root, binding, process))
    for root, binding, process in pending:
        check_event(root, binding, process)
