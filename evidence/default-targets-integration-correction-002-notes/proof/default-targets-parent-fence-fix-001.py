from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'autorouter/pipeline.py';s=p.read_text()
old="""    return record

def parent_dsn_basis(directory):"""
new="""    return record


def check_final_netclass_evidence(directory,data,candidate,protected,*,native_toolchain=None,
                                  default_target_policy=False,sandboxed=False):
    \"\"\"One final raw-class/generated-target/process audit for Route and export.\"\"\"
    from . import floor_route as f
    directory=Path(directory);candidate=Path(candidate)
    mapping=directory/'final-netclasses.json'
    audited=audit_candidate_netclasses(candidate,protected,f.read_json(mapping),
        native_toolchain=native_toolchain,default_target_policy=default_target_policy)
    audited['native_map_file_sha256']=sha(mapping)
    if f.read_json(directory/'final-netclass-audit.json')!=audited:
        raise Rejected('retained native netclass audit differs from candidate')
    f.process_check(directory,data,'final-netclasses',[*(f.SANDBOX if sandboxed else []),
        *native_prefix(native_toolchain),'netclasses',str(candidate),str(mapping)])
    return audited


def check_rejected_default_targets(directory,data,original,candidate,protected):
    \"\"\"A sole-thermal rejected incumbent keeps the same mandatory contract.\"\"\"
    record=check_default_target_transport(directory,data,original,candidate)
    if record is not None:
        check_final_netclass_evidence(directory,data,candidate,protected,default_target_policy=True)
    return record


def parent_dsn_basis(directory):"""
assert s.count(old)==1;s=s.replace(old,new)
old="""            elif inc.get('status')=='drc_rejected' and thermal.sole_thermal(inc.get('native')) is not None:
                thermal._report_binding"""
new="""            elif inc.get('status')=='drc_rejected' and thermal.sole_thermal(inc.get('native')) is not None:
                check_rejected_default_targets(child,inc,original,child_candidate,child_protected)
                thermal._report_binding"""
assert s.count(old)==1;s=s.replace(old,new)
old="""        native_classes=evidence('final-netclasses.json')
        audited=audit_candidate_netclasses(candidate,protected,native_classes,native_toolchain=native_toolchain,default_target_policy=default_target_contract is not None)
        audited['native_map_file_sha256']=sha(path.parent/'final-netclasses.json')
        if evidence('final-netclass-audit.json')!=audited: raise Rejected('retained native netclass audit differs from candidate')
        process=evidence('final-netclasses-process.json')
        expected=[*native_prefix(native_toolchain),'netclasses',str(candidate),str(path.parent/'final-netclasses.json')]
        if (process.get('argv')!=expected or process.get('cwd')!=str(path.parent) or process.get('name')!='final-netclasses'
                or process.get('exit_code')!=0 or process.get('status')!='success' or process.get('cleanup_complete') is not True):
            raise Rejected('native netclass process provenance is inconsistent')
        matching=[step for step in data.get('steps',[]) if step.get('name')=='final-netclasses' and step.get('cwd')==str(path.parent)]
        if len(matching)!=1 or any(matching[0].get(key)!=value for key,value in process.items()):
            raise Rejected('native netclass step differs from retained process')"""
new="""        check_final_netclass_evidence(path.parent,data,candidate,protected,native_toolchain=native_toolchain,
            default_target_policy=default_target_contract is not None)"""
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
p=root/'autorouter/review_export.py';s=p.read_text()
old="""            native_classes=f.read_json(folder/'final-netclasses.json');audited=p.audit_candidate_netclasses(candidate,protected,native_classes,default_target_policy='default_target_transport' in report,**({'native_toolchain':native_toolchain} if native_toolchain is not None else {}))
            audited['native_map_file_sha256']=p.sha(folder/'final-netclasses.json')
            if f.read_json(folder/'final-netclass-audit.json')!=audited:raise p.Rejected('export original native class targets changed')
            f.process_check(folder,data,'final-netclasses',[*f.SANDBOX,*p.native_prefix(native_toolchain),'netclasses',str(candidate),str(folder/'final-netclasses.json')])"""
new="""            p.check_final_netclass_evidence(folder,data,candidate,protected,native_toolchain=native_toolchain,
                default_target_policy='default_target_transport' in report,sandboxed=True)"""
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
import hashlib,ast
for name in ['pipeline.py','review_export.py']:
 p=root/'autorouter'/name;ast.parse(p.read_text());print(name,hashlib.sha256(p.read_bytes()).hexdigest())
