"""Bounded real-file handoff falsifiers, mocked validation; no native or engine."""
from pathlib import Path
import hashlib,importlib.util,json,os,signal,subprocess,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
spec=importlib.util.spec_from_file_location('autorouter.review_handoff_original',HERE/'original-handoff.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def case(name,signal_case=False):
 root=HERE/'original-cases'/name;root.mkdir(parents=True,exist_ok=False)
 source=root/'source';run=root/'run';candidate=run/'candidate';source.mkdir();candidate.mkdir(parents=True)
 for folder in [source,candidate]:
  (folder/'board.kicad_pcb').write_text('(kicad_pcb (version 20241229))\n');(folder/'board.kicad_pro').write_text('{"severity":"error"}\n')
 receipt=run/'result.json';receipt.write_text(json.dumps({'source':str(source/'board.kicad_pcb')}));destination=root/'review'
 source_before=p.tree_hash(source);candidate_before=p.tree_hash(candidate);calls=0;fired=False
 verified={'candidate':str(candidate/'board.kicad_pcb'),'candidate_sha256':p.sha(candidate/'board.kicad_pcb')}
 def check(_):
  nonlocal calls,fired
  calls+=1
  if calls==2 and name=='copied_rules_during_second_check':
   (destination/'project/board.kicad_pro').write_text('{"severity":"ignore"}\n');fired=True
  return dict(verified)
 original_save=h.save_json
 def save(path,data):
  nonlocal fired
  original_save(path,data)
  if Path(path).name=='review.json' and not fired:
   if name=='source_after_ready_write':(source/'board.kicad_pro').write_text('{"severity":"ignore"}\n');fired=True
   if name=='copied_board_after_ready_write':(destination/'project/board.kicad_pcb').write_text('(changed board)\n');fired=True
   if name=='interrupt_after_ready_write':fired=True;raise KeyboardInterrupt
   if signal_case:fired=True;os.kill(os.getpid(),signal.SIGTERM)
 outcome={}
 with patch.object(h,'check_result',check),patch.object(h,'save_json',save):
  try:outcome['returned']=h.review_copy(receipt,destination)
  except BaseException as exc:outcome['raised']=type(exc).__name__+': '+str(exc)
 canonical=destination/'review.json';record=json.loads(canonical.read_text()) if canonical.exists() else None
 outcome.update(case=name,checker_calls=calls,injected=fired,canonical_ready=bool(record and record.get('status')=='ready_for_manual_review'),source_changed=p.tree_hash(source)!=source_before,candidate_changed=p.tree_hash(candidate)!=candidate_before,copied_project_matches=destination.exists() and p.tree_hash(destination/'project')==candidate_before,original_module_sha256=p.sha(HERE/'original-handoff.py'),validation_mocked=True,native_jobs=0,engine_jobs=0)
 (root/'outcome.json').write_text(json.dumps(outcome,indent=2)+'\n');return outcome
def main():
 if len(sys.argv)>1 and sys.argv[1]=='--signal-child':case('sigterm_after_ready_write',True);return
 results=[case(name) for name in ['unchanged','copied_rules_during_second_check','source_after_ready_write','copied_board_after_ready_write','interrupt_after_ready_write']]
 child=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--signal-child'],cwd=ROOT,capture_output=True,timeout=5)
 childroot=HERE/'original-cases/sigterm_after_ready_write';ready=json.loads((childroot/'review/review.json').read_text())
 signal_result={'case':'sigterm_after_ready_write','returncode':child.returncode,'canonical_ready':ready['status']=='ready_for_manual_review','owned_signal_sent':'SIGTERM','validation_mocked':True,'native_jobs':0,'engine_jobs':0}
 (childroot/'parent-outcome.json').write_text(json.dumps(signal_result,indent=2)+'\n');results.append(signal_result)
 assert results[0]['canonical_ready'] and results[0]['copied_project_matches'] and not results[0]['source_changed']
 assert all(x['canonical_ready'] for x in results)
 assert not results[1]['copied_project_matches'] and results[2]['source_changed'] and not results[3]['copied_project_matches'] and results[4]['raised'].startswith('KeyboardInterrupt') and child.returncode==-signal.SIGTERM
 summary={'schema':1,'original_sha256':p.sha(HERE/'original-handoff.py'),'unchanged_positive_passed':True,'actual_native_evidence':False,'counterexamples_reproduced':5,'cases':results,'limitations':'Tiny real files with mocked central validation. These reproduce only handoff lifecycle defects; no routing/native correctness or GUI behavior is claimed.'}
 (HERE/'original-reproduction.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'unchanged_positive_passed':True,'counterexamples_reproduced':5,'all_bad_cases_left_ready':True},indent=2))
if __name__=='__main__':main()
