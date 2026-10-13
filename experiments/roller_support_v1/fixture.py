"""Owned two-pad copper-text controls derived from the board-floor fixture."""
import copy,json,uuid
from autorouter import sexpr as sx,pipeline as p
NS=uuid.UUID('75cb0fc5-41d9-4e4f-9c4d-67f96a4335db')
def uid(name):return str(uuid.uuid5(NS,name))
def fixture(tree,project,*,negative=False,layer_type='jumper'):
    if layer_type not in ('jumper','signal'):raise ValueError('declared layer type required')
    t=copy.deepcopy(tree);t[:]=[n for n in t if not isinstance(n,list) or not n or n[0] not in {'footprint','zone','segment','arc','via','net','gr_text'}]
    for n in sx.one(t,'layers')[1:]:
        if n[1]=='"B.Cu"':n[2]=layer_type
    for index,x in enumerate(('20','40')):
        t.append(['footprint','"OwnedCopperTextTerminal"',['layer','"F.Cu"'],['uuid',json.dumps(uid('fp'+str(index)))],['at',x,'10'],
            ['property','"Reference"',json.dumps('J'+str(index+1)),['at','0','-3'],['layer','"F.Fab"'],['hide','yes'],['effects',['font',['size','1','1']]]],
            ['property','"Value"','"OwnedCopperTextTerminal"',['at','0','3'],['layer','"F.Fab"'],['hide','yes'],['effects',['font',['size','1','1']]]],
            ['attr','board_only','exclude_from_pos_files','exclude_from_bom'],['pad','"1"','smd','rect',['at','0','0'],['size','2','2'],['layers','"F.Cu"','"F.Paste"','"F.Mask"'],['net','"SIGNAL_A"'],['uuid',json.dumps(uid('pad'+str(index)))]]])
    y='20' if negative else '10'
    for name,a,b,layer in [('left',['20','10'],['25',y],'F.Cu'),('cross',['25',y],['35',y],'B.Cu'),('right',['35',y],['40','10'],'F.Cu')]:
        t.append(['segment',['start',*a],['end',*b],['width','0.3'],['layer',json.dumps(layer)],['net','"SIGNAL_A"'],['uuid',json.dumps(uid(name))]])
    for name,x in [('via-left','25'),('via-right','35')]:
        t.append(['via',['at',x,y],['size','1.5'],['drill','0.3'],['layers','"F.Cu"','"B.Cu"'],['net','"SIGNAL_A"'],['uuid',json.dumps(uid(name))]])
    t.append(['gr_text','"X"',['at','30','20','0'],['layer','"B.Cu"','knockout'],['uuid',json.dumps(uid('text'))],['effects',['font',['size','1','1'],['thickness','0.25']],['justify','mirror']]])
    # Identical original floor/class/severity settings; only owned fixture geometry/layer type differ.
    return t,copy.deepcopy(project)
