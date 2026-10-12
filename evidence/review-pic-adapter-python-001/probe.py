"""Bounded pure adapter-observation falsifiers; no native/JVM/engine execution."""
import copy, hashlib, json, sys
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from experiments.pic_mixed_transport_probe_v1 import routing_adapter as a, routing_checks as c
OUT=Path(__file__).resolve().parent
retained=json.loads((ROOT/'evidence/pic-selective-area-observation-002/observations.json').read_text())['case']['state_after_selective']
raw=(ROOT/'evidence/pic-selective-routing-001/unrouted.dsn').read_bytes()
context=json.loads((ROOT/'evidence/pic-mixed-transport-probe-005/context.json').read_text())
_,_,receipt=a._derive(raw,context)
state=copy.deepcopy(retained)
plane=next(x for x in state['areas'] if x['nets']==['GND']);pid=plane['id']
state['areas']=[x for x in state['areas'] if x['id']!=pid];state['census']['areas']-=1
state['items']=[x for x in state['items'] if x['id']!=pid]
next(n for n in state['nets'] if n['name']=='GND')['contains_plane']=False
kind='app.freerouting.board.model.items.ObstacleArea'
state['adapter_obstacles']=[copy.deepcopy(x) for x in state['items'] if x['kind']==kind]
for index,rect in enumerate(receipt['adapter']['transformations'][1:]):
    layer=state['layers'].index(rect['dsn_layer']);x0,y0,x1,y1=map(Decimal,rect['rect_um'])
    item={'id':30000+index,'kind':kind,'nets':[],'fixed':'SYSTEM_FIXED','clearance_class_index':1,'first_layer':layer,'last_layer':layer,'contacts':[]}
    state['items'].append(item)
    ring=[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
    integer=[[int(x*10) for x in pt] for pt in ring]
    state['adapter_obstacles'].append(dict(copy.deepcopy(item),name=None,layer_index=layer,layer=rect['dsn_layer'],
        holes=0,hole_shapes=[],ring_unavailable=False,border_class='app.freerouting.geometry.planar.IntBox',corner_count=4,
        ring_classes=['app.freerouting.geometry.planar.IntPoint']*4,ring_um=[[float(x) for x in pt] for pt in ring],ring_board_integer=integer,
        bounds_board_integer=[int(x0*10),int(y0*10),int(x1*10),int(y1*10)],bounds_um=list(map(float,[x0,y0,x1,y1])),
        border_bounds_board_integer=[int(x0*10),int(y0*10),int(x1*10),int(y1*10)],border_bounds_um=list(map(float,[x0,y0,x1,y1]))))
state['adapter_obstacle_count']=33

def bowtie(v):
    row=v['adapter_obstacles'][-1]
    for key in ('ring_um','ring_board_integer','ring_classes'):
        row[key]=[row[key][i] for i in (0,2,1,3)]

def wrong_layer(v):
    row=v['adapter_obstacles'][-1];wrong=1-row['layer_index']
    row.update(layer_index=wrong,first_layer=wrong,last_layer=wrong)
    next(i for i in v['items'] if i['id']==row['id']).update(first_layer=wrong,last_layer=wrong)

def unavailable_border(v):
    v['adapter_obstacles'][-1].update(ring_unavailable=True,border_class='app.freerouting.geometry.planar.Circle',corner_count=0)

results=[]
for name,fn in [('positive',lambda v:None),('bowtie_order',bowtie),('wrong_layer_index',wrong_layer),('unavailable_border',unavailable_border)]:
    value=copy.deepcopy(state);fn(value)
    if name!='positive':assert value!=state
    try:matched=c.adapter_projection(value,retained,receipt);result={'accepted':True,'matched':len(matched)}
    except Exception as exc:result={'accepted':False,'error':type(exc).__name__+': '+str(exc)}
    results.append({'case':name,**result})
files=['routing_adapter.py','routing_checks.py','selective.py','routing_native.py','driver.py','ADAPTER_PROTOCOL.json']
record={'scope':'Synthetic observer JSON over retained public state; not actual native/importer evidence. No source/run mutations.',
        'sources':{n:hashlib.sha256((ROOT/'experiments/pic_mixed_transport_probe_v1'/n).read_bytes()).hexdigest() for n in files},'results':results}
target=OUT/(sys.argv[1] if len(sys.argv)>1 else 'probe-001.json')
with target.open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
print(json.dumps(record,indent=2))
