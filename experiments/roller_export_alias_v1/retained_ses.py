"""Exact zero-via retained-route diagnostic SES; no routing or optimization."""
import copy,json,re
from collections import Counter
from decimal import Decimal
from autorouter import sexpr as sx,pipeline as p,adapter
from experiments.pic_mixed_transport_probe_v1 import ses_checks as sc
from padless_alias import dsn_aliases,strip_ses_placements

def render(value):return str(value.to_integral()) if value==value.to_integral() else format(value,'f')

def restore_protected_order(original,rebuilt):
    """Reorder only after every original protected node survives exactly."""
    if p.immutable(original)!=p.immutable(rebuilt):raise ValueError('nonrouting source changed')
    def records(tree):
        rows={}
        for node in p.routes(tree):
            identity=sx.one(node,'uuid',sx.one(node,'tstamp'))
            if identity is None or len(identity)!=2 or identity[1] in rows:
                raise ValueError('unique protected route identity required')
            rows[identity[1]]=node
        return rows
    before,after=records(original),records(rebuilt)
    if not before or before!=after:raise ValueError('exact protected route population changed')
    result=copy.deepcopy(rebuilt);ordered=iter(copy.deepcopy(p.routes(original)))
    for i,node in enumerate(result):
        if isinstance(node,list) and node and node[0] in p.ROUTES:result[i]=next(ordered)
    return result

def build(raw,source,binding,*,geometry_source='native_dsn'):
    if geometry_source not in {'native_dsn','original_protected_source'}:raise ValueError('unknown retained geometry source')
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
    if geometry_source=='native_dsn' and actual!=wanted:raise ValueError('native DSN does not preserve exact original route population')
    if geometry_source=='original_protected_source':
        # A separately declared no-solver transport control. Never repair or
        # relabel the raw exporter geometry as an exact representation.
        nets={};constructed=Counter();names={n[1]:sx.unquote(n[2]) for n in sx.children(original,'net')}
        exported={sx.unquote(n[1]) for n in sx.children(sx.one(dsn,'network'),'net')}
        for route in p.routes(original):
            name=names.get(sx.one(route,'net')[1],sx.unquote(sx.one(route,'net')[1]))
            if name not in exported:raise ValueError('protected source route absent from native DSN net population')
            layer=sx.unquote(sx.one(route,'layer')[1]);points=[tuple(sc.number(x)*1000*(-1 if i else 1) for i,x in enumerate(sx.one(route,k)[1:])) for k in ('start','end')]
            width=sc.number(sx.one(route,'width')[1])*1000
            values=[width,*points[0],*points[1]]
            if any(v*scale!=(v*scale).to_integral_value() for v in values):raise ValueError('protected source geometry outside exact SES grid')
            shape=['path',json.dumps(layer),*[render(v*scale) for v in values]]
            nets.setdefault(name,['net',json.dumps(name)]).append(['wire',shape])
            constructed.update(sc.segments(name,{'F.Cu':'top_layer','B.Cu':'bottom_layer'}[layer],width,points))
        if constructed!=wanted:raise ValueError('constructed SES differs from exact protected source routes')
    routes=['routes',copy.deepcopy(resolution),['parser',['host_cad',json.dumps("KiCad's Pcbnew")],['host_version','"10.0.0"']],['library_out'],['network_out',*[nets[n] for n in sorted(nets)]]]
    ses=['session','"retained.ses"',['base_design',dsn[1]],place,['was_is'],routes]
    raw_ses=(sx.dump(ses)+'\n').encode();filtered,receipt=strip_ses_placements(raw_ses,raw,source,binding)
    receipt.update(exact_original_segments=sum(wanted.values()),solver_execution=False,reference_route_optimization=False,
        geometry_source=geometry_source,raw_native_dsn_route_diff=sc.diff(wanted,actual),raw_dsn_geometry_repaired=False)
    return raw_ses,filtered,receipt
