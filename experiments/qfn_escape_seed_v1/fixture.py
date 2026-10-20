"""Owned escape-initialization controls; no execution or routing claim.

SPDX-License-Identifier: GPL-3.0-or-later
The grant covers this factory and every generated design file. Grammar follows
native_schematic_transport_v1; identities, circuit and geometry are new.
This deliberately roomy 16-pad contact control is not a quality benchmark.
"""
from decimal import Decimal
import json
import uuid
from experiments.native_schematic_transport_v1 import fixture as base

STEM='owned-escape-seed'
NS=uuid.UUID('87785284-49c5-47fc-a635-ad4842708d4a')
CHIP='owned_escape_qfn16'
ANCHOR='owned_escape_anchor'
FIELD='OwnedEscapeIdentity'
PITCH=Decimal('1.6')

def uid(label):return str(uuid.uuid5(NS,label))
def q(text):return json.dumps(text,ensure_ascii=True)
def mm(value):return format(Decimal(str(value)),'f')

def pins():
    result=[]
    for side in range(4):
        for index in range(4):
            tangent=(Decimal(index)-Decimal('1.5'))*PITCH
            x,y,angle,ax,ay=(
                (Decimal('-3.5'),tangent,0,Decimal('-10'),tangent),
                (Decimal('3.5'),tangent,0,Decimal('10'),tangent),
                (tangent,Decimal('-3.5'),90,tangent,Decimal('-10')),
                (tangent,Decimal('3.5'),90,tangent,Decimal('10')))[side]
            number=side*4+index+1
            result.append(dict(number=str(number),net='N'+str(number).zfill(2),
                local=(x,y),angle=angle,anchor=(50+ax,50+ay)))
    return result

def pcb_prop(ref,name,value,layer):
    return ('(property '+q(name)+' '+q(value)+' (at 0 0 0) (layer '+q(layer)+') '
        '(hide yes) (uuid '+q(uid(ref+'-property-'+name))+') '
        '(effects (font (size 1 1) (thickness 0.15))))')

def properties(ref,footprint):
    return (('Reference',ref),('Value',footprint),('Datasheet','~'),
        ('Description','Owned escape contact control'),(FIELD,STEM+':'+ref))

def board():
    # Reuse only the qualified syntax/layer/setup header, not its routes/design.
    header=base.board().decode().split('(footprint ',1)[0]
    rows=[header]
    components=[('U1',CHIP,Decimal(50),Decimal(50))]
    components += [('J'+str(i+1),ANCHOR,*pin['anchor']) for i,pin in enumerate(pins())]
    components += [('J17',ANCHOR,Decimal(40),Decimal(65)),('J18',ANCHOR,Decimal(60),Decimal(65))]
    for ref,footprint,x,y in components:
        rows.append('(footprint '+q(footprint)+' (layer "F.Cu") (uuid '+q(uid(ref+'-footprint'))+') (at '+mm(x)+' '+mm(y)+')')
        for name,value in properties(ref,footprint):rows.append(pcb_prop(ref,name,value,'F.SilkS' if name=='Reference' else 'F.Fab'))
        rows.append('(path '+q('/'+uid(ref+'-symbol'))+') (attr '+('smd' if ref=='U1' else 'through_hole')+')')
        extent='4.2' if ref=='U1' else '0.5'
        rows.append('(fp_rect (start -'+extent+' -'+extent+') (end '+extent+' '+extent+') (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd") (uuid '+q(uid(ref+'-courtyard'))+'))')
        if ref=='U1':
            for pin in pins():
                px,py=pin['local'];n=pin['number']
                rows.append('(pad '+q(n)+' smd roundrect (at '+mm(px)+' '+mm(py)+' '+str(pin['angle'])+') (size 0.8 0.25) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25) (net '+q(pin['net'])+') (pinfunction '+q(n)+') (pintype "passive") (uuid '+q(uid('U1-pad-'+n))+'))')
        else:
            index=int(ref[1:]);net='KEEP' if index>=17 else pins()[index-1]['net']
            rows.append('(pad "1" thru_hole circle (at 0 0) (size 0.8 0.8) (drill 0.3) (layers "*.Cu" "*.Mask") (net '+q(net)+') (pinfunction "1") (pintype "passive") (uuid '+q(uid(ref+'-pad'))+'))')
        rows.append('(embedded_fonts no))')
    rows.append('(gr_rect (start 36 36) (end 64 68) (stroke (width 0.05) (type default)) (fill none) (layer "Edge.Cuts") (uuid '+q(uid('edge'))+'))')
    # Known feasible reference is only a control. The generator never sees it:
    # whole routing_task removes these before any escape proposal is made.
    for pin in pins():
        x,y=pin['local'];ax,ay=pin['anchor']
        rows.append('(segment (start '+mm(50+x)+' '+mm(50+y)+') (end '+mm(ax)+' '+mm(ay)+') (width 0.2) (layer "F.Cu") (net '+q(pin['net'])+') (uuid '+q(uid('reference-'+pin['number']))+'))')
    rows.append('(segment (start 40 65) (end 60 65) (width 0.2) (layer "F.Cu") (net "KEEP") (locked yes) (uuid '+q(uid('protected-keep'))+'))')
    rows.append('(embedded_fonts no))')
    return ('\n'.join(rows)+'\n').encode()

def lib_symbol(lib_id,name,footprint,count):
    rows=['(symbol '+q(lib_id)+' (pin_names (offset 0) hide) (exclude_from_sim no) (in_bom yes) (on_board yes)']
    for key,value in (('Reference','U' if count>1 else 'J'),('Value',footprint),('Footprint',footprint),('Datasheet',''),('Description','Owned escape contact control'),(FIELD,'')):
        rows.append(base.sch_property(key,value))
    rows.append('(symbol '+q(name+'_0_1')+' (rectangle (start -1.27 1.27) (end 1.27 -'+mm(Decimal(count)*Decimal('2.54'))+') (stroke (width 0.254) (type default)) (fill (type background))))')
    rows.append('(symbol '+q(name+'_1_1'))
    for index in range(count):
        number=str(index+1);y=-Decimal(index)*Decimal('2.54')
        rows.append('(pin passive line (at -2.54 '+mm(y)+' 0) (length 1.27) (name '+q(number)+' (effects (font (size 1.27 1.27)))) (number '+q(number)+' (effects (font (size 1.27 1.27)))))')
    rows.append('))');return '\n'.join(rows)

def schematic():
    rows=['(kicad_sch (version 20250114) (generator "eeschema") (generator_version "10.0") (uuid '+q(uid('schematic-root'))+') (paper "A4") (lib_symbols',lib_symbol('OwnedEscape:Chip16','Chip16',CHIP,16),lib_symbol('OwnedEscape:Anchor','Anchor',ANCHOR,1),')']
    components=[('U1',CHIP,'OwnedEscape:Chip16',Decimal('40.64'),Decimal('30.48'),[(p['number'],p['net']) for p in pins()])]
    components += [('J'+str(i+1),ANCHOR,'OwnedEscape:Anchor',Decimal('101.6'),Decimal('30.48')+Decimal(i)*Decimal('2.54'),[('1',p['net'])]) for i,p in enumerate(pins())]
    components += [(ref,ANCHOR,'OwnedEscape:Anchor',x,Decimal('83.82'),[('1','KEEP')]) for ref,x in (('J17',Decimal('40.64')),('J18',Decimal('101.6')))]
    for ref,footprint,lib_id,x,y,connections in components:
        for index,(number,net) in enumerate(connections):
            rows.append('(global_label '+q(net)+' (shape input) (at '+mm(x-Decimal('2.54'))+' '+mm(y+Decimal(index)*Decimal('2.54'))+' 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid '+q(uid(ref+'-label-'+number))+'))')
        rows.append('(symbol (lib_id '+q(lib_id)+') (at '+mm(x)+' '+mm(y)+' 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid '+q(uid(ref+'-symbol'))+')')
        for key,value in properties(ref,footprint):
            rows.append(base.sch_property(key,'' if key=='Datasheet' else value,mm(x),mm(y),hidden=key not in ('Reference','Value')))
        rows.append(base.sch_property('Footprint',footprint,mm(x),mm(y)))
        for number,_ in connections:rows.append('(pin '+q(number)+' (uuid '+q(uid(ref+'-schematic-pin-'+number))+'))')
        rows.append('(instances (project '+q(STEM)+' (path '+q('/'+uid('schematic-root'))+' (reference '+q(ref)+') (unit 1)))))')
    rows.append('(embedded_fonts no))');return ('\n'.join(rows)+'\n').encode()

def files():
    project=json.loads(base.project());project['meta']['filename']=STEM+'.kicad_pro'
    project['board']['design_settings']['rules']['min_track_width']=0.2
    project['board']['design_settings']['rules']['min_connection']=0.2
    project['net_settings']['classes'][0].update(track_width=0.2,clearance=0.2,via_diameter=0.6,via_drill=0.3)
    local=json.loads(base.files()[base.STEM+'.kicad_prl']);local['meta']['filename']=STEM+'.kicad_prl'
    return {STEM+'.kicad_pcb':board(),STEM+'.kicad_sch':schematic(),STEM+'.kicad_pro':(json.dumps(project,sort_keys=True,indent=2)+'\n').encode(),STEM+'.kicad_prl':(json.dumps(local,sort_keys=True,indent=2)+'\n').encode()}
