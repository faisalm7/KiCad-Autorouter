"""Pure, exact changes to six previously observed owned DSNs; never mutate native input."""
import copy
import hashlib
import json
from pathlib import Path
from autorouter import sexpr as sx
from autorouter.adapter import _parse_dsn, _dump_dsn

IDS = tuple(v + '-' + c for v in ('front0', 'back90') for c in ('positive', 'false_hull', 'foreign_intrusion'))
BASIS = 'evidence/pic-custom-native-controls-002'
FILES = ('native.dsn', 'custom-pads.json', 'observation.json', 'recipe.json',
         'observe-input/pic_programmer.kicad_pcb', 'observe-input/pic_programmer.kicad_pro', 'original-drc.json')


def sha(b): return hashlib.sha256(b).hexdigest()
def exact_one(node, name):
    values = sx.children(node, name)
    if len(values) != 1: raise ValueError('exactly one ' + name + ' required')
    return values[0]
def unquote(x): return sx.unquote(x)
def coord(point):
    if len(point) != 2 or any(type(n) is not int or n % 1000 for n in point):
        raise ValueError('native integer micrometre coordinate required')
    return [point[0] // 1000, -point[1] // 1000]
def contour(value):
    if value['arc_count'] != 0 or len(value['outlines']) != 1 or value['outlines'][0]['holes']:
        raise ValueError('only the qualified simple native polygon accepted')
    row = value['outlines'][0]['outline']
    points = row['points_nm']
    if row['closed'] is not True or len(points) != 5 or len({tuple(x) for x in points}) != 5:
        raise ValueError('qualified five-vertex native contour required')
    return [coord(x) for x in points]
def canonical_ring(points):
    values = [tuple(x) for x in points]
    return min(tuple(v[i:] + v[:i]) for v in (values, list(reversed(values))) for i in range(len(v)))
def area(points):
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1]))) / 2


def derive(raw, custom, context, recipe):
    """Byte-pinned callers retain originals; this only produces a separate DSN and expectations."""
    before = _parse_dsn(raw.decode()); tree = copy.deepcopy(before)
    if custom['native_version'] != '10.0.0' or context['native_version'] != '10.0.0': raise ValueError('native pin')
    if custom['same_loaded_board'] is not True or custom['board_saved'] is not False: raise ValueError('same-load witness')
    if custom['observation_before_export'] != custom['observation_after_export']: raise ValueError('native census drift')
    if custom['dsn_sha256'] != sha(raw) or context['dsn_sha256'] != sha(raw): raise ValueError('raw DSN hash')
    if custom['board_sha256'] != context['board_sha256'] or custom['project_sha256'] != context['project_sha256']: raise ValueError('input identity')
    if custom['input_hashes_before'] != custom['input_hashes_after']: raise ValueError('original inputs changed')
    if recipe['variant'] not in ('front0','back90') or recipe['case'] not in ('positive','false_hull','foreign_intrusion'): raise ValueError('scene scope')
    variant=recipe['variant']; layer='top_layer' if variant=='front0' else 'bottom_layer'
    if len(context['pads'])!=4 or len(context['nets'])!=2 or len(context['routes'])!=2: raise ValueError('native census')
    pads=custom['observation_before_export']['pads']
    if {x['reference'] for x in pads}!={'CONVEX','CONCAVE'} or len(pads)!=2: raise ValueError('custom census')
    lib=exact_one(tree,'library'); placement=exact_one(tree,'placement'); wiring=exact_one(tree,'wiring')
    structure=exact_one(tree,'structure'); network=exact_one(tree,'network')
    if sx.children(structure,'plane') or len(sx.children(wiring,'wire'))!=2: raise ValueError('no planes; exact original two traces')
    images={unquote(x[1]):x for x in sx.children(lib,'image')}
    stacks={unquote(x[1]):x for x in sx.children(lib,'padstack')}
    places={unquote(p[1]):(unquote(comp[1]),p) for comp in sx.children(placement,'component') for p in sx.children(comp,'place')}
    if len(places)!=4 or len(images)!=3 or len(stacks)!=4: raise ValueError('library/placement census')
    netpins={unquote(n[1]):[unquote(p) for p in exact_one(n,'pins')[1:]] for n in sx.children(network,'net')}
    if netpins!={'CONTACT':['CONVEX-1','CONCAVE-1'],'FOREIGN':['FOREIGN_A-1','FOREIGN_B-1']}: raise ValueError('terminal mapping')
    edits=[]; areas=[]
    for pad in sorted(pads,key=lambda p:p['reference']):
        if (pad['anchor']!='rect' or pad['size_nm']!=[300000,300000] or pad['offset_nm']!=[0,0]
                or pad['drill_nm']!=[0,0] or pad['number']!='1' or pad['net']!='CONTACT'
                or pad['copper_layers']!=[recipe['copper_layer']]): raise ValueError('unchanged qualified anchor')
        image_name,place=places[pad['reference']]; pin=exact_one(images[image_name],'pin')
        if pin[2:]!=['1','0','0']: raise ValueError('unchanged pin identity/offset')
        stack=stacks[unquote(pin[1])]; shape=exact_one(stack,'shape')
        if shape[1][0]!='polygon' or shape[1][1]!='top_layer': raise ValueError('original custom hull')
        replacement=['shape',['rect','top_layer','-150','-150','150','150']]
        index=stack.index(shape); edits.append((stack[1],index,copy.deepcopy(shape)))
        stack[index]=replacement
        points=contour(pad['effective_world'])
        if canonical_ring(points)!=canonical_ring(contour(pad['transformed_world'])): raise ValueError('native polygon disagreement')
        polygon=['polygon',layer,'0',*[str(v) for point in points for v in point]]
        wire=['wire',polygon,['net','CONTACT'],['type','protect']]
        wiring.append(wire)
        areas.append({'reference':pad['reference'],'pad_uuid':pad['uuid'],'net':'CONTACT','layer':layer,
                      'position_um':coord(pad['position_nm']),'anchor_size_um':[300,300],
                      'area_um2':area(points),'ring_um':points,'fixed':'USER_FIXED'})
    # Reverse exactly the two shape replacements and two appended areas, then demand whole AST identity.
    reverse=copy.deepcopy(tree); rlib=exact_one(reverse,'library'); rwiring=exact_one(reverse,'wiring')
    del rwiring[-2:]
    for name,index,old in edits:
        matches=[x for x in sx.children(rlib,'padstack') if x[1]==name]
        if len(matches)!=1: raise ValueError('padstack alias')
        matches[0][index]=old
    if reverse!=before: raise ValueError('non-target DSN change')
    expected={'case':variant+'-'+recipe['case'],'variant':variant,'kind':recipe['case'],'layer':layer,'areas':areas,
              'pins':[{'reference':p['reference'],'number':p['number'],'net':p['net'],'uuid':p['uuid'],
                       'position_um':coord(p['position_nm']),
                       'padstack_name':unquote(exact_one(images[places[p['reference']][0]],'pin')[1])} for p in context['pads']],
              'net_targets':{n['name']:{'width_um':n['width_nm']/1000,'clearance_um':n['clearance_nm']/1000} for n in context['nets']},
              'tracks':[{'id':t['id'],'net':t['net'],'start_um':coord(t['start']),'end_um':coord(t['end']),
                         'width_um':t['width_nm']//1000} for t in recipe['tracks']],
              'original_raw_sha256':sha(raw),'source_board_sha256':custom['board_sha256'],
              'source_project_sha256':custom['project_sha256'],'plane_nets_expected':False,
              'connectivity_expected':recipe['case']!='false_hull'}
    derived=_dump_dsn(tree).encode()
    if _parse_dsn(derived.decode())!=tree: raise ValueError('derived DSN roundtrip')
    expected['derived_sha256']=sha(derived)
    return derived,expected


def prepare(root, read):
    summary= json.loads(read(root/ BASIS /'summary.json'))
    if summary['controls_passed'] is not True or len(summary['cases'])!=6: raise ValueError('native basis unqualified')
    cases={c['variant']+'-'+c['case']:c for c in summary['cases']}
    inputs={}; expectations=[]
    for ident in IDS:
        folder=root/BASIS/ident; raw={n:read(folder/n) for n in FILES}; recorded=cases[ident]
        for name in ('native.dsn','custom-pads.json','observation.json'):
            if sha(raw[name])!=recorded['stages']['observe'][name]: raise ValueError('native recorded stage changed')
        if sha(raw['original-drc.json'])!=recorded['stages']['original-drc']['original-drc.json']: raise ValueError('native report changed')
        custom=json.loads(raw['custom-pads.json']); context=json.loads(raw['observation.json']); recipe=json.loads(raw['recipe.json'])
        if (sha(raw['observe-input/pic_programmer.kicad_pcb'])!=custom['board_sha256']
                or sha(raw['observe-input/pic_programmer.kicad_pro'])!=custom['project_sha256']
                or sha(raw['observation.json'])!=custom['floor_context_sha256']): raise ValueError('original input/context chain')
        if recipe!=recorded['scene']: raise ValueError('native scene binding')
        derived,expected=derive(raw['native.dsn'],custom,context,recipe)
        inputs[ident+'.dsn']=derived; expectations.append(expected)
    return inputs,expectations
