"""Unexecuted owned full4Cu unassigned conductive pad recipe; no Native calls.

SPDX-License-Identifier: GPL-3.0-or-later
Derived from the existing owned four_copper_class_transport_v1 fixture. Its
project, schematic, local settings, components and locked KEEP route stay exact.
New board geometry is authored at creation; this is not a new board family.
"""
import copy,json,uuid
from autorouter import sexpr as sx
from experiments.four_copper_class_transport_v1 import fixture as base
STEM=base.STEM
NS=uuid.UUID('db073620-bdf6-54dc-9cf0-0550f1d34279')
def uid(label):return str(uuid.uuid5(NS,label))
PAD_UUID=uid('unnumbered-no-net-pth')
INTRUSION_UUID=uid('invalid-inner-through-pad')
def q(value):return json.dumps(value)
def segment(label,start,end,layer,net,width):
    return ['segment',['start',*map(str,start)],['end',*map(str,end)],['width',str(width)],
            ['layer',q(layer)],['net',q(net)],['uuid',q(uid(label))]]

def files(case='positive'):
    if case not in {'positive','through_pad'}:raise ValueError('fixed owned case required')
    result=base.files();name=STEM+'.kicad_pcb';tree=sx.parse(result[name].decode())
    fps=[fp for fp in sx.children(tree,'footprint') if any(len(n)>2 and n[1:] and sx.unquote(n[1])=='Reference' and sx.unquote(n[2])=='J3' for n in sx.children(fp,'property'))]
    if len(fps)!=1 or sx.one(fps[0],'at')!=['at','12','16']:raise ValueError('owned J3 placement differs')
    fp=fps[0]
    # Exact HFE-shaped copper/drill fields, at a new owned global (19,10).
    # No pin function/type/net is fabricated; pad remains an unassigned object.
    fp.append(['pad','""','thru_hole','circle',['at','7','-6'],['size','4','4'],['drill','2'],
               ['layers','"*.Cu"','"*.Mask"'],['remove_unused_layers','no'],['uuid',q(PAD_UUID)]])
    # A second disjoint courtyard encloses the added pad without changing the
    # original J3 courtyard or intersecting neighboring component courtyards.
    fp.append(['fp_rect',['start','4.75','-8.25'],['end','9.25','-3.75'],
               ['stroke',['width','0.05'],['type','default']],['fill','none'],
               ['layer','"F.CrtYd"'],['uuid',q(uid('added-pad-courtyard'))]])
    for label,a,b,layer in (
        ('route-front',(12,10),(14,10),'F.Cu'),
        ('route-inner-left',(14,10),(14,13),'In1.Cu'),
        ('route-inner-detour',(14,13),(24,13),'In1.Cu'),
        ('route-inner-right',(24,13),(24,10),'In1.Cu'),
        ('route-back',(24,10),(26,10),'B.Cu')):
        tree.append(segment(label,a,b,layer,'ROUTE','.4'))
    for x in (14,24):
        tree.append(['via',['at',str(x),'10'],['size','1.2'],['drill','.5'],
                     ['layers','"F.Cu"','"B.Cu"'],['net','"ROUTE"'],['uuid',q(uid('route-via-'+str(x)))]])
    tree.append(segment('gnd-completion',(12,24),(26,24),'B.Cu','GND','.35'))
    if case=='through_pad':
        tree.append(segment('invalid-inner-through-pad',(14,'11.6'),(24,'11.6'),'In1.Cu','ROUTE','.4'))
    result[name]=(sx.dump(tree)+'\n').encode()
    return result


def validate_pair(positive,negative):
    """Pure preparation assertion; not executed or a Native acceptance test."""
    name=STEM+'.kicad_pcb'
    if set(positive)!=set(negative) or any(positive[k]!=negative[k] for k in positive if k!=name):raise ValueError('complete project/rules differ')
    a=sx.parse(positive[name].decode());b=sx.parse(negative[name].decode())
    expected=segment('invalid-inner-through-pad',(14,'11.6'),(24,'11.6'),'In1.Cu','ROUTE','.4')
    if b!=a+[expected]:raise ValueError('negative must add exactly the declared segment')
    pads=[p for fp in sx.children(a,'footprint') for p in sx.children(fp,'pad')]
    if len(pads)!=7 or len([p for p in pads if sx.unquote(p[1])==''])!=1:raise ValueError('exact physical pad census required')
    return {'pad_uuid':PAD_UUID,'intrusion_uuid':INTRUSION_UUID,'numbered_terminals':6,'physical_pads':7,
            'source_pad_preserved':True,'original_project_files_identical':True,'native_executed':False}
