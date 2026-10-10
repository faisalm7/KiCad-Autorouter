"""Ignored development certificate: continuous positive-margin copper paths only.

No KiCad/solver calls; never edits boards. Integer coordinates are nanometres.
No claim about global components, ampacity, native DRC, or routing acceptance.
"""
import math
import time

class Unsupported(ValueError): pass

class Guard:
    def __init__(self, seconds=8, operations=250000):
        self.deadline=time.monotonic()+seconds; self.remaining=operations; self.used=0
    def charge(self,n=1):
        self.remaining-=n;self.used+=n
        if self.remaining<0 or time.monotonic()>self.deadline:
            raise Unsupported('bounded geometry deadline/operation cap')

def orient(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def edges(poly): return zip(poly,poly[1:]+poly[:1])
def point_sq(a,b): return sum((x-y)**2 for x,y in zip(a,b))
def on_segment(p,a,b):
    return orient(a,b,p)==0 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1])
def intersects(a,b,c,d):
    oa,ob,oc,od=orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)
    return (oa*ob<0 and oc*od<0) or (oa==0 and on_segment(c,a,b)) or (ob==0 and on_segment(d,a,b)) or (oc==0 and on_segment(a,c,d)) or (od==0 and on_segment(b,c,d))
def point_segment_sq(p,a,b):
    """Exact rational squared distance as integer (numerator, denominator)."""
    ab=(b[0]-a[0],b[1]-a[1]);ap=(p[0]-a[0],p[1]-a[1]);den=ab[0]**2+ab[1]**2
    dot=ap[0]*ab[0]+ap[1]*ab[1]
    if not den or dot<=0:return point_sq(p,a),1
    if dot>=den:return point_sq(p,b),1
    return (ab[0]*ap[1]-ab[1]*ap[0])**2,den

def farther_point_segment(p,a,b,r):
    n,d=point_segment_sq(p,a,b);return n>r*r*d

def bbox_gap_sq(a,b,c,d):
    dx=max(0,min(a[0],b[0])-max(c[0],d[0]),min(c[0],d[0])-max(a[0],b[0]))
    dy=max(0,min(a[1],b[1])-max(c[1],d[1]),min(c[1],d[1])-max(a[1],b[1]))
    return dx*dx+dy*dy

def farther_segments(a,b,c,d,r):
    if bbox_gap_sq(a,b,c,d)>r*r:return True
    if intersects(a,b,c,d):return False
    return all(farther_point_segment(p,x,y,r) for p,x,y in ((a,c,d),(b,c,d),(c,a,b),(d,a,b)))

def inside(p,poly):
    """Even-odd membership with exact integer comparisons; excludes boundary."""
    result=False;x,y=p
    for a,b in edges(poly):
        if on_segment(p,a,b):return False
        if (a[1]>y)!=(b[1]>y):
            lhs=(x-a[0])*(b[1]-a[1]);rhs=(b[0]-a[0])*(y-a[1])
            if (lhs<rhs) if b[1]>a[1] else (lhs>rhs): result=not result
    return result

def valid_point(p):
    return isinstance(p,(tuple,list)) and len(p)==2 and all(type(v) is int and abs(v)<=10**12 for v in p)

def validate_domain(poly,holes):
    if not 3<=len(poly)<=2048 or not all(valid_point(v) for v in poly):raise Unsupported('bounded integer contour required')
    if len(holes)>2048:raise Unsupported('drill population cap')
    if any(not valid_point(h['center']) or type(h['radius']) is not int or h['radius']<=0 for h in holes):raise Unsupported('only exact integer concentric round physical drills')

def certified_leg(a,b,poly,holes,margin,guard):
    if not valid_point(a) or not valid_point(b) or type(margin) is not int or margin<=0:raise Unsupported('invalid certificate coordinates or margin')
    guard.charge(2*len(poly))
    if not inside(a,poly) or not inside(b,poly):return False
    for c,d in edges(poly):
        guard.charge()
        if not farther_segments(a,b,c,d,margin):return False
    for hole in holes:
        guard.charge()
        if not farther_point_segment(hole['center'],a,b,hole['radius']+margin):return False
    return True

def annular(p,pad,margin):
    d=point_sq(p,pad['center'])
    return (pad['drill_radius']+margin)**2<d<(pad['outer_radius']-margin)**2

def path_to_annulus(anchor,pad,poly,holes,margin,waypoints,angle_degrees,guard):
    """At most eight annular samples and twelve waypoints; straight first."""
    if len(waypoints)>12:raise Unsupported('waypoint cap')
    if annular(anchor,pad,margin) and certified_leg(anchor,anchor,poly,holes,margin,guard):return [list(anchor)]
    radius=(pad['drill_radius']+pad['outer_radius'])/2
    theta=math.radians(angle_degrees)
    witnesses=[]
    for i in range(8):
        a=theta+i*math.pi/4
        p=[round(pad['center'][0]+radius*math.cos(a)),round(pad['center'][1]+radius*math.sin(a))]
        if annular(p,pad,margin) and certified_leg(p,p,poly,holes,margin,guard):witnesses.append(p)
    # Distance tie order is the pad-local angular enumeration, not world axes.
    witnesses.sort(key=lambda p:point_sq(anchor,p))
    for p in witnesses:
        if certified_leg(anchor,p,poly,holes,margin,guard):return [list(anchor),p]
    first_legs=[]
    for waypoint in waypoints:
        if list(waypoint)!=list(anchor) and certified_leg(anchor,waypoint,poly,holes,margin,guard):first_legs.append(waypoint)
    for waypoint in first_legs:
        for p in witnesses:
            if certified_leg(waypoint,p,poly,holes,margin,guard):return [list(anchor),list(waypoint),p]
    return None
