"""Only remove placement nodes from pinned actual001 prohibited-area fixtures."""
import copy,hashlib
from autorouter import pipeline as p,sexpr as sx,board_floor as g
CASES=('track_prohibited','via_prohibited','mixed')
FLAGS=('tracks','vias','pads','copperpour','footprints')

def prepare(case,board_bytes,old_expected):
    if case not in CASES or old_expected.get('case')!=case or hashlib.sha256(board_bytes).hexdigest()!=old_expected.get('board_sha256'):
        raise p.Rejected('exact actual001 source/recipe binding required')
    before=sx.parse(board_bytes.decode());after=copy.deepcopy(before);expected=copy.deepcopy(old_expected)
    rows={z['uuid']:z for z in expected['zones']};removed=[]
    for zone in sx.children(after,'zone'):
        uid=sx.unquote(sx.one(zone,'uuid')[1]);row=rows[uid]
        if any(row['disallow'].values()):
            placement=sx.one(zone,'placement')
            if placement!=['placement',['enabled','no'],['sheetname','"/Diagnostic/"']]:raise p.Rejected('unexpected original placement node')
            zone.remove(placement);removed.append({'uuid':uid,'node':copy.deepcopy(placement)})
            row.update(placement_enabled=False,placement_source_type='SHEETNAME',placement_source='')
    if len(removed)!=(2 if case=='mixed' else 1):raise p.Rejected('prohibited placement population differs')
    # Reinsertion must reconstruct every original source AST entry in its old position.
    restored=copy.deepcopy(after)
    for old,new in zip(sx.children(before,'zone'),sx.children(restored,'zone')):
        place=sx.one(old,'placement')
        if place is not None and sx.one(new,'placement') is None:new.insert(old.index(place),copy.deepcopy(place))
    if restored!=before or p.routes(after)!=p.routes(before):raise p.Rejected('changed geometry or routes beyond placement omission')
    encoded=(sx.dump(after)+'\n').encode();expected['board_sha256']=hashlib.sha256(encoded).hexdigest()
    return encoded,expected,removed

def verify_observation(observed,expected):
    if observed.get('context_schema')!=1 or observed.get('native_version')!='10.0.0' or observed.get('units')!='integer nanometres':raise p.Rejected('native area context identity differs')
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
