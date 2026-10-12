"""Compare actual importer observations, retaining hypothesis failures without accepting routing."""
from fractions import Fraction
import math
from derive import IDS, canonical_ring


def number(n):
    if type(n) not in (int,float) or not math.isfinite(n) or abs(n)>10**9: raise ValueError('bounded finite numeric observation')
    return Fraction(str(n))
def point(p):
    if not isinstance(p,list) or len(p)!=2:raise ValueError('two-coordinate point')
    return tuple(number(n) for n in p)


def exact_trace_union(traces, target, layer):
    """Only segmentation is allowed: exact collinear same-width copper, no gap/overhang/overlap."""
    if not traces or len(traces)>32:return False
    start=point(target['start_um']);end=point(target['end_um']);delta=(end[0]-start[0],end[1]-start[1])
    axis=0 if delta[0] else 1
    if not delta[axis]:raise ValueError('zero original segment')
    intervals=[]
    for trace in traces:
        if trace.get('net')!=target['net'] or trace.get('layer')!=layer or number(trace['width_um'])!=target['width_um']:return False
        corners=trace.get('corners_um')
        if not isinstance(corners,list) or not 2<=len(corners)<=32:raise ValueError('bounded full trace corners required')
        if trace.get('corner_classes')!=['app.freerouting.geometry.planar.IntPoint']*len(corners):return False
        points=[point(p) for p in corners]
        if list(corners[0])!=trace['start_um'] or list(corners[-1])!=trace['end_um']:return False
        coordinates=[]
        for p in points:
            diff=(p[0]-start[0],p[1]-start[1])
            if diff[0]*delta[1]!=diff[1]*delta[0]:return False
            t=diff[axis]/delta[axis]
            if not 0<=t<=1:return False
            coordinates.append(t)
        for a,b in zip(coordinates,coordinates[1:]):
            if a==b:return False
            intervals.append(tuple(sorted((a,b))))
    cursor=Fraction(0)
    for a,b in sorted(intervals):
        if a!=cursor:return False
        cursor=b
    return cursor==1


def integer_coordinate_witness(item, state, *, area=False):
    points=item['ring_um' if area else 'corners_um']
    original=item.get('ring_board_integer' if area else 'corners_board_integer')
    classes=item.get('ring_classes' if area else 'corner_classes')
    if not isinstance(original,list) or len(original)!=len(points) or classes!=['app.freerouting.geometry.planar.IntPoint']*len(points):return False
    scale=number(state['board_units_per_um']);origin=point(state['board_origin_dsn_um'])
    if scale<=0:return False
    for raw,actual in zip(original,points):
        if not isinstance(raw,list) or len(raw)!=2 or any(type(n)is not int or abs(n)>2**31-1 for n in raw):return False
        if tuple(Fraction(raw[i])/scale+origin[i] for i in (0,1))!=point(actual):return False
    return True


def exact_area(item,state):
    if not integer_coordinate_witness(item,state,area=True):return None
    ring=item['ring_board_integer']; scale=number(state['board_units_per_um'])
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(ring,ring[1:]+ring[:1])))/(2*scale**2)


def state_comparison(state,want):
    pins=state['pins'];areas=state['areas'];traces=state['traces'];nets=state['nets']
    if not all(isinstance(v,list) for v in (pins,areas,traces,nets)):raise ValueError('item lists required')
    if len(pins)>16 or len(areas)>8 or len(traces)>32 or len(nets)>8:raise ValueError('observation population cap')
    allitems=pins+areas+traces;ids=[i['id'] for i in allitems]
    if any(type(x)is not int for x in ids) or len(set(ids))!=len(ids):raise ValueError('unique item identity')
    for i in allitems:
        for key in ('contacts','connected'):
            if not isinstance(i[key],list) or len(i[key])>64 or any(type(n)is not int for n in i[key]):raise ValueError('bounded contact identity')
    census=state.get('census',{})
    exact_census=(census.get('pins')==len(pins) and census.get('areas')==len(areas) and census.get('traces')==len(traces)
                  and census.get('vias')==0 and census.get('components')==4 and census.get('layers')==2) and len(pins)==4 and len(areas)==2 and len(nets)==2 and len(traces)>=2
    known_contacts=all(set(i[key])<=set(ids) for i in allitems for key in ('contacts','connected'))
    pmap={p['reference']:p for p in pins};amap={}
    pin_ok=exact_census and len(pmap)==4 and set(pmap)=={p['reference'] for p in want['pins']}
    for p in want['pins']:
        q=pmap.get(p['reference'],{})
        pin_ok &= all(q.get(k)==p[k] for k in ('number','net','position_um')) and q.get('layers')==[want['layer']]
        pin_ok &= q.get('padstack_name')==p['imported_padstack_name']
    name_map=want['padstack_name_map']
    pin_ok &= len(set(name_map.values()))==len(name_map) and all(name_map[p['padstack_name']]==p['imported_padstack_name'] for p in want['pins'])
    for a in want['areas']:
        found=[x for x in areas if canonical_ring(x['ring_um'])==canonical_ring(a['ring_um'])]
        if len(found)==1:amap[a['reference']]=found[0]
    area_ok=len(amap)==2 and len(areas)==2 and all(integer_coordinate_witness(x,state,area=True) and x['holes']==0 and x['net']=='CONTACT' and x['layer']==want['layer']
             and x['fixed']=='USER_FIXED' and exact_area(x,state)==next(a['area_um2'] for a in want['areas'] if a['reference']==ref)
             for ref,x in amap.items())
    for x in areas:number(x['area_api_um2'])  # Retain the API result, not a polygon-area oracle.
    anchor_ok=all(pmap.get(p['reference'],{}).get('bounds_um')==[p['position_um'][0]-150,p['position_um'][1]-150,p['position_um'][0]+150,p['position_um'][1]+150]
                  for p in want['pins'] if p['reference'] in ('CONCAVE','CONVEX'))
    traces_ok={t.get('net') for t in traces}=={'CONTACT','FOREIGN'};tmap={}
    for t in want['tracks']:
        members=[x for x in traces if x['net']==t['net']];tmap[t['id']]=members
        traces_ok &= exact_trace_union(members,t,want['layer']) and all(integer_coordinate_witness(x,state) for x in members)
    plane_ok={n['name'] for n in nets}=={'CONTACT','FOREIGN'} and all(n['contains_plane'] is False for n in nets)
    widths_ok=all(n.get('trace_width_um')==want['net_targets'][n['name']]['width_um'] for n in nets if n['name'] in want['net_targets']) and len(nets)==2
    # Matrix(false) is raw; pinned matrix(true) adds16 board units (not16 micrometres).
    margin=state.get('clearance_safety_margin_board_units')
    margin_ok=type(margin)is int and margin==16
    matrix_ok=bool(areas) and bool(tmap['FOREIGN_TRACK']) and all(
        t.get('area_raw_clearances_um',{}).get(str(a['id']))==want['net_targets']['CONTACT']['clearance_um']
        and t.get('area_raw_clearances_reverse_um',{}).get(str(a['id']))==want['net_targets']['CONTACT']['clearance_um']
        and number(t.get('area_clearances_um',{}).get(str(a['id'])))==number(want['net_targets']['CONTACT']['clearance_um'])+Fraction(16)/number(state['board_units_per_um'])
        for t in tmap['FOREIGN_TRACK'] for a in areas)
    matrix_ok &= margin_ok
    reciprocal=terminal_ok=False
    if pin_ok and area_ok and traces_ok and known_contacts:
        graph={i['id']:set(i['contacts']) for i in allitems}
        reciprocal=all(a in graph[b] for a,peers in graph.items() for b in peers)
        for ref,a in amap.items():
            p=pmap[ref];reciprocal &= a['id'] in p['contacts'] and p['id'] in a['contacts']
            ts=tmap['CONTACT_TRACK'];should=ref=='CONVEX' or want['kind']!='false_hull'
            reciprocal &= any(t['id'] in a['contacts'] for t in ts)==should and any(a['id'] in t['contacts'] for t in ts)==should
        terminal_ok=True;pin_ids={p['id'] for p in pins}
        for p in pins:
            peers={x['id'] for x in pins if x['net']==p['net']}
            if p['net']=='CONTACT' and want['kind']=='false_hull':peers={p['id']}
            engine={p['id']}|(pin_ids&set(p['connected']))
            reached={p['id']};todo=[p['id']]
            while todo:
                for target in graph[todo.pop()]-reached:reached.add(target);todo.append(target)
            terminal_ok &= engine==peers and (pin_ids&reached)==peers
    obstacle=state['mode']=='obstacle_true'
    flags_ok=bool(areas) and all(a['obstacle'] is obstacle for a in areas) and (state['mode']=='imported' or state['ignore_conduction'] is not obstacle)
    foreign=tmap['FOREIGN_TRACK'];blocked=want['kind']=='foreign_intrusion'
    clear_values=[t.get('tree_trace_check_clear') for t in foreign]
    # An anchor already blocks intrusion in001: false/imported states are observed, not isolation controls.
    obstruction_ok=bool(foreign) and all(type(v)is bool for v in clear_values)
    if obstacle:obstruction_ok &= all(clear_values) is not blocked
    if blocked and obstacle:
        obstruction_ok &= any(t.get('tree_trace_check_clear') is False and amap.get('CONCAVE',{}).get('id') in t.get('tree_overlap_ids',[]) for t in foreign)
    geometry_ok=pin_ok and anchor_ok and area_ok and traces_ok and plane_ok
    return {'mode':state['mode'],'observed_census':{'pins':len(pins),'areas':len(areas),'traces':len(traces),'nets':len(nets)},
            'exact_geometry_and_identity':bool(geometry_ok),'exact_trace_union':bool(traces_ok),
            'reciprocal_contacts':bool(reciprocal),'all_terminal_connectivity':bool(terminal_ok),
            'unchanged_width_targets':bool(widths_ok),'area_foreign_clearance_matches_native':bool(matrix_ok),
            'obstacle_flags_match':bool(flags_ok),'foreign_tree_check_matches':bool(obstruction_ok)}


def validate(observation,expected):
    if (observation.get('schema')!=2 or observation.get('scope')!='owned_area_contact_import_only'
        or observation.get('routing_executed') is not False or observation.get('native_executed') is not False
        or observation.get('units')!='micrometres'):raise ValueError('observation scope')
    rows=observation.get('cases')
    if not isinstance(rows,list) or [x.get('case') for x in rows]!=list(IDS):raise ValueError('six-case denominator')
    comparisons=[]
    for got,want in zip(rows,expected):
        if got.get('status')!='observed' or got.get('input_sha256')!=want['derived_sha256']:raise ValueError('actual import unavailable: '+want['case'])
        states=got.get('states')
        if not isinstance(states,list) or [s.get('mode') for s in states]!=['imported','obstacle_false','obstacle_true']:raise ValueError('state denominator')
        if not isinstance(got.get('parser_warnings'),list) or len(got['parser_warnings'])>32:raise ValueError('parser warning schema')
        matches=[state_comparison(s,want) for s in states]
        positive=matches[-1];false=matches[1];imported=matches[0]
        match=(not got['parser_warnings'] and all(x['exact_geometry_and_identity'] and x['unchanged_width_targets'] and x['area_foreign_clearance_matches_native'] for x in matches)
               and positive['reciprocal_contacts'] and positive['all_terminal_connectivity'] and positive['obstacle_flags_match']
               and positive['foreign_tree_check_matches'] and false['obstacle_flags_match'] and false['foreign_tree_check_matches'] and imported['obstacle_flags_match'])
        comparisons.append({'case':want['case'],'expected_observation_matches':bool(match),'states':matches})
    return comparisons
