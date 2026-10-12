# Shared DRC failure evidence — frozen source change

Only `Job.drc` in `autorouter/pipeline.py` and the new `tests/test_drc_failure_binding.py` changed. An AST comparison proves all other pipeline code identical to the saved pre-change source. ROOT owns integration and native execution; no production admission or original input/rule change was made here.

Previously, preservation rejection occurred before publication of the native validation copy's before/after binding. The first ten-method controlled run reproduced nine missing-failure-evidence errors while the unchanged positive passed (`tests-before.log`). The original complete pipeline is retained as `pipeline-before.py`. This demonstrates evidence control, not a fresh native PAW observation.

The revised method records the actual validation-copy inventory before invoking native. Successful return, parser, exit/report consistency check and five-key binding schema remain unchanged. On failure after the original source inventory was captured, it samples the validation copy and publishes the ordinary binding even when project preservation or report parsing fails. A separate failure record has `passed:false`, first error type/message, phase, inline source/input/before/after/saved binding, actual copy-before inventory, available report/log/process sizes and SHA-256 hashes, and explicit capture errors. Missing artifacts are null; an unavailable after inventory is null. It never restores or ignores an existing PRL or rule change. The report is retained exactly, including malformed bytes.

Native rejection/crash and KeyboardInterrupt retain the same original exception object after evidence capture. An evidence-capture/publication failure is attached as an exception note and, when writable, to the failure record; it cannot replace the first cause or produce a successful result. Keeping the inline original binding preserves the source inventory even if the separate binding write fails. Both normal metadata publication and failure artifact publication use existing helpers. These finite failure-time samples are not atomic concurrent-writer protection, and existing pipeline tree/file helper limits remain applicable.

Final targeted suite: 13 new methods plus 2 existing native-project preservation methods passed in 0.066 seconds (`tests-after-002.log`). Controls cover unchanged success with the exact old schema, permitted new PRL creation, saved-board-only content exemption, prohibited existing PRL/project/rule changes, malformed report, exit/report mismatch, process rejection, cancellation, unavailable after inventory and both binding/failure-record write errors. All native stages are fabricated and use real temporary files; no actual KiCad, Java, engine, network, Git or full-suite run occurred. Earlier intermediate test logs are preserved.

Reproduce the targeted controls:

    python3 -B -m unittest discover -s tests -p 'test_drc*.py' -v

All source and metadata writes are frozen at this manifest. ROOT should review the narrow diff, run integration checks and checkpoint before any new native lane. The failed PAW/native raw evidence remains unchanged and unsupported.
