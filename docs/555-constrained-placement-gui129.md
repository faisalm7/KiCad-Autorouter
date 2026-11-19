# 555 timer placement evaluation

Copperpath admitted the original MIT-licensed 555 timer project in KiCad 10.0.7. The saved source had zero opens, zero blocking findings, nine footprint-library warnings and five ignored checks preserved from the project. The same runtime had just completed its owned toolbar-to-export qualification. [Pinned publisher project](https://github.com/nitu2126/kicad-learning-path/tree/856b0daf1d358504cd035724f5ec9d1e6bfe3ad7/02-555-blinker) · [License](https://github.com/nitu2126/kicad-learning-path/blob/856b0daf1d358504cd035724f5ec9d1e6bfe3ad7/LICENSE) · [Installed qualification](../evidence/product104-usability-delivery-001.json).

The trial moved no parts. The operator selected R1 and R2 visually and requested that their complete courtyards fit within x 104.35–106.65 mm and y 81.30–90.45 mm. The declared plan permitted rebuilding 28 tracks on +5V, /DISCH and /TIMING after explicit review. It required the seven other parts, 24 unrelated tracks, original rules, orientation and zone intent to stay fixed. The single two-second search reported no starting placement. No placement validation, Freerouting or export started. All 52 original tracks and the original files remain exact. [Evaluation receipt](../evidence/product104-GUI129-555-001.json).

## What constrained the placement

An exact-source readback examined the same clearance model after the trial. Both full courtyards measure about 1.95 × 3.41 mm. The allowed rectangle gives their centers 0.35 mm of horizontal movement, so the parts need at least 3.71 mm of vertical separation with clearance. The model's bounding rectangles for two protected ground tracks leave only 2.99 mm of vertical separation across the full allowed width. That rules out the pair under the present model. The physical corridor under exact track geometry remains untested. The original constraint and result were retained without another search.

## Observed workflow

| Measure | Result |
|---|---:|
| Timed setup through observed refusal | 3 min 28.11 s |
| Inspection click to observed result | 2.84 s |
| Search click to observed refusal | 1.13 s |
| Operator-equivalent steps | 17 |
| Manual CAD edits applied | 0 |

The elapsed session includes automated control and observation time. The step count combines the system dialog's navigation into one step. There was no owner intervention. One script stopped before launching due to a bad log path. A second checked the window before it appeared. The direct picker and visual part selections worked. Manual repair time and delivery time remain unmeasured because the task stopped at placement.

The refusal offered little help identifying the limiting constraint. Displaying the actual rejected checks beside the current region and source findings is the immediate usability improvement. Release gaps include broader protected-copper placement coverage, a complete independent installation and engineer walkthrough, and qualification of the optional copilot on more than its one owned task. Geometry, visual review and approval gates remain shared by ordinary and model-assisted workflows.
