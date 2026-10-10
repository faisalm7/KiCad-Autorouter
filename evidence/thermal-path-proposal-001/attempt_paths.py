"""Bounded pure development attempt. No board write or native execution."""
import hashlib,json,math,time
from fractions import Fraction
from pathlib import Path
import copper_path as c
import diagnose as d
ROOT=Path(__file__).resolve().parent

def local_key(p,center,angle):
    co,si=math.cos(angle),math.sin(angle);x,y=p[0]-center[0],p[1]-center[1]
    return (round(co*x+si*y,6),round(-si*x+co*y,6))
def waypoint_candidates(poly,width):
    # Move a local contour corner toward a chord spanning a physical distance.
    # Points are merely candidates; every accepted leg is independently proved.
    result=[];n=len(poly)
    for i,p in enumerate(poly):
        ends=[]
        for direction in (-1,1):
            length=0;j=i;steps=0
            while length<2*width and steps<n:
                nxt=(j+direction)%n;length+=math.dist(poly[j],poly[nxt]);j=nxt;steps+=1
            ends.append(poly[j])
        q=[round((ends[0][k]+2*p[k]+ends[1][k])/4) for k in (0,1)]
        result.append(q)
    return list({tuple(p):p for p in result}.values())

def run(g):
    guard=c.Guard(seconds=8,operations=2000000)
    if g['api_error_count'] or not g['source_unchanged'] or len(g['layers'])!=1:raise c.Unsupported('incomplete native observations')
    layer=g['layers'][0]['id'];width=g['class']['width_nm'];margin=max(1,g['native_max_error_nm'])
    holes,errors=d.drill_census(g)
    if errors:raise c.Unsupported('physical hole census unsupported')
    target_row=next(p for p in g['pads'] if p['uuid']==g['target_pad_uuid']);target=d.exact_pad(target_row,layer)
    if target is None:raise c.Unsupported('target exact concentric round PTH unavailable')
    angle=math.radians(target_row['orientation_degrees']);co,si=math.cos(angle),math.sin(angle)
    def world(q):return [round(target['center'][0]+co*q[0]-si*q[1]),round(target['center'][1]+si*q[0]+co*q[1])]
    terms=[p for row in g['pads'] if (p:=d.exact_pad(row,layer)) is not None and p['net_code']==g['net_code'] and p['terminal']!=target['terminal']]
    terms.sort(key=lambda p:(c.point_sq(p['center'],target['center']),local_key(p['center'],target['center'],angle)))
    # Annular witnesses must actually be inside the destination body, not just
    # near it. Complete exact leg checks below account for every physical hole.
    bodies=[b for b in g['bodies'] if b['selected']]
    if not 2<=len(bodies)<=8 or sum(len(b['outer_nm']) for b in bodies)>2048:raise c.Unsupported('body cap')
    grid=[(i*width/4,j*width/4) for i in range(-16,17) for j in range(-16,17)]
    grid.sort(key=lambda q:(q[0]*q[0]+q[1]*q[1],q))
    caches=[];stats=[]
    for body in bodies:
        if body['holes_nm'] or body['hole_count'] or body['native_total_arc_count'] or not body['native_outer_closed']:raise c.Unsupported('explicit holes/arcs/open contour outside current path scope')
        poly=body['outer_nm'];c.validate_domain(poly,holes);anchors=[]
        for q in grid:
            p=world(q)
            if c.certified_leg(p,p,poly,holes,margin,guard):anchors.append(p)
            if len(anchors)>=8:break
        waypoints=waypoint_candidates(poly,width)
        sources=[];destinations=[];tested_terms=0
        for anchor in anchors:
            ranked=sorted(waypoints,key=lambda p:(Fraction(*c.point_segment_sq(p,anchor,target['center'])),c.point_sq(p,anchor),local_key(p,target['center'],angle)))[:12]
            source=c.path_to_annulus(anchor,target,poly,holes,margin,ranked,target_row['orientation_degrees'],guard)
            if source:sources.append({'anchor':anchor,'path':source})
        # At most four geometrically nearest supported independent terminals.
        # Other terminals remain explicit untested candidates, not failures.
        for terminal in terms[:4]:
            tested_terms+=1
            for anchor in anchors:
                ranked=sorted(waypoints,key=lambda p:(Fraction(*c.point_segment_sq(p,anchor,terminal['center'])),c.point_sq(p,anchor),local_key(p,target['center'],angle)))[:12]
                path=c.path_to_annulus(anchor,terminal,poly,holes,margin,ranked,target_row['orientation_degrees'],guard)
                if path:destinations.append({'anchor':anchor,'path':path,'terminal':terminal})
        caches.append((body,sources,destinations))
        stats.append({'outline_index':body['native_outline_index'],'anchors':len(anchors),'source_paths':len(sources),'destination_paths':len(destinations),'supported_other_terminals':len(terms),'tested_nearest_terminals':tested_terms,'waypoint_candidates':len(waypoints)})
    proposals=[]
    for source,source_paths,_ in caches:
        for dest,_,dest_paths in caches:
            if source is dest:continue
            for a in source_paths:
                for b in dest_paths:
                    length=math.dist(a['anchor'],b['anchor'])
                    if not width/2<length<=8*width:continue
                    proposals.append({'start_nm':a['anchor'],'end_nm':b['anchor'],'width_nm':width,'layer':g['layers'][0]['canonical'],'net_code':g['net_code'],'source_outline_index':source['native_outline_index'],'destination_outline_index':dest['native_outline_index'],'target_logical_terminal':target['terminal'],'other_logical_terminal':b['terminal']['terminal'],'source_copper_path_nm':a['path'],'destination_copper_path_nm':b['path'],'copper_path_margin_nm':margin,'length_nm':length,'routing_accepted':False,'native_validated':False,'certificate_scope':'positive-margin saved-fill paths outside every physical round hole to target and distinct logical terminal annuli; no global component claim'})
    proposals.sort(key=lambda p:(p['length_nm'],local_key(p['start_nm'],target['center'],angle),local_key(p['end_nm'],target['center'],angle)))
    unique=[]
    for p in proposals:
        if not any((p['start_nm'],p['end_nm'])==(q['start_nm'],q['end_nm']) for q in unique):unique.append(p)
        if len(unique)==4:break
    return {'status':'copper_path_candidates_found' if unique else 'bounded_path_search_found_no_certificate','path_certificate_candidates':unique,'body_stats':stats,'operations_used':guard.used,'margin_nm':margin,'margin_policy':'max(native polygon maximum error, 1 nm); fixed before attempt; positive-width existence only, no ampacity claim','physical_hole_count':len(holes),'native_executed':False,'solver_executed':False,'proposal_scene_qualified':False,'whole_body_certificate_qualified':False,'routing_accepted':False,'caps':{'seconds':8,'operations':2000000,'anchors_per_body':8,'annular_samples':8,'waypoints_per_path':12,'nearest_other_terminals':4,'returned_proposals':4}}

if __name__=='__main__':
    start=time.monotonic();geometry=ROOT.parent/'native-export-001/geometry.json';before=d.digest(geometry)
    g=json.loads(geometry.read_text())
    try:result=run(g)
    except c.Unsupported as e:result={'status':'unsupported','reason':str(e),'path_certificate_candidates':[],'native_executed':False,'routing_accepted':False}
    result.update({'geometry_sha256':before,'geometry_unchanged':before==d.digest(geometry),'wall_seconds':time.monotonic()-start,'script_sha256':d.digest(Path(__file__)),'copper_path_sha256':d.digest(ROOT/'copper_path.py')})
    with (ROOT/'path-attempt-001.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
