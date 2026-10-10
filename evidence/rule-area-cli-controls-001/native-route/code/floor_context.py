"""Bounded KiCad10 same-load floor/terminal/export context; never saves a board.

Called only by pinned bundled Python on the caller's disposable complete project.
The native data is observational: acceptance belongs to the parent validator.
"""
import hashlib
import json
import sys
from pathlib import Path

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


def collect(mode,source,output,dsn=None):
    if mode not in {'export','final'} or (mode=='export')!=(dsn is not None):raise ValueError('unknown context action')
    board,output=map(canonical_path,(source,output));project=board.with_suffix('.kicad_pro')
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


if __name__=='__main__':collect(*sys.argv[1:])
