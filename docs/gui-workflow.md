# Route and review from KiCad

Current build: **runtime033**, source `a476a0a0647bc51889d291e3e6e2598f4ec24370`, manifest `115c881aa04a34bf642c57d5af312fe692d1aff013bed095caa3856a614f3987`, selected KiCad10.0.7. [Full176/install006 and ordinary CLI](../evidence/runtime033-ordinary-install-001.json), [same-account clean environment](../evidence/runtime033-clean-environment-001.json) and the [actual GUI074 set](../evidence/gui-runtime033-074-native-controls-001.json) pass within their declared scopes.

GUI074 covers seven roles: actual owner-assisted toolbar launch, budget 0 refusal/preset round trip, protected F.Cu/B.Cu rendering, missing-review-acknowledgement and open-review-project refusals, close+accept/reject,90 checked opening,420 routing/120 export and three independent source/settings/typed-export refusals. Six owned2Cu positive Routes and five saved pre-open exports each have their own Native0/0/0/0/full-schematic/original proof and4 protected items. The cancellation role uses exposed Interf whole/default90: actual engine cancellation, CLI exit2/engine−9/cleanup, no accepted result/export. These two functional fixtures establish no broader routing quality, every-setting, all-phase/SIGINT-only/permanent-descendant, live application/undo or human PCB review. Forced queued timing was not observed; full176 callback regressions remain separate software proof.

The checked90 export actually opened and rendered in KiCad with 0 unrouted. Its PCB bytes remained exact; KiCad later changed PRO/PRL and added a backup ZIP despite no user editing. Saved pre-open proof and later correct stale refusal remain distinct; no fresh Native check after opening is inferred. [026/GUI072](../evidence/gui-runtime026-072-native-controls-001.json) and preserved029/GUI073 keep their historical scope.

The existing launcher is:

```text
/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-033/runtime/.runs/gui-launcher074/Launch Autorouter.command
```

Save and close other KiCad applications, then double-click it. It starts KiCad with its own local plugin/settings/cache and does not change global settings, fetch libraries or close unrelated applications. Keep the runtime and pinned tools at their recorded paths. [Preparation and limits](runtime-directory.md). A new launcher does not itself qualify a new build.

1. Open the saved project in this KiCad manager, open PCB Editor and click the green autorouter icon. The routing manager runs separately; expensive work stays outside the editor.
2. Choose the exact saved PCB and output folder. The matching project, schematic and original rule files must accompany it. Save and close source PCB/schematic editors, then acknowledge the paths. Unsaved buffers cannot be inspected.
3. Choose the supported task and budget. In current selected10.0.7 use **Route** with its default corrected-standard/both preferences, whole unlocked routing or **Finish gaps**, all source layers/default vias. Finish gaps protects all existing copper; locked copper is always protected. Selected-net/layer restrictions and Improve refuse in this profile; retained10.0.0 experiments are separate. Missing electrical current/return-path/impedance/timing requirements are never guessed.
4. Type a whole routing allocation from5 to900 seconds. Invalid/out-of-range text refuses instead of becoming a different budget. **Save settings as…** and **Load settings…** persist outside the source. Fresh export has a separately disclosed30–120-second validation allocation:90 routing gives90 export;420 routing gives120 export. Saved routing settings are unchanged. A short allocation can still be insufficient for required checks and safely refuse.
5. Use **Preview**, then **Route**. Preview is static support inspection, not Native acceptance. Progress/findings appear in the window. **Cancel** requests cleanup and never authorizes export; retained files remain. The observed074 cancellation is engine-phase with eventual−9 after a SIGINT request and CLI exit2, not all-phase or SIGINT-only proof.
6. Choose **Create review**, then **Open preview** or **Open review project**. Inspect copper on every layer and read all warnings/ignored checks. Before/after images can include original reference routes. Routing acceptance is distinct from whole-project cleanliness and electrical/manufacturing review.
7. Close review editors and use **File → Close Project** in the manager before acknowledging review. **Reject intent** cannot authorize export. **Accept intent** records a choice, not PCB certification or evidence of independent human review. Software qualification uses test intent.
8. **Fresh export** reruns original-rule Native refill, DRC, schematic and design checks into another separate project. **Open checked export** performs a cancellable current-proof check before opening it. The source is never overwritten; no live application/undo is offered.

Later editing/opening can change exported PRO/PRL/history and stale its proof. A stale check refuses without repairing metadata or falling back. The queued opener rechecks source/settings and typed export material; these cooperative byte checks are not atomic with later editor reads. Preserve originals/evidence and start a fresh workflow when necessary. Failure details and command/process logs stay in the job directory. Verify displayed choices after loading a preset; an earlier status message may remain until Preview.

For a preset under a hidden directory such as `.runs`, enable hidden-file visibility in the native picker with **Command–Shift–Period** if a selected file leaves **Open** disabled. This visibility step worked in retained sessions; it is not a security-setting change. Standard missing-library warnings remain visible and no library is fetched automatically.

The pristine074 qualification source is under this runtime’s `.runs/gui-session074/project`, with separate `inspection` and `jobs` directories. Preserve its recorded bytes; use the inspection copy for editor observations. User jobs must likewise bind the intended saved source and fresh output explicitly.

Thermal recovery in qualified033 remains **opt-in CLI only**. The ROOT graphical-recovery patch has 65 targeted checks but is unbuilt/unqualified and is not a033 menu capability. The next candidate must independently qualify its exact two-layer/whole/native/standard/both/all-source/default-via method,90–900-second whole-method budget, separate export, repair/no-repair/invalid/cancel and actual GUI paths. It does not promote the default or add algorithms.

The [CLI](quickstart.md), [preferences](routing-preferences.md) and [structured contract](structured-interface.md) remain underneath. From the runtime, with fresh names:

```sh
.venv/bin/python -B -m autorouter review-copy .runs/my-route/result.json --render --output .runs/my-review
.venv/bin/python -B -m autorouter review-choice .runs/my-review/review.json --choice accept --output .runs/my-choice
.venv/bin/python -B -m autorouter review-export .runs/my-choice/choice.json --seconds 120 --output .runs/my-export
.venv/bin/python -B -m autorouter review-export-check .runs/my-export/export.json
```

Explicit export budgets outside30–120 refuse; a longer route does not widen that API. Substitute `--choice reject` in a fresh workflow for rejection; Control-C requests CLI cancellation. Every delivered final requires its own current proof. [025 focus-loss failure](../evidence/runtime025-GUI071-budget-refusal-failure-001.json) and [023 GUI](../evidence/gui-runtime023-070-native-controls-001.json) remain historical, not substituted current qualification. Forced queued races, every phase/setting, live application/undo and human PCB approval remain unqualified.
