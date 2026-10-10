# Independent policy-routing evidence audit

All 312 checks passed. No native/engine process was run. The actual retained
implementation matches commit `421ba64`, the current verifier, and both recorded
code snapshots. Full source, snapshot, candidate, saved-refill and final native
input trees; immutable geometry; reports; process receipts/log sizes; commands;
CPU/wall/RSS arithmetic; and analytic track/via metrics were checked.

- Smoke: accepted, zero findings, 90 mm and zero vias; 8.604216 wall seconds and
  5.091716 measured CPU seconds within its 60-second limits. Fresh readback of
  its stored receipt passes `check_result`.
- Multichannel: correctly rejected, 160 opens, 95 blocking findings, 138
  warnings and no exclusions; 73.187888 wall / 81.858311 CPU seconds within its
  120-second limits. The engine logged `TIMED_OUT` near its cooperative
  60-second internal limit, saved partial routing and exited normally. That is
  not a successful routing outcome. Native blockers are 75 track widths,
  13 clearances, 3 via annuli, 3 via diameters and 1 starved thermal. The original
  source had 24 clearance errors and 93 warnings. Those source findings neither
  waive candidate errors nor establish fixed-geometry impossibility.

Each current public subset contains 29 raw files, all byte-identical to the
local run: 69,488 smoke bytes and 2,945,131 multichannel bytes. Manifest hashes
and sizes match; extra scope/manifest/readback files are explicitly accounted
for. The original licensed unrouted sibling copied in `6fe00c4` matches its
unchanged local source hash and remains in Git history. It is absent from the
current public subset, and the scope note explicitly discloses its removal.
Complete original and local run trees remain unchanged.

These public subsets omit complete native inputs, source snapshots and code,
so they cannot independently execute strict `check_result`. Default-class raw
DSN before the existing in-place adapter transformation was not retained; the
stored input hash alone is not a reconstructable raw export. Final candidate
native validation and binding are independently checkable locally. Rejected
partial-route length is not an accepted-board quality result or superiority
evidence.
