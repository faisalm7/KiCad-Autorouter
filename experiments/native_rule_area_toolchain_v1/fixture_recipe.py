"""Project-owned diagnostic areas added to one exact accepted routed fixture."""
from __future__ import annotations
import copy
from decimal import Decimal
import hashlib
from pathlib import Path
import sys
import uuid
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
from autorouter import sexpr as sx,pipeline as p,board_floor as g
BASE_SHA='79c46687d355a60f3917794f277ef41fb839088622123784dddc55c13e23af06'
PROJECT_SHA='ea1bc47355f707e1c4743af3e1c29e939bb5eaf4621c071bdac3841c43545538'
CASES=('allowed_placement','track_prohibited','via_prohibited','mixed')
FLAGS=('tracks','vias','pads','copperpour','footprints')
TARGET_SEGMENT='0661fc24-4411-4f35-ad36-9f97c4110962'
TARGET_VIA='692ddee1-7ca5-403d-9d6e-ef63ba59a986'
NAMESPACE=uuid.UUID('7068b842-e445-42b5-a96e-e0c4911190ed')


def rectangle(x1,y1,x2,y2):return [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]


def area(kind):
    specs={'allowed':(rectangle('20','19','30','21'),None,True),
           'track':(rectangle('24.5','19','25.5','21'),'tracks',False),
           'via':(rectangle('40.645','12.96','42.645','14.96'),'vias',False)}
    points,disallowed,placement=specs[kind]
    zid=str(uuid.uuid5(NAMESPACE,'placement-control-'+kind));name='diagnostic-'+kind
    flags={k:k==disallowed for k in FLAGS}
    node=['zone',['net','0'],['net_name','""'],['layers','"F.Cu"','"B.Cu"'],['uuid','"'+zid+'"'],
          ['name','"'+name+'"'],['hatch','none','0.5'],['connect_pads',['clearance','0']],['min_thickness','0.25'],
          ['filled_areas_thickness','no'],['keepout',*[[k,'not_allowed' if flags[k] else 'allowed'] for k in FLAGS]],
          ['placement',['enabled','yes' if placement else 'no'],['sheetname','"/Diagnostic/"']],
          ['fill',['thermal_gap','0.5'],['thermal_bridge_width','0.5']],['polygon',['pts',*[["xy",x,y] for x,y in points]]]]
    expected={'uuid':zid,'name':name,'parent':'board','is_rule_area':True,'placement_enabled':placement,
              'placement_source_type':'SHEETNAME','placement_source':'/Diagnostic/','disallow':flags,
              'layers':['F.Cu','B.Cu'],'outlines_nm':[[[int(Decimal(x)*1000000),int(Decimal(y)*1000000)]for x,y in points]],
              'outline_closed':[True],'holes':[0],'arc_count':0}
    return node,expected


def prepare(case,base_bytes):
    if case not in CASES:raise p.Rejected('unknown placement control case')
    if hashlib.sha256(base_bytes).hexdigest()!=BASE_SHA:raise p.Rejected('pinned accepted base candidate differs')
    base=sx.parse(base_bytes.decode())
    if sx.children(base,'zone') or any(sx.children(fp,'zone') for fp in sx.children(base,'footprint')):
        raise p.Rejected('base must have no board or footprint zones')
    routes=p.routes(base);uuids=[sx.unquote(sx.one(r,'uuid')[1])for r in routes]
    if uuids.count(TARGET_SEGMENT)!=1 or uuids.count(TARGET_VIA)!=1:raise p.Rejected('controlled route identity differs')
    seg=next(r for r in routes if sx.unquote(sx.one(r,'uuid')[1])==TARGET_SEGMENT)
    if (sx.one(seg,'start')!=['start','40','20'] or sx.one(seg,'end')!=['end','10','20'] or sx.one(seg,'layer')!=['layer','"F.Cu"']):
        raise p.Rejected('controlled track does not cross area')
    via=next(r for r in routes if sx.unquote(sx.one(r,'uuid')[1])==TARGET_VIA)
    if sx.one(via,'at')!=['at','41.645','13.96'] or sx.one(via,'size')!=['size','1.5']:
        raise p.Rejected('controlled via does not fit area')
    kinds={'allowed_placement':['allowed'],'track_prohibited':['track'],'via_prohibited':['via'],'mixed':['allowed','track','via']}[case]
    tree=copy.deepcopy(base);observations=[]
    def all_uuid(t):
        if isinstance(t,list):
            if t and t[0]=='uuid':yield sx.unquote(t[1])
            for x in t:yield from all_uuid(x)
    old=set(all_uuid(tree))
    for kind in kinds:
        node,expected=area(kind)
        if expected['uuid'] in old:raise p.Rejected('new area UUID collides with original object')
        old.add(expected['uuid']);tree.append(node);observations.append(expected)
    without=[n for n in tree if not isinstance(n,list) or not n or n[0]!='zone']
    if without!=base:raise p.Rejected('recipe modified something besides new diagnostic areas')
    targets=[]
    if 'track' in kinds:targets.append(TARGET_SEGMENT)
    if 'via' in kinds:targets.append(TARGET_VIA)
    encoded=(sx.dump(tree)+'\n').encode()
    return encoded,{'case':case,'board_sha256':hashlib.sha256(encoded).hexdigest(),'zones':observations,'prohibited_target_uuids':targets}


def verify_observation(observed,expected,*,expected_version='10.0.0'):
    if expected_version not in ('10.0.0','10.0.7'):raise p.Rejected('unknown explicitly expected native version')
    if observed.get('context_schema')!=1 or observed.get('native_version')!=expected_version or observed.get('units')!='integer nanometres':raise p.Rejected('native area context identity differs')
    if observed.get('board_saved') is not False or observed.get('routing_accepted') is not False or observed.get('adapter_transformation_performed') is not False:raise p.Rejected('unexpected native mutation/acceptance claim')
    if type(observed.get('footprint_zone_count')) is not int or observed['footprint_zone_count']!=0 or type(observed.get('footprint_rulearea_count')) is not int or observed['footprint_rulearea_count']!=0:
        raise p.Rejected('footprint area census outside fixture scope')
    rows=observed.get('zones')
    if not isinstance(rows,list) or len(rows)!=len(expected['zones']):raise p.Rejected('native zone census differs')
    # Canonical JSON avoids Python True==1 accepting wrong API types/coordinates.
    import json
    canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
    want={row['uuid']:row for row in expected['zones']};seen=set()
    for row in rows:
        if not isinstance(row,dict) or row.get('uuid') in seen or row.get('uuid') not in want:raise p.Rejected('native zone UUID differs/duplicates')
        if canonical(row)!=canonical(want[row['uuid']]):raise p.Rejected('native zone flags/placement/geometry differ')
        seen.add(row['uuid'])
    return {'passed':True,'zones':len(rows),'footprint_zones':0}


def verify_dsn(dsn_bytes,expected):
    """Observe exact exporter behavior; never remove or edit any keepout."""
    tree=g._parse_dsn(dsn_bytes.decode());structure=sx.one(tree,'structure')
    if structure is None:raise p.Rejected('export has no structure')
    keepouts=[n for n in structure if isinstance(n,list) and n and n[0] in ('keepout','wire_keepout','via_keepout')]
    bindings=[];used=[]
    for z in expected['zones']:
        flags=z['disallow'];kind='keepout' if flags['tracks']==flags['vias'] else ('wire_keepout' if flags['tracks'] else 'via_keepout')
        points=z['outlines_nm'][0]
        if any(x%1000 or y%1000 for x,y in points):raise p.Rejected('fixture needs exact micrometre coordinates')
        coords=[[x//1000,-y//1000] for x,y in points]
        for layer in z['layers']:
            node=[kind,'""',['polygon',layer,'0',*[str(x) for pt in coords+[coords[0]] for x in pt]]]
            matches=[i for i,value in enumerate(keepouts) if value==node]
            if len(matches)!=1 or matches[0] in used:raise p.Rejected('missing/ambiguous/wrong-kind native keepout')
            used.append(matches[0]);bindings.append({'zone_uuid':z['uuid'],'kind':kind,'layer':layer,'dsn_node':node,'all_flags_allowed':not any(flags.values())})
    if len(used)!=len(keepouts):raise p.Rejected('extra unmatched DSN keepout')
    return {'passed':True,'exact_bindings':bindings,'all_allowed_generic_keepouts':sum(x['all_flags_allowed'] for x in bindings),
            'genuine_restriction_keepouts':sum(not x['all_flags_allowed'] for x in bindings),'dsn_modified':False,'routing_accepted':False}
