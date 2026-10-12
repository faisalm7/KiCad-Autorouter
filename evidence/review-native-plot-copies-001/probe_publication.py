"""Real tiny-file handoff controls; fake central checker/render/runtime, no native."""
from pathlib import Path
import hashlib,json,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import handoff as h,review_view as view,pipeline as p,placement_clearance as pc
OUT=Path(sys.argv[1]).absolute();OUT.mkdir(parents=True,exist_ok=False)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
pins={name:sha(ROOT/name) for name in ('autorouter/review_view.py','autorouter/handoff.py','tests/test_review_view.py')}
rows=[]
for case in ('unchanged','late_added_rule'):
 root=OUT/case;root.mkdir();source=root/'source';source.mkdir();run=root/'run';run.mkdir();candidate=run/'candidate';candidate.mkdir();out=root/'review'
 for directory,board in ((source,'(kicad_pcb)'),(candidate,'(kicad_pcb (candidate))')):
  (directory/'board.kicad_pcb').write_text(board);(directory/'board.kicad_pro').write_text('{}')
 receipt=run/'result.json';identity={'candidate':str(candidate/'board.kicad_pcb'),'candidate_sha256':sha(candidate/'board.kicad_pcb')}
 receipt.write_text(json.dumps({'schema':1,'source':str(source/'board.kicad_pcb'),**identity}))
 before={'source':pc.inventory(source),'run':pc.inventory(run)}
 tool=root/'fake-tool';tool.write_text('not an executable');saved=h.save_json;injected=[]
 def render(destination,before_board,after_board,*args):
  assert before_board.read_bytes()==(source/'board.kicad_pcb').read_bytes()
  assert after_board.read_bytes()==(candidate/'board.kicad_pcb').read_bytes()
  private=destination/'plot-work/before-F.Cu-input';private.mkdir(parents=True)
  (private/'board.kicad_pro').write_text('{}');(destination/'preview.html').write_text('synthetic static preview')
  return {'plotter_sha256':sha(tool),'files':{'preview.html':sha(destination/'preview.html'),'plot-work/before-F.Cu-input/board.kicad_pro':sha(private/'board.kicad_pro')},'input_trees':{'plot-work/before-F.Cu-input':pc.inventory(private)}}
 def publish(path,record):
  saved(path,record)
  if case=='late_added_rule' and record['status']=='ready_for_manual_review':
   target=out/'plot-work/before-F.Cu-input/unexpected.kicad_dru';target.write_text('(version 1)');injected.append(str(target))
 result=None;error=None
 with patch.object(h,'check_result',return_value={'current':True,'applied':False,**identity}),patch.object(h,'runtime_inventory',return_value={'synthetic_runtime':'fixed'}),patch.object(view,'render',side_effect=render),patch.object(h.c,'CLI',tool),patch.object(h,'save_json',side_effect=publish):
  try:result=h.review_copy(receipt,out,render=True)
  except Exception as exc:error=type(exc).__name__+': '+str(exc)
 canonical=json.loads((out/'review.json').read_text())
 row={'case':case,'returned_status':result['status'] if result else None,'canonical_status':canonical['status'],'error':error,'injected':injected,'preview_exists':(out/'preview.html').exists(),'invalidated_files':sorted(x.name for x in out.glob('invalidated-*')),'originals_unchanged':before=={'source':pc.inventory(source),'run':pc.inventory(run)}}
 row['expectation_satisfied']=row['originals_unchanged'] and ((result is not None and row['canonical_status']=='ready_for_manual_review' and row['preview_exists']) if case=='unchanged' else (result is None and row['canonical_status']=='rejected' and not row['preview_exists'] and len(injected)==1 and len(row['invalidated_files'])==2))
 rows.append(row)
assert pins=={name:sha(ROOT/name) for name in pins}
summary={'schema':1,'source_sha256':pins,'native_executed':False,'central_checker_mocked':True,'renderer_mocked':True,'runtime_inventory_mocked':'isolates handoff review from separately owned pipeline edits','cases':rows,'all_expectations_met':all(x['expectation_satisfied'] for x in rows)}
(OUT/'results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
assert summary['all_expectations_met']
