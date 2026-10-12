# DRC failure evidence — copy freshness follow-up

This additive revision preserves the original report, manifest, source snapshots and failed controls unchanged. ROOT identified that recording the actual copied-input snapshot without comparing it could admit a copy modified before native and restored during native. A real-file test with fabricated copy/native stages reproduced that false admission: `copy-before-001.log` reports `Rejected not raised`.

One new guard compares the complete actual validation-input inventory to the original before inventory immediately before constructing/invoking native. The same test now rejects before any fake native call, retains the incorrect copied-rule hash in `validation_copy_before` and binding `after`, preserves the exact original `before` inventory, and marks absent process/report/log artifacts null. It does not restore a file or relax the existing PRL/rule constraints. The source/output identity and original exception behavior from the first revision remain.

Final targeted suite: 14 new failure-binding/copy controls plus the 2 unchanged project-preservation methods pass in 0.054 seconds (`tests-after-003.log`). Successful nonsaving and saving bindings retain their exact five-key schema. All native work is mocked; no actual native/JVM/network/Git/full-suite call occurred.

`BaseException.add_note` is valid for the supported supervisor: README line5 records Python3.11; docs/install-test.md line12 requires Python3.11; scripts/install_smoke.py lines286–287 rejects a supervisor outside exactly3.11. The control process here is3.11.9. Config's separately bundled KiCad Python3.9 executes native helpers, not this Job.drc supervisor. Exact source evidence hashes and AST scope proof are in `scope-proof.json`.

Only the already owned Job.drc method and the new regression file changed. `promotion.patch` is the complete current diff from the untouched initial pipeline, not a patch to apply on top of revision001. ROOT owns integration/full-suite/native qualification. All revision002 writes are frozen at its manifest.
