# Independent native board-floor geometry001 audit

**1,905 checks passed. Six executed native case predicates verified. The overall run remains invalidated.** No reviewer native or engine job was run. This review changed only its own ignored directory.

The exact source fixture, original complete project (SHA `ea1bc47355f707e1c4743af3e1c29e939bb5eaf4621c071bdac3841c43545538`), licensing files, immutable geometry, source code committed at `099cc8f72c145e43743c18c1549a7e2db36ce100`, helper copies, actual pinned tools, all 19 process receipts, completed evidence inventories, final native-input trees, final candidate/report/binding hashes, derived floors and native route readback were checked. All seven original ignored checks and original project severities remain unchanged.

| Case | Opens | Blocking errors | Warnings | Exact required native error |
|---|---:|---:|---:|---|
| Positive | 0 | 0 | 0 | None; native acceptance policy passed |
| Track width | 0 | 1 | 1 | `track_width` on the intended front segment |
| Clearance | 0 | 3 | 0 | `clearance` on the intended pair, plus two adjacent-segment findings |
| Via diameter | 0 | 2 | 0 | `via_diameter` on the intended via; secondary `annular_width` retained |
| Drill | 0 | 1 | 0 | `drill_out_of_range` on the intended via |
| Annulus | 0 | 1 | 0 | `annular_width` on the intended via |

Every case has zero exclusions. The width warning is `connection_width` and remains recorded. Seven segments plus one via were independently compared with actual native readback in every case, including exact coordinates, nets, layers, copper diameter and drill. The original loaded minima remain 0.3 mm track/clearance/through-drill/annulus and 1.5 mm via diameter. Geometry and dimensional controls satisfy the intended predicates under these unchanged settings.

The driver stored the five negative cases' `expected` values as Python tuples. JSON converts each tuple to a list. Its direct `json.loads(...) != record` comparison therefore raised `Rejected: summary changed` after native work had finished. The frozen actual `publish()` function reproduces exactly this failure with the actual retained record and no native work. The positive summary was archived and the canonical summary correctly says invalidated/controls_passed=false. Observed invalidated totals are 13.360307 seconds wall and 9.203077 seconds CPU; these are sampled before final correction writing and are not an accepted comparison budget claim.

Draft002 publication fix SHA `12d4eac8691c8abe8e382e5bbbd593c30c07e038b18d79dc30fd447c981b70cc` cleared read-only review. It compares a strict canonical JSON snapshot taken before the writer, retains duplicate/nonfinite rejection, and distinguishes Boolean from numeric values. The actual001 in-memory record now passes a pure serialization replay; strict malformed-summary probes pass. The eight new regression bodies and the author's 31-pass log were inspected; the reviewer did not rerun the author suite. No native002 claim is made: a fresh corrected run is still needed.

The first reviewer audit log is preserved with its rejected assumptions: an incorrectly guessed via enum constant and an overly strict exact refill-report comparison. The corrected audit compares actual two-layer via dimensions without guessing an enum, and compares refill/final findings by type, severity, description and target UUIDs. Native normalization changes a segment endpoint chosen for a finding position and finding order, without changing target identities or reported clearance. These were reviewer assumptions, not candidate or driver defects.

This is diagnostic capability evidence only. No engine/SES import occurred, so forced-via transport, production integration, benchmark acceptance and physical/electrical qualification remain unproven. All original actual001 evidence is unchanged.
