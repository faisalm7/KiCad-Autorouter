# Placement scope follow-up from 2427b2ebd

## NUS USB-C LED

Keep the original licensed board and frozen R1 task. The installed assessment stopped at source inspection. Its saved PCB matches SHA-256 `a8e69c14ceec9dd0954c3027cc89ca6bbb9c0b0ec3aeede5feacfdd47736f362`. The following checks use the same bytes. [Frozen task](workspace-delivery-qualification.md) · [Actual refusal](../evidence/product-workspace-nus-scope-001.json)

| Feature | Observation and consequence |
|---|---|
| Outline | Four `gr_arc` corners close the four straight Edge.Cuts segments. The rectangular placement solver cannot use the bounding box as the physical outline. |
| Vias and protected copper | Six front-to-back vias and 35 segments stay fixed. Six segments on the two approved R1 nets are the only rebuild candidates. The R1 courtyard is 3.30 × 1.46 mm before its stroke. Even omitting the stroke, every position in the original strip puts the courtyard within 0.39 mm of the via centered at X 158.75, Y 95.25 mm. Its copper radius is 0.50 mm before clearance. The protected via UUID is `71990440-f7e7-464d-a3f8-90f401ab617f`. This blocks the frozen R1 task under the existing courtyard protection model. |
| Rule area | The front-layer **No GND fill** rectangle at X 156.845–159.385, Y 90.805–92.075 mm prohibits copper pour. Its flags allow tracks, vias, pads and footprints. Preserve both the flags and the area. Copper refill and saved-fill readback still matter. |
| Other placement gates | The back-silkscreen knockout text uses a distinct field. Fixed J1 has ten pads, including four oval plated S1 slots with 0.6 × 1.2 mm drills. Legacy footprints lack the explicit jumper metadata required by the checked source-baseline scope. The current product search also requires a pair. Supporting a general one-part search needs separate qualification. |
| Routing | The actual selected-routing preflight rejects F.Cu `mixed` and B.Cu `power`. That gate remains even with placement geometry support. |

This is a limit of the original task and current placement contract. Physical fit and other regions have not been tested. The bounded local census found 42 unique retained licensed sources within the placement byte ceiling. Each source with vias as its only extra top-level item exceeds another current placement bound. Keep the already measured MIT PushButtonLed R1/R2 delivery as an exposed workflow reference. [Licensed reference](../evidence/runtime094-licensed-placement-delivery-001.json)

## Bounded extension and new owned test

Keep the existing actual rectangular outline gate. Admit standard two-layer, front-to-back through-vias only in placement with the exact source-baseline and Native witness. Preserve the via UUID, net, position, drill, diameter, layer span, lock and free flag. The full annulus and clearance bound every proposed courtyard. Vias on any requested rebuild net refuse before preparation. Other via types or manufacturing attributes and placement rule areas still refuse. KiCad checks final rules and refill after the original-copper check.

Use one generated owned fixture. Copy the saved owned-placement project into a new directory. Add a 0.60 mm diameter, 0.30 mm drill through-via on the existing KEEP trace at X 19, Y 16 mm, and a 0.30 mm KEEP back segment between that via and the existing pad at X 12, Y 16 mm. Keep every original object. The prepared fixture keeps the prior task of translating J1/J2 into X 14–22, Y 8–13 mm and rebuilding only ROUTE_A and ROUTE_B. Preserve the three KEEP objects. Run the first 2-second search only, placement validation within 120 seconds, routing and fresh export within 85 seconds each, and existing 60-second review and choice limits. A separate check deliberately puts a selected courtyard over a via and must refuse. Stop at the first unsupported or failed stage. No licensed-board delivery or coverage expansion follows from this owned control alone.

The first installed route stopped before Freerouting. KiCad exported the
0.60/0.30 mm locked-for-transport via beside the default 0.80/0.40 mm via.
Placement and its detached validation had already succeeded. The correction
requires matching saved-task positions, net and shapes for the fixed vias. It
keeps their definitions and exact wiring, and offers only the lawful Default
choice for new routing. Multiple-size transport refuses padstack names that
Freerouting would rewrite and fixed centers it could round or merge.
The single corrective attempt used the same source, first alternative and
budgets. It completed both routes and produced a current independently
checked export with the via and both protected tracks exact. The first
refusal remains part of the evidence. [Installed result](../evidence/product-workspace-through-via-001.json)

## Straight protected tracks in a two-part destination

The new destination policy measures clearance to the saved straight track
itself. It uses the complete stroked courtyard, source endpoints and width,
and the same 0.30 mm placement clearance. The earlier rectangle still serves
as a quick check before the exact distance check. Protected vias keep their
existing conservative clearance bound. Copper permissions, fixed geometry,
actual KiCad checks and final readback still apply. A loaded earlier preset
retains its original geometry policy. [KiCad track geometry](https://docs.kicad.org/doxygen/pcb__track_8cpp_source.html)

The installed follow-up used the exact saved MIT 555 project and the same
R1/R2 task, destination, 24 protected routes, 28-track rebuild plan and stage
budgets. One search and the first placement passed KiCad and exact geometry
readback. The placed copy has ten expected opens, zero blockers and nine
warnings. Routing preview refused the saved parent `Power` class in
selected-net mode. No routing ran and the trial stopped before delivery.
The earlier refusal stays in the record. [New placement and refusal](../evidence/product-straight-track-placement-555-001.json) · [Frozen original trial](555-constrained-placement-gui129.md)
