"""Fresh-export parity metadata gate; stops before geometry/native validation."""
from pathlib import Path
import json,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,review_export as e,floor_route as f
OWN=Path(__file__).resolve().parent;actual=f.read_json(OWN/'actual-audit.json');binding={'source':str(ROOT/'.runs/ardujoy-original-native-001/original/Ardujoy_HW/Ardujoy_HW.kicad_pcb'),'source_hashes':actual['original_project_sha256']};report={'scope':'whole_board_unlocked_routing','schematic_parity':'not checked'};rows=[]
class GuardReached(RuntimeError):pass
for declaration in ['not checked','unavailable: no native schematic in source project','checked by final native DRC']:
 with patch.object(p,'preflight',side_effect=GuardReached('after parity gate, before geometry/native validation')):
  try:e.check_stage(OWN,{'schematic_parity':declaration},binding,report,None,None,None)
  except GuardReached as ex:outcome='reached-geometry-gate';reason=str(ex)
  except p.Rejected as ex:outcome='rejected-at-parity-gate';reason=str(ex)
 expected='reached-geometry-gate' if declaration=='checked by final native DRC' else 'rejected-at-parity-gate';rows.append({'declaration':declaration,'outcome':outcome,'expected':expected,'matched':outcome==expected,'reason':reason})
p.save_json(OWN/'export-parity-gate-results.json',{'native_validation_performed':False,'source_sha256':p.sha(ROOT/'autorouter/review_export.py'),'historical_route_report_declaration':'not checked','current_source_has_native_schematic':True,'results':rows});assert all(x['matched'] for x in rows);print(json.dumps(rows,sort_keys=True))
