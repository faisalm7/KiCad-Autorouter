"""Source-bound complete field observations for one native placeholder warning.

This does not edit or filter a DRC finding. KiCad stops at the first mismatched
field; a warning description alone cannot establish complete field agreement.
"""
from pathlib import Path
from . import config as c

TYPE='footprint_symbol_field_mismatch'
POLICY='datasheet-absence-only-v1'

def has_fields(findings):
    return any(isinstance(row,dict) and row.get('type')==TYPE for row in findings)

def names(stage):
    return (stage+'-fields-netlist',stage+'-fields-audit')

def paths(directory,stage):
    directory=Path(directory)
    return (directory/(stage+'-fields.net'),directory/(stage+'-fields.json'),directory/(stage+'-fields-proof.json'))

def arguments(directory,stage,board):
    netlist,fields,_=paths(directory,stage)
    return ([str(c.CLI),'sch','export','netlist','--format','kicadsexpr','--output',str(netlist),str(Path(board).with_suffix('.kicad_sch'))],
            [str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'fields',str(board),str(fields)])

def check_source_fields(schematic,board):
    from . import sexpr as sx
    mandatory={name.casefold():name for name in ('Reference','Value','Footprint','Datasheet','Description','Component Class')}
    for owner in sx.children(schematic,'symbol')+sx.children(board,'footprint'):
        keys=[sx.unquote(node[1]) for node in sx.children(owner,'property')]
        if len(keys)!=len(set(keys)):raise ValueError('duplicate source symbol or footprint field')
        if any(mandatory.get(name.casefold(),name)!=name for name in keys):
            raise ValueError('ambiguous source mandatory-field spelling')

def derive(directory,stage,raw):
    from . import pipeline as p,floor_route as f,schematic_fields as fields_policy,sexpr as sx
    from .placement_clearance import read_bytes
    netlist,fields,_=paths(directory,stage)
    binding=f.read_json(Path(directory)/(stage+'-binding.json'))
    board=Path(binding['input']);after=binding['after']
    if p.tree_hash(board.parent)!=after:raise p.Rejected('field observation project differs from native DRC input')
    observation=f.read_json(fields)
    expected={key:p.sha(board.with_suffix(suffix)) for key,suffix in (
        ('board_sha256','.kicad_pcb'),('project_sha256','.kicad_pro'),('schematic_sha256','.kicad_sch'))}
    if observation.get('source')!=str(board) or any(observation.get(k)!=v for k,v in expected.items()):
        raise p.Rejected('field observation is not bound to native DRC project')
    findings=raw['violations']+raw['unconnected_items']+raw['schematic_parity']
    try:
        schematic=sx.parse(read_bytes(board.with_suffix('.kicad_sch')).decode())
        # CLI and headless parity share the pinned exporter, but their loaders
        # differ. Initially qualify the observed flat legacy schema only.
        if schematic[0]!='kicad_sch' or sx.one(schematic,'version')!=['version','20250114'] or sx.children(schematic,'sheet'):
            raise ValueError('effective-field bridge is qualified only for flat schematic schema20250114')
        check_source_fields(schematic,sx.parse(read_bytes(board).decode()))
        qualification=fields_policy.derive(read_bytes(netlist).decode(),observation,raw)
    except ValueError as exc:
        qualification={'qualified':False,'reason':str(exc)}
    if p.tree_hash(board.parent)!=after:raise p.Rejected('field observation project changed during readback')
    return {'schema':1,'policy':POLICY,'native_report_sha256':p.sha(Path(directory)/(stage+'.json')),
        'binding_sha256':p.sha(Path(directory)/(stage+'-binding.json')),'netlist_sha256':p.sha(netlist),
        'fields_sha256':p.sha(fields),'qualification':qualification}

def collect(job,stage,board,raw):
    from . import pipeline as p
    before=p.tree_hash(board.parent)
    a,b=arguments(job.out,stage,board)
    job.step(names(stage)[0],a)
    job.step(names(stage)[1],b)
    if p.tree_hash(board.parent)!=before:raise p.Rejected('effective-field observation changed DRC project')
    proof=derive(job.out,stage,raw)
    p.save_json(paths(job.out,stage)[2],proof)

def readback(report,raw):
    from . import pipeline as p,floor_route as f
    report=Path(report);stage=report.stem
    _,_,proof=paths(report.parent,stage)
    if not proof.exists() and not proof.is_symlink():return None
    actual=derive(report.parent,stage,raw)
    if f.read_json(proof)!=actual:raise p.Rejected('effective-field proof differs from retained native observations')
    return actual

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

def qualified(native):
    """Only derived complete proofs qualify this particular warning family."""
    from . import schematic_fields
    proof=native.get('field_parity')
    return (isinstance(proof,dict) and proof.get('schema')==1 and proof.get('policy')==POLICY
            and schematic_fields.qualified(proof.get('qualification'),
                [row for row in native.get('findings',[]) if isinstance(row,dict) and row.get('type')==TYPE]))
