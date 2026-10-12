"""Four exact development controls for POWER versus a footprint override.

Uses the existing complete-project native runner and geometry observer. This is
not routing acceptance or a general custom-pad clearance implementation.
"""
import copy
from fractions import Fraction
from autorouter import pipeline as p, sexpr as sx
import fixture
import recipes
import checks

SUITE='local-clearance'
CASES={
    'class_290_positive':(290000,None,True),
    'override_260_positive':(260000,250000,True),
    'class_260_negative':(260000,None,False),
    'override_240_negative':(240000,250000,False),
}
ORDER=tuple(('front0',case) for case in CASES)
POSITIVE={
    'class_290_positive':'class_290_positive',
    'override_260_positive':'override_260_positive',
    'class_260_negative':'class_290_positive',
    'override_240_negative':'override_260_positive',
}

def prepare(original,case,variant):
    if variant!='front0' or case not in CASES:raise ValueError('unknown fixed clearance case')
    gap,override,_=CASES[case]
    raw,scene=fixture.prepare(original,'positive',variant)
    board=sx.parse(raw.decode())
    # Only the known CONTACT net becomes original-project VCC/POWER. No project
    # settings/patterns are edited, and FOREIGN still resolves to Default.
    for fp in sx.children(board,'footprint'):
        pad=sx.one(fp,'pad');net=sx.one(pad,'net')
        if net[1]=='"CONTACT"':net[1]='"VCC"'
        if sx.unquote(fp[1])=='Owned_CONCAVE' and override is not None:
            if sx.children(fp,'clearance'):raise ValueError('fixture already has local clearance')
            fp.append(['clearance',fixture.mm(override)])
    for route in p.routes(board):
        net=sx.one(route,'net')
        if net[1]=='"CONTACT"':net[1]='"VCC"'
        if net[1]=='"FOREIGN"':sx.one(route,'end')[:]=fixture.node_xy('end',(20000000,14000000-gap))
    for pad in scene['pads']:
        if pad['net']=='CONTACT':pad['net']='VCC'
    for route in scene['tracks']:
        if route['net']=='CONTACT':route['net']='VCC'
        if route['net']=='FOREIGN':route['end']=(20000000,14000000-gap)
    scene.update(case=case,suite=SUITE,gap_nm=gap,target_footprint_clearance_nm=override,
        expected_classes={'VCC':'POWER','FOREIGN':'Default'},expected_required_clearance_nm=override or 280000)
    target=next(r for r in scene['pads'] if r['id']=='CONCAVE')
    approach=next(r for r in scene['tracks'] if r['id']=='FOREIGN_TRACK')
    if recipes.segment_gap2(approach['start'],approach['end'],target['polygon'])!=Fraction((gap+250000)**2):
        raise ValueError('exact flat-edge capsule clearance differs')
    return (sx.dump(board)+'\n').encode(),scene

def observe(native,custom,raw,scene,project):
    if scene.get('suite')!=SUITE or scene.get('expected_classes')!={'VCC':'POWER','FOREIGN':'Default'}:
        raise ValueError('clearance scene scope differs')
    result=checks.observe(native,custom,raw,scene,project,expected_classes=scene['expected_classes'])
    return {**result,'clearance_scope':'One footprint override against a Default foreign track; no pad-local/both-local/floor-clamp qualification.'}

def predicate(case,native,raw,scene,ignored):
    if case not in CASES or scene.get('case')!=case:return False,[]
    if CASES[case][2]:return checks.predicate('positive',native,raw,scene,ignored)
    # Every blocking finding must be the exact tested pad/track pair. Do not
    # erase unknown providers, opens, exclusions or unrelated native findings.
    if any(type(native.get(k)) is not int or native[k]<0 for k in ('opens','blocking','warnings','exclusions')):return False,[]
    if (native['opens'] or native['exclusions'] or raw.get('unconnected_items')!=[] or raw.get('schematic_parity')!=[]
            or sorted(r['key'] for r in native.get('ignored_checks',[]))!=ignored
            or native.get('findings')!=raw.get('violations')
            or any(row.get('type') not in (p.KNOWN_CHECKS|{'padstack_invalid'}) for row in native['findings'])):return False,[]
    target=next(r['uuid'] for r in scene['pads'] if r['id']=='CONCAVE')
    route=next(r['uuid'] for r in scene['tracks'] if r['id']=='FOREIGN_TRACK')
    hits=[r for r in raw['violations'] if r.get('severity')=='error']
    if len(hits)!=1 or native['blocking']!=1:return False,[]
    hit=hits[0]
    if (hit.get('type')!='clearance' or hit.get('excluded',False) or len(hit.get('items',[]))!=2
            or {r.get('uuid') for r in hit['items']}!={target,route}):return False,[]
    clean=copy.deepcopy(native);clean.update(blocking=0,findings=[r for r in native['findings'] if r not in hits])
    return p.native_accepted(clean),copy.deepcopy(hits)

def protocol(base):
    return {**base,'name':'owned-custom-local-clearance-v1','order':[{'variant':v,'case':c} for v,c in ORDER],
        'scope':'Four front0 owned geometry controls using unchanged original PIC project rules. VCC resolves POWER; FOREIGN resolves Default. Only CONCAVE footprint gets explicit 0.25mm in two cases.',
        'cases':{name:{'gap_nm':gap,'footprint_override_nm':override,'expected_native_accepted':positive,
                       'required_paired_positive':POSITIVE[name]} for name,(gap,override,positive) in CASES.items()},
        'intrusion_predicate':'Exactly one nonexcluded clearance error with the CONCAVE/FOREIGN_TRACK UUID pair; no opens or unrelated errors. Positive uses unchanged central native_accepted.',
        'prior_exposed_run':None,'transform':'front0 only; no new reflection qualification.',
        'clearance_nm':None,'native_classes':{'VCC':'POWER','FOREIGN':'Default'},
        'claim_limit':'No routing, engine transport equivalence, pairwise generalization, pad-local precedence, multiple local overrides or board-floor clamp qualification.'}
