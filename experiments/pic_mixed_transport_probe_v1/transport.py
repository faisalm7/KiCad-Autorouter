"""Pure two-body representation observation. Original rules/routes are retained."""
import copy
import math
from decimal import Decimal
import hashlib
import json
from autorouter import sexpr as sx
from autorouter.adapter import _parse_dsn,_dump_dsn,_check_units
from experiments.pic_custom_observer_v1 import mapping
from experiments.custom_pad_area_probe_v1 import derive as old

def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical_ring(points):return old.canonical_ring(points)

def placed_pins(tree):
    """Exact pin centers for this retained DSN's orthogonal placement scope."""
    images=sx.children(sx.one(tree,'library'),'image')
    image_map={sx.unquote(x[1]):x for x in images}
    if len(image_map)!=len(images):raise ValueError('duplicate DSN image')
    def integer(atom):
        value=Decimal(atom)
        if not value.is_finite() or value!=value.to_integral_value() or abs(value)>10**8:raise ValueError('integer DSN placement required')
        return int(value)
    pins={};references=set()
    for component in sx.children(sx.one(tree,'placement'),'component'):
        image=image_map.get(sx.unquote(component[1]))
        if image is None:raise ValueError('unknown placed image')
        for place in sx.children(component,'place'):
            atoms=[a for a in place[1:] if isinstance(a,str)]
            if len(atoms)!=5:raise ValueError('unqualified DSN placement')
            ref=sx.unquote(atoms[0]);x,y=map(integer,atoms[1:3]);side=atoms[3];angle=integer(atoms[4])
            # Back 180 is the sole original case. Mirror/rotation ordering agrees
            # for 180; arbitrary reflection or approximate rotation is not admitted.
            if (side=='front' and angle not in (-90,0,90,180)) or (side=='back' and angle!=180) or side not in ('front','back'):
                raise ValueError('unqualified DSN placement transform')
            if ref in references:raise ValueError('duplicate placed reference')
            references.add(ref)
            for pin in sx.children(image,'pin'):
                values=[a for a in pin[2:] if isinstance(a,str)];rotation=sx.children(pin,'rotate')
                if len(values)!=3 or len(rotation)>1 or any(c[0]!='rotate' for c in pin if isinstance(c,list)):
                    raise ValueError('unqualified DSN pin declaration')
                if rotation and (len(rotation[0])!=2 or integer(rotation[0][1])%90):raise ValueError('unqualified pin shape rotation')
                number=sx.unquote(values[0]);dx,dy=map(integer,values[1:])
                if side=='back':dx=-dx
                for _ in range((angle//90)%4):dx,dy=-dy,dx
                key=(ref,number)
                if key in pins:raise ValueError('duplicate placed DSN pin')
                pins[key]={'reference':ref,'number':number,'nets':[],'position_um':[x+dx,y+dy]}
    tokens={ref+'-'+number:key for key in pins for ref,number in [key]}
    if len(tokens)!=len(pins):raise ValueError('ambiguous DSN pin token')
    assigned=set()
    for net in sx.children(sx.one(tree,'network'),'net'):
        node=sx.one(net,'pins')
        if node is None:raise ValueError('missing DSN net pins')
        for atom in node[1:]:
            token=sx.unquote(atom)
            if token not in tokens or token in assigned:raise ValueError('unknown/duplicate DSN net pin')
            assigned.add(token);pins[tokens[token]]['nets']=[sx.unquote(net[1])]
    return [pins[key] for key in sorted(pins)]

def derive(raw,context,observation,notes):
    custom=mapping.custom_identity(observation,context,notes)
    correspondence=mapping.dsn_correspondence(raw,context,custom)
    original=_parse_dsn(raw.decode());_check_units(original);tree=copy.deepcopy(original)
    dsn_pins=placed_pins(original)
    terminals={(p['reference'],p['number']):p for p in context['pads'] if p['netcode']>0 and p['copper_layers']}
    assigned={(p['reference'],p['number']):p for p in dsn_pins if p['nets']}
    if len(dsn_pins)!=240 or len(assigned)!=236 or set(assigned)!=set(terminals):raise ValueError('original placed/assigned DSN census differs')
    for key,pin in assigned.items():
        if pin['nets']!=[terminals[key]['net']] or pin['position_um']!=old.coord(terminals[key]['position_nm']):raise ValueError('DSN placement differs from native connected terminal')
    library=sx.one(tree,'library');wiring=sx.one(tree,'wiring');structure=sx.one(tree,'structure')
    layers=[sx.unquote(x[1]) for x in sx.children(structure,'layer')]
    if layers!=['top_layer','bottom_layer']: # Exact pinned native exporter order.
        raise ValueError('original DSN physical layers differ')
    stacks={sx.unquote(x[1]):x for x in sx.children(library,'padstack')}
    if len(stacks)!=len(sx.children(library,'padstack')):raise ValueError('duplicate original padstack')
    names={name:old.imported_name(name) for name in stacks}
    if len(set(names.values()))!=len(names):raise ValueError('noninjective imported padstack spelling')
    rows=[];restores=[]
    by_uuid={r['uuid']:r for r in custom}
    for identity in correspondence['custom_pads']:
        row=by_uuid[identity['uuid']];stack=stacks[sx.unquote(identity['padstack_ast'][1])]
        if stack!=identity['padstack_ast']:raise ValueError('custom stack identity differs')
        # Only the exact custom stack bodies change. All placements and pin offsets remain byte-semantic equal.
        if row['copper_layers']!=['B.Cu'] or row['size_nm']!=[300000,300000]:raise ValueError('unqualified original custom anchor/layer')
        shapes=sx.children(stack,'shape')
        if len(shapes)!=1:raise ValueError('single original custom shape required')
        old_shape=copy.deepcopy(shapes[0]);layer=sx.unquote(shapes[0][1][1])
        if layer!='top_layer':raise ValueError('custom stack actual layer differs')
        shapes[0][:]=['shape',['rect',layer,'-150','-150','150','150']]
        poly=row['effective_world'];outline=poly['outlines'][0]
        if poly['arc_count']!=0 or len(poly['outlines'])!=1 or outline['holes']:raise ValueError('unqualified native area topology')
        ring=[old.coord(point) for point in outline['outline']['points_nm']]
        if ring[0]==ring[-1]:ring=ring[:-1]
        if len(ring)!=5 or old.area(ring)<=0:raise ValueError('unqualified native five-vertex area')
        body=['wire',['polygon','bottom_layer','0',*[str(v) for point in ring for v in point]],['net',json.dumps(row['net'])],['type','protect']]
        wiring.append(body);restores.append((stack,shapes[0],old_shape,body))
        rows.append({'uuid':row['uuid'],'reference':row['reference'],'number':row['number'],'net':row['net'],
            'padstack_name':names[sx.unquote(stack[1])],'original_padstack_name':sx.unquote(stack[1]),'layer':'bottom_layer',
            'position_um':old.coord(row['position_nm']),'ring_um':ring,'area_um2':old.area(ring),
            'native_class':next(n['class'] for n in context['nets'] if n['name']==row['net'])})
    result=_dump_dsn(tree).encode()
    # Reverse proof includes all original routes, planes, rules, images, pins and layers.
    for stack,shape,old_shape,body in restores:shape[:]=old_shape;wiring.remove(body)
    if tree!=original:raise ValueError('unexpected derived original AST mutation')
    expected={'schema':1,'source_dsn_sha256':sha(raw),'derived_dsn_sha256':sha(result),'areas':rows,
        'name_map':names,'terminal_count':correspondence['terminal_count'],'layer_order':layers,
        'dsn_pins':dsn_pins,'dsn_pin_count':len(dsn_pins),'dsn_unassigned_pin_count':len(dsn_pins)-len(assigned),
        'native_pad_count':len(context['pads']),
        'terminals':[{'reference':p['reference'],'number':p['number'],'net':p['net'],'position_um':old.coord(p['position_nm'])}
            for p in context['pads'] if p['netcode']>0 and p['copper_layers']],
        'nets':{n['name']:{'class':'kicad_default' if n['class']=='Default' else n['class'],
            'width_um':n['width_nm']/1000,'clearance_um':n['clearance_nm']/1000} for n in context['nets']},
        'unchanged_original_wire_count':len(sx.children(sx.one(original,'wiring'),'wire')),
        'unchanged_original_via_count':len(sx.children(sx.one(original,'wiring'),'via')),
        'unchanged_original_plane_count':len(sx.children(sx.one(original,'structure'),'plane')),
        'routing_accepted':False,'mixed_clearance_equivalence_qualified':False}
    return result,expected

def validate(observed,expected):
    if (type(observed.get('schema')) is not int or observed['schema']!=1 or observed.get('routing_executed') is not False
            or observed.get('ses_executed') is not False or len(observed.get('cases',[]))!=2):
        raise ValueError('mixed observation schema/cases differ')
    comparisons=[]
    for setting,row in zip((False,True),observed['cases']):
        if row.get('requested_obstacle') is not setting or row.get('input_sha256')!=expected['derived_dsn_sha256']:
            raise ValueError('case input/settings differ')
        if row.get('status')!='observed':comparisons.append({'observed':False,'error':row.get('error')});continue
        if row.get('post_load_awaited') is not True:raise ValueError('post-load completion must be explicitly observed')
        state=row['state'];nets={n['name']:n for n in state['nets']}
        if set(nets)!=set(expected['nets']) or len(nets)!=len(state['nets']):raise ValueError('engine original net inventory differs')
        for name,want in expected['nets'].items():
            if nets[name]['class']!=want['class'] or nets[name]['width_um']!=[want['width_um']]*2:raise ValueError('engine original class/width differs')
        if row['settings_before']['plane_as_obstacle'] is not setting or row['settings_after']['plane_as_obstacle'] is not setting:
            raise ValueError('effective lifecycle setting differs')
        if any(row[phase].get(flag) is not False for phase in ('settings_before','settings_after') for flag in ('router_enabled','optimizer_enabled')):
            raise ValueError('routing must remain disabled')
        if state['layers']!=expected['layer_order']:raise ValueError('engine layer order differs')
        scale=state['board_units_per_um']
        if type(scale) not in (int,float) or not math.isfinite(scale) or scale<=0:raise ValueError('engine coordinate scale differs')
        pins={(p['reference'],p['number']):p for p in state['pins']}
        if len(pins)!=len(state['pins']):raise ValueError('duplicate engine pin identity')
        placed={(p['reference'],p['number']):p for p in expected['dsn_pins']}
        if (set(pins)!=set(placed) or type(state['census'].get('pins')) is not int or state['census']['pins']!=len(placed)
                or len(placed)!=expected['dsn_pin_count']):raise ValueError('complete placed DSN pin census differs')
        for key,pin in pins.items():
            if pin['nets']!=placed[key]['nets'] or pin['position_um']!=placed[key]['position_um']:raise ValueError('placed DSN pin net/position differs')
        assigned={key:p for key,p in pins.items() if p['nets']}
        terminals={(p['reference'],p['number']):p for p in expected['terminals']}
        if set(assigned)!=set(terminals):raise ValueError('all original connected terminals must survive')
        for key,p in assigned.items():
            if p['nets']!=[terminals[key]['net']] or p['position_um']!=terminals[key]['position_um']:raise ValueError('original terminal net/position differs')
        classes=state['clearance_class_names'];matrix={}
        if not 1<=len(classes)<=32 or len(set(classes))!=len(classes):raise ValueError('matrix class identity differs')
        for cell in state['matrix']:
            key=tuple(cell[k] for k in ('a','b','layer'))
            if any(type(x) is not int for x in key) or key in matrix:raise ValueError('duplicate/illtyped matrix entry')
            for field in ('raw_um','compensated_um','raw_board_units','compensated_board_units'):
                if type(cell[field]) not in (int,float) or not math.isfinite(cell[field]) or cell[field]<0:raise ValueError('invalid clearance matrix value')
            if cell['raw_board_units']/scale!=cell['raw_um'] or cell['compensated_board_units']/scale!=cell['compensated_um']:raise ValueError('clearance scale readback differs')
            matrix[key]=cell
        if set(matrix)!={(a,b,l) for a in range(len(classes)) for b in range(len(classes)) for l in (0,1)}:raise ValueError('complete raw/compensated matrix required')
        matched=[]
        for want in expected['areas']:
            pin=pins.get((want['reference'],want['number']))
            if pin is None or pin['padstack_name']!=want['padstack_name'] or pin['nets']!=[want['net']] or pin['position_um']!=want['position_um']:
                raise ValueError('original anchor identity/net/position differs')
            areas=[a for a in state['areas'] if a['nets']==[want['net']] and a['layer']==want['layer'] and canonical_ring(a['ring_um'])==canonical_ring(want['ring_um'])]
            if len(areas)!=1:raise ValueError('exact native synthetic body not found uniquely')
            area=areas[0]
            if area['obstacle'] is not setting or area['fixed']!='USER_FIXED' or area['holes']!=0:raise ValueError('real manager body activation/fixed state differs')
            if any(p is None for p in area['ring_board_integer']):raise ValueError('exact integer body representation unobserved')
            origin=state['board_origin_dsn_um']
            exact=[[p[0]/scale+origin[0],p[1]/scale+origin[1]] for p in area['ring_board_integer']]
            if canonical_ring(exact)!=canonical_ring(want['ring_um']):raise ValueError('exact integer body coordinates differ')
            layer=expected['layer_order'].index(want['layer']);clearances=[]
            for name,n in nets.items():
                if n['class'] not in ('kicad_default','POWER'):raise ValueError('unexpected imported original class')
                if any(x['class']==n['class'] for x in clearances):continue
                cell=matrix[(area['clearance_class_index'],n['trace_clearance_class'],layer)]
                clearances.append({'class':n['class'],'area_to_trace_raw_um':cell['raw_um'],'compensated_um':cell['compensated_um'],
                    'pin_to_trace_raw_um':matrix[(pin['clearance_class_index'],n['trace_clearance_class'],layer)]['raw_um']})
            matched.append({'pad_uuid':want['uuid'],'pin_id':pin['id'],'area_id':area['id'],
                'pin_class':pin['clearance_class_index'],'area_class':area['clearance_class_index'],
                'own_normal_contacts_reciprocal':area['id'] in pin['contacts'] and pin['id'] in area['contacts'],
                'trace_class_clearances':clearances,'clearance_equivalence_qualified':False})
        comparisons.append({'observed':True,'obstacle_setting':setting,'bodies':matched,
            'interpretation':'Class/matrix observation only; original plane and retained routes remain; no solver/SES or rule-equivalence qualification.'})
    return comparisons
