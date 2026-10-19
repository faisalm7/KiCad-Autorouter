from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'autorouter/pipeline.py'; text=p.read_text()
def replace(old,new):
 global text
 assert text.count(old)==1,(old[:100],text.count(old));text=text.replace(old,new)
replace("ENGINE_GLOBAL_WIDTH_POLICY='original-global-minimum-width-v1'", "ENGINE_GLOBAL_WIDTH_POLICY='original-global-minimum-width-v1'\nDEFAULT_TARGET_ADMISSION_POLICY='single-default-global-floor-targets-v1'")
replace('def audit_candidate_netclasses(candidate, protected, native, *, native_toolchain=None):','def audit_candidate_netclasses(candidate, protected, native, *, native_toolchain=None, default_target_policy=False):')
replace("    mapping=audit_native(native,json.loads(project.read_text()),parent_policy=policy is not None and policy['mode']==PARENT_POLICY,native_toolchain=native_toolchain)\n    dimensions=audit_route_dimensions(source_tree,protected,native)\n    return {'native':mapping,'route_dimensions':dimensions,'candidate_sha256':sha(candidate),\n            'project_sha256':sha(project)}", """    if type(default_target_policy) is not bool:
        raise Rejected('explicit Default target audit flag required')
    if default_target_policy and not normal_default_target_scope(candidate,'both',native_toolchain=native_toolchain):
        raise Rejected('derived Default candidate audit outside normal selected7 scope')
    mapping=audit_native(native,json.loads(project.read_text()),parent_policy=policy is not None and policy['mode']==PARENT_POLICY,
        native_toolchain=native_toolchain,derive_default_targets=default_target_policy)
    effective=native
    if default_target_policy:
        from . import default_targets as targets
        targets._parents(native,json.loads(project.read_text())['net_settings']['classes'][0])
        derived=targets.source_dimensions(project.read_bytes())
        effective=copy.deepcopy(native)
        for row in effective['nets']:row.update(derived['derived_nm'])
    dimensions=audit_route_dimensions(source_tree,protected,effective)
    result={'native':mapping,'route_dimensions':dimensions,'candidate_sha256':sha(candidate),
            'project_sha256':sha(project)}
    if default_target_policy:result['default_targets']={'policy':DEFAULT_TARGET_ADMISSION_POLICY,**derived}
    return result


def normal_default_target_scope(board,adapter,*,native_toolchain=None):
    \"\"\"Corrected ordinary selected7 uses one source-derived Default policy.\"\"\"
    return (native_toolchain is None and c.NATIVE_VERSION=='10.0.7' and adapter=='both'
        and netclass_policy(board) is None)


def check_default_target_transport(directory,data,original,candidate,*,input_policy='native',native_toolchain=None):
    \"\"\"Require the new producer's exact lawful edit even after marker deletion.

    Retained old producers keep their historical scope. Captured code is checked,
    never executed. The normal engine/native/source/PRL readers remain mandatory.
    \"\"\"
    from . import default_targets as targets, floor_route as f
    from .placement_clearance import read_bytes
    from .local_settings import policy_declaration
    directory=Path(directory);candidate=Path(candidate)
    names=('default-targets.json','default-targets.dsn')
    marked=('default_target_transport' in data or any((directory/name).exists()
        or (directory/name).is_symlink() for name in names))
    producer=directory/'code/pipeline.py'
    if not producer.exists() and not producer.is_symlink():
        if marked:raise Rejected('Default target transport has no captured producer')
        return None
    raw_code=read_bytes(producer,1024**2)
    if hashlib.sha256(raw_code).hexdigest()!=data.get('tools',{}).get('implementation_sha256',{}).get('autorouter/pipeline.py'):
        raise Rejected('Default target captured producer differs')
    declared=policy_declaration(raw_code,name='DEFAULT_TARGET_ADMISSION_POLICY',expected=DEFAULT_TARGET_ADMISSION_POLICY)
    required=(declared is not None and input_policy=='native' and data.get('strategy') is None
        and data.get('scope') in {'whole_board_unlocked_routing','partial_completion'}
        and normal_default_target_scope(candidate,data.get('adapter'),native_toolchain=native_toolchain))
    if not required:
        if marked:raise Rejected('Default target transport outside declared producer scope')
        return None
    if targets.POLICY!=declared or selected_scope_markers(directory,data) or layer_markers(directory,data):
        raise Rejected('Default target transport requires ordinary source-all scope')
    snapshot=directory/'snapshot'/candidate.name
    if tree_hash(snapshot.parent)!=data['source_hashes']:
        raise Rejected('Default target original snapshot changed')
    task_raw=(sx.dump(routing_task(original,data['scope']))+'\\n').encode()
    if hashlib.sha256(task_raw).hexdigest()!=data.get('task_sha256'):
        raise Rejected('Default target original task differs')
    mapping=f.read_json(directory/'export-netclasses.json')
    expected,record=targets.transform(read_bytes(directory/'native.dsn',20*1024**2),mapping,
        read_bytes(snapshot.with_suffix('.kicad_pro')),task_raw,source=str(candidate))
    proof=directory/'default-targets.json'
    binding={'policy':declared,'file':proof.name,'sha256':sha(proof)}
    if (f.canonical(data.get('default_target_transport'))!=f.canonical(binding)
            or f.canonical(f.read_json(proof))!=f.canonical(record)
            or read_bytes(directory/'default-targets.dsn',20*1024**2)!=expected):
        raise Rejected('Default target required edit, source or receipt differs')
    f.process_check(directory,data,'export',[*native_prefix(),'export',str(candidate),str(directory/'task.dsn'),
        str(directory/'export-netclasses.json'),'--task-copper-fixed'])
    return record""")
replace('def validate_candidate(job, original, candidate, source_hashes, protected, *, guidance_contract=None, guidance_basis=None, layer_contract=None, selected_names=None, schematic_parity=False, class_context=None):','def validate_candidate(job, original, candidate, source_hashes, protected, *, guidance_contract=None, guidance_basis=None, layer_contract=None, selected_names=None, schematic_parity=False, class_context=None, default_target_policy=False):')
replace('    # A complete captured native schematic must participate in final acceptance', "    if type(default_target_policy) is not bool:raise Rejected('explicit Default target validation flag required')\n    # A complete captured native schematic must participate in final acceptance")
replace('    elif netclass_policy(candidate) is not None or getattr(job,"native_toolchain",None) is not None or class_requirement is not None:', '    elif netclass_policy(candidate) is not None or getattr(job,"native_toolchain",None) is not None or class_requirement is not None or default_target_policy:')
replace('        if netclass_policy(candidate) is not None or getattr(job,"native_toolchain",None) is not None:\n            audited=audit_candidate_netclasses(candidate,protected,json.loads(mapping.read_text()),native_toolchain=getattr(job,"native_toolchain",None))', '        if netclass_policy(candidate) is not None or getattr(job,"native_toolchain",None) is not None or default_target_policy:\n            audited=audit_candidate_netclasses(candidate,protected,json.loads(mapping.read_text()),native_toolchain=getattr(job,"native_toolchain",None),default_target_policy=default_target_policy)')
replace("            # Default-only hierarchy still needs Native identity observations.\n            # It has no composite dimension-target audit: unchanged global rule\n            # floors and final Native DRC retain their independent authority.\n            mapping_args=[output/'export-netclasses.json'] if class_requirement is not None else []", "            # Keep raw class identity, then derive lawful routing targets from\n            # unchanged Default values and hard original board minima.\n            mapping_args=[output/'export-netclasses.json'] if class_requirement is not None or normal_default_target_scope(candidate,adapter) else []")
replace("        report['native_dsn_sha256']=sha(output/'native.dsn')\n        if adapter!='none':", """        report['native_dsn_sha256']=sha(output/'native.dsn')
        default_targets=normal_default_target_scope(candidate,adapter,native_toolchain=native_toolchain)
        if default_targets:
            from . import default_targets as targets
            guided,derivation=targets.transform((output/'native.dsn').read_bytes(),
                json.loads((output/'export-netclasses.json').read_text()),candidate.with_suffix('.kicad_pro').read_bytes(),
                candidate.read_bytes(),source=str(candidate))
            (output/'default-targets.dsn').write_bytes(guided)
            save_json(output/'default-targets.json',derivation)
            report['default_target_transport']={'policy':DEFAULT_TARGET_ADMISSION_POLICY,'file':'default-targets.json',
                'sha256':sha(output/'default-targets.json')}
            (output/'task.dsn').write_bytes(guided)
        if adapter!='none':""")
replace("                corrected,correction=pour.correct(snapshot.read_bytes(),(output/'native.dsn').read_bytes())", "                corrected,correction=pour.correct(snapshot.read_bytes(),(output/'task.dsn').read_bytes())")
replace('strict_class_targets=policy is not None or selected is not None or width_guard is not None,scoring_variant=scoring_variant', 'strict_class_targets=policy is not None or selected is not None or width_guard is not None or default_targets,scoring_variant=scoring_variant')
replace('final_hash, native = validate_candidate(job, original, candidate, before, protected,layer_contract=layers,class_context=class_context,**extra)', 'final_hash, native = validate_candidate(job, original, candidate, before, protected,layer_contract=layers,class_context=class_context,default_target_policy=default_targets,**extra)')
replace("    corrected,record=pour.correct(source_bytes,read_bytes(directory/'native.dsn'))", "    corrected,record=pour.correct(source_bytes,read_bytes(directory/('default-targets.dsn' if 'default_target_transport' in data else 'native.dsn')))")
replace("        base=read_bytes(directory/('pour-corrected.dsn' if 'pour_dsn_correction' in data else 'native.dsn'))", "        base=read_bytes(directory/('pour-corrected.dsn' if 'pour_dsn_correction' in data else 'default-targets.dsn' if 'default_target_transport' in data else 'native.dsn'))")
replace("strict_class_targets=data.get('netclass_policy') is not None or data.get('scope')=='selected_nets' or width is not None,", "strict_class_targets=data.get('netclass_policy') is not None or data.get('scope')=='selected_nets' or width is not None or 'default_target_transport' in data,")
replace("strict_class_targets=effective['guidance']!='native' or data.get('netclass_policy') is not None or effective['scope']=='selected_nets' or width_guard is not None,", "strict_class_targets=effective['guidance']!='native' or data.get('netclass_policy') is not None or effective['scope']=='selected_nets' or width_guard is not None or 'default_target_transport' in data,")
replace("    from . import (adapter,board_floor,engine_angle,floor_context", "    from . import (adapter,board_floor,default_targets,engine_angle,floor_context")
replace("    modules=(sys.modules[__name__],c,sx,adapter,board_floor,engine_angle,floor_context,", "    modules=(sys.modules[__name__],c,sx,adapter,board_floor,default_targets,engine_angle,floor_context,")
# Before normal class checks, rederive from captured producer/snapshot independently of receipt markers.
replace("    if netclass_policy(candidate) is not None or native_toolchain is not None:\n        from .netclass import audit_dsn, audit_native, PARENT_POLICY", "    default_target_contract=check_default_target_transport(path.parent,data,original,candidate,input_policy=input_policy,native_toolchain=native_toolchain)\n    if netclass_policy(candidate) is not None or native_toolchain is not None or default_target_contract is not None:\n        from .netclass import audit_dsn, audit_native, PARENT_POLICY")
replace("        audited=audit_candidate_netclasses(candidate,protected,native_classes,native_toolchain=native_toolchain)\n        audited['native_map_file_sha256']", "        audited=audit_candidate_netclasses(candidate,protected,native_classes,native_toolchain=native_toolchain,default_target_policy=default_target_contract is not None)\n        audited['native_map_file_sha256']")
# Composite audit branch remains exact raw equality. Default path was fully reconstructed above.
replace("        if data.get('baseline')!='C-prototype':\n            # Reconstruct the exact native export input", "        if data.get('baseline')!='C-prototype' and default_target_contract is None:\n            # Reconstruct the exact native export input")
p.write_text(text)
q=ROOT/'autorouter/review_export.py';text=q.read_text()
replace("        if p.netclass_policy(candidate) is not None or native_toolchain is not None:\n            native_classes=f.read_json(folder/'final-netclasses.json');audited=p.audit_candidate_netclasses(candidate,protected,native_classes,**({'native_toolchain':native_toolchain} if native_toolchain is not None else {}))", "        if p.netclass_policy(candidate) is not None or native_toolchain is not None or 'default_target_transport' in report:\n            native_classes=f.read_json(folder/'final-netclasses.json');audited=p.audit_candidate_netclasses(candidate,protected,native_classes,default_target_policy='default_target_transport' in report,**({'native_toolchain':native_toolchain} if native_toolchain is not None else {}))")
replace("else ['final-netclasses'] if p.netclass_policy(candidate) is not None or native_toolchain is not None or class_requirement is not None else []", "else ['final-netclasses'] if p.netclass_policy(candidate) is not None or native_toolchain is not None or class_requirement is not None or 'default_target_transport' in report else []")
old="            digest,native=p.validate_candidate(job,original,candidate,binding['source_hashes'],protected,"
replace(old,old+"\n                default_target_policy='default_target_transport' in report,")
q.write_text(text)
print('Integrated source-derived Default routing target stage and final/export audit/readback.')
