"""Diagnostic same-load floor and area observation. No board writes or adapter policy.

Area footprint cap explicitly increased100->512; all other area bounds retained.
Floor context bounds/schema are unchanged. One LoadBoard and one native DSN export.
"""
import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode=True

FLOORS={'min_track_width':'m_TrackMinWidth','min_clearance':'m_MinClearance',
        'min_via_diameter':'m_ViasMinSize','min_through_hole_diameter':'m_MinThroughDrill',
        'min_via_annular_width':'m_ViasMinAnnularWidth'}
LIMITS={'project_bytes':100*1024*1024,'project_files':2000,'pads':10000,'nets':10000,'routes':100000,'graphics':10000}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    result={};size=0
    if root.is_symlink() or not root.is_dir():raise ValueError('real project directory required')
    for path in sorted(root.rglob('*')):
        if path.is_symlink():raise ValueError('project symlink unsupported')
        if path.is_file():
            size+=path.stat().st_size
            if size>LIMITS['project_bytes'] or len(result)>=LIMITS['project_files']:raise ValueError('project population ceiling')
            result[str(path.relative_to(root))]=sha(path)
    return result


def canonical_path(value):
    path=Path(value)
    if not path.is_absolute() or '..' in path.parts or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('canonical paths without symlinks required')
    return path


AREA_LIMITS={'files':2000,'bytes':100*1024*1024,'zones':16,'outlines':16,'vertices':10000,'footprints':512}

def native_bool(value):
    if type(value) is not bool:raise ValueError('native Boolean API type differs')
    return value

def observe_areas(native,pcbnew):
    names={'tracks':'GetDoNotAllowTracks','vias':'GetDoNotAllowVias','pads':'GetDoNotAllowPads',
           'copperpour':'GetDoNotAllowZoneFills','footprints':'GetDoNotAllowFootprints'}
    types={int(pcbnew.PLACEMENT_SOURCE_T_SHEETNAME):'SHEETNAME',int(pcbnew.PLACEMENT_SOURCE_T_COMPONENT_CLASS):'COMPONENT_CLASS',
           int(pcbnew.PLACEMENT_SOURCE_T_GROUP_PLACEMENT):'GROUP_PLACEMENT',int(pcbnew.PLACEMENT_SOURCE_T_DESIGN_BLOCK):'DESIGN_BLOCK'}
    zones=[];seen=set();points=0
    for zone in native.Zones():
        if len(zones)>=AREA_LIMITS['zones']:raise ValueError('zone census cap')
        uid=str(zone.m_Uuid.AsString())
        if uid in seen:raise ValueError('duplicate native zone UUID')
        seen.add(uid);poly=zone.Outline();count=int(poly.OutlineCount())
        if not 0<=count<=AREA_LIMITS['outlines']:raise ValueError('outline census cap')
        outlines=[];closed=[];holes=[]
        for i in range(count):
            line=poly.COutline(i);n=int(line.PointCount());points+=n
            if n<0 or points>AREA_LIMITS['vertices']:raise ValueError('vertex census cap')
            outlines.append([[int(line.CPoint(j).x),int(line.CPoint(j).y)] for j in range(n)])
            closed.append(native_bool(line.IsClosed()));holes.append(int(poly.HoleCount(i)))
        typ=int(zone.GetPlacementAreaSourceType())
        if typ not in types:raise ValueError('unrecognized native placement source type')
        zones.append({'uuid':uid,'name':str(zone.GetZoneName()),'parent':'board',
            'is_rule_area':native_bool(zone.GetIsRuleArea()),'placement_enabled':native_bool(zone.GetPlacementAreaEnabled()),
            'placement_source_type':types[typ],'placement_source':str(zone.GetPlacementAreaSource()),
            'disallow':{key:native_bool(getattr(zone,method)()) for key,method in names.items()},
            'layers':[name for layer,name in ((pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')) if zone.IsOnLayer(layer)],
            'outlines_nm':outlines,'outline_closed':closed,'holes':holes,'arc_count':int(poly.ArcCount())})
    footprints=list(native.GetFootprints())
    if len(footprints)>AREA_LIMITS['footprints']:raise ValueError('footprint census cap')
    fp_zones=0;fp_rules=0
    for fp in footprints:
        for zone in fp.Zones():
            fp_zones+=1;fp_rules+=int(native_bool(zone.GetIsRuleArea()))
            if fp_zones>AREA_LIMITS['zones']:raise ValueError('footprint zone census cap')
    return {'zones':zones,'footprint_zone_count':fp_zones,'footprint_rulearea_count':fp_rules}


def collect(source,output,area_output,dsn):
    mode='export'
    if mode not in {'export','final'} or (mode=='export')!=(dsn is not None):raise ValueError('unknown context action')
    board,output,area_output=map(canonical_path,(source,output,area_output));project=board.with_suffix('.kicad_pro')
    if area_output.parent!=output.parent or area_output.exists():raise ValueError('fresh local area context required')
    dsn=canonical_path(dsn) if dsn is not None else None
    if board.parent.parent!=output.parent or output.exists() or (dsn is not None and (dsn.parent!=output.parent or dsn.exists())):
        raise ValueError('fresh run-local context paths required')
    if not board.is_file() or not project.is_file():raise ValueError('complete project required')
    before=inventory(board.parent)
    import pcbnew
    if pcbnew.GetBuildVersion()!='10.0.0':raise ValueError('native version changed')
    native=pcbnew.LoadBoard(str(board))
    if not native or native.GetCopperLayerCount()!=2:raise ValueError('two native copper layers required')
    native.SynchronizeNetsAndNetClasses(False)
    areas=observe_areas(native,pcbnew)
    pads=[];nets=[];routes=[];obstacles=[];counts={}
    for pad in native.GetPads():
        if len(pads)>=LIMITS['pads']:raise ValueError('native pad population ceiling')
        pos=pad.GetPosition();row={'uuid':str(pad.m_Uuid.AsString()),'reference':str(pad.GetParentFootprint().GetReference()),
             'number':str(pad.GetNumber()),'netcode':pad.GetNetCode(),'net':str(pad.GetNetname()),
             'copper_layers':[name for layer,name in [(pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')] if pad.IsOnLayer(layer)],
             'position_nm':[pos.x,pos.y]}
        pads.append(row)
        if row['netcode']>0 and row['copper_layers']:counts[row['net']]=counts.get(row['net'],0)+1
    for name,net in native.GetNetsByName().items():
        if not str(name) or net.GetNetCode()<=0:continue
        if len(nets)>=LIMITS['nets']:raise ValueError('native net population ceiling')
        cls=net.GetNetClassSlow();nets.append({'name':str(name),'netcode':net.GetNetCode(),'class':str(cls.GetName()),
             'width_nm':cls.GetTrackWidth(),'clearance_nm':cls.GetClearance(),'via_diameter_nm':cls.GetViaDiameter(),
             'via_drill_nm':cls.GetViaDrill(),'copper_pad_count':counts.get(str(name),0)})
    for track in native.GetTracks():
        if len(routes)>=LIMITS['routes']:raise ValueError('native route population ceiling')
        row={'uuid':str(track.m_Uuid.AsString()),'net':str(track.GetNetname()),'width_nm':int(track.GetWidth())}
        if isinstance(track,pcbnew.PCB_VIA):
            pos=track.GetPosition();row.update(kind='via',position_nm=[pos.x,pos.y],drill_nm=int(track.GetDrillValue()),
                via_type=int(track.GetViaType()),layers=[name for layer,name in [(pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')] if track.IsOnLayer(layer)])
        elif isinstance(track,pcbnew.PCB_ARC):raise ValueError('generated arcs not qualified for floor policy')
        else:
            a,b=track.GetStart(),track.GetEnd();row.update(kind='segment',start_nm=[a.x,a.y],end_nm=[b.x,b.y],layer=str(pcbnew.LayerName(track.GetLayer())))
        routes.append(row)
    if mode=='export':
        graphics=list(native.GetDrawings())
        for fp in native.GetFootprints():graphics.extend(fp.GraphicalItems());graphics.extend([fp.Reference(),fp.Value()])
        if len(graphics)>LIMITS['graphics']:raise ValueError('native graphic population ceiling')
        for graphic in graphics:
            if not pcbnew.IsCopperLayer(graphic.GetLayer()):continue
            box=graphic.GetBoundingBox();obstacles.append({'layer':native.GetLayerName(graphic.GetLayer()),'kind':graphic.GetClass(),
                'bbox_mm':[pcbnew.ToMM(box.GetX()),pcbnew.ToMM(box.GetY()),pcbnew.ToMM(box.GetRight()),pcbnew.ToMM(box.GetBottom())]})
        if not pcbnew.ExportSpecctraDSN(native,str(dsn)):raise ValueError('DSN export failed')
        if dsn.is_symlink() or not dsn.is_file() or not 0<dsn.stat().st_size<=20*1024*1024:raise ValueError('invalid bounded native DSN')
    after=inventory(board.parent)
    if after!=before:raise ValueError('native context changed input project')
    settings=native.GetDesignSettings()
    result={'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','mode':mode,'source':str(board),
        'board_sha256':sha(board),'project_sha256':sha(project),'dsn_sha256':sha(dsn) if dsn else None,
        'floors_nm':{key:int(getattr(settings,value)) for key,value in FLOORS.items()},
        'pads':pads,'nets':sorted(nets,key=lambda row:row['name']),'routes':routes,'obstacles':obstacles,
        'input_hashes_before':before,'input_hashes_after':after,'board_saved':False,'limits':LIMITS,
        'routing_accepted':False}
    with output.open('x') as handle:json.dump(result,handle,indent=2,allow_nan=False);handle.write('\n')
    area_result={'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','source':str(board),
        'board_sha256':sha(board),'project_sha256':sha(project),'dsn_sha256':sha(dsn),'board_saved':False,
        'input_hashes_before':before,'input_hashes_after':after,**areas,'limits':AREA_LIMITS,
        'routing_accepted':False,'adapter_transformation_performed':False}
    with area_output.open('x') as handle:json.dump(area_result,handle,indent=2,allow_nan=False);handle.write('\n')


if __name__=='__main__':collect(*sys.argv[1:])

# tampered disposable executed snapshot
