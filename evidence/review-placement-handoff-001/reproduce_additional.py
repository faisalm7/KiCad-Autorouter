"""Two further old-handoff boundary controls. Native checking is explicitly mocked."""
from pathlib import Path
import importlib.util,json,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
spec=importlib.util.spec_from_file_location('autorouter.review_handoff_additional',HERE/'original-handoff.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
rows=[]
for kind in ('dru_during_second_check','canonical_after_ready_write'):
 base=HERE/'additional-original-cases'/kind;base.mkdir(parents=True,exist_ok=False)
 source=base/'source';candidate=base/'run/candidate';source.mkdir();candidate.mkdir(parents=True)
 for folder in (source,candidate):
  (folder/'board.kicad_pcb').write_text('(kicad_pcb)\n');(folder/'board.kicad_pro').write_text('{}\n');(folder/'board.kicad_dru').write_text('(version 1)\n')
 receipt=candidate.parent/'result.json';receipt.write_text(json.dumps({'source':str(source/'board.kicad_pcb')}));destination=base/'review';before=p.tree_hash(candidate);calls=[0]
 verified={'candidate':str(candidate/'board.kicad_pcb'),'candidate_sha256':p.sha(candidate/'board.kicad_pcb')}
 def check(_):
  calls[0]+=1
  if kind=='dru_during_second_check' and calls[0]==2:(destination/'project/board.kicad_dru').write_text('(version 1) (rule "changed")\n')
  return dict(verified)
 actual_save=h.save_json
 def save(path,data):
  actual_save(path,data)
  if kind=='canonical_after_ready_write':
   altered=json.loads(Path(path).read_text());altered['candidate_sha256']='0'*64;Path(path).write_text(json.dumps(altered))
 with patch.object(h,'check_result',check),patch.object(h,'save_json',save):returned=h.review_copy(receipt,destination)
 canonical=json.loads((destination/'review.json').read_text());row={'case':kind,'canonical_ready':canonical['status']=='ready_for_manual_review','copied_project_matches':p.tree_hash(destination/'project')==before,'canonical_matches_returned':canonical==returned,'validation_mocked':True,'native_jobs':0,'engine_jobs':0}
 assert row['canonical_ready'] and (not row['copied_project_matches'] if kind.startswith('dru') else not row['canonical_matches_returned'])
 (base/'outcome.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
(HERE/'additional-original-reproduction.json').write_text(json.dumps({'schema':1,'original_sha256':p.sha(HERE/'original-handoff.py'),'counterexamples':rows},indent=2)+'\n');print(json.dumps(rows,indent=2))
