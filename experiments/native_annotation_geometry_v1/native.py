"""Narrow caller-supplied Native glyph/ring capture; no execution authority.

Project-owned code.  Uses the pinned 10.0.7 owned-polygon getter seam, never
raw SHAPE child pointers.  Source/Native census, pose and final DRC remain the
caller's responsibility.  Known unsupported geometry may use a strict bbox
fallback; malformed evidence and unexpected Native failures must not do so.
"""
import math

from autorouter.padless_alias_native import polygons
from .ring import MAX_NM, MAX_OUTLINES, MAX_POINTS

ERROR_NM = 1000


class UnsupportedGeometry(ValueError):
    """A known unsupported geometry/style/population, never missing evidence."""


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def _int(value, *, minimum=-MAX_NM, maximum=MAX_NM):
    _need(type(value) is int and minimum <= value <= maximum,
          'Exact bounded Native integer required')
    return value


def _xy(value):
    return [_int(value.x), _int(value.y)]


def _anchor(value):
    _need(type(value) is list and len(value) == 2, 'Exact owner anchor required')
    return [_int(n) for n in value]


def _relative(point, anchor):
    return [_int(point[i] - anchor[i]) for i in range(2)]


def _bool(value):
    _need(type(value) is bool, 'Exact Native Boolean required')
    return value


def _text(value):
    _need(type(value) is str, 'Actual Native text string required')
    return value


def capture_text(item, pcbnew, anchor_nm):
    """Capture a conservative default-font ink superset in owner coordinates.

    Holes are intentionally filled.  Only the exact Native outward contours
    are returned, without cropping, resampling or a new polygon approximation.
    Native RuntimeError/AttributeError and malformed getter data propagate.
    """
    anchor = _anchor(anchor_nm)
    if not isinstance(item, pcbnew.PCB_TEXT):
        raise UnsupportedGeometry('Only PCB text glyph geometry is supported')
    visible, knockout = _bool(item.IsVisible()), _bool(item.IsKnockout())
    font = _text(item.GetFontName())
    bold, italic, mirror = (_bool(getter()) for getter in (item.IsBold, item.IsItalic, item.IsMirrored))
    raw, shown = _text(item.GetText()), _text(item.GetShownText(True))
    angle = item.GetTextAngleDegrees()
    _need(type(angle) in (int, float) and math.isfinite(angle), 'Finite Native text angle required')
    if (not visible or knockout or font != '' or bold or italic or mirror
            or not raw or len(raw) > 256 or shown != raw
            or any(ord(char) < 32 or ord(char) == 127 for char in raw)
            or abs(angle) > 360 or angle % 90 != 0):
        raise UnsupportedGeometry('Only visible plain default-font fixed-cardinal text is supported')
    pen = _int(item.GetEffectiveTextPenWidth(), minimum=1)
    if pen > 10_000_000:
        raise UnsupportedGeometry('Glyph effective pen width exceeds the supported bound')
    poly = pcbnew.SHAPE_POLY_SET()  # Keep this owner alive through both reads.
    item.TransformTextToPolySet(poly, 0, ERROR_NM, pcbnew.ERROR_OUTSIDE)
    count = _int(poly.OutlineCount(), minimum=0)
    arcs = _int(poly.ArcCount(), minimum=0)
    if not 1 <= count <= MAX_OUTLINES or arcs != 0:
        raise UnsupportedGeometry('Bounded nonempty straight glyph contours required')
    total = holes_count = 0
    exact = []

    def points(line):
        nonlocal total
        length = _int(line.PointCount(), minimum=0)
        if length < 3 or total + length > MAX_POINTS:
            raise UnsupportedGeometry('Glyph contour vertex population unsupported')
        total += length
        return [_xy(line.CPoint(index)) for index in range(length)]

    for index in range(count):
        holes = _int(poly.HoleCount(index), minimum=0)
        if holes_count + holes > 64:
            raise UnsupportedGeometry('Glyph hole population unsupported')
        holes_count += holes
        exact.append(dict(outer=points(poly.COutline(index)),
                          holes=[points(poly.CHole(index, hole)) for hole in range(holes)]))
    # Reuse the already Native-real reader, with stricter type/size preflight.
    # Compare its second read to the exact first read to reject mutation/coercion.
    detached = polygons(poly, strict=True)
    final_arcs = _int(poly.ArcCount(), minimum=0)
    _need(detached == exact and final_arcs == 0, 'Native glyph contours changed during detachment')
    return dict(kind='default-text-outer-polygons-v1', error_nm=ERROR_NM,
                outer_contours_nm=[[_relative(point, anchor) for point in row['outer']]
                                   for row in detached],
                holes_filled=True, holes_count=holes_count, font_name='', text=raw,
                effective_pen_width_nm=pen)


def capture_circle(item, pcbnew, anchor_nm, source_row):
    """Recheck one independently sourced unfilled circle before narrowphase."""
    anchor = _anchor(anchor_nm)
    _need(type(source_row) is dict, 'Exact source circle witness required')
    _need(type(source_row.get('kind')) is str, 'Exact source circle kind required')
    if source_row.get('kind') != 'fp_circle':
        raise UnsupportedGeometry('Only full footprint circle geometry is supported')
    if not isinstance(item, pcbnew.PCB_SHAPE) or item.GetShape() != pcbnew.SHAPE_T_CIRCLE:
        raise ValueError('Native source circle kind differs')
    fill = source_row.get('fill')
    _need(fill in ('none', 'solid'), 'Exact source circle fill required')
    native_fill = item.GetFillMode()
    expected_fill = pcbnew.FILL_T_NO_FILL if fill == 'none' else pcbnew.FILL_T_FILLED_SHAPE
    _need(type(native_fill) is int and native_fill == expected_fill, 'Native source circle fill differs')
    if fill != 'none':
        raise UnsupportedGeometry('Only unfilled circles are supported')
    _need(type(source_row.get('stroke_type')) is str, 'Exact source circle stroke style required')
    if source_row.get('stroke_type') not in ('default', 'solid'):
        raise UnsupportedGeometry('Only solid circle stroke style is supported')
    _need(source_row.get('layer') == 'F.SilkS' and item.GetLayer() == pcbnew.F_SilkS,
          'Native source circle layer differs')
    _need(type(source_row.get('uuid')) is str and str(item.m_Uuid.AsString()) == source_row['uuid'],
          'Native source circle identity differs')
    locked = _bool(item.IsLocked())
    _need(type(source_row.get('locked')) is bool and locked == source_row['locked'],
          'Native source circle lock differs')
    center, end = _xy(item.GetStart()), _xy(item.GetEnd())
    radius = _int(item.GetRadius(), minimum=1)
    width = _int(item.GetWidth(), minimum=0)
    for key, value in (('center_nm', center), ('end_nm', end)):
        supplied = source_row.get(key)
        _need(type(supplied) is list and len(supplied) == 2
              and all(type(n) is int for n in supplied) and supplied == value,
              'Native source circle coordinates differ')
    squared = sum((end[i] - center[i]) ** 2 for i in range(2))
    root = math.isqrt(squared)
    source_radius = root + int(root * root != squared)
    _need(type(source_row.get('radius_nm')) is int and source_row['radius_nm'] == source_radius
          and abs(source_radius - radius) <= 1
          and type(source_row.get('stroke_nm')) is int and source_row['stroke_nm'] == width,
          'Native source circle radius/stroke differs')
    _need(center != end, 'Nonzero source circle radius required')
    if not 0 < width <= 10_000_000:
        raise UnsupportedGeometry('Positive bounded circle stroke is required')
    return dict(kind='unfilled-circle-v1', center_nm=_relative(center, anchor),
                end_nm=_relative(end, anchor), stroke_nm=width)
