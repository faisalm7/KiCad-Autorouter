# Safe external KiCad workflow — experimental

The tested workflow writes a separate complete candidate project and never replaces an open board. It does not detect unsaved editor changes or support transactional editor undo. Save and close the source project before routing; use the exact board path, including its matching project/rules/library files. Selected-net routing is unavailable. Whole-board mode removes only unlocked routing; `--keep-existing` protects all original routes for partial completion.

```sh
python3 -m autorouter route '.data/boards/kicad-sonde-xilinx/sonde xilinx.kicad_pcb' --adapter both --seconds 120 --output .runs/manual-route-001
python3 -m autorouter check-result .runs/manual-route-001/result.json
python3 -m autorouter review-copy .runs/manual-route-001/result.json --output .runs/manual-review-001
```

Each output path must be new. `check-result` checks consistency of local saved evidence and current source/candidate files. It is not fresh DRC or cryptographic authentication of editable JSON. `review-copy` makes a disposable copy after these checks. Open the printed board inside its `project` directory in PCB Editor. Inspect the routes and metrics, then run **Inspect → Design Rules Checker → Refill all zones → Run DRC**, with errors, warnings and exclusions visible. A native routing acceptance is not manufacturing or electrical approval. Whole-project warnings and ignored rules remain visible.

To reject, close the disposable project and discard its board changes; the original and accepted evidence are preserved. To keep working on a candidate, use this separate project as a new design version after PCB review. Do not overwrite a source that has changed since routing. Saving or editing a review copy creates a new, unvalidated design; rerun validation before relying on its earlier result. No command applies it automatically to a live editor. A fully qualified production acceptance/undo flow remains unfinished.

## Actual GUI test on this Mac

October9,2026: KiCad10.0.0 PCB Editor opened a disposable copy of the combined B1 result from `adapter-ablation-001`. The actual board rendered with108pads,3vias,257tracksegments,42nonzero nets and0unrouted. The native GUI DRC, with zone refill enabled, reported0errors,0unconnected,25warnings and0exclusions. Schematic parity was not run. The raw GUI-exported report and hash inventory are in `evidence/gui-inspection/`.

All25warnings were the existing GUI configuration not enabling the project footprint library `sonde-xilinx`. The isolated CLI run instead reports one DSUB9 library-footprint mismatch. No application preferences or library settings were changed to suppress either result. This is a real configuration difference, so the GUI test is not a byte-identical reproduction of the CLI report.

The four ignored GUI checks were copper connection width, track endpoint centering, tuning-profile geometry, and footprint filters. Original rule severities were retained by the routing pipeline; these are not evidence of full electrical correctness. No ignored-rule settings were changed during the test.

Closing with **Discard Changes** preserved the disposable board's bytes, but KiCad still upgraded its `.kicad_pro` defaults/version and created `.kicad_prl` and a local `.history` repository. This observed behavior is why GUI review must use a disposable complete project copy. The accepted run and source were never opened in the editor. PCB Editor was confirmed closed afterwards. No screenshot was saved; the actual exported report and recorded tool observations are the durable evidence. Plugin execution, multiple open boards, unsaved-change detection, cancellation from GUI and undo are not qualified.
