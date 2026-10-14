# Earlier reviewed function body projected by removing only newly added machining guard calls.
def validate_candidate(job, original, candidate, source_hashes, protected, *, guidance_contract=None, guidance_basis=None, layer_contract=None, selected_names=None, schematic_parity=False):
    schematic_parity = schematic_parity or Path(candidate).with_suffix('.kicad_sch').name in source_hashes
    check_rule_area_support(original)
    if guidance_basis is not None and guidance_contract is None:
        raise Rejected('guidance basis requires a contract')
    if guidance_contract is not None:
        from .floor_route import validate_contract
        validate_contract(original, candidate, source_hashes, protected, guidance_contract, job.out, guidance_basis=guidance_basis)
    if immutable(sx.read(candidate)) != immutable(original):
        raise Rejected('immutable geometry changed')
    if any((n not in routes(sx.read(candidate)) for n in protected)):
        raise Rejected('protected route changed')
    if selected_names is not None:
        from . import routing_scope as rs
        rs.audit(original, sx.read(candidate), selected_names)
    if layer_contract is not None:
        layer_contract['audit'] = audit_layer_contract(candidate, layer_contract)
    verify_candidate_files(candidate, source_hashes)
    from . import pour_rule_area as pour
    pour_areas = pour.qualify(original)
    if pour_areas:
        before_refill = job.out / 'pour-before-refill.kicad_pcb'
        with before_refill.open('xb') as stream:
            stream.write(candidate.read_bytes())
    shutil.copytree(candidate.parent, job.out / 'refill')
    refill = job.out / 'refill' / candidate.name
    job.drc('refill-drc', refill, save=True)
    sx.write(candidate, transplant_fill(sx.read(candidate), sx.read(refill)))
    if immutable(sx.read(candidate)) != immutable(original):
        raise Rejected('immutable geometry changed after refill')
    if layer_contract is not None:
        layer_contract['audit'] = audit_layer_contract(candidate, layer_contract)
    final_hash = sha(candidate)
    if pour_areas:
        job.native('pour-keepout-audit', 'pour-audit', candidate, job.out / 'pour-keepout-audit.json')
        pour.verify_native_record(json.loads((job.out / 'pour-keepout-audit.json').read_text()), candidate)
    if guidance_contract is not None:
        from .floor_route import final_context
        final_context(job, original, candidate, source_hashes, protected, guidance_contract, guidance_basis=guidance_basis)
    elif netclass_policy(candidate) is not None:
        mapping = job.out / 'final-netclasses.json'
        job.native('final-netclasses', 'netclasses', candidate, mapping)
        audited = audit_candidate_netclasses(candidate, protected, json.loads(mapping.read_text()))
        audited['native_map_file_sha256'] = sha(mapping)
        save_json(job.out / 'final-netclass-audit.json', audited)
    if selected_names is not None:
        rs.audit(original, sx.read(candidate), selected_names)
    native = job.drc('final-drc', candidate, schematic_parity=True) if schematic_parity else job.drc('final-drc', candidate)
    verify_candidate_files(candidate, source_hashes, final_hash)
    return (final_hash, native)
