"""Pure fixed owned-fixture geometry only. No native calls, routing or support gate."""
from fractions import Fraction
from math import sqrt

MM=1_000_000
CONVEX=((1000000,0),(500000,-750000),(-500000,-750000),(-500000,750000),(500000,750000))
CONCAVE=((500000,-750000),(-650000,-750000),(-150000,0),(-650000,750000),(500000,750000))
ANCHOR=((-150000,-150000),(150000,-150000),(150000,150000),(-150000,150000))
WIDTH=500000

def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def dot(a,b):return a[0]*b[0]+a[1]*b[1]
def sub(a,b):return (a[0]-b[0],a[1]-b[1])
def edges(poly):return list(zip(poly,poly[1:]+poly[:1]))
def on(a,b,p):return cross(a,b,p)==0 and all(min(a[i],b[i])<=p[i]<=max(a[i],b[i]) for i in (0,1))
def inside(poly,p,*,boundary=True):
    winding=0
    for a,b in edges(poly):
        if on(a,b,p):return boundary
        if a[1]<=p[1]<b[1] and cross(a,b,p)>0:winding+=1
        if b[1]<=p[1]<a[1] and cross(a,b,p)<0:winding-=1
    return winding!=0

def distance2(p,a,b):
    v=sub(b,a);w=sub(p,a);norm=dot(v,v)
    if not norm:return Fraction(dot(w,w))
    t=max(Fraction(0),min(Fraction(1),Fraction(dot(w,v),norm)))
    delta=(w[0]-t*v[0],w[1]-t*v[1]);return dot(delta,delta)
def intersects(a,b,c,d):
    if any((on(a,b,p) for p in (c,d))) or any((on(c,d,p) for p in (a,b))):return True
    return cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0

def segment_gap2(a,b,poly):
    if inside(poly,a) or inside(poly,b):return Fraction(0)
    if any(intersects(a,b,c,d) for c,d in edges(poly)):return Fraction(0)
    return min(min(distance2(a,c,d),distance2(b,c,d),distance2(c,a,b),distance2(d,a,b)) for c,d in edges(poly))
def hull(poly):
    points=sorted(set(poly));lo=[];hi=[]
    for p in points:
        while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(points):
        while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return tuple(lo[:-1]+hi[:-1])
def move(poly,at):return tuple((p[0]+at[0],p[1]+at[1]) for p in poly)
def transform(p,variant):
    if variant=='front0':return tuple(p)
    if variant=='back90':return (40*MM-p[1],40*MM-p[0])
    raise ValueError('unknown fixed fixture transform')
def scene(case,variant='front0'):
    if case not in ('positive','false_hull','foreign_intrusion'):raise ValueError('unknown fixed control')
    pads=[{'id':'CONVEX','net':'CONTACT','at':(10*MM,15*MM),'polygon':move(CONVEX,(10*MM,15*MM))},
          {'id':'CONCAVE','net':'CONTACT','at':(20*MM,15*MM),'polygon':move(CONCAVE,(20*MM,15*MM))},
          {'id':'FOREIGN_A','net':'FOREIGN','at':(20*MM,6*MM),'round_diameter_nm':1500000},
          {'id':'FOREIGN_B','net':'FOREIGN','at':(20*MM,9*MM),'round_diameter_nm':1500000}]
    tracks=[{'id':'CONTACT_TRACK','net':'CONTACT','start':(10500000,15250000),'end':(19400000,15*MM) if case=='false_hull' else (20*MM,15500000),'width_nm':WIDTH},
            {'id':'FOREIGN_TRACK','net':'FOREIGN','start':pads[2]['at'],'end':(20*MM,14400000) if case=='foreign_intrusion' else pads[3]['at'],'width_nm':WIDTH}]
    for pad in pads:
        pad['at']=transform(pad['at'],variant)
        if 'polygon' in pad:pad['polygon']=tuple(transform(p,variant) for p in pad['polygon'])
    for track in tracks:
        for key in ('start','end'):track[key]=transform(track[key],variant)
    return {'schema':1,'fixture_role':'owned exposed diagnostic geometry, not a routed corpus member','case':case,'variant':variant,'units':'integer nanometres',
            'copper_layer':'F.Cu' if variant=='front0' else 'B.Cu','board_outline':[transform(p,variant) for p in ((0,0),(40*MM,0),(40*MM,30*MM),(0,30*MM))],
            'pads':pads,'tracks':tracks,'native_executed':False,'routing_accepted':False,'custom_pad_support_qualified':False}

def analytic(case,variant):
    s=scene(case,variant);pad=s['pads'][1];track=s['tracks'][0]
    gap2=segment_gap2(track['start'],track['end'],pad['polygon']);h=hull(pad['polygon'])
    return {'case':case,'variant':variant,'track_end_inside_native_polygon':inside(pad['polygon'],track['end'],boundary=False),
            'track_end_inside_export_hull':inside(h,track['end'],boundary=False),'centerline_to_pad_squared_nm':str(gap2),
            'capsule_to_pad_gap_nm':sqrt(gap2)-WIDTH/2 if gap2 else None,
            'claim':'Analytic fixture geometry only; exact native world polygon and DRC outcomes still required.'}
