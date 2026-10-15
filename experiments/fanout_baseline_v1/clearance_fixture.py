"""Project-owned roundrect corner control; GPL-3.0-or-later.
Creation only: source freezes before Native; no external CAD or source repair.
"""
from pathlib import Path
import re,uuid
from autorouter import sexpr as sx
from experiments.fanout_baseline_v1 import fixture as base
STEM='owned-roundrect-clearance'
SOURCE_ID='owned-roundrect-clearance-margin-v1'
NS=uuid.UUID('cd4684a1-3bc9-4ea9-a451-46e925cd502b')
UUID=re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')

def uid(label):return str(uuid.uuid5(NS,label))

def files():
    def authored(raw):
        text=raw.decode()
        for old in sorted({base.SOURCE_ID,base.base.SOURCE_ID},key=len,reverse=True):text=text.replace(old,SOURCE_ID)
        text=text.replace(base.STEM,STEM)
        return UUID.sub(lambda m:uid(m.group()),text).encode()
    result={name.replace(base.STEM,STEM):authored(raw) for name,raw in base.files().items()}
    tree=sx.parse(result[STEM+'.kicad_pcb'].decode());targets=[]
    for fp in sx.children(tree,'footprint'):
        if any(sx.unquote(p[1])=='Reference' and sx.unquote(p[2])=='J1' for p in sx.children(fp,'property')):targets.append(fp)
    if len(targets)!=1:raise ValueError('one owned J1 required')
    fp=targets[0];pads=sx.children(fp,'pad')
    if len(pads)!=1 or sx.unquote(pads[0][1])!='1' or sx.unquote(sx.one(pads[0],'net')[1])!='ROUTE':raise ValueError('owned terminal identity changed')
    pad=pads[0];pad[2:4]=['smd','roundrect'];pad[:]=[n for n in pad if not isinstance(n,list) or not n or n[0]!='drill']
    sx.one(pad,'at')[1:]=['0','0','90'];sx.one(pad,'size')[1:]=['1.125','1.75'];sx.one(pad,'layers')[1:]=['"F.Cu"','"F.Paste"','"F.Mask"']
    pad.append(['roundrect_rratio','0.222222']);sx.one(fp,'attr')[1:]=['smd']
    if len(sx.children(tree,'footprint'))!=6 or sum(len(sx.children(f,'pad')) for f in sx.children(tree,'footprint'))!=6:raise ValueError('complete six-terminal source changed')
    result[STEM+'.kicad_pcb']=(sx.dump(tree)+'\n').encode()
    return result


def corner_additions():
    # Owned scalar translation of measured corner geometry. Exact Native
    # clearance is prospective, not established by these authored coordinates.
    def segment(label,a,b,net,width):return ['segment',['start',*a],['end',*b],['width',width],['layer','"F.Cu"'],['net','"'+net+'"'],['uuid','"'+uid(label)+'"']]
    return [segment('corner-close-route',('12','10'),('26','13'),'ROUTE','0.3'),
        segment('corner-gnd-1',('12','24'),('8','24'),'GND','0.2'),
        segment('corner-gnd-2',('8','24'),('8','11.3'),'GND','0.2'),
        segment('corner-gnd-3',('8','11.3'),('11.16095','10.8284'),'GND','0.2'),
        segment('corner-grazing',('11.16095','10.8284'),('11.34505','10.8652'),'GND','0.2')]


def corner_identity(tree):
    fp=next(f for f in sx.children(tree,'footprint') if any(sx.unquote(p[1])=='Reference' and sx.unquote(p[2])=='J1' for p in sx.children(f,'property')))
    return dict(pad_uuid=sx.unquote(sx.one(sx.children(fp,'pad')[0],'uuid')[1]),track_uuid=uid('corner-grazing'),
        center_mm=[12,10],size_mm=[1.125,1.75],pad_rotation_deg=90,roundrect_rratio=.222222,
        required_original_clearance_mm=.2,arithmetic_expected_clearance_mm=.1978488255466144,
        arithmetic_expected_export_polygon_clearance_mm=.20167427682967046,
        arithmetic_scope='Scalar translation only; actual Native report and exported polygon remain authoritative.')
