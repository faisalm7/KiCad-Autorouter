"""Owned GPL smoke derivative; never a benchmark or reference route oracle."""
import copy
from autorouter import sexpr as sx
from experiments.native_components_v1 import fixtures as f

def recipe(base):
 tree,_=f.recipe('zone-islands',base)
 fp=copy.deepcopy(next(x for x in sx.children(tree,'footprint') if f.ref(x)=='J5'))
 sx.one(fp,'at')[:]=['at','14.5','30'];count=0
 def renew(node):
  nonlocal count
  if isinstance(node,list):
   if node and node[0]=='uuid':node[1]=f.uid('chain-J8-'+str(count));count+=1
   for child in node:renew(child)
 renew(fp)
 for prop in sx.children(fp,'property'):
  if sx.unquote(prop[1])=='Reference':prop[2]='"J8"'
 tree.append(fp)
 tree.append(f.segment('essential-GND-bridge',(10,30),(40,30),'GND'))
 points=[(10,30),(10,36)]+[(10+i*.25,36) for i in range(1,19)]+[(14.5,30)]
 redundant=[]
 for i,(a,b) in enumerate(zip(points,points[1:])):
  route=f.segment('redundant-chain-'+str(i),a,b,'GND');tree.append(route);redundant.append(route)
 # One real protected signal route must survive every candidate byte-for-byte.
 sx.children(tree,'segment')[0].append(['locked','yes'])
 return tree,redundant
