"""Read-only comparison of original placement-area flags to retained native DSN."""
from pathlib import Path
from decimal import Decimal
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import sexpr as sx,board_floor as g,pipeline as p
source=ROOT/'.data/boards/kicad-multichannel/multichannel_mixer.kicad_pcb'
run=ROOT/'.runs/board-floor-multichannel-001';out=Path(__file__).parent
hashes=p.tree_hash(source.parent);native_hash=p.sha(run/'native.dsn')
board=sx.read(source);dsn=g._parse_dsn((run/'native.dsn').read_text());areas=[]
keepouts=sx.children(sx.one(dsn,'structure'),'keepout');context=json.loads((run/'floor-export-context.json').read_text())
for zone in sx.children(board,'zone'):
 placement=sx.one(zone,'placement')
 if placement is None:continue
 points=sx.one(sx.one(zone,'polygon'),'pts')[1:]
 points=[[int(Decimal(x[1])*1000),-int(Decimal(x[2])*1000)] for x in points]
 flags={x[0]:x[1] for x in sx.one(zone,'keepout')[1:]}
 assert flags==dict.fromkeys(['tracks','vias','pads','copperpour','footprints'],'allowed')
 layers=[sx.unquote(x) for x in sx.one(zone,'layers')[1:]]
 expected=[['keepout','""',['polygon',layer,'0',*[str(v) for pt in points for v in pt],*[str(v) for v in points[0]]]] for layer in layers]
 assert all(keepouts.count(e)==1 for e in expected)
 areas.append({'uuid':sx.unquote(sx.one(zone,'uuid')[1]),'name':sx.unquote(sx.one(zone,'name')[1]),'placement':placement,'flags':flags,'polygon_xy_um_export_coordinates':points,'layers':layers,'exact_native_keepouts':expected})
assert len(areas)==4 and len(keepouts)==8
assert p.tree_hash(source.parent)==hashes and p.sha(run/'native.dsn')==native_hash
report={'schema':1,'analysis_only':True,'routing_accepted':False,'source':str(source),'source_hashes':hashes,'native_dsn_sha256':native_hash,'native_export_process_sha256':p.sha(run/'floor-export-process.json'),'native_context_sha256':p.sha(run/'floor-export-context.json'),'script_sha256':p.sha(Path(__file__)),'areas':areas,'native_structure_keepouts':len(keepouts),'exact_matches':8,'actual_observation':'Four original placement areas permit tracks/vias/pads/copperpour/footprints but correspond exactly to eight generic DSN keepouts. Original source and retained export unchanged.','hypothesis':'False interchange keepouts likely contribute to160opens; this has not yet been causally tested.','required_before_change':'Native controls for allowed placement vs genuine prohibited track/via areas, exact unambiguous map preservation, independent review and new explicit policy/receipt qualification. No source rule or placement area may be deleted or relaxed.'}
with (out/'analysis.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'exact_keepout_matches':8,'areas':4,'hypothesis_only':True}))
