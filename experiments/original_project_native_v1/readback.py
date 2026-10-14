"""Shared retained original-refill diagnostic consistency; never routing acceptance.

No Native/JVM/network launch. tool_manifest uses its existing read-only Git HEAD.
The caller owns bounded execution, honest cost accounting and output publication.
"""
import hashlib,math,stat
from importlib import import_module
from pathlib import Path
from autorouter import pipeline as p,floor_route as f,placement_clearance as io,sexpr as sx
from experiments.original_project_native_v1 import driver
from scripts import fetch_led_demo as demo

def check(directory,data):
    """Check an observed fixed-source original-refill receipt without new Native."""
    def require(ok,reason):
        if not ok:raise p.Rejected('original-refill readback: '+reason)
    def number(x):return type(x) in (int,float) and math.isfinite(x) and x>=0
    out=Path(directory);root=driver.ROOT;receipt=out/'result.json'
    require(out.is_absolute() and out.resolve()==out and root/'.runs' in out.parents,'canonical local diagnostic directory required')
    require(f.canonical(f.read_json(receipt))==f.canonical(data),'receipt differs from supplied data');receipt_pin=p.sha(receipt)
    require(type(data.get('schema')) is int and data['schema']==1 and data.get('kind')=='original_hardware_native_diagnostic' and data.get('status')=='observed','observed diagnostic required')
    require(all(data.get(k) is False for k in ('accepted','physical_electrical_validation','routing_executed','production_support_qualified','serialization_equivalence_qualified')),'diagnostic admission/scope differs')
    project=data['project'];require(project in driver.CASES and project in driver.REFILLED_ORIGINALS,'fixed original-refill case required')
    version,relative,commit,_=driver.CASES[project];require(data['source_commit']==commit,'fixed source commit differs')
    def capture():
        if version=='portable-demo':
            require(demo.fixed_profile(project)['commit']==commit,'source profile revision differs')
            return demo.capture_native_source(project,root=root)[1]
        if version=='managed-interf':return driver.capture_interf_source()
        return import_module('experiments.arcdice_native_class_v1.source' if version=='arcdice-source' else 'experiments.licensed_acquisition_'+version+'.native_snapshot').capture()
    captured=capture();hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in captured.items()}
    require(data['original_hashes']==hashes==p.tree_hash(out/'original'),'all original/acquired source bytes differ')
    if version=='portable-demo':require(data['source_profile_id']==project and data['source_file_count']==len(captured) and data['source_bytes']==sum(map(len,captured.values())),'source profile/population differs')
    original_board=out/'original'/relative;original=sx.read(original_board);source_hashes=p.tree_hash(original_board.parent)
    saved=out/'saved'/original_board.name;candidate=out/'candidate'/original_board.name;job=out/'job';current=sx.read(candidate);savedtree=sx.read(saved)
    require(data['final_candidate']==str(candidate) and p.sha(candidate)==data['final_candidate_sha256'],'candidate path/hash differs')
    p.verify_candidate_files(candidate,source_hashes,data['final_candidate_sha256'])
    require(p.immutable(current)==p.immutable(original) and driver.route_records(current)==driver.route_records(original),'original rules/geometry/all route records differ')
    require(io.read_bytes(candidate)==(sx.dump(p.transplant_fill(original,savedtree))+'\n').encode(),'saved fill to original-shell reconstruction differs')
    require((p.immutable(savedtree)==p.immutable(original)) is data['native_saved_nonfill_ast_equal'],'saved serializer geometry observation differs')
    require((driver.route_records(savedtree)==driver.route_records(original)) is data['native_saved_route_records_equal'],'saved serializer route observation differs')
    require(all(data.get(k) is True for k in ('original_shell_nonfill_ast_equal','all_original_route_records_exact','original_preserved','acquired_source_still_exact','within_budget')),'preservation/complete-budget metadata differs')
    refill=f.check_drc_stage(job,data,'original-refill',saved,saved,True,source_hashes)
    final=f.check_drc_stage(job,data,'original-final',candidate,job/'original-final-input'/candidate.name,False,{**source_hashes,candidate.name:data['final_candidate_sha256']},schematic_parity=True)
    require(f.canonical(refill)==f.canonical(data['original_native']) and f.canonical(final)==f.canonical(data['parity_native']) and p.sha(job/'original-final.json')==data['final_native_report_sha256'],'Native report/hash/duplicate differs')
    require(type(data['schematic_parity_findings']) is int and data['schematic_parity_findings']==len(f.read_json(job/'original-final.json')['schematic_parity']),'full schematic finding count differs')
    require(data['native_routing_scope_accepted'] is p.native_accepted(final),'diagnostic Native-acceptance observation differs')
    try:p.preflight(original_board)
    except p.Rejected as exc:require(data['static_supported'] is False and data['static_unsupported_reason']==str(exc),'production refusal differs')
    else:require(data['static_supported'] is True,'static support observation differs')
    tools=p.tool_manifest();require(data['tools']==tools,'current tool/code/HEAD bytes differ')
    code={**tools['implementation_sha256'],**data['additional_implementation_sha256']}
    require(p.tree_hash(out/'code')==code,'retained code snapshot differs')
    for name,pin in code.items():require(p.sha(root/name)==pin,'current implementation differs: '+name)
    require(data['helper_sha256']==p.sha(root/'experiments/original_project_native_v1/driver.py'),'driver pin differs')
    witness=driver.completed_evidence(out);require(hashlib.sha256(f.canonical(witness).encode()).hexdigest()==data['completed_evidence_sha256'],'completed inventory differs')
    require(data['budget_seconds']==data['cpu_budget_seconds']==driver.SECONDS and data['output_cap_bytes']==driver.LIMIT,'diagnostic finite caps differ')
    require(all(number(data[k]) for k in ('wall_seconds','total_cpu_seconds','output_bytes')) and max(data['wall_seconds'],data['total_cpu_seconds'])<=driver.SECONDS and data['output_bytes']<=driver.LIMIT,'actual diagnostic costs exceed caps')
    require(type(data['protect_local_settings']) is bool,'explicit PRL guard setting required');workers=[]
    for step in data['steps']:
        proc=f.process_check(job,data,step['name'],step['argv'],allowed=(0,5));log=Path(proc['log'])
        require(proc['argv'][:3]==f.SANDBOX and proc['cleanup_complete'] is True and proc['log_truncated'] is False and log.parent==job and log.stat().st_size==proc['log_bytes']<=256*1024,'worker/log provenance differs')
        require(proc['resource_guards']['max_workdir_bytes']==driver.LIMIT and proc['resource_guards']['max_group_rss_bytes']==2*1024**3,'worker resource caps differ')
        is_drc=proc['argv'][3:6]==[str(p.c.CLI),'pcb','drc'];event=proc.get('local_settings_protection')
        if is_drc and data['protect_local_settings']:
            prl=Path(proc['argv'][-1]).with_suffix('.kicad_prl')
            if prl.name in source_hashes:
                require(prl.exists() and prl.resolve()==prl and out in prl.parents and prl.suffix=='.kicad_prl' and stat.S_ISREG(prl.lstat().st_mode) and prl.stat().st_nlink==1 and prl.stat().st_flags==0,'current PRL path/type/flags differ')
                expected={'policy':'mac-owned-prl-immutable-v1','present':True,'path':str(prl),'sha256':p.sha(prl),'flags_before':0,'flags_during':stat.UF_IMMUTABLE,'flags_restored':True,'bytes_unchanged':True}
                require(f.canonical(event)==f.canonical(expected) and source_hashes[prl.name]==event['sha256'],'PRL original bytes/restored guard witness differs')
            else:require(f.canonical(event)==f.canonical({'policy':'mac-owned-prl-immutable-v1','present':False}),'absent PRL guard witness differs')
        else:require(event is None,'unexpected PRL guard event')
        workers.append({'name':step['name'],'process_sha256':p.sha(job/(step['name']+'-process.json')),'log_sha256':p.sha(log),'cleanup_complete':True,'local_settings_protection':event})
    def retained_prls():
        for board_copy in (original_board,saved,candidate,job/'original-final-input'/candidate.name):
            prl=board_copy.with_suffix('.kicad_prl')
            if prl.name in source_hashes:require(prl.exists() and prl.stat().st_flags==0 and p.sha(prl)==source_hashes[prl.name],'retained original PRL bytes/current flags differ')
            elif prl.exists():require(prl.stat().st_flags==0,'added native UI state has unexpected flags')
    retained_prls()
    require(sum(s['cpu_seconds']+s.get('monitor_cpu_seconds',0) for s in data['steps'])<=data['total_cpu_seconds']+1e-6,'worker CPU omitted')
    require(p.tree_hash(out/'original')==hashes and capture()==captured and p.sha(receipt)==receipt_pin and f.canonical(f.read_json(receipt))==f.canonical(data) and driver.completed_evidence(out)==witness and p.tool_manifest()==tools,'late source/runtime/publication changed')
    retained_prls()  # Flags are metadata, outside the byte inventories above.
    return {'consistent':True,'accepted':False,'production_admitted':False,'project':project,'receipt_sha256':receipt_pin,'source_hashes':hashes,'source_commit':commit,'candidate_sha256':data['final_candidate_sha256'],'saved_report_sha256':p.sha(job/'original-refill.json'),'final_report_sha256':data['final_native_report_sha256'],'saved_native':refill,'final_native':final,'schematic_parity_findings':data['schematic_parity_findings'],'all_original_route_records':len(driver.route_records(original)),'completed_evidence_sha256':data['completed_evidence_sha256'],'workers':workers,'diagnostic_wall_seconds':data['wall_seconds'],'diagnostic_full_cpu_seconds':data['total_cpu_seconds'],'static_supported':data['static_supported'],'static_unsupported_reason':data.get('static_unsupported_reason'),'new_native_execution':False,'limitations':['Mutable local evidence consistency only; no new Native or routing/physical acceptance.','Native serializer differences and all warnings/errors/exclusions/ignored checks remain visible.','Optional additional class/context observations, source rights and ancestry need their separate existing evidence.']}
