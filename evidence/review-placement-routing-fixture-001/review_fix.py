"""Isolated draft identity controls using retained actual inputs; no native execution."""
from pathlib import Path
import sys,json,copy,importlib.util,hashlib
HERE=Path(__file__).resolve().parent;ROOT=next(x for x in HERE.parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import sexpr as sx,pipeline as p
spec=importlib.util.spec_from_file_location('reviewed_floor',HERE/'proposed-board-floor.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
RUN=ROOT/'.runs/placement-routing-fixture-001';before=p.tree_hash(RUN);task=sx.read(RUN/'floor-export-input/fixture.kicad_pcb');native=json.loads((RUN/'floor-export-context.json').read_text());project=(RUN/'floor-export-input/fixture.kicad_pro').read_bytes();raw=(RUN/'native.dsn').read_bytes();tests=[]
def check(label,t,accept=False,names=None):
 try:value=g.source_net_identity(t)[0]
 except ValueError as exc:
  if accept:raise
  tests.append({'case':label,'passed':True,'outcome':'rejected','reason':str(exc)});return
 if not accept:raise AssertionError('accepted '+label)
 if names is not None:assert value==set(names),(label,value)
 tests.append({'case':label,'passed':True,'outcome':'parsed','names':sorted(value)})
check('actual named pads plus explicit unrestricted area zero',task,True,['SIGNAL_A','SIGNAL_B'])
for marker in ('1','-1','00','0.0','+0','unknown'):
 t=copy.deepcopy(task);sx.one(sx.children(t,'zone')[0],'net')[1]=marker;check('rule-area noncanonical numeric/alias '+marker,t)
for ownerkind in ('pad','route','nested_zone'):
 t=copy.deepcopy(task)
 if ownerkind=='pad':sx.one(sx.children(sx.children(t,'footprint')[0],'pad')[0],'net')[1]='0'
 elif ownerkind=='route':t.append(['segment',['net','0']])
 else:
  z=sx.children(t,'zone')[0];t.remove(z);sx.children(t,'footprint')[0].append(z)
 check('numeric zero outside actual board area '+ownerkind,t)
for change in ('duplicate_net','missing_name','nonempty_name','duplicate_name','unknown_flag','duplicate_flag','missing_flag','prohibited','no_keepout'):
 t=copy.deepcopy(task);z=sx.children(t,'zone')[0];ko=sx.one(z,'keepout')
 if change=='duplicate_net':z.append(['net','0'])
 elif change=='missing_name':z.remove(sx.one(z,'net_name'))
 elif change=='nonempty_name':sx.one(z,'net_name')[1]='"SIGNAL_A"'
 elif change=='duplicate_name':z.append(['net_name','""'])
 elif change=='unknown_flag':ko[1][0]='unknown'
 elif change=='duplicate_flag':ko[2]=copy.deepcopy(ko[1])
 elif change=='missing_flag':ko.pop()
 elif change=='prohibited':ko[1][1]='not_allowed'
 elif change=='no_keepout':z.remove(ko)
 check('ambiguous area '+change,t)
t=copy.deepcopy(task);sx.one(sx.children(t,'zone')[0],'net')[1]='"0"';check('quoted zero remains distinct named net',t,True,['SIGNAL_A','SIGNAL_B','0'])
t=copy.deepcopy(task);t.extend([['net','0','""'],['net','1','"SIGNAL_A"'],['net','2','"SIGNAL_B"']])
for fp in sx.children(t,'footprint'):
 for pad in sx.children(fp,'pad'):
  n=sx.one(pad,'net');n[:]=['net','1' if n[1]=='"SIGNAL_A"' else '2',n[1]]
check('legacy declared table preserved',t,True,['SIGNAL_A','SIGNAL_B'])
sx.one(sx.children(sx.children(t,'footprint')[0],'pad')[0],'net')[2]='"SIGNAL_B"';check('legacy declared conflicting code name rejected',t)
guided,receipt=g.transform(raw,native,project,(RUN/'floor-export-input/fixture.kicad_pcb').read_bytes());assert receipt['raw_audit']['terminal_count']==4;tests.append({'case':'actual same-load frozen raw floor transform after isolated draft fix','passed':True,'outcome':'pure transformation only','guided_sha256':g.sha(guided)})
assert p.tree_hash(RUN)==before
result={'schema':1,'native_executed':False,'production_edited':False,'routing_accepted':False,'passed':True,'controls':len(tests),'tests':tests,'draft_sha256':p.sha(HERE/'proposed-board-floor.py'),'original_run_unchanged':True}
with (HERE/'fix-review.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps({'controls':len(tests),'passed':True,'draft_sha256':result['draft_sha256']},indent=2))
