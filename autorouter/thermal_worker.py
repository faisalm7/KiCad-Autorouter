"""Native read-only thermal observations on fresh job-owned copies only."""
import hashlib,json,math,os,re,stat,sys
from pathlib import Path
sys.dont_write_bytecode=True

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inventory(root):
    result = {}
    total = 0
    for p in sorted(Path(root).rglob('*')):
        if p.is_symlink(): raise ValueError('symlink in input inventory')
        if p.is_file():
            total += p.stat().st_size
            if total > 100*1024*1024 or len(result) >= 2000: raise ValueError('input inventory cap')
            result[str(p.relative_to(root))] = digest(p)
    return result

def write_new(path, data):
    with Path(path).open('x') as f:
        json.dump(data, f, indent=2); f.write('\n')

def select_finding(report):
    findings = [f for f in report['violations'] if f.get('type') == 'starved_thermal']
    if len(findings) != 1 or findings[0].get('severity') != 'error' or findings[0].get('excluded', False):
        raise ValueError('requires one unexcluded blocking thermal finding')
    ids = [i['uuid'] for i in findings[0]['items']]
    if len(ids) != 2 or len(set(ids)) != 2: raise ValueError('thermal finding item identities ambiguous')
    return findings[0], ids

def xy(v):
    return [int(v.x), int(v.y)]

def uid(obj):
    return str(obj.m_Uuid.AsString())

def nearest(point, poly):
    best = float('inf')
    for a,b in zip(poly,poly[1:]+poly[:1]):
        x,y=b[0]-a[0],b[1]-a[1]
        q=x*x+y*y
        t=max(0.,min(1.,((point[0]-a[0])*x+(point[1]-a[1])*y)/q)) if q else 0.
        best=min(best,math.hypot(point[0]-a[0]-t*x,point[1]-a[1]-t*y))
    return best

def point_inside(point, poly):
    x,y=point;result=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]):result=not result
    return result

def owned(path,root,new=False):
    raw=Path(path)
    if not raw.is_absolute() or '..' in raw.parts:raise ValueError('worker requires absolute owned paths')
    try:parts=raw.relative_to(root).parts
    except ValueError:raise ValueError('worker path outside copied workspace') from None
    current=root
    for i,part in enumerate(parts):
        current=current/part
        try:info=os.lstat(current)
        except FileNotFoundError:
            if new and i==len(parts)-1:return raw
            raise
        if stat.S_ISLNK(info.st_mode):raise ValueError('worker refuses symlinks')
        if i<len(parts)-1 and not stat.S_ISDIR(info.st_mode):raise ValueError('worker path ancestor not directory')
    return raw

def require_native_identity(version, python, pcbnew_path, actual_version,
                            actual_python, actual_pcbnew, report_version):
    """Bind observation to the caller's selected tools, never to input JSON."""
    if (type(version) is not str or version not in ('10.0.0','10.0.7')
            or actual_version != version or report_version != version):
        raise ValueError('thermal native/report version differs from caller pin')
    paths=(python,pcbnew_path,actual_python,actual_pcbnew)
    if any(type(value) is not str or not Path(value).is_absolute() for value in paths):
        raise ValueError('absolute thermal native identity paths required')
    if (Path(actual_python).resolve()!=Path(python).resolve()
            or Path(actual_pcbnew).resolve()!=Path(pcbnew_path).resolve()):
        raise ValueError('loaded thermal Python/pcbnew path differs from caller pin')
    return dict(native_version=version,native_python=str(Path(actual_python).resolve()),
                native_pcbnew=str(Path(actual_pcbnew).resolve()))


def native_worker(board_path,request_path,output_path,expected_version,expected_python,expected_pcbnew):
    root=Path(__file__).absolute().parent
    if root.is_symlink():raise ValueError('worker root symlink')
    board_path=owned(board_path,root);request_path=owned(request_path,root);output_path=owned(output_path,root,new=True)
    owned(board_path.with_suffix('.kicad_pro'),root);owned(root/'input-drc.json',root)
    if board_path.parent!=root/'input' or request_path!=root/'request.json' or output_path!=root/'geometry.json' or output_path.exists():raise ValueError('fixed fresh worker paths required')
    import pcbnew
    import _pcbnew
    request=json.loads(request_path.read_text());before=inventory(board_path.parent)
    if before != request['candidate_files'] or digest(root/'input-drc.json') != request['final_drc_sha256']:
        raise ValueError('worker inputs differ from verified binding')
    raw_report=json.loads((root/'input-drc.json').read_text());finding,target_ids=select_finding(raw_report)
    identity=require_native_identity(expected_version,expected_python,expected_pcbnew,
        pcbnew.GetBuildVersion(),sys.executable,_pcbnew.__file__,raw_report.get('kicad_version'))
    board=pcbnew.LoadBoard(str(board_path))
    if not board: raise ValueError('native load failed')
    board.SynchronizeNetsAndNetClasses(False)
    pads=list(board.GetPads());zones=list(board.Zones())
    if len(pads)>512 or len(zones)>128: raise ValueError('native population cap')
    objects={}
    for obj in pads+zones: objects.setdefault(uid(obj),[]).append(obj)
    matched=[objects.get(i,[]) for i in target_ids]
    if any(len(v)!=1 for v in matched): raise ValueError('native thermal UUID not unique')
    target_pads=[v[0] for v in matched if isinstance(v[0],pcbnew.PAD)]
    target_zones=[v[0] for v in matched if isinstance(v[0],pcbnew.ZONE)]
    if len(target_pads)!=1 or len(target_zones)!=1: raise ValueError('finding does not bind exactly one native pad and zone')
    target,zone=target_pads[0],target_zones[0]
    errors=[]
    def observe(row,key,fn):
        try: row[key]=fn();return row[key]
        except Exception as exc:
            issue=key+': '+type(exc).__name__+': '+str(exc)[:240]
            row.setdefault('api_errors',[]).append(issue);errors.append(issue)
            return None
    layer_ids=[int(x) for x in zone.GetLayerSet().Seq() if pcbnew.IsCopperLayer(x)]
    zone_layers=[str(pcbnew.LayerName(x)) for x in layer_ids]
    mode=request.get('mode')
    if mode not in (None,'native-thermal-contact-v1'):raise ValueError('unknown thermal observation mode')
    reported_layer=None
    if mode=='native-thermal-contact-v1':
        match=re.fullmatch(r'Thermal relief connection to zone incomplete \(layer (F\.Cu|B\.Cu); zone min spoke count 2; actual 1\)',finding.get('description',''))
        if match is None:raise ValueError('explicit pinned thermal report layer required')
        reported_layer=match.group(1)
        chosen=[x for x in layer_ids if str(pcbnew.LayerName(x))==reported_layer]
        if len(chosen)!=1:raise ValueError('reported target layer not unique in original zone')
        layer_ids=chosen
    layers=[{'id':l,'canonical':str(pcbnew.LayerName(l)),'board_name':str(board.GetLayerName(l))} for l in layer_ids]
    output={'schema':1,'kind':'native thermal geometry observations only',**identity,
        'units':'integer nanometres unless explicitly named otherwise','board_sha256':digest(board_path),
        'project_sha256':digest(board_path.with_suffix('.kicad_pro')),'finding':finding,
        'zone_uuid':uid(zone),'target_pad_uuid':uid(target),'net_code':int(zone.GetNetCode()),'net_name':str(zone.GetNetname()),
        'layers':layers,'source_unchanged':False,'board_saved':False,'refill_executed':False,'drc_executed':False,'solver_executed':False,
        'proposal_scene_qualified':False,'unsupported_reasons':[],'pads':[],'vias':[],'bodies':[]}
    if mode is not None:output.update(mode=mode,reported_layer=reported_layer,zone_copper_layers=zone_layers)
    if board.GetCopperLayerCount()!=2:raise ValueError('only two-layer thermal scope')
    if len(layer_ids)!=1:raise ValueError('target zone must have one copper layer')
    if target.GetNetCode()<=0 or target.GetNetCode()!=zone.GetNetCode():raise ValueError('target/zone native net mismatch')
    native_class=target.GetNet().GetNetClassSlow()
    output['class']={'name':str(native_class.GetName()),'width_nm':int(native_class.GetTrackWidth()),'clearance_nm':int(native_class.GetClearance()),'via_diameter_nm':int(native_class.GetViaDiameter()),'via_drill_nm':int(native_class.GetViaDrill())}
    observe(output,'native_max_error_nm',lambda:int(board.GetDesignSettings().m_MaxError))
    target_pos=xy(target.GetPosition());output['target_position_nm']=target_pos
    for pad in pads:
        row={'uuid':uid(pad),'net_code':int(pad.GetNetCode()),'net_name':str(pad.GetNetname()),'position_nm':xy(pad.GetPosition()),
             'footprint_uuid':uid(pad.GetParentFootprint()),'pad_number':str(pad.GetNumber()),'unsupported_reasons':[],
             'native_layer_geometry_qualified':False}
        row['logical_terminal']=[row['footprint_uuid'],row['pad_number']]
        observe(row,'orientation_degrees',lambda:float(pad.GetOrientationDegrees()))
        observe(row,'attribute',lambda:int(pad.GetAttribute()))
        observe(row,'is_pth',lambda:pad.GetAttribute()==pcbnew.PAD_ATTRIB_PTH)
        observe(row,'drill_size_nm',lambda:xy(pad.GetDrillSize()))
        observe(row,'drill_is_round',lambda:pad.GetDrillShape()==pcbnew.PAD_DRILL_SHAPE_CIRCLE)
        try:
            hole=pad.GetEffectiveHoleShape()
            row['effective_hole']={'start_nm':xy(hole.GetStart()),'end_nm':xy(hole.GetEnd()),'width_nm':int(hole.GetWidth())}
        except Exception as exc:
            issue='effective_hole: '+type(exc).__name__+': '+str(exc)[:240]
            row.setdefault('api_errors',[]).append(issue);errors.append(issue)
        row['layers']=[]
        for layer in layer_ids:
            layer_row={'id':layer,'canonical':str(pcbnew.LayerName(layer)),'on_layer':bool(pad.IsOnLayer(layer))}
            observe(layer_row,'flash_layer',lambda:bool(pad.FlashLayer(layer)))
            observe(layer_row,'shape_is_circle',lambda:pad.GetShape(layer)==pcbnew.PAD_SHAPE_CIRCLE)
            if mode=='native-thermal-contact-v1':
                observe(layer_row,'shape_is_rect',lambda:pad.GetShape(layer)==pcbnew.PAD_SHAPE_RECT)
                observe(layer_row,'shape_is_roundrect',lambda:pad.GetShape(layer)==pcbnew.PAD_SHAPE_ROUNDRECT)
            observe(layer_row,'size_nm',lambda:xy(pad.GetSize(layer)))
            observe(layer_row,'offset_nm',lambda:xy(pad.GetOffset(layer)))
            observe(layer_row,'shape_position_nm',lambda:xy(pad.ShapePos(layer)))
            row['layers'].append(layer_row)
        if not row.get('is_pth'):row['unsupported_reasons'].append('not standard plated-through pad')
        if not row.get('drill_is_round'):row['unsupported_reasons'].append('nonround or unavailable drill shape')
        h=row.get('effective_hole',{})
        if h.get('start_nm')!=row['position_nm'] or h.get('end_nm')!=row['position_nm']:row['unsupported_reasons'].append('effective drill is nonconcentric/slot/unavailable')
        for layer_row in row['layers']:
            if not layer_row.get('on_layer'):continue
            size=layer_row.get('size_nm',[])
            if not layer_row.get('shape_is_circle') or len(size)!=2 or size[0]!=size[1]:row['unsupported_reasons'].append('noncircular per-layer copper')
            if layer_row.get('shape_position_nm')!=row['position_nm'] or layer_row.get('offset_nm')!=[0,0]:row['unsupported_reasons'].append('copper/drill center offset or unavailable')
        row['unsupported_reasons'].append('native parameters observed; geometric certificate and drilled-body topology not yet proved')
        output['pads'].append(row)
    for track in board.GetTracks():
        if not isinstance(track,pcbnew.PCB_VIA):continue
        if len(output['vias'])>=512:raise ValueError('via count cap')
        row={'uuid':uid(track),'net_code':int(track.GetNetCode()),'position_nm':xy(track.GetPosition()),'unsupported_reasons':[]}
        observe(row,'via_type',lambda:int(track.GetViaType()))
        observe(row,'drill_nm',lambda:int(track.GetDrillValue()))
        row['layer_membership']=[l for l in layer_ids if track.IsOnLayer(l)]
        output['vias'].append(row)
    total_points=0
    for layer in layer_ids:
        filled=zone.GetFilledPolysList(layer)
        count=int(filled.OutlineCount())
        if count>128:raise ValueError('zone outline count cap')
        for index in range(count):
            row={'native_outline_index':index,'layer_id':layer,'zone_uuid':uid(zone),'net_code':int(zone.GetNetCode()),
                 'holes_nm':[],'selected':False,'drills_accounted_for':False,'unsupported_reasons':[]}
            def contour(chain):
                nonlocal total_points
                n=int(chain.PointCount());total_points+=n
                if n>8192 or total_points>40000:raise ValueError('zone polygon point cap')
                return [xy(chain.CPoint(i)) for i in range(n)]
            row['outer_nm']=contour(filled.Outline(index))
            row['hole_count']=int(filled.HoleCount(index))
            if row['hole_count']>128:raise ValueError('polygon hole cap')
            for hole_index in range(row['hole_count']):row['holes_nm'].append(contour(filled.Hole(index,hole_index)))
            observe(row,'native_self_intersecting',lambda:bool(filled.IsPolygonSelfIntersecting(index)))
            observe(row,'native_outer_closed',lambda:bool(filled.Outline(index).IsClosed()))
            observe(row,'native_total_arc_count',lambda:int(filled.ArcCount()))
            observe(row,'native_island_flag',lambda:bool(zone.IsIsland(layer,index)))
            row['native_island_flag_interpretation']='observed only; not single-connection-island classification'
            row['repeated_vertices']=len(row['outer_nm'])-len({tuple(v) for v in row['outer_nm']})
            if row['hole_count']:row['unsupported_reasons'].append('explicit polygon holes outside draft proposal scope')
            if row.get('native_outer_closed') is not True:row['unsupported_reasons'].append('closed contour not demonstrated')
            if row.get('native_total_arc_count') != 0:row['unsupported_reasons'].append('arc-free native fill not demonstrated')
            if row['repeated_vertices']:row['unsupported_reasons'].append('repeated/fracture vertices')
            if row.get('native_self_intersecting') is not False:row['unsupported_reasons'].append('simple native contour not demonstrated')
            row['unsupported_reasons'].append('relation between body and all applicable drill cutouts not yet proved')
            poly=row['outer_nm']
            all_boundaries=[poly]+row['holes_nm']
            in_copper=point_inside(target_pos,poly) and not any(point_inside(target_pos,h) for h in row['holes_nm'])
            row['distance_to_target_nm']=0. if in_copper else min(nearest(target_pos,r) for r in all_boundaries)
            row['area_nm2']=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])))/2
            row['geometric_selection_key']=[round(row['distance_to_target_nm'],3),row['area_nm2'],len(poly)]
            output['bodies'].append(row)
    # All considered bodies and reasons stay in output. No outline index chooses
    # candidates. Geometry-tied groups crossing the cap are excluded together.
    limit_radius=4*output['class']['width_nm']
    nearby=[r for r in output['bodies'] if r['distance_to_target_nm']<=limit_radius]
    nearby.sort(key=lambda r:r['geometric_selection_key'])
    selected=[];i=0
    while i<len(nearby):
        j=i+1
        while j<len(nearby) and nearby[j]['geometric_selection_key']==nearby[i]['geometric_selection_key']:j+=1
        group=nearby[i:j]
        if len(selected)+len(group)>8:
            for r in nearby[i:]:r['unsupported_reasons'].append('eight-body cap; geometry ties never split by identity')
            break
        for r in group:r['selected']=True
        selected.extend(group);i=j
    for row in output['bodies']:
        if row['distance_to_target_nm']>limit_radius:row['unsupported_reasons'].append('outside fixed four-class-width target neighborhood')
    output['body_selection']={'radius_nm':limit_radius,'cap':8,'considered':len(output['bodies']),'selected':len(selected),'policy':'distance to saved filled region, area, vertex count; retain all reasons; do not split ties by IDs'}
    output['unsupported_reasons'].append('read-only observations require separate scene/certificate qualification; no proposal emitted')
    output['api_error_count']=len(errors)
    output['source_unchanged']=inventory(board_path.parent)==before
    if not output['source_unchanged']:raise ValueError('native read-only input inventory changed')
    output['status']='observations_partial' if errors else 'observations_complete'
    write_new(output_path,output)

if __name__=='__main__':
    if len(sys.argv)!=7:raise ValueError('expected board request output and caller-selected native version/Python/pcbnew')
    native_worker(*sys.argv[1:])
