"""Read-only Native four-layer API/class/pad census. No export, save or routing."""
from pathlib import Path
import hashlib,json,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,native
import pcbnew,_pcbnew
context,output,source=sys.argv[1:4];nt=p.ExperimentalNativeToolchain.from_record(json.loads(context)) if context!='null' else None;source=Path(source)
from autorouter import config as c
expected_version=nt.expected_version if nt else '10.0.0';expected_python=nt.python if nt else c.PYTHON;expected_pcbnew=nt.pcbnew if nt else c.PCBNEW
if pcbnew.GetBuildVersion()!=expected_version or Path(sys.executable).resolve()!=expected_python.resolve() or Path(_pcbnew.__file__).resolve()!=expected_pcbnew.resolve():raise RuntimeError('loaded matching Native toolchain required')
files=p.tree_hash(source.parent);board=pcbnew.LoadBoard(str(source))
if not board or board.GetCopperLayerCount()!=4:raise RuntimeError('four declared copper layers required')
rows=[]
for name in ('F.Cu','In1.Cu','In2.Cu','B.Cu'):
 lid=board.GetLayerID(name)
 if board.GetLayerName(lid)!=name or not board.IsLayerEnabled(lid):raise RuntimeError('Native declared layer mapping differs')
 rows.append(dict(name=name,id=int(lid),native_type=int(board.GetLayerType(lid)),enabled=bool(board.IsLayerEnabled(lid))))
pads=[]
for pad in board.GetPads():
 pads.append(dict(reference=str(pad.GetParentFootprint().GetReference()),uuid=str(pad.m_Uuid.AsString()),number=str(pad.GetNumber()),netcode=int(pad.GetNetCode()),net=str(pad.GetNetname()),layers=[row['name'] for row in rows if pad.IsOnLayer(row['id'])]))
legacy_outer_counts={}
for pad in board.GetPads():
 if pad.GetNetCode()>0 and (pad.IsOnLayer(pcbnew.F_Cu) or pad.IsOnLayer(pcbnew.B_Cu)):
  name=str(pad.GetNetname());legacy_outer_counts[name]=legacy_outer_counts.get(name,0)+1
mapping=native.netclasses(board,str(source),(native.file_hash(source),native.file_hash(source.with_suffix('.kicad_pro'))))
if p.tree_hash(source.parent)!=files:raise RuntimeError('read-only project changed')
result=dict(schema=1,kind='actual-native-four-cu-api-class-census',native_version=pcbnew.GetBuildVersion(),source=str(source),source_files_sha256=files,layers=rows,pads=pads,netclasses=mapping,legacy_outer_counts=legacy_outer_counts,board_saved=False,routing_accepted=False)
p.save_json(Path(output),result)
