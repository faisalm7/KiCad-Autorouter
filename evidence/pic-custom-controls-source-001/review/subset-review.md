# Independent AI review — stable subset 001

The reviewed four source hashes are in `subset-hashes-001.json`. This is source/pure-control review, not native or human PCB qualification. The lifecycle driver was still being authored and is not cleared by this note.

The fixed fixture has four separate centered footprints, two original custom primitives with their rectangular anchors, two nets and exactly two 0.5 mm tracks. Both proposed contact endpoints avoid their anchors; false contact uses the full rounded track capsule rather than an endpoint-only witness. Front0 and back90 use fixed recipes; native world/effective/local rings must match before interpreting DRC. World/pin identity and native default dimensions are compared explicitly. Unused original POWER configuration is preserved without invoking the production two-class audit, which would require that class to be exercised.

The worker getter body matches the previously executed observer apart from the intentionally narrowed 4-pad/4-footprint/2-custom census. The layer-aware APIs are retained. Back90 exporter placement270 is source-derived; see `back-angle-source.json`. The fixed Y-symmetric polygon controls cannot establish arbitrary chiral reflection behavior. Convex hull export is inspected as an approximation, not treated as copper connectivity.

R1 reproduced: `checks.predicate` admits `unknown_provider:warning` and `missing_tuning_profile:warning` for positive, expected-open and expected-clearance cases. The fifteen-row pure probe preserves raw findings and consistent counters; the known harmless library warning and unchanged cases pass, while padstack_invalid is rejected. The central helper intentionally does not reject all unknown finding names. A local diagnostic finding-type guard is required to meet the prospective unknown-warning rule. No central policy change is requested. Probe: `probe_predicate.py`, result `predicate-probe-001.json`.

Root separately identified a known source/native ignored-set difference: three explicit source keys versus four actual native keys including track_not_centered_on_via. Keep both independently bound; exact native matching must use the observed, predeclared native set without changing source settings. Await the final author correction before disposition.

No native, router, GUI or dataset script was executed. One narrowly scoped pinned primary source document was read/cached because FOOTPRINT::Flip was missing from prior cached material; its size, URL, license and hash are retained. This note does not clear orchestration or production custom support.
