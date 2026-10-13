def check_pour_evidence(directory,data,original,candidate,*,source_hashes=None,correction=True,sandboxed=None):
    """Require saved-refill/native-fill proof from source intent, never a flag."""
    from . import pour_rule_area as pour, floor_route as f
    from .placement_clearance import read_bytes
    directory=Path(directory);candidate=Path(candidate);areas=pour.qualify(original)
    names=('pour-before-refill.kicad_pcb','pour-keepout-audit.json','pour-dsn-correction.json','pour-corrected.dsn')
    if not areas:
        if any((directory/n).exists() or (directory/n).is_symlink() for n in names):raise Rejected('pour evidence without qualified source intent')
        return
    if sandboxed is None:sandboxed=data.get('input_policy') in {'board-floors-v1','placement-clearance-v1','placement-search-v1','placement-pruning-v1'}
    prefix=f.SANDBOX if sandboxed else []
    audit=f.read_json(directory/'pour-keepout-audit.json')
    try:pour.verify_native_record(audit,candidate)
    except ValueError as exc:raise Rejected(str(exc)) from exc
    f.process_check(directory,data,'pour-keepout-audit',[*prefix,str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'pour-audit',str(candidate),str(directory/'pour-keepout-audit.json')])
    before_path=directory/'pour-before-refill.kicad_pcb';before=sx.parse(read_bytes(before_path).decode())
    if immutable(before)!=immutable(original) or routes(before)!=routes(sx.read(candidate)):raise Rejected('pour refill changed original geometry/routing')
    hashes=dict(source_hashes if source_hashes is not None else data['source_hashes']);hashes[candidate.name]=sha(before_path)
    refill=directory/'refill'/candidate.name
    f.check_drc_stage(directory,data,'refill-drc',refill,refill,True,hashes,sandboxed=sandboxed)
    if (sx.dump(transplant_fill(before,sx.read(refill)))+'\n').encode()!=read_bytes(candidate):raise Rejected('pour saved-refill reconstruction differs')
    if not correction:return
    engine=[s for s in data.get('steps',[]) if s.get('name')=='engine' and s.get('cwd')==str(directory)]
    if not engine:
        if data.get('baseline')!='C-prototype':raise Rejected('pour correction requires original native engine lineage')
        check_result(directory/'incumbent/result.json')
        return
    if len(engine)!=1:raise Rejected('ambiguous pour correction engine lineage')
    if data.get('adapter')=='none':
        if ('pour_dsn_correction' in data or 'adapter_transformations' in data
                or any((directory/n).exists() or (directory/n).is_symlink() for n in names[2:])):
            raise Rejected('stock workflow cannot claim pour adapter correction')
        input_path=directory/('routing-scope-input.dsn' if data.get('scope')=='selected_nets' else 'task.dsn')
        if read_bytes(input_path)!=read_bytes(directory/'native.dsn'):raise Rejected('stock pour workflow raw engine input differs')
        return
    source_bytes=read_bytes(directory/'snapshot'/candidate.name)
    corrected,record=pour.correct(source_bytes,read_bytes(directory/'native.dsn'))
    if (f.canonical(data.get('pour_dsn_correction'))!=f.canonical(record)
            or f.canonical(f.read_json(directory/'pour-dsn-correction.json'))!=f.canonical(record)
            or read_bytes(directory/'pour-corrected.dsn')!=corrected
            or data.get('adapter_transformations',{}).get('input_sha256')!=pour.sha(corrected)):
        raise Rejected('missing/downgraded pour DSN correction lineage')
    from .adapter import adapt_bytes
    adapted,adapter_record=adapt_bytes(corrected,data['adapter'],f.read_json(directory/'obstacles.json'))
    engine_input=directory/('routing-scope-input.dsn' if data.get('scope')=='selected_nets' else 'task.dsn')
    if read_bytes(engine_input)!=adapted or f.canonical(data.get('adapter_transformations'))!=f.canonical(adapter_record):
        raise Rejected('pour corrected-to-adapter engine input differs')
