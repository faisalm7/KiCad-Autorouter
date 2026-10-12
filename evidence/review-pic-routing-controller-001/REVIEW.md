# PIC routing controller source review

Disposition: no remaining blocker found in the assigned controller scope at the exact reviewed snapshot hashes in `final-bindings.json`. This is an AI source review with real-file/mock-native controls. It is not solver, native DRC, GUI, electrical, or production-support qualification. ROOT subsequently reported an actual routing attempt stopping at its strict rational-coordinate comparator; that run and any proposed continuation are outside this review.

## Findings and disposition

1. **Refill lifecycle (reproduced and fixed).** The prior controller froze the working candidate before shared `validate_candidate` transplanted saved refill polygons. Its next native stage then rejected the legitimate change. `lifecycle-002/results.json` uses the actual old/current capture and stable function bodies, real shared validator and real copied board/project bytes, with native calls mocked: unchanged old output reaches the next-stage sentinel; changed old refill fails `retained evidence changed`; the corrected operation reaches the sentinel, seals the candidate even on failure, and rejects a later route-only edit. The exception is now restricted to one exact fresh candidate path during that synchronous operation; other evidence is never rebased.

2. **Requested cancellation binding (fixed).** The observation's cancel flag formerly was internally checked but not bound to the caller's requested action. The final driver requires identity equality before comparison. `boundary-003/results.json` evaluates the exact source gate against four independently valid synthetic observations: both matched modes pass and both mismatches reject. This is cancellation-mode binding, not a real process-cancellation test.

3. **Final candidate digest after sealing/metrics (fixed and tested).** The corrected continuation calls the existing exact candidate/project verifier against the native validator's returned digest immediately after the mutable context and after metrics. Actual `routing_native.execute` with mocked native stages succeeds unchanged and rejects route-only changes injected during sealing and during metrics. These are concrete sampling-boundary falsifiers; no claim of atomic exclusion of an arbitrary concurrent writer.

4. **Unsupported-source reporting (reproduced and fixed).** The first candidate-boundary positive exposed that `p.preflight` raises for PIC, rather than returning a reason list. `boundary-002/results.json` preserves the failure after successful mocked candidate validation. The final code catches only `p.Rejected` beginning `unsupported: `, records that list, and rethrows other failures. It leaves all candidate/native checks in place and `production_support_qualified=false`. The same real-file positive now reaches metrics successfully.

ROOT also corrected inherited protocol wording: planned routing/SES/native execution is separated from production/comparative qualification. Strict integer schema/effective settings/layer witnesses are present in the final comparator.

## Source and constraint review

- Exact committed helper/core and tool/API/source hashes are checked before dispatch and during final freshness sampling; cached native005, local250 and selective002 prerequisites retain their prior status, evidence inventories and separate costs. Cached observations are not fresh routing proof.
- The finite pure DSN derivation removes all 339 path wires and six ordinary vias, retaining the two custom-body polygons, original plane and other AST. The source task independently removes unlocked ordinary routes and derived fill only, preserving original project/rules and immutable source geometry. Protected original routing is unsupported here, rather than waived.
- New generated-mode SES checking requires an empty native/DSN seed, exact placement/library/polygon grammar and exact engine-to-SES new route geometry. It does not relabel failed retained-route precision obligations.
- Native continuation uses original project bytes, raw import/DRC, immutable checks, shared refill/netclass-target/final DRC, exact final candidate digest and metrics. Top-level diagnostic status is distinct from production admission. Generated route native equivalence is not asserted merely from the engine JSON; native validation remains necessary.
- The controller has one exclusive foreground lock, network-denied child commands, 256 MiB Java heap, 64 MiB output bound and shared 180 s wall/full measured CPU acceptance caps. Compile/import stage limits consume the same budget. Final publication invokes material freshness and cap checks; stored totals are explicitly sampled before final publication. This is not hard CPU preemption or an equal-budget comparison.

## Reproduction and limitations

Executed, with no native/JVM/network:

```
python3 -B .runs/review-pic-routing-controller-001/reproduce_lifecycle_v2.py .runs/review-pic-routing-controller-001/lifecycle-002
python3 -B .runs/review-pic-routing-controller-001/reproduce_boundary_v3.py .runs/review-pic-routing-controller-001/boundary-003
```

Both final controls completed successfully and recorded unchanged reviewed source hashes. The fixture source contains copied PCB and project bytes only; these are intentionally mock-stage controls, not complete-project native qualification. All failed exploratory scripts/logs/outputs remain locally retained and are explained in `attempts.json`. In particular, two early failures were harness extraction/signature mistakes; they are not reported as product defects. The first boundary positive's production-preflight exception was an actual product-source defect and is preserved separately.

The concise public selection excludes all copied project/board payload. Existing shared publisher and subprocess cancellation controls were read/reused, not redundantly rerun. ROOT owns actual runs, final source integration and any continuation after failed exact geometry checks.

The final source snapshot is preserved under `snapshot-reviewed/`. ROOT began a new native-only continuation amendment after these controls; its newly added optional diagnostic paths are not covered by this disposition. The saved controller/validator hashes match the exact control record. Snapshot material was recovered from commit 9c0b274 plus the narrow tested preflight-reporting patch, with byte hashes verified against the test result. No tests were rerun against changing continuation code.
