# Review and keep a routed KiCad project

The graphical entry point is `scripts/install_gui.py --output .runs/autorouter-launcher-001` in the prepared environment. Double-click its `Launch Autorouter.command`, open your saved project and PCB Editor, then click the green autorouter toolbar icon. This source-bound bootstrap creates local KiCad settings, plugins and cache without changing global configuration. It refuses observed other KiCad sessions or linked/oversized local state; close other KiCad windows first. [Bootstrap scope](gui-implementation-note.md). [Installed047](../evidence/installed-gui047-native-001.json) now qualifies readable findings, real in-worker cancellation, accept/fresh export and Improve90/reject in the standalone installed controller. [Actual048](../evidence/gui048-visible-budget-correction-001.json) now proves installed toolbar launch. That session exposed visible/captured budget mismatch after an accessibility edit, with no route run; the source correction reads displayed text directly. [Actual049](../evidence/gui049-inline-refusal-correction-001.json) engine cancellation passes, but a subsequent invalid-budget recovery stalled inside nested native menu/error modals. Current source uses the existing findings panel for routine refusals and defers method reset until the menu commits. Actual installed050 recovery/final qualification remains pending.

Choose **Route** for the fixed corrected-standard default. **Improve** is optional/experimental: it selects Tuned/Both algorithm settings and preserves routing protection, layers, budget and via preference. Unsupported partial/selected/layer combinations or a graphical Improve budget below90seconds visibly refuse; no source rule or budget is changed. This conservative operational minimum reserves incumbent/final checks and does not guarantee completion. Route and documented CLI budget contracts retain their own limits. Ordinary routing refusals show a bounded reason and full retained receipt; cancelled or corrupt work never authorizes export. Load/Save settings persists explicit preferences outside the source project.

Use Preview → Route → Create review, then Open preview and Open review project. Read every finding, including warnings and ignored checks. Close the review PCB and schematic editors, then choose **File → Close Project** in KiCad project manager before acknowledging review and choosing Accept intent. Closing an editor alone leaves the manager's lock and may defer automatic backups until a later project switch. The window keeps the valid route/review when an observed lock needs closing; it never removes a lock or ignores changed evidence. An absent lock does not establish that all editors are closed. Reject intent remains available without accepting or closing the review and never authorizes export. Fresh export reruns original-rule Native checks and writes another separate project. Cancel waits for cooperative worker cleanup. The original saved source is never overwritten, and there is no tested live-editor transaction or undo. The CLI and structured receipts underneath remain available:

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

[Current installation042](../evidence/installation042-native-001.json) qualifies an independent local distribution/venv on this Mac, with actual default10.0.0 partial and explicit experimental10.0.7 whole four-copper routing. [Installed four-copper workflow042](../evidence/installed-fourcu-workflow042-001.json) generated eight native plots across F.Cu/In1.Cu/In2.Cu/B.Cu and freshly validated the exported full-schematic project, preserving all ten protected source tracks, six warnings and two ignored checks. Both acceptance and rejection were software test inputs. The Mac was locked at the new GUI access attempt, so this adds no new GUI qualification. Earlier GUI evidence above retains its exact source/tool bindings. Production defaults remain KiCad10.0.0.

[Current installed044 workflow and GUI](../evidence/installation044-native-001.json) adds four two-layer native plots, accept/reject test intents and a fresh full-schematic export. An actual disposable copy opened through Manager/PCB Editor and ran one refill/parity check with all filters: zero violations, zero unconnected items, six retained Datasheet warnings and two ignored checks. The saved report is preserved. Its PCB/SCH and the authoritative export remain exact;335disposable PRO/PRL configuration differences are recorded. Current saved customization also passes. This supersedes earlier locked-access next steps, while earlier four-layer/1007 results keep their separate scopes. No live application/undo or human/electrical/physical approval.

[Installed046 GUI](../evidence/installed-global-width-gui046-001.json) now repeats that actual external workflow for the installed strict-width candidate: refill/parity/all filters,0violations/0unconnected/6Datasheetwarnings/twoignored and a saved native report. The four authoritative project files and disposable PCB/SCH remain exact. Local PRO/PRL/configuration changes are retained in the disposable workspace. This closes046 locked access only; no live application/undo, freshOS or human/electrical/physical approval.

Open checked export performs another cancellable `review-export-check` through the existing CLI before opening the exact exported project. Its new check log remains in the job workspace. Missing, changed or cancelled evidence refuses opening. This is a sampled check before handing the file to KiCad; opening or editing a mutable project can subsequently change metadata and invalidate the stored consistency proof. No immutable editor or atomic check-to-open guarantee is claimed.
