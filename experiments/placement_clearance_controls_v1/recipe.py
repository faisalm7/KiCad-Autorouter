"""Fixed exposed-case geometry counterfactual; not a general routing repair."""
from copy import deepcopy
from decimal import Decimal
from autorouter import pipeline as p,sexpr as sx

PAD='8e14d5c7-1e43-4f6e-863a-75ee7e612059'
TARGETS={
 '1b4dc6f3-ff49-4fb6-b749-fa13fafadc31':{'start':['105.0376','112.4586'],'end':['107.3545','110.1417'],'delta':['0.015','0.015']},
 'b5b9d5b3-61ab-435d-811e-aacd79aa8d08':{'start':['107.3545','106.6582'],'end':['106.6417','105.9454'],'delta':['0.015','-0.015']},
}
CASES=('unchanged_negative','translated_positive')

def uuid_index(tree):
 out={}
 def visit(node):
  if not isinstance(node,list)or not node:return
  if node[0]=='uuid':
   if len(node)!=2 or not isinstance(node[1],str):raise p.Rejected('malformed UUID')
  for child in node[1:]:
   if isinstance(child,list)and child and child[0]=='uuid':
    if len(child)!=2 or not isinstance(child[1],str):raise p.Rejected('malformed UUID')
    out.setdefault(sx.unquote(child[1]),[]).append(node)
   visit(child)
 visit(tree)
 return out

def translate(tree):
 index=uuid_index(tree);changed=deepcopy(tree);edited=uuid_index(changed)
 for ident,row in TARGETS.items():
  nodes=index.get(ident,[])
  if len(nodes)!=1 or nodes[0][0]!='segment' or nodes[0]not in sx.children(tree,'segment'):raise p.Rejected('target must be one top-level segment')
  node=nodes[0]
  if (sx.one(node,'width')!=['width','0.3']or sx.one(node,'net')!=['net','56']or sx.one(node,'layer')!=['layer','"B.Cu"']
      or sx.one(node,'locked')is not None):raise p.Rejected('fixed target dimensions/net/layer/lock differ')
  for field in ('start','end'):
   if sx.one(node,field)!=[field,*row[field]]:raise p.Rejected('fixed original target coordinates differ')
   sx.one(edited[ident][0],field)[1:]=[format(Decimal(v)+Decimal(delta),'f')for v,delta in zip(row[field],row['delta'])]
 # Exact proof: reverse only the four edited endpoint vectors and recover full source AST.
 restored=deepcopy(changed);back=uuid_index(restored)
 for ident,row in TARGETS.items():
  for field in ('start','end'):sx.one(back[ident][0],field)[1:]=row[field]
 if restored!=tree or p.immutable(changed)!=p.immutable(tree):raise p.Rejected('counterfactual changed unrelated geometry')
 return changed

def prepare(raw,case):
 if case not in CASES:raise p.Rejected('unknown predeclared case')
 tree=sx.parse(raw.decode());translated=translate(tree)
 return raw if case==CASES[0] else (sx.dump(translated)+'\n').encode()

def clearance_pairs(native):
 pairs=[]
 for row in native.get('findings',[]):
  if row.get('type')=='clearance' and row.get('severity')=='error':
   if row.get('excluded',False)is not False:raise p.Rejected('excluded diagnostic finding')
   pairs.append(frozenset(x.get('uuid')for x in row.get('items',[])))
 return pairs

def verdict(case,native,baseline):
 if case not in CASES:raise p.Rejected('unknown case')
 for key in ('opens','blocking','warnings','exclusions'):
  if type(native.get(key))is not int or native[key]<0:raise p.Rejected('invalid native counters')
 if not isinstance(native.get('findings'),list)or native.get('ignored_checks')!=baseline.get('ignored_checks'):raise p.Rejected('native findings/ignored checks differ')
 if native['exclusions']:return False
 def critical(values):
  return {(x['type'],x['severity'],tuple(sorted(i.get('uuid','')for i in x['items'])))for x in values['findings']if x['type']in p.CRITICAL_FINDINGS and x['type']not in ('unconnected_items','clearance')}
 if not critical(native)<=critical(baseline):return False
 expected=[frozenset((PAD,ident))for ident in TARGETS]
 errors=[r for r in native['findings']if r.get('severity')=='error'and r.get('type')!='unconnected_items']
 if case==CASES[0]:
  return (native['opens']==8 and native['blocking']==2 and native['warnings']==baseline['warnings']
          and len(errors)==2 and sorted(map(sorted,clearance_pairs(native)))==sorted(map(sorted,expected)))
 # Stronger than only no new blocking type: require every blocking finding gone.
 # Board acceptance is always separate; remaining opens keep the board rejected.
 return native['opens']<=8 and native['blocking']==0 and not errors and not clearance_pairs(native)
