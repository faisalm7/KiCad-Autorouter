# Saved preferences integration review

Disposition: no remaining reproduced blocker in the reviewed scope. ROOT must still checkpoint and run the full suite and fresh native saved-settings/cancellation cases. Final source hashes are in `source-final.json`; initial source and all failures remain preserved.

Four concrete defects were found and corrected:

1. Native preference binding filtered only `--router.*`; three effective engine-option aliases still passed. The shared full engine argv constructor now binds the complete argument list, cwd and process record. Exact unchanged-positive/alias controls pass after the fix.
2. An interrupt immediately after the first positive native receipt write left `accepted=true`; a canonical profile edit at checker return also escaped. The preference path now reuses guarded floor publication, archives invalidated positives, scopes/restores SIGINT/SIGTERM handlers and checks canonical metadata. Both falsifiers reject.
3. Floor publication checked the current preset before subprocess-bearing metadata. A mutation in the last metadata observation still left acceptance. The final preset and captured-byte recheck now rejects it.
4. Standalone native check-result accepted snapshot or receipt changes during its final code inventory. Final captured-preference verification plus the initial receipt digest now rejects both.

All three original reproduction scripts were rerun unchanged except new output directory names: 12 scenarios preserve the positives and reject the prior failures. Raw original/fixed results and logs are retained. The two native publication repros use explicitly mocked workers/checker; the standalone cases use the existing synthetic `test_result.py` fixture and the actual central checker. None is native evidence.

Added `tests/test_preference_publication.py`: seven methods, 13 scenarios, pass in 0.291 seconds. They exercise native/floor positive publication and late staleness, real self-SIGINT/SIGTERM in this owned mocked-stage process with handler restoration, the real full argv binder for an explicit 60-second/via-low override, and late captured/receipt edits through the actual central checker. The earlier message saying 14 scenarios was a counting error; 13 is correct. This file is the only tracked edit owned by this review.

The final source-only amendment moves source/snapshot samples after metadata in both publication guards. It was inspected after the fixed repro runs; those runs are not represented as execution of this final ordering-only change. ROOT owns the final integrated suite. The full engine argv remains byte-equivalent to the prior floor command, and old receipts without preference artifacts skip the new binder. Old saved-native/floor/placement readbacks were not repeated by this review.

The preferences helper captures bounded exact bytes, rejects malformed/duplicate/nonfinite/unknown keys, retains unspecified saved choices under explicit CLI overrides, and treats captured bytes as authoritative rather than a mutable parsed dictionary. Readback intentionally permits later intentional edits of the external preset; an active run rejects such edits. Static preview uses original-source guards, records no native validation and does not write source. Supported layer choice remains only `source_all`; no layer-mask support is inferred.

The small `scripts/native_cancellation.py` diff preserves owned PID/group cleanup and adds a SIGINT/SIGTERM selector plus exact expected signal name. Five argument-only controls pass: default, explicit INT, explicit TERM, rejected CLI KILL, and rejected direct KILL before output creation. Valid control bodies were mocked, so these checks made no native process and do not qualify real engine cancellation. ROOT's planned two sequential real runs supply that evidence.

Freshness is sampled consistency, not atomic authentication against an adversarial concurrent writer. Native routing, GUI, physical/electrical correctness and comparative performance are outside this review. No source rules, board geometry, validation policy or historical outcomes were altered.

Reproduction commands (fresh output names required):

```
python3 -B .runs/review-preferences-001/reproduce.py reproduction-NNN
python3 -B .runs/review-preferences-001/reproduce_floor.py floor-reproduction-NNN
python3 -B .runs/review-preferences-001/reproduce_readback.py readback-reproduction-NNN
python3 -B -m unittest discover -s tests -p test_preference_publication.py -v
```

For public preservation, `selected-public.json` includes only this report, compact results/logs, the three falsifiers and source bindings. Duplicate toy project/code trees and the initial full code snapshot remain local; the tracked regression file is referenced by its exact hash.
