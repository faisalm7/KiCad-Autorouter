"""Owned API falsifiers derived from the GPL smoke fixture, never benchmarks."""
import copy,uuid
from autorouter import sexpr as sx,pipeline as p
CASES=('chain','chain-cut','zone-islands','layer-gap','via-bridge','physical-short')
NS=uuid.UUID('6f557303-292a-4d9d-b5bd-fec4c00461cb')
def uid(label):return '"'+str(uuid.uuid5(NS,label))+'"'
def ref(fp):return sx.unquote(next(n[2] for n in sx.children(fp,'property') if sx.unquote(n[1])=='Reference'))
def segment(label,a,b,net):
 return ['segment',['start',*map(str,a)],['end',*map(str,b)],['width','0.25'],['layer','"F.Cu"'],['net','"'+net+'"'],['uuid',uid(label)]]
def recipe(case,base):
 if case not in CASES:raise p.Rejected('unknown component control')
 tree=copy.deepcopy(base);fps={ref(fp):fp for fp in sx.children(tree,'footprint')}
 if set(fps)!={'J1','J2','J3','J4','J5','J6'} or p.routes(tree) or len(sx.children(tree,'zone'))!=1:raise p.Rejected('exact owned smoke population required')
 fp=copy.deepcopy(fps['J1']);sx.one(fp,'at')[:]=['at','25','10']
 count=0
 def renew(node):
  nonlocal count
  if isinstance(node,list):
   if node and node[0]=='uuid':node[1]=uid('J7-object-'+str(count));count+=1
   for child in node:renew(child)
 renew(fp)
 for node in sx.children(fp,'property'):
  if sx.unquote(node[1])=='Reference':node[2]='"J7"'
 tree.append(fp)
 tree.extend([segment('A-left',(10,10),(25,10),'SIGNAL_A'),segment('B',(10,20),(40,20),'SIGNAL_B')])
 if case!='chain-cut':tree.append(segment('A-right',(25,10),(40,10),'SIGNAL_A'))
 expected=[['J1','J2','J7'],['J3','J4'],['J5','J6']]
 if case=='chain-cut':expected=[['J1','J7'],['J2'],['J3','J4'],['J5','J6']]
 if case=='zone-islands':
  # One valid continuous zone outline with a 0.1mm neck, below its original
  # 0.25mm minimum thickness. Fresh fill separates two pad-bearing islands.
  points=[(6,25),(20,25),(20,29.95),(30,29.95),(30,25),(44,25),(44,34),(30,34),(30,30.05),(20,30.05),(20,34),(6,34)]
  zone=sx.children(tree,'zone')[0];sx.one(zone,'polygon')[:]=['polygon',['pts',*[["xy",str(x),str(y)] for x,y in points]]]
  expected=[['J1','J2','J7'],['J3','J4'],['J5'],['J6']]
 if case in ('layer-gap','via-bridge'):
  fp=fps['J2'];sx.one(fp,'layer')[1]='"B.Cu"';pad=sx.children(fp,'pad')[0];pad[2]='smd'
  pad[:]=[x for x in pad if not(isinstance(x,list) and x and x[0]=='drill')];sx.one(pad,'layers')[:]=['layers','"B.Cu"','"B.Paste"','"B.Mask"']
  if case=='via-bridge':tree.append(['via',['at','40','10'],['size','0.6'],['drill','0.3'],['layers','"F.Cu"','"B.Cu"'],['net','"SIGNAL_A"'],['uuid',uid('bridge-via')]])
  else:expected=[['J1','J7'],['J2'],['J3','J4'],['J5','J6']]
 if case=='physical-short':tree.append(segment('short',(25,10),(25,20),'SIGNAL_A'))
 return tree,sorted(sorted(group) for group in expected)
