"""Fixed experimental DSN clearance planning; never native rule observations.

The unmodified input must pass the original floor export audit. Only three
existing clearance atom values change. Source geometry/rules and width/via
values remain unchanged. 20um is a hypothesis, not a guaranteed geometry bound.
"""
from __future__ import annotations
import copy,hashlib,json,sys
from pathlib import Path
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT))
from autorouter import board_floor as g,sexpr as sx

PRESETS={
 'placement-search-v2-margin0-default':(0,'via_default',50,5),
 'placement-search-v2-margin20um-default':(20000,'via_default',50,5),
 'placement-search-v2-margin20um-via-low':(20000,'via_low',25,3),
}


def parameters(policy):
    if not isinstance(policy,str) or policy not in PRESETS:raise ValueError('unknown fixed search diagnostic policy')
    margin,variant,via,plane=PRESETS[policy]
    return {'clearance_margin_nm':margin,'scoring_variant':variant,'via_costs':via,'plane_via_costs':plane}


def clearance_nodes(tree):
    # Full original grammar/identity is audited before these exact addresses.
    rule=sx.one(sx.one(tree,'structure'),'rule')
    classes=sx.children(sx.one(tree,'network'),'class')
    if len(classes)!=1:raise ValueError('one original class required')
    return [rule[2],rule[3],sx.one(classes[0],'rule')[2]]


def expected_tree(original,context,policy):
    settings=parameters(policy);g.audit_export(original,context,guided=True)
    result=copy.deepcopy(original);value=context['derived_nm']['clearance_nm']+settings['clearance_margin_nm']
    for node in clearance_nodes(result):node[1]=g.atom_um(value)
    return result


def verify_edit(original,planned,context,policy):
    expected=expected_tree(original,context,policy)
    if planned!=expected:raise ValueError('nondeclared planning DSN atom or geometry change')
    # Restore only the three edited atoms and repeat the original audit. Never
    # fabricate a native context or replace the original floor dimension contract.
    restored=copy.deepcopy(planned)
    for actual,before in zip(clearance_nodes(restored),clearance_nodes(original)):actual[1]=before[1]
    if restored!=original:raise ValueError('nonclearance AST differs')
    g.audit_export(restored,context,guided=True)
    return {'exact_declared_ast_change':True,'clearance_atom_count':3,'routing_accepted':False}


def transform(placement_dsn,context,policy):
    if not isinstance(placement_dsn,bytes) or not 0<len(placement_dsn)<=sx.MAX_BYTES:raise ValueError('bounded placement DSN bytes required')
    original=g._parse_dsn(placement_dsn.decode('utf-8'));settings=parameters(policy)
    planned=expected_tree(original,context,policy);audit=verify_edit(original,planned,context,policy)
    encoded=g._dump_dsn(planned).encode('utf-8')
    if len(encoded)>sx.MAX_BYTES or g._parse_dsn(encoded.decode('utf-8'))!=planned:raise ValueError('planning DSN roundtrip/size failed')
    receipt={'schema':1,'policy':policy,'parameters':settings,'input_sha256':g.sha(placement_dsn),'output_sha256':g.sha(encoded),
        'original_floor_context_sha256':hashlib.sha256(json.dumps(context,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),
        'original_derived_nm':copy.deepcopy(context['derived_nm']),
        'planning_clearance_nm':context['derived_nm']['clearance_nm']+settings['clearance_margin_nm'],
        'audit':audit,'native_rules_changed':False,'routing_accepted':False,'production_qualified':False,
        'scope':'Fixed conservative engine planning parameter; no universal geometry bound; original native acceptance unchanged.'}
    return encoded,receipt
