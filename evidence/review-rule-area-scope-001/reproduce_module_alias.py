"""Pure source preflight bypass; no native execution."""
from pathlib import Path
import json,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
HERE=Path(__file__).resolve().parent
flags=('tracks','vias','pads','copperpour','footprints')
area=['zone',['keepout',*[[key,'not_allowed' if key=='tracks' else 'allowed'] for key in flags]],['placement',['enabled','no'],['sheetname','"/Diagnostic/"']]]
tree=['kicad_pcb',['version','20260206'],['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal']],['module','"owned"',area]]
board=HERE/'source/fixture.kicad_pcb';board.parent.mkdir();sx.write(board,tree);board.with_suffix('.kicad_pro').write_text('{}\n')
result={'scope':'Source/pure preflight only, no native run. Pinned parser accepts module alias as footprint at board loop1267.', 'native_executed':False,'pipeline_sha256':p.sha(ROOT/'autorouter/pipeline.py')}
for name,fn in [('check_rule_area_support',lambda:p.check_rule_area_support(tree)),('preflight',lambda:p.preflight(board))]:
 try:fn();result[name]='accepted'
 except Exception as exc:result[name]=type(exc).__name__+': '+str(exc)
(HERE/'module-alias-001.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
