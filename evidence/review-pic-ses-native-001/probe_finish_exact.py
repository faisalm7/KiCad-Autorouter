"""Focused retained-file cache and tiny mocked-stage continuation controls. No native jobs."""
from pathlib import Path
import copy,hashlib,json,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.pic_mixed_transport_probe_v1 import driver as d,ses_native as n
from autorouter import pipeline as p
cached=ROOT/'.runs/pic-custom-ses-native-001';prior=d.inventory(cached)
old=n.floor.read_json(cached/'summary.json');before=copy.deepcopy(old['runtime'])
for name in ('autorouter/native.py','autorouter/pipeline.py','autorouter/floor_route.py','autorouter/sexpr.py'):
 before['sources'][name]=d.base.content(ROOT/name,2*1024**2,digest=True)
baseline,raw,binding=n.cached_positive(cached,before,prior)
assert baseline['warnings']==41 and not binding['new_baseline_execution'] and not binding['new_positive_import_execution']
read=n.floor.read_json;cache_cases=[]
for kind in ('changed_cwd','altered_cli_flag','positive_input_path','saved_baseline','extra_process','wrong_original','core_changed','frozen_raw','wrong_report'):
 def mutate(path):
  data=copy.deepcopy(read(path))
  if path.name=='summary.json':
   if kind=='changed_cwd':data['steps'][0]['cwd']=str(cached)
   if kind=='altered_cli_flag':data['steps'][0]['argv'].remove('--refill-zones')
   if kind=='positive_input_path':data['steps'][1]['argv'][-3]='another-board.kicad_pcb'
   if kind=='extra_process':data['steps'].append(copy.deepcopy(data['steps'][0]))
   if kind=='wrong_original':data['runtime']['original']['pic_programmer.kicad_pro']='0'*64
   if kind=='core_changed':data['runtime']['sources']['autorouter/native.py']['sha256']='0'*64
   if kind=='frozen_raw':data['frozen_evidence']['ses-native/raw-positive/pic_programmer.kicad_pcb']='0'*64
   if kind=='wrong_report':data['native_ses']['baseline']['warnings']=0
  elif path.name=='baseline-binding.json' and kind=='saved_baseline':data['saved']=True
  elif path.name=='ses-baseline-process.json':
   if kind=='changed_cwd':data['cwd']=str(cached)
   if kind=='altered_cli_flag':data['argv'].remove('--refill-zones')
  elif path.name=='ses-import-positive-process.json' and kind=='positive_input_path':data['argv'][-3]='another-board.kicad_pcb'
  return data
 with patch.object(n.floor,'read_json',side_effect=mutate):
  try:n.cached_positive(cached,before,prior)
  except (ValueError,p.Rejected):rejected=True
  else:rejected=False
 assert rejected,kind
 cache_cases.append({'case':kind,'rejected':rejected})
# Tiny real project, actual validation-copy/execute code, and deliberately mocked native workers.
# The sole false survival obligation must block a candidate even with identical mocked findings.
dest=HERE/'finish-flow-002';dest.mkdir();source_dir=dest/'source';source_dir.mkdir()
NET='/pic_sockets/VCC_PIC';UID='11111111-1111-4111-8111-111111111111'
source=source_dir/'fixture.kicad_pcb';source.write_text('(kicad_pcb (footprint (pad "1" smd rect (uuid '+UID+') (net "'+NET+'"))))\n')
source.with_suffix('.kicad_pro').write_text('{"original_rules":true}\n');(source_dir/'fixture.kicad_dru').write_text('(version 1)\n')
source_pins=p.tree_hash(source_dir)
saved_dir=dest/'saved-import';saved_dir.mkdir();saved=saved_dir/source.name;saved.write_bytes(source.read_bytes())
saved.with_suffix('.kicad_pro').write_text('{"changed_rules":true}\n');saved.with_suffix('.kicad_prl').write_text('generated\n');saved_pins=p.tree_hash(saved_dir)
out=dest/'out';out.mkdir();(out/'raw.ses').write_text('(session)')
base={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':[]};events=[]
class FakeJob:
 def __init__(self,path,*args):self.out=path;path.mkdir();self.steps=[]
 def native(self,name,action,original,output,*args):
  assert name=='import-negative',name
  events.append(name);output.write_bytes(original.read_bytes())
  output.with_suffix('.kicad_pro').write_text('{"new_defaults":true}\n')
 def drc(self,name,board,save=False):
  assert name in ('raw-positive-drc','negative-drc'),name
  events.append(name)
  assert board.name==source.name
  assert p.tree_hash(board.parent)==source_pins
  raw={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':board.name,'violations':[],'unconnected_items':[],'schematic_parity':[],'ignored_checks':[],'included_severities':['error','warning','exclusion']}
  if name=='negative-drc':raw['unconnected_items']=[{'type':'unconnected_items','severity':'error','excluded':False,'description':'controlled','items':[{'uuid':UID,'description':'Pad ['+NET+']'}]}]
  path=self.out/(name+'.json');path.write_text(json.dumps(raw));return p.parse_report(path,board.name)
with patch.object(n,'SesJob',FakeJob),patch.object(n.checks,'disconnected',lambda *a:(b'(session)',{'net':NET,'terminal_count':11})):
 result=n.execute(out,source,[],{}, {'exact_route_survival':False},lambda:30,None,{},lambda:None,{},reuse=(base,saved,{'new_baseline_execution':False,'new_positive_import_execution':False}))
assert events==['raw-positive-drc','import-negative','negative-drc']
assert result['raw_findings_equal'] and result['negative_detected'] and not result['candidate_emitted'] and not result['completed']
assert p.tree_hash(source_dir)==source_pins and p.tree_hash(saved_dir)==saved_pins
assert d.inventory(cached)==prior
report={'passed':True,'scope':'Pure cache falsifiers and mocked-native execute path, not native qualification','source_files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (d.HERE/'driver.py',d.HERE/'ses_native.py',d.HERE/'test_ses.py',d.HERE/'SES_FINISH_PROTOCOL.json',d.HERE/'README.md')},'cached_positive':binding,'cache_falsifiers':cache_cases,'mocked_stage_order':events,'original_rules_preserved':True,'failed_survival_blocks_candidate':True,'raw_cached_run_unchanged':True}
(HERE/'finish-probe-results-002.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
