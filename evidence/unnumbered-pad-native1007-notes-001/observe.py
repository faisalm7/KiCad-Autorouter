"""Unexecuted same-BOARD scalar callback; no load/save/export or acceptance.

SPDX-License-Identifier: GPL-3.0-or-later
Caller uses the existing native.netclasses/export_board functions on this same
BOARD and records this census before/after export. Explicit layers avoid the
installed no-layer padstack width/size ambiguity.
"""
LAYERS=((0,'F.Cu'),(4,'In1.Cu'),(6,'In2.Cu'),(2,'B.Cu'))
def point(value):return [int(value.x),int(value.y)]
def observe(board,pcbnew):
    if pcbnew.GetBuildVersion()!='10.0.7' or board.GetCopperLayerCount()!=4:raise ValueError('pinned experimental10.0.7 canonical4Cu required')
    for code,name in LAYERS:
        if (str(pcbnew.LayerName(code))!=name or str(board.GetLayerName(code))!=name
                or int(board.GetLayerID(name))!=code or board.IsLayerEnabled(code)is not True
                or int(board.GetLayerType(code))!=int(pcbnew.LT_SIGNAL)):
            raise ValueError('native physical layer identity differs')
    rows=[];seen=set()
    for pad in board.GetPads():
        if len(rows)>=7:raise ValueError('owned pad census exceeded')
        ident=str(pad.m_Uuid.AsString());fp=pad.GetParentFootprint()
        if ident in seen:raise ValueError('duplicate native pad identity')
        seen.add(ident);copper=[];shapes=[]
        for code,name in LAYERS:
            if pad.IsOnLayer(code):
                copper.append(name);shapes.append({'layer':name,'shape_enum':int(pad.GetShape(code)),
                    'circle':pad.GetShape(code)==pcbnew.PAD_SHAPE_CIRCLE,
                    'size_nm':point(pad.GetSize(code)),'offset_nm':point(pad.GetOffset(code))})
        rows.append({'uuid':ident,'footprint_uuid':str(fp.m_Uuid.AsString()),'reference':str(fp.GetReference()),
            'number':str(pad.GetNumber()),'net':str(pad.GetNetname()),'netcode':int(pad.GetNetCode()),
            'position_nm':point(pad.GetPosition()),'fp_relative_position_nm':point(pad.GetFPRelativePosition()),
            'attribute_enum':int(pad.GetAttribute()),'is_pth':pad.GetAttribute()==pcbnew.PAD_ATTRIB_PTH,
            'drill_nm':point(pad.GetDrillSize()),'copper_layers':copper,'shapes':shapes})
    if len(rows)!=7:raise ValueError('owned pad census incomplete')
    return {'schema':1,'native_version':pcbnew.GetBuildVersion(),'board_saved':False,
            'pads':sorted(rows,key=lambda r:r['uuid']),'routing_accepted':False}
