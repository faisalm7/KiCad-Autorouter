# Actual local-clearance001 addendum

The saved run at `1f983c1d4eacd1d37d05a1161dc3ec815cbb9d90` passes independent
readback of all four declared predicates. No native worker was rerun. The earlier
source review, its manifest and prospective wording remain unchanged.

| Case | Opens | Blocking errors | Warnings | Exclusions |
|---|---:|---:|---:|---:|
| class_290_positive | 0 | 0 | 5 | 0 |
| override_260_positive | 0 | 0 | 5 | 0 |
| class_260_negative | 0 | 1 | 5 | 0 |
| override_240_negative | 0 | 1 | 5 | 0 |

Every case has exactly four `missing_courtyard` warnings and one `track_dangling`
warning. The class negative reports required clearance 0.2800 mm and actual
0.2600 mm. The override negative names footprint CONCAVE and reports 0.2500 mm
required versus 0.2400 mm actual. Both errors target exactly the native CONCAVE
pad and FOREIGN_TRACK UUIDs. Neither is downgraded or excluded. Both corresponding
positives passed with unchanged project rules.

The existing `observation_binding(..., clearance_controls.observe)`,
`drc_binding`, `parse_report`, process checks and strict predicate all agree with
the receipt. The exact native class rows remain VCC/POWER at 800/280 µm and
FOREIGN/Default at 500/250 µm. Exact custom polygons, all four terminals, two
tracks, exporter restoration, source hashes and original-rule DRC input copies
match their frozen recipes. Source and effective ignored lists retain their
three-versus-four distinction.

All eight native stages have complete cleanup, untruncated logs and exact
network-denied argv. Observer exits are 0; DRC exits are 5 because warnings are
present even in the positives. Stored cost is 13.348006875 seconds wall and
10.586078 seconds full CPU; outer execution is 13.818080125 wall and 11.026903
waited CPU. Both are below the 180-second limits. Stored totals explicitly
precede final freshness checks; the outer measurement covers the completed
controller. Raw output is 6,932,324 bytes across 234 files, below 32 MiB.

All 37 runtime source pins match both the committed Git blobs and retained code
snapshot. Installed tool hashes and the native wrapper pin match. All 15 original
files (1,366,598 bytes) and the complete run inventory remained unchanged during
readback. The public manifest's 56 entries total 448,543 bytes: 55 source/raw
copies totaling 447,594 bytes are byte-identical, plus the authored 949-byte scope
note. The public manifest is `341e7b0fd60eb777b147b5ede31054039b64c72d85a80caf517037ef2b8e5f7d`.

This establishes these four owned native clearance controls and one explicit
footprint override under the original project. It does not establish clean whole
boards, general local-rule precedence, initialized pairwise getter semantics,
Freerouting equivalence, SES survival, production custom-pad support or routing
quality. The production gate remains closed. No blocking consistency defect was
found in this saved evidence.

Reproduction: `python3 -B .runs/pic-local-clearance-design-review-001/audit_actual.py`.
Exact reports, target records, source pins and costs are in `actual-audit.json`.
