"""Explicit single-Default floor guidance; no native execution or I/O.

Raw native DSN -> this exact rule/via edit -> existing graphics/plane adapter.
Caller retains all stages, binds the native process and original project, uses
ENGINE_REQUIREMENTS, checks final immutable geometry/generated dimensions and
runs original native DRC. Passing this module alone never accepts routing.
"""
from __future__ import annotations
import copy
from decimal import Context, Decimal, DecimalException, Inexact, InvalidOperation, Overflow, localcontext
import hashlib
import json
import re
from autorouter import sexpr as sx
from autorouter.adapter import _parse_dsn, _dump_dsn, _check_units
from autorouter.netclass import qualify_project

POLICY='board-floors-v1'
ENGINE_REQUIREMENTS={'automatic_neckdown':False,'fanout.enabled':False,'neck_width_um':0}
DIMENSIONS={'width_nm':'track_width','clearance_nm':'clearance',
            'via_diameter_nm':'via_diameter','via_drill_nm':'via_drill'}
FLOORS=('min_track_width','min_clearance','min_via_diameter','min_through_hole_diameter','min_via_annular_width')
ROUTES={'segment','arc','via'}
# Full parent-child grammar for the pinned two-layer *raw* exports observed by
# native context001. Unknown syntax is unsupported, even if likely harmless.
GRAMMAR={
 'pcb':{'parser','resolution','unit','structure','placement','library','network','wiring'},
 'parser':{'string_quote','space_in_quoted_tokens','host_cad','host_version'},
 'structure':{'layer','boundary','keepout','plane','via','rule'},
 'layer':{'type','property'},'property':{'index'},'boundary':{'path'},
 'keepout':{'polygon'},'plane':{'polygon'},'rule':{'width','clearance'},'clearance':{'type'},
 'placement':{'component'},'component':{'place'},'place':{'PN'},
 'library':{'image','padstack'},'image':{'outline','pin'},'outline':{'path','polygon'},
 'pin':{'rotate'},'padstack':{'shape','attach'},'shape':{'circle','rect','polygon','path'},
 'network':{'net','class'},'net':{'pins'},'class':{'rule','circuit'},'circuit':{'use_via'},
}
LEAVES={'string_quote','space_in_quoted_tokens','host_cad','host_version','resolution','unit',
        'type','index','path','polygon','via','width','PN','rotate','attach','circle','rect','pins','use_via','wiring'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def millimetres(value,zero=False):
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise ValueError('finite JSON dimensions required')
    return decimal_nm(str(value),1000000,zero)


def decimal_nm(atom,multiplier,zero=False):
    if not isinstance(atom,str):raise ValueError('dimension must be an atom')
    try:value=Decimal(atom)*multiplier
    except InvalidOperation:raise ValueError('malformed dimension') from None
    if not value.is_finite() or value<(0 if zero else 1) or value!=value.to_integral_value():
        raise ValueError('dimension must be exact nonnegative integer nanometres')
    return int(value)


def atom_um(value):
    if type(value) is not int or value<=0:raise ValueError('invalid derived dimension')
    value=format(Decimal(value)/1000,'f')
    return value.rstrip('0').rstrip('.') if '.' in value else value


def derive(raw,floors):
    if set(raw)!=set(DIMENSIONS) or set(floors)!=set(FLOORS):raise ValueError('missing or unexpected dimensions')
    if any(type(x) is not int or x<=0 for x in raw.values()) or any(type(x) is not int or x<0 for x in floors.values()):
        raise ValueError('integer native dimensions required')
    if any(raw[k]%(400 if k=='clearance_nm' else 200 if k in {'width_nm','via_diameter_nm'} else 100) for k in raw):
        raise ValueError('off-grid raw guidance unsupported')
    width=max(raw['width_nm'],floors['min_track_width'])
    clearance=max(raw['clearance_nm'],floors['min_clearance'])
    drill=max(raw['via_drill_nm'],floors['min_through_hole_diameter'])
    diameter=max(raw['via_diameter_nm'],floors['min_via_diameter'],drill+2*floors['min_via_annular_width'])
    targets={'width_nm':width,'clearance_nm':clearance,'via_diameter_nm':diameter,'via_drill_nm':drill}
    if diameter<=drill:raise ValueError('derived via has no annulus')
    # Conservative explicitly supported grid; no hidden quantization or rounding.
    for key,value in targets.items():
        if value%(200 if key in {'width_nm','via_diameter_nm'} else 100):raise ValueError('off-grid derived guidance unsupported')
    return targets


def source_net_identity(task):
    """Bind old numbered and KiCad10 named references without guessing aliases."""
    declared=sx.children(task,'net');table={};names=set()
    for node in declared:
        if (len(node)!=3 or any(not isinstance(x,str) for x in node)
                or re.fullmatch(r'0|[1-9][0-9]*',node[1]) is None):
            raise ValueError('malformed original net declaration')
        code,name=node[1],sx.unquote(node[2])
        if code in table or (name and name in names):raise ValueError('duplicate original net identity')
        if (code=='0') != (name==''):raise ValueError('original empty net must be code zero')
        table[code]=name
        if name:names.add(name)
    def resolve(node,*,owner=None):
        if node is None:return ''
        if any(not isinstance(x,str) for x in node):raise ValueError('malformed original net reference')
        if declared:
            if len(node) not in (2,3) or node[1] not in table:raise ValueError('undeclared original net reference')
            name=table[node[1]]
            if len(node)==3 and sx.unquote(node[2])!=name:raise ValueError('original net code/name conflict')
            return name
        # KiCad10 named-net boards can retain the legacy unconnected marker
        # on an explicitly unrestricted board rule area. This is NOT an alias
        # for any pad/route net or a named net whose text happens to be "0".
        if (node==['net','0'] and any(owner is zone for zone in sx.children(task,'zone'))
                and sx.children(owner,'net')==[node]
                and sx.children(owner,'net_name')==[['net_name','""']]):
            flags={'tracks','vias','pads','copperpour','footprints'}
            keepouts=sx.children(owner,'keepout')
            if (len(keepouts)==1 and len(keepouts[0])==6
                    and all(isinstance(x,list) and len(x)==2 and x[0] in flags and x[1]=='allowed' for x in keepouts[0][1:])
                    and {x[0] for x in keepouts[0][1:]}==flags):
                return ''
        if len(node)!=2 or not node[1].startswith(chr(34)) or not node[1].endswith(chr(34)):
            raise ValueError('unqualified named task net reference')
        return sx.unquote(node[1])
    def walk(node):
        for child in node[1:]:
            if not isinstance(child,list) or not child:continue
            if child[0]=='net':
                name=resolve(child,owner=node)
                if name:names.add(name)
            else:walk(child)
    # Root declarations have already been checked; inspect every other reference.
    for child in task[1:]:
        if isinstance(child,list) and child and child[0]!='net':walk(child)
    return names,resolve


def task_pads(task):
    _,resolve=source_net_identity(task)
    pads={};refs=set()
    for fp in sx.children(task,'footprint'):
        properties=[n for n in sx.children(fp,'property') if sx.unquote(n[1])=='Reference']
        if len(properties)!=1:raise ValueError('unqualified reference identity')
        ref=sx.unquote(properties[0][2])
        if ref in refs:raise ValueError('duplicate reference')
        refs.add(ref)
        for pad in sx.children(fp,'pad'):
            uid=sx.unquote(sx.one(pad,'uuid')[1]);name=resolve(sx.one(pad,'net'))
            layers=[sx.unquote(n) for n in sx.one(pad,'layers')[1:]]
            copper=[layer for layer in ('F.Cu','B.Cu') if layer in layers or '*.Cu' in layers]
            if uid in pads:raise ValueError('duplicate pad UUID')
            pads[uid]={'reference':ref,'number':sx.unquote(pad[1]),'net':name,'copper_layers':copper}
    return pads


def qualify_scope(project,task):
    if qualify_project(project)['mode']!='single_default':raise ValueError('floor mode requires single Default')
    if sx.children(task,'segment') or sx.children(task,'via') or sx.children(task,'arc'):
        raise ValueError('floor mode requires zero existing/protected routes')
    layers=sx.one(task,'layers')
    copper=[n for n in layers[1:] if isinstance(n,list) and len(n)>1 and sx.unquote(n[1]).endswith('.Cu')]
    if len(copper)!=2 or {sx.unquote(n[1]) for n in copper}!={'F.Cu','B.Cu'}:raise ValueError('two outer copper layers required')
    for zone in sx.children(task,'zone'):
        if sx.children(zone,'filled_polygon') or sx.children(zone,'fill_segments'):raise ValueError('derived task fill must be stripped')
    # Footprint/pad clearances and legacy board netclasses could add effective
    # preferences not represented by the per-net report. Keep them unsupported.
    if sx.children(task,'net_class'):raise ValueError('legacy board class overrides unsupported')
    for fp in sx.children(task,'footprint'):
        if sx.children(fp,'net_tie_pad_groups'):raise ValueError('net ties unsupported')
        for node in [fp,*sx.children(fp,'pad')]:
            if node[0]=='pad' and node[3]=='custom':raise ValueError('custom pad unsupported')
            for key in ('clearance','zone_connect'):
                value=sx.one(node,key)
                if value is not None and (len(value)!=2 or value[1]!='0'):raise ValueError('local pad/footprint rule override unsupported')


def qualify(project,native,task):
    if not isinstance(native,dict):raise ValueError('native context object required')
    qualify_scope(project,task)
    if (native.get('context_schema')!=1 or type(native.get('context_schema')) is not int or
        native.get('native_version')!='10.0.0' or native.get('units')!='integer nanometres' or
        native.get('board_saved') is not False):raise ValueError('unsupported native context')
    settings=project['board']['design_settings']
    if settings.get('drc_exclusions'):raise ValueError('DRC exclusions unsupported')
    raw={key:millimetres(project['net_settings']['classes'][0][value]) for key,value in DIMENSIONS.items()}
    floors={key:millimetres(settings['rules'][key],zero=True) for key in FLOORS}
    if native.get('floors_nm')!=floors or any(type(v) is not int for v in native['floors_nm'].values()):
        raise ValueError('native loaded floor mismatch')
    rows=native.get('nets');pads=native.get('pads')
    if not isinstance(rows,list) or not 1<=len(rows)<=10000 or not isinstance(pads,list) or len(pads)>100000:
        raise ValueError('missing or oversized native inventory')
    names=set();codes=set()
    for row in rows:
        if not isinstance(row.get('name'),str) or not row['name'] or row['name'] in names or row.get('class')!='Default':
            raise ValueError('native class identity mismatch')
        for key in ('netcode',*DIMENSIONS,'copper_pad_count'):
            if type(row.get(key)) is not int or row[key]<(0 if key=='copper_pad_count' else 1):raise ValueError('malformed native row')
        if row['netcode'] in codes or any(row[k]!=v for k,v in raw.items()):raise ValueError('raw native preferences mismatch')
        names.add(row['name']);codes.add(row['netcode'])
    expected_names,_=source_net_identity(task)
    if expected_names!=names:raise ValueError('native net inventory differs from original task')
    observed={}
    for pad in pads:
        if not isinstance(pad,dict) or not isinstance(pad.get('uuid'),str) or pad['uuid'] in observed:raise ValueError('duplicate/malformed native pad')
        if type(pad.get('netcode')) is not int or pad['netcode']<0:raise ValueError('malformed native pad netcode')
        observed[pad['uuid']]={k:pad[k] for k in ('reference','number','net','copper_layers')}
    if observed!=task_pads(task):raise ValueError('native pad mapping differs from original task')
    mapping={r['name']:r for r in rows};pad_counts={}
    for pad in pads:
        if pad['netcode']>0:
            if pad['net'] not in mapping or mapping[pad['net']]['netcode']!=pad['netcode']:raise ValueError('native pad netcode/name inconsistency')
            if pad['copper_layers']:pad_counts[pad['net']]=pad_counts.get(pad['net'],0)+1
        elif pad['net']:raise ValueError('netless pad has a name')
    for row in rows:
        if pad_counts.get(row['name'],0)!=row['copper_pad_count']:raise ValueError('native terminal count mismatch')
    return {'policy':POLICY,'raw_nm':raw,'floors_nm':floors,'derived_nm':derive(raw,floors),
            'nets':copy.deepcopy(rows),'pads':copy.deepcopy(pads),'engine_requirements':dict(ENGINE_REQUIREMENTS)}


def grammar(tree):
    counts={}
    arities={'pcb':1,'parser':0,'structure':0,'layer':1,'property':0,'boundary':0,'keepout':1,'plane':1,
             'rule':0,'clearance':1,'placement':0,'component':1,'place':5,'library':0,'image':1,
             'outline':0,'pin':4,'padstack':1,'shape':0,'network':0,'net':1,'circuit':0}
    def walk(node,path=()):
        if not isinstance(node,list) or not node or not isinstance(node[0],str):raise ValueError('invalid DSN node')
        head=node[0];path=path+(head,)
        if head not in GRAMMAR and head not in LEAVES:raise ValueError('unknown DSN grammar: '+head)
        if head in arities and sum(isinstance(x,str) for x in node[1:])!=arities[head]:
            raise ValueError('unexpected DSN atom in '+head)
        if head=='shape' and any(isinstance(x,list) and x and x[0]=='path' for x in node[1:]):
            # Pinned KiCad exports ordinary oval pads as a round-ended path,
            # including the circular/zero-centreline case. Accept only that
            # one-segment, two-outer-layer padstack form, never a new rule or
            # arbitrary multi-segment/custom shape scope.
            if (path!=('pcb','library','padstack','shape') or len(node)!=2
                    or len(node[1])!=7 or node[1][1] not in ('F.Cu','B.Cu')
                    or any(type(x) is not str or len(x)>64 for x in node[1])):
                raise ValueError('unqualified oval padstack path')
            values=[]
            try:
                # Every atom is bounded to64 characters above. Use enough
                # precision to keep scaling exact, independent of ambient
                # Decimal settings; rounding must never admit fractional nm.
                with localcontext(Context(prec=100,traps=[Inexact,InvalidOperation,Overflow])):
                    for atom in node[1][2:]:
                        value=Decimal(atom)*1000
                        if not value.is_finite() or value!=value.to_integral_value() or abs(value)>1000000000:
                            raise ValueError('bounded exact-nanometre oval path required')
                        values.append(value)
            except DecimalException as exc:raise ValueError('invalid oval padstack path dimension') from exc
            if values[0]<=0:raise ValueError('positive oval padstack path width required')
        for child in node[1:]:
            if isinstance(child,list):
                if not child or child[0] not in GRAMMAR.get(head,set()):raise ValueError('unknown DSN child scope: '+str(path))
                walk(child,path)
            elif not isinstance(child,str):raise ValueError('invalid DSN atom')
        if head in {'rule','clearance','width','circuit','use_via'}:counts[path]=counts.get(path,0)+1
    walk(tree)
    expected={('pcb','structure','rule'):1,('pcb','structure','rule','width'):1,
       ('pcb','structure','rule','clearance'):2,('pcb','network','class','rule'):1,
       ('pcb','network','class','rule','width'):1,('pcb','network','class','rule','clearance'):1,
       ('pcb','network','class','circuit'):1,('pcb','network','class','circuit','use_via'):1}
    if counts!=expected:raise ValueError('unexpected or duplicate routing rule scope')
    for head in GRAMMAR['pcb']:
        if sx.one(tree,head) is None:raise ValueError('missing DSN root section')
    if any(not isinstance(n,list) for n in tree[2:]):raise ValueError('unknown root atom')


def via_id(dimensions):
    return 'Via[0-1]_'+atom_um(dimensions['via_diameter_nm'])+':'+atom_um(dimensions['via_drill_nm'])+'_um'


def audit_export(tree,context,*,guided=False):
    grammar(tree);_check_units(tree)
    if sx.one(tree,'resolution')!=['resolution','um','10']:raise ValueError('unsupported native routing grid')
    if sx.one(tree,'wiring')!=['wiring']:raise ValueError('unexpected route wiring')
    structure,network,library,placement=[sx.one(tree,k) for k in ('structure','network','library','placement')]
    # A complete pin mapping alone does not reject an extra empty declaration,
    # duplicate declaration, or the same source net split over several nodes.
    # The pinned exporter declares exactly the native nets with copper terminals;
    # zero-copper source nets remain class members, never empty DSN declarations.
    declarations=sx.children(network,'net');exported=[]
    expected_nets={row['name'] for row in context['nets'] if row['copper_pad_count']>0}
    for node in declarations:
        if (len(node)!=3 or not isinstance(node[1],str) or not sx.unquote(node[1])
                or not isinstance(node[2],list) or not node[2] or node[2][0]!='pins'
                or len(node[2])<2 or any(not isinstance(x,str) or not sx.unquote(x) for x in node[2][1:])):
            raise ValueError('nonempty exact DSN net declaration required')
        exported.append(sx.unquote(node[1]))
    if len(exported)!=len(set(exported)) or set(exported)!=expected_nets:
        raise ValueError('DSN/source copper-terminal net inventory differs')
    layers=sx.children(structure,'layer')
    if len(layers)!=2 or {sx.unquote(x[1]) for x in layers}!={'F.Cu','B.Cu'}:raise ValueError('invalid layers')
    dim=context['derived_nm' if guided else 'raw_nm'];vid=via_id(dim)
    rules=sx.one(structure,'rule')
    if rules!=['rule',['width',atom_um(dim['width_nm'])],['clearance',atom_um(dim['clearance_nm'])],
            ['clearance',atom_um(dim['clearance_nm'] if guided else context['raw_nm']['clearance_nm']//4),['type','smd_smd']]]:
        raise ValueError('global width/clearance/type mismatch')
    classes=sx.children(network,'class')
    if len(classes)!=1 or sx.unquote(classes[0][1])!='kicad_default':raise ValueError('unexpected class')
    cls=classes[0];members=[sx.unquote(n) for n in cls[2:] if isinstance(n,str)]
    if len(set(members))!=len(members) or set(members)!={n['name'] for n in context['nets']}:
        raise ValueError('class membership mismatch')
    if sx.one(cls,'rule')!=rules[:3] or sx.one(cls,'circuit')!=['circuit',['use_via','"'+vid+'"']]:raise ValueError('class guidance mismatch')
    if sx.one(structure,'via')!=['via','"'+vid+'"']:raise ValueError('extra/missing via choice')
    stacks=sx.children(library,'padstack');ids=[sx.unquote(x[1]) for x in stacks]
    id_set=set(ids)
    if len(id_set)!=len(ids):raise ValueError('duplicate padstack ID')
    chosen=next((x for x in stacks if sx.unquote(x[1])==vid),None)
    if chosen!=['padstack','"'+vid+'"',['shape',['circle','F.Cu',atom_um(dim['via_diameter_nm'])]],
            ['shape',['circle','B.Cu',atom_um(dim['via_diameter_nm'])]],['attach','off']]:raise ValueError('via shape/drill mismatch')
    if any(name.startswith('Via[') and name!=vid for name in ids):raise ValueError('alternative via definition unsupported')
    images=sx.children(library,'image');image_map={sx.unquote(x[1]):x for x in images}
    if len(image_map)!=len(images):raise ValueError('duplicate library image')
    placed={}
    for component in sx.children(placement,'component'):
        image=sx.unquote(component[1])
        if image not in image_map:raise ValueError('unknown image reference')
        pins=sx.children(image_map[image],'pin');pin_ids=[]
        for pin in pins:
            if sx.unquote(pin[1]) not in id_set:raise ValueError('unknown padstack reference')
            atoms=[n for n in pin[2:] if isinstance(n,str)]
            if len(atoms)!=3:raise ValueError('malformed library pin')
            pin_ids.append(sx.unquote(atoms[0]))
        if len(set(pin_ids))!=len(pin_ids):raise ValueError('duplicate library pin')
        for place in sx.children(component,'place'):
            ref=sx.unquote(place[1])
            if ref in placed:raise ValueError('duplicate placement')
            placed[ref]=set(pin_ids)
    native={}
    for pad in context['pads']:
        if pad['netcode']<=0 or not pad['copper_layers']:continue
        ref,number=pad['reference'],pad['number'];token=ref+'-'+number
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',ref) or not re.fullmatch(r'[A-Za-z0-9_]+',number):raise ValueError('connected name escaping unsupported')
        if token in native or ref not in placed or number not in placed[ref]:raise ValueError('ambiguous/missing connected pin')
        native[token]=pad
    observed={}
    for net in sx.children(network,'net'):
        if len(net)!=3 or not isinstance(net[2],list) or net[2][0]!='pins':raise ValueError('net overrides unsupported')
        for atom in net[2][1:]:
            token=sx.unquote(atom)
            if token in observed or token not in native or native[token]['net']!=sx.unquote(net[1]):raise ValueError('pin mapping mismatch')
            observed[token]=native[token]['uuid']
    if set(observed)!=set(native):raise ValueError('missing terminal')
    return {'passed':True,'policy':POLICY,'guided':guided,'terminal_count':len(observed),'declared_copper_terminal_nets':len(exported),'source_class_nets':len(context['nets']),'via_id':vid,
            'routing_accepted':False,'physical_geometry_qualification':False}


def expected_edit(raw,context):
    tree=copy.deepcopy(raw);dim=context['derived_nm'];old=via_id(context['raw_nm']);new=via_id(dim)
    structure=sx.one(tree,'structure');network=sx.one(tree,'network');library=sx.one(tree,'library')
    existing={sx.unquote(x[1]) for x in sx.children(library,'padstack')}
    if new!=old and new in existing:raise ValueError('derived via ID collision')
    global_rule=sx.one(structure,'rule');global_rule[1][1]=atom_um(dim['width_nm'])
    global_rule[2][1]=atom_um(dim['clearance_nm']);global_rule[3][1]=atom_um(dim['clearance_nm'])
    cls=sx.children(network,'class')[0];sx.one(cls,'rule')[1][1]=atom_um(dim['width_nm']);sx.one(cls,'rule')[2][1]=atom_um(dim['clearance_nm'])
    sx.one(sx.one(cls,'circuit'),'use_via')[1]='"'+new+'"';sx.one(structure,'via')[1]='"'+new+'"'
    stack=next(x for x in sx.children(library,'padstack') if sx.unquote(x[1])==old);stack[1]='"'+new+'"'
    for shape in sx.children(stack,'shape'):sx.one(shape,'circle')[2]=atom_um(dim['via_diameter_nm'])
    return tree


def verify_edit(raw,guided,context):
    audit_export(raw,context);audit_export(guided,context,guided=True)
    if guided!=expected_edit(raw,context):raise ValueError('edit changed protected DSN semantics')
    return {'passed':True,'exact_allowed_change':True,'routing_accepted':False}


def transform(raw_dsn_bytes,native,project_bytes,task_bytes):
    if not isinstance(native,dict):raise ValueError('native context object required')
    for value in (raw_dsn_bytes,project_bytes,task_bytes):
        if not isinstance(value,bytes) or len(value)>sx.MAX_BYTES:raise ValueError('bounded input bytes required')
    if (native.get('dsn_sha256')!=sha(raw_dsn_bytes) or native.get('board_sha256')!=sha(task_bytes) or
            native.get('project_sha256')!=sha(project_bytes)):
        raise ValueError('native context/source/DSN byte binding mismatch')
    context=qualify(json.loads(project_bytes),native,sx.parse(task_bytes.decode('utf-8')))
    raw=_parse_dsn(raw_dsn_bytes.decode('utf-8'));raw_audit=audit_export(raw,context)
    guided=expected_edit(raw,context);edit_audit=verify_edit(raw,guided,context)
    encoded=_dump_dsn(guided).encode('utf-8')
    if _parse_dsn(encoded.decode('utf-8'))!=guided or len(encoded)>sx.MAX_BYTES:raise ValueError('guided DSN roundtrip/size failed')
    receipt={'schema':1,'policy':POLICY,'input_sha256':sha(raw_dsn_bytes),'output_sha256':sha(encoded),
             'project_sha256':sha(project_bytes),'task_sha256':sha(task_bytes),
             'native_context_content_sha256':sha(json.dumps(native,sort_keys=True,separators=(',',':')).encode()),
             'raw_nm':context['raw_nm'],'original_floors_nm':context['floors_nm'],'derived_nm':context['derived_nm'],
             'engine_requirements':dict(ENGINE_REQUIREMENTS),'raw_audit':raw_audit,'edit_audit':edit_audit,
             'routing_accepted':False,'production_support_qualified':False,
             'limitations':['Caller must bind real native process and all original project/rule files.',
               'No independent physical pad geometry/import qualification; full native validation remains required.',
               'Run existing geometry/plane adapter after floor guidance; preserve each distinct stage.']}
    return encoded,receipt


def audit_generated_routes(candidate,context):
    # All candidate route objects are generated: this mode refuses any original
    # route, including protected route exemptions. Source invariants stay separate.
    dim=context['derived_nm'];floors=context['floors_nm'];known={n['name'] for n in context['nets']}
    names,resolve=source_net_identity(candidate)
    if names!=known:raise ValueError('generated candidate source net inventory changed')
    counts={'segment':0,'arc':0,'via':0}
    for route in candidate:
        if not isinstance(route,list) or not route or route[0] not in ROUTES:continue
        net=sx.one(route,'net')
        if net is None or len(net)!=2 or resolve(net) not in known:raise ValueError('generated route has unknown net')
        if route[0]=='via':
            if 'micro' in route or 'blind' in route or [sx.unquote(n) for n in sx.one(route,'layers')[1:]]!=['F.Cu','B.Cu']:
                raise ValueError('generated advanced via unsupported')
            diameter=decimal_nm(sx.one(route,'size')[1],1000000);drill=decimal_nm(sx.one(route,'drill')[1],1000000)
            if diameter!=dim['via_diameter_nm'] or drill!=dim['via_drill_nm'] or diameter-drill<2*floors['min_via_annular_width']:
                raise ValueError('generated via differs from derived guidance/floor')
        elif decimal_nm(sx.one(route,'width')[1],1000000)!=dim['width_nm']:
            raise ValueError('generated track differs from derived guidance')
        counts[route[0]]+=1
    return {'passed':True,'counts':counts,'policy':'exact derived floor guidance for every generated route',
            'routing_accepted':False}


def task_from_source(original):
    """Reconstruct the ordinary whole-board task, rejecting protected routing."""
    from .pipeline import locked
    if any(locked(node) for node in original if isinstance(node,list) and node and node[0] in ROUTES):
        raise ValueError('floor policy does not support protected routes')
    task=copy.deepcopy(original)
    task[:]=[node for node in task if not isinstance(node,list) or not node or node[0] not in ROUTES]
    for zone in sx.children(task,'zone'):
        zone[:]=[node for node in zone if not isinstance(node,list) or not node or node[0] not in {'filled_polygon','fill_segments'}]
    return task


def adapter_bytes(guided,obstacles):
    """Independently reconstruct the qualified both-adapter semantic edit."""
    from . import adapter as a
    tree=a._parse_dsn(guided.decode('utf-8'));structure=sx.one(tree,'structure')
    layers={sx.unquote(node[1]):node[1] for node in sx.children(structure,'layer')}
    if set(layers)!={'F.Cu','B.Cu'} or not isinstance(obstacles,list) or len(obstacles)>10000:raise ValueError('unsupported adapter context')
    for node in sx.children(structure,'keepout'):
        if len(node)>1 and sx.unquote(node[1]).startswith(a._KEEP_OUT_PREFIX):raise ValueError('adapter keepout collision')
    structure[:]=[node for node in structure if not (isinstance(node,list) and node and node[0]=='plane')]
    for index,obstacle in enumerate(obstacles):
        if not isinstance(obstacle,dict) or obstacle.get('layer') not in layers or 'dsn_layer' in obstacle:raise ValueError('unsupported native obstacle layer')
        bbox=obstacle.get('bbox_mm')
        if not isinstance(bbox,list) or len(bbox)!=4:raise ValueError('invalid native obstacle rectangle')
        xmin,ymin,xmax,ymax=map(a._number,bbox)
        if xmin>=xmax or ymin>=ymax:raise ValueError('invalid native obstacle rectangle')
        coords=[a._atom_number(value*1000) for value in (xmin,-ymax,xmax,-ymin)]
        name=a._KEEP_OUT_PREFIX+sha(guided)[:12]+'_'+str(index)
        structure.append(['keepout',name,['rect',layers[obstacle['layer']],*coords]])
    return a._dump_dsn(tree).encode('utf-8')


def verify_chain(raw,guided,adapted,native,project,task):
    expected,receipt=transform(raw,native,project,task)
    if expected!=guided:raise ValueError('retained guided DSN differs from derived guidance')
    if adapter_bytes(guided,native.get('obstacles'))!=adapted:raise ValueError('adapter changed guided rules or geometry')
    return receipt


def audit_native_routes(tree,native):
    """Match every native saved route UUID, net, layer, coordinate and dimension."""
    _,resolve=source_net_identity(tree);expected={}
    def coordinate(atom):
        value=Decimal(atom)*1000000
        if not value.is_finite() or value!=value.to_integral_value():raise ValueError('inexact saved coordinate')
        return int(value)
    def xy(node):return [coordinate(v) for v in node[1:3]]
    for node in tree:
        if not isinstance(node,list) or not node or node[0] not in ROUTES:continue
        uid=sx.unquote(sx.one(node,'uuid')[1])
        if uid in expected:raise ValueError('duplicate generated route UUID')
        row={'uuid':uid,'net':resolve(sx.one(node,'net')),'kind':node[0]}
        if node[0]=='segment':row.update(start_nm=xy(sx.one(node,'start')),end_nm=xy(sx.one(node,'end')),layer=sx.unquote(sx.one(node,'layer')[1]),width_nm=decimal_nm(sx.one(node,'width')[1],1000000))
        elif node[0]=='via':row.update(position_nm=xy(sx.one(node,'at')),width_nm=decimal_nm(sx.one(node,'size')[1],1000000),drill_nm=decimal_nm(sx.one(node,'drill')[1],1000000),layers=[sx.unquote(v) for v in sx.one(node,'layers')[1:]])
        else:raise ValueError('generated arcs unsupported for floor policy')
        expected[uid]=row
    observed=native.get('routes')
    if not isinstance(observed,list) or len(observed)!=len(expected):raise ValueError('native route count differs')
    seen=set()
    for row in observed:
        if not isinstance(row,dict) or type(row.get('width_nm')) is not int or row['width_nm']<=0:
            raise ValueError('native route dimension schema differs')
        keys=('position_nm',) if row.get('kind')=='via' else ('start_nm','end_nm')
        if any(not isinstance(row.get(key),list) or len(row[key])!=2 or any(type(v) is not int for v in row[key]) for key in keys):
            raise ValueError('native route coordinate schema differs')
        if row.get('kind')=='via' and (type(row.get('drill_nm')) is not int or row['drill_nm']<=0 or type(row.get('via_type')) is not int):
            raise ValueError('native via schema differs')
        if not isinstance(row,dict) or row.get('uuid') in seen or row.get('uuid') not in expected or any(row.get(k)!=v for k,v in expected[row['uuid']].items()):raise ValueError('native route identity/geometry differs')
        if row['kind']=='via' and row.get('via_type')!=4:raise ValueError('native via is not through')
        seen.add(row['uuid'])
    return {'passed':True,'native_route_count':len(observed),'native_via_count':sum(row['kind']=='via' for row in observed)}
