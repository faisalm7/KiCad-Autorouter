# Geometry qualification 001 — retained unsupported result

This is ignored, exposed-development research. It changes no original source, rule, candidate, probe001 file, production gate or engine configuration. There were no native/solver jobs. No qualified scene or routing acceptance is emitted.

## Bound input and completed observations

The lead's successful read-only native-export-001 reports 1.350178 seconds wall / 0.900378 measured CPU, no API errors, and unchanged original inputs. Its geometry SHA256 is `d4ee4b89bce2ef798dda2c47176dbefe5188c0199c2a76e5cfded22c8dba0088`, bound to failed003 board `922c6ce93556732940b5bccc06794c84b35fd164f86abd0ac3f6faf5b76e3f41` and project `b9908a96e6113e6e51f488482108dc87aa5d9bcd838f9e3345c85e0db09bffa9`. The probe has 379 pads, 35 vias, and 27 filled outlines; its existing geometry-only local selection picked two outlines. Indices below identify evidence, never algorithmic choices.

`diagnose.py` independently examined 166,752 nonadjacent edge pairs in outline17 and 2,015 in outline20. Neither has exact crossings/touches. Both have nonadjacent edge separation squared exactly **4/17 nm²**, about **0.48507125 nm**, despite no repeated vertices. The complete retained JSON includes exact segments, rational squared distances, all 352 physical round holes, every selected-body/hole classification and a 32-file probe inventory. The runtime was 1.4394 seconds; all inventoried probe bytes remained unchanged.

There are 317 positive round pad holes and 35 positive via holes on the observed layer. No positive drill slot is present. The other 62 pads have no positive hole. At a fixed margin of 10,000 nm, outline17 has 348 strictly external drill disks and four boundary-ambiguous disks; outline20 has 351 strictly external disks and one boundary-ambiguous disk. There are no strictly internal drill disks. Each ambiguous circle extends approximately 0.30048449 nm across the saved polygon boundary. The sole outline20 case is the target drill; outline17's four cases are distinct GND PTH terminals. The exact identifiers and distances are stored in `diagnosis.json`.

Therefore the earlier whole-body assumption—every drill disk strictly outside or strictly interior and separated by a positive margin—is **unsupported**. Original `native_self_intersecting=true` and `drills_accounted_for=false` observations remain unchanged.

## Exact primary-source interpretation

Pinned KiCad10 source revision: `0feeca2a807f428ad2b3fa7c1e39625cb769f02c`. `source-manifest.json` stores actual URLs, content hashes and sizes; total downloaded source text was 263,477 bytes. One guessed SWIG source URL returned HTTP404 and is retained as a failed lookup; no source scripts were executed.

- [SHAPE_POLY_SET::IsPolygonSelfIntersecting](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/libs/kimath/src/geometry/shape_poly_set.cpp#L486) returns a native **bool**. It compares nonadjacent segments via `SEG::Collide(..., 0)`. This is the function the exporter actually called. The initial optional/SWIG suspicion was disproved by inspection and must not be repeated as an explanation.
- [SEG::Collide](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/libs/kimath/src/geometry/seg.cpp#L542) accepts exact intersections or an endpoint-to-segment squared distance rounded to zero.
- [SEG::SquaredDistance](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/libs/kimath/src/geometry/seg.cpp#L714) calculates projected squared distance then rounds it to an integer. `4/17` rounds to zero. Thus native `true` is consistent with KiCad's integer collision semantics even where an exact rational planar test has no crossing. It does not certify useful copper topology.
- The separate [SHAPE_LINE_CHAIN::SelfIntersecting](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/libs/kimath/src/geometry/shape_line_chain.cpp#L2102) returns an optional intersection. The installed Python wrapper exposes that optional signature, but this method was **not** used in probe001.

## Smaller path certificate and two bounded attempts

`copper_path.py` is a new, unintegrated pure module. It uses integer orientation and exact rational squared-distance comparisons. A certified straight leg requires both endpoints strictly inside the supplied saved contour, distance from **every** boundary segment strictly greater than the declared margin, and distance from **every** physical drill disk strictly greater than radius plus margin. A path's terminal point must lie strictly in the corresponding concentric round PTH annulus. The procedure tries a straight path before at most one bend. It does not infer global component connectivity or assert that two saved outline indices are independent electrical components.

The margin was fixed **before** the first search as `max(native_max_error_nm, 1 nm)`, giving 10 µm on this board. This provides a positive-width geometric witness outside the native polygon approximation scale. It does not establish ampacity, a manufacturable minimum route width, or suitability of the original copper neck. Proposed new tracks would still use the native effective class width, and the entire bridge would require independent original-rule native refill/DRC plus final-hash validation. No native success follows merely from a saved-fill path.

The module's 12 pure controls passed: positive leg, exact sub-nm distance, hole crossing, boundary tangency, concavity, narrow neck, all-hole census participation, one-bend positive path, deliberately blocked search, 37° rotation plus translation, winding reversal and operation-cap rejection. These are geometry tests, not PCB correctness evidence.

Both attempt scripts derive the local frame, width, net, target, other terminal identities and contour candidates solely from native geometry. They use 33×33 pad-local lattice candidates, at most eight strict interior anchors per body, eight annular samples, twelve geometrically ranked one-bend waypoints per path and at most four returned bridge proposals. A different UUID for the same footprint+pad number cannot count as another terminal. Unsupported pads are excluded from anchor candidacy; every physical drill remains in the clearance census regardless of pad/net qualification.

- `path-attempt-001.json`: 0.7167 seconds, 1,823,268 charged operations, cap 2M/8s. It considered the four nearest supported other terminals. It found eight source-anchor→target-annulus paths and no destination path. This exposed a restrictive candidate-selection gap: the nearest terminals did not necessarily contact the destination body.
- `path-attempt-002.json`: 0.8103 seconds, 2,034,212 charged operations, predeclared cap 4M/8s. It first filters for actual in-body annular sample membership, then considers the nearest four contact terminals. All four contact terminals in outline17 were tested; no other-terminal annular sample contacts outline20. The result remains eight source paths and **zero destination paths**. No cap was hit and no candidate was qualified.

The source and module bytes for both attempts remain present and hash-bound in their receipts. `attempt_paths_v2.py` is a development revision with a different declared operation cap, not a retrospectively altered first attempt. The waypoint construction and sorting remain bounded by the fixed 2,048 selected-vertex cap; the cooperative deadline is not an OS hard limit.

## Current limit and next decision

Failure of this finite search does not prove that no safe copper path exists. It means the proposed straight/one-bend, twelve-waypoint certificate did not find one under its declared margin and candidate caps. Do not enlarge the search or reduce the margin silently. The older whole-body kernel still cannot receive a qualified scene from these observations.

Before any production reuse, make the path-domain and receipt checks self-contained: verify the native geometry/report/source hashes, bind the exact all-hole census, reject unsupported curved/explicit-hole contours, and verify no proper contour crossings or ambiguous fill winding. The actual selected contours have already passed the exact crossing check in `diagnosis.json`, but the experimental path module alone does not authenticate that result. It is not a standalone production acceptance API.

A lead may next compare a separately declared, bounded multi-leg witness finder or inspect why the twelve candidate bends fail. Such a finder would remain only a proposal mechanism. Any emitted bridge needs new disposable-copy native validation and post-refill path recertification; existing counterfactual bridge evidence does not qualify this unexecuted generalized method.

## Graph003: bounded positive diagnostic, still unqualified

After a write freeze and the lead's verified full archive/restore at `1af0325` (all refs and 22,327 non-Git files), the lead authorized one further saved-geometry diagnostic. The exact predeclared script SHA256 was `5724f0e72db1f2a5f78bd4abfc3466f1e45252cd35aa69478d234ec930701387`; it was not changed after backup or before execution.

`attempt_graph_v3.py` uses at most 64 nodes and 2,016 candidate edges per selected body, an eight-second cooperative deadline and 12M charged-operation cap. It preserves the old physical-distance corner/chord waypoint construction, distributes up to 64 valid nodes by deterministic farthest-point coverage seeded by local anchors and terminal witnesses, and tests every visibility edge with the existing exact path-leg certificate. Dijkstra selects a shorter certified path. This expands geometric coverage without decreasing the 10 µm margin. IDs and net names are not ranking inputs.

Independent review had reproduced two material gaps in v2's hypothetical positive wrapper: a bridge could cross a hole between the two filled bodies, and a native target/body net mismatch could be accepted. V3 adds complete bridge centerline/drill checks, native target UUID uniqueness and net checks, selected body zone/layer/net/index checks, exact contour crossing checks, charged waypoint work and a final deadline check. Its 12 additional pure controls pass, including the actual reviewer counterexamples, duplicate logical terminal rejection, renamed identities, polygon order/winding and bounded-operation rejection. Old v1/v2 source/result bytes remain unchanged.

Actual retained `path-attempt-003.json` result:

- Four diagnostic candidate bridges; no native/solver execution, native routing acceptance, qualified scene or qualified whole-body flags.
- Wall time **3.059757 seconds** and **6,005,645 charged operations**. Separate measured CPU was not recorded for this pure diagnostic, so it is not suitable for equal-budget comparative cost claims.
- Each selected body used 64 nodes and all 2,016 bounded candidate edges. Outline17 accepted 518 edges and found 64 destination annulus paths, up to five legs; outline20 accepted 1,666 edges and found eight one-leg target paths.
- All 352 physical holes participated. 456 candidate bridge/path combinations were rejected by the additional bridge centerline/drill test.
- First bridge is `(149.995,72.140) → (150.120,73.640)` mm, width 0.5 mm on B.Cu, length 1.505199 mm. It reaches a distinct logical terminal through existing saved copper; the destination witness is `(150.120,73.640) → (150.562717,78.249409) → (157.726091,92.321091)` mm, ending in the other pad's positive annulus. This particular witness has **one bend**. Therefore the prior no-certificate results came from the restrictive twelve-waypoint ranking; they did not establish that more than one bend was necessary.

The four candidates' exact integer coordinates and path witnesses are in the receipt for lead review, not hardcoded into the algorithm. They are exposed development proposals. There is no end-to-end quality/completion result and no demonstration that the native thermal rule accepts any of them yet.

Remaining blockers before trusting/promoting a certificate:

1. `binding_verified=true` in graph003 means consistency with the **historical saved native-export summary**, not fresh authentication of current source/candidate/project/report bytes. A real trial must freshly rebind those inputs before and after execution, bind the final refilled board, and recertify paths against that final geometry. The lead already retains the complete original receipt; this pure result does not replace it.
2. The diagnostic wrapper still needs fail-closed rejection of negative physical pad-hole dimensions and nonpositive native maximum-error values before general use. Actual retained observations contain healthy positive holes and `native_max_error_nm=10000`; this gap does not change this stored diagnostic but is not acceptable as a generic production precondition.
3. Bridge checking currently proves a positive-margin **centerline** corridor outside holes, not full-width new-copper clearance to all foreign conductors, board edges, keepouts or constraints. Original-rule native DRC/refill is required, along with any extra geometry qualification needed by the final policy.
4. The path certificate demonstrates saved-copper path existence to distinct logical terminal annuli. It does not prove a new global electrical component merge, thermal/current capacity, manufacturing readiness, unchanged topology after refill, or a fair end-to-end improvement.

Probe001 is preserved byte-for-byte. The lead owns the review and any fresh native trial; this agent performed no native execution.
