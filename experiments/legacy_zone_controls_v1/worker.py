"""Nonsaving export callback; new connectivity APIs remain unexecuted until ROOT."""
from pathlib import Path
import sys
ROOT=next(path for path in Path(__file__).resolve().parents if (path/'autorouter/floor_context.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter.floor_context import collect


def integer(value):
    if type(value) is not int:raise ValueError('native integer return type differs: '+type(value).__name__)
    return value

def boolean(value):
    if type(value) is not bool:raise ValueError('native Boolean return type differs: '+type(value).__name__)
    return value

def observe(board,pcbnew):
    # Direct owned connectivity object avoids the unqualified shared_ptr accessor.
    connectivity=pcbnew.CONNECTIVITY_DATA();built=boolean(connectivity.Build(board))
    if not built:raise ValueError('native connectivity Build returned false')
    pads=[];zones=[];fp_zones=0
    for fp in board.GetFootprints():
        fp_zones+=len(list(fp.Zones()))
        if fp_zones:raise ValueError('footprint zones unsupported')
    for pad in board.GetPads():
        if len(pads)>=6:raise ValueError('pad census cap')
        pos=pad.GetPosition()
        pads.append({'uuid':str(pad.m_Uuid.AsString()),'reference':str(pad.GetParentFootprint().GetReference()),
            'number':str(pad.GetNumber()),'netcode':integer(pad.GetNetCode()),'net':str(pad.GetNetname()),
            'copper_layers':[name for layer,name in ((pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')) if boolean(pad.IsOnLayer(layer))],
            'position_nm':[integer(pos.x),integer(pos.y)]})
    for zone in board.Zones():
        if zones:raise ValueError('zone census cap')
        poly=zone.Outline()
        if integer(poly.OutlineCount())!=1:raise ValueError('one fixed zone outline required')
        line=poly.COutline(0)
        if integer(line.PointCount())!=4:raise ValueError('four fixed outline vertices required')
        code=integer(zone.GetNetCode());layers=list(zone.GetLayerSet().Seq())
        if len(layers)>2:raise ValueError('zone layer census cap')
        zones.append({'uuid':str(zone.m_Uuid.AsString()),'is_copper':boolean(zone.IsOnCopperLayer()),
            'is_rule_area':boolean(zone.GetIsRuleArea()),'layers':[{'id':integer(x),'name':str(pcbnew.LayerName(x))} for x in layers],
            'netcode':code,'net':str(zone.GetNetname()),'pad_count':integer(connectivity.GetPadCount(code)) if code>0 else None,
            'outline_nm':[[integer(line.CPoint(i).x),integer(line.CPoint(i).y)] for i in range(4)],
            'closed':boolean(line.IsClosed()),'holes':integer(poly.HoleCount(0)),'arc_count':integer(poly.ArcCount())})
    return {'schema':1,'connectivity_build_succeeded':built,'footprint_zone_count':fp_zones,
            'pads':sorted(pads,key=lambda row:row['uuid']),'zones':zones}

if __name__=='__main__':
    if len(sys.argv)!=5:raise SystemExit('worker BOARD CONTEXT DSN ZONE_OBSERVATION')
    collect('export',sys.argv[1],sys.argv[2],sys.argv[3],observation_output=sys.argv[4],observer=observe)
