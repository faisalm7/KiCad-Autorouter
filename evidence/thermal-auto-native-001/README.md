# Generated thermal repair-only control draft

Ready for lead review and lead-owned native execution. No native jobs were run while preparing this driver. It is an ignored development diagnostic, not production routing, comparison eligibility, candidate application or physical/electrical validation.

## Invocation

From the local checkout, in a lead-assigned quiet slot:

```
python3 -B .runs/thermal-auto-control-draft-001/driver.py \
  --receipt .runs/interf-native-003/result.json \
  --proposals .runs/thermal-generalization-draft-001/qualification-001/path-attempt-003.json \
  --export-summary .runs/thermal-generalization-draft-001/native-export-001/summary.json \
  --output .runs/thermal-auto-control-draft-001/native-001 \
  --validate
```

The output must be a fresh direct child of this draft directory. Without `--validate`, it only verifies evidence, snapshots source/helper code and creates four candidate copies. This was exercised successfully in `preparation-003`: `generated_only`, native_executed=false, originals unchanged, 1.663794 seconds wall and 1.590105 measured CPU. This is non-native preparation evidence, not mocked/native routing validation.

## Bounds and retained evidence

One 60-second wall/measured-CPU diagnostic budget covers evidence verification, snapshots, at most four sequential native candidate validations, stability checks and final publication. CPU uses self plus waited child rusage, including metadata/git subprocesses. This is a measured acceptance cap with cooperative per-step assignment; it is not an OS total-CPU hard limit. Native execution uses isolated KiCad config/cache/documents/temp directories, copied native helper code, and network denial. The existing experiment lock prevents concurrent heavy workers.

Before mutation, the driver verifies the current full source, original snapshot, failed candidate, final native input tree/report binding, export copied-input tree/request/report, geometry hashes, proposal/helper hashes and native tool pins. It rechecks all four exact path witnesses, all 352 physical drills, target/zone/net/layer/logical-terminal identity and the effective class width. Negative hole dimensions and nonpositive native maximum error are rejected. The original `native_self_intersecting=true` values are retained; no whole-body or scene qualification flag becomes true.

Each candidate is a fresh complete copy with exactly one generated track. Native validation refills zones, resolves effective classes, and runs final original-rule DRC through the current shared `native_accepted` policy. A candidate is rejected if target-zone saved fill changes, any pad/via/protected/base route changes, extra files/rules change, critical/native findings remain, warnings increase, or final evidence becomes stale. Final candidate/report/class-map/copied-native-input bindings are rehashed before and after summary publication. Saved-fill equality keeps the historical path witness applicable; it is deliberately restrictive and does not substitute for a future fresh post-refill geometry qualification.

Final publication is cancellable. An interruption after a positive summary write or during final verification preserves an interrupted partial when present and publishes `validation_passed=false`, `status=cancelled`. All routing/comparison/apply flags remain false even after a diagnostic native pass. Parent/child accounting limits and the source of each cost are retained.

Preparation001 failed safely because native dimension objects and their nested display text share UUIDs. Those immutable nonconductive objects remain unchanged; only referenced PAD/ZONE identities must be unique, and generated track UUIDs are checked against all existing identifiers. Preparation002 passed before final cancellation/CPU strengthening. Preparation003 uses the final source. Prior preparations and their frozen code snapshots remain as evidence.

Nineteen pure controls pass in `tests.log`, including actual four-proposal verification, negative/zero hole and max-error rejection, width/terminal/path tampering, exact saved-fill equality, duplicate target rejection, symlink/outside-path rejection, exact numeric serialization, post-positive-write cancellation, interrupted partial preservation, changed final evidence and post-publication budget crossing. These tests and preparations establish driver behavior only. Native execution and its outcome remain pending.

The independent graph geometry audit is `.runs/review-thermal-graph003-001/audit.json`: 1,313 checks using separate exact-distance/winding code, including native/saved pad, via, hole and fill correspondence. It is geometric evidence, not native routing acceptance.

## Remaining product work

This repair-only control consumes exposed historical inputs and excludes the cost of obtaining the failed engine candidate, native geometry export and proposal search. It must not be used as an equal-budget completion/quality result. A later method must acquire fresh engine output, detect the thermal failure, export fresh geometry, generate proposals and validate any repair within the same declared end-to-end budget, with no historical coordinates or cached proposals. The lead owns that integration and any subsequent native experiment.
