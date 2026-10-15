"""Reuse sole-zone deletion and shared thermal final-phase helpers; no process launch."""
from pathlib import Path
from autorouter import pipeline as p,floor_route as f,sexpr as sx
from autorouter import strategy as st,routing_scope as rs,board_floor as g
from experiments.thermal_group_pruning_v1 import actor as group


def need(value,reason):
    if not value:raise p.Rejected(reason)

def warnings(native):
    return sorted(f.canonical(row) for row in native['findings'] if row['severity']=='warning')

def deletion(original,warm):
    """ONE existing whole-zone proposal from own retained warm tree only."""
    need(p.immutable(warm)==p.immutable(original),'warm original design differs')
    nets=st.zone_net_ids(warm);need(len(nets)==1,'exactly one zone net required')
    _,resolve=g.source_net_identity(warm)
    zones=[z for z in sx.children(warm,'zone') if sx.one(z,'keepout') is None]
    need(len(zones)==1,'exactly one ordinary zone required')
    names=[resolve(sx.one(zones[0],'net'),owner=zones[0])]
    need(bool(names[0]),'zone net must resolve exactly')
    protected=rs.protected_routes(warm,names)
    proposals=st.proposals(warm,nets,protected,True)
    need(len(proposals)==1 and proposals[0]['kind']=='whole_zone_net' and bool(proposals[0]['route_ids']),'one nonempty existing whole-zone deletion required')
    tree=st.delete_routes(warm,proposals[0]['route_ids'],nets,protected)
    audit=rs.audit(warm,tree,names)
    return tree,proposals[0],protected,names,audit

def phase(folder,steps,source,hashes,tools,protected,warm,names,baseline):
    """New C Native evidence only, not an old reader/Native replay."""
    entry,metrics=group.phase(folder,steps,source,hashes,tools)
    candidate=Path(entry['candidate']);mapping=folder/'final-netclasses.json'
    need(p.netclass_policy(candidate) is not None,'active source classes required')
    audit=p.audit_candidate_netclasses(candidate,protected,f.read_json(mapping))
    audit['native_map_file_sha256']=p.sha(mapping)
    f.process_check(folder,{'steps':steps},'final-netclasses',[*f.SANDBOX,str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py'),'netclasses',str(candidate),str(mapping)])
    need(audit==f.read_json(folder/'final-netclass-audit.json'),'actual new class audit differs')
    protection=rs.audit(warm,sx.read(candidate),names)
    valid=p.native_accepted(entry['native']) and warnings(entry['native'])==warnings(baseline) and entry['native']['ignored_checks']==baseline['ignored_checks']
    return dict(entry=entry,metrics=metrics,protected_signal_audit=protection,candidate_valid=valid)
