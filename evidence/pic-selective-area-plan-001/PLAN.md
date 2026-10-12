# Selective custom-area obstacle plan — source only

The pinned engine supports changing only the two synthetic custom bodies after the manager has finished loading. This is a justified next **observation**, not routing or native equivalence qualification. Start from the existing `plane_as_obstacle=false` import; keep the original GND area's obstacle flag false, set the two identified USER_FIXED bodies true, explicitly set the global `ignoreConduction` flag false, and refresh the search tree. The global flag change must be recorded; “all original board state unchanged” would be too broad.

No Java, compiler, router or native board execution was performed for this plan. No current source was changed. The parent reports 287 original-plane collisions and 31 sub-micrometre source segments changed by DSN export; those are motivating leads here, not independently re-audited results. Selective obstacles do not repair the coordinate-survival failure or prove that routing will succeed.

## Exact implementation evidence

All engine sources are pinned to `b647a2f824cfbc54bc4dcaee71b03b7cd945eb76`, with actual public-declaration receipts binding JAR `f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7`. Local paths, sizes and full SHA-256 digests are in `bindings.json`, `additional-bindings.json` and `network-receipt.json`.

| Cached implementation | Consequence |
| --- | --- |
| `ConductionArea.java:389–413` | `setIsObstacle` changes only the local boolean. `isTraceObstacle(net)` and `isDrillable(net)` respect it; no cache refresh occurs in the setter. |
| `RoutingBoard.java:1268–1293` | `changePlaneAsObstacle` changes **every signal-layer area**, inverts `rules.ignoreConduction`, then reinserts tree items. Calling it after a selective patch would overwrite that patch. |
| `HeadlessBoardManager.java:623–632,839–881` | The manager applies that global override during loaded-board settings. Await the already-qualified post-load future before applying the selective changes; do not reapply settings afterward. |
| `SearchTreeManager.java:186–199` | `reinsertTreeItems` removes all entries, clears every item's cached derived shapes, and reinserts. Public declaration and `validateEntries(Item)` were already observed in the actual JAR. |
| `BoardRules.java:373–379` | `setIgnoreConduction` is only a field assignment. It supplies no independent tree refresh or routing qualification. |
| `ShapeSearchTree.java:1033–1062` | Obstacle-area tree geometry is split and clearance-enlarged regardless of the local flag. A false GND area may remain present in raw overlap results. |
| `ObstacleArea.java:175–181` | The item-overload obstacle predicate accepts foreign **Trace or Via**, not Pin. Consequently `area.isObstacle(foreignPin)` is not a valid expected-positive test, even for an enabled area. |
| `Item.java:163–165`; `BasicBoard.java:1013–1038,1048–1105` | Generic `checkShape` uses `isObstacle(int)` (net exclusion only), which does not respect the per-area boolean. `checkTraceShape` explicitly filters with `isTraceObstacle(net)` and is the appropriate trace-specific path. |

The three implementations missing from the prior cache were acquired from the official pinned source URLs in `network-receipt.json`: 78,103 bytes total, no executable dependency or dataset acquisition. The cached project license record identifies GPL-3.0 source; public selection excludes those source copies and preserves the unresolved bundled-JAR generic-license-entry caveat from earlier research.

## Smallest extension to the existing observer

Reuse the mixed import controller, original DSN/context pins, local250 proof, frozen source/tool checks, shared 180-second wall/full-CPU and 64-MiB output limits. One imported board is sufficient; no solver, SES writer, fresh native export or new framework is needed.

1. Import with router/optimizer disabled, `plane_as_obstacle=false`, and the existing unchanged empty explicit plane-net list; await post-load completion. Apply the already-qualified local250 override and its refresh. Capture full baseline state/ordinary route geometry and all area flags before further changes.
2. Resolve exactly the two existing synthetic USER_FIXED bodies by the existing original-pad/net/layer/integer-ring proof. Their association to the original JP1 pads is diagnostic scope, not a production name whitelist. Retain the full census and original SYSTEM_FIXED GND area's identity, geometry, class, nets and false flag. Do not choose “all non-GND areas” or rely on item-count order alone.
3. Set only those two `ConductionArea.setIsObstacle(true)`, then `board.rules.setIgnoreConduction(false)`, then `board.searchTreeManager.reinsertTreeItems()`. Validate entries for the complete bounded item population. Reject missing/extra targets, unexpected count, failed tree validation or changed original GND flags.
4. Capture the full state again. Reverse comparison may change only the two flags, the global ignore flag and corresponding derived obstacle/clearance observations. All item identities, fixed states, geometry, net/class memberships, matrices, widths, layer order, plane-net flags, route geometry and reciprocal contact sets must remain exact. Retain unexpected counts and observations before rejecting.
5. Record each area’s `getIsObstacle`, `isTraceObstacle`/`isDrillable` for own and foreign net numbers and item-overload predicates against actual foreign ordinary traces/vias. Classify clearance pairs by exact item IDs. Require the original false GND area to remain nonblocking under the **trace-specific** predicate, while each enabled custom body blocks foreign traces and remains contactable by its own net.
6. Reuse existing bounded tree-overlap inspection and trace tiles for `checkTraceShape(..., contactPins=null)` where a trace-specific board check is needed. Keep raw overlap IDs separately from flag-filtered blockers. Do not demand a globally clear false-mode query: anchors and other original copper can independently block it. Do not interpret a raw GND overlap as a failed selective flag. No invented geometric clearance exemption is allowed.

Useful prospective falsifiers are: one body left false; original GND enabled; wrong fixed state or target ring; matrix/width or route change; a later global settings reapplication; missing refresh/invalid entries; mislabeled generic `checkShape` as the selective predicate. Source inspection alone cannot prove the “missing refresh” case manifests a failure, so retain the observed result instead of forcing a negative claim.

This is sufficient to decide whether the pinned engine can represent the intended selective obstacle state on the retained board. A real routing lifecycle could reapply settings or otherwise consume `ignoreConduction`; that behavior remains a later gate. This cache inspection is not an exhaustive proof of every reader of the global flag. Native custom-pad geometry, original mixed clearance, retained-route SES survival, engine connectivity and native route acceptance remain separate obligations.

## Cached explanation for SES package labels

The cached **actual JAR bytecode** already explains trailing numeric package suffix removal; no new source/API survey was needed. In `.runs/pic-padstack-engine-inspection-001/app.freerouting.io.specctra.parser.Library.txt` (SHA `bc3f881b630eec3c2dce159ade3047f6ed7244af6101c8c00c472446e23861c3`), `readScope` begins at file line 574. Lines 1024–1034 / bytecode offsets 1058–1085 apply Java `String.replaceAll` with regex `::\d+$` and empty replacement to `Package.name`. Lines 1037–1105 then perform side-aware package lookup and pin-comparison deduplication, advancing a suffix counter when the pin set differs. It is not a universal promise that every suffix is simply absent in output.

`SesWriter.java:117–145` (SHA `a85f67a084f7c8164afd563b358c2782f42711b205188adac04f515a01ddd44d`) writes the resulting runtime `pkg.name`. This explains the parent's observed `::1/::2/::3` label difference. The cached KiCad `SPECCTRA_DB::FromSESSION` resolves each placement from `place.m_component_id` (reference), not the enclosing component/package label. Retain reference-to-pad and position/side/angle equivalence, original native footprint bytes/semantics and exact source-to-engine package mapping; do not waive those because a name regex matches. Angle equivalence modulo 360 must be narrowly checked separately. This observation does not reverse any failed original SES or coordinate-survival verdict.
