# Review and keep a routed KiCad project

This workflow creates separate complete projects. Save and close your source project before routing, and select its exact `.kicad_pcb` path with the matching schematic, project and rule files beside it. The original stays preserved. Unsupported constraints stop the attempt with a reason.

Use the prepared project environment from Terminal:

```sh
cd ~/Projects/KiCad-Autorouter-local
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B -m autorouter route '/path/to/MyBoard.kicad_pcb' --adapter both --seconds 120 --output .runs/my-route-001
.venv/bin/python -B -m autorouter check-result .runs/my-route-001/result.json
.venv/bin/python -B -m autorouter review-copy .runs/my-route-001/result.json --render --output .runs/my-review-001
```

Use a new output name for every attempt. Press **Control-C** in the routing terminal to cancel. A failed, cancelled or stale result cannot authorize acceptance. [Saved settings](routing-preferences.md) configure scope, permitted new layers, budgets and optimization. Whole-board routing protects locked copper; `--keep-existing` protects all existing copper for partial completion. The separately qualified experimental `improve` command gets its own fresh incumbent before pruning.

The review folder contains a complete disposable KiCad project and `preview.html`. The preview shows original and candidate copper on each layer with board edges, route metrics and all recorded findings. Plotting uses saved fills; it does not perform a new DRC or establish electrical approval. Original reference routing is visible for review but is not supplied to the optimizer.

Open the printed review `.kicad_pro` in **KiCad Project Manager**, then choose **Tools → PCB Editor**. Opening the board directly can load different library settings. Inspect the routing, then use **Inspect → Design Rules Checker**, enable **Refill all zones** and **Test for parity between PCB and schematic**, and run DRC with errors, warnings, unconnected items and exclusions visible. The test for schematic parity requires the complete matching schematic.

After PCB review, record your choice:

```sh
.venv/bin/python -B -m autorouter review-choice .runs/my-review-001/review.json --choice reject --output .runs/my-reject-001
```

For an acceptance choice, use this alternative and export a fresh validated project:

```sh
.venv/bin/python -B -m autorouter review-choice .runs/my-review-001/review.json --choice accept --output .runs/my-accept-001
.venv/bin/python -B -m autorouter review-export .runs/my-accept-001/choice.json --seconds 120 --output .runs/my-export-001
.venv/bin/python -B -m autorouter review-export-check .runs/my-export-001/export.json
```

The exporter repeats native refill, full DRC, schematic and original-design checks. Keep the exported complete project as a new design version after review. An acceptance record expresses your intent; it is not a human PCB review certificate. A rejection cannot authorize export. Source edits, changed evidence or expired budgets invalidate the result. All inherited warnings and ignored checks remain visible; routing acceptance and whole-project DRC cleanliness are separate.

Saving changes in the disposable GUI review can change project defaults and create local settings/history. Those edited files are a new unvalidated design. Use the fresh exported project and its proof as the handoff, and validate any subsequent edits. This external workflow cannot inspect unsaved editor buffers, apply a transaction to a live editor or promise tested undo.

Current qualification includes [Roller workflow002](../evidence/roller-current-workflow002-native-001.json): actual before/after copper plots, accept/reject test intents and fresh complete-schematic Native export, preserving zero opens, zero blocking findings, one SW1 warning and nine original ignored checks. The original workflow001 ceiling failure remains recorded; the fix reuses complete consistency checks within the operation and retains the same 30-second preview limit. No routing engine was repeated.

[Actual Roller GUI001](../evidence/roller-export-gui001-001.json) opened an exact disposable export copy through Manager/PCB Editor, ran refill and schematic parity with all finding filters enabled, and saved the same one-warning/zero-open/zero-parity/nine-ignored result. KiCad migrated the disposable PRO when closing, adding new-schema defaults and tuning metadata; all deltas are recorded. The saved PCB/SCH and authoritative export remain exact. Treat that GUI copy as an unvalidated inspection workspace. The earlier [complete-schematic LED GUI006](../evidence/normal-prl-export-gui006-001.json) remains qualified in its own scope; its GUI/isolated-CLI library-warning difference remains visible.

Current-source [installation032](../evidence/installation032-native-001.json) qualifies an independent local distribution/venv and real Native smoke on this Mac. These observations do not establish live editor application/undo, human PCB approval, electrical performance or manufacturing readiness. No old failed result was relabelled by these updates.
