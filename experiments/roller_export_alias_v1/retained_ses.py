"""Exact zero-via retained-route diagnostic SES; no routing or optimization."""
import copy,json,re
from collections import Counter
from decimal import Decimal
from autorouter import sexpr as sx,pipeline as p,adapter
from experiments.pic_mixed_transport_probe_v1 import ses_checks as sc
from padless_alias import dsn_aliases,strip_ses_placements

def render(value):return str(value.to_integral()) if value==value.to_integral() else format(value,'f')
def build(raw,source,binding):
    dsn,_=dsn_aliases(raw,source,binding);original=sx.parse(source.decode());wanted,vias=sc.source_routes(original)
    if vias or len(p.routes(original))!=11 or any(r[0]!='segment' for r in p.routes(original)):raise ValueError('exact Roller eleven-segment/no-via diagnostic required')
    resolution=sx.one(dsn,'resolution')
    if resolution!=['resolution','um','10']:raise ValueError('pinned DSN resolution differs')
    scale=Decimal(10);place=['placement',copy.deepcopy(resolution)]
    for comp in sx.children(sx.one(dsn,'placement'),'component'):
        c=['component',json.dumps(re.sub(r'::[0-9]+$','',sx.unquote(comp[1])))]
        for n in sx.children(comp,'place'):
            sc.children_only(n,{'PN'},6);c.append(['place',n[1],render(sc.number(n[2])*scale),render(sc.number(n[3])*scale),n[4],render((sc.number(n[5])%360+360)%360)])
        place.append(c)
    wiring=sx.one(dsn,'wiring');sc.children_only(wiring,{'wire'},1);nets={};actual=Counter()
    for wire in sx.children(wiring,'wire'):
        sc.children_only(wire,{'path','net','type'},1);path=sx.one(wire,'path');net=sx.one(wire,'net');typ=sx.one(wire,'type')
        if path is None or net is None or len(net)!=2 or typ not in (None,['type','route'],['type','fix'],['type','protect']):raise ValueError('unknown retained wire role')
        layer=sx.unquote(path[1]);canonical={'F.Cu':'top_layer','B.Cu':'bottom_layer'}.get(layer)
        if canonical is None:raise ValueError('unknown native DSN route layer')
        name=sx.unquote(net[1]);actual.update(sc.segments(name,canonical,sc.number(path[2]),sc.pairs(path[3:])))
        shape=['path',path[1],*[render(sc.number(x)*scale) for x in path[2:]]]
        nets.setdefault(name,['net',net[1]]).append(['wire',shape])
    if actual!=wanted:raise ValueError('native DSN does not preserve exact original route population')
    routes=['routes',copy.deepcopy(resolution),['parser',['host_cad',json.dumps("KiCad's Pcbnew")],['host_version','"10.0.0"']],['library_out'],['network_out',*[nets[n] for n in sorted(nets)]]]
    ses=['session','"retained.ses"',['base_design',dsn[1]],place,['was_is'],routes]
    raw_ses=(sx.dump(ses)+'\n').encode();filtered,receipt=strip_ses_placements(raw_ses,raw,source,binding)
    receipt.update(exact_original_segments=sum(wanted.values()),solver_execution=False,reference_route_optimization=False)
    return raw_ses,filtered,receipt
