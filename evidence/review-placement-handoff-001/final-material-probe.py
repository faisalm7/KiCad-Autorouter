"""Independent tiny real-file test of the proposed handoff final publication window."""
from pathlib import Path
import importlib.util,json,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
spec=importlib.util.spec_from_file_location('autorouter.review_handoff_snapshot',HERE/'snapshot-001/handoff.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def run(name,mutate=False):
 base=HERE/'final-material-probe-001'/name;base.mkdir(parents=True,exist_ok=False);source=base/'source';candidate=base/'run/candidate';source.mkdir();candidate.mkdir(parents=True);output=base/'review'
 for folder in (source,candidate):
  (folder/'board.kicad_pcb').write_text('(kicad_pcb)\n');(folder/'board.kicad_pro').write_text('{}\n')
 receipt=candidate.parent/'result.json';digest=p.sha(candidate/'board.kicad_pcb');receipt.write_text(json.dumps({'schema':1,'source':str(source/'board.kicad_pcb'),'candidate':str(candidate/'board.kicad_pcb'),'candidate_sha256':digest}))
 good={'current':True,'applied':False,'candidate':str(candidate/'board.kicad_pcb'),'candidate_sha256':digest};counts={'checks':0,'runtime':0,'injected':False};actual=h.runtime_inventory
 def check(_):counts['checks']+=1;return dict(good)
 def runtime():
  counts['runtime']+=1;ret=actual()
  # In this frozen source, initial snapshot + eight material samples. Last
  # material starts only after the postpublication canonical read.
  if mutate and counts['runtime']==9:
   path=output/'review.json';data=json.loads(path.read_text());data['candidate_sha256']='0'*64;path.write_text(json.dumps(data));counts['injected']=True
  return ret
 with patch.object(h,'check_result',check),patch.object(h,'runtime_inventory',runtime):
  try:returned=h.review_copy(receipt,output);error=None
  except BaseException as exc:returned=None;error=type(exc).__name__+': '+str(exc)
 canonical=json.loads((output/'review.json').read_text()) if (output/'review.json').exists() else None
 result={'case':name,'module_sha256':p.sha(HERE/'snapshot-001/handoff.py'),'counts':counts,'raised':error,'canonical_ready':canonical and canonical.get('status')=='ready_for_manual_review','canonical_candidate_hash':canonical.get('candidate_sha256') if canonical else None,'actual_candidate_hash':digest,'canonical_matches_returned':canonical==returned,'validation_mocked':True,'native_jobs':0}
 (base/'outcome.json').write_text(json.dumps(result,indent=2)+'\n');return result
rows=[run('unchanged'),run('canonical_mutated_during_final_material',True)]
assert rows[0]['canonical_ready'] and rows[0]['canonical_matches_returned']
assert rows[1]['counts']['injected'] and rows[1]['canonical_ready'] and not rows[1]['canonical_matches_returned']
(HERE/'final-material-probe-001/summary.json').write_text(json.dumps({'schema':1,'unchanged_positive':True,'blocking_finding_reproduced':True,'cases':rows},indent=2)+'\n');print(json.dumps(rows,indent=2))
