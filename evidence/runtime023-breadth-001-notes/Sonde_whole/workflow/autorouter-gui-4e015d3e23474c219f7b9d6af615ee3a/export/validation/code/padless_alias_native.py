"""Qualified same-load padless aliases; Native API supplied by the caller.

Mechanically promoted observations from the retained Roller controls. These
observations establish equality, not clearance, routing or asset acceptance.
This module imports without pcbnew; it never loads or saves an input project.
"""
import copy
import hashlib
from pathlib import Path
from . import floor_context as fc, sexpr as sx


def text_observe(board,pcbnew):
    layers=[];texts=[];vertices=0
    types={int(pcbnew.LT_SIGNAL):'signal',int(pcbnew.LT_JUMPER):'jumper'}
    for layer,name in ((pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')):
        kind=int(board.GetLayerType(layer))
        if kind not in types:raise ValueError('unqualified native layer type')
        layers.append({'name':str(board.GetLayerName(layer)),'canonical':name,'type':types[kind]})
    for item in board.GetDrawings():
        if not isinstance(item,pcbnew.PCB_TEXT) or not pcbnew.IsCopperLayer(item.GetLayer()):continue
        poly=pcbnew.SHAPE_POLY_SET();item.TransformTextToPolySet(poly,0,1000,pcbnew.ERROR_INSIDE)
        outlines=[]
        if poly.OutlineCount()>128:raise ValueError('text polygon census cap')
        for i in range(poly.OutlineCount()):
            line=poly.COutline(i);n=int(line.PointCount());vertices+=n
            if vertices>10000:raise ValueError('text polygon vertex cap')
            outlines.append({'points_nm':[[int(line.CPoint(j).x),int(line.CPoint(j).y)] for j in range(n)],'holes':int(poly.HoleCount(i))})
        pos=item.GetPosition();box=item.GetBoundingBox()
        texts.append({'uuid':str(item.m_Uuid.AsString()),'text':str(item.GetText()),'layer':str(pcbnew.LayerName(item.GetLayer())),
                      'knockout':bool(item.IsKnockout()),'position_nm':[int(pos.x),int(pos.y)],
                      'bbox_nm':[int(box.GetX()),int(box.GetY()),int(box.GetRight()),int(box.GetBottom())],
                      'shape_outlines':outlines})
    return {'layers':layers,'copper_text':sorted(texts,key=lambda row:row['uuid']),
            'shape_semantics':'TransformTextToPolySet(clearance=0,max_error=1000nm,ERROR_INSIDE); observational approximation, not clearance proof'}


def xy(v):return [int(v.x),int(v.y)]
def uid(v):return str(v.m_Uuid.AsString())
def box(v):
    b=v.GetBoundingBox();return [int(b.GetX()),int(b.GetY()),int(b.GetRight()),int(b.GetBottom())]


def polygons(poly):
    rows=[];vertices=0
    if poly.OutlineCount()>512:raise ValueError('native polygon census ceiling')
    def points(line):
        nonlocal vertices
        n=int(line.PointCount());vertices+=n
        if vertices>100000:raise ValueError('native polygon vertex ceiling')
        return [xy(line.CPoint(i)) for i in range(n)]
    for i in range(poly.OutlineCount()):rows.append({'outer':points(poly.COutline(i)),'holes':[points(poly.CHole(i,j)) for j in range(poly.HoleCount(i))]})
    return rows


def graphic(item,pcbnew):
    layers=[layer for layer in (pcbnew.F_Cu,pcbnew.B_Cu) if item.IsOnLayer(layer)]
    row={'uuid':uid(item),'kind':str(item.GetClass()),'position_nm':xy(item.GetPosition()),'layer':int(item.GetLayer()),'locked':bool(item.IsLocked()),'bbox_nm':box(item),'copper_polygons':{}}
    if isinstance(item,pcbnew.PCB_TEXT):
        row.update(text=str(item.GetText()),shown=str(item.GetShownText(False)),angle=float(item.GetTextAngleDegrees()),size_nm=[int(item.GetTextWidth()),int(item.GetTextHeight())],thickness_nm=int(item.GetTextThickness()),visible=bool(item.IsVisible()),knockout=bool(item.IsKnockout()))
    for layer in layers:
        poly=pcbnew.SHAPE_POLY_SET();item.TransformShapeToPolygon(poly,layer,0,1,pcbnew.ERROR_INSIDE)
        row['copper_polygons'][str(pcbnew.LayerName(layer))]=polygons(poly)
    return row


def observe(board,pcbnew):
    if board.GetCopperLayerCount()!=2:raise ValueError('two native copper layers required')
    fps=[];pads=[];routes=[];zones=[];drawings=[]
    if len(list(board.GetFootprints()))>512 or len(list(board.GetPads()))>10000 or len(list(board.GetTracks()))>10000:raise ValueError('native item census ceiling')
    for fp in board.GetFootprints():
        fields=[]
        for field in fp.GetFields():fields.append({'name':str(field.GetName()),**graphic(field,pcbnew)})
        if len({r['name'] for r in fields})!=len(fields):raise ValueError('duplicate native field')
        graphics=[graphic(g,pcbnew) for g in fp.GraphicalItems()]
        fps.append({'uuid':uid(fp),'reference':str(fp.GetReference()),'value':str(fp.GetValue()),'fpid':str(fp.GetFPIDAsString()),'position_nm':xy(fp.GetPosition()),'angle':float(fp.GetOrientationDegrees()),'layer':int(fp.GetLayer()),'locked':bool(fp.IsLocked()),'model_count':len(list(fp.Models())),'fields':sorted(fields,key=lambda x:x['name']),'graphics':sorted(graphics,key=lambda x:x['uuid'])})
        if list(fp.Zones()):raise ValueError('footprint zones outside native alias observation scope')
    for pad in board.GetPads():
        layers=[l for l in (pcbnew.F_Cu,pcbnew.B_Cu) if pad.IsOnLayer(l)];shapes={}
        for layer in layers:
            poly=pcbnew.SHAPE_POLY_SET();pad.TransformShapeToPolygon(poly,layer,0,1,pcbnew.ERROR_INSIDE);shapes[str(pcbnew.LayerName(layer))]=polygons(poly)
        pads.append({'uuid':uid(pad),'parent_uuid':uid(pad.GetParentFootprint()),'reference':str(pad.GetParentFootprint().GetReference()),'number':str(pad.GetNumber()),'net':str(pad.GetNetname()),'netcode':int(pad.GetNetCode()),'position_nm':xy(pad.GetPosition()),'angle':float(pad.GetOrientationDegrees()),'drill_nm':xy(pad.GetDrillSize()),'drill_shape':int(pad.GetDrillShape()),'copper_shapes':shapes})
    for route in board.GetTracks():
        if isinstance(route,pcbnew.PCB_ARC):raise ValueError('source arc outside retained-route protocol')
        row={'uuid':uid(route),'net':str(route.GetNetname()),'netcode':int(route.GetNetCode()),'locked':bool(route.IsLocked()),'width_nm':fc.route_width(route,pcbnew)}
        if isinstance(route,pcbnew.PCB_VIA):row.update(kind='via',position_nm=xy(route.GetPosition()),drill_nm=int(route.GetDrillValue()),via_type=int(route.GetViaType()))
        else:row.update(kind='segment',start_nm=xy(route.GetStart()),end_nm=xy(route.GetEnd()),layer=str(pcbnew.LayerName(route.GetLayer())))
        routes.append(row)
    for z in board.Zones():
        zones.append({'uuid':uid(z),'net':str(z.GetNetname()),'outline':polygons(z.Outline()),'fills':{str(pcbnew.LayerName(l)):polygons(z.GetFilledPolysList(l)) for l in (pcbnew.F_Cu,pcbnew.B_Cu) if z.IsOnLayer(l) and z.HasFilledPolysForLayer(l)}})
    for g in board.GetDrawings():drawings.append(graphic(g,pcbnew))
    if sum(len(fp['graphics'])+len(fp['fields']) for fp in fps)+len(drawings)>10000:raise ValueError('native graphic census ceiling')
    return {'layers_text':text_observe(board,pcbnew),'areas':fc.observe_areas(board,pcbnew),'footprints':sorted(fps,key=lambda x:x['uuid']),'pads':sorted(pads,key=lambda x:x['uuid']),'routes':sorted(routes,key=lambda x:x['uuid']),'zones':sorted(zones,key=lambda x:x['uuid']),'drawings':sorted(drawings,key=lambda x:x['uuid']),'shape_semantics':'TransformShapeToPolygon clearance0/error1nm/ERROR_INSIDE: bounded observational equality, not DRC clearance proof'}


def without_authorized_reference_display(observation,binding,during=False):
    result=copy.deepcopy(observation);aliases={r['uuid']:r for r in binding['aliases']}
    for fp in result['footprints']:
        if fp['uuid'] not in aliases:continue
        row=aliases[fp['uuid']]
        if fp['reference']!=(row['alias'] if during else row['reference']):raise ValueError('native alias reference mapping differs')
        fp['reference']=row['reference']
        refs=[f for f in fp['fields'] if f['name']=='Reference']
        if len(refs)!=1 or refs[0]['copper_polygons']:raise ValueError('exact noncopper Reference display required')
        if refs[0]['text']!= (row['alias'] if during else row['reference']):raise ValueError('native Reference field differs')
        # Only the authorized noncopper Reference strings/extents are masked.
        # Position, font, layer, visibility and every other field stay exact.
        for key in ('text','shown','bbox_nm'):refs[0].pop(key)
    return result


def emit(board,raw_source,binding,dsn_path,pcbnew,*,exporter=None):
    """Export with aliases in memory; save only before and after restoration.

    The caller owns the final JSON/proof and complete input-project witness.
    Native emission sidecars and DSN must be fresh siblings outside that input.
    """
    from . import padless_alias
    from .placement_clearance import read_bytes
    padless_alias.require_plan(raw_source,binding)
    source=fc.canonical_path(Path(str(board.GetFileName())))
    dsn=fc.canonical_path(Path(dsn_path))
    if (source.suffix!='.kicad_pcb' or dsn.suffix!='.dsn' or not dsn.parent.is_dir()
            or source.parent==dsn.parent or source.parent in dsn.parents
            or read_bytes(source)!=raw_source):
        raise ValueError('exact loaded source and external canonical DSN output required')
    before_board=dsn.with_name(dsn.stem+'.alias-before.kicad_pcb')
    after_board=dsn.with_name(dsn.stem+'.alias-after.kicad_pcb')
    for path in (dsn,before_board,after_board):
        if path.exists() or path.is_symlink():raise ValueError('fresh exclusive native alias output required')
    before=observe(board,pcbnew);events=[{'phase':'before_alias','observation':before}]
    if not pcbnew.SaveBoard(str(before_board),board):raise ValueError('native original-reference emission failed')
    def export_with_observation(native):
        during=observe(native,pcbnew)
        if without_authorized_reference_display(during,binding,True)!=without_authorized_reference_display(before,binding):
            raise ValueError('native copper/electrical/field geometry changed during aliases')
        events.append({'phase':'during_alias','observation':during})
        exported=(pcbnew.ExportSpecctraDSN if exporter is None else exporter)(native,str(dsn))
        after_export=observe(native,pcbnew)
        if after_export!=during:raise ValueError('export changed native state while aliases active')
        events.append({'phase':'after_export','observation':after_export})
        return exported
    result=padless_alias.native_export(board,raw_source,binding,export_with_observation,lambda b:observe(b,pcbnew))
    restored=observe(board,pcbnew)
    if restored!=before:raise ValueError('native board changed after alias restoration')
    if not pcbnew.SaveBoard(str(after_board),board):raise ValueError('native restored-reference emission failed')
    restored=observe(board,pcbnew)
    if restored!=before:raise ValueError('native board changed during restored emission')
    events.append({'phase':'restored','result':result,'observation':restored})
    before_raw=read_bytes(before_board);after_raw=read_bytes(after_board)
    if sx.parse(before_raw.decode())!=sx.parse(after_raw.decode()):raise ValueError('original-reference native emission changed after export')
    dsn_raw=read_bytes(dsn,20*1024**2)
    if not dsn_raw or read_bytes(source)!=raw_source:raise ValueError('empty DSN or changed source after native alias export')
    return {'schema':1,'source_sha256':hashlib.sha256(raw_source).hexdigest(),
            'dsn_sha256':hashlib.sha256(dsn_raw).hexdigest(),'events':events,
            'before_board':before_board.name,'after_board':after_board.name,
            'before_board_sha256':hashlib.sha256(before_raw).hexdigest(),'after_board_sha256':hashlib.sha256(after_raw).hexdigest(),
            'accepted':False,'production_support':False}
