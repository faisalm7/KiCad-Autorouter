from pathlib import Path
import sys,json
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));HERE=Path(__file__).resolve().parent
from autorouter import pipeline as p,sexpr as sx
source=p.sha(ROOT/'autorouter/pipeline.py');rows=[]
for name,layer,allowed in [('empty','""',False),('unknown','"MadeUp.Layer"',False),('numeric','25',False),('literal-offedge','"Dwgs.User"',True)]:
 folder=HERE/name;folder.mkdir();board=folder/'owned.kicad_pcb';tree=['kicad_pcb',['version','20260206'],['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal'],['17','"Dwgs.User"','user']],['gr_text','"Edge.Cuts"',['layer',layer]]];sx.write(board,tree);(folder/'owned.kicad_pro').write_text(json.dumps({'board':{'design_settings':{'rule_severities':{'hole_to_hole':'warning','text_on_edge_cuts':'error'}}},'net_settings':{'classes':[]}}));before=p.tree_hash(folder)
 try:p.preflight(board);admitted=True;error=None
 except p.Rejected as exc:admitted=False;error=str(exc)
 assert admitted is allowed and p.tree_hash(folder)==before;rows.append({'case':name,'admitted':admitted,'error':error,'source_unchanged':True})
assert p.sha(ROOT/'autorouter/pipeline.py')==source
(HERE/'probe.json').write_text(json.dumps({'schema':1,'source_sha256':source,'rows':rows,'native_qualification':False,'native_subprocess_Git_JVM_network_executed':False},indent=2)+'\n');print(json.dumps(rows))
