# Actual layer preference qualification review

All five prospective routing cases and the separate native-clean/disallowed-layer control match their declared predicates at code832b0a1a8b6aa25e5b0e7fd3894c519d82fd870e. Four accepted receipts pass the current central checker. Original projects, saved runs, core and previews were byte-identical before/after this review. This is owned two-layer fixture qualification; it adds no board families and establishes no routing-quality or beyond-B2 gain.

| Case | Outcome | Opens / blocking / warnings / exclusions | Length / vias | Stored wall / full CPU seconds |
|---|---|---|---|---|
| Front only | Accepted | 0 / 0 / 0 / 0 | 90mm / 0 | 10.408761 / 6.016494 |
| Back only | Accepted | 0 / 0 / 0 / 0 | 90mm / 0 | 8.961210 / 5.948314 |
| Partial, new front only | Accepted, not DRC-clean | 0 / 0 / 2 / 0 | 100mm / 0 | 8.966893 / 5.759350 |
| Required via, both allowed | Accepted | 0 / 0 / 0 / 0 | 90.178029mm / 1 | 8.763199 / 5.911034 |
| Required via, front only | Rejected by native DRC | 1 / 0 / 0 / 0 | 60mm / 0 | 8.985121 / 6.630452 |
| Separate moved SIGNAL_A track | Layer guard rejects despite clean native DRC | 0 / 0 / 0 / 0 | Diagnostic only | 1.696577 / 0.772024 |

The first five cases each had120s wall and measured full-CPU caps. The separate diagnostic had60s caps. Stored routing totals are sampled before final guarded publication; outer wrapper wall/waited-child CPU observations are retained in the JSON audits and also remain below their caps. No hard total-CPU preemption claim is made.

Partial completion keeps both exact original5mm B.Cu segment nodes, including their UUIDs. Its two track_dangling warnings match the original source warnings and target those protected segments; the receipt correctly says whole_project_drc_clean=false. Generated copper stays on F.Cu. This100mm outcome must not be presented as a quality improvement over90mm whole-board routing.

The required-via fixture changes only the two declared SIGNAL_A pads/footprint layers and attributes; all project rules and other source geometry stay exact. Both-layer routing produces one through via. Front-only routing has no via and one exact missing-connection finding between the front J1 pad and back J2 pad; its rejected result and full cost remain preserved.

The separate negative changes only one generated SIGNAL_A segment from F.Cu to B.Cu on a copied accepted project. Actual unchanged-rule native DRC reports no findings, but the real production early layer guard rejects that exact UUID before touching any Job method. This distinguishes a captured layer choice from ordinary native electrical clearance/connectivity acceptance.

The audit reuses central check_result, parse_report, layer bind/audit, preference argv checks, protected-import reconstruction and the original-rule project guard. It checks raw report/candidate/source hashes, complete native-input bindings, frozen code, exact process/settings/masks, logs, unchanged ignored-check sets, budgets, preview correspondence and complete project preservation.138 accepted-case checks and38 negative checks pass.17 additional in-memory single-field controls using real accepted bytes reject changed masks, effective choices, audit hashes, null bindings and disallowed candidate copper. Original evidence was never rewritten; no native, JVM, engine, network or software-suite execution occurred in this review.

The five native ignored-check keys remain unchanged: missing_courtyard, track_not_centered_on_via, tuning_profile_track_geometries, footprint_filters_mismatch and footprint_type_mismatch. Zero reported findings is scoped to those original settings; physical/electrical design validation, schematic parity and human PCB review remain separate.

Reproduce saved-evidence checks only:

- python3 -B .runs/review-layer-native-001/audit.py NEW-accepted.json
- python3 -B .runs/review-layer-native-001/audit_negatives.py

The second command overwrites only this review's negative audit JSON; copy the script or choose a new review directory to preserve this frozen review. Raw run/source directories are read-only inputs. Public review selection excludes repeated whole code/run/project copies.

Public package evidence/layer-preferences-native-001 was independently checked: all426 manifest entries total3,143,241 bytes.425 copied raw artifacts match their original local bytes; the remaining authored summary matches all five raw receipts/costs and the negative control. Its manifest SHA256 is9dda04b374040d6d56d9d2bab072975dcee5649e7dc1be5e028d4fe6c18dfa10. Two reviewer-only key-lookup errors while reading the summary inventory were retained; they were corrected to its actual absolute-path keys. Neither error involved native execution or changed evidence.
