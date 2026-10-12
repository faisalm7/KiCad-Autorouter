"""Actual render()/handoff flow with fake plot subprocesses and real small files."""
from pathlib import Path
from unittest.mock import patch
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import handoff as h,review_view as v,pipeline as p
OUT=Path(__file__).parent/sys.argv[1];OUT.mkdir(exist_ok=False)
results=[]
for case in ('positive','earlier_svg','before_project','source_project','postpublish_html','postpublish_cancel','earlier_native_svg','display_write','html_write'):
 directory=OUT/case;directory.mkdir();source=directory/'source';source.mkdir();run=directory/'run';run.mkdir();candidate=run/'candidate';candidate.mkdir()
 name='board<&".kicad_pcb';board='(kicad_pcb (layers (0 "F.Cu" signal) (31 "B.Cu" signal)))'
 for location in (source,candidate):
  (location/name).write_text(board);(location/'board.kicad_pro').write_text('{}')
 source_before=h.pc.inventory(source);candidate_before=h.pc.inventory(candidate)
 receipt=run/'result.json';receipt.write_text(json.dumps({'schema':1,'source':str(source/name),'candidate':str(candidate/name),'candidate_sha256':p.sha(candidate/name),'final_drc':{'opens':0,'blocking':0,'warnings':1,'exclusions':0,'ignored_checks':['<script>alert(1)</script>']},'metrics':{'label':'<&>'}}))
 evidence_before=h.pc.inventory(run);out=directory/'review';calls=[];caught=None;answer=None
 class Job:
  def __init__(self,path,seconds,remaining):
   self.out=path;self.out.mkdir();self.steps=[];self.remaining=remaining
  def step(self,label,argv):
   assert self.remaining()>0;argv=[str(x) for x in argv];calls.append(argv)
   target=Path(argv[argv.index('--output')+1]);target.write_bytes((ROOT/'.runs/review-render-fixture-001/plot-work/plots/before-F.Cu.svg').read_bytes())
   (self.out/(label+'.log')).write_text('fake plot, no native execution\n')
   row={'argv':argv,'status':'success','exit_code':0,'cleanup_complete':True,'name':label};self.steps.append(row)
   (self.out/(label+'-process.json')).write_text(json.dumps(row))
   if len(calls)==2:
    if case=='earlier_native_svg':(self.out/'native-plots/before-F.Cu.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    if case=='earlier_svg':(self.out/'plots/before-F.Cu.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    if case=='before_project':(out/'before'/name).write_text('changed copied original')
    if case=='source_project':(source/name).write_text('changed original')
   return row
 save=h.save_json
 def publish(path,value):
  save(path,value)
  if value.get('status')=='ready_for_manual_review':
   if case=='postpublish_html':(out/'preview.html').write_text('changed HTML')
   if case=='postpublish_cancel':raise KeyboardInterrupt
 write_bytes=Path.write_bytes;injected=[]
 def write_display(path,data):
  result=write_bytes(path,data)
  if ((case=='display_write' and path.parent==out/'plot-work/plots') or (case=='html_write' and path==out/'preview.html')) and not injected:
   path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>REPLACED</text></svg>');injected.append(str(path))
  return result
 identity={'current':True,'applied':False,'candidate':str(candidate/name),'candidate_sha256':p.sha(candidate/name)}
 with patch.object(h,'check_result',return_value=identity),patch.object(v.f,'FloorJob',Job),patch.object(h,'save_json',side_effect=publish),patch.object(Path,'write_bytes',write_display):
  try:answer=h.review_copy(receipt,out,render=True)
  except Exception as e:caught=type(e).__name__+': '+str(e)
 saved=json.loads((out/'review.json').read_bytes())
 if case=='positive' or (case=='display_write' and caught is None):
  assert caught is None and answer['status']==saved['status']=='ready_for_manual_review'
  html=(out/'preview.html').read_text();assert '<script>alert' not in html and '&lt;script&gt;' in html and 'board&lt;&amp;&quot;.kicad_pcb' in html
  assert len(calls)==4 and answer['preview']['native_validation_performed'] is False and answer['preview']['zone_refill_performed'] is False
  for argv in calls:
   assert argv[:4]==[str(p.c.CLI),'pcb','export','svg'] and '--mode-single' in argv
   assert '--check-zones' not in argv and '--save-board' not in argv
   assert argv[argv.index('--layers')+1] in ('F.Cu,Edge.Cuts','B.Cu,Edge.Cuts')
   assert Path(argv[argv.index('--output')+1]).parent==out/'plot-work/native-plots'
 else:assert caught is not None and saved['status'] in ('rejected','cancelled') and not (out/'preview.html').exists()
 assert h.pc.inventory(run)==evidence_before and h.pc.inventory(candidate)==candidate_before
 if case!='source_project':assert h.pc.inventory(source)==source_before
 if case=='positive':
  for raw in (out/'plot-work/native-plots').glob('*.svg'):
   assert (out/'plot-work/plots'/raw.name).read_bytes()==v.display_svg(raw.read_bytes())
 results.append({'injected':injected,'unexpected_ready':case=='display_write' and saved['status']=='ready_for_manual_review','case':case,'error':caught,'canonical_status':saved['status'],'plot_calls':len(calls),'canonical_html_present':(out/'preview.html').exists(),'source_unchanged':h.pc.inventory(source)==source_before,'evidence_unchanged':True})
value={'scope':'Fake native plot stages and central checker; real render/handoff and real small files. No native/JVM/network/Git command.','source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('autorouter/review_view.py','autorouter/handoff.py','autorouter/__main__.py','tests/test_review_view.py')},'cases':results}
(OUT/'results.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
