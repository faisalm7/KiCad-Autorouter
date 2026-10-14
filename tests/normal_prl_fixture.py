"""Synthetic receipt declarations for filesystem tests; NEVER Native evidence.

Only callers' owned TemporaryDirectory copies may be changed. This declares
what the fake worker fixture represents; it never runs Native or sets a flag.
"""
import copy,stat
from pathlib import Path
from autorouter import pipeline as p,floor_route as f,local_settings as ls

def mark_authored_receipt(directory,data,*,test_root):
    root=ls.canonical(Path(test_root));directory=ls.canonical(Path(directory))
    project=Path(__file__).resolve().parents[1]
    if (not any(base in root.parents for base in (project/'tests',project/'.cache'))
            or root not in directory.parents):
        raise AssertionError('PRL fixture helper requires one owned test TemporaryDirectory')
    source=ls.canonical(Path(data['source']))
    if root not in source.parents:raise AssertionError('PRL fixture source must be temporary too')
    policy=p.NORMAL_DRC_LOCAL_SETTINGS_POLICY
    if policy!=ls.JOB_POLICY:raise AssertionError('fixture must model the actual current normal policy')
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
    for binding_path,binding,process_path,process,step in updates:
        p.save_json(binding_path,binding);p.save_json(process_path,process)
        step['local_settings_policy']=policy;step['local_settings_protection']=copy.deepcopy(process['local_settings_protection'])
    return len(updates)
