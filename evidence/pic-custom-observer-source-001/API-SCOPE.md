# Declared API and evidence boundary

No installed native module was imported or called while preparing this draft.
The read-only declaration source was:
`/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/pcbnew.py`,
SHA256 `cd1c06c4709c653256ebd0c98c66d80cd72033767fac27c34ea01b5ec586116a`.
The controller binds these exact wrapper bytes in addition to the existing native
toolchain pins before and after the two stages and final metadata observations.

- `PAD.GetAnchorPadShape(layer)`14869; `MergePrimitivesAsPolygon(layer,poly,errorLoc)`14979;
  `TransformShapeToPolygon(poly,layer,clearance,maxError,errorLoc)`15372;
  `GetEffectivePolygon(layer,errorLoc)`15387; explicit-layer `GetShape/GetSize/GetOffset`15655–15702.
- `GetFPRelativePosition`10437; pad orientation15027; footprint orientation22772;
  pad/footprint `IsFlipped`14813/22999; `SHAPE_POLY_SET.COutline/CHole`7000/7004.
- Old `GetCustomShapeAsPolygon(layer)`15820–15824 ignores its parameter and calls
  `MergePrimitivesAsPolygon(F_Cu,...)`. It is not used.

Cached primary KiCad10.0.0 source at commit
`0feeca2a807f428ad2b3fa7c1e39625cb769f02c` already exists under
`.runs/support-scope-review-001/source/` and its source-receipt.json. No new source
download occurred. `specctra_export.cpp`543–573 merges custom primitives and
exports a convex hull;68–74 enables that choice. The exporter temporarily flips
back-side footprints, so two same-object observations bracket export. Merged
local shape, world transformed shape and effective shape are recorded separately;
they are related native algorithms, not three independent connectivity proofs.
Opaque SWIG shared-pointer access may fail. That result must remain a native
failure; the worker has no guessed/fabricated geometry fallback.

The original four unknown setting names remain in production's rejection:
`footprint_symbol_field_mismatch`(warning),`missing_tuning_profile`(warning),
`text_on_edge_cuts`(error),`track_on_post_machined_layer`(error). Their native report
keys are declared in cached drc_item.cpp210/307/66/315. The observer retains
original project settings and actual report/ignored keys; it does not call guessed
DRCE enum values, change KNOWN_CHECKS, enable schematic parity, or assert that
recognizing names proves provider execution. Central parse rejection is retained
if the actual report contains unsupported ignored-check metadata.

Pure logs001–003 preserve development failures in synthetic test construction
(missing fixture constant/README, empty pin quoting and duplicate unconnected
pin naming). Log004 passes24 controls;005 adds complete lifecycle falsifiers;
006 passes27 controls including callback/default behavior with a fake native
module. These are software controls only. No installed KiCad, engine, GUI,
network, source-project edit or production-support change was performed.

Reviewer static arithmetic also finds original JP1 copper separation about
0.2496150883mm versus its footprint clearance0.25mm, and0.06mm² overlap between
the two convex hulls. These are source-backed hypotheses, not native findings.
The complete original native report/items and raw DSN must determine whether a
fixed pad-to-pad violation prevents valid routing under unchanged constraints.
If confirmed, stop qualification or report infeasibility; never move pads, trim
polygons, relax clearance or count a clean-looking engine route as acceptance.
