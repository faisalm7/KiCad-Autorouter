# Placement routing diagnostic, not a production feature

This standalone experiment tests whether exact removal of generic DSN keepouts
attributed to enabled, explicitly unrestricted placement areas changes routing.
It is an input-adapter hypothesis, not system C novelty or a stronger B2 result.
Actual fixture001 at8497654 completed source DRC and the combined observer, then
rejected before engine at a legacy empty rule-area net field. This failed run is
preserved. Engine/import/final-validation qualification remains pending.

The two arms use the same original complete project, same-load observer, floor
policy, both adapter, completion-only engine profile and actual production floor
validation. Only one arm applies the separately named placement transform. The
unchanged board still contains every original area, terminal, rule and zone.
This diagnostic emits `routing_accepted` with `production_qualified: false`;
production `autorouter check-result` deliberately does not accept this schema.

The current KiCad 10.0.0 genuine keepout controls missed track/via violations,
with and without placement nodes. Both arms therefore reject ANY genuine or
disabled rule area, footprint zone or legacy module, before engine execution.
Only enabled SHEETNAME areas with all five explicit `allowed` flags, one simple
rectangular board boundary, no cutouts and the already qualified floor scope are
admitted. It does not claim native enforcement of genuine keepout restrictions.

## Source and evidence contract

- `native_combined.py` merges the production floor observer with the actual
  native-qualified area getter loop. It loads/synchronizes once, observes both
  contexts, exports once and never saves the board. It explicitly raises the
  area footprint cap from 100 to 512 for the 114-footprint full board; all other
  area limits and the original floor schema/limits are preserved. Actual fixture001 now binds this combined invocation to the expected
  area/floor observations; full routing qualification remains pending.
- `placement_transform.py` is an exact copy of reviewed source003, SHA256
  `bfd4ff85a92ad57a9908e46904e67b1d5fce65647689e489a566d6434260fdb5`.
  Its upstream raw-to-floor provenance is independently rederived here.
- `derive` checks complete original and stripped-task file inventories, both
  native context identities and all raw→floor→optional-placement→both bytes.
  Final native acceptance reuses original floor constraints and production
  import/refill/DRC primitives. Readback reconstructs the candidate from retained
  imported routing and native fill, and checks raw final reports/processes.
- Every runtime helper, the protocol and all production modules must match
  committed HEAD before any native/engine work. Their exact bytes are retained.
  Later readback checks frozen evidence; it is consistency, not a digital
  signature against replacement of an entire deliberately forged evidence set.
- The exact owned four-pad fixture full inventory is pinned in `protocol.json`.
  Its public original bytes are at
  `evidence/placement-area-native-001/allowed_placement/candidate`. Despite this
  historical directory name, these are this fixture's immutable source inputs.
  It uses our owned copper geometry and unchanged licensed multichannel project.

## Budget, cancellation and limits

A single route uses a shared 50–120 second wall and measured total CPU ceiling;
all Python work, waited children, failed stages, hashing and final checks count.
Native child and RSS caps are the existing runner limits. CPU is a measured
acceptance cap, not a hard OS quota. The pair assigns the same allowance to each
arm after setup, reserves five seconds for final shared work, and charges ALL
shared setup/freeze/publication/readback overhead to EACH arm. It keeps failures,
reports completion separately and computes length/via differences only when
both outputs are native accepted. Stored measurements explicitly precede final
publication/freshness; actual final caps are checked again afterward.

One foreground file lock protects the native lane. SIGINT and SIGTERM request
owned-child cancellation. Canonical positive receipts and partial writes are
retained under invalidated names before correction, and removed from the
canonical name if correction itself fails. No daemon or background loop exists.
The fixed order and uncontrolled desktop background contention are recorded;
this is one exposed development board, not an independent-family experiment.

## Lead-only next execution after review and commit

The five Python files and protocol/README are committed in this folder. The
helper hash mapping is recorded at execution. After a source fix, run pure
controls, commit and verify the checkpoint, then use a fresh fixture output:

```sh
python3 -B experiments/placement_diagnostic_v1/test_diagnostic.py
python3 -B experiments/placement_diagnostic_v1/diagnostic_route.py --run-diagnostic --source evidence/placement-area-native-001/allowed_placement/candidate/fixture.kicad_pcb --output .runs/placement-routing-fixture-002 --seconds 60 --policy floor-plus-placement-diagnostic-v1
python3 -B experiments/placement_diagnostic_v1/diagnostic_route.py --check-result .runs/placement-routing-fixture-002/result.json
```

These fixture002 commands have NOT executed. Only after the
same-code fixture's actual native checks and independent readback qualify it:

```sh
python3 -B experiments/placement_diagnostic_v1/experiment_pair.py --run-pair --fixture-result .runs/placement-routing-fixture-002/result.json --output .runs/placement-routing-pair-001
```

The pair refuses a different fixture, source inventory, production/helper code,
HEAD or tools. No new engine run should start while this source is being edited.
No package/release publication, GUI qualification, physical/electrical validity,
genuine-keepout support or full system improvement is implied.

## Pure controls

`pure-tests-001.log` retains an initial test-fixture failure: a stub DSN lacked
its required string_quote declaration. It was corrected in test data only.
The final pure run is `pure-tests-007.log`: 37 controls covering narrow scope,
legacy aliases, explicit native bounds, chain tampering, exact fixture identity,
resource accounting, post-publication staleness/cancellation, failed correction
and final shared caps. Simulated stages are explicitly mocked. No new native
claim derives from these controls. Retained actual fixture files are read only.

The first frozen draft is retained unchanged in `review-snapshot-001`. Root
review corrected completed-arm inventory replacement in a `finally` block and
removed an unobserved PCB Editor state claim. A real filesystem mutation control
now proves the first completed inventory is retained through rejection.

Observer review restored the qualified 20 MiB DSN export guard before hashing:
empty, non-file, symlink and oversized exports are refused. Pure fake-export
controls use real empty/symlink files and a bounded oversize stat substitution;
one shared mock loaded object feeds both contexts. Snapshot002 retains the
preceding reviewed files. No actual native result is inferred from these tests.

Final pair freshness also binds the qualification fixture original project
outside its output directory, in addition to its retained evidence. A real
post-gate source mutation control invalidates the comparison.
