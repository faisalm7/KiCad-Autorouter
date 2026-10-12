# Original PIC schematic-field parity diagnostic

Prospective, ROOT-only native diagnostic. The draft has run only pure and explicitly fake-native tests. No KiCad, Java, compiler, engine, GUI, netlist export or network operation ran while preparing it. No production support gate changes. The frozen source/recipe proposal remains separately preserved in `.runs/pic-parity-controls-proposal-001`.

The fixed order is:

1. Complete unchanged original15-file PIC copy with actual schematic parity enabled.
2. A complete copy with one hidden `AutorouterDiagnosticParity=PIC_FIELD_MATCH_001` field added to both the existing R1 schematic instance and existing R1 footprint.
3. The same complete field-matched project with only that PCB field's value changed to `PIC_FIELD_MISMATCH_001`.

A failed original or matched positive stops the sequence. Every later row remains `not_attempted`; there is no alternate target or recipe. Original/project/rules/schematic circuit/copper/pads/routes/zones remain unchanged. Only copied board/schematic metadata receives the declared field. There is no stand-in schematic, library rewrite, saved board or migration. Reference R1 and exact symbol/footprint identities, field spelling/value/hidden presentation and deterministic new field UUID are fixed in `fixture.py` and `PROTOCOL.json`. Source-span insertion is verified by a complete AST comparison; the negative is an exact one-value byte substitution relative to the positive.

The target negative is a **warning**, because the unchanged original project declares it so. It must be exactly one `footprint_symbol_field_mismatch` in raw `schematic_parity`, with the exact R1 footprint UUID and provider-generated field/value description, and no exclusion. This diagnostic distinguishes that expected warning from unrelated findings; it never changes the report or severity and never marks a routed board accepted. The pinned provider tests fields present in the schematic; a PCB-only added field would be an invalid negative.

## Actual-execution gate

The lead first captures, publishes and checkpoints the exact current CLI help under `evidence/pic-parity-cli-help-001`. Its reviewed actual bytes confirm `--schematic-parity`, SHA256 `da7c7fa31fb2f5a2cf44fca62031f1e619fcf8607146c94d030b205b8f326998`. The helper requires that report/log, pinned CLI identity and successful help-process metadata. It does not run help automatically or omit an unavailable flag.

After independent review, promote exactly these seven files to `experiments/pic_parity_controls_v1/`, commit, push and verify the source before ROOT runs:

```sh
python3 -B experiments/pic_parity_controls_v1/driver.py --run-native --output .runs/pic-parity-controls-001
```

This command is unexecuted. The helper requires every helper, all core modules reported by `tool_manifest`, tool lock, source acquisition manifest and CLI-help bytes to equal their committed HEAD blobs before starting native work. An ignored uncommitted draft cannot satisfy that check. No original input is changed. Output must be a fresh direct `.runs` directory. One shared foreground experiment lock prevents competing native jobs.

Each case has one exact sandboxed CLI DRC call with `--format json --severity-all --all-track-errors --refill-zones --schematic-parity --exit-code-violations`. It omits `--save-board`, uses complete source project copies under the same `pic_programmer` basename, and retains the child schematic/local libraries. Existing FloorJob initialization isolates config/cache/documents; this helper also isolates HOME/TMP and sets C locale. Process argv, cwd, cleanup, status/exit, log length/nontruncation and resource settings are checked against the retained process file and step. Accepted process exits are0 or5 according to the actual complete report, since warnings can produce5.

## Bound evidence and exact comparison

`f.read_json` provides bounded strict JSON (duplicate/nonfinite rejection). `native_summary.parse_data` copies the production `parse_report` validation/count body **unchanged**, omitting only its initial pathname read so it can consume captured strict data without an unbounded second reopen. At preparation time and in a pure test, AST equality with the production function's remaining body is required. It imports the live pinned production Rejected/KNOWN_CHECKS/CRITICAL_CHECKS constants. No parser schema/count change is claimed. Local field classification lives in `checks.py`, separate from that parser.

Raw report, log and process file hashes freeze before parsing. The binding records the complete case project before/after and `saved=false`; the shared production guard requires every copied original file to remain byte-identical and permits only a newly created `pic_programmer.kicad_prl`. The complete after-inventory is recorded and subsequently must remain exact. All three report arrays, full raw severities/excluded flags, ignored checks and actual native counters remain present. The parity-enabled log count must exist once and match the raw array, and explicit missing-netlist/annotation/skip diagnostics reject. Empty parity without this evidence is not a positive.

Positive cases need zero parity items and ordinary native-policy acceptance. Later cases must retain every ordinary finding from case1. Comparison sorts canonical **whole records** only: field values, descriptions, UUIDs/positions, severities/excluded flags and duplicate multiplicity are preserved. Native ordering alone may change; adding/removing/changing a finding fails. The effective ignored set remains the original observed four keys; it includes the native default `track_not_centered_on_via` absent from the three explicit original ignored keys. The source/project inventory remains authoritative. No existing source warning is erased from the record.

Reused foundations are the reviewed `pic_severity_controls_v1/driver.py` source/blob/path helpers and publication structure, production FloorJob/runner/process-check/bounded I/O, and original production report counting. The parity controller removes the unrelated six-case native observer and supplies one direct nonsaving parity stage. Its final current-material check follows subprocess-bearing tool observations and final output scans; a direct local HEAD/ref witness supplements tool metadata. Completed stages/cases are never rebased. Every final binding and local predicate is rederived from retained raw data. Cancellation/write/staleness/cap failure vacates a canonical positive and preserves invalidated evidence; signal handlers restore.

## Bounds and interpretation

One60-second wall/full SELF-plus-waited-CHILDREN CPU budget covers preparation, copies, native stages, metadata and final checks from controller experiment start. Each native stage gets at most30 seconds and the remaining overall budget. The summary explicitly samples before publication; final caps include publication checks. The lead should retain an outer process execution receipt for startup-inclusive duration/exit/CPU. Output is capped at20 MiB; three planned project copies are bounded by `3*(1,366,598+4096)` bytes plus code/config/report reserve. Child log cap256 KiB, observed group RSS2 GiB. Polling and post-stage/final CPU rejection are not hard OS quotas or atomic concurrency guarantees.

`routing_accepted`, `geometry_qualified`, `format_support_qualified`, `production_support_changed`, `schematic_parity_qualified`, `new_engine_execution`, and `board_saved` stay false. `controls_passed` is only this fixed three-case diagnostic. Native hierarchy annotation, actual custom-field netlist propagation and original parity are unobserved until ROOT runs. If a prerequisite fails, preserve it; do not normalize the original circuit or relax the expected outcome.

## Pure checks and attribution

```sh
python3 -B -m unittest discover -s .runs/pic-parity-controls-draft-001 -p test_controls.py -v
```

Final preparation:29 controls passed in29.656 seconds (`pure-controls-003.log`). Tests use actual immutable source bytes and complete scratch copies, but replace the native runner and committed-metadata acquisition for lifecycle controls. They do not establish native correctness. Controls include strict parser-body parity, exact source deltas, wrong targets/duplicates/hidden-field rejection, missing parity coverage, exact target/type/severity/value/UUID/exclusion, ordering equivalence with full-record loss/change rejection, process/log/guard mutation, prerequisite stop, raw mutation after parsing, crash/cancellation, final canonical/budget errors and real self-SIGINT/TERM handler restoration. Earlier26-control source/log is retained under `snapshots/pre-hardening-001`; intermediate and final logs are never overwritten.

Original PIC files and any emitted derivative geometry/metadata remain CC BY-SA4.0 under the already retained original demo grant/notices. Project-authored diagnostic software is GPL-3.0. This draft distributes no original board, library, model, binary or third-party implementation source. Original source is development-exposed; these three cases are not new independent families, a holdout, a completion comparison or C novelty.

Integration amendment, October 11: the independent reviewer reproduced an accepted stale source-rule mutation during the final HEAD read. Material checks now sample HEAD before all source, helper, tool and output bytes. The exact regression uses an owned complete source copy; the frozen original draft and failing evidence remain unchanged. Native execution is still pending.

The known native `.kicad_prl` behavior is established by original observation002. The parity helper now reuses `pipeline.check_drc_project`, also used by production DRC and receipt checks, instead of an incompatible stricter file-set assumption. Existing PRL files cannot change; all new files except the one exact local-state basename reject. This does not admit any original geometry, rule, schematic or project-setting change.
