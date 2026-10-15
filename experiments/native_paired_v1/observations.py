"""Shared actual matrix observation helpers, extracted unchanged from qualified300 reader.
No Native execution. Original source/candidate checks, rejected observations and
partial worker census retain the existing validation contracts.
"""
from pathlib import Path
import math
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
from autorouter import config as c,local_settings as ls,sexpr as sx
from experiments.native_paired_v1 import readback as shared
ROOT=c.ROOT
LIMIT=512*1024**2


def require(value,reason):
    if not value:raise p.Rejected(reason)


def number(value):
    require(type(value) in (int,float) and math.isfinite(value) and value>=0,'invalid finite cost')
    return value


def inventory(path):
    return pc.inventory(path,max_bytes=LIMIT,max_files=10000,max_entries=20000,with_directories=True)


def signatures(native):
    return sorted(f.canonical(x) for x in native['findings'] if x['severity']=='warning')


def workers(folder,data,board,hashes,original):
    """Shared completed-worker checks; failed workers remain explicitly unqualified."""
    rows=[];seen=set()
    for step in data.get('steps',[]):
        cwd=Path(step['cwd']);name=step['name'];identity=(str(cwd),name)
        require((cwd==folder or folder in cwd.parents) and cwd==cwd.resolve(strict=True),'worker escaped arm')
        require(identity not in seen and Path(name).name==name,'duplicate or unsafe worker name');seen.add(identity)
        path=cwd/(name+'-process.json');process=f.read_json(path)
        require(all(f.canonical(step.get(k))==f.canonical(v) for k,v in process.items()),'worker differs from step')
        require(process.get('cleanup_complete') is True,'worker cleanup unconfirmed')
        log=Path(process['log']);require(log==cwd/(name+'.log'),'worker log escaped stage')
        pc.read_bytes(log,16*1024**2)
        completed=process.get('status') in ('success','nonzero_exit') and type(process.get('exit_code')) is int
        if completed:f.process_check(cwd,data,name,process['argv'],allowed=(process['exit_code'],))
        argv=process['argv'];command=argv[len(f.SANDBOX):] if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
        stage_native=None
        if completed and command[:3]==[str(c.CLI),'pcb','drc']:
            require(process['exit_code'] in (0,5),'completed Native DRC has unexpected exit')
            if name=='source-drc':source=cwd/'snapshot'/board.name;input_path=cwd/'source-drc-input'/board.name;saved=False;before=hashes
            elif name=='refill-drc':source=cwd/'refill'/board.name;input_path=source;saved=True;before={**hashes,board.name:p.sha(cwd/'pre-refill.kicad_pcb')}
            elif name=='final-drc':source=cwd/'candidate'/board.name;input_path=cwd/'final-drc-input'/board.name;saved=False;before={**hashes,board.name:p.sha(source)}
            else:raise p.Rejected('unexpected Native DRC stage in normal matrix')
            require(name!='final-drc' or '--schematic-parity' in command,'complete schematic was omitted')
            stage_native=f.check_drc_stage(cwd,data,name,source,input_path,saved,before,
                schematic_parity='--schematic-parity' in command,sandboxed=argv[:len(f.SANDBOX)]==f.SANDBOX)
            if name=='final-drc':
                p.verify_candidate_files(source,hashes,p.sha(source))
                tree=sx.read(source);protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
                require(p.immutable(tree)==p.immutable(original) and all(r in p.routes(tree) for r in protected),'completed final Native observation lost original geometry/protected routes')
                shared.native_class_readback(cwd,data,source,protected)
        rows.append(dict(cwd=str(cwd),name=name,status=process['status'],exit_code=process.get('exit_code'),
            cleanup_complete=True,completed_shared_process_check=completed,native_stage=stage_native,process_sha256=p.sha(path),log_sha256=p.sha(log)))
    retained=inventory(folder)[0]
    actual={(str((folder/n).parent),Path(n).name[:-len('-process.json')]) for n in retained if n.endswith('-process.json')}
    require(actual==seen,'retained process census differs from declared workers')
    return rows


def candidate(folder,data,board,original,hashes,baseline,*,parent=None,resource_error=None):
    """Recheck actual final and saved refill, including rejected Native candidates."""
    final=folder/'candidate'/board.name;pre=folder/'pre-refill.kicad_pcb';saved=folder/'refill'/board.name
    if resource_error is None:
        proof=shared.final_candidate_readback(folder,data,board,original,hashes,resource_parent=parent)
    else:
        # A real over-budget rejected candidate still receives original-rule Native
        # observation checks; this is explicitly NOT the successful full reader.
        require(data.get('accepted') is False or (parent is not None and parent.get('accepted') is False),'accepted candidate cannot bypass resource checks')
        p.verify_candidate_files(final,hashes,data['candidate_sha256'])
        tree=sx.read(final);protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
        require(p.immutable(tree)==p.immutable(original) and all(r in p.routes(tree) for r in protected),'rejected candidate lost original design')
        p.check_protected_import(folder,data,original,final,protected)
        p.check_pour_evidence(folder,data,original,final,correction=data.get('adapter') in ('planes','both'))
        p.check_native_edge_transport(folder,data)
        native=f.check_drc_stage(folder,data,'final-drc',final,folder/'final-drc-input'/board.name,False,
            {**hashes,board.name:data['candidate_sha256']},schematic_parity=True,sandboxed=False)
        require(native==data['native'] and p.sha(folder/'final-drc.json')==data['native_report_sha256'],'rejected final report differs')
        class_audit,class_required=shared.native_class_readback(folder,data,final,protected)
        proof=dict(path=str(final),candidate_sha256=p.sha(final),native_counts={k:native[k] for k in ('opens','blocking','warnings','exclusions')},
            native_report_sha256=p.sha(folder/'final-drc.json'),original_design_checks=True,complete_schematic_native_checks=True,
            original_native_class_targets=class_audit,original_native_class_audit_required=class_required)
    proof.update(full_shared_candidate_readback=resource_error is None,qualification_failure=resource_error)
    pre_tree=sx.read(pre);protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
    require(p.immutable(pre_tree)==p.immutable(original) and all(x in p.routes(pre_tree) for x in protected),'pre-refill original design differs')
    native=f.check_drc_stage(folder,data,'refill-drc',saved,saved,True,{**hashes,board.name:p.sha(pre)},sandboxed=False)
    require((sx.dump(p.transplant_fill(pre_tree,sx.read(saved)))+'\n').encode()==pc.read_bytes(final),'saved refill does not reconstruct final candidate')
    if (folder/'code/pipeline.py').exists():
        imports=ls.check_normal_policy(folder,data)
        if parent is None:
            contract=p.normal_import_contract(folder,data,imports,input_policy='native',original=original)
            p.check_protected_import(folder,data,original,final,protected,**(contract or {}))
    metrics=None
    if 'metrics' in data:
        metrics=f.read_json(folder/'metrics.json')
        require(metrics==data['metrics'] and metrics['version']=='10.0.0','metrics/file/version mismatch')
        f.process_check(folder,data,'metrics',[str(c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',str(final),str(folder/'metrics.json')])
        require(type(metrics['vias']) is int and metrics['vias']>=0 and number(metrics['track_length_mm'])>=0,'invalid metrics')
    warning_equal=signatures(data['native'])==signatures(baseline)
    require(data.get('accepted') is not True or warning_equal,'accepted candidate lost or added original warnings')
    require(data['native']['ignored_checks']==baseline['ignored_checks'],'original ignored checks differ')
    proof.update(saved_refill_native=native,saved_refill_sha256=p.sha(saved),pre_refill_sha256=p.sha(pre),
        unchanged_original_warning_signatures=warning_equal,metrics=metrics,metrics_sha256=p.sha(folder/'metrics.json') if metrics else None)
    return proof


def resource_failure(folder,data,parent=None):
    try:
        if parent is None:p.check_resource_accounting(data)
        else:shared.inherited_trial_accounting(folder,data,parent)
    except p.Rejected as exc:
        require(data.get('accepted') is False or (parent is not None and parent.get('accepted') is False),'accepted receipt has invalid resources')
        return type(exc).__name__+': '+str(exc)
    return None
