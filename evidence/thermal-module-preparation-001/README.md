# Fresh thermal repair module draft

This ignored draft is for lead review and eventual promotion. It has not been executed natively. It contains no historical board coordinates, net names, pad UUIDs, source receipts, or research-script imports in the three runtime modules. The separate factoring check deliberately replays already exposed development evidence; that check is not a runtime dependency.

## Caller API and responsibilities

`autorouter.thermal.attempt_repair(parent_job, original_tree, candidate, source_hashes, protected_routes, native_summary, *, report_path, binding_path, remaining_seconds, out)` returns a dictionary. A successful repair has `validation_passed: true`, an absolute job-owned `candidate`, and exact `candidate_sha256`. Other results have no candidate and report `unsupported_reason`. It also returns trial details and geometry/proposal receipt paths. Every result retains `routing_accepted: false` and `comparison_eligible: false`: the caller owns adoption, final refill/checks, total accounting and publication.

The caller must freeze the current implementation and native tool hashes before starting the entire route, retain the complete original project in `parent_job.out/snapshot`, and keep source/code/tools unchanged through final publication. It passes a finite callback returning the smaller remaining whole-operation wall/CPU allowance after its finalization reserve. The module snapshots all implementation files and observes changes to them and source/candidate/report trees. Each native geometry/refill/map/DRC process uses an isolated Job with network denied and separate KiCad configuration; each actual step is appended once to the supplied parent's steps, including failed or cancelled steps. No incumbent steps are copied by this module. The parent must count parent CPU plus all waited-child CPU (including short metadata processes) and enforce final budget caps. Pure geometry and child launches cooperate with the callback; this is not a hard OS quota.

The caller must copy the selected candidate, run the ordinary final native pipeline, require the final board hash to equal the selected hash, and preserve source/rules before considering acceptance. Independent whole-project/physical/electrical review remains outside this proof.

## Narrow proof and native worker

The candidate must have exactly one unexcluded native `starved_thermal` error, no opens or other policy-critical finding, and pass current source preflight. `thermal_worker.py` is copied beside a fresh input directory and invoked as:

```
bundled-python -B /absolute/job/worker.py /absolute/job/input/name.kicad_pcb /absolute/job/request.json /absolute/job/geometry.json
```

The request binds every copied project file and raw DRC hash. The worker is read-only: exact KiCad 10.0.0, no save/refill/DRC/engine, actual UUID matching for one pad and zone, two copper layers and one target zone layer. It exports all pad/via holes and target-zone contours. Geometry selects at most eight nearby bodies without hardcoded body indexes. All original observation flags, including native self-intersection booleans and whole-body unsupported reasons, remain evidence. They are not overridden.

The pure module rejects slots/nonround or negative/unknown physical drills, nonpositive maximum error, offset target annuli, explicit selected polygon holes/arcs, ambiguous identities, exact contour crossings, and unsupported bounded populations. It uses integer/rational segment predicates to certify an explicit path from each proposed bridge endpoint through saved fill to a strict annular witness. The destination is a different logical terminal. Every path leg clears every contour boundary and every physical drill by more than the native maximum-error margin; the new bridge centerline separately clears all drills. This is a positive-area connectivity-path certificate, not an ampacity or newly merged global component claim. Foreign copper, the whole new track capsule, and all original rules require native validation.

The graph caps are eight seconds, 12 million charged operations, eight bodies/2,048 selected vertices, 512 pads/512 vias, 64 nodes and 2,016 edges per body, and four proposals. Each trial adds exactly one effective-class-width segment on a fresh candidate copy, then performs native refill, fresh class audit and final native DRC. Original immutable geometry and protected routes must match; all other routes must equal the incumbent plus that segment. Every saved polygon of the target zone must remain exactly unchanged, and the original witness is rechecked. Native acceptance uses the central policy and permits no new warning identity. Selected board, original project, native map/report/input and fill are rechecked during publication. Final errors/cancellation clear the candidate and preserve/vacate prior positive/partial receipts before publishing a false result.

## Validation performed

- 32 pure controls passed in `tests-002.log` (0.181 seconds). Coverage includes positive/rejected geometry, foreign-net drill crossing, strict margins/concavity, target and body identity, exact class-map binding, renamed/rotated/translated/reordered geometry, shared-budget scheduling, and ordinary/cancelled/partial publication failures. Native execution is mocked only in scheduling controls; these are not native correctness evidence.
- `factoring-001.json` replayed the actual exposed native-export-001 geometry without native jobs, reproduced all four graph003 proposals exactly, and rechecked every path. It took 3.276687 wall / 3.275160 CPU seconds. Original geometry and prior proposal hashes stayed unchanged. The earlier malformed pure fixture omitted `ignored_checks`; that failed run is retained as `tests-001-failed-fixture.log`, then the fixture was corrected.
- The earlier, separate repair-only native driver passed its first generated bridge in 5.413284 wall / 4.355851 CPU seconds. That result does not validate this new factoring or count as a fresh equal-budget route. Lead-scheduled fresh integration validation is still required.
