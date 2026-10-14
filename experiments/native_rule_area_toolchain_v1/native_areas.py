"""Read-only, bounded KiCad10 area census and DSN from one loaded board.

Invoked by the lead through the existing sandboxed supervisor. Never saves the
board; no routing/DRC/adapter policy or automatic removal occurs in this worker.
"""
import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode=True
LIMITS={'files':2000,'bytes':100*1024*1024,'zones':16,'outlines':16,'vertices':10000,'footprints':100}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    if root.is_symlink() or not root.is_dir():raise ValueError('real input project directory required')
    result={};size=0
    for file in sorted(root.rglob('*')):
        if file.is_symlink():raise ValueError('project symlink')
        if file.is_file():
            size+=file.stat().st_size
            if size>LIMITS['bytes'] or len(result)>=LIMITS['files']:raise ValueError('input population cap')
            result[str(file.relative_to(root))]=sha(file)
    return result


def local(value):
    path=Path(value)
    if not path.is_absolute() or '..' in path.parts or any(x.is_symlink() for x in (path,*path.parents)):
        raise ValueError('canonical path required')
    return path


def native_bool(value):
    if type(value) is not bool:raise ValueError('native Boolean API type differs')
    return value


def collect(source,output,dsn,expected_version):
    if expected_version not in ('10.0.0','10.0.7'):raise ValueError('explicit pinned native version required')
    board,output,dsn=map(local,(source,output,dsn))
    if board.parent.parent!=output.parent or dsn.parent!=output.parent or output.exists() or dsn.exists():
        raise ValueError('fresh run-local context paths required')
    project=board.with_suffix('.kicad_pro')
    if not board.is_file() or not project.is_file():raise ValueError('complete project required')
    before=inventory(board.parent)
    import pcbnew
    if pcbnew.GetBuildVersion()!=expected_version:raise ValueError('pinned native version differs')
    native=pcbnew.LoadBoard(str(board))
    if not native or native.GetCopperLayerCount()!=2:raise ValueError('two-layer native input required')
    native.SynchronizeNetsAndNetClasses(False)
    names={'tracks':'GetDoNotAllowTracks','vias':'GetDoNotAllowVias','pads':'GetDoNotAllowPads',
           'copperpour':'GetDoNotAllowZoneFills','footprints':'GetDoNotAllowFootprints'}
    types={int(pcbnew.PLACEMENT_SOURCE_T_SHEETNAME):'SHEETNAME',int(pcbnew.PLACEMENT_SOURCE_T_COMPONENT_CLASS):'COMPONENT_CLASS',
           int(pcbnew.PLACEMENT_SOURCE_T_GROUP_PLACEMENT):'GROUP_PLACEMENT',int(pcbnew.PLACEMENT_SOURCE_T_DESIGN_BLOCK):'DESIGN_BLOCK'}
    zones=[];seen=set();points=0
    for zone in native.Zones():
        if len(zones)>=LIMITS['zones']:raise ValueError('zone census cap')
        uid=str(zone.m_Uuid.AsString())
        if uid in seen:raise ValueError('duplicate native zone UUID')
        seen.add(uid);poly=zone.Outline();count=int(poly.OutlineCount())
        if not 0<=count<=LIMITS['outlines']:raise ValueError('outline census cap')
        outlines=[];closed=[];holes=[]
        for i in range(count):
            line=poly.COutline(i);n=int(line.PointCount());points+=n
            if n<0 or points>LIMITS['vertices']:raise ValueError('vertex census cap')
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
    if len(footprints)>LIMITS['footprints']:raise ValueError('footprint census cap')
    fp_zones=0;fp_rules=0
    for fp in footprints:
        for zone in fp.Zones():
            fp_zones+=1;fp_rules+=int(native_bool(zone.GetIsRuleArea()))
            if fp_zones>LIMITS['zones']:raise ValueError('footprint zone census cap')
    if not pcbnew.ExportSpecctraDSN(native,str(dsn)):raise ValueError('native DSN export failed')
    if dsn.is_symlink() or not dsn.is_file() or not 0<dsn.stat().st_size<=20*1024*1024:raise ValueError('invalid bounded native DSN')
    after=inventory(board.parent)
    if after!=before:raise ValueError('native observation modified input')
    result={'context_schema':1,'native_version':pcbnew.GetBuildVersion(),'native_python':str(Path(sys.executable).resolve()),'loaded_pcbnew':str(Path(pcbnew._pcbnew.__file__).resolve()),'units':'integer nanometres','source':str(board),
        'board_sha256':sha(board),'project_sha256':sha(project),'dsn_sha256':sha(dsn),'board_saved':False,
        'input_hashes_before':before,'input_hashes_after':after,'zones':zones,'footprint_zone_count':fp_zones,
        'footprint_rulearea_count':fp_rules,'limits':LIMITS,'routing_accepted':False,'adapter_transformation_performed':False}
    with output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')


if __name__=='__main__':collect(*sys.argv[1:])
