# Route and review from KiCad

Use the existing **immutable runtime042 / GUI081 experimental launcher** with KiCad10.0.7 on this Mac. Its [assigned functional roles](../evidence/gui-runtime042-081-functional-summary-001.json) and [Native qualification](../evidence/runtime042-native-milestone-001.json) are recorded. These are bounded functional checks, not full GUI, release or independent user qualification. Begin with a saved test project or copy and keep originals separate from generated candidates.

1. **Open the launcher.** Save your work and close conflicting KiCad sessions before starting the isolated test session. In Finder, double-click [Launch Autorouter.command](</Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-042/runtime/.runs/gui-launcher081/Launch Autorouter.command>). Or press **Command–Shift–G** in Finder and enter:

   ```text
   /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-042/runtime/.runs/gui-launcher081
   ```

   It starts KiCad with isolated local plugin/settings/cache. It does not install KiCad, change global settings, fetch libraries or close unrelated applications. Keep this runtime and its pinned dependencies at their recorded paths. [Setup and limits](runtime-directory.md).

2. **Open your project and the routing window.** In that KiCad manager, open the saved project, open PCB Editor and click the **green autorouter icon**. Choose the exact saved source PCB and output folder in the separate routing window. The matching project, schematic and original rule files must accompany the PCB. Save and close source PCB/schematic editors, then confirm their paths. Unsaved buffers cannot be inspected.

3. **Choose a supported task.** Start with the **90-second Finish gaps preset** and default preferences. Finish gaps protects all existing tracks/vias; locked copper is always protected. The ordinary Route method also supports whole-board unlocked routing in qualified two- and four-copper-layer combinations, using all source layers and default vias. Unsupported selected-net/layer settings and Improve refuse in this profile. Unknown electrical intent is not guessed.

4. **Preview, then Route.** **Preview** explains static support; it is not KiCad acceptance. **Route** runs work outside the editor and shows progress/findings. **Cancel** requests cleanup, retains evidence and cannot authorize export. Read the result before continuing, including incomplete connectivity or validation failures.

5. **Inspect the review.** Use **Create review** for local HTML with before/after layer images, or **Open review project** for KiCad inspection. Use **Microsoft Edge → File → Open File…** to view the generated `review/preview.html`, without changing the default browser or using Chrome. Read every warning and ignored check; original images can include reference routing. Close the review tab when finished. If you opened a KiCad review project, close its editors and use **File → Close Project** before acknowledging review.

6. **Record your decision.** Acknowledge that you inspected the review, then choose **Accept intent** or **Reject intent**. Reject cannot authorize export. Accept records a software choice, not PCB certification or an independent human engineering review.

7. **Create a fresh, separate export.** **Fresh export** reruns KiCad refill/connectivity, full-schematic, original-rule and design/protected-copper checks into another project. Validation has a separately displayed allocation: a 90-second route gives 90 seconds for export; a 420-second allocation gives 120 seconds for export. The saved routing settings are unchanged. A short allowance can safely refuse if checks cannot finish.

8. **Open the checked export.** **Open checked export** performs a cancellable current-proof check before opening the candidate in KiCad. The source is never overwritten; transactional live application/undo is not provided. Later opening/editing can change project settings or backups and stale the proof. A stale check refuses without repairing evidence or falling back. Preserve originals and start a fresh workflow when necessary. Checks are cooperative and not atomic with later editor reads.

You can change the routing allocation from 5 to 900 whole seconds; invalid text refuses instead of becoming a different budget. **Save settings as…** and **Load settings…** keep presets outside the source. Verify the displayed choices after loading; use Preview to refresh support information. For hidden folders such as `.runs`, **Command–Shift–Period** in the native file picker toggles visibility. This changes visibility, not a security setting. Standard missing-library warnings remain visible; nothing is fetched automatically. [Preferences and supported choices](routing-preferences.md).

The [frozen042 functional summary](../evidence/gui-runtime042-081-functional-summary-001.json) links actual toolbar/settings/invalid-budget refusal, protected canonical and display-alias delivery, Edge front/back review, acknowledgement/open-project refusals and explicit Reject. Source/settings refusals and an export change after its reader returned are observed; the finite GUI pause also delayed adoption and does not prove CallAfter was already queued. Ordinary Java Cancel and hierarchy420/export120 delivery pass. Canonical/alias controls protect4 items; hierarchy protects0. Original warnings and ignored checks remain visible.

Each delivery retains its own preopen Native proof. Later KiCad opening can change PRO/PRL/backups while source and candidate PCB stay unchanged; those observations do not renew validity of a changed export. The repair control displayed old-format and3D-model notices; only its automatic unsaved conversion was discarded. [Current state](../STATUS.md) retains the exact scope.

**Experimental thermal recovery** is optional; corrected-standard/B1 stays default. It requires selected10.0.7, two copper layers, whole-board/native/standard/both/all-source/default-via settings and90–900seconds for the whole method, plus separate capped export validation. Incompatible settings refuse without changing them. [Current081 recovery deliveries](../evidence/gui-runtime042-081-recovery-deliveries-001.json) retain no-repair90/export90 with0all findings/protected1 and repair420/export120 with0opens/0blocking/22warnings/0exclusions/seven ignored/protected0. The latter is not a protection positive or whole-project DRC-clean. Four-layer recovery refusal occurred at an earlier schematic-class gate, so the two-layer guard was not isolated by that control.

[Forced current081 cancellation](../evidence/gui-runtime042-081-postincumbent-cancel-001.json) held one identified Native refill worker before actual GUI Cancel. Worker-15/cleanup, CLI2, cancelled parent notchecked/unaccepted and separately valid incumbent were retained without fallback/export. This verifies the reporting correction at that interval; it does not establish natural timing, SIGINT-only, all-phase or permanent process absence.

For the ordinary owned control, use this runtime's `.runs/gui-session081/project/owned1007-transport.kicad_pro` and `.runs/gui-session081/route-settings.json`90-second preset. `inspection`, `alias-project` and `jobs` are separate. Preserve pristine recorded bytes and choose fresh output names. Fixed-path dependencies, no cleanOS/relocation/standalone/Windows, no human/electrical approval or live undo, and no general routing-quality claim remain explicit. [Historical041 roles](../evidence/gui-runtime041-080-functional-summary-001.json) retain their own scope and reporting defect; no old GUI evidence qualifies042.

The [CLI](quickstart.md), [saved preferences](routing-preferences.md) and [structured interface](structured-interface.md) use the same checks. From the runtime, with fresh output names:

```sh
.venv/bin/python -B -m autorouter review-copy .runs/my-route/result.json --render --output .runs/my-review
.venv/bin/python -B -m autorouter review-choice .runs/my-review/review.json --choice accept --output .runs/my-choice
.venv/bin/python -B -m autorouter review-export .runs/my-choice/choice.json --seconds 120 --output .runs/my-export
.venv/bin/python -B -m autorouter review-export-check .runs/my-export/export.json
```

Explicit CLI export budgets outside 30–120 seconds refuse. Use `--choice reject` in a fresh workflow for rejection; Control-C requests CLI cancellation. Each delivered final needs its own current proof. Routing-scope acceptance is separate from whole-project DRC cleanliness and physical/electrical validation.
