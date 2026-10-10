# Explicit placement and clearance guidance

`placement-clearance-v1` now passes fresh native qualification through the existing floor routing lifecycle: the owned required-via fixture and the exposed multichannel board both complete with unchanged original constraints. These observations qualify the explicit command on those inputs; they do not establish generalized superiority.

The fixed policy removes only DSN obstacles exactly attributed to original all-five-allowed, enabled SHEETNAME placement areas, then adds20µm to exactly three planning clearance atoms. Original source areas, rules, geometry, net mappings and floor dimensions stay intact. Native refill and final DRC use the original rules. The explicit via costs are50/5, with completion-only routing. The margin is a measured development parameter, not a universal guarantee.

Support is narrow: whole unlocked routing, two copper layers, one Default class and a four-line axis-aligned rectangular outline. Genuine keepouts, ambiguous/disabled/footprint rule areas, cutouts, custom rules, other profiles and user scoring overrides reject. Source32MiB and evidence100MiB ceilings use bounded descriptor reads and finite entry/file counts. The existing native and board-floor policies remain available; old valid receipts pass without migration.

A schema3 receipt preserves and rederives every DSN stage, binds committed implementation/toolchain snapshots and repeats final source/candidate/evidence checks. Receipt checking is mutable local consistency, not authentication or fresh DRC. The schema3 `review-copy` command prepares a bounded disposable project for manual review; its new native-copy and actual GUI qualification remain pending. Live application, strategy/recovery/portfolio propagation, human PCB review and electrical validation remain unqualified.

The completed fixture commands were:

```sh
python3 -B -m autorouter route evidence/placement-area-native-001/allowed_placement/candidate/fixture.kicad_pcb --output .runs/placement-production-native-001 --seconds 60 --adapter both --profile completion-only --guidance placement-clearance-v1
python3 -B -m autorouter check-result .runs/placement-production-native-001/result.json
```

At source checkpoint d6f7f81 the fixture passed with zero findings, seven segments and one required via; stored 8.037944 wall / 5.298197 CPU seconds under 60-second caps. Both real engine-stage SIGINT and SIGTERM controls rejected the cancelled route, cleaned the process group and preserved sources. Twelve offline semantic receipt corruptions rejected after successful relocated positives; these were not native tests.

At eab7540 the five native controls passed under a shared 60-second budget (stored 9.452607 wall / 6.336963 CPU seconds). The valid case passed, undersized track/via geometry produced targeted native errors, the removed required via produced an open, and changed project severity rejected through original-project provenance even though its standalone diagnostic DRC was clean. Attempt001 is retained as a harness failure before native execution; its corrected source/task binding was independently reviewed before002.

The full command then passed with zero opens, zero blocking findings, 96 warnings and zero exclusions. It produced 2,647.385729 mm of track and 21 vias within 36.878350 wall / 51.577022 measured CPU seconds under 120-second caps. The candidate hash is `65dd3b0e6e0bfe6bf45a84b58d94eb4388a8b318967c47c40c26714b6777a0ef`. Original ignored checks remain unchanged. Stored timings precede final receipt publication/freshness checks; acceptance caps include those checks. The 96 warnings include nine copper-connection-width warnings; the original source had six such warnings. The remaining 87 warnings match the source categories. Whole-project cleanliness and electrical adequacy are not established.

```sh
python3 -B -m autorouter route .data/boards/kicad-multichannel/multichannel_mixer.kicad_pcb --output .runs/placement-production-multichannel-001 --seconds 120 --adapter both --profile completion-only --guidance placement-clearance-v1
python3 -B -m autorouter check-result .runs/placement-production-multichannel-001/result.json
```

These output names are completed and immutable; use a new name only when a new verification need warrants a rerun. [Qualification and full population](../evidence/placement-production-qualification-001/summary.json), [native controls](../evidence/placement-production-controls-native-002/summary.json), and [receipt controls](../evidence/placement-production-receipt-controls-001/REVIEW.md) retain the exact evidence. Public copies are selected subsets; complete raw trees remain local. Current fresh local clone/venv installation003 at6c34110 passed with the explicit owned placement fixture. It reused installed dependencies on this Mac; Disposable schema3 review-copy preparation is supported by source/filesystem controls; native-copy and actual GUI qualification remain pending. Live application is not supported. See [installation scope](install-test.md).
