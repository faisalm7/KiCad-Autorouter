"""Exact controller AST negative controls; synthetic only, no Native claim."""
from pathlib import Path
import ast,copy,json,sys
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT)];sys.dont_write_bytecode=True
from autorouter import sexpr as sx
from experiments.four_copper_class_transport_v1 import fixture
names=['F.Cu','In1.Cu','In2.Cu','B.Cu'];packet=fixture.files();tree=sx.parse(packet[fixture.STEM+'.kicad_pcb'].decode());expected={}
for fp in sx.children(tree,'footprint'):
 ref=next(sx.unquote(x[2]) for x in sx.children(fp,'property') if sx.unquote(x[1])=='Reference');pad=sx.one(fp,'pad');net=sx.unquote(sx.one(pad,'net')[1]);uid=sx.unquote(sx.one(pad,'uuid')[1])
 expected[uid]=dict(reference=ref,number='1',net=net,layers=['In1.Cu'] if ref=='J1' else names)
board=ROOT/'.runs/observer-synthetic-input/owned.kicad_pcb';pins={board.name:'pcb',board.with_suffix('.kicad_pro').name:'pro'}
pads=[dict(uuid=uid,netcode=1,**row) for uid,row in expected.items()]
base=dict(kind='actual-native-four-cu-api-class-census',native_version='10.0.0',source=str(board),board_saved=False,routing_accepted=False,source_files_sha256=pins,pads=pads,legacy_outer_counts={'ROUTE':1,'KEEP':2,'GND':2},netclasses=dict(source=str(board),board_sha256='pcb',project_sha256='pro',board_saved=False,nets=[dict(name=n,copper_pad_count=2) for n in ['ROUTE','GND','KEEP']]))
def excerpt(path):
 tree=ast.parse(path.read_text());loops=[n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and [getattr(x,'id',None) for x in n.target.elts]==['name','nt']]
 loop=next(n for n in loops if any(isinstance(v,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='step' for x in v.targets) for v in n.body))
 start=next(i for i,v in enumerate(loop.body) if isinstance(v,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='step' for x in v.targets))
 return compile(ast.Module(body=loop.body[start:],type_ignores=[]),str(path),'exec')
old=excerpt(ROOT/'.runs/four-cu-inner-count-001-before-binding.py');new=excerpt(ROOT/'.runs/run-four-cu-inner-count-001.py')
def refused(code,variant):
 data=copy.deepcopy(base);state=dict(pin='original');record=dict(cases=[])
 if variant=='unknown-pad':data['pads'][2]['uuid']='unrelated-unknown-id'
 if variant=='wrong-source':data['source']='/wrong/source.kicad_pcb'
 def audit(*a,**k):
  if variant=='late-api-mutation':state['pin']='changed'
  return {'passed':True}
 scope=dict(p=NS(Rejected=ValueError,sha=lambda _:state['pin'],tree_hash=lambda _:pins),f=NS(read_json=lambda _:copy.deepcopy(data),canonical=lambda x:json.dumps(x,sort_keys=True)),ls=NS(protected_step=lambda *a:None),netclass=NS(FOUR_COPPER_NAMES=names,audit_native=audit),job=NS(steps=[],out=board.parent.parent),step='',argv=[],output=Path('api.json'),board=board,before=pins,pins=pins,nt=None,name='1000',record=record,expected_pads=expected,json=json)
 # Existing code reads the project only for the audit input. Supply captured project through a tiny Path double.
 class Board:
  name=board.name
  parent=board.parent
  def __str__(self):return str(board)
  def with_suffix(self,_):return NS(name=board.with_suffix('.kicad_pro').name,read_text=lambda:'{}')
 scope['board']=Board()
 try:exec(code,scope)
 except ValueError:return True
 return False
rows=[]
for case in ['late-api-mutation','unknown-pad','wrong-source']:
 before=refused(old,case);after=refused(new,case);assert not before and after,(case,before,after)
 rows.append(dict(case=case,before_refused=before,after_refused=after))
# The exact assignment expression must retain cancellation wrapped by BoundJob.
newtree=ast.parse((ROOT/'.runs/run-four-cu-inner-count-001.py').read_text());oldtree=ast.parse((ROOT/'.runs/four-cu-inner-count-001-before-binding.py').read_text())
def cancelled(tree):
 handler=next(n for n in ast.walk(tree) if isinstance(n,ast.ExceptHandler) and isinstance(n.name,str) and n.name=='exc')
 rec=dict(passed=False,status='failed');exec(compile(ast.Module(body=handler.body,type_ignores=[]),'handler','exec'),dict(record=rec,exc=ValueError('wrapped'),job=NS(steps=[dict(status='cancelled')]),p=NS(Rejected=ValueError)))
 return rec['status']=='cancelled'
assert not cancelled(oldtree) and cancelled(newtree);rows.append(dict(case='wrapped-native-cancellation',before_refused=False,after_refused=True))
out=ROOT/'.runs/four-cu-inner-count-regressions-001';out.mkdir();(out/'result.json').write_text(json.dumps(dict(passed=True,controls=rows,scope='Exact AST isolated software controls only; no Native/DRC/routing/whole publication claim'),indent=2)+'\n');print(json.dumps(dict(passed=True,controls=len(rows))))
