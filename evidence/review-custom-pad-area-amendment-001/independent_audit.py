"""Read-only existing evidence and independent exact segment reconstruction; no tools executed."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,sys,copy
HERE=Path(__file__).absolute().parent;ROOT=next(p for p in HERE.parents if (p/'autorouter/runner.py').is_file())
sys.path[:0]=[str(HERE/'source'),str(ROOT)]
import derive
from autorouter import sexpr as sx
from autorouter.adapter import _parse_dsn
inputs,expected=derive.prepare(ROOT,lambda p:p.read_bytes())
old=ROOT/'.runs/custom-pad-area-probe-001';observed=json.loads((old/'observations.json').read_bytes());rows=[]
for want,actual in zip(expected,observed['cases']):
 ident=want['case'];raw=(ROOT/derive.BASIS/ident/'native.dsn').read_bytes();a=_parse_dsn(raw.decode());b=_parse_dsn(inputs[ident+'.dsn'].decode());rebuilt=copy.deepcopy(b)
 one=lambda tree,key:next(x for x in tree if isinstance(x,list)and x[0]==key)
 original_wires=one(a,'wiring')[1:];derived_wires=one(b,'wiring')[1:];paths=[w for w in derived_wires if any(isinstance(n,list)and n[0]=='path'for n in w)];areas=[w for w in derived_wires if any(isinstance(n,list)and n[0]=='polygon'for n in w)]
 assert len(areas)==2 and len(paths)==(3 if 'intrusion'in ident else 2)
 for wire in original_wires:
  original_path=one(wire,'path');net=one(wire,'net');start=list(map(Fraction,original_path[3:5]));end=list(map(Fraction,original_path[-2:]));delta=[end[i]-start[i]for i in(0,1)];axis=0 if delta[0]else 1;intervals=[]
  for piece in paths:
   if one(piece,'net')!=net:continue
   shape=one(piece,'path');assert shape[1:3]==original_path[1:3]and len(shape)==7
   assert [n for n in piece if n!=shape]==[n for n in wire if n!=original_path]
   ts=[]
   for x,y in (shape[3:5],shape[5:7]):
    q=[Fraction(x)-start[0],Fraction(y)-start[1]];assert q[0]*delta[1]==q[1]*delta[0];ts.append(q[axis]/delta[axis])
   intervals.append(sorted(ts))
  cursor=Fraction(0)
  for lo,hi in sorted(intervals):assert lo==cursor and hi>lo;cursor=hi
  assert cursor==1
 one(rebuilt,'wiring')[1:]=copy.deepcopy(original_wires)
 oldlib=one(a,'library');newlib=one(rebuilt,'library');changed=[]
 for stack in [n for n in newlib if isinstance(n,list)and n[0]=='padstack']:
  oldstack=next(n for n in oldlib if isinstance(n,list)and n[0]=='padstack'and n[1]==stack[1])
  if stack!=oldstack:
   assert one(stack,'shape')==['shape',['rect','top_layer','-150','-150','150','150']]
   stack[stack.index(one(stack,'shape'))]=copy.deepcopy(one(oldstack,'shape'));changed.append(stack[1])
 assert len(changed)==2 and rebuilt==a
 names={p['reference']:p['padstack_name']for p in actual['states'][-1]['pins']}
 assert all(names[p['reference']]==p['imported_padstack_name']for p in want['pins'])
 assert len(set(want['padstack_name_map'].values()))==4
 state=actual['states'][-1];assert state['board_units_per_um']==10 and all(x['area_um2']==0 for x in state['areas'])
 assert all(v==251.6 for t in state['traces']for v in t['area_clearances_um'].values())
 rows.append({'case':ident,'independent_reverse_AST':True,'independent_exact_trace_union':True,'source_traces':2,'derived_trace_pieces':len(paths),'area_count':len(areas),'actual001_mapped_names_match':True,'actual001_api_area_values':[x['area_um2']for x in state['areas']],'actual001_effective_matrix_um':251.6,'raw250_interpretation':'Inferred from pinned getValue(true)=raw+16 at observed scale10; fresh raw readback still required.','new_capability_native_qualified':False})
report={'scope':'pure current derivation and read-only actual001 observations; no Java/native execution','cases':rows,'passed':True,'prior_observations_sha256':hashlib.sha256((old/'observations.json').read_bytes()).hexdigest()}
(HERE/'independent-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'cases':len(rows),'passed':True}))
