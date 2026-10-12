"""Strict retained-route SES diagnostic. No production acceptance or tolerance widening."""
import copy
import hashlib
import re
from collections import Counter
from decimal import Decimal
from autorouter import sexpr as sx, pipeline as p
from autorouter.adapter import _parse_dsn
from experiments.custom_pad_area_probe_v1.derive import imported_name, canonical_ring

MAX_SES=4*1024**2

def number(value):
    n=Decimal(str(value))
    if not n.is_finite() or abs(n)>10**9:raise ValueError('bounded finite coordinate required')
    return n

def children_only(node,keys,atoms):
    if len([x for x in node if isinstance(x,str)])!=atoms or any(not isinstance(x,(str,list)) or isinstance(x,list) and (not x or x[0] not in keys) for x in node):
        raise ValueError('unexpected '+str(node[0])+' fields')

def pairs(values,scale=1):
    if len(values)<4 or len(values)%2:raise ValueError('coordinate pairs required')
    return [tuple(number(x)/scale for x in values[i:i+2]) for i in range(0,len(values),2)]

def segments(net,layer,width,points):
    width=number(width)
    if width<=0 or layer not in ('top_layer','bottom_layer'):raise ValueError('route width/layer differs')
    result=[]
    for a,b in zip(points,points[1:]):
        if a==b:raise ValueError('zero route segment')
        result.append((net,layer,width,*sorted((tuple(a),tuple(b)))))
    return result

def diff(expected,actual):
    def rows(v):return [{'geometry':str(k),'count':c} for k,c in sorted(v.items(),key=lambda x:str(x[0]))]
    return {'equal':expected==actual,'expected_segments':sum(expected.values()),'actual_segments':sum(actual.values()),
        'missing':rows(expected-actual),'extra':rows(actual-expected)}

def placements(node,scale,dsn=False):
    result={}
    for component in sx.children(node,'component'):
        children_only(component,{'place'},2)
        package=sx.unquote(component[1])
        if dsn:
            # Pinned Library.readScope normalizes package labels before deduplication.
            # Actual all-pin/ref checks and native immutable footprint checks remain required.
            package=re.sub(r'::[0-9]+$', '', package)
        for place in sx.children(component,'place'):
            children_only(place,{'PN'} if dsn else set(),6)
            ref=sx.unquote(place[1])
            if ref in result:raise ValueError('duplicate SES placement')
            if place[4] not in ('front','back'):raise ValueError('unknown placement side')
            result[ref]=(package,number(place[2])/scale,number(place[3])/scale,place[4],(number(place[5])%360+360)%360)
    return result

def library(node,scale):
    result={}
    for stack in sx.children(node,'padstack'):
        children_only(stack,{'shape','attach'},2)
        name=imported_name(sx.unquote(stack[1]));shapes={}
        if name in result:raise ValueError('duplicate SES via stack')
        for shape in sx.children(stack,'shape'):
            if len(shape)!=2 or not isinstance(shape[1],list):raise ValueError('unknown via shape')
            c=shape[1]
            if c[0]!='circle' or len(c) not in (3,5):raise ValueError('only exact circular via stacks supported')
            layer=sx.unquote(c[1])
            if layer in shapes or layer not in ('top_layer','bottom_layer'):raise ValueError('duplicate/unknown via layer')
            center=tuple(number(x)/scale for x in c[3:]) if len(c)==5 else (Decimal(0),Decimal(0))
            shapes[layer]=(number(c[2])/scale,center)
        if set(shapes)!= {'top_layer','bottom_layer'} or sx.one(stack,'attach')!=['attach','off']:raise ValueError('via stack span/attach differs')
        result[name]=shapes
    return result

def source_routes(board):
    result=Counter();vias=Counter();layers={'F.Cu':'top_layer','B.Cu':'bottom_layer'}
    names={n[1]:sx.unquote(n[2]) for n in sx.children(board,'net')}
    for route in p.routes(board):
        net=sx.one(route,'net');net=names.get(net[1],sx.unquote(net[1]))
        if route[0]=='segment':
            points=[tuple(number(x)*1000*(-1 if i else 1) for i,x in enumerate(sx.one(route,k)[1:])) for k in ('start','end')]
            result.update(segments(net,layers[sx.unquote(sx.one(route,'layer')[1])],number(sx.one(route,'width')[1])*1000,points))
        elif route[0]=='via':
            if p.locked(route) or sx.one(route,'layers')!=['layers','"F.Cu"','"B.Cu"']:raise ValueError('unqualified retained via')
            xy=tuple(number(x)*1000*(-1 if i else 1) for i,x in enumerate(sx.one(route,'at')[1:]))
            vias[(net,xy,number(sx.one(route,'size')[1])*1000,number(sx.one(route,'drill')[1])*1000)]+=1
        else:raise ValueError('retained arcs outside exact-survival scope')
    return result,vias

def audit(raw,dsn_raw,expected,source,geometry=None,*,generated=False):
    if not raw or len(raw)>MAX_SES:raise ValueError('SES byte bound')
    tree=sx.parse(raw.decode());dsn=_parse_dsn(dsn_raw.decode())
    children_only(tree,{'base_design','placement','was_is','routes'},2)
    if tree[:2]!=['session','"original-mixed.ses"'] or sx.one(tree,'base_design')!=['base_design','"original-mixed.dsn"']:
        raise ValueError('SES design identity differs')
    if sx.one(tree,'was_is')!=['was_is']:raise ValueError('pin swapping unsupported')
    place=sx.one(tree,'placement');routes=sx.one(tree,'routes')
    children_only(place,{'resolution','component'},1);children_only(routes,{'resolution','parser','library_out','network_out'},1)
    resolution=['resolution','um','10']
    if sx.one(place,'resolution')!=resolution or sx.one(routes,'resolution')!=resolution or sx.one(dsn,'resolution')!=resolution:
        raise ValueError('exact SES resolution required')
    scale=Decimal(10)
    if placements(place,scale)!=placements(sx.one(dsn,'placement'),1,True):raise ValueError('SES placement differs')
    parser=sx.one(routes,'parser');children_only(parser,{'host_cad','host_version'},1)
    if sx.one(parser,'host_cad')!=['host_cad','"KiCad\'s Pcbnew"'] or sx.one(parser,'host_version')!=['host_version','"10.0.0"']:raise ValueError('SES host identity differs')
    lib=sx.one(routes,'library_out');children_only(lib,{'padstack'},1)
    stacks=library(lib,scale)
    wiring=sx.one(dsn,'wiring');dsn_paths=Counter();dsn_vias=Counter();needed=set()
    for wire in sx.children(wiring,'wire'):
        path=sx.one(wire,'path')
        if path:dsn_paths.update(segments(sx.unquote(sx.one(wire,'net')[1]),sx.unquote(path[1]),number(path[2]),pairs(path[3:])))
    for via in sx.children(wiring,'via'):
        name=imported_name(sx.unquote(via[1]));needed.add(name)
        dsn_vias[(sx.unquote(sx.one(via,'net')[1]),name,tuple(number(x) for x in via[2:4]))]+=1
    if generated:
        if dsn_paths or dsn_vias or p.routes(source) or geometry is None:raise ValueError('generated mode requires empty seed and final geometry')
        needed=set(stacks)
    wanted_library=['library_out',*[copy.deepcopy(n) for n in sx.children(sx.one(dsn,'library'),'padstack') if imported_name(sx.unquote(n[1])) in needed]]
    if stacks!=library(wanted_library,1):raise ValueError('SES via library differs')
    network=sx.one(routes,'network_out');children_only(network,{'net'},1)
    nets=set();paths=Counter();vias=Counter();polygons=[];path_count=0
    for node in sx.children(network,'net'):
        children_only(node,{'wire','via'},2);net=sx.unquote(node[1])
        if net in nets or net not in expected['nets']:raise ValueError('duplicate/unknown SES net')
        nets.add(net)
        for wire in sx.children(node,'wire'):
            children_only(wire,{'path','polygon','type'},1)
            path=sx.one(wire,'path');polygon=sx.one(wire,'polygon')
            if bool(path)==bool(polygon):raise ValueError('one known wire shape required')
            if sx.one(wire,'type') not in (None,['type','protect']):raise ValueError('unexpected wire protection')
            if path:
                paths.update(segments(net,sx.unquote(path[1]),number(path[2])/scale,pairs(path[3:],scale)));path_count+=1
            else:
                if polygon[2]!='0':raise ValueError('polygon aperture differs')
                polygons.append((net,sx.unquote(polygon[1]),canonical_ring(pairs(polygon[3:],scale))))
        for via in sx.children(node,'via'):
            children_only(via,{'type'},4)
            if sx.one(via,'type') not in (None,['type','protect']):raise ValueError('unexpected via protection')
            name=imported_name(sx.unquote(via[1]))
            if name not in stacks:raise ValueError('unknown via stack')
            vias[(net,name,tuple(number(x)/scale for x in via[2:4]))]+=1
    want=[(a['net'],a['layer'],canonical_ring(a['ring_um'])) for a in expected['areas']]
    if Counter(polygons)!=Counter(want) or len(polygons)!=2:raise ValueError('exact two native custom polygons required')
    native_paths,native_vias=source_routes(source)
    # Name encodes the drill in this pinned native DSN; verify against original vias,
    # in addition to exact serialized library circles. No inferred unknown stack.
    actual_native_vias=Counter()
    for (net,name,xy),count in vias.items():
        if name!='Via[0-1]_1600:600_um':raise ValueError('unqualified via drill identity')
        if any(shape[0]!=1600 or shape[1]!=(0,0) for shape in stacks[name].values()):raise ValueError('via body differs')
        actual_native_vias[(net,xy,Decimal(1600),Decimal(600))]+=count
    result={'safe_structure':True,'exact_custom_polygons':2,'placements':len(placements(place,scale)),
        'ses_paths':path_count,'ses_segments':sum(paths.values()),'ses_vias':sum(vias.values()),
        'native_to_dsn':diff(native_paths,dsn_paths),'dsn_to_ses':diff(dsn_paths,paths),
        'dsn_vias_equal':dsn_vias==vias,'native_vias_equal':native_vias==actual_native_vias}
    if geometry is not None:
        engine_paths=Counter();engine_vias=Counter()
        for row in geometry['traces']:
            if row['fixed']=='SYSTEM_FIXED' or len(row['nets'])!=1 or any(x is None for x in row['corners_board_integer']):raise ValueError('exact engine trace unavailable')
            engine_paths.update(segments(row['nets'][0],row['layer'],row['width_um'],[tuple(number(x) for x in point) for point in row['corners_um']]))
        for row in geometry['vias']:
            if row['fixed']=='SYSTEM_FIXED' or len(row['nets'])!=1 or row['position_board_integer'] is None:raise ValueError('exact engine via unavailable')
            engine_vias[(row['nets'][0],row['padstack_name'],tuple(number(x) for x in row['position_um']))]+=1
        if geometry['trace_count']!=len(geometry['traces']) or geometry['via_count']!=len(geometry['vias']):raise ValueError('engine geometry census differs')
        result.update(dsn_to_engine=diff(dsn_paths,engine_paths),engine_to_ses=diff(engine_paths,paths),engine_vias_equal=engine_vias==vias)
    result['exact_route_survival']=all(v['equal'] for v in result.values() if isinstance(v,dict) and 'equal' in v) and all(result[k] for k in ('dsn_vias_equal','native_vias_equal')) and result.get('engine_vias_equal',True)
    if generated:
        result['generated_engine_to_ses_exact']=result['engine_to_ses']['equal'] and result['engine_vias_equal']
        result['scope']='New ordinary routing from zero seed; retained-route survival is not the acceptance obligation.'
    return tree,result

def require_faithful(result):
    if result.get('safe_structure') is not True or result.get('exact_route_survival') is not True:raise ValueError('retained route geometry changed across SES transport')

def disconnected(tree,source,expected):
    net='/pic_sockets/VCC_PIC'
    terminals=[x for x in expected['terminals'] if x['net']==net]
    if len(terminals)!=11 or not any(x['reference']=='JP1' and x['number']=='2' for x in terminals):raise ValueError('negative terminal census differs')
    if any(p.locked(r) for r in p.routes(source)) or any(sx.one(z,'net')==['net','"'+net+'"'] for z in sx.children(source,'zone')):raise ValueError('negative protected/zone recipe unsupported')
    out=copy.deepcopy(tree);network=sx.one(sx.one(out,'routes'),'network_out');nodes=[n for n in sx.children(network,'net') if sx.unquote(n[1])==net]
    if len(nodes)!=1:raise ValueError('negative named net absent')
    node=nodes[0];removed=[x for x in node if isinstance(x,list) and (x[0]=='via' or x[0]=='wire' and sx.one(x,'path'))]
    if not removed:raise ValueError('negative has no ordinary routes')
    node[:]=[x for x in node if x not in removed]
    return (sx.dump(out)+'\n').encode(),{'net':net,'terminal_count':len(terminals),'removed_nodes':len(removed),'removed_sha256':hashlib.sha256(sx.dump(removed).encode()).hexdigest()}

def geometry_check(geometry,state):
    """Bind every added route coordinate to its exact integer and census witness."""
    scale=number(state['board_units_per_um']);origin=[number(x) for x in state['board_origin_dsn_um']]
    items={r['id']:r for r in state['items']}
    def point(integer,um):
        if not isinstance(integer,list) or len(integer)!=2 or any(type(x) is not int for x in integer):raise ValueError('exact integer engine point required')
        if [number(x)/scale+o for x,o in zip(integer,origin)]!=[number(x) for x in um]:raise ValueError('engine integer/um point mismatch')
    for key,kind in (('traces','app.freerouting.board.trace.PolylineTrace'),('vias','app.freerouting.board.model.items.Via')):
        rows=geometry[key];ids=[r['id'] for r in rows]
        if len(ids)!=len(set(ids)) or set(ids)!={i for i,r in items.items() if r['kind']==kind} or len(ids)!=state['census'][key]:raise ValueError('complete exact engine route census required')
        for row in rows:
            if any(row.get(k)!=v for k,v in items[row['id']].items()):raise ValueError('engine route identity differs')
            if any(type(row[k]) is not int or not 0<=row[k]<len(state['layers']) for k in ('first_layer','last_layer')):raise ValueError('engine route layer indices out of bounds')
            if key=='traces':
                if type(row['layer_index']) is not int or not 0<=row['layer_index']<len(state['layers']):raise ValueError('engine trace layer index out of bounds')
                if (row['corner_count']!=len(row['corners_um']) or row['corner_count']!=len(row['corners_board_integer'])
                        or row['corner_count']!=len(row['corner_classes']) or number(row['width_um'])!=number(row['half_width_board_units'])*2/scale
                        or row['layer']!=state['layers'][row['layer_index']] or row['layer_index']!=row['first_layer'] or row['first_layer']!=row['last_layer']):raise ValueError('engine route shape metadata differs')
                for integer,um in zip(row['corners_board_integer'],row['corners_um']):point(integer,um)
            else:
                point(row['position_board_integer'],row['position_um'])
                if row['first_layer']!=0 or row['last_layer']!=1 or row['layers']!=state['layers']:raise ValueError('engine via span differs')
