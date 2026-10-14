# CellScan edge-rule transport source review

This is a narrow read-only investigation of the completed `cellscan-b1-budget240-001` result and the pinned Freerouting implementation at `b647a2f824cfbc54bc4dcaee71b03b7cd945eb76`. No Java, compiler, KiCad, routing trial, original reference copper, source edit or Git mutation was run. Source-based proposals below require the lead's actual pinned-JAR importer and native controls before production qualification. The four fresh exact-revision Java bodies remain private in this folder; cached sources were reused rather than downloaded again.

## Demonstrated missing constraint

The recorded candidate is fully connected, retains 209 original warnings and fails one native copper-edge finding. Candidate SHA256 `231246dd743d9382634a82c156d365b6c88a234a01938985c667902630f288c1`; final native report `6cb9e4ff6634a978e5809975553b41ab42e9671212a35181475f86d9913a7687`. Its GREEN1-A via center x=187.3673, diameter 0.6, is 0.2827 mm from right edge x=187.95. Original project `min_copper_edge_clearance` is 0.3 mm. No rule, severity, exclusion, pad, boundary or source route may change to make this pass.

The retained task DSN has the original zero-width rectangular boundary, global clearance 200 micrometers and SMD-to-SMD clearance 50 micrometers. It has no explicit boundary clearance class or 300 micrometer edge pair. Cached `DefaultSettings.java:83,169` sets the engine's guessed edge default to 250 micrometers. The observed 0.2827 mm via gap can therefore satisfy the guessed engine setting while failing the original KiCad rule. This is an adapter rule-transport defect, not a novel routing-strategy gain.

## Supported source mechanism

`Structure.java:276–324` accepts `(clearance_class NAME)` inside a boundary scope and stores its name separately from the exact boundary shape. `Structure.java:614–680,1312–1318` applies structure rules before passing that name and unchanged outline geometry to board construction. No inset, boundary widening or source edit is needed.

Fresh [Rule.java](https://raw.githubusercontent.com/freerouting/freerouting/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/io/specctra/parser/Rule.java):238–280 parses numeric clearance and optional `type` class pairs. Cached `Structure.java:674–843` interprets `wire` as default matrix class 1; recognized `via`, `smd`, `pin` and `area` names bind the corresponding default item classes. Rules update both symmetric matrix entries and all layers. Use a fresh name without underscore, dash, quote or spaces to avoid ambiguous pair parsing.

Fresh [ReadScopeParameter.java](https://raw.githubusercontent.com/freerouting/freerouting/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/io/specctra/parser/ReadScopeParameter.java):139–164 resolves an explicit outline name into its matrix class. Without one it uses the Default netclass's AREA item class. Unknown explicit names fall back to class zero, so a missing or misspelled class can silently remove the expected clearance; actual load inspection must fail that case.

Cached `HeadlessBoardManager.java:802–861` loads through DsnReader and applies settings after receiving the parsed board. Its `applyCopperToEdgeClearanceOverride`:490–594 preserves an explicit non-fallback outline class when the configured value is the guessed 250 micrometer default. Thus a dedicated DSN edge class can survive the ordinary post-load setting. Other explicitly configured edge values override all outline matrix pairs. The lead must check the full manager load path and runtime command, not only the low-level parser.

Fresh [BoardOutline.java](https://raw.githubusercontent.com/freerouting/freerouting/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/board/model/structure/BoardOutline.java):53–84,214–240 uses a fixed all-layer outline object with its clearance class. It has an exception for traces belonging to nets with edge-touching pins. Native validation must remain authoritative for these cases.

## Small bounded proposal

For the currently evidenced Default-only, one simple closed rectangular boundary, preserve every existing DSN atom except these additions:

```lisp
(boundary
  (path pcb 0 ORIGINAL_COORDINATES_UNCHANGED)
  (clearance_class kicadedge))
(rule
  ORIGINAL_RULES_UNCHANGED
  (clearance 300 (type wire_kicadedge))
  (clearance 300 (type via_kicadedge))
  (clearance 300 (type smd_kicadedge))
  (clearance 300 (type pin_kicadedge))
  (clearance 300 (type area_kicadedge)))
```

This is illustrative syntax, not an executable transform or qualified candidate. Derive 300 from the checked source project in DSN units; never hard-code CellScan's value. Append after the existing global and typed rules so a later default-clearance assignment cannot reset the edge row. Refuse an existing name collision, existing boundary class, malformed/duplicate rules, unknown units or unsupported source-edge semantics. Never alter general 200 micrometer or SMD-to-SMD 50 micrometer requirements.

The `wire_` pair creates any missing standard item classes. Their effective nonedge matrix values must equal the unmodified load exactly, including SMD-to-SMD 50. For this concrete DSN an even smaller two-pair variant may be sufficient: `default_kicadedge` plus `smd_kicadedge`, leaving item assignments unchanged. This depends on confirming that the loaded vias, THT pins, traces and areas all use class1 and SMD pads use only the existing SMD class. Prefer the five named item pairs unless the actual importer control establishes that smaller coverage; neither form should be represented as already tested.

CLI `--router.copper_to_edge_clearance_um=300` is another source-supported possibility, but its special guessed-default behavior at exactly250, pin-gap capping, named-outline replacement and full runtime parameter binding require care. The dedicated DSN class directly carries the original constraint and avoids the equality-to-guessed-default ambiguity. No arbitrary safety margin or stronger unrelated clearance should be introduced.

## Falsifying controls and scope limits

1. Inspect the actual pinned JAR after full load. Outline class must be the new nonzero class; every reachable copper item class must have symmetric 300 micrometer edge entries on every copper layer. Boundary geometry and all nonedge effective matrix values must match the unmodified load. Check the configured guessed-default override did not replace the new class.
2. Include global edge values 0,200,250,300 micrometers and fractional native units. Matrix integer rounding must never understate the source minimum; document any conservatism. `ClearanceMatrix.java:100–113` rounds values to nonnegative even internal units. Negative/NaN, contradictory or unrepresentable values must reject.
3. Native positive and invalid controls must demonstrate a via and track at the exact allowed boundary, inside it and below the required edge clearance. Final refill and DRC run against unchanged original rules and report bindings. The existing CellScan invalid via remains a negative observation, not an accepted board.
4. Named/custom netclasses need all reachable class pairs, not merely standard Default item classes. Arbitrary class names containing underscores are parser-sensitive. Existing explicit outline classes, local/custom edge rules or layer-dependent overrides require independent qualification or fail closed.
5. Cutouts are not covered by this proposal. `Structure.java:1324–1330` extracts holes and inserts separate obstacles with class0; a named outer-outline class does not automatically give those obstacles the source edge requirement. Do not claim exact cutout preservation from an outer-boundary probe. Nonconvex outlines, arcs/curves, multiple boundaries and edge-touching pads likewise need distinct controls.

Grant the corrected adapter uniformly to B1, B2 and C. Keep the earlier all-failed batch and the new240-second fully connected but edge-invalid result, with their actual costs. This correction cannot alone establish an equal-budget C improvement or broad routing completion claim.

## Access/error record

`network-receipt.json` records four bounded source GETs: all200, 39,288 bytes total, 0.950717 seconds aggregate script wall. The Rule primary web read is an additional access to the same revision. A mistaken additional web lookup for `board/HeadlessBoardManager.java` returned404; the correct `management/HeadlessBoardManager.java` was already cached and reused. `web-observations.json` preserves that lookup error. The parent also reports two earlier404 leads; their exact URLs were not supplied to this reviewer and no independent verification or retry is claimed.
