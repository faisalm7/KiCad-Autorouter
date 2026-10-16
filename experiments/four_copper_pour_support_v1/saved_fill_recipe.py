"""Pure preparation for two owned Native saved-fill controls; no Native calls.

SPDX-License-Identifier: GPL-3.0-or-later
Use the shared pour-audit action/reader; this is not a second validator.
"""
import copy
from decimal import Decimal
from autorouter import sexpr as sx, pipeline as p, pour_rule_area as pour
SOURCE_SHA='bfddd155b80c0e9a86bbacd5490986047bca77f694810a62e91db6c3c3dc999d'
SAVED_SHA='26b451d3ef65dd7027e46ad5267781b0f002468ec8be6da4d807d9d5880f8e04'

def prepare(original_bytes,saved_bytes):
    """Return source-preserving candidate and only-derived-fill negative bytes."""
    if not all(isinstance(raw,bytes) and len(raw)<=4*1024*1024 for raw in (original_bytes,saved_bytes)):
        raise ValueError('bounded immutable board bytes required')
    if pour.sha(original_bytes)!=SOURCE_SHA or pour.sha(saved_bytes)!=SAVED_SHA:
        raise ValueError('exact observed owned source/saved input required')
    original=sx.parse(original_bytes.decode());saved=sx.parse(saved_bytes.decode())
    positive=p.transplant_fill(original,saved);areas=pour.qualify(positive)
    matrix=pour.fill_matrix(positive,areas)
    if len(areas)!=1 or [(r['layer'],r['applicable']) for r in matrix]!=[('In1.Cu',False),('In2.Cu',True)]:
        raise ValueError('exact owned two-zone inner-layer matrix required')
    if any(r['stored_fill_node_count']!=1 for r in matrix):raise ValueError('one retained filled outline per zone required')
    points=areas[0]['outlines_nm'][0];xs=sorted({p[0] for p in points});ys=sorted({p[1] for p in points})
    if len(points)!=4 or len(xs)!=2 or len(ys)!=2 or {tuple(p) for p in points}!={(x,y) for x in xs for y in ys}:
        raise ValueError('owned rectangle geometry required')
    dx=xs[1]-xs[0];dy=ys[1]-ys[0]
    if dx<=0 or dy<=0 or dx%4 or dy%4:raise ValueError('integer quarter inset required')
    x1,x2=xs[0]+dx//4,xs[1]-dx//4;y1,y2=ys[0]+dy//4,ys[1]-dy//4
    mm=lambda n:format(Decimal(n)/1000000,'f')
    injected=['filled_polygon',['layer','"In2.Cu"'],['pts',*[
        ['xy',mm(x),mm(y)] for x,y in ((x1,y1),(x2,y1),(x2,y2),(x1,y2))]]]
    negative=copy.deepcopy(positive);zone=next(z for z in sx.children(negative,'zone') if pour._atom(z,'uuid')==matrix[1]['zone_uuid'])
    zone.append(copy.deepcopy(injected))
    if p.immutable(positive)!=p.immutable(original) or p.routes(positive)!=p.routes(original):raise ValueError('shared fill transplant changed source intent')
    if p.immutable(negative)!=p.immutable(original) or p.routes(negative)!=p.routes(original):raise ValueError('negative changed more than derived fill')
    restored=copy.deepcopy(negative);next(z for z in sx.children(restored,'zone') if pour._atom(z,'uuid')==matrix[1]['zone_uuid']).pop()
    if restored!=positive:raise ValueError('negative delta is not exactly one appended fill polygon')
    return {'positive':(sx.dump(positive)+'\n').encode(),'negative':(sx.dump(negative)+'\n').encode(),
        'recipe':{'source_sha256':SOURCE_SHA,'saved_sha256':SAVED_SHA,'area_uuid':areas[0]['uuid'],
                  'zone_uuid':matrix[1]['zone_uuid'],'layer':'In2.Cu','injected_node':injected,
                  'matrix':matrix,'native_executed':False,'routing_accepted':False}}
