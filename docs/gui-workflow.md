# Route and review from KiCad

Current build: **runtime026**, source `1117de080524072046a61522845facd5d4c68575`, manifest `5371d08ccf5a0ae2e0c4024f752baca28f034c3b3cb50ade308e8e5e12e36fe5`, selected KiCad10.0.7. [Full167](../evidence/gui-budget-text-integration-001.json), doctor and [whole](../evidence/runtime026-installed-CLI-001.json)/[partial](../evidence/runtime026-installed-partial-CLI-001.json) six-stage CLI delivery pass.

[Actual GUI026/072 controls](../evidence/gui-runtime026-072-native-controls-001.json) complete the declared seven-job set on one exposed owned2Cu partial family: toolbar, strict invalid/0 budget refusal,90-second preset load/save, protected Route, rendered F.Cu/B.Cu review, acceptance acknowledgement refusal, accept/reject, fresh90/120 exports, checked90-second PCB opening and three independent source/settings/typed-export refusals. All six positive Routes and five pre-open exports retain their own Native0opens/0blocking/0warnings/0exclusions, full-schematic/original proof and4 protected items. Actual cancellation reached the engine: SIGINT was requested, final exit was−9, cleanup passed and no result/export was accepted. This is not SIGINT-only termination, all-phase cancellation, forced queued-race timing, every-setting, human review or live application/undo qualification. Opening the90-second export left the PCB hash unchanged but KiCad changed its PRO/PRL and added a backup ZIP. The saved82-file pre-open proof remains exact; the current export reader correctly refuses the later metadata-changed output. No new Native validation after opening is inferred.

The existing launcher is:

```text
/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-026/runtime/.runs/gui-launcher072/Launch Autorouter.command
```

Save and close other KiCad applications, then double-click it. It starts KiCad with its own local plugin/settings/cache and does not change global settings, fetch libraries or close unrelated applications. Keep the runtime and pinned tools at their recorded paths. [Preparation and limits](runtime-directory.md). A new launcher does not itself qualify a new build.

1. Open the saved project in this KiCad manager, open PCB Editor and click the green autorouter icon. The routing manager runs separately; expensive work stays outside the editor.
2. Choose the exact saved PCB and output folder. The matching project, schematic and original rule files must accompany it. Save and close source PCB/schematic editors, then acknowledge the paths. Unsaved buffers cannot be inspected.
3. Choose the supported task and budget. In current selected10.0.7 use **Route** with its default corrected-standard/both preferences, whole unlocked routing or **Finish gaps**, all source layers/default vias. Finish gaps protects all existing copper; locked copper is always protected. Selected-net/layer restrictions and Improve refuse in this profile; retained10.0.0 experiments are separate. Missing electrical current/return-path/impedance/timing requirements are never guessed.
4. Type a whole routing allocation from5 to900 seconds. Invalid/out-of-range text refuses instead of becoming a different budget. **Save settings as…** and **Load settings…** persist outside the source. Fresh export has a separately disclosed30–120-second validation allocation:90 routing gives90 export;420 routing gives120 export. Saved routing settings are unchanged. A short allocation can still be insufficient for required checks and safely refuse.
5. Use **Preview**, then **Route**. Preview is static support inspection, not Native acceptance. Progress/findings appear in the window. **Cancel** requests cleanup and never authorizes export; retained files remain. The observed072 cancellation is engine-phase with eventual−9 after a SIGINT request, not all-phase or SIGINT-only proof.
6. Choose **Create review**, then **Open preview** or **Open review project**. Inspect copper on every layer and read all warnings/ignored checks. Before/after images can include original reference routes. Routing acceptance is distinct from whole-project cleanliness and electrical/manufacturing review.
7. Close review editors and use **File → Close Project** in the manager before acknowledging review. **Reject intent** cannot authorize export. **Accept intent** records a choice, not PCB certification or evidence of independent human review. Software qualification uses test intent.
8. **Fresh export** reruns original-rule Native refill, DRC, schematic and design checks into another separate project. **Open checked export** performs a cancellable current-proof check before opening it. The source is never overwritten; no live application/undo is offered.

Later editing/opening can change exported PRO/PRL/history and stale its proof. A stale check refuses without repairing metadata or falling back. The queued opener rechecks source/settings and typed export material; these cooperative byte checks are not atomic with later editor reads. Preserve originals/evidence and start a fresh workflow when necessary. Failure details and command/process logs stay in the job directory. Verify displayed choices after loading a preset; an earlier status message may remain until Preview.

For a preset under a hidden directory such as `.runs`, enable hidden-file visibility in the native picker with **Command–Shift–Period** if a selected file leaves **Open** disabled. This visibility step worked in retained sessions; it is not a security-setting change. Standard missing-library warnings remain visible and no library is fetched automatically.

The [CLI](quickstart.md), [preferences](routing-preferences.md) and [structured contract](structured-interface.md) remain underneath. From the runtime, with fresh names:

```sh
.venv/bin/python -B -m autorouter review-copy .runs/my-route/result.json --render --output .runs/my-review
.venv/bin/python -B -m autorouter review-choice .runs/my-review/review.json --choice accept --output .runs/my-choice
.venv/bin/python -B -m autorouter review-export .runs/my-choice/choice.json --seconds 120 --output .runs/my-export
.venv/bin/python -B -m autorouter review-export-check .runs/my-export/export.json
```

Explicit export budgets outside30–120 refuse; a longer route does not widen that API. Substitute `--choice reject` in a fresh workflow for rejection; Control-C requests CLI cancellation. Every delivered final requires its own current proof. [025 focus-loss failure](../evidence/runtime025-GUI071-budget-refusal-failure-001.json) and [023 GUI](../evidence/gui-runtime023-070-native-controls-001.json) remain historical, not substituted current qualification. Forced queued races, every phase/setting, live application/undo and human PCB approval remain unqualified.
