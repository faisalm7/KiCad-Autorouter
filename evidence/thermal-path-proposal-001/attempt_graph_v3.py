"""One predeclared bounded multibend diagnostic; no KiCad/solver/board writes.

Wrapper corrects independent-review gaps in v2. Earlier attempts stay immutable.
"""
import heapq,json,math,time
from pathlib import Path
import copper_path as c
import diagnose as d
from attempt_paths_v2 import local_key
ROOT=Path(__file__).resolve().parent
CAPS={'seconds':8,'operations':12000000,'nodes_per_body':64,'edges_per_body':2016,'bodies':8,'vertices_total':2048,'pads':512,'vias':512,'anchors_per_body':8,'annular_samples_per_terminal':8,'returned_proposals':4}

def audit_observations(g,guard):
    if g.get('schema')!=1 or g.get('api_error_count')!=0 or g.get('source_unchanged') is not True:raise c.Unsupported('incomplete native observation schema')
    if len(g['layers'])!=1 or not g['net_code'] or len(g['pads'])>CAPS['pads'] or len(g['vias'])>CAPS['vias']:raise c.Unsupported('bounded single-layer population required')
    guard.charge(len(g['pads'])+len(g['vias']))
    ids=[p['uuid'] for p in g['pads']]+[v['uuid'] for v in g['vias']]
    if len(ids)!=len(set(ids)):raise c.Unsupported('duplicate native object UUID')
    targets=[p for p in g['pads'] if p['uuid']==g['target_pad_uuid']]
    if len(targets)!=1 or targets[0]['net_code']!=g['net_code']:raise c.Unsupported('target identity/net mismatch')
    body_keys=[(b['layer_id'],b['native_outline_index']) for b in g['bodies']]
    if len(body_keys)!=len(set(body_keys)):raise c.Unsupported('duplicate filled outline identity')
    layer=g['layers'][0]['id'];bodies=[b for b in g['bodies'] if b['selected']]
    if not 2<=len(bodies)<=CAPS['bodies'] or sum(len(b['outer_nm']) for b in bodies)>CAPS['vertices_total']:raise c.Unsupported('selected body cap')
    holes,errors=d.drill_census(g)
    if errors:raise c.Unsupported('physical drill census unsupported')
    for b in bodies:
        if b['zone_uuid']!=g['zone_uuid'] or b['layer_id']!=layer or b['net_code']!=g['net_code']:raise c.Unsupported('selected body zone/layer/net mismatch')
        if b['holes_nm'] or b['hole_count'] or b['native_total_arc_count'] or b['native_outer_closed'] is not True:raise c.Unsupported('arcs, explicit holes, or unclosed fill domain')
        poly=b['outer_nm'];c.validate_domain(poly,holes)
        if len({tuple(p) for p in poly})!=len(poly):raise c.Unsupported('repeated vertex topology unsupported')
        pairs=list(c.edges(poly))
        for i,(a,bb) in enumerate(pairs):
            for j,(cc,dd) in enumerate(pairs[i+1:],i+1):
                guard.charge()
                if j==i+1 or (i==0 and j==len(poly)-1):continue
                if not c.bbox_gap_sq(a,bb,cc,dd) and c.intersects(a,bb,cc,dd):raise c.Unsupported('exact contour crossing/touching unsupported')
    target=d.exact_pad(targets[0],layer)
    if target is None:raise c.Unsupported('target is not exact concentric round PTH')
    terms=[p for row in g['pads'] if (p:=d.exact_pad(row,layer)) is not None and p['net_code']==g['net_code'] and p['terminal']!=target['terminal']]
    width=g['class']['width_nm'];margin=max(1,g['native_max_error_nm'])
    if type(width) is not int or type(margin) is not int or not 0<margin<width/4:raise c.Unsupported('width/margin invalid')
    return bodies,holes,target,terms,targets[0]['orientation_degrees'],width,margin

def bridge_clear(a,b,holes,margin,guard):
    # The NEW copper need not remain in the old fill. It must avoid all drills.
    for h in holes:
        guard.charge()
        if not c.farther_point_segment(h['center'],a,b,h['radius']+margin):return False
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
        if len(nodes)>=CAPS['nodes_per_body']:raise c.Unsupported('root witness node cap exceeded')
        nodes.append(p);labels.append([] if label is None else [label]);return len(nodes)-1
    anchor_nodes=[add(p) for p in anchors]
    for pad in pads:
        radius=(pad['drill_radius']+pad['outer_radius'])/2
        for i in range(CAPS['annular_samples_per_terminal']):
            a=theta+i*math.pi/4;p=[round(pad['center'][0]+radius*math.cos(a)),round(pad['center'][1]+radius*math.sin(a))]
            if c.annular(p,pad,margin) and c.certified_leg(p,p,poly,holes,margin,guard):add(p,pad['terminal'])
    roots=len(nodes)
    candidates=[]
    for p in waypoints(poly,width,guard):
        if p not in nodes and c.certified_leg(p,p,poly,holes,margin,guard):candidates.append(p)
    candidate_count=len(candidates)
    # Fixed farthest-point coverage of the same geometry-derived candidates,
    # seeded by all anchors/terminal witnesses. No board/net/outline ID ranking.
    distances={tuple(p):min((c.point_sq(p,q) for q in nodes),default=0) for p in candidates}
    guard.charge(len(candidates)*len(nodes))
    while candidates and len(nodes)<CAPS['nodes_per_body']:
        p=min(candidates,key=lambda p:(-distances[tuple(p)],key(p)))
        add(p);candidates.remove(p)
        for q in candidates:
            guard.charge();distances[tuple(q)]=min(distances[tuple(q)],c.point_sq(p,q))
    adjacency=[[] for _ in nodes];tested=0;accepted=0
    for i,a in enumerate(nodes):
        for j,b in enumerate(nodes[i+1:],i+1):
            tested+=1
            if tested>CAPS['edges_per_body']:raise c.Unsupported('edge cap')
            if c.certified_leg(a,b,poly,holes,margin,guard):
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

def run(g,binding_verified=False):
    if binding_verified is not True:raise c.Unsupported('caller has not verified geometry/report/source binding')
    guard=c.Guard(CAPS['seconds'],CAPS['operations'])
    bodies,holes,target,terms,angle,width,margin=audit_observations(g,guard)
    theta=math.radians(angle);co,si=math.cos(theta),math.sin(theta)
    def world(q):return [round(target['center'][0]+co*q[0]-si*q[1]),round(target['center'][1]+si*q[0]+co*q[1])]
    grid=[(i*width/4,j*width/4) for i in range(-16,17) for j in range(-16,17)];grid.sort(key=lambda p:(c.point_sq(p,(0,0)),p))
    cache=[];stats=[]
    for body in bodies:
        poly=body['outer_nm'];anchors=[]
        for q in grid:
            p=world(q)
            if c.certified_leg(p,p,poly,holes,margin,guard):anchors.append(p)
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
    return {'status':'diagnostic_path_candidates_found' if proposals else 'bounded_graph_found_no_certificate','path_certificate_candidates':[p for _,p in proposals],'body_stats':stats,'operations_used':guard.used,'margin_nm':margin,'physical_hole_count':len(holes),'bridge_hole_rejections':bridge_hole_rejections,'native_executed':False,'solver_executed':False,'proposal_scene_qualified':False,'whole_body_certificate_qualified':False,'routing_accepted':False,'caps':CAPS,'limits':['positive-margin saved-fill path existence only; no global component, ampacity or native acceptance claim','candidate bridge centerline clears all drills; full new track capsule/foreign objects still require native validation','cooperative CPU/wall guard can overshoot bounded operations; not OS enforced','post-refill path certificate has not been evaluated']}

if __name__=='__main__':
    start=time.monotonic();probe=ROOT.parent/'native-export-001';geometry=probe/'geometry.json';summary=json.loads((probe/'summary.json').read_text());before=d.digest(geometry);g=json.loads(geometry.read_text())
    binding=(before==summary['geometry_sha256'] and g['board_sha256']==summary['candidate_sha256'] and summary['original_inputs_unchanged'] is True and summary['status']=='observations_complete')
    try:result=run(g,binding_verified=binding)
    except c.Unsupported as e:result={'status':'unsupported','reason':str(e),'path_certificate_candidates':[],'native_executed':False,'routing_accepted':False,'caps':CAPS}
    result.update({'geometry_sha256':before,'geometry_unchanged':before==d.digest(geometry),'wall_seconds':time.monotonic()-start,'script_sha256':d.digest(Path(__file__)),'copper_path_sha256':d.digest(ROOT/'copper_path.py'),'binding_verified':binding})
    with (ROOT/'path-attempt-003.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
