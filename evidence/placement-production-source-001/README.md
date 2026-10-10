# placement-clearance-v1 production draft

Ignored draft only. No native or engine process ran here; no tracked project
files were edited. Lead owns promotion, committed source freeze, integrated
suite and fresh native qualification. Current work adds one closed branch to
`floor_route`; it does not copy the diagnostic routing lifecycle.

## Fixed scope

`route --guidance placement-clearance-v1 --adapter both --profile completion-only`
uses whole unlocked2Cu routing, oneDefault class, the original floor contract,
a four-line axis-aligned rectangular outline and one or more enabled SHEETNAME
board areas whose five flags are explicitly allowed. Genuine keepouts,
disabled/unknown/footprint areas, legacy modules and unsupported geometry remain
rejected. Planning changes only the three existing global/global-smd_smd/class
clearance atoms by20,000nm, with explicit default via costs50/5. The margin is
an exposed measured planning parameter, not a universal geometry bound. All
original source/rules/areas and native acceptance remain unchanged. This is an
adapter correction, not C novelty or physical validation.

## Source and receipt boundary

- Reviewed `placement_transform.py` is byte-identical to the frozen diagnostic
  helper bfd4ff85a92ad57a9908e46904e67b1d5fce65647689e489a566d6434260fdb5.
- `placement_clearance.py` owns the fixed composition, complete source bytes,
  bounded reads, saved source freeze and final freshness checks.
- `floor_context.collect` adds optional fifth `area_output` on the same loaded
  board. The area getter/census AST exactly matches the qualified observer;
  old calls and final-context argv are unchanged.512footprints is the explicit
  reviewed cap; one native export supplies both observations.
- Raw→floor→placement→planning→adapter stages are separately retained and
  rederived. Inner `floor-policy.json` remains board-floors-v1; original floor
  widths/vias/drills are still checked by the existing validation lifecycle.
- New outer schema3 and strict dispatch use placement/planning artifact markers
  as well as claims. New runs require committed exact core/lock bytes. Historical
  schema1/2 readbacks use their retained code, without requiring new modules or
  currentHEAD. The current checker now strictly rejects duplicate/nonfinite
  outer JSON also for older malformed receipts; valid saved receipts pass.
- Complete new source reads are streamed with32MiB/2000file/4000entry bounds;
  retained new evidence uses100MiB/2000file/4000entry bounds. Descriptor reads
  enforce limits with fstat and read(limit+1), and native DSN reads cap20MiB.
- Existing job supervision, cancellation, CPU accounting, refill/DRC/metrics,
  import transport reconstruction and publication invalidation are reused.
  Schema3 standalone readback repeats complete evidence/source/candidate checks
  plus receipt digest. No GUI handoff, recovery, strategy or portfolio propagation.

## Reproduction and evidence

From the durable checkout:

```
python3 -B .runs/placement-production-draft-001/verify_draft.py
python3 -B .runs/placement-production-draft-001/verify_compatibility.py
```

`tests-010.log`:169 focused tests passed in3.540s. Includes44 promoted pure
placement controls, old floor/result/handoff controls, actual retained export
AST/byte parity, strict scope and rehashed semantic tampering, optional native
collector mock/parity, file-growth and oversized-descriptor sentinels, and
synthetic schema3 consistency/final-staleness controls. These do not establish
new native validity. `test_placement_policy.py` explicitly rewrites copied old
fixture process/settings metadata to construct a synthetic checker fixture;
it never presents that fixture as a native production execution.

`compatibility-002.json`: saved accepted native-smoke, board-floors-v1 and thermal
schema1 results all pass the draft checker; exact receipt/source/run trees are
unchanged. This is current consistency, not fresh native DRC. Earlier failed
logs001–005 remain preserved: expected error wording, distinct DSN filename
expectation, macOS temporary-path symlink rejection and relocated synthetic
context hashes were corrected without altering actual saved evidence.

`base-bindings.json` binds the original core copies; `promotion-files.json` is
the exact promotion list; `promotion.patch` contains only those seven core and
four test files. Apply after checking bases; do not copy the entire overlay.
`manifest.json` hashes this draft, tests and evidence. No source imports or new
routing population changes occur in this draft.

## Lead-only next gates

After independent review, promote exact files, run the full suite, commit/push
and remote-read-back before the fresh native fixture:

```
python3 -B -m autorouter route evidence/placement-area-native-001/allowed_placement/candidate/fixture.kicad_pcb --output .runs/placement-production-native-001 --seconds 60 --adapter both --profile completion-only --guidance placement-clearance-v1
python3 -B -m autorouter check-result .runs/placement-production-native-001/result.json
```

Root's separately owned `experiments/placement_production_controls_v1` supplies
fresh original-rules positive/invalid geometry and real SIGINT/SIGTERM controls.
Only after those gates should the lead run the exposed multichannel120s replay.
That replay qualifies production integration; it is not a new fair comparison.
Warnings must remain explicit; native routing acceptance is not whole-project
DRC cleanliness, human PCB review or physical/electrical validation.
