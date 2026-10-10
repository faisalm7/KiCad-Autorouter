# Explicit placement and clearance guidance

`placement-clearance-v1` is integrated but awaits fresh native production qualification at this checkpoint. It extends the existing floor routing lifecycle. The earlier diagnostic completed the exposed multichannel board; that does not automatically qualify this new production entry point.

The fixed policy removes only DSN obstacles exactly attributed to original all-five-allowed, enabled SHEETNAME placement areas, then adds20µm to exactly three planning clearance atoms. Original source areas, rules, geometry, net mappings and floor dimensions stay intact. Native refill and final DRC use the original rules. The explicit via costs are50/5, with completion-only routing. The margin is a measured development parameter, not a universal guarantee.

Support is narrow: whole unlocked routing, two copper layers, one Default class and a four-line axis-aligned rectangular outline. Genuine keepouts, ambiguous/disabled/footprint rule areas, cutouts, custom rules, other profiles and user scoring overrides reject. Source32MiB and evidence100MiB ceilings use bounded descriptor reads and finite entry/file counts. The existing native and board-floor policies remain available; old valid receipts pass without migration.

A schema3 receipt preserves and rederives every DSN stage, binds committed implementation/toolchain snapshots and repeats final source/candidate/evidence checks. Receipt checking is mutable local consistency, not authentication or fresh DRC. GUI handoff, strategy/recovery/portfolio propagation, human PCB review and electrical validation remain unqualified.

Root-only qualification sequence uses fresh output names:

```sh
python3 -B -m autorouter route evidence/placement-area-native-001/allowed_placement/candidate/fixture.kicad_pcb --output .runs/placement-production-native-001 --seconds 60 --adapter both --profile completion-only --guidance placement-clearance-v1
python3 -B -m autorouter check-result .runs/placement-production-native-001/result.json
```

The native control and actual cancellation commands are in `experiments/placement_production_controls_v1/README.md`. Only after those gates may the full exposed board be replayed with120-second wall/CPU ceilings; it is integration qualification, not a new fair benchmark or C novelty.
