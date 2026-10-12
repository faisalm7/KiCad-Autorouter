# Selective routing source review

No remaining blocker found in the assigned source scope after two concrete readback corrections. This is source/pure consistency review only: no Java, compiler, native process, solver, network, source edits or delegation were performed. Actual compilation, routing, cancellation and native validation remain ROOT's next qualification.

Reviewed `SelectiveRoutingProbe.java`, `routing_checks.py`, the shared `transport.validate_rows/validate_local_rows`, `selective.transition`, and `SelectiveAreaProbe.prepare` refactors. The later bounded-layer change in `ses_checks.geometry_check` was reviewed only for the reported counterexample. Driver/native integration and the new SES-generated mode were deliberately outside scope.

## Corrected findings

1. The original comparator accepted a captured two-disabled-layer mask, duplicate embedded configuration key, non-Boolean cost-applied witness, negative pipeline duration and Boolean schema, yet returned `lifecycle_verified=true`. The final code uses the existing strict bounded JSON parser and checks the actual `routable` spelling, schema/types, finite elapsed time, object-replacement Boolean and deadline/stop consistency. `probe-original.json` preserves the accepted falsifiers; the unchanged probe now retains its positive and rejects all five variants in `probe-fixed.json`.
2. A synthetic new trace built from actual002 retained geometry passed with layer index −1, because Python selected the last layer; it also passed after changing its clearance class to null. State and writer snapshots were changed consistently, avoiding a shallow outer mismatch. The final geometry guard requires an integer index in the real layer range; the routing guard requires each generated trace/via's original net clearance class. `route-probe-original.json` preserves both failures. The unchanged probe's positive passes and both variants reject in `route-probe-fixed.json`.

The two positive constructions are explicitly synthetic and establish validator behavior, not solver success. Reproduction commands from the project root:

```sh
python3 -B .runs/review-pic-routing-source-001/probe.py .runs/review-pic-routing-source-001/new-probe-output.json
python3 -B .runs/review-pic-routing-source-001/route_probe.py .runs/review-pic-routing-source-001/new-route-output.json
```

The scripts reuse only `setUpClass` and `synthetic` from the existing test through AST extraction. They do not execute its native-copy tests or any worker. Existing recorded outputs must remain immutable.

## Source conclusions and limits

The pinned `StoppableThread.run()` directly calls its action; the new call is synchronous and uses no scheduler/reload. The wrapper overrides both relevant stop-query methods, latches a monotonic 60-second cooperative request and observes the returned `job.board`. Cached pipeline/history source confirms that this final board can differ from the initially loaded object. A long operation may delay a cooperative query; outer process/time/full-CPU enforcement is ROOT's separate driver responsibility, not established here.

The input guard requires zero ordinary traces/vias before routing. Router enabling changes only the saved enabled field; all captured effective configuration/layer values are compared through final readback. The old two-case APIs still require two real cases, while the new single-row path does not fabricate another import. Actual selective002/local250 stored observations still pass the refactored validator and its one-case historical-envelope negative rejects (`shared-refactor-readback.json`). Input bytes remained exact.

Nonrouting equality covers retained observed fields: the three conduction rings, pin identities/positions/bounds/classes, net/layer settings and matrix. It omits changing route/contact connectivity, and does not export all arbitrary obstacle/padstack geometry. It must not be described as a general full engine-board geometry proof. Final original-project native invariants and native DRC remain essential. The refactored transition no longer claims a retained-baseline comparison by itself; only the wrapper that performs that comparison adds the corresponding field.

Exact original/final source pins and cached API/source/actual002 input hashes are retained. The hash of `ses_checks.py` binds the inspected bytes but does not extend this review to its concurrent SES-generated branch. No saved actual routing result is claimed.
