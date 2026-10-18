"""Invoked ONLY by KiCad's matching bundled Python. No writes to source projects."""
import json
import hashlib
import sys
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from autorouter.netclass_native import observe_class
from autorouter import config as c

FIXED_PLACEMENT_SESSION_POLICY='fixed-placement-session-v1'
EXPORT_ALIAS_POLICY='source-bound-padless-export-v1'
TASK_COPPER_FIXED_POLICY='native-task-copper-fixed-v1'

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def netclasses(board, source, before):
    """Resolve native classes without saving/normalizing the source board."""
    board.SynchronizeNetsAndNetClasses(False)
    count = board.GetCopperLayerCount()
    if type(count) is not int or count not in (2,4): raise ValueError('two/four native copper layers required')
    copper = [(pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')]
    layer_record = None
    if count == 4:
        copper = [(pcbnew.F_Cu,'F.Cu'),(pcbnew.In1_Cu,'In1.Cu'),(pcbnew.In2_Cu,'In2.Cu'),(pcbnew.B_Cu,'B.Cu')]
        layer_record = []
        for index,(layer,name) in enumerate(copper):
            if (int(layer)!=(0,4,6,2)[index] or int(board.GetLayerID(name))!=int(layer)
                    or str(board.GetLayerName(layer))!=name or board.IsLayerEnabled(layer) is not True
                    or int(board.GetLayerType(layer))!=int(pcbnew.LT_SIGNAL)):
                raise ValueError('exact canonical native four-copper signal layer required')
            layer_record.append({'id':int(layer),'name':name,'type':'signal','index':index})
    counts = {}
    for pad in board.GetPads():
        if pad.GetNetCode() > 0 and any(pad.IsOnLayer(layer) for layer,_ in copper):
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
    result = {'schema': 1, 'native_version': pcbnew.GetBuildVersion(), 'units': 'integer nanometres',
            'resolution': 'BOARD.SynchronizeNetsAndNetClasses(False); NETINFO_ITEM.GetNetClassSlow()',
            'source': source, 'board_sha256': before[0], 'project_sha256': before[1],
            'board_saved': False, 'nets': sorted(rows, key=lambda row: row['name'])}
    if layer_record is not None: result['copper_layers'] = layer_record
    return result

def main():
    experimental = len(sys.argv)>1 and sys.argv[1]=='--experimental-native'
    if len(sys.argv)>1 and sys.argv[1]=='--experimental-native':
        if len(sys.argv)<6 or len(sys.argv[2])>16*1024:raise RuntimeError('bounded explicit experimental record required')
        from autorouter.pipeline import ExperimentalNativeToolchain
        toolchain=ExperimentalNativeToolchain.from_record(json.loads(sys.argv[2]))
        import _pcbnew
        if (pcbnew.GetBuildVersion()!=toolchain.expected_version
                or Path(sys.executable).resolve()!=toolchain.python
                or Path(_pcbnew.__file__).resolve()!=toolchain.pcbnew):
            raise RuntimeError('loaded experimental Python/pcbnew version or path differs')
        sys.argv=[sys.argv[0],*sys.argv[3:]]
    else:
        import _pcbnew
        if (pcbnew.GetBuildVersion()!=c.NATIVE_VERSION
                or Path(sys.executable).resolve()!=c.PYTHON.resolve()
                or Path(_pcbnew.__file__).resolve()!=c.PCBNEW.resolve()):
            raise RuntimeError('production native worker version or selected Python/pcbnew path differs')
    from autorouter import task_copper
    fixed=task_copper.FLAG in sys.argv[1:]
    if fixed:
        if (experimental or sys.argv.count(task_copper.FLAG)!=1 or sys.argv[-1]!=task_copper.FLAG
                or sys.argv[1] not in ('export','import') or pcbnew.GetBuildVersion()!=c.NATIVE_VERSION
                or task_copper.POLICY!=TASK_COPPER_FIXED_POLICY):
            raise RuntimeError('unqualified Native task copper flag')
        sys.argv=sys.argv[:-1]
    action, source, output = sys.argv[1:4]
    mapping_requested = action == 'netclasses' or (action == 'export' and len(sys.argv) == 5)
    before = (file_hash(source), file_hash(Path(source).with_suffix('.kicad_pro'))) if mapping_requested or action in ('export','pour-audit') else None
    field_before = tuple(file_hash(Path(source).with_suffix(suffix)) for suffix in ('.kicad_pcb','.kicad_pro','.kicad_sch')) if action=='fields' else None
    board = pcbnew.LoadBoard(source)
    if not board:
        raise RuntimeError('KiCad could not load board')
    if action == 'export':
        mapping = netclasses(board, source, before) if mapping_requested else None
        from autorouter.padless_alias import export_board,POLICY
        if POLICY!=EXPORT_ALIAS_POLICY:raise RuntimeError('Native export alias policy differs')
        exporter=(lambda native,path:task_copper.invoke(native,source,pcbnew,
            lambda:pcbnew.ExportSpecctraDSN(native,path))) if fixed else None
        export_board(board,source,output,pcbnew,mapping=mapping,before=before,exporter=exporter)
        if mapping_requested:
            if before != (file_hash(source), file_hash(Path(source).with_suffix('.kicad_pro'))):
                raise RuntimeError('Board or project changed during DSN export')
            Path(sys.argv[4]).write_text(json.dumps(mapping, indent=2) + '\n')
    elif action == 'netclasses':
        Path(output).write_text(json.dumps(netclasses(board, source, before), indent=2) + '\n')
    elif action == 'import':
        from autorouter.adapter import fixed_placement_session
        from autorouter.placement_clearance import read_bytes
        filtered,session_record=fixed_placement_session(read_bytes(Path(sys.argv[4])))
        if session_record['policy']!=FIXED_PLACEMENT_SESSION_POLICY:
            raise RuntimeError('fixed-placement session policy differs')
        session_path=Path(output).with_suffix('.routes-only.ses')
        with session_path.open('xb') as stream:stream.write(filtered)
        session_record.update(source_session=str(Path(sys.argv[4])),import_session=str(session_path))
        imported=(task_copper.invoke(board,source,pcbnew,
            lambda:pcbnew.ImportSpecctraSES(board,str(session_path)),importing=True)
            if fixed else pcbnew.ImportSpecctraSES(board,str(session_path)))
        if not imported:
            raise RuntimeError('SES import failed')
        pcbnew.SaveBoard(output, board)
        session_record['imported_board_sha256']=file_hash(output)
        with session_path.with_suffix('.json').open('x') as stream:
            stream.write(json.dumps(session_record,indent=2)+'\n')
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
