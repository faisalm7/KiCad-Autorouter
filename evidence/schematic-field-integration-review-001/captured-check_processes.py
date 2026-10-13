def check_processes(directory,data,stage,board,*,sandboxed):
    from . import pipeline as p,floor_route as f
    raw=f.read_json(Path(directory)/(stage+'.json'))
    findings=raw['violations']+raw['unconnected_items']+raw['schematic_parity']
    artifacts=paths(directory,stage)
    if not has_fields(findings):
        if any(x.exists() or x.is_symlink() for x in artifacts):raise p.Rejected('field proof without native field finding')
        return
    binding=f.read_json(Path(directory)/(stage+'-binding.json'))
    if binding.get('input')!=str(board):raise p.Rejected('effective-field process input differs from DRC binding')
    drc=[row for row in data.get('steps',[]) if row.get('name')==stage and row.get('cwd')==str(directory)]
    if len(drc)!=1 or '--schematic-parity' not in drc[0].get('argv',[]):
        raise p.Rejected('effective-field proof requires actual complete native schematic parity')
    if not all(x.exists() and not x.is_symlink() for x in artifacts):raise p.Rejected('native field finding requires complete effective-field proof')
    readback(Path(directory)/(stage+'.json'),raw)
    for name,argv in zip(names(stage),arguments(directory,stage,board)):
        f.process_check(Path(directory),data,name,[*(f.SANDBOX if sandboxed else []),*argv])
