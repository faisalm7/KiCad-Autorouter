# Four-case local-clearance diagnostic review

No execution blocker found in the frozen diagnostic source. This review used
source bytes, exact rational fixture geometry and synthetic reports only. It ran
no native process, JVM, routing engine or network access and changed no tracked
source. The four native outcomes remain prospective.

| Case | Foreign track end y | Exact copper gap | CONCAVE override | Expected native result |
|---|---:|---:|---:|---|
| class_290_positive | 13.71 mm | 290 µm | absent | positive |
| override_260_positive | 13.74 mm | 260 µm | 250 µm | positive |
| class_260_negative | 13.74 mm | 260 µm | absent | one targeted clearance error |
| override_240_negative | 13.76 mm | 240 µm | 250 µm | one targeted clearance error |

The equal-geometry 260 µm pair differs in exactly one footprint clearance node.
The other pairs change only the foreign-track endpoint. Both original foreign
terminals remain on that track. Its capsule remains 840–890 µm from the target
anchor and at least 1.239 mm from the other-net contact track. Thus the proposed
test approaches the true custom pad's straight top edge rather than the anchor
or another route. Geometry and UUID census precede DRC interpretation.

The unchanged original project maps VCC to POWER (800 µm preferred width,
280 µm clearance), and FOREIGN to Default (500/250 µm). The observer requires
these exact loaded class rows, original floors, complete four-pad/two-track
mapping and both native custom polygons. The 500 µm route width remains fixed;
this does not claim equality to POWER's preferred width. All 15 acquired original
files remained byte-identical during review.

Both negatives require their corresponding positive and exactly one unexcluded
`clearance` error with the CONCAVE/FOREIGN_TRACK UUID pair. Independent synthetic
falsifiers rejected a shorting-only finding, mask companion, wrong pair, open,
unknown-provider warning, critical padstack warning and missing ignored key.
The original explicit three ignored keys remain distinguished from the four
observed effective keys. No severity admission or production support changed.

Four existing focused test methods passed in 0.088 seconds. The source pins and
pure arithmetic/predicate results are in `review.json`; reproduction is
`python3 -B .runs/pic-local-clearance-design-review-001/review.py`. No full suite
was repeated. The old six-case protocol still compares exactly. Shared process,
publication, capture, source-binding and resource helper ASTs are unchanged;
new final checks regenerate each exact recipe/board hash. The existing 180-second
wall/full-CPU and 32 MiB bounds remain. Eight full-project copies reserve
10,932,784 bytes before code, reports and the existing safety reserve.

This tests one footprint override against one Default foreign track. It adds no
independent native `GetLocalClearance` readback: exact authored AST, loaded class
metadata and the four pairwise native outcomes are the proposed evidence. It
cannot qualify pad-local precedence, competing local overrides, floor clamping,
arbitrary reflection, Freerouting/SES equivalence or routing acceptance. Final
freshness checks are finite samples, not atomic authentication. Unexpected
native errors or warnings must remain visible; no post-result threshold change
or companion-error waiver is justified by this review.

Frozen source: driver `73ba94e96da9debd4736e14a5bdd6c64934985979008b0756dc58175d1237da0`,
checks `57eaf5cd29fc57d46b34413a090e9cd2d02f6a70516ea7dd1cdf825e3c25bdf5`,
clearance helper `5b43480e42d3d50b1c2e3de7c4aca2a3debf8262e0fbd4e7918f078bbcc9333f`,
protocol `67309eb4c6e38ef87b8d0a9689c66b9ef97d03721f4cf5d9a96924d8d44ed551`.
