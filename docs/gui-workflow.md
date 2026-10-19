# Route and review from KiCad

Use the existing **runtime039 / GUI079 experimental launcher** with KiCad 10.0.7 on this Mac. Begin with a saved test project or a copy. Keep the original design separate from every generated candidate.

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

Current qualification is deliberately narrower than complete GUI support. Ordinary GUI079 has an actual positive through reviewed front/back images, accept intent, fresh Native export and checked KiCad rendering with 0 unrouted; all four original copper records remain protected. Reject and independent source/settings/typed-export change refusals were observed. Engine-phase cancellation produced CLI exit 2, engine −9 and cleanup, with no accepted export; this is not SIGINT-only, every-phase or permanent-descendant proof. One bounded queued-opening controller missed the reader interval without pausing or mutating it: it is **not** an actual forced queued-race pass. Callback timing remains software-test evidence in full184. [Ordinary controls](../evidence/gui-runtime039-079-ordinary-controls-001.json) retain those actual observations.

The recorded positive’s fresh 89-file preopen snapshot is retained. After KiCad opened and closed the candidate without a requested edit/save, export PRO/PRL and a backup ZIP changed; PCB/source bytes stayed unchanged and current proof correctly refused “export inputs/runtime/evidence changed”. Fresh preopen proof and later stale refusal are separate observations. [GUI positive/reject evidence](../evidence/gui-runtime039-079-positive-reject-001.json), [Native/CLI milestone](../evidence/runtime039-native-floor-schema-milestone-001.json), [status](../STATUS.md) and [support matrix](experimental-rc.md) retain the exact scope and remaining gates.

Experimental [**recovery**](../evidence/gui-runtime039-079-recovery-repair-001.json) remains optional; corrected-standard/B1 stays the ordinary default. It requires selected KiCad 10.0.7, two copper layers, whole-board/native/standard/both/all-source/default-via settings and a 90–900-second whole-method allocation, plus separate capped export. The current exposed Interf case completed routing with 0 opens, 0 blocking findings, 22 warnings and 0 exclusions; the 420-method/120-export display was correct. Edge review of all findings, acknowledged accept, fresh Native export120 and checked KiCad opening are now complete, with 0 unrouted. All 175 fresh preopen files are retained; later PRO/PRL/backup ZIP changes correctly stale current proof while PCB/source remain unchanged. Fresh post-incumbent cancellation, no-repair and hierarchy GUI remain pending. The 89-second-budget and layer refusal controls were observed before workspace creation. An earlier four-layer fixture refused at its schematic prerequisite; retain that distinct reason rather than claiming it as direct layer qualification. One exposed family establishes no broader routing/cleanup/electrical superiority.

The fixture used for the ordinary controls is this runtime’s `.runs/gui-session079/project`, with separate `inspection` and `jobs` directories. Preserve its recorded bytes and use inspection copies for editor observations. Real user jobs must bind their own saved source and fresh output. The local setup uses existing fixed-path dependencies; it is not clean-OS, relocation, standalone or Windows qualification. Human/electrical/manufacturing approval, every setting/phase, live undo and a formal release remain open. [Earlier workflow notes and historical evidence references](https://github.com/faisalm7/KiCad-Autorouter/blob/12ad0f6c/docs/gui-workflow.md) keep their original build-specific scope.

The [CLI](quickstart.md), [saved preferences](routing-preferences.md) and [structured interface](structured-interface.md) use the same checks. From the runtime, with fresh output names:

```sh
.venv/bin/python -B -m autorouter review-copy .runs/my-route/result.json --render --output .runs/my-review
.venv/bin/python -B -m autorouter review-choice .runs/my-review/review.json --choice accept --output .runs/my-choice
.venv/bin/python -B -m autorouter review-export .runs/my-choice/choice.json --seconds 120 --output .runs/my-export
.venv/bin/python -B -m autorouter review-export-check .runs/my-export/export.json
```

Explicit CLI export budgets outside 30–120 seconds refuse. Use `--choice reject` in a fresh workflow for rejection; Control-C requests CLI cancellation. Each delivered final needs its own current proof. Routing-scope acceptance is separate from whole-project DRC cleanliness and physical/electrical validation.
