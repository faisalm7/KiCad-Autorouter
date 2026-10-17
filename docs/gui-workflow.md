# Route and review from KiCad

The current installed CLI candidate is **runtime019**, source `321bc5bfdcb85c6975ee5b7e2accf09b6f43da84`. Its [fresh Native delivery](../evidence/runtime019-production-CLI-delivery-001.json) and [full156/installation/doctor](../evidence/runtime019-preflight-full156-001.json) pass. The [current launcher](../evidence/gui-runtime019-067-prepared-001.json) is prepared only; actual GUI qualification remains blocked by [fresh tool access failure](../evidence/gui-runtime019-067-access-blocked-001.json). Latest actual graphical evidence is [014/064](../evidence/gui-runtime014-064-native-opening-001.json), including protected four-layer Route, review, test intent, fresh export, checked opening and a correct stale refusal. Historical evidence does not qualify new GUI bytes. The [queued-opening correction](../evidence/gui-queued-open-source-001.json) adds final source/settings and export-material checks; it has controller regressions, not a new live GUI result.

On this Mac the prepared current launcher is `.runs/runtime-directory-019/runtime/.runs/gui-launcher067/Launch Autorouter.command` relative to the checkout. Close other KiCad applications before launching it. To prepare a different launcher from the checkout, use a fresh output:

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

Opening/editing a mutable exported project can update PRO/PRL/history and invalidate its proof. Any later edit requires new validation. A stale check refuses; it does not repair metadata or fall back to an older candidate. The queued opening callback rechecks saved source/settings and the authoritative export receipt/material using existing bounded byte witnesses. These checks are not atomic with later editor reads; the fresh cancellable CLI reader remains in the worker. Preserve the exported evidence and original, and start a fresh workflow when needed. A failed checked export now shows the specific retained cause and full failure-log path. The job folder also retains `.command.log` and `.command.process.json`. A successful settings load may leave an earlier status message until Preview; verify the displayed choices before starting.

**Route** uses the fixed corrected-standard default. **Improve** is optional/experimental, choosing Tuned/Both while preserving scope/protection/layers/budget/via preference. Graphical Improve below90seconds refuses; this reserve is not a completion guarantee. Unsupported advanced electrical requirements remain blockers. The workflow offers no live-board application transaction or tested undo.

Earlier [GUI061](../evidence/gui-runtime010-061-native-opening-001.json) retains saved-setting and specific stale-refusal observations. Prior cancellation/rejection and other GUI records retain their original source scope. No current live-editor transaction, undo or human PCB approval is claimed.

The CLI and structured interface remain underneath. [Quickstart](quickstart.md) and [preferences](routing-preferences.md) cover routing; [structured workflow](structured-interface.md) documents the contract. Typical review commands are:

```sh
.venv/bin/python -B -m autorouter review-copy .runs/my-route/result.json --render --output .runs/my-review
.venv/bin/python -B -m autorouter review-choice .runs/my-review/review.json --choice accept --output .runs/my-choice
.venv/bin/python -B -m autorouter review-export .runs/my-choice/choice.json --seconds 120 --output .runs/my-export
.venv/bin/python -B -m autorouter review-export-check .runs/my-export/export.json
```

Use fresh output names. Substitute `--choice reject` to record rejection; it cannot authorize export. Control-C cancels CLI work. Historical GUI evidence and prior detailed guide versions remain in Git; they do not expand the supported matrix.
