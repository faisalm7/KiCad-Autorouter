"""Tiny real-file renderer controls; plot runner is fake, no native execution."""
from pathlib import Path
import hashlib,json,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import review_view as view,pipeline as p,placement_clearance as pc
OUT=Path(sys.argv[1]).absolute();OUT.mkdir(parents=True,exist_ok=False)
source_hash=hashlib.sha256((ROOT/'autorouter/review_view.py').read_bytes()).hexdigest()
rows=[]
for case in ('unchanged','added_prl','changed_existing_prl','late_existing_file','late_added_rule'):
 root=OUT/case;root.mkdir();source=root/'source';source.mkdir();candidate=root/'candidate';candidate.mkdir();out=root/'review';out.mkdir()
 for directory in (source,candidate):
  (directory/'board.kicad_pcb').write_text('(kicad_pcb (layers (0 "F.Cu" signal) (31 "B.Cu" signal)))')
  (directory/'board.kicad_pro').write_text('{"original":true}')
  if case=='changed_existing_prl':(directory/'board.kicad_prl').write_text('{"existing":true}')
 baseline=[pc.inventory(source),pc.inventory(candidate)];calls=[];mutation=None
 tool=root/'fake-tool';tool.write_bytes(b'not executable')
 class Job:
  def __init__(self,path,*args):self.out=path;path.mkdir();self.steps=[]
  def step(self,name,argv):
   global mutation
   board=Path(argv[-1]);assert board.parent not in (source,candidate);calls.append(str(board.parent))
   target=Path(argv[argv.index('--output')+1]);target.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
   (self.out/(name+'.log')).write_text('fake native plot, no process')
   (self.out/(name+'-process.json')).write_text('{}')
   if case in ('added_prl','changed_existing_prl'):board.with_suffix('.kicad_prl').write_text('{"generated":true}')
   if len(calls)==2 and case.startswith('late_'):
    target=Path(calls[0])/('board.kicad_pro' if case=='late_existing_file' else 'unexpected.kicad_dru')
    target.write_text('unexpected late stage change');mutation=str(target)
 def material():assert [pc.inventory(source),pc.inventory(candidate)]==baseline
 pin={'tools':{'kicad_cli':{'path':str(tool),'sha256':p.sha(tool)}}}
 error=None;result=None
 with patch.object(view.c,'CLI',tool),patch.object(view.f,'read_json',return_value=pin),patch.object(view.f,'FloorJob',Job):
  try:result=view.render(out,source/'board.kicad_pcb',candidate/'board.kicad_pcb',{},lambda:30,material)
  except Exception as exc:error=type(exc).__name__+': '+str(exc)
 complete=result is not None
 rows.append({'case':case,'render_returned':complete,'error':error,'originals_unchanged':[pc.inventory(source),pc.inventory(candidate)]==baseline,'mock_plot_calls':len(calls),'mutation':mutation,
              'late_file_in_frozen_files':str(Path(mutation).relative_to(out)) in result['files'] if mutation and result else None,
              'expected_render_returned':case in ('unchanged','added_prl'),'expectation_satisfied':complete==(case in ('unchanged','added_prl'))})
assert hashlib.sha256((ROOT/'autorouter/review_view.py').read_bytes()).hexdigest()==source_hash
summary={'schema':1,'review_view_sha256':source_hash,'native_executed':False,'cases':rows,'all_expectations_met':all(x['expectation_satisfied'] for x in rows)}
(OUT/'results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
