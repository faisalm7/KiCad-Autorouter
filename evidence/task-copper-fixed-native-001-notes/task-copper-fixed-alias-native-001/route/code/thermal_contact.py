"""Speculative one-track contact proposals; never certified thermal acceptance.

Caller binds fresh Native worker/report/source/code and validates every proposal
with original saved-refill/fullSCH/rules before adoption. Existing PTH/two-body
certificate APIs are deliberately untouched.
"""
import math,re
from decimal import Decimal,InvalidOperation
from . import sexpr as sx,thermal_geometry as geom,board_floor as floor
POLICY='native-thermal-contact-v1'
RAYS=((1,0),(0,1),(-1,0),(0,-1))
CAPS={'proposals':4,'samples_per_ray':32,'vertices':2048,'bodies':8,'seconds':2,'operations':1000000}

def report_layer(g):
    finding=g.get('finding')
    if not isinstance(finding,dict) or finding.get('type')!='starved_thermal' or finding.get('severity')!='error' or finding.get('excluded',False) is not False:raise geom.Unsupported('one bound unexcluded thermal required')
    items=finding.get('items')
    if not isinstance(items,list) or len(items)!=2 or any(not isinstance(i,dict) or not isinstance(i.get('uuid'),str) for i in items) or len({i['uuid'] for i in items})!=2:raise geom.Unsupported('exact thermal pad/zone identities required')
    pattern=r'Thermal relief connection to zone incomplete \(layer (F\.Cu|B\.Cu); zone min spoke count 2; actual 1\)'
    match=re.fullmatch(pattern,finding.get('description',''))
    if match is None:raise geom.Unsupported('explicit pinned report layer/two-spoke wording required')
    return match.group(1),finding

def _body_polygons(tree,g,layer):
    owners=geom.uuid_index(tree,sx);zones=owners.get(g['zone_uuid'],[])
    if len(zones)!=1 or zones[0][0]!='zone':raise geom.Unsupported('unique target zone required')
    zone=zones[0];selectors=sx.children(zone,'layer')+sx.children(zone,'layers')
    if len(selectors)!=1:raise geom.Unsupported('unique original zone layer selector required')
    declared=[sx.unquote(x) for x in selectors[0][1:]]
    if (not declared or len(declared)!=len(set(declared)) or any(x not in ('F.Cu','B.Cu') for x in declared)
            or sorted(declared)!=sorted(g['zone_copper_layers']) or layer not in declared):raise geom.Unsupported('original/Native zone layers differ')
    selected=[n for n in sx.children(zone,'filled_polygon') if sx.one(n,'layer')==['layer','"'+layer+'"']]
    bodies=g['bodies'];polygons=[]
    if not 1<=len(bodies)<=CAPS['bodies'] or len(selected)!=len(bodies):raise geom.Unsupported('saved/native target-layer body census differs')
    for index,(saved,body) in enumerate(zip(selected,bodies)):
        if (body['native_outline_index']!=index or body['zone_uuid']!=g['zone_uuid'] or body['net_code']!=g['net_code']
                or body['layer_id']!=g['layers'][0]['id'] or body['hole_count']!=0 or body['holes_nm']
                or body['native_outer_closed'] is not True or body['native_self_intersecting'] is not False or body['native_total_arc_count']!=0):raise geom.Unsupported('ambiguous target-layer filled domain')
        points=sx.one(saved,'pts')
        if points is None or any(not isinstance(n,list) or len(n)!=3 or n[0]!='xy' for n in points[1:]):raise geom.Unsupported('exact saved contour required')
        poly=[[geom.nm(n[1]),geom.nm(n[2])] for n in points[1:]]
        if poly!=body['outer_nm']:raise geom.Unsupported('actual saved/native fill vertices differ')
        geom.validate_domain(poly,[]);polygons.append(poly)
    if sum(map(len,polygons))>CAPS['vertices']:raise geom.Unsupported('target-layer contour vertex cap')
    return zone,polygons

def _geometry(g):
    layer,finding=report_layer(g)
    if (type(g.get('schema')) is not int or g['schema']!=1 or g.get('mode')!=POLICY or g.get('native_version')!='10.0.0'
            or type(g.get('api_error_count')) is not int or g['api_error_count']!=0 or g.get('source_unchanged') is not True or g.get('board_saved') is not False
            or not isinstance(g.get('board_sha256'),str) or re.fullmatch('[0-9a-f]{64}',g['board_sha256']) is None
            or len(g.get('layers',[]))!=1 or g['layers'][0]['canonical']!=layer or g.get('reported_layer')!=layer):raise geom.Unsupported('fresh explicit Native contact observation required')
    observed=[p for p in g['pads'] if p['uuid']==g['target_pad_uuid']]
    if len(observed)!=1:raise geom.Unsupported('unique target pad required')
    p=observed[0];ids={x['uuid'] for x in finding['items']}
    if ids!={g['zone_uuid'],g['target_pad_uuid']} or type(g['net_code']) is not int or g['net_code']<=0 or p['net_code']!=g['net_code']:raise geom.Unsupported('report target/zone/net differs')
    layers=[x for x in p['layers'] if x['id']==g['layers'][0]['id']]
    if len(layers)!=1:raise geom.Unsupported('unique target layer geometry required')
    shape=layers[0];center=p['position_nm'];size=shape['size_nm'];angle=p['orientation_degrees'];width=g['class']['width_nm'];error=g['native_max_error_nm']
    if (not geom.valid_point(center) or len(size)!=2 or any(type(v) is not int or v<=0 or v%2 for v in size)
            or type(width) is not int or width<=0 or width%2 or type(error) is not int or not 0<error<width//4
            or type(angle) not in (int,float) or not math.isfinite(angle) or angle%90!=0
            or shape['offset_nm']!=[0,0] or shape['shape_position_nm']!=center or shape['on_layer'] is not True or shape['flash_layer'] is not True):raise geom.Unsupported('ordinary exact orthogonal pad/width geometry required')
    radius=width//2+error
    if p['is_pth'] is False and (shape.get('shape_is_rect') is True or shape.get('shape_is_roundrect') is True):
        if (p['is_pth'] is not False or p['drill_size_nm']!=[0,0] or p['effective_hole']['width_nm']!=0
                or min(size)//2<=radius):raise geom.Unsupported('ordinary zero-hole SMD interior required')
        start_radius=0
    elif p['is_pth'] is True:
        exact=geom.exact_pad(p,g['layers'][0]['id'])
        if exact is None:raise geom.Unsupported('exact round PTH required')
        start_radius=(exact['drill_radius']+exact['outer_radius'])//2
        if not exact['drill_radius']+radius<start_radius<exact['outer_radius']-radius:raise geom.Unsupported('PTH annulus cannot contain track start')
    else:raise geom.Unsupported('target pad shape outside contact policy')
    bodies=g['bodies']
    if not 1<=len(bodies)<=CAPS['bodies'] or sum(len(b['outer_nm']) for b in bodies)>CAPS['vertices']:raise geom.Unsupported('bounded target-layer body census required')
    for index,body in enumerate(bodies):
        if (type(body['native_outline_index']) is not int or body['native_outline_index']!=index or body['zone_uuid']!=g['zone_uuid'] or body['net_code']!=g['net_code'] or body['layer_id']!=g['layers'][0]['id']
                or body['hole_count']!=0 or body['holes_nm'] or body['native_outer_closed'] is not True or body['native_self_intersecting'] is not False or body['native_total_arc_count']!=0):raise geom.Unsupported('ambiguous target-layer filled domain')
        geom.validate_domain(body['outer_nm'],[])
    return layer,p,shape,center,size,angle,width,error,radius,start_radius,[b['outer_nm'] for b in bodies]

def fill_binding(tree,g,sx):
    layer,p,shape,*_= _geometry(g)
    zone,polygons=_body_polygons(tree,g,layer);owners=geom.uuid_index(tree,sx);pads=owners.get(g['target_pad_uuid'],[])
    if len(pads)!=1 or pads[0][0]!='pad':raise geom.Unsupported('unique source target pad required')
    pad=pads[0];_,resolve=floor.source_net_identity(tree)
    if resolve(sx.one(pad,'net'))!=g['net_name'] or resolve(sx.one(zone,'net'))!=g['net_name']:raise geom.Unsupported('exact same-net source target required')
    if pad[2]=='smd' and pad[3] in ('rect','roundrect'):
        if p['is_pth'] is not False or shape.get('shape_is_'+pad[3]) is not True:raise geom.Unsupported('source/Native SMD shape differs')
        if pad[3]=='roundrect':
            ratios=sx.children(pad,'roundrect_rratio')
            if len(ratios)!=1 or len(ratios[0])!=2:raise geom.Unsupported('ordinary explicit roundrect ratio required')
            try:ratio=Decimal(ratios[0][1])
            except InvalidOperation:raise geom.Unsupported('malformed roundrect ratio') from None
            if not ratio.is_finite() or not 0<=ratio<=Decimal('.5'):raise geom.Unsupported('ordinary roundrect ratio outside scope')
    elif pad[2]!='thru_hole' or pad[3]!='circle' or p['is_pth'] is not True:raise geom.Unsupported('source target shape outside policy')
    size=sx.one(pad,'size')
    if size is None or len(size)!=3 or [geom.nm(x) for x in size[1:]]!=shape['size_nm']:raise geom.Unsupported('source/Native target size differs')
    return {'policy':POLICY,'zone_uuid':g['zone_uuid'],'pad_uuid':g['target_pad_uuid'],'layer':layer,'original_zone_layers':g['zone_copper_layers'],'saved_contours_nm':polygons}

def propose(g,*,remaining_seconds,binding_verified=False):
    if binding_verified is not True:raise geom.Unsupported('caller must verify exact saved/source observation binding')
    layer,p,shape,center,size,angle,width,error,radius,start_radius,polygons=_geometry(g)
    left=remaining_seconds()
    if type(left) not in (int,float) or not math.isfinite(left) or left<=0:raise geom.Unsupported('contact shared budget exhausted')
    guard=geom.Guard(min(CAPS['seconds'],left),CAPS['operations'],remaining_seconds);rows=[];turn=int(angle//90)%4
    for ray,(dx,dy) in enumerate(RAYS):
        for _ in range(turn):dx,dy=-dy,dx
        start=[center[0]+dx*start_radius,center[1]+dy*start_radius]
        extent=(size[0] if ray%2==0 else size[1])//2
        lower=extent+radius+1;step=max(1,width//4)
        for i in range(CAPS['samples_per_ray']):
            distance=lower+i*step
            if distance>extent+4*width:break
            end=[center[0]+dx*distance,center[1]+dy*distance];found=None
            for index,poly in enumerate(polygons):
                guard.charge(2*len(poly))
                if geom.inside(end,poly) and all(geom.farther_point_segment(end,a,b,radius) for a,b in geom.edges(poly)):found=index;break
            if found is None:continue
            rows.append({'start_nm':start,'end_nm':end,'width_nm':width,'layer':layer,'net_code':g['net_code'],'target_pad_uuid':g['target_pad_uuid'],'zone_uuid':g['zone_uuid'],'saved_outline_index':found,'ray':ray,'endpoint_margin_nm':radius,'native_validation_required':True});break
    return {'schema':1,'policy':POLICY,'status':'diagnostic_speculative_contact_candidates_found' if rows else 'no_bounded_contact_endpoint','candidate_sha256':g['board_sha256'],'proposals':rows,'speculative_contact_only':True,'caps':CAPS,'operations_used':guard.used,'native_validation_performed':False,'routing_accepted':False,'whole_body_certificate_qualified':False,'ampacity_qualified':False,'limitation':'Only speculative contact endpoints in exact saved fill; track interiors/foreign copper/refilled outcomes require fresh original-rule Native validation.'}


def verify_proposals(g,receipt,*,remaining_seconds):
    expected=propose(g,remaining_seconds=remaining_seconds,binding_verified=True)
    if receipt!=expected or not expected['proposals']:raise geom.Unsupported('speculative contact receipt differs from exact deterministic replay')
    return [{'speculative_contact_only':True,'native_validation_required':True,'whole_body_certificate_qualified':False} for _ in expected['proposals']]
