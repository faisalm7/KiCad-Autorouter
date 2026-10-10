"""Invoked ONLY by KiCad's matching bundled Python. No writes to source projects."""
import json
import sys
from pathlib import Path
import pcbnew

def main():
    action, source, output = sys.argv[1:4]
    board = pcbnew.LoadBoard(source)
    if not board:
        raise RuntimeError('KiCad could not load board')
    if action == 'export':
        if not pcbnew.ExportSpecctraDSN(board, output):
            raise RuntimeError('DSN export failed')
    elif action == 'import':
        if not pcbnew.ImportSpecctraSES(board, sys.argv[4]):
            raise RuntimeError('SES import failed')
        pcbnew.SaveBoard(output, board)
    elif action == 'roundtrip':
        pcbnew.SaveBoard(output, board)
    elif action == 'obstacles':
        graphics=list(board.GetDrawings())
        for fp in board.GetFootprints():
            graphics.extend(fp.GraphicalItems())
            graphics.extend([fp.Reference(),fp.Value()])
        obstacles=[]
        for graphic in graphics:
            if not pcbnew.IsCopperLayer(graphic.GetLayer()): continue
            box=graphic.GetBoundingBox()
            obstacles.append({'layer':board.GetLayerName(graphic.GetLayer()),'kind':graphic.GetClass(), 'bbox_mm':[pcbnew.ToMM(box.GetX()),pcbnew.ToMM(box.GetY()),pcbnew.ToMM(box.GetRight()),pcbnew.ToMM(box.GetBottom())]})
        Path(output).write_text(json.dumps(obstacles,indent=2)+'\n')
    elif action == 'metrics':
        tracks = list(board.GetTracks())
        data = {'version':pcbnew.GetBuildVersion(), 'pads':len(list(board.GetPads())),
                'footprints':len(list(board.GetFootprints())), 'zones':len(list(board.Zones())),
                'vias':sum(isinstance(t,pcbnew.PCB_VIA) for t in tracks),
                'track_length_mm':sum(pcbnew.ToMM(t.GetLength()) for t in tracks if not isinstance(t,pcbnew.PCB_VIA)),
                'copper_layers':board.GetCopperLayerCount()}
        Path(output).write_text(json.dumps(data,indent=2)+'\n')
    else:
        raise ValueError('unknown action')

if __name__ == '__main__':
    main()
