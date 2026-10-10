"""Pinned native read/export context on bounded disposable fixture copies only."""
import hashlib,json,sys
from pathlib import Path
FLOORS={'min_track_width':'m_TrackMinWidth','min_clearance':'m_MinClearance','min_via_diameter':'m_ViasMinSize','min_through_hole_diameter':'m_MinThroughDrill','min_via_annular_width':'m_ViasMinAnnularWidth'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tree(root):
    result={}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():raise ValueError('symlink in fixture')
        if p.is_file():result[str(p.relative_to(root))]=sha(p)
    if len(result)>100 or sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>1024*1024:raise ValueError('fixture inventory ceiling')
    return result

def main(board,dsn,context):
    root=Path(__file__).absolute().parent.parent
    board,dsn,context=map(Path,(board,dsn,context))
    for path in (board,board.with_suffix('.kicad_pro'),dsn,context):
        if not path.is_absolute() or '..' in path.parts or not path.is_relative_to(root) or any(x.is_symlink() for x in (path,*path.parents)):raise ValueError('requires owned canonical fixture paths')
    if dsn.exists() or context.exists() or dsn.parent!=context.parent or board.parent.parent!=dsn.parent:raise ValueError('fresh case-local outputs required')
    import pcbnew
    if pcbnew.GetBuildVersion()!='10.0.0':raise ValueError('native version changed')
    before=tree(board.parent);native=pcbnew.LoadBoard(str(board))
    if not native or native.GetCopperLayerCount()!=2:raise ValueError('requires two native copper layers')
    native.SynchronizeNetsAndNetClasses(False);settings=native.GetDesignSettings();pads=[];nets=[];routes=[]
    if len(list(native.GetPads()))>16 or len(list(native.GetTracks()))>2048:raise ValueError('native fixture population cap')
    for pad in native.GetPads():
        pos=pad.GetPosition();pads.append({'uuid':str(pad.m_Uuid.AsString()),'reference':str(pad.GetParentFootprint().GetReference()),'number':str(pad.GetNumber()),'netcode':pad.GetNetCode(),'net':str(pad.GetNetname()),'copper_layers':[name for layer,name in [(pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')] if pad.IsOnLayer(layer)],'position_nm':[pos.x,pos.y]})
    for name,net in native.GetNetsByName().items():
        if not str(name) or net.GetNetCode()<=0:continue
        cls=net.GetNetClassSlow();nets.append({'name':str(name),'netcode':net.GetNetCode(),'class':str(cls.GetName()),'width_nm':cls.GetTrackWidth(),'clearance_nm':cls.GetClearance(),'via_diameter_nm':cls.GetViaDiameter(),'via_drill_nm':cls.GetViaDrill(),'copper_pad_count':sum(p['net']==str(name) and bool(p['copper_layers']) for p in pads)})
    for track in native.GetTracks():
        row={'uuid':str(track.m_Uuid.AsString()),'net':str(track.GetNetname()),'width_nm':int(track.GetWidth())}
        if isinstance(track,pcbnew.PCB_VIA):
            pos=track.GetPosition();row.update(kind='via',position_nm=[pos.x,pos.y],drill_nm=int(track.GetDrillValue()),via_type=int(track.GetViaType()),layers=[name for layer,name in [(pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')] if track.IsOnLayer(layer)])
        elif isinstance(track,pcbnew.PCB_ARC):raise ValueError('arc outside diagnostic fixture scope')
        else:
            a,b=track.GetStart(),track.GetEnd();row.update(kind='segment',start_nm=[a.x,a.y],end_nm=[b.x,b.y],layer=str(pcbnew.LayerName(track.GetLayer())))
        routes.append(row)
    if not pcbnew.ExportSpecctraDSN(native,str(dsn)):raise ValueError('DSN export failed')
    if tree(board.parent)!=before:raise ValueError('native read/export changed original fixture')
    result={'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','source':str(board),'board_sha256':sha(board),'project_sha256':sha(board.with_suffix('.kicad_pro')),'dsn_sha256':sha(dsn),'floors_nm':{key:int(getattr(settings,value)) for key,value in FLOORS.items()},'pads':pads,'nets':sorted(nets,key=lambda x:x['name']),'routes':routes,'input_hashes_before':before,'input_hashes_after':tree(board.parent),'board_saved':False,'routing_accepted':False,'production_support_qualified':False}
    with context.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
if __name__=='__main__':
    if len(sys.argv)!=4:raise ValueError('expected board DSN context paths')
    main(*sys.argv[1:])
