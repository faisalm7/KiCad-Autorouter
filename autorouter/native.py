"""Invoked ONLY by KiCad's matching bundled Python. No writes to source projects."""
import json
import hashlib
import sys
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from autorouter.netclass_native import observe_class

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def netclasses(board, source, before):
    """Resolve native classes without saving/normalizing the source board."""
    board.SynchronizeNetsAndNetClasses(False)
    counts = {}
    for pad in board.GetPads():
        if pad.GetNetCode() > 0 and (pad.IsOnLayer(pcbnew.F_Cu) or pad.IsOnLayer(pcbnew.B_Cu)):
            name = str(pad.GetNetname())
            counts[name] = counts.get(name, 0) + 1
    rows = []
    for name, net in board.GetNetsByName().items():
        if not str(name) or net.GetNetCode() <= 0:
            continue
        cls = net.GetNetClassSlow()
        rows.append({'name': str(name), 'netcode': net.GetNetCode(),
                     'copper_pad_count': counts.get(str(name), 0), **observe_class(cls)})
    project = Path(source).with_suffix('.kicad_pro')
    if before != (file_hash(source), file_hash(project)):
        raise RuntimeError('Board or project changed during native class resolution')
    return {'schema': 1, 'native_version': pcbnew.GetBuildVersion(), 'units': 'integer nanometres',
            'resolution': 'BOARD.SynchronizeNetsAndNetClasses(False); NETINFO_ITEM.GetNetClassSlow()',
            'source': source, 'board_sha256': before[0], 'project_sha256': before[1],
            'board_saved': False, 'nets': sorted(rows, key=lambda row: row['name'])}

def main():
    action, source, output = sys.argv[1:4]
    mapping_requested = action == 'netclasses' or (action == 'export' and len(sys.argv) == 5)
    before = (file_hash(source), file_hash(Path(source).with_suffix('.kicad_pro'))) if mapping_requested or action=='pour-audit' else None
    field_before = tuple(file_hash(Path(source).with_suffix(suffix)) for suffix in ('.kicad_pcb','.kicad_pro','.kicad_sch')) if action=='fields' else None
    board = pcbnew.LoadBoard(source)
    if not board:
        raise RuntimeError('KiCad could not load board')
    if action == 'export':
        mapping = netclasses(board, source, before) if mapping_requested else None
        if not pcbnew.ExportSpecctraDSN(board, output):
            raise RuntimeError('DSN export failed')
        if mapping_requested:
            if before != (file_hash(source), file_hash(Path(source).with_suffix('.kicad_pro'))):
                raise RuntimeError('Board or project changed during DSN export')
            Path(sys.argv[4]).write_text(json.dumps(mapping, indent=2) + '\n')
    elif action == 'netclasses':
        Path(output).write_text(json.dumps(netclasses(board, source, before), indent=2) + '\n')
    elif action == 'import':
        if not pcbnew.ImportSpecctraSES(board, sys.argv[4]):
            raise RuntimeError('SES import failed')
        pcbnew.SaveBoard(output, board)
    elif action == 'roundtrip':
        pcbnew.SaveBoard(output, board)
    elif action == 'pour-audit':
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
        from autorouter.pour_rule_area_native import audit
        result=audit(board,source,before)
        Path(output).write_text(json.dumps(result,indent=2)+'\n')
        if result['passed'] is not True:raise RuntimeError('stored copper intersects prohibited pour area')
    elif action == 'fields':
        footprints=[]
        for fp in board.GetFootprints():
            fields={}
            for field in fp.GetFields():
                if field.IsReference() or field.IsValue() or field.IsComponentClass():continue
                name=str(field.GetName())
                if name in fields:raise RuntimeError('duplicate native footprint field')
                fields[name]=str(field.GetText())
            footprints.append({'uuid':str(fp.m_Uuid.AsString()),'reference':str(fp.GetReference()),'fields':fields})
        if field_before!=tuple(file_hash(Path(source).with_suffix(suffix)) for suffix in ('.kicad_pcb','.kicad_pro','.kicad_sch')):
            raise RuntimeError('Board, project or schematic changed during native field observation')
        Path(output).write_text(json.dumps({'schema':1,'native_version':pcbnew.GetBuildVersion(),'source':source,
            'board_sha256':field_before[0],'project_sha256':field_before[1],'schematic_sha256':field_before[2],
            'board_saved':False,'footprints':sorted(footprints,key=lambda row:row['reference'])},indent=2)+'\n')
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
