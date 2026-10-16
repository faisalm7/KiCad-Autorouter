"""Owned seven-pad DSN/source/Native geometry check; no engine acceptance.

SPDX-License-Identifier: GPL-3.0-or-later
Fourth argument is caller-bound immutable positive source board bytes. Only
the exact round, unrotated owned fixture is supported. Back J2 uses retained
exporter top-view transformation: image F.Cu, placement back/180 degrees.
"""
from decimal import Decimal
from autorouter import sexpr as sx
from autorouter.adapter import _parse_dsn,_check_units
from experiments.pic_custom_observer_v1.mapping import dsn_correspondence
LAYERS=('F.Cu','In1.Cu','In2.Cu','B.Cu')
OWNED={'J1':(12,10,'ROUTE'),'J2':(26,10,'ROUTE'),'J3':(12,16,'KEEP'),
       'J4':(26,16,'KEEP'),'J5':(12,24,'GND'),'J6':(26,24,'GND')}
def number(atom):
    value=Decimal(atom)
    if not value.is_finite() or abs(value)>1000000:raise ValueError('bounded finite DSN number required')
    return value

def one(nodes,key,label):
    rows=sx.children(nodes,key)
    if len(rows)!=1:raise ValueError('unique '+label+' required')
    return rows[0]

def source_context(raw):
    if not isinstance(raw,bytes) or len(raw)>1024*1024:raise ValueError('bounded source required')
    tree=sx.parse(raw.decode());result={};seen=set();fps={}
    for fp in sx.children(tree,'footprint'):
        props={}
        for prop in sx.children(fp,'property'):
            key=sx.unquote(prop[1])
            if key in props:raise ValueError('duplicate source property')
            props[key]=sx.unquote(prop[2])
        ref=props['Reference']
        if ref not in OWNED or ref in fps:raise ValueError('owned source footprints differ')
        x,y,net=OWNED[ref];at=one(fp,'at','source footprint position')
        if len(at)not in (3,4) or list(map(number,at[1:3]))!=[x,y] or (len(at)==4 and number(at[3])!=0):raise ValueError('owned source placement differs')
        side='back' if ref=='J2' else 'front';layer='B.Cu' if ref=='J2' else 'F.Cu'
        if one(fp,'layer','source footprint layer')!=['layer','"'+layer+'"']:raise ValueError('owned source side differs')
        fpuid=sx.unquote(one(fp,'uuid','source footprint UUID')[1])
        if fpuid in seen:raise ValueError('duplicate source UUID')
        seen.add(fpuid);fps[ref]={'position_um':[x*1000,-y*1000],'side':side,
                                  'rotation':180 if side=='back' else 0,'value':props['Value']}
        local_numbers=set()
        for pad in sx.children(fp,'pad'):
            name=sx.unquote(pad[1]);blank=name==''
            if name in local_numbers or name not in ({'1',''} if ref=='J3' else {'1'}):raise ValueError('owned source pad census differs')
            local_numbers.add(name);uid=sx.unquote(one(pad,'uuid','source pad UUID')[1])
            if uid in seen:raise ValueError('duplicate source UUID')
            seen.add(uid)
            local=[7,-6] if blank else [0,0];size=4 if blank else 2
            pth=ref not in ('J1','J2');drill=2 if blank else Decimal('.8') if pth else 0
            if pad[2:4]!=['thru_hole' if pth else 'smd','circle']:raise ValueError('owned source pad type differs')
            pa=one(pad,'at','source pad position')
            if len(pa)not in (3,4) or list(map(number,pa[1:3]))!=local or (len(pa)==4 and number(pa[3])!=0):raise ValueError('owned source local position differs')
            if list(map(number,one(pad,'size','source size')[1:]))!=[size,size] or sx.children(pad,'offset'):raise ValueError('owned source size/offset differs')
            drills=sx.children(pad,'drill')
            if drills!=([['drill','2' if blank else '0.8']] if pth else []):raise ValueError('owned source drill differs')
            actual_layers=[sx.unquote(v) for v in one(pad,'layers','source pad layers')[1:]]
            wanted=['*.Cu','*.Mask'] if pth else [layer,layer.replace('Cu','Paste'),layer.replace('Cu','Mask')]
            if actual_layers!=wanted:raise ValueError('owned source pad layers differ')
            nets=sx.children(pad,'net')
            if (blank and nets) or (not blank and (len(nets)!=1 or nets[0]!=['net','"'+net+'"'])):raise ValueError('owned source pad net differs')
            if blank and one(pad,'remove_unused_layers','source layer preservation')!=['remove_unused_layers','no']:raise ValueError('unused copper may be removed')
            physical=list(LAYERS) if pth else [layer]
            result[uid]={'uuid':uid,'footprint_uuid':fpuid,'reference':ref,'number':name,
                'net':'' if blank else net,'position_nm':[(x+local[0])*1000000,(y+local[1])*1000000],
                'fp_relative_position_nm':[v*1000000 for v in local],
                'is_pth':pth,'drill_nm':[int(drill*1000000)]*2,'copper_layers':physical,
                'size_nm':[size*1000000]*2,'local_um':[local[0]*1000,-local[1]*1000],
                'image_layers':list(LAYERS) if pth else ['F.Cu']}
        if local_numbers!=({'1',''} if ref=='J3' else {'1'}):raise ValueError('missing owned source pad')
    if set(fps)!=set(OWNED) or len(result)!=7:raise ValueError('complete owned source required')
    return result,fps

def check(raw,observed,expected_uuid,source_raw):
    if not isinstance(raw,bytes) or len(raw)>4*1024*1024:raise ValueError('bounded raw DSN required')
    source,fps=source_context(source_raw);rows=observed['pads'];native={}
    if len(rows)!=7:raise ValueError('owned Native pad census differs')
    for row in rows:
        uid=row['uuid']
        if uid in native or uid not in source:raise ValueError('Native/source identity differs')
        native[uid]=row;want=source[uid]
        for key in ('uuid','footprint_uuid','reference','number','net','position_nm','fp_relative_position_nm','is_pth','drill_nm','copper_layers'):
            if row[key]!=want[key]:raise ValueError('Native/source '+key+' differs')
        if type(row['netcode'])is not int or (row['netcode']!=0 if want['number']=='' else row['netcode']<=0):raise ValueError('Native netcode differs')
        if len(row['shapes'])!=len(want['copper_layers']):raise ValueError('Native copper shape count differs')
        for shape,layer in zip(row['shapes'],want['copper_layers']):
            if shape.get('layer')!=layer or shape.get('circle')is not True or shape.get('size_nm')!=want['size_nm'] or shape.get('offset_nm')!=[0,0]:raise ValueError('Native/source copper shape differs')
    if expected_uuid not in source or source[expected_uuid]['number']!='':raise ValueError('unassigned UUID differs')
    connected=dsn_correspondence(raw,{'pads':rows},[])
    if connected['terminal_count']!=6:raise ValueError('numbered terminal census differs')
    tree=_parse_dsn(raw.decode());_check_units(tree)
    structure=one(tree,'structure','DSN structure')
    if [sx.unquote(n[1]) for n in sx.children(structure,'layer')]!=list(LAYERS):raise ValueError('exact four DSN layers required')
    library=one(tree,'library','DSN library');placement=one(tree,'placement','DSN placement');network=one(tree,'network','DSN network')
    def keyed(nodes,label):
        result={}
        for node in nodes:
            name=sx.unquote(node[1])
            if name in result:raise ValueError('duplicate '+label)
            result[name]=node
        return result
    images=keyed(sx.children(library,'image'),'DSN image');stacks=keyed(sx.children(library,'padstack'),'DSN padstack')
    netrows=keyed(sx.children(network,'net'),'DSN net')
    if set(netrows)!={'ROUTE','KEEP','GND'}:raise ValueError('owned DSN net census differs')
    placed={};checked=[]
    for comp in sx.children(placement,'component'):
        image=images[sx.unquote(comp[1])]
        for place in sx.children(comp,'place'):
            ref=sx.unquote(place[1])
            if ref not in fps or ref in placed:raise ValueError('owned DSN placements differ')
            want=fps[ref];placed[ref]=place
            if (len(place)!=7 or list(map(number,place[2:4]))!=want['position_um'] or place[4]!=want['side']
                    or number(place[5])!=want['rotation'] or place[6]!=['PN',want['value']]):raise ValueError('owned DSN placement geometry differs')
            pins={}
            for pin in sx.children(image,'pin'):
                atoms=[v for v in pin[2:] if isinstance(v,str)];extra=[v for v in pin[2:] if isinstance(v,list)]
                if len(atoms)!=3 or len(extra)>1 or any(v[0]!='rotate' or len(v)!=2 or number(v[1])!=0 for v in extra):raise ValueError('unqualified pin transform')
                name=sx.unquote(atoms[0])
                if name in pins:raise ValueError('duplicate image pin')
                pins[name]=(pin,atoms)
            if set(pins)!=({'1','@1'} if ref=='J3' else {'1'}):raise ValueError('complete physical image pin census differs')
            for uid,row in source.items():
                if row['reference']!=ref:continue
                name=row['number'] or '@1';pin,atoms=pins[name]
                if list(map(number,atoms[1:]))!=row['local_um']:raise ValueError('DSN/source local pin position differs')
                stack=stacks[sx.unquote(pin[1])];seen=[]
                for shape in sx.children(stack,'shape'):
                    if len(shape)!=2 or not isinstance(shape[1],list):raise ValueError('one circle per shape required')
                    circle=shape[1]
                    if len(circle)not in (3,5) or circle[0]!='circle' or number(circle[2])!=Decimal(row['size_nm'][0])/1000:raise ValueError('DSN/source copper diameter differs')
                    if len(circle)==5 and list(map(number,circle[3:]))!=[0,0]:raise ValueError('DSN/source copper offset differs')
                    seen.append(sx.unquote(circle[1]))
                if sorted(seen)!=sorted(row['image_layers']):raise ValueError('DSN/source physical copper layers differ')
                checked.append({'uuid':uid,'reference':ref,'number':row['number'],'pin_ast':pin,'padstack_ast':stack,'placement_ast':place})
    if set(placed)!=set(fps) or len(checked)!=7:raise ValueError('DSN seven-pad geometry incomplete')
    return {'numbered_terminal_count':6,'physical_pad_count':7,'unassigned_pin':'J3-@1','native_pad_uuid':expected_uuid,
            'checked_pads':checked,'representation_observed':True,'engine_obstacle_behavior_qualified':False,'routing_accepted':False}
