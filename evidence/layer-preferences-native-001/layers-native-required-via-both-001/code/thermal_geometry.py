"""Bounded thermal proposal geometry; no native calls, I/O, or board identities.

Saved copper path existence only. Caller binds fresh observations and validates
new copper with original native rules and unchanged final fill. No ampacity or
new-global-component claim. Coordinates are integer nanometres.
"""
import math
import time

class Unsupported(ValueError): pass

class Guard:
    def __init__(self, seconds=8, operations=250000, remaining_seconds=None):
        self.deadline=time.monotonic()+seconds; self.remaining=operations; self.used=0
        self.remaining_seconds=remaining_seconds;self.next_external_check=0
    def charge(self,n=1):
        self.remaining-=n;self.used+=n
        external_exhausted=False
        if self.remaining_seconds is not None and self.used>=self.next_external_check:
            external_exhausted=self.remaining_seconds()<=0;self.next_external_check=self.used+2048
        if self.remaining<0 or time.monotonic()>self.deadline or external_exhausted:
            raise Unsupported('bounded geometry deadline/operation cap')

def orient(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def edges(poly): return zip(poly,poly[1:]+poly[:1])
def point_sq(a,b): return sum((x-y)**2 for x,y in zip(a,b))
def on_segment(p,a,b):
    return orient(a,b,p)==0 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1])
def intersects(a,b,c,d):
    oa,ob,oc,od=orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)
    return (oa*ob<0 and oc*od<0) or (oa==0 and on_segment(c,a,b)) or (ob==0 and on_segment(d,a,b)) or (oc==0 and on_segment(a,c,d)) or (od==0 and on_segment(b,c,d))
def point_segment_sq(p,a,b):
    """Exact rational squared distance as integer (numerator, denominator)."""
    ab=(b[0]-a[0],b[1]-a[1]);ap=(p[0]-a[0],p[1]-a[1]);den=ab[0]**2+ab[1]**2
    dot=ap[0]*ab[0]+ap[1]*ab[1]
    if not den or dot<=0:return point_sq(p,a),1
    if dot>=den:return point_sq(p,b),1
    return (ab[0]*ap[1]-ab[1]*ap[0])**2,den

def farther_point_segment(p,a,b,r):
    n,d=point_segment_sq(p,a,b);return n>r*r*d

def bbox_gap_sq(a,b,c,d):
    dx=max(0,min(a[0],b[0])-max(c[0],d[0]),min(c[0],d[0])-max(a[0],b[0]))
    dy=max(0,min(a[1],b[1])-max(c[1],d[1]),min(c[1],d[1])-max(a[1],b[1]))
    return dx*dx+dy*dy

def farther_segments(a,b,c,d,r):
    if bbox_gap_sq(a,b,c,d)>r*r:return True
    if intersects(a,b,c,d):return False
    return all(farther_point_segment(p,x,y,r) for p,x,y in ((a,c,d),(b,c,d),(c,a,b),(d,a,b)))

def inside(p,poly):
    """Even-odd membership with exact integer comparisons; excludes boundary."""
    result=False;x,y=p
    for a,b in edges(poly):
        if on_segment(p,a,b):return False
        if (a[1]>y)!=(b[1]>y):
            lhs=(x-a[0])*(b[1]-a[1]);rhs=(b[0]-a[0])*(y-a[1])
            if (lhs<rhs) if b[1]>a[1] else (lhs>rhs): result=not result
    return result

def valid_point(p):
    return isinstance(p,(tuple,list)) and len(p)==2 and all(type(v) is int and abs(v)<=10**12 for v in p)

def validate_domain(poly,holes):
    if not 3<=len(poly)<=2048 or not all(valid_point(v) for v in poly):raise Unsupported('bounded integer contour required')
    if len(holes)>2048:raise Unsupported('drill population cap')
    if any(not valid_point(h['center']) or type(h['radius']) is not int or h['radius']<=0 for h in holes):raise Unsupported('only exact integer concentric round physical drills')

def certified_leg(a,b,poly,holes,margin,guard):
    if not valid_point(a) or not valid_point(b) or type(margin) is not int or margin<=0:raise Unsupported('invalid certificate coordinates or margin')
    guard.charge(2*len(poly))
    if not inside(a,poly) or not inside(b,poly):return False
    for c,d in edges(poly):
        guard.charge()
        if not farther_segments(a,b,c,d,margin):return False
    for hole in holes:
        guard.charge()
        if not farther_point_segment(hole['center'],a,b,hole['radius']+margin):return False
    return True

def annular(p,pad,margin):
    d=point_sq(p,pad['center'])
    return (pad['drill_radius']+margin)**2<d<(pad['outer_radius']-margin)**2


import heapq
from decimal import Decimal

def drill_census(g):
    holes=[];errors=[]
    for p in g['pads']:
        h=p['effective_hole'];diameter=h['width_nm']
        if diameter<=0:continue
        if h['start_nm']!=h['end_nm'] or not p['drill_is_round'] or diameter%2:
            errors.append({'uuid':p['uuid'],'reason':'noninteger-radius/slot/nonround drill'});continue
        holes.append({'kind':'pad','uuid':p['uuid'],'net_code':p['net_code'],'logical_terminal':p['logical_terminal'],'center':h['start_nm'],'radius':diameter//2})
    layers=[l['id'] for l in g['layers']]
    for v in g['vias']:
        if not set(layers).intersection(v['layer_membership']):continue
        if v['drill_nm']<=0 or v['drill_nm']%2:errors.append({'uuid':v['uuid'],'reason':'via drill unavailable'});continue
        holes.append({'kind':'via','uuid':v['uuid'],'net_code':v['net_code'],'center':v['position_nm'],'radius':v['drill_nm']//2})
    return holes,errors

def exact_pad(p,layer_id):
    rows=[l for l in p['layers'] if l['id']==layer_id]
    if len(rows)!=1:return None
    l=rows[0];h=p['effective_hole'];size=l['size_nm']
    if not (p['is_pth'] and p['drill_is_round'] and l['on_layer'] and l['flash_layer'] and l['shape_is_circle'] and size[0]==size[1] and l['offset_nm']==[0,0] and p['position_nm']==l['shape_position_nm']==h['start_nm']==h['end_nm']):return None
    if not 0<h['width_nm']<size[0] or h['width_nm']%2 or size[0]%2:return None
    return {'uuid':p['uuid'],'terminal':p['logical_terminal'],'net_code':p['net_code'],'center':p['position_nm'],'outer_radius':size[0]//2,'drill_radius':h['width_nm']//2}

def strict_dimensions(g):
    if type(g.get('native_max_error_nm')) is not int or g['native_max_error_nm']<=0:raise Unsupported('nonpositive/malformed maximum error')
    for pad in g['pads']:
        h=pad['effective_hole'];w=h['width_nm'];size=pad['drill_size_nm']
        if type(w) is not int or w<0 or len(size)!=2 or any(type(x) is not int or x<0 for x in size):raise Unsupported('negative/malformed pad hole dimension')
        if w==0:
            if size!=[0,0] or pad['is_pth']:raise Unsupported('zero hole inconsistent with native pad')
        elif (pad['drill_is_round'] is not True or size!=[w,w] or h['start_nm']!=h['end_nm']):raise Unsupported('positive physical pad hole is not exact round disk')
    for via in g['vias']:
        if type(via['drill_nm']) is not int or via['drill_nm']<=0:raise Unsupported('nonpositive/malformed via hole')

def local_key(p,center,angle):
    co,si=math.cos(angle),math.sin(angle);x,y=p[0]-center[0],p[1]-center[1]
    return (round(co*x+si*y,6),round(-si*x+co*y,6))

CAPS={'seconds':8,'operations':12000000,'nodes_per_body':64,'edges_per_body':2016,'bodies':8,'vertices_total':2048,'pads':512,'vias':512,'anchors_per_body':8,'annular_samples_per_terminal':8,'returned_proposals':4}

def audit_observations(g,guard):
    strict_dimensions(g)
    if g.get('schema')!=1 or g.get('api_error_count')!=0 or g.get('source_unchanged') is not True:raise Unsupported('incomplete native observation schema')
    if len(g['layers'])!=1 or not g['net_code'] or len(g['pads'])>CAPS['pads'] or len(g['vias'])>CAPS['vias']:raise Unsupported('bounded single-layer population required')
    guard.charge(len(g['pads'])+len(g['vias']))
    ids=[p['uuid'] for p in g['pads']]+[v['uuid'] for v in g['vias']]
    if len(ids)!=len(set(ids)):raise Unsupported('duplicate native object UUID')
    targets=[p for p in g['pads'] if p['uuid']==g['target_pad_uuid']]
    if len(targets)!=1 or targets[0]['net_code']!=g['net_code']:raise Unsupported('target identity/net mismatch')
    body_keys=[(b['layer_id'],b['native_outline_index']) for b in g['bodies']]
    if len(body_keys)!=len(set(body_keys)):raise Unsupported('duplicate filled outline identity')
    layer=g['layers'][0]['id'];bodies=[b for b in g['bodies'] if b['selected']]
    if not 2<=len(bodies)<=CAPS['bodies'] or sum(len(b['outer_nm']) for b in bodies)>CAPS['vertices_total']:raise Unsupported('selected body cap')
    holes,errors=drill_census(g)
    if errors:raise Unsupported('physical drill census unsupported')
    for b in bodies:
        if b['zone_uuid']!=g['zone_uuid'] or b['layer_id']!=layer or b['net_code']!=g['net_code']:raise Unsupported('selected body zone/layer/net mismatch')
        if b['holes_nm'] or b['hole_count'] or b['native_total_arc_count'] or b['native_outer_closed'] is not True:raise Unsupported('arcs, explicit holes, or unclosed fill domain')
        poly=b['outer_nm'];validate_domain(poly,holes)
        if len({tuple(p) for p in poly})!=len(poly):raise Unsupported('repeated vertex topology unsupported')
        pairs=list(edges(poly))
        for i,(a,bb) in enumerate(pairs):
            for j,(cc,dd) in enumerate(pairs[i+1:],i+1):
                guard.charge()
                if j==i+1 or (i==0 and j==len(poly)-1):continue
                if not bbox_gap_sq(a,bb,cc,dd) and intersects(a,bb,cc,dd):raise Unsupported('exact contour crossing/touching unsupported')
    target=exact_pad(targets[0],layer)
    if target is None:raise Unsupported('target is not exact concentric round PTH')
    terms=[p for row in g['pads'] if (p:=exact_pad(row,layer)) is not None and p['net_code']==g['net_code'] and p['terminal']!=target['terminal']]
    width=g['class']['width_nm'];margin=max(1,g['native_max_error_nm'])
    if type(width) is not int or type(margin) is not int or not 0<margin<width/4:raise Unsupported('width/margin invalid')
    return bodies,holes,target,terms,targets[0]['orientation_degrees'],width,margin

def bridge_clear(a,b,holes,margin,guard):
    # The NEW copper need not remain in the old fill. It must avoid all drills.
    for h in holes:
        guard.charge()
        if not farther_point_segment(h['center'],a,b,h['radius']+margin):return False
    return True

def waypoints(poly,width,guard):
    result=[];n=len(poly)
    for i,p in enumerate(poly):
        ends=[]
        for direction in (-1,1):
            length=0;j=i;steps=0
            while length<2*width and steps<n:
                guard.charge();nxt=(j+direction)%n;length+=math.dist(poly[j],poly[nxt]);j=nxt;steps+=1
            ends.append(poly[j])
        result.append([round((ends[0][k]+2*p[k]+ends[1][k])/4) for k in (0,1)])
    return list({tuple(p):p for p in result}.values())

def construct_graph(poly,holes,anchors,pads,margin,width,angle,center,guard):
    theta=math.radians(angle);key=lambda p:local_key(p,center,theta)
    nodes=[];labels=[]
    def add(p,label=None):
        if p in nodes:
            if label is not None:labels[nodes.index(p)].append(label)
            return nodes.index(p)
        if len(nodes)>=CAPS['nodes_per_body']:raise Unsupported('root witness node cap exceeded')
        nodes.append(p);labels.append([] if label is None else [label]);return len(nodes)-1
    anchor_nodes=[add(p) for p in anchors]
    for pad in pads:
        radius=(pad['drill_radius']+pad['outer_radius'])/2
        for i in range(CAPS['annular_samples_per_terminal']):
            a=theta+i*math.pi/4;p=[round(pad['center'][0]+radius*math.cos(a)),round(pad['center'][1]+radius*math.sin(a))]
            if annular(p,pad,margin) and certified_leg(p,p,poly,holes,margin,guard):add(p,pad['terminal'])
    roots=len(nodes)
    candidates=[]
    for p in waypoints(poly,width,guard):
        if p not in nodes and certified_leg(p,p,poly,holes,margin,guard):candidates.append(p)
    candidate_count=len(candidates)
    # Fixed farthest-point coverage of the same geometry-derived candidates,
    # seeded by all anchors/terminal witnesses. No board/net/outline ID ranking.
    distances={tuple(p):min((point_sq(p,q) for q in nodes),default=0) for p in candidates}
    guard.charge(len(candidates)*len(nodes))
    while candidates and len(nodes)<CAPS['nodes_per_body']:
        p=min(candidates,key=lambda p:(-distances[tuple(p)],key(p)))
        add(p);candidates.remove(p)
        for q in candidates:
            guard.charge();distances[tuple(q)]=min(distances[tuple(q)],point_sq(p,q))
    adjacency=[[] for _ in nodes];tested=0;accepted=0
    for i,a in enumerate(nodes):
        for j,b in enumerate(nodes[i+1:],i+1):
            tested+=1
            if tested>CAPS['edges_per_body']:raise Unsupported('edge cap')
            if certified_leg(a,b,poly,holes,margin,guard):
                length=math.dist(a,b);adjacency[i].append((j,length));adjacency[j].append((i,length));accepted+=1
    results=[]
    for start in anchor_nodes:
        distances={start:0.};previous={};heap=[(0.,start)];seen=set()
        while heap:
            guard.charge();distance,node=heapq.heappop(heap)
            if node in seen:continue
            seen.add(node)
            if labels[node]:
                seq=[];cursor=node
                while True:
                    seq.append(nodes[cursor])
                    if cursor==start:break
                    cursor=previous[cursor]
                seq.reverse()
                for terminal in labels[node]:results.append({'anchor':nodes[start],'path':seq,'terminal':terminal,'path_length_nm':distance})
            for other,weight in adjacency[node]:
                nd=distance+weight
                if nd<distances.get(other,float('inf')):distances[other]=nd;previous[other]=node;heapq.heappush(heap,(nd,other))
    guard.charge()
    return results,{'root_nodes':roots,'qualified_waypoints':candidate_count,'nodes':len(nodes),'edges_tested':tested,'edges_accepted':accepted,'path_count':len(results),'max_path_legs':max((len(p['path'])-1 for p in results),default=0)}

def propose(g,*,remaining_seconds,binding_verified=False):
    if binding_verified is not True:raise Unsupported('caller has not verified geometry/report/source binding')
    guard=Guard(min(CAPS['seconds'],remaining_seconds()),CAPS['operations'],remaining_seconds)
    bodies,holes,target,terms,angle,width,margin=audit_observations(g,guard)
    theta=math.radians(angle);co,si=math.cos(theta),math.sin(theta)
    def world(q):return [round(target['center'][0]+co*q[0]-si*q[1]),round(target['center'][1]+si*q[0]+co*q[1])]
    grid=[(i*width/4,j*width/4) for i in range(-16,17) for j in range(-16,17)];grid.sort(key=lambda p:(point_sq(p,(0,0)),p))
    cache=[];stats=[]
    for body in bodies:
        poly=body['outer_nm'];anchors=[]
        for q in grid:
            p=world(q)
            if certified_leg(p,p,poly,holes,margin,guard):anchors.append(p)
            if len(anchors)==CAPS['anchors_per_body']:break
        paths,stat=construct_graph(poly,holes,anchors,[target]+terms,margin,width,angle,target['center'],guard)
        source=[p for p in paths if p['terminal']==target['terminal']];dest=[p for p in paths if p['terminal']!=target['terminal']]
        cache.append((body,source,dest));stats.append(dict(stat,outline_index=body['native_outline_index'],source_paths=len(source),destination_paths=len(dest)))
    proposals=[];bridge_hole_rejections=0
    for source,source_paths,_ in cache:
        for dest,_,dest_paths in cache:
            if source is dest:continue
            for a in source_paths:
                for b in dest_paths:
                    guard.charge();length=math.dist(a['anchor'],b['anchor'])
                    if not width/2<length<=8*width:continue
                    if not bridge_clear(a['anchor'],b['anchor'],holes,margin,guard):bridge_hole_rejections+=1;continue
                    row={'start_nm':a['anchor'],'end_nm':b['anchor'],'width_nm':width,'layer':g['layers'][0]['canonical'],'net_code':g['net_code'],'source_outline_index':source['native_outline_index'],'destination_outline_index':dest['native_outline_index'],'target_logical_terminal':target['terminal'],'other_logical_terminal':b['terminal'],'source_copper_path_nm':a['path'],'destination_copper_path_nm':b['path'],'copper_path_margin_nm':margin,'length_nm':length,'routing_accepted':False,'native_validated':False}
                    score=(length,a['path_length_nm']+b['path_length_nm'],local_key(a['anchor'],target['center'],theta),local_key(b['anchor'],target['center'],theta))
                    existing=[x for x in proposals if (x[1]['start_nm'],x[1]['end_nm'])==(row['start_nm'],row['end_nm'])]
                    if existing:
                        if score>=existing[0][0]:continue
                        proposals.remove(existing[0])
                    proposals.append((score,row));proposals.sort(key=lambda item:item[0]);proposals=proposals[:CAPS['returned_proposals']]
    guard.charge()
    return {'status':'diagnostic_path_candidates_found' if proposals else 'bounded_graph_found_no_certificate','path_certificate_candidates':[p for _,p in proposals],'body_stats':stats,'operations_used':guard.used,'margin_nm':margin,'physical_hole_count':len(holes),'bridge_hole_rejections':bridge_hole_rejections,'native_executed':False,'solver_executed':False,'proposal_scene_qualified':False,'whole_body_certificate_qualified':False,'routing_accepted':False,'caps':CAPS,'limits':['positive-margin saved-fill path existence only; no global component, ampacity or native acceptance claim','candidate bridge centerline clears all drills; full new track capsule/foreign objects still require native validation','shared caller budget checked periodically; cooperative guard can overshoot bounded operations','post-refill path certificate has not been evaluated']}

def verify_proposals(g,receipt,*,remaining_seconds):
    strict_dimensions(g)
    guard=Guard(seconds=min(8,remaining_seconds()),operations=12000000,remaining_seconds=remaining_seconds)
    bodies,holes,target,terms,angle,width,margin=audit_observations(g,guard)
    proposals=receipt.get('path_certificate_candidates')
    if receipt.get('status')!='diagnostic_path_candidates_found' or not isinstance(proposals,list) or not 1<=len(proposals)<=4:raise Unsupported('bounded generated proposals unavailable')
    layer=g['layers'][0]['canonical'];byindex={b['native_outline_index']:b for b in bodies}
    terminals={tuple(p['terminal']):[] for p in terms}
    for term in terms:terminals[tuple(term['terminal'])].append(term)
    proofs=[]
    for proposal in proposals:
        if (proposal.get('net_code')!=g['net_code'] or proposal.get('layer')!=layer or proposal.get('width_nm')!=width or proposal.get('copper_path_margin_nm')!=margin or proposal.get('target_logical_terminal')!=target['terminal']):raise Unsupported('proposal target/net/layer/width/margin mismatch')
        other=tuple(proposal['other_logical_terminal'])
        if other==tuple(target['terminal']) or len(terminals.get(other,[]))!=1:raise Unsupported('destination logical terminal ambiguous/identical')
        start,end=proposal['start_nm'],proposal['end_nm']
        if not valid_point(start) or not valid_point(end) or not width/2<math.dist(start,end)<=8*width:raise Unsupported('bridge geometry outside declared bounds')
        indexes=[proposal['source_outline_index'],proposal['destination_outline_index']]
        if indexes[0]==indexes[1] or any(i not in byindex for i in indexes):raise Unsupported('distinct selected body identities required')
        for label,anchor,pad,index in [('source',start,target,indexes[0]),('destination',end,terminals[other][0],indexes[1])]:
            path=proposal[label+'_copper_path_nm'];poly=byindex[index]['outer_nm']
            if not isinstance(path,list) or not 1<=len(path)<=64 or path[0]!=anchor or not all(valid_point(p) for p in path):raise Unsupported('path endpoints/schema invalid')
            if not annular(path[-1],pad,margin):raise Unsupported('path does not end in strict independent annulus')
            legs=list(zip(path,path[1:])) or [(path[0],path[0])]
            if any(not certified_leg(a,b,poly,holes,margin,guard) for a,b in legs):raise Unsupported('saved copper path does not meet boundary/drill certificate')
        if not bridge_clear(start,end,holes,margin,guard):raise Unsupported('bridge centerline intersects physical hole/margin')
        proofs.append({'source_outline':indexes[0],'destination_outline':indexes[1],'other_terminal':list(other),'margin_nm':margin,'physical_holes_checked':len(holes),'passed':True})
    guard.charge()
    return proofs

def uuid_index(tree,sx):
    owners={}
    def walk(node):
        if not isinstance(node,list) or not node:return
        field=sx.one(node,'uuid')
        if field is not None:
            if len(field)!=2 or not isinstance(field[1],str):raise Unsupported('malformed candidate UUID')
            owners.setdefault(sx.unquote(field[1]),[]).append(node)
        for child in node[1:]:walk(child)
    walk(tree)
    # Native dimensions and their nested display text may share one UUID.
    # Preserve those immutable objects; require uniqueness of referenced copper.
    return owners

def nm(atom):
    v=Decimal(atom)*1000000
    if not v.is_finite() or v!=v.to_integral_value():raise Unsupported('noninteger native coordinate')
    return int(v)

def mm(value):
    if type(value) is not int:raise Unsupported('noninteger track coordinate')
    return format(Decimal(value)/1000000,'f')

def fill_binding(tree,g,sx):
    items=uuid_index(tree,sx);zones=items.get(g['zone_uuid'],[]);targets=items.get(g['target_pad_uuid'],[])
    if len(zones)!=1 or zones[0][0]!='zone' or len(targets)!=1 or targets[0][0]!='pad':raise Unsupported('native finding UUID not typed/unique in board')
    zone,target=zones[0],targets[0]
    layer=g['layers'][0]['canonical']
    if sx.one(zone,'net')!=['net',str(g['net_code'])] or sx.one(zone,'layer')!=['layer','"'+layer+'"']:raise Unsupported('saved zone net/layer differs from native observation')
    saved=sx.children(zone,'filled_polygon')
    native=[b for b in g['bodies'] if b['layer_id']==g['layers'][0]['id']]
    if len(saved)!=len(native):raise Unsupported('saved/native filled-body count differs')
    for b in native:
        index=b['native_outline_index']
        if type(index) is not int or not 0<=index<len(saved):raise Unsupported('native outline index outside saved fill')
        poly=saved[index]
        if sx.one(poly,'layer')!=['layer','"'+layer+'"'] or b['hole_count'] or b['holes_nm']:raise Unsupported('unsupported explicit filled hole or layer mismatch')
        points=sx.one(poly,'pts')
        if points is None or any(p[0]!='xy' or len(p)!=3 for p in points[1:]):raise Unsupported('unsupported filled contour atoms')
        actual=[[nm(p[1]),nm(p[2])] for p in points[1:]]
        if actual!=b['outer_nm']:raise Unsupported('saved/native fill vertices differ')
    return saved
