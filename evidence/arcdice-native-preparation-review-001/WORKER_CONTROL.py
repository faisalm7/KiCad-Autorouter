"""Pure worker getter/decode controls; never imports pcbnew or runs tools."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from experiments.arcdice_native_class_v1 import worker as w,source as s
names=w.namespace({'net_settings':{'classes':[{'name':'Default'},{'name':'POWER'},{'name':'SIGNAL'}]}})
results={}
for name in ['POWER,Default','SIGNAL,Default','Default']:
 assert w.decode(name,names)==name.split(',')
for name in ['POWER,Default,Default','POWER,Unknown','POWER,','POWER,,Default','POWER,POWER','power,Default']:
 try:w.decode(name,names)
 except ValueError:pass
 else:raise AssertionError('bad class encoding admitted')
for candidates in [['Default','default'],['Default','kicad_default'],['Default','POWER,Default'],['Default','POWER','power']]:
 try:w.namespace({'net_settings':{'classes':[{'name':n} for n in candidates]}})
 except ValueError:pass
 else:raise AssertionError('ambiguous namespace admitted')
class FakeClass:
 def __init__(self,name,priority=1,parent=None):self.name=name;self.priority=priority;self.parent=parent;self.thisown=False
 def GetName(self):return self.name
 def GetPriority(self):return self.priority
 def GetTuningProfile(self):return ''
 def __getattr__(self,name):
  if name in [r[0] for r in w.FIELDS.values()]:return lambda:600000 if name in ['GetTrackWidth','GetViaDiameter'] else 300000 if name=='GetViaDrill' else 200000
  if name in [r[1] for r in w.FIELDS.values()]:return lambda:self.parent or self
  if name in [r[2] for r in w.FIELDS.values()]:return lambda:1 if name=='HasViaDrill' else True
  raise AssertionError('unexpected native/vector/setter method '+name)
def observe(encoded):
 cls=FakeClass(encoded,parent=FakeClass('POWER'));net=SimpleNamespace(GetNetCode=lambda:1,GetNetClassSlow=lambda:cls)
 return w.observer(names)(SimpleNamespace(GetNetsByName=lambda:{'/N':net}),None)
good=observe('POWER,Default');assert good['closed_namespace_decoding_complete'] and good['nets'][0]['proposed_structure_matches'] and good['constituent_vector_api_called'] is False and good['production_support_qualified'] is False
bad=observe('POWER,Unknown');assert bad['closed_namespace_decoding_complete'] is False and bad['failed_net_names']==['/N'] and bad['nets'][0]['read_error']
unsupported=observe('POWER,SIGNAL,Default');assert unsupported['closed_namespace_decoding_complete'] and unsupported['nets'][0]['proposed_structure_matches'] is False and unsupported['production_support_qualified'] is False
results.update(closed_encodings_and_collision_negatives=True,known_parent_scalar_observation=True,no_vector_or_setter_called=True,unknown_read_error_visible=True,unsupported_structure_visible_without_admission=True)
captured=s.capture();expected={r['source_path']:r['sha256'] for r in s.ROWS}
assert len(captured)==5 and sum(map(len,captured.values()))==s.TOTAL_BYTES and {n:hashlib.sha256(raw).hexdigest() for n,raw in captured.items()}==expected
results['actual_five_original_files_exact_read_only']=True
results['code_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['experiments/arcdice_native_class_v1/worker.py','experiments/arcdice_native_class_v1/source.py','experiments/arcdice_native_class_v1/PROTOCOL.json','experiments/original_project_native_v1/driver.py','autorouter/floor_context.py']}
print(json.dumps({'schema':1,'scope':'Pure getter/decode controls plus read-only existing source capture; no native/source admission','results':results},indent=2))
