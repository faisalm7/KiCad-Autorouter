# Frozen HFE original diagnostic: narrow launch review

One concrete launch blocker found in original draft `run-hfe-original-native-001.py` SHA256 `80ce9c943fb14ba97e488ac26ec5f096826320def2f0eaf76ab422a7ca7d4e0f`.

At raw_stage line111, `except (Exception, KeyboardInterrupt)` converts an actual SIGINT/SIGTERM KeyboardInterrupt into `raw_capture_error`. Worker invokes this helper after its main diagnostic try/except at line177. If cancellation arrives while capturing raw reports after an otherwise positive final check, it can be swallowed while `passed=True/status=completed` survive and publish. The later account callback cannot identify the consumed signal.

The corrected copy changes only this cancellation path: raw_stage handles ordinary Exception only; the exact worker post-stage capture block catches propagated KeyboardInterrupt, retains reports already captured, and sets passed=False/status=cancelled. Native observation_complete may truthfully remainTrue if Native checks finished before cancellation; it never authorizes a positive outcome after cancellation. Existing guarded publication, caps, source/static refusal, native tool selection, shell reconstruction, PRL and stage checkers remain unchanged. Partial files remain retained. Ordinary raw read/schema errors remain unqualified diagnostics rather than cancellation.

`test_hfe_raw_capture_cancellation.py` has four unexecuted controls. It AST-extracts the literal raw_stage body and worker's actual post-stage block from the named controller, with owned temporary report bytes and substituted IO only. First two controls predict failures on original001 and passes on the corrected copy: helper must propagate KeyboardInterrupt, and actual worker capture block must clear passed and set cancelled before publication. Other controls preserve ordinary IO failure classification and valid raw-report diagnostic-only scope. No Native, subprocess, project imports or benchmark fixture is required.

Prospective commands for lead, not executed:

```sh
HFE_CONTROLLER="$PWD/.local-backups/hfe-original-native-draft-001/run-hfe-original-native-001.py" .venv/bin/python -B .local-backups/hfe-original-draft-review-001/test_hfe_raw_capture_cancellation.py
HFE_CONTROLLER="$PWD/.local-backups/hfe-original-draft-review-001/run-hfe-original-native-001.py" .venv/bin/python -B .local-backups/hfe-original-draft-review-001/test_hfe_raw_capture_cancellation.py
```

No additional concrete launch blocker was found in the reviewed child witness/literal equality, late source/material guards, source preservation, saved-refill/original shell flow, final full-SCH/PRL stage replay, or status/cap accounting. This is a bounded source review, not execution qualification. Existing critical4Cu/innerarea static refusal remains exact in preparation and `accepted/production_support_qualified` remainFalse. Nothing in this patch admits HFE or rewrites its files, original rules or severities. Unknown field/schema support may produce a safely retained failure; it is not waived.

The original draft and packet were not edited. Only this assigned review directory was written; current pc.read_bytes and backup work remain root-owned. No source/Git/network/tests/Native/JVM/heavy worker execution or delegation occurred. Both proposed Python files were AST parsed only. Review elapsed wall through note preparation: 173.297 seconds; full CPU/model work unmeasured; external spend$0. No benchmark/research independence or production capability claim follows.
