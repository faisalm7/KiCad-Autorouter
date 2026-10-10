# Independent review of production control fixture gate

No blocker found in the narrow fix. The old assertion rejected the exact owned
fixture because its original contains eight unlocked reference routes. The new
check pins the original board and project, reconstructs the production whole-board
task using `g.task_from_source`, rejects protected routes, and requires the exact
outer production `task_sha256`. It does not select new geometry from reference
routing or change the positive candidate, source rules, placement area, native
predicate, mutation cases or validator. The caller first verifies the complete
production receipt and original project, and retains the existing source and
positive evidence freshness checks.

Seventeen independent read-only/pure checks passed (`audit.json`). The original
reference has eight unlocked routes and one area; its reconstructed task has zero
routes and identical immutable source fields. Its hash is
0144c92bb45a55b10b7e61fdc51754b15aed62a5afa1c744da05ce4127b34aa0,
matching the actual saved export task and outer production receipt. Missing or
incorrect task hashes, wrong source identity, and a protected-route variant reject.

Actual production fixture001 remains current under `check_result`: zero opens,
blocking findings, warnings and exclusions, unchanged original ignored-check
metadata, one via and67.93373808491306mm track length. Its stored8.037943915995129wall
and5.298196999999999CPU seconds are below60; all eight stages are retained. This
readback is consistency validation, not a new native execution.

Failed control001 remains explicitly failed with empty cases/steps and
native_executed=false. Its error names the obsolete no-route predicate; no native
process receipt exists. The new fixture admission has not yet qualified the five
actual native controls; fresh output002 is the required next invocation.

The lead's30-control log was inspected, not rerun. All source, production-positive,
failed-run, helper and core file trees remained unchanged during this review.
`reviewed.patch` and `audit.json` bind the reviewed changes and full original trees.
No native/engine process was run and no tracked/evidence files were modified.
