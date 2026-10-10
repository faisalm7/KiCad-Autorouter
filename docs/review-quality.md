# Quality-strategy and receipt review

Reviewed locally on October 10, 2026. This is an independent code review of
`autorouter/strategy.py` and the review-copy boundary. The reviewer also
implemented the receipt consistency fix in `pipeline.check_result`; that fix
still requires lead integration review. No routing engine or native KiCad job
ran during this review. Filesystem/control-flow tests are not native routing
evidence, and this document makes no comparative performance claim.

## Reproduced receipt defect and correction

The pre-fix `check_result` accepted a real copied B1 result after moving its first
footprint by 10 mm and updating only the receipt's candidate digest. The unchanged
clean native report was reused. The original accepted run was
`.runs/adapter-ablation-001/combined`; the disposable reproduction is
`.runs/review-new/adapter-case`. The source project and actual accepted run were
not modified. `forgery-reproduction.json` records the before/after checks,
original result hash and implementation hash.

The attack returned `current: true` before the fix. The fixed check rejects it
with `immutable geometry changed`. Before adding the new explicit CPU-ceiling
requirement, the untouched real B1 result passed all strengthened consistency
checks. `.runs/review-new/forgery-fix-verification-final.json` records that
intermediate verification and the exact implementation hash then tested. An
earlier attempted reproduction using an older smoke receipt failed immediately
because that historic receipt lacked a native-report digest; its disposable
copy was retained rather than silently replaced.

The strengthened checker now requires:

* Unchanged source and original snapshot; exact candidate project-file inventory;
  recomputed immutable geometry; preserved locked copper, or all original copper
  for partial-completion scope.
* A final native binding to the exact candidate hash, unchanged original rules,
  and the retained actual native input directory. A candidate digest in editable
  JSON alone is insufficient.
* The raw native report, matching native summary, recorded metrics, complete
  pinned code snapshot, tool pins, exact final DRC command, process outcome, and
  matching root final-validation step. Nested trial steps with the same name do
  not substitute for the root check.
* Finite wall/CPU ceilings and consistent measured totals, with neither ceiling
  exceeded. Cancelled steps and incomplete cleanup reject qualification.

Both wall and measured CPU are now postcompletion acceptance caps in `route`.
The final receipt write is followed by a cap check; if serialization/fsync crosses
either cap, a corrective rejected receipt is saved. Stored summary totals are
sampled before that last write, as explicitly recorded. These are not hard
total-CPU preemption or complete escaped-descendant accounting guarantees. The
four-arm experiment must also record full invocation wall/self/child CPU around
the pipeline call, including metadata subprocesses and final evidence emission.

Historical receipts without `cpu_budget_seconds` now fail closed under the strict
checker. They remain historical evidence and were not rewritten to invent a
previously declared ceiling. New comparisons need fresh receipts from the frozen
implementation.

The check is **mutable local evidence consistency, not authentication**. Rewriting
an entire mutually consistent evidence set can still fabricate a history. It is
not a signature, proof of process execution, or a substitute for fresh native
validation before application. The API returns `applied: false` and states that
limitation. No live-board application was added.

Executed controls:

```sh
python3 -m unittest tests.test_result -q
# 24 passed
python3 -m unittest tests.test_result tests.test_strategy tests.test_handoff -q
# 44 passed at this review point (24 + 15 + 5)
python3 -m unittest tests.test_handoff -q
# 6 passed after the lead fixed the handoff finding below
```

The receipt controls cover the reproduced rehashed geometry attack, rehashed
route changes, locked/partial copper, snapshot/input tampering, missing bindings,
native-summary/metric inconsistencies, altered command provenance, nested final
step selection, CPU/wall ceilings, cancellation, and changed code/tool provenance.
The original real B1 report supplied the non-mocked regression described above;
the unit fixtures explicitly claim only consistency behavior.

## Strategy safety and comparison review

No blocking code flaw was identified in the final reviewed strategy after the
wall/CPU reserve changes. This is a review conclusion, not execution evidence.

The implementation starts with B1 inside the same global deadline and CPU
allowance, withholding a finalization reserve. The root parent-CPU interval
already includes nested baseline Python work; it correctly adds worker and
monitor CPU without adding the nested baseline's parent total a second time.
Every attempted trial contributes process costs. CPU reserve checks can stop
further proposals, and overruns reject the completed result. A slow or failed
trial cannot create extra comparative budget.

Only newly routed, unlocked items belonging to original copper-zone nets are
eligible for deletion. Protected original routes are checked separately. Trial
adoption requires native acceptance, non-increasing track length and via count,
at least one strict improvement, and no added warning signatures. Source hashes
are checked before adoption. Original unlocked reference routes do not select or
score proposals. Deterministic ordering is still development-specific tuning,
not evidence of held-out performance or algorithmic novelty.

Each trial has a distinct retained directory, candidate and process/native
receipts, including rejected and failed attempts. The final emitted root copy
undergoes fresh native validation and metrics; it does not merely inherit the
last trial's accepted flag. Final metrics must match the selected incumbent.
Cancellation and global budget failure reject the root result. Per-stage DRC
uses the same pipeline validation as B1.

Remaining practical limits:

* The B1 engine is still the route producer. Pruning redundant zone-net routing
  is a postprocessor hypothesis, not a claimed novel router or general victory.
* Connectivity and DRC preservation do not establish signal integrity, current
  capacity, thermal design, manufacturability under unstated constraints, or
  human PCB approval. Less track length alone does not prove those properties.
* `check_result` qualifies the final candidate's local evidence; it does not
  validate the complete comparative claim graph or every intermediate trial
  receipt. The experiment manifest and backups must retain all arms/trials and
  check their hashes before making comparative claims.
* A B2 tuned run is not an exhaustively tuned or restarted Freerouting baseline.
  Claims must name the precise B2 profile and remain limited to measured data.

## Disposable review-copy boundary

The reviewed `handoff.review_copy` rejects an existing destination, symlink
ancestors, and destinations inside either the source project or evidence run.
It copies the complete candidate project, compares hashes before and after,
and calls the strict receipt checker twice. It performs no live-editor write,
source overwrite, plugin registration, or automatic approval. On failure it
leaves a disposable partial directory without a ready receipt, avoiding deletion
of unrelated user files.

The receipt-switch finding is **resolved and re-reviewed**. The initial
implementation discarded the second checker return and captured the receipt
digest only at the end. The lead now captures the digest before the first check,
requires it unchanged after the second, compares both verified candidate
paths/digests, and checks the copied board against the verified digest before
writing `ready_for_manual_review`. The sixth handoff regression changes the real
receipt file during the second mocked checker call and verifies that no ready
receipt is emitted. All six handoff tests passed when rerun by this reviewer.
This closes the identified changed-but-valid receipt switch; the ordinary path
guards are not a hostile-process, race-free filesystem sandbox. Any saved GUI
change invalidates the original candidate validation; the handoff correctly
documents that it does not provide live stale-edit detection or undo.

## Smallest safe netclass coverage milestone

The actual retained native DSN from the accepted combined-adapter sonde run has
one `kicad_default` class, 42 net names, width 635 micrometres, clearance 254
micrometres and `Via[0-1]_1651:635_um`. Those dimensions match the source Default
class. The adapter preserves the complete DSN network subtree. This confirms
the representation for one class, not correct export of multiple classes.

`interf_u` is the smallest gate expansion among the acquired projects: its static
preflight rejects only unqualified netclass bindings. It has two literal patterns
(`GND`, `VCC`), both assigned to `Power`, no explicit assignment table, no custom
rule file and no custom pads. Its unchanged class dimensions are:

| Class | Track mm | Clearance mm | Via diameter mm | Via drill mm |
|---|---:|---:|---:|---:|
| Default | 0.4 | 0.254 | 1.4 | 0.6 |
| Power | 0.5 | 0.254 | 1.6 | 0.6 |

The installed pinned pcbnew wrapper exposes connected-item
`GetEffectiveNetClass`, `GetNetClassName`, and class width/clearance/via getters.
The next bounded milestone should export a complete copied `interf_u` project
and compare **every native resolved net-to-class mapping and geometry value**
against DSN class membership, rule values and via padstacks. Native load/export
must be tested first; these methods' presence alone does not prove correct
project loading or effective-resolution behavior. Do not implement wildcard or
priority resolution by guessing in Python.

Initially qualify only this narrow literal, unambiguous binding subset. Keep
wildcards, overlapping class priorities, custom rules, advanced vias and other
unsupported semantics gated. Preserve project/rule hashes and native terminal
mapping. Run real positive and deliberately invalid mapping/clearance/via
controls before routing, followed by original-rules refill/DRC and semantic
validation on routed output. A copied-class fallback to Default must fail the
mapping audit even if broad board minimums would let native DRC pass. In this
source, the board's minimum track/via diameters are 0.2/0.9 mm, which differ from
the class dimensions; do not conflate default routing choices with native minimum
constraints. No new source board was modified or natively exported during this
read-only feasibility review.
