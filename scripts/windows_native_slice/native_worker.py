"""Owned Windows10.0.7 substrate actions; deliberately independent of pipeline."""
import argparse,hashlib,json,sys
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--action',choices=['export','import','fill'],required=True);ap.add_argument('--board',required=True);ap.add_argument('--output',required=True);ap.add_argument('--session');a=ap.parse_args();sys.path.insert(0,a.repo)
import pcbnew,_pcbnew
from autorouter import sexpr as sx,adapter
from autorouter.native import netclasses
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
if pcbnew.GetBuildVersion()!='10.0.7':raise RuntimeError('exact experimental Windows10.0.7 required')
source=Path(a.board);before=(sha(source),sha(source.with_suffix('.kicad_pro')));board=pcbnew.LoadBoard(str(source))
if not board or board.GetCopperLayerCount()!=2:raise RuntimeError('owned two-layer board required')
if a.action=='export':
 classes=netclasses(board,str(source),before)
 if not pcbnew.ExportSpecctraDSN(board,a.output):raise RuntimeError('DSN export failed')
 Path(a.output+'.classes.json').write_text(json.dumps(classes,indent=2)+'\n')
elif a.action=='import':
 raw=Path(a.session).read_bytes();filtered,proof=adapter.fixed_placement_session(raw);path=Path(a.output+'.routes-only.ses');path.write_bytes(filtered)
 if not pcbnew.ImportSpecctraSES(board,str(path)):raise RuntimeError('SES import failed')
 pcbnew.SaveBoard(a.output,board);proof.update(raw_sha256=hashlib.sha256(raw).hexdigest(),filtered_sha256=sha(path));Path(a.output+'.ses-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
else:
 pcbnew.ZONE_FILLER(board).Fill(board.Zones());pcbnew.SaveBoard(a.output,board)
 if not board.GetAreaCount() or not any(zone.GetFilledPolysList(layer).OutlineCount()>0 for zone in board.Zones() for layer in (pcbnew.F_Cu,pcbnew.B_Cu) if zone.IsOnLayer(layer)):raise RuntimeError('nonempty actual zone refill required')
if before!=(sha(source),sha(source.with_suffix('.kicad_pro'))):raise RuntimeError('input PCB/PRO changed')
print(json.dumps(dict(action=a.action,version=pcbnew.GetBuildVersion(),python=sys.executable,pcbnew=str(_pcbnew.__file__),input_sha256=before,output_sha256=sha(a.output))))
