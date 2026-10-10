"""Local prospective controls only; unchanged central parser/policy is reused."""
from decimal import Decimal
from autorouter import pipeline as p
import fixture
TARGETS={'missing_tuning_profile','text_on_edge_cuts','track_on_post_machined_layer'}
# Exact pinned original layer table and native001 names, not a generic alias map.
TEXT_LAYERS={'Dwgs.User':(17,'User.Drawings'),'Edge.Cuts':(25,'Edge.Cuts'),'F.Fab':(35,'F.Fab')}
def nm(value):
    val=Decimal(str(value))*1000000
    if val!=val.to_integral_value():raise ValueError('noninteger nanometres')
    return int(val)
def keyed(rows,key):
    if not isinstance(rows,list) or len({r[key] for r in rows})!=len(rows):raise ValueError('duplicate observed identities')
    return {r[key]:r for r in rows}

def observe(native,scene,project):
    if native.get('native_version')!='10.0.0' or native.get('units')!='integer nanometres' or native.get('same_loaded_board') is not True:raise ValueError('native schema differs')
    for key in ('board_saved','dsn_exported','routing_accepted','schematic_parity_qualified'):
        if native.get(key) is not False:raise ValueError('nonsaving diagnostic scope differs')
    floors={key:nm(project['board']['design_settings']['rules'][key]) for key in ('min_track_width','min_clearance','min_via_diameter','min_through_hole_diameter','min_via_annular_width')}
    if native['floors_nm']!=floors:raise ValueError('original native floors differ')
    pads=keyed(native['pads'],'uuid');fps=keyed(native['footprints'],'uuid');routes=keyed(native['routes'],'uuid');texts=keyed(native['texts'],'uuid');nets=keyed(native['nets'],'name')
    if (len(pads),len(fps),len(routes),len(texts),set(nets))!=(4,4,2,2,{'GND','SIGNAL_A'}):raise ValueError('native scene census differs')
    for expected in scene['pads']:
        row=pads.get(expected['uuid'],{})
        if {k:row.get(k) for k in ('uuid','footprint_uuid','reference','number','net','position_nm')}!={k:expected[k] for k in ('uuid','footprint_uuid','reference','number','net','position_nm')}:raise ValueError('native terminal identity differs')
        if row.get('size_nm')!=[3000000,3000000] or row.get('drill_nm')!=[600000,600000] or row.get('layers')!=['F.Cu','B.Cu']:raise ValueError('native PTH dimensions/layers differ')
        if fps.get(expected['footprint_uuid'])!={'uuid':expected['footprint_uuid'],'reference':expected['reference'],'position_nm':expected['position_nm'],'layer':'F.Cu'}:raise ValueError('native footprint differs')
        for side in ('front','back'):
            post=row['post_machining'][side]
            if any(type(post.get(key)) is not int for key in ('mode_value','size_nm','depth_nm','angle_decidegrees')):raise ValueError('native machining scalar type differs')
            active=expected['post_machined'] and side=='front'
            if active:
                if post['mode']!='COUNTERBORE' or post['size_nm']!=1200000 or post['depth_nm']!=200000:raise ValueError('native intended counterbore differs')
            elif post['mode'] not in ('UNKNOWN','NOT_POST_MACHINED'):raise ValueError('unexpected native machining')
        if row['affected_layers']!=(['F.Cu'] if expected['post_machined'] else []):raise ValueError('native machining layer witness differs')
    expected_texts={r['uuid']:{**r,'layer_id':TEXT_LAYERS[r['layer']][0],'layer':TEXT_LAYERS[r['layer']][1]} for r in scene['texts']}
    if (routes!={r['uuid']:r for r in scene['tracks']} or texts!=expected_texts
        or any(type(r.get('layer_id')) is not int for r in texts.values())):raise ValueError('native route/text identity differs')
    classes={r['name']:r for r in project['net_settings']['classes']}
    codes=[]
    for name,class_name in (('GND','POWER'),('SIGNAL_A','Default')):
        row=nets[name];cls=classes[class_name];profile=cls['tuning_profile'] or classes['Default']['tuning_profile']
        # Actual001 shows this composite only for the declared inherited-profile
        # diagnostic. Every constituent dimension and profile remains exact.
        effective_name='POWER,Default' if scene['case']=='missing_default_profile' and name=='GND' else class_name
        expected={'name':name,'class':effective_name,'width_nm':nm(cls['track_width']),'clearance_nm':nm(cls['clearance']),'via_diameter_nm':nm(cls['via_diameter']),'via_drill_nm':nm(cls['via_drill']),
            'tuning_profile':profile,'has_tuning_profile':bool(profile)}
        if {k:row.get(k) for k in expected}!=expected or type(row.get('netcode')) is not int or row['netcode']<=0:raise ValueError('native effective class/profile differs')
        codes.append(row['netcode'])
    if len(set(codes))!=2:raise ValueError('native nets merged')
    return {'intent_and_geometry_observed':True,'native_effective_profiles':{n:row['tuning_profile'] for n,row in nets.items()},
        'post_machined_pad_uuids':[row['uuid'] for row in scene['pads'] if row['post_machined']],
        'provider_enforcement_inferred':False,'schematic_parity_qualified':False}

def summary(raw):
    findings=raw['violations']+raw['unconnected_items']+raw['schematic_parity']
    return {'opens':len(raw['unconnected_items']),'blocking':sum(r['severity']=='error' for r in raw['violations']+raw['schematic_parity']),
        'warnings':sum(r['severity']=='warning' for r in findings),'exclusions':sum(r['severity']=='exclusion' or r.get('excluded',False) for r in findings),'ignored_checks':raw['ignored_checks'],'findings':findings}

def predicate(case,native,raw,scene,ignored):
    # Raw report is immutable; rows are only classified here. A matched negative
    # NEVER turns into routing acceptance, and no changed central policy is used.
    result={'predicate_met':False,'provider_detected':False,'coverage_probe':case=='missing_default_profile',
        'coverage_outcome':None,'target_findings':[],'schematic_parity_qualified':False}
    if summary(raw)!=native:raise ValueError('raw/parsed native summary differs')
    keys=[row.get('key') for row in raw['ignored_checks']]
    if len(keys)!=len(set(keys)) or sorted(keys)!=list(ignored) or native['exclusions'] or raw['schematic_parity']:return result
    findings=native['findings']
    if any(row.get('type') not in p.KNOWN_CHECKS|{'padstack_invalid'}|TARGETS for row in findings):return result
    if native['opens'] or any(r.get('excluded',False) or r.get('severity')=='exclusion' for r in findings):return result
    target={'positive':None,'missing_named_profile':'missing_tuning_profile','missing_default_profile':'missing_tuning_profile',
        'board_edge_text':'text_on_edge_cuts','footprint_edge_text':'text_on_edge_cuts','pad_front_counterbore':'track_on_post_machined_layer'}[case]
    hits=[r for r in raw['violations'] if r['type']==target] if target else []
    result['target_findings']=hits
    if case=='positive' and any(r['type'] in TARGETS for r in findings):return result
    allowed_hits=[]
    for row in hits:
        items=row.get('items');ids=[r.get('uuid') for r in items] if isinstance(items,list) else None
        if target=='missing_tuning_profile':
            # This provider is global and deliberately has no item UUID.
            detail=row.get('description','')
            okay=(row.get('severity')=='warning' and ids==[] and isinstance(detail,str)
                and ('(Net Class: '+scene['target_class']+', Tuning Profile: '+fixture.PROFILE+')') in detail)
        elif target=='text_on_edge_cuts':
            expected=fixture.uid('boardtext' if case=='board_edge_text' else 'fptext')
            okay=row.get('severity')=='error' and ids==[expected]
        else:
            pair={fixture.uid('pad2'),fixture.uid('trackSIGNAL_A')}
            okay=row.get('severity')=='error' and ids is not None and len(ids)==2 and len(set(ids))==2 and set(ids)==pair
        if not okay:return result
        allowed_hits.append(row)
    if len(hits)>1:return result
    rest={key:( [r for r in value if r not in allowed_hits] if key=='violations' else value) for key,value in raw.items()}
    residual=summary(rest)
    if any(r['type'] in TARGETS for r in residual['findings']) or not p.native_accepted(residual):return result
    detected=len(hits)==1
    result.update(provider_detected=detected)
    if case=='missing_default_profile':
        result.update(predicate_met=True,coverage_outcome='finding_observed' if detected else 'finding_omitted_despite_loaded_intent')
    else:result['predicate_met']=(not hits if case=='positive' else detected)
    return result
