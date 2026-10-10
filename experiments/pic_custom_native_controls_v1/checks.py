"""Owned-scene observation/predicate checks, not a production custom-pad policy."""
import copy
from decimal import Decimal
from autorouter import pipeline as p,sexpr as sx,board_floor as g
from autorouter.adapter import _parse_dsn,_check_units
from experiments.pic_custom_observer_v1.mapping import dsn_correspondence
import fixture as fx
import recipes

def polygon(shape):
    if shape.get('arc_count')!=0 or len(shape.get('outlines',[]))!=1:raise ValueError('unexpected polygon topology')
    row=shape['outlines'][0];line=row['outline'];points=line['points_nm']
    if row.get('holes')!=[] or line.get('closed') is not True or shape.get('total_vertices')!=len(points):raise ValueError('unexpected polygon holes/closure')
    if any(len(pt)!=2 or any(type(n) is not int or abs(n)>10**10 for n in pt) for pt in points):raise ValueError('invalid polygon coordinates')
    return fx.poly_ring(points)

def observe(native,custom,raw,scene,project):
    """Exact original settings + fixed geometry precede every DRC interpretation."""
    expected={r['uuid']:r for r in scene['pads']};routes={r['uuid']:r for r in scene['tracks']}
    layer=scene['copper_layer'];back=scene['variant']=='back90';angle=90 if back else 0
    if (native.get('context_schema')!=1 or native.get('native_version')!='10.0.0' or native.get('units')!='integer nanometres'
            or native.get('mode')!='export' or native.get('board_saved') is not False or native.get('routing_accepted') is not False):raise ValueError('native context scope differs')
    if (len(native['pads'])!=4 or {r['uuid'] for r in native['pads']}!=set(expected)
            or len(native['routes'])!=2 or {r['uuid'] for r in native['routes']}!=set(routes)
            or native.get('obstacles')!=[]):raise ValueError('native owned census/obstacles differs')
    classes=[row for row in project['net_settings']['classes'] if row['name']=='Default']
    if len(classes)!=1:raise ValueError('original Default class ambiguous')
    cls=classes[0]
    dims={a:int(Decimal(str(cls[b]))*1000000) for a,b in [('width_nm','track_width'),('clearance_nm','clearance'),('via_diameter_nm','via_diameter'),('via_drill_nm','via_drill')]}
    if dims['width_nm']!=500000 or dims['clearance_nm']!=250000:raise ValueError('original Default intent changed')
    rows=native['nets'];codes={r['name']:r['netcode'] for r in rows}
    if len(rows)!=2 or set(codes)!={'CONTACT','FOREIGN'} or len(set(codes.values()))!=2 or any(type(code) is not int or code<=0 for code in codes.values()):raise ValueError('native two-net identity differs')
    for row in rows:
        if row!={'name':row['name'],'netcode':codes[row['name']],'class':'Default','copper_pad_count':2,**dims}:raise ValueError('native Default dimensions/resolution differs')
    floors={key:int(Decimal(str(project['board']['design_settings']['rules'][key]))*1000000) for key in g.FLOORS}
    if native['floors_nm']!=floors:raise ValueError('native original floors differ')
    for row in native['pads']:
        item=expected[row['uuid']]
        if row!={'uuid':item['uuid'],'reference':item['reference'],'number':'1','net':item['net'],'netcode':codes[item['net']],'copper_layers':[layer],'position_nm':list(item['at'])}:raise ValueError('native terminal mapping/position differs')
    for row in native['routes']:
        item=routes[row['uuid']]
        if row!={'uuid':item['uuid'],'net':item['net'],'kind':'segment','width_nm':500000,'start_nm':list(item['start']),'end_nm':list(item['end']),'layer':layer}:raise ValueError('native route geometry differs')
    if (custom.get('same_loaded_board') is not True or custom.get('board_saved') is not False
            or custom.get('geometry_qualified') is not False or custom.get('routing_accepted') is not False):raise ValueError('unexpected custom scope')
    state=custom['observation_before_export']
    if state!=custom['observation_after_export']:raise ValueError('export did not restore complete state')
    if state.get('total_pad_count')!=4 or state.get('schema')!=1 or state.get('routing_accepted') is not False or state.get('geometry_qualified') is not False:raise ValueError('native callback census/scope differs')
    fps={r['footprint_uuid']:r for r in scene['pads']}
    if len(state['all_footprints'])!=4 or {r['uuid'] for r in state['all_footprints']}!=set(fps):raise ValueError('native footprint census differs')
    for row in state['all_footprints']:
        item=fps[row['uuid']]
        if type(row.get('flipped')) is not bool:raise ValueError('native flipped flag differs')
        if row!={'uuid':item['footprint_uuid'],'reference':item['reference'],'position_nm':list(item['at']),'orientation_degrees':angle,'layer':layer,'flipped':back}:raise ValueError('native footprint transform differs')
    if len(state['all_terminals'])!=4 or {r['uuid'] for r in state['all_terminals']}!=set(expected):raise ValueError('native callback terminal census differs')
    for row in state['all_terminals']:
        item=expected[row['uuid']]
        if type(row.get('flipped')) is not bool:raise ValueError('native flipped flag differs')
        want=next(r for r in native['pads'] if r['uuid']==row['uuid'])
        if row!={**want,'footprint_uuid':item['footprint_uuid'],'fp_relative_position_nm':[0,0],'orientation_degrees':angle,'flipped':back}:raise ValueError('native callback terminal transform differs')
    expected_custom={uid:r for uid,r in expected.items() if 'polygon' in r}
    if len(state['pads'])!=2 or {r['uuid'] for r in state['pads']}!=set(expected_custom):raise ValueError('native custom census differs')
    for row in state['pads']:
        item=expected_custom[row['uuid']];source_poly=recipes.CONVEX if item['id']=='CONVEX' else recipes.CONCAVE
        local=tuple((x,-y if back else y) for x,y in source_poly)
        if type(row.get('pad_flipped')) is not bool or type(row.get('footprint_flipped')) is not bool:raise ValueError('native custom flipped flag differs')
        for key,want in {'reference':item['reference'],'number':'1','net':item['net'],'netcode':codes[item['net']],
            'copper_layers':[layer],'shape':'custom','anchor':'rect','attribute':'smd','size_nm':[300000,300000],
            'offset_nm':[0,0],'drill_nm':[0,0],'position_nm':list(item['at']),'fp_relative_position_nm':[0,0],
            'orientation_degrees':angle,'pad_flipped':back,'footprint_uuid':item['footprint_uuid'],
            'footprint_position_nm':list(item['at']),'footprint_orientation_degrees':angle,'footprint_flipped':back}.items():
            if row.get(key)!=want:raise ValueError('native custom field differs: '+key)
        if polygon(row['merged_local'])!=fx.poly_ring(local):raise ValueError('native local copper differs')
        if any(polygon(row[key])!=fx.poly_ring(item['polygon']) for key in ('transformed_world','effective_world')):raise ValueError('native world copper differs')
    correspondence=dsn_correspondence(raw,native,state['pads'])
    if correspondence['terminal_count']!=4:raise ValueError('native DSN terminal census differs')
    tree=_parse_dsn(raw.decode());_check_units(tree)
    if len(sx.children(sx.one(tree,'network'),'net'))!=2:raise ValueError('native DSN net census differs')
    for row in correspondence['custom_pads']:
        item=expected_custom[row['uuid']];shape=recipes.CONVEX if item['id']=='CONVEX' else recipes.CONCAVE
        # These exact local polygons are Y-symmetric. This does not qualify
        # arbitrary chiral reflection or a general DSN-to-world transform.
        want=fx.poly_ring(recipes.hull(tuple((x,-y) for x,y in shape)))
        shapes=sx.children(row['padstack_ast'],'shape')
        if len(shapes)!=1:raise ValueError('unexpected custom DSN shape count')
        poly=shapes[0][1]
        if poly[:3]!=['polygon','top_layer','0']:raise ValueError('unexpected custom DSN layer/aperture')
        exact=[Decimal(value)*1000 for value in poly[3:]]
        if any(not value.is_finite() or value!=value.to_integral_value() for value in exact):raise ValueError('nonintegral native DSN hull coordinates')
        points=[tuple(map(int,exact[i:i+2])) for i in range(0,len(exact),2)]
        if fx.poly_ring(points)!=want:raise ValueError('native DSN custom hull differs')
        pin=row['pin_ast']
        if pin[2:]!=['1','0','0'] and pin[2:]!=['"1"','0','0']:raise ValueError('unexpected custom DSN pin offset/rotation')
        place=row['placement_ast']
        if (len(place)!=7 or sx.unquote(place[1])!=item['reference'] or
            [Decimal(place[2])*1000,-Decimal(place[3])*1000]!=list(item['at']) or
            place[4]!=('back' if back else 'front') or Decimal(place[5])!=(270 if back else 0) or
            place[6][0]!='PN' or len(place[6])!=2 or sx.unquote(place[6][1])!='Owned_'+item['reference']):
            raise ValueError('native DSN placement transform differs')
    return {'geometry_matches_fixed_recipe':True,'default_only_settings_observed':True,'nondefault_resolution_qualified':False,
        'arbitrary_reflection_qualified':False,'custom_routing_support_qualified':False,'correspondence':correspondence,
        'native_floors_nm':floors,'native_nets':copy.deepcopy(rows)}

def predicate(case,native,raw,scene,ignored):
    """Expected findings must occur in the correct raw native report section."""
    if any(type(native.get(k)) is not int or native[k]<0 for k in ('opens','blocking','warnings','exclusions')):return False,[]
    if (not isinstance(native.get('findings'),list) or any(not isinstance(row,dict) or row.get('type') not in (p.KNOWN_CHECKS|{'padstack_invalid'}) for row in native['findings'])):return False,[]
    if native.get('exclusions') or sorted(r['key'] for r in native.get('ignored_checks',[]))!=ignored:return False,[]
    if raw.get('schematic_parity')!=[] or native['findings']!=raw['violations']+raw['unconnected_items']:return False,[]
    if case=='positive':return p.native_accepted(native),[]
    pads={r['id']:r['uuid'] for r in scene['pads']};tracks={r['id']:r['uuid'] for r in scene['tracks']}
    def target(row):
        ids={item.get('uuid') for item in row.get('items',[])}
        if row.get('severity')!='error' or row.get('excluded',False):return False
        if case=='false_hull':return row.get('type')=='unconnected_items' and pads['CONCAVE'] in ids and bool(ids & {pads['CONVEX'],tracks['CONTACT_TRACK']}) and ids<={pads['CONCAVE'],pads['CONVEX'],tracks['CONTACT_TRACK']}
        return row.get('type') in ('clearance','shorting_items') and len(row.get('items',[]))==2 and ids=={pads['CONCAVE'],tracks['FOREIGN_TRACK']}
    if case=='false_hull':
        hits=raw['unconnected_items']
        if not hits or native['opens']!=len(hits) or native['blocking']!=0 or not all(target(row) for row in hits):return False,[]
    elif case=='foreign_intrusion':
        if native['opens'] or raw['unconnected_items']:return False,[]
        hits=[r for r in raw['violations'] if r.get('severity')=='error']
        required=[row for row in hits if target(row)]
        companions=[row for row in hits if not target(row)]
        pair={pads['CONCAVE'],tracks['FOREIGN_TRACK']}
        def mask_companion(row):
            return (row.get('type')=='solder_mask_bridge' and row.get('severity')=='error'
                and not row.get('excluded',False) and len(row.get('items',[]))==2
                and {item.get('uuid') for item in row['items']}==pair)
        if (not required or native['blocking']!=len(hits) or len(companions)>1
                or not all(mask_companion(row) for row in companions)):return False,[]
    else:raise ValueError('unknown control case')
    clean=copy.deepcopy(native);clean.update(opens=0,blocking=0,findings=[row for row in native['findings'] if row not in hits])
    return p.native_accepted(clean),copy.deepcopy(hits)
