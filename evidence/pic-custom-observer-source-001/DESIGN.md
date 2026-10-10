# Pic custom polygon controls: prospective owned diagnostic design

No native, engine, GUI, network or production edit was executed. This directory contains only a fixed geometry recipe, analytic checks and an unexecuted native-control design. The existing custom-pad/preflight gate stays closed. These owned diagnostic cases are development-exposed controls, not new corpus inputs, independent families or holdout evidence. The full-board source and every original rule remain immutable; no full-board outcome has selected or changed this recipe.

## Narrow primitive and original settings

Use the two exact five-vertex, filled, width-zero polygon shapes from the acquired pic_programmer JP1, each with its original0.3×0.3mm rectangular anchor and `clearance outline`. One copper side plus matching mask only; no hole, drill, arc, additional primitive, offset, custom padstack or zone. The polygon coordinates in `recipes.py` match the original board pads exactly. The convex shape's hull equals its real polygon; the concave shape's hull drops the inward vertex.

An important source fact: the concave anchor's left edge touches the notch vertex(-0.15,0). It is wholly contained **including boundary**, but not strictly inside. A blanket positive-margin anchor requirement would exclude the actual intended source. Do not enlarge/remove the anchor, infer a hole or flip a native topology flag to force admission.

Preserve every byte of `pic_programmer.kicad_pro` across every case. Its Default preferred track width is0.5mm, clearance0.25mm and minimum track width0.25mm. Both new diagnostic net names CONTACT and FOREIGN resolve to Default; configured POWER/GND/VCC bindings remain untouched and unused. Use0.5mm tracks throughout. No class preference, minimum, severity, ignored check, exclusion, library table or alias is weakened. The native observer must verify resolved classes/rules rather than assuming the source JSON is attached.

Retain the complete15-file original project/notice inventory as immutable evidence. For later native execution, make a disposable complete project copy, replace its board with the newly authored diagnostic board under the matching basename, preserve all other14 original files byte-for-byte, and bind this derivation explicitly. The diagnostic board has its own UUIDs and geometry; it is not represented as the original pic board. No script from the dataset runs. The inherited geometric primitive is attributed to official KiCad demos commit69cafb907ebc09e7722a2a464b1d466fc2e3608d, CC-BY-SA4.0; retain both original notice files. Control code is project-authored. Do not publish third-party source files without their original notices.

## Fixed front geometry, millimetres

Board edge is the rectangle(0,0)–(40,30). All copper is F.Cu and all ordinary clearances to edges are generous. No zones, vias, keepouts, text copper or extra thermal mechanism.

| Identity | Geometry / net |
|---|---|
| CONVEX | Exact convex source custom pad centered(10,15), CONTACT |
| CONCAVE | Exact concave source custom pad centered(20,15), CONTACT |
| FOREIGN_A / FOREIGN_B | Ordinary1.5mm round SMD pads centered(20,6)/(20,9), FOREIGN |
| CONTACT_TRACK |0.5mm segment(10.5,15.25)→(20,15.5), CONTACT |
| FOREIGN_TRACK |0.5mm segment(20,6)→(20,9), FOREIGN |

A single self-contained footprint may hold the two custom pads at the stated local offsets; the two round pads may be distinct reference footprints. Unique references/numbers/UUIDs must be declared before execution. No original footprint-library identity is fabricated for these owned embedded test footprints. Courtyard/library warnings, if emitted under the original project, must remain visible; do not suppress them. Positive qualification requires0opens/0blocking/0exclusions with unchanged native ignored settings and no policy-critical warning, not a promised whole-project warning count.

Exactly three cases are declared for each of two transforms:

1. **Positive:** unchanged geometry above. Both custom pads contact real polygon copper outside their anchors on CONTACT; both ordinary pads contact their own FOREIGN track. All four required terminals must be connected to their corresponding counterpart. A native clean routing predicate plus exact geometry/terminal census is required.
2. **False hull landing:** change only CONTACT_TRACK's endpoint from(20,15.5) to(19.4,15). Its endpoint is pad-local(-0.60,0), strictly inside the exported concave convex hull but outside actual polygon/anchor copper. The entire0.25mm-radius track capsule is disjoint from actual custom copper, not merely its centerline. Exact squared centerline gap is140192307692.307692…nm²; the copper gap is124422.632452nm (0.124422632452mm), well above the source10µm polygon error setting. The track still contacts CONVEX. Native **must** identify CONCAVE as disconnected from the CONTACT component; a native report with0opens is a failed negative, not a successful approximation. A narrower track was deliberately unnecessary.
3. **Foreign intrusion:** retain CONTACT_TRACK and change only FOREIGN_TRACK's endpoint from(20,9) to(20,14.4). FOREIGN_B remains on that same segment, so the intended FOREIGN connection is retained. The segment positively overlaps real CONCAVE polygon copper at local(0,−0.6), while remaining disjoint from the anchor and farther than the original0.25mm clearance from CONTACT_TRACK. This avoids a false qualification caused solely by track–track detection or anchor geometry. Native must emit an unexcluded error of type `clearance` or `shorting_items` that binds both the FOREIGN_TRACK UUID and CONCAVE UUID. An error involving only another CONTACT track is insufficient. Unrelated errors, mere source-invariant rejection, or an engine failure do not satisfy this negative. Expect0opens; an unexpected open is retained and investigated rather than silently broadening the predicate.

Pure tests additionally prove the complete positive CONTACT capsule stays disjoint from both anchor rectangles, so a validator ignoring the custom primitives cannot pass merely through anchor contact. The foreign negative similarly requires actual polygon copper. The pure test also checks that an incorrect false-case endpoint at local(-0.20,0) really overlaps copper and is rejected as a geometry recipe. This is a useful test of the negative, not a native result.

## Rotation and backside check

Repeat all three fixed cases on B.Cu/B.Mask after the exact rigid reflection-plus-quarter-turn transform **T(x,y)=(40−y,40−x)mm**, applied to every board edge, footprint/pad center, primitive and track. This preserves all exact distances and clearance relationships, but reverses winding and changes the copper side. It tests both convex and concave pad roles, and carries the same false-contact falsifier through the transform.

The eventual fixture writer must encode actual nonzero footprint/pad rotation and a backside footprint, then require native per-layer effective polygons to equal this predeclared world geometry (up to cyclic vertex start and winding). Merely rotating serialized vertices while leaving all native orientation/flip fields zero is not a transform qualification. KiCad's angle sign, absolute pad orientation and flip primitive semantics must be verified; do not infer the transform from the B.Cu label alone or reselect expected coordinates after DRC. A mismatching construction fails before interpreting the native control. `recipes.py` is world-space truth only; it does not claim that an untested serialization/API operation produces that truth.

Pinned10.0.0 source supports this caution: PAD::Flip changes relative orientation, layers and custom primitives (`pad.cpp`1454–1532); custom TransformShapeToPolygon rotates merged local copper by pad orientation and moves it into position (2619–2624). Existing observer author owns the native extraction. Its installed-layer getter issue must remain fail-closed; the new recipe does not replace native observation with guessed geometry.

## Native predicates and evidence boundary

Reuse the current FloorJob/runner/native DRC primitives and strict report parser; do not create another route lifecycle. Root alone later schedules the native batch. The common source preflight must still reject these custom-pad fixtures until qualified production support exists; record that expected unsupported scope, never bypass the gate and label the result accepted routing. A separate explicit diagnostic may call the pinned nonsaving native DRC on its own immutable copies, as prior deliberate-unsupported controls did.

Before each DRC, freeze candidate/project/complete input tree, known case recipe and exact UUID/net/layer/world polygons. Use same-load observer/export to bind custom merged local copper, effective world polygons, anchor size/shape, native netclass, footprint/pad angles/flip and DSN ref→image→pin→padstack/net mapping. Require the convex export to represent its convex polygon and concave export to represent its hull under pinned semantics; do not call the hull exact copper. No engine or SES import is part of this first native-only batch. A later solver/import proof is separate and cannot be inferred from it.

After native in-memory zone refill, parse the raw bound report with all severities/exclusions visible and require unchanged original settings/default observations. False-contact pass requires an actual `unconnected_items` error with CONCAVE's UUID and an item in the independently verified connected CONTACT component (CONVEX or CONTACT_TRACK), strictly positive native opens, and no excluded finding. A generic central AST exception, unrelated open, changed net assignment, ignored connectivity rule, missing report or native crash is failure. Every negative must be paired with its same-transform positive. If the hull-only case returns no open, stop qualification and retain a native-connectivity defect; do not proceed to full-board routing on the strength of geometry invariants alone.

Reserve one shared **180-second wall and measured parent+all waited-child CPU** control budget for six sequential cases, including preparation, observations/exports, failed attempts, DRC and final publication. No engine job. Native observation of the original board is a separate previously declared60-second task, not free comparison overhead. Reuse the shared experiment lock, isolated settings, sandbox network denial, existing RSS/disk/log polling and strict committed code/tool/input snapshots. Retained batch artifacts capped250MiB; original15-file payload1,366,598B means twelve complete case/DRC input copies would be16,399,176B before replacing the original large PCB with a smaller fixture. Precompute actual copy reservation. Budget/run failures remain failures and no canonical successful control summary may survive staleness, cancellation, final-size mutation or final-cap crossing. No persistent worker.

## Go/no-go and scope

Only successful original observation plus both orientations' native positive/false-hull/foreign-intrusion controls can justify a narrowly reviewed support implementation. Four unknown severity keys still need source/native semantic handling; shape controls do not prove those providers ran. Imported routing, DSN/pin/rule mutation receipts, original geometry preservation, full native acceptance and fair B0/B1/B2/C experiments remain separate subsequent work. The existing C feedback-pruning mechanism is already selected prospectively; do not pick a new algorithm after observing pic's full-board outcome.

No acquisition, support expansion, alias substitution, family-count increase, C win, GUI, physical or human PCB qualification follows from this design or its pure controls.

## Preparation verification and next owner step

13 pure fixed-geometry tests passed in0.002s (`pure-controls-002.log`); `audit.py` independently matched all15 source/notice files,1,366,598bytes, exact247pad/63footprint census, both primitive shapes and the original project hash, then rehashed originals unchanged. Exact whole-segment/capsule checks, not sampled endpoint guesses, prove the false landing remains124422.632452nm from actual polygon copper for both transforms. Positive copper contacts and foreign intrusion are disjoint from their anchor-only explanations.

`snapshot-001` preserves the initial proposed geometry before strengthening positive contacts to require actual polygon copper outside the anchors and separating the foreign intrusion from the CONTACT route. No native run used either version. The updated six cases in audit.json are the current prospective design. Existing full-board source results have not changed.

Reproduce geometry tests with `python3 -B -m unittest discover -s .runs/pic-custom-controls-design-001 -p test_recipes.py -v`. Static audit output is immutable; rerun audit.py only from a new owned copy without audit.json. Next: root/independent reviewer inspect this design after the original-board native observer is qualified, then implement a small diagnostic controller by reusing existing runner/Job/report bindings. No executable native driver is supplied here, and no production eligibility change is proposed from pure tests.
