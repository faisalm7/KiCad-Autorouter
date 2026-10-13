"""Prospective KiCad3.9 memory-only alias export; ROOT sequential lane only."""
import copy,json,sys
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/floor_context.py').is_file())
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT),str(HERE)]
from autorouter import floor_context as fc,sexpr as sx
from experiments.roller_support_v1.worker import observe as text_observe
# ROOT promotes the separately reviewed transformer alongside this worker.
from padless_alias import plan,native_export

def literal_surfaces(node):
    if not isinstance(node,list) or not node:return
    if node[0] in ('gr_text','fp_text','gr_text_box','fp_text_box','dimension') or node[0]=='property' and sx.one(node,'layer') is not None:
        if any(isinstance(x,str) and any(t in x for t in ('${','%R','%V')) for x in node[1:]):raise ValueError('surface text expansion outside qualified alias scope')
    for x in node[1:]:literal_surfaces(x)
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
        # These six noncopper Reference display strings/extents are the sole
        # allowed during-alias difference. Position/font/layer/visibility remain.
        for key in ('text','shown','bbox_nm'):refs[0].pop(key)
    return result

def export(source,context,dsn,diagnostic,namespace,before_board,after_board):
    source=Path(source);context=Path(context);dsn=Path(dsn);diagnostic=Path(diagnostic);before_board=Path(before_board);after_board=Path(after_board)
    raw=source.read_bytes();literal_surfaces(sx.parse(raw.decode()));binding=plan(raw,namespace);events=[]
    for x in (dsn,before_board,after_board):
        if x.exists() or x.is_symlink() or x.parent!=context.parent:raise ValueError('fresh exclusive native output required')
    def callback(board,pcbnew):
        snapshot=observe(board,pcbnew)
        if not events:
            if not pcbnew.SaveBoard(str(before_board),board):raise ValueError('native original-reference emission failed')
            def emit(native):
                during=observe(native,pcbnew)
                if without_authorized_reference_display(during,binding,True)!=without_authorized_reference_display(snapshot,binding):raise ValueError('native copper/electrical/field geometry changed during aliases')
                events.append({'phase':'during_alias','observation':during})
                result=pcbnew.ExportSpecctraDSN(native,str(dsn))
                after_export=observe(native,pcbnew)
                if after_export!=during:raise ValueError('export changed native state while aliases active')
                return result
            result=native_export(board,raw,binding,emit,lambda b:observe(b,pcbnew))
            if not pcbnew.SaveBoard(str(after_board),board):raise ValueError('native restored-reference emission failed')
            if sx.read(before_board)!=sx.read(after_board):raise ValueError('original-reference native emission changed after export')
            events.append({'phase':'restored','result':result,'observation':observe(board,pcbnew)})
        return snapshot
    fc.collect('final',source,context,observation_output=diagnostic,observer=callback)
    if len(events)!=2 or not dsn.is_file() or not 0<dsn.stat().st_size<=20*1024**2:raise ValueError('missing bounded native export evidence')
    evidence={'schema':1,'namespace':namespace,'source_sha256':fc.sha(source),'context_sha256':fc.sha(context),'diagnostic_sha256':fc.sha(diagnostic),'dsn_sha256':fc.sha(dsn),'before_board_sha256':fc.sha(before_board),'after_board_sha256':fc.sha(after_board),'events':events,'accepted':False,'production_support':False}
    with context.with_name('alias-evidence.json').open('x') as handle:json.dump(evidence,handle,indent=2);handle.write('\n')
if __name__=='__main__':export(*sys.argv[1:])
