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
        for owner in sx.children(schematic,'symbol')+sx.children(sx.parse(read_bytes(board).decode()),'footprint'):
            keys=[sx.unquote(node[1]) for node in sx.children(owner,'property')]
            if len(keys)!=len(set(keys)):raise ValueError('duplicate source symbol or footprint field')
        qualification=fields_policy.derive(read_bytes(netlist).decode(),observation,raw)
    except ValueError as exc:
        qualification={'qualified':False,'reason':str(exc)}
    if p.tree_hash(board.parent)!=after:raise p.Rejected('field observation project changed during readback')
    return {'schema':1,'policy':POLICY,'native_report_sha256':p.sha(Path(directory)/(stage+'.json')),
        'binding_sha256':p.sha(Path(directory)/(stage+'-binding.json')),'netlist_sha256':p.sha(netlist),
        'fields_sha256':p.sha(fields),'qualification':qualification}
