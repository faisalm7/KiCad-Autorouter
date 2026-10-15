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

def project_board_only_fields(board,raw_netlist,observation,report):
    """Project only source-proved non-electrical artwork from field comparison.

    The complete original observation remains in fields.json and is hash-bound.
    This does not remove findings, alter the source, or qualify routed geometry.
    Ordinary component/footprint mismatches still use the strict field policy.
    """
    import copy
    from . import sexpr as sx,schematic_fields as fields
    sch=fields.components(raw_netlist,observation)
    rows=observation.get('footprints')
    if type(rows) is not list:raise ValueError('complete field footprint census required')
    extra=[row for row in rows if isinstance(row,dict) and row.get('reference') not in sch]
    fps=sx.children(board,'footprint')
    if not 1<=len(fps)<=10000 or len(fps)!=len(rows):raise ValueError('bounded complete source/Native footprint census required')
    source={};native={};references=set()
    for fp in fps:
        uid=fields.singleton(fp,'uuid')
        properties=sx.children(fp,'property')
        refs=[n for n in properties if len(n)>2 and sx.unquote(n[1])=='Reference']
        if len(refs)!=1 or fields.UUID.fullmatch(uid) is None or uid in source:raise ValueError('unambiguous source footprint identity required')
        ref=fields.atom(refs[0][2])
        if not ref or ref.casefold() in references:raise ValueError('unique source footprint references required')
        references.add(ref.casefold());source[uid]=(ref,fp)
    for row in rows:
        if (type(row) is not dict or set(row)!={'reference','uuid','fields'}
                or type(row['reference']) is not str or type(row['uuid']) is not str
                or type(row['fields']) is not dict or any(type(k) is not str or not k or type(v) is not str for k,v in row['fields'].items())
                or row['uuid'] in native or row['uuid'] not in source or source[row['uuid']][0]!=row['reference']):
            raise ValueError('complete source/Native field census differs')
        native[row['uuid']]=row
    if set(native)!=set(source):raise ValueError('source/Native footprint census incomplete')
    if not extra:return observation,None
    if len(fps)>512:raise ValueError('board-only field partition exceeds qualified footprint scope')
    excluded=[]
    for row in extra:
        ref,fp=source[row['uuid']]
        attrs=sx.one(fp,'attr',[])[1:]
        allowed={'layer','uuid','at','property','attr','fp_poly','fp_text','fp_text_box','fp_line','fp_arc','fp_circle','fp_rect','descr','tags','embedded_fonts'}
        if ('board_only' not in attrs or len(attrs)!=len(set(attrs)) or set(attrs)-{'board_only','exclude_from_pos_files','exclude_from_bom'}
                or any(not isinstance(n,list) or not n or n[0] not in allowed for n in fp[2:])):
            raise ValueError('unmatched footprint is outside padless board-only artwork scope')
        source_fields={};field_names=set()
        for node in sx.children(fp,'property'):
            if len(node)<3:raise ValueError('malformed board-only field')
            name=fields.atom(node[1]);value=fields.atom(node[2])
            if name in field_names:raise ValueError('duplicate board-only field')
            field_names.add(name)
            if name not in fields.SKIP:source_fields[name]=value
        if source_fields!=row['fields']:raise ValueError('board-only source/Native fields differ')
        # The container is placed on a copper side, but every actual artwork
        # and property surface must be non-electrical. No pads, models, zones,
        # schematic paths, net ties, rules or unknown footprint children pass.
        for node in fp[2:]:
            if node[0]=='property' or node[0].startswith('fp_'):
                layer=sx.one(node,'layer')
                if (layer is None or len(layer)!=2 or sx.unquote(layer[1]) not in {'F.SilkS','B.SilkS','F.Fab','B.Fab'}):
                    raise ValueError('board-only field artwork surface is unqualified')
        from .padless_alias import surfaces
        surfaces(fp)
        if any(any(item.get('uuid')==row['uuid'] for item in finding.get('items',[]) if isinstance(item,dict))
                for finding in report.get('schematic_parity',[]) if isinstance(finding,dict)):
            raise ValueError('board-only artwork has a schematic parity finding')
        excluded.append({'reference':ref,'uuid':row['uuid'],'footprint_ast_sha256':fields.digest((sx.dump(fp)+'\n').encode()),'pad_count':0,'board_only':True})
    projected=copy.deepcopy(observation)
    identities={r['uuid'] for r in excluded}
    projected['footprints']=[r for r in projected['footprints'] if r['uuid'] not in identities]
    return projected,{'policy':'source-bound-padless-field-census-v1','complete_footprint_count':len(rows),
        'compared_footprint_count':len(projected['footprints']),'artwork':sorted(excluded,key=lambda r:r['uuid']),
        'complete_observer_sha256':fields.digest(fields.canonical(observation)),
        'projected_observer_sha256':fields.digest(fields.canonical(projected))}


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
    artwork=None
    try:
        schematic=sx.parse(read_bytes(board.with_suffix('.kicad_sch')).decode())
        # CLI and headless parity share the pinned exporter, but their loaders
        # differ. Initially qualify the observed flat legacy schema only.
        if schematic[0]!='kicad_sch' or sx.one(schematic,'version')!=['version','20250114'] or sx.children(schematic,'sheet'):
            raise ValueError('effective-field bridge is qualified only for flat schematic schema20250114')
        source_board=sx.parse(read_bytes(board).decode())
        check_source_fields(schematic,source_board)
        netlist_text=read_bytes(netlist).decode()
        projected,artwork=project_board_only_fields(source_board,netlist_text,observation,raw)
        qualification=fields_policy.derive(netlist_text,projected,raw)
    except ValueError as exc:
        qualification={'qualified':False,'reason':str(exc)}
    if p.tree_hash(board.parent)!=after:raise p.Rejected('field observation project changed during readback')
    proof={'schema':1,'policy':POLICY,'native_report_sha256':p.sha(Path(directory)/(stage+'.json')),
        'binding_sha256':p.sha(Path(directory)/(stage+'-binding.json')),'netlist_sha256':p.sha(netlist),
        'fields_sha256':p.sha(fields),'qualification':qualification}
    if artwork is not None:proof['board_only_field_census']=artwork
    return proof

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

def check_availability(directory,stage,process,raw,*,required=False):
    """A requested native check is unavailable unless its completion is proved."""
    from . import pipeline as p,placement_clearance as pc
    import re
    if '--schematic-parity' not in process.get('argv',[]):
        if required:raise p.Rejected('requested native schematic parity flag missing from process')
        return
    path=Path(directory)/(stage+'.log')
    if (process.get('log')!=str(path) or process.get('log_truncated') is not False
            or type(process.get('log_bytes')) is not int):
        raise p.Rejected('native schematic parity availability log binding missing')
    log=pc.read_bytes(path,2*1024**2)
    if len(log)!=process['log_bytes']:
        raise p.Rejected('native schematic parity availability log size differs')
    if (b'Failed to fetch schematic netlist for parity tests.' in log
            or b'Schematic parity tests require a fully annotated schematic.' in log):
        raise p.Rejected('native schematic parity was skipped or unavailable')
    counts=re.findall(rb'^Found ([0-9]+) schematic parity issues\r?$',log,re.MULTILINE)
    if counts!=[str(len(raw['schematic_parity'])).encode()]:
        raise p.Rejected('native schematic parity completion missing or differs from report')

def check_processes(directory,data,stage,board,*,sandboxed):
    from . import pipeline as p,floor_route as f
    raw=f.read_json(Path(directory)/(stage+'.json'))
    drc=[row for row in data.get('steps',[]) if row.get('name')==stage and row.get('cwd')==str(directory)]
    if len(drc)==1:check_availability(directory,stage,drc[0],raw)
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
