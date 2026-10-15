"""Bounded endpoint groups for deletion trials, never connectivity evidence.

This deliberately uses no zone fill, terminal-demand rewriting or reference
routes. Every proposed deletion still needs the ordinary full native validator.
"""
from decimal import Decimal, InvalidOperation, localcontext
import re

from . import pipeline as p, sexpr as sx

MAX_ROUTES = 4096
MAX_PADS = 1024
MAX_GROUPS = 256
MAX_SEGMENTS = 32


def nm(atom):
    if not isinstance(atom, str) or len(atom) > 40 or re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)',atom) is None:
        raise ValueError('bounded coordinate required')
    with localcontext() as context:
        context.prec=64 # More than all forty source digits plus unit scaling.
        value = Decimal(atom) * 1000000
    if not value.is_finite() or value != value.to_integral_value() or abs(value) > 10**12:
        raise ValueError('exact finite native coordinate required')
    return int(value)


def xy(node):
    if not isinstance(node, list) or len(node) < 3:
        raise ValueError('coordinate pair required')
    return nm(node[1]), nm(node[2])


def build(tree, nets, protected):
    """Return groups plus explicit refusal/skip counts for this exact incumbent.

    A continuation requires exactly two eligible equal-width segments at the
    same net/layer endpoint. All routes enter the degree census. Vias, arcs,
    protected copper, branches and conservative pad envelopes stop a group.
    Contacts away from endpoints are deliberately not inferred. A group is a
    deletion hypothesis, not a claim that the copper is electrically unbranched.
    """
    from . import strategy as s
    result = dict(schema=1,kind='endpoint-chain-proposals-v1',proposals=[],
                  declined_reason='',oversize_groups=0,closed_cycles=0,
                  route_count=0,pad_count=0,eligible_segments=0)
    try:
        routes=p.routes(tree);result['route_count']=len(routes)
        if len(routes)>MAX_ROUTES:
            raise ValueError('chain route census ceiling')
        envelopes=[]
        for fp in sx.children(tree,'footprint'):
            centre=xy(sx.one(fp,'at'))
            for pad in sx.children(fp,'pad'):
                result['pad_count']+=1
                if result['pad_count']>MAX_PADS:raise ValueError('chain pad census ceiling')
                if len(pad)<4 or pad[3] not in ('circle','rect','oval','roundrect') or sx.one(pad,'rect_delta') is not None:
                    raise ValueError('unqualified chain pad envelope shape')
                local=xy(sx.one(pad,'at'));size=xy(sx.one(pad,'size'))
                if min(size)<=0:raise ValueError('positive pad envelope required')
                # L1 bound contains the rotated/flipped local centre and pad
                # rectangle for every orientation. It can over-split groups.
                radius=abs(local[0])+abs(local[1])+(size[0]+size[1]+1)//2+2
                envelopes.append((centre,radius))
        def pad_boundary(point):
            return any((point[0]-centre[0])**2+(point[1]-centre[1])**2<=radius**2
                       for centre,radius in envelopes)
        allowed={s.route_id(r) for r in s.eligible_routes(tree,nets,protected)}
        rows={};touch={};segments={};geometry=set()
        for route in routes:
            rid=s.route_id(route)
            if rid in rows:raise ValueError('duplicate route record')
            rows[rid]=route
            if route[0]=='via':
                point=xy(sx.one(route,'at'));layers=[sx.unquote(v) for v in sx.one(route,'layers')[1:]]
                if set(layers)!={'F.Cu','B.Cu'}:raise ValueError('unqualified chain via layer span')
                points=[(layer,point) for layer in layers]
            else:
                layer=sx.unquote(sx.one(route,'layer')[1])
                if layer not in ('F.Cu','B.Cu'):raise ValueError('unqualified chain route layer')
                a,b=xy(sx.one(route,'start')),xy(sx.one(route,'end'))
                if a==b:raise ValueError('zero-length chain route')
                if route[0]=='segment':
                    edge=(layer,*sorted((a,b)))
                    if edge in geometry:raise ValueError('ambiguous duplicate segment geometry')
                    geometry.add(edge)
                points=[(layer,a),(layer,b)]
                if route[0]=='segment' and rid in allowed:
                    width=nm(sx.one(route,'width')[1])
                    if width<=0:raise ValueError('positive chain width required')
                    segments[rid]=(sx.one(route,'net')[1],layer,width)
            for layer,point in points:touch.setdefault((layer,*point),[]).append(rid)
        result['eligible_segments']=len(segments);neighbors={rid:set() for rid in segments}
        for key,members in touch.items():
            if len(members)!=2 or any(rid not in segments for rid in members) or pad_boundary(key[1:]):continue
            a,b=members
            if segments[a]==segments[b]:neighbors[a].add(b);neighbors[b].add(a)
        seen=set();groups=[]
        for seed in sorted(segments):
            if seed in seen:continue
            group=set();pending=[seed]
            while pending:
                rid=pending.pop()
                if rid in group:continue
                group.add(rid);pending.extend(neighbors[rid]-group)
            seen.update(group)
            if len(group)<2:continue
            if all(len(neighbors[rid])==2 for rid in group):result['closed_cycles']+=1;continue
            if len(group)>MAX_SEGMENTS:result['oversize_groups']+=1;continue
            groups.append(dict(kind='endpoint_chain',net=segments[seed][0],route_ids=sorted(group),
                               segment_count=len(group),ranking_length_mm=sum(s._length(rows[rid]) for rid in sorted(group))))
        groups.sort(key=lambda row:(-row['ranking_length_mm'],row['route_ids']))
        if len(groups)>MAX_GROUPS:raise ValueError('chain proposal population ceiling')
        result['proposals']=groups
    except (ValueError,InvalidOperation,TypeError,IndexError,KeyError,AttributeError) as exc:
        result.update(proposals=[],declined_reason=type(exc).__name__+': '+str(exc))
    return result
