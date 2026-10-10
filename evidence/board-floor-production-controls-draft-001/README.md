# Production floor validation controls — unexecuted native draft

The driver tests the exact accepted production fixture from `.runs/board-floor-production-native-001/result.json`, candidate SHA `79c46687d355a60f3917794f277ef41fb839088622123784dddc55c13e23af06`. It does not run an engine or route a new project. No native execution has occurred in this draft; 23 pure controls pass in 0.055 seconds (`pure-tests-002.log`). The earlier pure pass is retained. `--help` was checked without native work.

Five cases share one 60-second wall and measured parent + waited-child CPU ceiling:

| Case | Exact controlled change | Required diagnostic observation | Required production outcome |
|---|---|---|---|
| positive | None | Zero opens/blocking/warnings/exclusions | Full `validate_candidate` with frozen guidance contract passes; exact candidate hash unchanged |
| narrow_track | Longest original generated segment width 0.3→0.2 mm | `track_width` error on its UUID, no opens/exclusions | Exact generated-track contract rejection, before native stages |
| small_via | Only generated via diameter 1.5→0.6 mm; drill stays 0.3 | `via_diameter` error on its UUID, no opens/exclusions; other native findings retained | Exact derived-via contract rejection, before native stages |
| missing_via | Delete only required SIGNAL_A via | Opens and `unconnected_items` error containing both original adjacent track UUIDs; no exclusions | Full native validation returns rejected opens, exact prepared candidate hash unchanged |
| changed_rule | Only project `track_width` severity error→warning | Still zero findings | Frozen original-project/context contract rejects, before native stages |

Each case receives two separate complete project copies: one for independent actual DRC, one for current production `validate_candidate(..., guidance_contract=...)`. Original source and positive evidence remain immutable. Required native/raw report/process/candidate/input hashes, exact changed fields, unchanged ignored-check metadata, final policy/context and all steps are retained. No original rule, protected copper or geometry is altered. The rule mutation exists only in its intentionally invalid copies.

At invocation, the driver verifies the accepted positive receipt and pins its full evidence tree, source tree, code and tools; current implementation/tool-file hashes must equal the positive's. A later docs-only Git HEAD is allowed at start but recorded and must remain unchanged during execution. Snapshots and all completed case trees are checked again before and after canonical summary publication. A stale input, signal, cap crossing, bad readback or failed correction cannot leave a canonical positive summary. Partial/invalidated receipts are retained. SIGINT/SIGTERM only cancel owned work; the shared foreground lock prevents concurrent benchmark execution. All native children use existing production runner and network-denial sandbox. CPU is a measured acceptance cap, not a hard OS aggregate quota; stored totals precede the explicitly charged final publication/freshness checks.

Only the lead should run the native command after a stable checkpoint, with no other native job and a new output:

```sh
python3 -B .runs/board-floor-production-controls-draft-001/test_driver.py
python3 -B .runs/board-floor-production-controls-draft-001/driver.py --run-native --out .runs/board-floor-production-controls-001
```

The native missing-via finding must actually reference the specified adjacent routes; that expectation is not yet qualified by execution. If the actual checker identifies different items, retain the failed invocation and inspect it before changing the recipe. Missing/open outputs are never accepted. Native diagnostic cleanliness on changed-rule copies is not production validity. Even all expected outcomes passing would qualify only these five fixture controls; it would not establish broad routing completion, native cancellation, a matched comparison, whole-project integration or physical/electrical safety.

Pure controls exercise exact real fixture mutations, real current pure `validate_contract` on all five variants, malformed/incorrect native identities and severities, final budget/cancellation/readback/correction-failure invalidation, path guards and explicit invocation. They deliberately substitute publication faults; they are not mocked evidence of KiCad correctness.
