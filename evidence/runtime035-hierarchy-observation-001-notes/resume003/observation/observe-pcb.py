from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
runtime=Path(sys.argv[6]);sys.path.insert(0,str(runtime))
import pcbnew,_pcbnew
from autorouter import config as c,placement_clearance as io
from autorouter.native import netclasses
board_path,output=map(Path,sys.argv[1:3]);version,python,extension=sys.argv[3:6]
assert c.ROOT==runtime
assert pcbnew.GetBuildVersion()==version==c.NATIVE_VERSION=='10.0.7'
assert Path(sys.executable).resolve()==Path(python).resolve()==c.PYTHON.resolve()
assert Path(_pcbnew.__file__).resolve()==Path(extension).resolve()==c.PCBNEW.resolve()
before=io.inventory(board_path.parent);board=pcbnew.LoadBoard(str(board_path));assert board
mapping=netclasses(board,str(board_path),(before[board_path.name],before[board_path.with_suffix('.kicad_pro').name]))
footprints=[];pads=[]
for fp in board.GetFootprints():
 if len(footprints)>=512:raise ValueError('footprint observation ceiling')
 path=None;error=None
 try:path=str(fp.GetPath().AsString())
 except Exception as exc:error=(type(exc).__name__+': '+str(exc))[:1024]
 footprints.append(dict(uuid=str(fp.m_Uuid.AsString()),reference=str(fp.GetReference()),path=path,path_method_error=error))
for pad in board.GetPads():
 if len(pads)>=10000:raise ValueError('pad observation ceiling')
 fp=pad.GetParentFootprint()
 pads.append(dict(uuid=str(pad.m_Uuid.AsString()),footprint_uuid=str(fp.m_Uuid.AsString()),reference=str(fp.GetReference()),number=str(pad.GetNumber()),netcode=int(pad.GetNetCode()),net=str(pad.GetNetname()),copper=any(pad.IsOnLayer(layer) for layer in (pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu))))
assert io.inventory(board_path.parent)==before
record=dict(schema=1,native_version=pcbnew.GetBuildVersion(),source=str(board_path),input_hashes_before=before,input_hashes_after=before,board_saved=False,native_classes=mapping,footprints=footprints,pads=pads,accepted=False,routing_accepted=False,support_admitted=False)
raw=json.dumps(record,sort_keys=True,indent=2,allow_nan=False)+'\n';assert len(raw.encode())<=8*1024**2
with output.open('x') as stream:stream.write(raw)
