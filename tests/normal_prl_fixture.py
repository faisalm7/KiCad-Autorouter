"""Synthetic receipt declarations for filesystem tests; NEVER Native evidence.

Only callers' owned TemporaryDirectory copies may be changed. This declares
what the fake worker fixture represents; it never runs Native or sets a flag.
"""
import copy,stat
from pathlib import Path
from autorouter import pipeline as p,floor_route as f,local_settings as ls,adapter,sexpr as sx

def mark_authored_receipt(directory,data,*,test_root,fixed_imports=False):
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
            authored=['session','"authored-receipt.ses"',['base_design','"authored-receipt.dsn"'],
                      ['placement',['resolution','um','10']],['was_is'],
                      ['routes',['resolution','um','10'],['library_out'],['network_out']]]
            session.write_bytes((sx.dump(authored)+'\n').encode())
            filtered,proof=adapter.fixed_placement_session(session.read_bytes());derived=output.with_suffix('.routes-only.ses')
            derived.write_bytes(filtered)
            proof.update(source_session=str(session),import_session=str(derived),imported_board_sha256=p.sha(output))
            p.save_json(derived.with_suffix('.json'),proof)
    return len(updates)
