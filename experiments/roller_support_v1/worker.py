"""KiCad3.9 worker: shared same-load export plus layer/copper-text observation."""
import sys
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/floor_context.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter.floor_context import collect

def observe(board,pcbnew):
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

if __name__=='__main__':
    board,context,dsn,diagnostic=sys.argv[1:5]
    collect('export',board,context,dsn,observation_output=diagnostic,observer=observe)
