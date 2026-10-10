"""Lead-only nonsaving custom-pad observation callback, run by pinned KiCad Python.

Declared APIs are not a runtime qualification. Any missing/opaque return fails
with a retained native process error; no fallback replaces geometry.
"""
import math
from pathlib import Path
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/floor_context.py').is_file() and (p/'toolchain.lock.json').is_file())
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
from autorouter import floor_context as fc

LIMITS={'pads':512,'footprints':128,'custom_pads':8,'outlines':4,'holes_per_outline':4,'vertices':4096,'coordinate_nm':10**10}

def integer(value):
    if type(value) is not int or abs(value)>LIMITS['coordinate_nm']:raise ValueError('native integer/range differs')
    return value

def point(value):return [integer(value.x),integer(value.y)]

def boolean(value):
    if type(value) is not bool:raise ValueError('native Boolean differs')
    return value

def angle(value):
    if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>3600:raise ValueError('native angle differs')
    return value

def polygon(poly):
    count=integer(poly.OutlineCount());arcs=integer(poly.ArcCount())
    if not 1<=count<=LIMITS['outlines'] or arcs!=0:raise ValueError('bounded straight polygon observation required')
    rows=[];points=0
    def line(shape):
        nonlocal points
        n=integer(shape.PointCount());points+=n
        if n<3 or points>LIMITS['vertices']:raise ValueError('native polygon vertex cap')
        return {'closed':boolean(shape.IsClosed()),'points_nm':[point(shape.CPoint(i)) for i in range(n)]}
    for i in range(count):
        holes=integer(poly.HoleCount(i))
        if not 0<=holes<=LIMITS['holes_per_outline']:raise ValueError('native hole cap')
        rows.append({'outline':line(poly.COutline(i)),'holes':[line(poly.CHole(i,j)) for j in range(holes)]})
    return {'arc_count':arcs,'outlines':rows,'total_vertices':points}

def observe(native,pcbnew):
    pads=[];terminals=[];footprints=[];seen=set();count=0
    for fp in native.GetFootprints():
        if len(footprints)>=LIMITS['footprints']:raise ValueError('native footprint census cap')
        footprints.append({'uuid':str(fp.m_Uuid.AsString()),'reference':str(fp.GetReference()),
            'position_nm':point(fp.GetPosition()),'orientation_degrees':angle(fp.GetOrientationDegrees()),
            'layer':str(pcbnew.LayerName(fp.GetLayer())),'flipped':boolean(fp.IsFlipped())})
    if len(footprints)!=63 or len({row['uuid'] for row in footprints})!=len(footprints):raise ValueError('native footprint census differs')
    for pad in native.GetPads():
        count+=1
        if count>LIMITS['pads']:raise ValueError('native pad census cap')
        uid=str(pad.m_Uuid.AsString())
        if uid in seen:raise ValueError('duplicate native pad UUID')
        seen.add(uid)
        layers=[(layer,name) for layer,name in ((pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')) if pad.IsOnLayer(layer)]
        terminals.append({'uuid':uid,'reference':str(pad.GetParentFootprint().GetReference()),
            'footprint_uuid':str(pad.GetParentFootprint().m_Uuid.AsString()),'number':str(pad.GetNumber()),
            'net':str(pad.GetNetname()),'netcode':integer(pad.GetNetCode()),'copper_layers':[name for _,name in layers],
            'position_nm':point(pad.GetPosition()),'fp_relative_position_nm':point(pad.GetFPRelativePosition()),
            'orientation_degrees':angle(pad.GetOrientationDegrees()),'flipped':boolean(pad.IsFlipped())})
        custom=[(layer,name) for layer,name in layers if pad.GetShape(layer)==pcbnew.PAD_SHAPE_CUSTOM]
        if not custom:continue
        if len(pads)>=LIMITS['custom_pads'] or len(custom)!=1 or custom!=layers:raise ValueError('single-layer custom-pad observation only')
        layer,name=custom[0];fp=pad.GetParentFootprint()
        # Do not use GetCustomShapeAsPolygon(layer): installed compatibility
        # wrapper ignores layer and calls MergePrimitivesAsPolygon(F_Cu,...).
        merged=pcbnew.SHAPE_POLY_SET()
        pad.MergePrimitivesAsPolygon(layer,merged,pcbnew.ERROR_INSIDE)
        world=pcbnew.SHAPE_POLY_SET()
        pad.TransformShapeToPolygon(world,layer,0,1,pcbnew.ERROR_INSIDE)
        effective=pad.GetEffectivePolygon(layer,pcbnew.ERROR_INSIDE)
        pads.append({'uuid':uid,'reference':str(fp.GetReference()),'number':str(pad.GetNumber()),
            'net':str(pad.GetNetname()),'netcode':integer(pad.GetNetCode()),'copper_layers':[name],
            'shape_enum':int(pad.GetShape(layer)),'anchor_enum':int(pad.GetAnchorPadShape(layer)),
            'shape':'custom','anchor':'rect' if pad.GetAnchorPadShape(layer)==pcbnew.PAD_SHAPE_RECTANGLE else 'other',
            'attribute_enum':int(pad.GetAttribute()),'attribute':'smd' if pad.GetAttribute()==pcbnew.PAD_ATTRIB_SMD else 'other',
            'size_nm':point(pad.GetSize(layer)),'offset_nm':point(pad.GetOffset(layer)),'drill_nm':point(pad.GetDrillSize()),
            'position_nm':point(pad.GetPosition()),'fp_relative_position_nm':point(pad.GetFPRelativePosition()),
            'orientation_degrees':angle(pad.GetOrientationDegrees()),'pad_flipped':boolean(pad.IsFlipped()),
            'footprint_uuid':str(fp.m_Uuid.AsString()),'footprint_position_nm':point(fp.GetPosition()),
            'footprint_orientation_degrees':angle(fp.GetOrientationDegrees()),'footprint_flipped':boolean(fp.IsFlipped()),
            'merged_local':polygon(merged),'transformed_world':polygon(world),'effective_world':polygon(effective)})
    if len(pads)!=2 or count!=247:raise ValueError('pinned original custom-pad census differs')
    return {'schema':1,'pads':sorted(pads,key=lambda row:row['uuid']),'total_pad_count':count,'limits':LIMITS,
            'all_terminals':sorted(terminals,key=lambda row:row['uuid']),'all_footprints':sorted(footprints,key=lambda row:row['uuid']),
            'apis':{'local':'MergePrimitivesAsPolygon(actual_copper_layer, ERROR_INSIDE)',
                    'world':'TransformShapeToPolygon(actual_copper_layer, clearance=0, max_error_nm=1, ERROR_INSIDE)',
                    'effective':'GetEffectivePolygon(actual_copper_layer, ERROR_INSIDE)'},
            'routing_accepted':False,'geometry_qualified':False}

def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if len(args)!=4:raise ValueError('source, floor context, native DSN, custom observation required')
    source,context,dsn,custom=map(Path,args)
    fc.collect('export',source,context,dsn,observation_output=custom,observer=observe)

if __name__=='__main__':main()
