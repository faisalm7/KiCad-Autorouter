# Placement/search v2 diagnostic draft

This draft is unexecuted and not qualified for production. It tests a fixed
conservative engine-planning parameter on the already exposed multichannel
board. It does not change original rules, pad shapes, floor context, or the
final native acceptance predicate. It is adapter/search work, not C novelty or
generalized superiority. The preceding v1 pair had160 versus8 opens and both
outputs were invalid; those historical results and runtime remain untouched.

Three fresh fixed-order arms each receive equal120-second wall and measured
CPU ceilings, with ALL shared preparation, publication and readback cost charged
to EACH arm:

1. Floor plus placement guidance, zero margin, explicit via costs50/5.
2. The same guidance,20,000nm clearance margin, explicit via costs50/5.
3. The same20,000nm margin, explicit lower via costs25/3.

This is a new matched reference, not a claim that historical implicit costs
were experimentally identical. All arms use completion-only, the same strict
no-neckdown/fanout settings, both adapter, same immutable complete project and
same native observer. One foreground lock protects the native lane. Background
desktop contention is uncontrolled and host load is recorded.

## Exact transformation and evidence

The distinct retained chain is `native.dsn` → `floor-guided.dsn` →
`placement-guided.dsn` → `pre-adapter.dsn` (planning margin) → `task.dsn`.
Each stage and its receipt is recomputed by `derive` during final readback.
The complete original native floor contract remains unchanged. `search_guidance`
first audits the placement output using that ORIGINAL context. It edits exactly
three existing clearance atom values: global, global smd_smd and class. It
compares the full resulting AST to the declared edit, restores only those atoms
and repeats the original audit. Every other AST node/atom must remain exact;
canonical serialization may normalize whitespace. Width and via copper/drill
values are untouched. Native context is never replaced by synthetic planning
observations. Explicit engine settings/argv are separately derived from the
named policy, with original native checks still authoritative.

The20µm parameter is a hypothesis, not a universal error bound. Retained exposed
board measurements found native clearances0.299394522/0.299465233mm versus DSN
polygon distances0.301629101/0.301699812mm (approximately2.235580µm inward deficit).
The exporter roundrect compensation and rounded segment count do not establish
a general max_error guarantee. A margin may help this exposed case, hurt route
completion, or still be insufficient. All outcomes must be retained.

`native_combined.py` is byte-identical to reviewed v1 SHA
`3fb123a8a1fdbe119a7de60e97677940e26a15b5562a822599d854ba04553a70`;
`placement_transform.py` is byte-identical to v1 SHA
`bfd4ff85a92ad57a9908e46904e67b1d5fce65647689e489a566d6434260fdb5`.
No getter, bound or native API changes are introduced. Existing scope continues:
board-only enabled SHEETNAME areas, all five flags explicitly allowed, one
rectangular outline, no cutouts, no footprint zones/legacy modules/genuine
prohibitions. Native keepout negative controls failed; this diagnostic cannot
admit genuine restrictions. All areas remain unchanged in the actual board.

## Execution gate and fairness

Runtime helpers, protocol, core and toolchain bytes must equal committed HEAD
and are copied into each run. Before this three-arm comparison, a NEW complete
owned fixture route with the SAME code/HEAD/tools and strongest20µm/via_low
policy must pass the actual diagnostic checker. Its exact source inventory is
pinned in the protocol. The prior v1 fixture cannot qualify this schema2 run.
The fixture receipt, evidence and EXTERNAL original source are bound throughout.

Shared setup determines one identical assigned route allowance after a5-second
final reserve. Every arm then pays its full invocation plus ALL shared actual
work; final charged caps include freshness/readback checks. CPU includes parent
and waited children, including failed work, and is a measured acceptance cap,
not a hard OS quota. Stored measurements precede final checks, as explicitly
recorded; post-check caps decide acceptance. Cancellation (SIGINT/TERM), stale
sources, changed first-completed inventories and failed canonical corrections
invalidate acceptance without losing original evidence. No background loops.

Completion and native findings are reported even when both outputs are invalid.
Pairwise margin/cost/combined length or via differences are emitted only if the
two corresponding outputs are both accepted. This is one exposed development
family, no independent-family, production, C/B2, GUI or physical validation claim.

## Pure checks and future lead-only commands

`pure-tests-002.log`:56 passing pure controls in0.338s. The12 original scope and
observer controls, wrapper accounting/publication controls and actual-file
freshness controls were adapted from v1. New controls use retained ACTUAL fixture
export/context/source bytes to derive the whole chain, reject rehashed planning
tampering and native-context relabeling, prove exactly three atom edits, and
verify explicit50/5 versus25/3 flags. Native/process stages in wrapper tests are
mocked; none of these checks establishes new native routing validity. Initial
49-control successful run is retained as `pure-tests-001.log`.

After review, promote this directory's runtime/tests/protocol/README into
`experiments/placement_diagnostic_v2`, rerun the pure controls, commit, push and
verify readback. Do not copy log/manifests into runtime unless deliberately
preserving evidence. Example commands use unused output names:

```sh
python3 -B -m unittest discover -s experiments/placement_diagnostic_v2 -p 'test_*.py'
python3 -B experiments/placement_diagnostic_v2/diagnostic_route.py --run-diagnostic --source evidence/placement-area-native-001/allowed_placement/candidate/fixture.kicad_pcb --output .runs/placement-search-fixture-001 --seconds 60 --policy placement-search-v2-margin20um-via-low
python3 -B experiments/placement_diagnostic_v2/diagnostic_route.py --check-result .runs/placement-search-fixture-001/result.json
python3 -B experiments/placement_diagnostic_v2/experiment_search.py --run-search --fixture-result .runs/placement-search-fixture-001/result.json --output .runs/placement-search-three-arm-001
```

The fixture is separate qualification work, not charged comparison work. The
three-arm job requires the successful fixture, same committed code/tool/source
freeze, one native lane and sufficient bounded storage. No new run was executed
by the draft author. No acquisition or full output tree duplication was needed.
