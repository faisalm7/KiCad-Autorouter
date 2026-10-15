# Explicit 10.0.7 pipeline source review

Scope: current modified `autorouter/pipeline.py` and `autorouter/floor_route.py`, narrowed to explicit route propagation, shared retained reader, reconstruction, process census and publication. No source edits, Git, project imports, tests, Native/engine, network or delegation. Only this excluded review directory was written.

## Findings

1. **Default-class task audit omission — fixed during review.** Initial producer exported a native class map when either a named policy or explicit toolchain existed, but assigned `netclass_task_audit` only under `if policy is not None`. Explicit reader required that audit for Default too. The newly authored fixture has Default policy None, so otherwise valid explicit output would invalidate on final shared readback. Lead was notified; source now uses `if policy is not None or native_toolchain is not None` for the task audit. This is source-confirmed correction, not a test pass.

2. **Late PRL metadata remains outside explicit publication freshness.** `route`'s guarded-publication `stable` checks manifest and byte inventories. Shared checker validates real PRL flags/events through `check_normal_policy`, `check_event` and `check_drc_stage`, but the explicit-reader tail subsequently reads process journals, tool manifests and whole-tree inventories. Final publication stable does not replay PRL flags/events. Setting a nonzero flag on the restored PRL during these late reads preserves every byte hash and can survive accepted publication. The prior snapshot source and Native stage bindings are intact; this is a late mutable-metadata gap. Reuse existing normal policy/field PRL replay through final guarded publication. Do not weaken the protected-file policy or substitute byte equality for immutable flags.

3. **Explicit context validation precedes the route's cost origin.** At function entry `experimental_route_record(nt, True)` hashes/validates three Native binary paths through `experimental_parity_policy -> experimental_native_version -> nt.check`. `operation_started`/`operation_cpu` are assigned afterward. Thus that explicit setup cost is absent from the route receipt's own wall/CPU budget. An outer controller can independently charge it, but the route API receipt is not literally whole-call accounting. If claiming whole-call caps, sample entry clocks before context construction and retain the existing inherited preference clocks. No measured duration or comparative effect is claimed.

## Narrow checks with no additional blocker found

- Caller-selected typed/pinned context controls version and worker argv; receipt markers cannot select a runtime. Default reader rejects experimental marker presence; explicit path bypasses production scoped cache.
- Current marker check uses canonical nested equality and an integer schema requirement, avoiding Python bool/int equality in nested context. Experimental preferences/selected/floor/tuned/scoring combinations reject before route setup.
- Normal default Job call shape remains separate; explicitly scoped Job carries actual tools and full-parity opt-in. Native worker prefix appears consistent with producer/checker ordering.
- Exact pre-refill source is retained. Explicit shared reader reconstructs original routing task, strict protected SES import, saved Native refill and final original-shell candidate. It checks all three actual DRC stages with the shared stage checker.
- Final Native parity is required by complete source SCH, with complete field proof when actual field findings exist. Source/refill producer stages are nonparity; the expected eight base workers plus optional final field workers matches that chosen execution path. Missing/extra/duplicate steps reject.
- `f.publish` accepts the caller-selected shared checker; default fallback stays available. It archives/clears accepted on exception or cancellation and enforces final remaining budget. Material/source/snapshot rechecks are now ordered with the full experimental evidence inventory last.
- No acceptance, transport support, actual process result, or generalized migration claim follows from this source review. Parser-context dependency fixes were inspected only at touched call surfaces; no full parser audit repeated.

## Suggested targeted reproductions (not executed)

See `REPRODUCTION.md`. These are source-level control plans, not claimed actual failures. In particular, test the Default producer/reader pairing with the integrated owned fixture after dependencies are ready; a static branch-count test alone is not routing evidence.

Observed wall through this note preparation: 210.981 seconds. Whole CPU was not instrumented and is unknown. No extra external spending.


Lead is addressing both remaining findings with entry wall/CPU sampling and shared final PRL replay. Important correction: retained PRL flags must be restored to zero. The late metadata fault is setting a nonzero flag (or changing link count), not clearing the worker-time immutable flag. `test_late_publication_metadata_draft.py` proposes one actual route-stable AST + shared publisher + existing NormalPolicyReceipt filesystem control, with positive and post-reader flag cases. It borrows setup methods only; its explicit-version checker seam is explicitly synthetic. Syntax parsed only; not executed or adopted.
