# Route and review from KiCad

Use the existing **runtime041 / GUI080 experimental launcher** with KiCad 10.0.7 on this Mac. Begin with a saved test project or a copy. Keep the original design separate from every generated candidate.

1. **Open the launcher.** Save your work and close other KiCad applications. In Finder, double-click [Launch Autorouter.command](</Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-039/runtime/.runs/gui-launcher079/Launch Autorouter.command>). Or press **Command–Shift–G** in Finder and enter:

   ```text
   /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-039/runtime/.runs/gui-launcher079
   ```

   It starts KiCad with isolated local plugin/settings/cache. It does not install KiCad, change global settings, fetch libraries or close unrelated applications. Keep this runtime and its pinned dependencies at their recorded paths. [Setup and limits](runtime-directory.md).

2. **Open your project and the routing window.** In that KiCad manager, open the saved project, open PCB Editor and click the **green autorouter icon**. Choose the exact saved source PCB and output folder in the separate routing window. The matching project, schematic and original rule files must accompany the PCB. Save and close source PCB/schematic editors, then confirm their paths. Unsaved buffers cannot be inspected.

3. **Choose a supported task.** Start with the **90-second Finish gaps preset** and default preferences. Finish gaps protects all existing tracks/vias; locked copper is always protected. The ordinary Route method also supports whole-board unlocked routing in qualified two- and four-copper-layer combinations, using all source layers and default vias. Unsupported selected-net/layer settings and Improve refuse in this profile. Unknown electrical intent is not guessed.

4. **Preview, then Route.** **Preview** explains static support; it is not KiCad acceptance. **Route** runs work outside the editor and shows progress/findings. **Cancel** requests cleanup, retains evidence and cannot authorize export. Read the result before continuing, including incomplete connectivity or validation failures.

5. **Inspect the review.** Use **Create review**, then **Open preview** for local HTML with before/after layer images, or **Open review project** for KiCad inspection. Read every warning and ignored check; original images can include reference routing. If Chrome is in use, open the generated local HTML in Edge through **File → Open File…**, without changing the OS default browser. Close the tab when finished. If you opened a KiCad review project, close its editors and use **File → Close Project** before acknowledging review.

6. **Record your decision.** Acknowledge that you inspected the review, then choose **Accept intent** or **Reject intent**. Reject cannot authorize export. Accept records a software choice, not PCB certification or an independent human engineering review.

7. **Create a fresh, separate export.** **Fresh export** reruns KiCad refill/connectivity, full-schematic, original-rule and design/protected-copper checks into another project. Validation has a separately displayed allocation: a 90-second route gives 90 seconds for export; a 420-second allocation gives 120 seconds for export. The saved routing settings are unchanged. A short allowance can safely refuse if checks cannot finish.

8. **Open the checked export.** **Open checked export** performs a cancellable current-proof check before opening the candidate in KiCad. The source is never overwritten; transactional live application/undo is not provided. Later opening/editing can change project settings or backups and stale the proof. A stale check refuses without repairing evidence or falling back. Preserve originals and start a fresh workflow when necessary. Checks are cooperative and not atomic with later editor reads.

You can change the routing allocation from 5 to 900 whole seconds; invalid text refuses instead of becoming a different budget. **Save settings as…** and **Load settings…** keep presets outside the source. Verify the displayed choices after loading; use Preview to refresh support information. For hidden folders such as `.runs`, **Command–Shift–Period** in the native file picker toggles visibility. This changes visibility, not a security setting. Standard missing-library warnings remain visible; nothing is fetched automatically. [Preferences and supported choices](routing-preferences.md).

Current041 qualification is partial: actual toolbar/settings/zero-budget refusal, protected canonical and source-display-alias routing, Edge F+B review, accept acknowledgement/open-project refusals, fresh export and checked KiCad opening0unrouted, plus separate Reject. Two original ignored checks remain. Remaining independent freshness/cancellation/hierarchy/high-budget/optional recovery roles are pending. Forced queued timing and Native interruption remain unproved. [Current progress](../evidence/gui-runtime041-080-progress-001.json).

Both041 positive deliveries retain fresh89-file preopen proof. Later KiCad opening changes PRO/PRL and adds a backupZIP while source/candidatePCB remain unchanged; these later bytes are preserved as observations after opening, not renewed Native validity. [Current state](../STATUS.md) and [Native evidence](../evidence/runtime041-native-milestone-001.json) retain the limits.

Experimental thermal recovery remains optional; corrected-standard/B1 is default. Recovery requires selected10.0.7/two-layer/whole/native/standard/both/all-source/default-via settings and90–900seconds whole-method budget plus a separate capped export. Current041 static partial/89-second and unsupported-schematic controls refuse; its positive/recovery-cancel/no-repair roles are pending. [Historical039 recovery](../evidence/gui-runtime039-079-recovery-repair-001.json), [no-repair](../evidence/gui-runtime039-079-recovery-no-repair-001.json) and [post-incumbent Cancel](../evidence/gui-runtime039-079-postincumbent-cancel-001.json) retain earlier scope, including22Interfwarnings and no proven Native interruption. One exposed family is not general completion/cleanup/electrical superiority.

The fixture used for the ordinary controls is this runtime’s `.runs/gui-session079/project`, with separate `inspection` and `jobs` directories. Preserve its recorded bytes and use inspection copies for editor observations. Real user jobs must bind their own saved source and fresh output. The local setup uses existing fixed-path dependencies; it is not clean-OS, relocation, standalone or Windows qualification. Human/electrical/manufacturing approval, every setting/phase, live undo and a formal release remain open. [Earlier workflow notes and historical evidence references](https://github.com/faisalm7/KiCad-Autorouter/blob/12ad0f6c/docs/gui-workflow.md) keep their original build-specific scope.

The [CLI](quickstart.md), [saved preferences](routing-preferences.md) and [structured interface](structured-interface.md) use the same checks. From the runtime, with fresh output names:

```sh
.venv/bin/python -B -m autorouter review-copy .runs/my-route/result.json --render --output .runs/my-review
.venv/bin/python -B -m autorouter review-choice .runs/my-review/review.json --choice accept --output .runs/my-choice
.venv/bin/python -B -m autorouter review-export .runs/my-choice/choice.json --seconds 120 --output .runs/my-export
.venv/bin/python -B -m autorouter review-export-check .runs/my-export/export.json
```

Explicit CLI export budgets outside 30–120 seconds refuse. Use `--choice reject` in a fresh workflow for rejection; Control-C requests CLI cancellation. Each delivered final needs its own current proof. Routing-scope acceptance is separate from whole-project DRC cleanliness and physical/electrical validation.
