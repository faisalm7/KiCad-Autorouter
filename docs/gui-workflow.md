# Route and review from KiCad

The current tested Mac directory is runtime008, built from source `76d2c666`. It runs locally without an AI account. It still needs the pinned existing KiCad10.0.0, Java25.0.2 and local engine; it is not a standalone installer or Windows product. [Installation](install-test.md), [supported scope and issues](experimental-rc.md).

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

Opening/editing a mutable exported project can update PRO/PRL/history and invalidate its proof. Any later edit requires new validation. A stale check refuses; it does not repair metadata or fall back to an older candidate. Preserve the exported evidence and original, and start a fresh workflow when needed. The current generic failure panel may omit the detailed cause; the job folder's `.command.log` and `.command.process.json` retain it.

**Route** uses the fixed corrected-standard default. **Improve** is optional/experimental, choosing Tuned/Both while preserving scope/protection/layers/budget/via preference. Graphical Improve below90seconds refuses; this reserve is not a completion guarantee. Unsupported advanced electrical requirements remain blockers. The workflow offers no live-board application transaction or tested undo.

[Actual GUI059](../evidence/gui-runtime008-059-native-opening-001.json) qualifies protected4Cu preview/Route/rendered review/test intent/fresh Native export and checked Manager/PCB opening. All six Datasheet warnings and two ignored checks remain. The95-file preopen proof is exact; subsequent KiCad normalization made the opened export stale, and the next opening visibly refused. [GUI058's accounting refusal](../evidence/gui-runtime007-058-export-accounting-refusal-001.json) remains preserved; the producer correction and [full141](../evidence/export-cpu-roundoff-source-full141-001.json) are separate. Earlier actual002/054 cancellation/rejection retain their original scope;059 does not add those tests or human approval.

The CLI and structured interface remain underneath. [Quickstart](quickstart.md) and [preferences](routing-preferences.md) cover routing; [structured workflow](structured-interface.md) documents the contract. Typical review commands are:

```sh
.venv/bin/python -B -m autorouter review-copy .runs/my-route/result.json --render --output .runs/my-review
.venv/bin/python -B -m autorouter review-choice .runs/my-review/review.json --choice accept --output .runs/my-choice
.venv/bin/python -B -m autorouter review-export .runs/my-choice/choice.json --seconds 120 --output .runs/my-export
.venv/bin/python -B -m autorouter review-export-check .runs/my-export/export.json
```

Use fresh output names. Substitute `--choice reject` to record rejection; it cannot authorize export. Control-C cancels CLI work. Historical GUI evidence and prior detailed guide versions remain in Git; they do not expand the supported matrix.
