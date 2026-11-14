# Exact glyph-contour/circle-ring prototype

This isolated experiment proves conservative separation of already outward
glyph polygons from an unfilled full-circle stroke. It does not obtain Native
glyph geometry or alter placement acceptance, source090, DRC or any runtime.

`ring.separate(outlines, center_nm, radius_squared_nm2, stroke_nm, clearance_nm)`
uses integer nanometres only. Contours are simple connected filled outer
polygons, represented by distinct vertices with an implicit closing edge.
Any holes are filled conservatively; there is no hole subtraction. Inputs
are not trusted to have come from KiCad. A caller must independently establish
that each contour encloses actual glyph material and that the full circle,
stroke and clearance describe the actual unchanged Native objects.

The radius interval is `[isqrt(r²)-1, ceil_sqrt(r²)+1]`; half stroke rounds
outward. Clearance further shrinks the inner hole and expands the outer disk.
Every polygon must be strictly inside that hole or strictly outside that disk.
The outside proof checks exact point/segment squared-distance inequalities and
rejects a polygon enclosing the circle. Tangency never returns `CLEAR`.
`NOT_PROVEN_CLEAR` does not prove a real collision. Invalid, non-simple,
degenerate, unknown or over-limit input raises `ValueError`.

Limits: coordinates and expanded circle bounds within ±2e9 nm; 1–64 outlines,
4096 total vertices, and 250000 candidate edge-pair checks for contour
simplicity. Work-limit exhaustion refuses rather than approximates. No float
geometry, external dependencies, Native, model, process or file API is used by
the predicate. Tests are pure owned synthetic geometry, not Native concordance.

Run the focused tests with the existing bounded runner around:

```sh
.venv/bin/python -B -m unittest experiments.native_annotation_geometry_v1.test_ring
```

Before product use, test actual pinned Native outward glyph contours and the
actual full-circle getter/formatter mapping. Include a text contour wholly in
the unfilled circle's hole despite overlapping bounding boxes, a true stroke
crossing, tangency/near-boundary positive and negative controls, and a polygon
enclosing the circle. Keep full actual Native DRC and source/candidate checks;
this pure predicate grants no engineering or approval authority.
