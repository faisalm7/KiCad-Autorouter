# Route and review from KiCad

The current tested directory is **runtime013**, source `c31fbeb8`. [Fresh Native qualification](../evidence/runtime013-flat-class-native-001.json) passes protected flat-class4Cu whole/direct/partial Route+fresh export, plain2Cu direct Route/export and2Cu Improve. [Actual GUI063](../evidence/gui-runtime013-063-native-opening-001.json) tests toolbar launch, pending class preview, Standard Route/review/test intent/fresh Native export, checked KiCad PCB opening and specific stale refusal. It retains6warnings/2ignored checks and the full106file pre-opening proof. Unsupported Improve correctly refuses but its specific preview reason was hidden; [the narrow display correction](../evidence/gui-preview-refusal-source-001.json) has targeted checks and still needs full148/fresh014 GUI qualification. No routing completion/family gain or completed release is claimed.

For the prepared checkout, close other KiCad applications and create a fresh launcher once:

```sh
.venv/bin/python -B scripts/install_gui.py --output .runs/autorouter-launcher-001
```

Choose a new folder name if that name exists. Double-click **Launch Autorouter.command**. The launcher starts KiCad with its own local settings, plugin and cache. It does not change global KiCad configuration, fetch libraries or close unrelated applications. Prepare a new launcher after a source update. Keep its checkout and pinned applications in place. Standard library warnings remain visible if libraries are absent.

1. Open your saved project in that KiCad manager, choose **Tools → PCB Editor**, then click the green autorouter icon. If KiCad's Open dialog leaves a valid file disabled, opening the exact `.kicad_pro` through Finder worked in the tested session. This is a workaround; the dialog cause is unresolved.
2. In the separate routing window, choose the exact saved **PCB** and an output folder. The matching project, schematic and original rule files must accompany it. Save and close source PCB/schematic editors before acknowledging the paths. Unsaved editor buffers cannot be inspected.
3. Choose scope and protection. **Finish gaps** preserves all existing copper; **Selected nets** preserves other copper; locked copper is always protected. Select supported layers, routing/via preferences and the time budget. **Save settings as…** and **Load settings…** persist choices outside the source. Unsupported combinations refuse with a reason instead of weakening constraints.
4. Use **Preview**, then **Route**. Preview is static support inspection; it does not establish Native acceptance. Progress appears in the findings panel. **Cancel** requests cooperative worker cleanup and never authorizes export. Retained files are not deleted.
5. Choose **Create review**, then **Open preview** and, when useful, **Open review project**. Compare the original/candidate copper on each layer and read every finding, warning and ignored check. Original reference routes may appear in the before view. The candidate's routing checks are separate from whole-project cleanliness and electrical/manufacturing review.
6. Close review PCB/schematic editors and use **File → Close Project** in KiCad manager before acknowledging review. **Reject intent** retains the original and cannot authorize export. **Accept intent** records a choice; it is not PCB certification or human review evidence. Software qualification uses test intent only.
7. **Fresh export** reruns original-rule Native refill, DRC, schematic and design-preservation checks into another separate project. **Open checked export** performs a cancellable current-proof check before opening that project in KiCad. The source is never overwritten.

Opening/editing a mutable exported project can update PRO/PRL/history and invalidate its proof. Any later edit requires new validation. A stale check refuses; it does not repair metadata or fall back to an older candidate. Preserve the exported evidence and original, and start a fresh workflow when needed. A failed checked export now shows the specific retained cause and full failure-log path. The job folder also retains `.command.log` and `.command.process.json`. A successful settings load may leave an earlier status message until Preview; verify the displayed choices before starting.

**Route** uses the fixed corrected-standard default. **Improve** is optional/experimental, choosing Tuned/Both while preserving scope/protection/layers/budget/via preference. Graphical Improve below90seconds refuses; this reserve is not a completion guarantee. Unsupported advanced electrical requirements remain blockers. The workflow offers no live-board application transaction or tested undo.

[Actual GUI061](../evidence/gui-runtime010-061-native-opening-001.json) qualifies toolbar launch, loading saved90second/protected settings,2Cu preview/Route/rendered review/test intent/fresh Native export and checked Manager/PCB opening. All8warnings/2ignored checks remain. Its87-file preopen proof is retained; natural KiCad normalization made the opened project stale and reopening visibly refused with the specific cause, next step and full log path. [Full143](../evidence/gui-export-refusal-full143-001.json) matches its runtime modules. Prior060Save/Load,059four-copper opening and002/054cancellation/rejection retain their separate evidence. No human approval or live undo claim.

The CLI and structured interface remain underneath. [Quickstart](quickstart.md) and [preferences](routing-preferences.md) cover routing; [structured workflow](structured-interface.md) documents the contract. Typical review commands are:

```sh
.venv/bin/python -B -m autorouter review-copy .runs/my-route/result.json --render --output .runs/my-review
.venv/bin/python -B -m autorouter review-choice .runs/my-review/review.json --choice accept --output .runs/my-choice
.venv/bin/python -B -m autorouter review-export .runs/my-choice/choice.json --seconds 120 --output .runs/my-export
.venv/bin/python -B -m autorouter review-export-check .runs/my-export/export.json
```

Use fresh output names. Substitute `--choice reject` to record rejection; it cannot authorize export. Control-C cancels CLI work. Historical GUI evidence and prior detailed guide versions remain in Git; they do not expand the supported matrix.
