"""Unexecuted owned four-copper pour recipe, GPL-3.0-or-later.

Derived from the existing owned fixture, not a new family or held-out input.
The baseline factory bytes are never edited. No file I/O or Native calls here.
"""
import copy,json,uuid
from autorouter import sexpr as sx
from experiments.four_copper_class_transport_v1 import fixture
NS=uuid.UUID('9c85a9ad-fb60-5d10-a81e-8b608793f3f8')
def uid(label):return str(uuid.uuid5(NS,label))
def q(value):return json.dumps(value)
def rectangle(x1,y1,x2,y2):
 return ['polygon',['pts',*(['xy',str(x),str(y)] for x,y in ((x1,y1),(x2,y1),(x2,y2),(x1,y2)))]]
def files(variant='explicit_net0'):
 if variant not in ('explicit_net0','explicit_net0_island0','omitted_net_island0'):raise ValueError('fixed recipe variant required')
 result=fixture.files();tree=sx.parse(result[fixture.STEM+'.kicad_pcb'].decode())
 # Complete the otherwise open ROUTE source on In1, preserving locked KEEP.
 for label,a,b,layer in [('front',(12,10),(14,10),'F.Cu'),('inner',(14,10),(24,10),'In1.Cu'),('back',(24,10),(26,10),'B.Cu')]:
  tree.append(['segment',['start',*map(str,a)],['end',*map(str,b)],['width','0.4'],['layer',q(layer)],['net','"ROUTE"'],['uuid',q(uid(label))]])
 for x in (14,24):tree.append(['via',['at',str(x),'10'],['size','1.2'],['drill','0.5'],['layers','"F.Cu"','"B.Cu"'],['net','"ROUTE"'],['uuid',q(uid('via-'+str(x)))]])
 for layer in ('In1.Cu','In2.Cu'):
  tree.append(['zone',['net','"GND"'],['layer',q(layer)],['uuid',q(uid(layer+'-zone'))],['hatch','edge','0.5'],
    ['connect_pads','yes',['clearance','0.3']],['min_thickness','0.25'],['filled_areas_thickness','no'],
    ['fill','yes',['thermal_gap','0.3'],['thermal_bridge_width','0.3']],rectangle(7,21,31,29)])
 area=['zone',['net','0'],['layer','"In2.Cu"'],['uuid',q(uid('pour-area'))],['name','"owned-inner-pour"'],
       ['hatch','edge','0.5'],['connect_pads',['clearance','0']],['min_thickness','0.25'],
       ['keepout',*[[name,'not_allowed' if name=='copperpour' else 'allowed'] for name in ('tracks','vias','pads','copperpour','footprints')]],
       ['placement',['enabled','no'],['sheetname','"/"']],
       ['fill',['thermal_gap','0.5'],['thermal_bridge_width','0.5']],rectangle(18,23,20,25)]
 if variant!='explicit_net0':sx.one(area,'fill').append(['island_removal_mode','0'])
 if variant=='omitted_net_island0':area.remove(sx.one(area,'net'))
 tree.append(area);result[fixture.STEM+'.kicad_pcb']=(sx.dump(tree)+'\n').encode();return result
