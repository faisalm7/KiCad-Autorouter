"""Exact edits for two owned scenes; no production custom-pad admission.

Reuse the area002 integer contour and retained-SES geometry utilities. The
unchanged two-class project is authoritative even though both active nets resolve
Default. Raising the DSN smd_smd target to its original Default clearance is a
declared diagnostic edit, never a change to the source project.
"""
import copy
from collections import Counter
import json
from autorouter import sexpr as sx, netclass as nc
from autorouter.adapter import _parse_dsn, _dump_dsn, _check_units
from autorouter.netclass_native import validate_floors
from experiments.custom_pad_area_probe_v1 import derive as area
from experiments.pic_mixed_transport_probe_v1 import ses_checks as ses

PRO_SHA='3b0ac39da5af86d0baa2a64da55a89c39ba00148dc82b54f3062f5c3650a5cc5'
ONE=area.exact_one

def targets(tree,mapping,project_raw):
    if area.sha(project_raw)!=PRO_SHA:raise ValueError('exact unchanged original project required')
    project=json.loads(project_raw);policy=nc.qualify_project(project)
    if policy['literal_assignments']!={'GND':'POWER','VCC':'POWER'}:raise ValueError('original unused patterns differ')
    if mapping['native_version']!='10.0.7' or mapping['units']!='integer nanometres':raise ValueError('current Native mapping required')
    cls=next(c for c in project['net_settings']['classes'] if c['name']=='Default')
    floors=validate_floors(mapping['effective_floors_nm'],project)
    dimensions=dict(width_nm=500000,clearance_nm=250000,via_diameter_nm=1600000,via_drill_nm=600000)
    nets=mapping['nets']
    if len(nets)!=2 or {n['name'] for n in nets}!={'CONTACT','FOREIGN'}:raise ValueError('complete two-net map required')
    for n in nets:
        if n['class']!='Default' or n['copper_pad_count']!=2:raise ValueError('active source Default/terminal census differs')
        nc._check_parameter_parents(n,cls)
        if any(type(n.get(k)) is not int or n[k]!=v for k,v in dimensions.items()):raise ValueError('source dimension differs')
    if (dimensions['width_nm']<floors['min_track_width'] or dimensions['clearance_nm']<floors['min_clearance']
            or dimensions['via_diameter_nm']<floors['min_via_diameter']
            or dimensions['via_drill_nm']<floors['min_through_hole_diameter']
            or dimensions['via_diameter_nm']-dimensions['via_drill_nm']<2*floors['min_via_annular_width']):
        raise ValueError('original hard floor undercut')
    network=ONE(tree,'network');structure=ONE(tree,'structure');library=ONE(tree,'library')
    if {sx.unquote(n[1]):[sx.unquote(p) for p in ONE(n,'pins')[1:]] for n in sx.children(network,'net')}!={'CONTACT':['CONVEX-1','CONCAVE-1'],'FOREIGN':['FOREIGN_A-1','FOREIGN_B-1']}:
        raise ValueError('complete original terminal mapping differs')
    expected=['class','kicad_default','CONTACT','FOREIGN',['circuit',['use_via','"Via[0-1]_1600:600_um"']],['rule',['width','500'],['clearance','250']]]
    if sx.children(network,'class')!=[expected] or len(network)!=4:raise ValueError('raw DSN class/override differs')
    rule=ONE(structure,'rule')
    if rule!=['rule',['width','500'],['clearance','250'],['clearance','62.5',['type','smd_smd']]]:raise ValueError('raw global/typed targets differ')
    via=next((s for s in sx.children(library,'padstack') if s[1]=='"Via[0-1]_1600:600_um"'),None)
    if via!=['padstack','"Via[0-1]_1600:600_um"',['shape',['circle','top_layer','1600']],['shape',['circle','bottom_layer','1600']],['attach','off']]:raise ValueError('exact original through via required')
    old=copy.deepcopy(rule);rule[-1]=['clearance','250',['type','smd_smd']]
    return old,dict(source_project_sha256=PRO_SHA,unused_POWER_and_patterns_preserved=True,active_Default_dimensions_nm=dimensions,hard_floors_nm=floors,typed_clearance_um=dict(before='62.5',after='250'),production_admitted=False)

def derive(raw,custom,context,recipe,project_raw,*,generated=False):
    if type(generated) is not bool:raise ValueError('explicit seed mode required')
    before=_parse_dsn(raw.decode());tree=copy.deepcopy(before);_check_units(tree)
    if ONE(ONE(tree,'parser'),'host_version')!=['host_version','"10.0.7"']:raise ValueError('current Native export required')
    if custom['native_version']!='10.0.7' or context['native_version']!='10.0.7':raise ValueError('current observation required')
    if not custom['same_loaded_board'] or custom['board_saved'] or custom['observation_before_export']!=custom['observation_after_export']:raise ValueError('same-load immutable observation required')
    if custom['dsn_sha256']!=area.sha(raw) or context['dsn_sha256']!=area.sha(raw):raise ValueError('raw export binding differs')
    if custom['board_sha256']!=context['board_sha256'] or custom['project_sha256']!=context['project_sha256'] or custom['project_sha256']!=PRO_SHA:raise ValueError('source binding differs')
    if custom['input_hashes_before']!=custom['input_hashes_after']:raise ValueError('source project changed')
    if recipe['variant']!='back90' or recipe['case'] not in ('positive','false_hull') or generated and recipe['case']!='positive':raise ValueError('two fixed owned scenes only')
    mapping=context['mapping']
    if (mapping.get('source')!=context['source'] or mapping.get('board_sha256')!=custom['board_sha256']
            or mapping.get('project_sha256')!=PRO_SHA or mapping.get('board_saved') is not False):raise ValueError('same-source Native map binding differs')
    old_rule,target=targets(tree,mapping,project_raw)
    lib=ONE(tree,'library');wiring=ONE(tree,'wiring');structure=ONE(tree,'structure')
    if sx.children(structure,'plane') or sx.children(wiring,'via'):raise ValueError('planes and seed vias prohibited')
    wires=sx.children(wiring,'wire')
    if len(wiring)!=1+len(wires) or len(wires)!=(0 if generated else 2):raise ValueError('exact seed-route census required')
    if not generated:
        for wire,t in zip(wires,recipe['tracks']):
            a,b=area.coord(t['start']),area.coord(t['end'])
            if wire!=['wire',['path','bottom_layer','500',*[str(v) for point in (a,b) for v in point]],['net',t['net']],['type','route']]:raise ValueError('original reference wire differs')
    images={sx.unquote(x[1]):x for x in sx.children(lib,'image')};stacks={sx.unquote(x[1]):x for x in sx.children(lib,'padstack')}
    places={sx.unquote(p[1]):(sx.unquote(c[1]),p) for c in sx.children(ONE(tree,'placement'),'component') for p in sx.children(c,'place')}
    if len(places)!=4 or len(images)!=3 or len(stacks)!=4:raise ValueError('complete placement/library census required')
    for pad in recipe['pads']:
        place=places[pad['reference']][1]
        if place[2:6]!=[*map(str,area.coord(pad['at'])),'back','270']:raise ValueError('source terminal placement differs')
    names=[area.imported_name(k) for k in stacks]
    if len(set(names))!=4:raise ValueError('imported padstack collision')
    pads=custom['observation_before_export']['pads']
    if len(pads)!=2 or {p['reference'] for p in pads}!={'CONVEX','CONCAVE'}:raise ValueError('exact custom census required')
    edits=[];areas=[]
    for pad in sorted(pads,key=lambda p:p['reference']):
        if (pad['anchor']!='rect' or pad['size_nm']!=[300000,300000] or pad['offset_nm']!=[0,0]
                or pad['drill_nm']!=[0,0] or pad['number']!='1' or pad['net']!='CONTACT' or pad['copper_layers']!=['B.Cu']):raise ValueError('unchanged source anchor required')
        points=area.contour(pad['effective_world'])
        if area.canonical_ring(points)!=area.canonical_ring(area.contour(pad['transformed_world'])):raise ValueError('native world contour disagreement')
        r=next(p for p in recipe['pads'] if p['reference']==pad['reference'])
        if pad['uuid']!=r['uuid'] or area.canonical_ring(points)!=area.canonical_ring([area.coord(p) for p in r['polygon']]):raise ValueError('original recipe contour differs')
        image,place=places[pad['reference']];pin=ONE(images[image],'pin')
        if pin[2:]!=['1','0','0']:raise ValueError('pin identity/offset differs')
        stack=stacks[sx.unquote(pin[1])];shape=ONE(stack,'shape')
        if shape[1][:2]!=['polygon','top_layer']:raise ValueError('expected raw hull required')
        i=stack.index(shape);edits.append((stack[1],i,copy.deepcopy(shape)));stack[i]=['shape',['rect','top_layer','-150','-150','150','150']]
        wiring.append(['wire',['polygon','bottom_layer','0',*[str(v) for point in points for v in point]],['net','CONTACT'],['type','protect']])
        areas.append(dict(reference=pad['reference'],net='CONTACT',layer='bottom_layer',ring_um=points,fixed='USER_FIXED'))
    reverse=copy.deepcopy(tree);ONE(reverse,'wiring')[-2:]=[];ONE(reverse,'structure')[ONE(reverse,'structure').index(ONE(ONE(reverse,'structure'),'rule'))]=old_rule
    for name,index,old in edits:next(s for s in sx.children(ONE(reverse,'library'),'padstack') if s[1]==name)[index]=old
    if reverse!=before:raise ValueError('undeclared DSN edit')
    out=_dump_dsn(tree).encode()
    if _parse_dsn(out.decode())!=tree:raise ValueError('DSN serialization differs')
    return out,dict(schema=1,areas=areas,target=target,seed_routes=0 if generated else 2,source_board_sha256=custom['board_sha256'],original_raw_sha256=area.sha(raw),derived_sha256=area.sha(out),generated=generated,nets=['CONTACT','FOREIGN'],production_admitted=False)

def import_session(raw,dsn_raw,expected):
    """Remove only the two exact synthetic areas; preserve every other SES atom."""
    if area.sha(dsn_raw)!=expected['derived_sha256']:raise ValueError('derived DSN binding differs')
    if not 0<len(raw)<=4*1024**2:raise ValueError('bounded SES required')
    before=sx.parse(raw.decode());tree=copy.deepcopy(before);dsn=_parse_dsn(dsn_raw.decode())
    ses.children_only(tree,{'base_design','placement','was_is','routes'},2)
    name='task' if expected['generated'] else 'original-mixed.dsn'
    if tree[0]!='session' or sx.unquote(tree[1])!=name.replace('.dsn','.ses') or sx.one(tree,'base_design') is None or len(sx.one(tree,'base_design'))!=2 or sx.unquote(sx.one(tree,'base_design')[1])!=name:raise ValueError('bound logical SES design differs')
    if sx.one(tree,'was_is')!=['was_is']:raise ValueError('pin swapping refused')
    place=ONE(tree,'placement');routes=ONE(tree,'routes')
    ses.children_only(place,{'resolution','component'},1);ses.children_only(routes,{'resolution','parser','library_out','network_out'},1)
    resolution=['resolution','um','10']
    if ONE(place,'resolution')!=resolution or ONE(routes,'resolution')!=resolution or ONE(dsn,'resolution')!=resolution:raise ValueError('exact resolution required')
    if ses.placements(place,10)!=ses.placements(ONE(dsn,'placement'),1,True):raise ValueError('SES placement differs')
    parser=ONE(routes,'parser');ses.children_only(parser,{'host_cad','host_version'},1)
    if (ONE(parser,'host_version')!=['host_version','"10.0.7"'] or ONE(parser,'host_cad')!=['host_cad','"KiCad\'s Pcbnew"']):raise ValueError('SES Native host differs')
    lib=ONE(routes,'library_out');ses.children_only(lib,{'padstack'},1)
    stacks=ses.library(lib,10);allowed=ses.library(['library_out',*[copy.deepcopy(n) for n in sx.children(ONE(dsn,'library'),'padstack') if sx.unquote(n[1])=='Via[0-1]_1600:600_um']],1)
    if any(k not in allowed or v!=allowed[k] for k,v in stacks.items()):raise ValueError('SES via library differs')
    netout=ONE(routes,'network_out');ses.children_only(netout,{'net'},1)
    found=[];removed=[];paths=Counter();vias=0;seen=set()
    for net in sx.children(netout,'net'):
        ses.children_only(net,{'wire','via'},2);name=sx.unquote(net[1])
        if name not in expected['nets'] or name in seen:raise ValueError('unknown/duplicate SES net')
        seen.add(name)
        for wire in sx.children(net,'wire'):
            ses.children_only(wire,{'path','polygon','type'},1);poly=sx.one(wire,'polygon');path=sx.one(wire,'path')
            if bool(poly)==bool(path) or sx.one(wire,'type') not in (None,['type','protect']):raise ValueError('unexpected SES wire')
            if poly:
                # Pinned SesWriter.writeConductionArea omits fixed-state/type.
                # USER_FIXED is verified independently in the loaded-board witness.
                if poly[2]!='0' or sx.one(wire,'type') is not None:raise ValueError('synthetic SES area aperture/grammar differs')
                found.append((name,sx.unquote(poly[1]),area.canonical_ring(ses.pairs(poly[3:],10))))
                removed.append((netout.index(net),net.index(wire),copy.deepcopy(wire)))
            else:
                if sx.unquote(path[1]) not in ('top_layer','bottom_layer') or ses.number(path[2])/10!=500:raise ValueError('source trace layer/width differs')
                paths.update(ses.segments(name,sx.unquote(path[1]),ses.number(path[2])/10,ses.pairs(path[3:],10)))
        for via in sx.children(net,'via'):
            ses.children_only(via,{'type'},4)
            if (area.imported_name(sx.unquote(via[1])) not in stacks or sx.one(via,'type') not in (None,['type','protect'])):raise ValueError('unknown via stack/fixed state')
            for atom in via[2:4]:ses.number(atom)
            vias+=1
    wanted=[(a['net'],a['layer'],area.canonical_ring(a['ring_um'])) for a in expected['areas']]
    if len(found)!=2 or Counter(found)!=Counter(wanted):raise ValueError('exact two generated areas required')
    original=Counter()
    for wire in sx.children(ONE(dsn,'wiring'),'wire'):
        path=sx.one(wire,'path')
        if path:original.update(ses.segments(sx.unquote(ONE(wire,'net')[1]),sx.unquote(path[1]),ses.number(path[2]),ses.pairs(path[3:])))
    if not expected['generated'] and (paths!=original or vias):raise ValueError('prewired SES route survival differs')
    for ni,wi,_ in sorted(removed,reverse=True):del netout[ni][wi]
    reverse=copy.deepcopy(tree);back=ONE(ONE(reverse,'routes'),'network_out')
    for ni,wi,wire in sorted(removed):back[ni].insert(wi,wire)
    if reverse!=before:raise ValueError('non-area SES edit')
    output=(sx.dump(tree)+'\n').encode()
    return output,dict(schema=1,raw_ses_sha256=area.sha(raw),import_ses_sha256=area.sha(output),synthetic_areas_removed=2,other_AST_exact=True,reference_routes_exact=not expected['generated'],paths=len(paths),vias=vias,production_admitted=False)
