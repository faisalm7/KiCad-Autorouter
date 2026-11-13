# Persistent routing settings

Save/load presets in the graphical window, or pass an explicit JSON file with `--settings`. Keep presets outside the saved source project. Jobs capture exact bytes; changing source or captured settings invalidates the job. There is no implicit personal/global configuration search, and routing does not rewrite presets or original KiCad rules.

Current081-and-later operation and warning-review clocks include host sleep. Expired work refuses adoption; sleep does not grant extra routing time.081 installation/Native/full254/GUI111 finite-core evidence is retained. Physical suspend itself remains untested; historical080 retains its timing limitation.

A value accepted by the JSON schema is not automatically supported by selected KiCad10.0.7:

| Choice | Current ordinary Route | Limit |
|---|---|---|
| Scope/protection | Whole-board reroutes unlocked copper while preserving locked routes. Finish gaps (`partial_completion`, CLI `--scope partial` or `--keep-existing`) preserves every existing route. | The bounded selected path requires pinned10.0.7, canonical20260206 or exact20241229 numeric-table input, original0/F.Cu and2/B.Cu, sole Default with no assignments/patterns, complete flat schematic, completion-only/both/native/source_all/default-score.086 has an actual20241229 protected delivery control; actual086GUI remains pending. Other formats, subsets and combinations refuse. Historical10.0.0 controls do not transfer. |
| Budget | Finite5–900 seconds, excluding booleans; default120. Preparation/final checks consume wall and measured CPU limits. | Small budgets may refuse. GUI Improve/recovery require90+. Separate export30–120s does not enlarge routing time. |
| Profile/corrections | Whole/partial Route uses `standard`, `both`; corrected-standard/B1 remains default. | The narrow selected path uses `completion-only`, `both`. Other ordinary combinations refuse; comparison administration is separate. |
| Guidance | `native`; original rules remain authoritative. | Other guidance is not ordinary-profile admission. |
| Allowed new layers | `source_all`, preserving original stackup, on supported2/4Cu sources. | Explicit subsets/single-layer choices remain refused. |
| Via preference | `scoring_preference: null` default, or explicit `"via_high"`. | Higher search cost does not guarantee fewer vias or electrical suitability. Other scores refuse; Improve/recovery require `null`. |

Use the installed runtime directory printed by installation before invoking its module. Replace the example path below with that directory:

```sh
cd '/absolute/path/to/installed-runtime'
.venv/bin/python -B -m autorouter settings-init --output .runs/my-settings-001.json
```

A partial90 ordinary preset is:

```json
{
  "schema": 1,
  "scope": "partial_completion",
  "seconds": 90,
  "adapter": "both",
  "profile": "standard",
  "guidance": "native",
  "layers": "source_all",
  "scoring_preference": null
}
```

For higher via cost, change only the final value to `"via_high"` in a fresh preset. Load it and verify displayed choices before Preview, or pass `--settings /absolute/preset.json`. Explicit CLI options override only that run; they do not edit the file. Keep critical copper locked or use Finish gaps. Current, impedance, timing and return-path requirements need their own checks/review; DRC alone cannot establish them.

Improve is a separate experimental canonical2Cu/flat/whole/native/tuned/both/source_all/default-score method using the single-proposal policy. Its source guard accepts sole explicit/implicit Default or the narrowly checked Native parent-class policy. The [074 matched-class control](../evidence/runtime074-installed-native-milestone-001.json) preserves the original `Default`, `SIGNAL` and `POWER` classes, exercises one actual trial and retains protected copper, own export proof and wrong-width/source-PRO negatives. This does not qualify arbitrary class assignments, selected Improve, explicit layer subsets or advanced constraints.

The whole Improve budget includes tuned incumbent, pruning trials, final checks and40s internal return reserve; the reserve does not enlarge wall/fullCPU caps or guarantee completion. [073 GUI104's addendum](../evidence/gui-runtime073-104-addendum-002.json) records class fresh export and checked opening; it does not qualify runtime074. Historical [GUI103](../evidence/gui-runtime070-103-qualification-001.json) retains its original cancellation outcomes and reporting defect. GUI105 finite core passes its recorded gates. The genuine changed-warning dialog and exact queued callback interval remain unexercised. Cancellation, staleness or invalid constraints never authorize fallback. Thermal Recover is distinct and not current GUI-qualified. [Method requirements](gui-workflow.md).

[074 headless evidence](../evidence/runtime074-installed-native-milestone-001.json) and [six live warning-review controls](../evidence/runtime074-warning-native-controls-001.json) apply to build `6fbbbf22dfb8`, manifest `584ee929eaf3`. The opt-in updated-warning path requires the same candidate/metrics/counts/ignored rules and complete current proof; both finding lists remain visible and retained. Explicit acknowledgement stays inside the original export30–120s budget, including human wait. Default CLI stays strict. Actual074 GUI acknowledgement/rejection remains unqualified; no warning equivalence or electrical approval is inferred. [STATUS](../STATUS.md), [release gates](experimental-rc.md) and [CLI](quickstart.md) identify separate gates. Historical versioned packets keep their original outcomes. The current074 large CLI delivery passes its frozen total and review/choice headroom gates; it is one exposed case, not a broad comparison.

The optional **Completion search (may add vias)** Route preset is included from075 onward. It selects `tuned` with `via_low` without changing scope, protected copper, layers or budget, and revokes the previous job's acceptance/export controls. It initially requires canonical two-layer20241229/20260206 boards, a sole Default class with no assignments/patterns, and a complete flat schematic. Preview and every result reader must derive and verify that eligibility. Improve and selected-net modes do not inherit it. This is existing Freerouting search configuration, not a new algorithm or evidence of superiority over restartB2. Runtime074 remains unchanged and refuses this ordinary combination.075 exposed-task evidence delivers EEPROM; STM32 routes to zero opens but strict export refuses changed warnings without fresh acknowledgement. This does not establish generalized gain. Each changed build still needs its relevant qualification.
