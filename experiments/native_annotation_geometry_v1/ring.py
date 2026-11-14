"""Conservative filled-contour/full-circle-ring separation in exact integers.

Contours must already conservatively enclose actual glyph material. Each is a
simple connected filled outer polygon, implicitly closed; holes are filled, never
subtracted. This module does not obtain or qualify Native geometry. An unknown
or overlapping result cannot establish a physical collision or design approval.
"""
from math import isqrt

POLICY = 'outward-filled-contours-vs-full-circle-ring-v1'
MAX_NM = 2_000_000_000
MAX_OUTLINES = 64
MAX_POINTS = 4096
MAX_PAIR_TESTS = 250_000


def _need(ok, why):
    if not ok: raise ValueError(why)


def _integer(value, lower, upper):
    _need(type(value) is int and lower <= value <= upper, 'Bounded exact integer required')
    return value


def _point(value):
    _need(type(value) is list and len(value) == 2, 'Exact XY list required')
    return tuple(_integer(n, -MAX_NM, MAX_NM) for n in value)


def _cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def _on(a, b, p):
    return (_cross(a, b, p) == 0 and min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def _intersect(a, b, c, d):
    x, y, z, w = _cross(a,b,c), _cross(a,b,d), _cross(c,d,a), _cross(c,d,b)
    return ((x*y < 0 and z*w < 0) or _on(a,b,c) or _on(a,b,d)
            or _on(c,d,a) or _on(c,d,b))


def _polygon(raw, work):
    _need(type(raw) is list and 3 <= len(raw) <= MAX_POINTS, 'Nonempty bounded contour required')
    points = [_point(p) for p in raw]
    _need(len(set(points)) == len(points), 'Repeated contour vertex unsupported')
    n = len(points)
    _need(sum(points[i][0]*points[(i+1)%n][1]-points[(i+1)%n][0]*points[i][1]
              for i in range(n)) != 0, 'Degenerate contour refused')
    for i, p in enumerate(points):
        a, b = points[i-1], points[(i+1)%n]
        if _cross(a, p, b) == 0:
            _need((p[0]-a[0])*(b[0]-p[0])+(p[1]-a[1])*(b[1]-p[1]) > 0,
                  'Contour doubles back')
    edges = [(points[i], points[(i+1)%n], i) for i in range(n)]
    edges.sort(key=lambda edge: min(edge[0][0], edge[1][0]))
    active = []
    for a, b, i in edges:
        left = min(a[0], b[0])
        active = [e for e in active if max(e[0][0], e[1][0]) >= left]
        for c, d, j in active:
            work[0] += 1
            _need(work[0] <= MAX_PAIR_TESTS, 'Contour intersection work limit exceeded')
            if (i-j) % n in (1, n-1): continue
            if max(a[1], b[1]) < min(c[1], d[1]) or max(c[1], d[1]) < min(a[1], b[1]): continue
            _need(not _intersect(a,b,c,d), 'Non-simple contour refused')
        active.append((a,b,i))
    return points


def _inside(p, points):
    """Exact parity test, including boundary, without ray division."""
    result = False
    for i, a in enumerate(points):
        b = points[(i+1) % len(points)]
        if _on(a,b,p): return True
        if (a[1] > p[1]) != (b[1] > p[1]):
            side = _cross(a,b,p)
            if (side > 0) == (b[1] > a[1]): result = not result
    return result


def _beyond_segment(p, a, b, squared):
    """Whether exact squared point/segment distance is strictly greater."""
    x, y = a[0]-p[0], a[1]-p[1]
    dx, dy = b[0]-a[0], b[1]-a[1]
    length = dx*dx+dy*dy
    projection = -(x*dx+y*dy)
    if projection <= 0: return x*x+y*y > squared
    if projection >= length:
        x, y = b[0]-p[0], b[1]-p[1]
        return x*x+y*y > squared
    determinant = x*dy-y*dx
    return determinant*determinant > squared*length


def separate(outlines, center_nm, radius_squared_nm2, stroke_nm, clearance_nm):
    """Return CLEAR only for a conservative exact separation proof.

    Radius interval is [floor(sqrt(r2))-1, ceil(sqrt(r2))+1]; odd stroke
    halves round outward. All polygon/circle extrema must remain in +/-2e9nm.
    Tangency is never CLEAR. Work-limit exhaustion refuses the whole input.
    """
    _need(type(outlines) is list and 1 <= len(outlines) <= MAX_OUTLINES, 'Outer contours required')
    _need(all(type(row) is list for row in outlines)
          and sum(map(len,outlines)) <= MAX_POINTS, 'Bounded contour population required')
    center = _point(center_nm)
    squared = _integer(radius_squared_nm2, 1, MAX_NM*MAX_NM)
    stroke = _integer(stroke_nm, 1, MAX_NM)
    clearance = _integer(clearance_nm, 0, MAX_NM)
    root = isqrt(squared)
    lower, upper = root-1, root+(root*root != squared)+1
    half = (stroke+1)//2
    inner, outer = max(0,lower-half-clearance), upper+half+clearance
    _need(all(abs(n)+outer <= MAX_NM for n in center), 'Expanded circle bounds unsupported')
    work = [0]
    polygons = [_polygon(row, work) for row in outlines]
    classes = []
    for points in polygons:
        inside = inner > 0 and all((x-center[0])**2+(y-center[1])**2 < inner*inner for x,y in points)
        outside = (not _inside(center, points)
            and all(_beyond_segment(center, a, points[(i+1)%len(points)], outer*outer)
                    for i,a in enumerate(points)))
        classes.append('inside-inner-hole' if inside else 'outside-outer-disk' if outside else 'not-proven-clear')
    clear = all(value != 'not-proven-clear' for value in classes)
    return dict(policy=POLICY, status='CLEAR' if clear else 'NOT_PROVEN_CLEAR', clear=clear,
        contour_classification=classes, radius_interval_nm=[lower,upper], half_stroke_ceil_nm=half,
        clearance_nm=clearance, inner_hole_nm=inner, outer_disk_nm=outer,
        holes_filled_conservatively=True, Native_concordance_proven=False, design_approval=False)
