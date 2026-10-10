# Actual pinned padstack import audit

The five retained observations are consistent with the actual committed probe at `9da5f9cdfbd6f709c9dd4235e2c6598574c2c46d`. The independent read-only audit passed 275 checks. No Java, compiler, KiCad, router, network request or downloaded script ran during this review. Git object reads and bounded Python geometry/hash checks were the only subprocess work.

The audited result is `.runs/pic-padstack-import-probe-001/summary.json`, SHA256 `889b538e82dec8d4ccf1780b8b7d8105adcad6e4ce441aa978f0aceafbf183b9`. Raw observations are SHA256 `6e0243fcccd9c64dcc70d35c5bc173dfa6b8f1eb346a4a3a5fd5bb1dcdcf0ab1`. All 21 original files (103,643 bytes), eight frozen source/lock files, recorded API-provenance receipts, execution wrapper/log and pinned tools were checked; the complete raw tree and read materials remained unchanged. No failed case or invalidated receipt was found in this run.

## Measured representation

| Fixed scope | Actual importer result | Independent geometry check |
|---|---|---|
| Convex five-point polygon | Same polygon, `Simplex` | 1,875,000 µm²; exact corners up to winding/start |
| Concave five-point polygon | Rectangular convex hull, `IntBox` | Original 1,350,000 µm² becomes 1,725,000 µm²; adds 375,000 µm² |
| Two disjoint rectangles on F.Cu, A then B | Only B survives | 250,000 µm²; A test point outside, B point inside |
| Same two rectangles, B then A | Only A survives | 250,000 µm²; A test point inside, B point outside |
| A on F.Cu and B on B.Cu | Both survive on their respective layers | 250,000 µm² on each layer |

The point (−600, 0) µm is outside the original concave copper and strictly inside the imported hull. The audit parsed the five exact DSN scopes independently, checked shape order/layers, recomputed the monotone convex hull, shoelace areas, canonical rings and winding membership, and compared those values with actual engine observations. It also matched the two polygon recipes to the previously exposed native-control recipe at integer-micrometre scale. The repeated-shape result is order-dependent overwrite for these inputs, not a union; the expected disjoint union would occupy 500,000 µm². Arbitrary shape types or transforms were not tested.

## Execution and limits

Compilation and import each recorded exit 0, success, complete cleanup, empty untruncated logs, exact intended argv/cwd and explicit network denial. Compilation disabled annotation processing. The class actually imported `Library.readPadstackScope`, then inspected named `Padstack` shapes, bounded corners, area, bounds and strict point membership. It constructed no routing board and invoked no routing or native validation. The compiled class hash is retained in metadata, but no class or JAR binary is selected for publication.

Stored **pre-publication** diagnostic samples were 0.942287166 seconds wall and 1.264525 parent-plus-waited-child CPU seconds. The external wrapper captured controller exit 0 with 1.020236917 seconds wall and 1.332717 waited-child CPU seconds, both below the declared 60-second limits. The wrapper directly waits on the controller: this is not a shell `cat` exit. The controller includes metadata and final checks in its caps; the stored inner sample precedes publication checks. Output was below 10 MiB; recorded child kernel RSS peaks were about 160–161 MB. Heap was capped at 256 MiB; process-group RSS/disk polling is an observational guard, not an OS hard limit or proof against between-sample growth.

The helper freezes raw stage outputs before parsing, rechecks source/tool/HEAD and raw outputs, and invalidates positive publication on cancellation/staleness/budget failure. This audit verifies retained consistency and source logic; it does not authenticate execution against a maliciously rewritten entire history or newly rerun cancellation controls.

## Scope and rights

This is a useful negative transport finding on five isolated library scopes. It does not establish complete board import, terminal-to-net mapping, contacts, foreign-net clearance, router behavior, SES transport, native correctness, custom-pad support or C novelty. Existing custom-pad source gates remain unchanged. A future anchor-plus-conduction-area proposal remains a separate unqualified B1 transport hypothesis requiring whole-DSN/contact/obstacle observations and later native controls. Original KiCad project files were neither imported nor changed by this probe; no new family or population result is counted.

The convex/concave coordinates derive from KiCad `pic_programmer` at `69cafb907ebc09e7722a2a464b1d466fc2e3608d`, CC BY-SA 4.0. The exact original grant notice and license are selected. Rectangle controls, probe/audit software and execution wrappers are project-authored; the project GPL-3.0 notice is also selected. The source-derived scope/input/output geometry is attributed separately from project code. No JAR, compiled class, full third-party source or source board is selected.

Reproduce the read-only audit in this checkout, using a fresh output filename:

```sh
python3 -B .runs/review-pic-padstack-import-actual-001/audit.py --output .runs/review-pic-padstack-import-actual-001/audit-recheck.json
```

The recorded source and tool files must remain available. A later intentional source/tool change should be investigated rather than replacing the recorded pins.
