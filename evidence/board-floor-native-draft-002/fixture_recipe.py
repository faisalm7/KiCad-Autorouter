"""Original diagnostic geometry, GPL-3.0-or-later; no native dependency.

Opposite-side SMD SIGNAL_A terminals require a copper layer transition. There
are no zones, plated pads, existing vias or physical layer bridges in the task.
The same unchanged original project is used for every fresh diagnostic case.
"""
import copy,uuid
from autorouter import sexpr as sx,pipeline as p

CASES=('positive','track_width','clearance','via_diameter','drill','annulus')
UID_NAMESPACE=uuid.UUID('22273fc2-cbcf-4d22-b8a8-9d0721bdfca3')
def uid(name):return str(uuid.uuid5(UID_NAMESPACE,name))
def quoted(text):return '"'+text+'"'

def original(smoke):
    tree=copy.deepcopy(smoke)
    sample=copy.deepcopy(sx.children(tree,'footprint')[0])
    tree[:]=[n for n in tree if not isinstance(n,list) or not n or n[0] not in {'footprint','net','zone','segment','arc','via'}]
    for index,(x,y,net,side) in enumerate([(10,10,'SIGNAL_A','F'),(40,10,'SIGNAL_A','B'),(10,20,'SIGNAL_B','F'),(40,20,'SIGNAL_B','F')],1):
        fp=copy.deepcopy(sample);fp[1]='"floor_control_terminal"'
        sx.one(fp,'layer')[1]=quoted(side+'.Cu');sx.one(fp,'at')[1:]=[str(x),str(y)]
        fp[:]=[n for n in fp if not isinstance(n,list) or not n or n[0]!='attr'];fp.append(['attr','smd'])
        for prop in sx.children(fp,'property'):
            key=sx.unquote(prop[1]);prop[2]=quoted('J'+str(index) if key=='Reference' else 'floor_control_terminal' if key=='Value' else '')
            sx.one(prop,'layer')[1]=quoted(side+('.SilkS' if key=='Reference' else '.Fab'))
            effects=sx.one(prop,'effects')
            if side=='B':effects.append(['justify','mirror'])
        pad=sx.one(fp,'pad');pad[2:4]=['smd','rect'];sx.one(pad,'size')[1:]=['2','2']
        pad[:]=[n for n in pad if not isinstance(n,list) or not n or n[0] not in {'drill','remove_unused_layers','layers','net'}]
        pad.append(['layers',quoted(side+'.Cu'),quoted(side+'.Paste'),quoted(side+'.Mask')]);pad.append(['net',quoted(net)])
        def identifiers(node,path=''):
            for i,n in enumerate(node):
                if isinstance(n,list) and n:
                    if n[0]=='uuid':n[1]=quoted(uid('J'+str(index)+path))
                    else:identifiers(n,path+'/'+str(i))
        identifiers(fp);tree.append(fp)
    return tree


def segment(name,a,b,layer,net,width='0.3'):
    return ['segment',['start',*map(str,a)],['end',*map(str,b)],['width',width],['layer',quoted(layer)],['net',quoted(net)],['uuid',quoted(uid(name))]]

def candidate(base,case):
    if case not in CASES:raise ValueError('unknown geometry control')
    tree=copy.deepcopy(base)
    upper='10.5' if case=='clearance' else '15'
    nodes=[segment('A-front',(10,10),(35,10),'F.Cu','SIGNAL_A', '0.2' if case=='track_width' else '0.3'),
           segment('A-back',(35,10),(40,10),'B.Cu','SIGNAL_A'),
           ['via',['at','35','10'],['size','0.6' if case=='via_diameter' else '1.5'],['drill','0.2' if case=='drill' else '1.1' if case=='annulus' else '0.3'],['layers','"F.Cu"','"B.Cu"'],['net','"SIGNAL_A"'],['uuid',quoted(uid('A-via'))]],
           segment('B-left',(10,20),(20,20),'F.Cu','SIGNAL_B'),
           segment('B-up',(20,20),(20,upper),'F.Cu','SIGNAL_B'),
           segment('B-near',(20,upper),(30,upper),'F.Cu','SIGNAL_B'),
           segment('B-down',(30,upper),(30,20),'F.Cu','SIGNAL_B'),
           segment('B-right',(30,20),(40,20),'F.Cu','SIGNAL_B')]
    tree.extend(nodes)
    if p.immutable(tree)!=base:raise ValueError('fixture recipe changed immutable geometry')
    expected={'positive':None,'track_width':('track_width',[uid('A-front')]),'clearance':('clearance',[uid('A-front'),uid('B-near')]),'via_diameter':('via_diameter',[uid('A-via')]),'drill':('drill_out_of_range',[uid('A-via')]),'annulus':('annular_width',[uid('A-via')])}[case]
    return tree,expected


def force_via_topology(tree):
    if p.routes(tree) or sx.children(tree,'zone'):raise ValueError('forced-via source must have no routes/zones')
    terminals={}
    for fp in sx.children(tree,'footprint'):
        for pad in sx.children(fp,'pad'):
            if pad[2]!='smd' or sx.one(pad,'drill') is not None:raise ValueError('plated/through-hole layer bridge unsupported')
            copper={sx.unquote(x) for x in sx.one(pad,'layers')[1:] if sx.unquote(x).endswith('.Cu')}
            if len(copper)!=1 or not copper<={'F.Cu','B.Cu'}:raise ValueError('exact single-side SMD pad required')
            net=sx.unquote(sx.one(pad,'net')[1]);terminals.setdefault(net,[]).append(copper)
    forced=[net for net,layers in terminals.items() if len(layers)==2 and layers[0]!=layers[1]]
    if len(forced)!=1:raise ValueError('exactly one opposing-side two-terminal net required')
    return {'net':forced[0],'necessity':'source terminals occupy disjoint F.Cu/B.Cu layers; no other conductive interlayer object exists','source_has_no_layer_bridge':True,'engine_via_emission_qualified':False}
