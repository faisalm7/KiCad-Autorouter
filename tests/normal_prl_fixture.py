"""Synthetic receipt declarations for filesystem tests; NEVER Native evidence.

Only callers' owned TemporaryDirectory copies may be changed. This declares
what the fake worker fixture represents; it never runs Native or sets a flag.
"""
import copy,stat,shutil
from pathlib import Path
from autorouter import pipeline as p,floor_route as f,local_settings as ls,adapter,sexpr as sx

def _authored_normal_import(directory,data):
    """Complete an explicitly opted-in software fixture, never Native evidence."""
    if (data.get('schema')!=1 or data.get('input_policy','native')!='native' or 'strategy' in data
            or any(step.get('name')=='import' for step in data['steps'])):
        raise AssertionError('authored normal transport requires a direct fixture without an import')
    source=Path(data['source']);candidate=Path(data['candidate']);original=sx.read(source)
    if candidate!=directory/'candidate'/source.name:raise AssertionError('authored normal candidate must be owned')
    imported=directory/'imported.kicad_pcb';shutil.copy2(candidate,imported)
    names=p.selected_scope_names(data);protection=p.protected_for_record(data,original)
    policy=p.normal_selected_import_policy(original,names) if names is not None else 'exact_non_uuid_lock_position_v2'
    audit={'imported_sha256':p.sha(imported)}
    rebuilt=p.transplant_routes(original,sx.read(imported),protected=protection,audit=audit,policy=policy,
        **({'selected_names':names} if policy==p.SELECTED_PROPOSAL_IMPORT_POLICY else {}))
    if p.routes(rebuilt)!=p.routes(sx.read(candidate)):raise AssertionError('authored normal candidate disagrees with import')
    shutil.copy2(candidate,directory/'pre-refill.kicad_pcb')
    data['protected_route_import']=audit
    worker={'name':'import','cwd':str(directory),'status':'success','exit_code':0,'cleanup_complete':True,
            'wall_seconds':0,'cpu_seconds':0,'monitor_cpu_seconds':0,
            'argv':[str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py'),'import',str(candidate),str(imported),str(directory/'routes.ses')]}
    p.save_json(directory/'import-process.json',worker);data['steps'].append(copy.deepcopy(worker))
    # A zero-change, explicitly synthetic saved-refill stage for semantic route
    # comparison. Original Native report fixtures remain synthetic, not rerun.
    refill=directory/'refill';shutil.copytree(candidate.parent,refill)
    inputs=p.tree_hash(refill);target=refill/source.name;name='refill-drc'
    shutil.copy2(directory/'final-drc.json',directory/(name+'.json'))
    binding={'source':str(target),'input':str(target),'saved':True,'before':inputs,'after':inputs}
    p.save_json(directory/(name+'-binding.json'),binding)
    worker={'name':name,'cwd':str(directory),'status':'success','exit_code':0,'cleanup_complete':True,
            'wall_seconds':0,'cpu_seconds':0,'monitor_cpu_seconds':0,
            'argv':[str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones',
                    '--exit-code-violations','--output',str(directory/(name+'.json')),'--save-board',str(target)]}
    p.save_json(directory/(name+'-process.json'),worker)
    data['steps'].append(dict(worker,validated_input_sha256=inputs[source.name],emitted_candidate=str(target)))


def _owned_fixture_paths(directory,data,test_root):
    root=ls.canonical(Path(test_root));directory=ls.canonical(Path(directory))
    project=Path(__file__).resolve().parents[1]
    if (not any(base in root.parents for base in (project/'tests',project/'.cache'))
            or root not in directory.parents):
        raise AssertionError('PRL fixture helper requires one owned test TemporaryDirectory')
    source=ls.canonical(Path(data['source']))
    if root not in source.parents:raise AssertionError('PRL fixture source must be temporary too')
    return root,directory


def refresh_authored_normal_import(directory,data,*,test_root):
    """Explicit setup-only rebuild after intentional synthetic source changes.

    Callers first update their source/candidate/final-input copies, source hashes
    and final DRC binding/step. Never call from a reader or after a tested fault.
    Only the existing zero-cost direct authored transport may be replaced.
    """
    _,directory=_owned_fixture_paths(directory,data,test_root)
    stages=[step for step in data['steps'] if step.get('cwd')==str(directory)
            and step.get('name') in {'import','refill-drc'}]
    if (len(stages)!=2 or {step['name'] for step in stages}!={'import','refill-drc'}
            or any(step.get('wall_seconds')!=0 or step.get('cpu_seconds')!=0
                   or step.get('monitor_cpu_seconds')!=0 or step.get('status')!='success'
                   or step.get('exit_code')!=0 or step.get('cleanup_complete') is not True for step in stages)):
        raise AssertionError('refresh requires the existing zero-cost authored direct transport')
    refill=ls.canonical(directory/'refill')
    from autorouter.placement_clearance import inventory
    inventory(refill)  # Refuse aliases/special files before deleting owned test copies.
    shutil.rmtree(refill)
    for name in ('imported.kicad_pcb','pre-refill.kicad_pcb','import-process.json',
                 'routes.ses','imported.routes-only.ses','imported.routes-only.json',
                 'refill-drc.json','refill-drc-binding.json','refill-drc-process.json'):
        path=ls.canonical(directory/name)
        if not path.is_file() or path.is_symlink():raise AssertionError('authored transport file missing or aliased')
        path.unlink()
    data['steps']=[step for step in data['steps'] if step not in stages]
    _authored_normal_import(directory,data)
    return mark_authored_receipt(directory,data,test_root=test_root,fixed_imports=True)


def mark_authored_receipt(directory,data,*,test_root,fixed_imports=False,normal_imports=False):
    root,directory=_owned_fixture_paths(directory,data,test_root)
    policy=p.NORMAL_DRC_LOCAL_SETTINGS_POLICY
    if policy!=ls.JOB_POLICY:raise AssertionError('fixture must model the actual current normal policy')
    if normal_imports:
        _authored_normal_import(directory,data);fixed_imports=True
    updates=[]
    for step in data['steps']:
        argv=step.get('argv');offset=len(f.SANDBOX) if type(argv) is list and argv[:len(f.SANDBOX)]==f.SANDBOX else 0
        if type(argv) is not list or argv[offset:offset+3]!=[str(p.c.CLI),'pcb','drc']:continue
        folder=ls.canonical(Path(step['cwd']));board=ls.canonical(Path(argv[-1]))
        if root not in folder.parents or folder not in board.parents:raise AssertionError('DRC fixture input outside owned worker root')
        name=step['name']
        if type(name) is not str or name in ('','.','..') or '/' in name or chr(92) in name:raise AssertionError('unsafe DRC fixture stage')
        binding_path=folder/(name+'-binding.json');process_path=folder/(name+'-process.json')
        binding=f.read_json(binding_path);process=f.read_json(process_path)
        if (binding['input']!=str(board) or process['argv']!=argv or process['name']!=name
                or process['cwd']!=str(folder) or process['cleanup_complete'] is not True
                or process['status'] not in ('success','nonzero_exit') or process['exit_code'] not in (0,5)):
            raise AssertionError('authored fixture must already bind a complete successful DRC worker')
        prl=board.with_suffix('.kicad_prl');before=binding['before']
        if prl.exists():
            ls.canonical(prl);info=prl.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or getattr(info,'st_flags',0)!=0:raise AssertionError('ordinary unflagged owned fixture PRL required')
        if prl.name in before:
            if not prl.exists() or p.sha(prl)!=before[prl.name]:raise AssertionError('fixture PRL does not match declared before bytes')
            event={'policy':ls.POLICY,'present':True,'path':str(prl),'sha256':before[prl.name],
                   'flags_before':0,'flags_during':stat.UF_IMMUTABLE,'flags_restored':True,'bytes_unchanged':True}
        else:event={'policy':ls.POLICY,'present':False}
        # flags_during/restored are synthetic worker declarations, not measured
        # OS observations. The enclosing test files explicitly state that scope.
        binding['local_settings_policy']=policy;process['local_settings_policy']=policy
        process['local_settings_protection']=event
        updates.append((binding_path,binding,process_path,process,step))
    if not updates:raise AssertionError('no authored DRC stages to declare')
    data['tools']['normal_drc_local_settings_policy']=policy
    data['tools']['normal_selected_proposal_import_policy']=p.NORMAL_SELECTED_PROPOSAL_IMPORT_POLICY
    for binding_path,binding,process_path,process,step in updates:
        p.save_json(binding_path,binding);p.save_json(process_path,process)
        step['local_settings_policy']=policy;step['local_settings_protection']=copy.deepcopy(process['local_settings_protection'])
    if fixed_imports:
        # Explicitly authored SES syntax/process metadata for current-code
        # receipt tests. No claim that these bytes produced the fixture board.
        for step in data['steps']:
            argv=step.get('argv');args=argv[len(f.SANDBOX):] if type(argv) is list and argv[:len(f.SANDBOX)]==f.SANDBOX else argv
            if type(args) is not list or args[:3]!=[str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py'),'import']:continue
            if len(args)!=6:raise AssertionError('authored import command must have source/output/session')
            folder=ls.canonical(Path(step['cwd']));board,output,session=(ls.canonical(Path(n))for n in args[3:])
            if (root not in folder.parents or output.parent!=folder
                    or any(root not in n.parents for n in (board,output,session))
                    or not board.is_file() or not output.is_file()):raise AssertionError('authored import input/output must exist in owned test root')
            process=f.read_json(folder/(step['name']+'-process.json'))
            if (process.get('argv')!=argv or process.get('name')!=step['name']
                    or process.get('cwd')!=str(folder) or process.get('status')!='success'
                    or type(process.get('exit_code'))is not int or process['exit_code']!=0
                    or process.get('cleanup_complete')is not True):raise AssertionError('authored import worker must be complete')
            from tests.test_fixed_placement_session import fixture,encode
            session.write_bytes(encode(fixture()))
            filtered,proof=adapter.fixed_placement_session(session.read_bytes());derived=output.with_suffix('.routes-only.ses')
            derived.write_bytes(filtered)
            proof.update(source_session=str(session),import_session=str(derived),imported_board_sha256=p.sha(output))
            p.save_json(derived.with_suffix('.json'),proof)
    return len(updates)
