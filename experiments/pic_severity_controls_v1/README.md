# Prospective owned severity/intent controls

Draft only. No native execution or production support change. Six fixed cases run sequentially under one 90-second wall/full self+waited-child CPU budget and a 20 MiB aggregate evidence ceiling. Native subprocesses are OS-network-denied, isolated, process-group monitored and limited to 30 seconds or the remaining shared budget, whichever is smaller. Polling/postcompletion limits are not hard CPU/disk quotas.

The original 15-file KiCad pic_programmer project is verified against its acquisition SHA256/Git blobs and never written. Each case replaces only the PCB in a complete disposable copy with an owned conventional four-PTH/two-track fixture. The baseline, text and pad-machining cases preserve the original project bytes exactly. The two profile cases change only one copied class `tuning_profile` value; the class values, global floors, rule severities, exclusions, stackup and every other project value stay unchanged. The independent project-delta proof rejects all other mutations.

Cases: clean positive; missing named profile; separate Default profile coverage probe; board text on Edge.Cuts; footprint text on Edge.Cuts; connected PTH front counterbore. All six outcomes remain in the denominator. Negative predicates require a matched positive, exact target finding/severity/item UUIDs, no other blocking/critical/unknown findings, no opens or exclusions, and exact observed native geometry/intent/floors. Additional findings remain raw and cause the declared control to fail, not be discarded. Native global missing-profile findings have no UUID, so class/profile detail and loaded effective profile must match. The Default probe can complete with a present or omitted finding, but never sets `default_profile_enforcement_qualified`; an omission is explicitly reported. A failed counterbore geometry/API/connectivity/DRC observation stays failed; no alternative recipe is silently retried.

The CLI never uses `--save-board` or `--schematic-parity`. The newly authored board intentionally does not match the copied original schematic. Empty parity results therefore prove nothing about schematic field parity. A future independent matched schematic/board positive and exact custom-field negative is still required. The diagnostic source-intent helper is a prospective guard, not a production validator: it rejects every nonempty class profile (including Default), profile definitions, generated objects, postmachining/backdrill tokens, and Edge.Cuts text/dimensions/unknown items. Existing tuning-pattern defaults alone are not active tuning intent. Its strict current schema does not establish absent-field semantics for older formats.

The native worker uses one loaded board for profiles, class dimensions, pad/track identities, text layers and machining mode/dimensions/affected-layer observations. New getters are declared in the pinned installed wrapper; this is not execution proof. Missing or opaque APIs fail visibly. No DSN, routing engine or board save is attempted. Native DRC uses a second complete copy and may add only a project-local `.kicad_prl`; every existing byte must remain unchanged. Full raw reports, logs, process/binding files and all failed outcomes are retained. The source explicit ignored3 and observed native ignored4 (extra track_not_centered_on_via default) are separately bound to prior actual evidence, never rewritten or called provider qualification.

Parent snapshot requires every runtime helper, unchanged core/toolchain and pinned original-native ignored-check report to match exact committed HEAD blobs before native launch. Completed evidence is captured once, rechecked through publication and never rebased. Signals become cancelled receipts; stale material, canonical/returned-record mutation, failed correction and budget expiry cannot leave a positive canonical summary. Stored totals precede final freshness/size checks; final cap decisions include them. These are bounded mutable-file consistency samples, not signatures or atomic concurrency guarantees.

After review and promotion to `experiments/pic_severity_controls_v1`, ROOT alone may run:

```
python3 -B experiments/pic_severity_controls_v1/driver.py --output .runs/pic-severity-controls-001 --run-native
```

Before promotion, only pure checks are authorized:

```
python3 -B .runs/pic-severity-controls-draft-002/test_controls.py
```

No native findings, coverage results or library completeness are established by those tests. The original remains production-blocked by custom pads and the four unqualified severity names. These controls do not widen support, qualify arbitrary postmachining/backdrills, prove electrical adequacy, or substitute for human PCB review.

The independent publication-scan finding is fixed in draft002: final bounded size scanning now precedes the last full material/semantic check, strict canonical/returned-record equality, and final resource sample. Original draft001 and its reproduced stale-source/raw-report positives remain unchanged. No geometry, worker, predicates, protocol or production support changed.
