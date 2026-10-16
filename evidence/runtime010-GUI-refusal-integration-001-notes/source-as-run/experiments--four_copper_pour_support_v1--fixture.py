"""Owned fixed-placement four-copper routing and pour-area control.

SPDX-License-Identifier: GPL-3.0-or-later
Generated project files carry the repository GPL grant. This exposed diagnostic
derives from forced_inner; it is not an independent benchmark family.
"""
import json
import uuid
from autorouter import sexpr as sx
from experiments.four_copper_class_transport_v1 import forced_inner as base

STEM=base.STEM
NS=uuid.UUID('9c85a9ad-fb60-5d10-a81e-8b608793f3f8')
def uid(label):return str(uuid.uuid5(NS,label))
def rectangle(x1,y1,x2,y2):
    return ['polygon',['pts',*(['xy',str(x),str(y)]for x,y in((x1,y1),(x2,y1),(x2,y2),(x1,y2)))]]

def files():
    """Open ROUTE pair, protected outer curtains and inner GND pours."""
    result=base.files();name=STEM+'.kicad_pcb';tree=sx.parse(result[name].decode())
    for layer in('In1.Cu','In2.Cu'):
        tree.append(['zone',['net','"GND"'],['layer',json.dumps(layer)],['uuid',json.dumps(uid(layer+'-zone'))],
            ['hatch','edge','0.5'],['connect_pads','yes',['clearance','0.3']],['min_thickness','0.25'],
            ['filled_areas_thickness','no'],['fill','yes',['thermal_gap','0.3'],['thermal_bridge_width','0.3']],rectangle(7,21,31,29)])
    tree.append(['zone',['layer','"In2.Cu"'],['uuid',json.dumps(uid('pour-area'))],['name','"owned-inner-pour"'],
        ['hatch','edge','0.5'],['connect_pads',['clearance','0']],['min_thickness','0.25'],
        ['keepout',*[[flag,'not_allowed'if flag=='copperpour'else'allowed']for flag in('tracks','vias','pads','copperpour','footprints')]],
        ['placement',['enabled','no'],['sheetname','"/"']],
        ['fill',['thermal_gap','0.5'],['thermal_bridge_width','0.5'],['island_removal_mode','0']],rectangle(18,23,20,25)])
    result[name]=(sx.dump(tree)+'\n').encode()
    return result
