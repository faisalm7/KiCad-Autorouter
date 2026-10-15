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

Actual qualification: installed LED GUI003 observed full refill/parity with every filter enabled; the isolated CLI's seven library warnings remain authoritative despite the different GUI library context. Current preset-driven pruning has a real five-command preview/accept/reject/fresh-native-export test with exact original constraints and seven warnings. Later GUI access reported the Mac locked, so current CellScan/preset candidates have no new GUI observation. See [GUI evidence](../evidence/installed-led-export-gui-003/SCOPE.md), [current product controls](../evidence/pruning-preferences-native-product-003/SCOPE.md) and [status](../STATUS.md).

Native validation does not establish electrical performance, manufacturing readiness or physical safety. Human PCB review and physical validation remain outstanding. Earlier workflow implementation details and GUI failures are preserved in Git history and their original evidence packets; no failed result was reclassified by this documentation update.

Current source also preserves existing local-settings files in disposable
routing, plotting and validation copies. A real complete-project test with an
older settings file passes preview and fresh schematic-parity export with all
seven warnings retained; a disconnected candidate is rejected and real engine
cancellation cleans up. See [the Native workflow evidence](../evidence/normal-prl-native-workflow-001.json).
This extends CLI/workflow qualification; GUI008 still reports the Mac locked.
Installation026 predates this source change.

Current scoped-source complete-schematic export is Native-validated with all seven warnings preserved. Its exact disposable GUIcopy004 was prepared, but the Mac locked again at the open-project command. No new GUI qualification follows. [Current real controls](../evidence/scoped-native-workflows-001.json).

The prepared complete-schematic scoped export now also has an actual GUI test: [GUI006](../evidence/normal-prl-export-gui006-001.json). It ran zone refill and schematic parity with every finding filter enabled, saved a report with zero GUI findings and the five original ignored checks, and preserved all original saved files. Its seven isolated CLI library warnings remain in the validation evidence. This observation closes that earlier access gate only; it does not establish human PCB approval or live-editor application/undo.

Closing the complete-schematic GUI test updated `schematic.used_designators` in its disposable project file, even though the PCB was closed without saving. This is recorded separately from the successful DRC. The authoritative validated export stayed exact. Treat the opened review copy as an inspection workspace and keep the fresh validated export as the handoff; project changes need validation again.
