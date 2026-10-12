"""Tiny real-file negative predicate control; worker stages deliberately mocked."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
module_path=Path(sys.argv[1]);dest=HERE/sys.argv[2];dest.mkdir()
spec=importlib.util.spec_from_file_location('review_ses_native',module_path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
NET='/pic_sockets/VCC_PIC';UID='11111111-1111-4111-8111-111111111111'
source_dir=dest/'source';source_dir.mkdir();source=source_dir/'fixture.kicad_pcb';source.write_text('(kicad_pcb (footprint (pad "1" smd rect (uuid '+UID+') (net "'+NET+'"))))\n');source.with_suffix('.kicad_pro').write_text('{}\n')
pins=p.tree_hash(source_dir);results=[]
for mode in ('error','warning','excluded','wrong_section','wrong_uuid'):
 out=dest/mode;out.mkdir();(out/'raw.ses').write_text('(session)')
 class FakeJob:
  def __init__(self,out,*args):self.out=out;out.mkdir();self.steps=[]
  def native(self,name,action,original,output,*args):output.write_bytes(original.read_bytes())
  def drc(self,name,board,save=False):
   raw={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':board.name,'violations':[],'unconnected_items':[],'schematic_parity':[],'ignored_checks':[],'included_severities':['error','warning','exclusion']}
   if name=='negative-drc':
    finding={'type':'unconnected_items','severity':'warning' if mode=='warning' else 'error','excluded':mode=='excluded','description':'controlled','items':[{'uuid':UID if mode!='wrong_uuid' else 'another','description':'Pad ['+NET+']'}]}
    raw['unconnected_items']=[finding]
    if mode=='wrong_section':raw['violations']=[finding];raw['unconnected_items']=[dict(finding,items=[])]
   path=self.out/(name+'.json');path.write_text(json.dumps(raw));return p.parse_report(path,board.name)
 with patch.object(m,'SesJob',FakeJob),patch.object(m.checks,'disconnected',lambda *a:(b'(session)',{'net':NET,'terminal_count':11})):
  result=m.execute(out,source,[],{}, {'exact_route_survival':False},lambda:30,None,{},lambda:None,{})
 results.append({'case':mode,'negative_detected':result['negative_detected'],'completed':result['completed'],'candidate_emitted':result['candidate_emitted'],'expected_negative_detected':mode=='error'})
assert p.tree_hash(source_dir)==pins
report={'module_sha256':hashlib.sha256(module_path.read_bytes()).hexdigest(),'mocked_workers':True,'source_unchanged':True,'results':results,'all_expected':all(r['negative_detected']==r['expected_negative_detected'] for r in results)}
(dest/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
