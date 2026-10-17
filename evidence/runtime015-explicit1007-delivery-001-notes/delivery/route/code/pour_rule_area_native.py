"""Pinned native saved-fill exclusion; never fills or saves an input board."""
import hashlib
import json
from pathlib import Path

def audit(board,source,before):
    import pcbnew
    from autorouter import pour_rule_area as policy,sexpr as sx
    from autorouter.floor_context import observe_areas,AREA_LIMITS
    source=Path(source);raw=source.read_bytes();project=source.with_suffix('.kicad_pro')
    captured=(hashlib.sha256(raw).hexdigest(),hashlib.sha256(project.read_bytes()).hexdigest())
    if before is None or before!=captured:raise ValueError('source changed across native board load')
    tree=sx.parse(raw.decode());areas=policy.qualify(tree)
    if not areas:raise ValueError('qualified pour-only areas required')
    layers=policy.source_layers(tree);four=len(layers)==4;layer_record=[]
    if four:
        if pcbnew.GetBuildVersion()!='10.0.0':raise ValueError('four-copper pour audit requires qualified Native 10.0.0')
        if type(board.GetCopperLayerCount())is not int or board.GetCopperLayerCount()!=4:raise ValueError('four native copper layers required')
        for index,(code,name) in enumerate(zip((0,4,6,2),layers)):
            if (int(board.GetLayerID(name))!=code or str(board.GetLayerName(code))!=name
                    or str(pcbnew.LayerName(code))!=name or board.IsLayerEnabled(code) is not True
                    or int(board.GetLayerType(code))!=int(pcbnew.LT_SIGNAL)):
                raise ValueError('native canonical copper identity differs')
            layer_record.append(dict(id=code,name=name,type='signal',index=index))
    observed=observe_areas(board,pcbnew,**({'copper_layers':layers} if four else {}))
    if observed['footprint_zone_count']:raise ValueError('footprint zones outside pour audit scope')
    native_zones={str(z.m_Uuid.AsString()):z for z in board.Zones()}
    ids=sorted(policy._atom(z,'uuid') for z in sx.children(tree,'zone'))
    if sorted(native_zones)!=ids:raise ValueError('native root zone census differs')
    rows={row['uuid']:row for row in observed['zones']};native_areas=[rows[a['uuid']] for a in areas]
    for row in native_areas:row['layers']=sorted(row['layers'])
    expected=[{k:v for k,v in row.items() if k!='source_zone_ast_sha256'} for row in areas]
    if json.dumps(native_areas,sort_keys=True)!=json.dumps(expected,sort_keys=True):raise ValueError('native pour flags/outline/layers differ')
    def contours(poly):
        result=[];points=0
        for i in range(poly.OutlineCount()):
            line=poly.COutline(i);n=int(line.PointCount());points+=n
            if points>AREA_LIMITS['vertices']:raise ValueError('native intersection vertex ceiling')
            result.append({'points_nm':[[int(line.CPoint(j).x),int(line.CPoint(j).y)] for j in range(n)],
                'closed':bool(line.IsClosed()),'holes':int(poly.HoleCount(i))})
        return result
    area_nets=[]
    if four:
        for row in areas:
            zone=native_zones[row['uuid']];code=zone.GetNetCode();name=str(zone.GetNetname())
            if type(code)is not int or code!=0 or name!='':raise ValueError('native rule area must remain NoNet')
            mode=zone.GetIslandRemovalMode()
            if type(mode)is not int or mode!=0 or int(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)!=0:raise ValueError('native rule-area island mode differs')
            area_nets.append(dict(uuid=row['uuid'],netcode=code,netname=name,island_removal_mode=mode))
    checks=[]
    for item in policy.fill_matrix(tree,areas):
        zone=native_zones[item['zone_uuid']];area=native_zones[item['area_uuid']]
        layer=({'F.Cu':pcbnew.F_Cu,'In1.Cu':pcbnew.In1_Cu,'In2.Cu':pcbnew.In2_Cu,'B.Cu':pcbnew.B_Cu}
               if four else {'F.Cu':pcbnew.F_Cu,'B.Cu':pcbnew.B_Cu})[item['layer']]
        if not zone.IsOnLayer(layer) or bool(area.IsOnLayer(layer))is not item['applicable']:raise ValueError('native/source layer applicability differs')
        fill=pcbnew.SHAPE_POLY_SET(zone.GetFilledPolysList(layer));count=int(fill.OutlineCount())
        fill.BooleanIntersection(area.Outline());intersection=contours(fill)
        checks.append(dict(item,native_fill_outline_count=count,intersection=intersection,
            passed=(not item['applicable'] or not intersection) and count==item['stored_fill_node_count']))
    if before!=(hashlib.sha256(source.read_bytes()).hexdigest(),hashlib.sha256(project.read_bytes()).hexdigest()):raise ValueError('source changed during native pour audit')
    return {'schema':2 if four else 1,'policy':policy.FOUR_AUDIT_POLICY if four else policy.AUDIT_POLICY,'native_version':pcbnew.GetBuildVersion(),'source':str(source),
        **({'copper_layers':layer_record,'native_area_nets':area_nets} if four else {}),
        'board_sha256':before[0],'project_sha256':before[1],'board_saved':False,'source_areas':areas,
        'native_areas':native_areas,'native_zone_uuids':ids,'fill_checks':checks,'passed':all(x['passed'] for x in checks)}
